# Vind-Roz Platform Memory
> Auto-loaded each session; also the Phi-3 offline system prompt. Live: ~/.claude/projects/-home-roz/memory/ | Backup: ~/codex-work/memory/ → GitHub ArvinVeiyon/Companion_Computer_Pxlabs
> ⚠️ **BACKUP IS MANUAL:** `cp -p ~/.claude/projects/-home-roz/memory/*.md ~/codex-work/memory/` then git add/commit/push. **Never `rsync --delete`** — the mirror is a UNION of two scopes. A 2nd scope at `~/.claude/projects/-home-roz-codex-work/memory/` is NOT auto-loaded — check it after any codex-work session.
> ⚠️ **KEEP UNDER 125 LINES / 17 KB.** One line per entry; detail belongs in the topic files.

## [MEMORY_FILES]
**feedback (RULES):** `check_docs_before_measuring` 🔴 **grep the WHOLE memory dir + `docs/` for a dimension BEFORE deriving it; an index line must name a file's LOAD-BEARING content; the operator's ID of their own hardware beats my inference** · `crash_recovery_checkpoint` (**checkpoint PER FINDING**) · `use_dds_not_mavlink` (**FC over DDS, never MAVLink probing**) · `camera_qgc_only` (**FPV cams set ONLY from QGC**) · `dkms_arch` · `wlan0_persistent_name` (udev rule GONE 07-30)
**reference:** `wfb_ng` · `wfb_rlyctl` · `wfb_cfg_apply` · `uart_map` · `services` · `known_fixes_archive` · `gcs_companion_interface` · `todos.md` · `ros2_nodes`/`ros2_topics` · `rover_odometry`
**project — ACTIVE:** `rover_autonav` (**🔴 YAW RUNAWAY ~21×, ⛔ no armed yaw tests; ALL pre-08-01 speeds read 12.2× LOW**) · `perception_3d_costmap` (**`/scan_3d` live, rate fixed, top-plate settled; reflex NOT switched**) · `autonomy_plan_reframe` (**Q1 localization = THE WALL**) · `rc_control_camera_retry_storm` (**FIXED `9893d6b` — WAS the "runaway" blamed twice on a stray process**)
**project — other:** `l4_gemini_nav2_prereqs` (🔴 **ALSO the 07-26 camera remount geometry + "deck IS in frame"**) · `vision_multicam_upgrade` (**Phase D remains**) · `l2_floortest_wheel0_reversed` · `wfb_undervoltage_dead_nic` (**DON'T raise the pot / set usb_max_current_enable=1**) · `external_wifi_uplink` · `gcs_link_degraded` · `relay_ntp_setup` · `relay2_relaystn` (Pi4 USB brownout; fix = powered hub) · `companion_network_degraded` · `boxb_pcie_usb` · `codexrelay_divergence` · `codexwork_token_in_remote` (🔴 **plaintext PAT in origin URL**) · `codexwork_branches` (**auto-sync does NOT git-add NEW files**)

## [VIDEO_FAULTS] → **FULL RECORD NOW LIVES IN `~/ros2_ws/docs/vision_streaming.md`** (spec, architecture, faults, traps, defects, change history, rules)
**(B) 🔴 CPU-STARVATION LATCH — CHECK THIS FIRST, no hardware work.** ffmpeg loses a CPU race and **never recovers** (7-28 pkt/s vs 208), service "active", logs silent. **A restart does NOT clear it. FIX: briefly `systemctl stop rover-camera rover-scan rover-odometry`.**
**(A) CAMERA WEDGE — looks identical.** ⛔ **NO SOFTWARE RECOVERY EXISTS — don't build one**; only physical VBUS removal clears it.
⛔ **Do NOT modify the ffmpeg command line** (vetoed) · ⛔ **never hardcode frame rate** · **`fps` conf key is INERT** · **never record resolution/fps/bitrate as fact — read them live.**

## [IDENTITY]
Claude Code CLI + onboard AI for the Vind-Roz drone/rover platform | user: roz / ArvinVeiyon | goal: continuous presence — develop, maintain, autonomize this platform

## [PLATFORM]
Vind-Roz: aerial drone + ground rover, same RPi5 companion, different PX4 airframe | RPi5 BCM2712 quad-core 8GB | Ubuntu 24.04.1 aarch64, kernel 6.8.0-1048-raspi, host `Vind-Roz`
⚠️ **Boot clock is WRONG until NTP steps it.** ⚠️ **Only 4 cores; rover stack + x264 oversubscribe them** → [VIDEO_FAULTS] (B).
⚠️ **No rate/CPU measurement here is trustworthy without `ps -eo pid,pcpu --sort=-pcpu` first** — a "7.5 Hz cloud" reading was really a runaway at 72.7%.

## [FLIGHT_CONTROLLER]
Custom Pixhawk 6X-RT (in-house PCB, NOT Holybro) | MCU: NXP i.MX RT1176 Cortex-M7+M4
PX4 **pxlabs-v1.17.0-2.0.0** | a52c38b07d | 2026-05-31 | px4_fmu-v6xrt (local ~/PX4-Autopilot @ c5b8445 is an upstream clone, NOT the fw source)

## [UART_MAP] → reference_uart_map.md
AMA0=MAVLink 921600 | AMA2=TFmini 115200 | AMA3=STL19 230400(disabled) | AMA4=DDS 921600 | AMA1=free

## [SOFTWARE_VERSIONS]
ROS2 Jazzy | Python 3.12.3 | Ollama v0.17.7 / phi3:mini | AIDE 0.18.6 | wfb-ng 1b88185 | mavlink-router c20337b | MicroXRCEAgent v3.0.0-2-gb9d84ac | px4_msgs + px4-ros2-interface-lib release/1.17 @ 86d8239 / 4a3370f | Orbbec wrapper+SDK 2.9.3 | ~/PX4-Autopilot: upstream @ c5b8445 + remote `pxlabs`, branch `pxlabs-fw`=a52c38b (real FC fw source)
⚠️ **Pi 5 has NO hardware H.264 encoder** (`v4l2h264enc` missing; `rpivid` decode-only) — all H.264 is software x264. GStreamer 1.24.2 gives no speed advantage; stay with ffmpeg.

## [SERVICES] → reference_services.md
core: mavlink.router | microxrce-agent | rc_control_node | vision_streaming | block-traffic | wifibroadcast@drone | system_files_sync.timer | ollama | ldlidar(disabled)
**AIDE `dailyaidecheck.timer` DISABLED 07-26** (~3.5h/day of a core). If re-enabling: `COPYNEWDB=yes` + Nice=19.
**tfmini DISABLED 07-26 — drone-only. ⚠️ MUST `systemctl enable --now tfmini` for the DRONE airframe.**
autonav: rover-camera | rover-scan | **rover-scan-3d (NEW)** | rover-odometry | rover-autonav-mode — enabled+active; **rover-ekf-bridge installed but DISABLED on purpose** (wheels-up limit-cycle hazard; start by hand on the floor).
**⚡ FPV video costs `/scan` 28.4→22.3 Hz** ⇒ don't stream FPV while driving. **🔴 `/odom` DIES AT REST — ESC doze (`esc_online_flags: 8`), NOT CPU.** ⚠️ `/odom` is RELIABLE QoS — a BEST_EFFORT subscriber reads 0 and mimics this fault exactly.
🔴 **A CAMERA RESTART CAN COME UP HALF-DEAD** — back "active", params answering, gyro/accel streaming, **no error logged, but depth & color never started**; `/scan` + both depth topics silently dead. A 2nd restart fixed it. **VERIFY EVERY camera restart:** `journalctl -u rover-camera --since -1min | grep "depth Frame - Width"` (absent = half-dead) **AND a topic rate. `systemctl is-active` does NOT catch this.**

## [PERCEPTION 08-01] → **all numbers + reasoning: project_perception_3d_costmap.md · geometry: ~/ros2_ws/docs/rover_geometry.md**
📗 **`docs/rover_geometry.md` (NEW) = THE authoritative source for every vehicle dimension + camera mount. READ IT BEFORE deriving geometry.** §6 = the 6 files consuming those numbers; §7 = sensors not fitted.
✅ **Cloud rate fixed:** `point_cloud_decimation_filter_factor:=3` (drop-in on `rover-camera`): **10.0 → 23.2 Hz**, worst gap 1066 → 301 ms. ⚠️ **`ros2 param set` on it does NOTHING** — live lever is the **service** `/camera/set_point_cloud_decimation`.
✅ **`cloud_to_scan` deployed as `rover-scan-3d.service`, PARALLEL.** Publishes **`/scan_3d`, not `/scan`, and NO TF** ⇒ **⛔ NEVER repoint `rover-scan.service` at it** (it alone provides `base_link->camera_link`). `/scan_3d` **29.2 Hz / 99 ms** vs `/scan` 23.5 / 233.
✅ **The near returns ARE the rover's OWN TOP PLATE** (plate z 0.235; `cam_z 0.305 = 0.235 + 0.070 bracket`; measured z 0.231 = 4 mm match). **Leave the camera CENTRED** — moving it forward trades a croppable object for a real blind strip and breaks `cam_x=0` (rotation centre). ⚠️ **I wrongly "overturned" this by comparing `/scan_3d` beams <0.60 m, but `range_min=0.40` had already clipped the plate out of that population. LESSON: check a filter doesn't already remove what you're testing for — verify at CLOUD level.** → [[feedback-check-docs-before-measuring]]
✅ **FAIL-OPEN CLOSED (`3f74af4`):** `range_min` 0.40→**0.31** + `autonav_mode` rejects **`x<0.345 && |y|<0.225` +20 mm margin** per-ray. **Radial cuts can't express a rectangular body**; 0.40 erased real obstacles 0.337-0.40 m and **a dropped ray reads as INFINITE clearance** ⇒ 6 cm fail-open at the bumper. ⚠️ **`/scan_3d` NOW CONTAINS THE TOP PLATE by design — every consumer must reject its own footprint.** Also `ca81d2a`: corridor 0.25→0.275; Nav2 `robot_radius` 0.30→explicit rectangle (0.30 left most of the rover OUTSIDE its own footprint). Both were sized off the superseded 0.405 m plate width.
✅ **HEIGHT BAND VALIDATED (one location):** RANSAC floor plane, 9833 inliers, RMS 9.9 mm ⇒ tilt **+0.37°**, crosses 0.12 m at **x=20.7 m**. ⚠️ repeat at 2-3 spots. 🔑 **percentiles DO NOT WORK — p5 sinks, p50 climbs with range, giving OPPOSITE wrong answers (±2.6° vs true +0.37°). ALWAYS RANSAC the plane.**
✅ **VL53L1X = the PRE-depth-camera collision system, SUPERSEDED — not a gap.** `rov_collision_stop`+`obstacle_distance` = dead code, retire with #17. ⚠️ consequence: the reflex is in `autonav_mode`'s executor, same sensor+computer ⇒ **not independent of the companion**; perception loss fails SAFE (`require_scan=true`).
🔴 **REFLEX SWITCH GATED — unexplained cluster: x 0.353-0.400, y +0.085..+0.161, z 0.100-0.218 (BELOW the plate, ~5 cm past its edge). NOT the VL53L1X.** Reads as 3.8 cm bumper clearance vs a 0.35 m stop ⇒ **if it's the rover, `/scan_3d` leaves it PERMANENTLY BLOCKED.** `front_overhang` couldn't catch it (2D band sits above z 0.22). **NEEDS EYES.**
🔎 `min_height=0.12` likely too conservative (floor measured −0.012 m) ⇒ 0.06-0.08 would ~halve the 12 cm minimum visible obstacle; measure 2-3 spots first.

## [WFB_NG] → reference_wfb_ng.md
ch161 5GHz | drone-wfb@10.5.5.87 ↔ gs-wfb@10.5.5.77 | keys /etc/drone.key /etc/gs.key | multi-adapter TX via fwmark+tc, both wlx NICs
**`wifibroadcast@` restart prints `rtw_mlmeext_disconnect` WARN + trace 2×. BENIGN — don't investigate or patch the driver.**
**Drone TX is flawless. When video breaks, WFB has an EMPTY input queue — suspect the source.** Live stats: TCP `127.0.0.1:8102` (GS 8103), JSON; do NOT use the `wfb-cli` TUI.
**⚡ 07-31:** uplink loses 13.57% mavlink. **ROOT CAUSE = drone NIC-A ant0 −48.5 vs ant1 −28.3 dBm (20 dB deaf)** ⇒ **ONLY WFB JOB LEFT: reseat that antenna.** ✅ DELETED as causes: ring-buffer/EAGAIN, GS TX power, peer `10.5.6.50`.
⚠️ **METHOD (cost a week):** compare payload `tx.incoming`→`rx.out` across 8102/8103. **Never `rx.all`** (double-counts 4 antennas). **Never infer radio health from MAVLink rates at two `tcp:5760` endpoints.** → reference_wfb_ng.md

## [RELAY_STATION]
vind-rly | RPi5 | `ssh vind-admin@10.5.5.77` (**sudo NEEDS A PASSWORD ⇒ journalctl of other units returns "No entries"**) | repo ~/codex-relay | tunnel 2222→drone 10.5.5.87:22 (autossh)
svcs: wifibroadcast@gs, mavlink.router, ssh-tunnel-to-companion, relay_files_sync.timer | wfb standalone(CURRENT) vs cluster(+CPE610, not connected)
**Wi-Fi Direct P2P-GO `p2p-wlan0-0`, SSID `vind_rely`, ch149, relay 10.5.6.101/24 → QGC laptop 10.5.6.50** | NO RTC → clock unreliable

## [REPOS]
codex-work: ~/codex-work → Companion_Computer_Pxlabs, branch master (origin/main stale) | codex-relay: ~/codex-relay on vind-rly → Relay_Station_Pxlabs (mirror ~/codex-relay-mirror) | ros2_ws: ~/ros2_ws, branch main, **released `v1.2.0` 08-01** (annotated, semver; prev v1.1.0 07-19)

## [CURRENT STATE — 2026-08-01 22:30, live-verified. Nothing broken]
All core + 5 autonav svcs active · `rover-ekf-bridge` inactive (correct) · **DISARMED** · `/odom` at rest ✅ · `/scan` 23.5 Hz · `/scan_3d` 29.2 Hz · `vision_streaming` inactive (deliberate, for perception testing). **ros2_ws CLEAN + PUSHED through `e1770c5`.**
⚠️ **`fps` is INERT — QGC's fps control does NOTHING**; resolution + bitrate DO work. 640x360 cut ffmpeg CPU 78-95% → 25.7% but bitrate still 2000K ⇒ **radio load unchanged. ⛔ frame rate NEVER hardcoded in ffmpeg — it comes from QGC via the conf.**
⚠️ **codex-work's last push used the plaintext PAT in its remote URL** ⇒ **#14 more urgent.** **UNDECIDED: "del mirror one" deferred — ask first.**

## [AUTONAV TUNING 08-01] → **project_rover_autonav.md TOP SECTION has the detail**
✅ `/odom`-at-rest (`bee3abe`) · ✅ **`erpm_to_ms` 0.000380→0.004633 (12.2× low!)** (`42f9aa2`) · ✅ speed loop re-validated armed
✅ **`RO_YAW_RATE_P` 2.0→0.05 + `RO_YAW_RATE_LIM` 1.57→0.5, `param save`d.** ⚠️ **re-read after any FC reboot; 2.0 = runaway.** `RO_YAW_RATE_LIM` clamps the SETPOINT only — **not protection.**
📋 **MEASURE FIRST:** `RO_MAX_THR_SPEED` 3.0 likely ~2× low; it normalises the FF in BOTH speed and rate control. ~50% stick outdoors, then revisit `RO_SPEED_P/I`.
⏭ **YAW PARKED → OUTDOOR 08-02.** Needs ~23-46°, NOT a 360. **Discriminator on `steering/setpoint`: ≈0.102 = OPEN loop (no gain fixes it) vs ≈0.052 = CLOSED.** ⚠️ NO yaw evidence yet — the "OPEN LOOP" print was a degenerate sp=0 case.
⚠️ **Depth cam sees only 92° — 268° incl. the rear is UNMEASURABLE. Never clear a spin from `/scan`.**

## [TODOS] → memory/todos.md (full detail + commands)
**🔴🔴 AUTONAV IS THE ACTIVE PRIORITY (user, 08-01 — supersedes the 07-31 WFB priority). NEXT = 🔴 #20 yaw-rate runaway**, then L5. #21 gyro-yaw odom open. **[OUTDOOR = PRIMARY TARGET] O1-O5:** STL-19 · DroneCAN GPS · lidar SLAM · GPS-waypoint Nav2 · outdoor safety
**WFB parked (not closed): #22 = the #1 WFB action, a HARDWARE job — reseat drone NIC-A ant0 antenna, re-measure on 8102.** W0-W6 closed. Then re-measure uplink, then test co-located desense.
1. Relay clock via local NTP · 2. ✅ onboard Wi-Fi GONE 🔴 **NO onboard fallback — recovery is WFB → relay:2222 ONLY** · 14. 🔴 **Rotate the GitHub PAT + move codex-work to SSH**
3+4+24. ❌ **ALL THREE DELETED — do not re-propose.** GS `rx_ring_size`, GS TX power (maxed 30 dBm), trim PX4 MAVLink rates (airtime-only).
5+7+8+9+10. Antenna tracker HW (relay :14551) · /scan → obstacle_distance/Nav2 · #17 delete camera_sw_node_obsolute.py · Multicam Phase D · vision: backoff reset on STALL, pin `6-2/power/control` `on`, `--bitrate`
23. ✅ **Throughput-floor watchdog LIVE** (`a5fb348`). **⛔ do NOT modify the ffmpeg command line** (`vision_streaming_node.py` ~176-207): `-g 30`/`-tune zerolatency`/`-pkt_size 1400` VETOED.
25. ✅ **rc_control retry storm FIXED** (`9893d6b`): latches the ATTEMPT, 3 retries+backoff, off-thread, give-up logged once, cycle the switch to re-try. 🔴 **still keys `/dev/video0` — real close-out is Phase D/#8 → usbcam ids.**

## [AI_STACK]
online: claude CLI → Claude API | offline: Ollama phi3:mini (~3 tok/s) | `ai` auto-routes | SSH login: b+Enter=bash | Enter/4s+internet=Claude | no internet=Phi-3

## [SENSORS]
TFmini: ttyAMA2 down 0.3-12m 50Hz → distance_sensor | VL53L1X: I2C 0x29 front 20-400cm 10Hz → obstacle_distance | OptFlow: Farneback 10Hz → sensor_optical_flow (manual)
STL-19: ttyAMA3 360° 0.02-25m ~10Hz — **PRIMARY-TARGET SENSOR**; with another team; on re-integration **lidar OWNS `/scan`** (remap depth→`/scan_depth`)
Cameras (**both FPV-capable, both proven on port 6-2; swap from QGC only**) — **See3CAM_CU135** `usbcam-2560c1d1-241D8306-i00` (100mA): real **60 fps** 720p MJPG. **LG Smart Cam** `usbcam-30c9009d-01.00.00-i00` (500mA): **30 fps**, cheaper on CPU, **currently the FPV cam**. | **Orbbec Gemini 336L** = autonomy-only, `usbcam-2bc50807-CPC7B53000AB-i04` (USB3 on BOX-B, ROS2 wrapper only, never ffmpeg); depth 848×480@30 configured but delivers ~15 Hz; min valid depth 0.308 m
**Three camera rules:** (1) **NEVER key a camera by `/dev/videoN` or by-id** — only `usbcam-<vidpid>-<serial>-i<iface>`. (2) **NEVER record resolution/fps/bitrate as fact** — operator-set from QGC; read the conf live. (3) **Orbbec video nodes appear/vanish with `rover-camera.service`**; renumbering also from the Pi5's own `rpivid`/`pispbe-*` nodes

## [AUTONOMY_ROADMAP] — **DECISION 08-01: STL-19 → the DRONE. Rover runs CAMERA-ONLY.** → project_autonomy_plan_reframe.md
🔴 **Mapping is NOT hardware-blocked.** `slam_toolbox` needs 360° (2D scan matching, 92° = too little overlap) but **RTAB-Map RGB-D visual SLAM is designed for this camera** — narrow forward FOV is its normal case, closes loops by *recognising places*. ⇒ **swap the ALGORITHM, not the sensor.** Blocked on config + CPU.
📊 Depth cam wins the axes cited: **~7× finer angular res, ~900× the points, 60.7° vertical FOV vs ZERO.** Lidar wins only horizontal FOV (360 vs 92) and range (25 vs ~3 m). **Proven 08-01: same instant, 2D `/scan` said 1.442 m clear, `/scan_3d` said 0.254 m.**
⚠️ **PERMANENT DESIGN CONSTRAINTS now, not gaps:** no rear/side coverage ⇒ **"never reverse into unseen space" is permanent**; **never clear a spin from any `/scan`**; ~3 m range costs map quality in big rooms even with RTAB-Map. **A 2nd STL-19 removes the choice.**
⏭ **O1 REMOVED from the rover ladder** (reassigned to the drone); the lidar-owns-`/scan` remap is PARKED. **Order: 🔴#20 yaw → RTAB-Map + CPU budget → map the home → localization → Nav2 goals.** Yaw gates everything: mapping is nothing but driving and turning.

> `docs/roadmap.md` (07-23) vs **`docs/autonomy_plan.md` (08-01, NEWER, outcome re-cut: L0 ✅ · L1 🔧 · L2-L5 NOT STARTED)** — **different L-numbers, don't mix the schemes.** 🔴 **Q1 "where am I?" IS THE WALL.** PX4 RTL has NO obstacle avoidance here — return-to-base must be BUILT. **Depth cam + lidar are COMPLEMENTARY: a lidar-only rover drives under a table.** Pending hw: DroneCAN GPS.
## [GCS_INTERFACE] → reference_gcs_companion_interface.md
G-Control.exe → pxlabs_cli.exe → SSH relay:2222 → companion:22 (relay always in middle) | binaries: vision_config_manager (camera), Rozcam (capture); sudo via printf|sudo -S | QGC source: github.com/ArvinVeiyon/PXLABS_qgroundcontrol, branch PXLABS-integration

## [TROUBLESHOOTING]
no_MAVLink: ttyAMA0 baud/wiring + PX4 MAVLink instance | no_DDS: microxrce-agent.service, ttyAMA4, PX4 XRCE param | WFB_down: wifibroadcast@drone.service, wlx* adapter, /etc/drone.key | offline_AI: ollama.service + `ollama list`
no_video: vision_streaming.service + /etc/vision_streaming.conf → then **[VIDEO_FAULTS] (check (B) latch FIRST)** | no_scan/no_cloud: **check the half-dead camera restart first** → [SERVICES]
