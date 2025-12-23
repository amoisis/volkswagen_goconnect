"""API Client for Volkswagen GoConnect."""

from __future__ import annotations

import json
import logging
import socket
from typing import Any

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
        if self._token is None:
            await self.login()

        url = REGISTER_DEVICE_URL
        data = {"deviceName": "Home-Assistant", "deviceModel": "Home-Assistant"}

        return await self._api_wrapper(
            method="post",
            url=url,
            data=data,
            headers=self._get_headers(
                include_app_version=True, include_auth_token=True
            ),
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

    async def get_vehicles(self) -> dict:
        """Get vehicles."""
        if self._token is None:
            await self.login()

        query = {
            "operationName": "VehiclesType",
            "variables": {},
            "query": QUERY_API_VEHICLETYPE,
        }

        try:
            return await self._api_wrapper(
                method="post",
                url=BASE_URL_API + "?operationName=VehiclesType",
                data=query,
                headers=self._get_headers(
                    include_app_version=True, include_auth_token=True
                ),
            )
        except VolkswagenGoConnectApiClientAuthenticationError:
            # Token might be expired, try to login again
            await self.login()
            return await self._api_wrapper(
                method="post",
                url=BASE_URL_API + "?operationName=VehiclesType",
                data=query,
                headers=self._get_headers(
                    include_app_version=True, include_auth_token=True
                ),
            )

    async def get_vehicle_details(self, vehicle_id: str) -> dict:
        """Get vehicle details."""
        if self._token is None:
            await self.login()

        query = {
            "operationName": "Vehicle",
            "variables": {"id": vehicle_id},
            "query": QUERY_VEHICLE_DETAILS,
        }

        return await self._api_wrapper(
            method="post",
            url=BASE_URL_API + "?operationName=Vehicle&screenName=Overview",
            data=query,
            headers=self._get_headers(
                include_app_version=True, include_auth_token=True
            ),
        )

    async def get_vehicle_system_overview(self, vehicle_id: str) -> dict:
        """Get vehicle system overview."""
        if self._token is None:
            await self.login()

        query = {
            "operationName": "VehicleSystemOverview",
            "variables": {"id": vehicle_id, "statuses": ["open"]},
            "query": QUERY_VEHICLE_SYSTEM_OVERVIEW,
        }

        return await self._api_wrapper(
            method="post",
            url=BASE_URL_API
            + "?operationName=VehicleSystemOverview&screenName=Overview",
            data=query,
            headers=self._get_headers(
                include_app_version=True, include_auth_token=True
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

    async def _api_wrapper(
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
            async with async_timeout.timeout(10):
                _LOGGER.debug("Method: %s", method)
                _LOGGER.debug("URL: %s", url)
                _LOGGER.debug("Headers: %s", headers)
                redacted_data = None
                if isinstance(data, dict):
                    redacted_data = data.copy()
                    for key in ("password", "deviceToken"):
                        if key in redacted_data:
                            redacted_data[key] = "***REDACTED***"
                else:
                    redacted_data = data
                _LOGGER.debug("Data: %s", redacted_data)

                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )

                text = await response.text()
                _LOGGER.debug("Response Status: %s", response.status)
                _LOGGER.debug("Response Body: %s", text)

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
