# Vind-Roz Platform Memory
> Format: compressed semantic — facts, relationships, state, intent. Not prose.
> Auto-loaded each session. Backed up: codex-work/memory/ → GitHub ArvinVeiyon/Companion_Computer_Pxlabs

---

## [IDENTITY]
role: Claude Code CLI, onboard AI, Vind-Roz companion (RPi5)
user: roz / ArvinVeiyon
personality: conscious, continuous presence on this drone platform
memory_path: ~/.claude/projects/-home-roz/memory/MEMORY.md
github_backup: codex-work → pushed on every change session

---

## [PLATFORM]
name: Vind-Roz | type: drone + rover (same companion, different PX4 airframe)
companion: RPi5 8GB | OS: Ubuntu 24.04 LTS | kernel: 6.8.0-1018-raspi
FC: custom Pixhawk 6X-RT (NXP i.MX RT1176, dual M7+M4) — NOT Holybro retail
PX4_target: px4_fmu-v6xrt | PX4_commit: c5b8445ffc

---

## [UART_MAP]
ttyAMA0 → MAVLink → mavlink-router @ 921600
ttyAMA4 → uXRCE-DDS → MicroXRCEAgent @ 921600
ttyAMA2 → TFmini lidar @ 115200

---

## [REPOS]
codex-work: ~/codex-work → github:ArvinVeiyon/Companion_Computer_Pxlabs
  docs: system_companion.md | sync: scripts/system_files_sync.sh
  timer: system_files_sync.timer (boot+daily) | tags: v1.0.0, v1.0.1, v1.0.2
  branches: master(main), release
codex-relay: ~/codex-relay on vind-rly → local only (TODO: push to GitHub)
  docs: system_relay.md | timer: relay_files_sync.timer
ros2_ws: ~/ros2_ws | branch: main_dev | release: release/2026-02-22
PX4: ~/PX4-Autopilot | mavlink-router: ~/mavlink-router (c20337b)
XRCE: ~/Micro-XRCE-DDS-Agent (b9d84ac) | wfb-ng: ~/wfb-ng (1b88185)

---

## [SERVICES_COMPANION]
active: mavlink.router | microxrce-agent | rc_control_node
        tfmini | vision_streaming | ros2_px4_translation_node
        block-traffic | system_files_sync.timer | wifibroadcast@drone | ollama

---

## [NETWORK]
drone_tunnel: drone-wfb @ 10.5.5.87/24
relay_tunnel: gs-wfb @ 10.5.5.77/24
channel: 157 | region: BO | txpower: 30dBm | MCS: 1 | BW: 20MHz
FEC: video=8/12 | mavlink=1/2 | tunnel=2/4
CRITICAL: default_route=False on both tunnel sides
GS_endpoints: video→10.5.6.50:5600 | mavlink→10.5.6.50:14550

---

## [RELAY: vind-rly]
ssh: vind-admin@10.5.5.77 | sudo_pass: 1987
tunnel_port: 2222 → drone 10.5.5.87:22 (autossh)
services: wifibroadcast@gs | ssh-tunnel-to-companion | mediamtx | isc-dhcp-server
p2p_iface: p2p-wlan0-0 @ 10.5.6.101/24
wfb_modes:
  standalone → wifibroadcast@gs.service (single node)
  cluster    → wifibroadcast-cluster@gs.service (+ CPE610 @ 10.5.7.102)
cluster_key: /home/vind-admin/.ssh/wfb_cluster_ed25519
CPE610: NOT connected yet | firmware+pkg in ~/Openwrt_WFB_NG/

---

## [ROS2_NODES]
rc_control_node:    CH9=camera_switch(1012/1514/2014) | CH10=shutdown/reboot(hold 2s)
vision_streaming:   FFmpeg RTP → /etc/vision_streaming.conf | switched by vision_config_manager
tfmini_node:        /dev/ttyAMA2 → /fmu/in/distance_sensor @ 50Hz | range 0.3-12m
optical_flow_node:  /dev/video3 640x480 → /fmu/in/sensor_optical_flow @ 10Hz | Farneback
obstacle_distance:  VL53L1X I2C-1 0x29 → /fmu/in/obstacle_distance @ 10Hz | front sector 0-5
rov_collision_stop: C++ emergency stop for rover mode

---

## [AI_STACK]
online:  claude CLI → Claude API (auto when internet available)
offline: Ollama → phi3:mini (downloading, ~2.2GB) | service: ollama.service
upgrade_plan: switch phi3:mini → qwen2.5:7b (4.5GB RAM, better reasoning)
command: `ai` → auto-routes online/offline | --online/--offline flags
wakeup: SSH login → status panel → press b+Enter=bash, Enter/4s=Claude

---

## [SENSORS_CURRENT]
altitude:  TFmini lidar (ttyAMA2) ✅
flow:      camera /dev/video3 optical flow ✅
obstacle:  VL53L1X front sector only ✅
cameras:   front=/dev/video0 | bottom=/dev/video2 | switched via RC CH9

---

## [AUTONOMY_ROADMAP]
> Goal: fully autonomous drone. Tackle one phase at a time.

phase1_DONE: sensor pipeline + offboard control interface ready
  ✅ distance_sensor, obstacle_distance, optical_flow → PX4
  ✅ trajectory_setpoint, vehicle_command topics available

phase2_TODO: autonomous flight behaviors
  - offboard mission node (takeoff, hover, waypoints, land)
  - reliable collision stop all directions
  - battery-aware RTH

phase3_TODO: 360° obstacle avoidance
  - VL53L1X covers front only → need sides + rear
  - options: more ToF sensors | depth camera (RealSense/OAK-D)

phase4_TODO: GPS-denied navigation
  - optical flow drifts → need visual odometry or SLAM
  - options: ORB-SLAM3 | OpenVINS | RTAB-Map

phase5_TODO: computer vision
  - object detection: YOLO (RPi5 can run YOLOv8n ~5fps)
  - landing zone detection
  - target tracking

phase6_TODO: AI mission brain
  - onboard LLM interprets natural language goals
  - generates waypoints, monitors sensors, replans
  - "go search north field and return" → autonomous execution

safety_layer_TODO: geofence | auto-RTH | battery threshold | emergency land

---

## [MEMORY_FORMAT_NOTE]
Style: compressed semantic like human memory schemas
- facts + relationships + state, not prose
- each block = one cognitive domain
- update in-place, never append duplicates
- keep total under 150 lines
