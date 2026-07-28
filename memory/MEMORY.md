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
- `project_relay2_relaystn.md` — 2nd relay RELAY-STN (RPi4, ssh vind-admin@192.168.1.221 pass 1987). OPEN: WFB/EU card browns out the Pi4 USB budget → kills uplink; fix = powered hub
- `project_external_wifi_uplink.md` — external USB RTL8821CU `wlx90de80d824d6` = PRIMARY uplink, netplan STATIC 192.168.1.240/24 metric50. Onboard wlan0 out of netplan, but **`dtoverlay=disable-wifi` never applied** (inline `#` comment on the same config.txt line ⇒ overlay silently dropped; `disable-bt` on the next line worked = control). **Fix applied 2026-07-26, NOT rebooted — verify next boot; TODO #2 stays open.**
- `project_wfb_undervoltage_dead_nic.md` — **LIKELY FIXED 2026-07-25** (XL4015 @5.25V, throttled 0x0, zero UV events; "dead" NIC d993c0 is ALIVE ⇒ brownout WAS the cause, WFB_NICS back to BOTH). **DON'T raise the pot** (155mV Pi-vs-DMM gap is a PMIC ADC offset, not wiring loss); **DO NOT set usb_max_current_enable=1.** Tool: `ext5v-logger.service` + `ext5v-report <min>` — ⚠️ reads the rail UPSTREAM, blind to drops at a device's own connector. `system_files_sync` SKIPS when the FC is armed.
- `feedback_use_dds_not_mavlink.md` — RULE: talk to FC over DDS topics, not MAVLink probing (it disturbs the link / kills px4_ros2 modes)
- `project_gcs_link_degraded.md` — OPEN 2026-07-20: GCS link — downlink ~15% delivered, uplink commands 0/8; real cause of QGC "Unknown mode"
- `feedback_camera_qgc_only.md` — RULE: camera config only via QGC by user; never run vision_config_manager/edit conf myself
- `feedback_wlan0_persistent_name.md` — onboard uplink naming: MAC pin raced vs USB WFB adapters ("Failed to rename: File exists") — fix = rename to wifi0, 2026-07-19 pending reboot verify
- `project_boxb_pcie_usb.md` — BOX-B PCIe→USB3.2 board RESOLVED+verified 2026-07-19 (FFC reseat): VL805 xHCI up, Orbbec=/dev/video0-7, LG cam=8/9, dual-NIC WFB restored, user confirmed all cameras visible
- `project_ros2ws_tag_cleanup.md` — ros2_ws tag scheme: annotated semver vX.Y.Z only, baseline v1.1.0@5bace1b; cleanup DONE 2026-07-19, branches consolidated: `main` is THE working branch (main_dev fast-forwarded into it + deleted; GitHub default=main). Final refs: main + release/2026-02-22 + v1.0.0,v1.0.2,v1.0.3,v1.1.0,release-20260222,archive/*; nothing orphaned
- ✅ **CAMERA MOUNT TF — as-built, `ros2_ws f210102` (07-27).** Truth = `depth_to_scan.launch.py` defaults: cam_x 0.00, cam_y 0.00, cam_z 0.305, pitch 0.0406, roll 0.0100, range_max 5.0 (pitch/roll measured from `/camera/accel/sample`). Supersedes the 07-21 x−0.125/z0.420/zero-rpy figures. L5 unblocked. → [[project_l4_gemini_nav2_prereqs]]
- `project_rover_autonav.md` — **ACTIVE. NEXT = yaw-gain tuning (#20), then L5 (slam_toolbox+Nav2).** ARM WORKFLOW: arm in **Manual** via RC → software DO_SET_MODE→AutoNav (AutoNav cannot arm via RC). RC: ch2 throttle, ch4 steer, ch5 arm, ch6 mode, ch8 kill. **Hazards:** wheels-up + ekf-bridge + closed loop = limit cycle only disarm stops; never `pkill -f`/`pgrep -f` (self-matches the calling shell). Resume steps + checklist in the file, [[project_l2_floortest_wheel0_reversed]], `ros2_ws/docs/yaw_tuning_session.md`.
- **2026-07-26 rover fact:** at rest only ESC addr 13 stays awake (`esc_online_flags 8`) so `/odom` is SILENT with `L:1 R:0` — a small **nudge wakes the other three** (flags→15, `/odom` ~100 Hz). Not a fault, not a CAN failure. Check `esc_online_flags==15` before trusting `/odom`.
- `project_l2_floortest_wheel0_reversed.md` — L2 PASS + reflex collision-stop built/validated/pushed (b38e413). Wheel-0 "reversal" = FALSE ALARM (mirrored ESC sign). Collision-stop lives INSIDE the autonav_mode executor (unbypassable), ±20° cone, block<0.60m/clear>0.75m. Params, test flow and validation detail in the file.
- `project_l4_gemini_nav2_prereqs.md` — **L4 DONE 2026-07-21**: Orbbec wrapper + `/scan` live (`~/ros2_ws/launch/depth_to_scan.launch.py`), Nav2 1.3.12 + slam_toolbox 2.8.5 installed. RO_SPEED_LIM fixed 0.01→0.70, MAVLink healed. **Mount TF now measured (see remount line above) ⇒ L5 fully unblocked.** Bring-up commands in the file.
- `project_ffmpeg_hung_alive_gap.md` — **⚠️ OPEN: FPV VIDEO DOWN, FAULT IS PHYSICAL (2026-07-28).** LG cam alive on ep0, ZERO frames on isoc; proven by `v4l2-ctl` alone ⇒ ffmpeg/node/watchdog/resolution/devnum ALL excluded. Undervoltage + WFB + USB-reset ruled out by measurement. Load-dependent ⇒ high-resistance contact. **USER ACTION evening 07-28: different USB port + reseat companion-side connector.** Full evidence, diagnostics and falsifier in the file.
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
HW: RPi5 BCM2712 Cortex-A76 quad-core 8GB LPDDR4X | 64GB SD (**49% used, 29G free — 2026-07-21 after 20.4G log cleanup**; card fully partitioned, no unallocated space)
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
core: mavlink.router | microxrce-agent | rc_control_node | vision_streaming | block-traffic | wifibroadcast@drone | system_files_sync.timer | ollama | ldlidar(disabled)
**AIDE `dailyaidecheck.timer` DISABLED 07-26** (worthless: `COPYNEWDB=no` ⇒ stale baseline + ~3.5h/day of a core). **⚠️ if re-enabling set `COPYNEWDB=yes` + Nice=19/IOSchedulingClass=idle.**
**tfmini DISABLED 07-26 — drone-only sensor. ⚠️ MUST `systemctl enable --now tfmini` for the DRONE airframe.** Sensorless it burned 38% CPU + 214 log lines/s; disabling took /scan to **29 Hz**. → [[reference_services]]
autonav (added 2026-07-21, replaces manual setsid): rover-camera | rover-scan | rover-odometry | rover-autonav-mode — all enabled+active; **rover-ekf-bridge installed but DISABLED on purpose** (wheels-up limit-cycle hazard; start by hand on the floor, AutoNav can't arm without it)

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
**NEW 2026-07-23 outdoor section [ROVER OUTDOOR — PRIMARY TARGET] O1-O5**: O1 re-integrate STL-19 lidar (needs unit back; lidar owns /scan, remap depth→/scan_depth) · O2 DroneCAN GPS (UAVCAN_ENABLE+EKF2_GPS_CTRL; model TBD) · O3 lidar SLAM · O4 GPS-waypoint Nav2 · O5 outdoor safety. Come AFTER indoor L5/L6.
**2026-07-23: #18 L2 floor test DONE (armed, PASSED) · #19 kill-in-AutoNav DONE (confirmed working armed).
Reflex collision-stop built+validated+pushed b38e413. Next action = #20 re-tune yaw gains (armed yaw
~700-850 rpm vs fwd ~156), then L5 (slam_toolbox+Nav2). #21 gyro-yaw odometry still open (highest-value
accuracy win, replaces slip-prone wheel-derived yaw)**
1. Fix relay clock for real (local NTP via companion) — OPEN, recurred 2026-07-11, see project_relay_ntp_setup.md
2. Disable drone onboard Wi-Fi wifi0/ex-wlan0 (5GHz interference with WFB-NG ch161)
3. Increase WFB rx_ring_size on GS (EAGAIN crashes, 19 restarts observed)
4. Check GS TX power (uplink severely worse than downlink)
5. Antenna tracker hardware (script ready on relay port 14551, HW pending)
6. ✅ DONE 2026-07-19: ffmpeg watchdog in vision_streaming node (a561e93)
7. ✅ Orbbec wrapper + /scan DONE 2026-07-21 (L4); ✅ #15 camera mount TF re-measured as-built 2026-07-27 (f210102); ✅ #16 OrbbecSDK pinned. Remains: wire /scan → obstacle_distance/Nav2, #17 delete camera_sw_node_obsolute.py
8. QGC half ✅ DONE (dynamic picker, phase C); ✅ 99-usb-cameras.rules RETIRED 2026-07-27 (neutered in place, not deleted — file is comments only). REMAINING = multicam Phase D: rc_control yamls + optical_flow → aliases/usbcam ids (see project_vision_multicam_upgrade.md)
9. **Vision open items 2026-07-28** (from [[project_ffmpeg_hung_alive_gap]], none tracked before): (a) `vision_streaming_node.py:325-326` still resets `backoff_s` on the STALL path — agreed fix, unapplied; (b) `/sys/bus/usb/devices/6-2/power/control` still `auto`, pin to `on` via udev; (c) `vision_config_manager` v2.3.0 = optional `--bitrate` on `set-cam-params` + `active.settings` in `list --json` (designed, not written; QGC half is theirs)

## [AI_STACK]
online: claude CLI → Claude API | offline: Ollama phi3:mini (~3 tok/s on RPi5)
cmd: `ai` auto-routes | --online | --offline "question"
SSH login: b+Enter=bash | Enter/4s+internet=Claude | no internet=Phi-3

## [SENSORS]
TFmini: ttyAMA2 downward 0.3-12m 50Hz → distance_sensor
VL53L1X: I2C 0x29 front 20-400cm 10Hz → obstacle_distance
OptFlow: /dev/video3 Farneback 10Hz → sensor_optical_flow (manual launch)
STL-19: ttyAMA3 360° 0.02-25m ~10Hz LaserScan — **NOW A PRIMARY-TARGET SENSOR** (outdoor 360°+SLAM, user re-fitting 2026-07-23); hw was moved to another team 2026-04-17 → needs the unit back; driver ready in ros2_ws; on re-integration lidar owns `/scan` (remap depth→/scan_depth). See roadmap O1.
Cameras (roles 2026-07-19): LG Smart Cam = FPV, id `usbcam-30c9009d-01.00.00-i00` (bus 6-2, 480M, 500mA) | Orbbec Gemini 336L = autonomy-only, alias NAV-COLOR role_lock, id `usbcam-2bc50807-CPC7B53000AB-i04` (USB3 on BOX-B, ROS2 wrapper only, never ffmpeg; rover-camera+rover-scan ACTIVE as of 07-28).
**Three camera rules — all learned the hard way:** (1) **NEVER key a camera by `/dev/videoN` or `/dev/v4l/by-id`** — only `usbcam-<vidpid>-<serial>-i<iface>` ids/aliases. (2) **NEVER record resolution/fps/bitrate as fact** — operator-set from QGC, changes without notice; read `/etc/vision_streaming.conf` live. (3) **The Orbbec's video nodes appear/vanish with `rover-camera.service`** (wrapper running ⇒ libusb owns it, no nodes; stopped ⇒ uvcvideo makes 8, taking video0) — both the old "video0=depth/video2/4=IR" map and the flat "has no nodes at all" claim are wrong. Renumbering also comes from the Pi5's own `rpivid`/`pispbe-*` axi nodes (video19-37). → [[project_vision_multicam_upgrade]]

## [AUTONOMY_ROADMAP]
> **SOURCE OF TRUTH = `~/ros2_ws/docs/roadmap.md`.** **PRIMARY TARGET = OUTDOOR autonomous nav** (GPS waypoint, 360° avoidance) — reframed 07-23 by user; indoor GPS-denied (L0-L4) = stepping-stone + GPS-loss fallback, not the goal.
> Ladder: **L0-L7 indoor (L0-L4 DONE, L5 Nav2 next)** then **O1(STL-19)→O2(DroneCAN GPS)→O3(lidar SLAM)→O4(GPS-waypoint Nav2)→O5(outdoor safety)**. Interstitial before L5: #20 yaw tuning. Aerial phase1-6 below = deferred.
> **Two hardware additions pending:** STL-19 lidar (**on re-integration it OWNS `/scan`; remap depth_to_scan → `/scan_depth`**; unit is with another team) and a DroneCAN GPS (CAN bus already live; UAVCAN_ENABLE + EKF2_GPS_CTRL, model TBD). **Gemini 336L IS outdoor-capable** (active-stereo/global-shutter; the old "blind in sun" note was wrong).
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
