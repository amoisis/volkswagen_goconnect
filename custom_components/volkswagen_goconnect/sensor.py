"""Sensor platform for volkswagen_goconnect."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any, ClassVar

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfElectricPotential
from homeassistant.util import dt as dt_util

from .entity import VolkswagenGoConnectEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="latestBatteryVoltage",
        name="Low Voltage Battery",
        icon="mdi:car-battery",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="chargeEvents",
        name="Last Charge End Time",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="driverScore",
        name="Driver Score",
        icon="mdi:steering",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="previousDriverScore",
        name="Previous Driver Score",
        icon="mdi:steering-off",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="predictedServiceDate",
        name="Predicted Service Date",
        icon="mdi:wrench-clock",
        device_class=SensorDeviceClass.DATE,
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
    vehicles = VolkswagenGoConnectEntity.extract_vehicles(coordinator.data)

    entities = []
    for vehicle in vehicles:
        if not vehicle or not vehicle.get("vehicle"):
            continue

        vehicle_data = vehicle["vehicle"]
        fuel_type = vehicle_data.get("fuelType", "").lower()
        is_electric = fuel_type == "electric"

        # Always add these sensors
        base_sensors = {
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
        }

        conditional_sensors = {
            "latestBatteryVoltage": lambda data: (
                isinstance(data.get("latestBatteryVoltage"), dict)
                and data["latestBatteryVoltage"].get("voltage") is not None
            ),
            "chargeEvents": lambda data: (
                isinstance(data.get("chargeEvents"), list)
                and len(data["chargeEvents"]) > 0
                and isinstance(data["chargeEvents"][0], dict)
                and data["chargeEvents"][0].get("endTime") is not None
            ),
            "driverScore": lambda data: (
                isinstance(data.get("driverScore"), dict)
                and data["driverScore"].get("driverScore") is not None
            ),
            "previousDriverScore": lambda data: (
                isinstance(data.get("driverScore"), dict)
                and data["driverScore"].get("previousDriverScore") is not None
            ),
            "predictedServiceDate": lambda data: (
                isinstance(data.get("service"), dict)
                and data["service"].get("predictedDate") is not None
            ),
        }

        entities.extend(
            VolkswagenGoConnectSensor(
                coordinator=coordinator,
                entity_description=desc,
                vehicle=vehicle,
            )
            for desc in ENTITY_DESCRIPTIONS
            if desc.key in base_sensors
        )

        entities.extend(
            VolkswagenGoConnectSensor(
                coordinator=coordinator,
                entity_description=desc,
                vehicle=vehicle,
            )
            for desc in ENTITY_DESCRIPTIONS
            if desc.key in conditional_sensors
            and conditional_sensors[desc.key](vehicle_data)
        )

        # Add fuel/charge sensors based on fuel type
        if is_electric:
            entities.extend(
                VolkswagenGoConnectSensor(
                    coordinator=coordinator,
                    entity_description=desc,
                    vehicle=vehicle,
                )
                for desc in ENTITY_DESCRIPTIONS
                if desc.key == "chargePercentage"
            )
        else:
            # For non-electric vehicles, add fuel percentage and level
            entities.extend(
                VolkswagenGoConnectSensor(
                    coordinator=coordinator,
                    entity_description=desc,
                    vehicle=vehicle,
                )
                for desc in ENTITY_DESCRIPTIONS
                if desc.key in {"fuelPercentage", "fuelLevel"}
            )

    async_add_entities(entities)


class VolkswagenGoConnectSensor(VolkswagenGoConnectEntity, SensorEntity):
    """volkswagen_goconnect Sensor class."""

    # Mapping for nested dict value extraction to avoid rebuilding per access
    _NESTED_EXTRACTORS: ClassVar[dict[str, Callable[[dict], Any]]] = {
        "fuelPercentage": lambda v: v.get("percent"),
        "fuelLevel": lambda v: v.get("liter"),
        "chargePercentage": lambda v: v.get("pct"),
        "odometer": lambda v: v.get("odometer"),
        "ignition": lambda v: v.get("on"),
        "rangeTotalKm": lambda v: v.get("km"),
        "highVoltageBatteryUsableCapacityKwh": lambda v: v.get("kwh"),
        "latestBatteryVoltage": lambda v: v.get("voltage"),
        "driverScore": lambda v: v.get("driverScore"),
    }
    _SPECIAL_VALUE_RESOLVERS: ClassVar[dict[str, str]] = {
        "brandContactInfo": "_resolve_brand_contact_info",
        "chargeEvents": "_resolve_charge_events",
        "chargingStatus": "_resolve_charging_status",
        "predictedServiceDate": "_resolve_predicted_service_date",
        "previousDriverScore": "_resolve_previous_driver_score",
        "workshop": "_resolve_workshop",
    }

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
            plate = getattr(self, "_license_plate", self.vehicle_id)
            self._attr_unique_id = f"vgc_{plate}_{entity_description.key}"

    @property
    def native_value(self) -> Any:  # noqa: PLR0911
        """Return the native value of the sensor."""
        if not self.vehicle_id:
            return self.coordinator.data.get("body")

        vehicle_data = self._get_vehicle_data_by_id(self.vehicle_id)
        if not vehicle_data:
            return None

        key = self.entity_description.key

        special_resolver = self._SPECIAL_VALUE_RESOLVERS.get(key)
        if special_resolver is not None:
            return getattr(self, special_resolver)(vehicle_data)

        if key not in vehicle_data:
            return None

        value = vehicle_data[key]
        if key in self._NESTED_EXTRACTORS and isinstance(value, dict):
            return self._NESTED_EXTRACTORS[key](value)

        if not isinstance(value, dict):
            return value

        return value

    def _resolve_previous_driver_score(self, vehicle_data: dict[str, Any]) -> Any:
        """Return previous driver score from the nested driver score payload."""
        driver_score = vehicle_data.get("driverScore")
        if isinstance(driver_score, dict):
            return driver_score.get("previousDriverScore")
        return None

    def _resolve_predicted_service_date(self, vehicle_data: dict[str, Any]) -> Any:
        """Return predicted service date from the nested service payload."""
        service_data = vehicle_data.get("service")
        if isinstance(service_data, dict):
            predicted_date = service_data.get("predictedDate")
            if isinstance(predicted_date, str):
                return self._parse_date(predicted_date)
            return predicted_date
        return None

    def _resolve_charge_events(self, vehicle_data: dict[str, Any]) -> Any:
        """Return the end time from the latest charge event."""
        charge_events = vehicle_data.get("chargeEvents")
        if isinstance(charge_events, list) and charge_events:
            first_event = charge_events[0]
            if isinstance(first_event, dict):
                end_time = first_event.get("endTime")
                if isinstance(end_time, str):
                    return self._parse_datetime(end_time)
                return end_time
        return None

    def _parse_date(self, value: str) -> date | None:
        """Parse an ISO date string from the API into a date object."""
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _parse_datetime(self, value: str) -> datetime | None:
        """Parse an ISO timestamp string from the API into an aware datetime."""
        parsed_datetime = dt_util.parse_datetime(value)
        if parsed_datetime is None:
            return None
        if parsed_datetime.tzinfo is None:
            return dt_util.as_utc(parsed_datetime.replace(tzinfo=dt_util.UTC))
        return dt_util.as_utc(parsed_datetime)

    def _resolve_charging_status(self, vehicle_data: dict[str, Any]) -> str | None:
        """Return a simplified charging status string."""
        value = vehicle_data.get("chargingStatus")
        if not isinstance(value, dict):
            return None
        self._charging_status_data = value
        return (
            "Charging"
            if value.get("startTime") and not value.get("endedAt")
            else "Not Charging"
        )

    def _resolve_workshop(self, vehicle_data: dict[str, Any]) -> str:
        """Return the workshop name when available."""
        value = vehicle_data.get("workshop")
        if isinstance(value, dict):
            self._workshop_data = value
            return value.get("name", "Available") if value else "Not Available"
        return "Not Available"

    def _resolve_brand_contact_info(self, vehicle_data: dict[str, Any]) -> str:
        """Return the brand roadside assistance name when available."""
        value = vehicle_data.get("brandContactInfo")
        if isinstance(value, dict):
            self._brand_data = value
            return value.get("roadsideAssistanceName", "Available")
        return "Not Available"

    def _get_vehicle_data_field(self, field_key: str, cache_attr: str) -> dict | None:
        """Get a specific field from vehicle data with caching."""
        # Try cache first
        data = getattr(self, cache_attr, None)
        if data is not None or not self.vehicle_id:
            return data

        vehicle_data = self._get_vehicle_data_by_id(self.vehicle_id)
        return vehicle_data.get(field_key) if vehicle_data else None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | float | None] | None:  # noqa: PLR0911
        """Return extra state attributes."""
        key = self.entity_description.key

        if key == "workshop":
            data = self._get_vehicle_data_field("workshop", "_workshop_data")
            if not data or not isinstance(data, dict):
                return None

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

        if key == "brandContactInfo":
            data = self._get_vehicle_data_field("brandContactInfo", "_brand_data")
            if not data or not isinstance(data, dict):
                return None

            return {
                "webshop_url": data.get("webshopUrl"),
                "webshop_name": data.get("webshopName"),
                "roadside_assistance_phone": data.get("roadsideAssistancePhoneNumber"),
                "roadside_assistance_name": data.get("roadsideAssistanceName"),
                "roadside_assistance_url": data.get("roadsideAssistanceUrl"),
                "roadside_emergency_assistance_url": data.get(
                    "roadsideEmergencyAssistanceUrl"
                ),
                "roadside_assistance_paid": data.get("roadsideAssistancePaid"),
            }

        if key == "chargingStatus":
            data = self._get_vehicle_data_field(
                "chargingStatus", "_charging_status_data"
            )
            if not data or not isinstance(data, dict):
                return None

            attributes = {
                "start_charge_percentage": data.get("startChargePercentage"),
                "start_time": data.get("startTime"),
                "ended_at": data.get("endedAt"),
                "charged_percentage": data.get("chargedPercentage"),
                "average_charge_speed": data.get("averageChargeSpeed"),
                "charge_in_kwh_increase": data.get("chargeInKwhIncrease"),
                "range_increase": data.get("rangeIncrease"),
                "time_until_80_percent_charge": data.get("timeUntil80PercentCharge"),
                "show_summary_for_charge_ended": data.get("showSummaryForChargeEnded"),
            }
            # Only return non-None attributes
            filtered_attributes = {k: v for k, v in attributes.items() if v is not None}
            return filtered_attributes or None

        return None
