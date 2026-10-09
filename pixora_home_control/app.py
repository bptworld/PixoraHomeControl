"""Local HA API bridge with an authenticated, outbound-only Pixora connection."""
import asyncio
import json
import hashlib
import logging
import os
from pathlib import Path
import re
import time
import aiohttp

ORIGIN = 'https://homecontrol.pixorahq.com'
SOCKET = 'wss://homecontrol.pixorahq.com/api/homecontrol/connector/socket'
API = 'http://supervisor/core/api'
HA_SOCKET = 'ws://supervisor/core/websocket'
LOG = logging.getLogger('pixora_home_control')


def allowed(path, method):
    return (method == 'GET' and (path in {'/api/', '/api/config', '/api/states', '/api/services', '/pixora/registry'} or re.fullmatch(r'/api/states/[a-z0-9_]+\.[a-z0-9_]+', path))) or (method == 'POST' and re.fullmatch(r'/api/services/[a-z0-9_]+/[a-z0-9_]+', path))


class LocalAPI:
    def __init__(self, session, token):
        self.session, self.token = session, token
        self.socket = None
        self.pending = {}
        self.counter = 1

    async def request(self, path, method='GET', payload=None):
        async with self.session.request(method, API + path.removeprefix('/api'), json=payload if method == 'POST' else None, headers={'Authorization': 'Bearer ' + self.token}, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=False) as response:
            if response.status >= 300:
                raise ValueError('Home Assistant rejected the local request.')
            raw = await response.content.read(5_000_001)
            if len(raw) > 5_000_000:
                raise ValueError('Home Assistant response is too large.')
            return json.loads(raw)

    async def query(self, kind):
        self.counter += 1
        ident = self.counter
        future = asyncio.get_running_loop().create_future()
        self.pending[ident] = future
        try:
            await self.socket.send_json({'id': ident, 'type': kind})
            return await asyncio.wait_for(future, 8)
        finally:
            self.pending.pop(ident, None)

    async def registry(self):
        values = await asyncio.gather(*(self.query(kind) for kind in ['config/area_registry/list', 'config/device_registry/list', 'config/entity_registry/list']))
        return dict(zip(['areas', 'devices', 'entities'], values))

    async def listen(self, cloud, events):
        async with self.session.ws_connect(HA_SOCKET, heartbeat=20, max_msg_size=5_000_000) as ws:
            self.socket = ws
            if (await ws.receive_json()).get('type') != 'auth_required':
                raise ValueError('Invalid local greeting.')
            await ws.send_json({'type': 'auth', 'access_token': self.token})
            if (await ws.receive_json()).get('type') != 'auth_ok':
                raise ValueError('Local authentication failed.')
            await ws.send_json({'id': 1, 'type': 'subscribe_events', 'event_type': 'state_changed'})
            result = await ws.receive_json()
            if result.get('type') != 'result' or not result.get('success'):
                raise ValueError('Local event subscription failed.')
            await cloud.send_json({'type': 'ready'})
            async for frame in ws:
                if frame.type != aiohttp.WSMsgType.TEXT:
                    break
                message = json.loads(frame.data)
                if message.get('type') == 'result':
                    future = self.pending.get(message.get('id'))
                    if future and not future.done():
                        if message.get('success'):
                            future.set_result(message.get('result'))
                        else:
                            future.set_exception(ValueError('Local registry request failed.'))
                elif message.get('type') == 'event' and message.get('id') == 1:
                    event = message.get('event', {})
                    if event.get('event_type') == 'state_changed':
                        events.put_nowait(event['data'])
            raise ConnectionError('Home Assistant event connection closed.')


class Connector:
    def __init__(self, data_dir=Path('/data')):
        self.data_dir = data_dir
        self.executed = {}

    async def pair(self, session, local, code):
        config = await local.request('/api/config')
        async with session.post(ORIGIN + '/api/homecontrol/connector/pair', json={'code': code, 'name': config.get('location_name'), 'url': config.get('external_url') or config.get('internal_url') or 'http://homeassistant.local:8123'}, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=False) as response:
            if response.status != 200:
                raise ValueError('Pairing failed. Generate a fresh code in Planner → Smart Home.')
            token = (await response.json())['credential']
        state = {'credential': token, 'codeHash': hashlib.sha256(code.encode()).hexdigest()}
        temp = self.data_dir / 'connection.tmp'
        temp.touch(mode=0o600, exist_ok=True)
        temp.chmod(0o600)
        temp.write_text(json.dumps(state), encoding='utf-8')
        temp.replace(self.data_dir / 'connection.json')
        return state

    async def execute(self, local, cloud, message):
        ident = message.get('id')
        path, method = message.get('path'), message.get('method')
        if not isinstance(ident, str) or not re.fullmatch(r'[a-f0-9]{32}', ident):
            raise ValueError('Invalid command ID.')
        previous = self.executed.get(ident)
        if previous:
            await cloud.send_json(previous)
            return
        response = {'type': 'result', 'id': ident, 'ok': False}
        # Only service calls need deduplication; never retain large state/registry reads.
        if method == 'POST':
            self.executed[ident] = response
            if len(self.executed) > 256:
                self.executed.pop(next(iter(self.executed)))
        try:
            expires = message.get('expiresAt')
            if type(expires) not in (int, float) or not time.time() < expires <= time.time() + 15 or not isinstance(path, str) or not allowed(path, method):
                raise ValueError('Expired or unsupported request.')
            result = await local.registry() if path == '/pixora/registry' else await local.request(path, method, message.get('payload'))
            response['data'] = None if method == 'POST' else result
            response['ok'] = True
        except (ValueError, aiohttp.ClientError, asyncio.TimeoutError):
            LOG.warning('A local Home Assistant request failed; it will not be retried automatically.')
        await cloud.send_json(response)

    async def run_connection(self, session, local, credential):
        async with session.ws_connect(SOCKET, heartbeat=20, max_msg_size=5_000_000) as cloud:
            await cloud.send_json({'type': 'auth', 'credential': credential})
            reply = await cloud.receive_json(timeout=15)
            if reply.get('type') != 'auth_ok':
                raise ValueError('Connector authorization failed. Pair again in Planner.')
            events = asyncio.Queue(maxsize=256)
            requests = asyncio.Queue(maxsize=16)

            async def send_events():
                while True:
                    await cloud.send_json({'type': 'event', 'data': await events.get()})

            async def commands():
                while True:
                    await self.execute(local, cloud, await requests.get())

            async def heartbeat():
                while True:
                    await asyncio.sleep(20)
                    await cloud.send_json({'type': 'ping'})

            async def receive():
                async for frame in cloud:
                    if frame.type != aiohttp.WSMsgType.TEXT:
                        break
                    message = json.loads(frame.data)
                    if message.get('type') == 'request':
                        requests.put_nowait(message)
                    elif message.get('type') != 'pong':
                        raise ValueError('Invalid cloud message.')
                raise ConnectionError('Pixora connection closed.')

            tasks = [asyncio.create_task(coro) for coro in [local.listen(cloud, events), send_events(), commands(), heartbeat(), receive()]]
            LOG.info('Paired connector connected to Pixora.')
            try:
                done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    task.result()
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                for future in local.pending.values():
                    if not future.done():
                        future.cancel()
                local.pending.clear()

    async def run(self):
        options = json.loads((self.data_dir / 'options.json').read_text(encoding='utf-8'))
        code = str(options.get('pairing_code') or '').strip()
        if not code:
            raise ValueError('Enter the pairing code from Planner → Smart Home in this app’s Configuration tab.')
        path = self.data_dir / 'connection.json'
        state = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        delay = 1
        async with aiohttp.ClientSession() as session:
            local = LocalAPI(session, os.environ['SUPERVISOR_TOKEN'])
            while True:
                try:
                    if state.get('codeHash') != hashlib.sha256(code.encode()).hexdigest():
                        state = await self.pair(session, local, code)
                    await self.run_connection(session, local, state['credential'])
                except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError, ValueError, asyncio.QueueFull, KeyError):
                    LOG.warning('Connector offline. Reconnecting; if this continues, generate a new pairing code in Planner.')
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    try:
        asyncio.run(Connector().run())
    except (ValueError, OSError, KeyError):
        LOG.error('Setup is incomplete. Check the pairing code and Home Assistant app permissions.')
        raise SystemExit(1)
