---
name: project-rc-control-camera-retry-storm
description: "rc_control_node spawns sudo vision_config_manager on every RC message forever when the switch fails, burning a core and blocking the RC callback. Found 2026-08-01; this is the 'runaway vision_config_manager' seen twice before."
metadata: 
  node_type: memory
  type: project
  originSessionId: 93b64ead-3e68-486d-b34f-783134bfb9b6
  modified: 2026-08-01T15:41:03.871Z
---

# rc_control_node camera-switch retry storm

**Found 2026-08-01 20:38. This IS the "runaway `vision_config_manager`" that was blamed twice
before on a stray process** — once at pid 1340510 / 72.7% CPU (which silently corrupted a cloud-rate
measurement → [[project-perception-3d-costmap]]), and again mid-session after the user had already
killed it. **It is not stray. `rc_control_node` respawns it, so killing it never helps.**

## THE BUG — `~/ros2_ws/src/rc_control/rc_control/rc_control_node.py` ~78-86
```python
if desired and desired != self.last_cam_state:
    cmd = ['sudo', '/usr/local/bin/vision_config_manager', desired[0]]
    try:
        subprocess.run(cmd, check=True)   # BLOCKING, inside the RC callback
        self.last_cam_state = desired     # <-- latched ONLY on success
    except subprocess.CalledProcessError as e:
        self.get_logger().error(...)      # failure -> not latched -> retries next message
```
**Two defects:**
1. **No failure latch and no backoff.** `last_cam_state` is assigned only on success, so a
   *permanent* failure is retried on **every** `/fmu/out/input_rc` message, forever.
2. **`subprocess.run(..., check=True)` blocks inside the RC callback** — the same callback that
   handles the shutdown/reboot stick holds. **This is the safety-relevant half.**

## MEASURED 2026-08-01
- `/dev/video0` **does not exist** (`vision_streaming` deliberately stopped, "no FPV while driving")
- `vision_config_manager /dev/video0` exits **1** every time
- `/fmu/out/input_rc` = **95.1 Hz**
- **2181 failures in 10 minutes** (~3.6/s — the fork cost is what throttles it below 95 Hz)
- Each iteration forks `sudo` + `python3` ⇒ **78-100% of a core**, load reached **6.45 on 4 cores**

## ⏹ INSTANT MITIGATION, NO CODE CHANGE
**Move the camera switch on the TX to neutral/off** ⇒ `desired = None` ⇒ the guard is skipped and
the storm stops. (Do NOT stop `rc_control_node` — it is the RC control path.)

## ✅ FIXED + PUSHED 2026-08-01 21:08 — `9893d6b` on ros2_ws origin/main
**Verified: 317 failures/min → 3 attempts over ~2 s, ONE log line, then silent. Load 6.5 → 2.6.**
What the fix does (`rc_control_node.py`):
- **Latches `cam_attempted` (the ATTEMPT), not the success** ⇒ a target is tried once, never per-message
- **3 retries with backoff** (0.5 s, 1.0 s) first, for genuinely transient failures, then gives up
- **Give-up logged ONCE**, with the real stderr, not at the RC rate
- **Clears the latch when the switch sits between detents** ⇒ **cycling the switch away and back
  re-attempts**, so a give-up is recoverable without restarting the service
- **Spawn moved to a worker thread** + `timeout=10` ⇒ can no longer delay the shutdown/reboot stick
  detection that runs later in the same `cb_rc`, and a hung binary cannot wedge it
- Bounds-checks the mapped channels against `channel_count`
- **`shutdown`/`reboot` logic deliberately UNCHANGED** (verified in the diff)
🔴 **STILL OPEN: it keys the camera by `/dev/video0`.** That is the root trigger and violates camera
rule (1). Real close-out is **Multicam Phase D / todo #8 → `usbcam-<vidpid>-<serial>`**.

## WHAT THE NODE ACTUALLY DOES (was undocumented)
Bridges **RC transmitter switches → companion actions**, off `/fmu/out/input_rc` at **95 Hz**.
Config: `rc_control/config/rc_mapping.yaml`, **read once at startup — NOT ROS params**, so
`ros2 param set` cannot change any of it.
- **CH9, tol ±50 — camera:** 1012=front `/dev/video0` · 1514=bottom `/dev/video2` · 2014=split (both)
- **CH10, tol ±100, hold 2.0 s — system:** 1514=`shutdown -h now` · 2014=`reboot` (one-shot latched)
⚠️ **CH9 RESTS AT 1011 = the "front" detent.** So a camera switch is requested at all times by default.
⚠️ Stopping `rc_control_node` costs **RC camera switching + the RC shutdown/reboot stick** — nothing
else. It publishes **no vehicle control**; that is PX4 on the FC. Safe to stop for bench testing.

## ORIGINAL FIX PLAN (kept for reference)
- **Latch the attempt, not the success:** record what was *attempted* so a permanent failure is not
  retried; re-arm only when `desired` actually changes.
- **Add backoff + a give-up** on repeated failure, and log once rather than 95×/s.
- **Get the blocking call out of the RC callback** — hand it to a worker thread or a timer.
- **Root trigger: it keys the camera by `/dev/video0`.** That violates camera rule (1) (never key by
  `/dev/videoN`) and is exactly what **todo #8 "Multicam Phase D → usbcam ids"** exists to fix.
  `camera_sw_node_obsolute.py:70` has the same call and is already slated for deletion (#17).

## ⚠️ THE LESSON THAT COST TWO MEASUREMENTS
**Check `ps -eo pid,pcpu --sort=-pcpu` BEFORE trusting any rate/CPU number on this 4-core box, and
if a hog reappears after being killed, find its PARENT (`ps -o ppid=`) rather than killing it again.**
The parent here was `rc_control_node`, not anything camera-related.
