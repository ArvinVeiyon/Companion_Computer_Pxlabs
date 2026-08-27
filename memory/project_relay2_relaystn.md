---
name: project_relay2_relaystn
description: "Second WFB relay RELAY-STN (RPi4) built 2026-07-12, sibling of vind-rly"
metadata: 
  node_type: memory
  type: project
  originSessionId: b345fe8c-a652-4392-a588-178f764af9e8
  modified: 2026-07-26T08:28:55.442Z
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
- ⚠️ **STALE AS OF 2026-07-26 — THAT ADAPTER IS NOW ON THE DRONE COMPANION.** `wlx90de80d824d6`
  (MAC 90:de:80:d8:24:d6) is currently the companion's primary uplink at static `192.168.1.240/24`
  (see [[project_external_wifi_uplink]]). A MAC belongs to one physical adapter, so **RELAY-STN no
  longer has this NIC** — and its `.221` DHCP lease is exactly why the companion was deliberately
  moved off `.221` to `.240`. `192.168.1.221` does not answer ping from the companion.
  **Confirm what NIC RELAY-STN actually has before following the section below.** A warning block is
  also in `codex-work/relay/RELAY_STATION_SETUP.md`.
- Internet uplink (as built 2026-07-12) = USB adapter `wlx90de80d824d6` (rtw_8821cu / RTL8821CU) on
  SSID `Nilan`, DHCP `192.168.1.221`, holds default route (netplan
  `/etc/netplan/60-relay-uplink.yaml`). This was the mgmt path (reach relay at .221, NOT .132).
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

## 2026-08-23 — ⛔ PI ZERO 2 W IS NOT A VIABLE RELAY. REVERTED TO THE RPi5 SAME DAY.
- **Operator rebuilt the relay on a Raspberry Pi Zero 2 W, configured it, could log in — but QGC
  disconnected INTERMITTENTLY.** Reverted to the RPi5 within the hour. ⛔ **Don't retry this swap.**
- 🔑🔑 **THE BLOCKING REASON IS A HARDWARE LIMIT, NOT A CONFIG MISTAKE: the Pi Zero 2 W's onboard Wi-Fi
  (CYW43438) is 2.4 GHz ONLY.** The relay's QGC hotspot is a Wi-Fi Direct **P2P-GO on ch149 / 5745 MHz
  (5 GHz) @31 dBm** (`vind_rely`, relay 10.5.6.101/24, QGC laptop 10.5.6.50). **A Zero 2 W physically
  cannot host that.** ⚠️ It also has **ONE usable USB port**, which the rtl8812eu WFB adapter needs —
  so there is no port left for a 5 GHz hotspot NIC either. ⇒ **the design needs a dual-band host.**
- ⚠️ Secondary (unconfirmed, we reverted before proving it): 4×A53 @1 GHz / **512 MB** also has to run
  WFB FEC decode + `mavlink-router` + the hotspot + the SSH tunnel. The RPi5 had headroom; this does not.
- 📈 **MEASURED WHILE IT WAS UP (useful method, reuse it):** `ping -c 100` companion→relay gave
  **0% loss, p50 15.5 ms, p90 16.9 ms, but two ~900 ms stalls ~16 s apart.** 🔑 **ZERO LOSS + HUGE DELAY =
  packets QUEUED AND RELEASED = a CPU/scheduling stall on the relay, NOT an RF problem.** Loss would mean RF.
- ✅ **THE RADIO WAS PROVEN INNOCENT at the same time** (drone-side JSON API on 8102, per
  [[wfb-ng-config]] — query the socket, never the `wfb-cli` TUI): tunnel TX **dropped=0 truncated=0
  fec_timeouts=0**; tunnel RX over 27,141 pkts **dec_err=0 bad=0**, lost 18, fec_rec 107. ⇒ **matches the
  standing rule: when something breaks, WFB is sitting on an EMPTY input queue — SUSPECT THE SOURCE.**
- 🔑 **SSH host key changes on every relay rebuild.** Zero 2 W was
  `SHA256:LKKrmSX0vORTGbrJAUlz+NI4BWJGxiNdVjIaytAYIRM`. **Clear the old entry BEFORE swapping back or the
  next login dies on "HOST IDENTIFICATION HAS CHANGED":** `ssh-keygen -f ~/.ssh/known_hosts -R 10.5.5.77`.
  ⚠️ **`grep 10.5.5.77 ~/.ssh/known_hosts` returns 0 even when an entry EXISTS** (hashed known_hosts) —
  **use `ssh-keygen -F 10.5.5.77`.** ⚠️ A fresh relay build has **no authorized_keys** ⇒ publickey denied
  until `ssh-copy-id`; **the operator must run that himself — never take a password into the transcript.**
- ⚠️ **`ping 10.5.6.50` (QGC laptop) FAILS by design — Windows firewall.** NOT evidence of a break.

## 2026-08-23 — RELAY RESTORED FROM AN OLD SD CARD (the newer card was damaged). AUDIT + PARTIAL FIX.
- **Context:** operator fell back to an OLDER relay SD card after the current one was damaged. RPi5 `vind-rly`,
  Ubuntu 24.04.2, kernel `6.8.0-1018-raspi` (companion runs `-1048`).
- ✅ **REPO BROUGHT CURRENT: `~/codex-relay` 01aa9ab (2026-03-15) → `70ef6aa` (2026-07-12)**, 9 commits, via the
  **git-bundle method** (relay has NO internet): `git bundle create B master ^01aa9ab` on `~/codex-relay-mirror`
  → `scp` → `git pull --ff-only B master`. ⚠️ **The old card had NO git remote configured at all.**
  🔑 The relay's uncommitted `scripts/system_files_sync.sh` edit was **byte-identical** to the incoming commit —
  checked with a real diff before discarding it. **Check, don't assume, before dropping a local edit.**
- 🔑🔑 **`scripts/system_files_sync.sh` SYNCS SYSTEM → REPO, NOT REPO → SYSTEM**
  (`rsync --files-from=list / $repo/System_files`). ⇒ **updating the repo CANNOT touch `/etc`** — verified
  `/etc/wifibroadcast.cfg` mtime unchanged after the pull. **`System_files/` is a BACKUP of the box, not a
  deployment source.** ⛔ **So "make /etc match the repo" is NOT a version upgrade — it is replaying an old
  snapshot of a DIFFERENT deployment.**
- 🔴🔴 **DO NOT COPY `System_files/etc/wifibroadcast.cfg` OVER THE LIVE `/etc/wifibroadcast.cfg`.**
  **The ONLY delta is the `[cluster]` block (21 lines, 1 hunk — every radio-critical value is ALREADY
  IDENTICAL: channel, MCS, txpower, FEC, keys, endpoints).** The repo version enables a **2-node WFB cluster**:
  `nodes = {'127.0.0.1': wlx00c0cab6db3b, '10.5.7.102': CPE610 OpenWrt phy0-mon0}`, `server_address='10.5.7.100'`,
  api_port 8203 / stats_port 8303, ssh key `~/.ssh/wfb_cluster_ed25519`.
  **MEASURED PREREQUISITES ON THE CURRENT BOX: ssh key PRESENT ✓, but `10.5.7.100` IS NOT ON ANY INTERFACE ✗,
  `eth0` is DOWN ✗, `10.5.7.102` UNREACHABLE ✗.** ⇒ **applying it would point wfb-server at an address the relay
  does not hold and a node that is not attached — near-certain link loss on a link that is CURRENTLY WORKING.**
  ⏭ Only apply if the **CPE610 is physically attached and eth0 is up on 10.5.7.100**, and then only behind the
  **`wfb-cfg-apply` watchdog**.
- ✅ **BACKUP TAKEN BEFORE ANY CONFIG WORK: `~/wfb_cfg_backups/wifibroadcast.cfg.<stamp>` on the relay.**
- 🔴 **STILL BROKEN — `mavlink-router` is `inactive`/`disabled` ⇒ QGC GETS NO TELEMETRY.** Config
  `/etc/mavlink-router/main.conf` is CORRECT (WFB-input :14560 → QGC `10.5.6.50:14550`, tracker :14551, TCP 5760).
  **PROOF the data reaches the relay and dies there:** GS-side WFB stats (port 8103) showed mavlink RX
  **dec_ok 17430, dec_err 6, lost 1, bad 0**, `out` 5720 → `127.0.0.1:14560` with nothing consuming it.
  ⏭ **FIX = `sudo systemctl enable --now mavlink-router`.** 🔑 **`sudo NEEDS A PASSWORD on the relay` ⇒ I cannot
  do this myself; the operator must run it.**
- 🔴 **NTP still `ntp.ubuntu.com` (unreachable — no internet) ⇒ `System clock synchronized: no`.** Old card, so
  the [[relay-ntp-setup]] plan was never applied here. ⚠️ **220 pending apt updates, and no internet to fetch
  them — don't try.**
- ⚠️ **`wfb-cfg-apply` watchdog: now TRACKED in the repo (`System_files/usr/local/sbin/`) but NOT INSTALLED**
  to `/usr/local/sbin` — the repo pull does not deploy (see the system→repo direction above). Needs sudo.
- ✅ **Healthy and untouched:** WFB ch161/5805 MHz MCS1 BW20 STBC+LDPC `default_route=False`; hotspot `vind_rely`
  ch149 up at 10.5.6.101 with **the QGC laptop `10.5.6.50` ASSOCIATED and REACHABLE**; SSH tunnel :2222 listening.

### 2026-08-23 ~22:15 — MAVLINK IS UP (operator fixed it). ⚠️ BUT NOT UNDER SYSTEMD.
- ✅ **`mavlink-routerd` IS RUNNING: PID 750, PPID 1, `-c /etc/mavlink-router/main.conf`**, started ~21:21 IST
  (~54 min uptime) — i.e. AFTER the 21:06 audit that found it dead, so that audit was right at the time.
- ✅ **PATH VERIFIED END TO END:** WFB GS mavlink `dec_ok` 98513→98789 in 5 s (~46 pkt/s), `lost=2`, `bad=0`;
  `out` advancing 15 pkt/s into `127.0.0.1:14560`; QGC laptop `10.5.6.50` **REACHABLE, inactive 0 ms,
  tx 86.6 Mbit/s** on `p2p-wlan0-0`.
- 🔴 **THE UNIT IS STILL `inactive`/`disabled` WITH AN EMPTY `ExecMainStartTimestamp` — THE DAEMON WAS STARTED
  OUTSIDE SYSTEMD ⇒ IT WILL NOT SURVIVE A REBOOT.** The relay has no RTC and does get power-cycled.
  ⏭ **`sudo systemctl enable mavlink-router`** (persists at next boot).
  ⛔ **NOT `enable --now`** — PID 750 already holds UDP 14560, so `start` fails "address in use".
  To hand it to systemd immediately: `kill 750` first, then `enable --now`.
- 🔑 **TRAP FOR NEXT TIME: `systemctl is-active` SAID `inactive` WHILE THE DAEMON WAS RUNNING FINE.**
  A hand-started daemon is invisible to the unit. **Check `ps -eo pid,ppid,etimes,args | grep mavlink` and
  who holds the port BEFORE concluding a service is down.** ⚠️ `ss` shows no `users=` for another user's
  socket without root — an unowned-looking bound port is a hint something else holds it.
