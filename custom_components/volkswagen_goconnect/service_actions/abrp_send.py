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


def _get_first_vehicle_data(data: dict[str, Any] | None) -> dict[str, Any]:
    """Return the first vehicle payload from coordinator data."""
    vehicles = VolkswagenGoConnectEntity.extract_vehicles(data)
    if not vehicles:
        return {}

    first_vehicle = vehicles[0]
    if not isinstance(first_vehicle, dict):
        return {}

    vehicle = first_vehicle.get("vehicle")
    return vehicle if isinstance(vehicle, dict) else {}


def _build_live_mapping(vehicle_data: dict[str, Any]) -> dict[str, Any]:
    """Build ABRP telemetry defaults from the latest vehicle payload."""
    charge_percentage = vehicle_data.get("chargePercentage")
    position = vehicle_data.get("position")
    odometer = vehicle_data.get("odometer")
    range_total = vehicle_data.get("rangeTotalKm")
    latest_speed = _get_latest_list_item(vehicle_data, "speedometers")
    latest_outdoor_temperature = _get_latest_list_item(
        vehicle_data, "outdoorTemperatures"
    )

    return {
        "soc": (
            charge_percentage.get("pct")
            if isinstance(charge_percentage, dict)
            else None
        ),
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
    }


async def async_abrp_send_service(
    hass: HomeAssistant, api_key: str, token: str, service_data: dict | None = None
) -> None:
    """Upload live data to ABRP."""
    # Use service_data if provided, else fall back to coordinator data
    tlm = dict(service_data) if service_data else {}

    # Fill in any missing ABRP telemetry fields from live data (coordinator)
    entry = next(iter(hass.config_entries.async_entries(DOMAIN)), None)
    coordinator = (
        getattr(getattr(entry, "runtime_data", None), "coordinator", None)
        if entry
        else None
    )
    data = getattr(coordinator, "data", None) if coordinator else None
    if data:
        live_mapping = _build_live_mapping(_get_first_vehicle_data(data))
        for k, v in live_mapping.items():
            if k not in tlm and v is not None:
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
