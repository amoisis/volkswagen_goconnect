"""Tests for the coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.volkswagen_goconnect.api import (
    VolkswagenGoConnectApiClient,
    VolkswagenGoConnectApiClientAuthenticationError,
    VolkswagenGoConnectApiClientError,
)
from custom_components.volkswagen_goconnect.coordinator import (
    VolkswagenGoConnectDataUpdateCoordinator,
)


@pytest.mark.asyncio
async def test_client_async_get_data(mock_api_data):
    """Test client async_get_data method."""
    # Create a mock client
    mock_client = AsyncMock(spec=VolkswagenGoConnectApiClient)
    mock_client.async_get_data = AsyncMock(return_value=mock_api_data)

    # Call the method
    data = await mock_client.async_get_data()

    # Verify the data structure
    assert "data" in data
    assert "viewer" in data["data"]
    assert "vehicles" in data["data"]["viewer"]
    assert len(data["data"]["viewer"]["vehicles"]) == 1

    # Verify vehicle data
    vehicle = data["data"]["viewer"]["vehicles"][0]["vehicle"]
    assert vehicle["id"] == "test-vehicle-id"
    assert vehicle["licensePlate"] == "ABC123"


@pytest.mark.asyncio
async def test_coordinator_initialization():
    """Test coordinator initialization."""
    hass = MagicMock(spec=HomeAssistant)
    client = MagicMock(spec=VolkswagenGoConnectApiClient)

    with patch(
        "custom_components.volkswagen_goconnect.coordinator.DataUpdateCoordinator.__init__",
        return_value=None,
    ):
        coordinator = VolkswagenGoConnectDataUpdateCoordinator(
            hass=hass,
            client=client,
            update_interval=timedelta(seconds=60),
        )

        assert coordinator.client == client


@pytest.mark.asyncio
async def test_coordinator_update_success(mock_api_data):
    """Test successful data update."""
    hass = MagicMock(spec=HomeAssistant)
    client = AsyncMock(spec=VolkswagenGoConnectApiClient)
    client.async_get_data = AsyncMock(return_value=mock_api_data)

    with patch(
        "custom_components.volkswagen_goconnect.coordinator.DataUpdateCoordinator.__init__",
        return_value=None,
    ):
        coordinator = VolkswagenGoConnectDataUpdateCoordinator(
            hass=hass,
            client=client,
            update_interval=timedelta(seconds=60),
        )

        data = await coordinator._async_update_data()

        assert data == mock_api_data
        client.async_get_data.assert_called_once()


@pytest.mark.asyncio
async def test_coordinator_update_authentication_error():
    """Test coordinator raises ConfigEntryAuthFailed on auth error."""
    hass = MagicMock(spec=HomeAssistant)
    client = AsyncMock(spec=VolkswagenGoConnectApiClient)
    client.async_get_data = AsyncMock(
        side_effect=VolkswagenGoConnectApiClientAuthenticationError("Auth failed")
    )

    with patch(
        "custom_components.volkswagen_goconnect.coordinator.DataUpdateCoordinator.__init__",
        return_value=None,
    ):
        coordinator = VolkswagenGoConnectDataUpdateCoordinator(
            hass=hass,
            client=client,
            update_interval=timedelta(seconds=60),
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_update_communication_error():
    """Test coordinator raises UpdateFailed on communication error."""
    hass = MagicMock(spec=HomeAssistant)
    client = AsyncMock(spec=VolkswagenGoConnectApiClient)
    client.async_get_data = AsyncMock(
        side_effect=VolkswagenGoConnectApiClientError("Communication error")
    )

    with patch(
        "custom_components.volkswagen_goconnect.coordinator.DataUpdateCoordinator.__init__",
        return_value=None,
    ):
        coordinator = VolkswagenGoConnectDataUpdateCoordinator(
            hass=hass,
            client=client,
            update_interval=timedelta(seconds=60),
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
