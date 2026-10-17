# 1.0.10

- Rename this legacy app to **Pixora Home Control - Old** so it is easy to distinguish from the current PixoraHQforHA app.
- Keep the existing app slug, configuration and saved data unchanged.

# 1.0.9

**IMPORTANT — This app has moved to PixoraHQ for Home Assistant.**

**New app repository: `https://github.com/bptworld/PixoraHQforHA`**

This update adds this notice; your existing installation and settings keep working. It does **not** move or uninstall your app. For the current app and future releases:

1. Back up this app and keep the old installation until the replacement is verified.
2. Add the new repository in **Settings → Apps → App store → ⋮ → Repositories**.
3. Turn off **Start on boot** and **Watchdog** for the old app, then **Stop** it before starting its replacement.
4. Install the app with the same name from **PixoraHQ for Home Assistant**, follow the pairing steps below, and verify it is working. Enable Start on boot and Watchdog for the new app.

**Keep the old app stopped. Adding the repository does not transfer app data, configuration or credentials automatically.**

Open **[planner.pixorahq.com](https://planner.pixorahq.com/)** to pair Home Control. Your Home Control layouts and Flows remain in your Pixora account.

Brought to you by [PixoraHQ.com](https://pixorahq.com/).

- Publish an app update so existing installations receive the bold Information-page notice and setup instructions. No automatic migration or device actions.

# 1.0.8

- Send each Home Assistant event once using one event-bus subscription, preserving state triggers, Lutron buttons, custom events and notification replies.
- Uses the optimized stream with Pixora cloud 1.42.366 or newer; automatically retains the compatible stream on older servers.

# 1.0.7

- Forward Home Assistant events for Flows Event nodes and safely correlated notification action responses.
- Preserve events received during subscription setup and retain reconnect recovery.
- Requires the matching Pixora cloud update before updating this app.

# 1.0.6

- Recover automatically when Pixora or Home Assistant closes a socket during authentication or event subscription, instead of exiting with WSMessageTypeError.
- Report which handshake connection closed and its close code without logging credentials or server payloads.

# 1.0.5

- Discover Lutron button controllers and forward their live button events to Flows.

# 1.0.4

- Reset reconnect backoff after sessions lasting at least 60 seconds.
- Log which connection closed, its close code, and the reconnect delay without exposing credentials.

# 1.0.3

- Read complete local HTTP responses before decoding JSON, preserving the response size limit. Fixes fragmented device-state and service catalog reads.

# 1.0.2

- Report specific local request failures, HTTP status, and request path in logs without exposing credentials or response bodies.

# 1.0.1

- Publish the app in its own public installation repository.

# 1.0.0

- Pair with Planner and connect outbound to Pixora.
- Send local Home Assistant events to the existing Flow engine.
- Execute shared Planner, Home Control, and Flow requests locally.
- Reconnect automatically; reject expired commands and duplicate IDs.
