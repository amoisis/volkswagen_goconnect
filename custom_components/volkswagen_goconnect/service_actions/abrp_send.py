"""Service action to upload live data to ABRP for route planning."""

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.volkswagen_goconnect.const import LOGGER

ABRP_URL = "https://api.iternio.com/1/tlm/send"
HTTP_OK = 200
async def async_abrp_send_service(
    hass: HomeAssistant, token: str, service_data: dict | None = None
) -> None:
    """Upload live data to ABRP."""
    # Use service_data if provided, else fall back to coordinator data
    tlm = {}
    if service_data:
        tlm.update(service_data)

    # If any high-priority fields are missing, try to fill from coordinator
    if not all(k in tlm for k in ("soc", "lat", "lon")):
        entries = hass.config_entries.async_entries("volkswagen_goconnect")
        if entries:
            entry = entries[0]
            runtime_data = getattr(entry, "runtime_data", None)
            if runtime_data and hasattr(runtime_data, "coordinator"):
                coordinator = runtime_data.coordinator
                data = coordinator.data
                if data:
                    # Map Home Assistant data keys to ABRP keys if possible
                    if "soc" not in tlm:
                        tlm["soc"] = data.get("battery_level")
                    if "lat" not in tlm:
                        tlm["lat"] = data.get("latitude")
                    if "lon" not in tlm:
                        tlm["lon"] = data.get("longitude")
                    if "is_charging" not in tlm:
                        tlm["is_charging"] = data.get("charging_state") == "charging"
                    if "is_parked" not in tlm:
                        tlm["is_parked"] = data.get("parking_state") == "parked"
                    if "odometer" not in tlm:
                        tlm["odometer"] = data.get("odometer")


    # Remove None values
    tlm = {k: v for k, v in tlm.items() if v is not None}

    if not all(k in tlm for k in ("soc", "lat", "lon")):
        msg = "Missing required data for ABRP (soc, lat, lon)"
        LOGGER.error(msg)
        raise HomeAssistantError(msg)

    payload = {"tlm": tlm}
    url = f"{ABRP_URL}?token={token}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != HTTP_OK:
                    msg = f"ABRP API error: {response.status}"
                    LOGGER.error("Failed to send data to ABRP: %s", response.status)
                    raise HomeAssistantError(msg)
                LOGGER.debug("Successfully sent data to ABRP")
    except aiohttp.ClientError as err:
        msg = f"ABRP communication error: {err}"
        LOGGER.error("Error communicating with ABRP: %s", err)
        raise HomeAssistantError(msg) from err
