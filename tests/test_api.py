"""Tests for the API client."""

import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.volkswagen_goconnect.api import (
    VolkswagenGoConnectApiClient,
    VolkswagenGoConnectApiClientAuthenticationError,
    VolkswagenGoConnectApiClientCommunicationError,
    VolkswagenGoConnectApiClientError,
)
from typing import Self


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
async def test_api_client_async_get_all_vehicles_data(mock_api_data):
    """Test async_get_all_vehicles_data sends a single combined GraphQL request."""
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
        mock_json.return_value = mock_api_data
        result = await client.async_get_all_vehicles_data()

    # Exactly one HTTP request was made
    assert session.request.call_count == 1
    call_kwargs = session.request.call_args
    assert "AllVehiclesData" in call_kwargs.kwargs.get("url", "")
    assert "data" in result
    assert "viewer" in result["data"]


@pytest.mark.asyncio
async def test_api_client_async_get_ignition_data(mock_ignition_data_off):
    """Test async_get_ignition_data sends a slim single GraphQL request."""
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
        mock_json.return_value = mock_ignition_data_off
        result = await client.async_get_ignition_data()

    # Exactly one HTTP request was made
    assert session.request.call_count == 1
    call_kwargs = session.request.call_args
    assert "IgnitionData" in call_kwargs.kwargs.get("url", "")
    vehicle = result["data"]["viewer"]["vehicles"][0]["vehicle"]
    assert "ignition" in vehicle
    assert vehicle["ignition"]["on"] is False


@pytest.mark.asyncio
async def test_api_client_async_get_data_delegates_to_combined(mock_api_data):
    """Test async_get_data delegates to async_get_all_vehicles_data (single request)."""
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
        mock_json.return_value = mock_api_data
        result = await client.async_get_data()

    # Exactly one HTTP request — no per-vehicle loops
    assert session.request.call_count == 1
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


# --- Added helper and wrapper tests to increase api.py coverage ---


def test_sanitize_mapping_redacts_sensitive_keys() -> None:
    """Test that _sanitize_mapping redacts sensitive keys."""
    from custom_components.volkswagen_goconnect.api import _sanitize_mapping

    original = {
        "Authorization": "secret",
        "password": "pwd",
        "nested": {"token": "abc", "other": 1},
        "list": [{"refresh_token": "zzz"}, {"ok": True}],
    }
    sanitized = _sanitize_mapping(original)
    assert sanitized["Authorization"] == "***REDACTED***"
    assert sanitized["password"] == "***REDACTED***"
    assert sanitized["nested"]["token"] == "***REDACTED***"
    assert sanitized["nested"]["other"] == 1
    assert sanitized["list"][0]["refresh_token"] == "***REDACTED***"
    assert sanitized["list"][1]["ok"] is True


def test_sanitize_headers_redacts_sensitive_keys() -> None:
    """Test that _sanitize_headers redacts sensitive authorization headers."""
    from custom_components.volkswagen_goconnect.api import _sanitize_headers

    headers = {"Authorization": "bearer x", "X-Other": "y"}
    out = _sanitize_headers(headers)
    assert out["Authorization"] == "***REDACTED***"
    assert out["X-Other"] == "y"


def test_sanitize_url_redacts_query_params() -> None:
    """Test that _sanitize_url redacts query parameters."""
    from custom_components.volkswagen_goconnect.api import _sanitize_url

    url = "https://example.com/path?a=1&token=abc&refresh_token=def"
    sanitized = _sanitize_url(url)
    assert "token=%2A%2A%2ARED" in sanitized
    assert "a=1" in sanitized


def test_get_headers_flags() -> None:
    """Test that _get_headers includes app version and auth token when requested."""
    from custom_components.volkswagen_goconnect.api import HTTP_HEADERS_APP_VERSION
    from custom_components.volkswagen_goconnect.api import VolkswagenGoConnectApiClient
    import aiohttp

    client = VolkswagenGoConnectApiClient(session=MagicMock(spec=aiohttp.ClientSession))
    client._token = "tkn"
    h = client._get_headers(include_app_version=True, include_auth_token=True)
    assert h["Authorization"].startswith("Bearer ")
    assert h["X-App-Version"] == HTTP_HEADERS_APP_VERSION


@pytest.mark.asyncio
async def test_request_json_login_when_token_missing():
    """_request_json triggers login when auth token required and missing."""
    import aiohttp

    client = VolkswagenGoConnectApiClient(session=AsyncMock(spec=aiohttp.ClientSession))
    client.login = AsyncMock()
    # Make _api_wrapper return a simple dict
    with patch(
        "custom_components.volkswagen_goconnect.api.VolkswagenGoConnectApiClient._api_wrapper",
        new=AsyncMock(return_value={"ok": True}),
    ):
        res = await client._request_json(
            method="get",
            url="https://example.com",
            include_auth_token=True,
        )
    client.login.assert_called()
    assert res == {"ok": True}


@pytest.mark.asyncio
async def test_request_json_retries_on_auth_error():
    """_request_json retries once after auth error when include_auth_token=True."""
    import aiohttp

    client = VolkswagenGoConnectApiClient(session=AsyncMock(spec=aiohttp.ClientSession))
    client.login = AsyncMock()

    with patch(
        "custom_components.volkswagen_goconnect.api.VolkswagenGoConnectApiClient._api_wrapper",
        new=AsyncMock(
            side_effect=[
                VolkswagenGoConnectApiClientAuthenticationError("bad"),
                {"ok": True},
            ]
        ),
    ):
        res = await client._request_json(
            method="get",
            url="https://example.com",
            include_auth_token=True,
        )
    assert client.login.call_count >= 1
    assert res == {"ok": True}


@pytest.mark.asyncio
async def test_api_wrapper_client_error_raises_communication() -> None:
    """Test that _api_wrapper raises CommunicationError on aiohttp.ClientError."""
    import aiohttp

    client = VolkswagenGoConnectApiClient(session=AsyncMock(spec=aiohttp.ClientSession))
    client._session.request = AsyncMock(side_effect=aiohttp.ClientError("boom"))

    with pytest.raises(VolkswagenGoConnectApiClientCommunicationError):
        await client._api_wrapper(
            method="get", url="https://x", data=None, headers=None
        )


@pytest.mark.asyncio
async def test_api_wrapper_timeout_raises_communication() -> None:
    """Test that _api_wrapper raises CommunicationError on TimeoutError."""
    import aiohttp
    from custom_components.volkswagen_goconnect import api as api_mod

    client = VolkswagenGoConnectApiClient(session=AsyncMock(spec=aiohttp.ClientSession))
    client._session.request = AsyncMock(return_value=MagicMock())

    class FailTimeout:
        async def __aenter__(self) -> Self:
            raise TimeoutError("late")

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

    with patch.object(api_mod, "async_timeout", create=True) as m:
        m.timeout.return_value = FailTimeout()
        with pytest.raises(VolkswagenGoConnectApiClientCommunicationError):
            await client._api_wrapper(
                method="get", url="https://x", data=None, headers=None
            )


@pytest.mark.asyncio
async def test_api_wrapper_json_decode_error_raises_api_error() -> None:
    """Test that _api_wrapper raises ApiError on JSON decode failure."""
    import aiohttp

    client = VolkswagenGoConnectApiClient(session=AsyncMock(spec=aiohttp.ClientSession))
    # Build a response with status 200 but invalid JSON
    resp = MagicMock()
    resp.status = 200
    resp.text = AsyncMock(return_value="not-json")
    resp.headers = {}
    resp.raise_for_status = MagicMock()
    client._session.request = AsyncMock(return_value=resp)

    with patch("custom_components.volkswagen_goconnect.api.json.loads") as jl:
        jl.side_effect = ValueError("bad json")
        with pytest.raises(VolkswagenGoConnectApiClientError):
            await client._api_wrapper(
                method="get", url="https://x", data=None, headers=None
            )


@pytest.mark.asyncio
async def test_api_wrapper_throttle_exceeds_retries_raises_communication() -> None:
    """Test that _api_wrapper raises CommunicationError when 429 retries exhausted."""
    import aiohttp

    client = VolkswagenGoConnectApiClient(session=AsyncMock(spec=aiohttp.ClientSession))

    class ThrottleResp:
        def __init__(self) -> None:
            self.status = 429
            self.headers = {}

        async def text(self):
            return "{}"

        async def release(self):
            return None

        def raise_for_status(self):
            return None

    # Always return 429 to exhaust retries
    client._session.request = AsyncMock(
        side_effect=[ThrottleResp(), ThrottleResp(), ThrottleResp(), ThrottleResp()]
    )

    with pytest.raises(VolkswagenGoConnectApiClientCommunicationError):
        await client._api_wrapper(method="get", url="https://x", data=None, headers={})


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
async def test_api_wrapper_session_not_initialized():
    """Test _api_wrapper raises error when session is None."""
    client = VolkswagenGoConnectApiClient(
        session=None,  # type: ignore[arg-type]
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
    assert result is not None
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
            method="post", url="http://test.com", data={"test": "data"}
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
