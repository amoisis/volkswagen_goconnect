"""Service action to upload live data to ABRP for route planning."""

import json
import time

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from yarl import URL

from custom_components.volkswagen_goconnect.const import DOMAIN, LOGGER

ABRP_URL = "https://api.iternio.com/1/tlm/send"
HTTP_OK = 200


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
        # ABRP common telemetry fields (add more as needed)
        live_mapping = {
            "soc": data.get("battery_level"),
            "lat": data.get("latitude"),
            "lon": data.get("longitude"),
            "is_charging": data.get("charging_state"),
            "is_parked": data.get("parking_state"),
            "odometer": data.get("odometer"),
            "speed": data.get("speed"),
            "power": data.get("power"),
            "elevation": data.get("elevation"),
            "ext_temp": data.get("external_temperature"),
            "batt_temp": data.get("battery_temperature"),
            "voltage": data.get("voltage"),
            "current": data.get("current"),
            "est_battery_range": data.get("range_estimated"),
            # Add more fields as needed
        }
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
