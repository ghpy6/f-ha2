"""Camera entity — on-demand screenshot of the Fire TV screen."""

from __future__ import annotations

import logging
import time

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import FireTVApiError
from .const import DOMAIN
from .coordinator import FireTVCoordinator

_LOGGER = logging.getLogger(__name__)

# Don't hammer the Fire TV — reuse the last frame for this many seconds.
MIN_INTERVAL = 2.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FireTVCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FireTVScreenshotCamera(coordinator, entry)])


class FireTVScreenshotCamera(Camera):
    _attr_has_entity_name = True
    _attr_name = "Screen"
    _attr_icon = "mdi:television"

    def __init__(self, coordinator: FireTVCoordinator, entry: ConfigEntry) -> None:
        super().__init__()
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_screenshot"
        name = entry.data.get(CONF_NAME, "Fire TV")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=name,
            manufacturer="Amazon",
            model="Fire TV (Companion APK)",
        )
        self._last_image: bytes | None = None
        self._last_fetch: float = 0.0

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        now = time.monotonic()
        if self._last_image is not None and (now - self._last_fetch) < MIN_INTERVAL:
            return self._last_image
        try:
            png = await self._coordinator.client.screenshot_png()
        except FireTVApiError as err:
            _LOGGER.debug("screenshot failed: %s", err)
            return self._last_image
        self._last_image = png
        self._last_fetch = now
        return png