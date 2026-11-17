"""Sensors: next pickup, today, tomorrow, notice text, and one per waste type."""

from __future__ import annotations

from datetime import date
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AfvalConfigEntry
from .const import ICONS
from .coordinator import AfvalCoordinator
from .entity import AfvalEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: AfvalConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    c = entry.runtime_data
    entities: list[SensorEntity] = [
        NextDateSensor(c), NextTypeSensor(c), DaySensor(c, 0), DaySensor(c, 1), NoticeSensor(c),
    ]
    entities += [FractionSensor(c, f) for f in c.fractions()]
    async_add_entities(entities)


class NextDateSensor(AfvalEntity, SensorEntity):
    """Date of the next pickup (any type)."""

    _attr_translation_key = "next_date"
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:calendar-arrow-right"

    def __init__(self, c: AfvalCoordinator) -> None:
        super().__init__(c, "next_date")

    @property
    def native_value(self) -> date | None:
        return self.coordinator.next_day()[0]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        day, pickups = self.coordinator.next_day()
        return {
            "waste_type": self.coordinator.names(pickups) or None,
            "days_until": (day - self.coordinator.today()).days if day else None,
        }


class NextTypeSensor(AfvalEntity, SensorEntity):
    """What goes out next, as text: "Papier"."""

    _attr_translation_key = "next_type"
    _attr_icon = "mdi:trash-can-outline"

    def __init__(self, c: AfvalCoordinator) -> None:
        super().__init__(c, "next_type")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.names(self.coordinator.next_day()[1]) or None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        day, _ = self.coordinator.next_day()
        return {
            "date": day.isoformat() if day else None,
            "days_until": (day - self.coordinator.today()).days if day else None,
        }


class DaySensor(AfvalEntity, SensorEntity):
    """Today / tomorrow: "Groente, fruit en tuin" or "Geen"."""

    def __init__(self, c: AfvalCoordinator, offset: int) -> None:
        key = "today" if offset == 0 else "tomorrow"
        super().__init__(c, key)
        self._offset = offset
        self._attr_translation_key = key
        self._attr_icon = "mdi:calendar-today" if offset == 0 else "mdi:calendar-arrow-right"

    @property
    def native_value(self) -> str:
        c = self.coordinator
        day = c.today() if self._offset == 0 else c.tomorrow()
        return c.names(c.on(day)) or c.text("_none")


class NoticeSensor(AfvalEntity, SensorEntity):
    """One line for a dashboard button: "Vandaag: Papier · Morgen: Groente, fruit en tuin"."""

    _attr_translation_key = "notice"
    _attr_icon = "mdi:delete-alert"

    def __init__(self, c: AfvalCoordinator) -> None:
        super().__init__(c, "notice")

    @property
    def native_value(self) -> str:
        c = self.coordinator
        parts = []
        if today := c.names(c.on(c.today())):
            parts.append(f"{c.text('_today')}: {today}")
        if tomorrow := c.names(c.on(c.tomorrow())):
            parts.append(f"{c.text('_tomorrow')}: {tomorrow}")
        return " · ".join(parts) or c.text("_none")


class FractionSensor(AfvalEntity, SensorEntity):
    """Next date for one waste type, e.g. "Papier: 20 nov"."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, c: AfvalCoordinator, fraction: str) -> None:
        super().__init__(c, f"type_{fraction}")
        self._fraction = fraction
        self._attr_icon = ICONS.get(fraction, "mdi:trash-can")
        if fraction in ICONS:
            self._attr_translation_key = fraction
        else:
            self._attr_name = fraction.upper()

    @property
    def native_value(self) -> date | None:
        up = self.coordinator.upcoming(self._fraction)
        return up[0].day if up else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        up = self.coordinator.upcoming(self._fraction)
        return {
            "days_until": (up[0].day - self.coordinator.today()).days if up else None,
            "upcoming": [p.day.isoformat() for p in up[:5]],
            "instructions": up[0].description if up else None,
        }
