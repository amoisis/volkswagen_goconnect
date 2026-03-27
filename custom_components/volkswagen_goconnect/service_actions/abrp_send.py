"""Service action to upload live data to ABRP for route planning."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError
from yarl import URL

from custom_components.volkswagen_goconnect.const import DOMAIN, LOGGER
from custom_components.volkswagen_goconnect.entity import VolkswagenGoConnectEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

ABRP_URL = "https://api.iternio.com/1/tlm/send"
HTTP_OK = 200


def _get_latest_list_item(
    vehicle_data: dict[str, Any], field_name: str
) -> dict[str, Any] | None:
    """Return the latest item from a latest-first list payload."""
    items = vehicle_data.get(field_name)
    if not isinstance(items, list) or not items:
        return None

    latest_item = items[0]
    return latest_item if isinstance(latest_item, dict) else None


def _get_vehicle_data_by_license_plate(
    data: dict[str, Any] | None, license_plate: str
) -> dict[str, Any]:
    """Return vehicle payload matching the provided license plate."""
    vehicles = VolkswagenGoConnectEntity.extract_vehicles(data)
    if not vehicles:
        return {}

    normalized_plate = license_plate.strip().upper()
    for vehicle_entry in vehicles:
        if not isinstance(vehicle_entry, dict):
            continue

        vehicle = vehicle_entry.get("vehicle")
        if not isinstance(vehicle, dict):
            continue

        plate = vehicle.get("licensePlate")
        if isinstance(plate, str) and plate.strip().upper() == normalized_plate:
            return vehicle

    return {}


def _build_live_mapping(vehicle_data: dict[str, Any]) -> dict[str, Any]:
    """Build ABRP telemetry defaults from the latest vehicle payload."""
    charge_percentage = vehicle_data.get("chargePercentage")
    position = vehicle_data.get("position")
    odometer = vehicle_data.get("odometer")
    range_total = vehicle_data.get("rangeTotalKm")
    battery_usable_capacity = vehicle_data.get("highVoltageBatteryUsableCapacityKwh")
    battery_temperature = vehicle_data.get("highVoltageBatteryTemperature")
    latest_speed = _get_latest_list_item(vehicle_data, "speedometers")
    latest_outdoor_temperature = _get_latest_list_item(
        vehicle_data, "outdoorTemperatures"
    )

    soc = charge_percentage.get("pct") if isinstance(charge_percentage, dict) else None
    soe = (
        battery_usable_capacity.get("kwh")
        if isinstance(battery_usable_capacity, dict)
        else None
    )

    capacity = None
    try:
        if soc is not None and soe is not None and float(soc) > 0:
            capacity = round(float(soe) / (float(soc) / 100.0), 3)
    except (TypeError, ValueError):
        capacity = None

    return {
        "soc": soc,
        "lat": position.get("latitude") if isinstance(position, dict) else None,
        "lon": position.get("longitude") if isinstance(position, dict) else None,
        "is_charging": vehicle_data.get("isCharging"),
        "odometer": (odometer.get("odometer") if isinstance(odometer, dict) else None),
        "speed": latest_speed.get("speed") if isinstance(latest_speed, dict) else None,
        "ext_temp": (
            latest_outdoor_temperature.get("celsius")
            if isinstance(latest_outdoor_temperature, dict)
            else None
        ),
        "est_battery_range": (
            range_total.get("km") if isinstance(range_total, dict) else None
        ),
        "batt_temp": (
            battery_temperature.get("celsius")
            if isinstance(battery_temperature, dict)
            else None
        ),
        "soe": soe,
        "capacity": capacity,
    }


def _get_vehicle_data_from_entries(
    hass: HomeAssistant, license_plate: str
) -> dict[str, Any]:
    """Return matching vehicle data, preferring ABRP coordinator snapshots."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        runtime_data = getattr(entry, "runtime_data", None)
        coordinator_candidates = (
            getattr(runtime_data, "abrp_coordinator", None),
            getattr(runtime_data, "coordinator", None),
        )

        for coordinator in coordinator_candidates:
            data = getattr(coordinator, "data", None) if coordinator else None
            vehicle_data = _get_vehicle_data_by_license_plate(data, license_plate)
            if vehicle_data:
                return vehicle_data
    return {}


async def async_abrp_send_service(
    hass: HomeAssistant,
    api_key: str,
    token: str,
    license_plate: str,
    service_data: dict | None = None,
) -> None:
    """Upload live data to ABRP."""
    # Use service_data if provided, else fall back to coordinator data
    tlm = dict(service_data) if service_data else {}

    # Fill in any missing ABRP telemetry fields from live data (coordinator)
    vehicle_data = _get_vehicle_data_from_entries(hass, license_plate)

    if not vehicle_data:
        msg = f"Vehicle with license plate '{license_plate}' not found"
        LOGGER.error(msg)
        raise HomeAssistantError(msg)

    live_mapping = _build_live_mapping(vehicle_data)
    if live_mapping:
        for k, v in live_mapping.items():
            # User-provided values override live values, except explicit nulls
            # which should be treated as missing and safely backfilled.
            if (k not in tlm or tlm.get(k) is None) and v is not None:
                tlm[k] = v

    if "utc" not in tlm:
        tlm["utc"] = int(time.time())

    # Remove None values
    tlm = {k: v for k, v in tlm.items() if v is not None}

    if not all(k in tlm for k in ("soc", "lat", "lon")):
        msg = "Missing required data for ABRP (soc, lat, lon)"
        LOGGER.error(msg)
        raise HomeAssistantError(msg)

    headers = {"Authorization": f"APIKEY {api_key}"}
    # tlm must be a JSON string, urlencoded
    tlm_json = json.dumps(tlm, separators=(",", ":"))
    url = URL(ABRP_URL).with_query({"token": token, "tlm": tlm_json})

    try:
        async with (
            aiohttp.ClientSession() as session,
            session.post(str(url), headers=headers, data=None) as response,
        ):
            if response.status != HTTP_OK:
                # Try to parse error details from JSON body, else use plain text
                body = await response.text()
                msg = f"ABRP API error: {response.status}"
                try:
                    data = json.loads(body)
                    error_detail = (
                        data.get("errors") or data.get("error") or data.get("status")
                    )
                    if error_detail:
                        msg += f" - {error_detail}"
                except json.JSONDecodeError:
                    if body:
                        msg += f" - {body.strip()}"
                    else:
                        msg += " (no error details)"
                LOGGER.error(
                    "Failed to send data to ABRP: %s | URL: %s | tlm: %s",
                    msg,
                    str(url),
                    tlm_json,
                )
                raise HomeAssistantError(msg)
            LOGGER.debug("Successfully sent data to ABRP")
    except aiohttp.ClientError as err:
        msg = f"ABRP communication error: {err}"
        LOGGER.error("Error communicating with ABRP: %s", err)
        raise HomeAssistantError(msg) from err
