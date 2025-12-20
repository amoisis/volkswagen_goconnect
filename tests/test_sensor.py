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
async def test_sensor_setup_entry_with_fuel_vehicle(mock_api_data):
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
    await async_setup_entry(None, config_entry, capture_entities)

    # Verify entities were added
    assert len(added_entities) > 0

    # Check for fuel sensors
    entity_keys = [e.entity_description.key for e in added_entities]
    assert "fuelPercentage" in entity_keys
    assert "fuelLevel" in entity_keys
    assert "chargePercentage" not in entity_keys


@pytest.mark.asyncio
async def test_sensor_setup_entry_with_electric_vehicle(mock_api_data_electric):
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
    await async_setup_entry(None, config_entry, capture_entities)

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
async def test_sensor_setup_entry_empty_data():
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

    await async_setup_entry(None, config_entry, capture_entities)

    # Should handle empty data gracefully
    assert len(added_entities) == 0


@pytest.mark.asyncio
async def test_sensor_setup_entry_no_vehicles():
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

    await async_setup_entry(None, config_entry, capture_entities)

    assert len(added_entities) == 0
