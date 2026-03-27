"""Custom types for volkswagen_goconnect."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.loader import Integration

    from .api import VolkswagenGoConnectApiClient
    from .coordinator import VolkswagenGoConnectDataUpdateCoordinator


@dataclass
class VolkswagenGoConnectData:
    """Data for the Volkswagen GoConnect integration."""

    client: VolkswagenGoConnectApiClient
    abrp_coordinator: VolkswagenGoConnectDataUpdateCoordinator
    coordinator: VolkswagenGoConnectDataUpdateCoordinator
    ignition_coordinator: VolkswagenGoConnectDataUpdateCoordinator
    integration: Integration
    abrp_enabled: bool
