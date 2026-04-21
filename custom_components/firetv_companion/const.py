"""Constants for Fire TV Companion."""

DOMAIN = "firetv_companion"

DEFAULT_PORT = 8787
DEFAULT_SCAN_INTERVAL = 5  # seconds

CONF_TOKEN = "token"

# Platforms loaded by this integration
PLATFORMS = ["media_player", "button", "sensor", "camera"]

# Packages hidden from the source (launchable apps) list
HIDDEN_PACKAGES = {
    "com.firetv.companion",
    "com.amazon.firetv.screensaver",
    "com.amazon.tv.notificationcenter",
}
