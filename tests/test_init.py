"""Tests for the __init__ module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from custom_components.volkswagen_goconnect import (
    async_setup,
    async_reload_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.volkswagen_goconnect.const import (
    CONF_ABRP_ENABLED,
    CONF_IGNITION_POLLING_INTERVAL,
    CONF_POLLING_INTERVAL,
    DOMAIN,
    SIGNAL_ABRP_ACKNOWLEDGE,
)


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


@pytest.mark.asyncio
async def test_async_setup_registers_services_and_handles_send(hass: HomeAssistant):
    """Register services and execute abrp_send handler with valid payload."""
    hass.services = MagicMock()
    hass.services.has_service = MagicMock(return_value=False)
    hass.services.async_register = MagicMock()

    with patch(
        "custom_components.volkswagen_goconnect.async_abrp_send_service",
        new=AsyncMock(),
    ) as mock_abrp_send:
        assert await async_setup(hass, {}) is True

        registered_handlers = {
            call.args[1]: call.args[2]
            for call in hass.services.async_register.call_args_list
        }
        send_handler = registered_handlers["abrp_send"]

        call = MagicMock()
        call.data = {
            "api_key": "api",
            "token": "token",
            "license_plate": "ABC123",
            "service_data": {"soc": 80},
        }
        await send_handler(call)

        mock_abrp_send.assert_awaited_once_with(
            hass,
            "api",
            "token",
            "ABC123",
            {"soc": 80},
        )


@pytest.mark.asyncio
async def test_async_setup_send_handler_requires_required_fields(
    hass: HomeAssistant,
):
    """abrp_send handler should reject missing required params."""
    hass.services = MagicMock()
    hass.services.has_service = MagicMock(return_value=False)
    hass.services.async_register = MagicMock()

    with (
        patch("custom_components.volkswagen_goconnect.LOGGER") as mock_logger,
        patch(
            "custom_components.volkswagen_goconnect.async_abrp_send_service",
            new=AsyncMock(),
        ) as mock_abrp_send,
    ):
        assert await async_setup(hass, {}) is True
        send_handler = {
            call.args[1]: call.args[2]
            for call in hass.services.async_register.call_args_list
        }["abrp_send"]

        call = MagicMock()
        call.data = {"api_key": "", "token": "", "license_plate": ""}
        await send_handler(call)

    mock_abrp_send.assert_not_awaited()
    assert mock_logger.error.called


@pytest.mark.asyncio
async def test_async_setup_acknowledge_handler_dispatches_for_enabled_entries(
    hass: HomeAssistant,
):
    """abrp_acknowledge handler dispatches per enabled config entry."""
    hass.services = MagicMock()
    hass.services.has_service = MagicMock(return_value=False)
    hass.services.async_register = MagicMock()

    enabled_entry = MagicMock()
    enabled_entry.entry_id = "entry-enabled"
    enabled_entry.runtime_data = MagicMock()
    enabled_entry.runtime_data.abrp_enabled = True

    disabled_entry = MagicMock()
    disabled_entry.entry_id = "entry-disabled"
    disabled_entry.runtime_data = MagicMock()
    disabled_entry.runtime_data.abrp_enabled = False

    hass.config_entries = MagicMock()
    hass.config_entries.async_entries = MagicMock(
        return_value=[enabled_entry, disabled_entry]
    )

    with patch(
        "custom_components.volkswagen_goconnect.async_dispatcher_send"
    ) as mock_dispatcher:
        assert await async_setup(hass, {}) is True
        ack_handler = {
            call.args[1]: call.args[2]
            for call in hass.services.async_register.call_args_list
        }["abrp_acknowledge"]

        call = MagicMock()
        call.data = {"license_plate": "abc123"}
        await ack_handler(call)

    mock_dispatcher.assert_called_once_with(
        hass,
        SIGNAL_ABRP_ACKNOWLEDGE.format(entry_id="entry-enabled"),
        "abc123",
    )


@pytest.mark.asyncio
async def test_async_setup_acknowledge_requires_license_plate(hass: HomeAssistant):
    """abrp_acknowledge handler should reject missing license_plate."""
    hass.services = MagicMock()
    hass.services.has_service = MagicMock(return_value=False)
    hass.services.async_register = MagicMock()

    with patch("custom_components.volkswagen_goconnect.LOGGER") as mock_logger:
        assert await async_setup(hass, {}) is True
        ack_handler = {
            call.args[1]: call.args[2]
            for call in hass.services.async_register.call_args_list
        }["abrp_acknowledge"]

        call = MagicMock()
        call.data = {}
        await ack_handler(call)

    assert mock_logger.error.called


@pytest.mark.asyncio
async def test_async_setup_entry_with_abrp_enabled_creates_all_coordinators(
    hass: HomeAssistant,
):
    """Set up ABRP and ignition coordinators when ABRP mode is enabled."""
    entry = MagicMock(spec=ConfigEntry)
    entry.data = {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "password123",
        "device_token": "test-token",
        CONF_POLLING_INTERVAL: 60,
        CONF_ABRP_ENABLED: True,
        CONF_IGNITION_POLLING_INTERVAL: 10,
    }
    entry.options = {CONF_ABRP_ENABLED: True, CONF_IGNITION_POLLING_INTERVAL: 10}
    entry.entry_id = "test-entry-id"

    with (
        patch(
            "custom_components.volkswagen_goconnect.async_get_integration"
        ) as integration,
        patch("custom_components.volkswagen_goconnect.async_get_clientsession"),
        patch("custom_components.volkswagen_goconnect.VolkswagenGoConnectApiClient"),
        patch(
            "custom_components.volkswagen_goconnect"
            ".VolkswagenGoConnectDataUpdateCoordinator"
        ) as coordinator_cls,
        patch(
            "custom_components.volkswagen_goconnect"
            ".VolkswagenGoConnectIgnitionCoordinator"
        ) as ignition_cls,
        patch(
            "custom_components.volkswagen_goconnect.VolkswagenGoConnectAbrpCoordinator"
        ) as abrp_cls,
    ):
        integration.return_value = MagicMock()
        coordinator = AsyncMock()
        ignition = AsyncMock()
        abrp = AsyncMock()
        coordinator_cls.return_value = coordinator
        ignition_cls.return_value = ignition
        abrp_cls.return_value = abrp

        hass.config_entries = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        entry.add_update_listener = MagicMock(return_value=MagicMock())
        entry.async_on_unload = MagicMock()

        result = await async_setup_entry(hass, entry)

    assert result is True
    coordinator.async_config_entry_first_refresh.assert_awaited_once()
    ignition.async_config_entry_first_refresh.assert_awaited_once()
    abrp.async_config_entry_first_refresh.assert_awaited_once()
    hass.config_entries.async_forward_entry_setups.assert_awaited_once()
    assert entry.runtime_data.abrp_enabled is True


@pytest.mark.asyncio
async def test_async_setup_skips_register_when_services_already_exist(
    hass: HomeAssistant,
):
    """Do not register services that already exist in Home Assistant."""
    hass.services = MagicMock()
    hass.services.has_service = MagicMock(return_value=True)
    hass.services.async_register = MagicMock()

    assert await async_setup(hass, {}) is True
    hass.services.has_service.assert_any_call(DOMAIN, "abrp_send")
    hass.services.has_service.assert_any_call(DOMAIN, "abrp_acknowledge")
    hass.services.async_register.assert_not_called()
