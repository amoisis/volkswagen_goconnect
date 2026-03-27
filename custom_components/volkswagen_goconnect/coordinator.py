"""DataUpdateCoordinator for volkswagen_goconnect."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    VolkswagenGoConnectApiClient,
    VolkswagenGoConnectApiClientAuthenticationError,
    VolkswagenGoConnectApiClientError,
)
from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from datetime import timedelta

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


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
            data = await self.client.async_get_data()
        except VolkswagenGoConnectApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except VolkswagenGoConnectApiClientError as exception:
            raise UpdateFailed(exception) from exception

        return data


class VolkswagenGoConnectIgnitionCoordinator(VolkswagenGoConnectDataUpdateCoordinator):
    """
    Coordinator for ignition state with adaptive polling.

    Polls a lightweight ignition query and dynamically adjusts the update
    interval: fast when any vehicle's ignition is on (e.g. driving), slow
    when all vehicles are parked.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: VolkswagenGoConnectApiClient,
        fast_interval: timedelta,
        slow_interval: timedelta,
    ) -> None:
        """Initialize with separate fast and slow polling intervals."""
        self._fast_interval = fast_interval
        self._slow_interval = slow_interval
        # Start at slow rate — will self-correct after first successful fetch.
        super().__init__(hass=hass, client=client, update_interval=slow_interval)

    async def _async_update_data(self) -> Any:
        """Fetch slim ignition data and adapt the polling interval."""
        try:
            data = await self.client.async_get_ignition_data()
        except VolkswagenGoConnectApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except VolkswagenGoConnectApiClientError as exception:
            raise UpdateFailed(exception) from exception

        vehicles = data.get("data", {}).get("viewer", {}).get("vehicles", [])
        any_ignition_on = any(
            entry.get("vehicle", {}).get("ignition", {}).get("on", False)
            for entry in vehicles
            if isinstance(entry, dict)
        )
        self.update_interval = (
            self._fast_interval if any_ignition_on else self._slow_interval
        )

        return data


class VolkswagenGoConnectAbrpCoordinator(VolkswagenGoConnectDataUpdateCoordinator):
    """Coordinator for slim ABRP telemetry data with ignition-based polling."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: VolkswagenGoConnectApiClient,
        fast_interval: timedelta,
        slow_interval: timedelta,
    ) -> None:
        """Initialize with separate fast and slow polling intervals."""
        self._fast_interval = fast_interval
        self._slow_interval = slow_interval
        super().__init__(hass=hass, client=client, update_interval=slow_interval)

    async def _async_update_data(self) -> Any:
        """Fetch slim ABRP data and adapt polling interval by ignition state."""
        try:
            data = await self.client.async_get_abrp_data()
        except VolkswagenGoConnectApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except VolkswagenGoConnectApiClientError as exception:
            raise UpdateFailed(exception) from exception

        vehicles = data.get("data", {}).get("viewer", {}).get("vehicles", [])
        any_ignition_on = any(
            entry.get("vehicle", {}).get("ignition", {}).get("on", False)
            for entry in vehicles
            if isinstance(entry, dict)
        )
        self.update_interval = (
            self._fast_interval if any_ignition_on else self._slow_interval
        )

        return data
