---
name: mavlink_shell_session_exhaustion
description: "Repeated mavlink_shell.py runs wedge the FC's MAVLink instance and kill the GCS link — one shot per reboot"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6daf144e-af4b-4b5f-9eaf-ca7a2efa94a8
  modified: 2026-08-16T18:44:15.943Z
---

**Repeated `mavlink_shell.py` invocations wedge the FC's MAVLink instance.** Observed 2026-08-16
late: the FIRST `ls /fs/microsd` returned a real listing; every subsequent call echoed the command
and returned NOTHING. Shortly after, the operator reported **"I lost mavlink on ground station"**.

Confirmed by enumerating `tcp:127.0.0.1:5760`: only `(255,190) HEARTBEAT` (the GCS) and
`(3,68) RADIO_STATUS` (the radio) were present — **zero traffic from the autopilot at 1:1** — while
**DDS stayed perfectly healthy** (`/fmu/out/vehicle_status_v1` live, timestamp advancing).

🔑 **The FC was ALIVE the whole time. Only its MAVLink instance was dead.** Do not read "GCS lost
MAVLink" as "FC crashed".

🔑 **It was NOT a hardfault** — after recovery `ls /fs/microsd` showed no `fault_*.log`. Per
`docs/fc_hardfault_analysis.md` §7.3 a hardfault ALWAYS commits a log; this committed none. This is
the same "different failure" class as the 14:57/15:05 restarts already noted in that doc.

**Why:** PX4 has very few MAVLink/FTP sessions and does not free them when the client exits — the
hardfault doc already warned of this for FTP. Every failed/hung `mavlink_shell.py` leaks one until
the instance stops serving.

**How to apply:**
- ⛔ **Budget ONE `mavlink_shell.py` session per FC boot.** If a call returns an empty result, STOP —
  do not retry. Retrying is what exhausts it. (I burned ~6 and killed the operator's GS link.)
- ✅ **Prefer DDS for anything DDS can do** — see [[use_dds_not_mavlink]]. Reboot, params, mode set
  all work over DDS and cost no MAVLink session.
- ✅ **Recovery = reboot the FC over DDS** (`VehicleCommand` /
  `VEHICLE_CMD_PREFLIGHT_REBOOT_SHUTDOWN`, `param1=1.0`, target 1:1, `from_external=True`, BEST_EFFORT
  + TRANSIENT_LOCAL QoS). A MAVLink reboot CANNOT work here — the channel needed to deliver it is the
  dead one. Verified 2026-08-16: DDS dropped 2.7 s, returned 10.2 s, MAVLink came back complete.
- ✅ **Prove the reboot happened** by the DDS drop/return gap, NOT by `time_boot_ms` — PX4 reports
  absolute epoch µs here, so that field does not reset. → [[verify_after_editing]]
- ⚠️ **Check CH10 BEFORE rebooting the FC**: the reboot resumes `/fmu/out/input_rc`, and a switch off
  its down detent latches a companion reboot/shutdown. 1011 = down = safe.
  → [[rc_ch10_reboots_companion]]
