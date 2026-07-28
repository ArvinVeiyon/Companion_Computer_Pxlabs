---
name: wfb-ng-config
description: "Full WFB-NG config detail (channel, FEC streams, endpoints, multi-adapter fwmark/tc)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
---

config: /etc/wifibroadcast.cfg | ch: 161 (5GHz) | region: BO | txpower: 3000 (30dBm rtl8812eu)
BW: 20MHz | MCS: 1 | STBC: 1 | LDPC: 1 | short_gi: off | CRITICAL: default_route=False both sides
drone: drone-wfb@10.5.5.87/24 | relay/GS: gs-wfb@10.5.5.77/24
streams: video TX 0x00 FEC 8/12 | mavlink RX 0x10/TX 0x90 FEC 1/3 | tunnel RX 0xa0/TX 0x20 FEC 2/4
GS endpoints: video→10.5.6.50:5600 | mavlink→10.5.6.50:14550 | keys: /etc/drone.key /etc/gs.key
stats API: drone 8002/8102 | GS 8003/8103
MULTI-ADAPTER: drone video service_type=udp_proxy (was udp_direct_tx) — enables TX across both wlx NICs via fwmark+tc (fwmark: video=20, mavlink=10, tunnel=30)
mavlink_sys_id=3 | both NIC in WFB_NICS (syntax fixed 2026-05-10)

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
