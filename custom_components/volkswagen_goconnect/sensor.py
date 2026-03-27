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
from homeassistant.const import UnitOfElectricPotential, UnitOfSpeed, UnitOfTemperature
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
        key="speedometers",
        name="Speed",
        icon="mdi:speedometer-medium",
        device_class=SensorDeviceClass.SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outdoorTemperatures",
        name="Outdoor Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
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
        key="highVoltageBatteryTemperature",
        name="High Voltage Battery Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="batteryEfficiencyKmPerKwh",
        name="Battery Efficiency",
        icon="mdi:leaf",
        native_unit_of_measurement="km/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="averageBatteryConsumptionInKwhPer100Km",
        name="Average Battery Consumption",
        icon="mdi:flash",
        native_unit_of_measurement="kWh/100 km",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
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
    SensorEntityDescription(
        key="openErrorCodeLeads",
        name="Open Error Codes",
        icon="mdi:alert-circle",
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
            "openErrorCodeLeads",
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
            "speedometers": lambda data: (
                isinstance(data.get("speedometers"), list)
                and len(data["speedometers"]) > 0
                and isinstance(data["speedometers"][0], dict)
                and data["speedometers"][0].get("speed") is not None
            ),
            "outdoorTemperatures": lambda data: (
                isinstance(data.get("outdoorTemperatures"), list)
                and len(data["outdoorTemperatures"]) > 0
                and isinstance(data["outdoorTemperatures"][0], dict)
                and data["outdoorTemperatures"][0].get("celsius") is not None
            ),
            "highVoltageBatteryTemperature": lambda data: (
                isinstance(data.get("highVoltageBatteryTemperature"), dict)
                and data["highVoltageBatteryTemperature"].get("celsius") is not None
            ),
            "batteryEfficiencyKmPerKwh": lambda data: (
                data.get("batteryEfficiencyKmPerKwh") is not None
            ),
            "averageBatteryConsumptionInKwhPer100Km": lambda data: (
                isinstance(data.get("averageBatteryConsumptionInKwhPer100Km"), dict)
                and data["averageBatteryConsumptionInKwhPer100Km"].get(
                    "efficiencyKwhPer100Km"
                )
                is not None
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
        "averageBatteryConsumptionInKwhPer100Km": (
            "_resolve_average_battery_consumption"
        ),
        "batteryEfficiencyKmPerKwh": "_resolve_battery_efficiency",
        "brandContactInfo": "_resolve_brand_contact_info",
        "chargeEvents": "_resolve_charge_events",
        "chargingStatus": "_resolve_charging_status",
        "highVoltageBatteryTemperature": "_resolve_high_voltage_battery_temperature",
        "openErrorCodeLeads": "_resolve_open_error_code_leads",
        "outdoorTemperatures": "_resolve_outdoor_temperature",
        "predictedServiceDate": "_resolve_predicted_service_date",
        "previousDriverScore": "_resolve_previous_driver_score",
        "speedometers": "_resolve_latest_speed",
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
        self._open_error_code_leads_data = None
        self._all_error_code_leads_data = None
        self._latest_speed_data = None
        self._outdoor_temperature_data = None
        self._high_voltage_battery_temperature_data = None

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

    def _resolve_battery_efficiency(self, vehicle_data: dict[str, Any]) -> float | None:
        """Return battery efficiency rounded to two decimals."""
        value = vehicle_data.get("batteryEfficiencyKmPerKwh")
        if value is None:
            return None

        try:
            return round(float(value), 2)
        except (TypeError, ValueError):
            return None

    def _resolve_average_battery_consumption(
        self, vehicle_data: dict[str, Any]
    ) -> float | None:
        """Return average battery consumption rounded to two decimals."""
        value = vehicle_data.get("averageBatteryConsumptionInKwhPer100Km")
        if not isinstance(value, dict):
            return None

        efficiency = value.get("efficiencyKwhPer100Km")
        if efficiency is None:
            return None

        try:
            return round(float(efficiency), 2)
        except (TypeError, ValueError):
            return None

    def _resolve_high_voltage_battery_temperature(
        self, vehicle_data: dict[str, Any]
    ) -> float | None:
        """Return high voltage battery temperature in celsius."""
        value = vehicle_data.get("highVoltageBatteryTemperature")
        if not isinstance(value, dict):
            self._high_voltage_battery_temperature_data = None
            return None

        self._high_voltage_battery_temperature_data = value
        celsius = value.get("celsius")
        return float(celsius) if celsius is not None else None

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

    def _resolve_latest_speed(self, vehicle_data: dict[str, Any]) -> float | None:
        """Return the latest speed from the speed history list."""
        latest_speed = self._get_latest_list_item(vehicle_data, "speedometers")
        if latest_speed is None:
            self._latest_speed_data = None
            return None

        self._latest_speed_data = latest_speed
        speed = latest_speed.get("speed")
        return float(speed) if speed is not None else None

    def _resolve_outdoor_temperature(
        self, vehicle_data: dict[str, Any]
    ) -> float | None:
        """Return the latest outdoor temperature from the temperature history list."""
        latest_temperature = self._get_latest_list_item(
            vehicle_data, "outdoorTemperatures"
        )
        if latest_temperature is None:
            self._outdoor_temperature_data = None
            return None

        self._outdoor_temperature_data = latest_temperature
        celsius = latest_temperature.get("celsius")
        return float(celsius) if celsius is not None else None

    def _get_latest_list_item(
        self, vehicle_data: dict[str, Any], field_name: str
    ) -> dict[str, Any] | None:
        """Return the first item from a latest-first list payload."""
        items = vehicle_data.get(field_name)
        if not isinstance(items, list) or not items:
            return None

        latest_item = items[0]
        return latest_item if isinstance(latest_item, dict) else None

    def _has_latest_list_value(
        self, vehicle_data: dict[str, Any], field_name: str, value_key: str
    ) -> bool:
        """Return True when the latest list item contains a usable value."""
        latest_item = self._get_latest_list_item(vehicle_data, field_name)
        return latest_item is not None and latest_item.get(value_key) is not None

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

    def _resolve_open_error_code_leads(self, vehicle_data: dict[str, Any]) -> int:
        """Return open error code lead count."""
        leads = vehicle_data.get("openLeads")
        if not isinstance(leads, list):
            self._open_error_code_leads_data = []
            return 0

        error_code_leads = self._filter_error_code_leads(leads)
        self._open_error_code_leads_data = error_code_leads
        return len(error_code_leads)

    def _filter_error_code_leads(self, leads: list[Any]) -> list[dict[str, Any]]:
        """Return only leads that contain an error-code context."""
        error_code_leads: list[dict[str, Any]] = []
        for lead in leads:
            if not isinstance(lead, dict):
                continue

            context = lead.get("context")
            if (
                isinstance(context, dict)
                and context.get("__typename") == "LeadErrorCodeContext"
            ):
                error_code_leads.append(lead)

        return error_code_leads

    def _build_error_code_lead_row(self, lead: dict[str, Any]) -> dict[str, Any] | None:
        """Build a normalized row for lead table output."""
        context = lead.get("context")
        if not isinstance(context, dict):
            return None

        return {
            "id": lead.get("id"),
            "status": lead.get("status"),
            "dismissed": lead.get("dismissed"),
            "important": lead.get("important"),
            "severityscore": lead.get("severityScore"),
            "errorCode": context.get("errorCode"),
            "provider": context.get("provider"),
            "ecu": context.get("ecu"),
            "description": context.get("description"),
            "rawCode": context.get("rawCode"),
            "severity": context.get("severity"),
            "firsterrorcodetime": context.get("firstErrorCodeTime"),
            "lasterrorcodetime": context.get("lastErrorCodeTime"),
            "errorcodecount": context.get("errorCodeCount"),
        }

    def _build_error_code_table(
        self, rows: list[dict[str, Any]], empty_text: str
    ) -> str:
        """Build a markdown table from normalized rows."""
        if not rows:
            return empty_text

        header = (
            "| id | status | dismissed | important | severityscore | errorCode "
            "| provider | ecu | description | raw code | severity | "
            "firsterrorcodetime | lasterrorcodetime | errorcodecount |"
        )
        separator = "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
        table_lines = [header, separator]

        for row in rows:
            values = [
                row.get("id"),
                row.get("status"),
                row.get("dismissed"),
                row.get("important"),
                row.get("severityscore"),
                row.get("errorCode"),
                row.get("provider"),
                row.get("ecu"),
                row.get("description"),
                row.get("rawCode"),
                row.get("severity"),
                row.get("firsterrorcodetime"),
                row.get("lasterrorcodetime"),
                row.get("errorcodecount"),
            ]
            table_lines.append(
                "| " + " | ".join("" if v is None else str(v) for v in values) + " |"
            )

        return "\n".join(table_lines)

    def _get_vehicle_data_field(self, field_key: str, cache_attr: str) -> Any:
        """Get a specific field from vehicle data with caching."""
        # Try cache first
        data = getattr(self, cache_attr, None)
        if data is not None or not self.vehicle_id:
            return data

        vehicle_data = self._get_vehicle_data_by_id(self.vehicle_id)
        return vehicle_data.get(field_key) if vehicle_data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:  # noqa: PLR0911, PLR0912
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
            # Add operating hours if available
            opening_hours = data.get("openingHours")
            if opening_hours and isinstance(opening_hours, list):
                for hours in opening_hours:
                    if isinstance(hours, dict):
                        day = hours.get("day", "").lower()
                        from_time = hours.get("from")
                        to_time = hours.get("to")
                        if from_time and to_time:
                            key_name = f"operating_hours_{day}"
                            attributes[key_name] = f"{from_time}-{to_time}"
            return attributes

        if key == "brandContactInfo":
            data = self._get_vehicle_data_field("brandContactInfo", "_brand_data")
            if not data or not isinstance(data, dict):
                return None

            return {
                "roadside_assistance_phone": data.get("roadsideAssistancePhoneNumber"),
                "roadside_assistance_name": data.get("roadsideAssistanceName"),
                "roadside_assistance_url": data.get("roadsideAssistanceUrl"),
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

        if key == "speedometers":
            data = self._get_vehicle_data_field("speedometers", "_latest_speed_data")
            latest_speed = data[0] if isinstance(data, list) and data else data
            if not latest_speed or not isinstance(latest_speed, dict):
                return None

            return {"time": latest_speed.get("time")}

        if key == "outdoorTemperatures":
            data = self._get_vehicle_data_field(
                "outdoorTemperatures", "_outdoor_temperature_data"
            )
            latest_temperature = data[0] if isinstance(data, list) and data else data
            if not latest_temperature or not isinstance(latest_temperature, dict):
                return None

            return {"time": latest_temperature.get("time")}

        if key == "highVoltageBatteryTemperature":
            data = self._get_vehicle_data_field(
                "highVoltageBatteryTemperature",
                "_high_voltage_battery_temperature_data",
            )
            if not data or not isinstance(data, dict):
                return None

            return {"time": data.get("time")}

        if key == "openErrorCodeLeads":
            data = self._get_vehicle_data_field(
                "openLeads", "_open_error_code_leads_data"
            )
            if not data or not isinstance(data, list):
                return {
                    "lead_count": 0,
                    "open_lead_count": 0,
                    "closed_lead_count": 0,
                    "all_lead_count": 0,
                    "rows": [],
                    "table": "No open error code leads",
                    "open_rows": [],
                    "open_table": "No open error code leads",
                    "closed_rows": [],
                    "closed_table": "No closed error code leads",
                    "all_rows": [],
                    "all_table": "No error code leads",
                }

            rows = [
                row
                for row in (self._build_error_code_lead_row(lead) for lead in data)
                if row is not None
            ]

            all_data = self._get_vehicle_data_field(
                "allLeads", "_all_error_code_leads_data"
            )
            all_leads: list[dict[str, Any]] = []
            if isinstance(all_data, list):
                all_leads = self._filter_error_code_leads(all_data)

            all_rows = [
                row
                for row in (self._build_error_code_lead_row(lead) for lead in all_leads)
                if row is not None
            ]
            closed_rows = [row for row in all_rows if row.get("status") == "closed"]
            open_rows = [row for row in all_rows if row.get("status") == "open"]

            return {
                "lead_count": len(rows),
                "open_lead_count": len(open_rows) if all_rows else len(rows),
                "closed_lead_count": len(closed_rows),
                "all_lead_count": len(all_rows) if all_rows else len(rows),
                "rows": rows,
                "table": self._build_error_code_table(rows, "No open error code leads"),
                "open_rows": open_rows if all_rows else rows,
                "open_table": self._build_error_code_table(
                    open_rows if all_rows else rows,
                    "No open error code leads",
                ),
                "closed_rows": closed_rows,
                "closed_table": self._build_error_code_table(
                    closed_rows,
                    "No closed error code leads",
                ),
                "all_rows": all_rows or rows,
                "all_table": self._build_error_code_table(
                    all_rows or rows,
                    "No error code leads",
                ),
            }

        return None
