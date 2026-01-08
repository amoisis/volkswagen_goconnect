"""Tests for the device tracker platform."""

from copy import deepcopy
from unittest.mock import MagicMock

import pytest

from custom_components.volkswagen_goconnect.device_tracker import (
    VolkswagenGoConnectDeviceTracker,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_device_tracker_setup_entry(mock_api_data):
    """Verify tracker entity is created when position data is present."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    config_entry = MagicMock()
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.coordinator = coordinator

    added_entities = []

    def capture_entities(entities):
        added_entities.extend(list(entities))

    hass = MagicMock()
    await async_setup_entry(hass, config_entry, capture_entities)  # type: ignore[arg-type]

    assert len(added_entities) == 1
    tracker = added_entities[0]
    assert isinstance(tracker, VolkswagenGoConnectDeviceTracker)
    assert tracker.latitude == -37.8136
    assert tracker.longitude == 144.9631
    assert tracker.extra_state_attributes == {"position_id": "position-1"}


@pytest.mark.asyncio
async def test_device_tracker_setup_entry_without_position(mock_api_data):
    """Ensure no tracker entities are added when position data is missing."""
    coordinator = MagicMock()
    coordinator.data = deepcopy(mock_api_data)
    coordinator.data["data"]["viewer"]["vehicles"][0]["vehicle"].pop("position", None)

    config_entry = MagicMock()
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.coordinator = coordinator

    added_entities = []

    def capture_entities(entities):
        added_entities.extend(list(entities))

    hass = MagicMock()
    await async_setup_entry(hass, config_entry, capture_entities)  # type: ignore[arg-type]

    assert len(added_entities) == 0


@pytest.mark.asyncio
async def test_device_tracker_attributes_update(mock_api_data):
    """Ensure tracker reads updated position from coordinator data."""
    coordinator = MagicMock()
    coordinator.data = mock_api_data

    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    tracker = VolkswagenGoConnectDeviceTracker(
        coordinator=coordinator, vehicle=vehicle_data
    )

    assert tracker.latitude == -37.8136
    assert tracker.longitude == 144.9631

    # Update data and confirm tracker reflects new coordinates
    coordinator.data["data"]["viewer"]["vehicles"][0]["vehicle"]["position"][
        "latitude"
    ] = -38.0
    coordinator.data["data"]["viewer"]["vehicles"][0]["vehicle"]["position"][
        "longitude"
    ] = 145.0

    assert tracker.latitude == -38.0
    assert tracker.longitude == 145.0
