---
name: project-gcs-link-degraded
description: "OPEN 2026-07-20: GCS MAVLink link — downlink delivers only ~15% of offered telemetry, uplink commands 0/8 delivered; explains QGC 'Unknown mode'"
metadata: 
  node_type: memory
  type: project
  originSessionId: e3048451-855a-4c5a-a615-d3cc75dac98f
  modified: 2026-07-20T15:39:43.489Z
---

# GCS MAVLink link degraded — OPEN (measured 2026-07-20)

Discovered while chasing the QGC "Unknown mode" name issue for [[project-rover-autonav]]. Measured with pymavlink on both ends (do NOT repeat casually — see [[feedback-use-dds-not-mavlink]]).

## Measurements (2026-07-20, rover on bench, RC off, 1/4 VESCs powered)
- **Downlink thinned ~6x, uniformly across every message type.** Companion `tcp:127.0.0.1:5760` = 352 msg/s, 21.4 KiB/s (176 kbit/s). Relay `tcp:10.5.5.77:5760` = 53 msg/s, 3.2 KiB/s (26 kbit/s). Ratio ≈0.16 for HEARTBEAT (1.92→0.36 Hz), ATTITUDE (100→16.4 Hz), AVAILABLE_MODES_MONITOR/436 (0.52→0.08 Hz) alike → whole-packet loss / saturation, not selective filtering. Offered rate (~176 kbit/s: ATTITUDE 100Hz + HIGHRES_IMU 50Hz + ATTITUDE_QUATERNION 50Hz + ODOMETRY/LOCAL_POSITION 30Hz each) plausibly exceeds the wfb mavlink stream budget.
- **Uplink commands: 0 delivered.** 6x MAV_CMD_REQUEST_MESSAGE(148) and 6x (435) sent from relay TCP → 0 COMMAND_ACK, 0 replies. Sniffer on the companion router confirmed **0 of 8** relay-injected COMMAND_LONGs ever arrived at the drone. Same commands on companion-local TCP: 6/6 acks, 6/6 replies. So the break is in the GCS→FC path, not the FC.
- WFB tunnel itself is healthy bidirectionally (SSH companion→relay works fine); drone `wifibroadcast@drone` logs continuous `mavlink rx: N packets lost` + `tunnel rx: N packets lost`.
- Relay config: `gs_mavlink peer = connect://127.0.0.1:14560` → mavlink-router `[UdpEndpoint WFB-input] Mode=server :14560`; drone: `drone_mavlink peer = listen://0.0.0.0:14550` ← mavlink-router `[UdpEndpoint WFB-NG] Mode=normal 127.0.0.1:14550`. Config *looks* correct; the failing hop is not yet isolated (candidates: relay mavlink-router not forwarding to the learned wfb peer, wfb gs mavlink tx not injecting, or GS TX power — see existing TODO #4 "uplink severely worse than downlink").
- Relay journal for `wifibroadcast@gs` needs sudo/adm group to read (returned "No entries" as vind-admin) — next diagnostic step.

## Why it matters
Explains QGC "Unknown <number>" without any QGC source bug: QGC learns mode names by seeing AVAILABLE_MODES_MONITOR (436) then **requesting** AVAILABLE_MODES (435) one index at a time. With the uplink dead the request never lands, and `StandardModes` has **no retry** (on failure it just emits requestCompleted and waits for the monitor seq to change) → names never populate. Also means DO_SET_MODE/arm from QGC cannot work over the radio right now.

## Next steps
1. Isolate the failing uplink hop (relay-side wfb gs mavlink tx vs mavlink-router forwarding vs RF).
2. Reduce PX4 GCS stream rates (or use a lower-rate MAVLink instance/profile for the wfb link) so downlink fits the budget.
3. Re-test: 436 arrival rate at relay + a REQUEST_MESSAGE round trip end-to-end.

Related: [[project-rover-autonav]], [[feedback-use-dds-not-mavlink]], [[reference-wfb-ng]], [[project-relay-ntp-setup]].
