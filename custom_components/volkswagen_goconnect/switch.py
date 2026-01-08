"""Switch platform for volkswagen_goconnect."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

from .entity import VolkswagenGoConnectEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import VolkswagenGoConnectDataUpdateCoordinator


ENTITY_DESCRIPTIONS = (
    SwitchEntityDescription(
        key="volkswagen_goconnect",
        name="Integration Switch",
        icon="mdi:format-quote-close",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    async_add_entities(
        VolkswagenGoConnectSwitch(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class VolkswagenGoConnectSwitch(VolkswagenGoConnectEntity, SwitchEntity):
    """volkswagen_goconnect switch class."""

    def __init__(
        self,
        coordinator: VolkswagenGoConnectDataUpdateCoordinator,
        entity_description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        plate = getattr(self, "_license_plate", coordinator.config_entry.title)
        name = entity_description.name
        self._attr_name = name if isinstance(name, str) else None
        self._attr_unique_id = f"vwgc_{plate}_{entity_description.key}"
        self._attr_suggested_object_id = f"vwgc_{plate}_{entity_description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return False

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the switch."""
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the switch."""
        await self.coordinator.async_request_refresh()
