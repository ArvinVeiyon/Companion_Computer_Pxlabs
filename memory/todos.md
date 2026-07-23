# TODO List
> Tasks to perform AFTER full OS backup of both drone and relay station.

---

## [WFB-NG FIXES] — do after OS backup

### 1. Fix GS clock / NTP for real (Relay station vind-rly) — RECURRED 2026-07-11
2026-03-15 fix (`timedatectl set-ntp true` + restart timesyncd) did NOT hold: relay has no RTC and no internet uplink, so `systemd-timesyncd` can never reach `ntp.ubuntu.com` (DNS/network unreachable) and clock drifts to boot-default every power cycle.
Real fix needs a **local NTP server** the relay can actually reach — companion (10.5.5.87) is reachable from relay (10.5.5.77) over the WFB tunnel and has real internet+correct time. Plan: install `chrony` on companion in server mode, allow 10.5.5.0/24, then point relay's `systemd-timesyncd` `NTP=` at 10.5.5.87.
Attempted 2026-07-11, aborted mid-install — see `project_relay_ntp_setup.md` and `project_companion_network_degraded.md`.

### 2. Disable drone onboard Wi-Fi (wifi0, ex-wlan0) during WFB-NG operation (Drone)
Onboard uplink renamed wlan0 → `wifi0` on 2026-07-19 (see feedback_wlan0_persistent_name.md).
`wifi0` connected to "Nilan" 5GHz AP — possible interference with WFB-NG on ch 157.
First verify channel:
```bash
iw dev wifi0 link | grep freq
```
If 5GHz, disable:
```bash
sudo ip link set wifi0 down
```
Consider making this persistent (disable wifi0 in netplan or add pre-start to wifibroadcast service).

### 3. Increase WFB ring buffer on GS OR reduce drone video bitrate (Relay station)
Root cause: GS wfb-server crashes with BlockingIOError EAGAIN (socket buffer overflow).
19 service restarts observed → each causes "New session detected" + decrypt errors + uplink loss spikes.
Option A — increase rx_ring_size in /etc/wifibroadcast.cfg on relay (currently 2MB, try 4-8MB).
Option B — reduce drone video bitrate in /etc/vision_streaming.conf.

### 5. Fix channel reference in PXLABS_qgroundcontrol docs (local edit + push)
ARCHITECTURE.md and DEVELOPMENT.md both say `ch157` — correct value is **ch161**.
Clone repo, search `ch157` / `channel 157`, replace with `ch161` in both files, then push.
Repo: https://github.com/ArvinVeiyon/PXLABS_qgroundcontrol (branch: master)

### 4. Check GS adapter TX power (Relay station) — NOW MEASURED, WORSE THAN THOUGHT (2026-07-20)
Uplink is not merely lossy, it is **dead for commands**: 8 MAVLink commands injected at the relay
reached the drone **0 times** (a sniffer on the companion router confirmed zero arrivals), while the
identical test on the companion locally succeeded 6/6. Downlink also delivers only **~15%** of offered
telemetry (176 kbit/s offered → 26 kbit/s at the relay, uniform thinning across every message type).
This is the real cause of QGC showing "Unknown <number>" instead of mode names, and it blocks all
QGC-side arming/mode/param work. Full detail + next diagnostic steps: `project_gcs_link_degraded.md`.
Asymmetry may still indicate GS TX power too low.
```bash
iw dev wlx00c0cab6db3b info
```

### 6. vision_streaming node: no ffmpeg watchdog — ✅ DONE 2026-07-19
Watchdog implemented + verified live (ros2_ws a561e93, multicam upgrade phase B):
child reaped, ERROR logged, restart with 2s→30s backoff. Stream death is never silent now.

### 7. Bring up Orbbec Gemini 336L autonomy pipeline — ✅ WRAPPER + /scan DONE 2026-07-21
OrbbecSDK_ROS2 built (@ec6bc22, Release) and verified live: SDK 2.9.3 over USB3.2, depth 848x480@30,
`/camera/depth/{image_raw,points}`, and **/scan @ 20-21 Hz** via `~/ros2_ws/launch/depth_to_scan.launch.py`.
Bring-up: `ros2 launch orbbec_camera gemini_330_series.launch.py`. Wrapper publishes its own TF tree
from `camera_link` — never re-publish those frames. See `project_l4_gemini_nav2_prereqs.md`.
STILL OPEN here: feeding obstacle_distance to PX4 (the original phase-3 goal) — /scan exists but is
not yet wired to PX4 or Nav2. Orbbec stays autonomy-exclusive; FPV = LG cam (see MEMORY [SENSORS]).

### 8. Camera preset/RC migration — QGC half ✅ DONE, companion half = multicam Phase D
QGC presets: DONE 2026-07-19 (phase C — hardcoded video0-3 picker + front/bottom buttons
replaced by dynamic camera-list/alias UI; guard implemented in v2.0, discovery fixed v2.1).
REMAINING (Phase D, companion, go-ahead given — see project_vision_multicam_upgrade.md):
migrate to aliases/usbcam ids via v2.1 resolver:
- ros2_ws/src/rc_control/camera_sw_params.yaml:10-11 (front=/dev/video0, bottom=/dev/video2)
- ros2_ws/src/rc_control/config/rc_mapping.yaml:55-56 (same)
  → CH9 plan per design doc: low=FPV primary, mid=FPV+NAV-COLOR PiP, high=spare
- ros2_ws/src/optical_flow/optical_flow/optical_flow_node1.py:36 (/dev/video2 = Orbbec IR)
- ros2_ws/src/optical_flow/optical_flow/optical_flow_node.py:36 (/dev/video3 = Orbbec IR)
  → make device a ROS param (id/alias); WHICH camera optflow should use = open user
    decision (its original camera was physically removed).
Then cleanup: delete /etc/udev/rules.d/99-usb-cameras.rules (dormant pins for removed cams).

---

## [ROVER AUTONAV] — added 2026-07-20 (see project_rover_autonav.md)

### 9. Set RO_SPEED_LIM — ✅ DONE 2026-07-21 (0.01 → **0.70**, saved + readback-verified)
Was THE forward-drive blocker: `DifferentialSpeedControl.cpp:119` clamped every speed setpoint to
±0.01 m/s, so 0.2 and 0.4 m/s produced identical wheel speeds. 0.70 deliberately sits *below*
`autonav_mode`'s own 0.8 m/s clamp → the FC is the binding cap; also above the ~0.58-0.60 m/s the
drivetrain actually reaches. Floor re-test is now item 18.

### 10. Restart mavlink.router — ✅ RESOLVED 2026-07-21 (companion reboot healed it)
FC heartbeat is back on `tcp:127.0.0.1:5760` (sys 1 comp 1, autopilot=12, type=10); QGC connects again.
**Lesson kept**: read params with pymavlink `PARAM_REQUEST_READ` — it does NOT re-wedge the link, unlike
`mavlink_shell.py`, which is what wedged it originally.

### 11. autonav_mode under systemd with Restart=always — ✅ DONE 2026-07-21
`rover-autonav-mode.service`, plus rover-camera / rover-scan / rover-odometry. See `reference_services.md`.

### 12. Map an RC mode channel — ✅ ALREADY DONE (verified 2026-07-21, earlier note was stale)
FC actually reads `RC_MAP_FLTMODE=6`, `RC_MAP_ARM_SW=5`, `RC_MAP_KILL_SW=8`, `NAV_RCL_ACT=6` (disarm on
RC loss). The old "RC_MAP_FLTMODE=0 / nothing mapped" record was wrong — user was right all along.
Kill/arm/disarm physically tested and working. Stick map: ch2=throttle, ch4=steer, ch3 unused.

### 13. L4/L5 installs — Orbbec SDK + Nav2 + slam_toolbox — ✅ DONE 2026-07-21
All installed: Nav2 **1.3.12** + nav2-bringup, slam_toolbox **2.8.5**, all 7 build deps, Orbbec udev
rule. Disk pressure also resolved: **85% → 49%, 29G free** after reclaiming 20.4 GB (17.85 GB of
pre-2025 `~/.ros/log` debris + 1.7 GB journal + 569 MB apt cache). SD card is fully partitioned; the
64GB-vs-58G gap is GB-vs-GiB + ext4 overhead, not lost space.

### 15. Measure the camera mount TF — ✅ DONE 2026-07-21, committed (ros2_ws 0bd5bf6)
`base_link → camera_link` = **x −0.125, y 0.000, z 0.420**, zero rpy, verified live via `tf2_echo`.
Pitch/roll were **measured from the camera's own IMU**, not assumed. Baked in as launch defaults.
STILL OPEN from L4 acceptance: the **tape-measure range check** ("ranges correct vs tape measure" —
only rate and plausibility confirmed so far). Camera is level, so `scan_height: 40` needs no revisit.

### 16. Pin OrbbecSDK_ROS2 in git — ✅ DONE 2026-07-21 (gitignored + documented, ros2_ws b5a9408)
201 MB clone, so not vendored. Repo + exact commit `ec6bc22` + build steps recorded in
`ros2_ws/docs/third_party.md`; `src/OrbbecSDK_ROS2/` added to `.gitignore`. Promote to a real git
submodule when convenient (nice-to-have, no longer blocking a fresh workspace rebuild).

### 17. Delete camera_sw_node_obsolute.py (added 2026-07-21)
`src/rc_control/camera_sw_node_obsolute.py` (node `camera_node_sw`) logged all 18 RC channels at INFO
on every ~50 Hz callback — ~950 lines/s, which is where the 18 GB of `~/.ros/log` came from. It is not
running (live `rc_control_node` is clean) but should be removed so it cannot be launched by accident.
Local edits from the April STL-19 work were saved to `~/codex-work/ldlidar_stl_local_edits_20260417.patch`
when the unused `ldlidar_stl_ros2` clone was removed the same day.

### 18. L2 forward test ON THE FLOOR — ✅ DONE 2026-07-22 (armed, L2 RESULT: PASS)
First-ever armed floor run. All 4 wheels respond to forward+yaw, watchdog zeroes motors, auto-disarm+Hold.
Wheel-0 "reverse" was a FALSE ALARM (mirrored ESC sign; all 4 physically forward — old sign check removed).
ARM WORKFLOW LEARNED: AutoNav can't arm via RC (external mode) → arm in Manual, then software
DO_SET_MODE→AutoNav (holds). `l2_test.py --live` does this, tolerates already-armed-in-Manual start.
Full detail in [[project-l2-floortest-wheel0-reversed]]. Committed+pushed ros2_ws b38e413.

### 19. Test the kill switch INSIDE AutoNav — ✅ DONE 2026-07-22 (confirmed working armed in AutoNav)
User killed the rover mid-AutoNav (first floor attempt) before a wall — kill (ch8) latched, motors stopped.

### 20. Revisit RO_YAW_RATE_P / RO_YAW_RATE_I after the floor test — ← NEXT ACTION (added 2026-07-21)
CONFIRMED NEEDED by the L2 run: armed yaw drove wheels MUCH harder (~700-850 rpm) than forward (~156 rpm).
Those gains were tuned while `RD_WHEEL_TRACK` was 0.43 — a ~39% oversized track, which sized the
commanded wheel differential (Δv = ω × track). The allocation they were implicitly compensating for
has changed now that it is 0.31. The gyro-closed rate loop hides much of this in steady state, so
expect the difference mainly in feedforward/transient response. Re-check after a real floor run.

### 22. Reflex collision-stop in AutoNav executor — ✅ DONE 2026-07-22/23 (ros2_ws b38e413, pushed)
Built INSIDE `autonav_mode` (single funnel to motors, can't be bypassed): ±20° front `/scan` cone, block
<0.60m / clear >0.75m hysteresis, stale-scan fail-safe, `collision.*` params, always-on edge-triggered
diagnostic. Validated passively on stands AND fired armed end-to-end (stopped ~0.59m from a real wall).
Doc: `ros2_ws/docs/rover_autonav_collision_stop.md`. This is the safety FLOOR only — real avoidance/
routing/rerouting is L5 (Nav2+slam_toolbox), still to do. Follow-up: widen cone / add side sectors with
Nav2 costmaps; armed wall-stop already proven so no separate proof run needed.

### 21a. Gyro yaw odometry — ✅ IMPLEMENTED 2026-07-21 (ros2_ws 3fdf2fc, pushed)
`rover_odometry` now takes heading from `/fmu/out/vehicle_attitude` (~92 Hz) instead of
`(v_right − v_left)/track`. New params `yaw_source` (default `gyro`, set `wheels` for A/B) and
`attitude_timeout` (0.5 s → auto-fallback to wheels, logged). Integrates yaw **deltas** not absolute
yaw (keeps /odom's own origin, sidesteps NED-vs-ENU); one sign flip since PX4 yaw is +CW from above
and ROS is +CCW; `quat_reset_counter` changes are EKF resets and those deltas are DROPPED, never
integrated; yaw baseline advances even on skipped steps so a bad dt can't become false rotation;
yaw covariance now source-dependent (0.002 gyro vs 0.02 wheels) so Nav2/SLAM weight it honestly.
**Note `/fmu/out/vehicle_angular_velocity` is NOT in this FC's dds_topics.yaml** — attitude is the
only gyro-derived source exposed.
Verified at rest: /odom 98.8 Hz, yaw drift **0.044° over 12 s**, angular.z −0.0004 rad/s.
**STILL TO VALIDATE (needs driving)**: turn the rover a known angle (e.g. 90° or 360° by floor marks)
and compare `/odom` yaw against reality; also A/B against `yaw_source:=wheels` to quantify how bad
the slip error actually was. Do this during the item-18 floor session.

### 21. Use the camera IMU alongside the FC IMUs (user idea, 2026-07-21) — assess before building
The Gemini 336L has its own IMU (`/camera/accel/sample`, `/camera/gyro/sample`; enable with
`enable_accel:=true enable_gyro:=true`, now on by default in `rover-camera.service`). Ranked by
value, honestly:
1. **HIGHEST VALUE, and it does not need the camera IMU at all: replace wheel-derived yaw with
   GYRO yaw in `rover_odometry`.** Skid-steer yaw from wheel speeds is inherently bad — all four
   wheels *must* slip laterally to turn, so `(v_right − v_left)/track` systematically misestimates
   rotation no matter how perfect the track width is. The FC's gyro/EKF yaw is already on DDS
   (`vehicle_attitude`, `vehicle_angular_velocity`) and is far better. Use wheels for forward
   distance, gyro for heading. This is the standard fix for skid-steer odometry and is likely the
   single biggest accuracy win available before SLAM.
2. **Independent cross-check of FC IMU health.** The camera IMU is a genuinely independent gravity
   reference — it is what let the camera mount pitch/roll be measured tonight. Useful for sanity-
   checking accel calibration (cf. the "accel 0 inconsistency" episode), where the FC's own IMUs
   cannot arbitrate between themselves.
3. **VIO (visual-inertial odometry)** — the ambitious option: camera IMU + depth/colour for
   drift-free-ish motion estimation that survives wheel slip entirely. Real payoff for GPS-denied
   nav, but heavy on the RPi5, which already shares compute with vision streaming (`/scan` alone
   drops to ~13-19 Hz under load). Do NOT start here; revisit only after Nav2 works.
4. **Feeding the camera IMU into EKF2 as an extra IMU: not practical.** PX4 EKF2 has no external-IMU
   input path; only external *vision* pose/velocity, which is what `rover_ekf_bridge` already uses.
**Recommendation: do (1) first — it is cheap, principled and helps SLAM immediately. Keep (2) as a
diagnostic. Defer (3). Drop (4).**

### 14. Rotate the GitHub PAT embedded in the codex-work remote URL
`~/codex-work/.git/config` holds a plaintext `ghp_...` token. Rotate it and switch that remote to SSH.
See `project_codexwork_token_in_remote.md`.

---

## [ROVER OUTDOOR — PRIMARY TARGET] — added 2026-07-23 (see ros2_ws/docs/roadmap.md §4, O1-O5)
Goal: rover drives itself to a **GPS waypoint** in open outdoor space, **360° obstacle avoidance**, no
operator. Indoor GPS-denied (L0-L4 done, L5/L6 next) is the stepping-stone + GPS-loss fallback. These
outdoor tasks come AFTER the indoor brain is proven (L5+L6). Both O1 and O2 need hardware the user is fitting.

### O1. Re-integrate the STL-19 360° LiDAR (blocked on getting the unit back)
LDRobot STL-19: 360° 2D, **0.02-25 m, ~10 Hz** LaserScan; UART **ttyAMA3 @ 230400, RX-only** (lidar TX →
RPi RX, no commands); `dtoverlay=uart3-pi5`, TF `base_link→base_laser` 0.18 m (re-measure mount).
- Hardware went to another team 2026-04-17 → **need the physical unit back first**.
- Driver `ldlidar_stl_ros2` (node LD19) already in `ros2_ws/src` with BOTH upstream fixes applied
  (pthread include + hardcoded `/dev/ttyAMA3`). Local edits: `codex-work/ldlidar_stl_local_edits_20260417.patch`.
- Steps: reconnect hw → enable `ttyAMA3` → build → install/enable `ldlidar.service` (unit template in
  `codex-work/ldlidar_stl19_install_guide.md`).
- ⚠️ **`/scan` conflict**: lidar driver AND `depth_to_scan` both publish `/scan`. Fix: **lidar owns `/scan`**
  (SLAM + 360° costmap); remap depth to **`/scan_depth`** as a separate Nav2 costmap layer.

### O2. Integrate the DroneCAN GPS (blocked on module choice + fitting)
- DroneCAN/UAVCAN bus already live (VESC ESCs addr 10-13) → GPS is one more node on it.
- PX4: enable `UAVCAN_ENABLE` (GPS subclass) + set `EKF2_GPS_CTRL` to fuse GPS (**FC param path, MAVLink-only,
  not DDS**). Verify `/fmu/out/vehicle_gps_position` populates + `vehicle_global_position` goes valid.
- Nav2: outdoor GPS nav via `navsat_transform_node` (robot_localization) or Nav2 GPS waypoint follower.
- **Module make/model: TBD — user to confirm** (sets the exact DroneCAN GPS driver params).

### O3. Outdoor 2D-lidar SLAM (builds on L6)
slam_toolbox on the lidar `/scan` (2D-lidar SLAM is far better than depth-derived scan) + fold the 336L
forward depth in as a costmap layer for low/overhang obstacles the flat 2D plane misses.

### O4. Outdoor Nav2 with GPS waypoints (builds on L5)
`navsat_transform` / GPS-waypoint-follower launch config (distinct from the indoor SLAM launch); global
plan to a GPS coordinate, local costmap from lidar+depth, controller → `/cmd_vel` → autonav_mode.

### O5. Outdoor safety hardening (extends L7)
Terrain handling, dynamic obstacles, and **GPS-loss failsafe → wheel/gyro dead-reckoning + reflex stop,
never an uncontrolled state**. Caveat to design around: STL-19 is a **2D** lidar (fixed-height plane) — on
uneven terrain it can miss low obstacles or read a slope as a wall; the forward 3D 336L covers that gap.
