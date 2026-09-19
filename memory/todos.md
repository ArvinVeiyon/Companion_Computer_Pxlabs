# TODO List
> ⛔ **The old "do these AFTER a full OS backup" framing is GONE** — it had not applied for months and
> was gating nothing. **Read the REQUIREMENTS REALIGNMENT below; that is the plan.** Everything under
> the older headings is detail, not the agenda.
> 🧹 **Pruned 2026-09-10: 793 → ~540 lines.** Removed were completed items, deleted items, two
> session logs and the withdrawn "camera was rotated" claim. **Every ⛔ "do not reopen / do not
> re-propose" warning was kept** — those are what stop work being redone.

---

# 🎯 REQUIREMENTS REALIGNMENT — 2026-09-04. **READ THIS BEFORE PICKING UP ANY ITEM BELOW.**
> Why: the requirements live in `docs/rover_autonav_requirements.md` (R1-R7), the goals in
> `docs/autonomy_plan.md` (M0-M4 modes, L0-L5 layers, A1-A9 features, S/T tests) — and **this file
> tracked neither.** Most of the list below is radio/vision/hardware; **most of the unbuilt
> requirements had no todo at all.** This section is the bridge. Everything under the old headings
> stays valid as detail, but is no longer the plan.

## 0. LADDER OWNERSHIP — settled, stop re-deriving it
| Scheme | Means | Status |
|---|---|---|
| **M0-M4** (`autonomy_plan.md` §5) | **what the rover DOES for a user** — the GOAL ladder | ✅ authoritative |
| **L0-L5** (`autonomy_plan.md` App. A+B) | **capability layers we must BUILD** | ✅ authoritative |
| **R1-R7** (`rover_autonav_requirements.md` §3) | **the requirements themselves** | ✅ authoritative |
| ~~L0-L7~~ (`rover_autonav_requirements.md` §4 build order) | env-first bring-up order | 🗄 **RETIRED — it is the third scheme.** L0-L4 all closed; its L5/L6/L7 are just M2/M3/the S+T tests. Do not plan off it. |

✅ **DOC FAULT CLOSED 09-04: "the L0-L5 ladder appears TWICE in `autonomy_plan.md`" (flagged 08-10)
is NOT a duplication.** Appendix A = *what to build*, Appendix B = *definition of done*. They agree
layer-for-layer (L0 ✅ · L1 🔧 · L2-L5 ❌). Nothing to resolve, nothing to delete.

## 1. WHERE WE ACTUALLY ARE AGAINST THE REQUIREMENTS
⚠️ **Table re-stated 2026-09-19. It had been frozen at its 09-04 wording for two weeks while G0, G2
and G3 all closed underneath it** — R4 still read "not honoured", R7 still read "launch file stale".
🔑 **If you close a gate, come back and edit this table. It is the first thing a fresh session trusts.**

| Req | State | The one thing blocking it |
|---|---|---|
| **R1** localization | 🔴 **DEAD** — **0 accepted of 20 on the map's OWN bag** (09-12) ⇒ fails at **GEOMETRY, not appearance** | ⛔ the `camera_info`-vs-DB-calibration lead is **DEAD** — do not re-run it. Needs a fresh pipeline diagnosis → **G1** |
| **R2** perception | ✅ `/scan` · 🔧 `/scan_3d` exists but **nothing consumes it** | voxel layer + reflex `scan_topic` (#27) → **G4** |
| **R3** planning | ✅✅ **Nav2 RAN 09-17/18 — Phase 0 passed DISARMED**, full chain to `/cmd_vel`. **Never run ARMED.** | cap DWB in-place rotation + a preflight-clean start position → Phase 1 |
| **R4** control bridge | ✅✅ **CLOSED 09-13 — speed commands ARE honoured, all four in RPM mode** (`RO_MAX_THR_SPEED` 4.93) | nothing. ⛔ Every torque-mode rule is history; don't quote them |
| **R5** safety | ✅ 1,2,3 proven · 🔧 **R5.4 has NUMBERS** (09-13: 0.52 s / 0.19 m / 1.28 m/s²) but the **≥300 mm standoff above ~0.11 m/s is UNMEASURED** · ❌ **R5.5 companion-crash disarm NEVER TESTED** | `collision_standoff_test.py` as a speed ladder (Session B) / **G6** |
| **R6** compute ≤2.0 cores | ❌ **never measured as a total** — and RTAB-Map + voxel go on top | **G4** gate |
| **R7** frames | ✅✅ **CLOSED 09-11** — measured, corrected, verified at a wall | nothing. ⛔ don't re-derive |

🔑 **R1's stated acceptance ("<0.3 m over a 20 m loop") CANNOT BE RUN HERE** — same room constraint
that blocks T2. It needs a corridor or a re-scope; that is an operator decision, see **G3**.
✅ **R1 doc conflict — CLOSED 2026-09-10, it was already fixed and this note was the stale one.**
`rover_autonav_requirements.md` carries the `slam_toolbox` line **struck through** with
*"🔴 SUPERSEDED 2026-08-01 — the map/localization source is RTAB-Map, not slam_toolbox"*. Nothing to
do. ⚠️ Remaining `slam_toolbox` mentions there are in the **retired** L0-L7 ladder and in install
inventories, which are factual.

## 2. 🔴 REQUIREMENTS THAT WERE TRACKED **NOWHERE** UNTIL NOW
Not late — **never filed.** These are the actual product, and none of them is a hardware problem:
- **N1. `/rover_health` monitor (L2, A9).** Level + reason string, never a bare boolean. Every row of
  its watch-table is a failure this project already hit **and only caught by hand** (`eph` 682 m ·
  ESC doze · CPU-starvation latch · yaw 21× command). ⇒ **mandatory for unattended.**
- **N2. Supervisor / decision layer (L3).** Owns the mission above Nav2; Nav2 has no answer to
  "blocked, now what" and both its recoveries are disabled here (blind at 92°). ⇒ **L3 IS the
  unattended milestone** — the first stage that changes what the OPERATOR must do.
- **N3. Waypoint sequencer (A6).** Drive a LIST of goals. Small node. Gates M3 "patrol".
- **N4. Return to base (A8).** ⚠️ **NOT inheritable from PX4** — RTL targets a **GPS** home and on
  this rover drives there with **zero obstacle avoidance**. Must be built in N2.
- **N5. Failsafe policy decisions — design only, no hardware, nothing started:**
  `NAV_RCL_ACT=6` (**disarm**) is right for the bench and **wrong for a mission** · lost-localization
  → stop+hold **does not exist** · no-route-to-goal **does not exist** · battery-low → return
  **not configured**. → `autonomy_plan.md` §6.
- **N6. R5.5 companion-crash disarm** — PX4 offboard-timeout behaviour, never bench-tested.
- **N7. R6 total CPU budget** — measure the whole stack against ≤2.0 cores **before** adding
  RTAB-Map or the voxel layer. ⚠️ **budget for `claude` itself: 55-86% of a core.**

## 3. THE REALIGNED ORDER — gates, not a wish list. Each one unblocks the next.
**G0 — GEOMETRY TRUTH.** ⛔⛔ **THE CAMERA IS NOT ROTATED AND NEVER WAS. THE OPERATOR HAS SAID SO
REPEATEDLY AND HE IS RIGHT — STOP RAISING IT.** The 08-10 "camera physically rotated" claim was
WITHDRAWN 09-04 and re-measured 09-09: **pitch 1.436°, roll −0.447°, |g| 9.7769, sd 0.006, 12,145
samples** (`tools/cam_mount_probe.py`). That is a normal, level mount.
🔑 **What was wrong was the LAUNCH FILE, not the hardware** — it carried the 07-27 `cam_pitch`
0.0406 / `cam_roll` 0.0100 from before the camera came off and went back on the top plate.
✅✅ **G0 IS CLOSED — corrected 09-10 to `cam_pitch` 0.0251 / `cam_roll` −0.0078, and VERIFIED AT A
WALL 09-11:** 5 parkings, fit RMS 0.3-3.4 mm, **inlier fraction 1.00 at every range ⇒ no floor in
the scan**, coverage 0.80 vs the 0.35 threshold, and on operator tape at 1.12 m `/scan` read
**1.4390 vs 1.4344 predicted (4.6 mm)** ⇒ **`front_overhang` 0.337 and scale 0.9845 BOTH STAND.**
Full method, numbers and limits → `project_rover_autonav` 2026-09-11.
**G1 — LOCALIZATION ALIVE (R1).** 🔑 **Adjudicate on the ACCEPTED-FIX COUNT — a changing `map→odom`
with 0 accepted is drift, not health.** ⛔ Do not re-map the house first. ⚠️ **Corrected 09-19: this
used to name "live `camera_info` vs `house_map_v4.db`'s calibration" as the thing to do. That lead is
DEAD** — 0 accepted of 20 on the map's OWN bag means it fails at **GEOMETRY, not appearance.**
⛔ never lower `Vis/MinInliers`. → `indoor_mapping_slam` §17.
**G2 — MOTION TRUTH (R4, R5.4, T1).** ✅✅ **CLOSED END TO END 2026-09-13 — rewritten 09-19; it used
to read "IT IS NOW A DECISION, NOT A TEST", which was the dead torque-vs-duty framing.** All four
ESCs are in **RPM mode**, tuned and floor-validated under load; `RO_MAX_THR_SPEED` **4.93**; odometry
scale and sign settled; `si_motor_poles` settled; R5.4 has its numbers.
⬜ **What is left is NOT part of the gate:** the brake reflex wiring (R5.4 — the reflex still only
zeroes the setpoint; the durable fix needs a VESC **firmware** change) · the zero-dropout floor
figure · **T1 re-examined, not re-ticked**.
⛔ Gate every moving test on MEASURED speed, never the command. *(The old tail "— and on DURATION,
not stick position" was a TORQUE-MODE rule and is deleted.)* → `project_rover_autonav` 09-13.
**G3 — VENUE DECISION → T2 PROVEN** *(title corrected 09-19: the gate closed on the venue + T2, **not**
on M2 — T3/T4/T5 are still ahead).* ✅✅✅ **CLOSED 2026-09-16 — T2 PASSED n=3 IN THE CORRIDOR,
TAPE-ADJUDICATED.** Taped 2.130 / 2.025 / 2.000 m against a 2.0 m goal at 0.15 / 0.25 / 0.75 m/s
⇒ error +0.130 / +0.025 / 0.000 m, all inside ±0.20 m, **reflex silent on all three.**
→ `bldc_can/evidence/t2_autonav_floor_20260916.md` · `project_rover_autonav` 09-15/16.
🔴 **THE SPEED PERMISSION WAS BYPASSED, AND THAT PART STANDS:** the 0.75 m/s run **exceeded the
`autonav_reference.md` §13 permission** without re-running `collision_standoff_test.py`
(operator-directed, after the constraint was stated). 🔑 **T2 DOES NOT TEST THE REFLEX — it drives at
NOTHING**; a silent reflex is the pass criterion, not evidence the reflex works at speed.
⇒ **THE ≥300 mm STANDOFF IS STILL UNMEASURED ABOVE ~0.11 m/s. That is the live item.**
⛔ **AND WHEEL RPM CANNOT MEASURE A STOP** — the signal is non-physical through it
(`autonav_reference.md` §13b); needs `/scan`-at-a-wall or tape.

✅✅ **THE `RO_DECEL_LIM`=5 STOP IS CLOSED — 2026-09-18, BY ARITHMETIC. ⛔ DO NOT BOOK FLOOR TIME.**
The concern was real: since 09-14 the reflex rides the SAME throttle ramp as the manual stick (it
publishes a fake `ManualControlSetpoint`), so its stop is no longer the fast one, and the 0.69 m
clearance was sized against a 0.19 m stop taken at `RO_DECEL_LIM` **−1**. **The arithmetic covers
exactly that path:** slew = `RO_DECEL_LIM ÷ RO_MAX_THR_SPEED` = 5 ÷ 4.93 = **1.01 /s** ⇒ at 0.75 m/s
the rover sits at 0.152 throttle, drains in **0.15 s**, and adds **0.057 m** (at 0.25 m/s: 6 mm).
Worst case **~0.25 m against 0.69 m.** The 08-14 half-metre came from the OLD divisor **0.60**, not
from the decel value. → `autonav_reference.md` §13 (09-18) · `px4_rover_control_scope` §RAMP ARITHMETIC.
⚠️ **STILL LIVE AND UNRELATED: `RO_SPEED_LIM` does NOT cap Manual** — full stick is 4.93 m/s, which
a corridor makes reachable.
Preflight = `tools/preflight_scan_check.py` (passive, mirrors the reflex sector/thresholds).
🗄 superseded options were: corridor (recommended) ·
re-scope T2 to 0.8 m · or drop this room as the M3 target. Then **T2 → T3 → T4 → T5** = M2 done.
⚠️ T3+ need turning, so **S3 (yaw open/closed) gates them.**
**G4 — 3D PERCEPTION (R2/A5) + N7.** Wire `/scan_3d` into a Nav2 `voxel_layer` and flip the reflex's
`collision.scan_topic` (#27 — **needs one low object `/scan` misses** as the proof). Measure R6 first.
**G5 — N1 `/rover_health` (L2).** Faults **INJECTED**, not waited for; 8 checkboxes in App. B.
**G6 — N2+N3+N4+N5+N6 (L3) → M3.** The unattended milestone.
**G7 — M4 outdoor.** O1-O5 + the **mission-ownership decision** (PX4 vs Nav2 — `roadmap.md` picked
Nav2; decide it consciously **before** building, it sets whether RTL is PX4's or ours).

## 4. ⏸ PARKED — real, but NOT on the requirements critical path. Do not let these set the agenda.
WFB block (**only action left is HW: reseat drone NIC-A ant0 = #22**) · vision_streaming node fixes
(8b, 07-30 item 3) · camera bitrate / v2.3.0 · multicam Phase D · doc-fix #5 (ch157→ch161) ·
#7 aide.db (⚠️ **still present, 117 MB, verified 09-19**) · #17 delete `camera_sw_node_obsolute.py`
(⚠️ **still present, verified 09-19 — path corrected below**) · #14 PAT rotation
(🔴 **except the operator browser-revoke, which stays live**).
*(P5 kill-switch doc-fix was here — ✅ DONE 09-12, `ros2_ws` `6506bdb`. Removed 09-19.)*

---

## ⏸ PARKED 2026-09-09 BY THE OPERATOR — brake work, resume AFTER AutoNav

🔴 **THE 09-09 BRAKE FIGURES IN THIS BLOCK WERE SUPERSEDED TWICE — corrected 09-19.** The block used
to read "0.69 m/s², stops in 0.30–0.50 m from ~0.8 m/s". **Current, floor-validated (09-13, all four,
stick only): 0.52 s / 0.19 m / 1.28 m/s².** ⛔ Do not quote the 09-09 numbers.
→ `codex-work/bldc_can/evidence/brake_floor_test_20260909.md` is the OLD run; the 09-13 numbers live
in `esc_config_audit` §THE BRAKE PATH. Loose ends, none blocking AutoNav:

1. **`codex-work` has unpushed/untracked work** — ⚠️ **re-checked 09-19: `master` is ahead of
   `origin/master` by 1, plus ~20 untracked `bldc_can/configs_live/*.xml` ESC dumps from the 09-16/17
   sessions.** (The old "5 modified + 11 new files" list was from 09-09 and no longer describes the
   tree.) **The PXLABS firmware session cannot pull what is not pushed.** Commit + push when convenient.
2. **One clean coast-to-stop** — still wanted, but the reason changed: the 09-12 floor run gave coast
   **0.46 m/s²** (0.70 m from 0.8 m/s) to a full stop, so the baseline is **n=1, not n=2**, and every
   brake-vs-coast ratio rests on it. Two minutes: spin up, throttle to neutral with ch3 at the bottom
   stop, roll out untouched.
   *(The old "3.4× / saves 1.4 m provisional" wording was superseded by that run — removed 09-19.)*
*(Item "MAVLINK IS BACK" was here — ✅ closed 09-10, G2 has since closed entirely. Removed 09-19.
⚠️ the one fact worth keeping: the MAVLink outage's cause was NEVER identified, so it may recur.)*

*(A line here claimed `MEMORY.md` was "19.8 kB against its own 17 kB cap" — **WRONG, removed 09-19.**
17.1 kB is the recompaction TARGET, not the ceiling; the real cap is **24.4 kB and it truncates the
tail silently**. See the 09-18/19 desk block below.)*

## 🗂 2026-09-18/19 — DESK SESSION, NO FLOOR TIME. **The AutoNav plan below is UNCHANGED — go to it.**

Paper only; nothing on the vehicle moved and no param was written. Three things closed:

1. ✅✅ **`RO_DECEL_LIM`=5 CLOSED BY ARITHMETIC — ⛔ DO NOT BOOK A FLOOR RUN FOR IT.**
   slew = 5 ÷ 4.93 = 1.01/s ⇒ **0.057 m at 0.75 m/s**, worst case ~0.25 m vs the reflex's 0.69 m.
   → `px4_rover_control_scope` §RAMP ARITHMETIC (which had already computed this on **09-14**).
   ⚠️ **STILL OPEN AND OFTEN CONFUSED WITH IT: the ≥300 mm reflex standoff above ~0.11 m/s.**
   That one is real, unmeasured, and needs `collision_standoff_test.py`.
2. ✅ **MEMORY RECONCILED.** `#22/#25/#26/#27` now exist here (they were cited in `MEMORY.md` for
   weeks while this file stopped at 21). Brake detail → `esc_config_audit` §THE BRAKE PATH; param
   tooling → `px4_rover_control_scope`; boot-clock trap → `this_machine`.
3. 🔴 **`MEMORY.md` HAS A HARD 24.4 KB CAP THAT TRUNCATES ITS TAIL SILENTLY** — no error, no marker.
   17.1 KB was never a limit (it is 0.7 × cap, the recompaction target). Index is ~21.8 KB after
   trimming; **⬜ still ~2 KB above the warn line.** Remaining fat: `[MOTION/SAFETY]`,
   `[MEMORY_FILES]`, `[CURRENT STATE]`.

⏭ **NEXT ON THE VEHICLE IS UNCHANGED: Phase 1 of the plan below.** ⛔⛔ **NEVER ARM WITH `voxel_layer`
ENABLED** (DWB commands a sustained max-rate spin) and ⛔ **cap DWB before any armed run.**
🔑 **A silent reflex beyond ~3 m is BLIND, not clear.** → `project_rover_autonav` 09-17/18.

## ✅✅ 2026-09-19 (late) — **THE T3 BLOCKER WAS MY OWN CRITICS. DWB NOW TURNS.**

🔑🔑 **Operator's call — "lift your constraint" — found it in one test.** `PreferForward` 50 +
`Twirling` 20, which **I added that same morning** for blocker 3, were making every rotating
trajectory score worse than creeping straight.
**Removed (stock critic set) ⇒ `/local_plan` lateral 0.000 → −0.11 and `cmd_vel_nav` `angular.z`
0.000 → 0.263 rad/s** (a ~0.95 m-radius arc — the gentle turn I had wrongly called impossible).
⛔⛔ **RETRACT the evening's diagnosis: NOT `sim_time`, NOT `BaseObstacle`, NOT the costmaps, NOT the
planner, NOT the vehicle. Do not re-run those.** 🔑 **When something breaks right after your own
edit, suspect the edit first.**
⚠️ **Blocker 3 re-opened in principle** (those critics were the spin guard) — but the 09-17 spin
needed **`voxel_layer` ON**, which the flat config has OFF, and `max_vel_theta`/executor clamp are
both 1.0. ⏭ **re-tune the critics properly (YAML + restart, ONE at a time), don't leave them out.**
⏭⏭ **T3 IS NOW RUNNABLE AND UNTESTED ARMED** — goal 2.2 m ahead, 0.8 m RIGHT. **This is the next
floor action.**

## 🔧 2026-09-19 — REGISTRATION WATCHDOG / `autonav_manager` — STARTED, NOT FINISHED
**Goal (operator): registration happens automatically at boot so ARMING is the only step for a test.**
✍️ `ros2_ws/tools/autonav_registration_watchdog.py` written (not installed). Detects an FC reboot via
the **backwards jump in PX4's boot-relative `vehicle_status` timestamp**, then restarts
`rover-autonav-mode` **only while DISARMED**.
⛔ **PX4 WILL NOT REGISTER AN EXTERNAL MODE WHILE ARMED — unavoidable**, which is exactly why
re-registration must happen in the disarmed window.
⛔ **A manager CANNOT register on another node's behalf** (px4_ros2 ties registration to the mode
object, which must answer the arming-check handshake). It **supervises only**.
⛔ **SCOPE CUT 09-19 (operator): NO add-mode, NO rename — not needed.** Just two functions:
**keep AutoNav registered after an FC reboot**, and **report registration from the handshake**
(⛔ never from `is-active`).
⬜ **BLOCKED:** `/etc/sudoers.d/rover-autonav-watchdog` (NOPASSWD for exactly
`systemctl restart rover-autonav-mode`) was written but **`visudo -c` was denied by the permission
classifier — UNVERIFIED, treat as suspect.** ⏭ operator: approve the check, or run the service as root.

## 🔴 2026-09-19 (evening) — **T3 FAILED 3×. THE BLOCKER IS DWB, NOT YAW.**

⛔ **T3 DID NOT PASS — goal never reached.** All three armed runs ended `GOAL ABORTED`
(`Failed to make progress`), stopping at 0.89-0.93 m. ⛔ **`angular.z` was EXACTLY 0.000 in all of
them — the yaw axis was never commanded, so T3 tested nothing about yaw or the motors.**

✅ **Ruled out by DISARMED probes (no motion, no eph cost):** obstacle IS in both costmaps (cost
92-100) · the global planner DOES curve around it (0.80 m lateral) · that curve DOES reach DWB.
🔴 **DWB chooses a DEAD-STRAIGHT trajectory and avoids the obstacle by SLOWING DOWN** (~0.14 m/s;
armed runs: `linear.x` mean 0.116 vs max 0.250) until the reflex blocks it.

🔴🔴 **REMEMBER THIS TRAP: DWB reads `sim_time` and every critic `scale` AT INITIALISE.** A runtime
`ros2 param set` says "successful" and reads back the new value while the critic keeps the old one.
⛔ **Only YAML + restart applies them — two of my experiments were meaningless because of this.**

⏭ **NEXT, IN ORDER:** ① 🔑 **try Regulated Pure Pursuit instead of DWB** — it follows the path
geometrically instead of sampling, which removes the whole critic-weighting question ② re-test the
critic weights PROPERLY (YAML + restart, one at a time) ③ ⛔ **RETRACTED: the "cannot make gentle turns" claim was WRONG.** 0.67 rad/s
is the STANDSTILL BREAKAWAY; while ROLLING the same day's arcs achieved **0.16 and 0.22 rad/s at
0.25 m/s = 1.1-1.6 m radius**. Gentle arcs are demonstrated. ⛔ **Never derive a moving limit from a
standstill measurement — and ASK THE OPERATOR, who drives it.**
✅ Config REVERTED to the Phase-1-validated values and rebuilt. 📐 scan-derived plan view:
`https://claude.ai/code/artifact/a715d45d-d10c-4958-8469-c2ce3c996842`
→ full detail `project_rover_autonav` **2026-09-19 (evening)**

## ⏭⏭ START HERE — 2026-09-19 (FLOOR). **PHASE 1 PASSED. A SIGN BUG IS FIXED. YAW IS THE BLOCKER.**
**Scope: finish M2 (T3·T4·T5), camera-only. ⛔ NO LIDAR — the STL-19 is assigned to the DRONE.**

✅✅ **PHASE 1 PASSED n=2, TAPE-ADJUDICATED — NAV2 DROVE AN ARMED ROVER.** 1.380 m tape vs a 1.5 m
goal ⇒ **−0.120 m, inside ±0.20**; lateral +0.013/+0.017; **`angular.z` max 0.053, ZERO in-place
rotation**; reflex silent. Config = **`nav2_forward_flat.yaml`** (voxel OFF + `PreferForward`/`Twirling`).
✅ **Blocker 3 CLOSED for straight-line work** (a disarmed probe with `/odom` frozen commanded zero
rotation for 21 s instead of spinning).

🔴🔴 **SIGN BUG FOUND AND FIXED — `mode.hpp` passed `/cmd_vel` `angular.z` UNNEGATED.** ROS FLU (+ =
LEFT) vs PX4 FRD (+ = RIGHT) ⇒ **every commanded turn went the WRONG WAY.** ⛔ **T3 would have steered
INTO the obstacle.** Caught by the OPERATOR'S EYE, not a log. ✅ fixed, rebuilt, **verified on the
floor** (gyro sign inverted; right-side-fast = left turn). ⚠️ straight-line results unaffected.

🔴 **THE BLOCKER IS NOW YAW, AND IT IS NOT REPRODUCIBLE.** Same `RO_YAW_RATE_CORR` 7.4, single steps
from rest: **0.4 weak · 0.7 STRONG (0.927 rad/s) · 1.0 weak (0.156)**, the 1.0 run drawing barely
above idle ⇒ the setpoint reaching the ESCs was small. ⛔ **NOT heat** (ESC temps 43-47 °C, pack
24.8 V; VESCs derate ~85 °C). **UNEXPLAINED — do not tune on top of it.**
🔑🔑 **THE 08-02 YAW CURVE DIED WITH THE RPM MIGRATION.** `CORR` went 1.8 → 14.8 (restored the old FF
*ratio* — right arithmetic, dead premise) → **7.4, in force**. ⛔⛔ `RO_YAW_RATE_I` STAYS 0.
⏭ **Re-measure the plant in MANUAL (`tools/yaw_response_log.py`) — bypasses the rate controller and
costs NO eph budget.**

⛔⛔ **NO MORE PIVOTS FROM REST.** These are hall-sensored hubs: **zero rpm from a stationary rotor is
EXPECTED, not a fault** — nothing for the halls to count, so the loop just pushes current (RR sat at
0 rpm / 18.8 A for 3.5 s). ✅ **RR is LIVE in an ARC** (59→84 rpm) ⇒ **T3 may not be gated on motors.**
🔧 **OPERATOR DECISION: replace the 3 old motors (RF, FL, RR).** RL was recently replaced and
outperforms them on the same axle under the same load. ⚠️ **Rear suspension sits LOWER** ⇒ ride height
is its own item; new motors will still carry that load.

⏭ **NEXT, IN ORDER:** Manual yaw characterisation → **standoff speed ladder** (straight-line, closes
the LAST open safety number: ≥300 mm above ~0.11 m/s) → T3 → T4 → T5.
⚠️ **T4 would pass too easily today** — "does not spin" is trivial for an axis that cannot pivot.
**Mark it a WEAK PASS if run before yaw is sound.**

🔑 **OPS THAT COST US FOUR RUNS:** ⛔ **after `COM_DISARM_PRFLT` auto-disarms, ch5 STAYING UP WILL NOT
RE-ARM — CYCLE IT DOWN THEN UP** · `eph` is on **`vehicle_local_position_v1`** (versioned, like
`vehicle_status_v1`) · **eph sequencing: reboot the FC and start the bridge TOGETHER** (10 min apart
gave eph 238 m; together gave 0.202 m — velocity aiding does not bound position, so it never
converges back) · the reflex corridor test is **`|y| <= 0.275 m`, not a bare ±20° sector.**
→ full detail: `project_rover_autonav` **2026-09-19**

## ⏭⏭ START HERE — 2026-09-16. **G3 CLOSED. NEXT IS T3, AND T3 IS A FIRST NAV2 BRINGUP.**

🔑🔑 **TONIGHT ALREADY PROVED HALF THE NAV2 CHAIN.** `t2_straight_goal_test.py` drives by publishing
**`/cmd_vel`** (Twist), and `autonav_mode/mode.hpp:154` subscribes to exactly that, with the R5.3
staleness watchdog and the reflex downstream. ⇒ **`/cmd_vel` → AutoNav → `RoverSpeedSetpoint` → PX4 →
ESCs is PROVEN 4× under load on the floor.** ⛔ **What has NEVER RUN is Nav2 itself** — the planner,
controller and costmap that *produce* `/cmd_vel`. `rover_nav2` written 2026-08-01, never launched.
⇒ **T3's risk is ALL UPSTREAM of a link that already works.**

### 📋 THE TWO-SESSION PLAN (agreed with the operator 2026-09-16)

**SESSION A — one sitting, no teardown between steps:**
1. **Phase 0 — Nav2 bringup DISARMED, no motion.** ⛔ NON-NEGOTIABLE FIRST. Launch
   `nav2_forward.launch.py` disarmed; verify in order: lifecycle nodes reach `active` → costmap
   populates from `/scan` → planner returns a path → controller emits `cmd_vel_nav` → smoother emits
   `/cmd_vel`. **Eyeball `/cmd_vel` magnitudes BEFORE arming** — 🔴 **AutoNav holds zero until
   `/cmd_vel` arrives, so a bad first `/cmd_vel` on an ARMED rover MOVES IT.** Costs nothing, needs
   no vehicle motion, can be done at a desk.
   ⚠️ **WATCH FOR THE COSTMAP SELF-MARKING** — with a 92° FOV the rover can mark its OWN footprint
   lethal and then refuse to plan. `footprint_clearing_enabled` is set on both layers; Phase 0 is
   where we find out if that is enough. (`nav2_forward.yaml` comments, corrected 2026-08-01.)
2. **Phase 1 — armed, Nav2 drives a STRAIGHT goal, NO obstacle.** Same corridor, same 2 m. Isolates
   "can Nav2 drive" from "can Nav2 avoid". 🔑 **Compare directly against 09-15/16**: expect ~2.0 m
   arrival, lateral ~0.03 m. If it wanders, the fault is NAV2, and we know that before an obstacle
   is involved.
3. **Phase 2 = T3.** Walk out, place ONE offset obstacle, send the goal again. Nav2 routes around it
   keeping inflation clearance.

**SESSION B — block the corridor, then in this order:**
4. **`collision_standoff_test.py` as a SPEED LADDER (0.25 / 0.45 / 0.75), tape-adjudicated.**
5. **T4** — same obstacle, same sitting.
🔑 **WHY THEY PAIR: T4 is a FULLY BLOCKED corridor, which is physically the same rig the standoff
test needs.** The standoff data then arrives exactly when T4 needs it, instead of as a detour.

⛔⛔ **THE STANDOFF TEST CANNOT BE FOLDED INTO T3 — STRUCTURALLY, NOT FOR CONVENIENCE.**
**T3 passes only if the reflex STAYS SILENT** (Nav2 routes around; a firing reflex = the planner
failed). **Standoff passes only if the reflex FIRES.** Same opposition as T2's two criteria; the
tool's own docstring says it: *"the standoff test wants an obstacle and fails without one; this one
wants a clear corridor and fails WITH one."* **One run cannot satisfy both.** Everything else in the
plan CAN be folded — Phases 0/1/2 are one session with no teardown.

### 🔧 SETTINGS AND TOOLING — decided, do not re-derive
- ✅ **USE `nav2_forward.yaml`, ⛔ NOT `nav2_mapped.yaml`.** Localization is DEAD (0 accepted of 20 on
  the map's own bag) ⇒ the mapped config would plan against a pose that does not exist. Odom frame only.
- ✅ **0.25 m/s throughout — ALREADY THE CONFIG DEFAULT** (`max_vel_x: 0.25`, `max_vel_theta: 0.5`).
  No tuning needed, **and it is the speed where the 09-15/16 data was cleanest** (odom scale exact,
  wheels matched ±1.35%, guard well clear of the noise).
- ✅ **NO NEW TOOL NEEDED.** T3 is a Nav2 goal — `ros2 action send_goal /navigate_to_pose` — not
  another `t*_test.py`.
- ⚠️ **Phase 2 is the FIRST TIME THE FOUR SPEED LOOPS MUST DISAGREE ON PURPOSE.** Every 09-15/16 run
  was a straight line. This vehicle **scrubs hard in a spin** (2.6-7.2 m/s², 4 independent loops that
  do not share load). **Read `bldc_can/evidence/turn_asym_20260914.csv` / `turn_lr_20260914.csv`
  before setting yaw rate.**

### ⚠️ STANDING GATES EVERY ARMED SESSION
`tools/preflight_scan_check.py` at the start position · `eph` vs the 5.0 m `COM_POS_FS_EPH` bar
(**~45-60 min of budget per bridge restart**; restarting `rover-ekf-bridge` resets the drift) ·
**start the bridge before, STOP IT AFTER** · hand on **ch12** · ⛔ registration dies on an FC reboot
and the node does not notice — **prove it by the LOG LINE, never by a message rate** (→
`project_rover_autonav` 09-15/16).

## 🗄 REMOVED 2026-09-19 — THE TWO 09-12 "START HERE" BLOCKS. **THEIR PREMISE IS DEAD.**

⛔⛔ **They were built on "PX4's speed controller cannot work against a TORQUE actuator", and posed an
operator decision between (A) duty mode and (B) rebuilding the loop in the companion. THAT WHOLE
FRAME WAS OVERTAKEN ON 09-13:** all four ESCs were migrated to **RPM mode**, tuned and
floor-validated under load, `RO_MAX_THR_SPEED` went 0.60 → **4.93**, and **G2 closed end to end.**
🔑 **Every torque-mode rule those blocks taught is HISTORY — including "DURATION is the control, not
stick position".** ⛔ Do not quote them; that is exactly what the deleted text invited.
Historical detail, if ever needed: `project_rover_autonav` 09-12 and 09-13.

### ⬜ WHAT SURVIVED THOSE BLOCKS — these are still open, and nothing else there was
1. ⬜ **ESC zero-dropout — the FLOOR figure is still missing.** Stands gave **54 ERPM ≈ 0.21 m/s**;
   never measured under load. `field_measure.py dropout`.
2. 🔴 **R5.4: the reflex still only ZEROES the setpoint — it cannot COMMAND a brake.** In RPM mode
   that zeroing is a real brake (and the duty-0 short brake finishes the stop), so this is no longer
   urgent — but the durable fix is unbuilt. `UAVCAN_EC_FUNC6`=301 is set and persisted and stays
   **INERT until all four VESCs read RawCommand idx 5** (`max(idx4, idx5)`, **bounds-check
   `cmd.len`**) — that is a **firmware change, USB only, one session per ESC.**
3. ⚠️ **T1 NEEDS RE-EXAMINING, NOT RE-TICKING.** Its recorded pass predates the RPM migration AND
   the odometry scale/sign fixes, so it was adjudicated with a ruler we have since replaced.
   ⛔ Do not treat that tick as evidence.
4. ⬜ **S1 is INCONCLUSIVE, not failed — ch12 was never pressed.** Settle what S1 means first
   (**PX4 kill ≠ disarm**), then run it and actually press **ch12**.
5. ⬜ The second coast run — tracked in the PARKED brake block above, not duplicated here.

### 🔑 MEASUREMENT RULES THAT OUTLIVED THE TORQUE ERA — read before any floor session
⛔ **Park ~2.5 m from a FLAT, SQUARE surface.** Gate on **jitter < 0.05 m AND spread < 0.05 m** before
driving. A sofa gave 0.074 m, then 2.069 m as the corridor flickered between two surfaces.
⛔ **`/scan` does not track beyond ~3 m** (the 0.275 m corridor spans ±4° there) ⇒ **a silent reflex
out there means BLIND, not clear.** Gate safety on `/scan` clearance, never on `/odom`.
🔑 **A high NaN count is NOT blindness** — the corridor filter drops everything outside 0.275 m by
design. Judge on whole-scan health plus the nearest in-corridor return.
🔑 **Gate every moving test on MEASURED speed, never the commanded value.**
🔧 **Tooling: `tools/field_measure.py` (nine routines, suggests and never writes) + `rover_diag.py`.**
⚠️ **Five analyser defects were found by checking output against runs readable by eye — all the same
family, a confident number from data that did not support it. Distrust any unchecked analyser output.**
⚠️ **`COM_DISARM_PRFLT` resets to 10 s on the FC — ASK before changing it.** Budget per bridge
restart is **~45-60 min of `eph`**, not the "~35 min" the deleted block claimed.

## 🗄 COMPRESSED 2026-09-19 — the 09-10 "START HERE" block. **Its three action items are all CLOSED**
(G0 09-11 · G2 09-13 · G3 venue 09-14 / T2 09-16), and its G0 evidence is duplicated in the
WITHDRAWN section below. **Two things from it are still worth having:**
🔴 **`fx` = 304.05 @ 640×360** — the real value; **409.85 @ 848×480 is stale everywhere it appears.**
🔴 **`/scan_3d` read 0.00 Hz while `rover-scan-3d` read `active`** — the documented trap. ⛔ **`active`
proves nothing; measure rates.** Needed for G4.

### 🔑 THE DOCTRINE THAT STILL STANDS: RUN THE GATES IN DEPENDENCY ORDER, NOT NUMERIC ORDER — **G0 → G2 → G3**, and let **G1 wait**.
`autonomy_plan.md` §5 is explicit that **M2 needs NO map and NO localization**, and warns in its own
words that *"anything that defers M2 behind mapping work is deferring the only autonomy currently
within reach."* G1 (localization) is the deadest item on the board — **0 accepted fixes out of 20** —
and it gates **only M3**. Nothing in M2 touches it. ⇒ **Do not put localization in front of M2.**

*(The three gate items that stood here — G0 geometry, G2 motion truth, G3 venue — are **all closed**
and were removed 09-19. G0 detail → the WITHDRAWN section below · G2 → `project_rover_autonav` 09-13
· G3 → `bldc_can/evidence/t2_autonav_floor_20260916.md`. ⛔ **One claim in the deleted G2 item was
already twice superseded** — "the brake measures 0.69 m/s², 0.30–0.50 m from ~0.8 m/s". Current:
**1.28 m/s², 0.19 m.**)*

⛔ **Before any armed autonomous campaign: re-confirm S1 (kill switch)** — inviolable rule 4, and it
is due anyway after the ESC firmware change. **Start `rover-ekf-bridge` first, FLOOR ONLY, stop after.**

## ⏸ [WFB-NG — PARKED, NOT HIGH PRIORITY] — added 2026-07-30
> ⚠️ **Heading corrected 09-19: this block used to say "HIGH PRIORITY — WORK THIS BLOCK FIRST",
> which contradicted §4 above, where the whole block is PARKED.** The radio work is DONE bar one
> hardware action (**#22, reseat drone NIC-A ant0**). ⛔ Do not let this block set the agenda.
> Measured, not theorised. Raw numbers: [[reference_wfb_ng]]. **Read W0 before touching anything.**

### ⚡⚡ 2026-07-31 RESOLUTION — most of this block is now CLOSED. Read this first.
A **20 min simultaneous both-ends run under full video load** settled it. Numbers: [[reference_wfb_ng]].

**THE ONLY WFB ACTION LEFT: 🔴 reseat/replace the drone's NIC-A ant0 u.FL + pigtail + antenna.**
It is ~20 dB deaf (−48.5 vs −28.3 dBm, steady over 224 samples / 20 min). The GS reads both its
antennas identical, so the defect is on the **drone's RX side** — exactly the direction that loses
packets. Re-measure via 8102 immediately after.

⛔ **CLOSED 07-31, COMPRESSED 09-19 — these are the NEGATIVE results; do not re-propose any of them:**
**W1** GS EAGAIN socket overflow (relay lost 4 video blocks of 341 057 in 20 min — dead) · **W2.1**
trim MAVLink rates (downlink already ~100%; airtime only) · **W2.2** raise GS `rx_ring_size` (nothing
overflows — leave at 2 MB) · **W2.3** the 176→26 kbit/s drop (does not reproduce; 99.86-99.99%) ·
**todo #4** GS TX power (already maxed, 30 dBm, regdom BO permits 30 — nothing to turn up).
✅ **W2.4 / #6** hardcoded peer `10.5.6.50` is **CORRECT** — QGC laptop on the relay's Wi-Fi Direct
hotspot (`p2p-wlan0-0`, SSID `vind_rely`, ch149, relay 10.5.6.101/24). 🔑 **Ping fails = Windows
firewall, NOT a break.**
🔴 **W3** antenna imbalance = **ROOT CAUSE**, and only **NIC-A ant0** is bad (NIC-B is 3 dB, not 9).

**Still open beyond the antenna:** (a) uplink GS→drone loses **13.57%** of MAVLink payload /
**5.46%** tunnel, continuous not bursty — expected to improve when the antenna is fixed, re-measure
before doing anything else; (b) relay TX to the laptop at **31 dBm on ch149** shares a chassis with
the WFB RX on ch161 — possible co-located desense, untested; (c) `journalctl -u wifibroadcast@gs`
still unread — **`vind-admin` is in `sudo` but sudo needs a password**, so journald hides the unit.

⚠️ **Method note that cost a week:** compare payload **`tx.incoming` → `rx.out`** across the two
APIs. Do NOT use `rx.all` (the drone double-counts across 4 antennas — makes 13.6% look like 2.4%),
and do NOT infer radio health from MAVLink message rates at two `tcp:5760` endpoints (that path
includes mavlink-router and PX4 stream config — it is what produced the bogus "15% downlink").

### W0. ⛔ FIRST PRINCIPLE — the drone radio is HEALTHY. Stop blaming WFB by default.
First real link measurement (07-30, WFB JSON API on `127.0.0.1:8102`):
- **0 dropped / 0 truncated / 0 fec_timeouts over 117,570 video packets** (whole session, cumulative)
- TX latency 6-35 us avg, 361 us worst | RF temps 32-39 C | `throttled=0x0`
- **~34% airtime** of a 13 Mbit/s MCS1 PHY (~367 pkt/s, ~3.9 Mbit/s injected) — headroom exists
- `mavlink tx`: offers 179 kbit/s, injects 549 kbit/s (k=1/n=3), **drops NOTHING**

**When video breaks, WFB is sitting on an EMPTY input queue.** The 07-30 session proved the FPV
outage was a dead camera while the radio was flawless. **Suspect the source before the link.**
How to check in 5 s: TCP-connect `127.0.0.1:8102`, read newline-delimited JSON, look at
`video tx . packets.incoming[0]`. If it is 0/s, the radio is fine and the camera is dead.
(Counters are `[per_second, cumulative]`. Do NOT use the `wfb-cli` TUI for this.)

### W3. 🔴🔴 RX antenna imbalance — **ROOT CAUSE, and it is ONE chain on ONE card** (rev. 07-31)
20 min / 224 samples, steady throughout ⇒ **not a fade**:

| chain | avg rssi | verdict |
|---|---|---|
| NIC-A **ant0** | **−48.5 dBm** (min −55) | 🔴 **20.2 dB down — FIX THIS** |
| NIC-A ant1 | −28.3 dBm | healthy |
| NIC-B ant256 | −35.0 dBm | 3.0 dB gap, acceptable |
| NIC-B ant257 | −32.0 dBm | healthy |

**⚠️ Corrects the 07-30 table above: NIC-B is 3 dB out, NOT 9 dB. Only NIC-A ant0 is broken.**
The GS reads **both** its own antennas identical ⇒ the defect is **entirely on the drone's RX
side** — which is exactly the direction losing packets (13.57% uplink MAVLink loss vs 0.14%
downlink). 20 dB ≈ 10× range. **Action: reseat u.FL on NIC-A ant0, check pigtail + antenna, then
re-measure on 8102.** This is the whole remaining WFB job.

### W5. MTU margin is thin (hardening, no live fault)
`radio_mtu = 1445`; ffmpeg RTP averages 1354 B and `truncated=0` over 117k packets. But ffmpeg's RTP
default `pkt_size` is **1472 (> 1445)** with no guaranteed margin. Pin `-pkt_size 1400` when the
vision-node flags are applied (session item 3).

### W6. Radio headroom is now MEASURED — unblocks the 07-28 bitrate item
That item recorded headroom as "NEVER MEASURED". It is now: **~34% airtime used of a 13 Mbit/s MCS1
PHY.** There IS room to raise video bitrate — go straight ahead; the old "trim MAVLink first"
precondition is deleted (it was never a fix). ⚠️ But note the real constraint is **CPU, not radio**:
software x264 already needs ~80-95% of a core, see `~/ros2_ws/docs/vision_streaming.md`.

---

## [WFB-NG FIXES] — ⏸ PARKED (the "after OS backup" gate no longer applies)

### 1. Fix GS clock / NTP for real (Relay station vind-rly) — RECURRED 2026-07-11
2026-03-15 fix (`timedatectl set-ntp true` + restart timesyncd) did NOT hold: relay has no RTC and no internet uplink, so `systemd-timesyncd` can never reach `ntp.ubuntu.com` (DNS/network unreachable) and clock drifts to boot-default every power cycle.
Real fix needs a **local NTP server** the relay can actually reach — companion (10.5.5.87) is reachable from relay (10.5.5.77) over the WFB tunnel and has real internet+correct time. Plan: install `chrony` on companion in server mode, allow 10.5.5.0/24, then point relay's `systemd-timesyncd` `NTP=` at 10.5.5.87.
Attempted 2026-07-11, aborted mid-install — see `project_relay_ntp_setup.md` and `project_companion_network_degraded.md`.

### 5. Fix channel reference in PXLABS_qgroundcontrol docs (local edit + push)
ARCHITECTURE.md and DEVELOPMENT.md both say `ch157` — correct value is **ch161**.
Clone repo, search `ch157` / `channel 157`, replace with `ch161` in both files, then push.
Repo: https://github.com/ArvinVeiyon/PXLABS_qgroundcontrol (branch: master)

### 8. Camera preset/RC migration — QGC half ✅ DONE, companion half = multicam Phase D
QGC presets: DONE 2026-07-19 (phase C — hardcoded video0-3 picker + front/bottom buttons
replaced by dynamic camera-list/alias UI; guard implemented in v2.0, discovery fixed v2.1).
REMAINING (Phase D, companion, go-ahead given — see project_vision_multicam_upgrade.md):
migrate to aliases/usbcam ids via v2.1 resolver:
- ros2_ws/src/rc_control/camera_sw_params.yaml:10-11 (front=/dev/video0, bottom=/dev/video2)
- ros2_ws/src/rc_control/config/rc_mapping.yaml:55-56 (same)
  → CH9 plan per design doc: low=FPV primary, mid=FPV+NAV-COLOR PiP, high=spare
- ros2_ws/src/optical_flow/optical_flow/optical_flow_node1.py:36 (/dev/video2)
- ros2_ws/src/optical_flow/optical_flow/optical_flow_node.py:36 (/dev/video3)
  → make device a ROS param (id/alias); WHICH camera optflow should use = open user
    decision (its original camera was physically removed).
  ⚠️ The "= Orbbec IR" annotations on those paths are NOT reliable — the Orbbec only owns
  /dev/videoN while `rover-camera.service` is STOPPED. With the wrapper running these paths
  hit whatever else is there (or nothing). The reason to migrate is that /dev/videoN is
  unstable, full stop — not that it specifically lands on the Orbbec.
✅ Cleanup DONE 2026-07-27: /etc/udev/rules.d/99-usb-cameras.rules **RETIRED IN PLACE**, not
deleted — the file now contains only a comment block explaining why (and a pointer to the
still-stale rc_control paths above). Repo copy restored in codex-work `b80034b` after
`d64850d` committed it empty.

### 8b. Vision open items — added 2026-07-28 (audit found these tracked NOWHERE)
From `~/ros2_ws/docs/vision_streaming.md`; all three were agreed/designed but never filed:
- **(a) backoff reset on the stall path** — `ros2_ws/src/vision_streaming/vision_streaming/
  vision_streaming_node.py:325-326` still resets `backoff_s` to 2 s after a run >60 s that
  **ended in a stall**. Longer waits are what actually recover the camera (16 s → 256 s of
  good video; 2 s → 14 s, dead), so the node earns a working delay and throws it away.
  Agreed fix = do NOT reset on the stall path. **STILL UNAPPLIED, re-verified live 07-30.**
  Item 2 of that list (settle delay with the device closed after a kill) is also unapplied.
  - **❌ CLOSED 2026-07-30 — item 3 (escalate to a USB port reset of 6-2 after N consecutive
    zero-frame starts) is NOT VIABLE. Do not build it.** Measured against a live-wedged LG:
    uvcvideo unbind/rebind → 0 frames; full USB de-authorize/re-authorize → 0 frames;
    retry at 640x480 → 0 frames; GStreamer → 0 buffers. **No software reset recovers this
    camera** — only physical VBUS removal. Replace the idea with: cap consecutive cold-start
    failures, then log a clear "camera requires physical replug" ERROR instead of looping
    silently for 20 minutes. → `~/ros2_ws/docs/vision_streaming.md`
- **(b) USB autosuspend** — `/sys/bus/usb/devices/6-2/power/control` is still `auto`
  (2000 ms). Pin to `on` via udev. "Fix regardless" per the 07-27 evening finding.
  **Priority DOWN 07-30**: hygiene only, already tested and NOT a cause, and the camera on 6-2
  has since been swapped. Do it if a udev rule is being written anyway; don't make a job of it.
- **(c) vision_config_manager v2.3.0 — bitrate control** (feature, not a fix; user's idea,
  agreed, designed, NOT started). Companion half: optional `--bitrate` on `set-cam-params`
  (MUST stay optional — the shipped QGC build calls it without); `update_cam_params_config()`
  gains `bitrate=None`; `list --json` gains `active.settings.{primary,secondary}` so QGC can
  prefill. QGC half is theirs. Constraint: video FEC is k=8/n=12 (50% overhead). ⚠️ **"Radio headroom
  has never been measured" — CORRECTED 09-19: W6 measured it at ~34% airtime of a 13 Mbit/s MCS1
  PHY, so there IS room and the old "measure first" precondition is met.** The binding constraint is
  **CPU** (software x264 ≈ 80-95% of a core). Cheaper first lever, still unmeasured:
  `-preset ultrafast` → `veryfast` (better quality at the SAME bitrate, zero extra radio load).
  Test one lever at a time.
  ⚠️ Do NOT hand-edit the conf as a workaround — [[feedback_camera_qgc_only]].

---

## [ROVER AUTONAV] — added 2026-07-20 (see project_rover_autonav.md)

### 17. Delete camera_sw_node_obsolute.py (added 2026-07-21) — ⚠️ **STILL PRESENT, verified 09-19**
🔑 **Path corrected 09-19 — the one recorded here was wrong** (missing the inner package dir), which
is why it may have looked done. It is at **`src/rc_control/rc_control/camera_sw_node_obsolute.py`**,
with a stale build copy at `build/rc_control/build/lib/rc_control/`.
`src/rc_control/camera_sw_node_obsolute.py` (node `camera_node_sw`) logged all 18 RC channels at INFO
on every ~50 Hz callback — ~950 lines/s, which is where the 18 GB of `~/.ros/log` came from. It is not
running (live `rc_control_node` is clean) but should be removed so it cannot be launched by accident.
Local edits from the April STL-19 work were saved to `~/codex-work/ldlidar_stl_local_edits_20260417.patch`
when the unused `ldlidar_stl_ros2` clone was removed the same day.

### 20. Revisit RO_YAW_RATE_P / RO_YAW_RATE_I after a real floor run (added 2026-07-21)
⚠️ **The "← NEXT ACTION" marker on this item was stale and has been removed** — it dated from
2026-07-21 and the plan has moved to the G-gates. S3 (yaw open/closed loop) is already solved.
This is a tuning refinement, not the next thing to do.
**FIELD CHECKLIST tracked at `~/ros2_ws/docs/yaw_tuning_session.md` (ros2_ws main @ 8f84bf1)** — preconditions,
bring-up, baseline-then-tune, opportunistic gyro-yaw + /scan checks, safety, teardown, results-log table.
CONFIRMED NEEDED by the L2 run: armed yaw drove wheels MUCH harder (~700-850 rpm) than forward (~156 rpm).
Those gains were tuned while `RD_WHEEL_TRACK` was 0.43 — a ~39% oversized track, which sized the
commanded wheel differential (Δv = ω × track). The allocation they were implicitly compensating for
has changed now that it is 0.31. The gyro-closed rate loop hides much of this in steady state, so
expect the difference mainly in feedforward/transient response. Re-check after a real floor run.

### 21. Use the camera IMU alongside the FC IMUs (user idea, 2026-07-21) — ✅ **ITEM 1 SHIPPED**
The Gemini 336L has its own IMU (`/camera/accel/sample`, `/camera/gyro/sample`; enable with
`enable_accel:=true enable_gyro:=true`, now on by default in `rover-camera.service`). Ranked by
value, honestly:
1. ✅✅ **SHIPPED 2026-08-09 AND VERIFIED — `yaw_source: camera_gyro` is LIVE in `rover_odometry`.**
   ⚠️ **Corrected 09-19: this item was still filed as OPEN, and the "historical list" note below
   asserted "#21 gyro-yaw remains OPEN". It is not.** Skid-steer yaw from wheel speeds is inherently
   bad — all four wheels *must* slip laterally to turn — so wheels now carry forward distance only
   and the **camera** gyro carries heading. 🔴 **It went to the CAMERA gyro, not the FC's, because
   the FC heading is UNUSABLE** (it is the EKF's fused yaw, not the gyro; 2 untested suspects,
   `bmm350` and GPS, and the DRONE shares that FC).
   ⏭ **The one piece left is the QUEUED index item:** bridge `vehicle_angular_velocity` to DDS
   (`dds_topics.yaml:60`) to decouple odometry from the camera — **needs an FC flash.**
   ⛔ Verify any reflash by GIT HASH (our own build carries the hardfault fix).
2. **Independent cross-check of FC IMU health.** The camera IMU is a genuinely independent gravity
   reference — it is what let the camera mount pitch/roll be measured tonight. Useful for sanity-
   checking accel calibration (cf. the "accel 0 inconsistency" episode), where the FC's own IMUs
   cannot arbitrate between themselves.
3. **VIO (visual-inertial odometry)** — the ambitious option: camera IMU + depth/colour for
   drift-free-ish motion estimation that survives wheel slip entirely. Real payoff for GPS-denied
   nav, but heavy on the RPi5, which already shares compute with vision streaming (`/scan` alone
   drops to ~13-19 Hz under load). Do NOT start here; revisit only after Nav2 works.
4. **Feeding the camera IMU into EKF2 as an extra IMU: not practical.** PX4 EKF2 has no external-IMU
   input path; only external *vision* pose/velocity, which is what `rover_ekf_bridge` already uses.
**Recommendation: do (1) first — it is cheap, principled and helps SLAM immediately. Keep (2) as a
diagnostic. Defer (3). Drop (4).**

### 14. Rotate the GitHub PAT embedded in the codex-work remote URL
`~/codex-work/.git/config` holds a plaintext `ghp_...` token. Rotate it and switch that remote to SSH.
See `project_codexwork_token_in_remote.md`.

---

## [ROVER OUTDOOR — PRIMARY TARGET] — added 2026-07-23 (see ros2_ws/docs/roadmap.md §4, O1-O5)
Goal: rover drives itself to a **GPS waypoint** in open outdoor space, **360° obstacle avoidance**, no
operator. Indoor GPS-denied (L0-L4 done, L5/L6 next) is the stepping-stone + GPS-loss fallback. These
outdoor tasks come AFTER the indoor brain is proven (L5+L6). Both O1 and O2 need hardware the user is fitting.

### O1. Re-integrate the STL-19 360° LiDAR (blocked on getting the unit back)
LDRobot STL-19: 360° 2D, **0.02-25 m, ~10 Hz** LaserScan; UART **ttyAMA3 @ 230400, RX-only** (lidar TX →
RPi RX, no commands); `dtoverlay=uart3-pi5`, TF `base_link→base_laser` 0.18 m (re-measure mount).
- Hardware went to another team 2026-04-17 → **need the physical unit back first**.
- Driver `ldlidar_stl_ros2` (node LD19) already in `ros2_ws/src` with BOTH upstream fixes applied
  (pthread include + hardcoded `/dev/ttyAMA3`). Local edits: `codex-work/ldlidar_stl_local_edits_20260417.patch`.
- Steps: reconnect hw → enable `ttyAMA3` → build → install/enable `ldlidar.service` (unit template in
  `codex-work/ldlidar_stl19_install_guide.md`).
- ⚠️ **`/scan` conflict**: lidar driver AND `depth_to_scan` both publish `/scan`. Fix: **lidar owns `/scan`**
  (SLAM + 360° costmap); remap depth to **`/scan_depth`** as a separate Nav2 costmap layer.

### O2. Integrate the DroneCAN GPS (blocked on module choice + fitting)
- DroneCAN/UAVCAN bus already live (VESC ESCs addr 10-13) → GPS is one more node on it.
- PX4: enable `UAVCAN_ENABLE` (GPS subclass) + set `EKF2_GPS_CTRL` to fuse GPS (**FC param path, MAVLink-only,
  not DDS**). Verify `/fmu/out/vehicle_gps_position` populates + `vehicle_global_position` goes valid.
- Nav2: outdoor GPS nav via `navsat_transform_node` (robot_localization) or Nav2 GPS waypoint follower.
- **Module make/model: TBD — user to confirm** (sets the exact DroneCAN GPS driver params).

### O3. Outdoor 2D-lidar SLAM (builds on L6)
slam_toolbox on the lidar `/scan` (2D-lidar SLAM is far better than depth-derived scan) + fold the 336L
forward depth in as a costmap layer for low/overhang obstacles the flat 2D plane misses.

### O4. Outdoor Nav2 with GPS waypoints (builds on L5)
`navsat_transform` / GPS-waypoint-follower launch config (distinct from the indoor SLAM launch); global
plan to a GPS coordinate, local costmap from lidar+depth, controller → `/cmd_vel` → autonav_mode.

### O5. Outdoor safety hardening (extends L7)
Terrain handling, dynamic obstacles, and **GPS-loss failsafe → wheel/gyro dead-reckoning + reflex stop,
never an uncontrolled state**. Caveat to design around: STL-19 is a **2D** lidar (fixed-height plane) — on
uneven terrain it can miss low obstacles or read a slope as a wall; the forward 3D 336L covers that gap.

## OPEN ITEMS RAISED 2026-07-26 (the "closed today" log has been removed)

### Opened today
*(Item 1 removed 09-19 — `dtoverlay=disable-wifi` was verified closed 09-10, nothing further.)*
2. **Establish what NIC RELAY-STN actually has.** `wlx90de80d824d6` is on the companion now, so the
   relay's documented uplink is gone and `.221` does not answer. See [[project_relay2_relaystn]].
   🔴 **09-03: `wlx90de80d824d6` IS NOT ON THE COMPANION EITHER — `0bda:c811` is absent from
   `lsusb`.** The companion uplink is a **TP-Link Archer T2U PLUS `2357:0120` (RTL8821AU)** =
   `wlx8c86dd5beed9`. **So that adapter is loose/elsewhere — find the physical hardware before
   planning around it.** → [[project_boxb_pcie_usb]], [[reference_this_machine]]
3. **Fit the printed camera bracket, then run the 4-step as-built check** at the foot of
   `ros2_ws/launch/depth_to_scan.launch.py` (measure to the left IR imager, re-derive pitch/roll from
   `/camera/accel/sample`, restart rover-scan, tape-measure a `/scan` return). **Blocks L5.**
4. **Crop the rover's own deck out of the depth cloud before the L5 Nav2 voxel layer** — at cam_z
   0.305 with cam_x 0 the top plate fills the bottom ~third of the frame (11.5°/83 px). Harmless for
   `/scan` (±20 px band) but Nav2 would mark a permanent obstacle around its own nose.
5. **Profile `wheel_odometry_node`** — 26.9% CPU for 100 Hz arithmetic is high, and it is in the
   autonomy path where L5 will need the headroom. Suspect the same unthrottled per-message logging
   pattern as tfmini / ros2_ws todo #17.
6. ✅ **CONFIRMED 2026-09-09/10 — the VESCs DO doze off, and it is reproducible.** Measured
   `esc_count 5, esc_online_flags 8` (bit 3 only = addr 13 rear-left) at rest, **before and after an
   FC reboot**; the other three were absent from the bus until the operator powered them for the
   brake test, after which all four reported. ⚠️ **Still UNKNOWN and still the thing that matters:
   can they sleep again WHILE ARMED?** If so `/odom` drops out under the EKF bridge, in the safety
   path. 🔑 **`esc_online_flags` is the cheap check — read it before trusting per-wheel ESC data,
   and never read a missing ESC as a silent one.**
7. **Delete `/var/lib/aide/aide.db.feb22.bak`** (117 MB) once the Feb baseline is definitely not wanted.
8. **Fix `system_files_sync`'s armed-skip** — it skips entirely when the FC reports armed, so it is
   an unreliable backstop during work sessions (this is how the WFB_NICS mitigation was lost on 07-25).

## 2026-07-28 — camera bitrate control (OPEN, agreed, not started)
⚠️ **Deduplicated 09-19 — this was a second copy of item 8b(c) above. Kept here, because this is the
version with the SYMPTOM:** raising the camera to 1280x720 left `bitrate = 2000K`, dropping
bits/pixel 0.129 → 0.072 (soft picture). Design + constraints are in 8b(c) and
`~/ros2_ws/docs/vision_streaming.md`; ⛔ don't maintain two lists.
✅ **One constraint there is now ANSWERED: "radio headroom UNMEASURED" is false** — W6 measured
**~34% airtime of a 13 Mbit/s MCS1 PHY.** There is room. 🔑 The binding constraint is **CPU**, and
the cheaper first lever is still `-preset ultrafast` → `veryfast` (better quality at the same
bitrate, zero extra radio load). ⛔ Do NOT hand-edit the conf — [[feedback_camera_qgc_only]].

---

## OPEN ITEMS RAISED 2026-07-30 (the "closed/killed today" log has been removed)

⚠️ **One retraction worth keeping:** *"See3CAM only does ~16 fps on the 480M bus"* was **WRONG**. It
does a real **60 fps** at 720p MJPG over USB 2.0 — the 16 fps was auto-exposure in a dark room.
**You do NOT need a blue USB3 port for full frame rate.** Correct this if it resurfaces anywhere.

### Opened today
1. ✅ **Camera swap — SOAK PASSED 07-31 (compressed 09-19).** See3CAM_CU135 on port 6-2 streamed
   1280x720 for a **continuous 41.8 min**: PID unchanged across 40 health samples, `NRestarts=0`,
   **0 errors / 0 stalls / 0 dup-padding**, 62.6-65.3 °C, `throttled=0x0`, and the relay delivered
   **234 331 of 234 362** video packets (99.99%) — so the picture genuinely moved, not just RTP.
   ⏭ **ONLY THE REBOOT CHECK REMAINS.** ⚠️ Load avg 4-7 on 4 cores from software x264 — stable, but
   it is why **CPU, not radio, is the real video constraint.**
   ⚠️ **A packet-flow check is NOT sufficient proof on its own** — see opened-item 9.
   ⚠️ **Since superseded in practice: the LG Smart Cam is the CURRENT FPV camera**, swapped from QGC.
2. **Discriminate LG-faulty vs connector-6-2-bad-under-load.** The swap confounds them: See3CAM
   100 mA vs LG 500 mA. Test = put the LG in the free port **`4-1`** (different host controller and
   power path) and soak. **Blocked: enclosure is assembled.** Do it next time it's open.
3. **Apply the vision_streaming_node.py fixes** (all verified live 07-30, all unapplied):
   - `-g 30` + `-tune zerolatency` + `-pkt_size 1400` — **highest value**; x264 default keyint is
     250 frames ≈ 8.3 s at 30 fps, so one lost keyframe smears for up to 8 s over the radio.
   - wire the `fps` conf key through to `-framerate` (currently read by QGC, **never used**).
   - `frame=0` counts as progress → 30 s grace silently becomes ~50 s.
   - backoff reset on the stall path (= item 8b(a)).
   - `rclpy.shutdown()` RCLError — fires on **every QGC camera change**, dumps a traceback exactly
     when you'd be checking whether the swap worked.
   - cap consecutive cold-start failures → log "camera requires physical replug" instead of looping.
*(Items 4 and 5 removed 09-19: **4** was a superseded copy of the antenna table that just pointed at
W3 above, and **5** was the already-deleted "trim PX4 MAVLink stream rates" — ⛔ which stays deleted:
it fixes nothing, downlink already delivers ~100%, and the bitrate item no longer depends on it.)*
6. **Verify the hardcoded GS peer `10.5.6.50`** in `/etc/wifibroadcast.cfg` (`gs_video` :5600,
   `gs_mavlink` :14550) — fixed IP on a subnet unrelated to the 10.5.5.0/24 tunnel. Wrong-IP
   presents as "WFB broken" while the radio is flawless. Check as part of todo #4.
7. **Boot-time clock is wrong until NTP steps it.** `systemd` claimed services started `Jul 29
   00:31`, `last -x reboot` said `Jul 25 11:36`, `uptime -s` said `Jul 30 22:41:45` — all three
   disagree on the same boot. **Journal timestamps around a boot are not trustworthy**; don't
   correlate a WFB event against a vision event across a reboot without checking. Companion has
   internet + NTP synced, so this is boot-window skew only. Related: [[project_relay_ntp_setup]].
8. **`camera_name` fallback in the conf is dangerous.** `/dev/video0` did not exist for most of
   07-30 (nodes were video8/video9). If sysfs `usbcam-*` resolution ever fails, ffmpeg is pointed
   at a node that is not the camera. Consider failing loudly instead of falling back.
9. **Verification method note (about MY checking, not a hardware bug).** A drone-side packet-flow
   check (`wfb_tx video incoming` ~200 pkt/s, 0 drops) does not by itself prove the picture is
   moving. Confirm at the GS when it matters. **No dup-padding problem has ever been observed on
   the See3CAM** — it ran 11:49 clean and the user saw a normal moving picture throughout.

---

## ✅ Historical completed/closed list — REMOVED 2026-09-10

The 2026-08-13 dump of finished items has been deleted; it was a record of work already done and was
not being read. ⚠️ **Its surviving note said "`#21 gyro-yaw` remains OPEN" — WRONG, corrected 09-19:
`yaw_source: camera_gyro` shipped 08-09.** See item 21 above; only the DDS `vehicle_angular_velocity`
bridge is left, and that needs an FC flash.

## 🔧 PX4 PARAMETER AUDIT — 2026-08-14
> 📄 **FULL AUDIT + CHANGE LOG: `~/ros2_ws/docs/px4_param_audit.md`** (every value as read, the
> verified-correct list, findings P1-P9, and the derivations). **Pull from there — not duplicated here.**
> Applied changes also land in `setup_manual.md` §A7, the canonical param changelog.

**Open items:** ✅ **P1 `RO_MAX_THR_SPEED` — CLOSED 09-13, removed from the open list 09-19.** The
sweep it asked for was answered in the negative under torque mode, and the RPM migration then made
the question moot: the value is now **4.93**, floor-validated. ⛔ Don't re-run an 08-14 sweep. ·
P4 `RO_SPEED_TH` −1 would kill the 0.14 floor but is **GATED ON THE ESC-DROPOUT FIX** ·
~~P5 `RC_MAP_KILL_SW`=12 vs docs "ch8"~~ ✅ **DONE 2026-09-12 — docs/tools fixed (`ros2_ws` `6506bdb`).** 🔴 **It had already cost an armed run before anyone actioned it: the operator was told to hit ch8, moved ch5 (ARM) instead, and S1 came back inconclusive.** · P6 read `si_motor_poles` ×4
in VESC Tool — ✅ **SETTLED 09-12, leave it alone** (`si_motor_poles` is a LINKED PAIR; "fixing"
poles silently HALVES `/odom`) · P8 outdoor/M4 params · P9 not audited: `EKF2_*` (SHARED WITH
DRONE), sensor/RC cal, per-ESC output index.

⛔ **SUPERSEDED — DO NOT RE-APPLY.** `RO_DECEL_LIM` 0.5 / `RO_ACCEL_LIM` 0.3 / `RO_SPEED_LIM` 0.60
were applied, saved and reboot-verified on 08-14 — and then **CAUSED A HARD WALL HIT IN MANUAL
DRIVE the same day and were ALL THREE REVERTED.** This entry recorded step 1 and was never updated
for step 2; read as-was it invites someone to restore the crash configuration.

✅ **READ FROM FLASH 2026-08-16, DISARMED — the reverted values are what the FC actually holds:**
`RO_ACCEL_LIM` **−1.0** · `RO_DECEL_LIM` **−1.0** · `RO_SPEED_LIM` **0.70**.
🔑 **The `param save` question (old item (c)) is CLOSED.** The FC hardfaulted and rebooted **≥9
times on 08-16**; RAM-only values cannot survive that, so the revert is provably **in flash**.
The reboot loop accidentally performed the verification nobody had run.
🔴 **SUPERSEDED 2026-09-14 — `RO_DECEL_LIM` IS NOW 5, DELIBERATELY. `RO_ACCEL_LIM` STAYS −1.**
⛔ Do NOT "restore" −1 on the strength of the paragraph above. The 08-14 crash was decel **0.5**
with `RO_MAX_THR_SPEED` **0.60** — a 1.2 s powered ramp-down. That divisor is now **4.93**, so
📏 **ramp = decel ÷ `RO_MAX_THR_SPEED`**: decel 5 ÷ 4.93 = **0.99 s** at FULL throttle, and only
0.05-0.5 s at the 3-30% stick actually used. ⛔ **Never reuse an August decel figure without
redoing that division.**
🔴 They still slew the MANUAL stick **and the collision reflex** (which publishes a fake
`ManualControlSetpoint`), so ⚠️ **re-verify the 0.69 m reflex standoff after any decel change** —
it was sized against a 0.19 m stop. 🔴 And `RO_SPEED_LIM` **does not limit Manual at all**: full
stick is 4.93 m/s, not 0.70. → [[px4_rover_control_scope]], [[scope_px4_params_by_control_flags]]

⏭ **STILL OPEN: ramp-tracking is NOT verified on the vehicle.** ⚠️ **Corrected 09-19 — this used to
read "moot while both limiters are −1". That stopped being true on 09-14, when `RO_DECEL_LIM` was
set to 5 deliberately.** There IS a ramp now, it slews the manual stick **and the reflex**, and it
has only ever been checked by **arithmetic** (09-18: +0.057 m at 0.75 m/s, worst case ~0.25 m against
0.69 m of clearance) — ⛔ **which is enough not to book floor time for it, but it is an open number,
not a measured one.** **Gate on MEASURED speed, never the command.**

---

## ✅ FC HARDFAULTS — CLOSED 2026-08-29. ⛔ DO NOT SWAP THE FC. DO NOT REOPEN THIS.

🔴 **The only live hazard, and it is a real one:** the firmware running is **OUR OWN BUILD** with the
NXP fix (PR #28141) cherry-picked. **Any reflash from upstream, or from `~/fc_firmware`, brings the
hardfaults back.** ⇒ **verify by GIT HASH, never by `flight_sw_version`.** Detail: `HARDFAULT.md`,
[[project_fc_hardfaults]].
⚠️ **3 fault logs are still on the SD card, so QGC re-announces them every boot.** That is cosmetic.

## 🗺️ 2D OCCUPANCY GRID — CHECKED 2026-08-16, CLOSED

✅ **The `house_map_v4` grid is roughly correct. ⛔ My earlier "unusable" call was WRONG.**
Method: `tools/grid_review.py`. ⛔ **Do NOT "fix" it:** `MaxGroundHeight` 0.28 is 3× the truth —
**keep 0.10**; and `NormalsSegmentation false` is what produced the ray-tracing spikes that got the
v5 reprocess rejected. **Changing either makes the grid worse, not better.**

### 🔴🔴 THE REAL CONSTRAINT IS THE ROOM, NOT THE MAP — ✅ **ANSWERED 09-14/16, kept as the reason why**
**Rover footprint 0.73 × 0.450 m ≈ 0.33 m² vs ~2 m² of open floor** (≈ a 1.4 × 1.4 m clear patch).
⚠️ **Width corrected 09-19: this said 0.56 m.** **0.450 is what the CODE uses** — verified in
`src/rover_nav2/config/nav2_forward.yaml` (both footprints are `±0.225` in y, `+0.345/−0.385` in x);
**0.560 came from a SALES QUOTATION** and four docs copied it. 🔑 No gap unless a tape disagrees.
**The rover is still ~a sixth of the room's free space**; add Nav2 inflation and there is almost
nothing to plan through.
⛔ **T2 CANNOT RUN IN *THIS ROOM*** — its spec is a clear 2 m corridor and `t2_straight_goal_test.py`
refuses to start below `distance × 1.35 + stop_distance` ≈ **3.05 m** of clearance.
✅✅ **BUT T2 IS NOT BLOCKED ANY MORE — the venue decision was taken 09-14 (CORRIDOR) and T2 PASSED
n=3 on 09-16, tape-adjudicated** (2.130 / 2.025 / 2.000 m against a 2.0 m goal). ⚠️ **The old
"OPEN GOAL-LEVEL DECISION — corridor / re-scope to 0.8 m / drop this room" was removed 09-19; it had
been answered for five days.**
🔑 **T2 ADJUDICATES ON TAPE, NOT `/odom`** — and that rule outlives the fix. ⚠️ **The "~24% under-read
at crawl" quoted here is superseded:** the error is **SPEED-DEPENDENT** — 0.946 @0.15 · 1.000 @0.25 ·
1.030 @0.75 m/s (3 tape points, 09-16). ⇒ **quote every odom distance with its speed** → `rover_odometry`.

## ⛔⛔ WITHDRAWN — "THE CAMERA WAS PHYSICALLY ROTATED" (claimed 2026-08-16)

**IT WAS NOT ROTATED. THE MOUNT IS AND WAS CORRECT. THE OPERATOR SAID SO REPEATEDLY AND HE WAS
RIGHT — DO NOT RAISE THIS AGAIN.** Withdrawn 2026-09-04, **re-measured 2026-09-10: pitch 1.436°,
roll −0.447°, |g| 9.7769, sd 0.006, 12,145 samples** (`tools/cam_mount_probe.py`). A normal level
mount. Every camera-referenced constant it declared "suspect" — `front_overhang` 0.337, `/scan`
scale 0.9845, the 0.345 m standoff, the gyro heading TF — **stands.**

🔑 **The only real defect was a STALE CONFIG, now fixed:** `depth_to_scan.launch.py` still carried
the 07-27 values (`cam_pitch` 0.0406, `cam_roll` 0.0100) from before the camera came off and went
back on the top plate. The remount landed ~1° different in each axis — ordinary variation. Updated
2026-09-10 to the measured values, **made live by the 2026-09-11 boot, and VERIFIED against a flat
wall that night — both constants held to 4.6 mm on tape.** ✅ **This sub-item is now CLOSED.**

### 📌 Surviving fact from the deleted 08-16 ESC experiment — ⚠️ **narrowed 09-19**
🔑 **What IS proven: the LEFT/RIGHT allocation.** A 0.3 rad/s yaw drove the right pair (10, 12) and
the left pair (11, 13) in opposite directions with the correct differential, matching
`actuator_function` 102=right / 101=left, and the **addr-10 sign inversion is confirmed** (09-16: the
old `-1` would have read HALF; it read 8% more).
⚠️ **What is still NOT proven: FRONT vs REAR within a side.** The index map (**10=RF 11=FL 13=RL
12=RR**) rests on config and docs, not on one turning wheel. The 08-16 episode is the warning — the
operator called the removed node "right rear" while the address that left the bus was **10** = right
**front**. ⇒ **Spin exactly one wheel before trusting any FRONT/REAR per-corner claim** — which is
exactly what the `esc_config_audit` corner-collapse work depends on.


---

# 🔗 ITEMS 22–27 — RECONCILED 2026-09-18. These were cited in `MEMORY.md` but never written here.

`MEMORY.md` pointed at `#22`, `#25`, `#26`, `#27` for weeks while this file's numbering stopped at
**21** — the references resolved to nothing. Content recovered from the index one-liners and given
real entries. 🔑 **Numbers are the contract between the two files. Never cite one here that does not
exist.** ℹ️ **#23 and #24 were never used** — the gap is deliberate, don't "fill" it.

⛔ **`5. Antenna tracker HW` — DROPPED 2026-09-19 ON THE OPERATOR'S CALL.** It was cited in
`MEMORY.md` as existing "ONLY there" while having **no content in either file** — a citation pointing
at nothing. Both mentions are now deleted. **Do not resurrect it from an old copy of the index.**

### 22. Reseat drone NIC-A ant0 — the last WFB action, and it is HARDWARE
⏸ The whole WFB block is PARKED and this is the only thing left in it. **Not a software item; do not
re-debug the radio to avoid doing it.** 🔑 Standing rule: the drone TX is healthy — when video breaks,
WFB's input queue is EMPTY ⇒ **suspect the source, not the link.** → `reference_wfb_ng.md`

### 25. `camera_sw_node` still keys `/dev/video0`
⛔ **Never key a camera by `/dev/videoN`** — the numbering reshuffles. Must key on
`usbcam-<vidpid>-<serial>-i<iface>` like the rest of the vision stack.
→ `docs/vision_streaming.md` · `project_vision_multicam_upgrade`

### 26. The Orbbec clone is GITIGNORED — a re-clone silently restores this bug
🔴 The fix is a local patch that is **not tracked**. Anyone re-cloning gets the broken tree back with
no warning. Patch is preserved at `codex-work 16665f5` — reapply after any re-clone.
⚠️ Related: `align_mode:=HW` is still **untested**; it would kill the depth-glitch class and save
~71% of a core.

### 27. Reflex still reads `/scan`, not `/scan_3d` — and it is only a param
`collision.scan_topic` is configurable; nothing needs rewriting. **The blocker is proof, not code:
it needs ONE low object that `/scan` misses**, to show the 3D topic catches what the 2D one cannot.
Gated behind G4 (wire `/scan_3d` into a Nav2 `voxel_layer`); measure R6 first.
