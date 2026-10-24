---
name: esc_golden_config
description: "Which ESC settings are OURS and which 24 the VESC wizard owns, where the machine-readable baseline lives, the three traps that cost 2026-10-20, and the 10-24 four-way alignment audit - including why a MAJORITY VOTE across wheels is not a ruler (si_wheel_diameter: the three that agree are the wrong ones)."
metadata: 
  node_type: memory
  type: reference
  originSessionId: ba4f4888-e93e-43d7-9ba3-d0717e129258
  modified: 2026-10-24T09:55:19.310Z
---

# ESC config — ours vs the wizard's, and how to check a board in one command

Procedure: **`codex-work/bldc_can/ESC_SETUP_PLAN.md`** · values: **`bldc_can/ours.json`** ·
one command: **`python3 diag/check_ours.py /dev/ttyACM0 --expect FL`** (READ-ONLY, identifies the
board by `controller_id`, archives both configs, prints functional vs cosmetic deviations, the
current-loop bandwidth, the wizard output, and a COVERAGE line).
Related: [[esc_config_audit]], [[vesc_tool_cli]], [[rover_odometry]], [[esc_telemetry]].

## 🔑 THE SPLIT — the wizard owns 24 FIELDS, EVERYTHING ELSE IS OURS

⛔ **"everything `foc_*` is the wizard's" IS WRONG.** 57 `foc_*` fields are deliberate policy —
`foc_mtpa_mode` 1 (MTPA, enabled on all four 2026-09-26), `foc_observer_type` 3, `foc_sat_comp_mode`
1, `foc_sl_erpm` 3000, `foc_openloop_rpm` 1200, the HFI block, the phase-filter block, `foc_pll_*`.
The wizard's 24: `foc_motor_r/l/ld_lq_diff/flux_linkage`, `foc_observer_gain`, `foc_current_kp/ki`,
`foc_hall_table__0..7`, and the nine current/voltage offsets. `ours.json` pins **169 of 198 mcconf +
19 of 21 appconf** fields, every shared value verified identical across all four Sep 26 configs.

🔑 **`foc_current_kp/ki` sit across the line: the wizard measures L and R, THE BANDWIDTH IS OURS AND
IT IS 2000 rad/s.** kp = L × 2000, ki = R × 2000 on that board's own fresh measurements. All four
Sep-26 configs divide out to ω ≈ 2000; a wizard run leaves ω = 1000, i.e. half. ⚠️ their kp/ki
VALUES differ per wheel because L and R differ — ⛔ never copy a neighbour's kp/ki, recompute.

## 🔴 THE THREE TRAPS OF 2026-10-20

1. **CAN fighting detection.** `can_mode` 1 + `uavcan_raw_mode` 3 means a powered FC publishes ESC
   setpoints the board obeys *while the wizard drives the motor*. R, L and hall detection survive
   it (stationary / low-speed); **the λ step silently returns the 0.1 DEFAULT with
   `foc_observer_gain` 100000.** 🔑 λ and gain are a coherent pair — `1000/λ²` must equal the stored
   gain (0.1 → 1e5; 0.015632 → 4.09e6), which is how you tell a measurement from a default.
   Fix: CAN lead OFF (or FC unpowered) and `timeout_brake_current` 0 for the run — `timeout_msec`
   300 otherwise brakes into the detection.
2. **An identity swap reads as a cable swap.** A board claiming `controller_id` 12 while holding
   FL's limits, invert flag and presets is FL with RR's appconf applied, not RR on the bench.
   ⛔ `controller_id` + `uavcan_esc_index` are refused by the field-setters on purpose; the
   deliberate exception is `diag/restore_fl_identity.py`, which checks a 5-field mcconf fingerprint
   first. Address 12 is a RIGHT-side motor in PX4's mapping, so FL sitting there is a drive hazard.
3. **A false "READBACK MISMATCH — do not drive".** The device re-serialises floats (8370000 →
   `8.37e+06`, 1023.40 → `1023.4`), and the old whole-text compare called that a failed write.
   ✅ fixed: `tune_esc.verify()` compares per field, numerically. 🔑 "write OK" from vesc_tool means
   the write landed; only the comparator was lying.

## 🔑 HALL TABLE ENTRIES WRAP — 199, 1 AND 0 ARE THE SAME ANGLE

The table is 8 slots indexed by hall state (0 and 7 always 255 = invalid) holding **angle in counts
of 200 per electrical revolution**. So 199 → 0 is **+1 count = 1.8°**, not a missed sector. FL's
350 W motor and three untouched 250 W boards agree within **+1/−1/+2/+3/0/+1 counts**, and RR reads
1 in slot 1 where FL-OLD reads 199. ⛔ **Do not call a slot-1 outlier a fault on the raw number** —
⚠️ this casts doubt on the *stated reason* in [[esc_config_audit]] for the 2026-09-14 RR restore;
the cross-wheel speed-disagreement measurement there still stands, the angle argument does not.

## ✅✅ ALL FOUR ARE 350 W NOW — 2026-10-24, AND `ours.json` WAS THE THING THAT WAS WRONG

⛔ **Do NOT read the FL section below as "one 350 W wheel and three 250 W wheels" any more.** All
four motors were replaced and re-detected. **Measured, not assumed:** λ reads **0.016191 (FR) ·
0.015439 (FL) · 0.015730 (RR) · 0.016693 (RL)** — every one clustered on FL's 350 W signature
0.015632 and every one ~40 % above the 250 W band 0.0104-0.0116. Limits **14/−14/20/15** on all four.

🔑🔑 **THE LESSON, AND IT WILL RECUR: `check_ours.py` REPORTED FOUR FUNCTIONAL DEVIATIONS PER WHEEL
ON FR/RR/RL AND ALL FOUR WERE FALSE.** `ours.json` still had those three as `250W` with 25/−25/35/20,
so the auditor flagged boards that were already correct. ⛔ **Never "restore" a current limit because
check_ours says so — confirm the motor rating from λ first.** Writing 25 A to a 350 W motor would
have been a thermal decision taken by a stale JSON file. Fixed the same day; all four now read 0
functional deviations. ⇒ **When the hardware changes, `ours.json` is a thing that must be EDITED,
and it is the likeliest stale ruler in this repo.**

🔴 **`m_invert_direction` WAS 1 ON ALL FOUR — THE RIGHT PAIR RAN BACKWARDS.** Written **1 → 0 on FR
(10) and RR (12)**. On a differential drive this flag is **MIRRORED: left 1, right 0**, otherwise
+ERPM drives the two sides in opposite physical directions. Confirmed twice — the config read, and
the operator watching each wheel spin. 🔑 **The all-four-identical pattern is the fingerprint of a
rebuild/re-detection, so CHECK THIS FLAG AFTER ANY MOTOR WORK.**
🔴 **FL alone was `uavcan_raw_mode` 0 (CURRENT) while the other three were 3 (RPM)** — written to 3.
A mixed-mode fleet means the FC's four setpoints do not mean the same thing on each wheel.

📂 **Restore point: `configs_by_motor/350W_14pole_geared/*_20261024_1102_*`** (committed `190696f`),
read after the fixes and deliberately **before a power cycle**. ⛔ **APPCONF IS PER WHEEL — there is
no COMMON file and one was deleted on purpose:** 19 of 21 fields are identical but `controller_id`
and `uavcan_esc_index` differ, so a shared file makes every board claim one node (and address 10 is
a RIGHT-side motor in PX4's mapping ⇒ drive hazard, not just a comms fault). → folder `README.md`

⚠️ **Current loops are still BELOW ω 2000** — measured 833 (FR) · 833 (FL) · 1000 (RR) · 1667 (RL).
Recomputed per board, ready to write: FR 1.0191/1114.80 · FL 1.1205/986.00 · RR 1.0054/830.60 ·
RL 1.1809/1001.80. ⛔ never copy a neighbour's kp/ki.
🔑 **`l_watt_max` 350 BINDS BEFORE `l_in_current_max` 15 A** — at 24.6 V, 350 W = 14.2 A battery-side,
so each wheel is power-limited at nameplate. Whether that is permanent or break-in is STILL the
operator's open decision.

## ✅✅ FOUR-WAY ALIGNMENT AUDIT, 2026-10-24 (post-reflash) — 2 FIELDS WERE OFF, BOTH NOW FIXED

Method worth reusing: read live appconf+mcconf off **all four at once**, diff every field across
wheels, and **classify** each difference as *expected-per-wheel* or *unexpected*. That separates the
~20 fields that MUST differ (the wizard's 24, `m_invert_direction`, the ADC offsets, the identity
pair) from real drift, which is otherwise invisible in a per-board audit like `check_ours.py`.

✅ **Confirmed aligned:** `si_motor_poles` **14 on all four** · `uavcan_esc_index` 0/1/2/3 correctly
paired to `controller_id` 10/11/12/13 · `uavcan_raw_mode` 3 and `can_baud_rate` 3 (=1 Mbit) on all
four · `m_invert_direction` correctly **mirrored** (FR 0, RR 0 / FL 1, RL 1).

🔴🔴 **`si_wheel_diameter` — FL 0.155, the other three 0.165. THE MAJORITY IS WRONG.** 0.155 is the
**measured, documented** wheel (see the FL section below, and
`ros2_ws/src/rover_odometry/config/rover_odometry.yaml:25-57`) ⇒ **FL is the correct board and
FR/RR/RL drifted up.** ⛔⛔ **DO NOT "FIX" FL TO MATCH THE OTHER THREE** — I proposed exactly that
from a three-against-one count and it was backwards. 🔑🔑 **A MAJORITY VOTE IS NOT A RULER WHEN A
MEASURED VALUE IS ALREADY ON RECORD — check the record first.** ⚠️ Cosmetic either way: this field
reaches nothing we consume (only `si_motor_poles` enters CAN rpm), which is why it drifted unseen.
✅✅ **RESOLVED 10-24 — FR/RR/RL WRITTEN DOWN TO 0.155, ALL FOUR NOW AGREE.** 🔑🔑 **THE TIRE IS
6 INCH AND THAT ARITHMETIC IS THE RULER THAT SETTLED IT:** 6″ nominal = **0.1524 m**, so 0.155 is a
plausible measured OD just over nominal — while **0.165 is exactly 6.5″** (6.5 × 25.4 = 165.1 mm),
i.e. a DIFFERENT WHEEL SIZE, not a measurement of this one. ⇒ the three agreeing boards carried a
spec for a wheel the rover does not have.

⚠️ **`can_status_msgs_r1` — FR 9, the other three 1** (firmware default is **0**, so 1 is the house
value). Bitmask gating the extra VESC-specific RtData broadcasts below the esc.Status send, so FR
emits one message type the others do not. Harmless to control; it is extra bus traffic.
🔑 It **survived the reflash** because the restore faithfully wrote back the pre-flash value — a
restore propagates drift, it does not clean it.
✅ **FIXED 10-24 → 1 on all four**: `diag/set_appconf_field.py <port> --expect-id 10 can_status_msgs_r1 1`.

✅✅ **POST-FIX RE-AUDIT: ZERO unexpected differences in BOTH appconf and mcconf across all four**
(`si_wheel_diameter` 0.155 · `can_status_msgs_r1` 1 · `si_motor_poles` 14, everywhere). ⚠️ The
`*_1524_*_pre.xml` per-field backups in `configs_live/` are the as-found values if this needs undoing.
⛔ **This did NOT change odometry** — `erpm_to_ms` = 0.003900 is tape-verified and stays CLOSED;
`si_wheel_diameter` reaches nothing we consume. ⛔ Do not let a tire measurement reopen that scale.

🔑 **The field-setters are the safe path and they self-guard:** they read the target's OWN config,
edit only the named fields, write the rest back byte-identical, and **refuse if `controller_id` does
not match `--expect-id`** — so a reshuffled ttyACM cannot hit the wrong motor. Both have `--dry-run`,
which is what caught the `si_wheel_diameter` mistake above before anything was written.

## FL's 350 W swap — closed 2026-10-20 01:57 (⚠️ NOW HISTORY, see the 10-24 section above)

Golden pair: `configs_by_motor/350W_14pole_geared/FL_350W_14pole_geared_20261020_0157_*`. Zero
functional deviations. λ **0.015632** measured (≈40% above the four 250 W motors' 0.0104-0.0116, so
the 350 W unit is NOT magnetically identical even though it is mechanically the same 14-pole part).
Limits 14/−14/20/15 — ⚠️ `l_watt_max` 350 means 14 A ≈ 336 W, so current and power now bind
together; still undecided whether that rating is permanent or break-in.
🔑 **Gear ratio is 1 and the wheel is 0.155 m** — the Sep-26 files' 3 and 0.083 are a disproved
drivetrain assumption (`ros2_ws/src/rover_odometry/config/rover_odometry.yaml:25-57`). Neither field
reaches anything we consume; only `si_motor_poles` enters CAN rpm, and it stays **14** ([[rover_odometry]]).
