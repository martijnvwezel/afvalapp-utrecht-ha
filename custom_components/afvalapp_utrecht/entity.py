"""Shared base entity: one device "Waste" per address."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AfvalCoordinator


class AfvalEntity(CoordinatorEntity[AfvalCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: AfvalCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            translation_key="waste",
            manufacturer="Gemeente Utrecht",
            model=entry.title,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://www.utrecht.nl/afval",
        )
