"""Tests for ABRP telemetry send service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
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
                            "carBatteryCharge": {
                                "kwh": 100.0,
                                "time": "2026-04-01T10:01:00+00:00",
                            },
                            "carBatteryDischarge": {
                                "kwh": 50.25,
                                "time": "2026-04-01T10:01:00+00:00",
                            },
                            "carBatteryCharges": [
                                {
                                    "kwh": 100.0,
                                    "time": "2026-04-01T10:01:00+00:00",
                                },
                                {
                                    "kwh": 99.95,
                                    "time": "2026-04-01T10:00:00+00:00",
                                },
                            ],
                            "carBatteryDischarges": [
                                {
                                    "kwh": 50.25,
                                    "time": "2026-04-01T10:01:00+00:00",
                                },
                                {
                                    "kwh": 50.0,
                                    "time": "2026-04-01T10:00:00+00:00",
                                },
                            ],
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


def test_get_vehicle_data_by_license_plate_handles_invalid_entries() -> None:
    """Skip non-dict entries and missing vehicle objects safely."""
    payload = {
        "data": {
            "viewer": {
                "vehicles": [
                    None,
                    {"vehicle": None},
                    {"vehicle": {"licensePlate": "ABC123", "id": "v1"}},
                ]
            }
        }
    }

    assert abrp_send._get_vehicle_data_by_license_plate(payload, "ZZZ999") == {}


def test_get_vehicle_data_by_license_plate_empty_payload() -> None:
    """Return empty dict when payload has no vehicles list."""
    assert abrp_send._get_vehicle_data_by_license_plate(None, "FWG28Q") == {}


def test_build_live_mapping_computes_capacity(abrp_vehicle_payload: dict) -> None:
    """Build mapping and verify derived capacity and field extraction."""
    vehicle = abrp_vehicle_payload["data"]["viewer"]["vehicles"][0]["vehicle"]
    mapping, power_source = abrp_send._build_live_mapping(vehicle)

    assert mapping["soc"] == 80
    assert mapping["lat"] == -35.2
    assert mapping["lon"] == 149.0
    assert mapping["speed"] == 82
    assert mapping["ext_temp"] == 23
    assert mapping["capacity"] == 75.0
    assert mapping["power"] == 12.0
    assert power_source == "series"


def test_build_live_mapping_handles_invalid_soe_and_capacity_inputs() -> None:
    """Handle invalid numeric fields without raising and keep derived fields None."""
    vehicle = {
        "id": "vehicle-err",
        "chargePercentage": {"pct": "not-a-number"},
        "position": {"latitude": -35.2, "longitude": 149.0},
        "carBatteryCharge": {"kwh": "bad", "time": "2026-04-01T10:01:00+00:00"},
        "carBatteryDischarge": {
            "kwh": 50.0,
            "time": "2026-04-01T10:01:00+00:00",
        },
    }

    mapping, _power_source = abrp_send._build_live_mapping(vehicle)
    assert mapping["soe"] is None
    assert mapping["capacity"] is None


def test_build_live_mapping_handles_invalid_soc_with_valid_soe() -> None:
    """Hit capacity fallback path when SoC parsing fails with valid SoE present."""
    vehicle = {
        "id": "vehicle-capacity-error",
        "chargePercentage": {"pct": "not-a-number"},
        "position": {"latitude": -35.2, "longitude": 149.0},
        "highVoltageBatteryUsableCapacityKwh": {"kwh": 60.0},
    }

    mapping, _power_source = abrp_send._build_live_mapping(vehicle)
    assert mapping["soe"] == 60.0
    assert mapping["capacity"] is None


def test_parse_timestamp_invalid_shapes() -> None:
    """Return None for invalid timestamp values."""
    assert abrp_send._parse_timestamp(123) is None
    assert abrp_send._parse_timestamp("not-a-timestamp") is None


def test_prune_counter_cache_removes_stale_and_enforces_limit() -> None:
    """Prune expired entries and cap cache size to configured maximum."""
    abrp_send._ABRP_COUNTER_CACHE.clear()
    now = datetime.now(UTC)

    # One stale entry that should always be removed.
    abrp_send._ABRP_COUNTER_CACHE["stale"] = (
        1.0,
        1.0,
        now,
        now,
        now - timedelta(days=2),
    )

    # Fill beyond max size with fresh entries.
    for index in range(40):
        seen = now - timedelta(seconds=index)
        abrp_send._ABRP_COUNTER_CACHE[f"fresh-{index}"] = (
            1.0,
            1.0,
            now,
            now,
            seen,
        )

    abrp_send._prune_counter_cache(now)

    assert "stale" not in abrp_send._ABRP_COUNTER_CACHE
    assert (
        len(abrp_send._ABRP_COUNTER_CACHE) <= abrp_send.ABRP_COUNTER_CACHE_MAX_ENTRIES
    )


def test_resolve_power_from_series_invalid_branches() -> None:
    """Cover invalid branches in list-based power calculation helper."""
    assert (
        abrp_send._resolve_power_from_series(
            {"carBatteryCharges": [], "carBatteryDischarges": []}
        )
        is None
    )

    # Non-dict latest elements.
    vehicle = {
        "carBatteryCharges": ["bad", {}],
        "carBatteryDischarges": [{}, {}],
    }
    assert abrp_send._resolve_power_from_series(vehicle) is None

    # Float conversion failure.
    vehicle = {
        "carBatteryCharges": [
            {"kwh": "bad", "time": "2026-04-01T10:01:00+00:00"},
            {"kwh": 10.0, "time": "2026-04-01T10:00:00+00:00"},
        ],
        "carBatteryDischarges": [
            {"kwh": 20.0, "time": "2026-04-01T10:01:00+00:00"},
            {"kwh": 19.8, "time": "2026-04-01T10:00:00+00:00"},
        ],
    }
    assert abrp_send._resolve_power_from_series(vehicle) is None

    # Invalid timestamp parse.
    vehicle["carBatteryCharges"][0]["kwh"] = 10.1
    vehicle["carBatteryCharges"][0]["time"] = "bad-time"
    assert abrp_send._resolve_power_from_series(vehicle) is None

    # Non-positive interval.
    vehicle["carBatteryCharges"][0]["time"] = "2026-04-01T10:00:00+00:00"
    vehicle["carBatteryCharges"][1]["time"] = "2026-04-01T10:01:00+00:00"
    assert abrp_send._resolve_power_from_series(vehicle) is None

    # Excessive drift and negative delta.
    vehicle["carBatteryCharges"] = [
        {"kwh": 10.0, "time": "2026-04-01T10:01:00+00:00"},
        {"kwh": 9.9, "time": "2026-04-01T10:00:00+00:00"},
    ]
    vehicle["carBatteryDischarges"] = [
        {"kwh": 20.1, "time": "2026-04-01T10:10:30+00:00"},
        {"kwh": 20.0, "time": "2026-04-01T10:09:30+00:00"},
    ]
    assert abrp_send._resolve_power_from_series(vehicle) is None

    vehicle["carBatteryDischarges"] = [
        {"kwh": 19.9, "time": "2026-04-01T10:01:00+00:00"},
        {"kwh": 20.0, "time": "2026-04-01T10:00:00+00:00"},
    ]
    assert abrp_send._resolve_power_from_series(vehicle) is None


def test_resolve_power_from_counters_with_cache_invalid_branches() -> None:
    """Cover invalid branches in counter-cache fallback helper."""
    abrp_send._ABRP_COUNTER_CACHE.clear()

    assert abrp_send._resolve_power_from_counters_with_cache({}) is None

    vehicle = {
        "id": "v-cache-invalid",
        "carBatteryCharge": {"kwh": "bad", "time": "2026-04-01T10:00:00+00:00"},
        "carBatteryDischarge": {"kwh": 10.0, "time": "2026-04-01T10:00:00+00:00"},
    }
    assert abrp_send._resolve_power_from_counters_with_cache(vehicle) is None

    vehicle["carBatteryCharge"]["kwh"] = 5.0
    vehicle["carBatteryCharge"]["time"] = "bad-time"
    assert abrp_send._resolve_power_from_counters_with_cache(vehicle) is None

    # Prime cache with valid first sample.
    vehicle["carBatteryCharge"] = {"kwh": 5.0, "time": "2026-04-01T10:00:00+00:00"}
    vehicle["carBatteryDischarge"] = {
        "kwh": 10.0,
        "time": "2026-04-01T10:00:00+00:00",
    }
    assert abrp_send._resolve_power_from_counters_with_cache(vehicle) is None

    # Non-positive interval.
    vehicle["carBatteryCharge"] = {"kwh": 5.1, "time": "2026-04-01T09:59:00+00:00"}
    vehicle["carBatteryDischarge"] = {
        "kwh": 10.1,
        "time": "2026-04-01T09:59:00+00:00",
    }
    assert abrp_send._resolve_power_from_counters_with_cache(vehicle) is None

    # Excessive interval.
    vehicle["carBatteryCharge"] = {"kwh": 5.1, "time": "2026-04-01T11:00:00+00:00"}
    vehicle["carBatteryDischarge"] = {
        "kwh": 10.1,
        "time": "2026-04-01T11:00:00+00:00",
    }
    assert abrp_send._resolve_power_from_counters_with_cache(vehicle) is None

    # Negative deltas.
    vehicle["carBatteryCharge"] = {"kwh": 4.9, "time": "2026-04-01T11:01:00+00:00"}
    vehicle["carBatteryDischarge"] = {
        "kwh": 9.9,
        "time": "2026-04-01T11:01:00+00:00",
    }
    assert abrp_send._resolve_power_from_counters_with_cache(vehicle) is None


def test_build_live_mapping_omits_power_for_invalid_series_window(
    abrp_vehicle_payload: dict,
) -> None:
    """Power is omitted when cumulative sample windows exceed quality gates."""
    vehicle = abrp_vehicle_payload["data"]["viewer"]["vehicles"][0]["vehicle"]
    vehicle["carBatteryCharges"] = [
        {"kwh": 100.0, "time": "2026-04-01T10:10:00+00:00"},
        {"kwh": 99.0, "time": "2026-04-01T10:00:00+00:00"},
    ]
    vehicle["carBatteryDischarges"] = [
        {"kwh": 50.5, "time": "2026-04-01T10:10:00+00:00"},
        {"kwh": 50.0, "time": "2026-04-01T10:00:00+00:00"},
    ]

    mapping, power_source = abrp_send._build_live_mapping(vehicle)

    assert mapping["power"] is None
    assert power_source == "none"


def test_build_live_mapping_uses_counter_cache_fallback() -> None:
    """Power falls back to single-counter deltas when list series are unavailable."""
    abrp_send._ABRP_COUNTER_CACHE.clear()
    vehicle = {
        "id": "vehicle-cache-1",
        "chargePercentage": {"pct": 50},
        "position": {"latitude": -35.0, "longitude": 149.0},
        "carBatteryCharge": {"kwh": 100.0, "time": "2026-04-01T10:00:00+00:00"},
        "carBatteryDischarge": {
            "kwh": 200.0,
            "time": "2026-04-01T10:00:00+00:00",
        },
    }

    first_mapping, first_source = abrp_send._build_live_mapping(vehicle)
    assert first_mapping["power"] is None
    assert first_source == "none"

    vehicle["carBatteryCharge"] = {"kwh": 100.02, "time": "2026-04-01T10:01:00+00:00"}
    vehicle["carBatteryDischarge"] = {
        "kwh": 200.2,
        "time": "2026-04-01T10:01:00+00:00",
    }
    second_mapping, second_source = abrp_send._build_live_mapping(vehicle)

    # charge = 1.2kW, discharge = 12kW, net = 10.8kW
    assert second_mapping["power"] == 10.8
    assert second_source == "cache"


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
    assert tlm["power"] == 12.0
    assert "utc" in tlm


@pytest.mark.asyncio
async def test_async_abrp_send_service_omits_power_when_unavailable(
    abrp_vehicle_payload: dict,
    hass,
    monkeypatch,
) -> None:
    """Do not include power key when no valid power calculation exists."""
    vehicle = abrp_vehicle_payload["data"]["viewer"]["vehicles"][0]["vehicle"]
    vehicle["carBatteryCharges"] = [
        {"kwh": 100.0, "time": "2026-04-01T10:10:00+00:00"},
        {"kwh": 99.0, "time": "2026-04-01T10:00:00+00:00"},
    ]
    vehicle["carBatteryDischarges"] = [
        {"kwh": 50.5, "time": "2026-04-01T10:10:00+00:00"},
        {"kwh": 50.0, "time": "2026-04-01T10:00:00+00:00"},
    ]

    entry = MagicMock()
    entry.runtime_data = SimpleNamespace(
        abrp_coordinator=SimpleNamespace(data=abrp_vehicle_payload),
        coordinator=SimpleNamespace(data=None),
    )
    hass.config_entries.async_entries.return_value = [entry]

    mock_session = _MockClientSession(response=_MockResponse(status=200))
    monkeypatch.setattr(abrp_send.aiohttp, "ClientSession", lambda: mock_session)

    await abrp_send.async_abrp_send_service(
        hass=hass,
        api_key="api-key",
        token="token-123",
        license_plate="FWG28Q",
    )

    called_url, _headers, _data = mock_session.calls[0]
    parsed = URL(called_url)
    tlm = json.loads(parsed.query["tlm"])
    assert "power" not in tlm


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
async def test_async_abrp_send_service_http_error_with_text_body(
    abrp_vehicle_payload: dict, hass, monkeypatch
) -> None:
    """Surface non-JSON ABRP body text in error messages."""
    entry = MagicMock()
    entry.runtime_data = SimpleNamespace(
        abrp_coordinator=SimpleNamespace(data=abrp_vehicle_payload),
        coordinator=SimpleNamespace(data=None),
    )
    hass.config_entries.async_entries.return_value = [entry]

    mock_session = _MockClientSession(response=_MockResponse(status=500, text="boom"))
    monkeypatch.setattr(abrp_send.aiohttp, "ClientSession", lambda: mock_session)

    with pytest.raises(HomeAssistantError, match="ABRP API error: 500 - boom"):
        await abrp_send.async_abrp_send_service(
            hass=hass,
            api_key="api-key",
            token="token",
            license_plate="FWG28Q",
        )


@pytest.mark.asyncio
async def test_async_abrp_send_service_http_error_with_empty_body(
    abrp_vehicle_payload: dict, hass, monkeypatch
) -> None:
    """Use explicit fallback text when ABRP error body is empty/non-JSON."""
    entry = MagicMock()
    entry.runtime_data = SimpleNamespace(
        abrp_coordinator=SimpleNamespace(data=abrp_vehicle_payload),
        coordinator=SimpleNamespace(data=None),
    )
    hass.config_entries.async_entries.return_value = [entry]

    mock_session = _MockClientSession(response=_MockResponse(status=500, text=""))
    monkeypatch.setattr(abrp_send.aiohttp, "ClientSession", lambda: mock_session)

    with pytest.raises(
        HomeAssistantError, match=r"ABRP API error: 500 \(no error details\)"
    ):
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
