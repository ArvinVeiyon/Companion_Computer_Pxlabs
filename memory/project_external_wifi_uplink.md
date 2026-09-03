---
name: project-external-wifi-uplink
description: External USB WiFi adapter added as primary onboard uplink (onboard wlan0 blocked by metal enclosure lid)
metadata: 
  node_type: memory
  type: project
  originSessionId: 711b1827-1cb0-4b8c-bdac-d95d7be22cd4
  modified: 2026-09-03T18:16:16.435Z
---

2026-07-25: Closing the enclosure (metal top plate → Faraday effect) killed/weakened the RPi5 onboard WiFi (`wlan0`, brcmfmac BCM4345). Added an **external USB adapter** as the primary management uplink.

- Adapter: **Realtek RTL8821CU** `0bda:c811`, driver `rtw_8821cu`, fw 24.11.0. Enumerates in USB CD/storage mode (`1a2b`) then mode-switches to NIC — normal.
- Interface: **`wlx90de80d824d6`** (MAC 90:de:80:d8:24:d6; MAC-based name = boot-stable).
- Config: `/etc/netplan/50-cloud-init.yaml` (renderer networkd; cloud-init net config is DISABLED via `/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg` so edits persist). `wifis:` entry on SSID **Nilan** (same precomputed PSK as wlan0). **STATIC 192.168.1.240/24** (`dhcp4: false`), default route via 192.168.1.1 **metric 50** (beats onboard wlan0's 600), nameservers [192.168.1.1, 8.8.8.8]. Backup at `50-cloud-init.yaml.bak.*`.
- Verified: assoc Nilan -61dBm, **192.168.1.240**, internet ~10ms, default route via the new adapter.
- Chose static **.240** (probed .240/.241/.245/.250 all free) to AVOID the earlier DHCP-assigned **192.168.1.221**, which collides with [[project_relay2_relaystn]] RELAY-STN RPi4 mgmt. Resolved 2026-07-25.

## REVERSED 2026-07-25 (later same day) — external out, wlan0 back
To isolate the 5 V rail sag in [[project-wfb-undervoltage-dead-nic]], user **physically disconnected the RTL8821CU** and asked for onboard wlan0 back. Staged (NOT yet rebooted at time of writing):
- `/boot/firmware/config.txt` line 65: `dtoverlay=disable-wifi` **commented out** (backup `config.txt.bak.20260725-wlan0restore`).
- netplan: `wlan0` stanza **uncommented** — `dhcp4: true`, `optional: true`, SSID Nilan (backup `50-cloud-init.yaml.bak.20260725-wlan0restore`). `netplan generate` validates clean.
- **The `wlx90de80d824d6` stanza was deliberately LEFT IN PLACE** — plugging the adapter back in auto-restores the .240/metric-50 uplink with no edits. That is the fallback.
- **wlan0 is DHCP now, not static** — it will NOT be 192.168.1.240. Find its address from the router lease table or via the WFB tunnel.
- Reboot is REQUIRED (dtoverlay). Fallback path if wlan0 won't associate through the metal lid: WFB → relay:2222 → 10.5.5.87:22.
- TODO #2 is therefore **RE-OPENED** — the onboard radio is back and will again contend with WFB ch161.

### ⚠️ CORRECTION 2026-07-26 — `dtoverlay=disable-wifi` NEVER TOOK EFFECT
Verified after the 2026-07-26 07:57 boot (config.txt last edited 2026-07-25 22:42, so the overlay
WAS in the booted config): `wlan0` **still exists**, `brcmfmac`/`brcmfmac_wcc` still loaded and bound
via sdio. The radio is NOT gone — it is only DOWN because netplan no longer configures it.
**Cause:** the line is `dtoverlay=disable-wifi  # onboard brcmfmac OFF 2026-07-25: …` — `config.txt`
has **no inline-comment support**, so everything after the value is parsed as part of the overlay
name and the overlay is silently dropped. **Control case proving it:** `dtoverlay=disable-bt` on the *previous* line (no inline comment) DID
work — `/sys/class/bluetooth` empty, `btbcm` not loaded. Same file, adjacent lines, same boot.
**FIX APPLIED 2026-07-26**: comment moved to its own lines above the directive (backup
`/boot/firmware/config.txt.bak.20260726-inlinecomment`). **NOT yet rebooted — unverified.**
Next boot, confirm with `ip link show wlan0` (should not exist) + `lsmod | grep brcmfmac` (empty).
**TODO #2 stays open until that reboot check passes.** If the external RTL8821CU ever fails after
this takes effect there is no onboard-Wi-Fi fallback — recover via WFB → relay:2222 → 10.5.5.87:22,
or comment out the `dtoverlay=disable-wifi` line.

### 🔴 CORRECTION #2, 2026-07-30 — the 07-26 fix was RIGHT but the OVERLAY NAME IS WRONG FOR PI 5
Reboot verification finally happened (boot 2026-07-30 22:41:45). **It still did not work.**
- `brcmfmac` + `brcmfmac_wcc` **still loaded**, bound via **sdio**, radio live as **`wlan1`** on
  wiphy0, parked at **channel 34 / 5170 MHz**. Interface is DOWN (netplan doesn't configure it), so
  it is not beaconing — but the radio IS initialized.
- The 07-26 inline-comment fix was correct and is intact: the line sits in `[all]` at config.txt:69
  with its comments on their own lines above. **The directive itself is simply the wrong one.**
- **ROOT CAUSE: Pi 5 needs a different overlay.** Both files exist in `/boot/firmware/overlays/`:
  `disable-wifi.dtbo` **and `disable-wifi-pi5.dtbo`**. This board needs the **`-pi5`** variant.
- **FIX (not applied — needs a reboot to verify, again):** `dtoverlay=disable-wifi-pi5`.
  More robust alternative that cannot be silently ignored by the firmware: **blacklist `brcmfmac`**
  at the driver level. `rfkill` is NOT installed on this box.
- ⚠️ **This is the SECOND time this one line has silently no-op'd** (07-25 inline comment, 07-30
  wrong overlay name). **Do not mark TODO #2 done again without a post-reboot `lsmod | grep
  brcmfmac` returning empty.** An `ip link` check alone is not enough — the interface name changed
  from `wlan0` to `wlan1`, so a check keyed on `wlan0` would have falsely passed.
- **Related drift:** the `wifi0` udev rename rule from [[feedback_wlan0_persistent_name]] is **GONE**
  — nothing under `/etc/udev/rules.d/` or `/etc/systemd/network/` references `wifi0`. That is why
  the radio came up as `wlan1` (kernel default, USB WFB adapters took the wlx* names).

### (superseded, and see the correction above) Onboard wlan0 DISABLED 2026-07-25 (was: finalizes TODO #2): wlan0 = phy0 = brcmfmac (USB adapters are phy1/2 rtl88x2eu WFB, phy3 rtw_8821cu = this uplink). (1) removed wlan0 stanza from netplan (commented) + `ip link set wlan0 down` → out of routing immediately, only .240 default route remains. (2) added `dtoverlay=disable-wifi` to `/boot/firmware/config.txt` (beside existing `disable-bt`; backup `.bak.*`) → firmware-level removal of onboard radio, kills 5GHz WFB ch161 interference. **Rebooted 2026-07-25 to finalize** — after reboot wlan0 no longer exists; uplink = wlx90de80d824d6 @ 192.168.1.240. rfkill NOT installed on this box. Supersedes [[feedback_wlan0_persistent_name]] wifi0-rename plan (radio now gone entirely).
- Note: onboard wlan0 still weakly associated (192.168.1.208, metric 600) during apply — marginal, not fully dead, but external wins routing. Relates to TODO #2 (disable onboard wifi0/ex-wlan0, 5GHz WFB interference).

### ✅ 2026-09-03 — the "no fallback if the RTL8821CU fails" gap is CLOSED (wired)
The worry stated twice above — *if the external adapter ever fails there is no onboard-Wi-Fi
fallback, recover via WFB → relay:2222* — no longer describes the box. **`eth0` is now a third,
independent way in**, and it does not depend on any radio: plug a cable →
`ssh roz@10.10.10.10` (laptop side static `10.10.10.20/24`) or `ssh roz@Vind-Roz.local`
(avahi/mDNS; works with the laptop left on "automatic", which link-locals to 169.254.x on both ends).
- Config `/etc/netplan/60-eth0-recovery.yaml` + a `RequiredForOnline=no` drop-in under
  `/etc/systemd/network/10-netplan-eth0.network.d/` — netplan's `optional: true` did **not** emit
  that key on this version, so I added it by hand.
- **It cannot hijack the uplink:** DHCP route metric **300** vs the uplink's **50**.
- ⚠️ **Address exists only while carrier is present.** Empty `ip -br addr show eth0` with no cable
  in is CORRECT. Judge it by `networkctl status eth0` → `State: routable`.
- ⚠️ **CABLE-UNTESTED as of 09-03** — the address bind was proven by forcing
  `ConfigureWithoutCarrier=yes` temporarily, not by plugging anything in.
- 🔴 **NOT JUST A NAME CHANGE — THE ADAPTER ITSELF WAS SWAPPED.** This whole file is about an
  **RTL8821CU `0bda:c811` = `wlx90de80d824d6`**. Measured 09-03: **that device is not in `lsusb`
  at all.** The live uplink is a **TP-Link Archer T2U PLUS `2357:0120` (RTL8821AU)** on driver
  **`rtl88xxau_wfb`**, syspath `4-2`, as **`wlx8c86dd5beed9`** — carrying the same
  `.240`/metric-50 netplan stanza, which is why nothing looked broken.
  ⚠️ **So the "leave the `wlx90de80d824d6` stanza in place as the fallback" plan (line 23) is
  DEAD** — that stanza is commented out and its hardware is gone. **Find the physical RTL8821CU
  before planning around it.** → [[project_boxb_pcie_usb]], [[reference_this_machine]],
  setup_manual §E5b
