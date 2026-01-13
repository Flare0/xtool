from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import XToolCoordinator
from .const import DOMAIN, CONF_IP_ADDRESS, CONF_DEVICE_TYPE

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the xTool button platform."""
    coordinator: XToolCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    device_name = hass.data[DOMAIN][entry.entry_id]["name"]

    buttons = []
    if coordinator.device_type == "m1ultra":
        buttons.append(XToolKnifeHeadSyncButton(coordinator, device_name, entry.entry_id))

    async_add_entities(buttons)


class XToolKnifeHeadSyncButton(CoordinatorEntity, ButtonEntity):
    """Defines a xTool Knife Head Sync button."""

    _attr_has_entity_name = True
    _attr_name = "Sync Multi-function Module"

    def __init__(
        self,
        coordinator: XToolCoordinator,
        device_name: str,
        entry_id: str,
    ) -> None:
        """Initialize the xTool Sync Multi-function Module button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_sync_multi_function_module_button"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": device_name,
            "manufacturer": "xTool",
        }

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.hass.async_add_executor_job(
            self.coordinator._fetch_m1ultra_data,
            "/peripheral/knife_head",
            "POST",
            {"action": "get_sync"},
        )
