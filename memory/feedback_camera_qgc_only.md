---
name: feedback-camera-qgc-only
description: User rule — camera selection/config is done ONLY from QGC (G-Control); never run vision_config_manager or edit vision_streaming.conf unilaterally
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 41726602-da8e-4edf-b5e2-8b266624ecfa
---

2026-07-19: After I manually ran `vision_config_manager /dev/video8` to revive the FPV stream,
user objected: "do not do anything, I will control the camera portion from QGC".

**Why:** The camera pipeline is operator-controlled from G-Control; companion-side manual changes
create state QGC doesn't know about. QGC's camera picker currently only lists up to video3 — so a
manually-applied video8 is invisible/unmanageable from the GCS, which is worse than a dead stream
from the operator's point of view.

**How to apply:**
- Diagnose and REPORT camera/stream problems; propose fixes; let the user execute via QGC.
- The correct fix for "QGC can't see the right device" is on the G-Control side (extend/make dynamic
  the camera device list in PXLABS_qgroundcontrol, see [[reference_gcs_companion_interface]] and
  todos #8) — not a companion-side workaround.
- Same restraint likely applies to other operator-facing controls (RC/camera/vision services):
  ask before acting.
