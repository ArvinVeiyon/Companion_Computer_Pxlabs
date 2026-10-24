# ESC setup plan — one wheel at a time

Written 2026-10-20 after FL's 350 W motor swap. Companion to `configs_by_motor/README.md`.
**The settings themselves live in `ours.json`. This file is the procedure.**

Tools, all of which identify the board by `controller_id` and never by the port:

| tool | what it does |
|---|---|
| `diag/check_ours.py <port> [--expect FL]` | **READ-ONLY.** Reports deviations from `ours.json`, splits functional from cosmetic, checks the current loop against the board's own L and R, prints the wizard output, archives both configs |
| `diag/set_mcconf_field.py <port> --expect-id <id> FIELD VALUE …` | writes named mcconf fields, one transaction, readback-verified |
| `diag/set_appconf_field.py <port> --expect-id <id> FIELD VALUE …` | same for appconf; refuses `controller_id` / `uavcan_esc_index` |
| `diag/restore_fl_identity.py <port>` | the deliberate exception for FL's identity; refuses unless the mcconf fingerprint is FL's |

## Ground rules

1. **One ESC on USB at a time.** It is always `/dev/ttyACM0`, whichever board it is, so the only
   trustworthy name is `controller_id`. Run `check_ours.py --expect <wheel>` first and let it refuse
   if the board is not the one you think you plugged in.
2. **CAN lead off the ESC being tuned.** With `can_mode` 1 / `uavcan_raw_mode` 3 a powered FC
   publishes ESC setpoints and fights the wizard — that is what left λ at the 0.1 default on
   2026-10-20. `timeout_msec` 300 with `timeout_brake_current` 2 also brakes into a detection run
   when the bus goes quiet. Both were disabled for the run that finally measured λ.
3. **Never write one wheel's config into another.** Restores are per-field from `ours.json`. A
   whole-file write from a neighbour carries its identity, its direction and its current limits —
   on 2026-10-20 RR's identity ended up on FL exactly this way.
4. **Only one program can hold the serial port.** If VESC Tool is connected, my reads fail; if I am
   reading, its connect fails. Close one before the other.
5. **No write without an explicit yes**, every write readback-verified field by field.
6. Wheel off the ground and free to spin for anything that turns the motor.

## What is ours and what is the wizard's

**The wizard owns exactly 24 fields. Everything else on the board is ours.** Not "everything except
`foc_*`" — that rule was wrong, because plenty of `foc_*` fields are policy we set deliberately.
`foc_mtpa_mode` 1 is the clearest case: MTPA was enabled on all four wheels on 2026-09-26
(`configs_live/archive/2026-09/*_mtpa_all_*`), it is still 1 on FL after tonight's two wizard runs,
and it is ours, not a measurement — though it does consume the wizard's `foc_motor_ld_lq_diff`.
The same goes for `foc_observer_type` 3, `foc_sat_comp_mode` 1, `foc_sl_erpm` 3000,
`foc_openloop_rpm` 1200, the HFI block, the phase-filter block, `foc_pll_*` and the rest.

The wizard's 24: `foc_motor_r`, `foc_motor_l`, `foc_motor_ld_lq_diff`, `foc_motor_flux_linkage`,
`foc_observer_gain`, `foc_current_kp`, `foc_current_ki`, `foc_hall_table__0..7`, and the nine
current / voltage offsets. Read them, archive them, never restore them from a file.

`ours.json` now pins **169 of the 198 mcconf fields and 19 of the 21 appconf fields** — all 24
wizard fields excluded, the 5 per-wheel fields held per wheel, and every value in the shared blocks
verified identical across all four Sep 26 configs. `check_ours.py` prints a COVERAGE line so an
unaccounted-for field shows up instead of passing silently.

**`foc_current_kp` / `foc_current_ki` sit across the line.** The wizard measures L and R; the
bandwidth is ours, and ours is **2000 rad/s** — all four Sep 26 configs work out to kp/L ≈ ki/R ≈ 2000.
So the rule is kp = L × 2000 and ki = R × 2000 **on that board's own fresh measurements**, which is
what `check_ours.py` prints.

### Three fields that must not be "fixed"

- **`si_motor_poles` 14** is the pole-*pair* count sitting in a pole-*count* field. The firmware
  divides CAN rpm by `si_motor_poles / 2` (`libcanard/canard_driver.c:494`) and `erpm_to_ms`
  0.003900 is tape-fitted to that error. They are a linked pair: correcting poles alone makes
  `/odom` read 2× short, silently, into PX4's speed loop.
- **`s_pid_ramp_erpms_s` 20000** is what makes the collision reflex an actual brake, and on a
  differential drive it also sets yaw onset. Never reduced for comfort.
- **`l_battery_regen_cut_start` 25.2 / `_end` 25.4.** Regen is already cut on a charged pack;
  raising the cut-in was ruled out.

### Settled, so no longer open questions

- **Gear ratio is 1.** These are direct-drive hub motors — `rover_odometry.yaml:25-57` disproved the
  3:1 assumption with six hand-rotation runs over four wheels. The Sep 26 files saying 3 are wrong,
  and `check_ours.py` will flag it on every board that still holds 3.
- **Wheel diameter is 0.155 m**, physically measured; 6" nominal runs over nominal. The old 0.083
  looks like a radius.
- Both are cosmetic: neither reaches anything we consume, because only `si_motor_poles` enters the
  CAN rpm and `/odom` scales ERPM in our own node.
- **`si_battery_type` 0.** FR, RR and RL all hold 0; FL-OLD's 1 was the outlier, and the wizard
  moved FL to 0, which brings it into line. Cuts stay at `l_battery_cut_start/end` 20.4 / 18.6,
  which is 3.40 / 3.10 V across `si_battery_cells` 6.

## Phase 1 — FL, COMPLETE 2026-10-20 01:57

`check_ours.py --expect FL` reads **0 functional, 0 cosmetic deviations, 198 + 21 fields, 0
unaccounted for.** Golden pair saved as
`configs_by_motor/350W_14pole_geared/FL_350W_14pole_geared_20261020_0157_{mcconf,appconf}.xml`,
holding id 11 / idx 1, `timeout_brake_current` 2, kp 1.1447 / ki 1023.4 at ω 2000, λ 0.015632,
`si_wheel_diameter` 0.155, limits 14 / −14 / 20 / 15. The superseded 00:01 and 00:23 references
moved to `configs_live/archive/` rather than being deleted.

Still undecided on FL: whether **14 / −14 / 20 / 15** is the permanent rating or a break-in setting.
`l_watt_max` is 350 and 14 A at pack voltage is ≈ 336 W, so FL's current limit and power cap now
bind at the same point, where the 250 W wheels at 25 A hit the 350 W cap first.

### What was done to get there (history)

Already on the board and verified: identity `controller_id` 11 / `uavcan_esc_index` 1 restored,
`timeout_brake_current` 2, λ measured at **0.015632** with `foc_observer_gain` 4.09e+06 self-consistent
(1000/λ² = 4092332), hall table agreeing with the 250 W motors within 3 counts, and **zero functional
deviations** from `ours.json`.

Outstanding, pending a yes:

1. `foc_current_kp` 0.5724 → **1.1447** and `foc_current_ki` 511.7 → **1023.40** — ω 1000 → 2000 on
   FL's own L 0.00057237 and R 0.5117. The one functional item.
2. `si_wheel_diameter` 0.165 → 0.155 — cosmetic, bundle it into the same transaction or skip.
3. Decide whether **14 / −14 / 20 / 15** is FL's permanent rating or a break-in setting. Note that
   `l_watt_max` is 350 and 14 A at pack voltage is ≈ 336 W, so FL's current limit and power cap now
   bind at the same point, where the 250 W wheels at 25 A hit the 350 W cap first.

Then re-save the golden pair into `configs_by_motor/350W_14pole_geared/` — its appconf reference is
stale, still showing `timeout_brake_current` 0 — and reconnect CAN without driving, confirming
address 11 appears exactly once.

## Phase 2 — the other three, one at a time

Order: **FR (10), then RL (13), then RR (12).** RR last: it is the demagnetised one and is due for
replacement, so tuning it before the swap is wasted work.

For each wheel, with the CAN lead off and only that ESC on USB:

1. `python3 diag/check_ours.py /dev/ttyACM0 --expect FR` — it refuses if the board is not FR, and
   archives both configs before anything else happens.
2. **Contamination check.** The identity swap on 2026-10-20 may have gone both ways, so FL's appconf
   may be sitting on one of these boards. `check_ours.py` catches it: `uavcan_esc_index` and
   `m_invert_direction` wrong for the reported `controller_id`, or 350 W limits on a 250 W wheel.
   `controller_id` itself is the one field the field-setters refuse — if it is wrong, say so and I
   will write a fingerprint-guarded one-off like `restore_fl_identity.py`.
   Expected per wheel: FR id 10 / idx 0 / invert 0 · RL id 13 / idx 3 / invert 1 · RR id 12 / idx 2 /
   invert 0. All three keep the 250 W limits 25 / −25 / 35 / 20.
3. You run the auto-tune if that wheel needs one. Enter **14 poles** and leave direct-drive
   unticked, or the preset overwrites both.
4. `check_ours.py` again, then **one** `set_mcconf_field.py` transaction for the functional
   deviations plus kp/ki rebased on that board's fresh L and R, and `set_appconf_field.py` for any
   appconf items.
5. `check_ours.py` a third time — it should read zero functional deviations.
6. Save the golden pair as a **new dated file** under `configs_by_motor/250W_14pole_geared/`. The
   Sep 26 files stay as history and are never overwritten.
7. Unplug, next wheel.

## Phase 3 — all four back on the bus

1. Addresses 10, 11, 12, 13 each appear **exactly once** in `esc_online_flags` over DDS, keyed on
   `esc_address` — not by position in the array, and not from QGC, whose ESC health light is
   permanently lit here. An absent ESC is indistinguishable from an unpowered one, so check power
   before diagnosing CAN.
2. `si_motor_poles` 14 on all four, confirming `/odom` scale is unchanged.
3. Direction per wheel on the stand, one wheel at a time, before any paired motion.
4. Only then powered tests. Kill switch is **ch12**.

## Where the files live

- `configs_by_motor/350W_14pole_geared/` — FL's golden pair. `250W_14pole_geared/` — the other three
  plus FL's old motor, dated Sep 26. Eight files, one pair per wheel; that folder is already tidy.
- `configs_live/` — working output, now **33 files, all from 2026-10-20**. The 413 older files moved
  to `configs_live/archive/2026-09/` and 8 throwaway probe files to `configs_live/archive/probes/`
  on 2026-10-20. **Nothing was deleted.**
- Keep it that way per session: the `_pre` / `_post` / `_readback` triplets are the audit trail of a
  write and are worth keeping until the golden pair is re-saved; the `_check_READONLY` pairs and
  the `_`-prefixed probes are disposable.

## Still open

- λ on FL measures 0.015632 against 0.0104-0.0116 on the four 250 W motors — about 40% higher, so
  the 350 W unit is not magnetically identical even if it is mechanically the same part. Keep the
  measurement; just do not expect the other three to land near it.
- `tune_esc.apply` and `diag/set_mcconf_field.py` still compare readback as whole text, so an
  exponent reformat (8370000 → 8.37e+06) reports a false "READBACK MISMATCH -- do not drive".
  `check_ours.py` and `restore_fl_identity.py` already compare per field. Fix the other two.
- `tune_esc.py`'s own `TARGET_MC` / `EXPECT_MC` still carry 250 W-era values (`l_current_min` −25,
  `l_current_max` 25) and would be wrong for FL. `ours.json` supersedes them; make `tune_esc.py`
  read it or stop using it.
