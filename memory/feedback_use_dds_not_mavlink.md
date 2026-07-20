---
name: feedback-use-dds-not-mavlink
description: "RULE from user 2026-07-20: interact with the FC over DDS/ROS2 topics, not MAVLink probing — MAVLink traffic disturbs the link"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e3048451-855a-4c5a-a615-d3cc75dac98f
  modified: 2026-07-20T15:39:14.669Z
---

RULE (user, 2026-07-20): For autonav/FC work, use **DDS (uXRCE-DDS / ROS2 topics)**, not MAVLink injection into mavlink-router. Verbatim: "instead of using mavlink try to use dds topic because it will distrub the the mavlik connection".

**Why:** Injecting MAVLink (pymavlink clients on tcp:5760 / relay:5760, REQUEST_MESSAGE bursts) loads the FC and the shared telemetry path. Evidenced same session: `autonav_mode` aborted with the px4_ros2 4s watchdog ("Timeout, no request received from FMU") *while* MAVLink probing was running, and ran clean for 25s+ and through a full mode cycle once probing stopped. The earlier 2026-07-20 "one-off" abort likely had the same cause.

**How to apply:**
- Mode changes: publish `px4_msgs/VehicleCommand` VEHICLE_CMD_DO_SET_MODE on `/fmu/in/vehicle_command` (param1=1, param2=main, param3=sub), read back `/fmu/out/vehicle_status_v1.nav_state`. Working script: `~/ros2_ws/tools/dds_setmode.py` (verified 4→23 AutoNav→4 Hold, 2026-07-20). QoS: BEST_EFFORT + TRANSIENT_LOCAL, depth 5.
- FC state/telemetry: `/fmu/out/*` topics, never a pymavlink client.
- MAVLink probing only when the question is specifically about the MAVLink/GCS link itself, and never while `autonav_mode` (or any px4_ros2 mode) is registered.

Related: [[project-rover-autonav]], [[project-gcs-link-degraded]].
