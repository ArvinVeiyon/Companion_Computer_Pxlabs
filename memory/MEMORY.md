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
- `project_codexwork_branches.md` — codex-work origin/main stale, left as-is; + auto-sync doesn't git-add NEW memory files, add manually after creating one
- `project_codexwork_token_in_remote.md` — SECURITY: codex-work origin URL embeds a plaintext GitHub PAT; rotate + switch to SSH/credential helper
- `project_codexrelay_divergence.md` — codex-relay master diverged from GitHub; merge-reconciled, relay still behind
- `project_relay2_relaystn.md` — 2nd relay RELAY-STN (RPi4, mgmt ssh vind-admin@192.168.1.221 pass 1987) built 2026-07-12. OPEN: WFB/EU card browns out Pi4 USB budget → kills uplink too; fix=powered hub (debug 2026-07-14, continue)
- `feedback_use_dds_not_mavlink.md` — RULE: talk to FC over DDS topics, not MAVLink probing (it disturbs the link / kills px4_ros2 modes)
- `project_gcs_link_degraded.md` — OPEN 2026-07-20: GCS link — downlink ~15% delivered, uplink commands 0/8; real cause of QGC "Unknown mode"
- `feedback_camera_qgc_only.md` — RULE: camera config only via QGC by user; never run vision_config_manager/edit conf myself
- `feedback_wlan0_persistent_name.md` — onboard uplink naming: MAC pin raced vs USB WFB adapters ("Failed to rename: File exists") — fix = rename to wifi0, 2026-07-19 pending reboot verify
- `project_boxb_pcie_usb.md` — BOX-B PCIe→USB3.2 board RESOLVED+verified 2026-07-19 (FFC reseat): VL805 xHCI up, Orbbec=/dev/video0-7, LG cam=8/9, dual-NIC WFB restored, user confirmed all cameras visible
- `project_ros2ws_tag_cleanup.md` — ros2_ws tag scheme: annotated semver vX.Y.Z only, baseline v1.1.0@5bace1b; cleanup DONE 2026-07-19, branches consolidated: `main` is THE working branch (main_dev fast-forwarded into it + deleted; GitHub default=main). Final refs: main + release/2026-02-22 + v1.0.0,v1.0.2,v1.0.3,v1.1.0,release-20260222,archive/*; nothing orphaned
- `project_rover_autonav.md` — **ACTIVE, RESUME HERE (2026-07-20 session 3)**: rover autonav. L0+L1 DONE (mode control via DDS: `~/ros2_ws/tools/dds_setmode.py`, nav_state 23=AutoNav). L2 blocked → **L3 FIRST**. Accel blocker CLEARED (quick cal, param5=4 — big vehicles never need rotating). rover_odometry bug FIXED (absolute msg.timestamp vs boot-relative nested esc[].timestamp) → /odom live @99.9Hz. New pkg **rover_ekf_bridge** built+running: /odom → EKF2 EV velocity @40Hz (must send velocity_z or EKF2 drops the sample). **L3 VERIFIED**: EKF2_EV_CTRL=4 set → cs_ev_vel true, xy_valid+v_xy_valid TRUE, dead_reckoning false, preflight passes, AutoNav holds nav_state 23. Both arm blockers cleared. **L2 run: ARMED + wheels turned + watchdog OK, but PARTIAL** — yaw drives all 4 correctly, FORWARD only turns addr 13 and does not scale with speed; magnitudes meaningless on stands (closed-loop control has no body motion). Manual RC test then proved ALL 4 wheels drive both directions (±1500 ERPM) → hardware/allocation GOOD, fault is in the closed-loop speed path (invalid feedback on stands). Full chain re-verified companion-side (tools/autonav_chain_check.py): register mode_id=23 → arming handshake can_arm_and_run=True → DO_SET_MODE ACCEPTED → ARM ACCEPTED → onActivate emits ~30Hz rover speed+rate setpoints at 0.000. Next: FLOOR test + check RO_* speed gains. RC: ch2=throttle, ch4=steer, ch3 unused. QGC "Unknown mode" is NOT a QGC bug — dead GCS uplink, see project_gcs_link_degraded.md. ALL COMMITTED 2026-07-20 on ros2_ws main (a72f1b9..2fa1097: px4_msgs pin, autonav_mode, rover_odometry+rover_ekf_bridge, tools, docs, chain-check) + PUSHED to origin/main.
- `project_vision_multicam_upgrade.md` — multi-camera+alias upgrade: phases A+B+C DONE, FPV UP (LG 720p); discovery v2.1 DONE 2026-07-19 (by-id index NOT boot-stable → sysfs usbcam-<vidpid>-<serial>-i<iface> ids, codex-work 9e61729 + ros2_ws 5bace1b, store migrated; reboot-stability check pending next power cycle) — **REMAINING: Phase D (rc_control+optflow→aliases) + udev rule cleanup, go-ahead given, see file**

## [KNOWN_FIXES]
→ full archive: reference_known_fixes_archive.md
Most recent: camera identity fix 2026-07-19 (by-id index unstable → usbcam sysfs ids, vision_config_manager v2.1.0); ffmpeg watchdog 2026-07-19
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
PX4 **pxlabs-v1.17.0-2.0.0** custom | git-hash a52c38b07d | built 2026-05-31 | target: px4_fmu-v6xrt
(verified via NuttShell `ver all` 2026-07-19 — was wrongly recorded as v1.16.0-rc1 c5b8445 before; FC reflashed 2026-05-31. Local ~/PX4-Autopilot @ c5b8445 is upstream clone, NOT the firmware source — pxlabs fork not on companion)

## [UART_MAP]
→ full table: reference_uart_map.md
AMA0=MAVLink 921600 | AMA2=TFmini 115200 | AMA3=STL19 230400(disabled) | AMA4=DDS 921600 | AMA1=free

## [SOFTWARE_VERSIONS]
ROS2: Jazzy | Python: 3.12.3 | Ollama: v0.17.7 / phi3:mini 2.2GB | AIDE: 0.18.6
mavlink-router: c20337b | MicroXRCEAgent: v3.0.0-2-gb9d84ac | wfb-ng: 1b88185
~/PX4-Autopilot: upstream clone @ c5b8445 + remote `pxlabs` (ArvinVeiyon/PXLABS_PX4-Autopilot) + branch `pxlabs-fw`=a52c38b (real FC firmware source)
px4_msgs: pinned release/1.17 @ 86d8239 (branch pinned-pxlabs-1.17, exact match vs FC fw) | px4-ros2-interface-lib: release/1.17 @ 4a3370f (branch pinned-1.17; has rover setpoints; 2.x needs newer fw)

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
ros2_ws: ~/ros2_ws | branch: main (main_dev merged+deleted 2026-07-19) | release: release/2026-02-22

## [TODOS]
→ See memory/todos.md (full detail + commands)
1. Fix relay clock for real (local NTP via companion) — OPEN, recurred 2026-07-11, see project_relay_ntp_setup.md
2. Disable drone onboard Wi-Fi wifi0/ex-wlan0 (5GHz interference with WFB-NG ch161)
3. Increase WFB rx_ring_size on GS (EAGAIN crashes, 19 restarts observed)
4. Check GS TX power (uplink severely worse than downlink)
5. Antenna tracker hardware (script ready on relay port 14551, HW pending)
6. ✅ DONE 2026-07-19: ffmpeg watchdog in vision_streaming node (a561e93)
7. Orbbec autonomy pipeline: OrbbecSDK_ROS2 → depth/pointcloud → obstacle avoidance (phase 3 prep)
8. QGC half ✅ DONE (dynamic picker, phase C); REMAINING = multicam Phase D: rc_control yamls + optical_flow → aliases/usbcam ids, then delete 99-usb-cameras.rules (see project_vision_multicam_upgrade.md)

## [AI_STACK]
online: claude CLI → Claude API | offline: Ollama phi3:mini (~3 tok/s on RPi5)
cmd: `ai` auto-routes | --online | --offline "question"
SSH login: b+Enter=bash | Enter/4s+internet=Claude | no internet=Phi-3

## [SENSORS]
TFmini: ttyAMA2 downward 0.3-12m 50Hz → distance_sensor
VL53L1X: I2C 0x29 front 20-400cm 10Hz → obstacle_distance
OptFlow: /dev/video3 Farneback 10Hz → sensor_optical_flow (manual launch)
STL-19: ttyAMA3 360° — TESTING ONLY, hw moved to other team 2026-04-17
Cameras (roles set 2026-07-19): LG Smart Cam=FPV alias FPV, id usbcam-30c9009d-01.00.00-i00 (video8 today, 1280x720 MJPG user-applied from QGC; stable ids survive boot shuffles since v2.1) | Orbbec Gemini 336L=autonomy-only, color alias NAV-COLOR role_lock, id usbcam-2bc50807-CPC7B53000AB-i04 (video6 today; video0=depth Z16, video2/4=IR; up to 1280x800 MJPG; USB3 on BOX-B; ROS2 wrapper for phase3/4, never ffmpeg) | old front/bottom cams removed | NEVER key cameras by /dev/v4l/by-id (index order not boot-stable)

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
