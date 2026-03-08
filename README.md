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
**PX4 Version:** v1.16.0-rc1 (custom build)

**UART Map:**
| Port | Role | Baud |
|---|---|---|
| `/dev/ttyAMA0` | FC MAVLink → mavlink-router | 921600 |
| `/dev/ttyAMA2` | TFmini lidar | 115200 |
| `/dev/ttyAMA4` | FC uXRCE-DDS → MicroXRCEAgent | 921600 |

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

**Camera Switching (RC CH9):**
- PWM 1012 → front camera `/dev/video0`
- PWM 1514 → bottom camera `/dev/video2`
- PWM 2014 → split/PiP (both cameras)
- Config: `ros2_ws/src/rc_control/config/rc_mapping.yaml`

**Vision streaming config** (remotely editable): `/etc/vision_streaming.conf`

## Auto-Backup

System config files are automatically synced to `System_files/` on boot and daily via `system_files_sync.timer`. Each sync creates a git commit and annotated tag `sync-YYYYMMDD-HHMM`.

## Relay Station

Relay (`vind-rly`) bridges WFB-NG to the ground station:
- WFB tunnel: `gs-wfb` @ `10.5.5.77/24`
- SSH port forward: relay `:2222` → drone `10.5.5.87:22`
- See `system_companion.md` §14 and `Setup_Procedure_for_Relay_Station.docx`
