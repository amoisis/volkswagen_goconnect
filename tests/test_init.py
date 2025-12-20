"""Tests for the __init__ module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from custom_components.volkswagen_goconnect import (
    async_reload_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.volkswagen_goconnect.const import CONF_POLLING_INTERVAL


@pytest.mark.asyncio
async def test_async_setup_entry_success(hass: HomeAssistant):
    """Test successful setup of entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.data = {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "password123",
        "device_token": "test-token",
        CONF_POLLING_INTERVAL: 60,
    }
    entry.options = {}
    entry.entry_id = "test-entry-id"

    with (
        patch(
            "custom_components.volkswagen_goconnect.async_get_integration"
        ) as mock_integration,
        patch(
            "custom_components.volkswagen_goconnect.async_get_clientsession"
        ) as mock_session,
        patch(
            "custom_components.volkswagen_goconnect.VolkswagenGoConnectApiClient"
        ) as mock_client_class,
        patch(
            "custom_components.volkswagen_goconnect.VolkswagenGoConnectDataUpdateCoordinator"
        ) as mock_coordinator_class,
    ):
        mock_integration.return_value = MagicMock()
        mock_session.return_value = MagicMock()

        mock_client = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        hass.config_entries = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        entry.add_update_listener = MagicMock(return_value=MagicMock())
        entry.async_on_unload = MagicMock()

        result = await async_setup_entry(hass, entry)

        assert result is True
        mock_client.login.assert_called_once()
        mock_coordinator.async_config_entry_first_refresh.assert_called_once()
        hass.config_entries.async_forward_entry_setups.assert_called_once()


@pytest.mark.asyncio
async def test_async_setup_entry_with_options(hass: HomeAssistant):
    """Test setup entry with options for polling interval."""
    entry = MagicMock(spec=ConfigEntry)
    entry.data = {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "password123",
        "device_token": "test-token",
        CONF_POLLING_INTERVAL: 60,
    }
    entry.options = {CONF_POLLING_INTERVAL: 120}
    entry.entry_id = "test-entry-id"

    with (
        patch("custom_components.volkswagen_goconnect.async_get_integration"),
        patch("custom_components.volkswagen_goconnect.async_get_clientsession"),
        patch(
            "custom_components.volkswagen_goconnect.VolkswagenGoConnectApiClient"
        ) as mock_client_class,
        patch(
            "custom_components.volkswagen_goconnect.VolkswagenGoConnectDataUpdateCoordinator"
        ) as mock_coordinator_class,
    ):
        mock_client = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        hass.config_entries = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        entry.add_update_listener = MagicMock(return_value=MagicMock())
        entry.async_on_unload = MagicMock()

        result = await async_setup_entry(hass, entry)

        assert result is True


@pytest.mark.asyncio
async def test_async_setup_entry_login_failure(hass: HomeAssistant):
    """Test setup entry when login fails."""
    entry = MagicMock(spec=ConfigEntry)
    entry.data = {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "password123",
        "device_token": "test-token",
        CONF_POLLING_INTERVAL: 60,
    }
    entry.options = {}
    entry.entry_id = "test-entry-id"

    with (
        patch("custom_components.volkswagen_goconnect.async_get_integration"),
        patch("custom_components.volkswagen_goconnect.async_get_clientsession"),
        patch(
            "custom_components.volkswagen_goconnect.VolkswagenGoConnectApiClient"
        ) as mock_client_class,
        patch(
            "custom_components.volkswagen_goconnect.VolkswagenGoConnectDataUpdateCoordinator"
        ) as mock_coordinator_class,
    ):
        mock_client = AsyncMock()
        mock_client.login = AsyncMock(side_effect=Exception("Login failed"))
        mock_client_class.return_value = mock_client

        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        hass.config_entries = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        entry.add_update_listener = MagicMock(return_value=MagicMock())
        entry.async_on_unload = MagicMock()

        # Should still return True, coordinator will handle auth errors
        result = await async_setup_entry(hass, entry)

        assert result is True


@pytest.mark.asyncio
async def test_async_unload_entry(hass: HomeAssistant):
    """Test unloading an entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry-id"

    hass.config_entries = MagicMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    result = await async_unload_entry(hass, entry)

    assert result is True
    hass.config_entries.async_unload_platforms.assert_called_once()


@pytest.mark.asyncio
async def test_async_reload_entry(hass: HomeAssistant):
    """Test reloading an entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry-id"

    hass.config_entries = MagicMock()
    hass.config_entries.async_reload = AsyncMock()

    await async_reload_entry(hass, entry)

    hass.config_entries.async_reload.assert_called_once_with("test-entry-id")
