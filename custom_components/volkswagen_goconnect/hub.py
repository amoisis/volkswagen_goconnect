"""The Volkswagen GoConnect Hub."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import VolkswagenGoConnectApiClient

_LOGGER = logging.getLogger(__name__)


class VolkswagenGoConnectHub:
    """A hub to manage the Volkswagen GoConnect integration."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        email: str,
        password: str,
        polling_interval: int,
    ) -> None:
        """Initialize."""
        self._hass = hass
        self._email = email
        self._password = password
        self._polling_interval = polling_interval

        self._api_client = VolkswagenGoConnectApiClient(
            email=self._email,
            password=self._password,
            session=async_get_clientsession(hass),
        )

        self.coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=self._email,
            update_method=self.update,
            update_interval=timedelta(seconds=self._polling_interval),
        )

    async def update(self) -> dict[str, Any]:
        """Update all devices."""
        # In a real integration, you would fetch data from the API here
        # For now, we'll just return some dummy data
        return {"dummy": "data"}

    async def authenticate(self) -> None:
        """Authenticate with the API."""
        await self._api_client.login()
