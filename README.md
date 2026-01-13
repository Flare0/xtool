# XTool Home Assistant Integration

This is a **custom integration for Home Assistant** that connects and monitors **xTool laser engravers** such as **P2**, **F1**, **M1**, and **Apparel**.

> ⚠️ This integration is an independent community project.  
> I am **not affiliated with xTool** or its employees — but I’d love to collaborate with the xTool team for further testing 😉.

---

## ✨ Features

- **Native Home Assistant integration** (no YAML required)
- **Multiple devices supported** — each xTool appears as its own device
- **Automatic entity creation** per device:
  - `binary_sensor.<name>_<device_type>_power` → shows if the machine is reachable/on
  - `sensor.<name>_<device_type>_status` → shows the current working state
  - **M1** adds extra sensors:
    - `sensor.<name>_m1_cpu_temp`
    - `sensor.<name>_m1_water_temp`
    - `sensor.<name>_m1_purifier`
- Typical status values: `Running`, `Done`, `Idle`, `Sleep`, `Ready`, `Unavailable`, `Unknown`

---

## 🧩 Installation

### via HACS (recommended)
1. Add this repository as a **Custom Repository** in HACS.  
2. Search for **“XTool”** and install.  
3. Restart Home Assistant.

### Manual Installation
1. Download or clone this repository.  
2. Copy the folder `xtool` into your `config/custom_components/` directory.  
3. Restart Home Assistant.

---

## ⚙️ Configuration (UI)

1. Go to **Settings → Devices & Services → Add Integration**.  
2. Search for **“XTool”**.  
3. Enter:
   - **Name** → freely chosen (e.g. `Laser1`)
   - **IP Address** → IP of your xTool device
   - **Device Type** → choose between `P2`, `F1`, `M1`,`M1 Ultra`, or `Apparel`
4. Confirm — done ✅  

Each device automatically creates the appropriate entities in Home Assistant based on its **`name`** and **`device_type`**.

---

## 🆔 Entity Naming

Entity IDs are automatically generated using the **Name** and **Device Type** you provide during setup:

| Example | Entities Created |
|----------|------------------|
| Name: `Laser1`, Type: `F1` | `binary_sensor.laser1_f1_power`<br>`sensor.laser1_f1_status` |
| Name: `Laser2`, Type: `P2` | `binary_sensor.laser2_p2_power`<br>`sensor.laser2_p2_status` |
| Name: `Studio`, Type: `M1` | `sensor.studio_m1_status`<br>`sensor.studio_m1_cpu_temp`<br>`sensor.studio_m1_water_temp`<br>`sensor.studio_m1_purifier` |

---

## 💬 Possible Status Values

| Status | Meaning | Device |
|---------|----------|----------|
| `Running` | The laser is currently engraving | `All` |
| `Done` | The engraving job is finished | `P2` `F1` `M1` `Apparel` |
| `Idle` | The machine is idle | `All` |
| `Sleep` | The device is in sleep mode | `All` |
| `Ready` | Machine ready for work | `M1` `M1 Ultra` |
| `Probing` | Auto Measure or Marking | `M1 Ultra` |
| `Unavailable` | Device offline or unreachable |  |
| `Unknown` | Unknown or invalid response |  |

---

## 🤖 Example Automations

### 🔹 1. Turn on exhaust fan when Laser1 (F1) starts
```yaml
alias: Laser1 – Exhaust Fan
description: Turn on the exhaust fan when Laser1 (F1) starts engraving
triggers:
  - trigger: state
    entity_id: sensor.laser1_f1_status
actions:
  - choose:
      - conditions:
          - condition: state
            entity_id: sensor.laser1_f1_status
            state: Running
        sequence:
          - service: switch.turn_on
            target:
              entity_id: switch.exhaust_fan
    default:
      - service: switch.turn_off
        target:
          entity_id: switch.exhaust_fan
mode: single
```

### 🔹 2. Notify when Laser1 job is finished
```yaml
alias: Laser1 – Job Finished
description: Send a mobile notification when the engraving is done
triggers:
  - trigger: state
    entity_id: sensor.laser1_f1_status
    to: Done
actions:
  - service: notify.mobile_app_my_phone
    data:
      title: "xTool Laser1 – Job Completed"
      message: "Your engraving on the F1 is done ✅"
mode: single
```

### 🔹 3. Prevent blinds from closing while Laser2 (P2) is on
```yaml
alias: Blinds – Safe Close with Laser2 Check
description: Prevent blinds from closing if Laser2 (P2) is powered on
trigger:
  - platform: state
    entity_id: cover.living_room_blinds
    to: closing
condition:
  - condition: state
    entity_id: binary_sensor.laser2_p2_power
    state: "on"
action:
  - service: cover.stop_cover
    target:
      entity_id: cover.living_room_blinds
  - service: notify.mobile_app_my_phone
    data:
      message: "⚠️ Blinds closing blocked: Laser2 (P2) is currently powered ON."
mode: single
```

### 🔹 4. Play an audio notification when Laser1 finishes
```yaml
alias: Laser1 – Audio Notification
description: Play a short audio clip when Laser1 (F1) completes a job
triggers:
  - trigger: state
    entity_id: sensor.laser1_f1_status
    to: Done
actions:
  - service: media_player.play_media
    target:
      entity_id: media_player.living_room_speaker
    data:
      media_content_id: "https://example.com/sounds/job_done.mp3"
      media_content_type: "music"
mode: single
```


##  M1 Ultra
### Entities card
```yaml
type: entities
entities:
  - entity: binary_sensor.devicename_m1ultra_power
  - entity: sensor.devicename_m1ultra_status
  - type: section
    label: Tools
  - entity: sensor.devicename_m1ultra_basic_carriage
  - entity: sensor.devicename_m1ultra_multi_function_carriage
  - entity: binary_sensor.devicename_m1ultra_multi_function_carriage_lock
  - entity: sensor.devicename_m1ultra_multi_function_module_tool
  - entity: binary_sensor.devicename_m1ultra_ink_module_cable
  - entity: button.devicename_sync_multi_function_module
  - type: section
    label: Accessories
  - entity: binary_sensor.devicename_m1ultra_electrostatic_mat
  - entity: binary_sensor.devicename_m1ultra_electrostatic_mat_static
  - type: divider
  - entity: binary_sensor.devicename_m1ultra_raiser
  - entity: binary_sensor.devicename_m1ultra_hatch
  - type: divider
  - entity: binary_sensor.devicename_m1ultra_exhaust_fan
  - entity: binary_sensor.devicename_m1ultra_exhaust_fan_state
  - entity: sensor.devicename_m1ultra_exhaust_fan_level
  - entity: sensor.devicename_m1ultra_exhaust_fan_current
  - type: divider
  - entity: binary_sensor.devicename_m1ultra_external_purifier
  - type: divider
  - entity: binary_sensor.devicename_m1ultra_air_assist
  - entity: sensor.devicename_m1ultra_airassist_level
  - type: section
    label: States
  - entity: binary_sensor.devicename_m1ultra_baseplate
  - entity: binary_sensor.devicename_m1ultra_lid
  - entity: sensor.devicename_m1ultra_fill_light_brightness
  - entity: binary_sensor.devicename_m1ultra_usb_machine_lock
  - type: section
    label: Time
  - entity: sensor.devicename_m1ultra_operating_times_offline
  - entity: sensor.devicename_m1ultra_operating_times_online
  - entity: sensor.devicename_m1ultra_operating_time
  - entity: sensor.devicename_m1ultra_standby_time
  - type: section
    label: Info
  - entity: sensor.devicename_m1ultra_wifi_ip_address
  - entity: sensor.devicename_m1ultra_mac_address
  - entity: sensor.devicename_m1ultra_serial_number
  - entity: sensor.devicename_m1ultra_position_x
  - entity: sensor.devicename_m1ultra_position_y
  - entity: sensor.devicename_m1ultra_cpu_temp
  - entity: sensor.devicename_m1ultra_z_ntc_temp
title: XTool M1 Ultra
```

Replace "devicename" with the name of your device.



### Missing for M1 Ultra
- Some info for External Purifier
- RA2 states, Seems to not monitor if plugged in or not
- Workhead ID for 20W Laser



## Support My Work
If you enjoy my projects or find them useful, consider supporting me on [Ko-fi](https://ko-fi.com/bassxt)!

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/bassxt)

## Collaboration
If you work at xTool or are part of the development team —
I’d love to collaborate for extended testing, new model support, or official API insights 😉
Just reach out!
