# Volkswagen GoConnect Integration for Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/amoisis/volkswagen_goconnect?style=flat-square)](https://github.com/amoisis/volkswagen_goconnect/releases)
[![Tests & Coverage](https://img.shields.io/github/actions/workflow/status/amoisis/volkswagen_goconnect/tests.yml?style=flat-square&label=tests)](https://github.com/amoisis/volkswagen_goconnect/actions/workflows/tests.yml)
[![codecov](https://img.shields.io/codecov/c/github/amoisis/volkswagen_goconnect?style=flat-square)](https://codecov.io/gh/amoisis/volkswagen_goconnect)
[![Last Commit](https://img.shields.io/github/last-commit/amoisis/volkswagen_goconnect?style=flat-square)](https://github.com/amoisis/volkswagen_goconnect/commits)

Volkswagen GoConnect lets you monitor your vehicle from Home Assistant using your Volkswagen GoConnect account.

## What This Integration Provides

After setup, the integration creates entities for each supported vehicle.

### Sensors

The sensor platform exposes vehicle information and telemetry including:

- Vehicle details: ID, VIN, license plate, make, model, year, fuel type
- Driving and status data: odometer, ignition state, charging status, total estimated range
- Energy data:
  - EVs: charge percentage and high-voltage battery capacity
  - Non-EVs: fuel percentage and fuel level
- Service/contact info: workshop and brand contact details

### Binary Sensors

- Charging state
- Vehicle blocked state
- Vehicle activated/connectivity state

### Device Tracker

- GPS location from the vehicle position (latitude/longitude)

### Service

- `volkswagen_goconnect.abrp_send` to send telemetry data to A Better Routeplanner (ABRP)

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
5. Configure options during setup:
	- Polling interval in seconds (required, default 60)
	- Ignition polling interval in seconds (optional, default 10)
	- ABRP API key (optional)
6. Submit to finish setup.

If authentication fails later, Home Assistant will prompt for reauthentication.

## Cars Supported

Any car fitted with the Connected Cars module (GoConnectApp).

Known working vehicles in Australia:

- ID.4
- ID.5
- ID Buzz

If you are outside Australia and can confirm regional API endpoints, please open a pull request.

## ABRP Upload Service

If you want to upload live data to ABRP, call `volkswagen_goconnect.abrp_send` with:

- `api_key` (required)
- `token` (required)
- `service_data` (optional object)

`service_data` should contain ABRP telemetry fields. At minimum, ABRP requires `soc`, `lat`, and `lon`.

## Support

- Issues: https://github.com/amoisis/volkswagen_goconnect/issues
- Discussions: https://github.com/amoisis/volkswagen_goconnect/discussions
