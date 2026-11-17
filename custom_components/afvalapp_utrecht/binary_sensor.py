"""On when something is collected today or tomorrow (show/hide a dashboard card)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AfvalConfigEntry
from .coordinator import AfvalCoordinator
from .entity import AfvalEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: AfvalConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([PickupSoonSensor(entry.runtime_data)])


class PickupSoonSensor(AfvalEntity, BinarySensorEntity):
    _attr_translation_key = "today_or_tomorrow"
    _attr_icon = "mdi:delete-clock"

    def __init__(self, c: AfvalCoordinator) -> None:
        super().__init__(c, "today_or_tomorrow")

    @property
    def is_on(self) -> bool:
        c = self.coordinator
        return bool(c.on(c.today()) or c.on(c.tomorrow()))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        c = self.coordinator
        return {
            "today": c.names(c.on(c.today())) or None,
            "tomorrow": c.names(c.on(c.tomorrow())) or None,
        }
