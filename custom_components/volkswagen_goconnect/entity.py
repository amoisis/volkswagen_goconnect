"""VolkswagenGoConnectEntity class."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import VolkswagenGoConnectDataUpdateCoordinator


class VolkswagenGoConnectEntity(
    CoordinatorEntity[VolkswagenGoConnectDataUpdateCoordinator]
):
    """VolkswagenGoConnectEntity class."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VolkswagenGoConnectDataUpdateCoordinator,
        vehicle: dict | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.vehicle = vehicle
        if vehicle:
            vehicle_data = vehicle["vehicle"]
            self._license_plate = vehicle_data.get("licensePlate") or vehicle_data["id"]
            self._attr_unique_id = f"{vehicle_data['id']}"

            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, vehicle_data["id"])},
                name=vehicle_data.get("licensePlate") or vehicle_data["id"],
                manufacturer=vehicle_data.get("make"),
                model=vehicle_data.get("name"),
            )
        else:
            self._license_plate = None
            self._attr_unique_id = coordinator.config_entry.entry_id
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
                name=coordinator.config_entry.title,
            )

    @staticmethod
    def extract_vehicles(data: dict[str, Any] | None) -> list[dict[str, Any]]:
        """Extract vehicles list from coordinator payload."""
        if not isinstance(data, dict):
            return []
        vehicles = data.get("data", {}).get("viewer", {}).get("vehicles", [])
        return vehicles if isinstance(vehicles, list) else []

    def _get_vehicles(self) -> list[dict[str, Any]]:
        """Return vehicles from coordinator data."""
        return self.extract_vehicles(self.coordinator.data)

    def _get_vehicle_data_by_id(self, vehicle_id: str | None) -> dict[str, Any] | None:
        """Return vehicle payload matching the provided vehicle id."""
        if not vehicle_id:
            return None

        for entry in self._get_vehicles():
            if not isinstance(entry, dict):
                continue
            vehicle_data = entry.get("vehicle")
            if isinstance(vehicle_data, dict) and vehicle_data.get("id") == vehicle_id:
                return vehicle_data
        return None
