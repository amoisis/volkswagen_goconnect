"""Binary sensor platform for volkswagen_goconnect."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import SIGNAL_ABRP_ACKNOWLEDGE
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

# Vehicle data fields compared to detect a change worth uploading to ABRP
_ABRP_SNAPSHOT_KEYS = ("chargePercentage", "isCharging", "odometer")


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    coordinator = entry.runtime_data.coordinator
    vehicles = VolkswagenGoConnectEntity.extract_vehicles(coordinator.data)

    ignition_coordinator = getattr(
        entry.runtime_data, "ignition_coordinator", coordinator
    )
    entities: list[BinarySensorEntity] = [
        VolkswagenGoConnectBinarySensor(
            coordinator=(
                ignition_coordinator
                if entity_description.key == "ignition"
                else coordinator
            ),
            entity_description=entity_description,
            vehicle=vehicle,
        )
        for vehicle in vehicles
        if vehicle and vehicle.get("vehicle")
        for entity_description in ENTITY_DESCRIPTIONS
    ]

    abrp_enabled: bool = getattr(entry.runtime_data, "abrp_enabled", False)
    if abrp_enabled:
        abrp_coordinator = getattr(entry.runtime_data, "abrp_coordinator", coordinator)
        entities.extend(
            VolkswagenGoConnectAbrpDataChangedSensor(
                coordinator=abrp_coordinator,
                main_coordinator=coordinator,
                vehicle=vehicle,
                entry_id=entry.entry_id,
            )
            for vehicle in vehicles
            if vehicle and vehicle.get("vehicle")
        )

    async_add_entities(entities)


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
            self._attr_unique_id = f"vgc_{plate}_{entity_description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        vehicle_data = self._get_vehicle_data_by_id(self.vehicle_id)
        if not vehicle_data:
            return False

        key = self.entity_description.key
        if key == "ignition":
            value = vehicle_data.get("ignition")
            return not bool(value)

        return bool(vehicle_data.get(key))


class VolkswagenGoConnectAbrpDataChangedSensor(
    VolkswagenGoConnectEntity, BinarySensorEntity
):
    """Binary sensor that is True when telemetry has changed since last ABRP upload."""

    _attr_icon = "mdi:cloud-upload"

    def __init__(
        self,
        coordinator: VolkswagenGoConnectDataUpdateCoordinator,
        main_coordinator: VolkswagenGoConnectDataUpdateCoordinator,
        vehicle: dict | None = None,
        entry_id: str = "",
    ) -> None:
        """Initialize the ABRP data-changed sensor."""
        super().__init__(coordinator, vehicle)
        self.vehicle_id = vehicle["vehicle"]["id"] if vehicle else None
        self._entry_id = entry_id
        self._last_acknowledged: dict[str, Any] | None = None
        self._main_coordinator = main_coordinator

        if self.vehicle_id:
            plate = getattr(self, "_license_plate", self.vehicle_id)
            self._attr_unique_id = f"vgc_{plate}_abrp_data_changed"
            self._attr_name = "ABRP Data Changed"

    def _current_snapshot(self) -> dict[str, Any]:
        """
        Return the current values of the tracked telemetry fields.

        Reads from the main coordinator (full query, confirmed to receive fresh
        data from the VW API) so that the snapshot reflects what HA entities
        show, rather than the slim ABRP query which may return cached responses.
        Falls back to the ABRP coordinator if main coordinator has no data yet.
        """
        vehicle_data = None
        for entry in self.extract_vehicles(self._main_coordinator.data):
            if isinstance(entry, dict):
                vd = entry.get("vehicle")
                if isinstance(vd, dict) and vd.get("id") == self.vehicle_id:
                    vehicle_data = vd
                    break
        if vehicle_data is None:
            vehicle_data = self._get_vehicle_data_by_id(self.vehicle_id) or {}
        snapshot = {k: vehicle_data.get(k) for k in _ABRP_SNAPSHOT_KEYS}
        position = vehicle_data.get("position") or {}
        snapshot["latitude"] = position.get("latitude")
        snapshot["longitude"] = position.get("longitude")
        speedometers = vehicle_data.get("speedometers") or []
        if (
            isinstance(speedometers, list)
            and speedometers
            and isinstance(speedometers[0], dict)
        ):
            snapshot["speed"] = speedometers[0].get("speed")
        else:
            snapshot["speed"] = None
        return snapshot

    @property
    def is_on(self) -> bool:
        """Return True when the telemetry snapshot differs from last acknowledged."""
        current = self._current_snapshot()
        # If we have never acknowledged and we have actual data, report changed
        if self._last_acknowledged is None:
            return any(v is not None for v in current.values())
        return current != self._last_acknowledged

    @callback
    def _handle_acknowledge(self, license_plate: str) -> None:
        """Store snapshot as acknowledged only when plate matches this sensor."""
        sensor_plate = (self._license_plate or "").strip().upper()
        requested_plate = (license_plate or "").strip().upper()
        if not sensor_plate or requested_plate != sensor_plate:
            return

        self._last_acknowledged = self._current_snapshot()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Subscribe to the acknowledge dispatcher signal when added to HA."""
        await super().async_added_to_hass()
        # Re-evaluate state when the main coordinator (fresh data) updates.
        self.async_on_remove(
            self._main_coordinator.async_add_listener(self._handle_coordinator_update)
        )
        signal = SIGNAL_ABRP_ACKNOWLEDGE.format(entry_id=self._entry_id)
        self.async_on_remove(
            async_dispatcher_connect(self.hass, signal, self._handle_acknowledge)
        )
        # Set the initial baseline from current data so the sensor starts as
        # False after a reboot rather than immediately True.
        snapshot = self._current_snapshot()
        if any(v is not None for v in snapshot.values()):
            self._last_acknowledged = snapshot
