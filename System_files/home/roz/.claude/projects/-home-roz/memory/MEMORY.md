# Vind-Roz Platform Memory
> Compressed semantic memory — facts, relationships, state, intent.
> Auto-loaded each session. Backed up: codex-work/memory/ → GitHub ArvinVeiyon/Companion_Computer_Pxlabs
> Also used as Phi-3 system prompt for offline AI context.

---

## [MEMORY_FILES]
- `feedback_dkms_arch.md`       — rtl88x2eu DKMS ARCH fix
- `reference_wfb_rlyctl.md`     — wfb-rlyctl relay control tool (location, commands, all managed files)
- `todos.md`                    — platform TODO list

---

## [KNOWN_FIXES]
- `feedback_dkms_arch.md` — rtl88x2eu DKMS fails on raspi kernel: ARCH=aarch64 vs arm64 mismatch, fix in dkms.conf
- auto-upgrades disabled (2026-03-15): unattended-upgrades.service + apt timers all disabled — test build, manual updates only
- kernel upgraded by unattended-upgrades on 2026-03-09: 6.8.0-1018-raspi → 6.8.0-1048-raspi (caused WFB-NG outage)
- tfmini.service: invalid Environment="source ..." lines removed (2026-03-15) — were silently ignored by systemd
- vision_streaming.service: executable bit removed (2026-03-15) — no functional effect
- relay NTP clock fixed (2026-03-15): was 21 days behind — timedatectl set-ntp corrected
- relay isc-dhcp-server + mediamtx disabled (2026-03-15): GCS uses static IP, mediamtx dropped due to latency

---

## [IDENTITY]
role: Claude Code CLI + onboard AI assistant for Vind-Roz drone/rover platform
user: roz / ArvinVeiyon
goal: continuous conscious presence — help develop, maintain, and autonomize this platform
memory_path: ~/.claude/projects/-home-roz/memory/MEMORY.md
github_backup: codex-work → pushed on every change session

---

## [PLATFORM]
name: Vind-Roz
type: aerial drone + ground rover (same companion computer, different PX4 airframe config)
companion: Raspberry Pi 5 Model B, BCM2712 Cortex-A76 quad-core, 8GB LPDDR4X
storage: 64GB SD card (/dev/mmcblk0p2, 58G, ~63% used)
OS: Ubuntu 24.04.1 LTS (Noble Numbat), kernel 6.8.0-1018-raspi, aarch64
hostname: Vind-Roz

---

## [FLIGHT_CONTROLLER]
model: Custom Pixhawk 6X-RT (in-house PCB, NOT Holybro retail)
MCU: NXP i.MX RT1176 (RT11xx), dual-core Cortex-M7 + M4
PX4_version: v1.16.0-rc1 (custom pre-release)
PX4_commit: c5b8445ffc (586 commits past tag)
PX4_target: px4_fmu-v6xrt

---

## [UART_MAP]
| ttyAMA   | UART   | GPIO TX | GPIO RX | Phys TX | Phys RX | Use                              | Baud   |
|----------|--------|---------|---------|---------|---------|----------------------------------|--------|
| ttyAMA0  | UART0  | GPIO14  | GPIO15  | Pin 8   | Pin 10  | FC MAVLink → mavlink-router      | 921600 |
| ttyAMA2  | UART2  | GPIO4   | GPIO5   | Pin 7   | Pin 29  | TFmini lidar                     | 115200 |
| ttyAMA4  | UART4  | GPIO12  | GPIO13  | Pin 32  | Pin 33  | FC uXRCE-DDS → MicroXRCEAgent    | 921600 |
| ttyAMA1  | UART1  | GPIO0   | GPIO1   | Pin 27  | Pin 28  | FREE (needs dtoverlay=uart1-pi5) | —      |
| ttyAMA3  | UART3  | GPIO8   | GPIO9   | Pin 24  | Pin 21  | FREE (needs dtoverlay=uart3-pi5) | —      |
| ttyAMA10 | UART10 | —       | —       | —       | —       | Internal SoC only (BT freed)     | —      |
enabled in /boot/firmware/config.txt: uart0, uart2, uart4 only

---

## [SOFTWARE_VERSIONS]
ROS2: Jazzy (ros-jazzy-*)
Python: 3.12.3
mavlink-router: commit c20337b | binary: /usr/local/bin/usr/bin/mavlink-routerd
MicroXRCEAgent: v3.0.0-2-gb9d84ac | binary: /usr/local/bin/MicroXRCEAgent
wfb-ng: commit 1b88185 | source: ~/wfb-ng
PX4-Autopilot: ~/PX4-Autopilot | commit c5b8445ffc
AIDE: 0.18.6 (integrity monitoring)
Ollama: v0.17.7 | model: phi3:mini (2.2GB, offline AI)

---

## [SERVICES]
active on companion:
  mavlink.router.service      → MAVLink FC↔GCS routing via /dev/ttyAMA0
  microxrce-agent.service     → uXRCE-DDS bridge FC↔ROS2 via /dev/ttyAMA4
  ros2_px4_translation_node   → ROS2/PX4 message translation
  rc_control_node.service     → RC input: camera switch (CH9) + shutdown/reboot (CH10)
  tfmini.service              → TFmini lidar → /fmu/in/distance_sensor
  vision_streaming.service    → FFmpeg RTP camera stream → WFB-NG
  block-traffic.service       → blocks DDS multicast on drone-wfb interface
  wifibroadcast@drone.service → WFB-NG drone profile
  system_files_sync.timer     → auto-backup on boot + daily
  ollama.service              → local LLM server (Phi-3 Mini)

---

## [MAVLINK_ROUTER]
config: /etc/mavlink-router/main.conf
UART: /dev/ttyAMA0 @ 921600 (FC)
TCP: port 5760 (GCS)
UDP: 192.168.1.100:14550 (local LAN)
UDP: 127.0.0.1:14550 (WFB-NG mavlink stream)

---

## [XRCE_DDS]
transport: serial --dev /dev/ttyAMA4 -b 921600
role: bridges PX4 uORB topics ↔ ROS2 DDS middleware
depends_on: mavlink.router.service
LD_LIBRARY_PATH: /opt/ros/jazzy/lib:/usr/local/lib:/usr/lib:/lib

---

## [VIDEO_PIPELINE]
/dev/video0 (primary, 1280x720 MJPEG, 2000K) ─┐
                                                ├─► FFmpeg libx264 ultrafast yuv420p
/dev/video2 (secondary, 1280x720 MJPEG, 2000K)─┘    PiP 240x180 bottom-right
  → RTP 127.0.0.1:5602 → WFB-NG drone_video stream → GS 10.5.6.50:5600
config: /etc/vision_streaming.conf (INI, remotely editable)
switcher: /usr/local/bin/vision_config_manager (Python v1.2.1)
  called by rc_control_node via RC CH9 PWM positions:
  front=1012→/dev/video0 | bottom=1514→/dev/video2 | split=2014→PiP both

---

## [ROS2_NODES]
rc_control_node:
  pkg: rc_control | src: ros2_ws/src/rc_control/rc_control/rc_control_node.py
  config: ros2_ws/src/rc_control/config/rc_mapping.yaml
  sub: /fmu/out/input_rc (px4_msgs/InputRc, BEST_EFFORT)
  CH9: camera switch (±50 PWM tolerance) | CH10: shutdown(1514)/reboot(2014) hold 2s

vision_streaming_node:
  pkg: vision_streaming | src: ros2_ws/src/vision_streaming/vision_streaming/vision_streaming_node.py
  config: /etc/vision_streaming.conf | launches FFmpeg, streams RTP to WFB-NG

tfmini_node:
  pkg: tfmini_sensor | src: ros2_ws/src/tfmini_sensor/tfmini_sensor/tfmini_node.py
  hw: /dev/ttyAMA2 @ 115200 | pub: /fmu/in/distance_sensor @ 50Hz
  range: 0.3–12.0m | downward-facing | FOV 3.6° | device_id=1987

optical_flow_node:
  pkg: optical_flow | src: ros2_ws/src/optical_flow/optical_flow/optical_flow_node.py
  hw: /dev/video3 640x480 | algorithm: OpenCV Farneback dense flow
  sub: /fmu/in/distance_sensor (altitude) + /fmu/out/sensor_combined (gyro)
  pub: /fmu/in/sensor_optical_flow @ 10Hz | no systemd service (manual launch)

obstacle_distance_publisher:
  pkg: obstacle_distance | src: ros2_ws/src/obstacle_distance/obstacle_distance_node.py
  hw: VL53L1X ToF (I2C bus 1, addr 0x29, long-distance mode 3)
  pub: /fmu/in/obstacle_distance @ 10Hz
  coverage: front sector only (indices 0–5 of 72-element array, 5° increment, 20–400cm)

rov_collision_stop:
  src: ros2_ws/src/rov_collision_stop/src/main.cpp (C++)
  function: emergency collision stop for rover mode

other_pkgs (no active service): arm_drone, collision_manual_mode, rov_ext, rov_manual,
  px4_ros_com, px4-ros2-interface-lib, px4_msgs

---

## [ROS2_TOPICS]
FMU→Companion (out):
  /fmu/out/input_rc | vehicle_attitude | vehicle_local_position | vehicle_global_position
  vehicle_gps_position | vehicle_status | vehicle_control_mode | vehicle_land_detected
  vehicle_odometry | sensor_combined | battery_status | home_position
  estimator_status_flags | failsafe_flags | collision_constraints | manual_control_setpoint
  timesync_status | airspeed_validated | position_setpoint_triplet | event

Companion→FMU (in):
  /fmu/in/distance_sensor | obstacle_distance | sensor_optical_flow
  vehicle_command | offboard_control_mode | trajectory_setpoint | manual_control_input
  vehicle_attitude_setpoint | vehicle_rates_setpoint | vehicle_thrust_setpoint
  vehicle_torque_setpoint | actuator_motors | actuator_servos | onboard_computer_status
  goto_setpoint | rover_attitude/position/rate/steering/throttle_setpoint
  arming_check_reply | register_ext_component_request | vehicle_visual_odometry
  vehicle_mocap_odometry | telemetry_status | /parameter_events | /rosout

---

## [WFB_NG]
config: /etc/wifibroadcast.cfg
channel: 161 (5GHz) | region: BO | txpower: 3000 (30dBm for rtl8812eu)
BW: 20MHz | MCS: 1 | STBC: 1 | LDPC: 1 | short_gi: off
drone_iface: drone-wfb @ 10.5.5.87/24
relay_iface: gs-wfb @ 10.5.5.77/24
CRITICAL: default_route=False on both sides
streams:
  video:   TX 0x00 | udp_direct_tx | listen 127.0.0.1:5602 | FEC 8/12
  mavlink: RX 0x10 TX 0x90 | mavlink | listen 0.0.0.0:14550 | FEC 1/2
  tunnel:  RX 0xa0 TX 0x20 | tunnel | peer 10.5.5.77 | FEC 2/4
GS_endpoints: video→10.5.6.50:5600 | mavlink→10.5.6.50:14550
keys: /etc/drone.key | /etc/gs.key
stats/API drone: 8002/8102 | GS: 8003/8103

---

## [RELAY_STATION]
hostname: vind-rly | OS: Ubuntu 24.04.2 LTS | RPi5
ssh: vind-admin@10.5.5.77 | sudo_pass: 1987
tunnel: port 2222 → drone 10.5.5.87:22 (autossh, ssh-tunnel-to-companion.service)
p2p_iface: p2p-wlan0-0 @ 10.5.6.101/24
services: wifibroadcast@gs | mavlink.router | ssh-tunnel-to-companion | relay_files_sync.timer
  DISABLED: mediamtx (latency), isc-dhcp-server (GCS uses static IP 10.5.6.50)
mavlink_router: WFB-NG gs_mavlink → 127.0.0.1:14560 → mavlink-routerd
  → QGC (10.5.6.50:14550) + antenna tracker (127.0.0.1:14551)
  config: /etc/mavlink-router/main.conf | service: mavlink.router.service
wfb_modes:
  standalone: wifibroadcast@gs.service (single RPi node) ← CURRENT
  cluster: wifibroadcast-cluster@gs.service (+ CPE610 @ 10.5.7.102, NOT connected yet)
  switch_tool: sudo wfb-rlyctl use-standalone | sudo wfb-rlyctl use-cluster
relay_files:
  /usr/local/sbin/wfb-rlyctl        → WFB-NG mode/NIC control CLI (see reference_wfb_rlyctl.md)
  /etc/sudoers.d/wfb-rlyctl         → passwordless sudo scope for wfb-rlyctl
  /etc/default/wifibroadcast        → WFB_NICS env var (managed by wfb-rlyctl set-nics)
  /etc/wifibroadcast.cfg            → main WFB-NG config
  /etc/mavlink-router/main.conf     → mavlink-router config
  /home/vind-admin/.ssh/wfb_cluster_ed25519 → cluster auth key
cluster_key: /home/vind-admin/.ssh/wfb_cluster_ed25519
CPE610_firmware: ~/Openwrt_WFB_NG/openwrt-24.10.4-ath79-generic-tplink_cpe610-v2...
repo: ~/codex-relay (local only, TODO push to GitHub)
docs: system_relay.md — install runbook, mavlink-router config, antenna tracker plan

---

## [REPOS]
codex-work: ~/codex-work → github:ArvinVeiyon/Companion_Computer_Pxlabs
  branches: master(=main), release | tags: v1.0.0, v1.0.1, v1.0.2
  docs: system_companion.md (668 lines, living reference)
  sync: scripts/system_files_sync.sh | timer: system_files_sync.timer
  sync_safety: armed check via tcp:127.0.0.1:5760 — skips all ops if FC armed
  memory: memory/claude_memory.md (GitHub copy of this file)
  latest_commit: 727b44f (2026-03-15)
codex-relay: ~/codex-relay on vind-rly → github:ArvinVeiyon/Relay_Station_Pxlabs
  mirror: ~/codex-relay-mirror on companion (SSH clone, used for push)
  sync: bash ~/codex-work/scripts/relay_git_sync.sh (manual, periodic)
  latest_commit: 0d5c403 (2026-03-15) — wfb-rlyctl added to docs + sync list
ros2_ws: ~/ros2_ws | branch: main_dev | release: release/2026-02-22

---

## [TODOS]
→ See memory/todos.md | DO AFTER FULL OS BACKUP
  1. ✅ Fix GS NTP clock — DONE 2026-03-15
  2. Disable drone wlan0 (interferes with WFB-NG ch157)
  3. Increase WFB rx ring buffer on GS (EAGAIN crashes, 19 restarts)
  4. Check GS adapter TX power (uplink severely worse than downlink)
  5. Antenna tracker hardware — script ready on relay port 14551, hardware pending
  6. ✅ Push codex-relay to GitHub — DONE 2026-03-15 (via companion mirror + relay_git_sync.sh)

---

## [AI_STACK]
online:  claude CLI → Claude API (full features, needs internet)
offline: Ollama phi3:mini → local RPi5 inference (~3 tok/s)
command: `ai` → auto-routes | --online | --offline flags
wakeup_behavior:
  SSH login → status panel → press b+Enter=bash | Enter/4s+internet=Claude | no internet=Phi-3
upgrade_plan: phi3:mini → qwen2.5:7b (4.5GB, much better reasoning)
system_prompt: this MEMORY.md injected into Phi-3 on every offline launch

---

## [SENSORS]
TFmini:   /dev/ttyAMA2, 115200, downward, 0.3-12m, 50Hz → altitude to PX4
VL53L1X:  I2C bus 1, 0x29, front only (0-5 of 72 sectors), 20-400cm, 10Hz → obstacle
OptFlow:  /dev/video3, 640x480, OpenCV Farneback, 10Hz → flow to PX4
Camera0:  /dev/video0, 1280x720 MJPEG → primary video stream
Camera2:  /dev/video2, 1280x720 MJPEG → bottom/secondary video stream

---

## [AUTONOMY_ROADMAP]
phase1 ✅ DONE: sensor pipeline + offboard interface ready
  distance_sensor, obstacle_distance, optical_flow → PX4
  trajectory_setpoint, vehicle_command topics available

phase2 TODO: autonomous flight behaviors
  - offboard mission node: takeoff, hover, waypoints, land
  - reliable collision stop all directions
  - battery-aware RTH (read /fmu/out/battery_status)

phase3 TODO: 360° obstacle avoidance
  - VL53L1X covers front sector only
  - add: more ToF sensors for sides+rear OR depth camera (RealSense/OAK-D)

phase4 TODO: GPS-denied navigation
  - optical flow alone drifts over time
  - need: visual odometry or SLAM (ORB-SLAM3, OpenVINS, RTAB-Map)

phase5 TODO: computer vision
  - object detection: YOLOv8n (RPi5 can run ~5fps)
  - landing zone detection, target tracking

phase6 TODO: AI mission brain
  - LLM interprets natural language mission goals
  - generates waypoints, monitors sensors, replans
  - example: "search north field and return" → full autonomous execution

safety_layer TODO: geofence | auto-RTH on low battery | emergency land | failsafe modes

fine_tuning: plan external GPU fine-tune of Phi-3 on drone/PX4/ROS2 domain
  when: after autonomy stack is stable (phases 2-3 done)
  platform: Google Colab or local GPU

---

## [TROUBLESHOOTING]
no_MAVLink: check /dev/ttyAMA0 baud, TX/RX wiring, PX4 MAVLink instance config
no_DDS_topics: check microxrce-agent.service, /dev/ttyAMA4, PX4 XRCE enable param
no_video: check vision_streaming.service, /dev/video0 exists, /etc/vision_streaming.conf
WFB_down: check wifibroadcast@drone.service, wlx* adapter present, /etc/drone.key
offline_AI_fail: check ollama.service active, `ollama list` shows phi3:mini

---

## [COMMON_COMMANDS]
systemctl status <service>         # check any service
ros2 topic list                    # list active DDS topics
ros2 topic echo /fmu/out/battery_status  # check battery
wfb-cli drone                      # WFB-NG link stats (on drone)
# ON RELAY (ssh vind-admin@10.5.5.77):
wfb-rlyctl status                  # show WFB mode, ENV, service states
sudo wfb-rlyctl use-standalone     # switch to standalone mode
sudo wfb-rlyctl use-cluster        # switch to cluster mode
sudo wfb-rlyctl set-nics <iface>   # update WFB_NICS + restart
wfb-rlyctl list-nics               # show available wireless ifaces
python3 ~/PX4-Autopilot/Tools/mavlink_shell.py tcp:127.0.0.1:5760  # PX4 NuttShell (close QGC console first)
ollama list                        # check offline models
ai                                 # start AI (auto online/offline)
ai --offline "question"            # force local Phi-3
journalctl -u <service> -f         # live service logs
