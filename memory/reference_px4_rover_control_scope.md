---
name: px4_rover_control_scope
description: "Which RO_* params actually reach the actuators in which mode, traced in PX4 source: decel limits DO slew the manual stick AND the collision reflex, RO_SPEED_LIM does NOT apply in Manual, jerk is auto-only. Read before changing any RO_* value."
metadata:
  node_type: memory
  type: reference
---

# PX4 rover params — what each one actually reaches

Traced 2026-09-14 against `~/apps/PX4-Autopilot` (`src/modules/rover_differential`,
`src/lib/rover_control`). Extends [[scope_px4_params_by_control_flags]], which is the *rule*; this
is the current *map*. Numbers in `codex-work/esc_px4_config_audit_20260914.md`.

## 🔴 THE DECEL/ACCEL LIMITS SLEW THE MANUAL STICK — AND THE COLLISION REFLEX

`RoverControl::throttleControl` is called from **`DifferentialActControl`**, which sits **downstream
of every flight mode**, Manual included. So `RO_ACCEL_LIM`/`RO_DECEL_LIM` are never bypassed.

🔴🔴 **THE COLLISION REFLEX GOES THROUGH THE SAME PATH.** `ros2_ws/src/collision_manual_mode`
publishes a **`ManualControlSetpoint` marked `SOURCE_RC`** — a fake stick. PX4 cannot tell it from
the operator's hand, so **any decel limit slows the emergency stop too.** There is no way to exempt
it. ⚠️ The reflex's 0.69 m clearance was sized against a 0.19 m stop; **re-verify standoff whenever
`RO_DECEL_LIM` changes.**

## 📏 THE RAMP ARITHMETIC — and why the 08-14 numbers no longer transfer

Throttle slew rate = **`RO_DECEL_LIM` ÷ `RO_MAX_THR_SPEED`** (normalised throttle per second).
Time from full throttle to zero = the reciprocal.

**`RO_MAX_THR_SPEED` was 0.60 in August and is 4.93 now**, so the same decel value is ~8× gentler
than it used to be. ⛔ **Never reuse an August decel figure without redoing this division.**

| `RO_DECEL_LIM` | ÷ `RO_MAX_THR_SPEED` | full-throttle release |
|---|---|---|
| 0.5 (08-14, **caused the wall hit**) | ÷ 0.60 | 1.2 s |
| 3 (set 09-14) | ÷ 4.93 | 1.64 s |
| 5 (**current**, set 09-14) | ÷ 4.93 | 0.99 s |

🔑 **The 08-14 wall hit was `RO_DECEL_LIM` 0.5 + `RO_ACCEL_LIM` 0.3, NOT `RO_SPEED_LIM`.**
`RO_SPEED_LIM` 0.60 was changed in the same batch and reverted with them, but was never the cause.
Centring the stick stopped cutting the motors; the throttle ramped down over ~1.2 s still driving.
⚠️ At low stick (3-30%) the ramp is 0.05-0.5 s and feels fine — **the hazard is at high throttle**,
which only a long run makes reachable.

## 🔴 `RO_SPEED_LIM` DOES NOT LIMIT MANUAL MODE

`DifferentialManualMode::manual()` passes the stick **straight to `throttle_body_x`**. Only
`position()` (POSCTL) interpolates it against `RO_SPEED_LIM`. ⇒ **In Manual, full stick commands the
full 9000 ERPM ≈ 4.93 m/s, not the 0.7 the parameter advertises.** The RC arms into Manual, so this
is the mode that is actually driven. ⚠️ Matters most in a corridor, where there is room to reach it.

## Other scopes worth knowing

- **`RO_JERK_LIM`** (reads 1) is consumed **only** by `DifferentialPosControl` for waypoint approach.
  It does nothing in Manual. Leave it set for AutoNav; disabling it stops auto slowing at waypoints.
- **`RD_WHEEL_TRACK`** (0.31) is the **only** vehicle dimension PX4 holds. It is hub-to-hub track,
  tape-measured 2026-07-21, used for the yaw feed-forward in `DifferentialRateControl`. **Correct —
  it is not, and should not be, the vehicle's width.** ⚠️ The 0.450-vs-0.560 width dispute is a
  Nav2/reflex question, not a PX4 one; both already use 0.450. 0.560 came from a sales quotation.
  ⛔ `wheelbase` 0.430 is NOT the track — that bug shipped once.
- **Manual/Acro/Stab** publish raw throttle; only **POSCTL** and auto build a speed setpoint that
  goes through `DifferentialSpeedControl`.

## ⚠️ QGC UNITS CAN MAKE A CORRECT VALUE LOOK WRONG

Cost two rounds of confusion on 09-14. With QGC in imperial, **`RD_WHEEL_TRACK` 0.31 m displays as
1.017 ft and `RO_MAX_THR_SPEED` 4.93 m/s displays as 11 mph.** Both correct. 🔑 **Read the FC with
`tools/set_param.py` before believing a QGC number is wrong.**

## 🔧 `dump_params.py` BUG — FIXED 2026-09-14

It trusted `wait_heartbeat()`, which latched a non-autopilot heartbeat, targeted **0:0**, received
**zero** parameters, and **still wrote a header-only `.params` file that looked like a valid backup**.
Now filters for component 1 with a valid autopilot type (as `set_param.py` already did) and refuses
to write without one. Verified 952/952. 🔑 **Check the parameter COUNT on any dump before trusting it.**
