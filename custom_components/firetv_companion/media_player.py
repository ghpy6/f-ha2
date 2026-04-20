"""Media player entity — mirrors Fire TV state, exposes controls."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import FireTVApiError
from .const import DOMAIN, HIDDEN_PACKAGES
from .coordinator import FireTVCoordinator

_LOGGER = logging.getLogger(__name__)

SUPPORTED = (
    MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.SELECT_SOURCE
)

if hasattr(MediaPlayerEntityFeature, "PLAY_PAUSE"):
    SUPPORTED |= MediaPlayerEntityFeature.PLAY_PAUSE

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FireTVCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FireTVMediaPlayer(coordinator, entry)])


class FireTVMediaPlayer(CoordinatorEntity[FireTVCoordinator], MediaPlayerEntity):
    _attr_has_entity_name = True
    _attr_name = None  # use device name
    _attr_supported_features = SUPPORTED

    def __init__(self, coordinator: FireTVCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_media_player"
        name = entry.data.get(CONF_NAME, "Fire TV")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=name,
            manufacturer="Amazon",
            model="Fire TV (Companion APK)",
        )

    # --- derived state ---

    @property
    def _state(self) -> dict[str, Any]:
        return self.coordinator.data or {}

    @property
    def state(self) -> MediaPlayerState | None:
        data = self._state
        if not data:
            return MediaPlayerState.OFF
        if not data.get("screen_on", True):
            return MediaPlayerState.OFF
        media = data.get("media") or {}
        if media.get("available"):
            s = media.get("state")
            if s == "playing":
                return MediaPlayerState.PLAYING
            if s == "paused":
                return MediaPlayerState.PAUSED
            if s in ("buffering", "connecting"):
                return MediaPlayerState.BUFFERING
            if s == "stopped":
                return MediaPlayerState.IDLE
        return MediaPlayerState.ON

    @property
    def volume_level(self) -> float | None:
        data = self._state
        vmax = data.get("volume_max") or 0
        if not vmax:
            return None
        return float(data.get("volume", 0)) / float(vmax)

    @property
    def is_volume_muted(self) -> bool | None:
        return bool(self._state.get("muted"))

    @property
    def source(self) -> str | None:
        """Return current foreground app name (if found in cache)."""
        pkg = self._state.get("current_app")
        if not pkg:
            return None
        for app in self.coordinator.apps:
            if app.get("package") == pkg:
                return app.get("name") or pkg
        return pkg

    @property
    def source_list(self) -> list[str]:
        return [
            a.get("name") or a.get("package")
            for a in self.coordinator.apps
            if a.get("launchable") and a.get("package") not in HIDDEN_PACKAGES
        ]

    @property
    def media_title(self) -> str | None:
        media = self._state.get("media") or {}
        return media.get("title")

    @property
    def media_artist(self) -> str | None:
        media = self._state.get("media") or {}
        return media.get("artist")

    @property
    def media_album_name(self) -> str | None:
        media = self._state.get("media") or {}
        return media.get("album")

    @property
    def app_id(self) -> str | None:
        return self._state.get("current_app")

    @property
    def app_name(self) -> str | None:
        return self.source

    # --- commands ---

    async def async_set_volume_level(self, volume: float) -> None:
        vmax = self._state.get("volume_max") or 15
        level = max(0, min(vmax, round(volume * vmax)))
        await self._safe(self.coordinator.client.volume_set(level))

    async def async_volume_up(self) -> None:
        await self._safe(self.coordinator.client.volume_up())

    async def async_volume_down(self) -> None:
        await self._safe(self.coordinator.client.volume_down())

    async def async_mute_volume(self, mute: bool) -> None:
        await self._safe(self.coordinator.client.volume_mute(mute))

    async def async_media_play(self) -> None:
        await self._safe(self.coordinator.client.media_play())

    async def async_media_pause(self) -> None:
        await self._safe(self.coordinator.client.media_pause())

    async def async_media_play_pause(self) -> None:
        await self._safe(self.coordinator.client.media_play_pause())

    async def async_media_stop(self) -> None:
        await self._safe(self.coordinator.client.media_stop())

    async def async_media_next_track(self) -> None:
        await self._safe(self.coordinator.client.media_next())

    async def async_media_previous_track(self) -> None:
        await self._safe(self.coordinator.client.media_previous())

    async def async_select_source(self, source: str) -> None:
        pkg = next(
            (a.get("package") for a in self.coordinator.apps
             if (a.get("name") or a.get("package")) == source),
            None,
        )
        if not pkg:
            _LOGGER.warning("Unknown source: %s", source)
            return
        await self._safe(self.coordinator.client.app_launch(pkg))
        await self.coordinator.async_request_refresh()

    async def _safe(self, coro) -> None:
        try:
            await coro
        except FireTVApiError as err:
            _LOGGER.warning("command failed: %s", err)
        else:
            await self.coordinator.async_request_refresh()
