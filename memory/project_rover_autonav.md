---
name: project-rover-autonav
description: "Rover autonomous navigation (Nav2 + px4_ros2 lib + Orbbec depth) — requirements agreed 2026-07-19, milestones M0-M7, next = M0"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5ff45709-5e20-4964-9bd8-fce6f3bc03f0
  modified: 2026-07-19T16:22:19.568Z
---

# Rover Autonomous Navigation — ACTIVE (started 2026-07-19)

Full spec: `~/ros2_ws/docs/rover_autonav_requirements.md` (commit e6a3a0d on main) — read it before any autonav work.

## Agreed scope (user-aligned 2026-07-19)
Indoor GPS-denied FIRST · Nav2 full stack · forward-only depth v1 (Gemini 336L depth stream only, never ffmpeg).

## Architecture in one line
Orbbec depth → /scan → Nav2 (slam_toolbox map, global planner, local costmap/controller) → cmd_vel → `nav2_px4_bridge` custom PX4 mode "AutoNav" (px4_ros2 control interface, TrajectorySetpoint vel+yawrate) → PX4 rover-diff → VESC UAVCAN. Wheel odom (`rover_odometry`, math in [[rover-odometry]]) → /odom+TF → Nav2 AND → EKF2 via px4_ros2 `LocalPositionMeasurementInterface`.

## Key facts verified 2026-07-19 (full detail: ros2_ws/docs/ros2_architecture.md, commit 8dbd75e)
- **px4_msgs PINNED @ d2c9ff2** — check-message-compatibility.py vs firmware source c5b8445 = exact match ("OK"); release/1.16 tip FAILS the check. Never update px4_msgs without firmware update.
- interface-lib updated 1.6.0→**1.6.1** (ZYX euler fix), builds clean vs pinned px4_msgs (7.5min on RPi5). Lib 2.x = blocked until PX4≥1.17. Local example experiments saved on branch `local/manual-mode-experiments`.
- **Firmware EXPOSES full rover setpoint set** (/fmu/in/rover_speed|rate|attitude|position|throttle|steering_setpoint) + all Rover*Setpoint msgs in pinned px4_msgs → M4 bridge plan = backport lib-2.x rover setpoint-type class into nav2_px4_bridge; fallback TrajectorySetpoint.
- Live topics measured (FC+VESCs powered): esc_status 49.7Hz ✅, vehicle_odometry 98.6Hz but quality=0, local_position xy_valid=false/dead_reckoning=true (the M2 target), input_rc 9.6Hz, battery 1Hz. Versioned names in use: vehicle_local_position_v1, vehicle_status_v1, battery_status_v1.
- Companion HTTPS→GitHub hangs (IPv6): fetch with `git -c url."git@github.com:".insteadOf="https://github.com/" fetch`.
- apt has ros-jazzy-navigation2 1.3.5 + slam-toolbox 2.8.2; depthimage_to_laserscan already installed.
- NOT yet present: Nav2 install, Orbbec ROS2 wrapper, rover_odometry pkg.
- PX4 rover params RO_*/RD_WHEEL_TRACK were ALL ZERO (2026-05-30 dump) — must set via QGC/NuttShell, pymavlink can't (see [[rover-odometry]]).

## Milestones (each = own commit(s) on main; tag v1.2.0 at end)
M0 installs+params+offboard bench ▸ M1 rover_odometry ▸ M2 EKF2 feed ▸ M3 depth→/scan ▸ M4 bridge AutoNav mode+watchdogs ▸ M5 odom-frame goal+avoidance ▸ M6 SLAM map+global routing ▸ M7 safety validation.
**STATUS: next = M0.**

## Safety invariants (never weaken)
RC override PX4-native; rov_collision_stop node stays active independent of Nav2; cmd_vel>500ms / scan>1s watchdog stops; no reverse into unseen space (forward-only sensing).

Related: [[rover-odometry]] (all odom math/params), [[project-vision-multicam-upgrade]] (camera ids/roles), [[feedback-camera-qgc-only]].
