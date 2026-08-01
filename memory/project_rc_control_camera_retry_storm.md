---
name: project-rc-control-camera-retry-storm
description: "rc_control_node spawns sudo vision_config_manager on every RC message forever when the switch fails, burning a core and blocking the RC callback. Found 2026-08-01; this is the 'runaway vision_config_manager' seen twice before."
metadata: 
  node_type: memory
  type: project
  originSessionId: 93b64ead-3e68-486d-b34f-783134bfb9b6
  modified: 2026-08-01T15:10:18.538Z
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

## FIX (not yet applied — needs the user's call)
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
