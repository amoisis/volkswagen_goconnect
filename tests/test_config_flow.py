"""Tests for the config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.volkswagen_goconnect.api import (
    VolkswagenGoConnectApiClientAuthenticationError,
    VolkswagenGoConnectApiClientCommunicationError,
    VolkswagenGoConnectApiClientError,
)
from custom_components.volkswagen_goconnect.config_flow import (
    VolkswagenGoConnectFlowHandler,
    VolkswagenGoConnectOptionsFlowHandler,
)
from custom_components.volkswagen_goconnect.const import CONF_POLLING_INTERVAL, DOMAIN


@pytest.mark.asyncio
async def test_config_flow_instantiation(hass: HomeAssistant):
    """Test that config flow can be instantiated."""
    flow = VolkswagenGoConnectFlowHandler()
    assert flow is not None
    assert flow.VERSION == 1


@pytest.mark.asyncio
async def test_config_flow_user_step_form(hass: HomeAssistant):
    """Test the user step shows the form."""
    flow = VolkswagenGoConnectFlowHandler()
    flow.hass = hass

    result = await flow.async_step_user(user_input=None)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


@pytest.mark.asyncio
async def test_config_flow_user_step_success(hass: HomeAssistant):
    """Test successful user step."""
    flow = VolkswagenGoConnectFlowHandler()
    flow.hass = hass
    flow.context = {}

    user_input = {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "password123",
        CONF_POLLING_INTERVAL: 60,
    }

    with (
        patch(
            "custom_components.volkswagen_goconnect.config_flow.VolkswagenGoConnectApiClient"
        ) as mock_client,
        patch.object(flow, "_abort_if_unique_id_configured"),
    ):
        mock_instance = AsyncMock()
        mock_instance.login = AsyncMock()
        mock_instance.register_device = AsyncMock(
            return_value={"deviceToken": "test-token-123"}
        )
        mock_client.return_value = mock_instance

        with patch(
            "custom_components.volkswagen_goconnect.config_flow.async_create_clientsession"
        ):
            result = await flow.async_step_user(user_input=user_input)

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@example.com"
    assert result["data"][CONF_EMAIL] == "test@example.com"
    assert result["data"]["device_token"] == "test-token-123"
    assert result["data"][CONF_POLLING_INTERVAL] == 60


@pytest.mark.asyncio
async def test_config_flow_user_step_auth_error(hass: HomeAssistant):
    """Test user step with authentication error."""
    flow = VolkswagenGoConnectFlowHandler()
    flow.hass = hass

    user_input = {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "wrong_password",
        CONF_POLLING_INTERVAL: 60,
    }

    with patch(
        "custom_components.volkswagen_goconnect.config_flow.VolkswagenGoConnectApiClient"
    ) as mock_client:
        mock_instance = AsyncMock()
        mock_instance.login = AsyncMock(
            side_effect=VolkswagenGoConnectApiClientAuthenticationError(
                "Invalid credentials"
            )
        )
        mock_client.return_value = mock_instance

        with patch(
            "custom_components.volkswagen_goconnect.config_flow.async_create_clientsession"
        ):
            result = await flow.async_step_user(user_input=user_input)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "auth"}


@pytest.mark.asyncio
async def test_config_flow_user_step_connection_error(hass: HomeAssistant):
    """Test user step with connection error."""
    flow = VolkswagenGoConnectFlowHandler()
    flow.hass = hass

    user_input = {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "password123",
        CONF_POLLING_INTERVAL: 60,
    }

    with patch(
        "custom_components.volkswagen_goconnect.config_flow.VolkswagenGoConnectApiClient"
    ) as mock_client:
        mock_instance = AsyncMock()
        mock_instance.login = AsyncMock(
            side_effect=VolkswagenGoConnectApiClientCommunicationError(
                "Connection failed"
            )
        )
        mock_client.return_value = mock_instance

        with patch(
            "custom_components.volkswagen_goconnect.config_flow.async_create_clientsession"
        ):
            result = await flow.async_step_user(user_input=user_input)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "connection"}


@pytest.mark.asyncio
async def test_config_flow_user_step_unknown_error(hass: HomeAssistant):
    """Test user step with unknown error."""
    flow = VolkswagenGoConnectFlowHandler()
    flow.hass = hass

    user_input = {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "password123",
        CONF_POLLING_INTERVAL: 60,
    }

    with patch(
        "custom_components.volkswagen_goconnect.config_flow.VolkswagenGoConnectApiClient"
    ) as mock_client:
        mock_instance = AsyncMock()
        mock_instance.login = AsyncMock(
            side_effect=VolkswagenGoConnectApiClientError("Unknown error")
        )
        mock_client.return_value = mock_instance

        with patch(
            "custom_components.volkswagen_goconnect.config_flow.async_create_clientsession"
        ):
            result = await flow.async_step_user(user_input=user_input)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


@pytest.mark.asyncio
async def test_config_flow_no_device_token(hass: HomeAssistant):
    """Test config flow when device token is missing."""
    flow = VolkswagenGoConnectFlowHandler()
    flow.hass = hass

    user_input = {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "password123",
        CONF_POLLING_INTERVAL: 60,
    }

    with patch(
        "custom_components.volkswagen_goconnect.config_flow.VolkswagenGoConnectApiClient"
    ) as mock_client:
        mock_instance = AsyncMock()
        mock_instance.login = AsyncMock()
        mock_instance.register_device = AsyncMock(return_value={})
        mock_client.return_value = mock_instance

        with patch(
            "custom_components.volkswagen_goconnect.config_flow.async_create_clientsession"
        ):
            result = await flow.async_step_user(user_input=user_input)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "auth"}


@pytest.mark.asyncio
async def test_options_flow_init(hass: HomeAssistant):
    """Test options flow initialization."""
    config_entry = MagicMock(spec=config_entries.ConfigEntry)
    config_entry.data = {CONF_POLLING_INTERVAL: 60}
    config_entry.options = {}

    flow = VolkswagenGoConnectOptionsFlowHandler(config_entry)

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


@pytest.mark.asyncio
async def test_options_flow_update(hass: HomeAssistant):
    """Test options flow update."""
    config_entry = MagicMock(spec=config_entries.ConfigEntry)
    config_entry.data = {CONF_POLLING_INTERVAL: 60}
    config_entry.options = {}

    flow = VolkswagenGoConnectOptionsFlowHandler(config_entry)

    user_input = {CONF_POLLING_INTERVAL: 120}
    result = await flow.async_step_init(user_input=user_input)

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_POLLING_INTERVAL] == 120


@pytest.mark.asyncio
async def test_async_get_options_flow():
    """Test getting options flow."""
    config_entry = MagicMock(spec=config_entries.ConfigEntry)

    options_flow = VolkswagenGoConnectFlowHandler.async_get_options_flow(config_entry)

    assert isinstance(options_flow, VolkswagenGoConnectOptionsFlowHandler)
    assert options_flow._config_entry == config_entry


@pytest.mark.asyncio
async def test_config_flow_reauth_step(hass: HomeAssistant):
    """Test reauth step."""
    flow = VolkswagenGoConnectFlowHandler()
    flow.hass = hass

    # Create a mock entry
    mock_entry = MagicMock(spec=config_entries.ConfigEntry)
    mock_entry.data = {
        CONF_EMAIL: "test@example.com",
        "device_token": "old-token",
    }

    hass.config_entries = MagicMock()
    hass.config_entries.async_get_entry = MagicMock(return_value=mock_entry)

    flow.context = {"entry_id": "test-entry-id"}

    result = await flow.async_step_reauth(entry_data={})

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"


@pytest.mark.asyncio
async def test_config_flow_reauth_confirm_success(hass: HomeAssistant):
    """Test successful reauth confirmation."""
    flow = VolkswagenGoConnectFlowHandler()
    flow.hass = hass

    # Create a mock entry
    mock_entry = MagicMock(spec=config_entries.ConfigEntry)
    mock_entry.data = {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "old-password",
        "device_token": "old-token",
    }
    mock_entry.entry_id = "test-entry-id"

    flow.entry = mock_entry

    hass.config_entries = MagicMock()
    hass.config_entries.async_update_entry = MagicMock()
    hass.config_entries.async_reload = AsyncMock()

    user_input = {CONF_PASSWORD: "new-password"}

    with patch(
        "custom_components.volkswagen_goconnect.config_flow.VolkswagenGoConnectApiClient"
    ) as mock_client:
        mock_instance = AsyncMock()
        mock_instance.login = AsyncMock()
        mock_instance.register_device = AsyncMock(
            return_value={"deviceToken": "new-token-123"}
        )
        mock_client.return_value = mock_instance

        with patch(
            "custom_components.volkswagen_goconnect.config_flow.async_create_clientsession"
        ):
            result = await flow.async_step_reauth_confirm(user_input=user_input)

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    hass.config_entries.async_reload.assert_called_once_with("test-entry-id")


@pytest.mark.asyncio
async def test_config_flow_reauth_confirm_auth_error(hass: HomeAssistant):
    """Test reauth confirmation with auth error."""
    flow = VolkswagenGoConnectFlowHandler()
    flow.hass = hass

    mock_entry = MagicMock(spec=config_entries.ConfigEntry)
    mock_entry.data = {
        CONF_EMAIL: "test@example.com",
        "device_token": "old-token",
    }

    flow.entry = mock_entry

    user_input = {CONF_PASSWORD: "wrong-password"}

    with patch(
        "custom_components.volkswagen_goconnect.config_flow.VolkswagenGoConnectApiClient"
    ) as mock_client:
        mock_instance = AsyncMock()
        mock_instance.login = AsyncMock(
            side_effect=VolkswagenGoConnectApiClientAuthenticationError("Invalid")
        )
        mock_client.return_value = mock_instance

        with patch(
            "custom_components.volkswagen_goconnect.config_flow.async_create_clientsession"
        ):
            result = await flow.async_step_reauth_confirm(user_input=user_input)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "auth"}
