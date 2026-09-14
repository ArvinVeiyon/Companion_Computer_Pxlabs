# ESC + PX4 configuration audit — 2026-09-14

Written after a floor session chasing an intermittent jerk at stop. One real fault was found and
fixed; this document records that, the full four-way config audit that followed, and what is still
outstanding. Backups behind it: `bldc_can/configs_live/vesc_{mc,app}conf_*_FINAL_20260914.xml`
(read off the devices over USB) and `~/fc_param_backups/fc_params_20260914_123637.params`
(952/952 over MAVLink).

---

## 1. The fault that was found and fixed — rear right hall table

**Rear right's hall table had one of its six rotor positions recorded at the wrong angle.** Entry 1
read `1` where both front wheels read `198`/`199`. RR was the only wheel whose mcconf had moved
since the 15 August baseline, and the other five entries had shifted by only 1–3 counts, which is
ordinary re-detection scatter. So detection had been re-run on RR at some point before 13 September
and came out wrong on one position.

**Consequence, measured.** RR's reported speed collapsed to near zero mid-drive — 206 rpm to 0 to
68 inside 20 ms while the other three read a steady ~200 — and the ESC believed it, spiking current
to +15 and +20 A to correct an error that did not exist. Several torque kicks on one corner during
every stop.

**Fix.** RR's *own* August values were written back (`diag/restore_rr_hall.py`). Not copied from
another wheel.

**Result.** Share of moving samples where a wheel disagrees with the other three by >100 rpm:

| wheel | before | after |
|---|---|---|
| FR | 6.0% | 0.8% |
| FL | 10.2% | 1.5% |
| RR | **20.2%** | **8.8%** |
| RL | 6.0% | 0.3% |

Every wheel improved, because one wheel reporting nonsense both disturbs the chassis and distorts
the comparison the others are measured against. Peak braking current during a stop fell from
~4.9 A to ~3.2 A; mean current during a stop roughly halved.

⚠️ **RR is still the worst by about six times.** The bad table was the main cause, not the whole
cause. Something about that corner remains unexplained.

---

## 2. Four-way ESC audit — candidate faults

Method: every mcconf/appconf field compared across all four wheels, and each wheel against its own
15 August baseline (`diag/config_audit.py --label FINAL_20260914`). This is the method that caught
the RR hall table, and it is the only thing that has ever surfaced a fault of that kind here.

### 🔴 FL — regen cut thresholds are reversed

| | FR | FL | RR | RL |
|---|---|---|---|---|
| `l_battery_regen_cut_start` | 25.2 | **25.4** | 25.2 | 25.2 |
| `l_battery_regen_cut_end` | 25.4 | **25.2** | 25.4 | 25.4 |

FL has the two the wrong way round. Working through `mc_interface.c:2451-2457`, the first branch
wins whenever it matches, so the effective behaviour is: **the other three cut regen above 25.3 V,
FL keeps full regen until 25.5 V.**

**Impact today: none.** Pack read 24.56–24.83 V during this session, below every threshold, so all
four had full regen. **Impact on a freshly charged pack: three wheels stop regen-braking while one
continues.** That is asymmetric braking, i.e. a yaw under brake. Memory already records only 0.34 V
of margin between the cut-in and a charged pack, so this is reachable, not theoretical.

**Recommend:** set FL to `start` 25.2 / `end` 25.4 to match the other three. One field pair, no
detection needed. ⛔ Do not raise the thresholds themselves (4.2 V/cell).

### 🟡 RL — FET thermal de-rating starts 10 °C later

| | FR | FL | RR | RL |
|---|---|---|---|---|
| `l_temp_fet_start` | 75 | 75 | 75 | **85** |
| `l_temp_fet_end` | 90 | 90 | 90 | **100** |

`mc_interface.c:2320-2332` de-rates max current linearly between these. Under sustained load the
other three begin backing off at 75 °C while RL keeps pushing to 85 — asymmetric drive when hot.
Only manifests at high FET temperature, so it has probably never been seen. Worth squaring up.

### 🟡 FL — battery cell count wrong

`si_battery_cells` FL=**6**, others=3; `si_battery_type` FL=**1**, others=0. These feed only the
battery-level estimate (`mc_interface.c:1558-1571`), not any control limit, so this is a reporting
error rather than a control fault. Fix for consistency.

### 🟡 RL — motor resistance less than half the others

`foc_motor_r`: FR 0.557, FL 0.5215, RR 0.4367, **RL 0.1988**. This is a detection result and is
legitimately per-motor, but a factor of 2.8 across four identical motors is a lot. It propagates
into `foc_current_kp`/`ki` (RL 0.8206/397.6 against FR 1.0932/1113.98), so RL's current loop is
tuned noticeably softer than the others. Candidate for re-running motor detection on RL, on the
stand. Not urgent, and ⛔ never copy another wheel's value.

### ✅ Differences that are expected — do not "fix" these

`m_invert_direction` mirrored (FR 0, FL 1, RR 0, RL 1) · `controller_id` / `uavcan_esc_index` ·
per-motor detection results (`foc_motor_r/l/ld_lq_diff`, `foc_motor_flux_linkage`, `foc_hall_table__*`,
`foc_offsets_*`). Appconf has **zero** unexpected differences across the four wheels.

### Changed since 15 August, and explained

All four moved together on the September RPM-mode migration: `s_pid_kp` 0.004→0.008,
`s_pid_min_erpm` 0→50, `s_pid_ramp_erpms_s` 5000→20000, `l_in_current_min` −5→−10. Current and
voltage offsets drift a little each detection, which is normal. `motor_description` fields picked
up VESC Tool's placeholder text — cosmetic. RR's `m_invert_direction` went 1→0, which brings it
into line with the mirroring rule, so August was the wrong value and this was a correction.

---

## 3. PX4 side

Current rover values, confirmed in the backup: `RO_ACCEL_LIM` −1 · `RO_DECEL_LIM` **3** ·
`RO_JERK_LIM` 1 · `RO_MAX_THR_SPEED` 4.93 · `RO_SPEED_LIM` 0.7 · `RO_YAW_ACCEL_LIM` −1 ·
`RO_YAW_DECEL_LIM` −1 · `COM_POS_FS_EPH` 5 · `NAV_RCL_ACT` 1 · `RC_MAP_KILL_SW` 12.

**`RO_DECEL_LIM` was raised from −1 to 3 during this session** and it works. Stops went from ~0.52 s
(the 09-13 figure) to ~0.75 s, then ~1.0 s after the hall fix. Read from
`src/lib/rover_control/RoverControl.cpp`, the accel and decel limits are genuinely separate — the
controller picks one or the other depending on whether the commanded value is above or below
current speed — so PX4 can do the asymmetry the ESC ramp structurally cannot.

🔴 **The limit is applied in `DifferentialActControl` via `RoverControl::throttleControl`, which is
downstream of every flight mode including Manual.** That is why it slews the manual stick, and it is
also why **it slows the collision reflex**: the reflex publishes a fake `ManualControlSetpoint`
(`ros2_ws/src/collision_manual_mode`), so PX4 cannot tell it from a real stick and applies the same
ramp. The reflex's 0.69 m clearance was sized against a much faster stop. **Re-verify standoff
before relying on the reflex at `RO_DECEL_LIM` 3.**

🔴 **`RO_SPEED_LIM` does not limit Manual mode.** `DifferentialManualMode::manual()` passes the stick
straight to `throttle_body_x`; only `position()` interpolates the stick against `RO_SPEED_LIM`. So
in Manual, full stick commands the full 9000 ERPM ≈ 4.93 m/s, not 0.7. **Relevant to the corridor
testing that is about to start.**

`RO_JERK_LIM` is only consumed by `DifferentialPosControl` for waypoint approach, so it does
nothing in Manual. Leave it set for AutoNav.

### Tool bug fixed

`ros2_ws/tools/dump_params.py` trusted `wait_heartbeat()`, which latched a non-autopilot heartbeat
and targeted `0:0`. `PARAM_REQUEST_LIST` then returned **nothing**, and the tool still wrote a
header-only `.params` file that looked like a backup. It now filters for component 1 with a valid
autopilot type, the way `set_param.py` already did, and refuses to write if no autopilot heartbeat
appears. Verified: 952/952.

---

## 4. The crawl catch — investigated, narrowed, still open

A catch you can feel and hear at low throttle, and a residual jerk at the end of a stop.

### 🔑 IT DOES NOT HAPPEN IN CURRENT MODE (operator, 2026-09-14)

This is the most informative fact we have, and it points at the **speed loop itself**, not the
motors and not the mechanics.

In current mode (`uavcan_raw_mode` 0) the throttle becomes a current demand directly — there is no
speed loop, so nothing compares a commanded speed against a measured one. In RPM mode
(`uavcan_raw_mode` 3, what we run) the speed PID does exactly that comparison, and **the measured
speed at crawl is very noisy**: a wheel's reported speed swings between 0 and 39 rpm while it is
turning steadily. The PID reads those dips as real error and answers with current pulses of 8-14 A.
Current mode has no loop to do that, which is why the symptom is absent there.

⛔ **This is not an argument for going back to current mode.** RPM mode is what makes PX4's speed
controller work against the hardware, and the whole September migration and `RO_MAX_THR_SPEED`
calibration depend on it. The observation is diagnostic, not a proposed fix.

⇒ The real levers are: make the low-speed estimate better (hall resolution is the ceiling; HFI is
the proper answer and is not enabled), or make the loop react less to it (gain — but that costs the
drive authority the September tuning established), or stay out of that speed band.

### ✅ Hall interpolation threshold is ONE cause — confirmed, then shown to be partial

`foc_hall_interp_erpm` decides where the ESC stops interpolating rotor angle between hall pulses and
snaps to the nearest sensor instead (`foc_math.c:646`). **The switch has no hysteresis.**

The catch **tracked the threshold**, which is what confirms the mechanism:

| threshold | nominal boundary | catch felt at |
|---|---|---|
| 250 (original) | 2.8% throttle | 3-4% |
| 500 | 5.6% | **8%** |
| 100 | 1.1% | **still ~4%** |

🔑 Both moves landed at roughly **1.4× the nominal** figure, consistently — expected, because the
firmware compares against a speed derived from hall-edge timing, and that estimate dips early.

🔴 **But 100 did not push it below ~4%, so there is a SECOND cause sitting at ~4% that does not move
with this parameter.** Unidentified. ⇒ **All four reverted to 250** (the known value; firmware
default is 500). 100 gave no benefit and carries the reversal risk the threshold exists to prevent.

### ✅ Mechanical causes RULED OUT

**With the rover powered off, all four wheels spin freely** (operator-checked). So no binding
bearing, no rubbing brake, no tyre or weight effect.

🔑 **The stiffness you feel when turning a wheel by hand with the rover POWERED ON is the ESC, and
it is by design.** In speed mode a centred stick means "hold zero speed", and below
`s_pid_min_erpm` (50) the ESC shorts the motor windings — a duty-zero short brake. A shorted motor
resists being turned. Measured standing current at rest: −0.07 / 0.12 / 0.02 / 0.13 A.
⚠️ **Any hand-spin drag comparison is meaningless unless the rover is powered down.**

### ⬜ Unexplained: per-wheel current asymmetry at no load

Current per unit speed, unloaded, consistent across forward, reverse and both turn directions:

| | FR | FL | RR | RL |
|---|---|---|---|---|
| right turn | 0.0214 | 0.0156 | 0.0134 | 0.0088 |
| left turn | 0.0235 | 0.0102 | 0.0184 | 0.0061 |

FR needs 2.4-3.9× what RL needs. Mechanics are equal, so FR is producing torque less efficiently —
which points back at the angle estimate. There is a rough correlation with detected `foc_motor_r`
(FR 0.557 highest, RL 0.199 lowest) but **not clean enough to claim**.
⚠️ **May not matter**: these are 0.4-1.5 A on an unloaded stand, against 8-20 A under load on the
floor. Needs a floor comparison before anyone spends time on it.

### ⚠️ Test-condition caveat

Late in the session it emerged that much of this was run **on the stand**, not the floor. The
interpolation effect was visible there, but the stand has already misled us once today (it could not
reproduce the brake-current behaviour at all). **Treat the 3/8/4% figures as stand observations and
re-confirm on the floor before building on them.**

⛔ Not the answer: lowering `s_pid_kp` to 0.004 masks it and gives back drive authority.

## 5. Recommended next actions

1. Square up FL's regen cut thresholds (25.2 / 25.4). Highest value, lowest cost.
2. Square up RL's FET temperature limits (75 / 90) and FL's battery cell count (3, type 0).
3. Re-verify the collision standoff at `RO_DECEL_LIM` 3 before trusting the reflex.
4. Then AutoNav in the corridor — see the session plan.
