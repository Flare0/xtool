from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import requests
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_IP_ADDRESS,
    CONF_DEVICE_TYPE,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# Diese Integration hat keine YAML-Konfiguration und wird ausschließlich über Config Entries (UI) eingerichtet.
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


class XToolCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Koordinator, der die Statusdaten vom Gerät abfragt."""

    def __init__(self, hass: HomeAssistant, ip_address: str, device_type: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"xtool_{ip_address}",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )
        self.ip_address = ip_address
        self.device_type = device_type.lower()

    def _fetch_m1ultra_data(self, endpoint: str, method: str = "GET", json_data: dict | None = None) -> Any | None:
        url = f"http://{self.ip_address}:8080{endpoint}"
        try:
            if method == "POST":
                resp = requests.post(url, json=json_data, timeout=5)
            else:
                resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as err:
            _LOGGER.debug("XTool M1 Ultra %s connection error for %s: %s", self.ip_address, endpoint, err)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("XTool M1 Ultra %s error for %s: %s", self.ip_address, endpoint, err)
        return None

    def _fetch_data_sync(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        try:
            if self.device_type == "m1ultra":
                # Version check - this is also used to confirm device is M1 Ultra
                version_data = self._fetch_m1ultra_data("/system?action=version_v2")
                if version_data:
                    data.update(version_data)

                # Running status
                running_status_response = self._fetch_m1ultra_data("/device/runningStatus")
                if running_status_response and running_status_response.get("code") == 0:
                    data.update({"runningStatus": running_status_response.get("data")})

                # Machine info
                machine_info_response = self._fetch_m1ultra_data("/device/machineInfo")
                if machine_info_response and machine_info_response.get("code") == 0:
                    data.update({"machineInfo": machine_info_response.get("data")})

                # Workhead ID
                workhead_id_response = self._fetch_m1ultra_data("/peripheral/workhead_ID", "POST", {"action": "get"})
                if workhead_id_response and workhead_id_response.get("code") == 0:
                    data.update({"workhead_ID": workhead_id_response.get("data")})

                # Knife head
                knife_head_response = self._fetch_m1ultra_data("/peripheral/knife_head", "POST", {"action": "get"})
                if knife_head_response and knife_head_response.get("code") == 0:
                    data.update({"knife_head": knife_head_response.get("data")})

                # Additional M1 Ultra peripherals
                working_info_response = self._fetch_m1ultra_data("/device/workingInfo")
                if working_info_response and working_info_response.get("code") == 0:
                    data.update({"workingInfo": working_info_response.get("data")})

                drawer_response = self._fetch_m1ultra_data("/peripheral/drawer")
                if drawer_response and drawer_response.get("code") == 0:
                    data.update({"drawer": drawer_response.get("data")})

                smoking_fan_response = self._fetch_m1ultra_data("/peripheral/smoking_fan")
                if smoking_fan_response and smoking_fan_response.get("code") == 0:
                    data.update({"smoking_fan": smoking_fan_response.get("data")})

                ext_purifier_response = self._fetch_m1ultra_data("/peripheral/ext_purifier")
                if ext_purifier_response and ext_purifier_response.get("code") == 0:
                    data.update({"ext_purifier": ext_purifier_response.get("data")})

                machine_lock_response = self._fetch_m1ultra_data("/peripheral/machine_lock")
                if machine_lock_response and machine_lock_response.get("code") == 0:
                    data.update({"machine_lock": machine_lock_response.get("data")})

                gap_response = self._fetch_m1ultra_data("/peripheral/gap")
                if gap_response and gap_response.get("code") == 0:
                    data.update({"gap": gap_response.get("data")})

                heighten_response = self._fetch_m1ultra_data("/peripheral/heighten")
                if heighten_response and heighten_response.get("code") == 0:
                    data.update({"heighten": heighten_response.get("data")})

                airassist_response = self._fetch_m1ultra_data("/peripheral/airassist")
                if airassist_response and airassist_response.get("code") == 0:
                    data.update({"airassist": airassist_response.get("data")})

                adsorption_mat_response = self._fetch_m1ultra_data("/peripheral/adsorption_mat", "POST", {"action": "get"})
                if adsorption_mat_response and adsorption_mat_response.get("code") == 0:
                    data.update({"adsorption_mat": adsorption_mat_response.get("data")})

                position_response = self._fetch_m1ultra_data("/peripheral/position", "POST", {"aix": "all", "datatype": "absolute"})
                if position_response and position_response.get("code") == 0:
                    data.update({"position": position_response.get("data")})

                z_ntc_temp_response = self._fetch_m1ultra_data("/peripheral/Z_ntc_temp", "POST", {"action": "get"})
                if z_ntc_temp_response and z_ntc_temp_response.get("code") == 0:
                    data.update({"Z_ntc_temp": z_ntc_temp_response.get("data")})

                config_kv = ["fillLightBrightness", "purifierTimeout", "workingMode", "flameLevelHLSelect", "airassistCut", "airassistGrave", "EXTPurifierTimeout", "purifierSpeed", "purifierBlockAlarm", "beepEnable", "taskId", "adsorptionMatAutoControl", "isAbnormalShakingMachine", "flameLevel1ValueH", "flameLevel1ValueL"]
                config_response = self._fetch_m1ultra_data("/config/get", "POST", {"alias": "config", "type": "user", "kv": config_kv})
                if config_response and config_response.get("code") == 0:
                    data.update({"config": config_response.get("data")})

                inkjet_printer_get_response = self._fetch_m1ultra_data("/peripheral/inkjet_printer", "POST", {"action": "get"})
                if inkjet_printer_get_response and inkjet_printer_get_response.get("code") == 0:
                    data.update({"inkjet_printer_get": inkjet_printer_get_response.get("data")})

                _LOGGER.debug("XTool M1 Ultra %s full response: %s", self.ip_address, data)



            else:
                # Existing device types
                url = f"http://{self.ip_address}:8080/status"
                resp = requests.get(url, timeout=5)
                resp.raise_for_status()
                data.update(resp.json())
                _LOGGER.debug("XTool %s response: %s", self.ip_address, data)

            return data
        except requests.exceptions.ConnectionError as err:
            _LOGGER.debug("XTool %s connection error: %s", self.ip_address, err)
            return {"_unavailable": True}
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("XTool %s error: %s", self.ip_address, err)
            return {"_unavailable": True}

    async def _async_update_data(self) -> dict[str, Any]:
        return await self.hass.async_add_executor_job(self._fetch_data_sync)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Eintrag einrichten."""
    ip = entry.data[CONF_IP_ADDRESS]
    dev_type = entry.data[CONF_DEVICE_TYPE]

    coordinator = XToolCoordinator(hass, ip, dev_type)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "name": entry.title,  # dein vergebener Name, z. B. "p2"
        "entry_id": entry.entry_id,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
