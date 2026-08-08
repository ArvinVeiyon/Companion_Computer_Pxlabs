# Vind-Roz Platform Memory
> Auto-loaded each session; also the Phi-3 offline system prompt. Live: ~/.claude/projects/-home-roz/memory/ | Backup: ~/codex-work/memory/ → GitHub ArvinVeiyon/Companion_Computer_Pxlabs
> ⚠️ **BACKUP IS MANUAL:** `cp -p ~/.claude/projects/-home-roz/memory/*.md ~/codex-work/memory/` + git push. **Never `rsync --delete`** — the mirror is a UNION of two scopes; the 2nd (`-home-roz-codex-work`) is NOT auto-loaded, check it after any codex-work session.
> ⚠️ **KEEP UNDER 125 LINES / 17 KB.** One line per entry; detail belongs in the topic files.

## [MEMORY_FILES]
**feedback (RULES) — READ THE FILE, these are one-line reminders:** `test_before_concluding` 🔴 **never publish a number I didn't measure; "validated" ≠ "works", RUN the real consumer; settle ambiguity by one-directional MECHANISM; label claims measured/source/recalled/assumed; record whether a decision was the OPERATOR'S or MY recommendation they accepted** · `check_docs_before_measuring` 🔴 **grep the whole memory dir + `docs/` BEFORE deriving a dimension; the operator's ID of their own hardware beats my inference** · `eliminate_hypothesis_whole_family` 🔴 **dump EVERY candidate param in ONE command before saying "not the cause"; name the CONSUMER; a real gap ≠ a significant one** · `crash_recovery_checkpoint` (**per FINDING**) · `use_dds_not_mavlink` · `camera_qgc_only` · `dkms_arch` · `wlan0_persistent_name`
**reference:** `px4_vio_collision` (🔴 **PX4 collision-prevention is MC-ONLY, dead on a rover; no PX4 path planner. `EKF2_EV_CTRL` is a BITMASK — ours=4=velocity-only, so Q1 is unsolved by SETTING, not by capability; `=9` (pos+yaw) is the fix**) · `wfb_ng` · `wfb_rlyctl` · `wfb_cfg_apply` · `uart_map` · `services` · `known_fixes_archive` · `gcs_companion_interface` · `todos.md` · `ros2_nodes`/`ros2_topics` · `rover_odometry`
**project — ACTIVE:** `indoor_mapping_slam` (✅ **MAP DONE 08-08 `~/house_map_v2`, map_server-verified; `Grid/RayTracing:=true` was THE fix. ⚠️ rtabmap `-g2` pgm = 89/178/0 unk/free/occ, NOT Nav2's 205/254/0. Old `house_map.pgm` STILL FALSE**) · `rover_autonav` (**🔴 YAW RUNAWAY ~21×, ⛔ no armed yaw tests; ALL pre-08-01 speeds read 12.2× LOW**) · `perception_3d_costmap` (**reflex NOT switched**) · `autonomy_plan_reframe` (**Q1 localization = THE WALL**) · `rc_control_camera_retry_storm` (**FIXED `9893d6b` — WAS the "runaway" blamed twice on a stray process**)
**project — other:** `l4_gemini_nav2_prereqs` · `vision_multicam_upgrade` (Phase D remains) · `l2_floortest_wheel0_reversed` · `wfb_undervoltage_dead_nic` (**DON'T raise the pot / set usb_max_current_enable=1**) · `external_wifi_uplink` · `gcs_link_degraded` · `relay_ntp_setup` · `relay2_relaystn` (Pi4 brownout; fix = powered hub) · `companion_network_degraded` · `boxb_pcie_usb` · `codexrelay_divergence` · `codexwork_token_in_remote` (🔴 **plaintext PAT in origin URL**) · `codexwork_branches` (**auto-sync does NOT git-add NEW files**)

## [VIDEO_FAULTS] → **FULL RECORD: `~/ros2_ws/docs/vision_streaming.md`**
**(B) 🔴 CPU-STARVATION LATCH — CHECK FIRST.** ffmpeg loses a CPU race and **never recovers** (7-28 pkt/s vs 208), service "active", logs silent. **A restart does NOT clear it. FIX: briefly `systemctl stop rover-camera rover-scan rover-odometry`.** **(A) CAMERA WEDGE looks identical** — ⛔ **no software recovery exists**; only physical VBUS removal clears it.
⛔ **Do NOT modify the ffmpeg command line** (vetoed) · ⛔ **never hardcode frame rate; the `fps` conf key is INERT** · **never record resolution/fps/bitrate as fact — read them live.**

## [IDENTITY]
Claude Code CLI + onboard AI for the Vind-Roz drone/rover platform | user: roz / ArvinVeiyon | goal: develop, maintain, autonomize this platform

## [PLATFORM]
Vind-Roz: aerial drone + ground rover, same RPi5 companion, different PX4 airframe | RPi5 BCM2712 4-core 8GB | Ubuntu 24.04.1 aarch64, kernel 6.8.0-1048-raspi, host `Vind-Roz`
⚠️ **Boot clock is WRONG until NTP steps it.** ⚠️ **Only 4 cores; rover stack + x264 oversubscribe them** → [VIDEO_FAULTS] (B). ⚠️ **No rate/CPU number here is trustworthy without `ps -eo pid,pcpu --sort=-pcpu` first** — a "7.5 Hz cloud" was a runaway at 72.7%; my own `claude` process hit 130% and skewed a 08-08 baseline.

## [FLIGHT_CONTROLLER]
Custom Pixhawk 6X-RT (in-house PCB, NOT Holybro) | NXP i.MX RT1176 M7+M4 | PX4 **pxlabs-v1.17.0-2.0.0** a52c38b07d, px4_fmu-v6xrt (⚠️ local ~/PX4-Autopilot is an upstream clone, NOT the fw source)

UARTs (→reference_uart_map.md): AMA0=MAVLink 921600 | AMA2=TFmini 115200 | AMA3=STL19 230400 (off) | AMA4=DDS 921600 | AMA1 free

## [SOFTWARE_VERSIONS]
ROS2 Jazzy | Python 3.12.3 | Ollama v0.17.7/phi3:mini | AIDE 0.18.6 | wfb-ng 1b88185 | mavlink-router c20337b | MicroXRCEAgent v3.0.0-2 | px4-ros2-interface-lib release/1.17 | Orbbec SDK 2.9.3 | RTAB-Map 0.22 | ~/PX4-Autopilot: remote `pxlabs`, branch `pxlabs-fw`=a52c38b (**the real FC fw source**)
⚠️ **Pi 5 has NO hardware H.264 encoder** (`rpivid` is decode-only) — all H.264 is software x264. GStreamer is no faster; stay with ffmpeg.

## [SERVICES] → reference_services.md
core: mavlink.router | microxrce-agent | rc_control_node | vision_streaming | block-traffic | wifibroadcast@drone | system_files_sync.timer | ollama
**AIDE timer DISABLED** (~3.5h/day of a core). **tfmini DISABLED — ⚠️ MUST `systemctl enable --now tfmini` for the DRONE airframe.**
autonav: rover-camera | rover-scan | rover-scan-3d | rover-odometry | rover-autonav-mode — active; **rover-ekf-bridge installed but DISABLED on purpose** (wheels-up limit-cycle hazard). ⚠️ **it already uses `LocalPositionMeasurementInterface`, velocity-only — the Q1 hook is half-built.**
**⚡ FPV video costs `/scan` 28.4→22.3 Hz.** **🔴 `/odom` CAN DIE AT REST — ESC doze, NOT CPU; INTERMITTENT (fine on 08-08).** ⚠️ `/odom` is RELIABLE QoS — a BEST_EFFORT subscriber reads 0 and mimics this exactly.
🔴 **A CAMERA RESTART CAN COME UP HALF-DEAD** — "active", params answering, **but depth & colour never started, no error logged**. A 2nd restart fixed it. **VERIFY EVERY restart:** `journalctl -u rover-camera --since -1min | grep "depth Frame - Width"` (absent = half-dead) **AND a topic rate. `systemctl is-active` does NOT catch it.**

## [PERCEPTION] → **project_perception_3d_costmap.md · 📗 `docs/rover_geometry.md` = THE authority on EVERY dimension + the camera mount; READ IT BEFORE deriving geometry**
✅ Cloud rate fixed (`point_cloud_decimation_filter_factor:=3`). ⚠️ **`ros2 param set` does NOTHING — the live lever is the SERVICE `/camera/set_point_cloud_decimation`.** `cloud_to_scan` = `rover-scan-3d.service`, PARALLEL: **`/scan_3d`, not `/scan`, and NO TF** ⇒ **⛔ NEVER repoint `rover-scan.service` at it** (it alone gives `base_link->camera_link`).
✅ **FAIL-OPEN CLOSED** (`3f74af4`, `ca81d2a`): `range_min` 0.31 + per-ray rectangular footprint reject. **Radial cuts can't express a rectangular body; a dropped ray = INFINITE clearance.** ⚠️ **`/scan_3d` CONTAINS THE TOP PLATE by design — every consumer must reject its own footprint.**
**CAMERA STAYS CENTRED (08-08)** — keeps the 0.300 m min-range circle **45 mm BEHIND the bumper = no blind strip**; moving it breaks `cam_x=0` + invalidates `front_overhang`/TF (`rover_geometry.md` §4). ⚠️ **MY recommendation the operator accepted, NOT their own preference; REOPEN if its (DERIVED) basis falls.**
✅ Height band at ONE spot: RANSAC floor ⇒ tilt **+0.37°**. 🔑 **percentiles DO NOT WORK — p5/p50 give OPPOSITE wrong answers. ALWAYS RANSAC the plane.**
✅ **VL53L1X SUPERSEDED** (dead code, retire with #17 + `collision_manual_mode` — it targeted PX4 Manual, but **everything is AutoNav-only**). ⚠️ the reflex is in `autonav_mode`'s executor ⇒ **not independent of the companion**; perception loss fails SAFE.
✅ **REFLEX UNGATED 08-08 — the "unexplained cluster" was A RACK the operator parked facing, not the rover.** 480 replay nodes: **plate 18.1% vs cluster 0.6%** ⇒ not body-fixed. 🔑 **operator's ID of their own hardware beats my inference.**

## [WFB_NG] → reference_wfb_ng.md
ch161 5GHz | drone-wfb@10.5.5.87 ↔ gs-wfb@10.5.5.77 | keys /etc/{drone,gs}.key | multi-adapter TX via fwmark+tc
**`wifibroadcast@` restart prints `rtw_mlmeext_disconnect` WARN + trace 2×. BENIGN — don't patch the driver.**
**Drone TX is flawless. When video breaks WFB's input queue is EMPTY — suspect the source.** Stats: TCP `127.0.0.1:8102` (GS 8103), JSON; NOT the `wfb-cli` TUI. **⚡ 07-31 uplink loses 13.57% mavlink; ROOT CAUSE = drone NIC-A ant0 20 dB deaf (−48.5 vs −28.3 dBm) ⇒ reseat it.**
⚠️ **METHOD (cost a week):** compare payload `tx.incoming`→`rx.out` across 8102/8103. **Never `rx.all`** (double-counts 4 antennas). **Never infer radio health from MAVLink rates at `tcp:5760`.**

## [RELAY_STATION]
vind-rly | RPi5 | `ssh vind-admin@10.5.5.77` (**sudo NEEDS A PASSWORD ⇒ journalctl of other units gives "No entries"**) | ~/codex-relay | tunnel 2222→drone :22 | NO RTC
svcs: wifibroadcast@gs, mavlink.router, ssh-tunnel-to-companion, relay_files_sync.timer | wfb standalone (CURRENT) vs cluster (+CPE610, unconnected)
**Wi-Fi Direct P2P-GO `p2p-wlan0-0`, SSID `vind_rely`, ch149, 10.5.6.101/24 → QGC 10.5.6.50**

## [REPOS]
codex-work: ~/codex-work → Companion_Computer_Pxlabs, branch master (origin/main stale) | codex-relay: ~/codex-relay on vind-rly → Relay_Station_Pxlabs | ros2_ws: ~/ros2_ws, main, `v1.2.0`

## [CURRENT STATE — 2026-08-08 14:00. NEVER ARMED. Operator repositioned the rover by hand]
All svcs active + DISARMED; `vision_streaming` stopped for the localization test then **RESTORED — operator confirmed video**. `rover-autonav-mode` restarted on the new binary (unchanged behaviour, still `/scan`). **`/odom` 100 Hz parked, `esc_online_flags:15` — did NOT doze today.** **Replays need `ROS_DOMAIN_ID=42`.** ros2_ws + memory PUSHED. **`~/house_map_v2.{pgm,yaml,db}` = THE map.** ⏭ resuming after 14:30.
⚠️ **`fps` is INERT — QGC's fps control does NOTHING**; resolution + bitrate DO work, but a 640x360 cut left bitrate at 2000K ⇒ **radio load unchanged.**
⚠️ **codex-work's last push used the plaintext PAT in its remote URL** ⇒ **#14.** **UNDECIDED: "del mirror one" — ask first.**

## [AUTONAV TUNING] → **project_rover_autonav.md** (✅ `/odom`-at-rest `bee3abe`; ✅ `erpm_to_ms` 12.2× low, fixed `42f9aa2`; ✅ speed loop re-validated armed)
✅ **`RO_YAW_RATE_P` 2.0→0.05 + `RO_YAW_RATE_LIM` 1.57→0.5, saved.** ⚠️ **re-read after any FC reboot; 2.0 = runaway.** `RO_YAW_RATE_LIM` clamps the SETPOINT only — **not protection.** 📋 `RO_MAX_THR_SPEED` 3.0 likely ~2× low — MEASURE first; it normalises the FF in BOTH loops.
⏭ **#20 is UNVALIDATED, not known-broken** — the 21× is a PRE-fix number and nothing re-measured it. ⚠️ no yaw evidence yet. **Depth cam sees 92°; the other 268° is UNMEASURABLE.** ⚠️ **can't read PX4 params over DDS — ask the operator to check `RO_YAW_RATE_P`(0.05), `RO_YAW_RATE_LIM`(0.5), `RO_MAX_THR_SPEED` in QGC.**

## [TODOS] → memory/todos.md (full detail + commands)
**🔴🔴 AUTONAV IS THE ACTIVE PRIORITY. NEXT = S1 kill test → 🔴 #20 yaw (INDOORS, see [AUTONOMY_ROADMAP]) — #20 gates the operator's WHOLE ladder.** #21 gyro-yaw open. **[OUTDOOR] O1-O5:** STL-19 · DroneCAN GPS · lidar SLAM · GPS Nav2 · outdoor safety. **WFB parked: #22 = HARDWARE, reseat drone NIC-A ant0.**
1. Relay NTP · 2. 🔴 **NO onboard Wi-Fi fallback — recovery is WFB → relay:2222 ONLY** · 14. 🔴 **Rotate the GitHub PAT, move codex-work to SSH**
3+4+24. ❌ **DELETED, don't re-propose:** GS `rx_ring_size`, GS TX power (maxed), trim PX4 MAVLink rates.
5+7+8+9+10. Antenna tracker HW · /scan → Nav2 · #17 delete camera_sw_node_obsolute.py (+`rov_collision_stop`, `collision_manual_mode`) · Multicam Phase D
23. ✅ watchdog LIVE (`a5fb348`). 25. ✅ rc_control retry storm FIXED, 🔴 **but still keys `/dev/video0` — close out via Phase D/#8 → usbcam ids.**
26. ✅ localization → `house_map_v2.db` + `RGBD/CreateOccupancyGrid:false`. ✅ **FITS: 27.5% of a core, 80 ms/cycle @2 Hz, `map->odom` published** (parked = a FLOOR). 🔴 **ABORTS on a ONE-FRAME 1280×800 depth glitch (confirmed by monitor) — FATAL. Gates 2A/2B.**
28. 🔴 **CAMERA IS STILL IN MAPPING CONFIG (`depth_fps:=15`) — the drop-in says REVERT BEFORE ANY AUTONOMOUS DRIVING; it halves `/scan` and the reflex rate. THIS is why `/scan` reads ~15 Hz, not load.**
27. ⏭ **Reflex `/scan_3d`: now a PARAM (`collision.scan_topic`), default still `/scan`.** `/scan_3d` is 12× steadier close-in (6 vs 74 mm spread), agrees to 8 mm at 1.34 m. **Needs ONE low/overhanging object that `/scan` misses before flipping.**

## [AI_STACK]
online: claude CLI → Claude API | offline: Ollama phi3:mini (~3 tok/s) | `ai` auto-routes | SSH login: b+Enter=bash | Enter/4s = Claude if online, else Phi-3

## [SENSORS]
TFmini: ttyAMA2 down 0.3-12m 50Hz → distance_sensor | VL53L1X + OptFlow: dead code, see [PERCEPTION]
STL-19: ttyAMA3 360° ~10Hz — **DRONE-bound**, with another team; on re-integration **lidar OWNS `/scan`** (remap depth→`/scan_depth`)
Cameras (**both FPV-capable, proven on port 6-2; swap from QGC only**) — **See3CAM_CU135** `usbcam-2560c1d1-241D8306-i00`: 60 fps 720p MJPG. **LG Smart Cam** `usbcam-30c9009d-01.00.00-i00`: 30 fps, cheaper CPU, **currently the FPV cam**. | **Orbbec Gemini 336L** = autonomy-only, `usbcam-2bc50807-CPC7B53000AB-i04` (USB3 on BOX-B, ROS2 wrapper only, **never ffmpeg**); min valid depth 0.308 m
**Three camera rules:** (1) **NEVER key a camera by `/dev/videoN` or by-id** — only `usbcam-<vidpid>-<serial>-i<iface>`. (2) **NEVER record resolution/fps/bitrate as fact** — read the conf live. (3) **Orbbec video nodes appear/vanish with `rover-camera.service`**; renumbering also from the Pi5's own `rpivid`/`pispbe-*` nodes

## [AUTONOMY_ROADMAP] — **DECISION: STL-19 → the DRONE. Rover = camera-only.** → project_autonomy_plan_reframe.md
🔑 **PX4 MANUAL BYPASSES THE YAW RATE LOOP** (fw-verified: `manual()` publishes STEERING, only `acro()` a RATE setpoint) ⇒ mapping drives are NOT yaw-gated, **but the reflex doesn't run there either — the operator is the only safety layer.** ⚠️ **AutoNav publishes `RoverSpeedRateSetpointType` (speed + RATE) ⇒ #20 gates EVERY AutoNav task, including plain guarded driving.**
📦 **OFFLINE: record on the Pi → map on a LAPTOP → localize on the Pi** (✅ localization measured, FITS). ⚠️ live-streaming RGB-D is NOT viable — `image_transport` has **only `raw_pub`** ⇒ ~100 vs 13 Mbit/s. 🔴 SD write ceiling 27.4 MB/s.
📊 **NO VIO EXISTS, don't build one** (verified 08-08): `rgbd_odometry` is installed but launched nowhere and costs 79.6% of a core; the 336L's `/camera/{gyro,accel}/sample` are live but unfused/unrecorded/uncalibrated; `/odom` is WHEEL odom from ESC eRPM. **Wheel beat visual 60 vs 4-5 closures** — RTAB-Map localizes by *place recognition*; odom only bridges between them. 🔑 **the camera gyro IS an independent inertial yaw-rate source for #20 — PX4's `vehicle_angular_velocity` is NOT bridged over DDS.**
🔴 **Mapping is NOT hardware-blocked:** `slam_toolbox` needs 360°, but **RTAB-Map RGB-D is built for a narrow forward FOV** and closes loops by *recognising places*. **Swap the ALGORITHM, not the sensor.** ⚠️ 92° is the whole RGB-D class, not a 336L weakness.
⚠️ **PERMANENT (camera-only):** no rear/side coverage ⇒ **"never reverse into unseen space"**; **never clear a spin from any `/scan`**. 🔴 **Nav2's default spin + back-up recoveries must stay DELETED** — exactly the two moves this rover cannot clear.
⏭ **MAPPING → `project_indoor_mapping_slam.md`. ✅ MAP DELIVERED + localization MEASURED 08-08.** Next = Q1 via `EKF2_EV_CTRL=9` fed by the **px4_ros2 Navigation Interface** (`LocalPositionMeasurementInterface`; `rover_ekf_bridge` ALREADY uses it, velocity-only; **experimental per PX4 docs**).
🔑 **#20 IS TESTABLE INDOORS** — pure rotation, worst-case corner radius 0.446 m ⇒ a ~1.2 m cleared circle, and only 23-46° needed. Signals: `/cmd_vel` in · **`/fmu/out/rover_steering_setpoint`** (≈0.102 open vs ≈0.052 closed) · **`/camera/gyro/sample`** (true inertial rate) · `/odom` angular.z (slip by difference). ⚠️ **S1 kill-switch-in-AutoNav is UNTESTED and must go first.** Prediction: if the 21× was pure P error, a 40× gain cut should now leave it turning ~HALF of commanded.
> `docs/roadmap.md` (07-23) vs **`docs/autonomy_plan.md` (08-01, NEWER)** — **different L-numbers, don't mix them.** 🔴 **Q1 "where am I?" IS THE WALL.** PX4 RTL has NO obstacle avoidance here. Pending hw: DroneCAN GPS.

## [GCS_INTERFACE] → reference_gcs_companion_interface.md
G-Control.exe → pxlabs_cli.exe → SSH relay:2222 → companion:22 (relay always in middle) | QGC: github.com/ArvinVeiyon/PXLABS_qgroundcontrol @ PXLABS-integration

## [TROUBLESHOOTING]
no_MAVLink: ttyAMA0 + PX4 MAVLink instance | no_DDS: microxrce-agent, ttyAMA4, XRCE param | WFB_down: wifibroadcast@drone, wlx*, /etc/drone.key | no_video: vision_streaming + its conf → **[VIDEO_FAULTS], (B) latch FIRST** | no_scan/no_cloud: **half-dead camera restart first**
