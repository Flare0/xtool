from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
    # noqa: E402
from homeassistant.const import UnitOfTemperature, UnitOfTime, UnitOfElectricCurrent, PERCENTAGE
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

    entities: list[SensorEntity] = [XToolWorkStateSensor(coordinator, name, entry_id)]

    if coordinator.device_type == "m1":
        entities += [
            XToolCPUTempSensor(coordinator, name, entry_id),
            XToolWaterTempSensor(coordinator, name, entry_id),
            XToolPurifierSensor(coordinator, name, entry_id),
        ]
    elif coordinator.device_type == "m1ultra":
        entities += [
            XToolM1UltraCPUTempSensor(coordinator, name, entry_id),
            XToolM1UltraDrivedToolSensor(coordinator, name, entry_id),
            XToolM1UltraDrivingToolSensor(coordinator, name, entry_id),
            XToolM1UltraKnifeHeadDrivingSensor(coordinator, name, entry_id),
            XToolM1UltraWorkingInfoOnlineWorkingSensor(coordinator, name, entry_id),
            XToolM1UltraWorkingInfoOfflineWorkingSensor(coordinator, name, entry_id),
            XToolM1UltraWorkingInfoTimeSystemWorkSensor(coordinator, name, entry_id),
            XToolM1UltraWorkingInfoTimeModeWorkingSensor(coordinator, name, entry_id),
            XToolM1UltraSmokingFanCurrentSensor(coordinator, name, entry_id),
            XToolM1UltraAirassistPowerSensor(coordinator, name, entry_id),
            XToolM1UltraPositionXSensor(coordinator, name, entry_id),
            XToolM1UltraPositionYSensor(coordinator, name, entry_id),
            XToolM1UltraZTCOutputTempSensor(coordinator, name, entry_id),
            XToolM1UltraWiFiIPSensor(coordinator, name, entry_id),
            XToolM1UltraMacAddrSensor(coordinator, name, entry_id),
            XToolM1UltraSerialNrSensor(coordinator, name, entry_id),
            XToolM1UltraFillLightSensor(coordinator, name, entry_id),
            XToolM1UltraSmokingFanLevelSensor(coordinator, name, entry_id),
        ]

    async_add_entities(entities, True)


class _XToolBaseSensor(CoordinatorEntity[XToolCoordinator], SensorEntity):
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


class XToolWorkStateSensor(_XToolBaseSensor):
    """Work state (Running, Idle, Sleep, Done, ...)."""

    _attr_icon = "mdi:laser-pointer"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Status"                    # visible as "<Name> Status"
        self._attr_unique_id = f"{entry_id}_status"   # stable

    @property
    def suggested_object_id(self) -> str:
        # Result: sensor.<name_slug>_<device_type>_status
        return f"{self.coordinator.device_type}_status"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        if data.get("_unavailable"):
            return "Unavailable"

        if self.coordinator.device_type in ("f1", "p2", "apparel"):
            mode = str(data.get("mode", "")).strip().upper()
            if mode:
                return self._map_mode(mode)
            return "Unknown"

        if self.coordinator.device_type == "m1":
            status = str(data.get("STATUS", "")).strip().upper()
            if status:
                return self._map_status(status)
            return "Unknown"

        if self.coordinator.device_type == "m1ultra":
            if data.get("runningStatus") and data["runningStatus"].get("curMode"):
                mode = str(data["runningStatus"]["curMode"].get("mode", "")).strip().upper()
                sub_mode = str(data["runningStatus"]["curMode"].get("subMode", "")).strip().upper()
                if mode or sub_mode:
                    return self._map_m1ultra_mode(mode, sub_mode)
            return "Unknown"

        return "Unknown"

    def _map_mode(self, mode: str) -> str:
        mapping = {"P_WORK_DONE": "Done", "WORK": "Running", "P_SLEEP": "Sleep", "P_IDLE": "Idle"}
        return mapping.get(mode, "Unknown")

    def _map_status(self, status: str) -> str:
        mapping = {
            "P_FINISH": "Done",
            "P_WORKING": "Running",
            "P_SLEEP": "Sleep",
            "P_ONLINE_READY_WORK": "Ready",
            "P_IDLE": "Idle",
        }
        return mapping.get(status, "Unknown")

    def _map_m1ultra_mode(self, mode: str, sub_mode: str) -> str:
        # M1 Ultra modes based on the provided data
        mapping = {
            "P_IDLE": "Idle",
            "P_MEASURE": "Probing",
            "P_SLEEP": "Sleep",
            "WORK_WORKREADY": "Ready",
            "WORK_WORKING": "Running",
            "WORK_WORKPAUSE": "Paused",

        }
        if sub_mode:
            return f"{mapping.get(mode, mode)}_{sub_mode}" if mode else sub_mode
        return mapping.get(mode, mode) if mode else "Unknown"


# ----- M1 extra sensors -----

class _M1Base(_XToolBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> dict[str, Any]:
        info = super().device_info
        info["model"] = "M1"
        return info


class XToolCPUTempSensor(_M1Base):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "CPU Temp"
        self._attr_unique_id = f"{entry_id}_cpu_temp"

    @property
    def suggested_object_id(self) -> str:
        # Result: sensor.<name_slug>_<device_type>_cpu_temp
        return f"{self.coordinator.device_type}_cpu_temp"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        return None if data.get("_unavailable") else data.get("CPU_TEMP")


class XToolWaterTempSensor(_M1Base):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Water Temp"
        self._attr_unique_id = f"{entry_id}_water_temp"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_water_temp"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        return None if data.get("_unavailable") else data.get("WATER_TEMP")


class XToolPurifierSensor(_M1Base):
    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Purifier"
        self._attr_unique_id = f"{entry_id}_purifier"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_purifier"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        return None if data.get("_unavailable") else data.get("Purifier")

# ----- M1 Ultra sensors -----

class _M1UltraBaseMeasurement(_XToolBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> dict[str, Any]:
        info = super().device_info
        info["model"] = "M1 Ultra"
        return info

class _M1UltraBase(_XToolBaseSensor):

    @property
    def device_info(self) -> dict[str, Any]:
        info = super().device_info
        info["model"] = "M1 Ultra"
        return info


class XToolM1UltraCPUTempSensor(_M1UltraBaseMeasurement):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "CPU Temp"
        self._attr_unique_id = f"{entry_id}_cpu_temp"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_cpu_temp"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("runningStatus"):
            return None
        return data["runningStatus"].get("cpuTemp")


class XToolM1UltraDrivedToolSensor(_M1UltraBase):
    _attr_icon = "mdi:dock-left"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Basic Carriage"
        self._attr_unique_id = f"{entry_id}_basic_carriage"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_basic_carriage"
    
    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("workhead_ID"):
            return None
        tool_id = data["workhead_ID"].get("drived")
        mapping = {
            41: "Empty",
            42: "Drawing Pen",
            43: "Fine-Point Blade",
            44: "Hot Foil Pen",
        }
        return mapping.get(tool_id, "Unknown")


class XToolM1UltraDrivingToolSensor(_M1UltraBase):
    _attr_icon = "mdi:dock-right"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Multi-function Carriage"
        self._attr_unique_id = f"{entry_id}_multi_function_carriage"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_multi_function_carriage"
    
    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("workhead_ID"):
            return None
        tool_id = data["workhead_ID"].get("driving")
        mapping = {
            0: "Empty",
            15: "10W Laser Module",
            29: "Multi-function Module",
            31: "Ink Module",
        }
        return mapping.get(tool_id, "Unknown")


class XToolM1UltraKnifeHeadDrivingSensor(_M1UltraBase):
    _attr_icon = "mdi:box-cutter"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Multi-function Module Tool"
        self._attr_unique_id = f"{entry_id}_multi_function_module_tool"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_multi_function_module_tool"
    
    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("knife_head"):
            return None
        if data.get("_unavailable"):
            return None
        
        driving_tool_id = None
        if data.get("workhead_ID"):
            driving_tool_id = data["workhead_ID"].get("driving")

        if driving_tool_id != 29:  # 29 is "Knife holder"
            return "Not Installed"

        if not data.get("knife_head"):
            return None
        
        tool_id = data["knife_head"].get("driving")
        mapping = {
             22: "Foil Transfer Tip",
             23: "Cutting Blade",
             24: "Rotary Blade",
        }
        return mapping.get(tool_id, "Unknown")


class XToolM1UltraWorkingInfoOnlineWorkingSensor(_M1UltraBase):
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Operating Times (Online)"
        self._attr_unique_id = f"{entry_id}_operating_times_online"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_operating_times_online"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("workingInfo"):
            return None
        return data["workingInfo"].get("numOnlineWorking")


class XToolM1UltraWorkingInfoOfflineWorkingSensor(_M1UltraBase):
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Operating Times (Offline)"
        self._attr_unique_id = f"{entry_id}_operating_times_offline"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_operating_times_offline"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("workingInfo"):
            return None
        return data["workingInfo"].get("numOfflineWorking")


class XToolM1UltraWorkingInfoTimeSystemWorkSensor(_M1UltraBaseMeasurement):
    _attr_icon = "mdi:timer-outline"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_suggested_unit_of_measurement = UnitOfTime.HOURS

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Standby Time"
        self._attr_unique_id = f"{entry_id}_standby_time"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_standby_time"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("workingInfo"):
            return None
        return data["workingInfo"].get("timeSystemWork")


class XToolM1UltraWorkingInfoTimeModeWorkingSensor(_M1UltraBaseMeasurement):
    _attr_icon = "mdi:timer-outline"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_suggested_unit_of_measurement = UnitOfTime.HOURS

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Operating Time"
        self._attr_unique_id = f"{entry_id}_operating_time"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_operating_time"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("workingInfo"):
            return None
        return data["workingInfo"].get("timeModeWorking")



class XToolM1UltraSmokingFanCurrentSensor(_M1UltraBaseMeasurement):
    _attr_icon = "mdi:current-ac"
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.MILLIAMPERE

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Exhaust Fan Current"
        self._attr_unique_id = f"{entry_id}_exhaust_fan_current"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_exhaust_fan_current"
    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("smoking_fan"):
            return None
        return data["smoking_fan"].get("current")

class XToolM1UltraSmokingFanLevelSensor(_M1UltraBaseMeasurement):
    _attr_icon = "mdi:fan-auto"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Exhaust Fan Level"
        self._attr_unique_id = f"{entry_id}_exhaust_fan_level"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_exhaust_fan_level"
    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("smoking_fan"):
            return None
        level = data["smoking_fan"].get("current")
        mapping = {
            0: 0,
            105: 1,
            150: 2,
            200: 3,
            255: 4
        }
        return mapping.get(level, 0)

class XToolM1UltraAirassistPowerSensor(_M1UltraBase):
    _attr_icon = "mdi:fan-auto"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Air Assist Level"
        self._attr_unique_id = f"{entry_id}_airassist_level"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_airassist_level"
    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("airassist"):
            return None
        return data["airassist"].get("power")



class XToolM1UltraPositionXSensor(_M1UltraBaseMeasurement):
    _attr_icon = "mdi:axis-x-arrow"
    _attr_suggested_display_precision = 2


    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Position X"
        self._attr_unique_id = f"{entry_id}_position_x"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_position_x"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("position"):
            return None
        return data["position"].get("X")


class XToolM1UltraPositionYSensor(_M1UltraBaseMeasurement):
    _attr_icon = "mdi:axis-y-arrow"
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Position Y"
        self._attr_unique_id = f"{entry_id}_position_y"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_position_y"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("position"):
            return None
        return data["position"].get("Y")


class XToolM1UltraZTCOutputTempSensor(_M1UltraBaseMeasurement):
    _attr_icon = "mdi:thermometer"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Z NTC Output Temp"
        self._attr_unique_id = f"{entry_id}_z_ntc_temp"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_z_ntc_temp"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("Z_ntc_temp"):
            return None
        return data["Z_ntc_temp"].get("value")



class XToolM1UltraWiFiIPSensor(_M1UltraBase):
    _attr_icon = "mdi:ip-outline"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "WiFi IP Address"
        self._attr_unique_id = f"{entry_id}_wifi_ip_address"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_wifi_ip_address"
    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("machineInfo"):
            return None
        return data["machineInfo"]["ip"].get("wlan0-ip")

class XToolM1UltraMacAddrSensor(_M1UltraBase):
    _attr_icon = "mdi:lan"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "MAC Address"
        self._attr_unique_id = f"{entry_id}_mac_address"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_mac_address"
    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("machineInfo"):
            return None
        return data["machineInfo"].get("mac")

class XToolM1UltraSerialNrSensor(_M1UltraBase):
    _attr_icon = "mdi:identifier"

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Serial Number"
        self._attr_unique_id = f"{entry_id}_serial_number"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_serial_number"
    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("machineInfo"):
            return None
        return data["machineInfo"].get("sn")

class XToolM1UltraFillLightSensor(_M1UltraBaseMeasurement):
    _attr_icon = "mdi:lightbulb"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: XToolCoordinator, name: str, entry_id: str) -> None:
        super().__init__(coordinator, name, entry_id)
        self._attr_name = "Fill Light Brightness"
        self._attr_unique_id = f"{entry_id}_fill_light_brightness"

    @property
    def suggested_object_id(self) -> str:
        return f"{self.coordinator.device_type}_fill_light_brightness"
    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if data.get("_unavailable") or not data.get("config"):
            return None
        brightness = data["config"].get("fillLightBrightness")
        if brightness is None:
            return None
        # Convert 0-255 to 0-100%
        return round((brightness / 255) * 100)
