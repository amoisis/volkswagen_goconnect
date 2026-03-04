"""Custom integration to integrate volkswagen_goconnect with Home Assistant."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_integration

from .api import VolkswagenGoConnectApiClient
from .const import CONF_IGNITION_POLLING_INTERVAL, CONF_POLLING_INTERVAL, DOMAIN, LOGGER
from .coordinator import VolkswagenGoConnectDataUpdateCoordinator
from .data import VolkswagenGoConnectData
from .service_actions.abrp_send import async_abrp_send_service

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, ServiceCall

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, _config: dict[str, Any]) -> bool:
    """Set up the volkswagen_goconnect integration and register services."""

    async def handle_abrp_send(call: ServiceCall) -> None:
        api_key = call.data.get("api_key")
        token = call.data.get("token")
        service_data = call.data.get("service_data")
        if not api_key or not token:
            LOGGER.error("ABRP api_key and token are required for abrp_send service")
            return
        await async_abrp_send_service(hass, api_key, token, service_data)

    if not hass.services.has_service(DOMAIN, "abrp_send"):
        hass.services.async_register(
            DOMAIN,
            "abrp_send",
            handle_abrp_send,
            schema=vol.Schema(
                {
                    vol.Required("api_key"): str,
                    vol.Required("token"): str,
                    vol.Optional("service_data"): dict,
                }
            ),
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    integration = await async_get_integration(hass, DOMAIN)
    client = VolkswagenGoConnectApiClient(
        session=async_get_clientsession(hass),
        email=entry.data.get(CONF_EMAIL),
        password=entry.data.get(CONF_PASSWORD),
        device_token=entry.data.get("device_token"),
    )

    polling_interval = entry.options.get(
        CONF_POLLING_INTERVAL,
        entry.data.get(CONF_POLLING_INTERVAL, 60),
    )
    ignition_interval = entry.options.get(
        CONF_IGNITION_POLLING_INTERVAL,
        entry.data.get(CONF_IGNITION_POLLING_INTERVAL, 10),
    )

    coordinator = VolkswagenGoConnectDataUpdateCoordinator(
        hass=hass,
        client=client,
        update_interval=timedelta(seconds=polling_interval),
    )
    ignition_coordinator = VolkswagenGoConnectDataUpdateCoordinator(
        hass=hass,
        client=client,
        update_interval=timedelta(seconds=ignition_interval),
    )

    await coordinator.async_config_entry_first_refresh()
    if ignition_coordinator is not coordinator:
        await ignition_coordinator.async_config_entry_first_refresh()

    entry.runtime_data = VolkswagenGoConnectData(
        client=client,
        coordinator=coordinator,
        ignition_coordinator=ignition_coordinator,
        integration=integration,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
