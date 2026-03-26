# Getting Started with Volkswagen GoConnect

> **Full documentation is in [README.md](../../README.md).** This page is a quick reference.

## Prerequisites

- Home Assistant 2025.7.0 or newer
- A Volkswagen GoConnect account
- A compatible vehicle fitted with the Connected Cars module

## Installation

See [README.md — Installation](../../README.md#installation) for HACS and manual installation steps.

## Setup

1. Go to **Settings** → **Devices & Services** → **+ Add Integration**
2. Search for **Volkswagen GoConnect**
3. Enter your credentials and configuration options:

| Field | Required | Default | Description |
|---|---|---|---|
| Email | Yes | — | Volkswagen GoConnect account email |
| Password | Yes | — | Account password |
| Polling Interval | Yes | 60 s | How often to poll the API (10 – 3600 s) |
| Enable ABRP Upload | No | Off | Enables fast ignition polling and creates the ABRP Data Changed sensor |

4. If **Enable ABRP Upload** is checked, a second page appears:

| Field | Required | Default | Description |
|---|---|---|---|
| Ignition Polling Interval | Yes | 10 s | Faster polling interval used when ignition is on (1 – 600 s) |

5. Click **Submit**. Home Assistant will authenticate and load your vehicles.

## What Gets Created

See [README.md — What This Integration Provides](../../README.md#what-this-integration-provides) for a full entity table.

Each vehicle in your account gets its own Home Assistant device with sensors, binary sensors, and a device tracker (when GPS position is available).
