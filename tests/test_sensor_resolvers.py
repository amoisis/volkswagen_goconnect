"""Additional tests for VolkswagenGoConnectSensor resolver branches."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from custom_components.volkswagen_goconnect.const import SENSOR_ERROR_CODE_MAX_ROWS
from custom_components.volkswagen_goconnect.sensor import VolkswagenGoConnectSensor

ERROR_CODE_MAX_ROWS = SENSOR_ERROR_CODE_MAX_ROWS


def _make_sensor(
    coordinator_data: dict,
    vehicle: dict,
    key: str,
    main_coordinator_data: dict | None = None,
) -> VolkswagenGoConnectSensor:
    """Create a sensor with a minimal description mock."""
    coordinator = MagicMock()
    coordinator.data = coordinator_data
    main_coordinator = None
    if main_coordinator_data is not None:
        main_coordinator = MagicMock()
        main_coordinator.data = main_coordinator_data

    description = MagicMock()
    description.key = key
    return VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=description,
        vehicle=vehicle,
        main_coordinator=main_coordinator,
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


def test_battery_state_of_energy_fallback_and_capacity_guards(mock_api_data) -> None:
    """Cover fallback SoE derivation and estimated capacity guard branches."""
    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]

    vehicle.pop("highVoltageBatteryUsableCapacityKwh", None)
    vehicle["carBatteryCharge"] = {"kwh": 120.4}
    vehicle["carBatteryDischarge"] = {"kwh": 100.1}

    soe_sensor = _make_sensor(mock_api_data, vehicle_entry, "batteryStateOfEnergyKwh")
    assert soe_sensor.native_value == 20.3

    vehicle["chargePercentage"] = {"pct": 0}
    capacity_sensor = _make_sensor(
        mock_api_data, vehicle_entry, "highVoltageBatteryUsableCapacityKwh"
    )
    assert capacity_sensor.native_value is None

    vehicle["chargePercentage"] = {"pct": "bad"}
    assert capacity_sensor.native_value is None

    vehicle["chargePercentage"] = {"pct": 50}
    assert capacity_sensor.native_value == 40.0


def test_battery_power_usage_valid_path_sets_quality_attributes(mock_api_data) -> None:
    """Calculate net power from aligned series and expose quality attributes."""
    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]

    vehicle["carBatteryCharges"] = [
        {"kwh": 10.03, "time": "2026-04-01T21:32:07+00:00"},
        {"kwh": 10.00, "time": "2026-04-01T21:31:07+00:00"},
    ]
    vehicle["carBatteryDischarges"] = [
        {"kwh": 20.20, "time": "2026-04-01T21:32:08+00:00"},
        {"kwh": 20.00, "time": "2026-04-01T21:31:08+00:00"},
    ]

    power_sensor = _make_sensor(mock_api_data, vehicle_entry, "batteryPowerUsageKw")
    assert power_sensor.native_value == 10.2

    attrs = power_sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["quality"] == "ok"
    assert attrs["stream_drift_seconds"] == 1


def test_battery_power_usage_with_user_window_payload_resolves_value() -> None:
    """Resolve battery power from the user 19:43-19:50 local window."""
    vehicle_id = "24686"
    abrp_data = {
        "data": {
            "viewer": {
                "vehicles": [
                    {
                        "vehicle": {
                            "id": vehicle_id,
                            "licensePlate": "FWG28Q",
                            "ignition": {"on": True},
                            "isCharging": False,
                        }
                    }
                ]
            }
        }
    }
    main_data = {
        "data": {
            "viewer": {
                "vehicles": [
                    {
                        "vehicle": {
                            "id": vehicle_id,
                            "licensePlate": "FWG28Q",
                            "ignition": {"on": True},
                            "isCharging": False,
                            "carBatteryCharges": [
                                {
                                    "kwh": 2793.348,
                                    "time": "2026-05-25T09:50:02.000Z",
                                },
                                {
                                    "kwh": 2793.323,
                                    "time": "2026-05-25T09:48:52.000Z",
                                },
                            ],
                            "carBatteryDischarges": [
                                {
                                    "kwh": 2707.108,
                                    "time": "2026-05-25T09:50:02.000Z",
                                },
                                {
                                    "kwh": 2707.087,
                                    "time": "2026-05-25T09:48:52.000Z",
                                },
                            ],
                        }
                    }
                ]
            }
        }
    }

    vehicle_entry = main_data["data"]["viewer"]["vehicles"][0]
    power_sensor = _make_sensor(
        abrp_data,
        vehicle_entry,
        "batteryPowerUsageKw",
        main_coordinator_data=main_data,
    )

    assert power_sensor.native_value == -0.21
    attrs = power_sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["quality"] == "ok"


def test_battery_power_usage_falls_back_when_abrp_vehicle_missing() -> None:
    """Use main fallback when ABRP snapshot has no matching vehicle."""
    vehicle_id = "24686"
    abrp_data = {"data": {"viewer": {"vehicles": []}}}
    main_data = {
        "data": {
            "viewer": {
                "vehicles": [
                    {
                        "vehicle": {
                            "id": vehicle_id,
                            "licensePlate": "FWG28Q",
                            "ignition": {"on": True},
                            "isCharging": False,
                            "carBatteryCharges": [
                                {
                                    "kwh": 2793.348,
                                    "time": "2026-05-25T09:50:02.000Z",
                                },
                                {
                                    "kwh": 2793.323,
                                    "time": "2026-05-25T09:48:52.000Z",
                                },
                            ],
                            "carBatteryDischarges": [
                                {
                                    "kwh": 2707.108,
                                    "time": "2026-05-25T09:50:02.000Z",
                                },
                                {
                                    "kwh": 2707.087,
                                    "time": "2026-05-25T09:48:52.000Z",
                                },
                            ],
                        }
                    }
                ]
            }
        }
    }

    vehicle_entry = main_data["data"]["viewer"]["vehicles"][0]
    power_sensor = _make_sensor(
        abrp_data,
        vehicle_entry,
        "batteryPowerUsageKw",
        main_coordinator_data=main_data,
    )

    assert power_sensor.native_value == -0.21


def test_battery_power_usage_invalid_window_and_missing_series(mock_api_data) -> None:
    """Return None with invalid_window quality or missing-series fallback."""
    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]

    vehicle["carBatteryCharges"] = [
        {"kwh": 10.03, "time": "2026-04-01T21:32:07+00:00"},
        {"kwh": 10.00, "time": "2026-04-01T21:20:07+00:00"},
    ]
    vehicle["carBatteryDischarges"] = [
        {"kwh": 20.20, "time": "2026-04-01T21:32:50+00:00"},
        {"kwh": 20.00, "time": "2026-04-01T21:20:08+00:00"},
    ]

    power_sensor = _make_sensor(mock_api_data, vehicle_entry, "batteryPowerUsageKw")
    assert power_sensor.native_value is None
    attrs = power_sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["quality"] == "invalid_window"

    vehicle["carBatteryCharges"] = []
    assert power_sensor.native_value is None
    assert power_sensor.extra_state_attributes is None


def test_series_and_rate_helpers_cover_invalid_branches(mock_api_data) -> None:
    """Cover invalid branches in rate, interval and timestamp helper methods."""
    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]
    sensor = _make_sensor(mock_api_data, vehicle_entry, "batteryPowerUsageKw")

    vehicle["carBatteryCharges"] = [
        {"kwh": 10.0, "time": "bad-time"},
        {"kwh": 9.9, "time": "2026-04-01T21:31:07+00:00"},
    ]
    assert sensor._resolve_energy_rate_kw(vehicle, "carBatteryCharges") is None
    assert sensor._resolve_series_interval_seconds(vehicle, "carBatteryCharges") is None
    assert sensor._resolve_series_latest_timestamp(vehicle, "carBatteryCharges") is None

    vehicle["carBatteryCharges"] = [
        {"kwh": 9.0, "time": "2026-04-01T21:31:07+00:00"},
        {"kwh": 10.0, "time": "2026-04-01T21:32:07+00:00"},
    ]
    assert sensor._resolve_energy_rate_kw(vehicle, "carBatteryCharges") is None
    assert sensor._resolve_series_interval_seconds(vehicle, "carBatteryCharges") is None


def test_car_battery_total_extra_attributes_and_rate_data_helper(mock_api_data) -> None:
    """Cover car battery total attribute export and list-rate helper guards."""
    from custom_components.volkswagen_goconnect.sensor import self_has_rate_data

    vehicle_entry = mock_api_data["data"]["viewer"]["vehicles"][0]
    vehicle = vehicle_entry["vehicle"]
    vehicle["carBatteryCharge"] = {
        "kwh": 120.4,
        "time": "2026-04-01T21:32:07+00:00",
    }

    charge_total_sensor = _make_sensor(mock_api_data, vehicle_entry, "carBatteryCharge")
    assert charge_total_sensor.native_value == 120.4
    assert charge_total_sensor.extra_state_attributes == {
        "time": "2026-04-01T21:32:07+00:00"
    }

    vehicle["carBatteryCharges"] = [
        {"kwh": 10.0, "time": "2026-04-01T21:31:07+00:00"},
        {"kwh": 9.9, "time": "2026-04-01T21:30:07+00:00"},
    ]
    assert self_has_rate_data(vehicle, "carBatteryCharges") is True

    vehicle["carBatteryCharges"] = [{"kwh": 10.0, "time": "2026-04-01T21:31:07+00:00"}]
    assert self_has_rate_data(vehicle, "carBatteryCharges") is False
