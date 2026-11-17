"""Push a notification the evening before a pickup."""

from __future__ import annotations

from datetime import datetime, time
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change

from .const import CONF_REMINDER_TARGETS, CONF_REMINDER_TIME, DEFAULT_REMINDER_TIME
from .coordinator import AfvalCoordinator

_LOGGER = logging.getLogger(__name__)


def reminder_message(c: AfvalCoordinator) -> str | None:
    """Text for tomorrow, or None when nothing is collected tomorrow."""
    names = c.names(c.on(c.tomorrow()))
    if not names:
        return None
    return f"{c.text('_tomorrow')}: {names}. {c.text('_reminder')}"


@callback
def async_setup_reminder(hass: HomeAssistant, entry: ConfigEntry, c: AfvalCoordinator) -> None:
    targets: list[str] = entry.options.get(CONF_REMINDER_TARGETS) or []
    if not targets:
        return
    at = time.fromisoformat(entry.options.get(CONF_REMINDER_TIME, DEFAULT_REMINDER_TIME))

    async def _remind(_now: datetime) -> None:
        if (message := reminder_message(c)) is None:
            return
        for target in targets:
            try:
                await hass.services.async_call(
                    "notify", target,
                    {"title": c.text("_reminder_title"), "message": message},
                    blocking=True,
                )
            except Exception:  # noqa: BLE001 - one broken phone must not block the others
                _LOGGER.exception("Could not send waste reminder via notify.%s", target)

    entry.async_on_unload(
        async_track_time_change(hass, _remind, hour=at.hour, minute=at.minute, second=at.second)
    )
