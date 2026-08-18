---
name: scope_px4_params_by_control_flags
description: "A PX4 rover param's scope comes from the flag_control_*_enabled bits per nav_state, never from its doc string — assuming otherwise put the rover into a wall."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 96c43e0e-e68d-4cd7-9119-2656bb156c0b
  modified: 2026-08-13T19:31:58.227Z
---

⛔ **Before changing ANY `RO_*` parameter, trace which controllers each `nav_state` enables. Do NOT
scope a parameter by its description.**

**Why:** On 2026-08-14 I set `RO_DECEL_LIM` 0.5 and `RO_ACCEL_LIM` 0.3 from `-1`, reasoning from the
firmware doc — *"the rover will not slow down when approaching waypoints in auto modes"* — that they
were auto-mode-only. **They are not.** The operator's next RC **manual** drive ended in a hard wall
hit. The chain (`~/PX4-Autopilot` `a52c38b07d`): `control_mode.cpp:55` sets
`flag_control_allocation_enabled` in `NAVIGATION_STATE_MANUAL` → `RoverDifferential.cpp:154` runs
`DifferentialActControl` → `DifferentialActControl.cpp:75` slew-limits the **raw stick throttle**.
Centring the stick stopped cutting the motors; the throttle ramped down over ~1.2 s while still
driving. **Allocation is enabled in EVERY manual mode**, so `DifferentialActControl` is never bypassed.

**How to apply:**
- Grep `commander/ModeUtil/control_mode.cpp` for every `nav_state` that enables the controller
  reading the param. Check `DifferentialActControl` **explicitly** — it runs in Manual, Acro, Stab.
- 🔑 **"Not yet verified on the vehicle" ≠ "not yet active."** I wrote the first and meant the
  second. A saved param is live on the operator's next stick input — there is no staging area.
  Anything that can reach the actuators is in force the moment it is written.
- 🔑 **A readback/reboot check proves a value is STORED, not that it is SAFE.** Mine passed, and the
  flash-save is precisely why the change was still live at the drive.
- ⚠️ **The reflex collision-stop does not cover manual drive** — it gates AutoNav setpoints, not the
  operator. A change that only degrades manual stopping has no safety net behind it.
- Revert direction matters: `set_param.py` writes RAM only, so **an unsaved revert means a reboot
  restores the dangerous values.** Always follow a safety revert with `param save`.

Related: [[verify_after_editing]] · [[check_docs_before_measuring]] (the manual beats my inference —
but here the *firmware* doc was the incomplete source, and the code was the ruler).
