"""State coordinator — polls /state every N seconds, caches apps list."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FireTVApiError, FireTVClient

_LOGGER = logging.getLogger(__name__)

APPS_REFRESH_EVERY = 12  # refresh apps list every N polls (~60s at 5s interval)


class FireTVCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls /state, caches /apps occasionally."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: FireTVClient,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="firetv_companion",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.apps: list[dict[str, Any]] = []
        self._tick = 0

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            state = await self.client.state()
        except FireTVApiError as err:
            raise UpdateFailed(str(err)) from err

        # Refresh app list occasionally (cheap to cache, expensive to fetch)
        if self._tick % APPS_REFRESH_EVERY == 0 or not self.apps:
            try:
                self.apps = await self.client.apps()
            except FireTVApiError as err:
                _LOGGER.debug("apps refresh failed: %s", err)
        self._tick += 1

        return state
