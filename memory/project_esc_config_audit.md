---
name: esc_config_audit
description: "The 2026-09-14 rear-right hall-table fault, the four-way config-diff method that found it, and the candidate faults still outstanding on FL and RL. Read before blaming ESC tuning for a motion problem."
metadata: 
  node_type: memory
  type: project
  originSessionId: c34e9fca-714e-4f33-9c82-fe6e0b6b0fb2
  modified: 2026-09-15T18:51:33.893Z
---

# ESC config audit — the method that finds faults tuning cannot

Full write-up with every number: **`codex-work/esc_px4_config_audit_20260914.md`**.
Tools: `bldc_can/diag/config_audit.py` · `backup_live_configs.py` · `set_mcconf_field.py` ·
`restore_rr_hall.py`. Related: [[vesc_can_flashing]], [[px4_rover_control_scope]].

## 🔑 THE METHOD — compare wheels against each other, and against August

Four identical motors on one chassis. **A value that is an outlier on one wheel, or that has moved
since the 15-Aug baseline in `configs_from_repo/` without a recorded reason, is a candidate fault.**
This is the only thing that has ever surfaced a fault of this class here — no amount of tuning or
floor measurement found it. Run `diag/config_audit.py --label <label>` whenever the rover misbehaves
in a way that is not obviously a tuning value.

⛔ **NEVER cross-write one wheel's values onto another.** `m_invert_direction` is mirrored (left 1,
right 0) and the detection results (`foc_motor_r/l`, `foc_motor_flux_linkage`, `foc_hall_table__*`,
`foc_offsets_*`) are genuinely per-motor. Restore a wheel's **own** history instead.

## ✅ FIXED 2026-09-14 — RR hall table, one rotor position at the wrong angle

`foc_hall_table__1` read **1** where both front wheels read 198/199; the other five entries had
moved only 1-3 counts (ordinary re-detection scatter). RR was the **only** wheel whose mcconf had
changed since August. Restored RR's own August values.

**Measured effect — the ruler is cross-wheel disagreement, not feel.** Share of moving samples where
a wheel's reported speed differs from the median of the other three by >100 rpm:

| | FR | FL | RR | RL |
|---|---|---|---|---|
| before | 6.0% | 10.2% | **20.2%** | 6.0% |
| after | 0.8% | 1.5% | **8.8%** | 0.3% |

Peak braking current per stop 4.9 A → 3.2 A. **Every wheel improved**, because one wheel reporting
nonsense disturbs the chassis *and* distorts the median the others are judged against.

🔑 **The symptom was: reported speed collapsing to near zero mid-drive (206 → 0 → 68 rpm in 20 ms
while the others read a steady 200), and the ESC believing it and spiking current to +15/+20 A to
correct an error that did not exist.** A torque kick on one corner, several times per stop.
⚠️ **RR is still ~6× the others at 8.8%. The bad table was the main cause, not the whole cause.**

## ⬜ STILL OPEN — candidate faults found by the same audit, not yet fixed

- 🟡 **RL FET de-rating starts late:** `l_temp_fet_start`/`_end` **85/100** against 75/90 on the
  other three. Under sustained load the others back off first. Only bites when hot.
- 🟡 **FL battery cell count:** `si_battery_cells` 6 vs 3, `si_battery_type` 1 vs 0. Feeds only the
  battery-level estimate (`mc_interface.c:1558`), **not** any control limit. Reporting only.
- 🟡 **RL motor resistance:** `foc_motor_r` **0.1988** against 0.4367-0.557. It is a detection result
  and legitimately per-motor, but 2.8× across identical motors is a lot, and it propagates into
  `foc_current_kp/ki` so RL's current loop is softer than the others. Candidate for re-running
  detection **on RL only**, on the stand.

## ✅ FIXED 2026-09-14 — FL regen cut thresholds were reversed

`l_battery_regen_cut_start`/`_end` read **25.4/25.2** where the other three read 25.2/25.4. Per
`mc_interface.c:2451-2457` the first branch wins, so **the other three cut regen above 25.3 V while
FL kept full regen to 25.5 V** — three wheels stop regen-braking and one does not, i.e. a yaw under
brake on a charged pack. No effect at the 24.8 V pack of that day. All four now 25.2/25.4.
⛔ Do not raise the thresholds themselves (4.2 V/cell).

## 🔴🔴 2026-09-16 — **THE FAULT SIGNATURE CAUGHT ON THE FLOOR, FULL RATE, FOR THE FIRST TIME**

Captured during T2 at **0.75 m/s** (the first run fast enough to trigger it — three slower runs that
night showed nothing). 98 Hz, `codex-work/bldc_can/evidence/t2_run4_075ms_20260916.csv`.

```
  t        FR            FL            RR            RL          (rpm | amp)
23.546   167|+3.09    172|+4.61     87|+2.14    164|-2.96   <- RR at HALF, others steady
23.644   107|+19.69   114|+18.69    63|+17.00    23|+11.16
23.687     0|+14.78    39|+21.34    14|+14.20    29|+14.05
23.706     0|+13.38     1|+12.13    55|+10.54    87|+6.31   <- RL 29 -> 87 rpm in 30 ms
```

🔑 **This is the 09-14 signature exactly**: one corner's reported speed collapsing while the others
read steady, the ESC believing it, and answering with **+14 to +22 A**. ⇒ **the RR hall-table fix
reduced this but did not remove it** — as this file already predicted ("the main cause, not the whole
cause"). RR leads the collapse; RL follows; both fronts then go non-monotonic to zero.
🔑 **Almost certainly the HARD NEUTRAL STOP and the residual end-of-stop jerk** — the thing the stand
could never reproduce (no mass ⇒ the loop never has to do it). ⚠️ **n=1, and not yet explained.**

⛔⛔ **DO NOT DERIVE A DECELERATION FROM THIS DATA.** Wheels do not go 8 → 93 rpm in 30 ms. A fit
moved between **0.30 and 4.97 m/s²** on the choice of start threshold alone. The speed signal is
non-physical exactly where the stop happens ⇒ **`RO_DECEL_LIM`=5 remains UNMEASURED** and needs an
independent ruler. → `autonav_reference.md` §13b

⚠️ **`brake_fullrate.py` ARMS ON MEAN WHEEL SPEED >300 rpm** and 0.75 m/s only reaches ~270 ⇒ it
reported **0 stop events** on a run that plainly contained one. **Lower the threshold or score the
CSV directly.** Three runs, ~26,000 samples, 0 events scored — twice for want of speed, once for this.

### ✅ CROSS-WHEEL AGREEMENT, MEASURED AT TWO SPEEDS (same metric as the 09-14 table)
| | FR | FL | RR | RL | spread |
|---|---|---|---|---|---|
| 0.25 m/s | −1.19% | −0.76% | **+1.35%** | +0.60% | ±1.35% |
| 0.75 m/s | +1.54% | **+3.60%** | **−3.53%** | −1.62% | ±3.60% |

✅ **RR is now the CLEANEST of the four at 0.25 m/s** (0.5% by the >20 rpm metric vs FR 2.6%) — the
hall fix has held. 🔑 **But disagreement TRIPLES from 0.25 to 0.75 m/s**, FL fastest / RR slowest,
7.1% between extremes. ⚠️ **The 09-14 ">100 rpm from the median" metric reads 0.0% on all four at
0.25 m/s and that is an ARTIFACT** — wheels only turn ~63 rpm there, so a wheel would have to read
>163 to trip it. **Use >20 rpm at low speed.** Always state the speed with the metric.
⬜ **NEW, unexplained:** at identical rpm the **front pair draws +1.17 A vs the rear pair's +0.84 A**
(~39% more). Front/rear, so it does not yaw the rover. Possibly weight distribution. Log, don't chase.

## ⏸ PARKED — the crawl catch. NARROWED, not solved

Catch you can feel/hear at low throttle, plus a residual jerk at the end of a stop.

🔑🔑 **IT DOES NOT HAPPEN IN CURRENT MODE (operator, 09-14) ⇒ THE SPEED LOOP IS THE MECHANISM.**
In current mode nothing compares commanded against measured speed. In RPM mode the PID does, and
**the crawl speed estimate is garbage** — a wheel reports 0-39 rpm while turning steadily — so the
loop reads the dips as error and answers with **8-14 A current pulses**. ⛔ **NOT an argument for
current mode**: RPM mode is what makes PX4's speed controller work, and the whole Sept migration +
`RO_MAX_THR_SPEED` rest on it. ⇒ real levers = better low-speed estimate (hall resolution is the
ceiling; **HFI is the proper answer, `foc_sl_erpm_hfi`=0, not enabled**) · less loop reaction (gain,
⛔ costs authority) · stay out of the band.

✅ **`foc_hall_interp_erpm` IS ONE CAUSE — the catch TRACKED it.** Below it the ESC snaps rotor angle
to the nearest hall instead of interpolating (`foc_math.c:646`), **no hysteresis**.
**250 → felt 3-4% · 500 → felt 8% · 100 → STILL ~4%.** 🔑 both moves landed at ~**1.4× the nominal**
boundary (it compares a hall-edge-timing speed, which dips early).
🔴 **So a SECOND cause sits at ~4% and does not move with it. Unidentified.**
⇒ **ALL FOUR REVERTED TO 250.** 100 bought nothing and carries the reversal risk the threshold exists
to prevent (angle can stick 60° off on a direction change). Firmware default is 500.

✅✅ **MECHANICAL RULED OUT — powered OFF, all four spin freely** (operator-checked). No binding, no
tyre, no weight effect.
🔑🔑 **THE STIFFNESS WHEN TURNING A WHEEL BY HAND WITH POWER ON IS THE ESC, BY DESIGN** — centred
stick = "hold 0 speed", and below `s_pid_min_erpm` (50) the ESC SHORTS THE WINDINGS (duty-0 short
brake); a shorted motor resists turning. Standing current at rest −0.07/0.12/0.02/0.13 A.
⚠️⚠️ **ANY HAND-SPIN DRAG TEST IS MEANINGLESS UNLESS THE ROVER IS POWERED DOWN.**

⬜ **UNEXPLAINED: current-per-rpm at NO LOAD is FR 0.0214-0.0235 vs RL 0.0061-0.0088 — FR needs
2.4-3.9× RL**, consistent across forward, reverse and both turn directions. Mechanics equal ⇒ FR
makes torque less efficiently ⇒ points back at the angle estimate. Rough correlation with detected
`foc_motor_r` (FR 0.557 high, RL 0.199 low) but ⛔ **not clean enough to claim**.
⚠️ **May be irrelevant**: 0.4-1.5 A unloaded vs 8-20 A loaded. **Needs a FLOOR comparison first.**

⚠️⚠️ **TEST-CONDITION CAVEAT: much of the 09-14 catch work was ON THE STAND, discovered late.** The
interp effect was visible there, but 🔴 **the stand already misled us once the same day** (it could
not reproduce the brake-current behaviour at all — no mass ⇒ the loop never has to do the thing you
are trying to observe). **Treat 3/8/4% as STAND numbers; re-confirm on the floor before building on
them.** ⛔ Lowering `s_pid_kp` to 0.004 is not the answer — masks it, costs authority.

## ⛔ HFI — CONSIDERED AND REJECTED 2026-09-14. Do not re-propose without reading this.

Raised as the proper fix for the noisy low-speed estimate. **Two reasons it is not the next step.**

🔴 **WE CANNOT CALIBRATE IT HEADLESS.** `vesc_tool_7.01 --help` has **no detection/measure routines
at all** — reading and writing config is scriptable, detection is not. The stored `foc_hfi_*` values
are firmware DEFAULTS never measured against these motors (`voltage_start` 20 / `_run` 4 / `_max` 6 /
`gain` 0.3). Enabling it would be a guess. Doing it properly needs VESC Tool **with a display**, over
USB, per ESC.

🔴 **HFI REPLACES THE HALL SENSORS, IT DOES NOT SUPPLEMENT THEM.** `foc_sensor_mode` is a single
choice and `mcpwm_foc.c:3442/3488` are separate `switch` branches — selecting HFI means the hall
branch never runs. 🔑 **HFI solves "where is the rotor at standstill", which is the SENSORLESS
problem; halls already give absolute position at rest.** What halls lack is RESOLUTION between their
42 steps/rev. HFI would help that, but the trade is giving up a working reliable sensor for an
uncalibrated technique, to fix roughness at 4% throttle on a vehicle that drives fine.
⚠️ Saliency is adequate if it is ever revisited: `foc_motor_ld_lq_diff / foc_motor_l` = 24-45%.

⏭ **THE CHEAPER LEAD IS THE DETECTION SCATTER.** `foc_motor_r` runs 0.199 (RL) to 0.557 (FR) across
four IDENTICAL motors, and saliency 24-45%, and **that scatter tracks the unexplained current
asymmetry** (FR highest on both, RL lowest on both) ⇒ the detections were likely run under different
conditions and some are poor. Re-detecting consistently is far less invasive than changing the
sensing architecture. 🔴🔴 **BUT RE-DETECTION IS ALMOST CERTAINLY WHAT CORRUPTED RR'S HALL TABLE** —
so: one wheel at a time, backup safe (`*_FINAL_20260914.xml`), and **diff the hall table against the
others afterwards**, which is the check that caught it.

## 🔧 USB — refined 2026-09-14

⛔ **A targeted `USBDEVFS_RESET` on a single wedged VESC made it WORSE** — the device dropped off the
bus entirely (`device descriptor read/64, error -110`) and only a **hub `1-1.2` reset** brought it
back. Prefer the hub reset; resolve the devnum at the moment of the reset, never from an earlier
listing. ⛔ Never reset `1-1`. 🔑 A wedge always hits the **first probe read**, so it never leaves an
ESC half-written — a failed run is safe to repeat.
🔑 **`is-active`, CAN telemetry and USB are independent rulers.** FL read online and healthy on
DroneCAN at 24.66 V while its USB refused every connection — **CAN health says nothing about USB.**
