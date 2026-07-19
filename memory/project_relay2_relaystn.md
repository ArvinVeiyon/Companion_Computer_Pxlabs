---
name: project_relay2_relaystn
description: "Second WFB relay RELAY-STN (RPi4) built 2026-07-12, sibling of vind-rly"
metadata: 
  node_type: memory
  type: project
  originSessionId: b345fe8c-a652-4392-a588-178f764af9e8
---

A **second WFB-NG ground-station relay** was provisioned 2026-07-12: hostname
`RELAY-STN`, Raspberry Pi 4, Ubuntu 24.04.4 (kernel 6.8.0-1060-raspi), mgmt IP
`192.168.1.132`, user `vind-admin`. It is a drop-in sibling of the production relay
`vind-rly` (see [[reference_wfb_rlyctl.md]], [[reference_wfb_ng.md]]).

Built from a single idempotent installer `relay_bootstrap.sh` (kept on the companion
at `~/codex-work/relay/` for git push, and on the relay at `~/relay_bootstrap.sh`).
Full on-box reference doc: `~/RELAY_STATION_SETUP.md` (also in `~/codex-work/relay/`).

**Cross-platform (Pi4+Pi5), relay-only:** relays run on both boards — vind-rly=Pi5,
RELAY-STN=Pi4 — so the ONE installer auto-detects the board via /proc/device-tree/model
(sets PI_GEN 4/5/3/0), records it to /etc/vind-relay-platform, and applies board-specific
USB power for the RTL8812AU: Pi5 appends usb_max_current_enable=1 to config.txt (idempotent,
backup, needs 5V/5A PSU, SET_USB_POWER=0 to skip); Pi4 makes no boot change (use powered
hub). Everything else (DKMS driver, wfb-ng/mavlink-router builds, configs) is board-agnostic.
Detection verified on real Pi4 + Pi5 boards. NOTE: the drone companion is a separate Pi5 and
is NOT a relay — out of scope for this script.

Installed: wfb-ng `25.2.25` (built from svpcom tag wfb-ng-25.01 → .deb), mavlink-router
(pin 51983a4), RTL8812AU DKMS driver from **aircrack-ng** (not svpcom — equivalent for
monitor+injection), control tools wfb-rlyctl/wfb-cfg-apply, Claude Code CLI 2.1.207.
Services `wifibroadcast@gs`, `mavlink.router`, `ssh-tunnel-to-companion` enabled for boot.

**Shares keys/channel/tunnel-IP with vind-rly**: `/etc/gs.key`+`/etc/drone.key` copied
from the live drone (do NOT regenerate — breaks pairing); channel 161, tunnel IP
10.5.5.77, drone 10.5.5.87, GCS 10.5.6.50. Don't run both relays on ch161 at once.

**Build fix (reusable):** wfb-ng `make deb` failed under `sudo -u -H make -C <dir>` because
sudo resets PWD and wfb-ng's Makefile uses `ENV ?= $(PWD)/env` → empty PWD made it `/env`
(virtualenv "destination . is not write-able at /"). Fix: `bash -c "cd <src> && make deb"`.

**Networking (configured 2026-07-12, mirrors vind-rly/Pi5):**
- Internet uplink = USB adapter `wlx90de80d824d6` (rtw_8821cu / RTL8821CU) on SSID `Nilan`,
  DHCP `192.168.1.221`, holds default route (netplan `/etc/netplan/60-relay-uplink.yaml`).
  This is the mgmt path (reach relay at .221, NOT .132 anymore).
- Onboard `wlan0` = P2P GO for the GS: `p2p-wlan0-0` @ `10.5.6.101/24`, SSID/device_name
  `RELAY-STN01`. The P2P password lives in the network block of
  `/etc/wpa_supplicant/wpa_supplicant.conf` (like the Pi5): `psk="Nilan@2409"`, plus
  `bssid=<own p2p MAC>`, mode=3, disabled=2. WPS PIN `1987` is also enabled via rely_p2p.sh.
  `~/rely_p2p.sh` = Pi5 verbatim minimal script; `@reboot rely_p2p.sh` in root crontab.
  cloud-init net regen disabled. (NOTE: the Pi5's wpa_supplicant.conf DOES carry a static
  psk in its network block — do not assume WPS-PIN-only.)
- Forwarding: `ip_forward=1` only (persist `/etc/sysctl.d/99-relay-forward.conf`); NO iptables
  NAT/FORWARD rules (matches Pi5 = empty). GS does not get internet through the relay.
- Naming scheme: this Pi4 P2P = RELAY-STN01; user will rename Pi5 vind_rely → RELAY-STN00.
- Cutovers were done detached with a 5-min dead-man auto-revert (safe over the wlan0 link).

P2P channel: GO auto-selected 5GHz **ch36 (5180)**, visible as RELAY-STN01, UP/COMPLETED.
Do NOT pin `freq=5745` in rely_p2p.sh — it landed on DFS ch140 and stalled (SCANNING/DOWN);
reverted to plain `p2p_group_add persistent=0`. (Pi5 P2P happens to run ch149.)

**No DHCP by design (GS uses static IP):** WFB video `[gs_video] peer=connect://10.5.6.50:5600`
and mavlink-router `[UdpEndpoint QGC] Address=10.5.6.50:14550` are UNICAST to the fixed GS IP
`10.5.6.50` — required for LOW-LATENCY video (broadcast is lossy on Wi-Fi). So the Windows GCS
must be set **static 10.5.6.50/24** to receive video+telemetry (Pi5 has no DHCP for this reason).
mavlink-router also has a TCP server on `:5760` (Mode=server) — DHCP-friendly for MAVLink only.
Alt if plug-and-play wanted later: dnsmasq on p2p-wlan0-0 with reservation GS-MAC->10.5.6.50
(same latency; assignment is one-time, not in the data path).

PENDING TEST (user testing 2026-07-13): join RELAY-STN01 (passphrase Nilan@2409 on Win/phone;
WPS PIN 1987 for Direct clients), set GCS static 10.5.6.50, verify video :5600 + MAVLink :14550/tcp 5760.

STATE AT SHUTDOWN (2026-07-12 eve): relay cleanly powered OFF at end of session; OFF until
physically powered on (Pi has no remote wake). On next boot everything auto-recovers: uplink
netplan -> mgmt at `ssh vind-admin@192.168.1.221` (pass 1987), P2P RELAY-STN01 via @reboot
rely_p2p.sh, services enabled. Nothing left half-done; safe to resume from the pending-test step.

Pending (hardware/other-side): plug RTL8812AU adapter + `wfb-rlyctl set-nics`; authorize
`~vind-admin/.ssh/id_rsa.pub` on drone for the autossh tunnel; cluster staged only
(set eth0 `10.5.7.100/24` + WFB_NICS + cluster node wlan when RTL8812AU + CPE610 present).

**DEBUG SESSION 2026-07-14 — WFB card kills uplink = USB POWER/OVER-CURRENT (CONFIRMED by user, continue tomorrow):**
Symptom: plugging the WFB adapter (user calls it the "EU card", i.e. rtl88x2eu type — NOTE
possible discrepancy vs build note "RTL8812AU/aircrack-ng"; verify actual chip next session)
into the Pi4 makes BOTH the WFB card AND the local-network uplink fail together.
- Root cause: **Pi4 ~1.2 A AGGREGATE USB budget across the whole board (not per-port).** Uplink
  RTL8821CU (`wlx90de80d824d6`, `0bda:c811`, rtw_8821cu) sits on an EXTERNAL VIA Labs hub
  (`2109:3431`, bus-powered — descriptor lies "Self Powered" but NO 5V brick). WFB/EU card plugs
  DIRECT into a Pi4 port. Both draw from the same budget; EU card's TX spike tips it over → Pi4
  USB power controller cuts the rail → uplink on the hub dies too. Direct-vs-hub does NOT isolate.
- Evidence: `vcgencmd get_throttled=0x0` (SoC 5V rail clean — Pi4 USB over-current does NOT show
  as SoC under-voltage, so 0x0 does NOT clear power). Uplink WEDGES when EU card present and does
  NOT auto-recover after unplug — needs uplink re-plug or reboot. Reproduced twice this session.
- FIX (matches this repo's own build note "Pi4 makes no boot change → use powered hub"): put the
  WFB/EU card (ideally BOTH adapters) on a **self-powered USB hub with its own 5V brick**, off the
  Pi4 internal budget. TODO next session: get powered hub, move adapters, then `wfb-rlyctl set-nics`.
- We ran a detached capture to `/tmp/wfbcap.log` (dmesg -wT + lsusb every 2s) but never read it —
  uplink stayed wedged; `/tmp` is wiped on reboot so that capture is likely gone. Re-capture if
  exact trip line wanted, but cause is already confirmed.

**Debug ACCESS PATH to RELAY-STN (Pi4) from the drone companion (Pi5) — reusable:**
- Companion wlan0 uplink is on the SAME `Nilan` LAN: companion `192.168.1.241/24`, relay uplink
  `192.168.1.221/24`. Reach relay: `sshpass -p 1987 ssh vind-admin@192.168.1.221` (sshpass IS
  installed on companion). Key auth is NOT set up for RELAY-STN (only vind-rly trusts the companion
  key) — consider copying companion pubkey to RELAY-STN to drop the password. Only works while the
  uplink (RTL8821CU) is UP — i.e. WFB/EU card unplugged.
- WFB-link IP `10.5.5.77` from the companion = **vind-rly (Pi5 production relay), NOT this Pi4**
  (both relays share tunnel IP 10.5.5.77; vind-rly was the active ch161 GS). No WFB-path to the Pi4.
- `sudo` on RELAY-STN needs password (1987) via `echo 1987 | sudo -S ...`; only wfb-rlyctl is
  passwordless (see [[reference_wfb_rlyctl.md]]).
