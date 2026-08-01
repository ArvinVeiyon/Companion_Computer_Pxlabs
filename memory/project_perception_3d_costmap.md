---
name: project-perception-3d-costmap
description: "3D height-aware perception from the Gemini depth cloud, replacing the 2D depthimage_to_laserscan band. Holds the MEASURED floor height, the rover-sees-its-own-bumper finding, and the Nav2 forward-only costmap config. Built 2026-08-01, NOT yet deployed or validated."
metadata: 
  node_type: memory
  type: project
  originSessionId: b207e8d3-f638-4331-a8d8-7c4c291479c2
  modified: 2026-08-01T14:04:44.666Z
---

# Perception: 3D height-aware obstacle layer + Nav2 forward costmap

**Built 2026-08-01 (late session, ~13:00-16:12). Status: code committed, config UNCOMMITTED,
NOTHING DEPLOYED, NOTHING VALIDATED ON THE FLOOR.** See [[project-rover-autonav]] for the vehicle
state and [[project-l4-gemini-nav2-prereqs]] for the Nav2/slam_toolbox install.
**WHY this layer exists at all → [[project-autonomy-plan-reframe]]:** it is the Q2 (perception) half
of L1, and the depth cam is what sees the table tops and drop-offs a 2D lidar passes under or over.
⚠️ This file was written from a crash recovery, not from the session that did the work —
see [[feedback-crash-recovery-checkpoint]].

## ⏭ RESUME HERE (re-verified live 2026-08-01 19:31, after a 19:19 reboot)
- `rover-scan.service` **still runs the OLD 2D pipeline** — `depth_to_scan.launch.py` →
  `/opt/ros/jazzy/lib/depthimage_to_laserscan/depthimage_to_laserscan_node`. Confirmed live. **Switching
  it over is a ONE-LINE `ExecStart` change — but read the rate blocker below first.**
- ✅ The config is no longer uncommitted: **`e0535f9` is pushed, tree clean, 0 ahead of origin/main.**
- ✅ Prereqs confirmed present: `pointcloud_to_laserscan_node` installed under `/opt/ros/jazzy`,
  and `/camera/depth/points` **is** being published by the Orbbec wrapper (2.9.3, Gemini 336L, USB3.2).
- Nothing has been driven with any of this. The numbers below are static measurements, not a test.

## 🔴 BLOCKER FOUND 2026-08-01 19:31 — THE CLOUD IS HALF THE RATE OF THE SCAN IT REPLACES
Measured over 15 s, services running, video OFF, load ~2.5/4:
| topic | rate | worst gap | mean gap |
|---|---|---|---|
| `/scan` (current 2D `depthimage_to_laserscan`) | **22.7 Hz** | **200 ms** | 44 ms |
| `/camera/depth/points` (input to the NEW pipeline) | **11.1 Hz** | **465 ms** | 91 ms |

⇒ **Deploying `cloud_to_scan` as-is roughly HALVES the obstacle update rate and MORE THAN DOUBLES the
worst-case blind interval.** At 0.6 m/s a 465 ms gap is **28 cm of travel** against a 0.35 m bumper
margin — it eats ~80% of the reflex distance on its own. **⛔ Do not flip `rover-scan.service` over
until this is closed.**
**It is NOT the sensor:** the depth stream is configured **848×480 @ 30 fps Y16** and the camera reports
healthy. The cloud is **CPU-bound in the wrapper's own point-cloud assembly** on 4 oversubscribed cores.
**Options, in order of cheapness:** (a) drop depth resolution — the scan collapses to one row band
anyway, so full 848×480 is wasted work; (b) subscribe `depth/image_raw`+`camera_info` and project only
the needed height band ourselves instead of taking a full organised cloud; (c) accept a lower speed cap
and re-derive the collision margin from the MEASURED worst gap. **Do not just lower the speed silently.**
⚠️ Note this also revises the earlier "`/scan` 16-19 Hz" figure — post-reboot it measures 22.7 Hz.

## 🔴 THE TWO MEASUREMENTS THAT MAKE OR BREAK IT (2026-08-01, from the live cloud)

### 1. The floor is NOT at z = 0 in `base_link`
**Measured: floor sits at z = 0.043 - 0.093 m** inside the driving corridor. `base_link` is therefore
**~5 cm ABOVE the floor**, not on it.
⇒ An "obvious" `min_height` / `min_obstacle_height` of 0.05 (or the old 0.06) **marks the FLOOR ITSELF
as a lethal obstacle in every visible cell, and the rover refuses to move anywhere.**
**Set to 0.12** — clears the measured floor by ~3 cm.
**COST: obstacles shorter than ~12 cm are invisible.** Still far better than the 2D band it replaces,
which at 1 m only covered z = 0.22 - 0.31 m.

### 2. The camera sees the ROVER'S OWN FRONT PLATE
**Measured: 1982 points at x = 0.305 - 0.331 m, z = 0.12 - 0.24 m** — a dense flat surface sitting
exactly at the **0.337 m bumper plane**, with 1.26 m of genuinely clear floor beyond it.
⇒ Left unfiltered it reports a **permanent obstacle 3 cm inside the bumper and the rover never moves**.
**Set `range_min` / `obstacle_min_range` / `raytrace_min_range` = 0.40 m.**
**Nothing is lost:** the reflex stops at 0.35 m of BUMPER clearance = 0.687 m from the camera, well
beyond this.
⚠️ **The old 2D `/scan` never noticed this** because at 0.3 m the plate falls below its narrow row
band. The height-aware scan is the first thing that ever looked there — expect more findings like it.

### 3. `sensor_frame` was wrong
`nav2_forward.yaml` had `sensor_frame: camera_link`. **The cloud is published in
`camera_depth_optical_frame`.** Now left `""` so Nav2 uses the message's own frame and raytracing
originates where the sensor actually is.

## ⚠️ THE CAVEAT THE CODE ITSELF FLAGS — RE-VALIDATE IN AN OPEN CORRIDOR
The height band was measured **with something blocking at 1.26 m**, so the floor was only sampled over
**1.0 - 1.4 m**. If camera pitch calibration is slightly off, the floor **TILTS in `base_link`** and can
cross the 0.12 threshold further out, producing **phantom obstacles at range**. Re-measure with a clear
run ahead before trusting it.

## Config values as they now stand (uncommitted)
`launch/cloud_to_scan.launch.py`: `min_height` 0.06→**0.12** · `max_height` 0.45 (drive-under limit) ·
`angle_min/max` ∓0.80 rad (~∓46°) · `range_min` 0.20→**0.40** · `range_max` 5.0 ·
`cloud_topic` `/camera/depth/points`
`src/rover_nav2/config/nav2_forward.yaml`, BOTH local and global costmaps:
`sensor_frame` ""· `min_obstacle_height` **0.12** · `max_obstacle_height` 0.45 ·
`obstacle_max_range` 3.0 (depth quality falls off well before 5 m) · `obstacle_min_range` **0.40** ·
`raytrace_max_range` 3.5 · `raytrace_min_range` 0.0→**0.40** · `inf_is_valid` False

## Commits (ros2_ws, all UNPUSHED as of 08-01 close)
- `6a7b42f` 13:14 — rover_nav2: forward-only Nav2 config for the depth camera alone
- `caa8691` 16:05 — collision-stop tests **the corridor the body sweeps, not an angular cone**
- `4ba83db` 16:12 — perception: 3D obstacle layer + height-aware scan from the point cloud
- working tree — the two files above, holding all the measured values

## ⚠️ CPU — measure before trusting collision-stop margins
`/scan` measured **16-19 Hz on 2026-08-01 with video OFF**. Prior recorded figures: 28.4 Hz idle,
22.3 Hz *while streaming FPV*. **So the new perception path may cost more than the video ever did.**
Load was 3.77 on 4 cores with `vision_streaming` stopped. Worst-gap latency feeds directly into the
collision margin — re-measure `/scan` worst gap before any armed test. See [[project-rover-autonav]]
for the 0.6 m/s margin arithmetic.
