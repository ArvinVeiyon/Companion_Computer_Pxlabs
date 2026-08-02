---
name: reference-px4-vio-collision
description: "Source-verified (pxlabs-fw a52c38b): PX4 collision prevention is MULTICOPTER-ONLY and no rover module touches it; PX4 has no path planner; EKF2_EV_CTRL bitmask meanings and why velocity-only VIO cannot fix localization."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 8643e18b-c953-47fd-a35d-3ca61f7d4394
  modified: 2026-08-02T11:37:22.372Z
---

# PX4 VIO + collision avoidance — what the firmware actually does (rover view)

**Read from the REAL firmware source: `~/PX4-Autopilot` branch `pxlabs-fw` @ `a52c38b07d`.**
Not docs, not inference. Re-verify against the branch if the firmware is upgraded.

## 🔴 1. COLLISION PREVENTION IS MULTICOPTER-ONLY. IT DOES NOTHING ON A ROVER.
`src/lib/collision_prevention/CollisionPrevention.{cpp,hpp}` is referenced by **exactly three** files:
- `flight_mode_manager/tasks/ManualPosition/FlightTaskManualPosition.hpp` (MC Position mode)
- `flight_mode_manager/tasks/Utility/StickAccelerationXY.hpp` (MC)
- `drivers/distance_sensor/lightware_sf45_serial` (only *publishes* `obstacle_distance`)

**`grep` over `src/modules/rover_differential`, `rover_ackermann`, `rover_mecanum` for
`CollisionPrevention|obstacle_distance|distance_sensor|collision` returns NOTHING.**
⇒ **`CP_DIST` / `CP_DELAY` / `CP_GUIDE_ANG` / `CP_GO_NO_DATA` have NO effect on this vehicle.**
⇒ **Our reflex inside `autonav_mode`'s executor is not a stopgap — it is the ONLY option.**
⇒ Publishing `/fmu/in/obstacle_distance` from a rover achieves nothing (confirms the VL53L1X path
was always dead for this airframe) → [[project-perception-3d-costmap]].

## 🔴 2. PX4 HAS NO PATH PLANNER
Only `navigator/GeofenceBreachAvoidance` exists — geofence, not obstacles. **PX4-Avoidance was a
separate OFFBOARD companion project, deprecated 2023.** ⇒ **Global + local planning MUST live on the
companion (Nav2). That is not a workaround, it is the only architecture PX4 supports.**

## 3. VIO PATH — `vehicle_visual_odometry` is consumed ONLY by EKF2
`EKF2_EV_CTRL` is a **bitmask** (`src/modules/ekf2/params_external_vision.yaml`):
| bit | value | fuses |
|---|---|---|
| 0 | 1 | **Horizontal position** |
| 1 | 2 | Vertical position |
| 2 | 4 | **3D velocity** |
| 3 | 8 | **Yaw** |

🔑 **OURS IS `EKF2_EV_CTRL = 4` = 3D VELOCITY ONLY — no position, no yaw.**
**Velocity fusion is still dead reckoning: it improves the velocity estimate but position drifts
without bound. This is exactly why Q1 "where am I?" stays unsolved even though the bridge works.**
To actually localize via PX4 you would need **bit 0 + bit 3 (`EKF2_EV_CTRL = 9`)** fed from a
**map-referenced** pose (RTAB-Map / AMCL), never from wheel odometry.

Other EV params that matter:
- **`EKF2_EV_DELAY` — default 0 ms, MAX 300 ms.** 🔴 **Our visual odometry ran ~1 s behind under
  realtime CPU load — far outside what EKF2 can compensate.** Offline with free CPU it was 0.13 s,
  which fits. **Any live VIO feed must stay under 300 ms or EKF2 cannot correct for it.**
- `EKF2_EV_POS_X/Y/Z` — sensor offset; must match the camera mount (`rover_geometry.md`).
- `EKF2_EV_QMIN` — minimum EV quality gate.

## 4. What rover_differential DOES accept
`trajectory_setpoint`, `position_setpoint`, `RoverRateSetpoint`, `RoverThrottleSetpoint`, and there
IS a `DifferentialPosControl`. **So PX4 can position-control a rover — but with ZERO obstacle
awareness**, because of §1.

## ⏭ THE ARCHITECTURAL CONCLUSION (rover, forward-only sensing)
Two coherent options; **(b) is what we have built and it is the simpler one:**
- **(a)** Feed map-referenced position+yaw into EKF2 (`EKF2_EV_CTRL=9`) so PX4 knows where it is, then
  use PX4 position control. Needs VIO latency <300 ms and a trustworthy map pose.
- **(b) ✅ Keep localization + planning entirely on the companion** (Nav2/AMCL over RTAB-Map's map),
  send only velocity to PX4 via `autonav_mode`. **PX4 never needs to know where it is.**
⇒ **Division of labour:** PX4 = motors, rate/speed loops, arming, failsafe. Companion = map,
localization, global plan, local avoidance, **and the collision reflex** (PX4 will never supply it).
