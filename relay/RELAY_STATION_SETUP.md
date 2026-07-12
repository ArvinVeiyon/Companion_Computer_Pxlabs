# Vind-Roz Relay Station (RELAY-STN) — Setup & Operations

> Single-source reference for this relay (RPi4). **Management IP: `192.168.1.221`**
> (USB uplink; the old onboard `192.168.1.132` is now repurposed for P2P — see §5).
> Sibling of the production relay `vind-rly` (RPi5 @ `10.5.5.77`); its config mirrors it.
> Built from `~/relay_bootstrap.sh`. Last provisioned / networked: 2026-07-12.

---

## 1. What this box is

A WFB-NG **ground-station relay** for the Vind-Roz drone/rover platform. It bridges
the long-range wifibroadcast link to the drone companion and exposes MAVLink + an
SSH tunnel to the ground-control PC. It is a drop-in equivalent of `vind-rly`, using
the **same WFB keys and channel** so it pairs with the existing drone.

| | |
|---|---|
| Hostname | `RELAY-STN` |
| Hardware | Raspberry Pi 4 (aarch64) |
| OS | Ubuntu 24.04.4 LTS, kernel 6.8.0-1060-raspi |
| Admin user | `vind-admin` (sudo) |
| Mgmt IP | `192.168.1.221` (USB adapter `wlx…24d6`, SSID `Nilan`) |
| Role | WFB-NG GS relay (`ROLE=gs`) |

---

## 2. Addressing / link plan

| Endpoint | Address | Notes |
|---|---|---|
| Internet / mgmt uplink | `192.168.1.221` (`wlx…24d6` on `Nilan`) | default route; SSH the relay here |
| P2P GS network | `10.5.6.101/24` (`p2p-wlan0-0`) | GS devices join SSID `RELAY-STN01` |
| Drone companion (WFB far end) | `10.5.5.87` (user `roz`) | SSH target of the autossh tunnel |
| Relay WFB tunnel IP (`gs-wfb`) | `10.5.5.77` | same as vind-rly |
| Ground-control PC (QGC) | `10.5.6.50` | mavlink-router `Address=` |
| Cluster (eth0, staged) | `10.5.7.100/24` | matches vind-rly; set when cluster is activated |
| SSH tunnel | `localhost:2222 -> roz@10.5.5.87:22` | reach the drone from the GS LAN |
| WFB channel / region / txpower | `161` / `BO` / `3000` | must match the drone |

---

## 3. What is installed (all done ✅)

- **RTL8812AU DKMS driver** — `8812au 5.6.4.2` from **aircrack-ng** (equivalent to
  svpcom's fork for monitor-mode + injection; the procedure doc lists svpcom v5.2.20).
- **WFB-NG** `25.2.25.64784-0~noble` — built from source (`svpcom/wfb-ng`, tag
  `wfb-ng-25.01`), installed as a `.deb`. Binaries: `wfb-cli`, `wfb_rx`, `wfb_tx`, etc.
- **mavlink-router** (`mavlink-routerd`) — built from source, pin `51983a4`.
- **Control tools** — `/usr/local/sbin/wfb-rlyctl`, `/usr/local/sbin/wfb-cfg-apply`
  (passwordless sudo scoped via `/etc/sudoers.d/wfb-rlyctl`).
- **Configs** — `/etc/wifibroadcast.cfg`, `/etc/mavlink-router/main.conf`,
  `/etc/default/wifibroadcast` (holds `WFB_NICS`).
- **WFB keys** — `/etc/gs.key` + `/etc/drone.key`, copied from the live drone so the
  link pairs (do NOT regenerate — that would break pairing with the drone).
- **Network** — internet uplink + P2P GS link + forwarding (see §5).
- **Services enabled for boot** — `wifibroadcast@gs`, `mavlink.router`,
  `ssh-tunnel-to-companion`. (Enabled but NOT started yet — see §6.)
- **Claude Code CLI** — `~/.local/bin/claude` (v2.1.207). Needs a one-time login (§8).

---

## 4. The installer — `~/relay_bootstrap.sh`

One self-contained script (configs embedded as a base64 payload; secrets are NOT
embedded). It is **idempotent** — re-running skips anything already installed.

```bash
# full run (safe defaults)
sudo ./relay_bootstrap.sh

# common overrides
sudo WFB_NIC=wlxAABBCCDDEEFF ./relay_bootstrap.sh   # pin the RF adapter
sudo START_SERVICES=0 ./relay_bootstrap.sh          # enable but don't start (no radio yet)
sudo DRONE_IP=10.5.5.87 GCS_IP=10.5.6.50 ./relay_bootstrap.sh
```

Keys: if `./keys/gs.key` + `./keys/drone.key` exist next to the script, they are used
(that is how this relay got the drone's keys). Otherwise existing `/etc/*.key` are kept,
else fresh keys are generated (which then must be copied to the drone).

**Build fix applied (2026-07-12):** the wfb-ng `make deb` step now runs *inside* the
source dir. `sudo -H` resets `PWD`, and wfb-ng's Makefile uses `ENV ?= $(PWD)/env`; with
an empty `PWD` it became `/env` and virtualenv failed with
`destination . is not write-able at /`. Running `bash -c "cd <src> && make deb"` fixes it.

Provisioning logs: `~/relay_install.log` (first, failed run) and `~/relay_install2.log`
(successful run, exit 0).

### 4.1 Cross-platform support (Raspberry Pi 4 / Pi 5)

Relay stations exist on both board types — **`vind-rly` runs on a Pi 5** and this
**`RELAY-STN` runs on a Pi 4** — so the installer is **one script for both**: it
auto-detects the board and adapts. No separate Pi4/Pi5 variants. (This is about the
relay hardware only; the drone companion is a different machine and out of scope here.)

- **Detection** — reads `/proc/device-tree/model` (falls back to
  `/sys/firmware/devicetree/base/model`) and sets `PI_GEN` (`4`, `5`, `3`, or `0`
  for unknown). The detected board is logged, printed in the completion summary, and
  recorded to **`/etc/vind-relay-platform`** (model, gen, arch, kernel, timestamp).
- **Sanity** — warns (does not abort) on non-aarch64, non-24.04, or an
  unrecognised/unsupported board, then continues with the generic aarch64 path.
- **Board-specific handling** — the only genuine hardware difference for a WFB relay
  is USB power for the power-hungry RTL8812AU adapter (`apply_usb_power_tuning`):
  - **Pi 5** — appends `usb_max_current_enable=1` to `config.txt` (idempotent, backs
    up to `config.txt.vind-relay.bak`; needs a proper 5V/5A PSU; effective after reboot).
    Disable with `SET_USB_POWER=0`.
  - **Pi 4** — no such knob exists; ports already share ~1.2 A. The script makes no
    boot-config change and advises a **powered USB hub** if the adapter resets under load.
- **Everything else is board-agnostic**: aarch64 driver DKMS build, wfb-ng /
  mavlink-router source builds, kernel headers (running-kernel first, `linux-headers-raspi`
  fallback), configs, keys, and services are identical on Pi4 and Pi5.

Detection/tuning logic verified on real hardware: a Pi 4 board → gen 4 (this relay's
board), and the Pi 5 code path exercised on a Pi 5 board (read-only, throwaway config)
— the same board generation vind-rly uses.

---

## 5. Network configuration (as deployed — mirrors vind-rly)

This section documents the live networking set up on `RELAY-STN`, which follows how
the Pi5 relay `vind-rly` is configured. **All secrets (Wi-Fi passphrases) live only in
on-box config files and are deliberately NOT in this repo.**

### 5.0 Interface roles

| Interface | Driver | Role | Address |
|---|---|---|---|
| `wlx90de80d824d6` | `rtw_8821cu` (RTL8821CU, USB) | **Internet uplink + mgmt** on SSID `Nilan` | `192.168.1.221` (DHCP), default route |
| `wlan0` → `p2p-wlan0-0` | `brcmfmac` (onboard) | **P2P GS link** (Wi-Fi Direct Group Owner) | `10.5.6.101/24` |
| `wlx…` (RTL8812AU) | `8812au` | **WFB monitor radio** (not yet plugged) | — (`WFB_NICS`) |
| `eth0` | — | GS wired / cluster (staged) | `10.5.7.100/24` when activated |
| `gs-wfb` | wfb tunnel | WFB tunnel to drone | `10.5.5.77/24` (when radio up) |

### 5.1 Internet uplink (USB adapter)

- A USB adapter `wlx90de80d824d6` (RTL8821CU / `rtw_8821cu`, a client-class adapter)
  is the relay's internet + management path, joined to SSID `Nilan`.
- Config: **`/etc/netplan/60-relay-uplink.yaml`** (DHCP, `route-metric: 100` so it wins
  the default route). Managed by netplan → systemd-networkd + wpa_supplicant.
- **Reach the relay at `192.168.1.221`** now — the old onboard `wlan0` (`.132`) was
  freed for P2P, so it no longer carries a management IP.
- Why: gives the relay its own internet (NTP/clock, apt, git, Claude) and frees the
  onboard Wi-Fi for the P2P GS link.

### 5.2 P2P ground-station link (onboard `wlan0`)

- Onboard `wlan0` runs a **Wi-Fi Direct P2P Group Owner**: `p2p-wlan0-0` @
  `10.5.6.101/24`, network name / device name **`RELAY-STN01`**.
- Brought up by **`~/rely_p2p.sh`** (the Pi5-verbatim minimal script) and auto-started
  at boot via **`@reboot /home/vind-admin/rely_p2p.sh`** in **root's** crontab.
- Credential config: **`/etc/wpa_supplicant/wpa_supplicant.conf`** — network block,
  `mode=3` (GO), `ssid="RELAY-STN01"`, `bssid=<own p2p MAC>`, and the WPA2 `psk=`
  (**passphrase value is in this file only, not in git**).
- **Two ways for a GS device to join** (both active — max compatibility):

  | Credential | Type | Who uses it | How |
  |---|---|---|---|
  | **`1987`** | WPS **PIN** (`wps_pin any 1987` in `rely_p2p.sh`) | WPS / Wi-Fi-Direct-aware clients (phones, `p2p_connect` PIN flow) | Client authenticates with the PIN; relay hands over Wi-Fi credentials automatically — no passphrase typed |
  | **passphrase** | WPA2 **PSK** (in `wpa_supplicant.conf`) | Ordinary Wi-Fi clients — e.g. the **Windows GCS laptop** | Client sees `RELAY-STN01` (broadcast `DIRECT-xx-RELAY-STN01`) and joins like any password Wi-Fi by typing the passphrase |

  > Windows can't cleanly do the Wi-Fi-Direct WPS-PIN handshake with an autonomous GO,
  > so on Windows you use the **passphrase**; the **PIN** path is for WPS/Direct clients.
  > WPS (the PIN) is weaker than the passphrase — fine for a closed field link, but don't
  > treat the PIN as a strong secret.

- **cloud-init network regeneration is disabled**
  (`/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg`) so this survives reboot and
  doesn't fight the P2P setup for `wlan0`.

### 5.3 IP forwarding

- `net.ipv4.ip_forward=1`, persisted in **`/etc/sysctl.d/99-relay-forward.conf`**.
- **No iptables NAT/FORWARD rules** — this matches `vind-rly` (default-ACCEPT policy,
  routing via `ip_forward`). GS clients do **not** get internet through the relay by
  default. If you later want to share the uplink to the GS, add on the uplink:
  `sudo iptables -t nat -A POSTROUTING -o wlx90de80d824d6 -j MASQUERADE`.

### 5.4 Cluster (staged — running standalone)

- The `[cluster]` block is present in `/etc/wifibroadcast.cfg` (copied from vind-rly:
  server `10.5.7.100`, second node CPE610 `10.5.7.102`), but the relay runs
  **standalone**. To activate cluster later: connect this Pi4's RTL8812AU (+ set
  `WFB_NICS` and the local cluster node's wlan), set `eth0 = 10.5.7.100/24`, bring up
  the CPE610 node, then `sudo wfb-rlyctl use-cluster`.

### 5.5 Naming scheme

- P2P network of this Pi4 = **`RELAY-STN01`**. Plan: rename the Pi5 `vind-rly`'s P2P
  (`vind_rely`) → **`RELAY-STN00`** so the pair is `…00` (Pi5) / `…01` (Pi4).

### 5.6 How the cutover was done safely

The uplink/P2P cutover was applied **detached with a 5-minute dead-man auto-revert**
(re-enable the old `wlan0` client and restore netplan if reachability isn't confirmed).
This is the safe pattern for reconfiguring networking over the very Wi-Fi link you're
logged in through. Repeat that pattern for any future change to `wlan0`/uplink.

---

## 6. Remaining manual steps (hardware / other-side)

### 6.1 Plug in the RTL8812AU adapter and set the NIC
No `wlx…` WFB adapter was present at install, so `WFB_NICS` is empty.
```bash
ls /sys/class/net/ | grep wlx           # find the interface name
iw dev <wlxNAME> info                   # confirm it's the 8812au
sudo wfb-rlyctl set-nics <wlxNAME>      # write it into /etc/default/wifibroadcast
sudo systemctl start wifibroadcast@gs.service
wfb-cli gs                              # watch link stats
```

### 6.2 Authorize the tunnel SSH key on the drone
The relay generated `~/.ssh/id_rsa`. Add its public key to the drone:
```bash
ssh-copy-id -i ~/.ssh/id_rsa.pub roz@10.5.5.87
sudo systemctl start ssh-tunnel-to-companion.service
sudo ss -tlnp | grep 2222              # should be LISTENING
```

### 6.3 P2P GS link — ✅ done (see §5.2)
Configured and auto-starting. To change the passphrase, edit the `psk=` line in
`/etc/wpa_supplicant/wpa_supplicant.conf` then `sudo ~/rely_p2p.sh` (**never over a
`wlan0`/P2P session** — run it from the `.221` uplink SSH).

---

## 7. Operate / verify

```bash
# network
ip -br addr                              # wlx…=192.168.1.221, p2p-wlan0-0=10.5.6.101
iw dev | grep -A2 p2p-wlan0-0            # P2P GO, ssid RELAY-STN01
cat /etc/vind-relay-platform             # detected board

# WFB link
wfb-cli gs
systemctl status wifibroadcast@gs.service
ip -br a | grep gs-wfb                   # tunnel iface once radio is up

# relay control (standalone <-> cluster, NIC mgmt)
sudo wfb-rlyctl status
sudo wfb-rlyctl set-nics <iface>

# MAVLink routing + drone tunnel
systemctl status mavlink.router.service
ssh roz@localhost -p 2222               # hop onto the drone via the relay
```

---

## 8. Claude Code on this relay

```bash
claude          # first run: log in (browser code or API key), then use normally
claude --version
```
`~/.local/bin` is on PATH via `~/.profile` (re-login or `source ~/.profile` if `claude`
isn't found yet). Use it here to continue relay work, edit configs, drive git, etc.

---

## 9. Files at a glance

| Path | What |
|---|---|
| `~/relay_bootstrap.sh` | the one-shot installer (idempotent, Pi4/Pi5) |
| `~/keys/gs.key`, `~/keys/drone.key` | WFB keys used at install (match the drone) |
| `~/rely_p2p.sh` | brings up the P2P GS link (Pi5-verbatim); runs `@reboot` |
| `~/relay_install2.log` | successful provisioning log |
| `~/RELAY_STATION_SETUP.md` | **this document** |
| `/etc/netplan/60-relay-uplink.yaml` | internet uplink (USB adapter → `Nilan`) |
| `/etc/wpa_supplicant/wpa_supplicant.conf` | P2P GO config + passphrase (secret; not in git) |
| `/etc/sysctl.d/99-relay-forward.conf` | `ip_forward=1` |
| `/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg` | stops cloud-init clobbering netplan |
| `/etc/vind-relay-platform` | detected board (model/gen/arch/kernel) |
| `/etc/wifibroadcast.cfg` | WFB config (channel/FEC/endpoints, `[cluster]`) |
| `/etc/default/wifibroadcast` | `WFB_NICS=` (set the RF adapter here) |
| `/etc/mavlink-router/main.conf` | MAVLink routing (GCS = 10.5.6.50) |
| `/usr/local/sbin/wfb-rlyctl` | relay control tool (standalone/cluster) |
| `/usr/local/sbin/wfb-cfg-apply` | WFB safe-apply watchdog |

---

## 10. Notes / gotchas

- **Manage via `192.168.1.221`** (the USB uplink), not the old `.132` — onboard `wlan0`
  is now the P2P radio and carries no management IP.
- **P2P has two join credentials** (see §5.2): WPS **PIN 1987** (Direct/WPS clients) and
  the **WPA2 passphrase** (Windows GCS + ordinary Wi-Fi clients). Different purposes;
  keep both. Passphrase lives only in `wpa_supplicant.conf` on the box.
- **Never reconfigure `wlan0`/uplink over the Wi-Fi you're logged in through** without
  the detached + dead-man-revert pattern (§5.6) — you can lock yourself out.
- **Keys are shared with the live drone.** Regenerating them (here or on the drone)
  breaks the link. Keep `/etc/gs.key` + `/etc/drone.key` identical on both.
- **Two relays, same keys/channel/tunnel IP + P2P IP (`10.5.6.101`)**: don't run this and
  `vind-rly` simultaneously — they will interfere / collide. Treat one as spare/replacement.
- **No RTC + clock:** verify time after boot if NTP is unreachable (the new uplink gives
  internet, which should help NTP sync — a plus over the Pi5 relay).
- **Driver choice:** aircrack-ng 8812au vs svpcom — functionally equivalent for WFB.
  If a future kernel breaks the DKMS build, `sudo dkms status` and rebuild, or switch to
  svpcom's fork per the procedure doc.
