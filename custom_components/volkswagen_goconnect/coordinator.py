"""DataUpdateCoordinator for volkswagen_goconnect."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

if TYPE_CHECKING:
    from datetime import timedelta

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .api import (
    VolkswagenGoConnectApiClient,
    VolkswagenGoConnectApiClientAuthenticationError,
    VolkswagenGoConnectApiClientError,
)
from .const import DOMAIN, LOGGER


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class VolkswagenGoConnectDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: VolkswagenGoConnectApiClient,
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.client = client
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            return await self.client.async_get_data()
        except VolkswagenGoConnectApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except VolkswagenGoConnectApiClientError as exception:
            raise UpdateFailed(exception) from exception
