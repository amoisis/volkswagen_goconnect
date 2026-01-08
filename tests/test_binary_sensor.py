"""Binary sensor tests."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.volkswagen_goconnect.binary_sensor import (
    ENTITY_DESCRIPTIONS,
    VolkswagenGoConnectBinarySensor,
)
from custom_components.volkswagen_goconnect.coordinator import (
    VolkswagenGoConnectDataUpdateCoordinator,
)


@pytest.mark.asyncio
async def test_binary_sensor_is_charging(hass: HomeAssistant, mock_api_data):
    """Test is_charging binary sensor."""
    # Create a mock coordinator
    coordinator = AsyncMock(spec=VolkswagenGoConnectDataUpdateCoordinator)
    coordinator.data = mock_api_data

    # Get the isCharging entity description
    charging_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "isCharging"
    )

    # Create binary sensor
    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectBinarySensor(
        coordinator=coordinator,
        entity_description=charging_desc,
        vehicle=vehicle_data,
    )

    # Test the is_on value
    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_binary_sensor_is_blocked(hass: HomeAssistant, mock_api_data):
    """Test isBlocked binary sensor."""
    # Create a mock coordinator
    coordinator = AsyncMock(spec=VolkswagenGoConnectDataUpdateCoordinator)
    coordinator.data = mock_api_data

    # Get the isBlocked entity description
    blocked_desc = next(desc for desc in ENTITY_DESCRIPTIONS if desc.key == "isBlocked")

    # Create binary sensor
    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectBinarySensor(
        coordinator=coordinator,
        entity_description=blocked_desc,
        vehicle=vehicle_data,
    )

    # Test the is_on value
    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_binary_sensor_activated(hass: HomeAssistant, mock_api_data):
    """Test activated binary sensor."""
    # Create a mock coordinator
    coordinator = AsyncMock(spec=VolkswagenGoConnectDataUpdateCoordinator)
    coordinator.data = mock_api_data

    # Get the activated entity description
    activated_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "activated"
    )

    # Create binary sensor
    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectBinarySensor(
        coordinator=coordinator,
        entity_description=activated_desc,
        vehicle=vehicle_data,
    )

    # Test the is_on value
    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_binary_sensor_setup_entry(hass: HomeAssistant, mock_api_data):
    """Test binary sensor setup entry."""
    from unittest.mock import MagicMock
    from custom_components.volkswagen_goconnect.binary_sensor import async_setup_entry

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
    mock_hass = MagicMock()
    await async_setup_entry(mock_hass, config_entry, capture_entities)  # type: ignore[arg-type]

    # Verify entities were added
    assert len(added_entities) > 0
    assert all(isinstance(e, VolkswagenGoConnectBinarySensor) for e in added_entities)


@pytest.mark.asyncio
async def test_binary_sensor_is_on_no_vehicle(hass: HomeAssistant, mock_api_data):
    """Test is_on returns False when vehicle is None."""
    coordinator = AsyncMock(spec=VolkswagenGoConnectDataUpdateCoordinator)
    coordinator.data = mock_api_data
    coordinator.config_entry = AsyncMock()
    coordinator.config_entry.entry_id = "test_entry_id"

    charging_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "isCharging"
    )

    # Create sensor with None vehicle (edge case)
    sensor = VolkswagenGoConnectBinarySensor(
        coordinator=coordinator,
        entity_description=charging_desc,
        vehicle=None,
    )

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_binary_sensor_is_on_vehicle_not_found(
    hass: HomeAssistant, mock_api_data
):
    """Test is_on returns False when vehicle ID not found in data."""
    coordinator = AsyncMock(spec=VolkswagenGoConnectDataUpdateCoordinator)
    coordinator.data = mock_api_data

    charging_desc = next(
        desc for desc in ENTITY_DESCRIPTIONS if desc.key == "isCharging"
    )

    vehicle_data = {
        "vehicle": {
            "id": "non-existent-id",
            "isCharging": True,
        }
    }

    sensor = VolkswagenGoConnectBinarySensor(
        coordinator=coordinator,
        entity_description=charging_desc,
        vehicle=vehicle_data,
    )

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_binary_sensor_is_on_key_not_in_data(hass: HomeAssistant, mock_api_data):
    """Test is_on returns False when key is not in vehicle data."""
    coordinator = AsyncMock(spec=VolkswagenGoConnectDataUpdateCoordinator)
    coordinator.data = mock_api_data

    # Use a key that doesn't exist in test data
    fake_desc = AsyncMock()
    fake_desc.key = "nonexistentKey"

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]

    sensor = VolkswagenGoConnectBinarySensor(
        coordinator=coordinator,
        entity_description=fake_desc,
        vehicle=vehicle_data,
    )

    assert sensor.is_on is False
