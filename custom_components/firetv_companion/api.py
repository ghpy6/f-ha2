"""HTTP client for the Fire TV Companion APK."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class FireTVApiError(Exception):
    """Generic API error."""


class FireTVAuthError(FireTVApiError):
    """Token was rejected."""


class FireTVClient:
    """Tiny async wrapper around every APK endpoint."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        token: str,
        timeout: float = 4.0,
    ) -> None:
        self._session = session
        self._base = f"http://{host}:{port}"
        self._token = token
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._headers = {"Authorization": f"Bearer {token}"}

    # --- low-level ---

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        parse_json: bool = True,
    ) -> Any:
        url = f"{self._base}{path}"
        try:
            async with self._session.request(
                method,
                url,
                json=payload,
                headers=self._headers,
                timeout=self._timeout,
            ) as resp:
                if resp.status == 401:
                    raise FireTVAuthError("Invalid token")
                if resp.status >= 400:
                    text = await resp.text()
                    raise FireTVApiError(f"{resp.status}: {text[:200]}")
                if not parse_json:
                    return await resp.read()
                return await resp.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise FireTVApiError(f"timeout contacting {url}") from err
        except aiohttp.ClientError as err:
            raise FireTVApiError(f"network error: {err}") from err

    # --- health / state ---

    async def ping(self) -> dict[str, Any]:
        return await self._request("GET", "/ping")

    async def state(self) -> dict[str, Any]:
        return await self._request("GET", "/state")

    async def device_info(self) -> dict[str, Any]:
        return await self._request("GET", "/device/info")

    # --- volume ---

    async def volume_get(self) -> dict[str, Any]:
        return await self._request("GET", "/volume")

    async def volume_set(self, level: int) -> dict[str, Any]:
        return await self._request("POST", "/volume/set", {"level": level})

    async def volume_up(self) -> None:
        await self._request("POST", "/volume/up")

    async def volume_down(self) -> None:
        await self._request("POST", "/volume/down")

    async def volume_mute(self, mute: bool | None = None) -> dict[str, Any]:
        payload = {"mute": mute} if mute is not None else {}
        return await self._request("POST", "/volume/mute", payload)

    # --- apps ---

    async def apps(self) -> list[dict[str, Any]]:
        data = await self._request("GET", "/apps")
        return data.get("apps", []) if isinstance(data, dict) else []

    async def app_launch(self, package: str) -> dict[str, Any]:
        return await self._request("POST", "/app/launch", {"package": package})

    async def app_stop(self, package: str) -> dict[str, Any]:
        return await self._request("POST", "/app/stop", {"package": package})

    async def app_icon_png(self, package: str) -> bytes:
        return await self._request("GET", f"/app/icon/{package}", parse_json=False)

    # --- media ---

    async def media_play(self) -> None:
        await self._request("POST", "/media/play")

    async def media_pause(self) -> None:
        await self._request("POST", "/media/pause")

    async def media_play_pause(self) -> None:
        await self._request("POST", "/media/play_pause")

    async def media_stop(self) -> None:
        await self._request("POST", "/media/stop")

    async def media_next(self) -> None:
        await self._request("POST", "/media/next")

    async def media_previous(self) -> None:
        await self._request("POST", "/media/previous")

    async def media_info(self) -> dict[str, Any]:
        return await self._request("GET", "/media/info")

    # --- navigation (Accessibility) ---

    async def nav(self, action: str) -> None:
        """action in: home / back / recents / notifications / power_dialog"""
        await self._request("POST", f"/nav/{action}")
