---
name: rover-odometry
description: All parameters and plan for rover wheel odometry ROS2 node from VESC ESC RPM via UAVCAN
metadata: 
  node_type: memory
  type: project
  originSessionId: 2d8c9512-eb8c-4b27-b518-3de2ce63ad22
  modified: 2026-07-21T18:57:54.165Z
---

# Rover Wheel Odometry — Implementation Plan

## Hardware
- 4x VESC 6 Mk5 (one per motor, all on UAVCAN)
- 4x Yalu 6" 250W 24V hub motors (geared hub, internal 3:1)
- Drive config: 4WD skid-steer (differential)

## UAVCAN ESC Address → Wheel Mapping
| Address | Side  | Position |
|---------|-------|----------|
| 10      | Right | (RF or RR) |
| 11      | Left  | (LF or LR) |
| 12      | Right | (RF or RR) |
| 13      | Left  | (LF or LR) |

Left side = addr {11, 13} | Right side = addr {10, 12}

## Motor Parameters (from VESC MCConfiguration XML)
- `si_motor_poles`: 14 → **pole_pairs = 7**
- `si_gear_ratio`: 3 (internal hub gearing)
- `si_wheel_diameter`: 0.083m — **IGNORE, wrong in VESC config**
- Actual wheel diameter: **6 inch = 0.1524m** → radius = 0.0762m
- sensor_mode: 2 (Hall sensor)

## Key Conversion Formula
```
ERPM_TO_MS = π × 0.1524 / (7 × 3 × 60) = 0.000380 m/s per ERPM unit

wheel_RPM = ERPM / (pole_pairs × gear_ratio) = ERPM / 21
velocity   = ERPM × 0.000380  m/s
```

Verified against live test data:
- addr 11: ERPM 696 → 0.265 m/s ✓
- addr 13: ERPM 881 → 0.335 m/s ✓

## Odometry Parameters
- **Track width (left↔right hub centres): 310mm = 0.31m — MEASURED 2026-07-21. NOT 0.43.**
  0.43 m is the **WHEELBASE** (front hub ↔ rear hub) and was wrongly sitting in the track slot
  until 2026-07-21, under-reporting every yaw rate by ~28%. Do not reintroduce it.
- Wheelbase (front↔rear hub centres): **0.43m** — used only for the camera mount TF, never odometry.
- Wheel diameter: **0.1524m**
- ERPM → m/s: **× 0.000380** (unaffected by the track error — straight-line odom was always correct)

## Differential Odometry Math
```python
v_left  = avg(ERPM addr 11, 13) × 0.000380
v_right = avg(ERPM addr 10, 12) × 0.000380

v_linear  = (v_left + v_right) / 2.0
v_angular = (v_right - v_left) / 0.31   # LEGACY wheel yaw — only used when yaw_source='wheels'
# DEFAULT SINCE 2026-07-21 is yaw_source='gyro': heading comes from the FC's
# /fmu/out/vehicle_attitude (~92 Hz), integrated as DELTAS. Skid-steer can only
# turn by scrubbing all four tyres sideways, so the wheels cannot observe true
# rotation at all — no track_width value can fix that. Wheels = distance, gyro = heading.

# Midpoint integration (each dt):
theta_mid = theta + v_angular * dt / 2
x     += v_linear * cos(theta_mid) * dt
y     += v_linear * sin(theta_mid) * dt
theta += v_angular * dt
```

**Sign map VERIFIED 2026-07-19** (all 4 wheels hand-spun forward, wheels-up, deadband-filtered capture — every sample sign-consistent):
`ERPM_SIGN = {10: -1, 11: +1, 12: +1, 13: +1}` — only addr 10 inverted. Apply as per-wheel parameter (not per-side).
**Idle noise VERIFIED 2026-07-19**: all ESCs jitter ±1..±35 ERPM at standstill (Hall noise) → node needs deadband param, default ±40 ERPM (≈0.015 m/s), else stationary drift.

## ROS2 Node Plan
- **Package**: `rover_odometry` (new, Python, ament_python — follow rc_control pattern)
- **Location**: `~/ros2_ws/src/rover_odometry/`
- **Node**: `wheel_odometry_node.py`
- **Subscribes**: `/fmu/out/esc_status` (px4_msgs/EscStatus)
- **Publishes**: `/odom` (nav_msgs/Odometry)
- **TF**: broadcasts `odom → base_link`
- **Dependencies**: rclpy, px4_msgs, nav_msgs, geometry_msgs, tf2_ros

## Package Structure (to create)
```
~/ros2_ws/src/rover_odometry/
├── package.xml
├── setup.py
├── setup.cfg
├── resource/
│   └── rover_odometry
└── rover_odometry/
    ├── __init__.py
    └── wheel_odometry_node.py
```

## ESC Status Topic
`/fmu/out/esc_status` — confirmed live, all 4 VESCs publishing
Only use entries where `esc.timestamp != 0` (zero = slot unused)

## PX4 Parameter Status (from full param file dump 2026-05-30)
Vehicle confirmed: CA_AIRFRAME=6 (Rover), MAV_TYPE=10, SYS_AUTOSTART=50000 (diff rover)

### Parameters needing correction — ALL ZERO / WRONG:
| Parameter        | Current | Target  | Notes                        |
|-----------------|---------|---------|------------------------------|
| RD_WHEEL_TRACK  | ✅ 0.31 | 0.31    | **FIXED + saved + readback-verified 2026-07-21.** Was 0.43 on the FC — the WHEELBASE in a track-width param. PX4 differential allocation uses it as Δv = ω × track, so 0.43 commanded a ~39% oversized differential (the gyro-closed yaw-rate loop masks much of it in steady state; error shows in feedforward/transient). **Note: odometry ALSO used 0.43, so the two errors were cancelling and the system looked self-consistent.** Both now 0.31. |
| RO_MAX_THR_SPEED| 0.0     | ~3.0    | Speed at full throttle m/s   |
| RO_SPEED_P      | 0.0     | ~0.5    | Speed controller P           |
| RO_SPEED_I      | 0.0     | ~0.1    | Speed controller I           |
| RO_YAW_RATE_P   | 0.0     | ~2.0    | Yaw rate P                   |
| RO_YAW_RATE_I   | 0.0     | ~0.1    | Yaw rate I                   |
| RO_YAW_RATE_LIM | 0.0     | ~1.57   | Max yaw rate (rad/s)         |
| RO_YAW_P        | 0.0     | ~2.0    | Yaw position P               |

### UAVCAN ESC mapping (confirmed from param file):
- UAVCAN_EC_FUNC1=101(L), FUNC2=102(R), FUNC3=101(L), FUNC4=102(R) ✓
- UAVCAN_EC_REV=1 (bitmask 0001) → only channel 1 reversed — may need adjustment
- MOT_POLE_COUNT=14 ✓
- UAVCAN_ENABLE=3 ✓

### VESC node 13 params (bottom of param file):
- can_status_rate_=50Hz ✓ | ctl_dir=1 (direction inverted) | can_esc_index=3

### vehicle_odometry quality=0 root cause:
EKF2_GPS_CTRL=7 (GPS fusing) but no GPS indoors → quality stays 0
EKF2_EV_CTRL=0 (external vision disabled)
Fix options: A) use outdoors with GPS, B) feed ROS2 odom back via /fmu/in/vehicle_visual_odometry

### MAVLink param read status:
pymavlink TCP:5760 only sees router heartbeats (sys=255 comp=190), not PX4 params.
Use QGC or PX4 NuttShell directly to set parameters.

## Why:
Autonomous rover nav (Nav2) needs /odom. PX4 vehicle_odometry has quality=0 (EKF2 not fusing wheel data). Cleanest approach is a direct ROS2 node reading ESC RPM → computing differential odometry → publishing /odom for Nav2.

## How to apply:
When user says "create rover odometry node" or "set up Nav2 odometry" — use all params above, follow rc_control package pattern, create rover_odometry package in ros2_ws/src/.
When user says "set PX4 rover params" — use QGC or NuttShell (not pymavlink TCP), set the table above.
