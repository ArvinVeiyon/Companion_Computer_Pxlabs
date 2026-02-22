# Rover / Drone / Marine Reference (PX4 Companion)

This document is a living reference for companion-computer setups used with PX4-based vehicles including:
- ground rovers
- aerial drones
- surface ships
- submarines / ROVs

Use this as a baseline; fill in the specifics for each build.

## 1) System Overview
**Vehicle Type:** rover / drone / ship / submarine (circle one)
**Primary Goal:** navigation / autonomy / mapping / inspection / research / other

## 2) Hardware
**Flight Controller (FC):**
- Model:
- MCU family (e.g., NXP RT6xx / RT11xx):
- PX4 support status:

**Companion Computer:**
- Board model:
- CPU/SoC:
- RAM/Storage:
- OS image and version:

**Sensors:**
- GNSS:
- IMU (if external):
- Camera(s):
- Lidar/sonar:
- Other:

**Power:**
- Battery and voltage:
- Power distribution:
- FC power input:
- Companion power input:

## 3) Firmware / Software Versions
**PX4:**
- Version (e.g., v1.16.0):
- Build type: release / custom
- Git commit (if custom):

**Companion Software:**
- OS version:
- ROS/ROS2:
- MAVLink toolchain:
- Other services:

## 4) Connections
**FC <-> Companion Link:**
- Interface: UART / USB / Ethernet
- Port names:
- Baud rate (UART):
- MAVLink instance:

**Peripheral Connections:**
- GNSS:
- Radio/Telemetry:
- Camera:
- Sonar/Lidar:

## 5) PX4 Configuration
**MAVLink:**
- Instance and port:
- Mode: normal / onboard / gimbal

**Serial Ports:**
- TELEM1/TELEM2 settings:
- GPS settings:

**Autonomy / Offboard:**
- Offboard enabled: yes/no
- Safety and failsafe:

## 6) Companion Setup
**Services:**
- MAVLink router / MAVSDK / MAVROS:
- Startup method (systemd, docker, etc.):

**Network:**
- IPs and interfaces:
- ROS2 DDS settings (if applicable):

## 7) Testing Checklist
1. FC boots and PX4 console accessible
2. Companion boots and services start
3. MAVLink link stable
4. Heartbeat from companion visible in QGC
5. Sensor data valid
6. Offboard control test (if used)

## 8) Troubleshooting
**No MAVLink connection:**
- Check port, baud, and PX4 MAVLink instance
- Verify wiring (TX/RX and ground)

**Companion cannot control vehicle:**
- Confirm arming rules and OFFBOARD enable
- Check failsafe and mode switching

**Sensor data missing:**
- Verify wiring and PX4 parameters

## 9) Notes / Decisions Log
- 
- 
- 

## 10) Attachments
- Wiring diagram:
- Parameter dump:
- Photos:

## 11) Local Backup Inventory (System_files)
All backup files are stored under `System_files` in the Codex repo and mirror their original paths.

**ROS2 workspace**
- `System_files/ros2_ws/src`
- `System_files/ros2_ws/.gitignore`
- `System_files/ros2_ws/fake_vo.py`

**Systemd services**
- `System_files/etc/systemd/system/mavlink.router.service`
- `System_files/etc/systemd/system/microxrce-agent.service`
- `System_files/etc/systemd/system/rc_control_node.service`
- `System_files/etc/systemd/system/ros2_external_node_reg.service`
- `System_files/etc/systemd/system/ros2_px4_translation_node.service`
- `System_files/etc/systemd/system/tfmini.service`
- `System_files/etc/systemd/system/vision_streaming.service`

**System configs and keys**
- `System_files/etc/mavlink-router/main.conf`
- `System_files/etc/vision_streaming.conf`
- `System_files/etc/vision_streaming.conf.bak`
- `System_files/etc/sid.conf`
- `System_files/etc/sid.conf.save`
- `System_files/etc/wifibroadcast.cfg`
- `System_files/etc/default/wifibroadcast`
- `System_files/etc/default/wifibroadcast.dpkg-old`
- `System_files/etc/default/wifibroadcast.drone_bind`
- `System_files/etc/default/wifibroadcast.gs_bind`
- `System_files/etc/logrotate.d/wifibroadcast`
- `System_files/etc/gnutls/config`
- `System_files/etc/pam.d/sshd`
- `System_files/etc/gs.key`
- `System_files/etc/drone.key`
- `System_files/etc/sudoers`

**Boot and runtime tools**
- `System_files/boot/firmware/config.txt`
- `System_files/usr/local/bin/block-traffic.sh`

**Not yet copied (need sudo if required)**
- `System_files/etc/netplan/50-cloud-init.yaml`
- `System_files/etc/ssh/sshd_config.d/50-cloud-init.conf`

## 12) Auto Sync (Boot + Daily)
Auto sync uses:
- File list: `System_files_list.txt`
- Script: `scripts/system_files_sync.sh`
- Log: `logs/system_files_sync.log`

Behavior:
- On boot and once per day, syncs originals into `System_files`.
- If changes exist, appends a change summary to this file and creates a git commit.
- Creates an annotated tag `sync-YYYYMMDD-HHMM` with the same change summary.
