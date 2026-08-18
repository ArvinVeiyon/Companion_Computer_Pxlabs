---
name: rc_ch10_reboots_companion
description: Companion reboot loop when the uXRCE UART is connected is NOT a fault — it is RC CH10 (shutdown/reboot stick) reaching rc_control_node over /fmu/out/input_rc
metadata: 
  node_type: memory
  type: project
  originSessionId: 6126dc14-53e8-400a-80c4-99e8d59e8dbf
  modified: 2026-08-16T09:26:52.778Z
---

# The "uXRCE connection reboots the companion" symptom is RC CH10 — 2026-08-16

**SYMPTOM (cost two sessions):** connect the FC uXRCE-DDS UART (`ttyAMA4`) → the **companion
computer** reboots ~40-60 s after every boot, endlessly. Disconnect the UART → rock stable.
Operator disconnected it to get work done; reconnecting after stopping vision rebooted it again.
**Vision is irrelevant to this — do not test it that way.**

## 🔑 THE MECHANISM — it is not a crash, it is a deliberate `sudo reboot`
`rc_control_node` subscribes to **`/fmu/out/input_rc`** (`rc_control_node.py:71`). That topic
**only exists when the uXRCE-DDS agent is talking to the FC.** So:

- **UART out** ⇒ no `input_rc` ⇒ the stick logic **never evaluates** ⇒ box is stable. *The stability
  is not evidence that the UART is the fault — it is evidence the RC data is being withheld.*
- **UART in** ⇒ `input_rc` flows ⇒ CH10 is read ⇒ `subprocess.Popen(['sudo','reboot'])`
  (`rc_control_node.py:181`) ⇒ clean reboot ⇒ repeat forever.

**CH10 3-position switch (`config/rc_mapping.yaml`, `shutdown_reboot_node`): tolerance ±100, hold 2.0 s**
| position | PWM | effect |
|---|---|---|
| down | 1012 | safe — the ONLY safe detent |
| **mid** | **1514** | **`sudo shutdown -h now`** |
| **up** | **2014** | **`sudo reboot`** |

⚠️ **The MIDDLE detent is shutdown.** A switch left anywhere but *down* is a latched kill.
⚠️ `channel_index: 10` in the yaml is **1-based** (code does `-1`); camera switch is CH9.

## ✅ HOW IT WAS PROVED (use this, it takes one command)
`journalctl -b -N | grep "COMMAND=/sbin/reboot"` →
`sudo[2843]: roz : PWD=/home/roz/ros2_ws ; USER=root ; COMMAND=/sbin/reboot`
`PWD=/home/roz/ros2_ws` is `rc_control_node.service`'s `WorkingDirectory` ⇒ **that is the node, not a human.**
Every boot ended via `systemd-reboot.service` (**clean, software-requested**) — 14 boots on 08-16.

## ⛔ DEAD ENDS — do not re-run these
- **Power/brownout: DISPROVEN.** `vcgencmd get_throttled` = `0x0`, no under-voltage in any boot.
- **Watchdog / kernel panic: DISPROVEN.** Clean shutdown path every time.
- **The rclpy tracebacks in `rc_control_node` logs at reboot time are a SYMPTOM** —
  `ExternalShutdownException` is just the node being SIGTERM'd *by* the shutdown. Reading them as
  the cause wastes a session. → [[test_before_concluding]]

## 🔴 SUSPECT THE 08-16 "FC HARDFAULT LOOP, ≥9 reboots" ENTRY
`todos.md` item (c) records `wq:uavcan` stack overflow with "≥9 reboots 08-16". **Today's ~14
reboots were the COMPANION, RC-triggered.** Before doing any FC firmware work, **re-check which
device each of those reboots belonged to** — the count may have been pooled across two devices.
Do not swap or reflash the FC on the strength of that number alone. → [[independent_rulers]]

**Why:** the reboot arrives on the DDS link, so it *correlates perfectly* with plugging the UART in
and points every hypothesis at the transport. The actual cause is a physical switch on the RC
transmitter, which nobody is looking at because nobody touched it.

**How to apply:** before debugging ANY companion restart, **check the CH10 stick position first**,
then grep the journal for `COMMAND=/sbin/reboot`. Only after both come back clean is it a fault.
When a symptom appears/vanishes with a *link*, ask what DATA the link carries — not what the link
does. Related: [[rc_control_camera_retry_storm]] (same node), [[use_dds_not_mavlink]].
