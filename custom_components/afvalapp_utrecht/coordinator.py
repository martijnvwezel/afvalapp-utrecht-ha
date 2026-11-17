"""Fetches the pickup calendar twice a day."""

from __future__ import annotations

from datetime import date, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import AfvalApi, ApiError, Pickup
from .const import (
    CONF_ADDRESS_ID,
    CONF_TEXT_LANGUAGE,
    CONF_UPDATE_HOURS,
    DEFAULT_TEXT_LANGUAGE,
    DEFAULT_UPDATE_HOURS,
    DOMAIN,
    label,
)

_LOGGER = logging.getLogger(__name__)


class AfvalCoordinator(DataUpdateCoordinator[list[Pickup]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(
                hours=entry.options.get(CONF_UPDATE_HOURS, DEFAULT_UPDATE_HOURS)
            ),
        )
        self.api = AfvalApi(async_get_clientsession(hass))
        self.address_id: str = entry.data[CONF_ADDRESS_ID]

    async def _async_update_data(self) -> list[Pickup]:
        try:
            return await self.api.calendar(self.address_id)
        except ApiError as err:
            raise UpdateFailed(f"Afvalapp not reachable: {err}") from err

    # -- helpers used by the entities -------------------------------------
    @property
    def lang(self) -> str:
        # Text in the sensors/calendar. Dutch by default: it's Utrecht.
        return self.config_entry.options.get(CONF_TEXT_LANGUAGE, DEFAULT_TEXT_LANGUAGE)

    def text(self, key: str) -> str:
        return label(self.lang, key)

    @staticmethod
    def today() -> date:
        return dt_util.now().date()

    def on(self, day: date) -> list[Pickup]:
        return [p for p in self.data or [] if p.day == day]

    def upcoming(self, fraction: str | None = None) -> list[Pickup]:
        today = self.today()
        return [
            p for p in self.data or []
            if p.day >= today and (fraction is None or p.fraction == fraction)
        ]

    def names(self, pickups: list[Pickup]) -> str:
        return " + ".join(dict.fromkeys(self.text(p.fraction) for p in pickups))

    def next_day(self) -> tuple[date | None, list[Pickup]]:
        up = self.upcoming()
        if not up:
            return None, []
        return up[0].day, self.on(up[0].day)

    def fractions(self) -> list[str]:
        return list(dict.fromkeys(p.fraction for p in self.data or []))

    def tomorrow(self) -> date:
        return self.today() + timedelta(days=1)
