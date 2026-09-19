---
name: px4_rover_control_scope
description: "Which RO_* params actually reach the actuators in which mode, traced in PX4 source: decel limits DO slew the manual stick AND the collision reflex, RO_SPEED_LIM does NOT apply in Manual, jerk is auto-only. Read before changing any RO_* value."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5a67ac2d-7ab0-4d9b-aa5a-4f8430b150c4
  modified: 2026-09-18T17:18:36.692Z
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

✅✅ **2026-09-18 — THAT LINE CLOSES THE AUTONAV CASE, AND IT WAS ALREADY TRUE WHEN WRITTEN (09-14).**
AutoNav drives at 0.15-0.75 m/s = **3-15% stick** — inside the "feels fine" band by construction.
At 0.75 m/s: throttle 0.152, drains in **0.15 s**, adds **0.057 m**; at 0.25 m/s, **6 mm**. Stacked on
the measured 0.19 m stop ⇒ **~0.25 m worst case against the reflex's 0.69 m clearance.**
⛔ **`RO_DECEL_LIM`=5 NEEDS NO FLOOR MEASUREMENT. Do not book one.**
🔴🔴 **RETRIEVAL FAILURE, NOT A KNOWLEDGE GAP — THE LESSON IS THE POINT:** this page had the formula,
the table and the conclusion on 09-14, while THREE other files (`autonav_reference.md` §13,
`todos.md` §G3, `MEMORY.md` [TODOS]) carried a red "STILL UNMEASURED" alarm. The alarm was louder and
sat higher in the index, so it won for four days and nearly bought a floor session.
🔑 **WHEN A FILE SHOUTS "UNMEASURED", CHECK WHETHER ANOTHER FILE ALREADY COMPUTED IT.** All three
alarms corrected 09-18.

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

## 🔧 PARAM READ/WRITE TOOLING — moved from `MEMORY.md` 2026-09-18

⛔⛔ **NEVER WRITE A VEHICLE PARAM WITHOUT AN EXPLICIT YES. Reading is free.**
🔧 **READ THE FC, NEVER TRUST A SNAPSHOT.** Values + RCA → `ros2_ws/docs/px4_param_audit.md` ·
RC procedure → `rc_configuration.md` §6 · full 09-12 audit → `project_rover_autonav`.

✅✅ **MAVLink `PARAM_SET` PERSISTS BY ITSELF** — `param_autosave()` fires ~300 ms after a write
(`autosave.cpp:60`). **PROVEN across a reboot 09-12.** ⛔ The old "RAM-ONLY, then run `param_save.py`"
rule was WRONG; both tools' NOTE was corrected 09-12. ⚠️ Don't reboot within ~2 s of a write.

🔑 **`<no reply>` USUALLY MEANS WRONG PARAM NAME, NOT "BUSY".** ⇒ **Prove it with a fake-name control**
before concluding the link or the FC is at fault.

⚠️ `tools/set_param.py` is **FLOAT-ONLY** · INT32 → `diag/set_param_int.py` · reboot → `fc_reboot.py`.
🔴 **`NAV_RCL_ACT` reads 1 (Hold), NOT 6 — RC loss will NOT disarm.**
