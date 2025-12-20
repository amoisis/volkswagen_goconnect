"""Tests for the API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.volkswagen_goconnect.api import (
    VolkswagenGoConnectApiClient,
    VolkswagenGoConnectApiClientAuthenticationError,
    VolkswagenGoConnectApiClientCommunicationError,
)


@pytest.mark.asyncio
async def test_api_client_login_with_email_password():
    """Test login with email and password."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    # Mock the API response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"token": "test-token-123"}')
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    # Mock json.loads
    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"token": "test-token-123"}
        await client._login_with_email_password()

    assert client._token == "test-token-123"


@pytest.mark.asyncio
async def test_api_client_login_missing_token():
    """Test login fails when token is missing from response."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    # Mock the API response without token
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="{}")
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {}
        with pytest.raises(VolkswagenGoConnectApiClientAuthenticationError):
            await client._login_with_email_password()


@pytest.mark.asyncio
async def test_api_client_get_vehicles(mock_api_data):
    """Test getting vehicles list."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )
    client._token = "test-token"

    # Mock the API response
    mock_response = MagicMock()
    mock_response.status = 200
    vehicles_response = {
        "data": {"viewer": {"vehicles": [{"vehicle": {"id": "vehicle-1"}}]}}
    }
    mock_response.text = AsyncMock(
        return_value='{"data": {"viewer": {"vehicles": []}}}'
    )
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = vehicles_response
        result = await client.get_vehicles()

    assert "data" in result
    assert "viewer" in result["data"]


@pytest.mark.asyncio
async def test_api_client_get_vehicle_details(mock_api_data):
    """Test getting vehicle details."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )
    client._token = "test-token"

    # Mock the API response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"data": {"vehicle": {}}}')
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"data": {"vehicle": {"id": "vehicle-1"}}}
        result = await client.get_vehicle_details("vehicle-1")

    assert "data" in result
    assert result["data"]["vehicle"]["id"] == "vehicle-1"


@pytest.mark.asyncio
async def test_api_client_get_vehicle_system_overview(mock_api_data):
    """Test getting vehicle system overview."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )
    client._token = "test-token"

    # Mock the API response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"data": {"vehicle": {}}}')
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"data": {"vehicle": {"id": "vehicle-1"}}}
        result = await client.get_vehicle_system_overview("vehicle-1")

    assert "data" in result
    assert result["data"]["vehicle"]["id"] == "vehicle-1"


@pytest.mark.asyncio
async def test_api_client_async_get_data(mock_api_data):
    """Test async_get_data method."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )
    client._token = "test-token"

    # Mock multiple API responses
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"data": {}}')
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = mock_api_data
        result = await client.async_get_data()

    assert "data" in result


@pytest.mark.asyncio
async def test_api_client_login():
    """Test the login method."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    # Mock the login response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"token": "test-token"}')
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"token": "test-token"}
        await client.login()

    assert client._token == "test-token"


@pytest.mark.asyncio
async def test_api_client_login_with_device_token():
    """Test login with device token."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        device_token="device-token-123",
    )

    # Mock the device token login response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"token": "bearer-token"}')
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"token": "bearer-token"}
        await client.login()

    assert client._token == "bearer-token"


@pytest.mark.asyncio
async def test_api_client_login_device_token_fallback():
    """Test login falls back to email/password if device token fails."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
        device_token="invalid-token",
    )

    # Mock device token login to fail
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock_response = MagicMock()
        if call_count == 1:
            # First call (device token) - fail with 401
            mock_response.status = 401
            mock_response.text = AsyncMock(return_value='{"error": "Invalid token"}')
        else:
            # Second call (email/password) - succeed
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value='{"token": "new-token"}')
        mock_response.raise_for_status = MagicMock()
        return mock_response

    session.request = AsyncMock()
    session.request.return_value.__aenter__.side_effect = side_effect

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.side_effect = [{"error": "Invalid token"}, {"token": "new-token"}]
        await client.login()

    assert client._token == "new-token"


@pytest.mark.asyncio
async def test_api_client_login_no_credentials():
    """Test login fails when no credentials provided."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(session=session)

    with pytest.raises(VolkswagenGoConnectApiClientAuthenticationError):
        await client.login()


@pytest.mark.asyncio
async def test_api_client_register_device():
    """Test device registration."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )
    client._token = "test-token"

    # Mock the register device response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"deviceToken": "new-device-token"}')
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"deviceToken": "new-device-token"}
        result = await client.register_device()

    assert result["deviceToken"] == "new-device-token"


@pytest.mark.asyncio
async def test_verify_response_401():
    """Test _verify_response_or_raise with 401 status."""
    from custom_components.volkswagen_goconnect.api import _verify_response_or_raise

    mock_response = MagicMock()
    mock_response.status = 401

    with pytest.raises(VolkswagenGoConnectApiClientAuthenticationError):
        _verify_response_or_raise(mock_response)


@pytest.mark.asyncio
async def test_verify_response_403():
    """Test _verify_response_or_raise with 403 status."""
    from custom_components.volkswagen_goconnect.api import _verify_response_or_raise

    mock_response = MagicMock()
    mock_response.status = 403

    with pytest.raises(VolkswagenGoConnectApiClientAuthenticationError):
        _verify_response_or_raise(mock_response)


@pytest.mark.asyncio
async def test_async_get_data_with_details():
    """Test async_get_data with vehicle details and system overview."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )
    client._token = "test-token"

    call_count = 0

    def mock_json_response(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # get_vehicles
            return {
                "data": {
                    "viewer": {
                        "vehicles": [{"vehicle": {"id": "vehicle-1", "name": "My Car"}}]
                    }
                }
            }
        elif call_count == 2:  # get_vehicle_details
            return {
                "data": {
                    "vehicle": {"id": "vehicle-1", "name": "My Car", "model": "ID.3"}
                }
            }
        else:  # get_vehicle_system_overview
            return {"data": {"vehicle": {"batteryStatus": {"currentSOC_pct": 80}}}}

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="{}")
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.side_effect = mock_json_response
        result = await client.async_get_data()

    assert "data" in result
    assert "viewer" in result["data"]
    assert len(result["data"]["viewer"]["vehicles"]) == 1
    vehicle_data = result["data"]["viewer"]["vehicles"][0]["vehicle"]
    assert "batteryStatus" in vehicle_data


@pytest.mark.asyncio
async def test_async_get_data_no_vehicle_id():
    """Test async_get_data skips vehicles without ID."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )
    client._token = "test-token"

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="{}")
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {
            "data": {
                "viewer": {
                    "vehicles": [
                        {"vehicle": {"name": "Car without ID"}},
                        {"vehicle": None},
                    ]
                }
            }
        }
        result = await client.async_get_data()

    assert len(result["data"]["viewer"]["vehicles"]) == 0


@pytest.mark.asyncio
async def test_async_get_data_detail_fetch_fails():
    """Test async_get_data when detail fetch fails."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )
    client._token = "test-token"

    call_count = 0

    def mock_json_response(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # get_vehicles
            return {
                "data": {
                    "viewer": {
                        "vehicles": [{"vehicle": {"id": "vehicle-1", "name": "My Car"}}]
                    }
                }
            }
        elif call_count == 2:  # get_vehicle_details - return empty/invalid
            return {"data": {}}  # Missing "vehicle" key
        else:
            return {}

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="{}")
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.side_effect = mock_json_response
        result = await client.async_get_data()

    assert len(result["data"]["viewer"]["vehicles"]) == 1


@pytest.mark.asyncio
async def test_async_get_data_exception_in_detail_fetch():
    """Test async_get_data handles exceptions during detail fetch."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )
    client._token = "test-token"

    call_count = 0

    def mock_json_response(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # get_vehicles
            return {
                "data": {
                    "viewer": {
                        "vehicles": [{"vehicle": {"id": "vehicle-1", "name": "My Car"}}]
                    }
                }
            }
        else:
            raise Exception("Network error")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="{}")
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.side_effect = mock_json_response
        result = await client.async_get_data()

    assert len(result["data"]["viewer"]["vehicles"]) == 1


@pytest.mark.asyncio
async def test_get_vehicles_auth_retry():
    """Test get_vehicles retries on authentication error."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )
    client._token = "old-token"

    call_count = 0

    async def mock_api_wrapper(method, url, data=None, headers=None):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # First attempt - raise auth error
            raise VolkswagenGoConnectApiClientAuthenticationError("Unauthorized")
        else:
            # Retry after login - succeed
            return {"data": {"viewer": {"vehicles": []}}}

    # Mock login to update token
    async def mock_login():
        client._token = "new-token"

    client._api_wrapper = mock_api_wrapper
    client.login = AsyncMock(side_effect=mock_login)

    result = await client.get_vehicles()

    assert client._token == "new-token"
    assert "data" in result
    assert call_count == 2


@pytest.mark.asyncio
async def test_api_wrapper_session_not_initialized():
    """Test _api_wrapper raises error when session is None."""
    client = VolkswagenGoConnectApiClient(
        session=None,
        email="test@example.com",
        password="password123",
    )

    with pytest.raises(VolkswagenGoConnectApiClientCommunicationError):
        await client._api_wrapper(method="get", url="http://test.com")


@pytest.mark.asyncio
async def test_api_wrapper_json_decode_error():
    """Test _api_wrapper handles JSON decode errors."""
    import json
    from custom_components.volkswagen_goconnect.api import (
        VolkswagenGoConnectApiClientError,
    )

    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="invalid json")
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.side_effect = json.JSONDecodeError("error", "doc", 0)
        with pytest.raises(VolkswagenGoConnectApiClientError):
            await client._api_wrapper(method="get", url="http://test.com")


@pytest.mark.asyncio
async def test_api_wrapper_timeout_error():
    """Test _api_wrapper handles timeout errors."""
    import asyncio

    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    session.request = AsyncMock(side_effect=asyncio.TimeoutError())

    with pytest.raises(VolkswagenGoConnectApiClientCommunicationError):
        await client._api_wrapper(method="get", url="http://test.com")


@pytest.mark.asyncio
async def test_api_wrapper_client_error():
    """Test _api_wrapper handles aiohttp ClientError."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    session.request = AsyncMock(side_effect=aiohttp.ClientError("Connection failed"))

    with pytest.raises(VolkswagenGoConnectApiClientCommunicationError):
        await client._api_wrapper(method="get", url="http://test.com")


@pytest.mark.asyncio
async def test_api_wrapper_socket_error():
    """Test _api_wrapper handles socket errors."""
    import socket

    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    session.request = AsyncMock(side_effect=socket.gaierror("DNS lookup failed"))

    with pytest.raises(VolkswagenGoConnectApiClientCommunicationError):
        await client._api_wrapper(method="get", url="http://test.com")


@pytest.mark.asyncio
async def test_api_wrapper_unexpected_exception():
    """Test _api_wrapper handles unexpected exceptions."""
    from custom_components.volkswagen_goconnect.api import (
        VolkswagenGoConnectApiClientError,
    )

    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    session.request = AsyncMock(side_effect=ValueError("Something went wrong"))

    with pytest.raises(VolkswagenGoConnectApiClientError):
        await client._api_wrapper(method="get", url="http://test.com")


@pytest.mark.asyncio
async def test_api_client_login_with_device_token_and_fallback():
    """Test login with device token falls back to email/password."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
        device_token="device-token-123",
    )

    # Mock the API response for email/password login
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"token": "test-token-456"}')
    mock_response.raise_for_status = MagicMock()
    session.request = AsyncMock(return_value=mock_response)

    with patch.object(
        client, "_login_with_device_token", new_callable=AsyncMock
    ) as mock_device_login:
        mock_device_login.side_effect = VolkswagenGoConnectApiClientAuthenticationError(
            "Device token expired"
        )
        with patch.object(
            client, "_login_with_email_password", new_callable=AsyncMock
        ) as mock_email_login:
            await client.login()
            mock_device_login.assert_called_once()
            mock_email_login.assert_called_once()


@pytest.mark.asyncio
async def test_get_vehicles_retries_on_auth_error():
    """Test get_vehicles retries on auth error."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    with patch.object(client, "_api_wrapper", new_callable=AsyncMock) as mock_wrapper:
        # First call raises auth error, second succeeds
        mock_wrapper.side_effect = [
            VolkswagenGoConnectApiClientAuthenticationError("Auth failed"),
            {"data": {"viewer": {"vehicles": []}}},
        ]
        with patch.object(client, "login", new_callable=AsyncMock):
            result = await client.get_vehicles()
            assert result == {"data": {"viewer": {"vehicles": []}}}


@pytest.mark.asyncio
async def test_get_vehicle_details_no_token():
    """Test get_vehicle_details with no token triggers login."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    with patch.object(client, "_api_wrapper", new_callable=AsyncMock) as mock_wrapper:
        mock_wrapper.return_value = {"data": {"vehicle": {"id": "123", "name": "Test"}}}
        with patch.object(client, "login", new_callable=AsyncMock) as mock_login:
            result = await client.get_vehicle_details("123")
            mock_login.assert_called_once()
            assert "data" in result


@pytest.mark.asyncio
async def test_get_vehicle_system_overview_no_token():
    """Test get_vehicle_system_overview with no token triggers login."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    with patch.object(client, "_api_wrapper", new_callable=AsyncMock) as mock_wrapper:
        mock_wrapper.return_value = {"data": {"vehicle": {"id": "123"}}}
        with patch.object(client, "login", new_callable=AsyncMock) as mock_login:
            result = await client.get_vehicle_system_overview("123")
            mock_login.assert_called_once()
            assert "data" in result
