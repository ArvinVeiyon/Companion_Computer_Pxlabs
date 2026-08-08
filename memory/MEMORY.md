# Vind-Roz Platform Memory
> Auto-loaded each session; also the Phi-3 offline system prompt. Live: ~/.claude/projects/-home-roz/memory/ | Backup: ~/codex-work/memory/ → GitHub ArvinVeiyon/Companion_Computer_Pxlabs
> ⚠️ **BACKUP IS MANUAL:** `cp -p ~/.claude/projects/-home-roz/memory/*.md ~/codex-work/memory/` + git push. **Never `rsync --delete`** — the mirror is a UNION of two scopes; the 2nd (`-home-roz-codex-work`) is NOT auto-loaded, check it after any codex-work session.
> ⚠️ **KEEP UNDER 125 LINES / 17 KB.** One line per entry; detail belongs in the topic files.

## [MEMORY_FILES]
**feedback (RULES) — READ THE FILE:** `test_before_concluding` 🔴 **never publish a number I didn't measure; "validated" ≠ "works", RUN the real consumer; settle ambiguity by one-directional MECHANISM; label claims measured/source/recalled/assumed; record whether a decision was the OPERATOR'S or MY recommendation they accepted** · `check_docs_before_measuring` 🔴 **grep the memory dir + `docs/` BEFORE deriving a dimension; the operator's ID of their own hardware beats my inference** · `eliminate_hypothesis_whole_family` 🔴 **dump EVERY candidate in ONE command before saying "not the cause"; name the CONSUMER** · `crash_recovery_checkpoint` (per FINDING) · `use_dds_not_mavlink` · `camera_qgc_only` · `dkms_arch` · `wlan0_persistent_name`
**reference:** `px4_vio_collision` (🔴 **PX4 collision-prevention is MC-ONLY, dead on a rover; no PX4 path planner. `EKF2_EV_CTRL` is a BITMASK — ours=4=velocity-only ⇒ Q1 unsolved by SETTING, not capability; `=9` (pos+yaw) is the fix**) · `wfb_ng` · `wfb_rlyctl` · `wfb_cfg_apply` · `uart_map` · `services` · `known_fixes_archive` · `gcs_companion_interface` · `todos.md` · `ros2_nodes`/`ros2_topics` · `rover_odometry`
**project — ACTIVE:** `indoor_mapping_slam` (✅ MAP `~/house_map_v2`; ⚠️ rtabmap `-g2` pgm = 89/178/0, NOT Nav2's 205/254/0; old `house_map.pgm` STILL FALSE; 🔴 **§11-12 = the #26 fix + localization never relocalizing**) · `rover_autonav` (**⛔ no armed yaw tests without re-reading the tune; ALL pre-08-01 speeds read 12.2× LOW**) · `perception_3d_costmap` (reflex NOT switched) · `autonomy_plan_reframe` (**Q1 = THE WALL**) · `rc_control_camera_retry_storm` (FIXED)
**project — other:** `l4_gemini_nav2_prereqs` · `vision_multicam_upgrade` · `l2_floortest_wheel0_reversed` · `wfb_undervoltage_dead_nic` (**DON'T raise the pot / usb_max_current_enable**) · `external_wifi_uplink` · `gcs_link_degraded` · `relay_ntp_setup` · `relay2_relaystn` (Pi4 brownout ⇒ powered hub) · `companion_network_degraded` · `boxb_pcie_usb` · `codexrelay_divergence` · `codexwork_token_in_remote` (🔴 **plaintext PAT**) · `codexwork_branches` (**auto-sync does NOT git-add NEW files**)

## [VIDEO_FAULTS] → **FULL RECORD: `~/ros2_ws/docs/vision_streaming.md`**
**(B) 🔴 CPU-STARVATION LATCH — CHECK FIRST.** ffmpeg loses a CPU race and **never recovers** (7-28 pkt/s vs 208), service "active", logs silent. **A restart does NOT clear it. FIX: briefly `systemctl stop rover-camera rover-scan rover-odometry`.** **(A) CAMERA WEDGE is identical-looking** — ⛔ **no software recovery**; only physical VBUS removal.
⛔ **Do NOT modify the ffmpeg command line** (vetoed) · ⛔ **never hardcode frame rate; the `fps` conf key is INERT** · **never record resolution/fps/bitrate as fact — read them live.**

## [PLATFORM]
Vind-Roz: aerial drone + ground rover, same RPi5 companion, different PX4 airframe | RPi5 BCM2712 4-core 8GB | Ubuntu 24.04.1 aarch64, kernel 6.8.0-1048-raspi, host `Vind-Roz`
⚠️ **Boot clock is WRONG until NTP steps it** — `uptime -s`/`who -b`/unit stamps disagree across a boot; don't correlate journals across one. ⚠️ **No rate/CPU number is trustworthy without `ps -eo pid,pcpu --sort=-pcpu` first** — a "7.5 Hz cloud" was a runaway at 72.7%; my own `claude` once hit 130% and skewed a baseline.

## [FLIGHT_CONTROLLER]
Custom Pixhawk 6X-RT (in-house PCB, NOT Holybro) | NXP i.MX RT1176 M7+M4 | PX4 **pxlabs-v1.17.0-2.0.0** a52c38b07d, px4_fmu-v6xrt

UARTs (→reference_uart_map.md): AMA0=MAVLink 921600 | AMA2=TFmini 115200 | AMA3=STL19 230400 (off) | AMA4=DDS 921600 | AMA1 free

## [SOFTWARE_VERSIONS]  (AI: claude CLI → API online, Ollama phi3:mini offline ~3 tok/s, `ai` auto-routes; SSH login b+Enter=bash, Enter/4s = Claude if online else Phi-3)
ROS2 Jazzy | Python 3.12.3 | Ollama v0.17.7/phi3:mini | AIDE 0.18.6 | wfb-ng 1b88185 | mavlink-router c20337b | MicroXRCEAgent v3.0.0-2 | px4-ros2-interface-lib release/1.17 | Orbbec SDK 2.9.3 | RTAB-Map 0.22 | ~/PX4-Autopilot: remote `pxlabs`, branch `pxlabs-fw`=a52c38b (**the real FC fw source**)
⚠️ **Pi 5 has NO H.264 encoder** (`rpivid` decode-only) — all H.264 is software x264; GStreamer no faster. GPU dead end: see [CURRENT STATE].

## [SERVICES] → reference_services.md
core: mavlink.router | microxrce-agent | rc_control_node | vision_streaming | block-traffic | wifibroadcast@drone | system_files_sync.timer | ollama · autonav: rover-camera | rover-scan | rover-scan-3d | rover-odometry | rover-autonav-mode
**AIDE timer DISABLED** (~3.5h/day of a core). **tfmini DISABLED — ⚠️ MUST `systemctl enable --now tfmini` for the DRONE.** **rover-ekf-bridge installed but DISABLED on purpose** (wheels-up limit-cycle hazard); it already uses `LocalPositionMeasurementInterface`, velocity-only — **the Q1 hook is half-built.**
**⚡ FPV video costs `/scan` 28.4→22.3 Hz.** **🔴 `/odom` CAN DIE AT REST — ESC doze, NOT CPU; INTERMITTENT.** ⚠️ `/odom` is RELIABLE QoS — a BEST_EFFORT subscriber reads 0 and mimics this exactly.
🔴 **A CAMERA RESTART CAN COME UP HALF-DEAD** — "active", params answering, **depth & colour never started, nothing logged**; a 2nd restart fixed it. **`systemctl is-active` does NOT catch it** ⇒ **verify every restart with `python3 ~/ros2_ws/tools/camera_restart_check.py`.**

## [PERCEPTION] → **project_perception_3d_costmap.md · 📗 `docs/rover_geometry.md` = THE authority on EVERY dimension + the camera mount; READ IT BEFORE deriving geometry**
✅ Cloud rate fixed (`point_cloud_decimation_filter_factor:=3`). ⚠️ **`ros2 param set` does NOTHING — the live lever is the SERVICE `/camera/set_point_cloud_decimation`.** `cloud_to_scan` = `rover-scan-3d.service`, PARALLEL: **`/scan_3d`, not `/scan`, and NO TF** ⇒ **⛔ NEVER repoint `rover-scan.service` at it** (it alone gives `base_link->camera_link`).
✅ **FAIL-OPEN CLOSED** (`3f74af4`, `ca81d2a`): `range_min` 0.31 + per-ray rectangular footprint reject. **Radial cuts can't express a rectangular body; a dropped ray = INFINITE clearance.** ⚠️ **`/scan_3d` CONTAINS THE TOP PLATE by design — every consumer must reject its own footprint.**
**CAMERA STAYS CENTRED** — keeps the 0.300 m min-range circle 45 mm BEHIND the bumper = no blind strip; moving it breaks `cam_x=0` + `front_overhang`/TF. ⚠️ **MY recommendation the operator accepted; REOPEN if its DERIVED basis falls.**
🔑 **Tilt +0.37° by RANSAC — percentiles DO NOT WORK (p5/p50 give OPPOSITE wrong answers). ALWAYS RANSAC the plane.**
✅ VL53L1X SUPERSEDED (dead code; retire with #17 + `collision_manual_mode` — all AutoNav-only). ⚠️ the reflex lives in `autonav_mode`'s executor ⇒ **not independent of the companion**; perception loss fails SAFE.
✅ **REFLEX UNGATED — the "unexplained cluster" was A RACK the operator parked facing** (plate 18.1% vs cluster 0.6% over 480 nodes ⇒ not body-fixed). 🔑 **operator's ID of their own hardware beats my inference.**

## [WFB_NG] → reference_wfb_ng.md (**PARKED — only action left is HW: reseat drone NIC-A ant0**)
ch161 5GHz | drone-wfb@10.5.5.87 ↔ gs-wfb@10.5.5.77 | keys /etc/{drone,gs}.key | multi-adapter TX fwmark+tc | **Drone TX is flawless. When video breaks WFB's input queue is EMPTY — SUSPECT THE SOURCE.** Stats: TCP `127.0.0.1:8102` (GS 8103) JSON, **not** `wfb-cli`. **⚡ uplink loses 13.57% mavlink ⇒ NIC-A ant0 is 20 dB deaf (−48.5 vs −28.3).** `wifibroadcast@` restart's `rtw_mlmeext_disconnect` WARN+trace is **BENIGN**.
⚠️ **METHOD (cost a week):** compare payload `tx.incoming`→`rx.out` across 8102/8103. **Never `rx.all`** (double-counts 4 antennas). **Never infer radio health from MAVLink rates at `tcp:5760`.**

## [RELAY_STATION]
vind-rly | RPi5 | `ssh vind-admin@10.5.5.77` (**sudo NEEDS A PASSWORD ⇒ journalctl of other units = "No entries"**) | ~/codex-relay | tunnel 2222→drone :22 | NO RTC | svcs: wifibroadcast@gs, mavlink.router, ssh-tunnel-to-companion, relay_files_sync.timer | wfb standalone (CURRENT) vs cluster (+CPE610, unconnected) | **Wi-Fi Direct P2P-GO `p2p-wlan0-0`, SSID `vind_rely`, ch149, 10.5.6.101/24 → QGC 10.5.6.50**

## [REPOS]
codex-work: ~/codex-work → Companion_Computer_Pxlabs, branch master (origin/main stale) | codex-relay: ~/codex-relay on vind-rly → Relay_Station_Pxlabs | ros2_ws: ~/ros2_ws, main, `v1.2.0`

## [CURRENT STATE — 2026-08-08 21:10. NEVER ARMED]
✅ **#26 fixed + #28 reverted.** Camera restart verified not half-dead. **rtabmap localization RUNNING since 17:25 — it RELOCALIZED at 17:39 and has been WAITING for a corroborating fix ever since (26b). Rover re-parked in the ROOM CENTRE; operator STOPPED vision_streaming 21:05.** ⏭ **NEXT: push the rover by hand a metre or two — wheel odom will accumulate and should complete the localization.**
⚠️ **sudo NEEDS the password** — `printf '1987\n' | sudo -S …` (operator's own documented method). ⚠️ **`fps` INERT in QGC**; resolution + bitrate work. **Replays need `ROS_DOMAIN_ID=42`; LIVE stack is domain 0.** ⚠️ codex-work push used the plaintext PAT ⇒ #14. **UNDECIDED: "del mirror one" — ask first.**
🖥 **Pi5 is NOT the bottleneck (measured): 5-41% idle, ~0% iowait, RAM 1.8/7.9 GB; everything heavy is ALREADY multi-threaded** (camera 41 threads, rtabmap 27, ffmpeg 19). ⛔ **NO GPU ENCODE EXISTS — `h264_v4l2m2m`="no valid device", `h264_vaapi`=no driver; card0=`v3d` (3D only). Headless changes NOTHING. Only real offload = a camera with ONBOARD H.264.**

## [AUTONAV TUNING] → **project_rover_autonav.md** (✅ `/odom`-at-rest `bee3abe`; ✅ `erpm_to_ms` 12.2× low, fixed `42f9aa2`; ✅ speed loop re-validated armed)
🏁 **#20 SOLVED 08-02 — FRICTION DEADBAND + INTEGRAL WINDUP, not a broken loop.** `yaw ≈ 7.6×(steer−0.40)`; **nothing below ~0.67 rad/s, design Nav2 for ~1.2 rad/s COARSE DISCRETE turns; ~2 s time constant.** 📗 **READ `docs/rover_yaw_response.md` BEFORE TOUCHING YAW.**
✅ **FINAL TUNE, re-read off the FC 08-08 16:20 and CORRECT:** `RO_YAW_RATE_P 0.08 · I 0.0 · CORR 1.8 · LIM 85.9 (⚠️ deg/s!) · RO_MAX_THR_SPEED 0.6 · RO_YAW_P 2.0 · RO_SPEED_LIM 0.70`. 🔴 **`I=0` is DELIBERATE — it is the windup source; never restore 0.1.** ⚠️ re-read after every FC reboot.
✅ **I CAN read/write PX4 params myself: `python3 ~/ros2_ws/tools/set_param.py NAME [value]`** (pymavlink over `tcp:5760`; refuses while armed). **Don't ask the operator to read QGC.** Params are absent from DDS only.
⏭ Remaining yaw work is **OUTDOOR**: 4 s holds at 60/70/80/90% to fill the mid-range gap. **Depth cam sees 92°; the other 268° is UNMEASURABLE.**

## [TODOS] → memory/todos.md
**🔴🔴 NEXT = 🔴🔴 26b: WHY LOCALIZATION NEVER RELOCALIZES (Q1, gates the WHOLE ladder).** ✅ #26 + #28 CLOSED 08-08. ~~#20 yaw~~ SOLVED 08-02. #21 gyro-yaw open. **Then S1 kill test.** **[OUTDOOR] O1-O5:** STL-19 · DroneCAN GPS · lidar SLAM · GPS Nav2 · outdoor safety. **WFB parked: #22 = HARDWARE, reseat drone NIC-A ant0.**
1. Relay NTP · 2. 🔴 **NO onboard Wi-Fi fallback — recovery is WFB → relay:2222 ONLY** · 14. 🔴 **Rotate the PAT, codex-work → SSH**
3+4+24. ❌ **DELETED, don't re-propose:** GS `rx_ring_size`, GS TX power (maxed), trim PX4 MAVLink rates.
5+7+8+9+10. Antenna tracker HW · /scan → Nav2 · #17 delete camera_sw_node_obsolute.py (+`rov_collision_stop`, `collision_manual_mode`) · Multicam Phase D **#5 wheel_odometry: ❌ NOT logging — profiled 20.0%/core = ~65% rclpy executor wait-set, only ~4% our logic. Only real fix = C++ port. Deferred: CPU is not binding.**
23. ✅ watchdog LIVE (`a5fb348`). 25. ✅ retry storm FIXED, 🔴 **still keys `/dev/video0` — close via Phase D/#8.**
26. ✅✅ **DEPTH-GLITCH ABORT FIXED** (`69d9c89`; patch `codex-work 16665f5`) — 1 h 23 m / 0 aborts, was ~13 min. ⚠️ **Orbbec clone is GITIGNORED — a re-clone RESTORES the bug.** ⏭ untested: `align_mode:=HW` kills the class + saves 71%/core. → §11
26b. 🔑🔑 **LOCALIZATION WORKS — IT RELOCALIZED (17:39). THE BLOCKER IS THAT THE ROVER NEVER MOVES.** `Rtabmap.cpp:3772` **"Localization was good, but waiting for another one to be more accurate (RGBD/MaxOdomCacheSize>0)"** — it needs a SECOND fix verified against the odometry travelled in between. Stationary ⇒ no odom ⇒ **waits forever** (3.5 h; all candidate proposals stop dead at that line). ⏭ **FIX = MOVE THE ROVER** (a hand-push turns the wheels and DOES make wheel odom), or `RGBD/MaxOdomCacheSize:0` to accept the first fix uncorroborated. ❌ Ruled out: intrinsics · depth · CPU · `Vis/MinInliers` · **map coverage (db keyframes near the room centre show the SAME drawer tower the camera sees now)**. ⛔ **a blank wall IS still fatal — a PLANE is DEGENERATE for PnP** (1466 rejects at 0 inliers). ⚠️ **I called this "never relocalized" from a grep that missed the success string** → [[feedback-test-before-concluding]]. → §12
28. ✅ **DONE — camera to DRIVING config 15→30 fps, `/scan` 15.0 → 26.3 Hz.** ⚠️ **NEVER revert via `...bak-20260802`** (predates `depth_registration:=true` + 640×360, which localization NEEDS). Re-pin 15/15 only while RECORDING a bag.
27. ⏭ **Reflex `/scan_3d` is now a PARAM (`collision.scan_topic`), default still `/scan`.** `/scan_3d` is 12× steadier close-in (6 vs 74 mm) and agrees to 8 mm at 1.34 m. **Needs ONE low/overhanging object `/scan` misses before flipping.**

## [SENSORS]
TFmini: ttyAMA2 down 0.3-12m 50Hz → distance_sensor | VL53L1X + OptFlow: dead code, see [PERCEPTION] | STL-19: ttyAMA3 360° ~10Hz — **DRONE-bound**, with another team; on re-integration **lidar OWNS `/scan`** (remap depth→`/scan_depth`)
Cameras (**both FPV-capable, port 6-2; swap from QGC only**): **See3CAM_CU135** `usbcam-2560c1d1-241D8306-i00` 60 fps 720p MJPG · **LG Smart Cam** `usbcam-30c9009d-01.00.00-i00` 30 fps, cheaper CPU, **currently the FPV cam** · **Orbbec Gemini 336L** autonomy-only `usbcam-2bc50807-CPC7B53000AB-i04` (USB3 on BOX-B, ROS2 wrapper only, **never ffmpeg**), min valid depth 0.308 m
**Three camera rules:** (1) **NEVER key a camera by `/dev/videoN` or by-id** — only `usbcam-<vidpid>-<serial>-i<iface>`. (2) **NEVER record resolution/fps/bitrate as fact** — read the conf live. (3) **Orbbec video nodes appear/vanish with `rover-camera.service`**; the Pi5's own `rpivid`/`pispbe-*` also renumber them

## [AUTONOMY_ROADMAP] — **DECISION: STL-19 → the DRONE. Rover = camera-only.** → project_autonomy_plan_reframe.md
🔴 **Q1 = the wall (status in 26b).** Route: `EKF2_EV_CTRL=9` via the **px4_ros2 Navigation Interface** (`rover_ekf_bridge` already uses `LocalPositionMeasurementInterface`, velocity-only; **experimental**). PX4 RTL has NO obstacle avoidance here. Pending hw: DroneCAN GPS.
🔑 **PX4 MANUAL BYPASSES THE YAW RATE LOOP** (fw-verified: `manual()` publishes STEERING, only `acro()` a RATE setpoint) ⇒ mapping drives are NOT yaw-gated, **but the reflex doesn't run there either — the operator is the only safety layer.** ⚠️ AutoNav publishes speed+RATE ⇒ the yaw loop gates EVERY AutoNav task.
📦 **OFFLINE: record on the Pi → map on a LAPTOP → localize on the Pi.** ⚠️ live-streaming RGB-D is NOT viable — `image_transport` has **only `raw_pub`** ⇒ ~100 vs 13 Mbit/s. 🔴 SD write ceiling 27.4 MB/s.
📊 **NO VIO EXISTS, don't build one:** `rgbd_odometry` is launched nowhere and costs 79.6%/core; the 336L IMU is unfused/uncalibrated; `/odom` is WHEEL odom from ESC eRPM and **BEAT visual 60 vs 4-5 closures** — RTAB-Map localizes by *place recognition*, odom only bridges between. 🔑 the camera gyro IS an independent inertial yaw-rate source (`vehicle_angular_velocity` is NOT on DDS).
🔴 **Mapping is NOT hardware-blocked:** slam_toolbox needs 360°, **RTAB-Map RGB-D is built for a narrow FOV — swap the ALGORITHM, not the sensor.** 92° is the RGB-D class, not a 336L fault.
⚠️ **PERMANENT (camera-only):** no rear/side coverage ⇒ **"never reverse into unseen space"**; **never clear a spin from any `/scan`**. 🔴 **Nav2's default spin + back-up recoveries must stay DELETED** — exactly the two moves this rover cannot clear.
⚠️ **S1 kill-switch-in-AutoNav is UNTESTED and must go before any AutoNav task.**
> `docs/roadmap.md` (07-23) vs **`docs/autonomy_plan.md` (08-01, NEWER)** — **different L-numbers, don't mix them.**

## [GCS_INTERFACE] → reference_gcs_companion_interface.md
G-Control.exe → pxlabs_cli.exe → SSH relay:2222 → companion:22 | QGC: github.com/ArvinVeiyon/PXLABS_qgroundcontrol @ PXLABS-integration

## [TROUBLESHOOTING]
no_MAVLink: ttyAMA0 + PX4 MAVLink instance | no_DDS: microxrce-agent, ttyAMA4, XRCE param | WFB_down: wifibroadcast@drone, wlx*, /etc/drone.key | **no_video: [VIDEO_FAULTS] (B) LATCH FIRST** | no_scan/no_cloud: **half-dead camera restart first**
