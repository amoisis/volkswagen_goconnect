"""Adds config flow for Volkswagen GoConnect."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    VolkswagenGoConnectApiClient,
    VolkswagenGoConnectApiClientAuthenticationError,
    VolkswagenGoConnectApiClientCommunicationError,
    VolkswagenGoConnectApiClientError,
)
from .const import (
    CONF_ABRP_ENABLED,
    CONF_IGNITION_POLLING_INTERVAL,
    CONF_POLLING_INTERVAL,
    DOMAIN,
    LOGGER,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from homeassistant.data_entry_flow import FlowResult


class VolkswagenGoConnectFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Volkswagen GoConnect."""

    VERSION = 1
    entry: config_entries.ConfigEntry | None = None

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._user_data: dict[str, Any] = {}

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
                await self.async_set_unique_id(user_input[CONF_EMAIL])
                self._abort_if_unique_id_configured()

                self._user_data = {
                    CONF_EMAIL: user_input[CONF_EMAIL],
                    "device_token": device_token,
                    CONF_POLLING_INTERVAL: user_input[CONF_POLLING_INTERVAL],
                    CONF_ABRP_ENABLED: user_input.get(CONF_ABRP_ENABLED, False),
                }

                if self._user_data[CONF_ABRP_ENABLED]:
                    return await self.async_step_abrp()

                return cast(
                    "FlowResult",
                    self.async_create_entry(
                        title=user_input[CONF_EMAIL],
                        data=self._user_data,
                    ),
                )

        return cast(
            "FlowResult",
            self.async_show_form(
                step_id="user",
                description_placeholders={
                    "docs_url": "https://github.com/amoisis/volkswagen_goconnect"
                },
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
                        vol.Optional(
                            CONF_ABRP_ENABLED,
                            default=(user_input or {}).get(CONF_ABRP_ENABLED, False),
                        ): selector.BooleanSelector(),
                    },
                ),
                errors=_errors,
            ),
        )

    async def async_step_abrp(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle ABRP settings step."""
        if user_input is not None:
            data = {
                **self._user_data,
                CONF_IGNITION_POLLING_INTERVAL: int(
                    user_input.get(CONF_IGNITION_POLLING_INTERVAL, 10)
                ),
            }
            return cast(
                "FlowResult",
                self.async_create_entry(
                    title=self._user_data[CONF_EMAIL],
                    data=data,
                ),
            )

        return cast(
            "FlowResult",
            self.async_show_form(
                step_id="abrp",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_IGNITION_POLLING_INTERVAL,
                            default=10,
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=1,
                                max=600,
                                step=1,
                                unit_of_measurement="s",
                                mode=selector.NumberSelectorMode.SLIDER,
                            )
                        ),
                    }
                ),
            ),
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:  # noqa: ARG002
        """Handle re-authentication with Volkswagen GoConnect."""
        entry_id = self.context.get("entry_id")
        if entry_id is None:
            return cast("FlowResult", self.async_abort(reason="unknown"))

        self.entry = self.hass.config_entries.async_get_entry(entry_id)
        if self.entry is None:
            return cast("FlowResult", self.async_abort(reason="unknown"))

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm re-authentication with Volkswagen GoConnect."""
        errors: dict[str, str] = {}

        entry = self.entry
        if entry is None:
            return cast("FlowResult", self.async_abort(reason="unknown"))

        if user_input:
            email = entry.data[CONF_EMAIL]
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
                new_data = entry.data.copy()
                new_data["device_token"] = device_token
                if CONF_PASSWORD in new_data:
                    del new_data[CONF_PASSWORD]

                self.hass.config_entries.async_update_entry(
                    entry,
                    data=new_data,
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return cast("FlowResult", self.async_abort(reason="reauth_successful"))

        return cast(
            "FlowResult",
            self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_PASSWORD): selector.TextSelector(
                            selector.TextSelectorConfig(
                                type=selector.TextSelectorType.PASSWORD
                            )
                        ),
                    }
                ),
                description_placeholders={"email": entry.data[CONF_EMAIL]},
                errors=errors,
            ),
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
            message = "Failed to obtain device token"
            raise VolkswagenGoConnectApiClientAuthenticationError(message)

        return device_token


class VolkswagenGoConnectOptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for Volkswagen GoConnect."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow handler for Volkswagen GoConnect."""
        self._config_entry = config_entry
        self._options: dict[str, Any] = {}

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step of the options flow."""
        if user_input is not None:
            self._options = dict(user_input)
            if self._options.get(CONF_ABRP_ENABLED):
                return await self.async_step_abrp()
            return cast(
                "FlowResult",
                self.async_create_entry(title="", data=self._options),
            )

        current_polling = self._config_entry.options.get(
            CONF_POLLING_INTERVAL,
            self._config_entry.data.get(CONF_POLLING_INTERVAL, 60),
        )
        current_abrp_enabled = self._config_entry.options.get(
            CONF_ABRP_ENABLED,
            self._config_entry.data.get(CONF_ABRP_ENABLED, False),
        )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_POLLING_INTERVAL,
                    default=current_polling,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=10,
                        max=3600,
                        step=10,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_ABRP_ENABLED,
                    default=current_abrp_enabled,
                ): selector.BooleanSelector(),
            }
        )

        return cast(
            "FlowResult",
            self.async_show_form(
                step_id="init",
                data_schema=data_schema,
            ),
        )

    async def async_step_abrp(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle ABRP settings step in options flow."""
        if user_input is not None:
            combined = {
                **self._options,
                CONF_IGNITION_POLLING_INTERVAL: int(
                    user_input.get(CONF_IGNITION_POLLING_INTERVAL, 10)
                ),
            }
            return cast(
                "FlowResult",
                self.async_create_entry(title="", data=combined),
            )

        current_ignition = self._config_entry.options.get(
            CONF_IGNITION_POLLING_INTERVAL,
            self._config_entry.data.get(CONF_IGNITION_POLLING_INTERVAL, 10),
        )

        return cast(
            "FlowResult",
            self.async_show_form(
                step_id="abrp",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_IGNITION_POLLING_INTERVAL,
                            default=current_ignition,
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=1,
                                max=600,
                                step=1,
                                unit_of_measurement="s",
                                mode=selector.NumberSelectorMode.SLIDER,
                            )
                        ),
                    }
                ),
            ),
        )
