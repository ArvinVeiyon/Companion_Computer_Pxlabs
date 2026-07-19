# Vind-Roz Platform Memory
> Compressed semantic memory. Auto-loaded each session. Also Phi-3 system prompt (offline AI).
> Live: ~/.claude/projects/-home-roz/memory/ | Backup: ~/codex-work/memory/ → GitHub ArvinVeiyon/Companion_Computer_Pxlabs

## [MEMORY_FILES]
All files live in ~/.claude/projects/-home-roz/memory/ and are mirrored in ~/codex-work/memory/
- `feedback_dkms_arch.md` — rtl88x2eu DKMS ARCH fix
- `reference_wfb_rlyctl.md` — wfb-rlyctl relay control tool (all managed files)
- `reference_wfb_cfg_apply.md` — wfb-cfg-apply WFB safe-apply watchdog (QGC-driven, both devices)
- `reference_wfb_ng.md` — full WFB-NG config (channel/FEC/endpoints/multi-adapter)
- `reference_uart_map.md` — full ttyAMA UART pin/baud table
- `reference_services.md` — full systemd service map (endpoints, configs, notes)
- `reference_known_fixes_archive.md` — chronological archive of resolved fixes
- `reference_gcs_companion_interface.md` — G-Control↔companion SSH interface, binaries, camera map
- `todos.md` — platform TODO list (WFB fixes, post OS backup)
- `ros2_nodes.md` — ROS2 node details (pkg paths, pub/sub, params)
- `ros2_topics.md` — full FMU↔companion DDS topic lists
- `rover_odometry.md` — rover wheel odometry node plan (all params, formulas, ESC mapping)
- `project_relay_ntp_setup.md` — relay clock fix plan/status — OPEN
- `project_companion_network_degraded.md` — companion IPv6 unreachable + slow bandwidth
- `project_codexwork_branches.md` — codex-work origin/main stale, left as-is
- `project_codexrelay_divergence.md` — codex-relay master diverged from GitHub; merge-reconciled, relay still behind
- `project_relay2_relaystn.md` — 2nd relay RELAY-STN (RPi4, mgmt ssh vind-admin@192.168.1.221 pass 1987) built 2026-07-12. OPEN: WFB/EU card browns out Pi4 USB budget → kills uplink too; fix=powered hub (debug 2026-07-14, continue)
- `feedback_wlan0_persistent_name.md` — wlan0 internet uplink pinned to MAC via udev (was drifting to wlan1)
- `project_boxb_pcie_usb.md` — BOX-B PCIe→4x USB3.2 board: PCIe link down (electrical, not driver) → Orbbec Gemini 336L + WFB adapter not enumerating — OPEN 2026-07-19

## [KNOWN_FIXES]
→ full archive: reference_known_fixes_archive.md
Most recent: WFB_NICS syntax fix 2026-05-10 (both NICs in one quoted string)
Open regression: 2026-03-15 relay NTP fix didn't hold — see project_relay_ntp_setup.md

## [IDENTITY]
role: Claude Code CLI + onboard AI for Vind-Roz drone/rover platform
user: roz / ArvinVeiyon | memory: ~/.claude/projects/-home-roz/memory/MEMORY.md
goal: continuous presence — develop, maintain, autonomize this platform

## [PLATFORM]
Vind-Roz: aerial drone + ground rover | same RPi5 companion, different PX4 airframe config
HW: RPi5 BCM2712 Cortex-A76 quad-core 8GB LPDDR4X | 64GB SD (~63% used)
OS: Ubuntu 24.04.1 LTS aarch64 | kernel 6.8.0-1048-raspi | hostname: Vind-Roz

## [FLIGHT_CONTROLLER]
Custom Pixhawk 6X-RT (in-house PCB, NOT Holybro) | MCU: NXP i.MX RT1176 Cortex-M7+M4
PX4 v1.16.0-rc1 custom | commit c5b8445ffc | target: px4_fmu-v6xrt

## [UART_MAP]
→ full table: reference_uart_map.md
AMA0=MAVLink 921600 | AMA2=TFmini 115200 | AMA3=STL19 230400(disabled) | AMA4=DDS 921600 | AMA1=free

## [SOFTWARE_VERSIONS]
ROS2: Jazzy | Python: 3.12.3 | Ollama: v0.17.7 / phi3:mini 2.2GB | AIDE: 0.18.6
mavlink-router: c20337b | MicroXRCEAgent: v3.0.0-2-gb9d84ac | wfb-ng: 1b88185 | PX4-Autopilot: c5b8445ffc

## [SERVICES]
→ full detail: reference_services.md
last verified 2026-05-09: mavlink.router + microxrce-agent active, FC connected, DDS negotiated
core: mavlink.router | microxrce-agent | rc_control_node | tfmini | vision_streaming | block-traffic | wifibroadcast@drone | system_files_sync.timer | ollama | ldlidar(disabled)

## [WFB_NG]
→ full detail: reference_wfb_ng.md
ch161 5GHz | drone-wfb@10.5.5.87 ↔ gs-wfb@10.5.5.77 | keys /etc/drone.key /etc/gs.key
multi-adapter TX via fwmark+tc across both wlx NICs (fixed 2026-05-10)

## [RELAY_STATION]
hostname: vind-rly | OS: Ubuntu 24.04.2 LTS RPi5 | ssh: vind-admin@10.5.5.77
tunnel: port 2222→drone 10.5.5.87:22 (autossh) | services: wifibroadcast@gs, mavlink.router, ssh-tunnel-to-companion, relay_files_sync.timer
wfb: standalone(CURRENT) vs cluster(+CPE610@10.5.7.102, not connected) | repo: ~/codex-relay
NO RTC + no internet uplink → clock unreliable, see project_relay_ntp_setup.md
(see reference_wfb_rlyctl.md for wfb-rlyctl tool + all managed files)

## [REPOS]
codex-work: ~/codex-work → Companion_Computer_Pxlabs | branch: master (origin/main stale, see project_codexwork_branches.md)
codex-relay: ~/codex-relay on vind-rly → Relay_Station_Pxlabs | mirror: ~/codex-relay-mirror
ros2_ws: ~/ros2_ws | branch: main_dev | release: release/2026-02-22

## [TODOS]
→ See memory/todos.md (full detail + commands)
1. Fix relay clock for real (local NTP via companion) — OPEN, recurred 2026-07-11, see project_relay_ntp_setup.md
2. Disable drone wlan0 (5GHz interference with WFB-NG ch161)
3. Increase WFB rx_ring_size on GS (EAGAIN crashes, 19 restarts observed)
4. Check GS TX power (uplink severely worse than downlink)
5. Antenna tracker hardware (script ready on relay port 14551, HW pending)

## [AI_STACK]
online: claude CLI → Claude API | offline: Ollama phi3:mini (~3 tok/s on RPi5)
cmd: `ai` auto-routes | --online | --offline "question"
SSH login: b+Enter=bash | Enter/4s+internet=Claude | no internet=Phi-3

## [SENSORS]
TFmini: ttyAMA2 downward 0.3-12m 50Hz → distance_sensor
VL53L1X: I2C 0x29 front 20-400cm 10Hz → obstacle_distance
OptFlow: /dev/video3 Farneback 10Hz → sensor_optical_flow (manual launch)
STL-19: ttyAMA3 360° — TESTING ONLY, hw moved to other team 2026-04-17
Camera0/2: /dev/video0 front, /dev/video2 bottom, 1280x720 MJPEG

## [AUTONOMY_ROADMAP]
phase1 ✅ sensor pipeline + offboard interface
phase2 TODO: offboard mission node + collision stop + battery RTH
phase3 TODO: 360° obstacle avoidance
phase4 TODO: GPS-denied nav (SLAM)
phase5 TODO: computer vision (YOLOv8n, landing zone, tracking)
phase6 TODO: AI mission brain (LLM → waypoints + replan)
safety TODO: geofence | auto-RTH | emergency land | failsafe modes

## [GCS_INTERFACE]
→ full detail: reference_gcs_companion_interface.md
G-Control.exe → pxlabs_cli.exe → SSH relay:2222 → companion:22 (relay always in middle)
key binaries: vision_config_manager (camera) | Rozcam (capture) | sudo via printf|sudo -S

## [TROUBLESHOOTING]
no_MAVLink: ttyAMA0 baud/wiring, PX4 MAVLink instance config
no_DDS: microxrce-agent.service, ttyAMA4, PX4 XRCE param
no_video: vision_streaming.service, /dev/video0, /etc/vision_streaming.conf
WFB_down: wifibroadcast@drone.service, wlx* adapter, /etc/drone.key
offline_AI: ollama.service active, `ollama list` shows phi3:mini

## [COMMON_COMMANDS]
systemctl status <svc> | journalctl -u <svc> -f
ros2 topic list | ros2 topic echo /fmu/out/battery_status
wfb-cli drone | wfb-rlyctl status | sudo wfb-rlyctl use-standalone|use-cluster|set-nics <iface>
python3 ~/PX4-Autopilot/Tools/mavlink_shell.py tcp:127.0.0.1:5760
ai | ai --offline "question"
