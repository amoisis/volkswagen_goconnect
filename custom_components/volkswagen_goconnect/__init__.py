"""
Custom integration to integrate volkswagen_goconnect with Home Assistant.

For more details about this integration, please refer to
https://github.com/amoisis/volkswagen_goconnect
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_integration

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .api import VolkswagenGoConnectApiClient
from .const import CONF_POLLING_INTERVAL, DOMAIN
from .coordinator import VolkswagenGoConnectDataUpdateCoordinator
from .data import VolkswagenGoConnectData

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
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

    coordinator = VolkswagenGoConnectDataUpdateCoordinator(
        hass=hass,
        client=client,
        update_interval=timedelta(
            seconds=entry.options.get(
                CONF_POLLING_INTERVAL, entry.data.get(CONF_POLLING_INTERVAL, 60)
            )
        ),
    )

    # This will trigger the first refresh and authentication check
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = VolkswagenGoConnectData(
        client=client,
        coordinator=coordinator,
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
