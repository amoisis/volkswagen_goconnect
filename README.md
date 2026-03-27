# Volkswagen GoConnect Integration for Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/amoisis/volkswagen_goconnect?style=flat-square)](https://github.com/amoisis/volkswagen_goconnect/releases)
[![Tests & Coverage](https://img.shields.io/github/actions/workflow/status/amoisis/volkswagen_goconnect/tests.yml?style=flat-square&label=tests)](https://github.com/amoisis/volkswagen_goconnect/actions/workflows/tests.yml)
[![codecov](https://img.shields.io/codecov/c/github/amoisis/volkswagen_goconnect?style=flat-square)](https://codecov.io/gh/amoisis/volkswagen_goconnect)
[![Last Commit](https://img.shields.io/github/last-commit/amoisis/volkswagen_goconnect?style=flat-square)](https://github.com/amoisis/volkswagen_goconnect/commits)

Volkswagen GoConnect lets you monitor your vehicle from Home Assistant using your Volkswagen GoConnect account.

## What This Integration Provides

After setup, the integration creates entities for each connected vehicle in your account.

### Sensors

One entity per vehicle is created for each row below. Fuel/charge sensors depend on the vehicle's fuel type.

| Entity | Key | Unit | Notes |
|---|---|---|---|
| Vehicle ID | `id` | — | Internal identifier |
| VIN | `vin` | — | |
| License Plate | `licensePlate` | — | |
| Make | `make` | — | |
| Model | `model` | — | |
| Year | `year` | — | |
| Fuel Type | `fuelType` | — | e.g. `electric`, `petrol` |
| Odometer | `odometer` | km | State class: total_increasing |
| Ignition | `ignition` | — | Raw ignition value from API |
| Range Total | `rangeTotalKm` | km | Combined estimated range |
| Speed | `speedometers` | km/h | Latest speed sample when available |
| Outdoor Temperature | `outdoorTemperatures` | °C | Latest outdoor temperature sample when available |
| Charging Status | `chargingStatus` | — | Charging state string from API |
| Battery Capacity | `highVoltageBatteryUsableCapacityKwh` | kWh | Estimated full capacity at 100%, derived from SoE and charge percentage |
| Battery State Of Energy | `batteryStateOfEnergyKwh` | kWh | Current energy value from API (`highVoltageBatteryUsableCapacityKwh.kwh`) |
| Battery Temperature | `highVoltageBatteryTemperature` | °C | High-voltage (EV) battery temperature |
| Average Battery Consumption (km/kWh) | `batteryEfficiencyKmPerKwh` | km/kWh | EV average efficiency from statistics |
| Average Battery Consumption (kWh/100 km) | `averageBatteryConsumptionInKwhPer100Km` | kWh/100 km | EV average energy consumption |
| Open Error Codes | `openErrorCodeLeads` | — | State is count of open error-code leads; attributes include `rows` and `table` |
| Workshop | `workshop` | — | Assigned workshop name |
| Brand Contact Info | `brandContactInfo` | — | Manufacturer support details |
| **Charge Percentage** | `chargePercentage` | % | **Electric vehicles only** |
| **Fuel Percentage** | `fuelPercentage` | % | **Non-electric vehicles only** |
| **Fuel Level** | `fuelLevel` | L | **Non-electric vehicles only** |

### Binary Sensors

| Entity | Key | Device Class | Notes |
|---|---|---|-|
| Charging | `isCharging` | `battery_charging` | True when actively charging |
| Blocked | `isBlocked` | `problem` | True when vehicle is blocked |
| Activated | `activated` | `connectivity` | True when vehicle connectivity is active |
| ABRP Data Changed | `abrp_data_changed` | — | True when telemetry has changed since last upload (only when ABRP enabled) |

### Device Tracker

| Entity | Source Type | Notes |
|---|---|---|
| Location | GPS | Created only when the API returns a vehicle position |

### Service Actions

| Service | Description |
|---|---|
| `volkswagen_goconnect.abrp_send` | Send live telemetry to A Better Routeplanner (ABRP) |
| `volkswagen_goconnect.abrp_acknowledge` | Reset the ABRP Data Changed sensor after a successful upload |

## Installation

### Via HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=amoisis&repository=volkswagen-goconnect&category=integration)

1. Open HACS in Home Assistant.
2. Go to Integrations.
3. Add this repository as a custom repository:
	- URL: `https://github.com/amoisis/volkswagen_goconnect`
	- Category: Integration
4. Install Volkswagen GoConnect from HACS.
5. Restart Home Assistant.

### Manual Installation

1. Download the latest release from the releases page.
2. Copy `custom_components/volkswagen_goconnect` into your Home Assistant config directory.
3. Restart Home Assistant.

## Configuration

After installation, configure the integration in Home Assistant:

1. Go to Settings -> Devices & Services.
2. Select Add Integration.
3. Search for Volkswagen GoConnect.
4. Enter your Volkswagen GoConnect credentials:
	- Email (required)
	- Password (required)
5. Set the **Polling Interval** (default 60 s).
6. Optionally enable **ABRP Upload** — if checked, a second page asks for the **Ignition Polling Interval** (default 10 s).
7. Submit to finish setup.

If authentication fails later, Home Assistant will prompt for reauthentication.

## Cars Supported

Any car fitted with the Connected Cars module (GoConnectApp).

Known working vehicles in Australia:

- ID.4
- ID.5
- ID Buzz

If you are outside Australia and can confirm regional API endpoints, please open a pull request.

## ABRP Upload

The integration includes a **ABRP Data Changed** binary sensor (only created when ABRP Upload is enabled in the config). It turns `True` whenever the vehicle's charge percentage, charging state, odometer, speed, or location differs from when you last acknowledged an upload. Use it to trigger your automation efficiently — the same data is never uploaded twice.

To upload, call `volkswagen_goconnect.abrp_send`, then call `volkswagen_goconnect.abrp_acknowledge` with the same `license_plate` to reset only that vehicle sensor.

### Minimal Blueprint

A minimal Home Assistant blueprint is included for ABRP upload automation:

- Blueprint file: `blueprints/automation/volkswagen_goconnect/abrp_upload_on_data_change.yaml`
- Raw import URL: `https://raw.githubusercontent.com/amoisis/volkswagen_goconnect/main/blueprints/automation/volkswagen_goconnect/abrp_upload_on_data_change.yaml`

How to import it into Home Assistant:

1. Go to **Settings -> Automations & Scenes -> Blueprints**.
2. Select **Import Blueprint**.
3. Paste the raw GitHub URL above.
4. Create an automation from the imported blueprint.

The blueprint only asks for:

- the `ABRP Data Changed` binary sensor for the vehicle
- the vehicle `license_plate`
- your ABRP `api_key`
- your ABRP `token`

No per-sensor mapping is needed because `volkswagen_goconnect.abrp_send` now auto-fills supported telemetry from the integration data.

### Required Parameters for `abrp_send`

- `api_key` (required) — your ABRP Telemetry API key
- `token` (required) — your ABRP vehicle token
- `license_plate` (required) — selects which configured vehicle is used for live auto-fill
- `service_data` (optional) — ABRP telemetry fields to override; must include at least `soc`, `lat`, `lon`

### ABRP Default Auto-Fill Mapping

When you omit these keys in `service_data` (or pass `null`), the integration backfills them from the selected vehicle's live data:

| ABRP key | Source field in integration data | Typical Home Assistant entity equivalent |
|---|---|---|
| `soc` | `chargePercentage.pct` | `sensor.<vehicle>_charge_percentage` |
| `lat` | `position.latitude` | `device_tracker.<vehicle>_location` attribute `latitude` |
| `lon` | `position.longitude` | `device_tracker.<vehicle>_location` attribute `longitude` |
| `is_charging` | `isCharging` | `binary_sensor.<vehicle>_charging` |
| `odometer` | `odometer.odometer` | `sensor.<vehicle>_odometer` |
| `speed` | latest `speedometers[0].speed` | `sensor.<vehicle>_speed` |
| `ext_temp` | latest `outdoorTemperatures[0].celsius` | `sensor.<vehicle>_outdoor_temperature` |
| `est_battery_range` | `rangeTotalKm.km` | `sensor.<vehicle>_range_total_km` |
| `batt_temp` | `highVoltageBatteryTemperature.celsius` | `sensor.<vehicle>_high_voltage_battery_temperature` |
| `soe` | `highVoltageBatteryUsableCapacityKwh.kwh` | `sensor.<vehicle>_battery_state_of_energy_kwh` |
| `capacity` | derived as `soe / (soc / 100)` | `sensor.<vehicle>_high_voltage_battery_usable_capacity_kwh` |
| `utc` | current Unix timestamp at send time | generated in service action |

Notes:

- Auto-fill only sets a key when your payload does not include it or includes it as `null`.
- Explicit values in `service_data` always win over live auto-filled values.
- After auto-fill and cleanup, `soc`, `lat`, and `lon` must be present or the service call fails.

### Example Automation

The example below sends telemetry to ABRP whenever vehicle data changes, including speed and outdoor temperature, then acknowledges the upload.

```yaml
automation:
  - alias: "Volkswagen GoConnect: Send ABRP telemetry on data change"
    mode: single
    trigger:
      - platform: state
        entity_id: binary_sensor.vgc_my_plate_abrp_data_changed
        to: "on"
    action:
      - service: volkswagen_goconnect.abrp_send
        data:
          api_key: !secret abrp_api_key
          token: !secret abrp_vehicle_token
          license_plate: "MYPLATE123"
          service_data:
            soc: "{{ states('sensor.vgc_my_plate_charge_percentage') | float(0) }}"
            lat: "{{ state_attr('device_tracker.vgc_my_plate_location', 'latitude') | float(0) }}"
            lon: "{{ state_attr('device_tracker.vgc_my_plate_location', 'longitude') | float(0) }}"
            speed: "{{ states('sensor.vgc_my_plate_speed') | float(0) }}"
            ext_temp: "{{ states('sensor.vgc_my_plate_outdoor_temperature') | float(0) }}"
            is_charging: "{{ 1 if is_state('binary_sensor.vgc_my_plate_charging', 'on') else 0 }}"
            odometer: "{{ states('sensor.vgc_my_plate_odometer') | float(0) }}"
      - service: volkswagen_goconnect.abrp_acknowledge
        data:
          license_plate: "MYPLATE123"
```

Replace `vgc_my_plate_abrp_data_changed` with your actual entity ID (based on the vehicle number plate).

## Displaying Open Error Codes in Lovelace

The `openErrorCodeLeads` sensor supports two display styles at the same time:

- `table` attribute: prebuilt Markdown table text
- `rows` attribute: structured row data for table cards

Additional status-aware attributes are also available:

- `open_table`, `open_rows`, `open_lead_count`
- `closed_table`, `closed_rows`, `closed_lead_count`
- `all_table`, `all_rows`, `all_lead_count`

### Option 1: Markdown Card (Built-in)

No custom card is required.

```yaml
type: markdown
title: Open Error Codes
content: >
  {{ state_attr('sensor.vgc_my_plate_open_error_codes', 'table') }}
```

### Option 1B: Markdown Card (Closed Error Codes)

```yaml
type: markdown
title: Closed Error Codes
content: >
  {{ state_attr('sensor.vgc_my_plate_open_error_codes', 'closed_table') }}
```

### Option 1C: Markdown Card (All Error Codes)

```yaml
type: markdown
title: All Error Codes
content: >
  {{ state_attr('sensor.vgc_my_plate_open_error_codes', 'all_table') }}
```

### Option 2: Table Card (HACS)

Yes, this is a HACS custom card. Install `flex-table-card` from HACS first.

```yaml
type: custom:flex-table-card
title: Open Error Codes
entities:
  include: sensor.vgc_my_plate_open_error_codes
strict: false
columns:
  - name: ID
    data: rows.0.id
  - name: Status
    data: rows.0.status
  - name: Dismissed
    data: rows.0.dismissed
  - name: Important
    data: rows.0.important
  - name: Severity Score
    data: rows.0.severityscore
  - name: Error Code
    data: rows.0.errorCode
  - name: Provider
    data: rows.0.provider
  - name: ECU
    data: rows.0.ecu
  - name: Description
    data: rows.0.description
  - name: Raw Code
    data: rows.0.rawCode
  - name: Severity
    data: rows.0.severity
  - name: First Error Time
    data: rows.0.firsterrorcodetime
  - name: Last Error Time
    data: rows.0.lasterrorcodetime
  - name: Error Count
    data: rows.0.errorcodecount
```

Replace `sensor.vgc_my_plate_open_error_codes` with your actual sensor entity ID.

## Support

- Issues: https://github.com/amoisis/volkswagen_goconnect/issues
- Discussions: https://github.com/amoisis/volkswagen_goconnect/discussions
