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
