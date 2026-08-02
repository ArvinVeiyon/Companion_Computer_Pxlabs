---
name: project-rover-autonav
description: "Rover autonomous navigation (Nav2 + px4_ros2 lib + Orbbec depth). L0-L4 done; L2 armed floor test PASSED 2026-07-22/23 + reflex collision-stop built/validated/pushed (b38e413). NEXT = yaw-gain tuning then L5 (slam_toolbox+Nav2)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5ff45709-5e20-4964-9bd8-fce6f3bc03f0
  modified: 2026-08-02T13:26:17.814Z
---

# Rover Autonomous Navigation — ACTIVE (started 2026-07-19)

## 🏁🏁 2026-08-02 — **#20 EXPLAINED. IT IS A FRICTION DEADBAND + INTEGRAL WINDUP, NOT A BROKEN LOOP.**
**MEASURED yaw response curve** (MANUAL, armed, stick held ≥0.8 s, gyro averaged over the settled half):
| steer out | 0.055 | 0.230 | 0.268 | 0.281 | 0.348 | 0.425 | **0.484** | **0.573** | **0.935** |
|---|---|---|---|---|---|---|---|---|---|
| yaw rate | 0 | 0 | 0 | 0 | 0 | 0 | **0.67** | **1.51** | **4.11** |
🔑 **DEADBAND 0 → ~0.45, then LINEAR: `yaw_rate ≈ 7.6 × (steer − 0.40)` rad/s.**
(fit checks: 0.573→1.35 vs 1.51 measured; 0.935→4.10 vs 4.11 measured.)
🔑 **MINIMUM ACHIEVABLE YAW RATE ≈ 0.67 rad/s. ⛔ NEVER COMMAND A SLOWER TURN** — Nav2 and
`autonav_mode` must clamp to this or the rover sits and grinds while the planner thinks it is turning.
🔴 **THE RUNAWAY MECHANISM, END TO END:** command 0.3 rad/s → correct FF lands INSIDE the deadband →
nothing moves → error persists → **`RO_YAW_RATE_I` winds the integrator toward its limit of 1.0 (the
whole output range)** → friction finally breaks at near-max output → `7.6 × (1.0−0.4) ≈ 4.6 rad/s`.
**That IS the observed 5.7-6.3 rad/s "~21×".** ⇒ **P was never the culprit; lowering it 40× could not
help.** The three misconfigurations below all pushed FF FURTHER into the deadband.
⚠️ **A LINEAR FF CANNOT REPRESENT A DEADBAND.** Required `CORR` varies with setpoint
(sp 0.67→2.8, sp 1.0→2.1, sp 2.0→1.3). **No single value serves both slow and fast commands** —
pick for the mid operating range and let P cover the rest.
⏭ **REMAINING TUNING:** `CORR` ≈ 2.0-2.5, restore a modest `RO_YAW_RATE_P` (~0.3-0.5) for authority,
and **keep `RO_YAW_RATE_I` at 0 or very small — the deadband is exactly what makes windup dangerous.**
⏭ Physical alternative if slow turns are ever needed: less weight / different tyres / different
surface. This is traction, not software.
✅ **FC REBOOTED 2026-08-02 right after these changes — ALL EIGHT PARAMS SURVIVED, verified by
readback.** ⇒ **`PARAM_SET` over MAVLink (pymavlink) PERSISTS on this firmware; no NuttShell
`param save` is needed.** FC came back **DISARMED** (it can come back armed — always check).
`eph` reset to 0.016 m, all 7 services active, DDS re-established, `/odom` 100.3 Hz.
🔴 **`RO_YAW_RATE_I = 0` IS DELIBERATE — do not let it drift back to 0.1.** It is the windup source
that produced the runaway across the friction deadband.
⚠️ **STILL RE-READ AFTER EVERY FC REBOOT ANYWAY** — persistence held once; that is not proof it
always will, and the failure mode (silent revert to a runaway config) is expensive.

## 🔑 2026-08-02 — **#20 PART 1: `RO_YAW_RATE_LIM` IS deg/s, NOT rad/s.**
**Source of truth — the param doc in `src/lib/rover_control/rovercontrol_params.c`:**
> *Yaw rate limit … Used to cap yaw rate setpoints and map controller inputs to yaw rate setpoints
> in Acro, Stabilized and Position mode.* **`@unit deg/s  @min 0  @max 10000`**
`DifferentialManualMode.cpp:52`: `_max_yaw_rate = RO_YAW_RATE_LIM * M_DEG_TO_RAD_F`.
| setting | believed | ACTUALLY |
|---|---|---|
| 1.57 (old) | 1.57 rad/s | **0.0274 rad/s** |
| **0.5 (current)** | 0.5 rad/s | 🔴 **0.0087 rad/s** |
| `RO_YAW_RATE_TH` 3.0 | — | 0.0524 rad/s deadband |
🔴 **THE ACRO YAW COMMAND IS 6× BELOW THE MEASUREMENT DEADBAND** ⇒ `DifferentialRateControl` zeroes
it ⇒ **the rate controller emits EXACTLY 0.0000 and the rover cannot yaw in Acro at all.**
✅ **MEASURED PROOF: 1820 samples, all `nav_state=10` (ACRO), all ARMED, holding yaw stick →
`/fmu/out/rover_steering_setpoint` flat 0.0000, gyro ±0.004 rad/s.** Matches the operator's report
("in acro only forward/reverse work, yaw sits idle") exactly.
⚠️ **`RO_YAW_RATE_LIM` is NOT referenced by `DifferentialRateControl` at all** (only by
`DifferentialManualMode` and the *ackermann* modules) ⇒ **it never constrained the AutoNav path where
the 07-29 runaway happened.** The old note *"exceeds RO_YAW_RATE_LIM 1.57 by ~4×"* assumed rad/s AND
assumed it applied — **both wrong; delete that reasoning.**
⏭ **FIX: set `RO_YAW_RATE_LIM` ≈ 28.6 (deg/s) for a real 0.5 rad/s**, then Acro becomes a SAFE test
bench for the rate loop at `RO_YAW_RATE_P=0.05`.

## ✅ 2026-08-02 — `RO_MAX_THR_SPEED` WAS 5× WRONG: 3.0 → **0.6** (set + verified)
Param doc: *"Speed the rover drives at maximum throttle … @unit m/s"*. The drivetrain actually reaches
**~0.58-0.60 m/s** (which is why `RO_SPEED_LIM` was set to 0.70). It divides the feedforward in
**BOTH** the speed and yaw-rate loops: `FF = sp*track/2 / RO_MAX_THR_SPEED` ⇒ FF was **5× too small**,
so the PID had to supply everything — which is why `P=2.0` produced a violent command from a 0.3 rad/s
request. **Now 0.6, verified by readback; other gains untouched.**

## ⚠️ 2026-08-02 — TWO #20 HYPOTHESES KILLED. Do not re-propose.
1. ❌ **NOT a gyro sign error.** Operator drove Manual RIGHT-then-LEFT: first burst **+5.23 rad/s**,
   second **−5.40 rad/s** — PX4 FRD says clockwise = positive. **Sign and magnitude both correct.**
2. ❌ **NOT "measurement never reaches the estimator".** `ATTITUDE.yawspeed` is fed from
   `vehicle_angular_velocity`, reads ±0.0015 rad/s at rest and tracks real rotation ⇒ **that topic is
   alive and correct.**
🔑 **Also measured: Manual full stick = 5.2-5.4 rad/s.** The 07-29 "runaway" of 5.7-6.3 rad/s was
therefore **≈ full-stick output**, not an exotic instability.
⚠️ **METHOD — I briefly claimed "positive feedback" from data that was actually MANUAL driving.**
In Manual the rate controller is not in the loop, so its output proves nothing. **ALWAYS log
`nav_state` alongside any control-loop probe** (`tmp/rate_probe2.py` does; v1 did not).
⏭ **STILL OPEN: the AutoNav runaway itself is NOT yet reproduced or explained.** Fix the LIM units
first, then use Acro at P=0.05 as the safe bench.

## 🔴🔴 2026-08-02 — **#21 GYRO-YAW ODOMETRY IS VALIDATED, AND IT FAILS.** First real driving test.
A 206 s manual mapping run through one room + hall. **Operator CONFIRMED the rover physically
finished where it started.** Odometry disagrees:
| | measured |
|---|---|
| path length | 54.1 m |
| **closure gap (start→end)** | 🔴 **6.83 m — pure DRIFT, ~13% of path** |
| total rotation | 🔴 **2554°** (≈7.1 turns, for one room + a hall) |
| net heading change | **−89.8°** ✅ **NOT an error** — operator confirms they finished on a
DIFFERENT heading (drove forward out of the loop), so ~−90° is plausibly the true final orientation |
| peak yaw rate | 🔴 **13.15 rad/s = 753°/s** (`RO_YAW_RATE_LIM` is 0.5; physically impossible) |
| \|w\|>1.0 rad/s | **7.9% of samples**, 679 discrete spike events, bursty |

### What it is NOT — three hypotheses KILLED by measurement, do not re-propose
1. ❌ **NOT a tiny-`dt` division artifact.** Header-stamp `dt`: median **10.17 ms**, min 0.957 ms,
   **zero non-positive**. Samples with |w|>5 have *normal* dt (median 11.56 ms).
2. ❌ **NOT a bug in `rover_odometry`'s rate computation.** Reported `twist.angular.z` agrees with
   `d(yaw)/dt` from the pose quaternion within 1 rad/s for **97.95%** of samples.
3. ❌ **NOT fixable by clipping the rate.** Re-integrating with clips 2.0/1.0/0.5 gives gaps
   7.94 / 4.94 / 7.98 m vs 5.67 m unclipped — **no clip closes the loop**, and heading error stays
   72-338°. **Do not build a spike filter and call it fixed.**

### What it IS
🔑 **The jumps are REAL discontinuities in the attitude quaternion itself** — total |d(yaw)|
integrated straight from the pose quaternions is the same **2554°**. `rover_odometry` takes heading
from `/fmu/out/vehicle_attitude` deltas and **its `quat_reset_counter` guard is not catching these**
(see 21a). ~679 spike events at ~11 ms each plausibly account for **most of the excess** over the
~600-700° the route actually needed. ⇒ **the defect is UPSTREAM of `rover_odometry`, in what the FC
publishes (or in which resets we drop), not in the arithmetic.**

### 🔑 REFINED once heading was exonerated — POSITION is wrong while NET HEADING is right
That combination is diagnostic. Errors that cancel in the *net* heading still accumulate in
*position*, because position integrates heading **continuously**. Two mechanisms, both live:
1. **The 679 attitude jumps** inject TRANSIENT heading error. Position integrates through each one
   and never recovers it, even when the net washes out. This is the defect.
2. ⚠️ **Skid-steer LATERAL SLIP — inherent, not a bug, and NOT fixable in odometry.** A skid-steer
   *must* slide sideways to rotate, and forward-wheel odometry is blind to sideways motion. With
   **2554° of rotation** in 206 s that is a large unobserved translation. **No amount of gyro
   accuracy removes it** — only an exteroceptive fix (visual/lidar) can.
⇒ **Do not expect to "fix" `/odom` into a mapping-grade prior. Even repaired, mechanism 2 remains.**
⚠️ **2554° is NOT by itself proof of a fault** — a skid-steer manoeuvring around a room genuinely
turns a lot. **The physically impossible 13.15 rad/s spikes are the hard evidence; the rotation
total is not.** Do not cite the 2554° as the defect.

### Consequences — act on these
- 🔴 **`/odom` MUST NOT be used as a motion prior for RTAB-Map.** It would bend the map. **Use
  VISUAL odometry** — the bag holds everything to try both on the same drive.
  → [[project-autonomy-plan-reframe]]
- 🔴 **Every `/odom`-derived pose is suspect through turns.** Straight-line speed was validated
  (`42f9aa2`) and is unaffected; **heading is not.**
- ⚠️ **Possible link to #20.** If the attitude source jumps, an apparent "yaw rate runaway ~21×"
  measured against it may be partly MEASUREMENT, not motion. **Not established — but re-examine #20's
  evidence before assuming the controller is at fault.**
- ⏭ Next diagnostic: log `quat_reset_counter` alongside `vehicle_attitude` and see whether the jumps
  coincide with resets that are being missed.
- Data: `~/mapping_run2_20260802` (3.4 GiB, 99.7% capture) — re-runnable, no re-drive needed.

## ⏭ RESUME HERE — 2026-08-01 (session crashed ~16:12; state recovered + verified 16:55)
**Verified live at recovery: services mavlink.router / microxrce-agent / wifibroadcast@drone /
rover-camera / rover-scan / rover-odometry / rover-autonav-mode ALL ACTIVE. `rover-ekf-bridge`
inactive (correct, deliberate). `/odom` 99.7 Hz ✅. `/scan` 16-19 Hz ⚠️. Load 3.77 on 4 cores.
`vision_streaming` STOPPED at 10:51 by SIGTERM after a 9h12m clean run — deliberate, matches the
"don't stream FPV while driving" rule, NOT a fault.**
🔴 **A LATE SESSION (13:00-16:12) WAS LOST AND ITS WORK WAS NEARLY UNDOCUMENTED.** It built the 3D
perception layer and rewrote the autonomy ladder → **[[project-perception-3d-costmap]]** and
**[[project-autonomy-plan-reframe]]**. **ros2_ws is 12 commits AHEAD of origin/main and has 2
UNCOMMITTED files holding measured calibration values — push and commit before anything else.**
⚠️ **`/scan` is 16-19 Hz with video OFF, vs 22.3 Hz previously measured WITH video streaming** — the
new perception path may cost more than the video did. Re-measure the worst gap before any armed test.

### Yaw — PARKED FOR **OUTDOOR, 2026-08-02** (unchanged by the crash)
**State left: DISARMED, nav_state 0 (Manual), `rover-ekf-bridge` STOPPED, other 4 autonav services
active, `/odom` 99.9 Hz. ros2_ws committed, NOT pushed.**
- ✅ **`RO_YAW_RATE_P` = 0.05 and `RO_YAW_RATE_LIM` = 0.5 — user ran `param save` 08-01, both read
  back correct.** (Was 2.0 / 1.57.) ⚠️ Persistence NOT independently verified: the saved-vs-RAM flag
  is only visible via NuttShell `param show`, which has wedged this link before. **Re-read both after
  any FC reboot** (`tools/set_param.py RO_YAW_RATE_P`) — 2.0 is the runaway value.
  ⚠️ `RO_YAW_RATE_LIM` clamps the **SETPOINT ONLY, never the achieved rate** — it did not stop the
  6.3 rad/s runaway. It limits what can be asked for, it is NOT protection. Test setpoints 0.2/0.4
  both sit under the new 0.5 cap, so no conflict.
- **Why yaw was parked:** indoor space insufficient. Measured the visible arc — obstacle at **0.48 m
  on the far right = only 0.21 m clear of the rover body**; a skid-steer spin TRANSLATES into it.
- ⚠️ **The depth cam sees only 92° (-46..+46) and `range_min` is 0.30 m.** 268° incl. the whole rear
  is UNMEASURABLE, and anything closer than 0.30 m reads as "nothing there". **Never clear a spin
  from `/scan` alone — it cannot see where a spin goes.**
- **The yaw test needs only ~23-46°** (l2_test yaw leg = 2.0 s: 0.2 rad/s→23°, 0.4→46°). NOT a 360.
  Space needed: ~1.5 m clear radius **plus ~0.5 m ahead**, because l2_test always runs its forward
  leg first and `--speed 0` makes that check fail and abort before yaw.
- **Tomorrow:** `yaw_response_log.py 290 --p-gain 0.05` in one shell, then
  `l2_test.py --live --speed 0.1 --yaw 0.2` and again `--yaw 0.4`. Two setpoints so the ratio is a
  confirmed constant, not a single-point fit.

## ⚠️ 2026-08-01 — HOW TO READ THE YAW TEST (the discriminator, learned the hard way)
**Discriminate on `steering/setpoint`, NOT absolute output, and NOT on how the rover behaves.**
Dropping `RO_YAW_RATE_P` 2.0→0.05 to make the test safe ALSO made an open loop produce roughly the
*commanded* yaw rate — so **the rover's visible behaviour stops distinguishing the hypotheses.**
| `steering ÷ setpoint` | verdict |
|---|---|
| **≈ 0.102** (= FF 0.0517 + P 0.05) | **OPEN loop** — controller never sees `vehicle_angular_velocity`. **No gain fixes it**; firmware/sensor work. |
| **≈ 0.052** (FF only, error → 0) | **CLOSED loop** — feedback alive, it IS a tuning job (`RO_YAW_RATE_P/I`). |
⚠️ **The tool printed a confident "matches OPEN LOOP" on the 08-01 forward-only run where yaw sp was
0.0 — a degenerate case with ZERO discriminating power (separation 0.001). That verdict was
MEANINGLESS.** Guard added (`fdf8d37`, `f8f1988`): it now refuses a verdict below |sp| 0.05.
**No yaw evidence has been collected yet.** The open-loop hypothesis still rests only on the 07-29
arithmetic.

## ✅ 2026-08-01 — SPEED LOOP VALIDATED ARMED after the scale fix (L2 re-PASS, forward-only)
Commanded 0.2 m/s: **peak ERPM 170 → 80**, `/odom` peak **0.363 m/s** (80 x 0.004633 = 0.371, agrees
to 2%). Clean auto-disarm + Hold. Gyro sustained −0.014 rad/s ⇒ tracked straight.
🔴 **THE REAL SAFETY POINT: under the old scale the setpoint was PHYSICALLY UNREACHABLE.** Making
`/odom` read 0.2 m/s needed **526 ERPM ≈ 2.4 m/s** real, and `RO_SPEED_LIM` 0.7 implied ~1840 ERPM
≈ **8.5 m/s** — so the speed controller had no equilibrium and **just accelerated until it ran out of
floor.** That is why forward legs kept climbing instead of holding. Setpoint is now 43 ERPM, reachable.
⚠️ Still ~1.8x over (80 peak vs ~43 expected) — **probably accel overshoot + `RO_SPEED_I` windup, but
UNCONFIRMED**: only *peak* was logged, not sustained. Sustained logging added; re-check on a longer leg.

## ✅ 2026-08-01 — `erpm_to_ms` MEASURED: was **12.2x TOO SMALL**, now FIXED (`42f9aa2`)
**0.000380 → 0.004633.** The old value was assumed geometry, `pi*0.1524/(7*3*60)`, implying
`pole_pairs*gear_ratio = 21`. **Measured, that product is ~1.75** — the assumed drivetrain is not
this drivetrain. ⇒ **every distance and velocity `/odom` ever reported was ~12.2x low.**
**METHOD THAT WORKED (use this again): push the rover BY HAND through N counted wheel revolutions.**
No slip, no tape measure, and **the wheel diameter cancels out**:
`pole_pairs*gear_ratio = ERPM_seconds / (60*revolutions)` = 516.7/(60*5) = **1.722**.
Powered 2.13 m tape drive agreed independently (1.788 / 0.004463 — tape error + slip bias it low).
Tool: **`tools/odom_scale_measure.py --revs 5`** (reports coverage, straightness, implied product).
- ⚠️ **The old ">=2.3x low" figure was a LOWER BOUND ONLY**, from a skid-steer spin. Scrub makes
  wheels turn far more than the achieved rotation implies — **real slip factor in that spin was ~5x.**
  Never treat a spin-derived scale as an estimate; it is a floor.
- **`deadband_erpm` 40 → 5** as a consequence. 40 ERPM was chosen when it meant 0.015 m/s; at the
  true scale it is **0.185 m/s** and would have swallowed most of Nav2's fine-positioning range.
  Standstill noise re-measured, 2930 samples x 4 wheels: **min 0, max 0 — the "+/-35 ERPM idle
  jitter" note does NOT reproduce.** ⚠️ re-check armed (dithering motors may differ from idle).
- 🔴 **RE-READ ALL PRE-08-01 SPEED NUMBERS AS 12.2x LOW.** "commanded 0.2 m/s → /odom 0.081" means
  the rover was really doing **~1.0 m/s — 4-5x the commanded speed.** The FC speed loop closes on
  EKF velocity fed from `/odom` via `rover_ekf_bridge`, so it was over-driving to chase an
  under-reported measurement. **This fix is a prerequisite for any armed AutoNav floor test.**
  The "forward is comparatively tame (~0.08-0.15 m/s)" note was the under-reported figure, not reality.
- ⚠️ Two earlier versions of the measuring tool produced **confident wrong answers** (0.00452, then
  ~0.0044) by silently dropping frames and by measuring straightness against `/odom`'s ABSOLUTE pose
  (which includes every earlier drive). **Instrument coverage and straightness or don't believe the run.**
- Also cleared: `esc_status` runs at **99.4 Hz** (not ~50), and its timestamps track wall clock to
  1.0003 — the integration timebase is sound, ruled out as a cause.

## ✅ 2026-08-01 — `/odom` at rest FIXED (`bee3abe`) — the ESC-doze L5 blocker
`wheel_odometry_node` now publishes a **zero-velocity** sample when a side has no online ESC but
**every awake ESC reads inside the deadband**. Rationale: a dozing VESC cannot be driving its wheel,
and a wheel turned externally wakes its ESC — so that state is a real measurement, not missing data.
Guard stays narrow: **any awake wheel reporting motion while the other side is unreadable still skips
and warns.** Param `publish_at_rest` (default true) restores the old behaviour for A/B.
Verified on synthetic EscStatus: flags=15 stopped publishes, flags=8 stopped publishes, flags=8 with
addr 13 spinning stays silent, recovers on all-four. ⚠️ **Not yet seen against a live doze** — the
ESCs stayed awake for a 4-minute watch.

## 🔴 2026-08-01 — `/odom` DIES AT REST (ESC doze). NEW L5 BLOCKER. Answers the 07-26 "unknown".
Measured: **zero `/odom` messages in 25 s, with FPV video both ON and OFF — so it is NOT a CPU
problem.** `/fmu/out/esc_status` reports `esc_online_flags: 8` = **only ESC 13 awake**, the other
three asleep, so `wheel_odometry_node` logs `incomplete wheel data (L:1 R:0) — skipping update`
every 5 s and publishes nothing at all. Recovers on a wheel nudge (flags → 15).
**Why it blocks L5:** Nav2 cannot plan against an odometry topic that goes silent whenever the rover
sits still, and `rover_ekf_bridge` would lose its input mid-mission if the ESCs can also doze while
armed (still untested armed).
⚠️ **`/odom` is RELIABLE QoS** — a BEST_EFFORT subscriber reads 0 msgs and looks exactly like this
fault. Check QoS before diagnosing. (`/scan` publishes both RELIABLE and BEST_EFFORT.)

## ⚡ 2026-08-01 — FPV video taxes autonomy ~21% (measured, both directions)
| | `/scan` rate | worst gap |
|---|---|---|
| video ON | **22.3 Hz** | **235 ms** |
| video OFF | **28.4 Hz** | 132 ms |

28.4 Hz matches the post-tfmini baseline. At ~0.6 m/s a 235 ms gap = **~14 cm travelled before the
collision reflex sees anything**, ≈ ¼ of the 0.60 m block margin (8 cm with video off). Tolerable
now; **L5 Nav2 costmaps/planners land on the same 4 cores**, which are already oversubscribed —
software x264 alone needs 80-95% of one. ⇒ **don't stream FPV during autonomous driving if you want
full reaction speed.** Related failure mode: `~/ros2_ws/docs/vision_streaming.md` (CPU-starvation latch).

## ⏭ RESUME HERE — 2026-07-28 (floor session: #20 baseline captured, WALL CONTACT, collision-stop hardened)

**#20 baseline is MEASURED but NOT finished. Collision-stop hardened + committed (`7261fc7`, NOT pushed).**

### Baseline numbers (floor, armed, AutoNav, gains still 2.0/0.1) — L2 re-PASS
- forward 0.2 m/s → peak ERPM `[-169, 171, 170, 171]` (all 4 respond, tight)
- yaw 0.3 rad/s → peak ERPM `[-868, -762, 813, -1065]` = **~5x the forward effort, ~40% L/R asymmetry**
- watchdog zeroed motors; clean auto-disarm + Hold.
- **STILL MISSING = achieved body yaw rate.** Commanded-vs-achieved is the number that decides whether
  the gains are hot or whether skid-steer scrub genuinely costs that much. `l2_test.py` does not record
  it → wrote **`tools/yaw_response_log.py`** (passive, commands nothing, run it alongside `l2_test.py --live`).
- `l2_test.py` gained **`--speed` / `--yaw`** so 0.2 and 0.4 m/s can be swept without editing code.
  The 0.4 m/s leg was never run.

### ⚠️ TRAP 1 — EKF eph grows without bound → AutoNav/Hold refused WHILE ARMED
`rover_ekf_bridge` feeds EKF2 **velocity only** (by design — wheel position drifts unbounded). With no
position aiding at all, EKF2's horizontal position variance grows forever. Found this session:
**eph = 682 m, x = 697 m, y = 1936 m** after long FC uptime, vs **`COM_POS_FS_EPH` = 5.0 m**
⇒ `local_position_invalid = true`.
- **While ARMED, PX4 refuses to ENTER any mode requiring local position — AutoNav (23) AND Hold (4).**
  The rover just stays in Manual and the DO_SET_MODE looks silently ignored.
- **While DISARMED the requirement is not enforced**, so a `--dry-run` mode switch succeeds and looks
  fine. Armed-vs-disarmed is the whole difference — do not read a passing dry-run as proof.
- `local_velocity_invalid` stays **false** throughout (evh ~0.06 m/s, excellent) — only *position* rots.
- **Fix = reboot the FC** (`VehicleCommand` 246 `PREFLIGHT_REBOOT_SHUTDOWN` param1=1, over DDS; script
  kept at scratchpad `fc_reboot.py`, refuses unless disarmed + wheels stopped). After reboot: eph
  682 m → **0.42 m**, x/y → ~0, `local_position_invalid` → false, FC came back **disarmed** (it can come
  back armed — always check). `autonav_mode` dies on FC restart and systemd restarts it clean.
- **GROWTH RATE measured 07-28: eph 0.42 m → 1.61 m in ~15 min ≈ 0.08 m/min.** From a fresh reboot that
  is a **~45-60 minute working window** before the 5.0 m gate bites. Plan floor sessions around it and
  re-check `eph` before each armed run rather than being surprised mid-session.
- **This WILL recur** — it is inherent to velocity-only aiding, so budget an FC reboot before floor work.
  Durable fix is an L5/L6 item: give EKF2 a bounded position source (SLAM pose → `vehicle_visual_odometry`
  position). Nav2 will hit this too.

### 🔎 2026-08-01 YAW ANALYSIS (firmware + live params, no armed test) — points at ABSENT FEEDBACK
Read the REAL firmware (`~/PX4-Autopilot` branch **`pxlabs-fw` @ a52c38b** = the FC build) plus live
params via pymavlink PARAM_REQUEST_READ. Chain is `DifferentialRateControl.cpp` →
`RoverControl::rateControl` (`src/lib/rover_control/RoverControl.cpp:163`).
- **`RD_WHEEL_TRACK` = 0.31, CORRECTLY SET** (default is 0). ❌ "feed-forward is disabled" — WRONG, deleted.
  ⚠️ but note `runSanityChecks` only errors if FF params **and** `RO_YAW_RATE_P` are all ~0, so a zero
  track would have been silent. Worth re-checking after any param wipe.
- FF term = `yaw_rate_sp * RD_WHEEL_TRACK/2 / RO_MAX_THR_SPEED` = 0.3*0.31/2/3.0 = **0.0155** — tiny.
- Observed yaw differential was ~870/1500 ERPM ≈ **0.58 normalized** ⇒ the PID supplied ~0.56
  = `RO_YAW_RATE_P (2.0) x error` ⇒ **error ≈ 0.28 rad/s ≈ the ENTIRE setpoint** ⇒ the yaw rate the
  loop *measures* is **≈ 0** while the gyro logged 5.7-6.3 rad/s. **The loop is running OPEN.**
  A closed loop at P=2.0 would have slammed to full reverse (error -6 → -12, clamped -1); the rover
  instead span steadily one way, which a working loop cannot do.
- Explains why achieved rate blew through `RO_YAW_RATE_LIM` 1.57 by ~4x: **that limit clamps the
  SETPOINT, never the outcome.**
- Live params: RO_YAW_RATE_P 2.0 · I 0.1 · LIM 1.57 · TH 3.0 (**degrees**, x M_DEG_TO_RAD_F in fw) ·
  CORR 1.0 · ACCEL/DECEL_LIM -1 · RO_MAX_THR_SPEED 3.0 · RO_SPEED_LIM 0.7 · RD_YAW_STK_GAIN 1.0.
- **NEW INSTRUMENTATION nobody used before: `/fmu/out/rover_steering_setpoint` and
  `/fmu/out/rover_throttle_setpoint` ARE exported over DDS** (dds_topics.yaml:111,114) — that is the
  rate controller's own OUTPUT. Log it vs `sensor_combined.gyro_rad[2]` to settle open-loop vs
  unstable-loop directly. (`rover_rate_status`, which carries measured_yaw_rate + PID integral, is
  NOT exported — would need a dds_topics.yaml change on next flash. Worth adding.)
- **SAFE NEXT TEST:** set `RO_YAW_RATE_P` 2.0 → ~0.05 FIRST. Even fully open-loop that gives
  0.05*0.3 + 0.0155 ≈ 0.03 normalized (~45 ERPM) — **it cannot run away** — then log steering vs gyro.

### 🔴 FINDING A (2026-07-29, BIGGEST OF THE SESSION) — YAW RATE RUNAWAY, ~21x COMMAND
Commanded **0.3 rad/s** → the rover actually rotated at **~6.3 rad/s** (≈1 rev/s, **~2 full turns in the
2 s leg**). Three agreeing sources: raw gyro `sensor_combined.gyro_rad[2]` **sustained 5.70 / peak 8.02
rad/s**, `/odom` angular.z sustained 7.28, and **the user watching it** ("fast — roughly 2 full turns").
- This also **exceeds the FC's own `RO_YAW_RATE_LIM` = 1.57 rad/s by ~4x**, so the FC's yaw-rate loop is
  not controlling at all — this is NOT a gain-trim job, it is a broken/saturating loop.
- **This is what drove the rover into a wall**, and why yaw "translates" so violently.
- ⛔ **DO NOT run armed yaw tests until this is fixed.** Forward-only is comparatively tame
  (~0.08-0.15 m/s).
- Reproduced identically across 3 armed runs: yaw peak ERPM `[-868,-762,813,-1065]`,
  `[-1021,-977,764,-1123]`, `[-1030,-993,752,-1129]` vs forward only ~170.
- **Measure yaw rate from `sensor_combined.gyro_rad[2]`** (99.6 Hz, reads −0.004 rad/s at rest; negate
  for ROS FLU sense). `vehicle_angular_velocity` is NOT in this FC's dds_topics.yaml.
  Tool: **`tools/yaw_response_log.py`** — passive, commands nothing, logs gyro vs /odom vs ERPM per burst.

### 🔴 FINDING B (2026-07-29) — `erpm_to_ms` IS WRONG BY ≥2.3x, /odom UNDER-REPORTS SPEED
`src/rover_odometry/config/rover_odometry.yaml:12` has **`erpm_to_ms: 0.000380`**. Back-calculated from
the confirmed ~6.28 rad/s spin: 0.31 m track ⇒ ~0.97 m/s per side ⇒ at the measured ~1090 ERPM the true
scale is **≈0.00089 m/s per ERPM**. Slip only pushes the real value HIGHER, never lower, so ≥2.3x low.
- Explains forward: commanded 0.2 m/s, `/odom` reported only **0.081 m/s** (true ≈0.15-0.19).
- **Contaminates everything downstream**: `/odom` → EKF2 EV velocity (via rover_ekf_bridge) → and
  Nav2 + slam_toolbox at L5. Fix this BEFORE L5; a 2.3x velocity scale error would wreck SLAM.
- **Clean way to fix it: drive a tape-measured straight distance (e.g. 2 m) and compare `/odom`'s
  reported travel.** That gives the scale directly, no back-calculation. Do this first next session.
- Formula in the yaml for reference: `ERPM -> m/s = pi * wheel_diameter / (pole_pairs * gear_ratio * 60)`
  — so one of wheel_diameter / pole_pairs / gear_ratio is wrong.

### ⚠️ FINDING C — the collision-stop's ±20° cone is BLIND to the sides and rear
Yaw translation carries the rover sideways toward obstacles the sensor **cannot see at all**. Forward
clearance is therefore the WRONG metric when planning a yaw test — what matters is open **radius**.
(Partial self-correction: I first called `/odom` angular.z "physically impossible garbage". Its
*sustained* value tracks the gyro fine; only its **peaks** are differentiation noise — 47.8 vs 8.02.
It was not inventing the rotation, the rotation was real.)

### ⚠️ TRAP 1b — `eph` after an FC reboot is a LOTTERY, not a convergence
An FC reboot usually lands eph ~0.13-0.42 m, but one reboot on 07-28 came up at **14.15 m and STAYED
there** — flat, creeping up only 0.008 m/min at rest, never coming down. With velocity-only aiding there
is **no position measurement that can ever shrink eph**, so a bad initial value is permanent for that
boot. Another reboot fixed it (0.146 m).
⇒ **Always read `eph` after a reboot before planning an armed run.** Don't wait for it to "settle" — it
won't. If it comes up over the gate, just reboot again.
Growth rate depends on motion: ~0.08 m/min while doing drive tests, ~0.008 m/min sitting still.

### ⚠️ TRAP 1c — FC reboot can wedge the AutoNav registration into a restart loop
After one reboot, `autonav_mode` hit `Registration failed` (it DOES get `RegisterExtComponentReply`,
then the lib throws) and systemd `Restart=always` looped it every ~12 s forever. A 30 s stop-and-wait
did NOT clear it — the FC holds the external-mode slot.
⇒ **Fix = stop the service FIRST, then reboot the FC, then start the service.** Ordering matters: the
service must not be racing the FC's boot. Rebooting while the node is restart-looping just re-wedges it.

### ⚠️ TRAP 2 — the rover hit a wall WITH the collision-stop working correctly
Not a malfunction; two design gaps, both now fixed in `7261fc7`:
1. **Yaw was never gated** (`mode.hpp` only ever zeroed `speed`). A skid-steer spin with unequal L/R
   wheel speeds **TRANSLATES** — the yaw leg above is 760-1065 ERPM with 40% asymmetry — so yaw drove
   the rover into a wall the forward brake could see and had no authority over.
   ⇒ yaw is now **capped** to `collision.blocked_yaw_rate` 0.30 rad/s while blocked (cap, not cancel —
   it must still rotate away). Reverse still free.
2. **Thresholds were compared against raw `/scan` range**, but `/scan` originates at `camera_link`,
   which is BEHIND the bumper. 0.60 m of range was only ~0.26 m of real bumper clearance.
   ⇒ new `collision.front_overhang`; distances now mean **clearance at the bumper**.
   Defaults now **stop 0.35 / clear 0.50 at the bumper** (raw 0.69/0.84).
- **`front_overhang` = 0.337 m is MEASURED, not assumed**: park the rover square against a flat wall
  with ZERO gap and read the forward-sector min — 178 scans, min == max == 0.337 m, no spread. Agrees
  with the 0.345 m `base_link`→plate-tip doc figure to within 8 mm. **Re-measure this way after ANY
  camera remount** (scratchpad `measure_overhang.py`). This is a cheap, high-confidence calibration.
- My planning error to not repeat: I cleared the run on "front = 1.85 m" by budgeting only the forward
  legs (~0.7 m) and **ignored translation during the ungated yaw leg**. Budget the yaw leg too, or
  point the rover at open space for yaw work.
- Correction worth keeping: I first blamed the 07-26/27 remount for reducing margin. **Wrong — it
  roughly doubled it** (old cam_x −0.125 sat 0.470 m behind the tip ⇒ 0.60 m raw was only 0.130 m of
  bumper clearance). No damage from the contact; user confirmed.

### Next session, in order
1. Reboot the FC first if it has been up a while (check `eph` < 5 m before anything armed).
2. Reposition facing **several metres of open floor** (the rover ended nose-to-wall).
3. Re-run the baseline with `yaw_response_log.py` running → get **achieved vs commanded yaw rate**,
   then sweep `--speed 0.4`. Only then change `RO_YAW_RATE_P/I` (pymavlink `PARAM_SET` on tcp:5760).
4. Verify the new yaw cap fires armed (it has only been validated passively, disarmed, at the wall).
5. Then L5.

## ⏭ (previous) 2026-07-23 (planning/alignment session; #20 yaw tuning deferred by user to a floor session)
**L2 IS DONE. Reflex collision-stop built, validated end-to-end, committed + pushed. Next = yaw-gain tuning (#20), then L5.**
Full session detail in [[project-l2-floortest-wheel0-reversed]].

### Session 2026-07-23 (realignment — no hardware)
- **Created `ros2_ws/docs/roadmap.md` = the tracked SOURCE OF TRUTH for direction** (goal definition +
  L0-L7 ladder + critical path + supporting debt). Committed + **pushed origin/main**: `8f5c522` roadmap,
  `ae647a4` dds_topics next-flash note. Tree clean, main even with origin.
- **Goal restated (in roadmap.md §1)**: North Star = dual aerial+ground GPS-denied autonomy on one RPi5;
  current campaign = rover indoor Nav2. Ladder status: **L0-L4 DONE, L5 (Nav2 goal+avoidance) = next big
  milestone**, then L6 SLAM/routing, L7 safety. Interstitial before L5: #20 yaw tuning + gyro-yaw
  drive-validation + `/scan` tape check.
- **Live topic audit (ros2 topic list + hz)**: everything Nav2/slam_toolbox/L5-L7 needs is already
  exposed AND flowing — `/scan` 25 Hz, `/tf`+`/tf_static`, `/cmd_vel`, `vehicle_attitude` 100 Hz,
  `vehicle_local_position_v1` 50 Hz, `esc_status` 50 Hz, `failsafe_flags`, `collision_constraints`,
  `home_position_v1`. **No firmware reflash needed to reach the first autonomous drive.**
  - `/odom` was SILENT during the audit → **rover motor bus unpowered** (rover parked/off), NOT a bug;
    `esc_status` streams regardless, `/odom` only publishes when all 4 VESCs report online.
  - **`/fmu/out/vehicle_angular_velocity` confirmed ABSENT from dds_topics.yaml** (matches prior note).
    Recorded in roadmap supporting-debt as an "add on next flash" nice-to-have (helps #20 yaw tuning +
    gyro-yaw odometry; today worked around via `vehicle_attitude` deltas + raw `sensor_combined.gyro_rad`).
    Optional companion: `sensors_status_imu` for IMU-health diagnostics over DDS (uplink is dead).
- **#20 yaw tuning NOT started** — user deferred to a session with the rover on the floor. When resuming:
  floor + RC-ready → start `rover-ekf-bridge` by hand → **baseline `l2_test.py` first** (measure yaw-vs-fwd
  rpm against the fixed 0.31 track before changing gains) → adjust `RO_YAW_RATE_P/I` (2.0/0.1) via pymavlink
  `PARAM_SET` on tcp:5760 (NOT mavlink_shell.py). FC left disarmed/Hold, bridge stopped.
  **FIELD CHECKLIST is now a tracked doc: `~/ros2_ws/docs/yaw_tuning_session.md`** (ros2_ws main @ 8f84bf1) —
  full preconditions/bring-up/baseline-then-tune/opportunistic(gyro-yaw + /scan tape)/safety/teardown +
  a results-log table to fill in on the floor. Open it and work down the checkboxes when at the rover.

What got done 2026-07-22/23:
- **L2 armed floor run PASSED.** First-ever armed floor drive. All 4 wheels respond to fwd+yaw, watchdog
  zeroes motors, auto-disarm+Hold clean. Wheel-0 "reverse" was a FALSE ALARM (mirrored ESC sign, all 4
  physically go forward — the old sign check is removed).
- **Reflex collision-stop built INSIDE the executor** (can't be bypassed): ±20° front cone, block <0.60m /
  clear >0.75m hysteresis, stale-scan fail-safe, `collision.*` params. Validated passively on stands AND
  **fired armed end-to-end** — stopped the rover ~0.59m from a real wall. See
  `~/ros2_ws/docs/rover_autonav_collision_stop.md`.
- **Committed + pushed: ros2_ws origin/main @ `b38e413`.** Tree clean.

**ARM WORKFLOW (important, use this every time):** AutoNav (external mode) CANNOT be armed via RC — RC
arming lands in Manual. So: operator **arms in Manual via RC (throttle neutral)**, THEN software
`DO_SET_MODE main=4 sub=11` → AutoNav, which HOLDS. `l2_test.py --live` does this (tolerates an
already-armed-in-Manual start; never software-arms). **Kill (ch8) confirmed working armed in AutoNav.**

State left behind: FC **disarmed, Hold (nav 4)**, `rover-ekf-bridge` **stopped** (start by hand on the
floor only; wheels-up + bridge = limit cycle). Other services auto-start from boot (camera/scan/odometry/
autonav-mode). ros2_ws tree clean @ b38e413.

Next session, in order:
1. `systemctl is-active rover-camera rover-scan rover-odometry rover-autonav-mode` (all active from boot).
2. **Yaw-gain tuning (todos #20)** — armed yaw drove wheels MUCH harder (~700-850 rpm) than forward (~156).
   Revisit RO_YAW_RATE_P/I (2.0/0.1) — they were tuned against the old oversized track. Re-run l2_test on
   the floor after each change (arm in Manual → it switches to AutoNav; bridge on the floor only).
3. (opt) validate gyro yaw — turn a known angle vs floor marks, compare `/odom` yaw, A/B `yaw_source:=wheels`.
4. **L5**: slam_toolbox on `/scan`+`/odom`, then Nav2 — the real routing/avoidance/reroute brain (the
   collision-stop is only the safety floor). Camera TF measured, Nav2+slam_toolbox installed → unblocked.

Nav2 footprint must follow the **0.405 m top plate**, not the 0.31 m track — wheels sit inboard.
Full spec: `~/ros2_ws/docs/rover_autonav_requirements.md`; collision-stop + arm workflow:
`~/ros2_ws/docs/rover_autonav_collision_stop.md`. Read both before any autonav work.

## Agreed scope (user-aligned 2026-07-19)
Indoor GPS-denied FIRST · Nav2 full stack · forward-only depth v1 (Gemini 336L depth stream only, never ffmpeg).

## Architecture in one line
Orbbec depth → /scan → Nav2 (slam_toolbox map, global planner, local costmap/controller) → cmd_vel → `nav2_px4_bridge` custom PX4 mode "AutoNav" (px4_ros2 control interface, TrajectorySetpoint vel+yawrate) → PX4 rover-diff → VESC UAVCAN. Wheel odom (`rover_odometry`, math in [[rover-odometry]]) → /odom+TF → Nav2 AND → EKF2 via px4_ros2 `LocalPositionMeasurementInterface`.

## Key facts verified 2026-07-19 (full detail: ros2_ws/docs/ros2_architecture.md)
- **FIRMWARE CORRECTION 2026-07-19**: FC actually runs **pxlabs-v1.17.0-2.0.0** @ a52c38b07d, built 2026-05-31 (NuttShell `ver all`) — NOT v1.16.0-rc1/c5b8445 as previously recorded. Pxlabs fork source NOT on companion → static msg check impossible; compat is RUNTIME-proven (DDS up, all topics flow) + lib's messageCompatibilityCheck gates at mode registration (M4).
- **Pxlabs firmware source ON COMPANION since 2026-07-19**: repo https://github.com/ArvinVeiyon/PXLABS_PX4-Autopilot.git = remote `pxlabs` in ~/PX4-Autopilot; build commit a52c38b kept as local branch `pxlabs-fw`. Static msg checks now possible.
- **px4_msgs RE-PINNED 2026-07-19 → release/1.17 @ 86d8239** (local branch `pinned-pxlabs-1.17`): check-message-compatibility.py vs REAL firmware a52c38b = **full exact match**. Old pin d2c9ff2 had ArmingCheckRequest v0 (2 fields) vs firmware v1 (+valid_registrations_mask) — would have broken px4_ros2 mode registration at M4. Workspace rebuild (px4_msgs + all dependents) launched in background 2026-07-19; VERIFY completion + live topics before relying on it.
- **interface-lib PINNED → release/1.17 @ 4a3370f** (branch `pinned-1.17`, 2026-07-19): HAS native rover setpoint types (RoverSpeedRateSetpointType, update(speed,yaw_rate) @30Hz) + rover_velocity example. **2.1.1 FAILED build** vs 1.17 msgs (uses ConfigOverrides.disable_auto_set_home — added before 2.0.0, needs px4_msgs >1.17) → ALL lib 2.x blocked until firmware upgrade. Policy: everything on the firmware's release/1.17 line. Older pins tried this session: 1.6.0→1.6.1 (superseded). Local example experiments saved on branch `local/manual-mode-experiments`.
- **Firmware EXPOSES full rover setpoint set** (/fmu/in/rover_speed|rate|attitude|position|throttle|steering_setpoint — a 1.17 feature) + all Rover*Setpoint msgs in pinned px4_msgs.
- ALL 4 VESCs verified online 2026-07-19 (addr 10-13, esc_online_flags=15, ~25.3V, fresh timestamps): can_status telemetry works on every node, not just 13 — M1 data source fully confirmed.
- Live topics measured (FC+VESCs powered): esc_status 49.7Hz ✅, vehicle_odometry 98.6Hz but quality=0, local_position xy_valid=false/dead_reckoning=true (the M2 target), input_rc 9.6Hz, battery 1Hz. Versioned names in use: vehicle_local_position_v1, vehicle_status_v1, battery_status_v1.
- Companion HTTPS→GitHub hangs (IPv6): fetch with `git -c url."git@github.com:".insteadOf="https://github.com/" fetch`.
- apt has ros-jazzy-navigation2 1.3.5 + slam-toolbox 2.8.2; depthimage_to_laserscan already installed.
- NOT yet present: Nav2 install, Orbbec ROS2 wrapper, rover_odometry pkg.
- PX4 rover params RO_*/RD_WHEEL_TRACK were ALL ZERO (2026-05-30 dump) — must set via QGC/NuttShell, pymavlink can't (see [[rover-odometry]]).

## Flow: LAYERED environment-first (re-ordered 2026-07-19 by user; each layer proven w/ QGC before next)
L0 transport+msg alignment ▸ L1 custom mode skeleton in QGC ▸ L2 mode I/O + wheels-up test ▸ L3 sensor fusion (odom→EKF2) ▸ L4 Gemini SDK+/scan ▸ L5 Nav2 goal+avoidance ▸ L6 SLAM+routing ▸ L7 safety. Tag v1.2.0 at end.
**STATUS 2026-07-19: L0 CLOSED** — px4_msgs 1.17 built (18min) + live topics decode correctly (esc_status/local_position verified; arming_check_request_v1 silent = expected until a mode registers). PX4 rover params set+saved via NuttShell (RO_YAW_RATE_I=0.1, RO_YAW_RATE_LIM=1.57; rest already correct from reflash — only EKF2_EV_CTRL/GPS_CTRL left for L3).
**L1 BUILT + FC-SIDE VERIFIED 2026-07-20** (session ended at limit 2026-07-19 ~23:30; verified next day):
- Full ws rebuild DONE: 26 pkgs on px4_msgs+lib release/1.17, ZERO failures (incl. autonav_mode, rover_odometry, example_rover_velocity_mode_cpp). autonav_mode clock-type warning fixed + rebuilt clean.
- `autonav_mode` (src/autonav_mode, C++): mode "AutoNav", /cmd_vel→RoverSpeedRateSetpointType, clamps 0.8m/s / 1.0rad/s, 500ms cmd watchdog, zero-on-activate.
- **L1 VERIFIED 2026-07-20 (FC side, full loop)**: node registers clean (messageCompatibilityCheck pass, RegisterExtComponentReply, arming check replies flowing). AutoNav = **External Mode 1** (slot 0: COM_MODE0_HASH=-1639016601 = fnv1a("AutoNav"), verified match; nav_state 23=EXTERNAL1). **DO_SET_MODE base=1,main=4(AUTO),sub=11(EXTERNAL1) accepted → nav_state 23 confirmed live**; restored Manual after. onActivate only fires when ARMED (lib mode.cpp: nav_state match && armed, unless activate_even_while_disarmed) — silence while disarmed is correct.
- **QGC/RC selection facts (2026-07-20)**: firmware streams AVAILABLE_MODES (msg 435 present in pinned mavlink submodule 33af200d common.xml; dialect=common) → QGC shows "AutoNav" by name ONLY if fork base has dynamic-modes support (upstream QGC 4.4+). RC path = COM_FLTMODEx=100 ("External Mode 1") — BUT **RC_MAP_FLTMODE=0 currently, no RC mode channel mapped at all** (user's old external-mode RC assignment lost in 2026-05-31 reflash). User must map mode channel + slot in QGC (Radio/Flight Modes) or GCS commands DO_SET_MODE directly.
- **Incident 2026-07-20**: node aborted once "Timeout, no request received from FMU" (lib 4s watchdog on ArmingCheckRequest, by design; FC fell back to Hold since AutoNav was selected — sane rover failsafe = stopped). NOT reproducible: baseline Manual 60s + AutoNav-disarmed 180s both ~3.3Hz max gap 0.62s. One-off DDS transient. Mitigation for later: run autonav_mode as systemd service Restart=always.
- **QGC "Unknown mode" ROOT-CAUSED 2026-07-20 (session 2)**: user watched QGC during my tests — saw Hold → "Unknown <number>" (that WAS AutoNav, my DO_SET_MODE) → Manual (my restore). L1 loop therefore user-observed end-to-end; only the NAME is missing. Fork analysis (PXLABS_qgroundcontrol @ ea1e297 v3.3.0, sparse blob:none clone w/ upstream remote — re-clone if scratchpad gone): fork HAS src/Vehicle/StandardModes.cc + Vehicle.cc hookups (ctor :284, modesUpdated→flightModesChanged :291, monitor seq :621) BUT PX4FirmwarePlugin.cc resolves names ONLY from static `_modeEnumToString` (:139 → "Unknown %1:%2") — dynamic list never consumed. Upstream master fix mechanism: StandardModes.cc:84 on completion calls `_vehicle->firmwarePlugin()->updateAvailableFlightModes(_modeList)` → rebuilds plugin map → names flow through existing paths (upstream plugin defines updateAvailableFlightModes(FlightModeList&) at :753). **PENDING CHECK (interrupted)**: whether fork's StandardModes.cc has the :84 call, whether fork plugin's updateAvailableFlightModes rebuilds _modeEnumToString, and where initial `_standardModes->request()` fires on connect. Firmware side verified fine: AVAILABLE_MODES streamed @0.3Hz in all profiles. QGC fix = user's PC work (port upstream wiring).
- **RC discrepancy to resolve with user**: user believes external-mode RC stick selection IS configured, but FC params read RC_MAP_FLTMODE=0 + all COM_FLTMODE unassigned → not on the FC (likely lost in 2026-05-31 reflash, or configured only QGC-side and never saved). Re-configure: RC_MAP_FLTMODE=<mode channel> + COM_FLTMODEx=100 (External Mode 1).
- **QGC "Unknown mode" RE-ROOT-CAUSED 2026-07-20 (session 3) — earlier fork-patch hypothesis was WRONG, no QGC source patch needed**:
  - Fork PXLABS_qgroundcontrol @ ea1e297 (branch PXLABS-integration) **HAS the complete upstream wiring**: StandardModes.cc:96 calls `_vehicle->firmwarePlugin()->updateAvailableFlightModes(_modeList)` on completion → PX4FirmwarePlugin.cc:804 (declared .h:81) → `FirmwarePlugin::_updateFlightModeList` (FirmwarePlugin.cc:454) which **clears and rebuilds `_modeEnumToString`** — the very map PX4FirmwarePlugin.cc:139 reads for the "Unknown %1:%2" fallback. Trigger path fine too: Vehicle.cc:615 AVAILABLE_MODES_MONITOR → :621 `availableModesMonitorReceived`, `_lastSeq{-1}` so the first monitor fires `request()`.
  - **FC side fully correct**: streams AVAILABLE_MODES_MONITOR (436) @0.52Hz; answers REQUEST_MESSAGE(435) for all 26 modes. **idx 19/26 = name 'AutoNav', custom_mode=0x0b040000 (main=4 sub=11), properties=0x0 → user-selectable, not advanced.** (435 is on-request only, never streamed — earlier note saying "AVAILABLE_MODES streamed @0.3Hz" was actually the 436 monitor.)
  - **Real cause = the GCS link, see [[project-gcs-link-degraded]]**: uplink commands from the relay reach the drone 0/8; QGC's mode-name request therefore never lands, and StandardModes has no retry → names never populate. Fix the link, not QGC.
- **DDS mode control VERIFIED 2026-07-20** (replaces MAVLink DO_SET_MODE for all testing, per [[feedback-use-dds-not-mavlink]]): publish `VehicleCommand` DO_SET_MODE (param1=1, param2=main, param3=sub) on `/fmu/in/vehicle_command` → `/fmu/out/vehicle_status_v1.nav_state` 4→**23 (AutoNav)**→4 (Hold restore). Script kept at **`~/ros2_ws/tools/dds_setmode.py`**.
- **autonav_mode re-verified 2026-07-20 session 3**: registers clean on relaunch, survives a full mode cycle. Also aborted once more with the 4s FMU watchdog — but that abort happened *during* heavy MAVLink probing, so the "one-off" now has a likely cause (MAVLink load), not just a DDS transient. systemd `Restart=always` still worth adding.
- **L2 ATTEMPTED + BLOCKED 2026-07-20 (session 3) — LAYER ORDER MUST CHANGE: L3 comes before L2.** Bench powered (all 4 VESCs online 25.2-25.4V, RC connected, wheels up). Mode switch to AutoNav works (nav_state 23), but **arming is refused: VehicleCommandAck result=1 TEMPORARILY_REJECTED, `pre_flight_checks_pass=False`**.
  - Cause (measured over DDS, no MAVLink): `vehicle_local_position_v1` → **`v_xy_valid=False`**, xy_valid=False, z_valid=True, dead_reckoning=True. EKF aiding active = baro hgt + mag heading + **fake pos** only (`cs_valid_fake_pos`, `cs_inertial_dead_reckoning`); no GPS, no vision/odom.
  - `failsafe_flags` bit analysis for nav_state 23 (EXTERNAL1): AutoNav requires **mode_req_local_position + mode_req_local_alt + mode_req_angular_velocity**; `local_position_invalid` / `local_velocity_invalid` are True → preflight fails.
  - **Not fixable by picking a different setpoint type**: EVERY rover setpoint in lib release/1.17 (speed_rate, throttle_rate, throttle_steering, speed_steering, throttle_attitude) sets `config.velocity_enabled = true` in getConfiguration() → all demand a velocity estimate. There is no open-loop bench shortcut through this lib.
  - **Therefore the only path to a wheels-up motion test is to make local velocity valid first = L3** (rover_odometry → /odom → EKF2 via px4_ros2 LocalPositionMeasurementInterface, + EKF2_EV_CTRL). Requirement is legitimate (speed-controlled mode needs a speed estimate), not a bug to bypass.
- **SECOND, INDEPENDENT ARM BLOCKER (user-reported from QGC, 2026-07-20): "accel 0 inconsistency 1.00596"** = PX4 preflight `Accels inconsistent` — accel instance 0 differs from the other IMUs by 1.006 m/s², over `COM_ARM_IMU_ACC` (default 0.7). This blocks arming in **every** mode, AutoNav or not, and is separate from the velocity-estimate issue.
  - Primary/fused accel is HEALTHY (measured over `sensor_combined`, 768 samples at rest): |a|=9.791 m/s² vs 9.807 expected (−0.016 error), per-axis stdev 0.018, gyro bias ~3e-4 rad/s. Mean x=+0.403 y=+1.906 z=−9.595 → vehicle sitting ~11° tilted on its stands, which is fine and not the cause. So the fault is a *different* IMU instance's calibration, likely stale since the 2026-05-31 reflash.
  - Fix = redo accelerometer calibration (6-orientation) — **needs QGC command path, which is currently dead per [[project-gcs-link-degraded]] → will likely require a direct USB/serial link to the FC**, or fix the uplink first. Not doable over DDS (`sensors_status_imu` isn't even in the FC's dds_topics.yaml; only `sensor_combined` is exposed).
- **ACCEL BLOCKER CLEARED 2026-07-20 (user ran quick cal + levelled)**: `pre_flight_checks_pass=True` now, tilt 11.2°→2.0°, |a|=9.854. Method for a vehicle too big to rotate: **`commander calibrate accel quick`**, or over DDS `VehicleCommand` 241 (PREFLIGHT_CALIBRATION) with **param5=4** (verified in real fw pxlabs-fw Commander.cpp:1349 + accelerometer_calibration.cpp:423; note the in-source comment saying "param5 = 3" is WRONG, the code sends/checks 4). Quick cal = offsets only, one position, uses EKF attitude as gravity reference (falls back to normalising to 1g if >10° disagreement), rejects offsets >1g. Full 6-orientation alternative for big vehicles = calibrate the FC off-vehicle, remount, then level-horizon cal (param5=2). Third option = deprioritise the bad instance via `CAL_ACCn_PRIO=0` (ACC3 already is). Saved historical param sets: `~/ubuntu-server/Rover/*.params` (newest Rover_NXP_10_08_25.params, SYS_AUTOSTART 51000) — sensors there: ACC0 BMI088 SPI3, ACC1 ICM45686 SPI2, ACC2 ICM42688P SPI1, ACC3 ICM42686P SPI1 (disabled). **Accel instance numbering is NOT stable** — CAL_ACC0_ID differs across all three dumps, so "accel N" never reliably names the same chip.
- **L3 BUILT 2026-07-20 — `rover_ekf_bridge` (new C++ pkg, src/rover_ekf_bridge)**: subscribes `/odom`, feeds EKF2 via px4_ros2 `LocalPositionMeasurementInterface` → publishes to `/fmu/in/vehicle_visual_odometry` at ~40Hz (throttle param `publish_rate_hz`=50). **Velocity only** (wheel position drifts unbounded), frame **BodyFRD** (/odom twist is FLU → y negated), variance params `velocity_variance`/`velocity_z_variance`=0.05.
  - **Critical impl detail**: EKF2 drops the ENTIRE EV sample unless the velocity vector is all-finite (`ev_vel_control.cpp:56 ev._sample.vel.isAllFinite()`), and the lib fills unset fields with NAN → **must send velocity_z explicitly** (we send 0.0, valid for a wheeled rover on the ground).
  - Timestamp epoch is FINE here: the FC time-offset-corrects both `timestamp` and `timestamp_sample` on inbound deserialize (Tools/msg/templates/ucdr/msg.h.em:167-169), so ROS-clock stamps are correct — unlike the *outbound* nested-field trap that broke rover_odometry.
  - **L3 VERIFIED WORKING 2026-07-20**: user set `EKF2_EV_CTRL=4` → `cs_ev_vel=True`, **xy_valid=True, v_xy_valid=True, dead_reckoning=False**, local_position_invalid/local_velocity_invalid BOTH False, pre_flight_checks_pass=True. `cs_inertial_dead_reckoning` and `cs_valid_fake_pos` dropped out, replaced by real EV aiding (aiding now = tilt/yaw align, mag hdg+dec, baro hgt, **ev_vel**, at_rest). AutoNav re-entered and HOLDS nav_state 23 with requirements satisfied. Both L2 arm blockers are therefore cleared; only the physical wheels-up motion test remains.
  - (was) **NEEDED (user, param write — not settable over DDS): `EKF2_EV_CTRL` = 4** (bitmask bit 2 = "3D velocity"; default 0 = EV disabled — confirmed in pxlabs-fw params_external_vision.yaml). Until then `estimator_status_flags` shows NO ev flags and aiding stays baro+mag+fake-pos, `v_xy_valid=False`. After setting it, verify `cs_ev_vel` goes true and local_position/velocity_invalid clear, then retry arming in AutoNav.
- **L2 RUN 2026-07-20 — PARTIAL PASS, drive response NOT conclusively verified (wheels-up confound)**. Sequence ran end-to-end: AutoNav entered, **ARMED successfully** (first time ever), /cmd_vel accepted, watchdog zeroed wheels within 2s of last command, auto-disarm + Hold restore clean. Final state safe (nav 4, disarmed, rpm 0).
  - **Yaw 0.3 rad/s: all 4 wheels spin, correct differential pattern** after applying the addr-10 sign inversion — right pair (10,12) +1512/+1583 ERPM, left pair (11,13) -1513/-1531. **Proves all 4 VESCs/motors drive and the L/R allocation is right** (actuator_function 101=left on addr 11,13; 102=right on addr 10,12 — matches rover_odometry config).
  - **Forward 0.2 m/s: BROKEN — only addr 13 turns (+430 ERPM ≈ 0.163 m/s); addr 10 and 12 dead at 0, addr 11 ~3-6 ERPM. And it does NOT scale: 0.4 m/s gives +431, identical.** Unexplained; needs follow-up.
  - **Magnitudes are meaningless on stands**: yaw produced ~1500 ERPM (≈0.58 m/s wheel speed) where the geometry wants ~170 ERPM (0.3 rad/s × 0.43 m track / 2) — ~9x over. Expected: PX4 rover speed AND yaw-rate control are **closed-loop on body motion that cannot happen on stands**, so the controllers wind up. A wheels-up bench can verify plumbing/direction but NOT control-loop correctness or scaling.
  - **HAZARD to remember: with rover_ekf_bridge running, a wheels-up test feeds FICTION into EKF2** — wheel odometry reports motion while the body is stationary, EKF2 believes it, and the speed controller closes on that false measurement. For future bench tests either stop rover_ekf_bridge or treat all results as plumbing-only.
  - **MANUAL-MODE RC TEST 2026-07-20 CLEARS THE HARDWARE**: user drove forward+reverse on stands in Manual (open-loop, bypasses speed/yaw-rate controllers). **ALL FOUR wheels drive BOTH directions at full range: addr 10 -1519/+1512, 11 -1516/+1520, 12 -1576/+1574, 13 -1534/+1533 ERPM (≈±0.58-0.60 m/s).** Motors, ESCs, wiring and L/R allocation are all GOOD, and the addr-10 sign inversion in the odometry config is confirmed correct. ⇒ **The AutoNav forward failure is NOT hardware — it is in the closed-loop speed-control path** (whose feedback is invalid on stands, and was additionally being fed wheel-derived fiction by rover_ekf_bridge during that test). Treat the earlier forward result as void; redo on the floor.
  - **FULL CHAIN RE-VERIFIED end-to-end from the companion 2026-07-20** (`tools/autonav_chain_check.py --arm`, all over DDS): registration reply `success=True, mode_id=23` (mode_id IS the External Mode slot = nav_state) ▸ arming-check handshake live, 20 requests / 13 replies in a 6 s window with `can_arm_and_run=True` ▸ DO_SET_MODE(main=4,sub=11) **ACCEPTED** → nav_state 23 ▸ ARM **ACCEPTED** → arming_state 2 ▸ **onActivate confirmed by output: 152 `/fmu/in/rover_speed_setpoint` + 151 `/fmu/in/rover_rate_setpoint` msgs in 5 s, both holding exactly 0.000** (correct — zero-on-activate, no /cmd_vel sent) ▸ clean disarm + Hold restore.
  - **QoS GOTCHA when observing the chain**: the px4_ros2 lib publishes `/fmu/in/*` with **VOLATILE** durability while the uXRCE agent publishes `/fmu/out/*` **TRANSIENT_LOCAL**. A TRANSIENT_LOCAL subscriber gets *silently nothing* from the lib's topics — first run of the checker showed 0 setpoints and 0 arming replies purely from this, not a real fault. Subscribe to /fmu/in/ with VOLATILE.
  - **Shell gotcha**: `pkill -f autonav_mode` matches the invoking shell's own command line and kills the session (exit 144). Kill by exact path (`pgrep -f install/autonav_mode/lib`) or by PID.
  - **RC mapping discovered from the log** (useful for the pending RC_MAP_FLTMODE work): **ch2 = forward/reverse throttle** (range 1023-1981), **ch4 = steering** (1116-1671), ch1 static 1500, **ch3 static 1001 (unused, NOT throttle)**. No mode channel moved — consistent with RC_MAP_FLTMODE=0.
  - Tool: `~/ros2_ws/tools/manual_drive_log.py <seconds>` — read-only per-wheel + stick logger with sign correction, for exactly this kind of RC-driven test.
  - **ROOT CAUSE OF THE FORWARD FAILURE FOUND 2026-07-20: `RO_SPEED_LIM = 0.0100` (m/s).** Read from NuttShell `param show RO_*`. In the firmware, `DifferentialSpeedControl.cpp:119` does
    `speed_setpoint = math::constrain(_speed_setpoint, -RO_SPEED_LIM, +RO_SPEED_LIM)` — so **every** speed setpoint is clamped to ±0.01 m/s. Commanding 0.2 and 0.4 m/s both clamp to 0.01 → **exactly why the two runs produced identical 430/431 ERPM and why only the least-loaded wheel (addr 13) crept** while the rest stayed below break-away torque. Param doc: "Speed limit — used to cap speed setpoints and map controller inputs to speed setpoints in Position mode", default -1 (disabled). 0.01 is a mis-set value, and it is saved (`+`).
    **FIX (not yet applied):** `param set RO_SPEED_LIM 1.0` + `param save` (1.0 keeps a hard FC-side cap just above autonav_mode's own 0.8 m/s clamp = defence in depth; 3.0 would match RO_MAX_THR_SPEED). Then re-run the forward test ON THE FLOOR.
  - **Full RO_* dump 2026-07-20** (x=used, +=saved): RO_ACCEL_LIM -1 · RO_DECEL_LIM -1 · RO_JERK_LIM -1 (all disabled) · **RO_MAX_THR_SPEED 3.0+** · **RO_SPEED_I 0.1+** · **RO_SPEED_LIM 0.01+ ← BUG** · **RO_SPEED_P 0.5+** · RO_SPEED_RED -1 · RO_SPEED_TH 0.1 · RO_YAW_ACCEL_LIM -1 · RO_YAW_DECEL_LIM -1 · RO_YAW_EXPO 0 · **RO_YAW_P 2.0+** · RO_YAW_RATE_CORR 1.0 · **RO_YAW_RATE_I 0.1+** · **RO_YAW_RATE_LIM 1.57+** · **RO_YAW_RATE_P 2.0+** · RO_YAW_RATE_TH 3.0 · RO_YAW_STICK_DZ 0.1 · RO_YAW_SUPEXPO 0. (952/2048 params used.) Yaw params are sane — the yaw path was never clamped, which is why yaw drove all four wheels while forward did not.
  - **MAVLINK LINK WEDGED 2026-07-20 (open)**: after several `Tools/mavlink_shell.py` sessions the FC's heartbeat DISAPPEARED from `tcp:127.0.0.1:5760` — only a GCS-type heartbeat (sys 255 comp 190, autopilot=8 type=6) remains, and `param show`/PARAM_REQUEST_READ stopped responding. **DDS is completely unaffected** (ESC/mode/arming all live), so the FC is healthy and nothing autonav-critical is blocked, but **QGC cannot connect until this is fixed**. Suspected fix: `sudo systemctl restart mavlink.router` (attempt was declined, needs user sudo). Reinforces [[feedback-use-dds-not-mavlink]] — the first `param show RO_*` succeeded, subsequent shell sessions killed the link.
  - **Reading params is ONLY possible over MAVLink** (NuttShell or PARAM protocol) — parameters are not exposed over DDS at all. Budget for the link disturbance when doing it, and stop `autonav_mode` first.
  - **NEXT for L2 closure**: low-speed forward test on the FLOOR in a clear area (the only valid check of drive response), and inspect `RO_MAX_THR_SPEED` / `RO_SPEED_P` / `RO_SPEED_I` / `RO_YAW_RATE_P|I` via QGC (params unreadable over DDS) — the forward-vs-yaw asymmetry smells like speed-loop gains/limits.
- **rover_odometry BUG FIXED + VERIFIED 2026-07-20**: fix applied (staleness vs `max(nested esc timestamps)` + `esc_online_flags` bit gate), rebuilt, node now publishes **`/odom` at 99.9Hz** with odom→base_link TF, no more "incomplete wheel data". Original bug detail below.
- **rover_odometry BUG (original diagnosis) 2026-07-20**: node runs but logs `incomplete wheel data (L:0 R:0)` forever. `wheel_odometry_node.py:81` compares `msg.timestamp` (absolute — uXRCE-DDS applies its time offset to the TOP-LEVEL field only) against nested `esc[i].timestamp` (raw PX4 boot-relative hrt, e.g. 1.754e9 µs vs 1.784e15 µs) → every ESC looks impossibly stale → all skipped. ESC addresses 10-13 and signs in config are correct; `esc_online_flags=15`, `esc_armed_flags=15`, voltages/rpm decode fine. **Fix**: measure per-ESC staleness against `max(nested esc timestamps)` (same epoch), and/or gate on the `esc_online_flags` bit — never against msg.timestamp. This is now on the critical path for L3→L2.
- Tools added (uncommitted): `~/ros2_ws/tools/dds_setmode.py`, `tools/l2_watch.py` (live ESC/mode/arming view), `tools/l2_test.py` (staged L2 sequence, refuses to arm without `--wheels-are-up`, auto-disarms + restores Hold).
- **autonav_mode 4s FMU watchdog aborts RECUR without MAVLink load** (died again 21:26 after ~20 min idle, no probing running) → the MAVLink-load explanation is NOT sufficient; treat as a real DDS/agent instability. Bench workaround used: bash restart wrapper; proper fix = systemd unit with Restart=always.
- **NEXT**: 1) L2 wheels-up bench — BLOCKED on hardware: only 1/4 VESCs online (`esc_online_flags=8`) and RC transmitter off (`rc_lost=true`), needs user to power the rover bus; then arm → onActivate fires → publish /cmd_vel small speed/yaw, verify wheel response. 2) resolve/set RC mode mapping (RC_MAP_FLTMODE=0 still). 3) uplink fix per [[project-gcs-link-degraded]]. Relaunch node: `source install/setup.bash && ros2 run autonav_mode autonav_mode`. FC left in **Hold (nav_state 4)**, disarmed. ALL COMMITTED 2026-07-20 on ros2_ws `main` (a72f1b9 px4_msgs pin, 915304e autonav_mode, 16353d7 rover_odometry+rover_ekf_bridge, 5fc9f9c tools, 2c46e5e docs, 2fa1097 chain-check) — **pushed to origin/main 2026-07-20**. `src/ldlidar_stl_ros2/` deliberately left untracked (nested git repo).
- UNCOMMITTED in ros2_ws: src/autonav_mode/, src/rover_odometry/, docs edits after commit b08766e (layered L0-L7 flow + status log in requirements doc). Commit when L1 verified.
- rover_odometry pkg built, tests at L3. Nav2 apt install still pending user sudo (`sudo apt install -y ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox`).

## SESSION 2026-07-21 (evening) — ALL COMMITTED + PUSHED to origin/main (3bcba10..b5a9408)
Commits: `2075ddd` track width 0.31 fix · `0bd5bf6` depth_to_scan + measured camera TF ·
`642f50d` systemd units · `b5a9408` docs + OrbbecSDK gitignore (docs/third_party.md).
Working tree clean. Remote is SSH (`git@github.com:ArvinVeiyon/ros2_ws.git`) — no PAT embedded,
unlike codex-work.

## SESSION 2026-07-21 (evening) — stack restored after companion reboot, RO_SPEED_LIM FIXED
Pi rebooted (FC did NOT — it stayed up throughout). All detached `setsid` nodes were wiped.
- **`RO_SPEED_LIM` FIX APPLIED by user: 0.01 → 0.70**, `param save` confirmed by MAVLink readback
  (`0.699999988`). 0.70 is *below* autonav_mode's own 0.8 m/s clamp, so the **FC is now the binding
  cap** — safer ordering than the 1.0 originally proposed, and above the ~0.58-0.60 m/s the drivetrain
  actually reaches. The L2 forward root cause is therefore CLOSED pending the floor test.
- **MAVLink link healed by the reboot** — FC heartbeat back on tcp:127.0.0.1:5760 (sys1/comp1,
  autopilot=12, type=10). Reading params via **pymavlink PARAM_REQUEST_READ did NOT re-wedge it**
  (unlike `mavlink_shell.py`, which did). Prefer PARAM_REQUEST_READ for future param reads.
- **Param-readback gotcha**: `EKF2_EV_CTRL` reads as `5.605e-45` — that is INT32 **4** carried in
  PARAM_VALUE's float field (bit pattern), NOT a corrupt value. Don't "fix" it.
- **`pre_flight_checks_pass=false` episode — REAL CAUSE WAS THE RC TRANSMITTER BEING OFF.**
  Observed: preflight false while everything else looked healthy — xy_valid / v_xy_valid true,
  dead_reckoning false, cs_ev_vel true, local_position_invalid + local_velocity_invalid both false,
  all SYS_STATUS health bits green, **zero STATUSTEXT**, accel fused fine (|a|=9.852, tilt 1.1°).
  I hypothesised a stale external-mode registration (FC kept AutoNav in slot 0 while its
  `autonav_mode` component died with the Pi) because preflight flipped true right after restarting
  the node — **but the user then reported the RC transmitter had only just been connected**, which is
  the simpler explanation and the timing is ambiguous. User confirmed QGC shows all-green in Manual.
  **Check the RC transmitter FIRST for unexplained preflight failures.** The stale-registration
  theory is UNCONFIRMED — do not treat it as fact; note that SYS_STATUS's `rc` health bit read
  `True` even while the transmitter was off, so that bit is not a reliable RC indicator.
- Restored + verified live: `/scan` ~25Hz · `/odom` ~100Hz (all 4 VESCs, esc_online_flags=15) ·
  rover_ekf_bridge → `/fmu/in/vehicle_visual_odometry` ~39Hz (its 1s "no /odom received yet" warning
  is a harmless startup transient) · autonav_mode registered clean. FC left **disarmed, nav_state 0**.
- Reminder: `/odom` silent with `esc_online_flags=8` + `incomplete wheel data (L:1 R:0)` = **rover
  motor bus unpowered**, not a software bug (8 = only addr 13, a LEFT wheel — hence L:1 R:0).
- **NEXT: the L2 low-speed forward test ON THE FLOOR** — all blockers now cleared. Stop
  rover_ekf_bridge or treat results as plumbing-only if wheels are up (see hazard note above).
- ✅ **RESOLVED same session: systemd units installed 2026-07-21**, replacing the manual `setsid`
  bring-up that a reboot had wiped twice. rover-camera / rover-scan / rover-odometry /
  rover-autonav-mode enabled+active; **rover-ekf-bridge installed but DISABLED on purpose**.
  Full detail in [[services]]. `Restart=always` also covers the autonav_mode 4 s watchdog aborts.

## RC MAPPING RESOLVED 2026-07-21 — the long-open "RC discrepancy" is CLOSED, user was right
Read via pymavlink PARAM_REQUEST_READ on tcp:5760 (values are INT32 in a float field — decode the
bit pattern, don't read the float): **RC_MAP_KILL_SW=8 · RC_MAP_ARM_SW=5 · RC_MAP_FLTMODE=6 ·
NAV_RCL_ACT=6 (Disarm on RC loss) · COM_RC_IN_MODE=3.** Memory previously recorded
RC_MAP_FLTMODE=0/"nothing mapped" — that is now STALE; kill, arm and mode channels are all mapped.
**PHYSICALLY TESTED + WORKING 2026-07-21 (user-verified on the bench): kill switch (ch8), arm and
disarm all confirmed functional.** Safety gate for floor driving is therefore CLOSED.
Still untested: kill *while in AutoNav* specifically (bench test was in Manual — AutoNav could not
arm at the time because rover_ekf_bridge was deliberately stopped). Worth confirming opportunistically
on the floor, since AutoNav is the mode that will actually be driving autonomously.
Also: SYS_STATUS's `rc` health bit read True while the transmitter was OFF → not a reliable RC check.
Param reads sometimes return `<no reply>` when QGC is attached to the same link — retry, and send
several requests spaced ~0.3 s; it recovers without wedging.

## WHEELS-UP LIMIT CYCLE 2026-07-21 — observed, root-caused, and how to avoid it
**Symptom (user-reported + measured):** armed on stands in **Position mode (nav_state 2)** is quiet
at first. Arming alone does nothing. But the instant a **forward/reverse stick input** is given, all
four wheels start swinging **full range ±1500 ERPM with a ~1.2 s period** and **never stop — even
with the stick back at centre — until disarm**. Measured: addr10 -1450/+1510, addr11 -1516/+1507,
addr12 -1565/+1536, addr13 -1527/+1518; EKF2 meanwhile reported **x=-4.25 m, y=+3.06 m of phantom
travel** on a vehicle that never moved.
**Root cause = positive feedback through `rover_ekf_bridge` while the wheels are off the ground.**
Zero is a *stable equilibrium* (stopped wheels → 0 odom → 0 correction), which is why arming is
harmless. A stick input *perturbs* it: wheels spin → rover_odometry reports it as real velocity →
bridge integrates it into EKF2 → the rover believes it has travelled. Centring the stick does NOT
help because **Position mode is a position HOLD** — it now thinks it is ~0.5 m off station and drives
back to "return", which spins the wheels, which manufactures displacement the other way → overshoot
→ undamped **limit cycle**. The only corrective action available is the same action that creates the
error; on stands there is no body motion, so no friction/load damping. `RO_SPEED_I=0.1` winds up and
guarantees the overshoot. Disarm is the only thing that breaks it.
**This does NOT indicate a fault** — it re-confirms all 4 motors drive both directions at full range.
**It will NOT happen on the floor**, where driving back actually arrives and real dynamics damp it.
**Avoidance on stands — either:** use **Manual (nav_state 0) only** (open-loop, no estimator in the
path), **or stop `rover_ekf_bridge`** before arming. With the bridge stopped, `cs_ev_vel=false`,
xy_valid/v_xy_valid=false, dead_reckoning=true → Position/AutoNav **cannot arm at all**, only Manual.
That is the correct safe stands configuration (verified 2026-07-21).
**Never stop the bridge while ARMED in Position/AutoNav** — dropping v_xy_valid under a mode that
requires it triggers a PX4 failsafe. Disarm first, then stop it.
**FC restart clears the corrupted estimate** (x went 4.25 m → ~0.5) but the FC may come back **still
armed in Position mode**, restarting the loop immediately — check arming_state after any FC reboot.
`autonav_mode` dies on FC restart (4 s FMU watchdog, expected) and re-registers cleanly on relaunch.

## SHELL GOTCHA — killed this session's shell THREE times (exit 144), extends the known note
`pkill -f`/`pgrep -f` match **the invoking shell's own command line**, including **text inside
`echo` strings**. `pkill -f "[r]over_ekf_bridge"` still self-killed because a later
`echo "rover_ekf_bridge STOPPED"` in the SAME command line contained the literal name. The bracket
trick alone is NOT enough — **the target name must not appear anywhere in the command line, echo
text included**. Reliable form used successfully:
`N='rover_ekf'; N="[${N:0:1}]${N:1}_bridge"; pkill -f "$N"` and never echo the literal name.

## Safety invariants (never weaken)
RC override PX4-native; rov_collision_stop node stays active independent of Nav2; cmd_vel>500ms / scan>1s watchdog stops; no reverse into unseen space (forward-only sensing).

Related: [[rover-odometry]] (all odom math/params), [[project-vision-multicam-upgrade]] (camera ids/roles), [[feedback-camera-qgc-only]].


## 2026-07-26 — VESC wake-on-nudge (confirmed by user)

At rest **only ESC address 13 stays awake** — `esc_status.esc_online_flags == 8` (bit 3 only), the
other three report `timestamp 0 / address 0`. `wheel_odometry_node` is configured `L=[11,13]
R=[10,12]`, so it sees `L:1 R:0`, cannot form a differential pair, and **`/odom` stays silent**.
Every one of the 3846 warnings in the journal is `L:1 R:0` — never any other combination.

**A small physical nudge wakes the other three**: flags go `8 → 15` and `/odom` comes up at ~100 Hz.
User: *"only one motor is always on, then I move it a little bit and the rest are powered on."*

**This is normal, not a fault.** Do not go hunting CAN wiring or loose connectors for it (I did,
2026-07-26 — cost ~15 min). `/fmu/out/esc_status` flowing at ~50 Hz with `esc_count 4` proves the
bus is fine; the flags are what matter.

**Check `esc_online_flags == 15` before trusting `/odom`** — and before starting
`rover-ekf-bridge`, since no `/odom` means no EV aiding and AutoNav cannot arm.
Open question, worth watching during the first long run: do the wheels **stay** awake, or can they
doze off mid-session? `/odom` dropping out under the EKF bridge while armed would be nasty — though
the collision-stop's stale-scan fail-safe covers the `/scan` side of that.

## ESC wake-up behaviour at rest (2026-07-26) — not a fault
At rest only ESC addr 13 stays awake (`esc_online_flags 8`), so `/odom` is **silent** and reports
`L:1 R:0`. A small **nudge wakes the other three** (flags → 15, `/odom` resumes ~100 Hz).
This is normal ESC sleep, **not a CAN failure**. **Always check `esc_online_flags == 15` before
trusting `/odom`** — otherwise you will misread sleeping ESCs as an odometry bug.

## 🔑 MANUAL MODE BYPASSES THE YAW RATE LOOP — verified in the REAL firmware 2026-08-02
**Source: `~/PX4-Autopilot` branch `pxlabs-fw` (the actual fw source, NOT the upstream clone),
`src/modules/rover_differential/DifferentialDriveModes/DifferentialManualMode/DifferentialManualMode.cpp`**
```cpp
manual(): rover_steering_setpoint.normalized_steering_setpoint =
              RD_YAW_STK_GAIN * superexpo(roll stick)   -> publishes STEERING directly
acro():   rover_rate_setpoint.yaw_rate_setpoint = _max_yaw_rate * superexpo(...)
                                                        -> publishes a RATE setpoint
```
`RoverDifferential.cpp:114` dispatches `NAVIGATION_STATE_MANUAL -> _manual_mode.manual()`.
⇒ **The ~21× yaw runaway lives in the RATE controller (`RO_YAW_RATE_P`), which MANUAL NEVER INVOKES.**
⇒ **Driving in MANUAL is not exposed to it. ACRO / STAB / POSCTL / OFFBOARD / AUTO all are.**
⚠️ **BUT the collision reflex does NOT apply in Manual** — it lives inside `autonav_mode`'s executor,
a CUSTOM PX4 mode, so PX4 never routes through it. **In Manual the operator is the ONLY safety layer.**
⇒ **#20 still gates every AUTONOMOUS mode. It does NOT gate manual driving.**
