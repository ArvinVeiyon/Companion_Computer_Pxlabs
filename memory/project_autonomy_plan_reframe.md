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
**Do NOT silently starve the control loop for it.** (Same 4-core contention as [[project-ffmpeg-hung-alive-gap]].)
