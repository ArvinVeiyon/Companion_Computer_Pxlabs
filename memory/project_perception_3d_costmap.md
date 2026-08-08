---
name: project-perception-3d-costmap
description: "3D height-aware perception from the Gemini depth cloud, replacing the 2D depthimage_to_laserscan band. Holds the MEASURED floor height, the rover-sees-its-own-bumper finding, and the Nav2 forward-only costmap config. Built 2026-08-01, NOT yet deployed or validated."
metadata: 
  node_type: memory
  type: project
  originSessionId: b207e8d3-f638-4331-a8d8-7c4c291479c2
  modified: 2026-08-08T05:32:19.931Z
---

# Perception: 3D height-aware obstacle layer + Nav2 forward costmap

**Built 2026-08-01 (late session, ~13:00-16:12). Status: code committed, config UNCOMMITTED,
NOTHING DEPLOYED, NOTHING VALIDATED ON THE FLOOR.** See [[project-rover-autonav]] for the vehicle
state and [[project-l4-gemini-nav2-prereqs]] for the Nav2/slam_toolbox install.
**WHY this layer exists at all → [[project-autonomy-plan-reframe]]:** it is the Q2 (perception) half
of L1, and the depth cam is what sees the table tops and drop-offs a 2D lidar passes under or over.
⚠️ This file was written from a crash recovery, not from the session that did the work —
see [[feedback-crash-recovery-checkpoint]].

## 📗 GEOMETRY NOW HAS ONE HOME — `~/ros2_ws/docs/rover_geometry.md` (NEW 2026-08-01, `0759161`)
**Read it before deriving any vehicle dimension.** Body + `base_link` footprint, camera mount and why
`cam_x=0` / why the bracket is 70 mm, live-verified optics, the plate-sliver derivation, the
don't-move-the-camera-forward table, `front_overhang`, the floor plane, **§6 a CONSUMER LIST of the
six files to revisit when a number changes**, and **§7 sensors NOT on the vehicle**.
Created because a superseded plate width (0.405 vs the real 0.450) sat in shipped code for a week.

## ✅ FAIL-OPEN CLOSED 2026-08-01 22:10 — `3f74af4`. Footprint rejected PER-RAY, not radially
`cloud_to_scan` **`range_min` 0.40 → 0.31** (just above the 0.308 m sensor floor) + `autonav_mode`
`onScan()` now rejects **`x < 0.345 && |y| < 0.225`** (the top plate about `base_link`) **+ 20 mm margin**.
**Why radial cuts are wrong:** they cannot express a rectangular body. 0.40 also erased real obstacles
between the 0.337 m bumper and 0.40 m, and **a dropped ray is indistinguishable from empty space, so
the reflex read that strip as INFINITE clearance — a ~6 cm fail-open band at the bumper.** Even 0.35
misses an obstacle at bearing 45° / range 0.34 (x=0.24, y=0.24): beside the body, inside the corridor,
entirely real. **The footprint test belongs in the CONSUMER, where x and y both exist.**
⚠️ **The 20 mm margin is NOT cosmetic** — the plate's own edges lie EXACTLY on the boundary and a
strict `<` let the side edge through as a phantom obstacle at bearing 35° / 0.392 m.
⚠️ **`/scan_3d` NOW CONTAINS THE ROVER'S OWN TOP PLATE, by design.** Every consumer must reject its own
footprint. `autonav_mode` does; Nav2 does via `footprint_clearing_enabled` on both costmaps.
✅ Also fixed (`ca81d2a`): corridor half-width **0.25 → 0.275** and the Nav2 **`robot_radius` 0.30 → an
explicit rectangle on BOTH costmaps** — 0.30 was the wheelbase half-diagonal and left most of the rover
outside its own footprint. Both were sized off the superseded 0.405 m plate.

## ✅ CLOSED 2026-08-08 — THE "UNEXPLAINED CLUSTER" WAS A RACK, NOT THE ROVER
The cluster (**x 0.353-0.400, y +0.085..+0.161, z 0.100-0.218** — below the plate at 0.235, ~5 cm past
its front edge) was treated for a week as possible rover hardware, which would have left `/scan_3d`
**permanently self-blocked**. It is not. **The operator stated the rover had been parked facing a
rack.** Then tested, over the 480 nodes of `rtabmap_replay_wheel.db` (per-node obstacle cells are in
`base_link`, so a body-fixed return must recur in every node):

| box tested | nodes containing it |
|---|---|
| near-field sanity — ANY point x 0.31-0.45 | 103/480 = 21.5% |
| **top plate**, z 0.22-0.25 — known body-fixed | 87/480 = **18.1%** |
| **the cluster**, z 0.100-0.218 | 3/480 = **0.6%** |

**The plate appears in 84% of every node that has any near-field return at all — that is what a
self-return looks like. The cluster appears in 3.** Near-field z is p10 0.221 / p50 0.325: returns sit
at and above plate height, almost nothing below. ⇒ **not body-fixed.**

🔑 **The 3.8 cm bumper-clearance reading was CORRECT, not a fault** — the rover really was ~4 cm off a
rack, and the reflex was doing its job. ⇒ **`/scan_3d` is not self-blocked; the reflex switch is
UNGATED.**
⚠️ **METHOD, reusable:** to decide whether a return is the vehicle or the world, count what fraction of
*many poses* contain it, and **always run a positive control** — my first control box (x 0.10-0.20) sat
inside the camera's 0.308 m blind zone and returned 0%, which would have made the whole test vacuous.
⚠️ `front_overhang = 0.337` could not have caught it — calibrated on the 2D `/scan`, whose band sits
above z 0.10-0.22. That remains true and is now moot.
→ [[feedback-check-docs-before-measuring]] (the operator's ID of their own hardware beats my inference)
· [[feedback-test-before-concluding]]

## ✅ DEPLOYED 2026-08-01 20:08 — `rover-scan-3d.service`, PARALLEL, publishing `/scan_3d`
**`cloud_to_scan.launch.py` publishes `/scan_3d`, NOT `/scan`, and publishes NO TF.**
`base_link->camera_link` comes ONLY from `rover-scan`'s `depth_to_scan.launch.py`.
⇒ **NEVER repoint `rover-scan.service` at `cloud_to_scan.launch.py`** — it would kill the TF, kill the
`/scan` the live reflex consumes, and leave a topic nothing subscribes to. New unit
`/etc/systemd/system/rover-scan-3d.service` runs it alongside, with `Requires=rover-scan.service`.
**Measured head-to-head, same 30 s window:** `/scan_3d` **29.2 Hz / worst gap 99 ms** vs
`/scan` **23.5 Hz / worst gap 233 ms**. `/scan_3d` is in `base_link`, 184 beams over 92°, 96% finite.

## 🔴 BLOCKER FOR SWITCHING THE REFLEX — `/scan_3d` REPORTS THE NEAR-FIELD STRUCTURE AS OBSTACLES
**`range_min = 0.40` DOES NOT remove the self-view, because a LaserScan range is √(x²+y²), not x.**
The structure reaches y = −0.395 at x ≈ 0.34 ⇒ range ≈ **0.52 m**, sailing past a 0.40 m filter.
**Measured: 34 of 184 beams (18%) have a median range < 0.60 m** — a solid arc from **−45.8° to −33.9°
at 0.40-0.46 m**, plus isolated bearings at **−9.9° (0.414 m), +10.0° (0.628 m), +31.9° (0.457 m)**.
**Several have std 0.0004-0.0010 m across 30 frames** — rigid to sub-millimetre, which no real scene
return looks like. Negative bearing = the vehicle's RIGHT (ROS REP-103 +y is left), matching the
y median −0.282 of the near-field cluster.
⇒ **These sit INSIDE the reflex threshold (0.687 m from camera). Switch the reflex to `/scan_3d` today
and the rover refuses to move.** ⛔ Do not switch until this is masked or explained.

## ⏭ RESUME HERE (re-verified live 2026-08-01 19:31, after a 19:19 reboot)
- `rover-scan.service` **still runs the OLD 2D pipeline** — `depth_to_scan.launch.py` →
  `/opt/ros/jazzy/lib/depthimage_to_laserscan/depthimage_to_laserscan_node`. Confirmed live. **Switching
  it over is a ONE-LINE `ExecStart` change — but read the rate blocker below first.**
- ✅ The config is no longer uncommitted: **`e0535f9` is pushed, tree clean, 0 ahead of origin/main.**
- ✅ Prereqs confirmed present: `pointcloud_to_laserscan_node` installed under `/opt/ros/jazzy`,
  and `/camera/depth/points` **is** being published by the Orbbec wrapper (2.9.3, Gemini 336L, USB3.2).
- Nothing has been driven with any of this. The numbers below are static measurements, not a test.

## ✅ RATE BLOCKER FIXED 2026-08-01 20:00 — `point_cloud_decimation_filter_factor:=3`
**The cloud is now FASTER than the 2D scan it replaces, on both rate and worst gap.** 60 s runs:
| decimation | cloud rate | worst gap | msg size | points |
|---|---|---|---|---|
| 1 (was) | 10.0 Hz | **1066 ms** | 3.37 MB | 210 339 |
| 2 | 17.8 Hz | 265 ms | 0.84 MB | 52 621 |
| **3 (deployed)** | **23.2 Hz** | **301 ms** | **0.37 MB** | 23 268 |
| 4 | 26.2 Hz | 409 ms | 0.21 MB | 13 152 |
For comparison the OLD 2D `/scan` measures **16.4 Hz, worst gap 390 ms** on the same run.
**Nothing that matters is lost at 3:** 283 columns across the ~90° depth FOV = **0.32°/column = 1.7 cm
at 3 m**, well inside a 5 cm costmap cell. 4 gives a higher mean rate but a WORSE worst gap — don't.
**Deployed as a systemd drop-in** `/etc/systemd/system/rover-camera.service.d/10-point-cloud-decimation.conf`
(original unit untouched; revert = delete the file + `systemctl daemon-reload`).
⚠️ **`ros2 param set … point_cloud_decimation_filter_factor` reports "successful" and DOES NOTHING.**
The working runtime lever is a **service**: `ros2 service call /camera/set_point_cloud_decimation
orbbec_camera_msgs/srv/SetInt32 "{data: 3}"` — takes effect immediately, no restart. Use it to A/B.
⚠️ **The DEPTH IMAGE is now the slow path, not the cloud** — 14.6 Hz worst 533 ms, despite being
configured 848×480 **@30 fps**. It publishes 814 KB/frame on `default` (RELIABLE) QoS. Once
`cloud_to_scan` is deployed nothing needs `/camera/depth/image_raw` at all — turning it off is the
next free win. Not yet investigated why 30 fps only delivers ~15.

## 🔴 HAZARD FOUND THE HARD WAY 2026-08-01 19:55 — A CAMERA RESTART CAN COME UP HALF-DEAD
`systemctl restart rover-camera` came back **"active", params answering, gyro+accel streaming, NO error
logged — but depth and color never started.** `/camera/depth/points`, `/camera/depth/image_raw` and
`/scan` were all silently dead. **A second `systemctl restart` fixed it.** Not caused by the decimation
arg — the identical command worked on the retry.
**DISCRIMINATOR: after any camera restart, grep the log for the stream-start lines**
`journalctl -u rover-camera --since -1min | grep "depth Frame - Width"` — **present = streams live;
absent = half-dead, restart again.** `systemctl is-active` does NOT catch this, and neither does a
param read. ⇒ **never trust a camera restart without checking a topic rate.**

## 🔴 SUPERSEDED — the original blocker, kept for the method
**The first 7.3-7.7 Hz reading was measured while a runaway `vision_config_manager` (pid 1340510) ate
72.7% of a core**; it died with the 19:19 reboot. Clean-system baseline was 10.0 Hz. **Always check
`ps -eo pid,pcpu --sort=-pcpu` before trusting a rate measurement on this 4-core box.**
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

## ✅ SETTLED 2026-08-01 21:20 — IT **IS** THE ROVER'S OWN **TOP PLATE**. Confirmed against the docs.
**The user identified it ("that is top plate edge"); the measurement and the existing docs agree.**
| source | value |
|---|---|
| `docs/rover_autonav_requirements.md:75` | **ground to top plate = 0.235 m** (plate 0.730 × 0.450 m) |
| `launch/depth_to_scan.launch.py:50` | `cam_z 0.305` = **0.235 plate + 0.070 bracket** |
| MEASURED near band (range 0.30-0.37 m) | **z mean 0.231 m, max 0.241** — matches the plate to **4 mm** |
| MEASURED | x **0.301-0.347 m, std 4.9 mm**; global min range **0.3079 m** |
**Why it looks like an ARC at constant range, not a flat deck:** the sensor's near limit is **0.308 m**,
so **only the outer ~4 cm sliver of the plate is visible** — the rest of the deck is inside the blind
zone. The inner boundary of the return IS the min-range circle, which is why range looks constant.
🔴 **THEREFORE `range_min = 0.40` IS CORRECT AND LOAD-BEARING. DO NOT LOWER IT** to the 0.308 m sensor
limit — that re-admits the rover's own top plate as a permanent obstacle 3 cm inside the bumper.
✅ Also confirms **leave the camera centred** — the self-view is inherent to looking down over your own
deck from a 7 cm bracket, and sliding the camera forward would not remove it.

### ⚠️ MY 20:36 "OVERTURNED" CLAIM WAS WRONG — the error is worth keeping
I ran a two-pose test and concluded the near returns were room objects, not the rover. **The test was
sound; the population was wrong.** I compared **`/scan_3d` beams < 0.60 m — but `range_min = 0.40`
CLIPS the plate (0.31-0.35 m), so those beams never contained the plate.** They were room objects,
which correctly moved with the room. I then generalised that to "the self-view finding is overturned".
**LESSON: before concluding a filtered signal disproves something, check the filter does not already
remove the thing you are testing for.** Verify at the CLOUD level, where `range_min` has not applied.

**🔶 SUPERSEDED (kept for the method) — RE-MEASURED 2026-08-01 19:45:**
Live cloud, 4 consecutive frames: **18 472 points with x < 0.40 m — 8.9% of the whole cloud**, not 1982.
Extent in `base_link`: **x 0.305-0.398 (med 0.342) · z 0.089-0.498 (med 0.323) · y -0.395..0.250
(med -0.282)**. So it reaches from **9 cm off the floor to 50 cm — i.e. ~20 cm ABOVE the camera**
(camera sits at z = 0.305), and is offset to the RIGHT.
**Shape: x std 0.021 vs z std 0.095 and y std 0.094 ⇒ a roughly VERTICAL, forward-facing surface at
constant x ≈ 0.34 m**, NOT a horizontal top deck (a top plate would show constant *z*).
**Rigidity: the y median is −0.2817 in all four frames, to four decimals.**
⚠️ **HONEST LIMIT: that only proves the scene is STATIC, not that the surface is the ROVER.** The
decisive test is to rotate the vehicle and see whether the surface follows — **not possible yet**
(indoor, and the yaw-rate runaway is unresolved → [[project-rover-autonav]]). **Until then do not
record "it is the rover's own bodywork" as fact.** Either way `range_min = 0.40` removes it.

### 3. `sensor_frame` was wrong
`nav2_forward.yaml` had `sensor_frame: camera_link`. **The cloud is published in
`camera_depth_optical_frame`.** Now left `""` so Nav2 uses the message's own frame and raytracing
originates where the sensor actually is.

## 📐 CAMERA MOUNTING — CENTRE vs FORWARD (asked 2026-08-01). ANSWER: **LEAVE IT, TEST FIRST**
**Current mount (live TF):** `base_link->camera_link` = **(0, 0, 0.305)**, pitch **2.33° down**, roll 0.57°.
So the camera is at the **vehicle centre**, 30.5 cm up, **33.7 cm behind the 0.337 m bumper plane**.
**🔴 DO NOT MOVE IT YET — the measurement that would justify moving it has not been made.** We cannot
yet prove the occluding structure is the ROVER rather than the room (see the re-measure note above).
**THE DECISIVE TEST, and it is cheap:** rotate the vehicle **30-45°** and re-measure the `/scan_3d`
beams at **−45.8°..−33.9°**. **Bearing+range unchanged ⇒ it is the rover** (mount change or masking
justified). **Sweeps with the vehicle ⇒ it is the room** and the mount is fine. Fold this into the
**outdoor 08-02** session that already has to happen for yaw → [[project-rover-autonav]].
**Why a setback is probably RIGHT anyway, two independent geometric reasons:**
1. **Sensor near limit.** Min valid depth measured **0.308 m** (nothing closer is ever returned).
An obstacle touching the bumper is currently at slant range √(0.337² + 0.305²) ≈ **0.454 m** — safely
inside the working range. **Move the camera onto the bumper and that same obstacle sits at ~0.305 m,
right at the blind-zone edge — invisible at exactly the moment it matters most.**
2. **Vertical FOV, not range, sets the near blind zone.** VFOV ~65° with 2.33° down-pitch puts the
lower edge **34.8° below horizontal**; from 0.305 m that meets the floor at **0.44 m from the camera =
only ~10 cm past the bumper.** Moving the camera forward drags this blind zone forward with it — it
does not shrink it. **Raising or tilting the camera changes this; sliding it forward does not.**
⇒ **If the occluder does turn out to be the rover, prefer (a) an angular mask on the known self-occupied
bearings or (b) raising the camera — both far cheaper than relocating, which invalidates the extrinsics
that are already only sampled over 1.0-1.4 m.**

## ✅ HEIGHT BAND VALIDATED 2026-08-01 20:53 — **RANSAC PLANE FIT, ONE LOCATION**
Clean system (retry storm stopped), open area, 10 pooled frames, 245 911 pts.
**Floor plane in `base_link`, 9833 inliers, residual RMS 9.9 mm, coverage 0.4-3.5 m:**
`z = +0.00638·x +0.02681·y −0.01203`  ⇒ **forward tilt +0.37°**, lateral tilt +1.54°
| x | 0.5 | 1.5 | 2.5 | 3.0 m |
|---|---|---|---|---|
| floor z | −0.009 | −0.003 | +0.004 | +0.007 |
| margin to 0.12 | +0.129 | +0.123 | +0.116 | +0.113 |
**Crosses 0.12 m at x = 20.7 m — ~7× beyond the 3 m working range. NO phantom obstacles.**
⚠️ **ONE LOCATION ONLY.** Repeat at 2-3 spots before treating it as general.

### 🔑 METHOD — percentiles DO NOT WORK for this, use a plane fit
**p5 and p50 give OPPOSITE answers and both are wrong.** Depth noise grows with range, so the low
percentile SINKS (p5: −0.015 → −0.048 over 1.5-2.5 m) while the median CLIMBS past the threshold
(p50: 0.008 → 0.132). Percentile fits reported **±2.6° of tilt; the plane fit says +0.37°.**
⇒ **Always RANSAC-fit the floor plane over z<0.25, 0.4<x<3.5, then read the crossing off the plane.**

### 🔎 TWO FOLLOW-UPS THIS RAISED
1. **`min_height = 0.12` is likely more conservative than needed.** This fit puts the floor at
**−0.012 m**, ~6 cm lower than the 0.043-0.093 m the 0.12 was chosen against. If the floor really sits
near z≈0, **0.12 could come down to ~0.06-0.08 and roughly HALVE the minimum visible obstacle height**
(today anything under ~12 cm is invisible). **Measure 2-3 locations before changing it.**
2. **Lateral tilt +1.54° vs 0.573° roll in the static TF.** Either a genuinely sloped floor or a roll
extrinsics error — **a single pose cannot tell them apart.** Harmless for the band (within the ±46°
FOV the floor stays under 0.09 m at 3 m) but it WILL matter for the wider-FOV STL-19.

## ❌ ATTEMPT 1, 20:35 — INCONCLUSIVE (kept for the method)
Do NOT read this as a pass. Script: `validate_band.py` (floor p5 per 0.25 m bin, then a linear fit).
**Why it failed:** only **3 bins had floor data (1.5-2.25 m)** — nothing from 0.5-1.5 m or beyond
2.25 m. The fit claimed "floor reaches 0.12 m at x = 6.55 m, SAFE" but that is a **3-point
extrapolation over a 0.75 m span**, from p5 values that are **non-monotonic and NEGATIVE
(−0.021, −0.050, −0.005)** — contradicting the recorded floor of 0.043-0.093 m. It also ran at
**load 4.18-6.45** because of [[project-rc-control-camera-retry-storm]].
**To redo properly:** stop the retry storm (TX switch to neutral), find **≥4 m genuinely clear**,
and require floor data in **most bins from 0.5 to 3.0 m** before believing any slope.
⚠️ **Use p5, never the median** — the median is contaminated the moment anything stands in a bin.
⚠️ Negative p5 suggests p5 is picking up the depth-noise tail at range; consider a plane fit to the
floor points instead of per-bin percentiles.

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
