"""Device tracker platform for volkswagen_goconnect."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType

from .entity import VolkswagenGoConnectEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import VolkswagenGoConnectDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the device_tracker platform."""
    coordinator = entry.runtime_data.coordinator
    data = coordinator.data or {}
    vehicles = data.get("data", {}).get("viewer", {}).get("vehicles", [])

    async_add_entities(
        [
            VolkswagenGoConnectDeviceTracker(
                coordinator=coordinator,
                vehicle=vehicle,
            )
            for vehicle in vehicles
            if vehicle and vehicle.get("vehicle", {}).get("position")
        ]
    )


class VolkswagenGoConnectDeviceTracker(VolkswagenGoConnectEntity, TrackerEntity):
    """Device tracker representing vehicle position."""

    _attr_source_type = SourceType.GPS
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: VolkswagenGoConnectDataUpdateCoordinator,
        vehicle: dict | None = None,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator, vehicle)
        self.vehicle_id = vehicle["vehicle"]["id"] if vehicle else None
        if self.vehicle_id:
            plate = getattr(self, "_license_plate", self.vehicle_id)
            self._attr_unique_id = f"vwgc_{plate}_tracker"
            self._attr_name = "Location"
            self._attr_suggested_object_id = f"vwgc_{plate}_location"

    def _get_vehicle_data(self) -> dict[str, Any] | None:
        """Return the vehicle data for this tracker."""
        if not self.vehicle_id:
            return None

        coordinator_data = self.coordinator.data or {}
        vehicles = (
            coordinator_data.get("data", {}).get("viewer", {}).get("vehicles", [])
        )
        for entry in vehicles:
            vehicle_data = entry.get("vehicle") if entry else None
            if vehicle_data and vehicle_data.get("id") == self.vehicle_id:
                return vehicle_data
        return None

    @property
    def latitude(self) -> float | None:
        """Return vehicle latitude."""
        vehicle_data = self._get_vehicle_data()
        position = vehicle_data.get("position") if vehicle_data else None
        return position.get("latitude") if isinstance(position, dict) else None

    @property
    def longitude(self) -> float | None:
        """Return vehicle longitude."""
        vehicle_data = self._get_vehicle_data()
        position = vehicle_data.get("position") if vehicle_data else None
        return position.get("longitude") if isinstance(position, dict) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes for the tracker."""
        vehicle_data = self._get_vehicle_data()
        position = vehicle_data.get("position") if vehicle_data else None
        if not isinstance(position, dict):
            return None

        # Only expose attributes that add value beyond lat/lon
        attributes = {
            "position_id": position.get("id"),
        }
        return {k: v for k, v in attributes.items() if v is not None}
