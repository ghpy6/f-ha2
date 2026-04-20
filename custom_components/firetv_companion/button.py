"""Navigation buttons — Home / Back / Recents / Notifications / Power."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import FireTVApiError
from .const import DOMAIN
from .coordinator import FireTVCoordinator

NAV_BUTTONS = [
    ("home", "Home", "mdi:home"),
    ("back", "Back", "mdi:arrow-left"),
    ("recents", "Recents", "mdi:format-list-bulleted"),
    ("notifications", "Notifications", "mdi:bell"),
    ("power_dialog", "Power menu", "mdi:power"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FireTVCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        FireTVNavButton(coordinator, entry, action, label, icon)
        for action, label, icon in NAV_BUTTONS
    )


class FireTVNavButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FireTVCoordinator,
        entry: ConfigEntry,
        action: str,
        label: str,
        icon: str,
    ) -> None:
        self._coordinator = coordinator
        self._action = action
        self._attr_name = label
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_nav_{action}"
        name = entry.data.get(CONF_NAME, "Fire TV")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=name,
            manufacturer="Amazon",
            model="Fire TV (Companion APK)",
        )

    async def async_press(self) -> None:
        try:
            await self._coordinator.client.nav(self._action)
        except FireTVApiError:
            pass
