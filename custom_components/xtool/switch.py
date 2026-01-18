from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import XToolCoordinator
from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: XToolCoordinator = data["coordinator"]
    name: str = data["name"]
    entry_id: str = data["entry_id"]

    entities: list[SwitchEntity] = []

    if coordinator.device_type == "m1ultra":
        entities.append(XToolM1UltraSmokingFanSwitch(coordinator, name, entry_id))

    async_add_entities(entities, True)


class _XToolBaseSwitch(CoordinatorEntity[XToolCoordinator], SwitchEntity):
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


class XToolM1UltraSmokingFanSwitch(_XToolBaseSwitch):
    """Smoking Fan on/off toggle for M1 Ultra."""

    _attr_icon = "mdi:fan"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Exhaust Fan"
        self._attr_unique_id = f"{entry_id}_exhaust_fan_switch"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_exhaust_fan_switch"

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("smoking_fan"):
            return None
        # Use 'state' to determine on/off status, and 'exist' to ensure it's plugged in.
        if not data["smoking_fan"].get("exist"):
            return None  # Not available if not plugged in
        return data["smoking_fan"].get("state") == "on"

    async def async_turn_on(self, **kwargs: Any) -> None:
        data = self.coordinator.data or {}
        smoking_fan_info = data.get("smoking_fan")

        if smoking_fan_info and smoking_fan_info.get("exist") and not self.is_on:
            _LOGGER.debug("Turning on exhaust fan")
            response = await self.hass.async_add_executor_job(
                self.coordinator._fetch_m1ultra_data,
                "/peripheral/smoking_fan",
                "POST",
                {"action": "on"},
            )
            if response and response.get("code") == 0:
                self.coordinator.data["smoking_fan"] = response.get("data")
            self.coordinator.async_set_updated_data(self.coordinator.data)

    async def async_turn_off(self, **kwargs: Any) -> None:
        data = self.coordinator.data or {}
        smoking_fan_info = data.get("smoking_fan")

        if smoking_fan_info and smoking_fan_info.get("exist") and self.is_on:
            _LOGGER.debug("Turning off exhaust fan")
            response = await self.hass.async_add_executor_job(
                self.coordinator._fetch_m1ultra_data,
                "/peripheral/smoking_fan",
                "POST",
                {"action": "off"},
            )
            if response and response.get("code") == 0:
                self.coordinator.data["smoking_fan"] = response.get("data")
            self.coordinator.async_set_updated_data(self.coordinator.data)

