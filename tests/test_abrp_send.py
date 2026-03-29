"""Tests for ABRP telemetry send service."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Self
from unittest.mock import MagicMock

import aiohttp
import pytest
from homeassistant.exceptions import HomeAssistantError
from yarl import URL

from custom_components.volkswagen_goconnect.service_actions import abrp_send


class _MockResponse:
    """Mock aiohttp response object."""

    def __init__(self, status: int, text: str = "") -> None:
        self.status = status
        self._text = text

    async def text(self) -> str:
        """Return mocked body text."""
        return self._text


class _MockPostContext:
    """Async context manager for session.post()."""

    def __init__(
        self,
        response: _MockResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self._response = response
        self._error = error

    async def __aenter__(self) -> _MockResponse:
        """Return response or raise configured error."""
        if self._error is not None:
            raise self._error
        assert self._response is not None
        return self._response

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        """Do not suppress exceptions."""
        return False


class _MockClientSession:
    """Mock aiohttp client session used by ABRP sender."""

    def __init__(
        self,
        response: _MockResponse | None = None,
        post_error: Exception | None = None,
    ) -> None:
        self.response = response
        self.post_error = post_error
        self.calls: list[tuple[str, dict | None, None]] = []

    async def __aenter__(self) -> Self:
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        """Do not suppress exceptions."""
        return False

    def post(
        self,
        url: str,
        headers: dict | None = None,
        data: None = None,
    ) -> _MockPostContext:
        """Capture post call and return an async post context manager."""
        self.calls.append((url, headers, data))
        return _MockPostContext(response=self.response, error=self.post_error)


@pytest.fixture
def abrp_vehicle_payload() -> dict:
    """Return a minimal vehicle payload with ABRP telemetry fields."""
    return {
        "data": {
            "viewer": {
                "vehicles": [
                    {
                        "vehicle": {
                            "id": "vehicle-1",
                            "licensePlate": "FWG28Q",
                            "chargePercentage": {"pct": 80},
                            "position": {"latitude": -35.2, "longitude": 149.0},
                            "isCharging": False,
                            "odometer": {"odometer": 12345},
                            "rangeTotalKm": {"km": 420},
                            "speedometers": [{"speed": 82}],
                            "outdoorTemperatures": [{"celsius": 23}],
                            "highVoltageBatteryUsableCapacityKwh": {"kwh": 60},
                            "highVoltageBatteryTemperature": {"celsius": 31},
                        }
                    }
                ]
            }
        }
    }


def test_get_latest_list_item_handles_shapes() -> None:
    """Validate latest-item extraction from list fields."""
    assert abrp_send._get_latest_list_item({}, "speedometers") is None
    assert abrp_send._get_latest_list_item({"speedometers": []}, "speedometers") is None
    assert (
        abrp_send._get_latest_list_item(
            {"speedometers": ["not-a-dict"]},
            "speedometers",
        )
        is None
    )

    result = abrp_send._get_latest_list_item(
        {"speedometers": [{"speed": 12}, {"speed": 10}]}, "speedometers"
    )
    assert result == {"speed": 12}


def test_get_vehicle_data_by_license_plate_case_insensitive(
    abrp_vehicle_payload: dict,
) -> None:
    """Ensure plate matching ignores case and surrounding whitespace."""
    vehicle = abrp_send._get_vehicle_data_by_license_plate(
        abrp_vehicle_payload,
        "  fwg28q ",
    )
    assert vehicle["id"] == "vehicle-1"


def test_build_live_mapping_computes_capacity(abrp_vehicle_payload: dict) -> None:
    """Build mapping and verify derived capacity and field extraction."""
    vehicle = abrp_vehicle_payload["data"]["viewer"]["vehicles"][0]["vehicle"]
    mapping = abrp_send._build_live_mapping(vehicle)

    assert mapping["soc"] == 80
    assert mapping["lat"] == -35.2
    assert mapping["lon"] == 149.0
    assert mapping["speed"] == 82
    assert mapping["ext_temp"] == 23
    assert mapping["capacity"] == 75.0


def test_get_vehicle_data_from_entries_prefers_abrp_coordinator(
    abrp_vehicle_payload: dict,
    hass,
) -> None:
    """Use ABRP coordinator data before falling back to main coordinator."""
    abrp_data = abrp_vehicle_payload
    coordinator_data = {
        "data": {
            "viewer": {
                "vehicles": [
                    {
                        "vehicle": {
                            "id": "vehicle-1",
                            "licensePlate": "FWG28Q",
                            "position": None,
                        }
                    }
                ]
            }
        }
    }

    entry = MagicMock()
    entry.runtime_data = SimpleNamespace(
        abrp_coordinator=SimpleNamespace(data=abrp_data),
        coordinator=SimpleNamespace(data=coordinator_data),
    )
    hass.config_entries.async_entries.return_value = [entry]

    vehicle = abrp_send._get_vehicle_data_from_entries(hass, "FWG28Q")
    assert vehicle.get("position") == {"latitude": -35.2, "longitude": 149.0}


@pytest.mark.asyncio
async def test_async_abrp_send_service_success(
    abrp_vehicle_payload: dict,
    hass,
    monkeypatch,
) -> None:
    """Send telemetry successfully and verify request payload/query params."""
    entry = MagicMock()
    entry.runtime_data = SimpleNamespace(
        abrp_coordinator=SimpleNamespace(data=abrp_vehicle_payload),
        coordinator=SimpleNamespace(data=None),
    )
    hass.config_entries.async_entries.return_value = [entry]

    mock_session = _MockClientSession(response=_MockResponse(status=200))
    monkeypatch.setattr(
        abrp_send.aiohttp,
        "ClientSession",
        lambda: mock_session,
    )

    await abrp_send.async_abrp_send_service(
        hass=hass,
        api_key="api-key",
        token="token-123",
        license_plate="FWG28Q",
    )

    assert len(mock_session.calls) == 1
    called_url, headers, data = mock_session.calls[0]
    assert headers == {"Authorization": "APIKEY api-key"}
    assert data is None

    parsed = URL(called_url)
    assert parsed.query["token"] == "token-123"
    tlm = json.loads(parsed.query["tlm"])
    assert tlm["soc"] == 80
    assert tlm["lat"] == -35.2
    assert tlm["lon"] == 149.0
    assert tlm["capacity"] == 75.0
    assert "utc" in tlm


@pytest.mark.asyncio
async def test_async_abrp_send_service_vehicle_not_found(hass) -> None:
    """Raise clear error when requested plate cannot be found."""
    hass.config_entries.async_entries.return_value = []

    with pytest.raises(HomeAssistantError, match="Vehicle with license plate"):
        await abrp_send.async_abrp_send_service(
            hass=hass,
            api_key="api-key",
            token="token",
            license_plate="UNKNOWN",
        )


@pytest.mark.asyncio
async def test_async_abrp_send_service_missing_required_tlm(hass, monkeypatch) -> None:
    """Raise error when required ABRP fields cannot be assembled."""
    payload = {
        "data": {
            "viewer": {
                "vehicles": [
                    {
                        "vehicle": {
                            "id": "vehicle-1",
                            "licensePlate": "FWG28Q",
                            "chargePercentage": {"pct": 50},
                            # No position means missing lat/lon after mapping.
                        }
                    }
                ]
            }
        }
    }
    entry = MagicMock()
    entry.runtime_data = SimpleNamespace(
        abrp_coordinator=SimpleNamespace(data=payload),
        coordinator=SimpleNamespace(data=None),
    )
    hass.config_entries.async_entries.return_value = [entry]

    # Avoid making a network call; validation should fail first.
    monkeypatch.setattr(
        abrp_send.aiohttp,
        "ClientSession",
        lambda: _MockClientSession(response=_MockResponse(status=200)),
    )

    with pytest.raises(HomeAssistantError, match="Missing required data for ABRP"):
        await abrp_send.async_abrp_send_service(
            hass=hass,
            api_key="api-key",
            token="token",
            license_plate="FWG28Q",
        )


@pytest.mark.asyncio
async def test_async_abrp_send_service_http_error_with_json_detail(
    abrp_vehicle_payload: dict, hass, monkeypatch
) -> None:
    """Surface ABRP API errors including parsed JSON detail."""
    entry = MagicMock()
    entry.runtime_data = SimpleNamespace(
        abrp_coordinator=SimpleNamespace(data=abrp_vehicle_payload),
        coordinator=SimpleNamespace(data=None),
    )
    hass.config_entries.async_entries.return_value = [entry]

    mock_session = _MockClientSession(
        response=_MockResponse(status=400, text='{"error":"bad token"}')
    )
    monkeypatch.setattr(abrp_send.aiohttp, "ClientSession", lambda: mock_session)

    with pytest.raises(HomeAssistantError, match="ABRP API error: 400 - bad token"):
        await abrp_send.async_abrp_send_service(
            hass=hass,
            api_key="api-key",
            token="token",
            license_plate="FWG28Q",
        )


@pytest.mark.asyncio
async def test_async_abrp_send_service_client_error(
    abrp_vehicle_payload: dict, hass, monkeypatch
) -> None:
    """Translate aiohttp communication failures to HomeAssistantError."""
    entry = MagicMock()
    entry.runtime_data = SimpleNamespace(
        abrp_coordinator=SimpleNamespace(data=abrp_vehicle_payload),
        coordinator=SimpleNamespace(data=None),
    )
    hass.config_entries.async_entries.return_value = [entry]

    mock_session = _MockClientSession(post_error=aiohttp.ClientError("boom"))
    monkeypatch.setattr(abrp_send.aiohttp, "ClientSession", lambda: mock_session)

    with pytest.raises(HomeAssistantError, match="ABRP communication error"):
        await abrp_send.async_abrp_send_service(
            hass=hass,
            api_key="api-key",
            token="token",
            license_plate="FWG28Q",
        )
