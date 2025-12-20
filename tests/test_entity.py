"""Tests for the entity base class."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

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
