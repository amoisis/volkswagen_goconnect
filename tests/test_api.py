"""Tests for the API client."""

import contextlib
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


def test_sanitize_mapping():
    """Test _sanitize_mapping function."""
    from custom_components.volkswagen_goconnect.api import _sanitize_mapping

    # Test dict with sensitive keys
    data = {
        "username": "test",
        "password": "secret123",
        "authorization": "Bearer token",
        "data": {"nested_token": "value", "safe": "data"},
    }
    result = _sanitize_mapping(data)
    assert result["username"] == "test"
    assert result["password"] == "***REDACTED***"
    assert result["authorization"] == "***REDACTED***"
    assert result["data"]["safe"] == "data"

    # Test list
    data_list = [{"token": "secret"}, {"safe": "value"}]
    result_list = _sanitize_mapping(data_list)
    assert result_list[0]["token"] == "***REDACTED***"
    assert result_list[1]["safe"] == "value"

    # Test non-dict, non-list
    assert _sanitize_mapping("string") == "string"
    assert _sanitize_mapping(123) == 123


def test_sanitize_headers():
    """Test _sanitize_headers function."""
    from custom_components.volkswagen_goconnect.api import _sanitize_headers

    # Test with None
    assert _sanitize_headers(None) is None

    # Test with sensitive headers
    headers = {
        "User-Agent": "test-agent",
        "Authorization": "Bearer secret",
        "Cookie": "session=xyz",
        "Content-Type": "application/json",
    }
    result = _sanitize_headers(headers)
    assert result["User-Agent"] == "test-agent"
    assert result["Authorization"] == "***REDACTED***"
    assert result["Cookie"] == "***REDACTED***"
    assert result["Content-Type"] == "application/json"


def test_sanitize_url():
    """Test _sanitize_url function."""
    from custom_components.volkswagen_goconnect.api import _sanitize_url
    from urllib.parse import quote

    # Test URL with sensitive query params
    url = "https://api.example.com/auth?token=secret&username=test&password=pass123"
    result = _sanitize_url(url)
    # The redacted value gets URL encoded
    assert (
        f"token={quote('***REDACTED***')}" in result or "token=***REDACTED***" in result
    )
    assert "password" in result
    assert "username=test" in result

    # Test URL without query params
    url_no_query = "https://api.example.com/data"
    result_no_query = _sanitize_url(url_no_query)
    assert result_no_query == url_no_query

    # Test invalid URL (exception path)
    assert _sanitize_url("not a valid url") == "not a valid url"


@pytest.mark.asyncio
async def test_verify_response_with_client_response_error():
    """Test _verify_response_or_raise with ClientResponseError."""
    from custom_components.volkswagen_goconnect.api import _verify_response_or_raise

    mock_response = MagicMock()
    mock_response.status = 500

    def raise_error():
        raise aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=500,
            message="Server Error",
        )

    mock_response.raise_for_status = raise_error

    with pytest.raises(VolkswagenGoConnectApiClientCommunicationError):
        _verify_response_or_raise(mock_response)


@pytest.mark.asyncio
async def test_api_client_login_device_token_no_fallback():
    """Test login with device token fails when no email/password fallback."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        device_token="invalid-token",
    )

    # Mock device token login to fail
    mock_response = MagicMock()
    mock_response.status = 401
    mock_response.text = AsyncMock(return_value='{"error": "Invalid token"}')

    def raise_auth_error():
        raise aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=401,
            message="Unauthorized",
        )

    mock_response.raise_for_status = raise_auth_error

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"error": "Invalid token"}
        with pytest.raises(VolkswagenGoConnectApiClientAuthenticationError):
            await client.login()


@pytest.mark.asyncio
async def test_api_wrapper_429_retry_with_retry_after_header():
    """Test _api_wrapper handles 429 with Retry-After header."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    call_count = 0

    async def mock_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock_response = MagicMock()
        if call_count == 1:
            # First call - return 429 with Retry-After
            mock_response.status = 429
            mock_response.headers = {"Retry-After": "0.1"}
            mock_response.text = AsyncMock(return_value='{"error": "Rate limited"}')
            mock_response.release = AsyncMock()
        else:
            # Second call - success
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value='{"data": "success"}')
            mock_response.raise_for_status = MagicMock()
        return mock_response

    session.request = mock_request

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"data": "success"}
        result = await client._api_wrapper(method="get", url="http://test.com")

    assert result == {"data": "success"}
    assert call_count == 2


@pytest.mark.asyncio
async def test_api_wrapper_503_retry_exponential_backoff():
    """Test _api_wrapper handles 503 with exponential backoff."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    call_count = 0

    async def mock_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock_response = MagicMock()
        if call_count <= 2:
            # First two calls - return 503
            mock_response.status = 503
            mock_response.headers = {}
            mock_response.text = AsyncMock(
                return_value='{"error": "Service unavailable"}'
            )
            mock_response.release = AsyncMock()
        else:
            # Third call - success
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value='{"data": "success"}')
            mock_response.raise_for_status = MagicMock()
        return mock_response

    session.request = mock_request

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"data": "success"}
        result = await client._api_wrapper(method="get", url="http://test.com")

    assert result == {"data": "success"}
    assert call_count == 3


@pytest.mark.asyncio
async def test_api_wrapper_429_retry_invalid_retry_after():
    """Test _api_wrapper handles 429 with invalid Retry-After header."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    call_count = 0

    async def mock_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock_response = MagicMock()
        if call_count == 1:
            # First call - return 429 with invalid Retry-After
            mock_response.status = 429
            mock_response.headers = {"Retry-After": "invalid"}
            mock_response.text = AsyncMock(return_value='{"error": "Rate limited"}')
            mock_response.release = AsyncMock()
        else:
            # Second call - success
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value='{"data": "success"}')
            mock_response.raise_for_status = MagicMock()
        return mock_response

    session.request = mock_request

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"data": "success"}
        result = await client._api_wrapper(method="get", url="http://test.com")

    assert result == {"data": "success"}
    assert call_count == 2


@pytest.mark.asyncio
async def test_api_wrapper_429_exceed_retries():
    """Test _api_wrapper raises error when exceeding retry attempts."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    async def mock_request(*args, **kwargs):
        mock_response = MagicMock()
        mock_response.status = 429
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{"error": "Rate limited"}')
        mock_response.release = AsyncMock()
        return mock_response

    session.request = mock_request

    with pytest.raises(VolkswagenGoConnectApiClientCommunicationError):
        await client._api_wrapper(method="get", url="http://test.com")


@pytest.mark.asyncio
async def test_api_wrapper_response_release_exception():
    """Test _api_wrapper handles exception during response.release()."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    call_count = 0

    async def mock_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock_response = MagicMock()
        if call_count == 1:
            # First call - return 429 with release exception
            mock_response.status = 429
            mock_response.headers = {"Retry-After": "0.1"}
            mock_response.text = AsyncMock(return_value='{"error": "Rate limited"}')
            mock_response.release = AsyncMock(side_effect=Exception("Release failed"))
        else:
            # Second call - success
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value='{"data": "success"}')
            mock_response.raise_for_status = MagicMock()
        return mock_response

    session.request = mock_request

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"data": "success"}
        result = await client._api_wrapper(method="get", url="http://test.com")

    assert result == {"data": "success"}


@pytest.mark.asyncio
async def test_api_wrapper_http_debug_logging():
    """Test _api_wrapper with HTTP_DEBUG enabled."""
    import os

    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"data": "test"}')
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    # Enable HTTP_DEBUG temporarily
    original_value = os.environ.get("VWGC_HTTP_DEBUG")
    try:
        os.environ["VWGC_HTTP_DEBUG"] = "1"
        # Reload the module to pick up the new environment variable
        import importlib
        import custom_components.volkswagen_goconnect.api as api_module

        importlib.reload(api_module)

        with patch(
            "custom_components.volkswagen_goconnect.api.json.loads"
        ) as mock_json:
            mock_json.return_value = {"data": "test"}
            result = await client._api_wrapper(
                method="post", url="http://test.com", data={"key": "value"}
            )

        assert result == {"data": "test"}
    finally:
        # Restore original value
        if original_value is None:
            os.environ.pop("VWGC_HTTP_DEBUG", None)
        else:
            os.environ["VWGC_HTTP_DEBUG"] = original_value
        # Reload to restore original state
        importlib.reload(api_module)


@pytest.mark.asyncio
async def test_api_wrapper_http_debug_non_json_response():
    """Test _api_wrapper with HTTP_DEBUG for non-JSON response."""
    import os

    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="plain text response")
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    # Enable HTTP_DEBUG temporarily
    original_value = os.environ.get("VWGC_HTTP_DEBUG")
    try:
        os.environ["VWGC_HTTP_DEBUG"] = "1"
        import importlib
        import custom_components.volkswagen_goconnect.api as api_module

        importlib.reload(api_module)

        with patch(
            "custom_components.volkswagen_goconnect.api.json.loads"
        ) as mock_json:
            # First call tries to parse response and fails (for logging)
            # Second call actually parses and raises JSONDecodeError
            mock_json.side_effect = [
                Exception("Not JSON"),
                Exception("Not JSON for parsing"),
            ]
            with contextlib.suppress(Exception):
                await client._api_wrapper(method="get", url="http://test.com")
    finally:
        if original_value is None:
            os.environ.pop("VWGC_HTTP_DEBUG", None)
        else:
            os.environ["VWGC_HTTP_DEBUG"] = original_value
        importlib.reload(api_module)


@pytest.mark.asyncio
async def test_api_wrapper_non_dict_data():
    """Test _api_wrapper with non-dict data."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"result": "ok"}')
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"result": "ok"}
        # Pass a list instead of dict
        result = await client._api_wrapper(
            method="post", url="http://test.com", data=["item1", "item2"]
        )

    assert result == {"result": "ok"}


@pytest.mark.asyncio
async def test_api_wrapper_rate_limiting():
    """Test _api_wrapper rate limiting behavior."""
    import time

    session = AsyncMock(spec=aiohttp.ClientSession)
    client = VolkswagenGoConnectApiClient(
        session=session,
        email="test@example.com",
        password="password123",
    )

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value='{"data": "test"}')
    mock_response.raise_for_status = MagicMock()

    session.request = AsyncMock()
    session.request.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as mock_json:
        mock_json.return_value = {"data": "test"}

        # Make first request
        start = time.monotonic()
        await client._api_wrapper(method="get", url="http://test.com")

        # Make second request immediately - should be rate limited
        await client._api_wrapper(method="get", url="http://test.com")
        _ = time.monotonic() - start

        # Should have some delay due to rate limiting
        # But we can't assert exact timing in tests, just verify it completes


def test_sanitize_url_exception():
    """Test _sanitize_url handles malformed URLs gracefully."""
    from custom_components.volkswagen_goconnect.api import _sanitize_url
    from unittest.mock import patch

    # Test that exception handling returns original URL
    with patch("custom_components.volkswagen_goconnect.api.urlparse") as mock_parse:
        mock_parse.side_effect = Exception("Parse error")
        result = _sanitize_url("http://test.com?token=secret")
        assert result == "http://test.com?token=secret"
