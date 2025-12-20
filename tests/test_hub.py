"""Tests for the hub."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.volkswagen_goconnect.hub import VolkswagenGoConnectHub


@pytest.mark.asyncio
async def test_hub_initialization():
    """Test hub initialization."""
    hass = MagicMock(spec=HomeAssistant)

    with (
        patch(
            "custom_components.volkswagen_goconnect.hub.async_get_clientsession"
        ) as mock_session,
        patch(
            "custom_components.volkswagen_goconnect.hub.DataUpdateCoordinator"
        ) as mock_coordinator,
    ):
        mock_session.return_value = MagicMock()
        mock_coordinator.return_value = MagicMock()

        hub = VolkswagenGoConnectHub(
            hass=hass,
            email="test@example.com",
            password="password123",
            polling_interval=60,
        )

        assert hub._email == "test@example.com"
        assert hub._password == "password123"
        assert hub._polling_interval == 60
        assert hub._api_client is not None
        assert hub.coordinator is not None


@pytest.mark.asyncio
async def test_hub_update():
    """Test hub update method."""
    hass = MagicMock(spec=HomeAssistant)

    with (
        patch(
            "custom_components.volkswagen_goconnect.hub.async_get_clientsession"
        ) as mock_session,
        patch(
            "custom_components.volkswagen_goconnect.hub.DataUpdateCoordinator"
        ) as mock_coordinator,
    ):
        mock_session.return_value = MagicMock()
        mock_coordinator.return_value = MagicMock()

        hub = VolkswagenGoConnectHub(
            hass=hass,
            email="test@example.com",
            password="password123",
            polling_interval=60,
        )

        result = await hub.update()

        assert result is not None
        assert isinstance(result, dict)
        assert "dummy" in result
        assert result["dummy"] == "data"


@pytest.mark.asyncio
async def test_hub_authenticate():
    """Test hub authenticate method."""
    hass = MagicMock(spec=HomeAssistant)

    with (
        patch(
            "custom_components.volkswagen_goconnect.hub.async_get_clientsession"
        ) as mock_session,
        patch(
            "custom_components.volkswagen_goconnect.hub.DataUpdateCoordinator"
        ) as mock_coordinator,
    ):
        mock_session.return_value = MagicMock()
        mock_coordinator.return_value = MagicMock()

        hub = VolkswagenGoConnectHub(
            hass=hass,
            email="test@example.com",
            password="password123",
            polling_interval=60,
        )

        # Mock the API client's login method
        hub._api_client.login = AsyncMock()

        await hub.authenticate()

        hub._api_client.login.assert_called_once()


@pytest.mark.asyncio
async def test_hub_coordinator_setup():
    """Test hub coordinator is properly configured."""
    hass = MagicMock(spec=HomeAssistant)

    with (
        patch(
            "custom_components.volkswagen_goconnect.hub.async_get_clientsession"
        ) as mock_session,
        patch(
            "custom_components.volkswagen_goconnect.hub.DataUpdateCoordinator"
        ) as mock_coordinator_class,
    ):
        mock_session.return_value = MagicMock()
        mock_coordinator = MagicMock()
        mock_coordinator_class.return_value = mock_coordinator

        hub = VolkswagenGoConnectHub(
            hass=hass,
            email="test@example.com",
            password="password123",
            polling_interval=120,
        )

        # Verify coordinator was created with correct params
        assert hub.coordinator is not None
        mock_coordinator_class.assert_called_once()


@pytest.mark.asyncio
async def test_hub_with_different_polling_intervals():
    """Test hub with different polling intervals."""
    hass = MagicMock(spec=HomeAssistant)

    with (
        patch(
            "custom_components.volkswagen_goconnect.hub.async_get_clientsession"
        ) as mock_session,
        patch(
            "custom_components.volkswagen_goconnect.hub.DataUpdateCoordinator"
        ) as mock_coordinator,
    ):
        mock_session.return_value = MagicMock()
        mock_coordinator.return_value = MagicMock()

        # Test with 10 seconds
        hub1 = VolkswagenGoConnectHub(
            hass=hass,
            email="test@example.com",
            password="password123",
            polling_interval=10,
        )
        assert hub1._polling_interval == 10

        # Test with 3600 seconds
        hub2 = VolkswagenGoConnectHub(
            hass=hass,
            email="test2@example.com",
            password="password456",
            polling_interval=3600,
        )
        assert hub2._polling_interval == 3600
