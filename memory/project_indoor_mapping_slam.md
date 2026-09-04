---
name: indoor-mapping-slam
description: "Indoor RTAB-Map mapping — DONE 08-08. Wheel-odom replay fixed loop closure (4→60), Grid/RayTracing:=true fixed the grid. house_map_v2 is Nav2-loadable."
metadata: 
  node_type: memory
  type: project
  originSessionId: 3d2afe7a-6695-4390-92a2-ad91c7476c89
  modified: 2026-08-08T06:29:52.064Z
---

# Indoor mapping / RTAB-Map — 2026-08-07/08 session

**One line: `house_map.pgm` (08-02) was INVALID. Root cause found and fixed. A wheel-odometry
bag replay now gives 60 accepted loop closures vs 4–5, and a map with straight walls.**

Companion docs: `~/ros2_ws/docs/indoor_mapping_plan.md` (the plan; §6 Step 5 is what this
session finally executed), `docs/autonomy_plan.md` (M3 / T6–T7 is where mapping sits).

---

## 1. 🔴 `house_map.pgm` IS A FALSE MAP — do not build on it

It looked plausible — a smooth closed blob — because **38 loop closures were accepted with the
consistency check DISABLED**. They crushed the map shut. Evidence: the optimizer squeezed the
trajectory 6.37 m → 5.51 m in x and halved z 1.92 → 0.90 m. Not structure, folding.

**34 of those 38 closures fail the check.** They stay rejected even with the graph forced planar,
so they are genuinely inconsistent, not victims of 6-DoF slop.

## 2. The two settings that were wrong (KEEP THESE FIXED)

| param | was | why it mattered |
|---|---|---|
| **`Reg/Force3DoF`** | `false` | A planar ground rover solved in full 6-DoF. Odometry drifted **up to 3.95 m vertically** (raw db), 1.92 m in the optimized one. Setting `true` → z span exactly **0.00**. |
| **`RGBD/OptimizeMaxError`** | `0` | `0` **disables loop-closure rejection**. This is what let the 34 bad closures in. Restore to **3.0** for MAPPING. |

⚠️ **`RGBD/OptimizeMaxError: "0"` in `rover_nav2/config/rtabmap_localization.yaml` is
DELIBERATE and correct THERE** — localization must accept a large map→odom correction. Mapping
and localization want opposite values. Don't "fix" the localization one.

## 3. 🔑 THE BREAKTHROUGH — wheel odometry, not visual

Replaying the bag with **odom taken from TF** (wheel) instead of visual odometry:

| | visual odom (08-02) | **wheel odom (replay)** |
|---|---|---|
| accepted closures | **4–5** | **60–67** |
| nodes | 418 | 480 |
| odom length | 44.4 m | 48.7 m |
| optimized poses / path | 198 / 34.2 m | 292 / 46.4 m |
| extent | — | 7.92 × 4.71 m |
| z span | 0.90 m | **0.00 m** |

**Answers the plan's open question "is `/odom` good enough through turns?" → YES.** Not because
it doesn't drift (it does, 33–44°/few min per the localization yaml) but because **closures fire
often enough to correct it**. The prediction that wheel-odom yaw drift would sink this was WRONG.

⚠️ **Feed odom from TF, NOT the `/odom` message** — `rover_odometry` publishes a CONSTANT pose
covariance; RTAB-Map derives link info from the CHANGE in covariance, gets zero, and hits a fatal
in `Link.cpp::setInfMatrix`. Use `odom_frame_id: odom` + `odom_tf_{linear,angular}_variance`.

## 4. ⛔ `rtabmap-reprocess -odom` CANNOT RECOMPUTE ODOMETRY — structural, not tunable

The db stores **SLAM keyframes at 1.59 Hz**; the bag has images at **14.9 Hz**. Visual odometry
needs consecutive frames close together — at 0.63 s apart tracking dies immediately.
Two runs failed this way (134/418 and 82/418 nodes, 0 closures) before the cause was seen.
**Any odometry change requires replaying the BAG.** DB reprocess can only fix the *graph*.

## 5. ❌ The ROI/plate finding — REAL PARAMETER GAP, NEGLIGIBLE EFFECT

`Kp/RoiRatios` and `Vis/RoiRatios` = `0.0 0.0 0.0 0.35` (plate masked from matching) but
**`Grid/DepthRoiRatios` = `0.0 0.0 0.0 0.0`** — never masked from the occupancy grid.

**BUT a 6-point sweep (0.00 → 0.35) changes the map by ~0.1%:** free 33.5–34.9%, occ 3.9–4.1%,
and the three rendered grids are visually identical. **The plate is NOT the central black
cluster** — those clusters are real furniture and survive every mask setting.
⇒ Set `Grid/DepthRoiRatios` for correctness, but **do not expect it to fix anything.**
Full ROI family (only one hole): `Kp/RoiRatios` ✅ · `Vis/RoiRatios` ✅ · `Grid/DepthRoiRatios` ❌ ·
`Mem/DepthAsMask` / `Vis/DepthAsMask` = true ✅.

## 6. ✅ CLOSED 2026-08-08 — it was `Grid/RayTracing`, and §6's old diagnosis was BACKWARDS

**`Grid/RayTracing` was `false`.** RTAB-Map then writes free cells ONLY where it segments *ground*
points, and this rover barely sees floor (camera at 0.305 m): across 480 nodes the stored cells hold
**17 210 ground points vs 550 146 obstacle points, 32:1**. The grid became "every surface above
`Grid/MaxGroundHeight` 0.10 m", with no carved interiors.

| | RayTracing false | **true** |
|---|---|---|
| occupied | 34.2% (19 300 cells) | **12.5%** |
| free | 3.9% (2 190) | **34.1%** |
| unknown | 61.9% | 53.4% |

⚠️ **Ray tracing is NOT optional on a low-mounted RGB-D rover.** The reason to leave it off ("the
sensor already reports free space") assumes a lidar sweeping the floor plane.

🔴 **THE 08-07 "walls not marked occupied" FINDING WAS THE COLOUR TABLE, NOT THE MAP.**
`rtabmap-reprocess -g2` writes **89=unknown, 178=free, 0=occupied**; Nav2 uses **205/254/0**. Only
*occupied* agrees. `0` is the LARGEST class in a bad map and the SMALLEST in a good one, so reading
`0` as free **inverts the diagnosis exactly**. ⚠️ I flip-flopped twice on this by arguing from
plausibility. **Disambiguate by MECHANISM: enabling ray tracing can only ADD empty cells, so
whichever value grows is free.** → [[eliminate-hypothesis-whole-family]]

**Deliverable: `~/house_map_v2.pgm` + `.yaml` (+ `house_map_v2.db`), Nav2 trinary, 257×221 @0.05,
origin `[-10.554, -4.843, 0]`.** The export needs three fixes: flip vertically (**it stores y
increasing with row index**), remap the colours, and **recover the origin** — rasterise the stored
`obstacle_cells` at `rtabmap-export --poses --opt 2` poses and correlate vs the occupied mask
(5846/7103 cells overlap ⇒ unambiguous).
🔑 **ALWAYS validate a map on the trajectory: every optimized pose must land on a free cell.**
Got **285/292 free, 7 occupied (poses hard against furniture), 0 unknown** — one check that
confirms origin + flip + colour convention at once.

✅ **VERIFIED IN `map_server`, not just geometrically:** loads, activates, publishes `/map`
257×221 @0.05, origin (−10.554,−4.843), **unknown 53.4% / free 34.1% / occupied 12.5%**; all 292
poses in bounds, **285 free / 7 occ / 0 unknown** on the published `OccupancyGrid`.
⚠️ **I first wrote "walls 0.3–0.5 m thick and doubled" — EYEBALLED off the image, WRONG.** Measured
two ways (distance-transform ridge + run lengths): **median thickness 0.10 m = 2 cells**, p90 0.22 m,
max 0.71 m (furniture, not doubled walls). ⇒ **Map geometry is NOT the bottleneck — do NOT go tune
the pose graph on the strength of how the picture looks.** → [[feedback-test-before-concluding]]
📌 Params promoted out of scratch → **`ros2_ws/src/rover_nav2/config/rtabmap_mapping.yaml`**
(`d182856`); full write-up in `docs/indoor_mapping_plan.md` §9.

## 7. Hypotheses ELIMINATED (do not re-propose)

- ❌ **Re-drive needed** — no. `/odom`, `/tf`, registered RGB-D all in the bag.
- ❌ **Depth not registered** — it IS. RGB and depth both **640×360**; calibration carries cam
  z = 0.3049 matching `rover_geometry.md`. The plan's "camera reconfig" step was already done.
- ❌ **IMU needed** — not recorded in either bag, and not required: `Force3DoF` is a *stronger*
  constraint than gravity-alignment for a planar rover.
- ❌ **Yaw deadband (#20) wrecking odometry via violent turns** — measured p50 0.02, p90 0.39 rad/s,
  only 3.6% of intervals >0.67. Driving was gentle. (Caveat: 601 ms keyframes average over 0.6 s.)
- ❌ **Plate masking broken in the matching path** — it was correct all along.

## 8. Where mapping sits — it is the LAST rung

`autonomy_plan.md`: mapping = **M3 / tests T6–T7**, behind S1 kill · S2 sensor loss · T1 speed ·
T2 straight goal · **S3 yaw (= #20)** · T3–T5. **M2 point-and-go needs NO map and is available now.**
L1 is 0 of 7 done. Building the map now is defensible (offline, Manual bypasses the yaw loop,
long-lead item) but a perfect map still leaves L1 untouched. → [[rover-autonav]]

## 9. Reproducing the replay

**Params now live in `ros2_ws/src/rover_nav2/config/rtabmap_mapping.yaml`.** ⚠️ The 08-07 scratch
`replay.sh` + `replay_wheel.yaml` are **GONE** (scratchpad is per-session) — the launch/bag-play
wrapper still needs rewriting; only the params survived.
**Grid-only changes need no replay:** `rtabmap-reprocess -g2 --Grid/X val in.db out.db` (~3 min).
- **`ROS_DOMAIN_ID=42` is MANDATORY** — `rover-odometry` and `rover-camera` are live and publish
  `/tf` and `/camera/*` on domain 0. A replay there collides with the running rover.
- `ros2 bag play --clock --rate 0.3` (264 s bag → ~15 min), `use_sim_time: true`, `nice -n 19`.
- ⚠️ **Shutdown was too aggressive** (SIGINT then SIGKILL at 30 s): db closed with `0 words` and
  `Optimized graph: 0 poses`. Link counts survived, but **give it longer to flush.**
- **KEEP:** `~/house_map_v2.{pgm,yaml,db}` (the deliverable) and `rtabmap_replay_wheel.db` (the
  source graph every grid reprocess starts from).
- **SAFE TO DELETE in `~/`:** `rtabmap_run3_{fixedA,B1,B2,C,E}*`, `sweep_roi_*.db`,
  `rtabmap_replay_wheel_grid*`, `gridtest_raytrace*`, and the whole 08-02 set
  (`rtabmap_{final,visual,masked,nav,icp_*,run3_raw,run3_nav,run3_visual,run3_vis_nav}.db`)
  — ⚠️ except `rtabmap_run3_vis_nav.db`, which `rtabmap_localization.yaml` still points at.

---

## 10. LOCALIZATION MEASURED ON THE PI 2026-08-08 — it fits, but it CRASHES

Ran `rtabmap_slam/rtabmap` with `rtabmap_localization.yaml` against `house_map_v2.db`, live
camera, `vision_streaming` active, rover parked.

✅ **It fits comfortably. ~27.5% of ONE core steady-state** (46% during the startup transient),
6.7% RAM, **RTAB-Map 71-87 ms per cycle against a 0.5 s budget = ~16% duty**, delay ~0.19 s,
291 nodes in working memory, `/localization_pose` at 1.8 Hz (config 2.0). **`map->odom` IS
published** — the AMCL replacement works. **No measurable `/scan` degradation** (16.8 / 15.5 Hz
with it running, ≥ the run-before-it baseline). Compare mapping's `rgbd_odometry` alone at 79.6%
of a core with `/scan` HALVED. ⚠️ **Rover was STATIONARY — this is a FLOOR, not a ceiling.**

✅ **`RGBD/CreateOccupancyGrid: "false"` is the right setting for localization** — the map already
has grids. Saved ~18 points of CPU (46 → 27.5%) and killed a per-frame ERROR: the db carries
`Grid/DepthRoiRatios 0.35`, which at 640×360 leaves 234 rows, **not divisible by
`Grid/DepthDecimation=4`**, so `util3d.cpp:1251` rejected the ROI every single frame.
⚠️ **So the `Grid/DepthRoiRatios` I added for "correctness" NEVER APPLIED at 640×360.**

✅ **CONFIRMED by a 15-min monitor: `/camera/depth/image_raw` emitted ONE 1280×800 frame at
t=341.5 s and was back to 640×360 0.2 s later.** `/camera/depth/image_unaligned` runs at exactly
1280×800 ⇒ the unaligned stream briefly surfaces on the aligned topic. ⚠️ `depth_registration:=true`
IS set (in the **drop-in** `10-point-cloud-decimation.conf`, not the base unit — I misread that once).
🔴 **THE CAMERA IS STILL IN MAPPING CONFIG: `color_fps:=15 depth_fps:=15`.** The drop-in's own note
says **REVERT BEFORE ANY AUTONOMOUS DRIVING — it halves `/scan` ~30→~15 Hz and widens the collision
reflex gap.** Not reverted. **This is also why I measured `/scan` 15.7 / `/scan_3d` 14.1 Hz and
wrongly blamed my own session load.** Restore from `...conf.bak-20260802` (KEEP decimation +
registration), daemon-reload, restart, then the half-dead check.

🔴 **BLOCKER — a single bad depth frame KILLS localization outright.** After ~13 min it hit a
FATAL in `Memory.cpp:4579::createSignature()`: **`image=(640/360)` but `depth=(1280/800)`**. Depth
must be ≤ colour, so the assertion aborts the PROCESS (`terminate called after throwing UException`)
— not a dropped frame, not a warning. **Both topics read 640×360 when polled, so the 1280×800 depth
frame is INTERMITTENT and its source is unidentified.** ⇒ **2A/2B cannot rely on localization until
this is understood**; at minimum it needs a supervisor/restart, but the frame itself is the bug.

⚠️ **`/odom` did NOT doze this session** — 100 Hz while parked, `esc_online_flags: 15` (all four
online), **zero TF stalls in the whole run**. An earlier run the same day DID stall on
`odom->base_link`. So the "dies at rest" fault is intermittent, not deterministic.
❓ **UNRESOLVED:** `map->base_link` would not chain even while `map->odom` and `odom->base_link`
both existed — but rtabmap had already aborted by then, so this is probably just the crash. Re-test.

→ [[perception-3d-costmap]] · [[check-docs-before-measuring]] · [[eliminate-hypothesis-whole-family]]
· [[feedback-test-before-concluding]] · [[rover-autonav]]

---

# 2026-08-08 EVENING — the crash is FIXED, and it was hiding a bigger problem

## 11. ✅ #26 SOLVED — the wrapper published UNALIGNED depth on the ALIGNED topic

**Root cause (code, not luck):** `gemini_330_series.launch.py:263` defaults `align_mode:=SW`, so
depth is aligned to colour **in software, per frameset**. In `ob_camera_node.cpp:6157`, when a
frameset arrives without a usable colour frame the align step is **skipped — and execution falls
through and publishes the still-native 1280×800 depth on `/camera/depth/image_raw` anyway.**
The skip is `RCLCPP_DEBUG`, which is why nothing was ever in the journal.
🔑 **Upstream ALREADY KNOWS unaligned depth reaches that point — it guards `logFrameInfoOnce()`
against this exact dimension mismatch. It guarded the LOGGING and not the PUBLISHING.**

**Fix:** `isDepthAlignedToTarget()` drops the depth image **and the point cloud** for such a
frameset, with a throttled WARN. Dropping the cloud matters as much: an unaligned cloud becomes
one garbage `/scan_3d` frame and **the collision reflex reads that.**
📦 `~/codex-work/orbbec_unaligned_depth_guard_20260808.patch` (`codex-work 16665f5`) — **the clone
is GITIGNORED, so a re-clone silently restores the bug.** ros2_ws `69d9c89`. Build = 15 min 45 s.

**PROOF:** 1 h 23 m soak, 9976 cycles, **0 aborts** (was ~13 min to death). Guard fired **4×**:
🔑 **1 at EVERY camera start, 23 ms before colour's first frame — DETERMINISTIC, and it was
publishing a 1280×800 frame every single boot.** That was a second occurrence nobody knew about.
The other **3 were mid-run — each one would have killed rtabmap.** A 16.6 min pre-fix baseline
never reproduced it (43 669 frames, all 640×360, colour and depth counts EXACTLY equal), so the
event is **load-linked and rare — do not conclude "fixed" from a quiet baseline.**

🛠 `tools/depth_align_watch.py` (catch the frame + colour staleness) · `tools/camera_restart_check.py`
(**`systemctl is-active` does NOT catch a half-dead camera start**).
⏭ **`align_mode:=HW` would move the 71%-of-a-core software alignment onto the camera AND kill this
bug class structurally** (the align_filter_ path never runs). Check `isSupportedResolution` for
640×360 first. Not tested.

## 12. 🔴🔴 LOCALIZATION HAS NEVER RELOCALIZED — 0 accepted closures, ever

🔑🔑 **ACCEPTANCE TEST = ≥1 ACCEPTED LOOP CLOSURE. `map->odom` PROVES NOTHING.** In localization
mode RTAB-Map publishes the db's **stored** pose against a fresh odom origin (measured −7.31 m /
−167°) and `/localization_pose` ticks 2.1 Hz **whether or not it knows where it is.**
⚠️ **§10's "map->odom IS published — the AMCL replacement works" rests on exactly this signal and
is NOT evidence.** It was never checked for accepted closures. Do not carry it forward.

### Ruled out by measurement — do not re-propose
| hypothesis | verdict |
|---|---|
| intrinsics mismatch db vs live | ❌ **IDENTICAL**: `fx 304.050 fy 304.232 cx 322.632 cy 183.795 @640×360`. **fps 15→30 does NOT change intrinsics** — they follow sensor MODE, not rate. |
| bad/absent depth | ❌ **83% valid** in the ROI RTAB-Map uses |
| CPU / the Pi being too small | ❌ **5–41% idle, ~0% iowait**, RAM 1.8 of 7.9 GB |
| `Vis/MinInliers` too strict | ❌ **0 inliers is structural, not a threshold miss** |

### Position 1 — blank wall: DIAGNOSED
1466 candidates, **all rejected at exactly 0 inliers** from 26–47 matches.
Depth p25/p50/p75 = **1.256 / 1.265 / 1.285 m ⇒ 83% of the ROI within 3 cm of ONE PLANE.**
🔑 **A PLANE IS A DEGENERATE CONFIGURATION for PnP/RANSAC** — coplanar points cannot resolve a
unique pose, so 0 inliers is *forced*. **83 min parked facing a wall is the worst possible test:
no new viewpoint ever arrives.**
📷 **Grabbing the actual colour frame settled in ONE STEP what three hypotheses could not. LOOK AT
THE IMAGE.** (Rover ~1.27 m from a featureless green wall; own top plate in the bottom third.)

### Position 2 — centre of the room: 🔑 IT LOCALIZED. THE BLOCKER IS THAT THE ROVER NEVER MOVES.

    17:39:38.847  Rejected loop closure 413 -> 2036: 0/12 inliers
    17:39:39.322  Rtabmap.cpp:3772::process() Localization was good, but waiting
                  for another one to be more accurate (RGBD/MaxOdomCacheSize>0)

**RTAB-Map RELOCALIZED at cycle 2037.** With `RGBD/MaxOdomCacheSize > 0` it then requires a
**SECOND, corroborating localization, verified against the odometry travelled in between**, before
it commits the correction. **The rover is stationary ⇒ no odometry accumulates ⇒ the second fix can
never be verified ⇒ it waits forever.** Every candidate proposal stops dead at that line; the log
ran another 3.5 h in silence, which is the *waiting* state, not failure.
⇒ **Same root cause as the wall test in a different mask: a STATIONARY rover cannot finish this.**

**⏭ FIX — try in this order:**
1. **Push the rover a metre or two by hand.** Pushing turns the wheels, the VESCs wake and report
   eRPM (nudge test, 07-26), so **wheel odom DOES accumulate** — no arming, no S1 dependency.
2. If that is not wanted: `RGBD/MaxOdomCacheSize: 0` accepts the first fix uncorroborated —
   faster, but it trusts a single match with no consistency check.

**Map coverage is NOT the problem** — db keyframes within 1 m of the mapped centre (ids 398-409)
show the **same drawer tower, wardrobe, green wall and black pipe the camera sees right now.**
⚠️ But from that centre the mapping run only ever looked in **two directions (~−88° and ~+160°)**,
and the map was built in **daylight** vs this 19:30 artificial-light test. Both are worth keeping in
mind if matching stays marginal — neither is currently proven to matter.

⚠️⚠️ **METHOD FAILURE, recorded so it is not repeated:** I reported "0 accepted closures, has never
relocalized" — into MEMORY.md as a headline blocker — because a grep for
`Accepted loop closure|Loop closure detected|Global loop closure` returned nothing. **The success is
a WARN, in different words, one line after the last rejection.** A grep that finds nothing proves
the PATTERN was absent, not the EVENT. → [[feedback-test-before-concluding]]

### ⏭ Exact resume command (2026-08-08 session end)

```bash
cd ~/ros2_ws && source install/setup.bash && unset ROS_DOMAIN_ID
ros2 run rtabmap_slam rtabmap --ros-args \
  --params-file src/rover_nav2/config/rtabmap_localization.yaml \
  -r rgb/image:=/camera/color/image_raw \
  -r depth/image:=/camera/depth/image_raw \
  -r rgb/camera_info:=/camera/color/camera_info
```

Then **push the rover a metre by hand** and watch for the second localization to commit.
⚠️ **Grep the log for `Rtabmap.cpp:3772` / "Localization was good", NOT for "accepted loop
closure"** — the success path does not contain that string.

---

## 13. ✅✅ 26b SOLVED 2026-08-09 — `RGBD/MaxOdomCacheSize: "0"`. §12's "MOVE THE ROVER" fix was WRONG.

**The fix, committed to `rtabmap_localization.yaml`:** `RGBD/MaxOdomCacheSize: "0"`.
Localization then commits fresh fixes **while completely stationary** — measured 21 `map->odom`
updates in 50 s, rover parked, `odom->base` frozen. This is the STRONGER outcome: the rover can
localize at power-on without moving, which "press go from base" needs.

### §12's fix was disproven by experiment — do not re-propose "push the rover"
The operator hand-pushed **2.4 m** (`odom->base` x 0.388 -> 2.218, y 0.028 -> 1.541, measured).
**`map->odom` did not change once.** So "a stationary rover cannot finish this" was wrong; real
odometry accumulated and corroboration still never happened.
**Why:** heading comes from the PX4 EKF gyro (`wheel_odometry_node yaw_source=gyro`), which drifts
**0.19 deg/s at rest — measured 18.6 deg over 96 s, wheels stationary, position frozen** (matches
the "33-44 deg over a few minutes" already noted at line 47 of the yaml). Two fixes 12 s apart
therefore disagree by ~2.3 deg of pure fiction, so the second is never "more accurate".
⇒ **There is no trustworthy heading to corroborate against. Corroboration is not a safety feature
on this vehicle, it is a deadlock.**

## 14. 🔴 NEW FAILURE MODE — THE CAMERA SILENTLY DEGRADES OVER ~1.5 h AND KILLS LOCALIZATION

**This is NOT the known half-dead-restart fault.** The camera starts healthy and **decays**:

| time | colour | depth | localization |
|---|---|---|---|
| 11:47 (boot +45 min) | 17.9 Hz | 27.6 Hz | (not running) |
| 12:23 | 12.6 Hz | 19.7 Hz | committing |
| 12:31 | 9.5 Hz | 19.6 Hz | **dead, 0/12 inliers** |
| 12:32 | 8.3 Hz | 26.5 Hz | dead |
| **after restart 12:36** | **~18-21 Hz** | **29.6-30.0 Hz** | **committing again** |

`camera_restart_check.py` **PASSES THE WHOLE TIME** — both streams negotiate 30 fps, depth-aligned-
to-colour OK, zero errors, and rtabmap logs `Did not receive data` **0** times. Only the RATES show
it. ⇒ **When localization dies, MEASURE THE COLOUR RATE FIRST, and restart the camera.**
⚠️ **Colour is capped ~17-21 Hz vs 30 negotiated even when healthy** — structural, likely MJPG
decode. **#28 was validated on `/scan`, which is DEPTH-derived, so the COLOUR rate was never
checked after it.**

### Signature to recognise
**High descriptor matches + EXACTLY 0 inliers = bad imagery, NOT a wrong place.** Match counts
went UP (21-34 -> 40-47) while inliers went to 0. A genuinely wrong place gives few matches; a
degraded colour stream gives many matches whose pixel positions are mush.

### Hypotheses DISPROVEN by measurement today — do not re-propose
- ❌ **Map coverage.** It failed at the SAME spot that had worked 6 min earlier. Position was not
  the variable. (This was my hypothesis; the operator's drive-back test killed it.)
- ❌ **Room light / auto-exposure throttling.** Light off vs on, one process, one clock:
  colour 17.6-21.4 Hz OFF vs 16.8-17.7 Hz ON — it went slightly **UP** in the dark; depth
  unchanged at ~30. ⚠️ Caveat: tested at 12:40 in **daylight**, so the lamp may be a small part of
  the illumination. This kills "the lamp throttles colour", NOT "a dark room hurts matching".
- ❌ **Rover parked inside the 0.308 m depth minimum.** Measured 85% valid rays, min 0.49 m,
  median 2.53 m. Depth was healthy throughout — the failure was never in depth.

## 15. ⏭ WHERE IT STANDS — T6 does NOT pass yet. The blocker is now POSE QUALITY.
Localization commits, but on a **stationary** rover the pose jitters:
**yaw +15.31 to +36.22 deg (21 deg spread), x -6.982 to -7.594 (61 cm)** — worse than the
±11 deg / 18 cm of the first run. 21 deg at 2 m is ~0.7 m lateral, against a 0.55 m inflation.
**Not yet good enough to hand to Nav2.**
Inliers run 3: 22x 0/12, **5x 11/12**, 6x 7/12, 3x 9/12, 1x 8/12, 1x 6/12 — everything scrapes the
`Vis/MinInliers: 12` bar. ⚠️ **LOWERING MinInliers would make jitter WORSE, not better** (weaker
fixes accepted); raising it cuts the fix rate. The real levers are **better imagery (get colour to
30 Hz)** or **a better map** — not this threshold.
⏭ Also never verified: that the committed pose is CORRECT, only that it commits. Needs ground truth.

---

# 2026-08-09 EVENING — A GOOD ROOM MAP AT LAST. THE CAUSE OF DUPLICATE WALLS WAS ODOM SCALE.

**Bag `~/map_run_20260809_185011`** — 488 s, 192,207 msgs, **ZERO drops**, colour+depth matched at
~12.3 Hz, camera restarted to 15/15 first (⚠️ it came up HALF-DEAD; the 2nd restart was fine).
Drive: 2 validation circles (1 continuous + 1 paused), a closed forward loop with stop-and-stare
full rotations, 2 more circles. 22.7 m over 472 s. ⛔ **We did NOT record `/fmu/out/esc_status`, so
odometry cannot be RECOMPUTED from this bag, only rescaled. RECORD THE RAW ESC DATA NEXT TIME.**

## The map lineage
| db | what | verdict |
|---|---|---|
| `house_map_v3` | first map on the new camera-gyro heading | ❌ **every wall drawn MULTIPLE times** |
| `house_map_v4` | SAME bag, odom translation × 1/1.188 | ✅ **walls collapsed to single lines** |
| `house_map_v5` | v4 grid reprocessed, `Grid/DepthDecimation 2` | ⚠️ ROI fixed but NEW ray-tracing spikes — **NOT ADOPTED** |

## 🔑 THE DUPLICATE WALLS WERE **ODOM SCALE**, NOT HEADING
Heading was already at 0.00028 deg/s and walls still multiplied. **19% over-reported travel × 22.4 m
= 4.3 m of error in a 3.2 × 3.9 m room.** Rescaling by 1/1.188 fixed it and shrank the room 24 cm to
its true size. ⇒ `erpm_to_ms` 0.004633 → **0.003900** (committed `192681e`).
🔑 **Rescaling recorded TF == driving with the corrected constant**, exactly: heading is
gyro-derived and independent of `erpm_to_ms`, so scaling v scales x,y by the same factor. Same-bag
re-map is therefore the RIGOROUS experiment, not merely the convenient one.

## 🔴 THE ROVER'S OWN TOP PLATE IS IN THE MAP — "NEGLIGIBLE EFFECT" IS WITHDRAWN
`Grid/DepthRoiRatios 0.0 0.0 0.0 0.35` was **IGNORED ON EVERY FRAME**: 360×0.65 = 234 rows, and
RTAB-Map needs that divisible by `Grid/DepthDecimation` (was 4; 234/4 = 58.5). **11.8% of v4's cloud
(31,299 of 266,053 points) was the rover's own body**, drawn at every position it occupied —
the operator SAW the driven path traced through the floor. §5's "negligible effect" was WRONG.
✅ Fixed for future maps: **`Grid/DepthDecimation: "2"`** (234/2 = 117) — 740 ROI errors → 0.
⚠️ **BUT v5 gained ray-tracing SPIKES past the walls** (4× more depth points → noisy long-range
returns become spurious rays). Could punch false free space through walls. **EVALUATE BEFORE USING.**
⚠️ **UNPROVEN AND WITHDRAWN:** I claimed the plate marks the driven corridor as obstacle and would
wall Nav2 in. The grid comparison does NOT support it — v4's interior is already mostly free,
because ray tracing from later poses clears what the plate marked from earlier ones. Cloud
contamination is MEASURED; the grid consequence was inference.

## ✅ Camera gyro scale is FINE and NOT rate-dependent (retested from the bag)
0.9996 @ 9.3 deg/s · 0.9953 @ 6.1 deg/s · **1.0012 @ 19.5 deg/s**. The earlier "−4.53% at
32.7 deg/s" was **the probe integrating on ARRIVAL time**, not the sensor. Camera stamp clock is
**+0.0022%** of ROS time (0.008 deg per circle). ⇒ slow paused turns are good for image sharpness
but NOT required for scale.
✅ Also verified from the bag: **image topics ARE in ROS time** (TF lookups correct) and
**colour↔depth are synced to 0.3 ms**. Only `/camera/gyro/sample` uses the device clock.

## ⏭ OPEN — the almirah
Operator: walls fine, but the **blue almirah (x 0.4→1.6, y −0.85→−1.05) is still drawn several
times** and sits INSIDE the room. Measured: that surface is **~14 cm thick vs ~9 cm for clean walls**
(IQR, narrow strips) and is **darker and bluer** (RGB 64-153 vs 90-179). Consistent with glossy dark
steel reflecting the IR pattern away and reading short — **but NOT proven**: an almirah is a genuine
3D object, so some spread is real geometry. ⚠️ **Error is toward the rover ⇒ FAILS SAFE for nav.**
⛔ Do NOT "fix" it by deleting points from the cloud — that changes the picture, not the map.

## ⏭ NEXT
1. **Localize in v4** and measure jitter against v2's 21° — the test that decides whether the map works.
2. Evaluate the v5 spikes before adopting decimation 2 on an existing map.
3. Camera roll **1.54°** still uncorrected (floor plane `z = +0.00638x +0.02681y −0.01203`).

## ✅ LOCALIZATION IN v4 — MEASURED 2026-08-09 21:32
110 s, 222 samples, rover verified stationary (odom moved 0.0 cm):
| | house_map_v2 | house_map_v4 |
|---|---|---|
| yaw spread | 21.0 deg | **8.79 deg** (2.4x better) |
| x spread | 61 cm | **13.5 cm** (4.5x better) |
| y spread | — | 22.8 cm |
| typical sd | — | **1.56 deg · 3.0 cm · 4.5 cm** |

1.56 deg at 2 m = 5 cm lateral, well inside the 0.55 m inflation radius. The 8.79 deg is full
min-to-max from an OUTLIER population, not continuous noise. Health: **35 rejections in ~1018
cycles** (28 of them against ONE keyframe, **node 98** — suspect weak keyframe), **0 errors**,
0.385 s/cycle (slower than v2's 0.06-0.17 s because v4 has 740 nodes vs 480).
⇒ **The pose is USABLE where v2's was not**, and the gain tracks exactly the two root causes fixed
today (FC heading, odom scale). **NOT yet "finished"** — the outliers are the remaining work.

---

# 2026-08-16 — 🔴 LOCALIZATION HAS REGRESSED TO ZERO. IT IS NOT THE COMMIT BUG.

Re-ran E3 localization against `house_map_v4.db` per setup_manual §E3, with the §14 protocol
observed: `vision_streaming` stopped (freed 139% of a core), `rover-camera` restarted, camera
verified healthy **before** starting — colour **24.9 Hz**, depth 30.0 Hz, `/scan` 29.8 Hz — rover
parked, and I stayed off the CPU for the whole 6-minute window.

## The result: 1213 rejected loop closures, ZERO accepted
```
1176 x  0/12 inliers      <- 97% of all attempts
  11 x  7/12
  11 x  6/12
   7 x 10/12
   4 x 11/12              <- never once reaches the threshold
```
The only "correction" line in the entire log is at startup — *"Update map correction based on last
localization **saved in database**"* — i.e. the value restored from the db, not a live fix.

## 🔑 THE TRAP THAT ALMOST PRODUCED A WRONG ANSWER
`map→odom` **DID change** — 16 distinct values across 72 samples in 6 min, wandering ~19 cm in x and
~4.5° in yaw. I read that as "it commits now, the gate is clear" and **published that conclusion
before checking the acceptance count. It was wrong.** With zero fixes accepted and the rover parked,
a moving `map→odom` is **odometry drift bleeding through a stale correction**, not relocalization.
⇒ **`map→odom` CHANGING IS NOT SUFFICIENT.** setup_manual §E3 says "success is `map→odom` changing,
not merely existing" — that is necessary, not sufficient. **Always confirm with the ACCEPTED-fix
count from the rtabmap log**, never from the transform alone.

## 🔴 THIS IS A REGRESSION, AND THAT IS THE IMPORTANT PART
The section above (**08-09 21:32**) measured this same map as **35 rejections in ~1018 cycles**
(3.4%) with a pose judged USABLE. Today the same map, same config file, gives **~100% rejection**.
⇒ **Localization worked on 08-09 and does not work now.** Something changed in between. This is a
much more tractable question than the old "does it ever commit" one, which is now **moot** — nothing
is accepted, so there is nothing to commit. ⛔ **Do not keep chasing the commit/`MaxOdomCacheSize`
deadlock; that was fixed on 08-09 and is not today's failure.**

## What 0 inliers on 29–50 matches actually means
Appearance matching (the bag-of-words stage) is **working** — it proposes candidates with 29–50
feature matches every time. Geometric verification then finds **zero** consistent inliers. Zero, not
a few. That pattern says the matched features have **unusable 3D positions**, which points at the
depth/RGB relationship rather than at the rover being lost or the map being wrong.

## ⏭ NEXT — ONE CHECK DECIDES WHETHER RE-MAPPING IS WORTH DOING
Compare the **live `camera_info` (resolution + intrinsics)** against the calibration stored per node
inside `house_map_v4.db`. Cheap, stationary, needs no FC and no clear floor.
- **Mismatch** ⇒ the map and the current camera no longer agree ⇒ **re-mapping fixes it for free**,
  and the operator's offer to map the whole house is the right move.
- **Match** ⇒ the live depth pipeline is producing bad depth ⇒ **a new map would be built just as
  broken.** Fix first, then map.
🔑 **Do not start a whole-house mapping run before this check** — that is hours of work that a
5-minute comparison could save.

Related: [[perception_3d_costmap]] · [[rover_autonav]] · autonav_reference §13/§14 · setup_manual §E3

---

# §17 — 2026-09-04: THE LOCALIZATION FAULT IS REAL AND IT IS GEOMETRIC, NOT VISUAL

**Adjudicated by replaying `~/map_run_20260809_185011` — the bag `house_map_v4.db` was BUILT from —
back through `rtabmap_localization.yaml` on a COPY of the map** (`ROS_DOMAIN_ID=42`, `use_sim_time`,
rtabmap started 20 s before playback so it restores the DB first). Recipe kept in the scratch script
`replay_reloc.sh`; it is the strongest possible test because it removes viewpoint as a variable.

## RESULT: 0 accepted / 20 rejected over 649 processed frames
| inliers | attempts | |
|---|---|---|
| **0** | 17 | `Vis/MinInliers` = **12** |
| 6 / 7 / 9 | 1 each | best ever reached = **9** |

**2D matches are plentiful — median 56, min 29, max 92.** So appearance retrieval works and
**geometric verification is what fails.** Fed its own source images from the pose that created map
node 1, it still cannot verify. ⇒ **NOT a viewpoint/coverage problem. NOT "the rover is somewhere
unmapped."** A systematic depth error would CANCEL between map and replay (same images, same
pipeline) and still verify — so the surviving explanation is that **the map's 3D features and the
localization-time features are built under DIFFERENT PARAMETERS.**

## ❌ HYPOTHESES KILLED BY MEASUREMENT — do not re-propose
1. **`camera_info` mismatch** (the #1 queued suspect). Map-build bag and live are **IDENTICAL to 4
   decimals**: `640x360`, fx **304.0501**, fy **304.2317**, cx **322.6317**, cy **183.7952**, frame
   `camera_color_optical_frame`, `plumb_bob` D all-zero.
   🔴 **THE DOCS' `fx=fy=409.85 @ 848x480` IS STALE** — that is the UNREGISTERED depth path. With
   `depth_registration:=true` depth is resampled into the COLOUR frame at 640x360. **Anything derived
   from 409.85 is computed off the wrong intrinsics — including the `scan_height: 40` ⇒ ±2.79° figure.**
2. **Corrupt / feature-less map.** `Data` 740 rows, **740 with image, 740 with depth**; `Feature`
   **615 983 rows, EVERY ONE with non-null `depth_x/y/z`**. Node 333 = 917 features, all 3D,
   plausible ranges (~0.7-0.8 m). The map is intact.
3. **Missing live depth.** `/camera/depth/image_raw` 16UC1 640x360: **56.7% valid in the top-65% ROI**
   (307-5331 mm, median 416). Bottom 35% is 5.5% valid — that is the rover's own top plate, which is
   exactly what `Kp/RoiRatios "0 0 0 0.35"` masks. Working as designed.

## ⏭ NEXT LEAD (untested): DB-inherited parameters
**RTAB-Map inherits parameters from the database**, and `rtabmap_localization.yaml` already documents
one case where that bit (`Grid/DepthRoiRatios` at 640x360 leaves 234 rows, not divisible by
`Grid/DepthDecimation=4`). Compare what `house_map_v4.db` baked in against the localization YAML —
**`Kp/DetectorStrategy` + descriptor first** (a detector/descriptor mismatch gives exactly this
signature: words still match, 3D never verifies), then `Kp/RoiRatios` vs `Vis/RoiRatios`.
Read it with `rtabmap-info <db>`. ⚠️ `sqlite3` CLI is NOT installed — use python `sqlite3`.

⛔ **DO NOT "FIX" THIS BY LOWERING `Vis/MinInliers` TO 6-9.** That manufactures acceptances at exactly
the confidence that produced the FALSE 08-02 map (38 loop closures accepted with rejection disabled,
34 of which failed the check). The threshold is not the bug until the inlier distribution says so,
and a distribution of 17x0 says the opposite.

⚠️ **MEASUREMENT CAVEAT:** the bag player logged repeated `Message queue starved` — a 6.6 GB bag off
the SD card while RTAB-Map saturates the CPU. Timestamps come from the bag under `--clock` so pairing
should hold, but **if a future run's numbers look marginal, re-run with `--read-ahead-queue-size`
before concluding anything.**
