# Fire TV Companion (HTTP) — Home Assistant Integration

Talks to the **Fire TV Companion APK** over a local HTTP API (port 8787).
No ADB, no cloud, no shell commands — just a bearer token over your LAN.

Pairs with: https://github.com/detalhe/firetv-companion-apk

---

## Install

1. Copy the `firetv_companion` folder into your HA `config/custom_components/`
   directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration** and search for
   **Fire TV Companion**.
4. Enter:
   - **Host / IP** — your Fire TV's LAN IP (shown in the Companion app)
   - **Port** — `8787` (default)
   - **API Token** — copy from the Companion app, or run on your PC:
     `adb logcat -d -s FireTVCompanion:I *:S`
   - **Name** — friendly name (e.g. "Living Room Fire TV")

---

## What you get

One device with:

| Entity type | Purpose |
|---|---|
| `media_player` | State, real Fire TV volume, play/pause/next/previous, app launcher |
| `button` × 5 | Home / Back / Recents / Notifications / Power menu |
| `sensor` | Current app, media title, media artist |

Controls work in all apps that publish a `MediaSession` — Spotify, YouTube,
Netflix, Prime Video, Plex, Kodi, etc.

---

## Why this is better than the ADB-based integration

- **Instant commands** — no TCP handshake, no 2–5 s lag.
- **Real Fire TV volume** — no more Samsung TV overlay hijacking.
- **Working media controls** — Spotify/YouTube play/pause/next actually work.
- **Accurate state** — "idle" truly means idle; "playing" means playing.
- **Real app names & icons** — no more raw package names.
- **Zero cloud** — everything is LAN-local, token-protected.

---

## Troubleshooting

**"Cannot connect"**
— Fire TV IP wrong, or APK service not running. Open the Companion app on the
  Fire TV once to wake it up.

**"Invalid token"**
— Copy the token again from the Companion app (or from logcat). Tokens are
  rotated when the APK is reinstalled.

**Buttons do nothing**
— Accessibility service not granted. Run:
  ```
  adb shell settings put secure enabled_accessibility_services com.firetv.companion/com.firetv.companion.services.FireTVAccessibilityService
  adb shell settings put secure accessibility_enabled 1
  ```

**Media controls do nothing**
— Notification Access not granted. Run:
  ```
  adb shell cmd notification allow_listener com.firetv.companion/com.firetv.companion.services.MediaNotificationListener
  ```

**Current app always empty**
— Usage Access not granted. Run:
  ```
  adb shell appops set com.firetv.companion GET_USAGE_STATS allow
  ```
