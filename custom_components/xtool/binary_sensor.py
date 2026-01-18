from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
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
    """Set up the binary sensor (Power) for each XTool entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: XToolCoordinator = data["coordinator"]
    name: str = data["name"]
    entry_id: str = data["entry_id"]

    entities: list[BinarySensorEntity] = [
        XToolPowerBinarySensor(coordinator, name, entry_id)
    ]

    if coordinator.device_type == "m1ultra":
        entities += [
            XToolM1UltraDrawerBinarySensor(coordinator, name, entry_id),
            XToolM1UltraGapBinarySensor(coordinator, name, entry_id),
            XToolM1UltraMachineLockBinarySensor(coordinator, name, entry_id),
            XToolM1UltraHeightenStateBinarySensor(coordinator, name, entry_id),
            XToolM1UltraInkjetPrinterExistBinarySensor(coordinator, name, entry_id),
            XToolM1UltraAdsorptionMatStateBinarySensor(coordinator, name, entry_id),
            XToolM1UltraAdsorptionMatStaticBinarySensor(coordinator, name, entry_id),
            XToolM1UltraDoorBinarySensor(coordinator, name, entry_id),
            XToolM1UltraAirassistStateBinarySensor(coordinator, name, entry_id),
            XToolM1UltraExtPurifierPlugBinarySensor(coordinator, name, entry_id),
            XToolM1UltraSmokingFanStateSensor(coordinator, name, entry_id),
            XToolM1UltraSmokingFanPlugSensor(coordinator, name, entry_id),
            XToolM1UltraDrivedLockBinarySensor(coordinator, name, entry_id),
            XToolM1UltraExtPurifierStateBinarySensor(coordinator, name, entry_id),

        ]

    async_add_entities(entities, True)


class _M1UltraBinarySensorBase(CoordinatorEntity[XToolCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True

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
            "model": "M1 Ultra",
        }


class XToolPowerBinarySensor(CoordinatorEntity[XToolCoordinator], BinarySensorEntity):
    """Shows whether the device is reachable/powered on."""

    _attr_device_class = BinarySensorDeviceClass.POWER
    _attr_has_entity_name = True  # -> entity_id prefix = <name_slug>_

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator)
        self._device_name = name
        self._entry_id = entry_id

        self._attr_name = "Power"                  # visible as "<Name> Power"
        self._attr_unique_id = f"{entry_id}_power" # stable unique id

    @property
    def suggested_object_id(self) -> str:
        # IMPORTANT: do NOT include the name here.
        # HA will prefix with <name_slug>_ automatically because has_entity_name=True.
        # Result: binary_sensor.<name_slug>_<device_type>_power
        return f"{self.coordinator.device_type}_power"

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,                       # device name = your given name
            "manufacturer": MANUFACTURER,
            "model": self.coordinator.device_type.upper(),
        }

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable"):
            return False
        if self.coordinator.device_type in ("f1", "p2", "apparel"):
            return bool(str(data.get("mode", "")).strip())
        if self.coordinator.device_type == "m1":
            return bool(str(data.get("STATUS", "")).strip())
        if self.coordinator.device_type == "m1ultra":
            return bool(data.get("runningStatus") and data["runningStatus"].get("curMode") and (data["runningStatus"]["curMode"].get("mode") or data["runningStatus"]["curMode"].get("subMode")))
        return False


class XToolM1UltraDrawerBinarySensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_icon = "mdi:artboard"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Baseplate"
        self._attr_unique_id = f"{entry_id}_baseplate"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_baseplate"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("drawer"):
            return False
        return bool(data["drawer"].get("state") == "on")  # "on" is present


class XToolM1UltraGapBinarySensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.OPENING

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Lid"
        self._attr_unique_id = f"{entry_id}_lid"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_lid"
    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("gap"):
            return False
        return bool(data["gap"].get("state") == "off")  #  "off" is open
    
class XToolM1UltraDoorBinarySensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.OPENING

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Hatch"
        self._attr_unique_id = f"{entry_id}_hatch"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_hatch"
    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("heighten"):
            return False
        return bool(data["heighten"].get("door") == "off")  # "off" is open

class XToolM1UltraMachineLockBinarySensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.PLUG

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "USB Machine Lock"
        self._attr_unique_id = f"{entry_id}_usb_machine_lock"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_usb_machine_lock"

    @property
    def icon(self) -> str:
        if self.is_on:
            return "mdi:lock-open-variant-outline"
        return "mdi:lock-outline"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("machine_lock"):
            return False
        return bool(data["machine_lock"].get("state") == "on")  # "on" is unlocked
     

class XToolM1UltraHeightenStateBinarySensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_icon = "mdi:dock-bottom"


    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Raiser"
        self._attr_unique_id = f"{entry_id}_raiser"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_raiser"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("heighten"):
            return False
        return bool(data["heighten"].get("state") == "on")  # "on" is present
    
class XToolM1UltraInkjetPrinterExistBinarySensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.PLUG
    _attr_icon = "mdi:power"


    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Ink Module Cable"
        self._attr_unique_id = f"{entry_id}_ink_module_cable"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_ink_module_cable"
    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("inkjet_printer_get"):
            return False
        return bool(data["inkjet_printer_get"].get("exist") == True)  # true means plugged in
    
class XToolM1UltraAdsorptionMatStateBinarySensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.PLUG
    _attr_icon = "mdi:power"


    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Electrostatic Mat"
        self._attr_unique_id = f"{entry_id}_electrostatic_mat"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_electrostatic_mat"
    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("adsorption_mat"):
            return False
        return bool(data["adsorption_mat"].get("state") == "on")  # "on" means plugged in
    
class XToolM1UltraAdsorptionMatStaticBinarySensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.POWER
    _attr_icon = "mdi:flash"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Electrostatic Mat Static"
        self._attr_unique_id = f"{entry_id}_electrostatic_mat_static"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_electrostatic_mat_static"
    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("adsorption_mat"):
            return False
        if data["adsorption_mat"].get("state") == "on":
            return bool(data["adsorption_mat"].get("enSta") == True)  # true means on
        return False

class XToolM1UltraAirassistStateBinarySensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.PLUG
    _attr_icon = "mdi:air-filter"


    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Air Assist"
        self._attr_unique_id = f"{entry_id}_air_assist"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_air_assist"
    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("airassist"):
            return False
        return bool(data["airassist"].get("state") == "on")  # "on" means plugged in
   

class XToolM1UltraExtPurifierPlugBinarySensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.PLUG
    _attr_icon = "mdi:air-purifier"


    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "External Purifier"
        self._attr_unique_id = f"{entry_id}_external_purifier"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_external_purifier"
    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("ext_purifier"):
            return False
        return bool(data["ext_purifier"].get("state") == "on")  # "on" means plugged in

class XToolM1UltraExtPurifierStateBinarySensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.POWER
    _attr_icon = "mdi:power"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "External Purifier"
        self._attr_unique_id = f"{entry_id}_external_purifier_state"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_external_purifier_state"
    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("ext_purifier"):
            return False
        if data["ext_purifier"].get("state") == "on":
            return bool(data["ext_purifier"].get("enSta") == True)  # Assume it is similar to adsorption mat's state enSta
        return False

class XToolM1UltraSmokingFanStateSensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.POWER
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Exhaust Fan State"
        self._attr_unique_id = f"{entry_id}_exhaust_fan_state"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_exhaust_fan_state"
    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("smoking_fan"):
            return False
        return bool(data["smoking_fan"].get("state") == "on")  # "on" means running
    

class XToolM1UltraSmokingFanPlugSensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.PLUG
    _attr_icon = "mdi:power"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Exhaust Fan"
        self._attr_unique_id = f"{entry_id}_exhaust_fan"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_exhaust_fan"
    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("smoking_fan"):
            return False
        return bool(data["smoking_fan"].get("exist") == True)  # true means plugged in
    

class XToolM1UltraDrivedLockBinarySensor(_M1UltraBinarySensorBase):
    _attr_device_class = BinarySensorDeviceClass.LOCK

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Multi-function Carriage Lock"
        self._attr_unique_id = f"{entry_id}_multi_function_carriage_lock"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_multi_function_carriage_lock"
    @property
    def icon(self) -> str:
        if self.is_on:
            return "mdi:lock-open-variant-outline"
        return "mdi:lock-outline"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("workhead_ID"):
            return False
        return bool(data["workhead_ID"].get("drivingLock") == 0)  # 1 is locked, but SensorDeviceClass.LOCK assumes 1 means unlocked
