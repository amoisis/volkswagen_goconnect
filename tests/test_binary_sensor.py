"""Binary sensor tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.volkswagen_goconnect.binary_sensor import (
    ENTITY_DESCRIPTIONS,
    VolkswagenGoConnectAbrpDataChangedSensor,
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
    config_entry.runtime_data.abrp_enabled = False

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


@pytest.mark.asyncio
async def test_binary_sensor_setup_entry_with_abrp_enabled(
    hass: HomeAssistant,
    mock_api_data,
):
    """Set up ABRP data-changed sensors when ABRP is enabled."""
    from custom_components.volkswagen_goconnect.binary_sensor import async_setup_entry

    coordinator = MagicMock()
    coordinator.data = mock_api_data

    config_entry = MagicMock()
    config_entry.entry_id = "entry-1"
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.coordinator = coordinator
    config_entry.runtime_data.ignition_coordinator = coordinator
    config_entry.runtime_data.abrp_coordinator = coordinator
    config_entry.runtime_data.abrp_enabled = True

    added_entities: list = []

    def capture_entities(entities):
        added_entities.extend(list(entities))

    await async_setup_entry(hass, config_entry, capture_entities)  # type: ignore[arg-type]

    assert any(
        isinstance(entity, VolkswagenGoConnectAbrpDataChangedSensor)
        for entity in added_entities
    )


def test_abrp_data_changed_sensor_on_state_and_acknowledge(mock_api_data):
    """Track changes and reset only for matching acknowledge plate."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data
    main_coordinator = MagicMock()
    main_coordinator.data = mock_api_data

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectAbrpDataChangedSensor(
        coordinator=coordinator,
        main_coordinator=main_coordinator,
        vehicle=vehicle_data,
        entry_id="entry-1",
    )
    sensor.hass = MagicMock()
    sensor.async_write_ha_state = MagicMock()

    # Initial non-empty snapshot should report changed.
    assert sensor.is_on is True

    # Wrong plate should not acknowledge.
    sensor._handle_acknowledge("OTHER123")
    assert sensor.is_on is True

    # Matching plate acknowledges current snapshot.
    sensor._handle_acknowledge("ABC123")
    assert sensor.is_on is False

    # Change telemetry in the main coordinator payload to flip sensor on again.
    vehicle_data["vehicle"]["odometer"] = {
        "id": "odometer-2",
        "odometer": 15001,
        "time": "2025-12-19T10:31:00Z",
    }
    assert sensor.is_on is True


def test_abrp_data_changed_sensor_snapshot_falls_back_to_abrp_coordinator(
    mock_api_data,
):
    """Use ABRP coordinator data when main coordinator has no vehicle payload."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data
    main_coordinator = MagicMock()
    main_coordinator.data = {"data": {"viewer": {"vehicles": []}}}

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectAbrpDataChangedSensor(
        coordinator=coordinator,
        main_coordinator=main_coordinator,
        vehicle=vehicle_data,
        entry_id="entry-1",
    )

    snapshot = sensor._current_snapshot()
    assert snapshot["latitude"] == -37.8136
    assert snapshot["longitude"] == 144.9631


@pytest.mark.asyncio
async def test_abrp_data_changed_sensor_async_added_to_hass(mock_api_data):
    """Register coordinator and dispatcher listeners when entity is added."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data
    main_coordinator = MagicMock()
    main_coordinator.data = mock_api_data
    main_coordinator.async_add_listener = MagicMock(return_value=lambda: None)

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    sensor = VolkswagenGoConnectAbrpDataChangedSensor(
        coordinator=coordinator,
        main_coordinator=main_coordinator,
        vehicle=vehicle_data,
        entry_id="entry-1",
    )
    sensor.hass = MagicMock()

    removers: list = []
    sensor.async_on_remove = removers.append  # type: ignore[method-assign]

    with (
        patch(
            "homeassistant.helpers.update_coordinator.CoordinatorEntity"
            ".async_added_to_hass",
            new=AsyncMock(),
        ),
        patch(
            "custom_components.volkswagen_goconnect.binary_sensor"
            ".async_dispatcher_connect",
            return_value=lambda: None,
        ) as mock_dispatcher_connect,
    ):
        await sensor.async_added_to_hass()

    assert main_coordinator.async_add_listener.called
    assert mock_dispatcher_connect.called
    assert len(removers) == 2
