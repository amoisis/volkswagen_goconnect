"""API Client for Volkswagen GoConnect."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import socket
import time
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import aiohttp
import async_timeout

from .const import (
    AUTH_TOKEN_URL,
    AUTH_URL,
    BASE_URL_API,
    HTTP_HEADERS_APP_VERSION,
    HTTP_HEADERS_ORGANIZATION_NAMESPACE,
    HTTP_HEADERS_USER_AGENT,
    QUERY_API_VEHICLETYPE,
    QUERY_VEHICLE_DETAILS,
    QUERY_VEHICLE_SYSTEM_OVERVIEW,
    REGISTER_DEVICE_URL,
)

_LOGGER = logging.getLogger(__name__)

# Toggle verbose HTTP debug logging (sanitized). Set VWGC_HTTP_DEBUG=1 to enable.
HTTP_DEBUG = os.getenv("VWGC_HTTP_DEBUG", "").lower() in {"1", "true", "yes", "on"}

# Single source of truth for request timeout (seconds)
REQUEST_TIMEOUT_SECONDS = 10

# Client-side throttling and backoff settings
MIN_REQUEST_INTERVAL_SECONDS = 0.2  # ensure spacing between requests
THROTTLE_MAX_RETRIES = 3  # retries on 429/503
THROTTLE_BASE_DELAY_SECONDS = 1.0  # base backoff when no Retry-After

SENSITIVE_KEYS = {
    "authorization",
    "password",
    "deviceToken",
    "token",
    "access_token",
    "refresh_token",
    "id_token",
    "client_secret",
    "secret",
    "cookie",
    "set-cookie",
}


def _redacted() -> str:
    return "***REDACTED***"


def _sanitize_mapping(obj: Any) -> Any:
    """Recursively sanitize mappings by redacting sensitive keys."""
    if isinstance(obj, dict):
        return {
            k: (
                _redacted()
                if str(k).lower() in SENSITIVE_KEYS
                else _sanitize_mapping(v)
            )
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_sanitize_mapping(v) for v in obj]
    return obj


def _sanitize_headers(headers: dict | None) -> dict | None:
    if not headers:
        return headers
    sanitized = {}
    for k, v in headers.items():
        if str(k).lower() in SENSITIVE_KEYS:
            sanitized[k] = _redacted()
        else:
            sanitized[k] = v
    return sanitized


def _sanitize_url(url: str) -> str:
    try:
        parts = urlparse(url)
        q = []
        for k, v in parse_qsl(parts.query, keep_blank_values=True):
            if k.lower() in SENSITIVE_KEYS:
                q.append((k, _redacted()))
            else:
                q.append((k, v))
        return urlunparse(parts._replace(query=urlencode(q)))
    except Exception:  # noqa: BLE001
        return url


class VolkswagenGoConnectApiClientError(Exception):
    """Exception to indicate a general API error."""


class VolkswagenGoConnectApiClientCommunicationError(
    VolkswagenGoConnectApiClientError,
):
    """Exception to indicate a communication error."""


class VolkswagenGoConnectApiClientAuthenticationError(
    VolkswagenGoConnectApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise VolkswagenGoConnectApiClientAuthenticationError(
            msg,
        )
    try:
        response.raise_for_status()
    except aiohttp.ClientResponseError as err:
        raise VolkswagenGoConnectApiClientCommunicationError from err


class VolkswagenGoConnectApiClient:
    """API Client for Volkswagen GoConnect."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str | None = None,
        password: str | None = None,
        device_token: str | None = None,
    ) -> None:
        """Initialize the API Client for Volkswagen GoConnect."""
        self._email = email
        self._password = password
        self._session = session
        self._device_token = device_token
        self._token: str | None = None
        # Throttling state
        self._rate_lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def login(self) -> None:
        """Login to the API."""
        if self._device_token:
            try:
                await self._login_with_device_token()
            except VolkswagenGoConnectApiClientAuthenticationError:
                if not self._email or not self._password:
                    raise
            else:
                return

        if self._email and self._password:
            await self._login_with_email_password()
        else:
            msg = "No credentials provided"
            raise VolkswagenGoConnectApiClientAuthenticationError(msg)

    async def _login_with_email_password(self) -> None:
        """Login with email and password."""
        response = await self._api_wrapper(
            method="post",
            url=AUTH_URL,
            data={"email": self._email, "password": self._password},
            headers=self._get_headers(),
        )
        if not response or "token" not in response:
            msg = "Missing token in response"
            raise VolkswagenGoConnectApiClientAuthenticationError(msg)
        self._token = response["token"]

    async def _login_with_device_token(self) -> None:
        """Login with device token."""
        response = await self._api_wrapper(
            method="post",
            url=f"{AUTH_TOKEN_URL}?expiresIn=3600",
            data={"deviceToken": self._device_token},
            headers=self._get_headers(),
        )
        if not response or "token" not in response:
            msg = "Missing token in response"
            raise VolkswagenGoConnectApiClientAuthenticationError(msg)
        self._token = response["token"]

    async def register_device(self) -> dict:
        """Register the device."""
        return await self._request_json(
            method="post",
            url=REGISTER_DEVICE_URL,
            data={"deviceName": "Home-Assistant", "deviceModel": "Home-Assistant"},
            include_app_version=True,
            include_auth_token=True,
        )

    async def async_get_data(self) -> dict:
        """Get data from the API."""
        # First get the list of vehicles
        vehicles_response = await self.get_vehicles()

        vehicles_data = (
            vehicles_response.get("data", {}).get("viewer", {}).get("vehicles", [])
        )

        detailed_vehicles = []
        for vehicle_entry in vehicles_data:
            vehicle = vehicle_entry.get("vehicle")
            if not vehicle or "id" not in vehicle:
                continue

            vehicle_id = vehicle["id"]
            try:
                # Fetch details for each vehicle
                details = await self.get_vehicle_details(vehicle_id)
                system_overview = await self.get_vehicle_system_overview(vehicle_id)

                if details and "data" in details and "vehicle" in details["data"]:
                    vehicle_data = details["data"]["vehicle"]

                    # Merge system overview data
                    if (
                        system_overview
                        and "data" in system_overview
                        and "vehicle" in system_overview["data"]
                    ):
                        system_data = system_overview["data"]["vehicle"]
                        # Deep merge: only update top-level keys that don't
                        # have nested objects or update nested objects without
                        # overwriting complete data with partial data
                        for key, value in system_data.items():
                            # Skip updating keys that are complex objects from details
                            # to avoid overwriting complete data with partial data
                            if key not in [
                                "brandContactInfo",
                            ]:
                                vehicle_data[key] = value

                    detailed_vehicles.append({"vehicle": vehicle_data})
                else:
                    # Fallback or just append original if detail fetch fails?
                    # Let's append original but warn? Or just skip?
                    # For now, let's keep the original entry if detail fetch fails,
                    # but maybe it's better to just skip to avoid inconsistencies.
                    # Or we can just log error.
                    _LOGGER.warning("Failed to get details for vehicle %s", vehicle_id)
                    detailed_vehicles.append(vehicle_entry)

            except Exception:
                _LOGGER.exception("Error fetching details for vehicle %s", vehicle_id)
                detailed_vehicles.append(vehicle_entry)

        # Construct a response structure similar to the original one
        return {"data": {"viewer": {"vehicles": detailed_vehicles}}}

    # No metadata caching: GraphQL selection sets are already efficient.

    async def get_vehicles(self) -> dict:
        """Get vehicles."""
        query = {
            "operationName": "VehiclesType",
            "variables": {},
            "query": QUERY_API_VEHICLETYPE,
        }
        return await self._request_json(
            method="post",
            url=BASE_URL_API + "?operationName=VehiclesType",
            data=query,
            include_app_version=True,
            include_auth_token=True,
        )

    async def get_vehicle_details(self, vehicle_id: str) -> dict:
        """Get vehicle details."""
        query = {
            "operationName": "Vehicle",
            "variables": {"id": vehicle_id},
            "query": QUERY_VEHICLE_DETAILS,
        }
        return await self._request_json(
            method="post",
            url=BASE_URL_API + "?operationName=Vehicle&screenName=Overview",
            data=query,
            include_app_version=True,
            include_auth_token=True,
        )

    async def get_vehicle_system_overview(self, vehicle_id: str) -> dict:
        """Get vehicle system overview."""
        query = {
            "operationName": "VehicleSystemOverview",
            "variables": {"id": vehicle_id, "statuses": ["open"]},
            "query": QUERY_VEHICLE_SYSTEM_OVERVIEW,
        }
        return await self._request_json(
            method="post",
            url=BASE_URL_API
            + "?operationName=VehicleSystemOverview&screenName=Overview",
            data=query,
            include_app_version=True,
            include_auth_token=True,
        )

    async def _request_json(
        self,
        *,
        method: str,
        url: str,
        data: dict | None = None,
        include_app_version: bool = False,
        include_auth_token: bool = False,
    ) -> Any:
        """
        Call API and transparently retry once on auth error.

        - Ensures login when auth is required and token is missing.
        - Rebuilds headers on retry so refreshed token is used.
        """
        if include_auth_token and self._token is None:
            await self.login()

        headers = self._get_headers(
            include_app_version=include_app_version,
            include_auth_token=include_auth_token,
        )
        try:
            return await self._api_wrapper(
                method=method,
                url=url,
                data=data,
                headers=headers,
            )
        except VolkswagenGoConnectApiClientAuthenticationError:
            if not include_auth_token:
                # No auth expected; bubble up
                raise
            # Refresh and retry once
            await self.login()
            return await self._api_wrapper(
                method=method,
                url=url,
                data=data,
                headers=self._get_headers(
                    include_app_version=include_app_version,
                    include_auth_token=include_auth_token,
                ),
            )

    def _get_headers(
        self, *, include_app_version: bool = False, include_auth_token: bool = False
    ) -> dict:
        """Get headers for the request."""
        headers = {
            "User-Agent": f"{HTTP_HEADERS_USER_AGENT}",
            "X-Organization-Namespace": f"{HTTP_HEADERS_ORGANIZATION_NAMESPACE}",
        }

        if include_auth_token:
            headers["Authorization"] = f"Bearer {self._token}"
        if include_app_version:
            headers["X-App-Version"] = HTTP_HEADERS_APP_VERSION
        return headers

    async def _api_wrapper(  # noqa: PLR0912, PLR0915
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        if self._session is None:
            msg = "Session not initialized"
            raise VolkswagenGoConnectApiClientCommunicationError(msg)
        try:
            attempt = 0
            while True:
                # Basic rate limiting: ensure minimal spacing between requests
                now = time.monotonic()
                async with self._rate_lock:
                    elapsed = now - self._last_request_at
                    if elapsed < MIN_REQUEST_INTERVAL_SECONDS:
                        to_sleep = MIN_REQUEST_INTERVAL_SECONDS - elapsed
                    else:
                        to_sleep = 0.0
                    if to_sleep > 0:
                        await asyncio.sleep(to_sleep)
                    self._last_request_at = time.monotonic()

                async with async_timeout.timeout(REQUEST_TIMEOUT_SECONDS):
                    _LOGGER.debug("Method: %s", method)
                    _LOGGER.debug("URL: %s", _sanitize_url(url))
                    _LOGGER.debug("Headers: %s", _sanitize_headers(headers))

                    if isinstance(data, dict):
                        if HTTP_DEBUG:
                            _LOGGER.debug("Data: %s", _sanitize_mapping(data))
                        else:
                            sanitized_keys = [
                                _redacted() if str(k).lower() in SENSITIVE_KEYS else k
                                for k in data.keys()
                            ]
                            _LOGGER.debug("Request data keys: %s", sanitized_keys)
                    elif data is not None:
                        _LOGGER.debug("Request has non-dict JSON body")

                    response = await self._session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=data,
                    )

                    # Handle throttling responses (429) and transient 503
                    if response.status in (429, 503):
                        retry_after = response.headers.get("Retry-After")
                        delay = None
                        if retry_after:
                            try:
                                delay = float(retry_after)
                            except ValueError:
                                delay = None
                        if delay is None:
                            delay = THROTTLE_BASE_DELAY_SECONDS * (2**attempt)
                        _LOGGER.warning(
                            "Received %s, backing off for %.2fs (attempt %d)",
                            response.status,
                            delay,
                            attempt + 1,
                        )
                        # consume body to release connection
                        with contextlib.suppress(Exception):
                            await response.release()
                        if attempt >= THROTTLE_MAX_RETRIES:
                            msg = (
                                f"Exceeded retry attempts after "
                                f"status {response.status}"
                            )
                            raise VolkswagenGoConnectApiClientCommunicationError(  # noqa: TRY301
                                msg
                            )
                        attempt += 1
                        await asyncio.sleep(delay)
                        continue

                    text = await response.text()
                    _LOGGER.debug("Response Status: %s", response.status)
                    if HTTP_DEBUG:
                        try:
                            _LOGGER.debug(
                                "Response Body: %s", _sanitize_mapping(json.loads(text))
                            )
                        except Exception:  # noqa: BLE001
                            # Fallback to truncated raw text when not JSON
                            _LOGGER.debug("Response Body (raw): %.200s", text)
                    else:
                        _LOGGER.debug(
                            "Response body omitted (set VWGC_HTTP_DEBUG=1 to log)"
                        )

                    _verify_response_or_raise(response)

                    try:
                        return json.loads(text)
                    except json.JSONDecodeError as exc:
                        _LOGGER.exception("Failed to decode json")
                        raise VolkswagenGoConnectApiClientError from exc

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise VolkswagenGoConnectApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise VolkswagenGoConnectApiClientCommunicationError(
                msg,
            ) from exception
        except VolkswagenGoConnectApiClientError:
            raise
        except Exception as exception:
            msg = f"Something really wrong happened! - {exception}"
            raise VolkswagenGoConnectApiClientError(
                msg,
            ) from exception
