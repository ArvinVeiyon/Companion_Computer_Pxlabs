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

## 🔄 2026-09-17/18 — THE OPERATOR RESTORED RR, AND WHAT THE AUDIT FOUND

**The operator restored RR's motor config, then asked for a four-way comparison.** `config_audit.py`
earned its keep a second time.

🔑🔑 **RR's live mcconf was an EXACT match for `configs_live/vesc_mcconf_RR_20260913_1226_pre.xml`** —
its **as-found state at 09-13 12:26**, i.e. before the G2 speed tune AND before the 09-14 hall fix.
⇒ **When a restore looks like a mix of eras, diff it against EVERY stored snapshot** (ignore
`foc_offsets_*`, `ConfigVersion`, `motor_*_description` — they drift on every read). One file matched
at zero differences and named the era instantly; guessing from individual fields had suggested three
different sources.

Out of family vs FR/FL/RL, and what each costs:
| field | RR was | others | consequence |
|---|---|---|---|
| `foc_hall_table__1..5` | 1/135/168/65/33 | FR 198/134/167/66/30 · FL 199/134/166/65/33 | the 09-14 hall fault, back |
| `s_pid_kp` | 0.004 | 0.008 | the gain that under-asks for current (12.0 -> 20.7 A) |
| `s_pid_min_erpm` | 200 | 50 | drops into the duty-0 short brake **4x earlier** in crawl |
| `l_in_current_min` | -5 | -10 | half the regen input current on the brake path |

✅ **APPCONF WAS CLEAN** — all four identical apart from `controller_id`/`uavcan_esc_index`, and the
RPM-mode migration (`uavcan_raw_mode` 3, `uavcan_raw_rpm_max` 9000) intact on all four. A config
restore that touches mcconf need not touch appconf; **check both, report both.**
🔑 `m_invert_direction` RR=0 is **NOT** a regression — it has been 0 since 09-13 and matches FR
(left wheels 1, right wheels 0). ⚠️ **`MOTOR_MAP.md` still lists RR=1 from the August file — that
doc is the stale one.**

### 🔴 END STATE, 2026-09-18 00:00 — RR IS DELIBERATELY CARRYING THE 09-13 HALL TABLE
Sequence, all readback-verified on device: restored the three tune values -> restored the 15-Aug hall
table (`diag/restore_rr_hall.py`) -> **operator asked for the OLD hall table back, so it was reverted
to 1/135/168/65/33/99.** ⇒ **RR NOW: hall = the 09-13 (suspect) table · tune = in family with the
other three.** ⛔ **Do not "fix" the hall table without asking — it is set that way on purpose,
pending a floor A/B.**
📏 **The A/B metric is already on record from 09-14:** RR's reported speed collapsed to near zero in
**20.2%** of moving samples vs FR/RL 6.0%, FL 10.2%, with a +20 A spike in the same samples. Re-run
that and the comparison decides it. ⚠️ Use the **>20 rpm** threshold (>100 reads 0.0% at 0.25 m/s as
an artifact), state the speed, and use `diag/brake_fullrate.py` — `brake_run_record.py` logs 1 sample
in 20. ⚠️ `brake_fullrate.py` arms on mean >300 rpm.
Backups both directions: `vesc_mcconf_RR_20260917_2318_hallpre.xml` (09-13 table) ·
`diag/restore_rr_hall.py` (August table).

### ⬜ `s_pid_kp` 0.004 ON ALL FOUR — TRIED AND REVERTED THE SAME NIGHT
Operator asked for a quick all-four test at 0.004, then reverted to 0.008. Both directions verified
on device. No measurement was taken in between, so **this produced no data** — recorded only so the
0.004 backups (`*_20260917_2344_s_pid_kp_pre.xml`) are not mistaken for a considered setting.

## 🔴🔴 USB — 2026-09-17 CONFIRMS THE 09-14 RULE, FIVE TIMES OVER
**Five wedges in one session.** Every one showed `Could not read firmware version` / `Could not
connect` while the device enumerated cleanly (`0483:5740`, no dmesg errors, `vcgencmd get_throttled`
**0x0** ⇒ not undervoltage).
⛔⛔ **A TARGETED SINGLE-DEVICE `USBDEVFS_RESET` MADE IT WORSE EVERY TIME** — the device dropped off
the bus entirely (`ioctl: [Errno 19] No such device`, then gone from `/sys/bus/usb/devices`), and
only the **hub `1-1.2` reset** brought it back. **This is the second independent confirmation. Go
STRAIGHT to the hub reset; do not try the single device first.** (I tried it anyway tonight, having
not re-read this file — cost ~15 min.)
✅ **The hub reset recovered all four, every single time.** Guard the reset on
`idVendor == 214b`; ⛔ never `1-1` (Realtek NICs + WFB).
🔑 **A wedge can also clear ITSELF** — FL refused every connection for ~20 min, then answered
normally after an unrelated hub reset.
🔑 **The wedge MOVES between wheels** — FL, then RR, then FR/RL. It is not one bad ESC.
🔑 **CAN health says nothing about USB, again:** FL read `online_flags 0xf` at **24.84 V** on
DroneCAN while its USB refused everything. ⇒ **a USB-dead ESC is still fully configurable... just
not tonight** — and its config CANNOT have changed, since USB is the only write path. That is what
made it safe to substitute FL's last verified readback into the audit (checked afterwards against a
live read: **identical apart from `foc_offsets_*`**).
🔑 Port mapping was stable all session after each hub reset: **ACM0=12 RR · ACM1=10 FR · ACM2=13 RL ·
ACM3=11 FL** — but `set_mcconf_field.py --expect-id` is what actually protects you; it refuses on a
mismatch, so a reshuffle costs a retry, never a wrong wheel.

---

## 🛑 THE BRAKE PATH — 2026-09-18, MOVED HERE FROM `MEMORY.md`

Consolidated out of the index on 09-18 (the index had grown to 99% of its read cap and was about to
silently drop its own tail). **Nothing here is new; nothing here was recorded anywhere else.**

### ✅ THE TUNE IN FORCE (09-13, all four, floor-validated under load)

`s_pid_kp` **0.008** · `s_pid_min_erpm` **50** · `l_in_current_min` **−10** · `l_current_min` **−25**
· `s_pid_ramp_erpms_s` **20000** · speed cap **4.93 m/s**.
⚠️ `s_pid_kp` 0.004 UNDER-ASKED for current (12.0 → 20.7 A) — see the 09-17/18 section above.

### ⛔⛔ DO NOT CHASE THE HARD NEUTRAL BRAKE WITH `l_current_min`

**Measured 09-14, 99 Hz log, 9 stops: peak braking is only −3.5 to −4.6 A.** So −25, −15 and −6 all
sit *above* it and **none of them ever bind.** Taken −25 → −15 → −6; the operator felt **nothing**;
**all reverted to −25.**
🔑 **NEUTRAL IS "HOLD 0 ERPM" — AN ACTIVE STOP**, not a release.

🔴 **THE STAND CANNOT REPRODUCE THE SYMPTOM.** Those stops were 1.3–2.7 s coast-downs with *mean
current positive* (+0.7 to +1.1 A). No mass ⇒ no kinetic energy ⇒ the speed loop is never asked for
brake current. (Same trap as the crawl-catch work — see the test-condition caveat above.)
⏭ **THE HARD STOP REMAINS UNDIAGNOSED. It needs a FLOOR run.**

### ⚠️⚠️ THE MEASUREMENT TOOL IS A TRAP

`brake_run_record.py` logs its CSV on a **0.2 s timer (5 Hz)** while `esc_status` arrives at **~98 Hz**
— 1 sample in 20, **blind to a spike inside a 0.4 s stop.** ⇒ **use `diag/brake_fullrate.py`.**
⚠️ But `brake_fullrate.py` **arms on mean wheel speed >300 rpm**, and 0.75 m/s only reaches ~270 ⇒ it
scored **0 stop events** on a run that contained one. **Lower the arming threshold before trusting it.**
🔑🔑 **AND WHEEL RPM CANNOT MEASURE A STOP AT ALL** — the end-of-stop speed signal is non-physical.
→ `ros2_ws/docs/autonav_reference.md` §13b. Use an independent ruler: `/scan` against a wall, or tape.

### ⛔⛔ `s_pid_ramp_erpms_s` STAYS 20000 — 2000 WAS TRIED AND REVERTED (09-13/14)

Sluggish off the line, and the real reason:
🔴 **ON A DIFFERENTIAL DRIVE THE RAMP THROTTLES YAW ONSET** — a turn *is* a side-to-side speed
difference, so ramping speed ramps steering. Every turn went long. **This is CONTROL AUTHORITY, not
comfort.**
🔴 **AND THE COLLISION REFLEX RIDES ON IT:** the reflex only zeroes the setpoint, which in RPM mode
*is* a duty-0 brake — but that is only instant at ramp 20000. **Any future ramp cut slews the
EMERGENCY stop at comfort-stop rate.**
⏭ **Durable fix: make the reflex COMMAND A BRAKE rather than collapse the setpoint.**

🔑 **THE RAMP IS SYMMETRIC BY CONSTRUCTION** — `foc_math.c:504` → `utils_step_towards`
(`utils_math.h:131`), same step both directions ⇒ it can **NEVER** give soft stop + snappy launch.
⛔ **`cc_ramp_step_max` / `m_duty_ramp_step` ARE NOT USABLE BRAKE RAMPS** — they live only in
`mcpwm.c` (BLDC), which is dead code on this FOC firmware.
⇒ **Asymmetry has to come from PX4's `RO_DECEL_LIM`**, which is separate from `RO_ACCEL_LIM`.
✅ **`RO_DECEL_LIM` is 5 since 09-14** (`RO_ACCEL_LIM` stays −1), and its stop contribution was
**closed by arithmetic 09-18**: slew = 5 ÷ 4.93 = 1.01/s ⇒ ~0.06 m at 0.75 m/s.
→ `autonav_reference.md` §13 (09-18). ⛔ The old "pinned −1 after the 08-14 wall hit" note is STALE.

### ⏭ THE ONE UNTESTED ESC BRAKE LEVER

**`foc_duty_dowmramp_kp` 50 / `foc_duty_dowmramp_ki` 1000** *(spelling is the firmware's, not a typo)*.
Only 2 lines in the firmware, both inside the duty-control PI — and the **only** path into duty
control here is the neutral duty-0 short brake ⇒ **brake-path-only: it cannot touch accel or yaw.**
⚠️ **UNCONFIRMED — get floor data before touching it.**

### 🔴 CEILINGS THAT MAKE A "CAP" MEANINGLESS

`esc_rpm` is **MECHANICAL — multiply by 7** for the ERPM that `rpm_max` expects.
Ceiling is **~10500 ERPM** (`l_max_duty` 0.95) ⇒ **a cap set above that is not a cap.**

## 🔑 2026-09-19 — YAW CAPTURES ON THE FLOOR, AND A "FAULT" THAT RETIRES

⛔⛔ **ZERO RPM FROM A STATIONARY HUB MOTOR IS NOT A FAULT SIGNATURE — OPERATOR, 09-19.** These are
hall-sensored hubs: if the rotor never breaks away there is nothing for the halls to count, so the
speed loop servos a measurement that cannot change and just pushes current. ⇒ **low yaw commands are
STRUCTURALLY UNSERVOABLE FROM REST on this drivetrain.**
🔴 **This retires my 09-19 reading of the pivot capture.** RR sat at **0 rpm drawing up to 18.8 A for
3.5 s** at a 0.4 rad/s in-place command, which I first read as the corner-collapse fault. It is a
test-design artifact: **a pivot from rest is the one condition where this drivetrain cannot servo.**
✅ **RR IS LIVE IN AN ARC** — 26 rpm, later 59→84 rpm at 12-15 A, rolling. ⛔ **NO MORE PIVOTS FROM
REST**: they cannot work, and they bake heat into motors at 15-19 A with no airflow.

**Captures (full rate, per-wheel rpm+current+gyro on one timeline), in the scratchpad as
`yawesc_*.csv`:** 0.4 / 0.7 / 1.0 rad/s pivots, one arc, one sign-verification arc.
🔴 **THE OPEN PUZZLE: yaw is NOT reproducible run-to-run at the same command.** Same `CORR` 7.4,
single steps from rest: 0.4 weak · **0.7 STRONG (0.927 rad/s, all four live)** · 1.0 weak (0.156),
with the 1.0 run drawing barely above idle (9.9→13 A vs 18.8 A at 0.4) ⇒ **the setpoint reaching the
ESCs was small — they were NOT fighting a load.**
⛔ **NOT thermal:** ESC temps **RF 44.4 · FL 43.1 · RR 47.1 · RL 45.9 °C**, pack 24.7-24.9 V. A VESC
does not derate until ~85 °C. **UNEXPLAINED — do not tune on top of it.**
⚠️ In the arc the RIGHT side (RF+RR, both OLD motors) under-ran its commanded speed (0.10 vs 0.19 m/s)
while the LEFT side tracked. Distinct from the rear-load story.

🔧 **OPERATOR DECISION 09-19: replace the three OLD motors (RF, FL, RR).** His evidence: **RL was
recently replaced and outperforms the rest**, and RL/RR share an axle under the same load — new
turned, old stalled. ⚠️ **the rear sits LOWER (suspension variation) so the rear axle carries more
stress** ⇒ ride height is its own item; new motors will still carry that load.
🔑 **The RR hall-table A/B is therefore NOT the pending question it was** — the pivot evidence that
pointed at it was an artifact. Re-open it only with an ARC capture.
