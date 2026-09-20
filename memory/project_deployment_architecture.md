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
  half. ⇒ **publish the MAP-RELATIVE pose from relocalization to PX4, not raw VIO** (same topic).
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
