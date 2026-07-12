# Vind-Roz Relay Station (RELAY-STN) — Setup & Operations

> Single-source reference for this relay (RPi4 @ `192.168.1.132`).
> Sibling of the production relay `vind-rly` (RPi5 @ `10.5.5.77`).
> Built from `~/relay_bootstrap.sh`. Last provisioned: 2026-07-12.

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
| Mgmt IP | `192.168.1.132` (onboard `wlan0`, dev LAN + internet) |
| Role | WFB-NG GS relay (`ROLE=gs`) |

---

## 2. Addressing / link plan

| Endpoint | Address | Notes |
|---|---|---|
| Drone companion (WFB far end) | `10.5.5.87` (user `roz`) | SSH target of the autossh tunnel |
| Relay WFB tunnel IP (`gs-wfb`) | `10.5.5.77` | same as vind-rly |
| Ground-control PC (QGC) | `10.5.6.50` | mavlink-router `Address=` |
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
- **Services enabled for boot** — `wifibroadcast@gs`, `mavlink.router`,
  `ssh-tunnel-to-companion`. (Enabled but NOT started yet — see §5.)
- **Claude Code CLI** — `~/.local/bin/claude` (v2.1.207). Needs a one-time login (§7).

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

## 5. Remaining manual steps (hardware / other-side)

These are expected and were flagged as warnings at the end of the run.

### 5.1 Plug in the RTL8812AU adapter and set the NIC
No `wlx…` adapter was present at install, so `WFB_NICS` is empty.
```bash
# after plugging the adapter in:
ls /sys/class/net/ | grep wlx           # find the interface name
iw dev <wlxNAME> info                   # confirm it's the 8812au
sudo wfb-rlyctl set-nics <wlxNAME>      # write it into /etc/default/wifibroadcast
# (optional) rename to wlan1 persistently, per the procedure doc:
#   /etc/udev/rules.d/70-persistent-net.rules
#   SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="<MAC>", NAME="wlan1"
sudo systemctl start wifibroadcast@gs.service
wfb-cli gs                              # watch link stats
```

### 5.2 Authorize the tunnel SSH key on the drone
The relay generated `~/.ssh/id_rsa`. Add its public key to the drone:
```bash
# from the relay (once it can reach the drone), or copy manually:
ssh-copy-id -i ~/.ssh/id_rsa.pub roz@10.5.5.87
# then:
sudo systemctl start ssh-tunnel-to-companion.service
sudo ss -tlnp | grep 2222              # should be LISTENING
```

### 5.3 P2P uplink PSK (only if using Wi-Fi P2P GS LAN)
`/etc/wpa_supplicant/wpa_supplicant.conf` has a placeholder PSK. Edit it, then bring
up P2P with `sudo ~/rely_p2p.sh` (**never** over a `wlan0` SSH session — it drops it).

### 5.4 (Optional) eth0 DHCP + netplan for the GS LAN
Per `Setup_Procedure_for_Relay_Station.docx` — `isc-dhcp-server` on `eth0`
(`10.5.6.0/24`), netplan addresses, IP forwarding. Only needed if this relay serves
the wired GS network like vind-rly does.

---

## 6. Operate / verify

```bash
# WFB link
wfb-cli gs
systemctl status wifibroadcast@gs.service
ip -br a | grep gs-wfb                  # tunnel iface once radio is up

# relay control (standalone <-> cluster, NIC mgmt)
sudo wfb-rlyctl status
sudo wfb-rlyctl set-nics <iface>

# MAVLink routing
systemctl status mavlink.router.service
journalctl -u mavlink.router -f

# SSH tunnel to the drone
systemctl status ssh-tunnel-to-companion.service
ssh roz@localhost -p 2222              # hop onto the drone via the relay
```

---

## 7. Claude Code on this relay

```bash
claude          # first run: log in (browser code or API key), then use normally
claude --version
```
`~/.local/bin` is on PATH via `~/.profile` (re-login or `source ~/.profile` if `claude`
isn't found yet). Use it here to continue relay work, edit configs, drive git, etc.

---

## 8. Files at a glance

| Path | What |
|---|---|
| `~/relay_bootstrap.sh` | the one-shot installer (idempotent) |
| `~/keys/gs.key`, `~/keys/drone.key` | WFB keys used at install (match the drone) |
| `~/relay_install2.log` | successful provisioning log |
| `~/RELAY_STATION_SETUP.md` | **this document** |
| `/etc/wifibroadcast.cfg` | WFB config (channel/FEC/endpoints) |
| `/etc/default/wifibroadcast` | `WFB_NICS=` (set the RF adapter here) |
| `/etc/mavlink-router/main.conf` | MAVLink routing (GCS = 10.5.6.50) |
| `/usr/local/sbin/wfb-rlyctl` | relay control tool |
| `/usr/local/sbin/wfb-cfg-apply` | WFB safe-apply watchdog |

---

## 9. Notes / gotchas

- **Keys are shared with the live drone.** Regenerating them here (or on the drone)
  breaks the existing link. Keep `/etc/gs.key` + `/etc/drone.key` identical on both.
- **Two relays, same keys/channel/tunnel IP** (`10.5.5.77`): don't run this and
  `vind-rly` on the same channel simultaneously — they will interfere / collide on IP.
  Treat one as primary, the other as spare/replacement.
- **No RTC + clock:** like other field Pis, verify time after boot if NTP is unreachable.
- **Driver choice:** aircrack-ng 8812au vs svpcom — functionally equivalent for WFB.
  If a future kernel breaks the DKMS build, `sudo dkms status` and rebuild, or switch to
  svpcom's fork per the procedure doc.
