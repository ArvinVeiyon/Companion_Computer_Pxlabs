---
name: project-deployment-architecture
description: "SETTLED 2026-09-21: product = Case B (mission on a pre-built map) at a bounded SITE (yard / manufacturing unit), GPS optional, INDOOR FIRST. Depth camera is primary for localization; LiDAR is not primary but not excluded. Camera is NOT replaceable by a LiDAR. Next action is a DIAGNOSIS, not a purchase."
metadata:
  node_type: memory
  type: project
---

# Deployment architecture — SETTLED 2026-09-21

📗 **Full text with citations: `ros2_ws/docs/deployment_site_scope.md` §6–§8** (and
`px4_companion_interface.md` §9). This file is the pointer + the conclusions, not the argument.

## The product

* ✅ **Case B — a mission executed on a PREVIOUSLY BUILT MAP.** ⛔ Not Case A (start-relative), so
  **relocalization is unavoidable.**
* ✅ **Venue is a bounded SITE — a yard or a manufacturing unit, not a house.** GPS **may or may
  not** be present, even within one site ⇒ **GPS is an AID, never the architecture.**
* ✅✅ **INDOOR ("internal mode") IS FIRST.** Agrees with `autonomy_plan.md` §3 *"(first target)"*.
  ⛔ Nothing in the M/L/R ladders was reordered — only the venue was made explicit.
* 🔑 **Application A's shape (A1–A9) was already correct.** The only thing wrong in the docs was the
  **venue assumption**. ⛔ Do not renumber or rewrite A1–A9.

## The sensor decision (operator, and the reasoning that survived challenge)

* ✅ **DEPTH CAMERA IS PRIMARY FOR LOCALIZATION**, feeding **both local and global planner**.
* ✅ **LiDAR is NOT primary** — its jobs are collision/obstacle and the **268° blind arc**.
* ⚠️ **"Not primary" ≠ "excluded":** RTAB-Map is a **LiDAR *and* visual SLAM library** and fuses
  both. A fitted LiDAR may add **geometric constraint** indoors. 🔑 **Fusion, not replacement.**
* ⛔⛔ **THE CAMERA IS NOT REPLACEABLE BY A LiDAR.** A 2D LiDAR cannot see: a **person lying on the
  floor** (ISO 3691-4's 70 × 400 mm test piece — a scan plane at 200–300 mm passes over it) ·
  forklift tines / overhangs / partially occupied shelves · **negative obstacles** · anything
  semantic. ✅ And it is already bought, mounted and G0-calibrated.
  ⇒ **the question is "do we ADD a LiDAR", never "camera or LiDAR".**
* ✅ **Commonality argument (real):** a camera stack **transfers to the drone**, a 2D-LiDAR one does
  not, and the two vehicles **share the FC**. Rover alone indoors → LiDAR localizes better; rover +
  drone one stack → only the camera serves both.
* ⏭ **OPEN:** the STL-19 is *"not fitted — allocated to the drone"*. If that is for **localization**
  it is on the vehicle a 2D LiDAR helps **least**. **Check what job it was assigned.**

## The three distinctions that kept being re-argued — ⛔ do not re-open

* 🔑 **PLANNING ≠ LOCALIZATION.** Localization *produces* a pose; local/global planners *consume*
  one. **PX4's own stack proves it:** `local_planner` = VFH+\* vector field histogram,
  `global_planner` = graph planner over an octomap, camera supplies **obstacle information** to
  both — and PX4 states the global planner *"requires accurate global position and heading"*.
  ⇒ ✅ "camera feeds both planners" is **correct**, and is **not** a claim that it localizes.
  On this rover localization is **RTAB-Map**, the component returning 0/20.
* 🔑 **VIO REPLACES ENCODERS, NOT GPS.** A drone needs VIO because it has **no wheels**. This rover
  already has the incremental half ⇒ VIO matters **less** here; what is missing is the **absolute**
  half. ⇒ **publish the MAP-RELATIVE pose from relocalization to PX4, not raw VIO.**
  🔑🔑 **THE ROUTE IS THE BRIDGE WE ALREADY RUN — no new node, topic or firmware.**
  `rover-ekf-bridge` already uses `px4_ros2::LocalPositionMeasurementInterface`, and
  `LocalPositionMeasurement` carries **`position_xy` + `position_xy_variance`** next to the
  `velocity_*` fields it fills today ⇒ **populate two more optional fields.**
  ⚠️ **A WELL-DEFINED VARIANCE IS MANDATORY** — *"its associated variance value is well defined"*,
  *"Values do not have a NAN"*, else **`NavigationInterfaceInvalidArgument`**. ✅ right design:
  after a long unmatched stretch hand PX4 a **bigger variance**, not a confident lie.
  Global/lat-lon route = `GlobalPositionMeasurementInterface`, gated by **`EKF2_AGPn_CTRL`**.
  📗 PX4 Guide → *ROS 2 → PX4 ROS 2 Navigation Interface*; detail in
  `ros2_ws/docs/px4_companion_interface.md` §9.5.
* 🔑 **Drones use VIO indoors because of the MOTION MODEL.** 2D scan matching assumes **planar
  motion** — a rover meets it (3-DOF, plane parallel to floor), a drone violates it (roll/pitch tilt
  the slice, climbing moves it, no altitude, weight). ⛔ **Not evidence that LiDAR is weak indoors.**

## 🔴 Safety rating is a SEPARATE, CERTIFIED purchase

* **ISO 3691-4** (driverless industrial trucks) expects a **safety-rated laser scanner** for
  personnel detection where people may be present — layered fields, outer warns, inner stops.
* Must be **IEC 61496 Type 3**; typically **PL d** across the chain.
* 🔴 **Neither the Gemini 336L nor an STL-19P qualifies.** ⇒ a **third device**, separate from both.
* ⏭ **Confirm applicability before site selection** — it drives cost and mounting more than
  anything else discussed.

## ⚠️ "MAP" MEANS TWO DIFFERENT THINGS — the trap that recurred three times

* **Obstacle map / costmap** = *what is in the way*. Built **using** your pose, consumed by the
  planner. **PX4's `global_planner` octomap is this**; so are our Nav2 costmaps.
* **Localization map** = *what the world looks like*, matched against live sensing to recover pose.
  **RTAB-Map's `house_map_v4.db` is this.**
* 🔑🔑 **An obstacle map can NEVER localize you — it was built assuming you already knew where you
  were.** Drift writes obstacles at the drifted place; the error is baked in, not detectable.
* ⇒ PX4's *"builds a map of the environment"* is **true and irrelevant** — the same page requires
  *"accurate global position and heading"* as an input.
* ✅ **We have both; only one is broken:** Nav2 costmaps ✅ (T3 avoided + rejoined) ·
  RTAB-Map DB 🔴 0/20.

## 🔴 PX4's OWN WARNING ON GPS + VISION — bears on the site plan

* PX4 VIO page, verbatim: *"This is really difficult, because when they disagree it will confuse the
  EKF. **From testing it is more reliable to just use vision velocity.**"*
* ⇒ ⛔ **The easy plan — fuse GPS where available, fall back to vision — is the exact case PX4 says
  confuses the estimator.** 🔑 **ARBITRATE, DON'T BLEND** (one source per area), or design the
  handover deliberately. ⚠️ `EKF2_GPS_CTRL` reads **7** (fully enabled) **with no GPS fitted.**

## 🔧 PREREQUISITES BEFORE ENABLING POSITION FUSION — all read live 2026-09-21

* ✅ **The code change is small and located:** `rover_ekf_bridge/src/main.cpp:25` constructs with
  `PoseFrame::Unknown, VelocityFrame::BodyFRD`; lines 63-70 fill `velocity_xy`/`velocity_z` +
  variances and **never `position_xy`**. ⇒ **add `position_xy` + `position_xy_variance`, move
  `PoseFrame` off `Unknown`.** Nothing else moves.
* ⚠️ **`EKF2_EV_POS_X/Y/Z` = 0.0, 0.0, 0.0 — right TODAY, wrong LATER.** They are the *VI sensor
  focal point relative to the CoG*. Today velocity comes from **wheel odometry at the body frame**,
  so zero is correct. 🔑 **The moment a CAMERA-derived pose is fed they must be set from the
  measured mount** — `front_overhang` **0.337**, `cam_z` **0.305**, already known from G0.
  ⛔ Unmodelled lever arm ⇒ yaw rate becomes **spurious lateral velocity**.
* ⚠️ **`EKF2_EV_DELAY` = 0.0, UNTUNED.** PX4: estimate the IMU↔vision offset from logs, then vary it
  for **lowest EKF innovations during dynamic manoeuvres**.
* ⚠️ `EKF2_HGT_REF` is **not** Vision (PX4 says it should be for VIO). Low priority on a rover.
* 🔑 **Bring-up step worth copying:** *"Yaw the vehicle until the quaternion of the ODOMETRY message
  is very close to a unit quaternion (w=1, x=y=z=0)."* Velocities stay **FRD body frame** — already correct.
* ⚠️ **Vibration:** PX4 warns VIO cameras are *"very sensitive to high-frequency vibrations"* —
  ⛔ untested here, and relevant to hard wheels on concrete.
* ✅ **The PX4 VIO page says NOTHING about relocalization or mapping** — vendor confirmation that
  **VIO is odometry, not map localization.**

## ⏭ NEXT ACTION — a diagnosis, not a purchase

* 🔴🔴 **Relocalization: 0 accepted of 20 on the map's OWN bag, failing at GEOMETRY not appearance
  ⇒ PIPELINE FAULT.** → [[project-indoor-mapping-slam]] §17.
* ⛔ **BUY NOTHING UNTIL IT IS DIAGNOSED.** A new sensor feeding a broken pipeline buys nothing, and
  the diagnosis decides which sensor is even right. 🔑 **True under every architecture above.**
* Then, in order: finish T3 to a working value and **stop** · survey the unit (dimensions, surface,
  lighting, traffic, **longest unmatched stretch**) · decide **fiducials** (AprilTag — the proven
  answer for featureless/repetitive sites, and unique IDs kill the false-match risk) · confirm
  safety rating · then negative obstacles, the blind arc, and outdoor.

## ⚠️ Still open, unchanged by any of this

* **Negative obstacles** — `/scan_3d` filters to 0.12–0.45 m so sub-ground points are discarded;
  `/scan` reads a hole as clear road. ⛔ Neither sensor as configured sees a pothole.
* **`/odom` circular feedback** — `rover-ekf-bridge` feeds the EKF from `/odom`, so the controller
  regulates against its own under-read. ⛔ Not fixed by better calibration.
* **Odometry is a PRIOR, not the position source.** ✅ the calibration is **not** wasted — it carries
  the estimate between absolute fixes, which is how industry fuses it. ⛔ Never re-open the scale.

## ✅ THE DEPTH CAMERA'S PRIMARY JOB — confirmed by the operator 2026-09-21

* ✅ **The depth camera builds the LOCAL MAP (the costmap), and that is what PLANNING runs on.**
  This is its main role and it **already works** — T3 demonstrated avoidance and rejoin on it.
* 🔑 Consistent with the planning-vs-localization split above: the camera supplies the **obstacle
  information** the local and global planners consume. ⛔ That is not the same as it localizing.
* ⇒ **Two separate jobs, do not conflate them:**
  * **camera → local map → planning** ✅ working today
  * **relocalization → pose** 🔴 the 0/20 blocker

## 🔬 VIO / SLAM STACK OPTIONS — assessed 2026-09-21 against the live box

### ⚠️ Option A — ORB-SLAM3 / OpenVINS (VI mode) → `robot_localization` EKF

* ✅ **IMU is available and live:** `/camera/accel/sample`, `/camera/gyro/sample`.
* ❌🔴 **THE STEREO IR STREAMS ARE NOT PUBLISHED.** Live topic list is **colour + depth + IMU only**
  — no `/camera/ir/*`, no left/right. ⇒ Option A needs streams **enabled first**, at USB-bandwidth
  and CPU cost, before any SLAM runs. ⛔ Do not plan on them being there.
* ✅ The "clean IR, IR-pass filter kills indoor glare" claim is **genuine** — the 336L *is* the
  IR-pass variant. The reasoning is sound; it just is not free.
* 🔴 **CPU makes it unaffordable today.** Measured 09-21: **load 2.68 of 4 cores**, `wheel_odometry`
  54.5%, camera container 45.5% ⇒ **~1.3 cores free — and FPV streaming was OFF** (it costs **139%
  of a core**). ⇒ near-zero headroom with video. For scale, `rgbd_odometry` alone is **79.6% of a
  core stationary**.
* 🔴 **It solves the WRONG HALF.** It produces **VIO = odometry**. The blocker is **Case B
  relocalization**. ⛔ **OpenVINS has no map reuse at all** and cannot help.
* ⚠️ It would add a **third estimator** (`robot_localization` on top of PX4 EKF2 on top of RTAB-Map)
  to a system that already has `/odom`↔EKF circular feedback.
* ✅✅ **BUT IT HAS ONE REAL USE — AS A DIAGNOSTIC, NOT AN ARCHITECTURE.** Running **ORB-SLAM3's
  relocalization against the same bag** answers: *is the failure RTAB-Map-specific, or fundamental
  to visual relocalization in this environment?* 🔑 That is a different question from "should we
  ship it", and it is worth one experiment.

### ✅ Option B — RTAB-Map all-in-one (camera + `/scan`) = THE TARGET ARCHITECTURE

* ✅ **Right shape:** already running here, does **odometry AND relocalization**, and fusing visual
  features with laser scan matching is exactly the *fusion-not-replacement* conclusion.
* 🔴🔴 **CATCH THE PROPOSAL MISSED: our `/scan` COMES FROM THE DEPTH CAMERA**
  (`depthimage_to_laserscan`), **not a LiDAR.** Feeding it to RTAB-Map as a laser input is **the
  same data twice** — no independent geometric constraint, no independent failure mode.
* ⇒ **Option B only pays off once a REAL LiDAR is fitted.** ⛔ Do not expect a gain from wiring it
  up against the camera-derived `/scan`. ⏭ Worth **designing toward** now so the LiDAR decision is
  not retrofitted.

### ⏭ Order

1. 🔴 **Diagnose the 0/20 first.** Both options are "add more stack"; neither explains why
   relocalization fails at **geometry** on its own bag, and both would inherit the fault.
2. **Option A once, as an experiment** (enable IR, measure bandwidth + CPU, A/B the relocalization).
3. **Option B as the target**, gated on a LiDAR.
