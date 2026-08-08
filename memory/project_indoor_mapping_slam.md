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
