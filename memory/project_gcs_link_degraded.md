---
name: project-gcs-link-degraded
description: "2026-07-31: downlink HALF RESOLVED (delivers ~100%, was a misdiagnosis); uplink still lossy at 13.6% — root cause = drone NIC-A ant0 ~20 dB deaf"
metadata: 
  node_type: memory
  type: project
  originSessionId: e3048451-855a-4c5a-a615-d3cc75dac98f
  modified: 2026-07-31T16:35:45.284Z
---

# GCS MAVLink link degraded — DOWNLINK CLOSED, UPLINK OPEN (re-measured 2026-07-31)

## ⚡ 2026-07-31 UPDATE — read this before any of the 07-20 material below
20 min simultaneous both-ends measurement **under full video load** (the condition every earlier
test lacked). Full numbers + method: [[wfb-ng-config]].

- ✅ **"Downlink delivers only ~15%" is DEAD — it delivers ~100%.** video 0.01% loss,
  mavlink 0.14%, tunnel 0.16%. The 07-20 figure below compared **MAVLink message rates at two TCP
  endpoints**, which is not a radio measurement — mavlink-router endpoint behaviour and PX4 stream
  config sit in that path. **The radio was never dropping that traffic.** Do not re-derive link
  health from `tcp:5760` message counts again; use the WFB JSON API on 8102/8103.
- ✅ **GS `wfb-server` EAGAIN crash loop — NOT HAPPENING.** PID 696 stable across the whole run,
  `NRestarts=0`, 4 video blocks lost of 341 057. Old todo #3 (raise `rx_ring_size`) is closed.
- ✅ **GS TX power — already maxed at 30 dBm** (`wifi_txpower=3000`, regdom BO allows 30). Old
  todo #4 is closed; there was never any power to add.
- ✅ **Hardcoded peer `10.5.6.50` is CORRECT** — the QGC laptop on the relay's Wi-Fi Direct
  hotspot (`p2p-wlan0-0`, SSID `vind_rely`, 10.5.6.101/24). Ping fails only due to Windows firewall.
- 🔴 **STILL OPEN, and now localised: uplink (GS→drone) loses 13.57% of MAVLink payload**
  (1710 sent → 1478 delivered) and 5.46% of tunnel. **Continuous, not bursty** — 104 of 116
  intervals affected. ~100× worse than the reverse direction.
- 🔴 **ROOT CAUSE: drone NIC-A ant0 sits ~20 dB below its partner** (−48.5 vs −28.3 dBm, steady
  over 224 samples). The GS reads both its own antennas identical ⇒ the defect is on the **drone's
  receive side**, exactly where the loss is. **Fix the antenna, then re-measure.**
- ⚠️ **Not yet ruled out** (do after the antenna): the relay transmits to the laptop at **31 dBm on
  ch149** from the same chassis whose WFB card receives on ch161 — possible co-located desense.
- ⚠️ **Still un-gathered:** `journalctl -u wifibroadcast@gs` history. `vind-admin` is in `sudo` but
  sudo needs a password, so journald hides the unit. Needs the password or a manual run.

---

# Original record — measured 2026-07-20 (downlink half now known to be a misdiagnosis)

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
