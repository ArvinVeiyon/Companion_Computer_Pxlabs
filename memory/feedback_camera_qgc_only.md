---
name: feedback-camera-qgc-only
description: User rule — camera selection/config is done ONLY from QGC (G-Control); never run vision_config_manager or edit vision_streaming.conf unilaterally
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 41726602-da8e-4edf-b5e2-8b266624ecfa
  modified: 2026-07-28T16:59:51.792Z
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

---

## 2026-07-28 — REAFFIRMED, and the rule is BROADER than I had it

After the faulty LG cam was swapped for a See3CAM (`~/ros2_ws/docs/vision_streaming.md`), the conf
still held the dead camera's `camera_id`. I offered to make "just this one identity change" to
`/etc/vision_streaming.conf` on the companion. User pushed back, annoyed:

> "why it still point out old camera... our requirement is whatever camera we can configure from
> ground using the vision manager" / "then why we have camera config button or option there,
> selecting it manually on companion?"

**Why this matters more than I treated it:** the requirement is not "avoid touching the conf", it
is **any camera must be selectable from the ground**. The QGC camera page + `vision_config_manager`
IS the mechanism, and it works — the user applied the See3CAM from QGC and the tool rewrote the
conf and restarted the service itself. A companion-side edit does not just create hidden state, it
**masks whether the ground-side flow actually works** — the thing that has to keep working.

**How to apply:**
- A camera **swap** is NOT a special case that justifies a manual edit. Hardware changed ⇒ operator
  hits Apply. Never frame a conf edit as "just an identity fix" or "not really camera config".
- When the conf points at absent hardware, **say so and stop.** Do not offer to edit it.
- If a camera does not appear in the QGC list, THAT is the bug to chase (discovery/`list --json`),
  not something to route around on the companion.
- Cleaning up my OWN mess (killing a manually-started ffmpeg, restarting a service I stopped) is
  fine and distinct from camera configuration — but say which one you are doing.
