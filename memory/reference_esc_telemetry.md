---
name: reference-esc-telemetry
description: "ESC/DroneCAN telemetry on the rover — what esc_status actually means, that esc_rpm is MECHANICAL rpm (÷7 from ERPM), the two brake slots (5 = RC, 6 = software), the UAVCAN_EC scaling, the per-address mode split (13 = RPM, 10/11/12 = CURRENT), and why zero throttle is not braking. Read before diagnosing any ESC, setting uavcan_raw_rpm_max, or quoting a stopping figure."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 3d6fddee-7330-454a-a767-3665b8dfbebf
  modified: 2026-09-12T18:05:18.893Z
---

# ESC / DroneCAN telemetry — how to read it, and what it does NOT mean

Consolidated 2026-09-11 out of four overlong `MEMORY.md` lines. `MEMORY.md` keeps only the
traps; the reasoning lives here. Related: [[project_vesc_can_flashing]], [[rover_odometry]],
`codex-work/rc_configuration.md` §6, `codex-work/px4_vesc_dronecan_implementation.md`.

## 🔴 READING `esc_status` — three things that are routinely got wrong

**1. `esc_errorcount` IS NOT A FAULT CODE.** `EscReport.msg` defines it as *"Number of reported
errors by ESC"* — a **cumulative count**. A reading of **51 means 51 accumulated errors, NOT
fault code 51.** Memory asserted the opposite until 2026-09-11; that claim is **withdrawn**.

**2. The fault IDENTITY is `failures`**, a `uint16` **bitmask**, with named bits in the message:
`OVER_CURRENT` · `OVER_VOLTAGE` · `MOTOR_OVER_TEMPERATURE` · `OVER_RPM` · `INCONSISTENT_CMD` ·
`MOTOR_STUCK` · `GENERIC` · motor/ESC temperature warnings. That is the field to read for *what
went wrong*, not `esc_errorcount`.

**3. `EscReport[8] esc` is ALWAYS 8 entries long**, whatever is connected. Only **`esc_count`**
and **`esc_online_flags`** (bit N = ESC N online) say which entries are real. Iterating the array
blind returns zero-filled phantoms that look exactly like a dead ESC.

🔑 `input_rc` / `manual_control_setpoint` / `esc_status` are **all on DDS** ⇒ diagnose ESCs with
**no VESC Tool and no `mavlink_shell`**.

## 🔑 SLOTS 5 AND 6 ARE BRAKES — and they have broken QGC's ESC health (2026-09-11/12)

🔴 **UPDATED 2026-09-12: `esc_count` now reads 6.** Slot 5 (array index 4) is the **RC brake** on
`UAVCAN_EC_FUNC5 = 407` (`RC_AUX1`, pure stick passthrough). Slot 6 (index 5) was added by the
operator the same day as `UAVCAN_EC_FUNC6 = 301` = **`Peripheral_via_Actuator_Set1`**, a
**software-commandable** brake channel so the collision reflex can finally reach the brake — see
[[project_rover_autonav]] 2026-09-12. Measured live after the change: `esc_armed_flags` **63**
(six bits) against `esc_online_flags` **15** (four bits). **Neither brake is ever online**, because
a brake output is not a telemetry-reporting ESC. (Before 09-12 the readings were 5 and 31.)

🔑 **BOTH GO OUT ON THE SAME DroneCAN `RawCommand`.** `esc.cpp:104-123` fills `cmd` from the mixer
then `msg.cmd.resize(min_size)`, where `min_size` is the highest slot with `UAVCAN_EC_FUNCn > 0`.
Five entries before, six now. ⛔ **The VESC firmware must bounds-check `cmd.len` before reading
index 5** — the array is 5 long whenever `FUNC6` is 0.
⏭ **Slot 6 IS INERT until all four ESCs are reflashed** to read index 5 (`canard_driver.c`,
`max(idx4, idx5)`). ⛔ **−1.0 = off, 0.0 ≈ 50% brake**, and the value **latches**.

⇒ **QGC's "ESC 5 not connected" error is EXPECTED, not a fault.**
🔴 **BUT it permanently lights QGC's ESC health, so ⛔ QGC CAN NO LONGER FLAG A REAL DISCONNECT.**
Before the brake, a dropped ESC cleared its bit and QGC named it. Now there is always an error
showing and a genuine failure does not stand out. **Read `esc_online_flags` bit-by-bit over DDS.**
⚠️ This matters most during **G2**, which is exactly when an ESC zero-dropout must be caught.

⛔ **NEVER index `esc[]` by array position.** Key on `esc_address` and drop `timestamp == 0`.
Fixed 2026-09-11 in `tools/l2_test.py` and `tools/yaw_response_log.py`; `wheel_erpm_log.py`,
`odom_scale_measure.py`, `speed_command_test.py`, `s1_kill_test.py`, `t2_straight_goal_test.py`
and `collision_standoff_test.py` already did it correctly.
⚠️ The drive addresses are **10, 11, 12, 13**, but that is a **stable ordering only** — the
address ↔ wheel-corner mapping **has never been verified against one turning wheel.**

## ⛔ `UAVCAN_EC_MIN1..4` = 110 / `MAX1..4` = 8082 ARE DELIBERATE
**Never "tidy" them back to 10/8191.** Sum 8192 ⇒ neutral lands exactly on 4096; **10 is dead
full-reverse.** Set 2026-09-04. ⚠️ Those were **bench only** — stands, unloaded, never driven.

## ⛔⛔ ZERO THROTTLE IS FREE-FLOW COAST, NOT BRAKING
Regenerative drive ⇒ **≈zero torque at standstill**, and **a hand test cannot measure it.**
This is why the standoff guarantee is **speed-bound**: the collision reflex only zeroes the
setpoint, so the rover *coasts*. The threshold fired within **1–6 mm** of its 0.350 m spec every
time; the coast is what ran out of room, and at ~0.9 m/s it **contacted the wall with 0.020 m
left.** Holding brake = `set_handbrake_rel`. ⚠️ `timeout_brake_current` = 2 A on 300 ms command loss.

🔴 **THE REFLEX STILL ONLY ZEROES THE SETPOINT — IT NEVER COMMANDS THE BRAKE.** Wiring it in is
the highest-value unmade change, and **0.69 vs ~0.20 m/s² is the argument for it.**

### The brake itself — MEASURED 2026-09-09, loaded, on the floor
All four wheels, ch3 → AUX1 → `UAVCAN_EC_FUNC5` slot 5 → idx 4: **0.69 m/s², stopping in
0.30–0.50 m from ~0.8 m/s.** Proportional `aux1` confirmed, `RC3_TRIM` 1487.5, `esc_errorcount`
0 under load. ⚠️ **Coast baseline is n=2, so the 3.4× ratio and the "saves 1.4 m" are PROVISIONAL.**
→ `codex-work/bldc_can/evidence/brake_floor_test_20260909.md` (`_bench_` = run 1) ·
procedure `rc_configuration.md` §6.

## 🔑 RULERS — and the comparisons that are invalid
**`esc_current` is the loaded/unloaded discriminator:** ±1 A at rest against −12…+8 A moving.
**`/odom` DRIFTS AT STANDSTILL** (~0.38 m/min at 0 rpm, the camera-gyro term) ⇒ corroborate with
IMU `sensor_combined`; never trust `/odom` alone.

⛔ **The 0.345 m standoff (n=3, tape) and the "~0.30 m coast at 0.9 m/s" are NOT the same kind of
number.** The latter is **distance-before-contact** — it left 0.020 m and **contacted**. It is not
a stopping distance and **must never be compared against a braking figure.**

⚠️ **S1's recorded "<20 ms to wheels zero" is SUSPECT.** Disarm cannot physically stop a rolling
rover in 20 ms; that is very likely the **ESC zero-dropout** reporting 0 rpm while the wheel still
turns. **Re-measure against `esc_current` when S1 is re-run.**

**`/scan` reads SHORT** (scale 0.9845) ⇒ the reflex fires **early**, which is the safe direction.
⚠️ Read `autonav_reference` §5 / §12 / §13 before quoting any of these.

## 🔑🔑 `esc_rpm` IS **MECHANICAL** RPM — THE FACTOR AGAINST ERPM IS **7** (MEASURED 2026-09-12)

⛔ **`uavcan_raw_rpm_max` is ELECTRICAL RPM (`set_pid_speed` takes ERPM); `esc_rpm` on DDS is
MECHANICAL.** The ESC divides by pole pairs = `si_motor_poles`/2 = **7**. Measured twice on addr 13,
at two caps 4.67× apart:

| `uavcan_raw_rpm_max` | predicted ÷7 | measured plateau | n |
|---|---|---|---|
| 300 | 42.9 | **42** (40–43) | ~20 |
| 1400 | 200 | **194** (192–197) | ~25 |
| 8000 | 1143 | **1136** | 672 |
| 9000 | 1286 | **1273** | 729 |

⛔ **DO NOT compute a cap as `target_m_s / 0.0039` and write it to `uavcan_raw_rpm_max`** — that
gives the MECH number; multiply by 7. 🔑 Tracking is 97–99% of setpoint (loop sits just under).
🔑 **Geometry cross-check, NOT a reason to re-open the scale:** the tyre is **6 inch** (0.1524 m,
NOT the `si_wheel_diameter` 0.083 in the mcconf), which predicts 0.0080 m/s per reported rpm vs the
tape-validated 0.0039 — almost exactly 2×. That is the known `si_motor_poles` 14-vs-28 pairing; the
two errors cancel. ⛔ **`erpm_to_ms` 0.0039 STAYS — fixing poles silently halves `/odom`.**

## ✅✅ ALL FOUR ESCs ARE IN RPM MODE AS OF 2026-09-12 — THE TORQUE-MODE ERA IS OVER

⛔⛔ **THE SECTION BELOW IS HISTORY. Do NOT quote "the ESCs run in CURRENT/torque mode" — it was
true until 2026-09-12 and is now FALSE on all four.** Every wheel: `uavcan_raw_mode` 3 ·
`uavcan_raw_rpm_max` 9000 · `s_pid_min_erpm` 200 · `s_pid_ramp_erpms_s` 20000.
✅ **VERIFIED ON STANDS, all four at once:** forward means **985.4 / 982.6 / 986.7 / 983.5** (FR/FL/
RR/RL) — **4 rpm spread, 0.4%** — peaks 1261–1272 against the 1286 cap, 499/499 samples POSITIVE on
every address, reverse −932…−941. 🔑 **Cap = 1265 rpm ≈ 4.93 m/s ≈ 17.8 km/h**, and
**`RO_MAX_THR_SPEED` was set 0.60 → 4.93** to match (RAM write 09-12).
⚠️ **ALL OF IT IS UNLOADED.** Stands cannot show sag, slip or turn scrub. ⏭ the floor run is what
validates commanded-vs-measured.
⚠️ **NEW BEHAVIOUR TO WATCH: four INDEPENDENT speed loops do not share load.** In torque mode the
wheels slipped and shared during a turn; now each one forces its own number ⇒ expect scrub and
higher current in turns. Unverified.
📂 **The live configs are in git:** `PXLABS_BLDC_VESC6_MK5`, branch **`pxlabs-6.06-rover-uavcan_main`**,
`Motor_Config_Bldc/*_12_Sep_Rc.xml` — verified against the files, and the `controller_id` →
`uavcan_esc_index` map is correct (10→0, 12→2, 13→3). ⇒ `configs_live/` in codex-work is SUPERSEDED.

### ⛔ HISTORY — the CURRENT-mode finding, TRUE ONLY BEFORE 2026-09-12

All four `configs_from_repo/vesc_appconf_*.xml` carry **`uavcan_raw_mode = 0` =
`UAVCAN_RAW_MODE_CURRENT`**, and a wheels-up ladder confirmed it behaviourally: **speed was FLAT at
~1505 ERPM from 0.148 stick to full stick**, ~2.0 A throughout. With no load, any torque above
friction accelerates to the same back-EMF ceiling; the stick only changes how fast it gets there.
⚠️ The config value has **never been read off live hardware** (needs USB) — open in `RESUME.md`.

🔑 **CONSEQUENCES, and they are structural:**
- `RO_MAX_THR_SPEED` assumes **throttle ∝ speed**, which is a DUTY-mode property. ⛔ **It cannot be
  calibrated to a single correct value** — in torque mode speed depends on the load/surface.
- ⛔ **A WHEELS-UP TEST CANNOT MEASURE A THROTTLE→SPEED CURVE HERE.** It saturates. Run it loaded.
- **Lower stick is REVERSE, not brake** — which is exactly why a separate brake slot had to exist.

→ full reasoning, numbers and the unresolved ~10× speed-scale conflict: [[project_rover_autonav]]
2026-09-12.
