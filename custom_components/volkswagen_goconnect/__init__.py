
from __future__ import annotations
from homeassistant.core import HomeAssistant
from homeassistant.core import ServiceCall
from .service_actions.abrp_send import async_abrp_send_service
from .const import CONF_ABRP_API_KEY
import voluptuous as vol

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the volkswagen_goconnect integration (register services)."""

    async def handle_abrp_upload(call: ServiceCall) -> None:
        token = call.data.get("api_key")
        if not token:
            # Try to get the token from the first config entry
            entries = hass.config_entries.async_entries(DOMAIN)
            if entries:
                entry = entries[0]
                token = entry.options.get(CONF_ABRP_API_KEY) or entry.data.get(CONF_ABRP_API_KEY)
        if not token:
            from custom_components.volkswagen_goconnect.const import LOGGER
            LOGGER.error("ABRP API key not provided in service call or config entry.")
            return
        await async_abrp_send_service(hass, token)

    hass.services.async_register(
        DOMAIN,
        "abrp_upload",
        handle_abrp_upload,
        schema=vol.Schema({vol.Optional("api_key"): str}),
    )
    return True

"""
Custom integration to integrate volkswagen_goconnect with Home Assistant.

For more details about this integration, please refer to
https://github.com/amoisis/volkswagen_goconnect
"""

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_integration

from .api import VolkswagenGoConnectApiClient
from .const import CONF_IGNITION_POLLING_INTERVAL, CONF_POLLING_INTERVAL, DOMAIN
from .coordinator import VolkswagenGoConnectDataUpdateCoordinator
from .data import VolkswagenGoConnectData

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
]


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
