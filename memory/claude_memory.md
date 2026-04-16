# Vind-Roz Platform Memory
> Compressed semantic memory. Auto-loaded each session. Also Phi-3 system prompt (offline AI).
> Backup: codex-work/memory/ → GitHub ArvinVeiyon/Companion_Computer_Pxlabs

---

## [MEMORY_FILES]
- `feedback_dkms_arch.md`  — rtl88x2eu DKMS ARCH fix
- `reference_wfb_rlyctl.md` — wfb-rlyctl relay control tool (all managed files)
- `todos.md`               — platform TODO list (WFB fixes, post OS backup)
- `ros2_nodes.md`          — ROS2 node details (pkg paths, pub/sub, params)
- `ros2_topics.md`         — full FMU↔companion DDS topic lists

---

## [KNOWN_FIXES]
- rtl88x2eu DKMS: ARCH=aarch64 vs arm64 mismatch → fix in dkms.conf (see feedback_dkms_arch.md)
- auto-upgrades disabled 2026-03-15: unattended-upgrades + apt timers off (manual updates only)
- kernel upgraded 2026-03-09 by unattended-upgrades: 1018→1048-raspi (caused WFB-NG outage)
- tfmini.service 2026-03-15: removed invalid `Environment="source ..."` lines
- relay NTP fixed 2026-03-15: was 21d behind — timedatectl set-ntp true
- relay isc-dhcp-server + mediamtx disabled 2026-03-15: GCS static IP, mediamtx→latency
- ldlidar build fix 2026-04-17: added `#include <pthread.h>` to ldlidar_driver/src/logger/log_module.cpp (GCC 14+)
- ldlidar port fix 2026-04-17: hardcoded `/dev/ttyAMA3` in launch/ld19.launch.py line 35 — CLI port_name arg silently ignored by upstream

---

## [IDENTITY]
role: Claude Code CLI + onboard AI for Vind-Roz drone/rover platform
user: roz / ArvinVeiyon | memory: ~/.claude/projects/-home-roz/memory/MEMORY.md
goal: continuous presence — develop, maintain, autonomize this platform

---

## [PLATFORM]
Vind-Roz: aerial drone + ground rover | same RPi5 companion, different PX4 airframe config
HW: RPi5 BCM2712 Cortex-A76 quad-core 8GB LPDDR4X | 64GB SD (~63% used)
OS: Ubuntu 24.04.1 LTS aarch64 | kernel 6.8.0-1048-raspi | hostname: Vind-Roz

---

## [FLIGHT_CONTROLLER]
Custom Pixhawk 6X-RT (in-house PCB, NOT Holybro) | MCU: NXP i.MX RT1176 Cortex-M7+M4
PX4 v1.16.0-rc1 custom | commit c5b8445ffc | target: px4_fmu-v6xrt

---

## [UART_MAP]
| ttyAMA | Use                              | Baud   | GPIO TX/RX |
|--------|----------------------------------|--------|------------|
| AMA0   | FC MAVLink → mavlink-router      | 921600 | GPIO14/15  |
| AMA2   | TFmini lidar                     | 115200 | GPIO4/5    |
| AMA3   | STL-19 LiDAR (RX-only, no PWM)   | 230400 | GPIO8/9    |
| AMA4   | FC uXRCE-DDS → MicroXRCEAgent    | 921600 | GPIO12/13  |
| AMA1   | FREE (needs dtoverlay=uart1-pi5) | —      | GPIO0/1    |
| AMA10  | Internal SoC / JST debug (BT)    | 115200 | —          |
enabled in /boot/firmware/config.txt: uart0, uart2, uart3-pi5, uart4

---

## [SOFTWARE_VERSIONS]
ROS2: Jazzy | Python: 3.12.3 | Ollama: v0.17.7 / phi3:mini 2.2GB | AIDE: 0.18.6
mavlink-router: c20337b → /usr/local/bin/usr/bin/mavlink-routerd
MicroXRCEAgent: v3.0.0-2-gb9d84ac → /usr/local/bin/MicroXRCEAgent
wfb-ng: 1b88185 ~/wfb-ng | PX4-Autopilot: c5b8445ffc ~/PX4-Autopilot

---

## [SERVICES]
mavlink.router.service   → FC MAVLink↔GCS via ttyAMA0 | cfg: /etc/mavlink-router/main.conf
                          TCP:5760(GCS) UDP:192.168.1.100:14550 UDP:127.0.0.1:14550(WFB)
microxrce-agent.service  → uXRCE-DDS FC↔ROS2 via ttyAMA4 @ 921600 | dep: mavlink.router
rc_control_node.service  → RC CH9=camera switch | CH10=shutdown(1514)/reboot(2014) hold 2s
tfmini.service           → TFmini → /fmu/in/distance_sensor @ 50Hz
vision_streaming.service → FFmpeg dual-cam RTP→WFB-NG | cfg: /etc/vision_streaming.conf
                          CH9 PWM: front=1012(video0) bottom=1514(video2) split=2014(PiP)
block-traffic.service    → block DDS multicast on drone-wfb iface
wifibroadcast@drone      → WFB-NG drone profile
system_files_sync.timer  → auto-backup boot+daily | armed check: tcp:127.0.0.1:5760
ollama.service           → Phi-3 Mini local LLM
ldlidar.service          → STL-19 → /scan (LaserScan) via ttyAMA3

---

## [WFB_NG]
config: /etc/wifibroadcast.cfg | ch: 161 (5GHz) | region: BO | txpower: 3000 (30dBm rtl8812eu)
BW: 20MHz | MCS: 1 | STBC: 1 | LDPC: 1 | short_gi: off | CRITICAL: default_route=False both sides
drone: drone-wfb@10.5.5.87/24 | relay/GS: gs-wfb@10.5.5.77/24
streams: video TX 0x00 FEC 8/12 | mavlink RX 0x10/TX 0x90 FEC 1/2 | tunnel RX 0xa0/TX 0x20 FEC 2/4
GS endpoints: video→10.5.6.50:5600 | mavlink→10.5.6.50:14550 | keys: /etc/drone.key /etc/gs.key
stats API: drone 8002/8102 | GS 8003/8103

---

## [RELAY_STATION]
hostname: vind-rly | OS: Ubuntu 24.04.2 LTS RPi5 | ssh: vind-admin@10.5.5.77
tunnel: port 2222→drone 10.5.5.87:22 (ssh-tunnel-to-companion.service / autossh)
services: wifibroadcast@gs | mavlink.router | ssh-tunnel-to-companion | relay_files_sync.timer
wfb: standalone(CURRENT) vs cluster(+CPE610@10.5.7.102, not connected yet)
mavlink: WFB gs_mavlink:14560 → QGC(10.5.6.50:14550) + tracker(127.0.0.1:14551)
repo: ~/codex-relay → ArvinVeiyon/Relay_Station_Pxlabs | docs: system_relay.md
(see reference_wfb_rlyctl.md for wfb-rlyctl tool + all managed files)

---

## [REPOS]
codex-work: ~/codex-work → ArvinVeiyon/Companion_Computer_Pxlabs | latest: 727b44f 2026-03-15
  sync: scripts/system_files_sync.sh | memory backup: memory/claude_memory.md
codex-relay: ~/codex-relay on vind-rly → ArvinVeiyon/Relay_Station_Pxlabs | latest: 0d5c403 2026-03-15
  mirror on companion: ~/codex-relay-mirror | sync: scripts/relay_git_sync.sh (manual)
ros2_ws: ~/ros2_ws | branch: main_dev | release: release/2026-02-22

---

## [TODOS]
→ See memory/todos.md (full detail + commands) | DO AFTER FULL OS BACKUP
1. ✅ Fix GS NTP — DONE 2026-03-15
2. Disable drone wlan0 (5GHz interference with WFB-NG ch161)
3. Increase WFB rx_ring_size on GS (EAGAIN crashes, 19 restarts observed)
4. Check GS TX power (uplink severely worse than downlink)
5. Antenna tracker hardware (script ready on relay port 14551, HW pending)
6. ✅ Push codex-relay to GitHub — DONE 2026-03-15

---

## [AI_STACK]
online: claude CLI → Claude API | offline: Ollama phi3:mini (~3 tok/s on RPi5)
cmd: `ai` auto-routes | --online | --offline "question"
SSH login: status panel → b+Enter=bash | Enter/4s+internet=Claude | no internet=Phi-3
upgrade plan: phi3:mini → qwen2.5:7b (4.5GB) | fine-tune: post phase2-3, Google Colab

---

## [SENSORS]
TFmini:  ttyAMA2 115200 downward 0.3-12m 50Hz → PX4 distance_sensor
VL53L1X: I2C bus1 0x29 front-only (0-5/72 sectors 5°) 20-400cm 10Hz → obstacle_distance
OptFlow: /dev/video3 640x480 OpenCV Farneback 10Hz → sensor_optical_flow (manual launch)
STL-19:  ttyAMA3 230400 360° 0.02-12m → /scan LaserScan (ldlidar.service)
Camera0: /dev/video0 1280x720 MJPEG → primary stream
Camera2: /dev/video2 1280x720 MJPEG → bottom/secondary stream

---

## [AUTONOMY_ROADMAP]
phase1 ✅ sensor pipeline + offboard interface (distance/obstacle/optical_flow → PX4)
phase2 TODO: offboard mission node (takeoff/hover/waypoints/land) + all-dir collision stop + battery RTH
phase3 TODO: 360° obstacle avoidance (add ToF sides/rear or depth camera)
phase4 TODO: GPS-denied nav (visual odometry / SLAM: ORB-SLAM3, OpenVINS, RTAB-Map)
phase5 TODO: computer vision (YOLOv8n ~5fps, landing zone, target tracking)
phase6 TODO: AI mission brain (LLM → natural language → waypoints + replan)
safety TODO: geofence | auto-RTH low battery | emergency land | failsafe modes

---

## [TROUBLESHOOTING]
no_MAVLink:  ttyAMA0 baud, TX/RX wiring, PX4 MAVLink instance config
no_DDS:      microxrce-agent.service, ttyAMA4, PX4 XRCE param enabled
no_video:    vision_streaming.service, /dev/video0 exists, /etc/vision_streaming.conf
WFB_down:    wifibroadcast@drone.service, wlx* adapter present, /etc/drone.key
offline_AI:  ollama.service active, `ollama list` shows phi3:mini

---

## [COMMON_COMMANDS]
systemctl status <svc> | journalctl -u <svc> -f
ros2 topic list | ros2 topic echo /fmu/out/battery_status
wfb-cli drone                        # WFB link stats on drone
wfb-rlyctl status                    # relay: WFB mode/ENV/services
sudo wfb-rlyctl use-standalone|use-cluster|set-nics <iface>
python3 ~/PX4-Autopilot/Tools/mavlink_shell.py tcp:127.0.0.1:5760  # PX4 NuttShell
ai | ai --offline "question"
