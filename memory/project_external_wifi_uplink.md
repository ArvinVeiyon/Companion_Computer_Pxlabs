---
name: project-external-wifi-uplink
description: External USB WiFi adapter added as primary onboard uplink (onboard wlan0 blocked by metal enclosure lid)
metadata: 
  node_type: memory
  type: project
  originSessionId: 711b1827-1cb0-4b8c-bdac-d95d7be22cd4
  modified: 2026-07-25T04:29:40.429Z
---

2026-07-25: Closing the enclosure (metal top plate → Faraday effect) killed/weakened the RPi5 onboard WiFi (`wlan0`, brcmfmac BCM4345). Added an **external USB adapter** as the primary management uplink.

- Adapter: **Realtek RTL8821CU** `0bda:c811`, driver `rtw_8821cu`, fw 24.11.0. Enumerates in USB CD/storage mode (`1a2b`) then mode-switches to NIC — normal.
- Interface: **`wlx90de80d824d6`** (MAC 90:de:80:d8:24:d6; MAC-based name = boot-stable).
- Config: `/etc/netplan/50-cloud-init.yaml` (renderer networkd; cloud-init net config is DISABLED via `/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg` so edits persist). `wifis:` entry on SSID **Nilan** (same precomputed PSK as wlan0). **STATIC 192.168.1.240/24** (`dhcp4: false`), default route via 192.168.1.1 **metric 50** (beats onboard wlan0's 600), nameservers [192.168.1.1, 8.8.8.8]. Backup at `50-cloud-init.yaml.bak.*`.
- Verified: assoc Nilan -61dBm, **192.168.1.240**, internet ~10ms, default route via the new adapter.
- Chose static **.240** (probed .240/.241/.245/.250 all free) to AVOID the earlier DHCP-assigned **192.168.1.221**, which collides with [[project_relay2_relaystn]] RELAY-STN RPi4 mgmt. Resolved 2026-07-25.

**Onboard wlan0 DISABLED 2026-07-25 (finalizes TODO #2):** wlan0 = phy0 = brcmfmac (USB adapters are phy1/2 rtl88x2eu WFB, phy3 rtw_8821cu = this uplink). (1) removed wlan0 stanza from netplan (commented) + `ip link set wlan0 down` → out of routing immediately, only .240 default route remains. (2) added `dtoverlay=disable-wifi` to `/boot/firmware/config.txt` (beside existing `disable-bt`; backup `.bak.*`) → firmware-level removal of onboard radio, kills 5GHz WFB ch161 interference. **Rebooted 2026-07-25 to finalize** — after reboot wlan0 no longer exists; uplink = wlx90de80d824d6 @ 192.168.1.240. rfkill NOT installed on this box. Supersedes [[feedback_wlan0_persistent_name]] wifi0-rename plan (radio now gone entirely).
- Note: onboard wlan0 still weakly associated (192.168.1.208, metric 600) during apply — marginal, not fully dead, but external wins routing. Relates to TODO #2 (disable onboard wifi0/ex-wlan0, 5GHz WFB interference).
