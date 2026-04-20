"""Sensors — current app, media title/artist."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FireTVCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FireTVCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        CurrentAppSensor(coordinator, entry),
        MediaTitleSensor(coordinator, entry),
        MediaArtistSensor(coordinator, entry),
    ])


class _BaseSensor(CoordinatorEntity[FireTVCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: FireTVCoordinator, entry: ConfigEntry, key: str, name: str, icon: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        device_name = entry.data.get(CONF_NAME, "Fire TV")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=device_name,
            manufacturer="Amazon",
            model="Fire TV (Companion APK)",
        )

    @property
    def _state(self) -> dict[str, Any]:
        return self.coordinator.data or {}


class CurrentAppSensor(_BaseSensor):
    def __init__(self, coordinator: FireTVCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "current_app", "Current app", "mdi:apps")

    @property
    def native_value(self) -> str | None:
        pkg = self._state.get("current_app")
        if not pkg:
            return None
        for app in self.coordinator.apps:
            if app.get("package") == pkg:
                return app.get("name") or pkg
        return pkg

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"package": self._state.get("current_app")}


class MediaTitleSensor(_BaseSensor):
    def __init__(self, coordinator: FireTVCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "media_title", "Media title", "mdi:music")

    @property
    def native_value(self) -> str | None:
        return (self._state.get("media") or {}).get("title")


class MediaArtistSensor(_BaseSensor):
    def __init__(self, coordinator: FireTVCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "media_artist", "Media artist", "mdi:account-music")

    @property
    def native_value(self) -> str | None:
        return (self._state.get("media") or {}).get("artist")
