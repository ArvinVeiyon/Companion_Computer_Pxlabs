---
name: wfb-ng-config
description: "Full WFB-NG config detail (channel, FEC streams, endpoints, multi-adapter fwmark/tc)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
  modified: 2026-07-30T18:07:26.577Z
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

### 🔴 RX antenna imbalance — one weak chain on BOTH cards
Stable to ±1 dB across every sample, so **not a fade**:

| NIC-A ant1 | −28 dB | NIC-B ant257 | −33 dB |
|---|---|---|---|
| **NIC-A ant0** | **−46 dB** | **NIC-B ant256** | **−42 dB** |

18 dB ≈ 8× range. Half the diversity is contributing nothing. Check u.FL seating / pigtail /
antenna type on the weak chain of each card. **Not yet investigated.**

### 🔴 Uplink burst loss at point-blank range — the `project_gcs_link_degraded` mechanism
At −28 dBm and 29 dB SNR on a bench link:
- `mavlink rx`: **109 lost / 4884**, FEC recovered only **27** → 82 blocks lost outright
- `tunnel rx`: 304 lost / 18064, FEC recovered 277 → 27 hard

MAVLink runs **k=1/n=3 — three full copies of every block**. Losing all three at −28 dBm means
**burst loss = interference or a starved GS transmitter, NOT link budget.** ⇒ **Raising GS TX power
will not fix it** (relevant to todo #4).

### MAVLink is expensive
~175 kbit/s of telemetry → **~525 kbit/s injected** (3× FEC) at 46-49 pkt/s ≈ 13% of the airtime
budget. Trimming PX4 stream rates is the cheapest headroom available.

### MTU margin is thin but currently fine
`radio_mtu = 1445`; ffmpeg RTP averages 1354 B and `truncated=0` over 117k packets. But ffmpeg's
RTP default `pkt_size` is 1472 (> 1445) with no guaranteed margin — pin `-pkt_size 1400`.

### ⚠️ GS peer is a hardcoded IP
`gs_video peer = connect://10.5.6.50:5600`, `gs_mavlink = connect://10.5.6.50:14550` — a fixed
address on a subnet unrelated to the 10.5.5.0/24 tunnel. **If the QGC host lands anywhere else the
symptom is "no video, WFB broken" while the radio link is flawless.** Check this first.

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
