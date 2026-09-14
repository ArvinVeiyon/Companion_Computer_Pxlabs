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

## 4. Parked — the crawl jerk

A residual jerk at the end of a stop, and an audible on-off at ~3% throttle. The wheel speed
estimate is very noisy at crawl: FR's reported speed swings 0–39 rpm while the rover rolls steadily,
and current pulses to 8–14 A in response, on all four wheels equally.

Hypothesis, untested: `foc_hall_interp_erpm` = 250 is ~36 mechanical rpm, and 3% throttle is
270 ERPM — right on it. Below that threshold the firmware snaps the rotor angle to the nearest hall
sensor instead of interpolating (`foc_math.c:646`), and the switch has **no hysteresis**, so a noisy
speed estimate crossing it repeatedly steps the angle and therefore the torque.

⛔ **Tested on RL on the stand and it was inconclusive, because the stand does not reproduce the
symptom at all** — 0–5 rpm of jitter there against 0–39 on the floor, and current spread ~1–2 A
against 8–14. With the wheels unloaded the speed loop barely works. RL has been reverted to 250.
**If this is revisited it needs a floor run. Do not re-test it on the stand and conclude anything.**

⛔ Not the answer: lowering `s_pid_kp` back to 0.004 would mask it and give back the drive authority
the September tuning established.

---

## 5. Recommended next actions

1. Square up FL's regen cut thresholds (25.2 / 25.4). Highest value, lowest cost.
2. Square up RL's FET temperature limits (75 / 90) and FL's battery cell count (3, type 0).
3. Re-verify the collision standoff at `RO_DECEL_LIM` 3 before trusting the reflex.
4. Then AutoNav in the corridor — see the session plan.
