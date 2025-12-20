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
    await async_setup_entry(hass, config_entry, capture_entities)

    # Verify entities were added
    assert len(added_entities) > 0
    assert all(isinstance(e, VolkswagenGoConnectBinarySensor) for e in added_entities)
