---
name: project-rover-autonav
description: "Rover autonomous navigation (Nav2 + px4_ros2 lib + Orbbec depth). L0-L4 done; L2 armed floor test PASSED 2026-07-22/23 + reflex collision-stop built/validated/pushed (b38e413). NEXT = yaw-gain tuning then L5 (slam_toolbox+Nav2)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5ff45709-5e20-4964-9bd8-fce6f3bc03f0
  modified: 2026-09-20T12:11:57.413Z
---

# Rover Autonomous Navigation — ACTIVE (started 2026-07-19)

## ✅ 2026-09-20 (desk, disarmed) — **EVERYTHING IS PUSHED OFF THE CARD. SIGN FIX PROVEN IN THE RUNNING BINARY.**

Session `bb07cdc3`, 13:40→17:00 IST. **Nothing was lost** — the push below landed 17:09. Rover
disarmed and the EKF bridge stopped throughout; nothing moved.

**🔑 THE SAFETY NET CLOSED.** `ros2_ws` → `79c82bf` on `main`, `codex-work` → `72514ce` on `master`,
both pushed, both trees clean. 🔴 **Until that push, `nav2_forward_flat.yaml` — the config T3 passed
on and the one `rover-nav2.service` loads by default — and the `mode.hpp` sign fix existed NOWHERE
BUT THIS SD CARD.** Both remotes are SSH, so this did not touch the two unrevoked PATs.

**✅✅ THE 09-19 SIGN FIX IS IN THE BINARY THAT IS RUNNING. Verified four ways — ⛔ don't re-derive:**
1. header edited 09-19 13:06:23, object recompiled 13:07:42, binary linked 13:07:51 — rebuild *after* edit;
2. the CMake depfile lists `autonav_mode/mode.hpp` as a dependency of `main.cpp.o`, so it cannot have been skipped;
3. ⚠️ **the install path is a SYMLINK into the build tree, not a copy** — `install/autonav_mode/lib/autonav_mode/autonav_mode` → `build/…`. Its own mtime reads **2026-08-01** and looks stale. **That is the symlink's date, not the binary's.** 🔑 `/proc/<pid>/exe` is the ruler that settles it;
4. **decisive:** disassembly shows an `fneg` inside the `/cmd_vel` callback in `AutoNavMode::AutoNavMode`.

**✅ Clean rebuild is BYTE-IDENTICAL.** `colcon build --packages-select autonav_mode --cmake-clean-first`,
46 s, genuinely recompiled (new object+binary timestamps 16:54, one `Building CXX` line) → same
sha256 `5a95d3cb…59915` before and after. So the build is reproducible **and** the binary that had
been running since 09-19 was already built from current source.

**✅ Service re-verified end to end after the restart** (16:55:35) — because `is-active` proves
nothing here: registration request+reply at t=8.8 s, `success=True`, **`mode_id=23`**; arming-check
handshake running continuously (28 requests / 20 replies), **`can_arm_and_run=True`**; mode selectable.

**🅿️ Parked deliberately, NOT documented anywhere:** the **second Pi 5 running Nav2 in parallel**
over DDS. Operator: *"not now but later."* The design exists only in the lost transcript. The four
constraints identified: same `ROS_DOMAIN_ID` **and** same RMW; `px4_msgs` built from the **same
commit** (a mismatch shows up as a topic that silently never connects, not as an error); a **wired**
link, not the radio; clocks agreed to a few ms, because TF and costmap stamps are compared across
machines.

**⏭ THE QUESTION THE SESSION DIED ON, and its answer:** *"we introduced two UAVCAN actuator outputs,
one is for brake and another one is for?"* → **both are the brake.** Slot 5 (`UAVCAN_EC_FUNC5` =
**407** = `RC_AUX1`) is the operator's **RC passthrough hand-brake, with no software path at all**;
slot 6 (`FUNC6` = **301** = `Peripheral_via_Actuator_Set1`) is the **software-commandable** brake the
collision reflex needs, drivable from the companion over DDS. ⛔ **Do NOT move slot 5.** Slot 6 is
**still inert** pending the VESC firmware change. Full detail in the 2026-09-12 slot-6 section below.

## ✅✅✅ 2026-09-15/16 (corridor, floor) — **G3 CLOSED. T2 PASSED n=3, TAPE-ADJUDICATED, ACROSS A 5× SPEED RANGE**

First autonomous drives since 09-12. Armed AutoNav, `nav_state=23`, `tools/t2_straight_goal_test.py`.

| speed | goal | **TAPED** | error | lateral | yaw | reflex |
|---|---|---|---|---|---|---|
| 0.15 m/s | 2.0 m | **2.130 m** | +0.130 m | +0.033 m | +2.08° | silent |
| 0.25 m/s | 2.0 m | **2.025 m** | +0.025 m | +0.036 m | +2.02° | silent |
| 0.75 m/s | 2.0 m | **2.000 m** | 0.000 m | +0.023 m | +1.56° | silent |

✅ **Both T2 criteria, three times.** Tolerance ±0.20 m. 🔑 **ACCURACY IMPROVES WITH SPEED** — and so
does tracking. Runs `t2_20260915_233204` (aborted) / `_234300` / `_235442` / `t2_20260916_000848`.

### 🔑🔑 THE ODOM SCALE IS SPEED-DEPENDENT — THREE TAPE POINTS, MONOTONIC, CROSSOVER AT ~0.25 m/s
| speed | odom/real | |
|---|---|---|
| 0.15 m/s | **0.946** | under-reads 5.4% — ESC zero-dropout loses counts |
| 0.25 m/s | **1.000** | exact — this is where `erpm_to_ms` 0.003900 is effectively calibrated |
| 0.75 m/s | **1.030** | over-reads 3.0% — wheel slip, wheels turn further than the ground moves |

**Two mechanisms pulling opposite ways, each already documented, crossing near 0.25 m/s.**
⛔ **NOT grounds to retune `erpm_to_ms` — the constant is fine, the error is physical.** ⇒ **every
odom distance needs a SPEED caveat.** 🔴 **This RETIRES the T2 tool's `ODOM_WORST_CASE = 1.35`**
(a 24% under-read from 08-13): measured 0.97–1.06, wrong at every speed tested, though wrong in the
SAFE direction (it oversizes the corridor). ⚠️ n=1 per speed. → [[rover-odometry]]

### 🔴 TRAPS THAT COST TIME TONIGHT — ALL THREE WILL RECUR
🔴🔴 **`arming_check_request` IS A ONE-SHOT AT REGISTRATION, NOT A HEARTBEAT.** I measured 0 messages
over 30 s against a live 2.0 Hz `vehicle_status_v1` control and called the mode UNREGISTERED. **Wrong
— it was registered the whole time.** ⇒ 🔑 **PROOF OF REGISTRATION IS THE LOG LINE** `Registering
'AutoNav'` + `Got RegisterExtComponentReply` + `Arming check request (id=N, only printed once)`,
**NEVER a message rate on that topic.** (Registration id=47, then 251 after a restart.)
🔴🔴 **IT IS `/fmu/out/vehicle_local_position_v1`** — the unversioned name returns NOTHING and I read
that as "the EKF bridge is not feeding". Same trap as `vehicle_status_v1`. **`eph` lives on the `_v1`
topic.** The bridge was fine: `/odom` 87 Hz in → `/fmu/in/vehicle_visual_odometry` 31 Hz out.
🔴 **THE MEASURED-SPEED GUARD FALSE-TRIPS AT CRAWL.** Run 1 at 0.08 m/s aborted at 0.575 m on
`max_measured_speed` 0.20 while two independent rulers put the rover at **0.105 m/s** (travel/dt max
0.127). The instantaneous ESC estimate spiked to 0.234 m/s. ⇒ **the guard gates on a signal that is
garbage in the crawl band.** Fix = drive out of the band, not raise the guard.

### ⬜ OPEN — carried out of this session
- 🔴 **`RO_DECEL_LIM`=5 stop distance STILL UNMEASURED**, and wheel rpm **cannot** measure it
  (autonav_reference §13b). Needs `/scan`-against-a-wall or tape.
- 🔴 **The ≥300 mm standoff is unmeasured above ~0.11 m/s** and the 0.75 m/s run **exceeded the
  §13 speed permission** without re-running `collision_standoff_test.py`. **T2 does not test the
  reflex** — it drives at nothing; the reflex was silent because there was nothing to see.
- 🟡 Speed tracking is **exact at 0.25 m/s but ~8% short at 0.75** (0.688–0.706 vs 0.750 commanded),
  after an initial overshoot to **0.902 m/s** in the first 0.5 s.
- 🟡 `COM_DISARM_PRFLT`=10 s **never auto-disarmed** an idle armed rover across repeated observation.
- 📏 `eph` drifted **0.758 → 2.618 m** over the session against the 5.0 m `COM_POS_FS_EPH` gate
  (~0.0013 m/s) ⇒ **~45-60 min of armed budget per bridge restart.** Restarting the bridge resets it.

## ⚠️ SUPERSEDED BY THE RPM-MODE MIGRATION (2026-09-13) — the section below is HISTORY
⛔ **"The ESCs take throttle as TORQUE", "the overspeed is an INTEGRAL", "don't calibrate
`RO_MAX_THR_SPEED`", "duration is the control" — ALL FOUR ARE DEAD.** All four wheels are in RPM
mode; `RO_MAX_THR_SPEED` is **4.93** and speed commands ARE honoured (0.150 commanded → 0.149
measured, 2026-09-15). Kept for the odometry and coast/brake numbers, which still stand.

## ✅✅ 2026-09-12 (floor) — **THE FLOOR RUNS. SCALE VALIDATED · COAST CLOSED · BRAKE RATIO REAL · G2 ANSWERED**

Operator-driven, Manual, open loop. `tools/field_measure.py`, four recordings in
`~/rover_data/logs/floor_*.json`. ⛔ I commanded nothing; he drove and I watched.

### 🔴🔴 THE G2 ANSWER — **AT A CONSTANT STICK THE ROVER NEVER REACHES A STEADY SPEED**
Stick held at **~0.11 for 2.5 s**: ERPM **82 → 184 → 279 → 373 → 466 → 564**, climbing the whole
time, **current FLAT at 2.6-2.9 A**. Constant current = constant torque = constant acceleration, no
equilibrium. ⇒ **CONFIRMED ON THE FLOOR: the ESCs take throttle as TORQUE.**
🔑🔑 **THE OVERSPEED IS AN INTEGRAL, NOT A RATIO.** ⛔ **STOP QUOTING "~5.5×"** — hold twice as long
and you get twice the speed. `RO_MAX_THR_SPEED` describes a throttle→speed relationship that **DOES
NOT EXIST ON THIS VEHICLE**. ⛔ Do not "calibrate" it. Acceleration **0.75 m/s² at 2.7 A**.
⚠️ That run reached **2.2 m/s on a tenth of stick**, covered 3.2 m, and stopped **0.185 m** from a
wall — INSIDE the 0.35 m standoff — only because the operator hit reverse. **Duration is the control,
not stick position.**

### ✅ ODOMETRY SCALE VALIDATED — `/odom` over-reads **8.1%** ⇒ THE SIGN FIX IS CONFIRMED
Gentle burst, `/scan` tracking from the first sample: **3.188 m by `/scan` vs 3.469 m from the
wheels.** 🔑 **With the OLD addr-10 inversion the wheels would have read ~HALF. They read 8% MORE.
Only the corrected sign map produces that.** ⛔ **THE ~10× CONFLICT IS DEAD** — the old 0.000380
would predict 0.21 m/s where the wall measured 2.13.
⛔ **DO NOT CHANGE `erpm_to_ms`.** The tool suggests 0.003584; 8% is inside the slip spread the
constant was fitted across, and one run at one speed on one floor is not grounds to move a
tape-validated value. ⚠️ The aggressive run gave **13%** — slip grows with acceleration.

### ✅✅ COAST BASELINE CLOSED (open since 09-09) AND THE BRAKE RATIO IS NOW REAL
| | deceleration | stop from 0.8 m/s | run |
|---|---|---|---|
| **coast** | **0.46 m/s²** | 0.70 m | 1.42 → −0.03 m/s over 2.01 s, **to rest** |
| **RC brake** | **1.44 m/s²** | 0.22 m | 1.53 → 0.05 m/s over 1.17 s, **to rest** |
🔑 **BRAKE IS 3.1× COASTING — MEASURED, same session, same floor, BOTH runs to a full stop.** The
old "3.4× PROVISIONAL" (coast n=2, neither to rest) is superseded and lands close.
🔴 **THE BRAKE TAKES ~0.3 s TO BITE.** Throttle centred at 1.535 m/s; current stayed ~0 for 0.32 s,
during which it slowed at **0.43 m/s² on drag alone — independently reproducing the coast figure.**
Total stopping distance **0.925 m**, of which the first **0.14 m** was before the brake engaged.
🔑 **REGEN CURRENT CAPPED AT −4.99 A** ⇒ **`l_in_current_min` = −5 A IS what binds**, answering the
`RESUME.md` open item that tried to reconcile a −12.06 A peak against the −5 A cap.
🔑 Current faded −4.99 A @1.1 m/s → −0.44 A @0.06 m/s ⇒ **regenerative, strongest when fast** — right
for cutting the reflex coast, wrong for holding still.
🔴 **COASTING IS LONG: 1.78 m from 1.40 m/s.** A burst released with 1.78 m of clearance rolled to
**0.34 m raw ≈ ZERO bumper clearance.** ⇒ the standoff is speed-bound, exactly as recorded.

### ⚠️ MEASUREMENT TRAPS FOUND THE HARD WAY — READ BEFORE THE NEXT FLOOR SESSION
🔴 **`/scan` DOES NOT TRACK BEYOND ~3 m IN THIS CORRIDOR.** At 3.8 m the 0.275 m corridor subtends
only **±4°** and the wall sat at the **5 m range limit**, so for the first **1.9 s** the sector
minimum was FLAT (drifting UP) while the wheels integrated 1.7 m. Scoring it in gave **36%** error
against **8%** for the tracking window. ⇒ **PARK ~2.5 m OUT, NOT 3.5.**
🔴 **A SOFA IS A POOR RULER** — jitter 0.074 m, and once 2.069 m as the corridor flickered between
two surfaces. ⛔ **Gate on jitter < ~0.05 m AND spread < ~0.05 m before driving.** A flat wall
squared-up gave 0.002 m on 09-11.
🔑 **HIGH NaN COUNT IS NOT BLINDNESS** — the corridor filter rejects everything outside 0.275 m BY
DESIGN, which is most of the sector at range. Judging on NaN alone called a clear corridor "blind"
twice. Judge on whole-scan health (was 66-88%) plus the nearest in-corridor return.
🔧 **FIVE defects fixed in my own analysers today, ALL the same family — a confident number from
data that did not support it:** steepest-sample-pair decel reporting **87 m/s²** (nine g) as a brake
figure · a coasting wheel counted as evidence of a deadband · an inverted bracket averaged into a
plausible answer · scale scored first-to-last so an out-and-back cancelled to "scan −0.006 m, erpm
15.281 m" · a decel run broken by ERPM noise, truncating a 1.44 m/s² brake to 0.60.
⇒ **`ros2_ws` `1ca3fdf`. ⛔ Distrust any analyser output that has not been checked against a run you
can read by eye.**

## 🔴🔴🔴 2026-09-12 (day) — **G2 REFRAMED: THE ESCs TAKE THROTTLE AS *TORQUE*, SO `RO_MAX_THR_SPEED` CANNOT BE CALIBRATED**

> ⛔ **STOP TREATING THE OVERSPEED AS A WRONG CONSTANT. IT IS THE WRONG *KIND* OF COMMAND.**
> The operator's own question — *"why not just calibrate max wheel speed × circumference like a
> human would?"* — is what exposed this. He was right to ask, and the answer is that the number
> would not stay put.

**MEASURED, wheels-up, Manual, 21 held rungs** (`tools/throttle_ladder_record.py`, new this day;
raw log `~/rover_data/logs/ladder_20260912_103319.json`):

| stick | 0.148 | 0.238 | 0.356 | 0.540 | 0.602 | 1.000 |
|---|---|---|---|---|---|---|
| ERPM | 1502 | 1507 | 1511 | 1510 | 1510 | 1504–1511 |

**Speed is FLAT from ~1/7 stick to full stick**, current ~2.0 A throughout. 🔑 **That is the
signature of a CURRENT (torque) command with no load:** anything above friction accelerates to the
same ceiling, which is set by back-EMF against the 24.7 V pack, not by the stick. Bigger stick only
means it *arrives sooner*.

✅ **CONFIRMED IN CONFIG, TWO INDEPENDENT RULERS:** all four `configs_from_repo/vesc_appconf_*.xml`
carry **`uavcan_raw_mode = 0` = `UAVCAN_RAW_MODE_CURRENT`**, and the behaviour matches.
⚠️ Still never read off live hardware (needs USB) — it is an open item in `bldc_can/RESUME.md`.

🔴 **WHY THIS BREAKS PX4:** `RoverControl::speedControl` computes
`throttle = setpoint / RO_MAX_THR_SPEED`, which assumes **throttle ∝ speed** — true for a DUTY-mode
ESC. In torque mode speed is whatever the load allows, so the "right" value of `RO_MAX_THR_SPEED`
differs on every surface. ⇒ **the 5.5× overspeed is structural.** ⛔ Do not set the parameter from
one floor run and call it fixed.
✅✅✅ **RESOLVED LATER THE SAME DAY (09-12): PATH (A) WAS TAKEN AND IS DONE ON ALL FOUR ESCs.**
`uavcan_raw_mode` 3 · `rpm_max` 9000 · `s_pid_min_erpm` 200 · ramp 20000, one USB session per wheel;
`RO_MAX_THR_SPEED` 0.60 → 4.93. Bench-matched to 0.4% across the four. ⇒ **the section below is the
reasoning that led to the decision, NOT an open question.** Path (B) (companion-side throttle loop)
was NOT needed. ⚠️ still bench-only — the floor run under load is the open item.
→ [[project_vesc_can_flashing]] + [[reference_esc_telemetry]] 09-12.

⏭ **THE ORIGINAL FRAMING — TWO WAYS OUT, OPERATOR'S CALL (kept for the reasoning):**
**(A) `uavcan_raw_mode` = 3 (`UAVCAN_RAW_MODE_RPM`)** — the VESC closes its OWN speed loop
(`mc_interface_set_pid_speed`), so PX4's assumption becomes true, and **`uavcan_raw_rpm_max` IS the
speed cap the operator wanted.** Then set `RO_MAX_THR_SPEED` to that cap in m/s. ⛔ **Not settable
over CAN** (8 params only) — **UART or USB, ONE SESSION PER ESC, no multi-drop.** ⛔ **BLE is out on
these boards** (the module sits on the DRV8301 SPI). → `project_vesc_can_flashing` 09-12
**(B) CLOSE THE LOOP IN THE COMPANION** — ✅ **feasible, confirmed:** `px4_ros2` ships rover
**throttle** setpoint types (`throttle_steering.hpp` · `throttle_attitude.hpp` · `throttle_rate.hpp`
alongside the `speed_*` ones). `rover-autonav-mode` uses a **speed** type today, which hands control
to PX4's broken loop; switching to a **throttle** type lets us run the PI on our own validated
`/odom` and enforce the cap ourselves. **One file in `ros2_ws`, nothing on the vehicle changes.**
🔑 **OPERATOR'S OWN POINT, AND IT IS RIGHT: DRIVE ON MEASURED DISPLACEMENT, NOT ON TIME.** The
2 m→10 m failure came from test harnesses that commanded a speed for N seconds and assumed the
distance. Integrating `/odom` and stopping on distance removes it **without touching the ESCs** —
and today's coast/brake figures are what let the stop be commanded EARLY enough.
⚠️ **A displacement controller is a workaround; Nav2's local planner already closes on pose.** But it
publishes `cmd_vel` in m/s and assumes the base honours it, so it inherits the same defect —
**G2 is a precondition for Nav2, not an alternative to it.**

🔑 **METHOD LESSON — STANDS CANNOT MEASURE A THROTTLE→SPEED CURVE ON THIS VEHICLE.** Under no load
the answer saturates. The ladder MUST be run loaded. `throttle_ladder_record.py --analyse` now
detects the flat case and refuses to print a fit. ⚠️ It also drops rungs where ERPM is still
drifting or current is NEGATIVE — those are spin-downs, and scoring them invented low-throttle
points that were never held.
⚠️ **`0.0039 × 1505 = 5.87 m/s` is an EXTRAPOLATION ~6× beyond where that constant was validated.**
`setup_manual` §A7 records the drivetrain measured at **0.58–0.60 m/s** on 08-02, and the pre-08-13
`erpm_to_ms` of 0.000380 would give 0.57 m/s at 1505. **That ~10× conflict is UNRESOLVED — the
taped floor run settles it.** ⛔ Do not quote a top speed until it does.

## 🔴🔴 2026-09-12 — **`/odom` WAS READING HALF: THE ADDR-10 SIGN INVERSION WAS STALE. FIXED.**

**Measured on stands, BOTH directions, 38,396 samples** (`ladder_*.json` + `reverse_*.json`):

| addr | forward | reverse |
|---|---|---|
| 10 | 11,410 positive vs 43 | 5,001 negative vs 33 |
| 11 | 11,430 positive vs 15 | 5,002 negative vs 33 |
| 12 | 11,412 positive vs 40 | 4,999 negative vs 31 |
| 13 | 11,460 positive vs 16 | 5,008 negative vs 39 |

⇒ **all four ESCs report SIGNED ERPM on ONE convention and flip together.** Operator confirmed by
eye, both directions. With the old `wheel_signs = [-1.0, ...]` the right side averaged
`(-1487 + 1532)/2 ≈ 9` ERPM instead of ~1500 — **it cancelled itself**, and `/odom` published ~half.
✅ **FIXED:** `wheel_odometry_node.py` default → `[1.0, 1.0, 1.0, 1.0]`, rebuilt, service restarted,
log verified `signs={10: 1.0, ...}`. Same correction applied to `manual_drive_log.py` (the ORIGIN of
the claim — every other tool copied it), `wheel_erpm_log.py`, `odom_scale_measure.py`.
⚠️ `config/rover_odometry.yaml` is **NOT LOADED** (no `--params-file` on the unit) — the node
defaults are what run. Both were changed, but only the source default takes effect.
🔑 **The scale is safe:** had `erpm_to_ms` been tape-fitted while the right side cancelled, it would
have had to come out ~0.0085; it is 0.0039 against ~0.0042 from geometry. **So the map was correct
in August and broke later** — the 09-09 four-ESC reflash is the likeliest trigger, NOT PROVEN.
🔴 **`/odom` NOW REPORTS ~2× WHAT IT DID. UNVALIDATED UNTIL IT MEETS TAPE.** It feeds the EKF
bridge, so the next armed run hands PX4 roughly double the velocity of yesterday's runs ⇒
**yesterday's overspeed numbers are NOT directly comparable to whatever comes next.**
⏭ **FIRST FLOOR ITEM: drive a taped distance, compare with `/odom`.** That validates the fix and
yields the loaded torque→speed point in one run.

## 🔧 2026-09-12 — **PX4 PARAM AUDIT, READ LIVE. Nothing written by me; 4 written by the operator.**

✅ **Correct, verified against the flashed source:** `RD_WHEEL_TRACK` 0.31 · `CA_AIRFRAME` 6 ·
`CA_R_REV` 3 · `UAVCAN_ENABLE` 3 · `RC_MAP_ARM_SW` 5 / `KILL_SW` **12** / `FLTMODE` 6 /
`THROTTLE` 2 / `YAW` 4 · `RC_KILLSWITCH_TH` 0.75 · `UAVCAN_EC_FUNC1..4` = 101,102,101,102
(Motor1/Motor2 — correct left/right pairing) · `MIN` 110 / `MAX` 8082 · `EKF2_EV_CTRL` 4 ·
`EKF2_GPS_CTRL` 7 · `EKF2_MAG_TYPE` 1 · `COM_POS_FS_EPH` 5 · `COM_DISARM_PRFLT` 10.

🔴 **`NAV_RCL_ACT` READS 1 (Hold), NOT 6 (Disarm).** `bldc_can/RESUME.md` argues brake-off-on-RC-loss
FROM `=6` — **that argument no longer holds, and RC loss will NOT disarm.**
✅ **`RO_YAW_RATE_I` = 0.0 IS DELIBERATE — IT IS THE FIX, NOT A DRIFTED VALUE.** ⛔ **NEVER restore
it to 0.1.** Corrected 2026-09-12 against the AutoNav Technical Reference artifact §5
(`bc09dd55`, rev 08-09), which carries the rule verbatim: *"Integral windup was one of the two
causes of the yaw problem."* ⚠️ My first reading of it as a stale RCA was wrong.
🔑 `RO_SPEED_I` is still **0.1**, so **speed**-loop windup remains possible — that is a different
loop and a live suspect.
⚠️ `RO_ACCEL_LIM`/`RO_DECEL_LIM`/`RO_JERK_LIM` all −1. Deliberate (they slew the manual stick), but
`RO_DECEL_LIM = -1` guarantees waypoint overshoot in auto modes — an M2/M3 blocker, not a floor one.
⚠️ `RO_SPEED_LIM` 0.7 · `RO_SPEED_TH` 0.10 against a measured ESC dropout ~0.14.
⛔ **`COM_POS_FS_EPV` DOES NOT EXIST on this firmware** (only `_EPH`) — settled with the fake-name
control. ⚠️ **`dump_params.py` (bulk `PARAM_REQUEST_LIST`) returns "received 0" today** — named
reads work fine, so the param BACKUP path is broken while single reads are not.
🔑 **MANUAL MODE BYPASSES THE WHOLE SPEED LOOP** (`DifferentialManualMode::manual()` copies the stick
into `throttle_body_x`) ⇒ every `RO_*` value is INERT for an open-loop ladder. Nothing needed
changing to run it.

## ⏭ 2026-09-12 — **SOFTWARE BRAKE PATH OPENED: SLOT 6 = `Peripheral_via_Actuator_Set1`**

**Why:** the RC brake is on `UAVCAN_EC_FUNC5 = 407 = RC_AUX1`, i.e. **pure RC passthrough — there is
no software path to it at all.** That is the verified reason the collision reflex can only zero the
setpoint. ⛔ **Do NOT move slot 5** — that would make the operator's emergency brake depend on the
companion, whose crash behaviour is untested (R5.5).

✅ **OPERATOR SET THESE 2026-09-12, VERIFIED LIVE:** `UAVCAN_EC_FUNC6` **301** · `MIN6` **1** ·
`MAX6` **8191** · `FAIL6` **0** (slot 5 left at 407). **`esc_count` 5 → 6, `esc_armed_flags` 63,
`esc_online_flags` still 15.** ✅ **PERSISTED — set from QGC, which commits to flash on write; the
operator confirmed no reboot is needed.** (⚠️ that is NOT true of `set_param.py`, which is RAM-only
and needs `param_save.py`.)
🔑 **IT REALLY DOES GO OUT ON DroneCAN RawCommand** — `esc.cpp:104-123` fills `cmd` then
`msg.cmd.resize(min_size)` where `min_size` = highest slot with `FUNCn > 0`. 5 slots before, 6 now,
so index 5 is broadcast. Same message, no protocol change.
🔑 **`Peripheral_via_Actuator_Set1..6` = 301-306, driven ONLY by `VEHICLE_CMD_DO_SET_ACTUATOR` (187)
on `vehicle_command`** (`FunctionActuatorSet.hpp:55-80`): `param7`=group (0), `param1..6`=values,
NaN = leave alone. **`/fmu/in/vehicle_command` is ALREADY BRIDGED** (same topic as the force-disarm)
⇒ the companion can drive it over DDS, no MAVLink.
⛔ **−1.0 = OFF, 0.0 ≈ 50% BRAKE** (the value maps onto MIN..MAX) — the `RC3_TRIM` trap in a new
costume. ⚠️ **The value LATCHES**; the reflex must explicitly release. Outputs act only ARMED.
⏭ **STILL INERT — the VESC side is not done.** `canard_driver.c` (~746, line from notes, the
firmware tree is NOT on this machine) must read index 5 as well and take `max(idx4, idx5)`.
🔴 **BOUNDS-CHECK `cmd.len` BEFORE READING INDEX 5** — PX4 resizes the array, so it is 5 long
whenever `FUNC6` is 0. With the check either side can be updated in any order; without it, not.
Needs all four reflashed over USB; rollback tag `v6.06.0-pxlabs-rover-r1`.

## ✅✅ 2026-09-12 (02:00) — **ARMED AUTONAV ENGAGED FOR THE FIRST TIME. THE eph PROCEDURE WORKS.**
`AutoNav holding (nav_state=23)` **while ARMED** — the first time all evening, and the direct
confirmation of the eph diagnosis below. **Nothing about the mode, the bridge or the registration was
ever broken; the blocker was position uncertainty and it is now a solved, repeatable procedure.**

### 🔑🔑 THE PROCEDURE THAT WORKS — run it in THIS order, it got all three gates green
1. **Reboot the FC** (disarmed) — `codex-work/bldc_can/diag/fc_reboot.py`. This is what resets `eph`.
2. FC was back in **3 s**. Then **restart `rover-ekf-bridge` AND `rover-autonav-mode` together**
   (`systemctl restart rover-ekf-bridge rover-autonav-mode`) — the reboot wipes the mode registration,
   and the node must re-register **while DISARMED**.
3. ⚠️ **`COM_DISARM_PRFLT` resets to 10 s on every FC reboot.** ⛔ **ASK BEFORE CHANGING IT** →
   [[feedback_ask_before_param_change]]. Restored to **10** at end of session 09-12.
4. **Verify all three gates before arming — do not assume:**
   `failsafe_flags.local_position_invalid` **false** · handshake counts **non-zero both ways**
   (`can_arm_and_run=True`) · `preflight_scan_check` runway.
5. Operator arms on **ch5**; engage AutoNav; kill is **ch12**.

### 📏 `eph` GROWTH — MEASURED, and the first estimate was WRONG
| t after FC reboot | `eph` |
|---|---|
| ~6 s | **0.16 m** |
| ~5 min | **0.78 m** |
🔑 **Sustained growth ≈ 0.002 m/s ⇒ roughly 35 MINUTES of budget under the 5.0 m
`COM_POS_FS_EPH` threshold — NOT the ~5 min I first quoted.** ⛔ **That first "0.01 m/s / 330 s left"
figure was NOISE ON AN 8-SECOND SAMPLE — do not quote it.** It is a comfortable window, not a race.
⚠️ Growth was measured **STATIONARY**. It will be faster while driving; re-measure before relying on it.

### 🔴 OVERSPEED — NOW CONFIRMED TWICE ON THE FLOOR, SAME RATIO
| run | commanded | bound | expected | **`/scan` MEASURED travel** | ratio |
|---|---|---|---|---|---|
| 1 | 0.10 m/s | 5.0 s | ~0.5 m | **2.69 m** | ~5.4× |
| 2 | 0.10 m/s | 3.0 s | ~0.3 m | **1.66 m** (4.524 → 2.861 m) | ~5.5× |
🔑 **Two independent runs, the same ~5.5× ratio.** This is the R4 defect with a repeatable number.
⛔ **Both runs ended with the rover STILL MOVING after the tool commanded zero** (rpm 104, then 118);
both were stopped by a **DDS force-disarm** (`VehicleCommand` 400, `param1=0`, `param2=21196`).

### ⬜ S1 STILL INCONCLUSIVE — operator confirmed he did NOT press ch12
⛔ **Do NOT log S1 as failed. It has never been exercised on the correct channel.**
⚠️ **AND THE PASS CRITERION ITSELF IS SUSPECT:** in PX4 the **kill switch and disarm are DIFFERENT
actions** — `RC_MAP_KILL_SW` triggers a manual kill that stops motors, and the vehicle can remain
ARMED in that killed state. `s1_kill_test.py` requires "wheels stop **AND** disarms". **Decide what S1
actually means before the next run**, or a real pass could be recorded as a failure.

## 🔴🔴🔴 2026-09-12 — **WHY ARMED AUTONAV IS REFUSED: `eph` 307 m vs `COM_POS_FS_EPH` 5 m. SOLVED.**
> This closes the "armed → refused, disarmed → accepted" mystery that has recurred since August.
> ⛔ **It is NOT the registration, NOT the bridge, NOT the mode. It is POSITION UNCERTAINTY.**

**THE CHAIN, MEASURED END TO END:**
1. `autonav_mode` uses **`RoverSpeedRateSetpointType`**, which declares (`speed_rate.cpp:50-54`)
   `velocity_enabled=true`, **`position_enabled=FALSE`** — the mode does NOT ask for position.
2. ⛔ **BUT `FailsafeFlags` HAS NO `mode_req_local_velocity` FIELD.** The only fields are
   `mode_req_local_position` / `_relaxed` / `_local_alt` / `_angular_velocity` / … ⇒ **PX4 expresses a
   velocity requirement AS the LOCAL_POSITION requirement.** Measured for AutoNav (**bit 23**):
   `mode_req_local_position` **=1** · `mode_req_local_alt` **=1** · `mode_req_angular_velocity` **=1** ·
   `mode_req_local_position_relaxed` **=0**.
3. `local_position_invalid` is judged on **ACCURACY, not existence**: `vehicle_local_position` reads
   **`xy_valid: true`** while `failsafe_flags` reads **`local_position_invalid: true`** — not a
   contradiction, a stricter test.
4. 🔑🔑 **THE NUMBER: `eph` = 306.78 m against `COM_POS_FS_EPH` = 5.0 m.** Velocity-only fusion
   DEAD-RECKONS, so eph grows without bound. (Velocity itself is fine: `evh` 0.060 vs
   `COM_VEL_FS_EVH` 1.0 ⇒ `local_velocity_invalid: false`. Altitude fine: `epv` 0.19.)
5. PX4 **relaxes** mode requirements while DISARMED and **enforces** them ARMED ⇒ disarmed accepts,
   armed refuses. **That is the entire pattern.**

### 🔑 WHY IT WORKED IN JULY/AUGUST — nothing regressed, the procedure was always time-limited
**`eph` starts small after an FC reboot and GROWS while dead-reckoning.** The July/August runs started
the bridge and engaged AutoNav **promptly**, inside the window where `eph` < 5 m. Tonight the FC had
been up for a long time, so we were ~60× past the threshold. ⇒ ⛔ **STOP recording S1/AutoNav as
"works" or "broken" without the `eph` at that moment — it is the hidden variable.**

### ⏭ TWO WAYS FORWARD — operator's call
- **(a) RACE IT (works today, fragile):** reboot the FC → start `rover-ekf-bridge` → arm and engage
  AutoNav **before `eph` passes 5 m**. ⚠️ **The window has never been measured — measure `eph` vs time
  first**, it is the whole basis of the procedure.
- **(b) FIX IT PROPERLY:** give PX4 a bounded position. That is `EKF2_EV_CTRL` **bit0** fed from
  RTAB-Map `map→odom` via the **Navigation Interface `position_xy` channel we already do not use**
  → [[reference_px4_vio_collision]] §4. ⇒ **LOCALIZATION IS NOT ONLY AN M3 ITEM — it is what makes
  ARMED AUTONAV ROBUST.** This contradicts the plan's "M2 needs no localization" only in ROBUSTNESS,
  not in principle: M2 still needs no MAP, but it needs `eph` under 5 m.
- ⚠️ **Raising `COM_POS_FS_EPH` is the third option and is NOT recommended without discussion** — it
  disables a real failsafe. Arguable for this vehicle (AutoNav is speed+rate and uses position for
  NOTHING), but it is a safety threshold, so it is the operator's decision, not mine.

## 🔴🔴 2026-09-12 — **G2 ATTEMPT: S1 INCONCLUSIVE, BUT "ZERO SETPOINT DOES NOT STOP THE ROVER" PROVEN ON THE FLOOR**

### ⛔⛔ THE ARMING/REGISTRATION ORDER — THIS BLOCKED THE WHOLE EVENING, IT IS NOT IN ANY MANUAL
🔑 **PX4 REFUSES TO REGISTER AN EXTERNAL MODE WHILE THE VEHICLE IS ARMED.** Measured twice armed:
`register_ext_component_reply` **`success=False, mode_id=0`**, arming-check handshake **0 in / 0 out**,
`DO_SET_MODE(4,11)` → **TEMPORARILY_REJECTED**. Disarmed, the identical restart gives
**`success=True, mode_id=23`**, handshake ~23 req / 26 reply per 8 s, `can_arm_and_run=True`, mode ACCEPTED.
⇒ **ORDER IS: DISARM → restart `rover-autonav-mode` → CONFIRM registration → ARM → switch mode.**
🔴 **AN FC REBOOT WIPES THE REGISTRATION AND `autonav_mode` DOES NOT NOTICE — it keeps running
unregistered.** After ANY FC reboot you MUST restart `rover-autonav-mode` (while disarmed).
🔑 **PROOF OF LIFE = the arming-check handshake, not `is-active`**: count `/fmu/out/arming_check_request_v1`
and `/fmu/in/arming_check_reply_v1`; **zero on both = unregistered**, whatever systemd says.
⚠️ `autonav_chain_check.py` only sees registration if the node starts AFTER it, and **stops at STAGE 2**
otherwise — it cannot report current state. Measure the handshake directly instead.

### ⚠️ `COM_DISARM_PRFLT` = 10 s — PX4 AUTO-DISARMS 10 s AFTER ARMING IF NOTHING MOVES
This produced repeated "you armed but it reads disarmed" confusion. For a supervised test raise it in
**RAM only** (`set_param.py`, not saved) and **restore it after** — done and restored 09-12.

### 🔴🔴 THE REAL RESULT: COMMANDING 0.0 m/s DID NOT STOP THE ROVER
Run: `s1_kill_test.py --speed 0.10 --bound 5.0`, armed, AutoNav held (`nav_state=23`), floor, hall.
**The tool DID command zero** — its exit path is `drive(0.0)` → spin 0.5 s → `drive(0.0)`.
**`final rpm 104` was read AFTER those zero commands.** The wheels were still turning.
📏 **TRAVEL MEASURED BY `/scan`: bumper clearance 4.498 m → 1.808 m = 2.69 m travelled** on a command
that should have produced ~0.5 m — **~5× over**, consistent with the recorded 0.05→0.14 / 0.25→~0.9.
It consumed **65% of a 4.15 m runway.** Stopped by a **DDS disarm** (`VEHICLE_CMD_COMPONENT_ARM_DISARM`,
param2 magic 21196 as force after 2 s) — that worked: `arming_state=1`, all ESCs 0 rpm.
⇒ 🔑 **THIS IS THE EVIDENCE FOR WIRING THE BRAKE INTO THE REFLEX.** Zero setpoint = free-flow coast,
and below `RO_SPEED_TH` the firmware zeroes its OWN feedback so the loop re-accelerates. **0.69 m/s²
of brake vs a coast that left 104 rpm after two zero commands.** → [[reference_esc_telemetry]]

### ⬜ S1 IS **INCONCLUSIVE — NOT FAILED**, AND THE ROOT CAUSE IS A WRONG CHANNEL IN THE DOCS
⛔⛔ **THE KILL SWITCH IS `ch12`. `RC_MAP_KILL_SW` = 12, read live off the FC 2026-09-12** and confirmed
against a fake-name control. Supporting map: `RC_KILLSWITCH_TH` **0.75** · `RC_MAP_ARM_SW` **5** ·
`RC_MAP_FLTMODE` **6**. **NOTHING is mapped to ch8.**
🔴 **Every tool and doc said "ch8", so the operator was told to press a channel that does nothing.**
He moved **ch5 — the ARM switch** — which is why `input_rc` ch8 read 1011 before AND after.
⚠️ **This was ALREADY KNOWN: `todos.md` P5 says "`RC_MAP_KILL_SW`=12 vs docs ch8 — fix the DOCS, not the
param". It was never actioned.** The tools detect the kill via `arming_state`, not by reading a channel,
so the CODE was always correct and only the printed instruction was stale — that is why it survived.
✅ **Corrected 2026-09-12 in `s1_kill_test`, `speed_command_test`, `collision_standoff_test`,
`s2_sensor_loss_test`, `t2_straight_goal_test`, `l2_test`** (`ros2_ws` `6506bdb`).
🔑 **Historical July records of "ch8 worked" are NOT wrong — the mapping almost certainly moved when the
RC was reconfigured for the brake on ch3/AUX1. Do not rewrite them.**
⛔ **Do NOT record this run as an S1 failure.** S1 remains due, and the next attempt must confirm the
ch8 channel index on the transmitter FIRST.
⚠️ `s1_kill_test.py` has **NO `/scan` clearance backstop** (no `LaserScan` subscription at all) — it is
the only moving test without one, and this run shows why that matters: nothing but the operator bounds it.


## ✅✅ 2026-09-11 — **G0 CLOSED. `/scan` GEOMETRY VERIFIED LIVE AT A WALL after the pitch/roll fix.**

**WHY IT MATTERED:** `depth_to_scan.launch.py` got the measured mount angles 09-10 (`cam_pitch`
0.0406→**0.0251**, `cam_roll` 0.0100→**−0.0078**). The box **rebooted 22:44:56 on 09-11**, so
`rover-scan` picked them up — the geometry went **LIVE AND UNVERIFIED**, the exact state the old
warning forbade, because the collision reflex acts on `/scan`. 0.0155 rad = **0.89°** ≈ ⅓ of the
scan band's ±2.79° half-width ⇒ ~23 mm vertical shift at 1.5 m, ~47 mm at 3 m. Down ⇒ floor enters
the scan and reads as a permanent obstacle; up ⇒ low objects get cleared (**the unsafe direction**).

**THE REAL RISK, AND IT CAME THROUGH INTACT:** `/scan` scale **0.9845** and `front_overhang`
**0.337** were tape-fitted 08-12/13 **with the OLD 0.0406 pitch baked in**. They are a fit, not a
law. `preflight_scan_check.py` hardcodes 0.337 in source; the standoff pass rests on both.

### THE LADDER THAT SETTLED IT — 5 parkings, one wall, nothing ever moved under power
| parking | `/scan` perp | bearing | fit RMS | inliers | coverage |
|---|---|---|---|---|---|
| 1 | 1.3827 m | −3.90° sd 0.04 | 3.4 mm | 1.00 | 0.80 |
| 2 (operator re-squared) | 0.3449 m | −3.49° sd 0.02 | 0.4 mm | 1.00 | 0.80 |
| 3 (**rover** corrected) | 0.3848 m | **−0.25°** sd 0.01 | 0.4 mm | 1.00 | 0.80 |
| 4 (never explained) | 0.3404 m | −0.40° sd 0.00 | 0.3 mm | 1.00 | 0.80 |
| **5 — THE DECISIVE ONE** | **1.4390 m** | **+0.30°** sd 0.03 | 2.1 mm | 1.00 | 0.80 |

✅ **PASS, ON OPERATOR TAPE AT PARKING 5:** taped bumper→wall **face** 1.12 m. Model predicts
`0.9845 × (1.12 + 0.337)` = **1.4344 m**; `/scan` read **1.4390 m** ⇒ **4.6 mm on 1.46 m (0.32%)**.
Inverted: `1.4390/0.9845 − 0.337` = **1.1247 m** vs taped 1.12 ⇒ **4.7 mm**, inside tape resolution.
⇒ **BOTH CONSTANTS SURVIVE THE TRANSFORM CHANGE. ⛔ DO NOT RE-DERIVE THEM.**
🔑 The mm-level agreement also **proves the tape reference point was the bumper** — any other
reference would have missed by cm, not mm.

🔑🔑 **THE FLOOR-IN-SCAN TEST IS `inlier fraction`, NOT RMS ALONE.** RANSAC returned **1.00 at every
range including 1.44 m** = ONE clean plane filling the whole ±20° sector. Floor in the band would
fit two surfaces at different ranges and blow RMS to cm.

### 🔑🔑 `cam_yaw` — CONFIRMED 0.0, AND `wall_probe` IS THE ONLY INSTRUMENT THAT CAN SEE IT
`cam_yaw` **exists** as a launch arg (`depth_to_scan.launch.py:98`, wired to `--yaw`) and has always
been **0.0**. ⛔ **`cam_mount_probe.py` CANNOT CHECK IT — its own line 30: "Yaw is unobservable from
gravity."** The −3.90°/−3.49° bearings at parkings 1–2 looked like a real mount yaw (two ranges
1.04 m apart agreeing within **0.41°**, both fits immaculate) — **it was the PARKING.**
✅ **DISCRIMINATOR: the operator re-squared THE ROVER — he explicitly did NOT touch the camera — and
the bearing collapsed to −0.25°.** (Third time he has been right about the mount. See the standing
⛔⛔ rule.)
🔑 **A bearing that persists across parkings at DIFFERENT ranges is NOT proof of camera yaw.** Square
the rover first. The camera-independent check is **equal tape gaps at both front corners**: a 0.56 m
front edge yawed 3.5° gives a **34 mm** left-vs-right difference (0.73 m ⇒ 45 mm), and near-contact
parking (~8 mm) is the easiest place to read it.

### FREE VALIDATIONS PICKED UP ALONG THE WAY
✅ **The reflex behaves correctly under the NEW geometry:** BLOCKED at 0.008 m ("AutoNav will refuse
to drive forward from this spot"), CLEAR at 1.039 m with 0.69 m of usable runway. Coverage **0.80
against `min_valid_fraction` 0.35** at every parking, **0 empty-sector scans**, jitter ≤4 mm.
✅ **Chain baselined NON-ZERO BEFORE measuring** (never read a quiet topic as evidence): `/scan`
**26.7 Hz**, `/odom` **89.3 Hz**, **556/640 valid rays**, `camera_info` **fx 304.05 @ 640×360**.
⚠️ `ros2 topic hz` again returned **nothing** on a healthy `/scan`, and `--no-daemon` **is not a flag
on `topic hz`** — a direct rclpy subscriber is the reliable ruler here.

### ⚠️ LIMITS OF THIS RESULT — state them, do not overclaim
- **ONE tape point.** At 1.12 m the accepted model and the rival fit refuted in §5 (scale 0.9573 /
  overhang 0.377) differ by only **~1 mm**. This run **confirms the accepted constants survived the
  transform change**; it does **NOT** independently re-refute the rival. §5's 1.973 m point still
  does that job and does not need repeating.
- **Parking 4 (0.3404 m) read CLOSER after "moved it back" and was never explained.** Superseded by
  parking 5. A frozen-frame check was started and interrupted — but the stream tracked the rover
  across 5 parkings and the bearing responded to a deliberate re-square, which is **stronger**
  evidence of liveness than that script would have produced.
- **All 5 parkings were the same wall.** A second wall at a different heading was never tried.

⏭ **NEXT = G2.** On the FC tonight: `RO_MAX_THR_SPEED` **0.6**, `RO_SPEED_TH` **0.10** — ⚠️ memory
records the ESC dropout floor as ~0.14, **unreconciled, belongs to G2.** **G3 venue call still OPEN
and still blocks T2.**


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
📗 **FULL RECORD → `~/ros2_ws/docs/rover_yaw_response.md`** (curve, mechanism, final tune, compass,
heading-control option, companion-loop option, method notes). **READ IT BEFORE TOUCHING YAW.**
✅ **FINAL TUNE APPLIED + FLOOR-VALIDATED:** `CORR 1.8 · P 0.08 · I 0.0 · LIM 85.9 deg/s (1.5 rad/s)
· MAX_THR_SPEED 0.6`. 50% stick → no rotation (deadband, correct) · 65% slow · 80% turns · 100%
fast — **monotonic and controllable**, where before Acro yaw did NOTHING and AutoNav ran away.
Top-end holds matched the model to **0.27 rad/s** (steer 1.000 → 4.60 vs 4.56 predicted).
⏱ **YAW IS SLOW: ~2 s time constant (2.24 s to 90%).** Steady-state needs a ~4.5 s hold ⇒ **the
65%/80% mid-range points are STILL UNMEASURED — an OUTDOOR job** (a skid-steer spin TRANSLATES;
no room indoors). **Nav2 must not re-plan faster than the vehicle can respond.**
🧭 **THERE IS A WORKING COMPASS** (`SYS_HAS_MAG=1`, `CAL_MAG0_ID=396809`, live on `HIGHRES_IMU`).
It CANNOT help the rate loop (heading ≠ rate) but **enables HEADING control via
`DifferentialAttControl`, which PX4 already has (`RO_YAW_P = 2.0` set)** and which degrades
gracefully against a deadband because heading error persists until the rover actually turns.
🔑 **`minimum correctable heading error = 0.9 / RO_YAW_P` ⇒ ~26° now, ~13° at P=4.** Design Nav2
around that number. **This is the recommended architecture** — Nav2 wants to command heading anyway.
🔎 **Why this rover is harder than most:** TurtleBot/Roomba/warehouse AMRs are **2 driven wheels +
casters** — casters swivel, so almost NO scrub and no deadband. This is a **4-wheel skid-steer,
25 kg, hard floor** = close to worst case. **Not misconfigured relative to the field — different
physics.** 4-wheel skid-steers (Husky/Jackal) cope via big torque margin + loose outdoor surfaces
+ accepting coarse yaw and planning wide arcs, not tight pivots.
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
- 🔴 **Data: `mapping_run2_20260802` was DELETED 2026-09-12** (operator's call, disk was at 85%). The old
  "re-runnable, no re-drive needed" no longer holds — **the `quat_reset_counter` diagnostic above now
  REQUIRES A RE-DRIVE**, and the 13.15 rad/s attitude-spike evidence is no longer re-examinable from a bag.
  ⚠️ If the #20 "measurement not motion" question is reopened, budget a fresh recording first.

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

---

# 2026-08-09 — WALL-REFERENCED ODOMETRY CALIBRATION. THE FC HEADING IS UNUSABLE; THE GEMINI GYRO IS GOOD.

**Method (operator's idea, and it worked):** park square to a flat wall, RANSAC-fit a line to `/scan`
(perpendicular distance ±1 mm, bearing ±0.26 deg — an ABSOLUTE reference, independent of the wheels),
and compare against odometry. Tape-measured confirmation matched: `wall_d` 2.268 m at `base_link`
minus `front_overhang` 0.337 m = 1.931 m to the bumper. Probe: `/tmp/wall_probe.py`, `/tmp/yaw3_probe.py`.

## 1. FC heading (PX4 EKF, `yaw_source: gyro`) — BROKEN, AND INTERMITTENTLY SO
Rover verified STATIONARY by the wall each time:

| window | dur | wall (truth) | FC | rate |
|---|---|---|---|---|
| parked, cold | 476 s | −0.07 deg | −2.46 deg | −0.005 deg/s |
| after a 0.364 m/s drive | 111 s | +0.01 deg | **−18.88 deg** | −0.170 deg/s |
| after turning | 21 s | −0.18 deg | **+23.23 deg** | **+1.106 deg/s** |
| after turning | 41 s | −0.07 deg | −7.17 deg | −0.175 deg/s |

⛔ **It is ERRATIC, not a bias — the sign flips.** Across one 4-min session it invented **+27.1 deg**
during stationary periods alone. Over 727 deg of real rotation its error was ~18 deg.
❌ **NOT proportional to motor effort** — run 7 at 0.341 m/s gave +0.54 deg phantom yaw where run 1 at
0.364 m/s gave −8.28 deg. **15x less at the same speed.** My "motor current / magnetometer" story is
NOT supported; the fault is intermittent and unexplained. `EKF2_MAG_TYPE=1` (mag in use) — the
disable test was never run, and with a fault this intermittent a single clean run would prove nothing.

## 2. ✅ GEMINI 336L GYRO — VALIDATED ON BOTH DRIFT AND SCALE. USE IT.
`/camera/gyro/sample`, 195 Hz, frame `camera_gyro_optical_frame`; rotate into `base_link` **via TF**,
do not hand-derive the axis mapping.

| property | value |
|---|---|
| bias | **+0.72 deg/s** — large but REMOVABLE |
| bias stability, cold (9x20 s) | sd **0.0028 deg/s** |
| bias stability, straight after driving | sd **0.0015 deg/s** — driving does NOT disturb it |
| **scale error** | **RATE-DEPENDENT under-read — see below** |

### 🔑 SCALE UNDER-READS, AND THE ERROR GROWS WITH ROTATION SPEED (3 runs, wall-referenced)
| run | manoeuvre | rotation time | mean rate | scale | error |
|---|---|---|---|---|---|
| 1 | 2 circles, paused | 87 s | 8.3 deg/s | 0.99623 | **-0.38%** |
| 3 | 2 circles, paused | 33 s | 21.8 deg/s | 0.98834 | **-1.17%** |
| 2 | 1 circle, continuous | 11 s | 32.7 deg/s | 0.95466 | **-4.53%** |

Monotonic and SUPERLINEAR (4x rate -> 12x error). ⇒ **MAP WITH SLOW, PAUSED TURNS: tap, full stop,
pause 3-4 s.** Over ~720 deg of cumulative rotation that is ~3 deg of error instead of ~33 deg.
⚠️ **The effect may be MY PROBE, not the sensor.** `/tmp/yaw3_probe.py` integrates on message
ARRIVAL time; if samples drop during a fast spin (peak CPU) and the next arrives after the peak,
the lower rate is applied across the gap ⇒ systematic under-read with exactly this signature.
⇒ **THE PRODUCTION NODE MUST integrate on `header.stamp` deltas, NOT arrival time, and must detect
and report gaps in the 195 Hz stream.** If the effect is the probe, full 0.4% accuracy is available
at any speed; if it is sensor bandwidth, the "turn slowly" rule stands. NOT YET DISTINGUISHED.

⇒ over a 263 s mapping run: **~1 deg of heading error, vs tens-to-hundreds from the FC.**
⚠️ bias creeps slowly (thermal): +0.0083 deg/s over 3 min ⇒ **re-estimate at rest**, don't calibrate once.
⚠️ **A MEMS gyro cannot observe absolute heading** — it only integrates rate. It fixes map-building
drift; it does not give you a north reference.

## 3. Translation: odom over-reports ~19% — but this is SLIP, do NOT "fix" `erpm_to_ms`
5 runs, both directions, 0.146–0.364 m/s: ratios 1.212 / 1.224 / 1.153 / 1.155 / 1.196,
**mean 1.188, sd 0.029.** Round trip: wall says back within **9 mm**, odom claims **0.891 m** away.
⛔ **`erpm_to_ms` = 0.004633 is CORRECT** — derived from a hand-push over 5 counted wheel revolutions,
which is slip-free and diameter-independent (see `config/rover_odometry.yaml`). A POWERED drive
measures eRPM→ground, which includes slip. Rewriting the constant would bake one acceleration
profile's slip in and be wrong everywhere else. **The 19% is real physical slip, not miscalibration.**

## 4. ⛔ `yaw_source: wheels` IS NOT AN OPTION — REFUTED BY THE CONFIG
"this is a skid-steer, so it can ONLY turn by making all four tyres scrub sideways, and the wheels
therefore cannot observe true rotation at all." I proposed this twice; it is structurally blind.

## ⏭ NEXT: add `yaw_source: camera_gyro` to `wheel_odometry_node`
Subscribe `/camera/gyro/sample`, rotate via TF, auto-estimate bias whenever the wheels read zero,
integrate. The `yaw_source` param + stale-fallback logic already exist — this is a new branch.
⚠️ **It couples odometry to `rover-camera`** — needs a fallback when the camera dies, and the camera
is the component that silently degrades (see MEMORY [SERVICES]).

## ✅ SHIPPED 2026-08-09 — `yaw_source: camera_gyro` IS LIVE AND VERIFIED
`wheel_odometry_node.py` + `config/rover_odometry.yaml`, built, deployed, service restarted.
**ACCEPTANCE (wall-referenced, 144 s parked, 538 samples): `/odom` yaw drift `+0.00028 deg/s`,
total 0.040 deg, spread 0.070 deg — BELOW the wall's own noise (+0.060 deg).**
vs FC on the same wall the same afternoon: −0.170 deg/s after a drive, **+1.106 deg/s after a turn**
(3950x worse). Over a 263 s map: **0.07 deg** instead of ~45 deg.

Startup sequence to expect in the journal:
```
wheel odometry up: ... yaw_source=camera_gyro
camera gyro unavailable — falling back to FC attitude   <- normal, pre-bias
camera gyro TF locked: base_link <- camera_gyro_optical_frame row_z=(-0.0100,-0.9991,-0.0406)
camera gyro bias established: +0.6963 deg/s from 400 at-rest samples
heading source: CAMERA GYRO (336L, bias-corrected)
```
Design: TF-derived axis mapping (a remount cannot silently flip the sign) · bias re-estimated from a
rolling 12 s at-rest window (thermal creep) · **integrates `header.stamp` deltas and REFUSES to
integrate across >50 ms gaps**, counting them · warns if the camera stamp clock diverges >1% from
wall clock · degrades `camera_gyro -> gyro -> wheels`, loudly · per-source yaw covariance
**0.002 / 0.02 / 0.2** (the FC path previously advertised 0.002 — overconfident by 10x).

⏭ **NOT YET RETESTED: the rate-dependent scale under-read.** The at-rest drift is fixed; whether
`header.stamp` integration also removes the −4.53%-at-32.7 deg/s scale error needs a fresh circle
test against the wall. **Until then, still map with slow paused turns.**

🔴 **TWO DEPLOY GOTCHAS FOUND:**
1. **`config/rover_odometry.yaml` IS NEVER LOADED** — the unit runs `ros2 run` with **no
   `--params-file`**, so only the `declare_parameter` DEFAULTS in the node take effect. Editing the
   yaml alone changes NOTHING. Banner added to the file.
2. `rover-odometry` has `StartLimitBurst=10`; a crash-looping deploy **latches `failed` and stops
   retrying**. Needs `systemctl reset-failed rover-odometry` before it will start again.

### ⚠️ THE CAMERA-GYRO HEADING COSTS ~28 POINTS OF A CORE (measured 08-09)
`wheel_odometry_node` steady-state CPU: **~25% before → 58.8% after → 53.5%** once the bias
estimator was made O(1) (deque + running sum instead of re-summing a ~2300-sample window at 195 Hz).
🔑 **The arithmetic is NOT where it goes** — the jump is rclpy per-message overhead on a **195 Hz**
subscription, matching the existing "~65% executor overhead, ~4% our logic" finding. ⛔ Do not try to
micro-optimise the callback. **The real levers: lower the IMU publish rate at the source, or the C++
port.** ⚠️ I first claimed the O(n) mean caused the doubling — it did not; measure before asserting.
Budget check with all this live: camera ~80%, wheel_odometry ~53%, XRCE ~20%, rc_control ~11%.

### 🔎 WHY THE FC YAW IS WRONG — SENSOR INVENTORY FROM THE FC WORK QUEUE (operator-supplied 08-09)
```
wq:SPI1  icm42688p 395 Hz | wq:SPI2  icm45686 400 Hz | wq:SPI3  bmi088_accel/gyro 400 Hz
wq:I2C3  bmm350 50 Hz  (the ONLY magnetometer)  |  vehicle_magnetometer 50 Hz
wq:nav_and_controllers  vehicle_gps_position 3.3 Hz | wq:uavcan  uavcan 333 Hz
wq:lp_default  mag_bias_estimator 50 Hz · gyro_calibration 50 Hz
wq:rate_ctrl   vehicle_angular_velocity 397.9 Hz  (exists on the FC; NOT bridged to DDS)
```
⛔ **THE GYRO IS NOT THE CAUSE — 3 INDEPENDENT IMUs** from 3 vendors at ~400 Hz. Three MEMS gyros do
not all drift 4000 deg/h together. **Measured**: `CAL_GYRO{0,1,2}_ZOFF` = −0.100 / +0.242 / −0.038
deg/s, three distinct IDs, **all normal-sized — no corrupted calibration.** ⇒ what we measured is the
**EKF's FUSED YAW**, not the gyro. Indoors the gyro only integrates rate; something else moves the
reference under it. ⚠️ I repeatedly wrote "the FC gyro drifts" — wrong wording, wrong blame.

**TWO CANDIDATES, NEITHER TESTED — separate them one at a time, several runs each (intermittent!):**
| suspect | why | test |
|---|---|---|
| **bmm350 mag** | SINGLE, internal, inside a metal body; the ONLY yaw observer indoors; `mag_bias_estimator` actively chases the distortion | `EKF2_MAG_TYPE=5` |
| **GPS aiding** | `vehicle_gps_position` IS publishing at 3.3 Hz over a live UAVCAN bus and `EKF2_GPS_CTRL=7` has EVERY aiding bit on, incl. GPS-velocity yaw — erratic + motion-dependent fits our signature | `EKF2_GPS_CTRL=0` |
⚠️ **"DroneCAN GPS pending hw" is STALE** — something is already feeding `vehicle_gps_position`.
🔑 Plausible but UNEVIDENCED: mag error → EKF yaw error → EKF gyro-bias state absorbs it →
`gyro_calibration` writes a wrong offset → drift persists after the disturbance. Stored offsets are
clean, so this has NOT happened yet; the runtime bias state is not readable this way.
⛔ **NOT on the rover's critical path** (rover heading = camera gyro, 0.00028 deg/s). **It matters for
the DRONE**, which shares this FC and needs a real mag + GPS. Any change here is ROVER-ONLY and must
be reverted before flight.

### ⏭ QUEUED (operator offered 08-09): BRIDGE `vehicle_angular_velocity` TO DDS AND A/B IT
Already present but COMMENTED OUT at `src/modules/uxrce_dds_client/dds_topics.yaml:60` — enabling is
uncommenting two lines, then rebuild + flash `pxlabs-fw`:
```yaml
  - topic: /fmu/out/vehicle_angular_velocity
    type: px4_msgs::msg::VehicleAngularVelocity
```
**Why it is worth it:** 3 fused IMUs @397.9 Hz, and it **DECOUPLES ODOMETRY FROM `rover-camera`** —
the one real weakness of the shipped camera-gyro heading, since the camera degrades silently. It is a
RATE, not an attitude, so it should largely escape the mag problem (the mag corrupts the yaw
REFERENCE, not the rate); it would inherit only the EKF's folded-in bias error.
**Why NOT rushed:** it is a firmware flash on the FC **that also flies the DRONE** ⇒ own session +
verification · we already have a measured 0.00028 deg/s ⇒ improvement, not a fix · **400 Hz costs MORE
CPU than the camera's 195 Hz** and `wheel_odometry` is already at 53.5% — measure before assuming a win.
**The A/B is then ~10 min** with the wall rig (`/tmp/wall_probe.py`, `/tmp/yaw3_probe.py`).

---

## The speed-command fault: the controller is EXONERATED (2026-08-12/13)

**Run:** `tools/speed_command_test.py`, commanded 0.050 m/s, 8.1 s, 3301 moving samples, armed on the
floor with `rover-ekf-bridge` up. Log: `~/speed_cmd_20260812_231229.json`.

### What was measured

| quantity | value |
|---|---|
| throttle | **0.032 mean**, range 0.010–0.109, **saturated 0/3301** |
| feedforward alone (cmd / `RO_MAX_THR_SPEED` 0.6) | 0.083 |
| throttle slope | **−0.0014 /s** (integral windup predicts **+0.0050 /s**) |
| `/odom` speed | 0.111 m/s |
| bumper speed (independent ruler) | **0.140 m/s** ⇒ **2.80× the command** |
| `/odom` error | **under-reads 20.9%** |

### What that kills

* **Integral windup (H1) — DEAD.** No ramp, no saturation. The loop pulled throttle to **2.6× BELOW
  the feedforward**: it saw the overspeed and fought it. ⛔ Do not re-propose `RO_SPEED_I=0`.
* **"The EKF feedback is dead" — DEAD.** `v_xy_valid: true`, `dead_reckoning: false` **with the bridge
  running**. The 08-10 record of `false/true` was taken with the bridge STOPPED — not a contradiction,
  a different configuration. State the bridge's state whenever quoting those flags.
* **My "stick-slip / mechanical floor" story — WITHDRAWN, it was never real.** See below.

⇒ The fault is **DOWNSTREAM of the speed controller**: allocation, ESC, or `erpm_to_ms`. Look there.

### 🔑 The lesson: three agreeing numbers were ONE number wearing three hats

`/odom`, the EKF feedback, and PX4's throttle response are **all** derived from wheel ERPM —
`rover-ekf-bridge` feeds the EKF *from* `/odom`. They agreed (EKF 0.113 vs `/odom` 0.111) and that
agreement **proved nothing**. Only the bumper, which ranges the room, broke the tie.
⛔ **Before quoting agreement as corroboration, ask what the two numbers are DERIVED from.**

### 🔑 `/odom` fakes stick-slip at crawl — I nearly recorded a drivetrain fault that does not exist

`/odom` swung with **CoV 0.30**, dipping to 0.070, and I wrote it up as the rover lurching below its
minimum sustainable speed. The bumper over the same windows: steady **0.13–0.15, CoV 0.124**. The
rover was moving **smoothly**. ERPM is coarsely quantised at low rpm (observed 1, 5, 7, 8, 11, 12 …)
and `/odom` inherits every step. The `H3` detector in the tool now judges lurching **only** against
the bumper, and refuses to judge at all without one.

### The tool also produced a DANGEROUS recommendation, now fixed

It printed *"RO_MAX_THR_SPEED understates true full-throttle speed (≥3.45 m/s), correct it"* on a
~0.6 m/s vehicle. Cause: `implied = speed / throttle` assumes proportionality through the origin,
which collapses at the bottom of the range. Acting on it would have gutted the feedforward.
Now **refused** below `THROTTLE_FLOOR_FOR_IMPLIED` (0.15) or when the bumper shows lurching.
🔑 **A verdict printed by my own tool is not evidence — it is a hypothesis I coded earlier.**

## The bumper ruler, and how the operator's tape earned it (2026-08-13)

The whole conclusion rests on `/scan`, so the operator insisted on verifying it before anything was
written down. **Correct call** — and it took three attempts to get a clean measurement:

1. **Tape to a 14 mm rib** at the base of the wall ⇒ made the calibration look wrong. The `/scan` band
   sits **0.23–0.38 m above the floor** at ~1.5 m and **cannot see a skirting rib**. Tape the wall
   FACE at ~0.30 m up.
2. **The operator standing beside the rover** while taping put a body in the ±20° cone — one 2° bin at
   +18° read **1.751 m against a 2.39 m wall**, dragging the sector minimum *below* the reading from a
   **closer** position. Profiling range-vs-angle exposed it instantly.
3. Clean read: **predicted 2.274 m, measured 2.273 m — 1 mm.** A rival free fit (scale 0.9573,
   overhang 0.377) that matched two closer points equally well was **refuted by 26 mm**.

⇒ `/scan` scale **0.9845** and `front_overhang` **0.337** both stand unchanged, and the ×1.0155
correction used above is correct. 🔑 **Two unknowns need three well-separated ranges — a single
absolute reading can never separate a SCALE error from an OFFSET error.**

### Still open

* **0.25 → ~0.9 m/s is unexplained.** Tonight says nothing about it: at 0.05 the rover sits at the
  bottom of the drivetrain range, a different regime. Needs a long runway, and it is the dangerous one.
* **PX4's speed feedback is circular** — the controller inherits `/odom`'s ~21% under-read and will
  always hold the rover ~21% faster than it believes. This sits in the safety path.
* **The reflex uses the sector MINIMUM**, so it blocks on off-axis objects before the wall ahead
  (a real feature at −18° persists in the profile).
* `tools/preflight_scan_check.py`'s squareness warning is **too tight at range**: a perfectly square
  flat wall at 1.78 m yields 0.114 m of spread from geometry alone (`d·(1/cos20°−1)`), so it cries
  "not square" when nothing is wrong. Compare against the geometric expectation instead. NOT yet fixed.

## The odometry calibration run — operator's method (2026-08-13)

**Operator's proposal**, and it was the right one: drive straight, count wheel revolutions, tape the
start and end distances. `tools/wheel_erpm_log.py` (new) logs all four ESC addresses separately at
full rate. **RC Manual throughout — open loop, nothing armed by the companion, no EKF bridge.**

### Result

| | |
|---|---|
| duration / coverage | 21.97 s, **100%**, 0 gaps, 0 dropped frames |
| travel, taped | **1.931 m** (1.973 → 0.042 m, operator) |
| travel, `/scan` | **1.928 m** — agrees to **3 mm** |
| `/odom` | 1.750 m ⇒ **under-reads 9.2%** |
| **`erpm_to_ms` measured** | **0.004286** at **0.088 m/s** (configured 0.003900) |

The tool's replication of `wheel_odometry_node`'s rule reproduces `/odom` to **0.03%**
(0.003899 vs the configured 0.003900), so the model of the node is right.

### Three things settled

1. **The deadband hypothesis is DEAD.** 50% of per-wheel samples read under the 5-ERPM deadband and
   it costs the integral **0.37%**. Zeroing a wheel that reads 2 removes 2 — the deadband can only
   delete what is *below* 5, so it cannot produce a 20% error. A synthetic test caught this *before*
   the run, which is the only reason it was not written up as the answer.
2. **`tools/odom_scale_measure.py` cannot be used at crawl.** Its deadband is **40, on the COMBINED
   mean**; the node's is **5, PER WHEEL, before averaging**. Its docstring says they match. They do
   not, and it would have eaten **15.27%** of this run.
3. **The real signal defect: 46% of samples read EXACTLY 0 ERPM while the rover was provably moving**
   — 46.2 / 46.7 / 46.4 / 46.4% across the four wheels, side asymmetry 1.3%. Evenly spread, so this
   is the **ESC's low-speed ERPM reporting dropping out**, not a wheel or a wiring fault.

### 🔴 The slip story is now contradicted

| run | speed | `/odom` error |
|---|---|---|
| AutoNav, closed loop | 0.140 m/s | −20.9% |
| RC Manual, open loop | **0.088 m/s** | **−9.2%** |

**Slower produced LESS under-read** — the opposite of "slip rising with speed". The runs differ in
more than speed, so this is not yet a curve. ⛔ **Two points. Do not fit a story.**

### On the revolution count, and a limit I pushed past

4 revolutions were counted, giving 112.8 ERPM-s/rev (recorded: 103.34 = 516.7/5) and 0.4828 m/rev
(geometric π×0.1524 = 0.4788). Both *lean* toward the recorded figures being wrong — but at ±¼ turn
the count carries **±6.25%**, which swamps the 0.8% circumference claim and leaves the 9% encoder
discrepancy merely suggestive. **Neither is proven.**
🔑 **`erpm_to_ms` never needed the revolution count at all** — it is `tape ÷ ERPM-seconds`. The
operator pointed this out after I asked them to tape the wheel; the request was for a *secondary*
question (whether the recorded geometric bound 0.004633 was ever right) and I presented it as the
obvious next step. **Ask what the measurement actually requires before asking for more of it.**

### Fixed on the way

* `tools/manual_drive_log.py` hardcoded `ERPM_TO_MS = 0.000380` against the node's `0.003900` — a
  missing decimal place. **Every m/s that tool ever printed was ~10x too small.**
* The bumper ruler must NOT use the reflex's ±20° minimum: edge objects silently replace the wall
  (measured — a stationary rover read 2.01 m by minimum vs 2.27 m straight ahead). The logger uses a
  **±5° central median** instead. The ±20° minimum remains correct for the *reflex*.

---

## 2026-08-13 (late) — `erpm_to_ms` CLOSED, the speed floor SOLVED, and two of my own claims retracted

### The headline: the scale constant was never the problem

| source | share of the 23.3% crawl under-read |
|---|---|
| `erpm_to_ms` scale error | **~0%** |
| **ESC zero-dropout corrupting `∫ERPM·dt`** | **~24%** |

⛔ **`erpm_to_ms` calibration is CLOSED. Keep 0.003900. Do not re-open it.**

### How the scale was finally pinned — six runs, not one

Hand-rotation runs of ERPM-s per WHEEL revolution, pooled across three sessions and four wheels:

| run | revs | ERPM-s/rev |
|---|---|---|
| orig (5 rev) | 5 | 103.34 |
| 2026-08-13 (4 rev) | 4 | 112.80 |
| front-left addr 11 | 20 | 133.30 |
| rear-left addr 13 | 30 | 132.86 |
| rear-left addr 13 | 30 | 114.46 |
| right-front addr 10 | 20 | 120.71 |
| **pooled** | | **119.58, sd 9.9% ⇒ R = 1.9930** |

**R = 2.000 to within 0.35%.** Wheel **measured 155 mm** — a 6" nominal tyre runs *over* nominal, it
is not worn under. Slip-free constant `π×0.155/120 = 0.004058`; the configured ground-distance
0.003900 therefore implies **4.0% slip**, which is physical. The old 0.004633 forced 18.8%, which
was not.

⛔ **0.004633 was NEVER a valid geometric bound.** *Both* its inputs were wrong in the same
direction (103.34 → 119.58, and 152.4 → 155 mm). The long-standing paradox that "the crawl scale
exceeds a bound slip cannot exceed" was **the bound being wrong**. Do not reconstruct that argument.

### Why R = 2 — read the firmware, don't infer it

`libcanard/canard_driver.c:494` (repo `ArvinVeiyon/PXLABS_BLDC_VESC6_MK5`):

```c
status.rpm = mc_interface_get_rpm() / ((float)conf->si_motor_poles / 2.0);
```

The CAN value is **MOTOR RPM — pole-corrected, NOT gear-corrected.** The motors are **direct-drive
Yalu 6" 24 V 250 W hub motors with no gearbox**, so R must physically be 1. It measures 2 because
`si_motor_poles` holds the pole-**pair** count where the pole **count** belongs — a factor of exactly
2 whatever the real pole count is.

⛔ **`config/rover_odometry.yaml` claimed the ratio was `pole_pairs × gear_ratio`. That model is
wrong** — pole pairs are already divided out in firmware. Corrected in the file.

🔴🔴 **LINKED PAIR: `si_motor_poles` ↔ `erpm_to_ms`.** "Fixing" the pole count in VESC Tool halves the
reported rpm and makes `/odom` read **2× short, silently**, straight into PX4's speed loop via
`rover-ekf-bridge`. Neither may change without the other. Same for swapping an ESC or motor.

✅ **All four ESCs verified on the same scale** — right-front 120.71 sits inside the left-side
spread, so `wheel_odometry_node` averages like with like. **Address map: 10 = right-front (INVERTED,
its raw integral came out negative as `SIGN` predicts) · 11 = front-left · 13 = rear-left ·
12 = right-rear by elimination, not directly confirmed.**

### The 0.14 m/s floor is `RO_SPEED_TH`

`DifferentialSpeedControl.cpp:105` forces the feedback speed to **exactly zero** below
`RO_SPEED_TH` (0.10), so the loop believes it has stopped and re-accelerates. From
`speed_cmd_20260812_231229.json` (3329 samples): EKF speed **pinned 0.096–0.118** across the 0.10
edge; throttle modulating **0.0258 (live) ↔ 0.0531 (zeroed) = 2.06×** switching on that boundary;
solving `thr = FF + P·(sp−v_fb) + I` predicts the live branch to **4 decimals** and the zeroed branch
to **1%**. **You cannot command below `RO_SPEED_TH` — structural, not tuning.**

### 🔴 Two claims I made today and had to retract

1. **"`RO_MAX_THR_SPEED` understates the plant gain 7.4×."** Computed as mean-speed ÷ mean-throttle
   on a **closed-loop** run. In closed loop throttle is a *function of the error*, so that recovers
   the **controller**, not the plant — lag correlations were all `|r| ≤ 0.28` with a −0.27
   simultaneous term and a +0.28 short-lag term that cancel. 🔑 **A plant gain needs an OPEN-LOOP
   sweep. Never fit one to closed-loop data.**
2. **"The hand-spin constant agrees with the configured value to 0.38%."** A **units error**: a hand
   spin measures the **slip-free** constant, the configured value is a **ground-distance** constant.
   They are different quantities and must not be compared directly.

Also retracted en route: a "0.18% reproduction" that was two different revolution counts coinciding;
an implied 0.1816 m wheel diameter; and a "worn 6\" ⇒ D ≤ 152.4 mm" ceiling that the measured 155 mm
falsified — the ceiling had been doing real work in the argument.

### Method notes worth keeping

* ⚠️ **The human revolution count is a ±10–16% ruler.** Two runs on the *same wheel* at a nominal 30
  revs disagreed by 16%. **Never trust one run.** Where possible eliminate counting entirely —
  `erpm_to_ms = taped distance ÷ ERPM-seconds` needs no count at all.
* ⚠️ **Separate genuine stillness from dropout before quoting a zero fraction.** A raw "47.9% zeros"
  was mostly a 10.7 s pause; interpolating across the *real* dropouts moved the integral only 2.4%.
* 🔑 **A blind pre-registered prediction is worth more than a post-hoc fit** — predicting the
  right-front count as 20 (actual 20) is what ruled out the side-asymmetry bug. But note it did
  **not** discriminate R = 2 from R = 2.143; both predicted inside the stated range.

### ⏭ Next on this thread

**The ESC zero-dropout is now the one odometry defect.** New lead: **severity varies per ESC**, not
just with speed — addr 10 dropped only 31.4% zeros while spun *slower* than addr 11/13 at 42–57%,
which a pure low-speed effect predicts backwards. Also queued: read `si_motor_poles` /
`si_gear_ratio` / `si_wheel_diameter` from **all four** ESCs in VESC Tool (confirms R = 2, no vehicle
movement), and an **open-loop throttle sweep** to identify `RO_MAX_THR_SPEED` properly.

## 2026-09-04 — AutoNav resumed: the whole perception stack was DEAD, and the gating tool did not exist
Session was "prepare and continue AutoNav". Nothing about AutoNav itself got tested, because the
bring-up check failed at step one. Both findings are the useful output.

### 1. 🔴 `tools/wall_probe.py` NEVER EXISTED — now written (`ros2_ws` `b52d732`)
`autonav_reference.md` §14 and `setup_manual.md` §E4 have cited it as **the** wheel-independent
ruler since 08-14, and there was no such file and **nothing in git history**. So the 08-16
camera-rotation recovery — the item gating every moving test — was blocked on a tool that was not
there. ⚠️ **Two manuals citing a thing is not evidence the thing exists; `ls` it.**
Written passive (subscribes `/scan` only, never arms): RANSAC + total-least-squares line fit,
deterministic sampling, reports perpendicular distance · wall-normal bearing · fit RMS · inlier
fraction · sector coverage, and judges its own run (coverage < 0.35 reflex gate, RMS > 10 mm,
sd > 5 mm, > 2° off square).
**First run, 40/40 scans fitted:** `1.6260 m sd 5.0 mm · bearing −7.88° · RMS 5.4 mm ·
coverage 0.80 · inliers 0.30` ⇒ correctly reporting **the rover is NOT parked square** (it is not).
⏭ **THE ACTUAL NEXT ACTION: operator parks the rover SQUARE and CLOSE to a flat featureless wall,
then re-run.** Everything camera-referenced waits on that.

### 2. 🔴 THE CAMERA HAD BEEN DEAD FOR HOURS AND EVERY UNIT READ `active`
Measured before touching anything: **depth 0.0 Hz · colour 0.0 Hz · `/scan` 0.0 Hz**, after ~23 h
of uptime. `systemctl is-active` said `active` for all six rover units — the documented lie (D2).
🔑 **The tell in the journal:** `Depth registration is on but this frameset was not aligned (no
usable align target); dropping its depth image and point cloud` — that guard fires when the
frameset arrives **without a usable colour frame**, so a dead COLOUR stream silently kills depth,
the cloud, `/scan`, `/scan_3d` and localization together.
🔑🔑 **RESTARTING `rover-camera` IS NOT ENOUGH — and this is the part that will bite again.**
After the camera restart: depth **26.9 Hz**, colour **20.7 Hz**, alignment OK — but **`/scan` was
still 0.0 Hz** and `/odom` still silent. The downstream nodes do not recover on their own.
**Restart order that actually worked:** `rover-camera` → `rover-scan` + `rover-scan-3d` →
`rover-odometry`. Result: `/scan` **25.9 Hz** · `/scan_3d` **28.8 Hz** · `/odom` **49.9 Hz**.
⚠️ `rover-odometry` matters most: while the camera was dead it logged **"camera gyro unavailable —
falling back to FC attitude"**, i.e. it had quietly demoted itself to the heading source known to
invent 23° in 21 s. After the restart: **`heading source: CAMERA GYRO`, bias +0.7303 °/s** — which
independently corroborates §5's +0.72 °/s.

### 3. Smaller facts measured today
- **`UAVCAN_ENABLE = 3`, not 0** — MEMORY.md's "(silent again while `UAVCAN_ENABLE=0`)" was wrong.
  `/odom` was silent because the NODE needed restarting, not because of CAN.
- `/scan` frame is **`camera_depth_frame`**, spans **−46.1..+46.7°** over **640 rays**;
  276 rays fall in the ±20° reflex sector.
- New warning worth watching: `camera stamp clock runs at 0.9835x wall clock — every integrated
  angle is scaled by this factor` (21:40, while the camera was dying). §5 records the camera clock
  at **+0.0022%**, so 0.9835 is ~1.65% out and appeared only as the camera failed. **If it recurs
  on a HEALTHY camera it invalidates every integrated gyro angle — check it before the wall run.**
- Vehicle was **DISARMED** (`arming_state 1`, `nav_state 4`, no failsafe) throughout. Nothing moved.
- `ros2 topic list` returned an INCOMPLETE list (no `/scan`, `/odom`, `/tf`) while
  `count_publishers()` found publishers on all of them — the CLI-is-an-unreliable-ruler trap again.
  ⚠️ `/proc/<pid>/io` is ALSO a weak ruler here: DDS shared-memory writes do not move `wchar`.

✅ **THAT RESUME-HERE IS DONE — CLOSED 2026-09-11** (park square → `wall_probe.py` → roll corrected
in the launch TF → `front_overhang` + `/scan` scale re-verified on tape to 4.6 mm). See the
**2026-09-11 G0 CLOSED** block at the top of this file. ⏭ **Next is G2 (motion truth), NOT
localization** — `autonomy_plan.md` §5: M2 needs no map and no localization, so G1 gates only M3.
⛔ **The "no moving test before geometry is verified" bar is now MET.**

---

# 🟢🟢 2026-09-17/18 — **PHASE 0: NAV2 RAN FOR THE FIRST TIME. IT PASSES, AND IT FOUND TWO BLOCKERS.**

`rover_nav2` was written 2026-08-01 and had **never been launched**. It has now. Rover DISARMED
throughout (`arming_state 1`, `nav_state 0`); nothing moved at any point.

## ✅ THE CHAIN IS REAL — end to end, in the corridor
```
ARMING        arming_state=1 (disarmed), nav_state=0
SCAN          3.77 m clear ahead (+-15 deg)
COSTMAP       1.0m:0  1.5m:0  2.0m:0   free along heading
GOAL          accepted, planner returned 81 poses
/cmd_vel_nav  151 msgs, vx steady 0.250 m/s
/cmd_vel      160 msgs, vx 0.050 -> 0.100 -> 0.150 -> 0.200 -> 0.250
```
🔑🔑 **THE SMOOTHER RAMPS THE FIRST COMMAND.** The first `/cmd_vel` an armed rover would see is
**0.05 m/s over five messages**, not a step to 0.25. That is the property that makes an armed
Phase 1 defensible. Peak 0.25 m/s against a 4.93 m/s stick cap; yaw stayed -0.026..0.237 rad/s.
🔑 Costmap reading 45/41 at 0.0/0.5 m is the rover's OWN footprint + inflation (body extends
0.345 m forward of `base_link`) — **not** self-marking. The 92-deg self-marking fear did not happen.

## 🔴 BLOCKER 1 — `bt_navigator` COULD NOT ACTIVATE AT ALL (fixed)
Nav2's default tree `navigate_to_pose_w_replanning_and_recovery.xml` calls the **`spin`** action, and
`behavior_plugins` is `["wait"]` **on purpose** here (spin/backup drive through unobserved space).
No spin server ⇒ `Exception when loading BT: Action server spin not available` ⇒ bt_navigator fails
to ACTIVATE ⇒ **the lifecycle manager aborts the ENTIRE bringup.** Nothing else in the stack is at
fault and the error names the XML, not the missing plugin — easy to misread.
✅ **FIX, in `src/rover_nav2/config/nav2_forward.yaml` under `bt_navigator`:**
`default_nav_to_pose_bt_xml: "/opt/ros/jazzy/share/nav2_bt_navigator/behavior_trees/navigate_w_replanning_time.xml"`
(ComputePathToPose + FollowPath on a replan timer, **zero recovery actions**).
⚠️⚠️ **SOURCE ONLY — `rover_nav2` HAS NOT BEEN `colcon build`-ED.** The installed share copy still
lacks it. Tonight's runs used `params_file:=<source path>`. **Build it or keep passing params_file.**

## 🔴🔴 BLOCKER 2 — WITH THE VOXEL LAYER ON, NAV2 COMMANDS A SPIN. THIS WOULD HAVE SPUN AN ARMED ROVER.
Same corridor, same 2.0 m goal, voxel_layer re-enabled:
```
accepted: True   plan: 424 poses (vs 81 with voxel off -- a long detour)
/cmd_vel_nav  vx 0.000   wz -0.500 SUSTAINED (max_vel_theta)
/cmd_vel      vx 0.000   wz -0.500 .. -0.100
```
while `/scan` reported **nothing closer than 3.79 m**. The planner believes the direct path is
blocked, detours, and DWB — with no admissible forward trajectory — falls back to **rotating in
place at max yaw rate**. ⛔⛔ **DO NOT ARM WITH `voxel_layer` ENABLED.** Both layers left disabled
as a **runtime param override**; the YAML on disk still has them enabled.

### 🔬 What the voxel layer is actually doing — PARTLY diagnosed, DO NOT claim it is solved
✅ **Floor tilt is REAL and measured** (81,688 pts, 6 clouds, `|lat|<0.30`, base_link):
| band | n | floor z |
|---|---|---|
| 0.5-1.0 m | 144 | **-0.027** |
| 1.5-2.0 m | 625 | **+0.060** (whole band 0.058-0.091 = the floor sheet) |
⇒ **~8.7 cm rise per metre of range ≈ 5 deg residual tilt**, far more than the 1.44 deg the mount
probe measured. Extrapolated it crosses `min_obstacle_height: 0.12` at **~2.4 m**.
🔴🔴 **BUT THAT DOES NOT EXPLAIN THE SYMPTOM — I CLAIMED IT DID AND WAS WRONG.** The spurious mark
in the corridor sits at **0.5 m**, where the floor measures **-0.027 m**, nowhere near 0.12.
**The height threshold is A problem, not THE problem. A second marking cause is UNIDENTIFIED.**
⛔ **Do not tune `min_obstacle_height` to make the symptom hide** — publish the voxel grid
(`publish_voxel_map: True`) and compare marked cells against the raw cloud first.
🔴 **`/camera/depth/points` is published in `camera_color_optical_frame`, NOT
`camera_depth_optical_frame`** — depth_registration aligns it to colour. The yaml comment is STALE.
`sensor_frame: ""` means nav2 uses the message frame, so this is not itself a fault, but ⚠️ a TF
lookup on the wrong frame name throws `LookupException`, and the buffer needs ~10 s of spin first.

## 🔴 BLOCKER 3, INDEPENDENT OF THE COSTMAP — **DWB WILL SPIN IN PLACE WHEN IT CANNOT GO FORWARD**
The config removes `spin` as a **recovery behaviour**; nothing stops the **controller** from
commanding rotation, and this rover has **no rear or side sensing**. ⏭ Cap or forbid in-place
rotation in DWB so "no forward path" yields a **stop**, not a spin. **Close this before ANY armed run.**

## 🔴 PHASE 1 WAS SET UP AND THEN STOPPED — THE PREFLIGHT GATE FAILED
`tools/preflight_scan_check.py` at the corridor start position:
```
217 scans (21.7 Hz) | sector coverage 67.0% | scans with EMPTY sector: 217  (ALL of them)
!! NOTHING VALID SEEN IN THE FORWARD SECTOR IN ANY SCAN -- it will NOT stop you.
```
🔑 **NOT a fault — GEOMETRY.** The reflex filters to a 0.275 m-wide corridor, which spans ~±4 deg at
3 m, and the nearest thing ahead was **3.79 m**, past where `/scan` tracks. **A silent reflex there
means BLIND, not CLEAR.** ⛔ Refused to arm on that reading: flat-scan-only was chosen *because* the
reflex is the remaining protection, so a blind reflex removes the whole basis for the choice.
⏭ **THE FIX IS PHYSICAL:** matte surface at **2.5-3.0 m**, goal **1.5 m** ⇒ bumper ends ~1.1 m short,
reflex live from the start. The window is narrow by construction: reflex sees ≤3 m, needs 0.69 m to
stop. ⚠️ Glossy/dark surfaces return no depth — that is what the tool's "re-aim at a matte surface"
line means.

## 🔑 ODOM DOES **NOT** DRIFT AT STANDSTILL — MEASURED
**0.0000 m over 10.0 s**, `|vx|` max 0.0000, while stationary and disarmed. The `x≈71 m` odom
position is **accumulated from earlier sessions**, harmless with rolling windows in `odom`.
⚠️ Nuance against the standing "`/odom` DRIFTS AT STANDSTILL" note: it did not tonight.

## ⏭ RESUME HERE (2026-09-18)
1. **Reposition** per the preflight fix above, re-run `preflight_scan_check.py`, **go only if the
   forward sector is populated.**
2. **Phase 1** — armed, Nav2 drives a straight **1.5 m** goal, flat scan only, voxel OFF, hand on
   **ch12**. Standing gates: start `rover-ekf-bridge` BEFORE (floor only) and **STOP IT AFTER** ·
   `eph` vs 5.0 m `COM_POS_FS_EPH` · registration proved by the **LOG LINE**, never a message rate ·
   `COM_DISARM_PRFLT` 10 s auto-disarms an idle armed rover, so send the goal promptly.
3. Then Phase 2 = T3 (one offset obstacle).
⚠️ **`RO_DECEL_LIM` 5 stop is STILL UNMEASURED** and wheel RPM cannot measure it. At 0.25 m/s the
margins are generous, but it is an open number, not a verified one.

# 🔴🔴 2026-09-19 — **THE YAW AXIS IS DEAD IN AUTONAV, AND G2 IS WHY.** Desk session, nothing moved.

Scope set with the operator: **finish M2 (T3 → T4 → T5), camera-only.** ⛔ **No LiDAR work** — see
the verdict at the foot of this entry.

## The finding, confirmed on the live FC (not from docs)
`FF = sp × track/2 × RO_YAW_RATE_CORR / RO_MAX_THR_SPEED` ⇒ **the FF gain is the RATIO
`CORR / RO_MAX_THR_SPEED`.** Read off the FC 09-19: `CORR` **1.8** · `RO_MAX_THR_SPEED` **4.93** ·
`RO_YAW_RATE_P` **0.08** · `RO_YAW_RATE_I` **0.0** · `RO_YAW_RATE_LIM` **85.9 deg/s** ·
`RD_WHEEL_TRACK` **0.31**.

| | divisor | CORR | ratio | FF at 1.2 rad/s | rotates? |
|---|---|---|---|---|---|
| validated 08-02 | 0.60 | 1.8 | **3.0000** | 0.558 | ✅ clears the 0.45 breakaway |
| **live today** | **4.93** | 1.8 | **0.3651** | **0.068** | ❌ **8.22× short** |

🔑 **G2 moved the divisor on 09-13 and nothing touched `CORR`.** The plant has a **friction
deadband** — `steer < ~0.45` ⇒ NO rotation; above it `yaw ≈ 7.6 × (steer − 0.40)` ⇒ **minimum
achievable yaw ≈ 0.67 rad/s**. Even with P at full error the output reaches only ~0.20.
⇒ **THE ROVER CANNOT ROTATE IN AUTONAV.** 🔑 **T2 never caught it because T2 drives in a straight
line** — T3 is the first test that turns.

⏭ **OPERATOR DECISION 09-19: `RO_YAW_RATE_CORR` 1.8 → 14.8, TO BE WRITTEN AT THE NEXT FLOOR SESSION**
(not at the desk — operator's call, so the change and its first test share a sitting). 14.8/4.93 =
**3.0020**, the 08-02 ratio restored to 0.07%; the param's max is **10000**, so it is well in bounds.
⛔⛔ **NEVER "fix" this by restoring `RO_YAW_RATE_I`** — that is the windup path behind the 21×
runaway. With I = 0 it is bounded: worst case at the executor's 1.0 rad/s clamp is 0.545 steer ⇒
**~1.10 rad/s achieved.**
🔑 **THE GENERAL RULE, worth more than this instance: when a SHARED DIVISOR moves, check every RATIO
it appears in, not the gain next to it.** `RO_MAX_THR_SPEED` divides the speed loop AND the yaw loop.

## Second consequence of the same root cause — ⚠️ turn-away-while-blocked is dead
`autonav_mode` caps yaw to `collision.blocked_yaw_rate` = **0.3 rad/s** while blocked (mode.hpp
kBlockedYawRate), which is **below the 0.67 rad/s floor** ⇒ "enough authority to turn away" is no
longer true; it cannot turn at all while blocked. ✅ **Left as-is deliberately** — blind rotation is
the manoeuvre this whole config forbids, so a dead turn-away is the safe failure. **Documented, not
changed.** The node runs bare from systemd with compiled defaults (no yaml), so changing it means
`--ros-args -p collision.blocked_yaw_rate:=…` or an edit.

## ✅ SHIPPED THIS SESSION — `nav2_forward_flat.yaml`, the armed-run config
`src/rover_nav2/config/nav2_forward_flat.yaml`, built and installed. Six functional changes vs
`nav2_forward.yaml`, verified by a comment-stripped diff:
1. **`voxel_layer` OUT of BOTH costmap plugin lists** (its param blocks are left in place so G4 can
   re-enable by name). ⛔⛔ **NEVER ARM WITH IT ENABLED** — 09-17 it produced a sustained max-rate spin.
2. **`PreferForward` + `Twirling` critics added** (scales 50.0 / 20.0, first-cut) — blocker 3. Both
   are stock `dwb_critics` plugins, already built here; **no code change.**
3. **`max_vel_theta` 0.5 → 1.0** and the velocity smoother's theta with it — **they must move
   together.** 🔑 **1.0, not higher, because `autonav_mode` clamps |yaw| to `kMaxYawRate` = 1.0**;
   anything above that is clipped downstream and the config would be lying.
4. `nav2_forward.yaml` keeps a ⛔ header: it is the 3D/G4 config, **not for armed runs.**
🔑 **No launch change needed** — `nav2_forward.launch.py` already takes `params_file:=`.
⚠️ Also corrected in-file: the old comment claiming `RO_YAW_RATE_P` is 0.05 and the runaway is
"still under investigation". Both stale — P reads 0.08 and the runaway was diagnosed as windup.

## ⏭ RESUME HERE — next floor session, in this order
1. **Write `RO_YAW_RATE_CORR` 14.8 DISARMED**, read it back. ⛔ leave `RO_YAW_RATE_I` at 0.
2. **Reposition per the 09-18 fix** — matte surface **2.5-3.0 m**, goal **1.5 m** — and re-run
   `tools/preflight_scan_check.py`. **Go only if the forward sector is populated**; an empty sector
   in every scan is a refusal. 🔑 a silent reflex beyond ~3 m is **BLIND, not clear**.
3. **Phase 1** — armed, Nav2 straight 1.5 m goal, launched with **`nav2_forward_flat.yaml`**.
   Eyeball `/cmd_vel` **before arming**. Expect ~1.5 m arrival, lateral ~0.03 m, reflex silent,
   `angular.z` ≈ 0 throughout.
4. **T3** — one offset obstacle. Pass = routes around, **reflex stays silent**. ⚠️ first time the
   four speed loops must disagree on purpose; read `turn_asym_20260914.csv` / `turn_lr_20260914.csv`
   first. If yaw still will not break out, **stop and re-measure with `tools/yaw_response_log.py`** —
   ⛔ do not raise gains on the floor.
Standing gates unchanged: bridge before / **stop after** · `eph` vs 5.0 m, ~45-60 min · registration
proved by the **LOG LINE** · hand on **ch12**.

## 🔑 THE LIDAR VERDICT (operator asked 09-19) — **NOT REQUIRED, and not a blocker for M2 or M3**
⛔ **Stay camera-only.** `autonomy_plan.md` §2: the sensors are **complementary, not redundant** — a
2D slice passes UNDER table tops and OVER low boxes, cables and thresholds, and cannot see
drop-offs; for the forward avoidance that IS M2, the depth camera is the better sensor. §2.2
**withdrew** "mapping needs the STL-19" (true only for `slam_toolbox`, which needs wide FOV) ⇒ **M3
is not hardware-blocked either** — config + CPU. `indoor_mapping_plan.md` §113: **the STL-19 is
assigned to the DRONE; the rover is camera-only** — a decision on record, not waiting for parts.
⚠️ It would not be quick anyway: `ldlidar_stl_ros2` is **no longer in `ros2_ws/src`** (patch at
`codex-work/ldlidar_stl_local_edits_20260417.patch`) and **`slam_toolbox` is NOT installed here.**
🔑 Accepted permanent costs: **no rear/side coverage · a spin can never be cleared from a scan ·
~3 m usable range.** ⏭ The ONLY place a LiDAR would change the answer: **if M3 localization stays
dead**, 2D lidar + `slam_toolbox` is the cheap CPU-light alternative to reviving RTAB-Map. M3
decision, deferred.

# 🟢🟢 2026-09-19 — **FLOOR SESSION: PHASE 1 PASSED (n=2, TAPE), AND A SIGN BUG THAT WOULD HAVE BROKEN T3**

Scope: finish M2, **camera-only** (⛔ no LiDAR — verdict in the 09-19 desk entry above).

## ✅✅ PHASE 1 PASSED — NAV2 DROVE AN ARMED ROVER, TWICE
`nav_state=23`, goal completed, **reflex silent throughout** (the only BLOCK lines are node startup
before `/scan` arrived). Config: **`nav2_forward_flat.yaml`** (voxel OFF + `PreferForward`/`Twirling`).

| | run 1 | run 2 |
|---|---|---|
| along-track `/odom` | 1.293 m | 1.277 m |
| lateral | +0.017 m | +0.013 m |
| `angular.z` max | 0.053 | 0.053 |
| in-place rotation samples | **0** | **0** |

🔑 **TAPE-ADJUDICATED: 1.380 m against a 1.5 m goal ⇒ true error −0.120 m, INSIDE the ±0.20 criterion.**
✅ **Blocker 3 (DWB spins when it cannot go forward) is CLOSED for straight-line work** — a *disarmed*
probe with `/odom` frozen (the exact 09-17 condition) commanded **zero rotation for 21 s** and wound
down to zero instead of spinning. The two stock critics do the job; no code was needed.
📏 **NEW ODOM POINT: 0.925 at a MEAN speed of 0.060 m/s** (odom 1.277 vs tape 1.380 = under-read 7.5%).
Extends the speed curve below every prior point (0.946@0.15 · 1.000@0.25 · 1.030@0.75).
🔑 **A Nav2 goal spends most of its time in the ramp, so its MEAN speed is far below `max_vel_x`** —
quote the mean, not the cap, when picking which odom ratio applies.

## 🔴🔴 THE SIGN BUG — FOUND, FIXED, VERIFIED ON THE FLOOR
**`mode.hpp:158` passed `/cmd_vel` `angular.z` STRAIGHT THROUGH to the PX4 setpoint.** ROS REP-103 is
**FLU** (+z = CCW = **LEFT**); PX4 is **FRD** (+ = CW = **RIGHT**). The conversion is a negation and it
was missing ⇒ **every commanded turn went the WRONG WAY.**
🔑 **Caught by the operator's eye, not by a log:** commanded +0.4 rad/s, he reported "Right".
⛔ **T3 WOULD HAVE STEERED INTO THE OBSTACLE IT WAS ROUTING AROUND** — and the reflex only looks
straight ahead, so it would not reliably have saved it. It would have read as a planner failure.
✅ **FIXED + BUILT + VERIFIED 09-19:** negate on ingest. Verification arc (+0.4 rad/s, 0.25 m/s, 2 s):
FC gyro now **−0.102 → −0.221** where the same command previously gave **+0.106 → +0.160**, and the
wheel differential inverted (right side fast = left turn). Operator confirmed visually.
⚠️ **Straight-line results are unaffected** — Phase 1 never exercised the sign.

## 🔑 YAW: THE 08-02 CURVE DID NOT SURVIVE THE RPM MIGRATION
`RO_YAW_RATE_CORR` **1.8 → 14.8 → 7.4** this session. The 14.8 write restored the 08-02 FF *ratio*
(`CORR/RO_MAX_THR_SPEED` = 3.00) — **correct arithmetic, dead premise**: the 08-02 plant (friction
deadband below steer 0.45, min yaw 0.67 rad/s) was measured in **TORQUE mode**, and G2 moved all four
ESCs to **RPM mode** on 09-13. At 14.8 the axis over-drove ~2× (0.4 cmd → 0.828 achieved; 1.0 → 1.93,
tripping the 2.0 rad/s guard). **7.4 is in force.**
⛔⛔ **`RO_YAW_RATE_I` STAYS 0** — the 21× windup path. Bounded by design with I=0.
🔑🔑 **EVERY YAW NUMBER MEASURED BEFORE 09-13 IS SUSPECT. Re-measure the plant in MANUAL
(`tools/yaw_response_log.py`) — it bypasses the rate controller AND costs no eph budget.**

## 🔑 HALL FEEDBACK — OPERATOR'S CORRECTION, AND IT RETIRES A "FAULT"
⛔ **ZERO RPM FROM A STATIONARY HUB MOTOR IS EXPECTED, NOT A FAULT SIGNATURE.** These are
hall-sensored hubs: if the rotor never breaks away there is nothing for the halls to count, so the
speed loop servos on a measurement that cannot change and simply pushes current. That is what the
0.4 rad/s pivot captured (RR **0 rpm at up to 18.8 A for 3.5 s**) — a test-design artifact, not a
diagnosis. 🔑 **LOW YAW COMMANDS ARE STRUCTURALLY UNSERVOABLE FROM REST ON THIS DRIVETRAIN.**
⇒ ⛔ **NO MORE PIVOTS FROM REST.** Turn while ROLLING: in an arc the halls are already transitioning
and yaw is a small *difference* between two live wheel speeds.
✅ **PROVEN: RR is LIVE in an arc** (26 rpm, later 59→84 rpm at 12-15 A) where it was pinned at 0 in
the pivot. ⇒ **T3 is not necessarily gated on the motors.**

## 🔧 MOTORS — OPERATOR DECISION: REPLACE THE THREE OLD ONES (RF, FL, RR)
His evidence, which beats mine: **RL was recently replaced and outperforms the rest**, and RL/RR sit
on the SAME axle under the SAME load — new turned, old stalled. ⚠️ **The rear also carries more
stress because the suspension sits LOWER at the rear (suspension variation).** ⇒ treat ride height as
its own item: new motors will still carry the extra rear load, they will just cope.
🔑 My "rear-vs-front load, so the motors are innocent" reading was half right and the wrong
conclusion. ⛔ Not re-litigated.

## ⬜ OPEN, AND THE REAL HEADLINE FOR NEXT SESSION
🔴 **YAW RESPONSE IS NOT REPRODUCIBLE RUN-TO-RUN AT THE SAME COMMAND.** Same `CORR` 7.4, single steps
from rest: **0.4 → weak · 0.7 → STRONG (0.927 rad/s, all four live) · 1.0 → weak (0.156)**. The 1.0
run drew barely above idle (9.9→13 A vs 18.8 A in the 0.4 run) ⇒ **the setpoint reaching the ESCs was
small, they were not fighting a load.** ⛔ NOT heat: ESC temps **RF 44.4 · FL 43.1 · RR 47.1 · RL 45.9 °C**,
pack 24.7-24.9 V — a VESC does not derate until ~85 °C. **UNEXPLAINED. Do not tune on top of it.**
⬜ Arc yaw also under-delivers: **0.16-0.22 rad/s achieved vs 0.4 commanded (~40-55%)**, with the
RIGHT side (RF+RR, both old) under-running its commanded speed while the left side tracks.

## ⏭ RESUME HERE (2026-09-19)
1. ⛔ **No pivots from rest.** Arcs only.
2. **Re-measure the yaw plant in MANUAL** (`yaw_response_log.py`) — no eph cost, bypasses the rate
   controller, replaces every pre-09-13 yaw number.
3. **Then T3** (the sign fix makes it meaningful) — or the straight-line work first: the **standoff
   speed ladder closes the LAST open safety number** (≥300 mm above ~0.11 m/s) and needs no turning.
4. ⚠️ **T4 would pass too easily today** — "does not spin" is trivially satisfied by an axis that
   cannot pivot. **Mark it a WEAK PASS if run before yaw is sound.**

## 🔑 OPERATIONS LEARNED TODAY — these cost us four runs
🔴🔴 **AFTER `COM_DISARM_PRFLT` AUTO-DISARMS (10 s idle), ch5 STAYING UP WILL NOT RE-ARM. PX4 NEEDS A
LOW→HIGH TRANSITION — CYCLE ch5 DOWN THEN UP.** The switch read 1988 (up) while the FC read disarmed.
🔴 **`eph` LIVES ON `/fmu/out/vehicle_local_position_v1`** — the UNVERSIONED name does not exist here
and reads as a dead topic. Same trap as `vehicle_status_v1`.
🔑 **eph SEQUENCING IS EVERYTHING:** FC booted 11:41, bridge started 11:51 ⇒ **eph 238 m**. Rebooted
and started the bridge immediately ⇒ **eph 0.202 m**. Velocity-only aiding bounds velocity error, NOT
position, so **eph does NOT converge back down — reboot and start the bridge together.**
⚠️ Budget observed: 0.202 m at 11:55 → 3.44 m by 13:15 (~80 min).
🔑 **The reflex/preflight corridor test is `|y| <= 0.275 m` (mode.hpp `kCorridorHalfWidth`), NOT a bare
±20° sector** — at 5 m that is ±3°. A cone without the corridor test reads objects BESIDE the path
(3.2 m vs the true 4.9 m) and produced a bogus "3× odometry disagreement" this session.
⛔ `pkill -f <pattern>` self-kills (exit 144) — it is in the index and I did it anyway.

## 📐 2026-09-19 (late) — **THE STEER→YAW PLANT CURVE, MEASURED IN MANUAL AND IN RPM MODE**

Method: passive full-rate log (`yawplant.py`, commands nothing) while the operator drove **ARCS** in
Manual, both directions plus reverse. 🔑 **Arcs, not pivots** — rolling wheels mean live hall feedback,
so there are usable points at low steer instead of a stalled wheel and no measurement.
Point = a window where `|steer|` is stable within 0.05 for ≥0.8 s; yaw averaged over the **settled
half** (averaging the whole hold measures acceleration, not steady state). 10 holds survived.

🔑 **yaw ≈ 2.9 rad/s per unit of steering setpoint**, consistent both ways — **LEFT 2.79, RIGHT 3.03**
(⇒ no large left/right asymmetry in *output*, even though RR contributes almost nothing). Full steer
≈ 3 rad/s, which matches the ±3.5 rad/s seen at full stick.
📏 **IMPLIES `RO_YAW_RATE_CORR` ≈ 11 for 1:1 tracking** (FF steer = sp × track/2 × CORR /
`RO_MAX_THR_SPEED`; 2.9 × 0.155 × CORR/4.93 = 1 ⇒ CORR ≈ 11). In force today: **7.4**.
⛔⛔ **DO NOT APPLY 11 YET.** The curve was measured with **RR demagnetised and contributing almost
nothing** — it describes a three-and-a-bit-wheel rover. **Fix the motors, re-measure, then set CORR**,
or the tune bakes in a dead corner and has to be redone.

🔑🔑 **THE PLANT IS STRONG — THE PROBLEM IS THE AUTONAV RATE PATH.** Manual reaches **±3.5 rad/s**;
AutoNav could not reliably produce 1 rad/s minutes earlier, and its results were not reproducible at
the same command. Motors, traction and ESCs are therefore NOT the limiter for yaw. ⇒ the hunt is in
`RoverSpeedRateSetpoint` → `DifferentialRateControl` → allocation.
🔴 **`/odom` YAW IS UNUSABLE AT SPEED** — read **−21.4 rad/s** where the FC gyro read **−3.5** (~6×).
⇒ **use `sensor_combined` for yaw truth**, never `/odom`. (`yaw_response_log.py` already flags it.)
⚠️ **`yaw_response_log.py` burst detection is too coarse for a curve** — 0.8 s of quiet ends a burst,
so holds merge (one was 34.6 s spanning both directions). It gives per-burst peaks, not steady
points. **Use the passive full-rate logger + `plantcurve.py` instead.**
⚠️ Its hardcoded `RO_MAX_THR_SPEED` was **3.0**, stale twice over — corrected to **4.93** 09-19.

# 🔴 2026-09-19 (evening) — **T3 FAILED, 3 ARMED ATTEMPTS. THE FAULT IS DWB, AND IT IS NOT YET FIXED.**

⛔ **T3 DID NOT PASS. The goal was never reached.** Three armed runs, all ended `GOAL ABORTED by Nav2`
(`Failed to make progress`), rover stopping at **0.89 / 0.93 / 0.93 m** every time.

## ✅ WHAT IS PROVEN GOOD — ruled out one by one, all from DISARMED probes (no motion, no eph cost)
1. **Perception → costmap WORKS.** The obstacle reads cost **92-100 in BOTH** costmaps at 1.5-2.2 m.
2. **The global planner WORKS.** `/plan` = 104 poses with **0.80 m of lateral deviation — it curves
   around the obstacle.**
3. **The curve REACHES DWB.** `/transformed_global_plan` carries lateral −0.71 m.
4. 🔴 **DWB CHOOSES A DEAD-STRAIGHT TRAJECTORY.** `/local_plan` lateral = **0.000**, and it avoids the
   obstacle by **SLOWING DOWN instead of turning** — chosen speed falls to ~0.14 m/s. The armed runs
   show the same: `linear.x` max 0.250 but **mean 0.116**.
⇒ **The rover creeps straight until the reflex blocks it at 0.69 m raw, cannot progress, and the goal
aborts ~20 s later.** ⛔ **The yaw axis was NEVER COMMANDED — `angular.z` was exactly 0.000 across all
three runs (650+ messages). T3 told us nothing about yaw, the motors or the tune.**

## 🔴🔴 THE GOTCHA THAT INVALIDATED TWO OF MY OWN EXPERIMENTS — REMEMBER THIS
⛔⛔ **DWB READS `sim_time` AND EVERY CRITIC `scale` AT INITIALISE. A RUNTIME `ros2 param set` RETURNS
"successful" AND READS BACK THE NEW VALUE WHILE THE RUNNING CRITIC KEEPS THE OLD ONE.**
🔑 **Only a YAML edit + node restart actually applies them.** I "exonerated" `Twirling`/`PreferForward`
by setting them live and seeing no change — **that test was meaningless.** They are NOT exonerated.
⚠️ Same trap for `BaseObstacle.scale`. ⛔ **Never conclude anything from a live-set DWB param again.**

## ⬜ WHAT WAS TRIED (config + restart, all disarmed)
| change | result |
|---|---|
| `sim_time` 2.0 → 4.0 | horizon 0.46 → **0.88 m**, trajectory still **dead straight** |
| `sim_time` → 6.0 | trajectory got **SHORTER (0.82 m)** — DWB picked a slower speed instead |
| `BaseObstacle.scale` 0.02 → 1.0 | no change (⚠️ set live, so possibly never applied) |
| softened critics in YAML + restart | **controller_server crashed / lifecycle failure** — reverted |
✅ **CONFIG REVERTED to the Phase-1-validated values** (`sim_time` 2.0 · `BaseObstacle` 0.02 ·
`PreferForward` 50 · `Twirling` 20) and rebuilt. The investigation notes are kept as comments in
`nav2_forward_flat.yaml`. ⚠️ My repeated kill/relaunch cycles left the stack broken once — kill ALL
of controller/planner/bt/smoother/lifecycle together, then relaunch.

## ⏭ THE REAL CANDIDATES FOR NEXT SESSION, in order
1. 🔑🔑 **REPLACE DWB WITH REGULATED PURE PURSUIT (`nav2_regulated_pure_pursuit_controller`).** DWB
   *samples* velocities and scores them; RPP *follows the path geometrically* with a lookahead point.
   For a differential rover tracking a known good plan it is the better-suited controller, it has no
   sampling grid to mis-tune, and it removes every critic-weighting question at once. **This is the
   one I would try first.**
2. Re-test the critic weights **properly** (YAML + restart, one at a time) — they were never
   actually tested.
3. ⛔⛔ **RETRACTED SAME DAY — "this rover cannot make GENTLE turns" WAS WRONG.** I took the
   **0.67 rad/s STANDSTILL BREAKAWAY** and generalised it into a limit on curvature while moving.
   It does not follow, and **this session's own arc captures refute it**: 0.25 m/s with 0.4 rad/s
   commanded achieved **0.160 rad/s (r ≈ 1.56 m)** and **0.221 rad/s (r ≈ 1.14 m)** — both far below
   0.67, both smooth. 🔑 **Rolling, yaw is only a small speed DIFFERENCE between the sides; there is
   no breakaway to overcome.** The breakaway figure applies to PIVOTS FROM REST and nowhere else.
   ⛔ **Do not derive a moving constraint from a standstill measurement.**
   🔑 **And ask the operator before asserting a vehicle limit — he drives it and said so directly.**
   ⇒ **Gentle path-following IS within this rover's capability**, which strengthens the case that
   DWB's straight-line choice is a controller problem, not a vehicle one.

## 📐 ARTIFACT — the scan-derived plan view of this setup
`https://claude.ai/code/artifact/a715d45d-d10c-4958-8469-c2ce3c996842` — 473 live points, corridor,
inflation circle, and which side is plannable. 🔴 **It also records a correction: POSITIVE scan
angles are LEFT (REP-103). I had left/right inverted in several messages before the operator caught
it.** ⚠️ Rebuild it from a fresh scan if the rover moves — it is a snapshot, not live.

# ✅✅ 2026-09-19 (late) — **FOUND IT: MY OWN CRITICS WERE FORBIDDING EVERY TURN.**

🔑🔑 **THE OPERATOR'S CALL FOUND IT — "try one test, lift your constraint."** I had spent the evening
hunting the fault in the horizon, the costmaps, the planner and the vehicle. It was the two critics
**I added that same morning** for blocker 3.

| `/local_plan` lateral | `cmd_vel_nav` `angular.z` | |
|---|---|---|
| 0.000 (dead straight) | **0.000** | with `PreferForward` 50 + `Twirling` 20 |
| **−0.11 (curves)** | **0.263 rad/s** | with both **REMOVED** (stock critic set) |

⇒ **DWB now commands a gentle turn — 0.263 rad/s ≈ 0.95 m radius.** Exactly the arc the operator said
the rover takes and I had wrongly declared impossible.
⛔⛔ **RETRACT THE EVENING'S DIAGNOSIS: it was NOT `sim_time`/horizon, NOT `BaseObstacle`, NOT the
costmaps, NOT the planner, NOT the vehicle.** Those experiments were also invalid because DWB ignores
runtime param sets (see the gotcha above). **Do not re-run them.**
🔑 **The lesson is sharper than the fix: I introduced the blocker, then searched everywhere except my
own change.** When something breaks right after your own edit, suspect the edit first.
⚠️ **Blocker 3 is therefore RE-OPENED in principle** — those critics were the spin guard. ⚠️ mitigating
facts: the 09-17 max-rate spin happened with **`voxel_layer` ON** and the flat config has it OFF;
`max_vel_theta` is 1.0 and `autonav_mode` clamps at 1.0 as well. ⏭ **Re-tune the critics PROPERLY
(YAML + restart, one at a time) rather than removing them permanently.**

## 📦 CONFIG STATE AS LEFT (built and installed)
`nav2_forward_flat.yaml`: critics = the **stock 7** (`PreferForward`/`Twirling` removed, with a
comment saying why) · `sim_time` **2.0** · `BaseObstacle.scale` **0.02** · `max_vel_theta` **1.0**.
⏭ **T3 IS NOW RUNNABLE AND UNTESTED ARMED.** Goal used: 2.2 m ahead, 0.8 m RIGHT.

# 🔧 2026-09-19 — REGISTRATION WATCHDOG / `autonav_manager` (STARTED, NOT FINISHED)

**Operator's requirement: registration should happen automatically when the system comes online, so
that ARMING is the only action needed for a test — no disarm/restart dance.**

✍️ **WRITTEN: `ros2_ws/tools/autonav_registration_watchdog.py`** (parses; NOT yet installed as a
service). Watches `/fmu/out/vehicle_status_v1`; the timestamp is PX4 **boot-relative**, so an FC
reboot makes it **jump BACKWARDS** — that is the trigger. On that edge, **and only while DISARMED**,
it restarts `rover-autonav-mode`. Rate-limited, 4 s settle, never restarts while armed (that would
drop the mode executor under an armed rover).
⛔ **THE CONSTRAINT THAT CANNOT BE ENGINEERED AWAY: PX4 WILL NOT REGISTER AN EXTERNAL MODE WHILE
ARMED.** So re-registration only ever happens in a disarmed window — which is precisely what makes
"arm and go" work: registration is already in place before the switch moves.

## 🔑 DESIGN AGREED WITH THE OPERATOR — one `autonav_manager` service + CLI
⛔ **A manager CANNOT register a mode on another node's behalf** — px4_ros2 ties registration to the
mode object, and the registered component must answer the FC's arming-check handshake itself. So the
manager **supervises**, it does not register. What it owns:
- **supervision** — FC-reboot detection + disarmed restart (the watchdog, as its first function)
- **status** — "is AutoNav actually registered?", answered from the **handshake**, ⛔ never `is-active`
⛔ **SCOPE CUT BY THE OPERATOR 09-19: NO additional-mode support, NO rename. Not needed.**
⇒ **the manager is ONLY: keep AutoNav registered + report whether it is.** Don't build more.
⬜ **BLOCKED ON A PERMISSION DECISION:** the watchdog needs to restart the unit. I wrote
`/etc/sudoers.d/rover-autonav-watchdog` granting `roz` NOPASSWD for **exactly**
`systemctl restart rover-autonav-mode`, but **the validate/test command was denied by the permission
classifier, so it is UNVERIFIED — treat that file as suspect until `visudo -c` passes.**
⏭ Operator to choose: approve the validation, or run the manager service as **root** (no sudoers, but
broader privilege).

# ✅✅✅ 2026-09-19 — **T3 PASSED (operator-adjudicated). THE FIX WAS `ObstacleFootprint`.**

⚠️ **THE RUN BEFORE THIS ONE "SUCCEEDED" AND STILL HIT THE OBSTACLE.** Nav2 reported
`GOAL SUCCEEDED`, the reflex stayed silent — and the rover's **LEFT FLANK struck the bag** as it
turned back toward the goal line. 🔴🔴 **"REFLEX SILENT" MEANS NO CONTACT *IN THE FORWARD CORRIDOR*
(|y|≤0.275 m, ±20°) AND NOTHING MORE. THIS ROVER HAS NO SIDE SENSING — a flank or rear strike is
STRUCTURALLY INVISIBLE to it.** ⛔⛔ **NEVER CALL T3/T4 FROM TELEMETRY. EYES OR TAPE ONLY.** I called
that run a pass and was wrong.

## 🔑🔑 ROOT CAUSE — DWB WAS PLANNING AS A POINT ROBOT
**`BaseObstacle` scores only the robot's CENTRE POINT against the costmap** — no length, no width.
The centre cleared the bag; **the 0.73 m body did not.** 🔑 `base_link` sits 0.345 m from the front
but **0.385 m from the REAR**, so a yaw swings the tail sideways — the operator identified this
("it collided with left side not front") before I did.
✅ **FIX: add the `ObstacleFootprint` critic (scale 32, weighted with the path critics 32/24).** It
scores the **actual footprint polygon swept along each trajectory**. Stock `dwb_critics`, no code.
⚠️ `BaseObstacle` was left at 0.02 — it is near-useless at that weight and is NOT the protection.

## 📋 THE CONDITIONS OF THE PASS — reproduce with these, they are not all settled
`nav2_forward_flat.yaml`: **`ObstacleFootprint` 32** · `max_vel_theta` **0.7** (it slammed the 1.0
clamp on 121/133 samples the run before and cut the corner) · `max_vel_x` **0.35** · `xy_goal_tolerance`
**0.30** · `yaw_goal_tolerance` **3.14 = final heading IGNORED** · progress checker **0.15 m / 25 s**
· ⚠️ **`PreferForward` + `Twirling` still REMOVED** (the blocker-3 spin guard is OUT).
**Result:** goal 2.2 m STRAIGHT AHEAD, obstacle in the path. along-track **2.136 m**, lateral
**−0.183 m** (right, tighter than the −0.270 of the colliding run), `angular.z` max **0.626**,
reflex silent, **no contact (operator)**.
⚠️ **n=1 · distance is ODOM-adjudicated (mean 0.159 m/s, where odom under-reads ~7%) · clearance is
EYE-adjudicated.** ⏭ repeat for n=3 and tape it before treating T3 as closed.

## 🔑 WHY "GOAL STRAIGHT AHEAD" IS THE RIGHT T3 SETUP
⛔ My earlier lateral goals (0.8 m right) **steered the rover into a wall** — I was making the routing
decision instead of the planner. **Goal straight ahead + obstacle in the path ⇒ Nav2 chooses the side
with room.** That is both a truer test and safer.
🔑 **Operator's framing, which is the behaviour to aim for:** drive the line → find the obstacle →
deviate only as much as needed → **rejoin the line** → continue. The rejoin is where the collision
happened, and it is the thing to watch on every future run.
⚠️ **Odometry dependence is real but was NOT this failure:** the path, the goal and the "line to
rejoin" are all in the `odom` frame. Fine over 2 m (~7% ⇒ 0.15 m); ⛔ **it gets worse with distance** —
keep goals SHORT until localization exists.

# 🔴 2026-09-19 (night) — **T3 IS NOT REPRODUCED. n=1 PASS, 4 FAILS. MOSTLY MY PROCESS.**

⛔ **THE PASS STANDS AS n=1 AND NOTHING MORE.** Four attempts after it, none successful.
🔴🔴 **THE PROCESS FAILURE, WHICH IS THE REAL LESSON: I was asked to repeat T3 for n=3 and instead
CHANGED THE CONFIG AFTER THE FIRST FAILURE** — re-added `PreferForward`, then swapped the whole
controller to RPP, then tuned lookahead twice. ⇒ **no two runs share a configuration, so nothing is
reproducible and the pass cannot be confirmed.** 🔑 **A repeat means CHANGE NOTHING. A single failure
is data about repeatability, not a reason to tune.** (Operator called this out directly.)
⚠️ **Geometry also never matched:** the pass started **1.68 m** from the obstacle at ~25° heading;
the repeats started at **2.50 m** and 28-35°. ⇒ pivot-vs-drive behaviour is **SENSITIVE TO START
GEOMETRY** and that sensitivity is uncharacterised.

## 🔑 WHAT THE FAILURES LOOK LIKE (operator: "it never reached the obstacle at all")
Mean `linear.x` **0.028 m/s** over ~57 s, 179/573 samples rotating in place, 1.6 m of a 2.5 m approach.
**It crawls and pivots instead of committing to the way round.**
🔑 **PRIME SUSPECT, ONE NUMBER: `ObstacleFootprint.scale` = 32** (my guess, chosen to match
`PathAlign`). It **fixed the flank collision** — but it also makes every trajectory whose footprint
nears the obstacle expensive, so the approach degenerates into a crawl. **The collision fix and the
crawl are the same setting.** ⏭ **try 10-15 and re-test — ONE change, then three runs unchanged.**

## 📦 STATE AS LEFT
`nav2_forward_flat.yaml` = **the exact configuration T3 passed on**, restored verbatim: DWB ·
`ObstacleFootprint` 32 · **no `PreferForward`, no `Twirling`** · `max_vel_theta` 0.7 · `max_vel_x` 0.35
· xy tol 0.30 · yaw tol 3.14 (heading ignored). ⚠️ **spin guard still OUT.**
🅿️ **RPP is PARKED, NOT DELETED** — config preserved. It installs and activates cleanly, **never
pivots** (`use_rotate_to_heading: false` forbids it structurally), and **refuses to move on
"collision ahead" even from 2.5 m with 1.7 m of clear room on the right** — while the costmap at the
rover reads **cost 0 centre / 0 right / 49-55 left** (wall inflation, NOT lethal). ⇒ **its collision
check is unexplained and needs DESK study against the costmap, not more floor tuning.**

## ⏭ NEXT SESSION — THE DISCIPLINE, NOT JUST THE TASK
1. **Set the geometry to the PASS geometry and mark it**: obstacle **1.68 m**, heading ~25°, floor
   mark at the bumper. ⛔ **Do not run until the preflight matches those numbers.**
2. **Three runs, ZERO config changes between them.** Tape each. That is the test.
3. Only then, if it still fails: **one** change (`ObstacleFootprint` 10-15), then three runs again.
4. ⛔ **Never re-arm on a config that has not been characterised disarmed first** — the disarmed
   probes (`planprobe3.py`) answered more tonight than the armed runs did, at zero risk and zero cost.

## 🔴🔴 VERDICT 2026-09-19 (night) — **THE T3 PASS WAS ACCIDENTAL. 1 SUCCESS IN 6.**
**Repeated at MATCHED configuration AND matched geometry (1.62 m vs the pass's 1.68 m, heading 17.8°
vs ~25°, goal moved to 3.0 m so it was actually reachable) ⇒ SAME FAILURE:** 177/303 samples rotating
in place, `angular.z` pinned at the 0.7 cap on 284/303, mean `linear.x` **0.021 m/s**, and it turned
AWAY from the obstacle (clearance 1.907 → 2.795). Operator disarmed it.
⛔ **DO NOT TREAT T3 AS PASSED.** The operator called it: *"otherwise passed one is accidental."*

🔑🔑 **MECHANISM — IT IS THE COMBINATION I LEFT IN PLACE, AND IT WAS NEVER TESTED BALANCED:**
- **nothing penalises pivoting** (`PreferForward` AND `Twirling` both removed) ⇒ rotating is FREE
- **`ObstacleFootprint` 32 makes forward motion near the obstacle EXPENSIVE** ⇒ driving is costly
⇒ **DWB's cheapest option is to turn instead of drive.** The one pass needed a lucky start alignment
where almost no turning was required.
⏭ **THE UNTESTED COMBINATION, AND THE FIRST THING TO TRY: `PreferForward` ≈15 *TOGETHER WITH*
`ObstacleFootprint` ≈12.** Every configuration tried tonight had one or the other, never both
balanced. ⛔ Then THREE runs with nothing changed between them.

⚠️ **ANOTHER TEST-DESIGN TRAP FOUND: the GOAL MUST CLEAR obstacle + `inflation_radius`.** At 1.62 m
the obstacle sits ~1.97 m from `base_link`; +0.55 m inflation ⇒ **everything inside 2.52 m is
unreachable**, so a 2.2 m goal made the PLANNER fail instantly (BT aborted 30 ms in, before the
controller ever ran). 🔑 **A goal inside inflation looks like a controller failure and is not one.**

## 🔑 2026-09-19 — **ch12 KILL PRESSED IN ARMED AUTONAV FOR THE FIRST TIME. THE ROVER STOPPED.**
The operator hit **ch12** during a misbehaving T3 run (it was pivoting and crawling). **The rover
stopped**, the goal cancelled, and `arming_state` read **1** afterwards.
🔑 **S1 has been "INCONCLUSIVE, NOT FAILED" since 09-12 for exactly one reason — ch12 was never
pressed.** It has now been pressed, in AutoNav, armed, and it worked.
⚠️ **NOT a formal S1 pass:** no latency measured, no tape, and "stopped" is the operator's
observation rather than an instrumented stop distance. ⛔ Do not tick S1 off this.
⏭ **To close S1 properly:** deliberate run at a known speed, hit ch12, and measure the stop with
TAPE or `/scan` (⛔ wheel rpm cannot measure a stop). Also settle what S1 means first — **PX4 KILL ≠
DISARM** — which was the other half of why it stayed open.

## ⛔⛔ RETRACTED SAME NIGHT — **"THE T3 PASS WAS ACCIDENTAL" IS WITHDRAWN. I COMPARED THE WRONG NUMBERS.**
🔴🔴 **UNITS ERROR: `t3r.py` logs the RAW scan range; `preflight_scan_check.py` reports BUMPER
clearance. They differ by the 0.337 m front overhang.** I read the pass's **1.680 raw** as bumper
clearance and had the operator park **0.3 m FURTHER BACK than the pass**. ⇒ **the "matched geometry"
repeats were never matched.**

| run | raw | bumper | heading | result |
|---|---|---|---|---|
| **PASS** | 1.680 | 1.343 | **24.9°** | ✅ SUCCEEDED |
| repeat 1 | 1.683 | 1.346 | **34.8°** | ABORTED |
| repeat 2 | 1.686 | 1.349 | 33.3° | ABORTED |
| repeat 3 | 2.520 | 2.183 | 20.9° | ABORTED |
| repeat 4 | 1.952 | 1.615 | 17.1° | DISARMED (operator hit ch12) |

🔑 **Repeats 1-2 matched the pass distance to 6 mm and still failed — the difference was HEADING
(~34° vs 24.9°).** Repeat 1 also ran the pass configuration ⇒ **the closest controlled comparison we
have points at HEADING SENSITIVITY, not luck.** ⛔ **NO run has ever matched BOTH distance and
heading.** ⇒ **T3 is UNREPRODUCED, NOT DISPROVEN.** The operator pushed back on the "accidental"
call and was right.
⏭ **THE REPEAT THAT STILL NEEDS RUNNING: raw 1.68 m (= BUMPER 1.34 m) AND heading ~25°, goal ≥3.0 m,
three runs, no config changes.** ⚠️ **State which ruler you mean — RAW or BUMPER — every single time.**

## ✅✅ 2026-09-19 (night) — **THE T3 AVOIDANCE REPRODUCED AT MATCHED CONDITIONS. THE PASS WAS REAL.**
**Controlled run — first of the night with EVERYTHING pinned:** pass config untouched · bumper
**1.360 m** (pass 1.343) · obstacle dead ahead, right side open 0.9-1.8 m lateral · **BOTH COSTMAPS
CLEARED** · fresh `eph` 1.135 m.
**Result: it drove 2.815 m of a 3.0 m goal, deviated −0.419 m RIGHT, AND CLEARED THE BAG — operator
confirms no contact.** in-place rotation only **97/392** (the pivot-crawl failures were 177-237).
⇒ ⛔ **"THE PASS WAS ACCIDENTAL" IS FULLY WITHDRAWN. The avoidance reproduces.**

## 🔑🔑 THE REMAINING GAP IS THE REJOIN — AND IT IS THE SAME ONE NUMBER
**Operator: "it avoided the bag but not rejoined to its track."** It finished **0.458 m** from the
goal against a 0.30 m tolerance — it trailed right and never came back to the line, so Nav2 never
registered arrival and aborted.
🔑 **MECHANISM: `ObstacleFootprint.scale` 32 forbids the return.** Rejoining means moving back
TOWARD the obstacle laterally while still alongside it ⇒ footprint cost ⇒ those trajectories lose.
**The critic that prevents the flank collision also prevents the rejoin.**
🔑🔑 **ONE COHERENT EXPLANATION FOR EVERYTHING TONIGHT:**
- `ObstacleFootprint` **0.02** ⇒ rejoins, **HITS the bag** (the flank collision)
- `ObstacleFootprint` **32** ⇒ **avoids cleanly, NEVER rejoins**
⇒ ⏭ **THE ANSWER IS BETWEEN. Try 10-15, then THREE runs with nothing changed.** This is now a
motivated experiment, not a guess.
⚠️ Also note: absolute odom heading was a RED HERRING — the goal is defined along the current
heading, so the rover-relative geometry is identical at 12° or 25°. **What matters is the SCENE**
(obstacle ahead + which side is open). ⛔ Don't chase compass numbers again.
