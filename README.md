# Companion Computer — PX4 (Vind-Roz)

> **Working on this platform with another Claude/agent?** Read and append to
> [`COORDINATION.md`](COORDINATION.md) — the companion↔QGC-PC handoff log (current
> versions, standing rules, open items). The two sides cannot see each other; that
> file is the channel.

Companion computer configuration, service files, and living documentation for the **Vind-Roz** platform — a Raspberry Pi 5 companion running PX4-based drone and rover builds.

## Contents — the document index

⚠️ **Rover and DroneCAN docs live HERE, at this root — not in `ros2_ws`.** `ros2_ws/docs/README.md`
is the separate index for the ROS 2 / autonomy side; this table covers the companion repo only.

### Platform reference

| Path | What it is | Read it when |
|---|---|---|
| [`system_companion.md`](system_companion.md) | **Main reference** — hardware, software stack, ROS 2 nodes, WFB-NG, services, topics | Anything about how this box is put together |
| [`COORDINATION.md`](COORDINATION.md) | Companion ↔ QGC-PC handoff log: versions, standing rules, open items | Another agent is working the other side; append here |
| [`rc_configuration.md`](rc_configuration.md) | RC input and UAVCAN ESC output, as measured | Channel mapping, kill switch, brake channel. §6 is the RC procedure |
| [`pxlabs_release_note_v1.17.0-r2.1.md`](pxlabs_release_note_v1.17.0-r2.1.md) | Release note for the flashed PX4 build | Confirming what firmware is on the FC |

### Rover motion — ESCs, DroneCAN, config

| Path | What it is | Read it when |
|---|---|---|
| [`esc_px4_config_audit_20260914.md`](esc_px4_config_audit_20260914.md) | **Latest full audit**: the RR hall-table fault and its fix, four-way ESC comparison, outstanding candidate faults, PX4 rover-param findings | Rover drives oddly; before changing any ESC or `RO_*` value |
| [`px4_vesc_dronecan_implementation.md`](px4_vesc_dronecan_implementation.md) | PX4 ↔ VESC DroneCAN diagnosis and implementation spec | Wiring PX4 outputs to the ESCs |
| [`bldc_can/README.md`](bldc_can/README.md) | VESC flashing over CAN/USB — **§5 has the brick derivation** | Before touching ESC firmware |
| [`bldc_can/RESUME.md`](bldc_can/RESUME.md) | Where the RC-brake work stands; firmware hashes per wheel | Picking the brake work back up |
| [`bldc_can/MOTOR_MAP.md`](bldc_can/MOTOR_MAP.md) | Motor ↔ node ID map (FR 10 · FL 11 · RR 12 · RL 13) | Any per-wheel work. ⛔ Never index ESCs by position |
| [`bldc_can/configs_live/README.md`](bldc_can/configs_live/README.md) | What the captured-off-hardware configs are and are not | Before trusting any config XML |
| [`companion_can_driver_status.md`](companion_can_driver_status.md) | The dropped MCP2515 CAN-HAT work and how to finish reverting it | ⛔ Only to revert. Do not reopen the debugging |

### Evidence — measured runs

| Path | What it is |
|---|---|
| [`bldc_can/evidence/brake_floor_test_20260909.md`](bldc_can/evidence/brake_floor_test_20260909.md) | RC brake, loaded, on the floor |
| [`bldc_can/evidence/brake_bench_test_20260909.md`](bldc_can/evidence/brake_bench_test_20260909.md) | RC brake, bench |
| [`bldc_can/evidence/t2_autonav_floor_20260916.md`](bldc_can/evidence/t2_autonav_floor_20260916.md) | **T2 PASSED n=3, G3 closed.** The speed-dependent odom scale curve (3 tape points), and the 09-14 fault signature caught on the floor at full rate |
| `bldc_can/evidence/*.csv` | Full-rate ESC logs. 2026-09-14 set: straight-line stops before/after the hall fix, sustained crawl, stand comparison. 2026-09-15/16 set (`t2_*`): the four T2 runs, incl. the end-of-stop current spike |
| `px4_param_backups/` | Full PX4 parameter dumps, QGC-loadable `.params` |

### Sensors and payload

| Path | What it is |
|---|---|
| [`vision_multicam_companion.md`](vision_multicam_companion.md) | Multi-camera vision, companion side |
| [`ldlidar_stl19_install_guide.md`](ldlidar_stl19_install_guide.md) | STL-19 LiDAR install (outdoor O1) |

### Relay station

| Path | What it is |
|---|---|
| [`relay/RELAY_STATION_SETUP.md`](relay/RELAY_STATION_SETUP.md) | Relay station setup and operations |
| [`relay/NETWORK_SETUP_PROCEDURE.md`](relay/NETWORK_SETUP_PROCEDURE.md) | Relay network bring-up runbook |

### Not documentation

| Path | What it is |
|---|---|
| `System_files/` | Tracked backups of live system config (mirrors `/etc/`, `/boot/`) |
| `System_files_list.txt` · `scripts/system_files_sync.sh` · `logs/` | Auto-backup file list, script, run log |
| `memory/` | **Manual mirror** of the agent memory at `~/.claude/projects/-home-roz/memory/`. ⛔ Never `rsync --delete` — it is a union of two scopes |
| `Setup_Procedure_for_Relay_Station.docx` | Relay setup guide (Word) |

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

**Network (2026-09-03):** mgmt/internet uplink = `wlx8c86dd5beed9`, static `192.168.1.240/24`
(SSID `Nilan`) — measured 09-03 as a **TP-Link Archer T2U PLUS `2357:0120` (RTL8821AU)** on
`rtl88xxau_wfb`, **not** the RTL8821CU / `wlx90de80d824d6` this file used to name.
Onboard `wlan0` is **gone**, not merely down — `dtoverlay=disable-wifi-pi5` is live and
`brcmfmac` is unloaded. Wired last resort on `eth0` (see below). Detail: `system_companion.md` §4.

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

## Reaching the companion when the radio is down

Every remote path above rides WFB, and there is no onboard Wi-Fi to fall back to. Since 2026-09-03
`eth0` is a wired last resort: plug a cable in and use `ssh roz@10.10.10.10` (laptop side static
`10.10.10.20/24`) or `ssh roz@Vind-Roz.local` (works with the laptop left on "automatic").
It cannot disturb the normal uplink — DHCP route metric 300 vs the uplink's 50 — and boot never
waits on it. Detail: `system_companion.md` §4/§8, `ros2_ws/docs/setup_manual.md` §E5b.

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
