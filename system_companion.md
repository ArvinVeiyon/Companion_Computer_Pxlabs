# Vind-Roz — PX4 Companion Computer (Drone + Rover)

This document is the living reference for the **Vind-Roz** companion computer.
Hostname: `Vind-Roz` | Platform: PX4 — used across aerial drone and ground rover builds.

## 1) System Overview
**Vehicle Types:** Aerial drone / Ground rover (same companion, vehicle-specific PX4 airframe config)
**Primary Goal:** Autonomy / offboard control / vision / manual RC modes

## 2) Hardware
**Flight Controller (FC):**
- Model: Custom board based on Pixhawk 6X-RT reference design (NXP)
- MCU family: NXP i.MX RT1176 (RT11xx, dual-core Cortex-M7 + M4)
- PX4 support status: supported (px4_fmu-v6xrt target)
- Note: custom in-house PCB — not the off-the-shelf Holybro unit

**Companion Computer:**
- Board model: Raspberry Pi 5 Model B Rev 1.0
- CPU/SoC: Broadcom BCM2712, ARM Cortex-A76 quad-core, aarch64
- RAM: 8 GB LPDDR4X
- Storage: ~64 GB SD card (`/dev/mmcblk0p2` 58 G, 63% used as of 2026-03-08)
- OS: Ubuntu 24.04.1 LTS (Noble Numbat), kernel 6.8.0-1018-raspi

**Sensors:**
- GNSS: (document port/model)
- IMU (if external): (document)
- Camera(s): Primary `/dev/video0` (1280×720, MJPEG), Secondary `/dev/video2` (1280×720, MJPEG, PiP)
- Lidar/sonar: TFmini (ROS2 node: `tfmini.service`)
- Other: Optical flow node in ros2_ws

**Power:**
- Battery: LiPo 4S (14.8 V nominal) or 6S (22.2 V nominal) depending on build
- Power distribution: (document PDB/ESC setup per vehicle)
- FC power input: (document)
- Companion power input: (document)

## 3) Firmware / Software Versions
**PX4:**
- Version: v1.16.0-rc1
- Build type: custom pre-release
- Git commit: c5b8445ffc (586 commits past v1.16.0-rc1 tag)

**Companion Software:**
- OS: Ubuntu 24.04.1 LTS, kernel 6.8.0-1018-raspi
- ROS2: Jazzy (ros-jazzy-*)
- Python: 3.12.3
- MAVLink toolchain: mavlink-router (custom build, `/usr/local/bin/usr/bin/mavlink-routerd`)
- Micro-XRCE-DDS Agent: `/usr/local/bin/MicroXRCEAgent` (source build in `~/Micro-XRCE-DDS-Agent`)
- WFB-NG: `~/wfb-ng` (WiFi broadcast link)
- AIDE: 0.18.6 (integrity monitoring)

**ROS2 Workspace packages** (`~/ros2_ws/src/`):
- arm_drone, collision_manual_mode, obstacle_distance, optical_flow
- px4_msgs, px4-ros2-interface-lib, px4_ros_com
- rc_control, rov_collision_stop, rov_ext, rov_manual
- tfmini_sensor, vision_streaming

## 4) Connections
**FC <-> Companion Links (two serial connections):**
- MAVLink: `/dev/ttyAMA0` @ 921600 baud → mavlink-router
- uXRCE-DDS: `/dev/ttyAMA4` @ 921600 baud → MicroXRCEAgent

**Peripheral Connections:**
- GNSS: (document)
- Radio/Telemetry: WFB-NG via WiFi adapter (wfb-ng)
- Camera: CSI (auto-detect)
- Sonar/Lidar: TFmini (UART, via tfmini_sensor ROS2 node)

## 5) PX4 Configuration
**MAVLink (via mavlink-router `/etc/mavlink-router/main.conf`):**
- TCP server: port 5760 (GCS)
- UART endpoint: `/dev/ttyAMA0` @ 921600
- UDP endpoint local2: `192.168.1.100:14550`
- UDP endpoint WFB-NG: `127.0.0.1:14550`

**uXRCE-DDS:**
- Serial: `/dev/ttyAMA4` @ 921600 → connects PX4 uORB topics to ROS2

**Autonomy / Offboard:**
- Offboard: enabled (ros2_px4_translation_node + rc_control_node)
- DDS multicast blocked on drone-wfb interface (`block-traffic.service`)

## 6) Companion Setup
**Active Systemd Services:**
| Service | Description |
|---|---|
| `mavlink.router.service` | MAVLink routing FC ↔ GCS/network |
| `microxrce-agent.service` | uXRCE-DDS bridge FC ↔ ROS2 |
| `ros2_px4_translation_node.service` | ROS2/PX4 message translation |
| `rc_control_node.service` | RC input handling |
| `ros2_external_node_reg.service` | External ROS2 node registration |
| `tfmini.service` | TFmini lidar ROS2 node |
| `vision_streaming.service` | Camera/vision streaming ROS2 node |
| `block-traffic.service` | Firewall: block DDS multicast on WFB iface |

**Video Pipeline:**
```
/dev/video0 (primary, MJPEG)  ─┐
                                ├─► FFmpeg (libx264 ultrafast) ─► RTP → 127.0.0.1:5602 ─► WFB-NG ─► GS 10.5.6.50:5600
/dev/video2 (secondary, MJPEG)─┘    PiP overlay bottom-right
```
- ROS2 node: `vision_streaming_node` (Python, package `vision_streaming`)
- Config file: `/etc/vision_streaming.conf`
- Primary: `/dev/video0`, 1280×720, 3000K bitrate
- Secondary: `/dev/video2`, 1280×720, 2000K bitrate, PiP 240×180 bottom-right
- Encoder: `libx264 ultrafast`, output format `yuv420p`
- RTP destination: `127.0.0.1:5602` → picked up by WFB-NG `drone_video` stream

**Micro XRCE-DDS Agent:**
- Binary: `/usr/local/bin/MicroXRCEAgent` (installed from source build in `~/Micro-XRCE-DDS-Agent`)
- Version: v3.0.0-2-gb9d84ac (2 commits past v3.0.0 tag)
- Transport: `serial --dev /dev/ttyAMA4 -b 921600`
- Role: bridges PX4 uORB topics ↔ ROS2 DDS middleware
- Depends on: `mavlink-router.service` (After + Wants in unit file)
- LD_LIBRARY_PATH: `/opt/ros/jazzy/lib:/usr/local/lib:/usr/lib:/lib`
- Available UART ports on this board: `ttyAMA0`, `ttyAMA2`, `ttyAMA4`, `ttyAMA10`
  - `ttyAMA0` → MAVLink (mavlink-router)
  - `ttyAMA4` → uXRCE-DDS (microxrce-agent)

**MAVLink Router (`/etc/mavlink-router/main.conf`):**
- Binary: `/usr/local/bin/usr/bin/mavlink-routerd` (unusual path — installed with bad `--prefix`, but correct and working as-is)
- UART endpoint: `/dev/ttyAMA0` @ 921600 baud (FC MAVLink)
- TCP server: port 5760 (GCS)
- UDP → `192.168.1.100:14550` (local net)
- UDP → `127.0.0.1:14550` (WFB-NG mavlink stream)

**Network:**
- WFB tunnel drone side: `10.5.5.87/24`
- WFB tunnel relay side: `10.5.5.77/24`
- Local LAN (mavlink UDP): `192.168.1.100`
- ROS2 DDS: multicast blocked on WFB interface (block-traffic.service)

## 7) WFB-NG (WiFi Broadcast) Configuration
Config file: `/etc/wifibroadcast.cfg`

**RF Settings:**
| Parameter | Value |
|---|---|
| WiFi channel | 157 (5 GHz) |
| Region | BO |
| TX power | 3000 (30 dBm × 100, for rtl8812eu) |
| Bandwidth | 20 MHz |
| MCS index | 1 |
| STBC | 1 |
| LDPC | 1 |
| Short GI | disabled |

**Streams (drone side):**
| Stream | Direction | Stream ID | Service type | Peer |
|---|---|---|---|---|
| video | TX only | 0x00 | udp_direct_tx | listen `127.0.0.1:5602` ← fed by vision_streaming ROS2 node |
| mavlink | RX 0x10 / TX 0x90 | — | mavlink | listen `0.0.0.0:14550` ← fed by mavlink-router |
| tunnel | RX 0xa0 / TX 0x20 | — | tunnel | peer `10.5.5.77/24` |

**FEC settings:**
| Stream | fec_k | fec_n |
|---|---|---|
| video | 8 | 12 |
| mavlink | 1 | 2 |
| tunnel | 2 | 4 |

**Tunnel (WFB IP layer):**
- Drone interface: `drone-wfb` @ `10.5.5.87/24`
- GS/relay interface: `gs-wfb` @ `10.5.5.77/24`
- `default_route = False` on both sides (critical — do not change)

**GS side endpoints:**
- Video → `connect://10.5.6.50:5600`
- MAVLink → `connect://10.5.6.50:14550`

**Keys:** `drone.key` / `gs.key` (tracked in `System_files/etc/`)

**Stats/API ports:**
- Drone: stats `8002`, API `8102`
- GS: stats `8003`, API `8103`

## 8) Testing Checklist
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
- `System_files/etc/systemd/system/block-traffic.service`
- `System_files/home/roz/mavlink.sh`

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
**2026-02-23 22:55**
- M	System_files/etc/netplan/50-cloud-init.yaml
**2026-03-08 10:41**
- M	System_files/etc/netplan/50-cloud-init.yaml
- A	bootstrap.sh
- A	install.sh
**2026-03-08 11:14**
- A	System_files/etc/systemd/system/block-traffic.service
- A	System_files/home/roz/mavlink.sh
