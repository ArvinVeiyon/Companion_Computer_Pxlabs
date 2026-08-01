---
name: project-autonomy-plan-reframe
description: "2026-08-01 rewrite of the autonomy ladder in ros2_ws/docs/autonomy_plan.md. Redefines L0-L5 by USER OUTCOME, contradicts the old 'L0-L4 DONE' status, and names localization (Q1) as the real wall. L3 is the step-change."
metadata: 
  node_type: memory
  type: project
  originSessionId: b207e8d3-f638-4331-a8d8-7c4c291479c2
  modified: 2026-08-01T11:34:09.503Z
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
