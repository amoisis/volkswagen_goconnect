"""Tests for the entity base class."""

from unittest.mock import MagicMock

import pytest

from custom_components.volkswagen_goconnect.entity import VolkswagenGoConnectEntity


@pytest.mark.asyncio
async def test_entity_unique_id(mock_api_data):
    """Test entity unique_id is correctly set."""
    # Create a mock coordinator
    coordinator = MagicMock()

    # Create entity with vehicle data
    vehicle_data = mock_api_data["data"]["viewer"]["vehicles"][0]
    entity = VolkswagenGoConnectEntity(
        coordinator=coordinator,
        vehicle=vehicle_data,
    )

    # Verify unique_id
    assert entity._attr_unique_id == "test-vehicle-id"


@pytest.mark.asyncio
async def test_entity_attribution():
    """Test entity attribution is set."""
    from custom_components.volkswagen_goconnect.const import ATTRIBUTION

    # Create a mock coordinator
    coordinator = MagicMock()

    # Create entity without vehicle
    entity = VolkswagenGoConnectEntity(coordinator=coordinator)

    # Verify attribution
    assert entity._attr_attribution == ATTRIBUTION


def test_extract_vehicles_returns_empty_for_non_dict_data() -> None:
    """extract_vehicles should return empty list for invalid payload roots."""
    assert VolkswagenGoConnectEntity.extract_vehicles(None) == []
    assert VolkswagenGoConnectEntity.extract_vehicles("invalid") == []


def test_extract_vehicles_returns_empty_for_non_list_vehicles() -> None:
    """extract_vehicles should guard when vehicles node is not a list."""
    payload = {"data": {"viewer": {"vehicles": {"unexpected": "mapping"}}}}
    assert VolkswagenGoConnectEntity.extract_vehicles(payload) == []


def test_get_vehicle_data_by_id_handles_mixed_vehicle_entries() -> None:
    """_get_vehicle_data_by_id should skip malformed entries and find valid one."""
    coordinator = MagicMock()
    coordinator.data = {
        "data": {
            "viewer": {
                "vehicles": [
                    None,
                    {"vehicle": None},
                    {"vehicle": "not-a-dict"},
                    {"vehicle": {"id": "vehicle-1", "licensePlate": "ABC123"}},
                ]
            }
        }
    }

    entity = VolkswagenGoConnectEntity(
        coordinator=coordinator,
        vehicle={"vehicle": {"id": "vehicle-1", "licensePlate": "ABC123"}},
    )

    assert entity._get_vehicle_data_by_id("vehicle-1") == {
        "id": "vehicle-1",
        "licensePlate": "ABC123",
    }
    assert entity._get_vehicle_data_by_id(None) is None
