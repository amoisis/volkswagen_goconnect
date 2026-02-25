"""Service action to upload live data to ABRP for route planning."""

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.volkswagen_goconnect.const import LOGGER

ABRP_URL = "https://api.iternio.com/1/tlm/send"
HTTP_OK = 200


async def async_abrp_send_service(hass: HomeAssistant, token: str) -> None:
    """Upload live data to ABRP."""
    # Get the coordinator from the first config entry
    entries = hass.config_entries.async_entries("volkswagen_goconnect")
    if not entries:
        msg = "No Volkswagen GoConnect integration found"
        LOGGER.error(msg)
        raise HomeAssistantError(msg)

    entry = entries[0]
    if "coordinator" not in entry.runtime_data:
        msg = "Coordinator not found"
        LOGGER.error(msg)
        raise HomeAssistantError(msg)

    coordinator = entry.runtime_data["coordinator"]
    data = coordinator.data

    if not data:
        msg = "No data available from coordinator"
        LOGGER.error(msg)
        raise HomeAssistantError(msg)

    # Extract required data
    soc = data.get("battery_level")
    is_charging = data.get("charging_state") == "charging"
    is_parked = data.get("parking_state") == "parked"
    lat = data.get("latitude")
    lon = data.get("longitude")
    odometer = data.get("odometer")

    if soc is None or lat is None or lon is None:
        msg = "Missing required data for ABRP"
        LOGGER.error("Missing required data for ABRP (soc, lat, lon)")
        raise HomeAssistantError(msg)

    payload = {
        "tlm": {
            "soc": soc,
            "is_charging": is_charging,
            "is_parked": is_parked,
            "lat": lat,
            "lon": lon,
            "odometer": odometer,
        }
    }

    url = f"{ABRP_URL}?token={token}"

    try:
        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload) as response,
        ):
            if response.status != HTTP_OK:
                msg = f"ABRP API error: {response.status}"
                LOGGER.error("Failed to send data to ABRP: %s", response.status)
                raise HomeAssistantError(msg)
            LOGGER.debug("Successfully sent data to ABRP")
    except aiohttp.ClientError as err:
        msg = f"ABRP communication error: {err}"
        LOGGER.error("Error communicating with ABRP: %s", err)
        raise HomeAssistantError(msg) from err
