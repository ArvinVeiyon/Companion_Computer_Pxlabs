# 350 W 14-pole geared — the live config set

## ⚠️ UNDER TESTING — the current set: `20261024_1527_undertesting`

**This is the only config set to use right now, and it is UNDER TESTING — not a proven restore
point yet.** Read off all four boards at 15:27 on 2026-10-24, after reflashing every ESC to the
brake-free **r1** build and after that afternoon's two alignment fixes. A four-way field-by-field
audit of this set reports **zero unexpected differences** in both appconf and mcconf — the only
remaining cross-wheel differences are the ones that must differ (the wizard's 24, the mirrored
invert flag, the ADC offsets, and the `controller_id`/`uavcan_esc_index` identity pair).

⚠️ **It has not been driven under load in this state.** Until it has, `20261024_1102` below remains
the last set that was proven on the floor.

| wheel | node | files | `m_invert_direction` |
|---|---|---|---|
| FR | 10 | `FR_350W_14pole_geared_20261024_1527_undertesting_{mcconf,appconf}.xml` | **0** (right side) |
| FL | 11 | `FL_..._20261024_1527_undertesting_*` | 1 (left side) |
| RR | 12 | `RR_..._20261024_1527_undertesting_*` | **0** (right side) |
| RL | 13 | `RL_..._20261024_1527_undertesting_*` | 1 (left side) |

### Firmware that goes with this set

All four ESCs run the **r1 brake-free build**, flashed over USB on 2026-10-24, each board
re-identified by `controller_id` immediately before its own flash.

🔴 **The r1 *release binary* is NOT a build of the r1 tag.** It embeds
`67ca4de09604a0a2201c597700590dada55f6204-dirty` (branch `px4_uavcan_reversible`) — an *ancestor* of
the tag plus uncommitted edits — while the tag itself is `6fc2cf17337ce6d1e494c47a5969b93acac0661e`.
🔑 **Both builds report `6.6 60_MK5`, so the version string cannot distinguish them.** Read the
embedded commit instead: `strings <bin> | grep -E '[0-9a-f]{40}'`. A clean build of the tag is
pending (`make arm_sdk_install` then `make 60_mk5` — the **Trampa** target, not `flipsky_60_mk5`).
⛔ `Testing_Bin/60_mk5.bin` in the firmware repo is the **r2-alpha1 brake build** (`a75a0dbf`), not
this one.

PX4 side to match: **`UAVCAN_EC_FUNC5`/`FUNC6` cleared to 0** (were 407/301), so no brake demand is
sent and RawCommand now sizes to 4 entries instead of 6.

## The previous set: `20261024_1102`

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
4. **All four reflashed to the brake-free r1 build** (15:00–15:10), configs backed up first and
   restored after. appconf came back byte-identical on every board; mcconf differed only in the six
   `foc_offsets_current/voltage__0..2`, which the firmware **rewrites at startup** via the
   `m_dccal_done` path in `motor/mcpwm_foc.c`. ⛔ Never read those six as a failed restore.
5. **Two alignment fixes** (15:24), each written with `--expect-id` and verified by readback:
   - `si_wheel_diameter` **0.165 → 0.155 on FR, RR and RL.** FL was already correct. 🔑 The tire is
     **6 inch** = 0.1524 m nominal, so 0.155 is a measured OD just over nominal, whereas **0.165 is
     exactly 6.5″** (6.5 × 25.4 = 165.1 mm) — a different wheel size the rover does not have.
     🔴 **The three boards that agreed were the wrong ones** — a majority vote across wheels is not
     a ruler when a measured value is already on record.
   - `can_status_msgs_r1` **9 → 1 on FR** (firmware default is 0; the other three read 1). It gates
     the extra VESC-specific RtData broadcasts, so FR was emitting a message type the others did
     not. It survived the reflash because the restore faithfully replayed the pre-flash value — a
     restore propagates drift, it does not clean it.

## Verified this day: node ↔ corner

**10 = FR · 11 = FL · 12 = RR · 13 = RL**, each wheel spun **alone** and named by the operator.
This closes a caveat that had stood since the mapping was first written from config files only.

PX4 cannot do this test: `UAVCAN_EC_FUNC1/3` are both Motor1 and `2/4` both Motor2, so every
FC-side command reaches two wheels at once. Driving exactly one wheel needs `COMM_SET_RPM` down
that board's own USB port — `diag/spin_one_wheel.py`, which keeps the FC out of the loop entirely
(no arming, no EKF bridge) and relies on the VESC's own 300 ms command timeout to stop the wheel.

## Still open

- **Current loops sit below our bandwidth.** ω measures 833 (FR), 833 (FL), 1000 (RR), 1667 (RL)
  against our 2000 rad/s. `foc_current_kp/ki` must be **recomputed per board** from that board's own
  L and R — never copied from a neighbour. Values ready: FR 1.0191/1114.80 · FL 1.1205/986.00 ·
  RR 1.0054/830.60 · RL 1.1809/1001.80.
- **`l_watt_max` 350 / 14 A**: still undecided whether that is the permanent rating or a break-in
  rating.
- ~~`si_wheel_diameter` reads 0.165 against our 0.155 on FR/RR/RL.~~ **CLOSED 2026-10-24** — all
  four written to 0.155, confirmed against the 6-inch tire. Was cosmetic (it reaches nothing we
  consume); ⛔ it did **not** change odometry — `erpm_to_ms` = 0.003900 stays tape-verified and
  closed.
- ⏭ **This set has not been driven under load.** That is the test that would promote
  `20261024_1527_undertesting` from "under testing" to the restore point.
