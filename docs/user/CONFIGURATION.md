# Configuration Reference

> **Full documentation is in [README.md](../../README.md).** This page is a quick reference for configuration options.

## Setup Options

All options are presented in the UI during initial setup. There is no YAML configuration.

### Step 1 — Credentials and polling

| Option | Type | Required | Default | Range | Description |
|---|---|---|---|---|---|
| Email | string | Yes | — | — | Volkswagen GoConnect account email |
| Password | string | Yes | — | — | Account password |
| Polling Interval | integer (s) | Yes | 60 | 10 – 3600 | How often to fetch vehicle data |
| Enable ABRP Upload | boolean | No | false | — | Enables fast ignition polling and the ABRP Data Changed sensor |

### Step 2 — ABRP Settings (only when Enable ABRP Upload is checked)

| Option | Type | Required | Default | Range | Description |
|---|---|---|---|---|---|
| Ignition Polling Interval | integer (s) | Yes | 10 | 1 – 600 | Faster interval used while ignition is on |

## Reconfiguration

To change options after setup:

1. Go to **Settings** → **Devices & Services**
2. Find **Volkswagen GoConnect** and click **Configure**
3. Update the options and click **Submit**

## ABRP Service

Call `volkswagen_goconnect.abrp_send` to upload live telemetry to ABRP:

| Parameter | Required | Description |
|---|---|---|
| `api_key` | Yes | Your ABRP API key |
| `token` | Yes | Your ABRP vehicle token |
| `service_data` | No | ABRP telemetry fields (e.g. `soc`, `lat`, `lon`) |

At minimum, ABRP requires `soc`, `lat`, and `lon` in `service_data`.

After a successful upload, call `volkswagen_goconnect.abrp_acknowledge` to reset the **ABRP Data Changed** binary sensor so the same data is not uploaded again.
