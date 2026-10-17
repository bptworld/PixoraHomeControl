**This legacy installation is now named Pixora Home Control - Old. The name change preserves its existing app ID, configuration and data.**

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

---

> [!WARNING]
> **DEPRECATED — Home Assistant app moved to PixoraHQforHA.**
>
> Use **[PixoraHQforHA](https://github.com/bptworld/PixoraHQforHA)** for new installations and future HA app releases.
> This app's new directory is **[pixora_home_control](https://github.com/bptworld/PixoraHQforHA/tree/main/pixora_home_control)**.
>
> Existing installs keep working: this directory and its code have been retained.
> No automatic migration occurs. Back up settings/data and stop the old app before
> starting a replacement from the new repository. Keep the old install until the
> replacement is verified. Other platform components in this repository are unaffected.

# Pixora Home Control

Connects Home Assistant to Planner, Home Control, and Flows using a secure outbound connection. No public Home Assistant address, Nabu Casa subscription, long-lived token, or port forwarding is needed.

1. Add `https://github.com/bptworld/PixoraHQforHA` to your Home Assistant app/add-on repositories.
2. Install **Pixora Home Control**.
3. In **Planner → Smart Home → Home Assistant**, choose **Pair Home Control app**.
4. Copy the pairing code into this app’s **Configuration → pairing_code**, save, and start the app. Codes expire after ten minutes and work once.
5. Enable **Start on boot** and **Watchdog**. Planner will show the app as online.

The app uses Home Assistant’s internal API permission, receives local state events, and executes commands through the standard local service API. The Flow engine remains on Pixora’s server. Internet access is required; old commands are not queued for later execution. Uncertain command results are never retried automatically.

Disconnecting Home Assistant in Planner revokes this app’s credential. To reconnect, generate a new pairing code, replace `pairing_code`, and restart the app. Previously chosen device tiles and Flows remain in Pixora.

Requires Home Assistant OS with the app/add-on store. A standalone Container installation is not supported by this package.

## Local installation before release

Extract the supplied ZIP so its `pixora_home_control` folder is at `/addons/pixora_home_control` on Home Assistant. Reload the app/add-on store, then install **Pixora Home Control** from **Local apps**. Leave the app stopped until the matching Pixora server release is deployed; pairing is not available on the previous server release. Then follow steps 3–5 above.

## Server deployment

The Pixora connector socket and existing Flow engine run in the same server process. Deploy one Render instance with `WEB_CONCURRENCY=1` (set in this release’s Render blueprint). Multiple workers or replicas require a shared connection broker before enabling this transport. Pairing credentials use the existing encrypted Home Assistant connection storage. No credentials are placed in URLs or logs.
