# T2 — armed AutoNav on the floor, 2026-09-15/16 (corridor)

Four runs, three tape-adjudicated. **G3 closed.** Raw data in this directory:
`t2_brake_20260915.csv` · `t2_brake_run2_20260915.csv` · `t2_run3_wheels_20260915.csv` ·
`t2_run4_075ms_20260916.csv`. Run JSON in `~/ros2_ws/` as `t2_2026091*.json`.

Tool: `ros2_ws/tools/t2_straight_goal_test.py` · recorder: `bldc_can/diag/brake_fullrate.py`

---

## 1. Result — T2 PASSED, n=3, across a 5× speed range

| run | speed | goal | **TAPED** | error | lateral | yaw | reflex | verdict |
|---|---|---|---|---|---|---|---|---|
| `233204` | 0.08 m/s | 2.0 m | — | — | +0.005 m | +1.06° | silent | **aborted at 0.575 m** (see §4) |
| `234300` | 0.15 m/s | 2.0 m | **2.130 m** | +0.130 m | +0.033 m | +2.08° | silent | ✅ PASS |
| `235442` | 0.25 m/s | 2.0 m | **2.025 m** | +0.025 m | +0.036 m | +2.02° | silent | ✅ PASS |
| `000848` | 0.75 m/s | 2.0 m | **2.000 m** | 0.000 m | +0.023 m | +1.56° | silent | ✅ PASS |

Tolerance ±0.20 m. Both criteria met three times — arrival **and** a silent reflex on a clear
corridor, which fail in opposite directions. **Accuracy and tracking both improve with speed.**

Adjudicated on **tape**, per the tool's design. `/odom` cannot arbitrate a 0.20 m tolerance when its
own error is speed-dependent (§2).

---

## 2. 🔑 The odometry scale error is SPEED-DEPENDENT — the session's main finding

| speed | taped real | `/odom` | **odom/real** | mechanism |
|---|---|---|---|---|
| 0.15 m/s | 2.130 m | 2.015 m | **0.946** | under-reads 5.4% — ESC zero-dropout loses counts |
| 0.25 m/s | 2.025 m | 2.025 m | **1.000** | exact |
| 0.75 m/s | 2.000 m | 2.059 m | **1.030** | over-reads 3.0% — wheel slip |

Monotonic, with a **crossover near 0.25 m/s**. Two mechanisms pulling opposite ways, each already
documented separately. `erpm_to_ms` = 0.003900 is effectively calibrated at ~0.25 m/s.

**This reconciles two findings that looked contradictory for a month:** the 2026-09-12 "8.1%
over-read" (fast burst) and the 2026-08-13 "21–24% under-read" (crawl) are **two ends of one curve**,
not a disagreement.

- ⛔ **Not grounds to retune `erpm_to_ms`.** The constant is fine; the error is physical, and no
  single constant cancels it.
- 🔑 **Quote every odom distance with the speed it was taken at.**
- 🔴 **Retires `ODOM_WORST_CASE = 1.35`** in `t2_straight_goal_test.py` — measured 0.97–1.06, wrong
  at every speed tested. ⚠️ Wrong in the **safe** direction (it oversizes the corridor), so fixing it
  *reduces* margin. Leave it unless the corridor length is needed back.
- ⚠️ **n=1 per speed**, one corridor, one floor. A trend, not a calibration curve.

---

## 3. 🔴🔴 The end-of-stop signal is non-physical — and it caught the 09-14 fault

Full rate (98 Hz), 0.75 m/s, from `t2_run4_075ms_20260916.csv`:

```
  t        FR            FL            RR            RL          (rpm | amp)
23.546   167|+3.09    172|+4.61     87|+2.14    164|-2.96   <- RR at HALF, others steady
23.644   107|+19.69   114|+18.69    63|+17.00    23|+11.16
23.687     0|+14.78    39|+21.34    14|+14.20    29|+14.05
23.706     0|+13.38     1|+12.13    55|+10.54    87|+6.31   <- RL 29 -> 87 rpm in 30 ms
```

Wheels do not go 8 → 93 rpm in 30 ms on a decelerating rover.

**⛔ Do not derive a deceleration, stop distance or reflex clearance from wheel rpm through a stop.**
A fit to this data moved between **0.30 and 4.97 m/s²** on the choice of start threshold alone — that
spread is the tell, which is why no figure from this run is quoted anywhere.

**🔑 What it does show is the 2026-09-14 fault signature, on the floor, at full rate, for the first
time:** one corner's reported speed collapsing while the others read steady, the ESC believing it and
answering with **+14 to +22 A**. The stand could never reproduce this (no mass ⇒ the loop never has
to do the thing you are trying to observe), and the three slower runs that night never reached the
speed to trigger it.

⇒ **The RR hall-table fix reduced this but did not remove it**, exactly as `esc_config_audit`
predicted ("the main cause, not the whole cause"). RR leads the collapse, RL follows, both fronts then
go non-monotonic to zero. **Probably the hard neutral stop and the residual end-of-stop jerk.**
⚠️ n=1, unexplained.

### `RO_DECEL_LIM`=5 is still unmeasured — three runs, zero scored events

~26,000 samples at ~97 Hz across three recordings, **0 stop events** every time:

- runs 2 and 3 — too slow; at 0.15–0.25 m/s there is no kinetic energy to shed
- run 4 — ⚠️ **`brake_fullrate.py` arms on *mean* wheel speed >300 rpm**, and 0.75 m/s only reaches
  ~270. It scored 0 events on a run that plainly contained one. **Lower the threshold, or score the
  CSV directly.**

The reflex's 0.69 m clearance is still sized against a 0.19 m stop measured at `RO_DECEL_LIM` **−1**,
not the **5** now in force. Closing this needs an independent ruler — `/scan` against a wall, or tape.

---

## 4. Cross-wheel agreement, at two speeds

| | FR | FL | RR | RL | spread |
|---|---|---|---|---|---|
| 0.25 m/s | −1.19% | −0.76% | **+1.35%** | +0.60% | ±1.35% |
| 0.75 m/s | +1.54% | **+3.60%** | **−3.53%** | −1.62% | ±3.60% |

✅ **RR is now the cleanest of the four at 0.25 m/s** (0.5% by the >20 rpm metric, against FR's 2.6%)
— the hall fix has held. **But disagreement triples from 0.25 to 0.75 m/s**, FL fastest and RR
slowest, 7.1% between the extremes. Left runs +2.01% faster than right.

⚠️ **The 09-14 ">100 rpm from the median of the other three" metric reads 0.0% on all four at
0.25 m/s, and that is an artifact** — the wheels only turn ~63 rpm there, so a wheel would have to
read >163 to trip it. **Use >20 rpm at low speed, and always state the speed with the metric.**

⬜ **Unexplained:** at identical rpm the **front pair draws +1.17 A against the rear pair's +0.84 A**
(~39% more). Front/rear, so it does not yaw the rover. Possibly weight distribution. Log, don't chase.

---

## 5. Traps that cost time, and will recur

**🔴🔴 `arming_check_request` is a ONE-SHOT at registration, not a heartbeat.** Zero messages over 30 s
against a live 2.0 Hz `vehicle_status_v1` control was read as "the mode is not registered". It was
registered the whole time. **Proof of registration is the log line** — `Registering 'AutoNav'` +
`Got RegisterExtComponentReply` + `Arming check request (id=N, only printed once)` — **never a message
rate on that topic.**

**🔴🔴 It is `/fmu/out/vehicle_local_position_v1`.** The unversioned name returns nothing, which was
misread as "the EKF bridge is not feeding". Same versioned-topic trap as `vehicle_status_v1`. `eph`
lives on the `_v1` topic. The bridge was healthy throughout: `/odom` 87 Hz in →
`/fmu/in/vehicle_visual_odometry` 31 Hz out.

**🔴 The measured-speed guard false-trips at crawl.** Run 1 at 0.08 m/s aborted at 0.575 m on
`max_measured_speed` 0.20, while two independent rulers put the rover at 0.105 m/s (travel/dt peaked
at 0.127). The instantaneous ESC estimate had spiked to 0.234 m/s. **The fix is to drive out of the
crawl band, not to raise the guard.**

**🔴 Two bugs in `t2_straight_goal_test.py`:**
1. `n.odom_vx` is read once for the comparison and **again** for the abort message, with a callback
   updating it between — which printed the impossible *"measured 0.00 m/s exceeds the 0.20 m/s
   limit"*. The number in the message is not the number that tripped the guard.
2. `ODOM_WORST_CASE = 1.35` — see §2.

**🔴 `/scan` sector coverage is not blindness.** `preflight_scan_check.py` reported "NOTHING VALID
SEEN" with 68% whole-scan validity, because the ±0.28 m corridor filter drops nearly everything
beyond ~3 m by design. Confirm with a Cartesian probe (`x = r·cosθ`, `y = r·sinθ`) before believing
the rover is blind — twice tonight the corridor was genuinely clear.

---

## 6. Carried forward

- 🔴 `RO_DECEL_LIM`=5 stop distance — unmeasured; wheel rpm cannot measure it (§3)
- 🔴 **The ≥300 mm standoff is unmeasured above ~0.11 m/s.** The 0.75 m/s run **exceeded the
  `autonav_reference.md` §13 speed permission** without re-running `collision_standoff_test.py`.
  Operator-directed, after the constraint was stated. **T2 does not test the reflex** — it drives at
  nothing, and the reflex was silent on all three runs because there was nothing to see.
- 🟡 Speed tracking exact at 0.25 m/s, **~8% short at 0.75** (0.688–0.706 vs 0.750), after an initial
  overshoot to **0.902 m/s** in the first 0.5 s
- 🟡 `COM_DISARM_PRFLT`=10 s never auto-disarmed an idle armed rover across repeated observation
- 🟡 **FR and RL refuse USB** (`Could not connect`); all four enumerate on hub `1-1.2`. CAN telemetry
  on both is healthy — CAN health says nothing about USB. A four-way config audit is not possible
  until the hub is reset.
- 📏 `eph` drifted **0.758 → 2.618 m** over the session against the 5.0 m `COM_POS_FS_EPH` gate
  (~0.0013 m/s) ⇒ **~45–60 min of armed budget per bridge restart**
