# Companion Computer — PX4 (Vind-Roz)

Companion computer configuration, service files, and living documentation for the **Vind-Roz** platform — a Raspberry Pi 5 companion running PX4-based drone and rover builds.

## Contents

| Path | Description |
|---|---|
| [`system_companion.md`](system_companion.md) | **Main reference doc** — hardware, software stack, ROS2 nodes, WFB-NG, services, topics |
| `System_files/` | Tracked backups of live system config files (mirrors `/etc/`, `/boot/`, etc.) |
| `System_files_list.txt` | List of files synced by the auto-backup script |
| `scripts/system_files_sync.sh` | Auto-backup script (rsync → git commit → annotated tag) |
| `logs/system_files_sync.log` | Sync run log |
| `Setup_Procedure_for_Relay_Station.docx` | Relay station (vind-rly) setup guide |

## Quick Reference

**Flight Controller:** Custom Pixhawk 6X-RT (NXP i.MX RT1176) — PX4 target `px4_fmu-v6xrt`
**Companion:** Raspberry Pi 5 (8 GB), Ubuntu 24.04 LTS, ROS2 Jazzy
**PX4 Version:** pxlabs-v1.17.0-2.0.0 (custom PXLABS build, git `a52c38b07d`, flashed 2026-05-31)

**UART Map:**
| Port | Role | Baud |
|---|---|---|
| `/dev/ttyAMA0` | FC MAVLink → mavlink-router | 921600 |
| `/dev/ttyAMA2` | TFmini lidar | 115200 |
| `/dev/ttyAMA3` | STL-19 lidar (RX-only, disabled — unit with other team) | 230400 |
| `/dev/ttyAMA4` | FC uXRCE-DDS → MicroXRCEAgent | 921600 |

**Network (2026-07-25):** mgmt/internet uplink = external USB RTL8821CU `wlx90de80d824d6`, static
`192.168.1.240/24` (SSID `Nilan`). Onboard `wlan0` is out of netplan (link DOWN) — see
`system_companion.md` §6 *Network* for the caveat about `dtoverlay=disable-wifi`.

**Key Services:**
| Service | Role |
|---|---|
| `mavlink.router.service` | MAVLink FC ↔ GCS/network |
| `microxrce-agent.service` | uXRCE-DDS bridge FC ↔ ROS2 |
| `rc_control_node.service` | RC input → camera switch + shutdown/reboot |
| `vision_streaming.service` | FFmpeg camera → RTP → WFB-NG |
| `tfmini.service` | TFmini lidar → `/fmu/in/distance_sensor` |
| `ros2_px4_translation_node.service` | PX4 ↔ ROS2 message translation |
| `system_files_sync.timer` | Daily auto-backup of config files to this repo |
| `ext5v-logger.service` | 5 V rail / throttling / NIC-drop watchdog (2026-07-25) |
| `rover-camera` · `rover-scan` · `rover-odometry` · `rover-autonav-mode` | Rover autonomy stack (all enabled, auto-start) |
| `rover-ekf-bridge.service` | EV→EKF2 bridge — **disabled on purpose**, start by hand on the floor only |

**Camera Switching (RC CH9):**
- PWM 1012 / 1514 / 2014 → front / bottom / split — **STALE (2026-07-19):** device paths predate
  the multicam upgrade (video0/2 are now Orbbec nodes; v2 guard rejects them). Migration to
  aliases pending (todos #8). Current camera model: `vision_multicam_companion.md`
- Config: `ros2_ws/src/rc_control/config/rc_mapping.yaml`

**Vision streaming config** (remotely editable): `/etc/vision_streaming.conf`

## Auto-Backup

System config files are automatically synced to `System_files/` on boot and daily via `system_files_sync.timer`. Each sync creates a git commit and annotated tag `sync-YYYYMMDD-HHMM`.

## Relay Station

Relay (`vind-rly`) bridges WFB-NG to the ground station:
- WFB tunnel: `gs-wfb` @ `10.5.5.77/24`
- SSH port forward: relay `:2222` → drone `10.5.5.87:22`
- GCS also SSHes relay directly (port 22) for WFB mode control via `wfb-rlyctl`
- See `system_companion.md` §15 (GCS Interface) and `Setup_Procedure_for_Relay_Station.docx`
- Relay docs: `ArvinVeiyon/Relay_Station_Pxlabs` (mirror at `~/codex-relay-mirror`)

## PX4 MAVLink Utility

Script: `scripts/px4_mavlink.py`

Connects via mavlink-router TCP:5760 — no conflict with mavlink-router or WFB-NG.

```bash
python3 ~/codex-work/scripts/px4_mavlink.py monitor       # live STATUSTEXT / SYS_STATUS logs
python3 ~/codex-work/scripts/px4_mavlink.py ls            # list SD card (/fs/microsd)
python3 ~/codex-work/scripts/px4_mavlink.py ls <path>     # list specific path
python3 ~/codex-work/scripts/px4_mavlink.py rm-faults     # delete all fault_*.log from SD
python3 ~/codex-work/scripts/px4_mavlink.py shell <cmd>   # run NuttShell command on FC
```

Requires: `pymavlink` (already installed)

## Release History

| Tag | Branch | Commit | Date | Key Changes |
|-----|--------|--------|------|-------------|
| `v1.0.0` | `release` | `36cd704` | 2026-03-08 | Initial release — README, ROS2 nodes, topics, camera switch, auto-backup |
| `v1.0.1` | `release` | `422f4d2` | 2026-03-08 | Clean up sync list |
| `v1.0.2` | `release` | `1de24c4` | 2026-03-08 | bump v1.3.7 — WFB-NG diagnostics logged |
| `v1.0.3` | `release` | `ea9a5c9` | 2026-03-09 | fix wifibroadcast.cfg, mavlink_sys_id |
| `v1.0.4` | `release` | `0ebf862` | 2026-03-09 | add px4_mavlink.py: PX4 MAVLink utility |
| `v1.0.5` | `release` | `74f3c48` | 2026-03-09 | auto-sync: include px4_mavlink.py |
| `v1.0.6` | `release` | `6bf1749` | 2026-03-09 | wfb-ng: fix mavlink streams, increase FEC |
| `v1.0.7` | `release` | `b1236a9` | 2026-03-15 | Security: replace hardcoded PAT with SSH URL; remove sudo password from docs |
| `v1.0.8` | `master` | `96816fc` | 2026-04-17 | WFB-NG channel 157→161 (work in `a60791f`); stale kernel version fixed + missing memory backups |
| `v1.0.9` | `master` | `9e172fb` | 2026-05-10 | WFB-NG multi-adapter: video udp_direct_tx→udp_proxy, dual NIC, fwmark documented (work in `ea17fe4`) |
| `v1.1.0` | `master` | `474e05e` | 2026-07-10 | Section 15 GCS Interface (work in `2087fce`) + WFB-NG full drone config reference + memory backup sync |
| `v1.2.0` | `master` | `740ebc7` | 2026-07-12 | WFB safe-apply watchdog (`wfb-cfg-apply`, 755 root:root) + `wifibroadcast.cfg.default` tracked |

> **Commit column = the commit each tag actually points at** (`git rev-list -n1 <tag>`), verified
> 2026-07-26. Where the documenting/content commit differs it is named in the description — earlier
> revisions of this table listed those content commits in the Commit column, which did not match the tags.
> Latest tag: **`v1.2.0`**. `v1.0.0`–`v1.0.7` are on both `master` and `release`; `v1.0.8`+ are `master` only.
