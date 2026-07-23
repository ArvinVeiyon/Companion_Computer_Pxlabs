---
name: project-l4-gemini-nav2-prereqs
description: "L4 DONE 2026-07-21: Gemini 336L wrapper built, /scan live at 20Hz via depthimage_to_laserscan; Nav2+slam_toolbox installed, L5 unblocked. Camera mount TF still a placeholder."
metadata: 
  node_type: memory
  type: project
  originSessionId: 855c903a-dc57-4bd6-ad2e-825937697502
  modified: 2026-07-21T19:02:37.169Z
---

# L4 (Gemini → /scan) — DONE 2026-07-21 · L5 (Nav2) ready

Audit of 2026-07-20 said nothing was installed. As of 2026-07-21 all of it is in.

## Installed / built
- **Nav2 `1.3.12`** + `nav2-bringup`, **`slam_toolbox 2.8.5`**, all 7 build deps (nlohmann-json,
  gflags, camera-info-manager, diagnostic-updater, image-publisher, backward-ros, xacro).
- **OrbbecSDK_ROS2** cloned to `~/ros2_ws/src/OrbbecSDK_ROS2` @ `ec6bc22`, built Release
  (`orbbec_camera` 8min, plus `_msgs` + `_description`). Udev rule `99-obsensor-libusb.rules` in place.
  **Still untracked in git** — needs submodule-pin or gitignore.
- Camera bring-up: `ros2 launch orbbec_camera gemini_330_series.launch.py` (a `_low_cpu` variant
  exists if CPU gets tight). SDK 2.9.3, USB3.2, depth 848x480@30 Y16, color 1280x720@30 MJPG.
- Wrapper publishes its own TF tree rooted at `camera_link` (→ `camera_depth_frame` →
  `camera_depth_optical_frame`, −90/−90 optical rotation). Do NOT re-publish those.

## /scan pipeline
`~/ros2_ws/launch/depth_to_scan.launch.py` — **standalone file, not a package** (run by path).
Adds only `base_link → camera_link` static TF + `depthimage_to_laserscan_node`.
Verified live: **/scan @ 20-21 Hz**, frame `camera_depth_frame`, FOV ~92° (±0.8 rad), range 0.3-8.0 m,
real returns. Params: scan_height 40, scan_time 0.033.

## (SUPERSEDED — resume from [[project-rover-autonav]], not here. L4 is closed; camera TF is
## MEASURED, not a placeholder; RO_SPEED_LIM and the MAVLink link are both fixed. Kept for the
## bring-up commands and the L4 detail below.)
## Old resume note — updated 2026-07-21 evening
The Pi rebooted and killed both detached nodes; **both were relaunched and re-verified**
(`/scan` ~25Hz, camera depth+color streaming). Relaunch order if dead again: camera first
(`ros2 launch orbbec_camera gemini_330_series.launch.py`, ~25s to come up), then
`ros2 launch ~/ros2_ws/launch/depth_to_scan.launch.py`.
Next actions in order:
1. ~~STILL BLOCKING L5: get the measured camera mount pose~~ ✅ **DONE 2026-07-21** — measured and
   baked into the launch defaults (x −0.125, y 0, z 0.420, zero rpy). L5 is unblocked.
2. Then L5: `slam_toolbox` on `/scan` + `/odom` (odom live @~100Hz from `rover_odometry`),
   then Nav2 bringup.
3. Housekeeping: pin OrbbecSDK as submodule, delete `camera_sw_node_obsolute.py`, add systemd units.
No longer blocking: **`RO_SPEED_LIM` fixed to 0.70** and **MAVLink link healed** by the reboot —
see [[project-rover-autonav]].

## CAMERA MOUNT TF — MEASURED 2026-07-21 evening, no longer a placeholder (L5 UNBLOCKED)
Baked into `launch/depth_to_scan.launch.py` defaults; verified live via `tf2_echo base_link
camera_depth_frame` → Translation **[-0.125, 0.000, 0.420]**.
- **cam_x = -0.125** — wheelbase 0.43 m (front hub → rear hub), lens 0.34 m behind the front axle
  ⇒ 0.43/2 − 0.34. **Negative is correct**: camera sits 12.5 cm BEHIND the rotation centre.
  Cross-check that validated the numbers: lens 0.49 back from front chassis edge, front axle 0.15
  back from it ⇒ lens 0.34 behind front axle + 0.09 ahead of rear = 0.43 = wheelbase ✓
- **cam_y = 0.0** — camera on the centreline of the 40.5 cm top chassis plate.
- **cam_z = 0.42** — 18 cm chassis + 24 cm mast, ground to lens.
- **pitch = roll = 0, MEASURED not assumed** — via the **Gemini 336L's own IMU**. Enable with
  `ros2 launch orbbec_camera gemini_330_series.launch.py enable_accel:=true enable_gyro:=true`
  (off by default → no /camera/accel/sample topic otherwise), then average
  `/camera/accel/sample`: gravity read 9.785 of 9.787 m/s² on a single axis, orthogonal components
  −0.7° and +0.9° ⇒ level within ~1°. **Keep IMU enabled — makes future TF checks a 30-second job.**

## ROVER GEOMETRY — all measured 2026-07-21, the two dimensions were being confused
- **Wheelbase = 0.43 m** (front hub centre → rear hub centre). Used ONLY for the camera TF (cam_x).
- **Track width = 0.31 m** (left hub centre → right hub centre). Used ONLY for yaw-rate odometry.
- Top chassis plate 40.5 cm wide ⇒ **wheels sit INBOARD of the plate** (~4.75 cm overhang each side).
- **BUG FOUND + FIXED 2026-07-21: `track_width` was 0.43 — the WHEELBASE sitting in the track slot.**
  Yaw rate = (v_right − v_left)/track, so every rotation was **under-reported by ~28%** (0.31/0.43):
  the rover believed it turned less than it did. Exactly the error that makes SLAM fight odometry.
  Straight-line odometry was NOT affected (that comes from `erpm_to_ms`, independently verified).
  Fixed in BOTH `src/rover_odometry/config/rover_odometry.yaml` AND the hardcoded
  `declare_parameter('track_width', ...)` default in `wheel_odometry_node.py:35`.
  **Why both matter**: the node is launched as plain `ros2 run rover_odometry wheel_odometry_node`
  with **no `--params-file`**, so the YAML is never read and the code default is what actually runs —
  that silent override is what hid the bug. Rebuilt + restarted + verified via
  `ros2 param get /wheel_odometry_node track_width` → 0.31, /odom ~100 Hz.

## Open items
- Depth delivers ~24 Hz against configured 30 (and /scan ~20) — suspect CPU/USB contention with
  `vision_streaming` on the LG FPV cam. Not blocking.
- Both bring-ups are manual `setsid` runs (logs `~/ros2_ws/orbbec_launch.log`, `scan_launch.log`);
  no systemd units yet, deliberately, until proven.

## Disk (was the blocker)
Cleanup 2026-07-21 reclaimed **~20.4 GB**: 17.85 GB of pre-2025 `~/.ros/log` debris (16,063 files,
spam from the obsolete `camera_sw_node_obsolute.py` logging 18 RC channels at 50 Hz), 1.7 GB journal
vacuum, 569 MB apt cache. **Disk 85% → 49%, 29G free.** SD card is fully partitioned (63.8 GB card,
no unallocated space) — 58G rootfs is just GiB-vs-GB plus ext4 overhead.
`camera_sw_node_obsolute.py` still sits in `src/rc_control/` and should be deleted.

Related: [[project-rover-autonav]], [[project-vision-multicam-upgrade]], [[project-boxb-pcie-usb]],
[[feedback-camera-qgc-only]].
