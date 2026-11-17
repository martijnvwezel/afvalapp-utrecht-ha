"""Afvalapp Utrecht: when is the bin collected (gemeente Utrecht)."""

from __future__ import annotations

from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change

from .coordinator import AfvalCoordinator
from .reminder import async_setup_reminder

PLATFORMS = [Platform.BINARY_SENSOR, Platform.CALENDAR, Platform.SENSOR]

type AfvalConfigEntry = ConfigEntry[AfvalCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: AfvalConfigEntry) -> bool:
    coordinator = AfvalCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    # "Today" / "tomorrow" change at midnight without new data: re-render then.
    @callback
    def _new_day(_now: datetime) -> None:
        coordinator.async_update_listeners()

    entry.async_on_unload(
        async_track_time_change(hass, _new_day, hour=0, minute=0, second=5)
    )
    async_setup_reminder(hass, entry, coordinator)
    # Changed options (interval, language, reminder): reload.
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_reload(hass: HomeAssistant, entry: AfvalConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: AfvalConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
