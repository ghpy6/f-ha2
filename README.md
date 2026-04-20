# Fire TV Companion — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Talks to the **Fire TV Companion APK** over a local HTTP API (port 8787).
No ADB, no cloud, no shell commands — just a bearer token over your LAN.

**Companion APK repo:** https://github.com/detalhe/firetv-companion-apk

---

## Why use this instead of an ADB-based integration?

| Problem with ADB | Fix with Companion APK |
|---|---|
| 2–5 s lag on every command | Instant — HTTP is stateless |
| Volume ends up on Samsung TV (HDMI-CEC overlay) | Real Fire TV media volume |
| Spotify / YouTube play-pause silently fails | Works (uses MediaSession) |
| State stuck on "idle" | Accurate — reads foreground app + playback state |
| Raw `com.netflix.ninja` app names | Real names & icons |
| ADB pairing dies, needs re-auth | Token-based, never expires |

---

## Install via HACS (recommended)

1. **Add as custom repository**:
   HACS → Integrations → ⋮ → Custom repositories
   - URL: `https://github.com/detalhe/firetv-companion-ha`
   - Category: `Integration`
2. Click **Install** on "Fire TV Companion".
3. **Restart Home Assistant.**

## Install manually

Copy `custom_components/firetv_companion/` into your HA `config/custom_components/`
folder and restart HA.

---

## Configure

Before adding the integration, install and open the **Fire TV Companion APK** on
your Fire TV and grant its 3 permissions via ADB (see its README).

Then in HA:

**Settings → Devices & Services → Add Integration → "Fire TV Companion"**

Fill in:

| Field | Value |
|---|---|
| Host / IP | Your Fire TV's LAN IP (shown in the Companion app) |
| Port | `8787` |
| API Token | Token from the Companion app, or run on your PC: `adb logcat -d -s FireTVCompanion:I *:S` |
| Name | Friendly name, e.g. "Living Room Fire TV" |

---

## What you get

One device with:

| Entity | Purpose |
|---|---|
| `media_player.<name>` | State, real volume, play/pause/next/previous, app launcher (Select Source) |
| `button.<name>_home` | D-pad Home |
| `button.<name>_back` | D-pad Back |
| `button.<name>_recents` | Recents list |
| `button.<name>_notifications` | Open notification shade |
| `button.<name>_power_menu` | Power menu |
| `sensor.<name>_current_app` | Current foreground app name |
| `sensor.<name>_media_title` | Media title (Spotify / YouTube / Netflix etc.) |
| `sensor.<name>_media_artist` | Media artist |

Controls work in every app that publishes a `MediaSession`: Spotify, YouTube,
Netflix, Prime Video, Plex, Kodi, Disney+, etc.

---

## Troubleshooting

**"Cannot connect"** — Fire TV IP wrong, or APK service not running.
Open the Companion app on the Fire TV once, confirm the URL shown matches
what you entered.

**"Invalid token"** — Copy the token again from the app or from
`adb logcat -d -s FireTVCompanion:I *:S`. Tokens rotate when the APK is
reinstalled.

**Buttons press OK but nothing happens** — Accessibility service not granted:
```
adb shell settings put secure enabled_accessibility_services com.firetv.companion/com.firetv.companion.services.FireTVAccessibilityService
adb shell settings put secure accessibility_enabled 1
```

**Media controls do nothing** — Notification Access not granted:
```
adb shell cmd notification allow_listener com.firetv.companion/com.firetv.companion.services.MediaNotificationListener
```

**`current_app` sensor stays empty** — Usage Access not granted:
```
adb shell appops set com.firetv.companion GET_USAGE_STATS allow
```

---

## License

MIT
