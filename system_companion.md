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
- Managed in its own repo (`~/ros2_ws`) and not backed up under `System_files`.

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

## Auto Sync Log
**2026-02-22 13:19**
- A	System_files/ros2_ws/src/px4-ros2-interface-lib/examples/cpp/modes/manual/include/mode.hpp.save
- M	logs/system_files_sync.log
- M	scripts/system_files_sync.sh
- A	system_companion.mdnn##

## 13) AIDE Integrity Monitoring
Status captured on **2026-02-22**:
- `aide` installed (`AIDE 0.18.6`).
- `dailyaidecheck.timer` is enabled and active.
- Timer next trigger: **2026-02-23 02:35:19 IST**.
- Manual start was executed: `sudo systemctl start dailyaidecheck.service`.
- `dailyaidecheck.service` entered `activating (start)` and ran `aide --update`.

Observed files:
- `/var/log/aide/first-check-2026-02-22_17-59.log` (0 bytes)
- `/var/log/aide/first-check-2026-02-22_17-51.log` (0 bytes)
- `/var/log/aide/first-check-2026-02-22_17-49.log` (0 bytes)
- `/var/log/aide/first-check-2026-02-22_17-48.log` (0 bytes)
- `/var/log/aide/first-check-2026-02-22_17-40.log` (0 bytes)

Notes:
- Reading root-owned AIDE logs may require sudo password (`sudo -n` can fail depending on session).
- To re-check quickly:
  - `sudo systemctl status dailyaidecheck.timer --no-pager`
  - `sudo systemctl status dailyaidecheck.service --no-pager`
  - `sudo ls -lt /var/log/aide/first-check-*.log`

### AIDE Run Log
Use this block format for each new run:

**YYYY-MM-DD HH:MM TZ**
- Trigger: manual (`systemctl start dailyaidecheck.service`) / timer
- Service result: success / failed / timeout
- Database action: update / check / init
- Log file: `/var/log/aide/<file>.log`
- Findings summary: no changes / expected changes / unexpected changes
- Follow-up action: none / reviewed / fixed / pending

First recorded entry:

**2026-02-22 18:21 IST**
- Trigger: manual (`sudo systemctl start dailyaidecheck.service`)
- Service result: in progress at capture time (`activating (start)`)
- Database action: `aide --update`
- Log file(s): `/var/log/aide/first-check-2026-02-22_17-59.log` and earlier same-day files
- Findings summary: pending (log content requires sudo access)
- Follow-up action: re-check after service completes

## 14) Relay Station (vind-rly) Install + Recovery Runbook
Current known access path:
- Relay reachable via WFB tunnel IP `10.5.5.77` (from drone side).
- Relay direct LAN/Wi-Fi management IP may change during WPA/P2P setup.
- When relay uses the same adapter for WPA/P2P and other links, temporary disconnect can happen.

Target behavior:
- Relay acts as GS bridge for WFB-NG.
- Ground systems (QGC or any OS) connect to relay management SSH on `:22`.
- Ground systems connect to drone SSH through relay on `:2222`.

Critical rule:
- In `/etc/wifibroadcast.cfg` keep `[gs_tunnel] default_route = False`.
- Do not set tunnel default route to true on relay in this mixed-network setup.

### Safe implementation order
1. Prepare base packages:
   - `sudo apt-get update`
   - `sudo apt-get install -y wpasupplicant wireless-tools net-tools dnsmasq openssh-server autossh socat`
2. Configure WFB first and verify tunnel still works:
   - Relay tunnel interface IP should be `10.5.5.77/24`.
   - Drone side tunnel interface should be `10.5.5.87/24`.
3. Configure relay management network (LAN/Wi-Fi) with static plan.
4. Configure WPA/P2P only after confirming fallback access path.
5. Add boot services (`ssh`, WFB services, relay P2P service, tunnel service).
6. Reboot once and validate all paths.

### WPA/P2P baseline
`/etc/wpa_supplicant/wpa_supplicant.conf`
- `ctrl_interface=/var/run/wpa_supplicant GROUP=netdev`
- `update_config=1`
- `device_name=VIND_RLY_P2P`
- Optional P2P network block as required by field pairing.

P2P startup commands:
- `wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf -C /var/run/wpa_supplicant`
- `wpa_cli -i wlan0 p2p_group_add persistent=0`
- `ifconfig p2p-wlan0-0 10.5.6.101 netmask 255.255.255.0 up`
- `wpa_cli -i p2p-wlan0-0 wps_pin any 1987`

### Drone SSH bridge through relay
Use service to expose relay port `2222` to drone SSH:
- Listen: relay management IP `:2222`
- Target: `10.5.5.87:22` (drone over WFB tunnel)
- Recommended backend: `socat` or `autossh` systemd service with restart policy.

### Validation checklist after each change
1. `ip -br a` shows tunnel interface with `10.5.5.77/24`.
2. `ping 10.5.5.87` succeeds from relay.
3. `systemctl status wifibroadcast@gs.service` is active.
4. `ss -tulpen | rg 2222` shows listener on relay.
5. Ground station can:
   - SSH relay: `ssh <user>@<relay_mgmt_ip> -p 22`
   - SSH drone via relay: `ssh <user>@<relay_mgmt_ip> -p 2222`

### Recovery when relay disconnects mid-setup
1. Re-enter relay through tunnel path (current known: `10.5.5.77`).
2. Stop temporary P2P flow if needed:
   - `sudo pkill -f \"wpa_supplicant.*wlan0\"`
   - `sudo ip link set p2p-wlan0-0 down || true`
3. Restore known-good WFB config:
   - Ensure `[gs_tunnel] default_route = False`
   - Restart WFB:
     - `sudo systemctl restart wifibroadcast.service wifibroadcast@gs.service`
4. Confirm tunnel ping to drone (`10.5.5.87`) before reattempting WPA/P2P.

### Notes for future Codex sessions
- Always confirm current reachable relay IP before making network changes.
- Prefer applying one network subsystem at a time (WFB -> management LAN/Wi-Fi -> P2P -> bridge).
- Avoid enabling competing managers on same interface during bring-up (NetworkManager vs manual wpa_supplicant).
**2026-02-23 18:24**
- A	Setup_Procedure_for_Relay_Station.docx
- A	System_files/etc/sudoers.d/roz-codex
- M	system_companion.md
