"""Tests for the sensor platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.volkswagen_goconnect.sensor import (
    ENTITY_DESCRIPTIONS,
    VolkswagenGoConnectSensor,
)


@pytest.mark.asyncio
async def test_sensor_native_value_fuel_percentage(mock_api_data):
    """Test sensor native value for fuel percentage."""
    # Create a mock coordinator
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    # Get the fuel percentage entity description
    fuel_pct_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "fuelPercentage"
    )

    # Create sensor
    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=fuel_pct_desc,
        vehicle=vehicle_data,
    )

    # Test the native value
    value = sensor.native_value
    assert value == 75


@pytest.mark.asyncio
async def test_sensor_native_value_odometer(mock_api_data):
    """Test sensor native value for odometer."""
    # Create a mock coordinator
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    # Get the odometer entity description
    odometer_desc = next(desc for desc in ENTITY_DESCRIPTIONS if desc.key == "odometer")

    # Create sensor
    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=odometer_desc,
        vehicle=vehicle_data,
    )

    # Test the native value
    value = sensor.native_value
    assert value == 15000


@pytest.mark.asyncio
async def test_sensor_native_value_simple_field(mock_api_data):
    """Test sensor native value for simple fields."""
    # Create a mock coordinator
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    # Get the fuel type entity description
    fuel_type_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "fuelType"
    )

    # Create sensor
    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=fuel_type_desc,
        vehicle=vehicle_data,
    )

    # Test the native value
    value = sensor.native_value
    assert value == "Petrol"


@pytest.mark.asyncio
async def test_sensor_setup_entry_with_fuel_vehicle(hass, mock_api_data):
    """Test sensor setup entry with fuel vehicle."""
    from custom_components.volkswagen_goconnect.sensor import async_setup_entry

    coordinator = MagicMock()
    coordinator.data = mock_api_data

    # Create mock config entry
    config_entry = MagicMock()
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.coordinator = coordinator

    # Mock async_add_entities
    added_entities = []

    def capture_entities(entities):
        added_entities.extend(list(entities))

    # Call setup
    await async_setup_entry(None, config_entry, capture_entities)  # type: ignore[arg-type]  # type: ignore[arg-type]

    # Verify entities were added
    assert len(added_entities) > 0

    # Check for fuel sensors
    entity_keys = [e.entity_description.key for e in added_entities]
    assert "fuelPercentage" in entity_keys
    assert "fuelLevel" in entity_keys
    assert "chargePercentage" not in entity_keys


@pytest.mark.asyncio
async def test_sensor_setup_entry_with_electric_vehicle(hass, mock_api_data_electric):
    """Test sensor setup entry with electric vehicle."""
    from custom_components.volkswagen_goconnect.sensor import async_setup_entry

    coordinator = MagicMock()
    coordinator.data = mock_api_data_electric

    # Create mock config entry
    config_entry = MagicMock()
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.coordinator = coordinator

    # Mock async_add_entities
    added_entities = []

    def capture_entities(entities):
        added_entities.extend(list(entities))

    # Call setup
    await async_setup_entry(hass, config_entry, capture_entities)  # type: ignore[arg-type]

    # Verify entities were added
    assert len(added_entities) > 0

    # Check for charge sensors
    entity_keys = [e.entity_description.key for e in added_entities]
    assert "chargePercentage" in entity_keys
    assert "fuelPercentage" not in entity_keys
    assert "fuelLevel" not in entity_keys


@pytest.mark.asyncio
async def test_sensor_extra_attributes_workshop(mock_api_data):
    """Test sensor extra state attributes for workshop."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    workshop_desc = next(desc for desc in ENTITY_DESCRIPTIONS if desc.key == "workshop")

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=workshop_desc,
        vehicle=vehicle_data,
    )

    # Access native_value to trigger attribute setting
    _ = sensor.native_value

    # Check extra attributes
    attributes = sensor.extra_state_attributes
    assert attributes is not None
    assert "name" in attributes
    assert "phone" in attributes
    assert "timezone_offset" in attributes
    assert attributes["timezone_offset"] == "+10:00"
    assert "opening_hours_monday_from" in attributes
    assert attributes["opening_hours_monday_from"] == "08:00"
    assert "opening_hours_monday_to" in attributes
    assert attributes["opening_hours_monday_to"] == "17:00"
    assert "opening_hours_tuesday_from" in attributes
    assert attributes["opening_hours_tuesday_from"] == "08:00"


@pytest.mark.asyncio
async def test_sensor_extra_attributes_brand_contact(mock_api_data):
    """Test sensor extra state attributes for brand contact info."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    brand_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "brandContactInfo"
    )

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=brand_desc,
        vehicle=vehicle_data,
    )

    # Access native_value to trigger attribute setting
    _ = sensor.native_value

    # Check extra attributes
    attributes = sensor.extra_state_attributes
    assert attributes is not None


@pytest.mark.asyncio
async def test_sensor_extra_attributes_charging_status(mock_api_data):
    """Test sensor extra state attributes for charging status."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    charging_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "chargingStatus"
    )

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=charging_desc,
        vehicle=vehicle_data,
    )

    # Access native_value to trigger attribute setting
    _ = sensor.native_value

    # Check extra attributes
    attributes = sensor.extra_state_attributes
    assert attributes is not None


@pytest.mark.asyncio
async def test_sensor_setup_entry_empty_data(hass):
    """Test sensor setup entry with empty data."""
    from custom_components.volkswagen_goconnect.sensor import async_setup_entry

    coordinator = MagicMock()
    coordinator.data = {}

    config_entry = MagicMock()
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.coordinator = coordinator

    added_entities = []

    def capture_entities(entities):
        added_entities.extend(list(entities))

    await async_setup_entry(hass, config_entry, capture_entities)  # type: ignore[arg-type]

    # Should handle empty data gracefully
    assert len(added_entities) == 0


@pytest.mark.asyncio
async def test_sensor_setup_entry_no_vehicles(hass):
    """Test sensor setup entry with no vehicles."""
    from custom_components.volkswagen_goconnect.sensor import async_setup_entry

    coordinator = MagicMock()
    coordinator.data = {"data": {"viewer": {"vehicles": []}}}

    config_entry = MagicMock()
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.coordinator = coordinator

    added_entities = []

    def capture_entities(entities):
        added_entities.extend(list(entities))

    await async_setup_entry(hass, config_entry, capture_entities)  # type: ignore[arg-type]

    assert len(added_entities) == 0


@pytest.mark.asyncio
async def test_sensor_native_value_no_vehicle(mock_api_data):
    """Test sensor native value when vehicle is None."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    fuel_pct_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "fuelPercentage"
    )

    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=fuel_pct_desc,
        vehicle=None,
    )

    assert sensor.native_value is None


@pytest.mark.asyncio
async def test_sensor_native_value_body_type(mock_api_data):
    """Test sensor native value for body type (not in vehicle)."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data
    # Add body field to the top-level data
    coordinator.data["body"] = "sedan"

    body_desc = MagicMock()
    body_desc.key = "body"

    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=body_desc,
        vehicle=None,
    )

    assert sensor.native_value == "sedan"


@pytest.mark.asyncio
async def test_sensor_native_value_dict_value(mock_api_data):
    """Test sensor native value when value is a dict (returns dict)."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    # Create a desc for a field that returns a dict
    dict_desc = MagicMock()
    dict_desc.key = "service"

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    # Add a dict field to vehicle
    vehicle_data["vehicle"]["service"] = {"status": "ok"}

    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=dict_desc,
        vehicle=vehicle_data,
    )

    # When value is dict, it returns the dict
    value = sensor.native_value
    assert isinstance(value, dict)


@pytest.mark.asyncio
async def test_sensor_native_value_key_not_found(mock_api_data):
    """Test sensor native value when key is not in vehicle data."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    missing_desc = MagicMock()
    missing_desc.key = "nonexistentField"

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=missing_desc,
        vehicle=vehicle_data,
    )

    assert sensor.native_value is None


@pytest.mark.asyncio
async def test_sensor_extra_state_attributes_workshop(mock_api_data):
    """Test extra state attributes for workshop information."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    workshop_desc = MagicMock()
    workshop_desc.key = "workshop"

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=workshop_desc,
        vehicle=vehicle_data,
    )

    attrs = sensor.extra_state_attributes
    # Workshop should return a dict with shop data
    assert isinstance(attrs, (dict, type(None)))


@pytest.mark.asyncio
async def test_sensor_extra_state_attributes_no_vehicle_id(mock_api_data):
    """Test extra state attributes when vehicle ID is None."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    workshop_desc = MagicMock()
    workshop_desc.key = "workshop"

    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=workshop_desc,
        vehicle=None,
    )

    assert sensor.extra_state_attributes is None


@pytest.mark.asyncio
async def test_sensor_extra_state_attributes_unknown_key(mock_api_data):
    """Test extra state attributes for unknown key."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    unknown_desc = MagicMock()
    unknown_desc.key = "unknownAttributeKey"

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=unknown_desc,
        vehicle=vehicle_data,
    )

    assert sensor.extra_state_attributes is None


@pytest.mark.asyncio
async def test_sensor_setup_entry_with_null_vehicle():
    """Test sensor setup entry with null vehicle in list."""
    from custom_components.volkswagen_goconnect.sensor import async_setup_entry

    coordinator = MagicMock()
    coordinator.data = {"data": {"viewer": {"vehicles": [None, {"vehicle": None}]}}}

    config_entry = MagicMock()
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.coordinator = coordinator

    added_entities = []

    def capture_entities(entities):
        added_entities.extend(list(entities))

    hass = MagicMock()
    await async_setup_entry(hass, config_entry, capture_entities)  # type: ignore[arg-type]

    # Should skip null vehicles gracefully
    assert len(added_entities) == 0


@pytest.mark.asyncio
async def test_sensor_native_value_vehicle_not_found(mock_api_data):
    """Test sensor native value when vehicle ID doesn't match."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    fuel_pct_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "fuelPercentage"
    )

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=fuel_pct_desc,
        vehicle=vehicle_data,
    )
    # Change the vehicle ID to non-matching
    sensor.vehicle_id = "non-existent-vehicle-id"

    # Should return None when vehicle not found
    assert sensor.native_value is None


@pytest.mark.asyncio
async def test_sensor_native_value_with_null_vehicle_in_list(mock_api_data):
    """Test sensor native value with null vehicles in the list."""
    import copy

    coordinator = MagicMock()
    # Create a deep copy to avoid modifying the original fixture
    mock_api_data_copy = copy.deepcopy(mock_api_data)
    vehicles = mock_api_data_copy["data"]["viewer"]["vehicles"]
    # Prepend null vehicles to the list
    mock_api_data_copy["data"]["viewer"]["vehicles"] = [
        None,
        {"vehicle": None},
        *vehicles,
    ]
    coordinator.data = mock_api_data_copy

    fuel_pct_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "fuelPercentage"
    )

    # Use the copied vehicle data
    vehicle_data = mock_api_data_copy["data"]["viewer"]["vehicles"][2]
    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=fuel_pct_desc,
        vehicle=vehicle_data,
    )

    # Should still find the correct vehicle and return value
    assert sensor.native_value == 75


@pytest.mark.asyncio
async def test_sensor_get_vehicle_data_field_not_found(mock_api_data):
    """Test _get_vehicle_data_field when vehicle not found."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    workshop_desc = next(desc for desc in ENTITY_DESCRIPTIONS if desc.key == "workshop")

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=workshop_desc,
        vehicle=vehicle_data,
    )
    # Change vehicle ID to non-matching
    sensor.vehicle_id = "non-existent-id"

    # Should return None when vehicle not found
    result = sensor._get_vehicle_data_field("workshop", "_workshop_data")
    assert result is None


@pytest.mark.asyncio
async def test_sensor_extra_state_attributes_brand_contact_not_dict(mock_api_data):
    """Test extra state attributes for brandContactInfo when not a dict."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    brand_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "brandContactInfo"
    )

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    # Set brandContactInfo to a non-dict value
    vehicle_data["vehicle"]["brandContactInfo"] = "Not a dict"

    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=brand_desc,
        vehicle=vehicle_data,
    )

    # Should return None when data is not a dict
    assert sensor.extra_state_attributes is None


@pytest.mark.asyncio
async def test_sensor_extra_state_attributes_brand_contact_none(mock_api_data):
    """Test extra state attributes for brandContactInfo when None."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    brand_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "brandContactInfo"
    )

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    # Set brandContactInfo to None
    vehicle_data["vehicle"]["brandContactInfo"] = None

    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=brand_desc,
        vehicle=vehicle_data,
    )

    # Access native_value first to cache the data
    _ = sensor.native_value

    # Should return None when data is None
    assert sensor.extra_state_attributes is None


@pytest.mark.asyncio
async def test_sensor_extra_state_attributes_charging_status_not_dict(mock_api_data):
    """Test extra state attributes for chargingStatus when not a dict."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    charging_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "chargingStatus"
    )

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    # Set chargingStatus to a non-dict value
    vehicle_data["vehicle"]["chargingStatus"] = "Not a dict"

    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=charging_desc,
        vehicle=vehicle_data,
    )

    # Should return None when data is not a dict
    assert sensor.extra_state_attributes is None


@pytest.mark.asyncio
async def test_sensor_extra_state_attributes_charging_status_none(mock_api_data):
    """Test extra state attributes for chargingStatus when None."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    charging_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "chargingStatus"
    )

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    # Set chargingStatus to None
    vehicle_data["vehicle"]["chargingStatus"] = None

    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=charging_desc,
        vehicle=vehicle_data,
    )

    # Access native_value first to cache the data
    _ = sensor.native_value

    # Should return None when data is None
    assert sensor.extra_state_attributes is None


@pytest.mark.asyncio
async def test_sensor_extra_state_attributes_workshop_not_dict(mock_api_data):
    """Test extra state attributes for workshop when not a dict."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    workshop_desc = next(desc for desc in ENTITY_DESCRIPTIONS if desc.key == "workshop")

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    # Set workshop to a non-dict value
    vehicle_data["vehicle"]["workshop"] = "Not a dict"

    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=workshop_desc,
        vehicle=vehicle_data,
    )

    # Should return None when data is not a dict
    assert sensor.extra_state_attributes is None


@pytest.mark.asyncio
async def test_sensor_extra_state_attributes_charging_status_empty_dict(
    mock_api_data,
):
    """Test extra state attributes for chargingStatus with empty attributes."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    charging_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "chargingStatus"
    )

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    # Set chargingStatus to an empty dict
    vehicle_data["vehicle"]["chargingStatus"] = {}

    sensor = VolkswagenGoConnectSensor(
        coordinator=coordinator,
        entity_description=charging_desc,
        vehicle=vehicle_data,
    )

    # Access native_value first
    _ = sensor.native_value

    # Should return None when all attributes are None
    assert sensor.extra_state_attributes is None
