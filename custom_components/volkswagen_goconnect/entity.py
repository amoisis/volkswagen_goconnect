"""VolkswagenGoConnectEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import VolkswagenGoConnectDataUpdateCoordinator


class VolkswagenGoConnectEntity(
    CoordinatorEntity[VolkswagenGoConnectDataUpdateCoordinator]
):
    """VolkswagenGoConnectEntity class."""

    _attr_attribution = ATTRIBUTION

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
