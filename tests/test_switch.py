"""Tests for the switch platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.volkswagen_goconnect.switch import (
    ENTITY_DESCRIPTIONS,
    VolkswagenGoConnectSwitch,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_switch_setup_entry(mock_api_data):
    """Test switch setup entry."""
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
    hass = MagicMock()
    await async_setup_entry(hass, config_entry, capture_entities)  # type: ignore[arg-type]

    # Verify entities were added
    assert len(added_entities) > 0
    assert all(isinstance(e, VolkswagenGoConnectSwitch) for e in added_entities)


@pytest.mark.asyncio
async def test_switch_is_on():
    """Test switch is_on property."""
    coordinator = MagicMock()

    switch = VolkswagenGoConnectSwitch(
        coordinator=coordinator,
        entity_description=ENTITY_DESCRIPTIONS[0],
    )

    # Default should be False
    assert switch.is_on is False


@pytest.mark.asyncio
async def test_switch_turn_on():
    """Test turning switch on."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()

    switch = VolkswagenGoConnectSwitch(
        coordinator=coordinator,
        entity_description=ENTITY_DESCRIPTIONS[0],
    )

    await switch.async_turn_on()

    # Verify refresh was called
    coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_switch_turn_off():
    """Test turning switch off."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()

    switch = VolkswagenGoConnectSwitch(
        coordinator=coordinator,
        entity_description=ENTITY_DESCRIPTIONS[0],
    )

    await switch.async_turn_off()

    # Verify refresh was called
    coordinator.async_request_refresh.assert_called_once()
