"""Sensor platform for volkswagen_goconnect."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import VolkswagenGoConnectEntity

if TYPE_CHECKING:
    from .coordinator import VolkswagenGoConnectDataUpdateCoordinator


ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="id",
        name="Vehicle ID",
        icon="mdi:identifier",
    ),
    SensorEntityDescription(
        key="fuelType",
        name="Fuel Type",
        icon="mdi:gas-station",
    ),
    SensorEntityDescription(
        key="licensePlate",
        name="License Plate",
        icon="mdi:car",
    ),
    SensorEntityDescription(
        key="make",
        name="Make",
        icon="mdi:car",
    ),
    SensorEntityDescription(
        key="model",
        name="Model",
        icon="mdi:car-side",
    ),
    SensorEntityDescription(
        key="year",
        name="Year",
        icon="mdi:calendar",
    ),
    SensorEntityDescription(
        key="vin",
        name="VIN",
        icon="mdi:identifier",
    ),
    SensorEntityDescription(
        key="odometer",
        name="Odometer",
        icon="mdi:speedometer",
        native_unit_of_measurement="km",
        state_class="total_increasing",
    ),
    SensorEntityDescription(
        key="fuelPercentage",
        name="Fuel Percentage",
        icon="mdi:gas-station",
        native_unit_of_measurement="%",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="fuelLevel",
        name="Fuel Level",
        icon="mdi:gas-station",
        native_unit_of_measurement="L",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="chargePercentage",
        name="Charge Percentage",
        icon="mdi:battery",
        native_unit_of_measurement="%",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="ignition",
        name="Ignition",
        icon="mdi:key",
    ),
    SensorEntityDescription(
        key="rangeTotalKm",
        name="Range Total",
        icon="mdi:map-marker-distance",
        native_unit_of_measurement="km",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="chargingStatus",
        name="Charging Status",
        icon="mdi:ev-station",
    ),
    SensorEntityDescription(
        key="highVoltageBatteryUsableCapacityKwh",
        name="Battery Capacity",
        icon="mdi:battery",
        native_unit_of_measurement="kWh",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="workshop",
        name="Workshop",
        icon="mdi:wrench",
    ),
    SensorEntityDescription(
        key="brandContactInfo",
        name="Brand Contact Info",
        icon="mdi:phone",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator
    data = coordinator.data or {}
    vehicles = data.get("data", {}).get("viewer", {}).get("vehicles", [])

    entities = []
    for vehicle in vehicles:
        if not vehicle or not vehicle.get("vehicle"):
            continue

        vehicle_data = vehicle["vehicle"]
        fuel_type = vehicle_data.get("fuelType", "").lower()
        is_electric = fuel_type == "electric"

        # Always add these sensors
        base_sensors = [
            "id",
            "fuelType",
            "licensePlate",
            "make",
            "model",
            "year",
            "vin",
            "odometer",
            "ignition",
            "rangeTotalKm",
            "chargingStatus",
            "highVoltageBatteryUsableCapacityKwh",
            "workshop",
            "brandContactInfo",
        ]

        for key in base_sensors:
            for desc in ENTITY_DESCRIPTIONS:
                if desc.key == key:
                    entities.append(
                        VolkswagenGoConnectSensor(
                            coordinator=coordinator,
                            entity_description=desc,
                            vehicle=vehicle,
                        )
                    )
                    break

        # Add fuel/charge sensors based on fuel type
        if is_electric:
            # For electric vehicles, add charge percentage
            for desc in ENTITY_DESCRIPTIONS:
                if desc.key == "chargePercentage":
                    entities.append(
                        VolkswagenGoConnectSensor(
                            coordinator=coordinator,
                            entity_description=desc,
                            vehicle=vehicle,
                        )
                    )
                    break
        else:
            # For non-electric vehicles, add fuel percentage and level
            for desc in ENTITY_DESCRIPTIONS:
                if desc.key in ["fuelPercentage", "fuelLevel"]:
                    entities.append(
                        VolkswagenGoConnectSensor(
                            coordinator=coordinator,
                            entity_description=desc,
                            vehicle=vehicle,
                        )
                    )

    async_add_entities(entities)


class VolkswagenGoConnectSensor(VolkswagenGoConnectEntity, SensorEntity):
    """volkswagen_goconnect Sensor class."""

    def __init__(
        self,
        coordinator: VolkswagenGoConnectDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        vehicle: dict | None = None,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator, vehicle)
        self.entity_description = entity_description

        # vehicle is guaranteed to have "vehicle" due to check in async_setup_entry
        self.vehicle_id = vehicle["vehicle"]["id"] if vehicle else None
        self._workshop_data = None
        self._brand_data = None
        self._charging_status_data = None

        if self.vehicle_id:
            self._attr_unique_id = f"{self.vehicle_id}_{entity_description.key}"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
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
                        # Handle nested objects
                        if isinstance(value, dict):
                            if key == "fuelPercentage" and "percent" in value:
                                return value["percent"]
                            if key == "fuelLevel" and "liter" in value:
                                return value["liter"]
                            if key == "chargePercentage" and "pct" in value:
                                return value["pct"]
                            if key == "odometer" and "odometer" in value:
                                return value["odometer"]
                            if key == "ignition" and "on" in value:
                                return value["on"]
                            if key == "rangeTotalKm" and "km" in value:
                                return value["km"]
                            if (
                                key == "highVoltageBatteryUsableCapacityKwh"
                                and "kwh" in value
                            ):
                                return value["kwh"]
                            if key == "chargingStatus":
                                # Store attributes for later
                                self._charging_status_data = value
                                return (
                                    "Charging"
                                    if value.get("startTime")
                                    and not value.get("endedAt")
                                    else "Not Charging"
                                )
                            if key == "workshop":
                                # Store attributes for later
                                self._workshop_data = value
                                return (
                                    value.get("name", "Available")
                                    if value
                                    else "Not Available"
                                )
                            if key == "brandContactInfo":
                                # Store attributes for later
                                self._brand_data = value
                                return (
                                    value.get("roadsideAssistanceName", "Available")
                                    if value
                                    else "Not Available"
                                )
                        return value
            return None
        return self.coordinator.data.get("body")

    @property
    def extra_state_attributes(self) -> dict[str, str | int | float | None] | None:
        """Return extra state attributes."""
        key = self.entity_description.key

        if key == "workshop":
            # Get workshop data - try cache first, then fetch from coordinator
            data = getattr(self, "_workshop_data", None)

            # If not cached, fetch from coordinator
            if not data and self.vehicle_id:
                coordinator_data = self.coordinator.data or {}
                vehicles = (
                    coordinator_data.get("data", {})
                    .get("viewer", {})
                    .get("vehicles", [])
                )
                for v in vehicles:
                    if v and v.get("vehicle", {}).get("id") == self.vehicle_id:
                        data = v.get("vehicle", {}).get("workshop")
                        break

            if data and isinstance(data, dict):
                attributes = {
                    "id": data.get("id"),
                    "number": data.get("number"),
                    "name": data.get("name"),
                    "address": data.get("address"),
                    "zip": data.get("zip"),
                    "city": data.get("city"),
                    "phone": data.get("phone"),
                    "emergency_contact_phone": data.get("emergencyContactPhoneNumber"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                    "brand": data.get("brand"),
                    "mobile_booking_url": data.get("mobileBookingUrl"),
                    "timezone_offset": (
                        data.get("timeZone", {}).get("offset")
                        if data.get("timeZone")
                        else None
                    ),
                }
                # Add opening hours if available
                opening_hours = data.get("openingHours")
                if opening_hours and isinstance(opening_hours, list):
                    for hours in opening_hours:
                        if isinstance(hours, dict):
                            day = hours.get("day", "").lower()
                            attributes[f"opening_hours_{day}_from"] = hours.get("from")
                            attributes[f"opening_hours_{day}_to"] = hours.get("to")
                return attributes

        elif key == "brandContactInfo":
            # Get brand contact data - try cache first, then fetch from coordinator
            data = getattr(self, "_brand_data", None)

            # If not cached, fetch from coordinator
            if not data and self.vehicle_id:
                coordinator_data = self.coordinator.data or {}
                vehicles = (
                    coordinator_data.get("data", {})
                    .get("viewer", {})
                    .get("vehicles", [])
                )
                for v in vehicles:
                    if v and v.get("vehicle", {}).get("id") == self.vehicle_id:
                        data = v.get("vehicle", {}).get("brandContactInfo")
                        break

            if data and isinstance(data, dict):
                return {
                    "webshop_url": data.get("webshopUrl"),
                    "webshop_name": data.get("webshopName"),
                    "roadside_assistance_phone": data.get(
                        "roadsideAssistancePhoneNumber"
                    ),
                    "roadside_assistance_name": data.get("roadsideAssistanceName"),
                    "roadside_assistance_url": data.get("roadsideAssistanceUrl"),
                    "roadside_emergency_assistance_url": data.get(
                        "roadsideEmergencyAssistanceUrl"
                    ),
                    "roadside_assistance_paid": data.get("roadsideAssistancePaid"),
                }

        elif key == "chargingStatus":
            # Get charging status data - try cache first, then fetch from coordinator
            data = getattr(self, "_charging_status_data", None)

            # If not cached, fetch from coordinator
            if not data and self.vehicle_id:
                coordinator_data = self.coordinator.data or {}
                vehicles = (
                    coordinator_data.get("data", {})
                    .get("viewer", {})
                    .get("vehicles", [])
                )
                for v in vehicles:
                    if v and v.get("vehicle", {}).get("id") == self.vehicle_id:
                        data = v.get("vehicle", {}).get("chargingStatus")
                        break

            if data and isinstance(data, dict):
                attributes = {
                    "start_charge_percentage": data.get("startChargePercentage"),
                    "start_time": data.get("startTime"),
                    "ended_at": data.get("endedAt"),
                    "charged_percentage": data.get("chargedPercentage"),
                    "average_charge_speed": data.get("averageChargeSpeed"),
                    "charge_in_kwh_increase": data.get("chargeInKwhIncrease"),
                    "range_increase": data.get("rangeIncrease"),
                    "time_until_80_percent_charge": data.get(
                        "timeUntil80PercentCharge"
                    ),
                    "show_summary_for_charge_ended": data.get(
                        "showSummaryForChargeEnded"
                    ),
                }
                # Only return non-None attributes
                filtered_attributes = {
                    k: v for k, v in attributes.items() if v is not None
                }
                return filtered_attributes if filtered_attributes else None

        return None
