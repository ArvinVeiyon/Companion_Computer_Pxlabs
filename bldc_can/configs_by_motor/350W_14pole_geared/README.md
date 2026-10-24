# 350 W 14-pole geared — the live config set

## The set to restore from: `20261024_1102`

Read off all four boards on 2026-10-24 at 11:02, immediately after the two fixes of that day and
with `check_ours.py` reporting **0 functional deviations on every wheel**. This is the restore
point. Taken deliberately **before a power cycle**, so it also serves as the proof of what was in
flash beforehand.

| wheel | node | mcconf | appconf | `m_invert_direction` |
|---|---|---|---|---|
| FR | 10 | `FR_..._mcconf.xml` | `FR_..._appconf.xml` | **0** (right side) |
| FL | 11 | `FL_..._mcconf.xml` | `FL_..._appconf.xml` | 1 (left side) |
| RR | 12 | `RR_..._mcconf.xml` | `RR_..._appconf.xml` | **0** (right side) |
| RL | 13 | `RL_..._mcconf.xml` | `RL_..._appconf.xml` | 1 (left side) |

**All four motors are 350 W as of this date** — not just FL. Measured, not assumed: `flux_linkage`
reads 0.016191 / 0.015439 / 0.015730 / 0.016693 (FR/FL/RR/RL), all clustered on FL's 350 W signature
0.015632 and all ~40 % above the 250 W band of 0.0104–0.0116. Limits are 14/−14/20/15 on all four,
with `l_watt_max` 350; at a 24.6 V pack that power cap binds at **14.2 A battery-side**, i.e. just
*before* `l_in_current_max` 15 A, so each wheel is effectively power-limited at its nameplate.

## ⛔ APPCONF IS STORED PER WHEEL — ON PURPOSE, AND THERE IS NO COMMON FILE

The four appconfs were diffed field by field: **19 of 21 fields are identical, and exactly two
differ — `controller_id` and `uavcan_esc_index`.** So a single shared appconf is tempting, and a
`COMMON_*_appconf.xml` was briefly written here on 2026-10-24. **It was deleted deliberately.**

🔴 Any common appconf is a byte copy of *some* wheel, so it carries that wheel's node ID. Restoring
it to all four makes **every board claim the same node**: three wheels go deaf to the FC and the bus
gets a four-way ID collision. Worse, PX4 maps address 10 to a **right-side** motor, so a left wheel
answering as 10 is a drive hazard, not merely a comms fault — the trap already on record as "an
identity swap reads as a cable swap".

⇒ **One appconf per wheel, restored only to that wheel.** The two identity fields are also refused
by `diag/set_appconf_field.py` by design, so there is no quick repair path if they get crossed —
which is exactly why the per-wheel files are the only form kept here.

## What changed on 2026-10-24

1. **`m_invert_direction` 1 → 0 on FR (10) and RR (12).** It was 1 on all four, so the right pair
   ran backwards against the left pair. Caught by reading the config, then confirmed by the operator
   watching each wheel turn. On a differential drive this flag **must** be mirrored.
2. **`uavcan_raw_mode` 0 → 3 on FL (11).** FL alone was in CURRENT/torque mode while the other three
   were in RPM mode, so the FC's four setpoints did not mean the same thing on every wheel.
3. **`ours.json` corrected** — it still described FR/RR/RL as 250 W with 25 A limits, so it was
   reporting four *false* functional deviations per wheel. The boards were right; the file was stale.

## Verified this day: node ↔ corner

**10 = FR · 11 = FL · 12 = RR · 13 = RL**, each wheel spun **alone** and named by the operator.
This closes a caveat that had stood since the mapping was first written from config files only.

PX4 cannot do this test: `UAVCAN_EC_FUNC1/3` are both Motor1 and `2/4` both Motor2, so every
FC-side command reaches two wheels at once. Driving exactly one wheel needs `COMM_SET_RPM` down
that board's own USB port — `diag/spin_one_wheel.py`, which keeps the FC out of the loop entirely
(no arming, no EKF bridge) and relies on the VESC's own 300 ms command timeout to stop the wheel.

## Still open

- **ESC → FC telemetry is silent.** `esc_status` published 0 messages in 30 s over DDS while
  `vehicle_status_v1` flowed normally. The command direction works (the rover drives from RC), so
  this is the **status-broadcast direction only**. Not yet diagnosed; the DroneCAN driver source is
  at `~/apps/bldc_vesc6_mk5/libcanard/canard_driver.c`.
- **Current loops sit below our bandwidth.** ω measures 833 (FR), 833 (FL), 1000 (RR), 1667 (RL)
  against our 2000 rad/s. `foc_current_kp/ki` must be **recomputed per board** from that board's own
  L and R — never copied from a neighbour. Values ready: FR 1.0191/1114.80 · FL 1.1205/986.00 ·
  RR 1.0054/830.60 · RL 1.1809/1001.80.
- **`l_watt_max` 350 / 14 A**: still undecided whether that is the permanent rating or a break-in
  rating.
- `si_wheel_diameter` reads 0.165 against our 0.155 on FR/RR/RL. Cosmetic — it reaches nothing we
  consume.
