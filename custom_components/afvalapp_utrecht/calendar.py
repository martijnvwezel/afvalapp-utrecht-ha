"""Calendar with all pickup days (all-day events)."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AfvalConfigEntry
from .api import Pickup
from .coordinator import AfvalCoordinator
from .entity import AfvalEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: AfvalConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([AfvalCalendar(entry.runtime_data)])


class AfvalCalendar(AfvalEntity, CalendarEntity):
    _attr_translation_key = "calendar"
    _attr_icon = "mdi:calendar-blank"

    def __init__(self, c: AfvalCoordinator) -> None:
        super().__init__(c, "calendar")

    def _event(self, p: Pickup) -> CalendarEvent:
        return CalendarEvent(
            start=p.day,
            end=p.day + timedelta(days=1),
            summary=self.coordinator.text(p.fraction),
            description=p.description or None,
            uid=f"{self.coordinator.address_id}-{p.day.isoformat()}-{p.code}",
        )

    @property
    def event(self) -> CalendarEvent | None:
        up = self.coordinator.upcoming()
        return self._event(up[0]) if up else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        start, end = start_date.date(), end_date.date()
        return [
            self._event(p) for p in self.coordinator.data or []
            if start <= p.day <= end
        ]
