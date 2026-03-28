"""Additional tests for VolkswagenGoConnectSensor resolver branches."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from custom_components.volkswagen_goconnect.sensor import (
    ERROR_CODE_MAX_ROWS,
    VolkswagenGoConnectSensor,
)


def _make_sensor(
    coordinator_data: dict,
    vehicle: dict,
    key: str,
) -> VolkswagenGoConnectSensor:
    """Create a sensor with a minimal description mock."""
    coordinator = MagicMock()
    coordinator.data = coordinator_data
    description = MagicMock()
    description.key = key
    return VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=description,
        vehicle=vehicle,
    )


def test_previous_driver_score_and_battery_efficiency(mock_api_data) -> None:
    """Resolve nested previous score and efficiency conversion paths."""
    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]

    vehicle["driverScore"] = {"previousDriverScore": 84}
    previous_score_sensor = _make_sensor(
        mock_api_data,
        vehicle_entry,
        "previousDriverScore",
    )
    assert previous_score_sensor.native_value == 84

    vehicle["batteryEfficiencyKmPerKwh"] = "7.456"
    efficiency_sensor = _make_sensor(
        mock_api_data,
        vehicle_entry,
        "batteryEfficiencyKmPerKwh",
    )
    assert efficiency_sensor.native_value == 7.46

    vehicle["batteryEfficiencyKmPerKwh"] = "invalid"
    assert efficiency_sensor.native_value is None


def test_average_consumption_and_predicted_service_date(mock_api_data) -> None:
    """Cover average consumption and service date parsing branches."""
    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]

    vehicle["averageBatteryConsumptionInKwhPer100Km"] = {
        "efficiencyKwhPer100Km": "19.126"
    }
    avg_sensor = _make_sensor(
        mock_api_data,
        vehicle_entry,
        "averageBatteryConsumptionInKwhPer100Km",
    )
    assert avg_sensor.native_value == 19.13

    vehicle["service"] = {"predictedDate": "2026-05-01"}
    date_sensor = _make_sensor(mock_api_data, vehicle_entry, "predictedServiceDate")
    assert date_sensor.native_value == date(2026, 5, 1)

    vehicle["service"] = {"predictedDate": "not-a-date"}
    assert date_sensor.native_value is None


def test_charge_event_and_parse_datetime_paths(mock_api_data) -> None:
    """Resolve charge event timestamp and handle invalid formats."""
    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]

    vehicle["chargeEvents"] = [{"endTime": "2026-03-27T12:00:00Z"}]
    charge_sensor = _make_sensor(mock_api_data, vehicle_entry, "chargeEvents")
    assert charge_sensor.native_value is not None

    vehicle["chargeEvents"] = [{"endTime": "bad-datetime"}]
    assert charge_sensor.native_value is None


def test_speed_outdoor_and_battery_temp_time_attributes(mock_api_data) -> None:
    """Expose cached time attributes for list-based and dict-based sensors."""
    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]

    vehicle["speedometers"] = [{"speed": 88, "time": "2026-03-27T10:00:00Z"}]
    speed_sensor = _make_sensor(mock_api_data, vehicle_entry, "speedometers")
    assert speed_sensor.native_value == 88.0
    assert speed_sensor.extra_state_attributes == {"time": "2026-03-27T10:00:00Z"}

    vehicle["outdoorTemperatures"] = [{"celsius": 26.4, "time": "2026-03-27T10:00:01Z"}]
    outdoor_sensor = _make_sensor(mock_api_data, vehicle_entry, "outdoorTemperatures")
    assert outdoor_sensor.native_value == 26.4
    assert outdoor_sensor.extra_state_attributes == {"time": "2026-03-27T10:00:01Z"}

    vehicle["highVoltageBatteryTemperature"] = {
        "celsius": 29.2,
        "time": "2026-03-27T10:00:02Z",
    }
    hv_temp_sensor = _make_sensor(
        mock_api_data,
        vehicle_entry,
        "highVoltageBatteryTemperature",
    )
    assert hv_temp_sensor.native_value == 29.2
    assert hv_temp_sensor.extra_state_attributes == {"time": "2026-03-27T10:00:02Z"}


def test_resolve_charging_status_workshop_and_brand_contact(mock_api_data) -> None:
    """Cover charging status and string fallback resolvers."""
    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]

    vehicle["chargingStatus"] = {"startTime": "2026-03-27T10:00:00Z", "endedAt": None}
    status_sensor = _make_sensor(mock_api_data, vehicle_entry, "chargingStatus")
    assert status_sensor.native_value == "Charging"

    vehicle["chargingStatus"] = {
        "startTime": "2026-03-27T10:00:00Z",
        "endedAt": "2026-03-27T11:00:00Z",
    }
    assert status_sensor.native_value == "Not Charging"

    vehicle["workshop"] = {}
    workshop_sensor = _make_sensor(mock_api_data, vehicle_entry, "workshop")
    assert workshop_sensor.native_value == "Not Available"

    vehicle["brandContactInfo"] = {}
    brand_sensor = _make_sensor(mock_api_data, vehicle_entry, "brandContactInfo")
    assert brand_sensor.native_value == "Available"

    vehicle["brandContactInfo"] = "not-a-dict"
    assert brand_sensor.native_value == "Not Available"


def test_open_error_code_leads_attributes_and_tables(mock_api_data) -> None:
    """Build open/closed/all error-code tables and truncation metadata."""
    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]

    long_description = "X" * 200
    lead_open = {
        "id": "lead-open",
        "status": "open",
        "dismissed": False,
        "important": True,
        "severityScore": 7,
        "context": {
            "__typename": "LeadErrorCodeContext",
            "errorCode": "P0001",
            "provider": "VW",
            "ecu": "ECU-1",
            "description": long_description,
            "rawCode": "RAW1",
            "severity": "high",
            "firstErrorCodeTime": "2026-03-27T10:00:00Z",
            "lastErrorCodeTime": "2026-03-27T10:30:00Z",
            "errorCodeCount": 4,
        },
    }
    lead_closed = {
        "id": "lead-closed",
        "status": "closed",
        "dismissed": True,
        "important": False,
        "severityScore": 2,
        "context": {
            "__typename": "LeadErrorCodeContext",
            "errorCode": "P0002",
            "provider": "VW",
            "ecu": "ECU-2",
            "description": "Closed issue",
            "rawCode": "RAW2",
            "severity": "low",
            "firstErrorCodeTime": "2026-03-27T09:00:00Z",
            "lastErrorCodeTime": "2026-03-27T09:10:00Z",
            "errorCodeCount": 1,
        },
    }
    vehicle["openLeads"] = [lead_open]
    vehicle["allLeads"] = [lead_open, lead_closed]

    open_leads_sensor = _make_sensor(mock_api_data, vehicle_entry, "openErrorCodeLeads")
    assert open_leads_sensor.native_value == 1

    attrs = open_leads_sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["lead_count"] == 1
    assert attrs["open_lead_count"] == 1
    assert attrs["closed_lead_count"] == 1
    assert attrs["all_lead_count"] == 2
    assert attrs["max_rows_applied"] == ERROR_CODE_MAX_ROWS
    assert "| id | status |" in attrs["table"]
    assert attrs["rows"][0]["description"].endswith("...")


def test_open_error_code_leads_defaults_when_data_missing(mock_api_data) -> None:
    """Return default empty lead attributes when list data is unavailable."""
    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]
    vehicle["openLeads"] = None

    open_leads_sensor = _make_sensor(mock_api_data, vehicle_entry, "openErrorCodeLeads")
    assert open_leads_sensor.native_value == 0

    attrs = open_leads_sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["lead_count"] == 0
    assert attrs["table"] == "No open error code leads"


def test_has_latest_list_value_helper(mock_api_data) -> None:
    """Validate helper that checks for latest list values."""
    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]

    sensor = _make_sensor(mock_api_data, vehicle_entry, "speedometers")

    vehicle["speedometers"] = [{"speed": 55}]
    assert sensor._has_latest_list_value(vehicle, "speedometers", "speed") is True

    vehicle["speedometers"] = [{"time": "2026-03-27T10:00:00Z"}]
    assert sensor._has_latest_list_value(vehicle, "speedometers", "speed") is False

    vehicle["speedometers"] = []
    assert sensor._has_latest_list_value(vehicle, "speedometers", "speed") is False
