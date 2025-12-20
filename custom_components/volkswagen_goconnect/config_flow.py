"""Adds config flow for Volkswagen GoConnect."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from slugify import slugify

from .api import (
    VolkswagenGoConnectApiClient,
    VolkswagenGoConnectApiClientAuthenticationError,
    VolkswagenGoConnectApiClientCommunicationError,
    VolkswagenGoConnectApiClientError,
)
from .const import CONF_POLLING_INTERVAL, DOMAIN, LOGGER


class VolkswagenGoConnectFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Volkswagen GoConnect."""

    VERSION = 1
    entry: config_entries.ConfigEntry | None = None

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return VolkswagenGoConnectOptionsFlowHandler(config_entry)

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                device_token = await self._authenticate_and_register(
                    email=user_input[CONF_EMAIL],
                    password=user_input[CONF_PASSWORD],
                )
            except VolkswagenGoConnectApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except VolkswagenGoConnectApiClientCommunicationError:
                LOGGER.exception("Connection error")
                _errors["base"] = "connection"
            except VolkswagenGoConnectApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(slugify(user_input[CONF_EMAIL]))
                self._abort_if_unique_id_configured()

                data = {
                    CONF_EMAIL: user_input[CONF_EMAIL],
                    "device_token": device_token,
                    CONF_POLLING_INTERVAL: user_input[CONF_POLLING_INTERVAL],
                }

                return self.async_create_entry(
                    title=user_input[CONF_EMAIL],
                    data=data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EMAIL,
                        default=(user_input or {}).get(CONF_EMAIL, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.EMAIL,
                            autocomplete="email",
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                    vol.Required(
                        CONF_POLLING_INTERVAL,
                        default=60,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=10,
                            max=3600,
                            step=10,
                            unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                },
            ),
            errors=_errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """Handle re-authentication with Volkswagen GoConnect."""
        self.entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm re-authentication with Volkswagen GoConnect."""
        errors: dict[str, str] = {}

        if user_input:
            email = self.entry.data[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]
            try:
                device_token = await self._authenticate_and_register(email, password)
            except VolkswagenGoConnectApiClientAuthenticationError:
                errors["base"] = "auth"
            except VolkswagenGoConnectApiClientCommunicationError:
                errors["base"] = "connection"
            except VolkswagenGoConnectApiClientError:
                errors["base"] = "unknown"
            else:
                new_data = self.entry.data.copy()
                new_data["device_token"] = device_token
                if CONF_PASSWORD in new_data:
                    del new_data[CONF_PASSWORD]

                self.hass.config_entries.async_update_entry(
                    self.entry,
                    data=new_data,
                )
                await self.hass.config_entries.async_reload(self.entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    )
                }
            ),
            description_placeholders={"email": self.entry.data[CONF_EMAIL]},
            errors=errors,
        )

    async def _authenticate_and_register(self, email: str, password: str) -> str:
        """Validate connection and register device."""
        client = VolkswagenGoConnectApiClient(
            session=async_create_clientsession(self.hass),
            email=email,
            password=password,
        )
        await client.login()  # Login with email/pass

        # Register device to get token
        result = await client.register_device()
        device_token = result.get("deviceToken")

        if not device_token:
            raise VolkswagenGoConnectApiClientAuthenticationError(
                "Failed to obtain device token"
            )

        return device_token


class VolkswagenGoConnectOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for VolkswagenGoConnect."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLLING_INTERVAL,
                        default=self._config_entry.options.get(
                            CONF_POLLING_INTERVAL,
                            self._config_entry.data.get(CONF_POLLING_INTERVAL, 60),
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=10,
                            max=3600,
                            step=10,
                            unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                }
            ),
        )
