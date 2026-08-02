---
name: project-autonomy-plan-reframe
description: "2026-08-01 rewrite of the autonomy ladder in ros2_ws/docs/autonomy_plan.md. Redefines L0-L5 by USER OUTCOME, contradicts the old 'L0-L4 DONE' status, and names localization (Q1) as the real wall. L3 is the step-change."
metadata: 
  node_type: memory
  type: project
  originSessionId: b207e8d3-f638-4331-a8d8-7c4c291479c2
  modified: 2026-08-02T12:20:14.065Z
---

# Autonomy plan reframe — 2026-08-01

**New doc: `~/ros2_ws/docs/autonomy_plan.md` (569 lines, commits `4c7a0b5` → `7adf478` → `b7b9fa9`).**
**The Q2/L1 perception work done in the SAME session → [[project-perception-3d-costmap]].**
⚠️ Written from a crash recovery, not by the session that did it — [[feedback-crash-recovery-checkpoint]].
Companion to `docs/roadmap.md` (dated 07-23, unchanged): **roadmap = ladder/status,
autonomy_plan = what the rover does FOR A USER.**

## 🔴 IT CONTRADICTS THE OLD STATUS — the new doc is the newer thinking
Old memory + `roadmap.md`: *"L0-L4 DONE, L5 (Nav2) next."*
New `autonomy_plan.md`: **L0 ✅ · L1 🔧 IN PROGRESS · L2, L3, L4 ❌ NOT STARTED · L5 ❌ OPTIONAL.**
These are **not the same L-numbers** — the ladder was re-cut by outcome, not by component installed.
Do not mix the two numbering schemes. **Neither doc has been reconciled with the other yet.**

## The four questions, and our real state
| | Question | Provided by | State |
|---|---|---|---|
| Q1 | **Where am I?** | Localization | ❌ **THE MAIN GAP** |
| Q2 | What is around me? | Perception | ✅ forward sector only |
| Q3 | How do I get there? | Planning | 🔧 configured, unproven |
| Q4 | What if it goes wrong? | Failsafe | ⚠️ partial |

🔴 **Q1 IS THE WALL.** Obstacle avoidance is nearly solved; knowing *where the rover is* is not.
**Every capability above "drive 3 m forward" — go to a room, patrol, return home — is a localization
problem, not an avoidance problem.** Aim work there.

## The ladder by outcome
| Layer | Outcome | Operator must... |
|---|---|---|
| **L0** ✅ | Telemetry is true, velocity commands execute | drive it |
| **L1** 🔧 | Goes to a goal without hitting visible obstacles | watch it |
| **L2** | States its own trustworthiness, with reasons | watch it, but informed |
| **L3** | **Completes or safely abandons a mission alone** | **leave the room** |
| **L4** | Reports what it saw, where and when | read the report |
| **L5** | Turns a stated goal into behaviour | state a goal |

**🔴 THE STEP-CHANGE IS L3.** Everything before it produces a better-behaved remote-control vehicle.
**L3 is where the operator stops being required.**
L3 done = blocked-by-person → wait/reroute/skip · permanently blocked leg → skip and continue ·
health DEGRADED → slow down and continue · health UNSAFE → stop and hold ·
**localization lost → stop IMMEDIATELY, never drive blind** · battery low → abandon and return ·
runs to completion with the operator out of the room.
⚠️ **"Return to base" is built HERE, not inherited from PX4.** PX4 RTL targets a GPS home and on this
rover **drives there with no obstacle avoidance whatsoever.**

## Sensor roles — lidar and depth cam are COMPLEMENTARY, not redundant
**Depth camera (Gemini 336L)** sees a 3D volume ahead: table tops, desk edges, chair seats, shelves,
overhangs, low boxes, thresholds, cables, **stairs/drop-offs** — all of which a 2D lidar misses by
passing over or under. **Physically cannot see behind or beside.**
**2D lidar (STL-19)** sees one horizontal slice, but covers **behind and beside**, longer range, dark
rooms, and robust geometric SLAM.
⇒ **Depth cam = safe going forward. Lidar = safe turning/reversing.**
**A lidar-only rover drives under a table and wedges itself.** Reinforces STL-19 (O1) as necessary,
not optional — see [[project-rover-autonav]].

## L4 known risk, already costed
YOLOv8n ≈ **1-3 fps on 4 already-oversubscribed cores**. If measurement says the budget isn't there,
the honest options are: **run detection only while stopped, or add an accelerator.**
**Do NOT silently starve the control loop for it.** (Same 4-core contention as `~/ros2_ws/docs/vision_streaming.md`.)

---

## 🔴 DECISION 2026-08-01 — the STL-19 goes to the DRONE; the rover runs camera-only
**User's call, and it is well-founded.** Recorded with the reasoning so it is not re-litigated.

**Why it holds:**
- **Mapping is NOT hardware-blocked.** `docs/autonomy_plan.md` §2.2 already withdrew the claim that
  the house needs the lidar: **`slam_toolbox` needs it** (2D scan matching, 92° gives too little
  overlap) but **RTAB-Map RGB-D visual SLAM is designed for exactly this camera** — a narrow forward
  FOV is its normal case and it closes loops by *recognising places*. It emits a 3D map plus a 2D
  occupancy grid Nav2 can use. ⇒ **swap the SLAM algorithm, not the sensor.** Blocked on CONFIG + CPU.
- **The depth camera genuinely wins on the axes the user cited.** Measured/spec:
  | | STL-19 | Gemini 336L depth |
  |---|---|---|
  | Horizontal FOV | **360°** | 91.9° |
  | Vertical FOV | **0° (one plane)** | **60.7°** |
  | Angular resolution | ~0.8° (class-typical, unverified) | **0.108°/px** |
  | Points per frame | ~450 | **407 040** |
  | Range | **0.02-25 m** | usable to ~3 m |
  | Rate | ~10 Hz | 23 Hz cloud / 29 Hz `/scan_3d` |
  ⇒ **~7× finer angular resolution, ~900× the points, and 60.7° of vertical FOV against zero.**
- **Proven on hardware 08-01:** same scene, same instant — 2D `/scan` reported **1.442 m** clear,
  height-aware `/scan_3d` reported **0.254 m**. The 2D band passes straight OVER low obstacles.
- **The drone cannot substitute.** It moves in all directions and cannot adopt a "never reverse" rule.

**What the rover permanently gives up — treat as DESIGN CONSTRAINTS, not temporary gaps:**
1. **No rear or side coverage.** "Never command reverse into unseen space" becomes permanent. A rover
   that cannot reverse safely can wedge itself in a dead end.
2. **Turning sweeps unobserved space.** ⚠️ **Never clear a spin from `/scan` or `/scan_3d`** — 268°
   including the rear is unmeasurable.
3. **~3 m usable range vs 25 m.** The camera cannot see the far wall of a large room, which costs map
   quality in open spaces **even with RTAB-Map**.
**A second STL-19 removes the choice entirely and is cheap against the time already spent.**

## ⏭ ROADMAP RE-CUT that follows from it
- **O1 (STL-19 re-integration) is REMOVED from the rover ladder** → reassigned to the aerial platform
  for 360° collision. The `/scan` topic-conflict plan (lidar owns `/scan`, depth → `/scan_depth`)
  is **parked**, not deleted — it applies again only if a second unit arrives.
- **Indoor mapping switches from `slam_toolbox` to RTAB-Map.** `slam_toolbox` stays installed but is
  the wrong tool for a 92° sensor. **Not hardware-blocked — blocked on config + CPU on 4 cores.**
- **Localization (Q1) remains THE WALL.** The route is now RTAB-Map place recognition rather than
  360° geometric scan matching.
- **🔴 The gate on all of it is still yaw (#20).** Mapping is nothing but driving and turning, and the
  yaw-rate runaway is unresolved with **no yaw evidence either way**. ⛔ No armed yaw tests until
  characterised → [[project-rover-autonav]].
- Order: **#20 yaw → RTAB-Map bring-up + CPU budget → map the home → AMCL/RTAB localization → Nav2 goals.**

⚠️ **PROCESS NOTE:** I asserted "mapping the house needs the STL-19" on 08-01, which this very
document had already withdrawn in §2.2. That is the SECOND time in one evening I asserted something
the repo had already settled → [[feedback-check-docs-before-measuring]].

## 📊 RTAB-MAP CPU MEASURED 2026-08-02 00:00 — **IT DOES NOT FIT AS CONFIGURED**
Installed `ros-jazzy-rtabmap-ros` 0.22.1 (14 pkgs, apt). All required topics already publish:
`/camera/color/image_raw`+`camera_info`, `/camera/depth/image_raw`+`camera_info`.
**Measured `rtabmap_odom rgbd_odometry` ALONE, rover stationary:**
| | baseline | + rgbd_odometry |
|---|---|---|
| load1 (4 cores) | **2.25** | **9.44** (max 10.57) |
| `rgbd_odometry` CPU | — | **79.6% of a core** |
| `/scan_3d` | 23.2 Hz | **17.3 Hz** |
| `/scan` | 13.4 Hz | **7.0 Hz — HALVED** |
| `/scan` worst gap | 462 ms | **648 ms** |
**Its own throughput: update time 0.29-0.43 s (~3 Hz), delay 0.83-1.04 s (~1 SECOND of latency).**
🔴 **And this is ONLY the odometry node** — the `rtabmap` node (map + loop closure) was never started,
and **depth registration was OFF**, which RGB-D mode needs for correctness. **Real cost is higher.**
⇒ **`autonomy_plan.md`'s "blocked on configuration and CPU" is CONFIRMED, and it is CPU.**

**⏭ LEVERS, cheapest first (none tried yet):**
1. **Colour is 1280×720 and feature cost scales with it — drop to 640×360 for ~4×.** Same lever that
   took ffmpeg 78-95% → 25.7%. ⚠️ launch-time on the Orbbec ⇒ camera restart ⇒ **run the half-dead
   check afterwards** (`journalctl -u rover-camera --since -1min | grep "depth Frame - Width"`).
2. `Vis/MaxFeatures` (defaults track ~300), frame decimation, `Odom/Strategy`.
3. Separate the two problems: the ~1 s delay is probably queueing CAUSED by starvation. If it survives
   a CPU fix, 1 s is **fine for mapping** (drive slowly) and **unusable for control**.
⚠️ **`depth_registration` is FALSE and colour 1280×720 vs depth 848×480 are NOT aligned.** RGB-D needs
registration; `align_mode` is **SW** (software) ⇒ more CPU again. Launch-time only — `ros2 param set`
reports success and does nothing, same trap as `point_cloud_decimation_filter_factor`.
⚠️ **`Odom/Strategy` / `Vis/MaxFeatures` are STRING params** — `ros2 run ... -p Odom/Strategy:=0`
throws `InvalidParameterTypeException`; quoting does not help, use a params file or omit.
⚠️ Measurement hygiene: a transient `pemmican-cli` at 90-143% contaminated the first run, and
`pgrep -f rgbd_odometry` **matched its own command line** and falsely reported the node still alive.

## 📦 BAG-RECORD COST MEASURED 2026-08-02 — **CPU is fine, the SD CARD is the constraint**
Offline architecture: **record on the Pi → process on a laptop → run localization-only on the Pi.**
Mapping (features, loop closure, graph optimisation) is the expensive half; **localizing against an
existing map is far cheaper** — AMCL on a 184-beam scan is nothing like RTAB-Map.
`ros2 bag record` of color+depth images & camera_infos, `/odom`, `/tf`, `/tf_static`:
| | baseline | + bag record | (RTAB-Map for contrast) |
|---|---|---|---|
| recorder CPU | — | **42.6% of a core** | 79.6% |
| `/scan` | 13.4 Hz | **14.2 Hz** | 7.0 Hz |
| `/scan_3d` cloud | 23.2 Hz | **25.3 Hz** | 17.3 Hz |
✅ **Recording does NOT degrade the safety path** (within noise) — the opposite of RTAB-Map.
🔴 **DISK IS THE BINDING CONSTRAINT: 29.3 MB/s growth vs a measured 27.4 MB/s SD sustained-write
ceiling — it writes AT the card's limit, so hiccups WILL drop messages. 27 GB free ≈ 15 MIN of
driving.** ⇒ **A USB SSD is effectively required for a real run** (none attached). Dropping colour to
640×360 shrinks the bag AND RTAB-Map's cost — one change, both problems.
⚠️ **Live-streaming RGB-D to the laptop instead is NOT viable:** `image_transport` here has **only
`raw_pub`** (the `compressedDepth` plugin fails to load — visible in every `rover-camera` start), so
depth would go uncompressed at ~12 MB/s ≈ 100 Mbit/s. WFB is 13 Mbit/s. Record locally, transfer after.

## ⏭ MAPPING IS NOT YAW-GATED — drive it in MANUAL
**Manual mode bypasses the yaw rate controller (firmware-verified → [[project-rover-autonav]]).**
⇒ **A mapping run can happen BEFORE #20 is fixed.** ⚠️ **but the collision reflex does NOT apply in
Manual — the operator is the only safety layer.** Drive slowly (motion blur kills feature matching)
and **make deliberate LOOPS** — returning to known places is exactly what loop closure needs.
**Revised order: USB SSD → 640×360 colour + `depth_registration` (one camera restart, then the
half-dead check) → manual mapping run → offline RTAB-Map on the laptop → AMCL/Nav2 on the Pi.**
⚠️ **SSD-first is superseded by `docs/indoor_mapping_plan.md` §5**, which re-measures the bag at
640×360 FIRST — the shrink may remove the SSD requirement entirely. Measure before buying.

## ✅ STEP 1 APPLIED 2026-08-02 10:51 — and SW depth registration is NOT free
Drop-in `10-point-cloud-decimation.conf` now adds `depth_registration:=true color_width:=640
color_height:=360` (backup: `/etc/systemd/system/10-point-cloud-decimation.conf.bak-20260802`).
Half-dead check **PASSED** first try. Safety path improved: `/scan` 27.1 → **28.0 Hz**,
`/scan_3d` 27.1 → **29.7 Hz**, load1 2.12.
🔑 **`depth_registration:=true` FORCES DEPTH TO THE COLOUR RESOLUTION — depth is now 640×360, no
longer its native 848×480.** Both camera_infos confirm 640×360. Consequence: fewer cloud columns
(~213 not 283 after decimation 3, ~0.42°/col) and depth now carries the COLOUR intrinsics/FOV.
🔴 **ANSWERS THE OPEN QUESTION "how much does SW registration cost?": camera container CPU went
34.2% → 48.9% of a core (stable, 5 samples) EVEN THOUGH colour dropped 1280×720 → 640×360.**
⇒ **SW alignment costs MORE than the resolution drop saved, ~+15 pp net.** ⚠️ the 34.2% baseline
was a single `ps` snapshot at boot+5 min, so treat the delta as directional, not precise.
**The camera budget and the RTAB-Map budget are SEPARATE** — RTAB-Map's 79.6% was feature
extraction at 1280×720 and should still fall at 640×360. Whether it now fits = **Step 2, untested.**

## 🔴 STEP 2 MEASURED 2026-08-02 11:18 — **640×360 DID NOT MAKE RTAB-MAP FIT. HYPOTHESIS FALSIFIED.**
`rgbd_odometry` re-measured at 640×360 **with `depth_registration:=true`** (the correct RGB-D config):
| | 1280×720, reg **OFF** (08-02 00:00) | 640×360, reg **ON** (now) |
|---|---|---|
| `rgbd_odometry` CPU | 79.6% | 🔴 **94.6%** — WENT UP |
| `/scan` | 13.4 → 7.0 Hz | 28.0 → **19.1 Hz** |
| `/scan_3d` | 23.2 → 17.3 Hz | 29.7 → **20.0 Hz** |
| update time | 0.29-0.43 s | **0.25-0.39 s** (~3 Hz, barely moved) |
| delay | 0.83-1.04 s | **0.78-1.02 s** (~1 s, UNCHANGED) |
| load1 | 9.44 | **10.44** |
⇒ **`indoor_mapping_plan.md` §5 Step 2's hope ("if it drops to ~20%, realtime is back on") is DEAD.
The OFFLINE architecture stands — map on a laptop, localize on the Pi.**
⚠️ **CONFOUNDED, state it honestly:** resolution dropped AND registration turned on in the same
change, so the 79.6→94.6 rise cannot be attributed to one alone. The 79.6% was a *cheaper but
incorrect* config (RGB-D needs registration). **What is solid: in the CORRECT config at 640×360 it
still does not fit.** Isolating the two would need a 640×360 + reg-OFF run.
🔑 **The ~1 s delay is looking INTRINSIC, not starvation** — a **4× cut in pixel count moved it
essentially not at all**. Answers open question 2 in `indoor_mapping_plan.md` §6, provisionally.
✅ **Silver lining: the safety path degrades far less than before** — `/scan` loses 32% (28.0→19.1)
where it used to lose 48% (13.4→7.0), because the baseline pipeline itself is faster now.
✅ Odometry quality was healthy throughout (150-271 inliers, std dev ~0.002 m) — it WORKS, it is
just too slow. Recovery after kill: `/scan` 30.1, `/scan_3d` 27.0, all 5 services active.
⚠️ Hygiene: a stray `npm` at 63.4% appeared at launch and had exited before the measurement window
— exactly the contamination trap from the last run. **Always re-check mid-measurement, not just at
the start.** → [[feedback-check-docs-before-measuring]]

## ✅ STEP 3 MEASURED 2026-08-02 11:25 — **THE USB SSD IS NO LONGER REQUIRED (for throughput)**
Same topic set, colour AND depth now both 640×360 (registration forced depth down too):
| | 1280×720 + 848×480 | both 640×360 |
|---|---|---|
| bag growth | 🔴 **29.3 MB/s** (over the 27.4 ceiling) | ✅ **16 MB/s** — ~40% under it |
| minutes on 27 GB | ~15 min | ✅ **~28 min** |
| `/scan` | 13.4 → 14.2 Hz ("no cost") | 🔴 **30.5 → 23.1 Hz (−23%)** |
| load1 | 5.64 | 🔴 **15.18** |
🔑 **THE SSD QUESTION IS ANSWERED: throughput no longer breaches the card** (16 vs 27.4 MB/s), so an
SSD is **optional**, not required. Capacity now gives ~28 min per run — enough for a first house
circuit. **Do not buy hardware for this yet.**
🔴 **BUT THE OLD "RECORDING IS FREE" CLAIM IS WITHDRAWN.** It was measured against a **degraded
13.4 Hz baseline** where a 14.2 Hz reading looked like an improvement — that was noise, not headroom.
Against a clean **30.5 Hz** baseline, recording costs a real **23% of `/scan`**, and load1 hits
**15.18** (largely I/O wait: SD writes park processes in D-state, which Linux counts as load).
⇒ **Recording is CHEAPER ON DISK but NOT free on the safety path. Drive slowly on a mapping run.**
⚠️ **METHOD LESSON: never conclude "no cost" from a comparison taken against an already-degraded
baseline.** Fix the baseline first, then measure the delta. → [[feedback-check-docs-before-measuring]]
⚠️ `du` growth is bursty at start (72 MB/s for the first ~10 s, then settles) — **sample a steady
window ≥30 s in, not from t=0.** Bag deleted after the run; disk back to 27 GB / 53%.

## 🔴🔴 STEP 3'S CONCLUSION WAS WRONG — CORRECTED BY THE 11:34 RUN. **THE BAG WAS SILENTLY DROPPING.**
First real mapping run (253 s, one room + hall). `ros2 bag info` vs live rates:
| topic | live | recorded | captured |
|---|---|---|---|
| `/camera/color/image_raw` | **67.2 Hz** | 24.4 Hz | 🔴 **36%** |
| `/camera/depth/image_raw` | 30.0 Hz | 7.7 Hz | 🔴 **26%** |
| `/odom` | 100.5 Hz | 26.0 Hz | 🔴 **26%** |
**`rosbag2` logged `Cache buffers lost messages ... Total lost: 73547`** against 29 440 recorded —
**only ~29% of the data survived.**
🔴 **THE 16 MB/s IN STEP 3 WAS NOT "IT FITS" — IT WAS THE RATE THE CARD COULD ABSORB WHILE
DISCARDING 71% OF THE MESSAGES.** I measured write throughput and never checked for message loss.
**Real demand: colour 46.5 + depth 13.8 = 60.3 MB/s vs the 27.4 MB/s ceiling.**
🔑 **ROOT CAUSE — colour is running at 67 Hz.** At 640×360 the Orbbec picked a **90 fps** mode
(`color Frame - ... fps: 90` in the start log). **Nothing needs 67 Hz colour for mapping.**
✅ **FIX: `color_fps:=15 depth_fps:=15`** (both exist as launch args; `color_fps` L97, `depth_fps`
L133, default `0` = auto/max) ⇒ 10.4 + 6.9 = **17.3 MB/s, comfortably under the ceiling.**
⚠️ **METHOD — this is the same error twice in one session: a rate that looked fine hid the real
state.** **`ros2 bag record` fails SILENTLY-ish** — the loss line appears only at shutdown.
**ALWAYS diff `ros2 bag info` counts against live `topic hz`, and grep the recorder log for
`lost`, BEFORE trusting a bag.** → [[feedback-check-docs-before-measuring]]

## 🔴 RTAB-MAP RUN 2026-08-02 12:30 — **MAP BUILT, BUT ZERO LOOP CLOSURES. THE ROUTE WAS WRONG.**
Ran offline on the Pi over `~/mapping_run2_20260802`, **VISUAL odometry only** (`/odom` and `/tf`
excluded from playback so wheel odom could not contaminate it; `/tf_static` kept for
`base_link->camera_link`). Bag replayed at **0.3×** with `--clock` + `use_sim_time`.
✅ **Visual odometry WORKS WELL:** **93% tracking**, 370-400 inliers, **0.07-0.14 s per update**
offline vs 0.25-0.39 s realtime. **⇒ the OFFLINE ARCHITECTURE IS SOUND.**
🔴 **BUT: 0 loop closures.** Grid: **15 853 occupied vs only 1 253 free** cells — inverted; a good
map is mostly free inside a thin wall shell. Cloud spans **3.64 m vertically** (−0.66..2.98) for a
single storey ⇒ pitch/height drift down an unclosed pose chain. **Map is NOT usable.**
🔑 **ROOT CAUSE IS THE DRIVE SHAPE, NOT A SETTING: an OUT-AND-BACK cannot close loops on a
forward-facing camera.** Coming back, the camera sees the *opposite* view of the same corridor, and
RTAB-Map closes loops by **recognising places from appearance** — the far end of a hall does not look
like its near end. **This is the direct, predicted cost of the 92° forward-only sensor.**
✅ **FIX FOR THE NEXT RUN: drive a CIRCUIT, not an out-and-back** — return to the start still moving
FORWARD, so each place is re-seen from the direction it was first seen.
⚙️ **Working recipe (reusable):** `rtabmap_odom rgbd_odometry` + `rtabmap_slam rtabmap`, both with
`--params-file` (**RTAB-Map core params are STRINGS — `-p Mem/IncrementalMemory:=true` throws
`InvalidParameterTypeException`; a YAML file with quoted values works**). Key params:
`Odom/ResetCountdown: "1"` (**essential** — without it VO lost tracking permanently and
`publish_null_when_lost=true` made rtabmap log *"no odometry is provided. Image N is ignored"* for
the whole rest of the run, mapping NOTHING) and `publish_null_when_lost: false`.
⚠️ Freed CPU first by stopping `rover-camera`/`rover-scan`/`rover-scan-3d`; restored after and the
**half-dead check PASSED** first try. ⚠️ `pkill -f rgbd_odometry` **kills the calling shell too** —
kill by PID.

## ✅✅ 2026-08-02 SOLVED — **32 LOOP CLOSURES. THE BLOCKER WAS THE ROVER'S OWN TOP PLATE IN COLOUR.**
🔑 **OPERATOR'S HYPOTHESIS WAS RIGHT** ("its own top plate disrupts the mapping") → [[feedback-check-docs-before-measuring]] "the operator's ID of their own hardware beats my inference".
**GEOMETRY (computed + confirmed against a real frame):** camera is **70 mm above the plate**,
pitched 2.33°. Bottom ray = 30.35°(½ vFOV) + 2.33° = **32.68° below horizontal**, reaching plate
height at **109 mm** forward; plate runs to the bumper at **345 mm** (11.5° below horizontal)
⇒ plate fills **21.2° = 35% of frame HEIGHT**.
🔴 **DEPTH vs COLOUR DIVERGE COMPLETELY — this is the whole point:**
| | depth | colour |
|---|---|---|
| geometric band | 35% | 35% |
| min range | **0.308 m — clips it** | **NONE** |
| actually recorded | 45 mm strip, **0.74% of pixels** | 🔴 **the full 35% band** |
⇒ **Depth barely saw it; colour is one-third rover.** Plate features never move w.r.t. the camera and
look identical from every pose ⇒ they match between ANY two frames, padding `matches=` while
contributing zero consistent geometry. **That is exactly the observed signature: matches 75-102,
inliers only 14-19/20.** RANSAC was discarding the self-view.
✅ **FIXES THAT WORKED (all software, NO hardware change):**
1. `point_cloud_xyz` **`min_depth: 0.45`** ⇒ ICP correspondence ratio **0.612 → 0.770**.
2. **`Kp/RoiRatios` + `Vis/RoiRatios` = `"0.0 0.0 0.0 0.35"`** (mask bottom 35% of colour)
   ⇒ loop-closure detections **26 → 47**. **THE key fix.**
3. **`RGBD/OptimizeMaxError: "0"`** — detections were all still being REJECTED with
   *"maximum graph error ratio"* because odometry had drifted **33-44° in heading**; the gate is a
   guard against FALSE loops, but these were genuine. ⇒ **32 accepted (Loop=20, Prox=12).**
📊 **RESULT, like-for-like:** bulk vertical span **p1-p99 3.09 → 2.31 m**, p5-p95 2.65 → 1.68 m
(a storey is ~2.3-2.5 m ✅). Floor scatter 143 → 134 mm. ⚠️ **raw span WORSENED 3.57 → 4.91 m** —
optimisation flung a few outliers out. Map: `~/rtabmap_final.db`, `~/map_opt_cloud.ply` (1.25 M pts).
🔴🔴 **METHOD — REALTIME BAG REPLAY IS NOT REPRODUCIBLE. Two runs differing ONLY in a gate param gave
47 vs 0 detections**, because `--rate 0.3` drops different frames under different CPU load, building a
different pose graph each time. **⛔ NEVER compare RTAB-Map parameters via `ros2 bag play`.**
✅ **USE `rtabmap-reprocess --uwarn --Param val in.db out.db`** — deterministic, reprocesses a saved
DB, no replay, far faster. All parameter comparisons must go through it.
## 🔴 RUN 3 (CIRCUIT) 2026-08-02 — **THE CIRCUIT DID NOT HELP. ODOMETRY IS NOW THE BOTTLENECK.**
Re-drove as a closed circuit on my advice. Capture perfect (264 s, 67 037 msgs, **0 loss**,
depth 99.5% / colour 99.3%). `~/mapping_run3_20260802`, db `~/rtabmap_run3_raw.db`.
| | loops | p1-p99 | p5-p95 | floor std |
|---|---|---|---|---|
| run2 out-and-back | 32 | **2.31 m** | **1.68 m** | **134 mm** |
| run3 CIRCUIT | **39** | 3.71 m | 2.24 m | 🔴 **425 mm** |
🔴 **MORE loop closures but a WORSE map.** Route shape was not the limiter. ⚠️ **I advised the
circuit and it did not pay off — record that so it is not re-tried as the fix.**
✅ **`OptimizeMaxError` SWEEP (deterministic, `rtabmap-reprocess`) — MY GATE HYPOTHESIS WAS WRONG:**
| gate | 1 | 3 | 10 | 20 | 0=off |
|---|---|---|---|---|---|
| loops | 0 | 0 | 6 | 36 | 39 |
| floor std | 600 mm | 600 mm | 496 mm | 428 mm | **425 mm** |
**Monotonic — more closures ALWAYS gave a better map.** The gate never protected against bad
closures, it only blocked good ones. ⇒ **keep `RGBD/OptimizeMaxError` at 0 (or ≥20). Do not
re-propose a "moderate gate" as a fix.**
🔑 **CONCLUSION: with the plate masked and loops closing, the limiter is ICP ODOMETRY QUALITY, not
loop closure and not the route.** run3 turned more (2731° vs 2554°) in a tighter space and its
odometry degraded accordingly. **425-600 mm of floor scatter is the symptom to chase next.**
## ✅ VISUAL ODOMETRY + MASK BEATS ICP (2026-08-02, same run3 data)
| run | odom | loops | p1-p99 | floor std |
|---|---|---|---|---|
| run2 out-and-back | ICP | 32 | 2.31 m | 134 mm |
| run3 circuit | ICP | 39 | 3.71 m | 🔴 425 mm |
| run3 circuit | **VISUAL+mask** | 36 | 2.97 m | ✅ **161 mm** |
⇒ **run3's bad map was ICP ODOMETRY, not the route or the driving.** Visual+mask also ran at
**0.13 s delay** offline vs ~1 s under realtime load. **STANDING RECIPE: visual odometry + colour
mask + plate crop + `OptimizeMaxError 0` + ray tracing, via `rtabmap-reprocess`.**
🔑 **`rtabmap-export --cloud` does NOT apply `Grid/NoiseFiltering*`** — that only cleans the GRID.
The exported cloud stays raw, which is why it still looked full of floating points while the grid was
already clean. **Use `--noise_radius 0.06 --noise_k 12`: removed 517 793 pts (38.8%) of FLYING PIXELS
(depth-edge interpolation artifacts, a sensor property, NOT a capture fault — capture was 99.5%),
floor std 161 → 125 mm.** Two products, same DB: judge navigation on the GRID, not the cloud.

# 🏁 2026-08-02 — **Q1 "WHERE AM I?" IS ANSWERED. RTAB-MAP LOCALIZATION WORKS; AMCL DOES NOT.**
Map: `~/rtabmap_run3_vis_nav.db` + `~/house_map.pgm/.yaml` (11.8×11.7 m, 5 cm, **free 48.1 m²,
free:occupied 8.9** — was 0.08 before ray tracing).
| localizer | driving | σx | σy | σyaw | verdict |
|---|---|---|---|---|---|
| **AMCL** | 46.9 m | 1.10 m | 0.78 m | **28.9°** | 🔴 **plateaued at 25-30° then DRIFTED BACK UP** |
| **RTAB-Map** | 19.6 m | **0.06 m** | **0.06 m** | ✅ **4.3°** | ✅ **CONVERGED, best 0.01/0.01/1.7°** |
🔑 **~18× better in position, ~7× in heading, on LESS THAN HALF the driving.**
🔴 **WHY AMCL FAILS — SAME CLASS OF MISTAKE AS `slam_toolbox` FOR MAPPING.** AMCL matches a **360°
lidar ring** against an occupancy grid; we have a **92° forward wedge, ~4 m range**. From many spots
along a wall that wedge is identical ⇒ irreducible ambiguity. **⛔ Do not re-try AMCL on this
vehicle, and do not "tune" it — swap the ALGORITHM, not the parameters.**
✅ **RTAB-Map relocalizes with the SAME visual place recognition that built the map**, publishes
`map->odom` identically, so **Nav2 sits on top unchanged** and `map_server` still serves the grid.
⚠️ **BEHAVIOUR IS BINARY, NOT GRADUAL: lost (σ=100 m / 5729°) or locked (σ 0.056 m / 4.3°), nothing
between.** First lock took **150 s of driving**; **after first lock it stayed localized 100% of the
time** with zero variation. ⇒ **The hard part is INITIAL ACQUISITION (kidnapped-robot), not
tracking.** Seed an initial pose to skip it. **L2/L3 must treat "not yet localized" as a real state
and refuse to drive autonomously in it.**
⚙️ Config: `ros2_ws/src/rover_nav2/config/rtabmap_localization.yaml` (+ `localization.yaml` = the
superseded AMCL attempt, kept as the negative result).
🔴 **TRAP: `rover_odometry` publishes a CONSTANT pose covariance** (x/y 0.01, yaw 0.002). RTAB-Map
derives link information from the CHANGE in covariance between poses ⇒ constant gives zero ⇒
**FATAL in `Link.cpp:137::setInfMatrix`, node aborts.** ✅ **FIX: set `odom_frame_id: odom` +
`odom_tf_linear_variance`/`odom_tf_angular_variance` so RTAB-Map reads odom from TF instead.**
⚠️ Ran at ~1.2 s delay under live CPU contention — fine for localization, **NOT for closed-loop
control**. Needs measuring before autonomous driving.
⏭ Also unchecked: whether the 2.33° camera pitch calibration contributes to the floor tilt.
