---
name: wfb-ng-config
description: "Full WFB-NG config detail (channel, FEC streams, endpoints, multi-adapter fwmark/tc)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
  modified: 2026-07-31T19:13:41.420Z
---

config: /etc/wifibroadcast.cfg | ch: 161 (5GHz) | region: BO | txpower: 3000 (30dBm rtl8812eu)
BW: 20MHz | MCS: 1 | STBC: 1 | LDPC: 1 | short_gi: off | CRITICAL: default_route=False both sides
drone: drone-wfb@10.5.5.87/24 | relay/GS: gs-wfb@10.5.5.77/24
streams: video TX 0x00 FEC 8/12 | mavlink RX 0x10/TX 0x90 FEC 1/3 | tunnel RX 0xa0/TX 0x20 FEC 2/4
GS endpoints: video→10.5.6.50:5600 | mavlink→10.5.6.50:14550 | keys: /etc/drone.key /etc/gs.key
stats API: drone 8002/8102 | GS 8003/8103
MULTI-ADAPTER: drone video service_type=udp_proxy (was udp_direct_tx) — enables TX across both wlx NICs via fwmark+tc (fwmark: video=20, mavlink=10, tunnel=30)
mavlink_sys_id=3 | both NIC in WFB_NICS (syntax fixed 2026-05-10)

## 2026-07-30 — first real link measurement (JSON API on 8102, 10 s sample)
**Query it directly, don't use the `wfb-cli` TUI:** TCP-connect `127.0.0.1:8102`, read newline-
delimited JSON. Records are `type: tx|rx`; counters are `[per_second, cumulative]` pairs.

**The radio is HEALTHY — when video breaks, WFB is sitting on an empty input queue.**
- TX over 117,570 video packets: **`dropped=0, truncated=0, fec_timeouts=0`**
- TX latency 6-35 µs avg, 361 µs worst | RF temps 32-39 °C | `throttled=0x0`
- Load: ~367 pkt/s ≈ **3.9 Mbit/s injected** vs a 13 Mbit/s MCS1 PHY ≈ **34% airtime**
- Video 2.13 Mbit/s in → 3.2 Mbit/s injected (k=8/n=12, 1.5×)

### 🔴 RX antenna imbalance — SUPERSEDED by the 07-31 run below (only NIC-A is bad)
07-30 first look (NIC-B figure turned out to be a short-sample artifact):

| NIC-A ant1 | −28 dB | NIC-B ant257 | −33 dB |
|---|---|---|---|
| **NIC-A ant0** | **−46 dB** | **NIC-B ant256** | **−42 dB** |

### ❌ "Uplink BURST loss / interference / starved GS transmitter" — WRONG, deleted 08-01
The 07-30 reading (109 lost / 4884, only 27 FEC-recovered, at −28 dBm / 29 dB SNR) was real, but the
*interpretation* was not. The 07-31 both-ends run shows the loss is **continuous, not bursty**
(104/116 intervals affected) and is simply the drone's own ~20 dB-deaf **NIC-A ant0**. It is not
interference and not a GS transmitter problem. Correct account below.

### MAVLink airtime cost (a fact, NOT a to-do)
~175 kbit/s of telemetry → **~525 kbit/s injected** (3× FEC) at 46-49 pkt/s ≈ 13% of the airtime
budget. ❌ **The "trim PX4 stream rates" action was DELETED 08-01** — downlink already delivers
99.86-99.99%, so it fixes nothing; it buys airtime only, cannot touch the uplink loss (uplink is
~1.4 pkt/s), and cannot help CPU (mavlink-router isn't in the top 8 processes).

### MTU margin is thin but currently fine
`radio_mtu = 1445`; ffmpeg RTP averages 1354 B and `truncated=0` over 117k packets. But ffmpeg's
RTP default `pkt_size` is 1472 (> 1445) with no guaranteed margin — pin `-pkt_size 1400`.

### ✅ GS peer `10.5.6.50` — RESOLVED 2026-07-31, it is CORRECT. Stop suspecting it.
`gs_video peer = connect://10.5.6.50:5600`, `gs_mavlink = connect://127.0.0.1:14560`.
The relay runs a **Wi-Fi Direct P2P-GO**: iface `p2p-wlan0-0`, SSID **`vind_rely`**, **ch149 /
5745 MHz, 31 dBm**, relay itself at **10.5.6.101/24**. `10.5.6.50` is the **QGC laptop** on that
hotspot — ARP `REACHABLE`, lladdr `d8:80:83:5e:d5:57`. **ICMP fails (Windows firewall) — that is
NOT evidence of a break; do not re-open this on a failed ping.**
mavlink path: wfb → `127.0.0.1:14560` → mavlink-router `[UdpEndpoint WFB-input]` → `[UdpEndpoint
QGC] 10.5.6.50:14550`. Also `[UdpEndpoint tracker] 127.0.0.1:14551`.

## 2026-07-31 — 20 min SIMULTANEOUS both-ends run UNDER FULL VIDEO LOAD (the definitive one)
Method: `wfb_sample.py` against 8102 (drone) and 8103 (GS) at once, 10 s samples, 117/118 samples,
19.8 min, See3CAM streaming 1280x720 the whole time. **This is the load condition every earlier
measurement lacked.** Compare payload **`tx.incoming` → `rx.out`**, NOT the `rx.all` block counter —
`all` double-counts because the drone hears each packet on up to 4 antennas.

### THE LINK IS ASYMMETRIC. Downlink is perfect; uplink is the fault.
| direction | stream | sent | delivered | loss |
|---|---|---|---|---|
| drone→GS | **video** | 234 362 | 234 331 | **0.01%** |
| drone→GS | mavlink | 18 434 | 18 408 | 0.14% |
| drone→GS | tunnel | 10 896 | 10 879 | 0.16% |
| **GS→drone** | **mavlink** | 1 710 | 1 478 | **13.57%** |
| **GS→drone** | tunnel | 11 757 | 11 115 | **5.46%** |

~100× worse toward the drone. **Continuous, not bursty**: 104/116 intervals lost mavlink,
115/116 lost tunnel. Drone TX side `dropped=0 truncated=0 fec_timeouts=0` throughout.

### ✅ GS socket-overflow / EAGAIN theory (old todos #3, #4) — KILLED
Under 3.2 Mbit/s video + telemetry for 20 min the relay lost **4 video blocks of 341 057**
(0.001%), `wfb-server` held **PID 696** across all 33 health samples, **`NRestarts=0`**, zero
EAGAIN. The "downlink delivers 15%" symptom **does not reproduce**. Do not raise `rx_ring_size`.

### ✅ GS TX power (old todo #4) — KILLED, it is already MAXED
`wifi_txpower=3000`; `iw dev wlx00c0cab6db3b info` reports **30.00 dBm**; regdom **BO** permits 30
dBm across 5735-5835. **There is nothing to turn up.**

### 🔴🔴 ROOT CAUSE — drone NIC-A ant0 is ~20 dB deaf. THE top WFB action item.
224 samples, steady all 20 min (so **not a fade**), and the GS reads **both** its antennas
identical — so the defect is **entirely on the drone, on the RX side**, which is exactly the
direction losing packets:

| chain | avg rssi | note |
|---|---|---|
| NIC-A **ant0** | **−48.5 dBm** (min −55) | 🔴 **20.2 dB down — the fault** |
| NIC-A ant1 | −28.3 dBm | healthy |
| NIC-B ant256 | −35.0 dBm | 3.0 dB gap — acceptable |
| NIC-B ant257 | −32.0 dBm | healthy |

**⚠️ Corrects the 07-30 record: NIC-B is NOT 9 dB out, it is 3 dB. Only ONE chain is broken.**
Fix = reseat the u.FL on NIC-A ant0, check pigtail + antenna. Re-measure via 8102 straight after.

## Benign kernel WARN on every `wifibroadcast@` restart — DO NOT INVESTIGATE (verified 2026-07-28)
Each restart prints `WARNING ... rtw_mlme_ext.c:11582 rtw_mlmeext_disconnect` + a call trace from
`8812eu`, **exactly 2× (once per NIC)**, via `rtw_cmd_thread → disconnect_hdl`. Confirmed by
timestamp against 11 consecutive restarts: fires only at teardown, never during operation.

**Why it's harmless:** it is a `WARN`, not an Oops/BUG — the kernel prints and continues. The cards
run in **monitor mode** and never associate, so there is no association state to tear down and an
internal assertion in the out-of-tree Realtek DKMS fork trips. Both NICs print
`entered promiscuous mode` ~130 ms later = monitor mode restored, every single time.

**Verified healthy after:** `tx_errors=0` on both NICs, `operstate=up`, `type monitor`,
`wifibroadcast@drone` `NRestarts=0`, 3 `wfb_tx` instances, video flowing.
Taint flags `G W C OE` are expected here (OE = DKMS module, C = staging, W = a warn was issued).

**Do NOT patch the DKMS driver to silence it** — zero operational gain and it risks the link.
Its only real cost is distraction: it looks like a fault mid-investigation. → [[feedback_dkms_arch]]
