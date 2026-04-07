"""Service action to upload live data to ABRP for route planning."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError
from yarl import URL

from custom_components.volkswagen_goconnect.const import (
    ABRP_COUNTER_CACHE_MAX_ENTRIES,
    ABRP_COUNTER_CACHE_TTL_SECONDS,
    ABRP_HTTP_OK,
    ABRP_URL,
    DOMAIN,
    LOGGER,
    POWER_MAX_INTERVAL_SECONDS,
    POWER_MAX_STREAM_DRIFT_SECONDS,
    SERIES_MIN_POINTS,
)
from custom_components.volkswagen_goconnect.entity import VolkswagenGoConnectEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


_ABRP_COUNTER_CACHE: dict[str, tuple[float, float, datetime, datetime, datetime]] = {}


def _prune_counter_cache(now: datetime) -> None:
    """Prune stale entries and enforce global cache size limits."""
    stale_vehicle_ids = [
        vehicle_id
        for vehicle_id, value in _ABRP_COUNTER_CACHE.items()
        if (now - value[4]).total_seconds() > ABRP_COUNTER_CACHE_TTL_SECONDS
    ]
    for vehicle_id in stale_vehicle_ids:
        _ABRP_COUNTER_CACHE.pop(vehicle_id, None)

    over_limit = len(_ABRP_COUNTER_CACHE) - ABRP_COUNTER_CACHE_MAX_ENTRIES
    if over_limit <= 0:
        return

    oldest_vehicle_ids = sorted(
        _ABRP_COUNTER_CACHE.items(),
        key=lambda item: item[1][4],
    )[:over_limit]
    for vehicle_id, _value in oldest_vehicle_ids:
        _ABRP_COUNTER_CACHE.pop(vehicle_id, None)


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


def _build_live_mapping(vehicle_data: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Build ABRP telemetry defaults from the latest vehicle payload."""
    charge_percentage = vehicle_data.get("chargePercentage")
    position = vehicle_data.get("position")
    odometer = vehicle_data.get("odometer")
    range_total = vehicle_data.get("rangeTotalKm")
    battery_usable_capacity = vehicle_data.get("highVoltageBatteryUsableCapacityKwh")
    car_battery_charge = vehicle_data.get("carBatteryCharge")
    car_battery_discharge = vehicle_data.get("carBatteryDischarge")
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
    if (
        soe is None
        and isinstance(car_battery_charge, dict)
        and isinstance(car_battery_discharge, dict)
    ):
        try:
            charge_kwh = car_battery_charge.get("kwh")
            discharge_kwh = car_battery_discharge.get("kwh")
            if charge_kwh is not None and discharge_kwh is not None:
                soe = round(float(charge_kwh) - float(discharge_kwh), 3)
        except (TypeError, ValueError):
            soe = None

    capacity = None
    try:
        if soc is not None and soe is not None and float(soc) > 0:
            capacity = round(float(soe) / (float(soc) / 100.0), 3)
    except (TypeError, ValueError):
        capacity = None

    power_kw, power_source = _resolve_power_kw(vehicle_data)

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
        "power": power_kw,
        "soe": soe,
        "capacity": capacity,
    }, power_source


def _parse_timestamp(value: Any) -> datetime | None:
    """Parse API timestamp strings into timezone-aware datetimes."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _resolve_power_from_series(  # noqa: PLR0911
    vehicle_data: dict[str, Any],
) -> float | None:
    """Calculate net power from latest two samples in cumulative series lists."""
    charge_series = vehicle_data.get("carBatteryCharges")
    discharge_series = vehicle_data.get("carBatteryDischarges")
    if (
        not isinstance(charge_series, list)
        or not isinstance(discharge_series, list)
        or len(charge_series) < SERIES_MIN_POINTS
        or len(discharge_series) < SERIES_MIN_POINTS
    ):
        return None

    charge_latest = charge_series[0]
    charge_previous = charge_series[1]
    discharge_latest = discharge_series[0]
    discharge_previous = discharge_series[1]
    if (
        not isinstance(charge_latest, dict)
        or not isinstance(charge_previous, dict)
        or not isinstance(discharge_latest, dict)
        or not isinstance(discharge_previous, dict)
    ):
        return None

    charge_latest_kwh_raw = charge_latest.get("kwh")
    charge_previous_kwh_raw = charge_previous.get("kwh")
    discharge_latest_kwh_raw = discharge_latest.get("kwh")
    discharge_previous_kwh_raw = discharge_previous.get("kwh")
    if (
        charge_latest_kwh_raw is None
        or charge_previous_kwh_raw is None
        or discharge_latest_kwh_raw is None
        or discharge_previous_kwh_raw is None
    ):
        return None

    try:
        charge_latest_kwh = float(charge_latest_kwh_raw)
        charge_previous_kwh = float(charge_previous_kwh_raw)
        discharge_latest_kwh = float(discharge_latest_kwh_raw)
        discharge_previous_kwh = float(discharge_previous_kwh_raw)
    except (TypeError, ValueError):
        return None

    charge_latest_time = _parse_timestamp(charge_latest.get("time"))
    charge_previous_time = _parse_timestamp(charge_previous.get("time"))
    discharge_latest_time = _parse_timestamp(discharge_latest.get("time"))
    discharge_previous_time = _parse_timestamp(discharge_previous.get("time"))
    if (
        charge_latest_time is None
        or charge_previous_time is None
        or discharge_latest_time is None
        or discharge_previous_time is None
    ):
        return None

    charge_delta_seconds = (charge_latest_time - charge_previous_time).total_seconds()
    discharge_delta_seconds = (
        discharge_latest_time - discharge_previous_time
    ).total_seconds()
    if charge_delta_seconds <= 0 or discharge_delta_seconds <= 0:
        return None
    if (
        charge_delta_seconds > POWER_MAX_INTERVAL_SECONDS
        or discharge_delta_seconds > POWER_MAX_INTERVAL_SECONDS
    ):
        return None

    stream_drift_seconds = abs(
        (discharge_latest_time - charge_latest_time).total_seconds()
    )
    if stream_drift_seconds > POWER_MAX_STREAM_DRIFT_SECONDS:
        return None

    charge_delta_kwh = charge_latest_kwh - charge_previous_kwh
    discharge_delta_kwh = discharge_latest_kwh - discharge_previous_kwh
    if charge_delta_kwh < 0 or discharge_delta_kwh < 0:
        return None

    charge_kw = charge_delta_kwh * 3600.0 / charge_delta_seconds
    discharge_kw = discharge_delta_kwh * 3600.0 / discharge_delta_seconds
    return round(discharge_kw - charge_kw, 3)


def _resolve_power_from_counters_with_cache(  # noqa: PLR0911
    vehicle_data: dict[str, Any],
) -> float | None:
    """Calculate net power from single cumulative counters using cached history."""
    vehicle_id = vehicle_data.get("id")
    charge_counter = vehicle_data.get("carBatteryCharge")
    discharge_counter = vehicle_data.get("carBatteryDischarge")
    if (
        not isinstance(vehicle_id, str)
        or not isinstance(charge_counter, dict)
        or not isinstance(discharge_counter, dict)
    ):
        return None

    charge_kwh_raw = charge_counter.get("kwh")
    discharge_kwh_raw = discharge_counter.get("kwh")
    if charge_kwh_raw is None or discharge_kwh_raw is None:
        return None

    try:
        charge_kwh = float(charge_kwh_raw)
        discharge_kwh = float(discharge_kwh_raw)
    except (TypeError, ValueError):
        return None

    charge_time = _parse_timestamp(charge_counter.get("time"))
    discharge_time = _parse_timestamp(discharge_counter.get("time"))
    if charge_time is None or discharge_time is None:
        return None

    stream_drift_seconds = abs((discharge_time - charge_time).total_seconds())
    now = datetime.now(UTC)
    _prune_counter_cache(now)

    previous = _ABRP_COUNTER_CACHE.get(vehicle_id)
    _ABRP_COUNTER_CACHE[vehicle_id] = (
        charge_kwh,
        discharge_kwh,
        charge_time,
        discharge_time,
        now,
    )
    if stream_drift_seconds > POWER_MAX_STREAM_DRIFT_SECONDS or previous is None:
        return None

    (
        previous_charge_kwh,
        previous_discharge_kwh,
        previous_charge_time,
        previous_discharge_time,
        _previous_seen_time,
    ) = previous
    charge_delta_seconds = (charge_time - previous_charge_time).total_seconds()
    discharge_delta_seconds = (discharge_time - previous_discharge_time).total_seconds()
    if charge_delta_seconds <= 0 or discharge_delta_seconds <= 0:
        return None
    if (
        charge_delta_seconds > POWER_MAX_INTERVAL_SECONDS
        or discharge_delta_seconds > POWER_MAX_INTERVAL_SECONDS
    ):
        return None

    charge_delta_kwh = charge_kwh - previous_charge_kwh
    discharge_delta_kwh = discharge_kwh - previous_discharge_kwh
    if charge_delta_kwh < 0 or discharge_delta_kwh < 0:
        return None

    charge_kw = charge_delta_kwh * 3600.0 / charge_delta_seconds
    discharge_kw = discharge_delta_kwh * 3600.0 / discharge_delta_seconds
    return round(discharge_kw - charge_kw, 3)


def _resolve_power_kw(vehicle_data: dict[str, Any]) -> tuple[float | None, str]:
    """Calculate net battery power usage in kW for ABRP payload."""
    power_from_series = _resolve_power_from_series(vehicle_data)
    if power_from_series is not None:
        return power_from_series, "series"

    power_from_cache = _resolve_power_from_counters_with_cache(vehicle_data)
    if power_from_cache is not None:
        return power_from_cache, "cache"

    return None, "none"


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
    normalized_plate = license_plate.strip().lower()

    # Use service_data if provided, else fall back to coordinator data
    tlm = dict(service_data) if service_data else {}

    # Fill in any missing ABRP telemetry fields from live data (coordinator)
    vehicle_data = _get_vehicle_data_from_entries(hass, license_plate)

    if not vehicle_data:
        msg = f"Vehicle with license plate '{license_plate}' not found"
        LOGGER.error(msg)
        raise HomeAssistantError(msg)

    live_mapping, power_source = _build_live_mapping(vehicle_data)
    if live_mapping:
        for k, v in live_mapping.items():
            # User-provided values override live values, except explicit nulls
            # which should be treated as missing and safely backfilled.
            if (k not in tlm or tlm.get(k) is None) and v is not None:
                tlm[k] = v

    LOGGER.debug(
        "ABRP power source for plate=%s: %s (included=%s)",
        normalized_plate,
        power_source,
        "power" in tlm,
    )

    if "utc" not in tlm:
        tlm["utc"] = int(time.time())

    # Remove None values
    tlm = {k: v for k, v in tlm.items() if v is not None}

    LOGGER.debug(
        "ABRP send prepared for plate=%s with payload keys=%s",
        normalized_plate,
        sorted(tlm.keys()),
    )

    if not all(k in tlm for k in ("soc", "lat", "lon")):
        msg = "Missing required data for ABRP (soc, lat, lon)"
        LOGGER.error(msg)
        raise HomeAssistantError(msg)

    headers = {"Authorization": f"APIKEY {api_key}"}
    # tlm must be a JSON string, urlencoded
    tlm_json = json.dumps(tlm, separators=(",", ":"))
    url = URL(ABRP_URL).with_query({"token": token, "tlm": tlm_json})
    request_started = time.monotonic()

    try:
        async with (
            aiohttp.ClientSession() as session,
            session.post(str(url), headers=headers, data=None) as response,
        ):
            elapsed_ms = int((time.monotonic() - request_started) * 1000)
            LOGGER.debug(
                "ABRP response for plate=%s status=%s elapsed_ms=%s",
                normalized_plate,
                response.status,
                elapsed_ms,
            )
            if response.status != ABRP_HTTP_OK:
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
