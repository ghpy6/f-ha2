"""Config flow — ask host/port/token, validate via /ping + /state."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import FireTVApiError, FireTVAuthError, FireTVClient
from .const import CONF_TOKEN, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN


class FireTVCompanionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = int(user_input.get(CONF_PORT, DEFAULT_PORT))
            token = user_input[CONF_TOKEN].strip()
            name = user_input.get(CONF_NAME, "Fire TV").strip() or "Fire TV"

            session = async_get_clientsession(self.hass)
            client = FireTVClient(session, host, port, token)
            try:
                await client.ping()
                await client.state()  # verifies token
            except FireTVAuthError:
                errors["base"] = "invalid_token"
            except FireTVApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_TOKEN: token,
                        CONF_NAME: name,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_TOKEN): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                vol.Optional(CONF_NAME, default="Fire TV"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)),
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return FireTVCompanionOptionsFlow(config_entry)


class FireTVCompanionOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self._config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "scan_interval",
                    default=opts.get("scan_interval", DEFAULT_SCAN_INTERVAL),
                ): NumberSelector(NumberSelectorConfig(
                    min=1, max=60, step=1,
                    unit_of_measurement="seconds",
                    mode=NumberSelectorMode.BOX,
                )),
            }),
        )
