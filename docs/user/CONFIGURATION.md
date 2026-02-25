# Configuration Reference

This document describes all configuration options and settings available in the Volkswagen GoConnect custom integration.

## Integration Configuration

### Initial Setup Options

These options are configured during initial setup via the Home Assistant UI.

#### Connection Settings

| Option         | Type    | Required | Default | Description                                      |
|----------------|---------|----------|---------|--------------------------------------------------|
| **Email**      | string  | Yes      | -       | Your Volkswagen account email address           |
| **Password**   | string  | Yes      | -       | Your Volkswagen account password                |
| **Region**     | string  | Yes      | -       | Select your region (e.g., Europe, North America)|

#### Update Settings

| Option            | Type              | Required | Default | Description                                      |
|-------------------|-------------------|----------|---------|--------------------------------------------------|
| **Update Interval** | integer (seconds) | No       | 300     | How often to poll for updates (minimum: 30 seconds) |
| **Name**          | string            | No       | "Vehicle" | Friendly name for the integration instance      |

### Options Flow (Reconfiguration)

After initial setup, you can modify settings:

1. Go to **Settings** → **Devices & Services**
2. Find "Volkswagen GoConnect"
3. Click **Configure**
4. Modify settings
5. Click **Submit**

**Available options:**

- Update interval
- Name/identifier
- Connection timeout
- Additional features (device-specific)

## Entity Configuration

### Entity Customization

Customize entities via the UI or `configuration.yaml`:

#### Via Home Assistant UI

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Find and click the entity
3. Click the settings icon
4. Modify:
   - Entity ID
   - Name
   - Icon
   - Device class (for applicable entities)
   - Area assignment

#### Via configuration.yaml

```yaml
homeassistant:
  customize:
    sensor.vehicle_battery_level:
      friendly_name: "Battery Level"
      icon: mdi:battery
      unit_of_measurement: "%"
```

### Disabling Entities

If you don't need certain entities:

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Find the entity
3. Click it, then click **Settings** icon
4. Toggle **Enable entity** off

Disabled entities won't update or consume resources.

## Services

The integration provides the following services:

### `volkswagen_goconnect.start_climate`

Start the climate control system in your vehicle.

**Service data:**

| Parameter    | Type            | Required | Description                          |
|--------------|-----------------|----------|--------------------------------------|
| `entity_id`  | string or list  | No       | Target entity/entities (if omitted, targets all) |
| `duration`   | integer         | No       | Duration in minutes (default: 10)   |

**Example:**

```yaml
service: volkswagen_goconnect.start_climate
target:
  entity_id: switch.vehicle_climate_control
data:
  duration: 15
```

### Using Services in Automations

```yaml
automation:
  - alias: "Start climate control at 7 AM"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: volkswagen_goconnect.start_climate
        target:
          entity_id: switch.vehicle_climate_control
        data:
          duration: 20
```

## Advanced Configuration

### Multiple Instances

You can add multiple instances of this integration for different vehicles:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Volkswagen GoConnect"
4. Configure with different connection details

Each instance creates separate entities with unique entity IDs.

### Network Configuration

If the vehicle is on a different network or behind a firewall:

- Ensure ports are open (default: 443 for HTTPS)
- Configure port forwarding if needed
- Consider VPN for remote access
- Some vehicles may require static IP addresses

### Polling Behavior

The integration uses polling to fetch updates:

- **Minimum interval:** 30 seconds (prevents overloading the vehicle API)
- **Recommended interval:** 5 minutes (default)
- **Longer intervals:** Save resources but reduce responsiveness

Adjust based on your needs:

- Real-time monitoring: 30-60 seconds
- Regular updates: 5 minutes
- Slow-changing values: 15-30 minutes

## Diagnostic Data

The integration provides diagnostic data for troubleshooting:

1. Go to **Settings** → **Devices & Services**
2. Find "Volkswagen GoConnect"
3. Click on the vehicle
4. Click **Download Diagnostics**

Diagnostic data includes:

- Connection status
- Last update timestamp
- API response data
- Entity states
- Error history

**Privacy note:** Diagnostic data may contain sensitive information. Review before sharing.

## Blueprints

The integration works with Home Assistant Blueprints for reusable automations:

### Example Blueprint

```yaml
blueprint:
  name: Volkswagen GoConnect Alert
  description: Notify when battery level drops below threshold
  domain: automation
  input:
    battery_sensor:
      name: Battery Sensor
      selector:
        entity:
          domain: sensor
          integration: volkswagen_goconnect
    threshold:
      name: Threshold
      selector:
        number:
          min: 0
          max: 100

trigger:
  - platform: numeric_state
    entity_id: !input battery_sensor
    below: !input threshold

action:
  - service: notify.notify
    data:
      message: "Battery level is below threshold!"
```

## Configuration Examples

See [EXAMPLES.md](./EXAMPLES.md) for complete automation and dashboard examples.

## Troubleshooting Configuration

### Config Entry Fails to Load

If the integration fails to load after configuration:

1. Check Home Assistant logs for errors
2. Verify connection details are correct
3. Test connectivity from Home Assistant to the vehicle API
4. Try removing and re-adding the integration

### Options Don't Save

If configuration changes aren't persisted:

1. Check for validation errors in the UI
2. Ensure values are within allowed ranges
3. Review logs for detailed error messages
4. Try restarting Home Assistant

## Related Documentation

- [Getting Started](./GETTING_STARTED.md) - Installation and initial setup
- [Examples](./EXAMPLES.md) - Automation and dashboard examples
- [GitHub Issues](https://github.com/amoisis/volkswagen_goconnect/issues) - Report problems
