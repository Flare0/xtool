from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import XToolCoordinator
from .const import DOMAIN, MANUFACTURER

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the xTool button platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: XToolCoordinator = data["coordinator"]
    name: str = data["name"]
    entry_id: str = data["entry_id"]

    entities: list[ButtonEntity] = []

    if coordinator.device_type == "m1ultra":
        entities.append(XToolKnifeHeadSyncButton(coordinator, name, entry_id))

    async_add_entities(entities, True)

class _XToolBaseButton(CoordinatorEntity[XToolCoordinator], ButtonEntity):
    """Base with consistent device info and naming."""

    _attr_has_entity_name = True  # -> entity_id prefix = <name_slug>_

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator)
        self._device_name = name
        self._entry_id = entry_id

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
            "manufacturer": MANUFACTURER,
            "model": self.coordinator.device_type.upper(),
        }

class XToolKnifeHeadSyncButton(_XToolBaseButton):
    """Defines a xTool Knife Head Sync button."""


    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Sync Multi-function Module"
        self._attr_unique_id = f"{entry_id}_sync_multi_function_module"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_sync_multi_function_module"


    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.hass.async_add_executor_job(
            self.coordinator._fetch_m1ultra_data,
            "/peripheral/knife_head",
            "POST",
            {"action": "get_sync"},
        )
