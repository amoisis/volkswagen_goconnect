"""Binary sensor platform for volkswagen_goconnect."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .entity import VolkswagenGoConnectEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import VolkswagenGoConnectDataUpdateCoordinator


ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="isCharging",
        name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
    BinarySensorEntityDescription(
        key="isBlocked",
        name="Blocked",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="activated",
        name="Activated",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    coordinator = entry.runtime_data.coordinator
    data = coordinator.data or {}
    vehicles = data.get("data", {}).get("viewer", {}).get("vehicles", [])

    async_add_entities(
        [
            VolkswagenGoConnectBinarySensor(
                coordinator=coordinator,
                entity_description=entity_description,
                vehicle=vehicle,
            )
            for vehicle in vehicles
            if vehicle and vehicle.get("vehicle")
            for entity_description in ENTITY_DESCRIPTIONS
        ]
    )


class VolkswagenGoConnectBinarySensor(VolkswagenGoConnectEntity, BinarySensorEntity):
    """volkswagen_goconnect binary_sensor class."""

    def __init__(
        self,
        coordinator: VolkswagenGoConnectDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
        vehicle: dict | None = None,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator, vehicle)
        self.entity_description = entity_description

        # vehicle is guaranteed to have "vehicle" due to check in async_setup_entry
        self.vehicle_id = vehicle["vehicle"]["id"] if vehicle else None

        if self.vehicle_id:
            plate = getattr(self, "_license_plate", self.vehicle_id)
            self._attr_unique_id = f"vwgc_{plate}_{entity_description.key}"
            if isinstance(entity_description.name, str):
                self._attr_name = entity_description.name
            self._attr_suggested_object_id = f"vwgc_{plate}_{entity_description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        if self.vehicle_id:
            data = self.coordinator.data or {}
            vehicles = data.get("data", {}).get("viewer", {}).get("vehicles", [])
            for v in vehicles:
                if not v or not v.get("vehicle"):
                    continue
                if v["vehicle"]["id"] == self.vehicle_id:
                    vehicle_data = v["vehicle"]
                    key = self.entity_description.key
                    if key in vehicle_data:
                        value = vehicle_data[key]
                        return bool(value)
            return False
        return False
