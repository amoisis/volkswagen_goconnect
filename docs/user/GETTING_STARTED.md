# Getting Started with Volkswagen GoConnect

This guide will help you install and set up the Volkswagen GoConnect custom integration for Home Assistant.

## Prerequisites

- Home Assistant 2025.7.0 or newer
- HACS (Home Assistant Community Store) installed
- Network connectivity to your Volkswagen vehicle

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/amoisis/volkswagen_goconnect`
6. Set category to "Integration"
7. Click "Add"
8. Find "Volkswagen GoConnect" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/amoisis/volkswagen_goconnect/releases)
2. Extract the `volkswagen_goconnect` folder from the archive
3. Copy it to `custom_components/volkswagen_goconnect/` in your Home Assistant configuration directory
4. Restart Home Assistant

## Initial Setup

After installation, add the integration:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Volkswagen GoConnect"
4. Follow the configuration steps:

### Step 1: Connection Information

Enter the required connection details:

- **Volkswagen Account Email:** Your Volkswagen account email address
- **Password:** Your Volkswagen account password
- **Region:** Select your region (e.g., Europe, North America)

Click **Submit** to test the connection.

### Step 2: Configuration Options

Configure optional settings:

- **Update Interval:** How often to poll for updates (default: 5 minutes)
- **Name:** Friendly name for this integration instance

Click **Submit** to complete setup.

## What Gets Created

After successful setup, the integration creates:

### Devices

- **Volkswagen Vehicle:** Main device representing your connected vehicle
  - Model information
  - Software version
  - Configuration URL (link to Volkswagen Connect portal)

### Entities

The following entities are automatically created:

#### Sensors

- `sensor.vehicle_battery_level` - Battery level of the vehicle
- `sensor.vehicle_range` - Estimated range based on current charge/fuel

#### Binary Sensors

- `binary_sensor.vehicle_door_status` - Indicates if any door is open
- `binary_sensor.vehicle_window_status` - Indicates if any window is open

#### Switches

- `switch.vehicle_climate_control` - Turn climate control on/off
- `switch.vehicle_charging` - Start/stop vehicle charging

## First Steps

### Dashboard Cards

Add entities to your dashboard:

1. Go to your dashboard
2. Click **Edit Dashboard** → **Add Card**
3. Choose card type (e.g., "Entities", "Glance")
4. Select entities from "Volkswagen GoConnect"

Example entities card:

```yaml
type: entities
title: Volkswagen GoConnect
entities:
  - sensor.vehicle_battery_level
  - binary_sensor.vehicle_door_status
  - switch.vehicle_climate_control
```

### Automations

Use the integration in automations:

**Example - Notify on door open:**

```yaml
automation:
  - alias: "Notify when door is open"
    trigger:
      - platform: state
        entity_id: binary_sensor.vehicle_door_status
        to: "on"
    action:
      - service: notify.notify
        data:
          message: "A door is open on your vehicle."
```

**Example - Start charging at night:**

```yaml
automation:
  - alias: "Start charging at night"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.vehicle_charging
```

## Troubleshooting

### Connection Failed

If setup fails with connection errors:

1. Verify your Volkswagen account credentials are correct
2. Ensure no firewall is blocking the connection
3. Check Home Assistant logs for detailed error messages

### Entities Not Updating

If entities show "Unavailable" or don't update:

1. Check that the vehicle is online and reachable
2. Verify account credentials haven't expired
3. Review logs: **Settings** → **System** → **Logs**
4. Try reloading the integration

### Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: warning
  logs:
    custom_components.volkswagen_goconnect: debug
```

Add this to `configuration.yaml`, restart, and reproduce the issue. Check logs for detailed information.

## Next Steps

- See [CONFIGURATION.md](./CONFIGURATION.md) for detailed configuration options
- See [EXAMPLES.md](./EXAMPLES.md) for more automation examples
- Report issues at [GitHub Issues](https://github.com/amoisis/volkswagen_goconnect/issues)

## Support

For help and discussion:

- [GitHub Discussions](https://github.com/amoisis/volkswagen_goconnect/discussions)
- [Home Assistant Community Forum](https://community.home-assistant.io/)
