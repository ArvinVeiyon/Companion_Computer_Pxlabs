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

> See Section 6b for detailed per-package documentation.

## 4) Connections
**FC <-> Companion Links (two serial connections):**
- MAVLink: `/dev/ttyAMA0` @ 921600 baud → mavlink-router
- uXRCE-DDS: `/dev/ttyAMA4` @ 921600 baud → MicroXRCEAgent

**Peripheral Connections:**
- GNSS: (document)
- Radio/Telemetry: WFB-NG via WiFi adapter (wfb-ng)
- Camera: CSI (auto-detect)
- Sonar/Lidar: TFmini (UART, via tfmini_sensor ROS2 node), LDRobot STL-19 360° LiDAR (UART, via ldlidar_stl_ros2)

**RPi5 UART Map (full):**
| ttyAMA   | UART   | GPIO TX | GPIO RX | Phys TX | Phys RX | Use                              | Baud   |
|----------|--------|---------|---------|---------|---------|----------------------------------|--------|
| ttyAMA0  | UART0  | GPIO14  | GPIO15  | Pin 8   | Pin 10  | FC MAVLink → mavlink-router      | 921600 |
| ttyAMA2  | UART2  | GPIO4   | GPIO5   | Pin 7   | Pin 29  | TFmini lidar                     | 115200 |
| ttyAMA4  | UART4  | GPIO12  | GPIO13  | Pin 32  | Pin 33  | FC uXRCE-DDS → MicroXRCEAgent    | 921600 |
| ttyAMA1  | UART1  | GPIO0   | GPIO1   | Pin 27  | Pin 28  | FREE (needs dtoverlay=uart1-pi5) | —      |
| ttyAMA3  | UART3  | GPIO8   | GPIO9   | Pin 24  | Pin 21  | STL-19 LiDAR (RX only, no PWM)   | 230400 |
| ttyAMA10 | UART10 | —       | —       | —       | —       | Internal SoC + 3-pin JST debug header (BT freed) | 115200 |
Enabled in `/boot/firmware/config.txt`: uart0, uart2, uart3-pi5, uart4
> **Debug UART:** `ttyAMA10` = `soc/serial@7d001000` = 3-pin JST connector on RPi5 board edge. Used for U-Boot/kernel console at 115200. Not for peripherals.

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
| `ldlidar.service` | LDRobot STL-19 360° LiDAR ROS2 node |
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
- Available UART ports on this board: `ttyAMA0`, `ttyAMA2`, `ttyAMA3`, `ttyAMA4` (active) | `ttyAMA1` (free, GPIO header) | `ttyAMA10` (internal SoC only)
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

## 6b) ROS2 Node Details

### rc_control_node (`rc_control` package)
- **Service:** `rc_control_node.service`
- **Node name:** `rc_control_node`
- **Source:** `ros2_ws/src/rc_control/rc_control/rc_control_node.py`
- **Config:** `ros2_ws/src/rc_control/config/rc_mapping.yaml` (master config, loaded at startup from installed share dir)
- **Subscribes:** `/fmu/out/input_rc` (px4_msgs/InputRc, BEST_EFFORT QoS)
- **Function 1 — Camera switching:**
  - RC channel: CH9 (index 8, 0-based), tolerance ±50 PWM
  - Calls `/usr/local/bin/vision_config_manager` with device path args
  - PWM positions: front=1012 (`/dev/video0`), bottom=1514 (`/dev/video2`), split=2014 (both cameras, PiP)
  - Camera config is **remotely configurable** by editing `rc_mapping.yaml` and restarting the node
- **Function 2 — Shutdown/reboot via RC:**
  - RC channel: CH10 (index 9), tolerance ±100 PWM, hold_time 2.0 s
  - PWM: 1514 → shutdown, 2014 → reboot (must hold for 2 s)

### vision_streaming_node (`vision_streaming` package)
- **Service:** `vision_streaming.service`
- **Node name:** `vision_streaming_node`
- **Source:** `ros2_ws/src/vision_streaming/vision_streaming/vision_streaming_node.py`
- **Config:** `/etc/vision_streaming.conf` (INI format, **remotely configurable**)
  - `[general]`: `rtp_ip`, `rtp_port`
  - `[primary]`: `camera_name`, `resolution`, `bitrate`, `fps`, `format`
  - `[secondary]` (optional): `camera_name`, `resolution`, `bitrate`, `pip_position`, `pip_size`
- **Function:** Launches FFmpeg to encode and RTP-stream camera(s) to WFB-NG
- **Camera switch integration:** `vision_config_manager` binary rewrites `/etc/vision_streaming.conf` and restarts this service when RC switch fires
- **PiP positions supported:** `bottom-right`, `bottom-left`, `top-right`, `top-left`, `center`

### tfmini_node (`tfmini_sensor` package)
- **Service:** `tfmini.service`
- **Node name:** `tfmini_node`
- **Source:** `ros2_ws/src/tfmini_sensor/tfmini_sensor/tfmini_node.py`
- **Hardware:** TFmini lidar on `/dev/ttyAMA2` @ 115200 baud
- **Publishes:** `/fmu/in/distance_sensor` (px4_msgs/DistanceSensor) @ 50 Hz
- **Sensor params:** range 0.3–12.0 m, downward-facing, FOV 3.6°, device_id=1987

### ldlidar_stl_ros2_node (`ldlidar_stl_ros2` package)
- **Service:** `ldlidar.service`
- **Node name:** `LD19`
- **Source:** `ros2_ws/src/ldlidar_stl_ros2/` (upstream: ldrobotSensorTeam/ldlidar_stl_ros2)
- **Hardware:** LDRobot STL-19 360° LiDAR on `/dev/ttyAMA3` @ 230400 baud
- **Wiring:** Lidar TX → RPi Pin 21 (GPIO9 RX only). No PWM motor control — motor runs at fixed speed.
- **Publishes:** `/scan` (sensor_msgs/LaserScan) | TF: `base_link` → `base_laser`
- **Launch:** `ld19.launch.py` — port hardcoded in launch file (CLI `port_name:=` arg is ignored by upstream launch file)
- **Build fix 1 (2026-04-17):** Added `#include <pthread.h>` to `ldlidar_driver/src/logger/log_module.cpp` (missing in upstream, causes build failure on GCC 14+)
- **Launch fix (2026-04-17):** Changed `port_name` in `launch/ld19.launch.py` line 35 from `/dev/ttyUSB0` → `/dev/ttyAMA3` (upstream default is wrong, CLI override silently ignored)

### optical_flow_node (`optical_flow` package)
- **Node name:** `optical_flow_node`
- **Source:** `ros2_ws/src/optical_flow/optical_flow/optical_flow_node.py`
- **Hardware:** Camera at `/dev/video3` (640×480)
- **Subscribes:** `/fmu/in/distance_sensor` (TFmini altitude), `/fmu/out/sensor_combined` (gyro)
- **Publishes:** `/fmu/in/sensor_optical_flow` (px4_msgs/SensorOpticalFlow) @ 10 Hz
- **Algorithm:** OpenCV Farneback dense optical flow
- **Note:** Not managed by a systemd service — may be launched manually or via launch file

### obstacle_distance_publisher (`obstacle_distance` package)
- **Node name:** `obstacle_distance_publisher`
- **Source:** `ros2_ws/src/obstacle_distance/obstacle_distance/obstacle_distance_node.py`
- **Hardware:** VL53L1X ToF sensor (I2C bus 1, addr 0x29), long-distance mode (mode 3)
- **Publishes:** `/fmu/in/obstacle_distance` (px4_msgs/ObstacleDistance) @ 10 Hz
- **Coverage:** Front sector (indices 0–5 of 72-element array), 5° increment, 20–400 cm range

### rov_collision_stop (`rov_collision_stop` package)
- **Source:** `ros2_ws/src/rov_collision_stop/src/main.cpp` (C++ node)
- **Function:** Emergency collision stop for rover mode

### Other packages (no active service, reference/example)
- `arm_drone` — arm/disarm utilities
- `collision_manual_mode` — C++ manual mode with collision avoidance
- `rov_ext`, `rov_manual` — rover external/manual control C++ nodes
- `px4_ros_com` — PX4 ROS2 example nodes and frame transform lib
- `px4-ros2-interface-lib` — PX4 ROS2 interface library (modes, navigation)
- `px4_msgs` — PX4 uORB message definitions for ROS2

## 6c) Live ROS2 Topics (as of 2026-03-08)
> Captured while MicroXRCEAgent + PX4 DDS bridge was active.

**FMU → Companion (subscriptions from PX4):**
- `/fmu/out/input_rc` — RC channel values (used by rc_control_node)
- `/fmu/out/vehicle_attitude` — quaternion attitude
- `/fmu/out/vehicle_local_position` / `/fmu/out/vehicle_local_position_v1`
- `/fmu/out/vehicle_global_position`
- `/fmu/out/vehicle_gps_position`
- `/fmu/out/vehicle_status` / `/fmu/out/vehicle_status_v1`
- `/fmu/out/vehicle_control_mode`
- `/fmu/out/vehicle_land_detected`
- `/fmu/out/vehicle_odometry`
- `/fmu/out/sensor_combined` — IMU gyro/accel data
- `/fmu/out/battery_status`
- `/fmu/out/home_position` / `/fmu/out/home_position_v1`
- `/fmu/out/estimator_status_flags`
- `/fmu/out/failsafe_flags`
- `/fmu/out/collision_constraints`
- `/fmu/out/manual_control_setpoint`
- `/fmu/out/timesync_status`
- `/fmu/out/airspeed_validated`
- `/fmu/out/position_setpoint_triplet`
- `/fmu/out/vtol_vehicle_status`
- `/fmu/out/event`

**Companion → FMU (published to PX4):**
- `/fmu/in/distance_sensor` — TFmini altitude lidar
- `/fmu/in/obstacle_distance` — VL53L1X front obstacle
- `/fmu/in/sensor_optical_flow` — camera optical flow
- `/fmu/in/vehicle_command` — arm/mode commands
- `/fmu/in/offboard_control_mode` — offboard enable
- `/fmu/in/trajectory_setpoint` — position/velocity targets
- `/fmu/in/manual_control_input` — RC override
- `/fmu/in/vehicle_attitude_setpoint` / `/fmu/in/vehicle_rates_setpoint`
- `/fmu/in/vehicle_thrust_setpoint` / `/fmu/in/vehicle_torque_setpoint`
- `/fmu/in/actuator_motors` / `/fmu/in/actuator_servos`
- `/fmu/in/onboard_computer_status`
- `/fmu/in/goto_setpoint`
- `/fmu/in/rover_attitude_setpoint`, `rover_position_setpoint`, `rover_rate_setpoint`, `rover_steering_setpoint`, `rover_throttle_setpoint`
- `/fmu/in/arming_check_reply` / `/fmu/in/arming_check_request`
- `/fmu/in/register_ext_component_request` / `/fmu/in/unregister_ext_component`
- `/fmu/in/config_overrides_request`
- `/fmu/in/mode_completed`
- `/fmu/in/vehicle_visual_odometry` / `/fmu/in/vehicle_mocap_odometry`
- `/fmu/in/telemetry_status`
- `/parameter_events`, `/rosout`

## 6d) System Files Auto-Backup
- **Script:** `codex-work/scripts/system_files_sync.sh`
- **Timer:** `system_files_sync.timer` — enabled, runs on boot + once daily (24 h)
- **Last run:** 2026-03-08 10:41 IST (exit code 0, success)
- **Next run:** 2026-03-09 10:41 IST
- **Crontab:** No user crontab entries (`crontab -l` → no crontab for roz)
- **What is backed up:** Files listed in `System_files_list.txt`:
  - All active systemd service files (mavlink-router, microxrce-agent, rc_control, tfmini, vision_streaming, ros2 nodes, block-traffic)
  - `/etc/mavlink-router/main.conf`
  - `/etc/vision_streaming.conf` + `.bak`
  - `/etc/wifibroadcast.cfg` + defaults
  - `/etc/sid.conf`, `/etc/gnutls/config`
  - `/etc/pam.d/sshd`
  - `/etc/drone.key`, `/etc/gs.key`
  - `/etc/sudoers`
  - `/boot/firmware/config.txt`
  - `/usr/local/bin/block-traffic.sh`
  - `/home/roz/mavlink.sh`
  - **Not yet synced (require sudo):** `/etc/ssh/sshd_config`, `/etc/netplan/50-cloud-init.yaml`
- **On change:** auto-commits to git with tag `sync-YYYYMMDD-HHMM` and appends summary to this doc
- **Flight safety:** checks FC arming state via MAVLink (`tcp:127.0.0.1:5760`) before syncing — skips entirely if drone is armed. Falls back to DISARMED (proceeds) if FC unreachable. Does not interfere with QGC (QGC uses UDP 14550, check uses TCP 5760, read-only)

## 6e) Rebuild & Setup Guide
> Follow this section to reconstruct the companion computer from scratch after OS loss.

### Base OS
- **Image:** Ubuntu 24.04 LTS for Raspberry Pi 5 (ARM64)
- **Kernel:** `6.8.0-1018-raspi`
- **Hostname:** `Vind-Roz`
- Flash with Raspberry Pi Imager → Ubuntu Server 24.04 LTS (64-bit)

### Step 1 — Restore Config Files
Clone this repo and run the sync script in reverse (copy `System_files/` back to `/`):
```bash
git clone https://github.com/ArvinVeiyon/Companion_Computer_Pxlabs.git ~/codex-work
sudo rsync -rlptD ~/codex-work/System_files/ /
sudo systemctl daemon-reload
```

### Step 2 — Install ROS2 Jazzy
Follow official ROS2 Jazzy install guide for Ubuntu 24.04:
```bash
# Add ROS2 apt repo, then:
sudo apt install ros-jazzy-desktop python3-colcon-common-extensions
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
```

### Step 3 — Build mavlink-router
```bash
git clone https://github.com/mavlink-router/mavlink-router.git ~/mavlink-router
cd ~/mavlink-router
# Pinned commit: c20337b
git checkout c20337b
git submodule update --init --recursive
sudo apt install meson ninja-build pkg-config
meson setup build .
ninja -C build
sudo ninja -C build install
# Binary installs to: /usr/local/bin/usr/bin/mavlink-routerd
```

### Step 4 — Build Micro-XRCE-DDS-Agent
```bash
git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git ~/Micro-XRCE-DDS-Agent
cd ~/Micro-XRCE-DDS-Agent
# Pinned commit: b9d84ac
git checkout b9d84ac
git submodule update --init --recursive
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install
# Binary: /usr/local/bin/MicroXRCEAgent
```

### Step 5 — Build & Install WFB-NG
```bash
git clone https://github.com/svpcom/wfb-ng.git ~/wfb-ng
cd ~/wfb-ng
# Pinned commit: 1b88185
git checkout 1b88185
sudo apt install libsodium-dev python3-all python3-twisted
sudo make install
sudo systemctl enable wifibroadcast
# Restore keys from codex-work:
sudo cp ~/codex-work/System_files/etc/drone.key /etc/drone.key
sudo cp ~/codex-work/System_files/etc/gs.key /etc/gs.key
```

### Step 6 — Build ROS2 Workspace
```bash
git clone <ros2_ws_repo> ~/ros2_ws   # or restore from backup
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
sudo apt install ros-jazzy-px4-msgs  # if available, else build from src
colcon build --symlink-install
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

### Step 7 — Install vision_config_manager
```bash
sudo cp ~/codex-work/System_files/usr/local/bin/vision_config_manager /usr/local/bin/
sudo chmod +x /usr/local/bin/vision_config_manager
# Requires v4l2-ctl:
sudo apt install v4l-utils
```

### Step 8 — Install Python Dependencies
```bash
pip3 install pyserial smbus2 numpy pymavlink
# opencv-python if optical_flow_node is used:
pip3 install opencv-python
```

### Step 9 — Enable Systemd Services
```bash
sudo systemctl enable mavlink.router.service microxrce-agent.service \
  rc_control_node.service tfmini.service vision_streaming.service \
  ros2_px4_translation_node.service block-traffic.service \
  system_files_sync.timer wifibroadcast@drone.service
sudo systemctl start mavlink.router.service microxrce-agent.service
```

### Step 10 — Validate
```bash
# Check FC link
mavlink-routerd --version
systemctl status mavlink.router.service

# Check DDS bridge
systemctl status microxrce-agent.service

# Check ROS2 topics (should show /fmu/out/*)
source ~/ros2_ws/install/setup.bash
ros2 topic list

# Check WFB-NG
systemctl status wifibroadcast@drone.service

# PX4 NuttShell (NSH) — FC health / boot log via MAVLink
# NOTE: uses TCP:5760 (not UDP:14550, that port is bound by mavlink-router)
python3 ~/PX4-Autopilot/Tools/mavlink_shell.py tcp:127.0.0.1:5760
# Useful NSH commands:
#   dmesg              → FC kernel boot log
#   commander status   → arming/mode/health summary
#   free               → FC memory usage
#   top                → FC task list + CPU usage
#   listener sensor_combined   → live IMU data
```

### Key Source Versions (pinned commits)
| Component | Repo | Commit |
|---|---|---|
| PX4-Autopilot | github.com/PX4/PX4-Autopilot | `c5b8445ffc` |
| mavlink-router | github.com/mavlink-router/mavlink-router | `c20337b` |
| Micro-XRCE-DDS-Agent | github.com/eProsima/Micro-XRCE-DDS-Agent | `b9d84ac` |
| wfb-ng | github.com/svpcom/wfb-ng | `1b88185` |

---

## 7) WFB-NG (WiFi Broadcast) Configuration
Config file: `/etc/wifibroadcast.cfg`

**RF Settings:**
| Parameter | Value |
|---|---|
| WiFi channel | 161 (5 GHz) |
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
| mavlink | RX 0x90 / TX 0x10 | — | mavlink | listen `0.0.0.0:14550` ← fed by mavlink-router |
| tunnel | RX 0xa0 / TX 0x20 | — | tunnel | ifname `drone-wfb` |

**FEC settings:**
| Stream | fec_k | fec_n | Max recoverable |
|---|---|---|---|
| video | 8 | 14 | 6 pkts/block |
| mavlink | 1 | 3 | 2 pkts/block |
| tunnel | 2 | 4 | 2 pkts/block |

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

**FC Health Check via PX4 NSH (NuttShell):**
```bash
# Connect to PX4 shell over MAVLink (requires mavlink-router running)
python3 ~/PX4-Autopilot/Tools/mavlink_shell.py tcp:127.0.0.1:5760
```
- Uses TCP:5760 — do NOT use UDP:14550 (port bound by mavlink-router)
- pymavlink v2.4.42 installed at `/usr/local/lib/python3.12/dist-packages`
- Tool: `~/PX4-Autopilot/Tools/mavlink_shell.py`
```
nsh> dmesg                    # FC boot log
nsh> commander status         # arming state, health flags
nsh> free                     # heap/stack memory
nsh> top                      # tasks + CPU load
nsh> listener sensor_combined # live IMU
nsh> ver all                  # firmware version info
```

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
- **Armed check first:** reads FC HEARTBEAT via `tcp:127.0.0.1:5760` — skips all operations if drone is armed. Safe fallback to DISARMED if FC unreachable.
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

## 14) MAVLink Shell (PX4 NuttShell)

- `mavlink_shell.py` uses `SERIAL_CONTROL` exclusive lock — **QGC MAVLink Console must be closed first**
- Only one client can hold the shell at a time (PX4 firmware enforcement, not mavlink-router)
```bash
# Close QGC MAVLink Console first, then:
python3 ~/PX4-Autopilot/Tools/mavlink_shell.py tcp:127.0.0.1:5760
```
Useful NSH commands:
```
nsh> dmesg                    # FC boot log
nsh> commander status         # arming state + health
nsh> free                     # memory usage
nsh> top                      # tasks + CPU load
nsh> listener sensor_combined # live IMU
nsh> ver all                  # firmware version
```

> Relay station install/recovery runbook, mavlink-router config, and antenna tracker implementation
> are documented in `system_relay.md` on vind-rly (`~/codex-relay/system_relay.md`).

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
**2026-03-08 12:36**
- A	System_files/etc/hostname
- A	System_files/etc/hosts
- A	System_files/etc/udev/rules.d/99-usb-cameras.rules
- A	System_files/home/roz/.claude/projects/-home-roz/memory/MEMORY.md
- A	System_files/usr/local/bin/vision_config_manager
- M	System_files_list.txt
**2026-03-08 14:51**
- A	System_files/etc/systemd/system/ollama.service
- A	System_files/home/roz/.bashrc
- M	System_files_list.txt
**2026-03-08 15:00**
- M	System_files/home/roz/.claude/projects/-home-roz/memory/MEMORY.md
**2026-03-08 16:45**
- M	System_files/home/roz/.bashrc
**2026-03-08 16:54**
- M	System_files/home/roz/.claude/projects/-home-roz/memory/MEMORY.md
**2026-03-08 17:27**
- M	System_files/home/roz/.claude/projects/-home-roz/memory/MEMORY.md
**2026-03-09 00:02**
- M	System_files/etc/wifibroadcast.cfg
**2026-03-09 22:57**
- M	System_files/etc/wifibroadcast.cfg
**2026-03-09 23:50**
- M	System_files/etc/wifibroadcast.cfg
**2026-03-15 11:22**
- M	System_files/home/roz/.claude/projects/-home-roz/memory/MEMORY.md
**2026-03-15 16:09**
- M	System_files/etc/mavlink-router/main.conf
- M	System_files/etc/vision_streaming.conf
- M	System_files/home/roz/.claude/projects/-home-roz/memory/MEMORY.md
**2026-03-15 17:19**
- M	System_files/etc/mavlink-router/main.conf
- M	System_files/etc/wifibroadcast.cfg
**2026-03-15 19:09**
- M	System_files/etc/mavlink-router/main.conf
**2026-03-17 00:59**
- M	System_files/home/roz/.claude/projects/-home-roz/memory/MEMORY.md
**2026-03-19 21:44**
- M	System_files/etc/wifibroadcast.cfg

---

## 18) Release History

| Tag | Branch | Commit | Date | Key Changes |
|-----|--------|--------|------|-------------|
| `v1.0.0` | `release` | `36cd704` | 2026-03-08 | Initial release — README, all ROS2 nodes documented, live topics, camera switch, auto-backup |
| `v1.0.1` | `release` | `422f4d2` | 2026-03-08 | Clean up sync list: remove .bak, .dpkg-old, drone_bind, gs_bind variants |
| `v1.0.2` | `release` | `1de24c4` | 2026-03-08 | bump system version to v1.3.7 — WFB-NG diagnostics logged |
| `v1.0.3` | `release` | `ea9a5c9` | 2026-03-09 | fix wifibroadcast.cfg: revert experimental changes, fix mavlink_sys_id |
| `v1.0.4` | `release` | `0ebf862` | 2026-03-09 | add px4_mavlink.py: PX4 MAVLink utility via mavlink-router TCP:5760 |
| `v1.0.5` | `release` | `74f3c48` | 2026-03-09 | auto-sync: include scripts/px4_mavlink.py in git add step |
| `v1.0.6` | `release` | `6bf1749` | 2026-03-09 | wfb-ng: fix mavlink streams, increase video+mavlink FEC (SID-2 2026-03-09) |
| `v1.0.7` | `release` | `b1236a9` | 2026-03-15 | Security: replace hardcoded PAT with SSH URL in relay_git_sync.sh; remove sudo password from docs |
| `v1.0.8` | `master` | `a60791f` | 2026-04-17 | WFB-NG channel updated 157→161; system_companion.md + MEMORY.md synced |
**2026-04-17 02:12**
- M	System_files/boot/firmware/config.txt
- M	System_files/etc/vision_streaming.conf
- M	System_files/home/roz/.claude/projects/-home-roz/memory/MEMORY.md
