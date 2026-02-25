"""Service action to upload live data to ABRP for route planning."""

import aiohttp
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.template import Template
from homeassistant.helpers.entity import Entity
from homeassistant.helpers import entity_registry
from homeassistant.exceptions import HomeAssistantError
from ..const import LOGGER

ABRP_URL = "https://api.iternio.com/1/tlm/send"


async def async_abrp_send_service(
    hass: HomeAssistant, call: ServiceCall, token: str
) -> None:
    """Upload live data to ABRP."""
    # Render templates for each value
    utc = hass.helpers.template.Template(
        "{{ as_timestamp(now().utcnow()) | float() }}", hass
    ).async_render()
    soc = hass.helpers.template.Template(
        "{{ states('sensor.charge_percentage') }}", hass
    ).async_render()
    lat = hass.helpers.template.Template(
        "{{ state_attr('device_tracker.location', 'latitude') }}", hass
    ).async_render()
    lon = hass.helpers.template.Template(
        "{{ state_attr('device_tracker.location', 'longitude') }}", hass
    ).async_render()
    is_charging = hass.helpers.template.Template(
        "{{ states('binary_sensor.charging') }}", hass
    ).async_render()
    odometer = hass.helpers.template.Template(
        "{{ states('sensor.odometer') }}", hass
    ).async_render()

    payload = {
        "token": token,
        "utc": utc,
        "soc": soc,
        "lat": lat,
        "lon": lon,
        "is_charging": is_charging,
        "odometer": odometer,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(ABRP_URL, json=payload) as resp:
            if resp.status != 200:
                LOGGER.error(
                    "ABRP upload failed: %s %s", resp.status, await resp.text()
                )
                raise HomeAssistantError(
                    f"ABRP upload failed: {resp.status} {await resp.text()}"
                )
            else:
                LOGGER.info("ABRP upload successful: %s", resp.status)
