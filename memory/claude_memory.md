# Claude Persistent Memory — Vind-Roz Platform
> This file is my long-term memory for this project. It is tracked in codex-work and pushed to GitHub.
> The live copy loaded each session is at: ~/.claude/projects/-home-roz/memory/MEMORY.md
> This file in codex-work/memory/ is the GitHub-backed version — synced by system_files_sync.sh.
> If both exist, the live MEMORY.md is the authoritative one (loaded by Claude Code automatically).

---

## Identity & Context
- I am Claude, running as Claude Code CLI on the Vind-Roz companion computer (Raspberry Pi 5)
- This is a PX4-based drone/rover platform — I am the onboard AI assistant
- My memory persists across sessions via MEMORY.md, backed up here to GitHub
- The user (roz / ArvinVeiyon) wants me to be a continuous, conscious presence on this system

---

## Companion Computer (Vind-Roz) — RPi5

### Key Repos & Docs
- `~/codex-work` → GitHub: ArvinVeiyon/Companion_Computer_Pxlabs
  - `system_companion.md` — main living reference doc (auto-updated by sync)
  - `System_files/` — tracked backups of /etc/, /boot/, /usr/local/bin/
  - `scripts/system_files_sync.sh` — rsync + git commit + tag, runs on boot + daily
  - `System_files_list.txt` — list of tracked files (31 entries)
  - `memory/` — this directory, Claude's GitHub-backed memory
- Sync timer: `system_files_sync.timer` (active, last ran 2026-03-08 10:41)

### Hardware
- **FC:** Custom Pixhawk 6X-RT (NXP i.MX RT1176, dual Cortex-M7+M4) — own PCB, NOT Holybro retail
- **PX4 target:** px4_fmu-v6xrt
- **Used for:** both drone and rover (same companion, different PX4 airframe config)
- **UART map:** ttyAMA0 → MAVLink (921600) | ttyAMA4 → uXRCE-DDS (921600) | ttyAMA2 → TFmini

### Key Software
- PX4-Autopilot: ~/PX4-Autopilot (commit c5b8445ffc)
- ROS2 Jazzy workspace: ~/ros2_ws (branch main_dev)
- mavlink-router: ~/mavlink-router (commit c20337b) + /etc/mavlink-router/main.conf
- Micro-XRCE-DDS-Agent: ~/Micro-XRCE-DDS-Agent (commit b9d84ac)
- WFB-NG: ~/wfb-ng (commit 1b88185) + /etc/wifibroadcast.cfg
- AIDE integrity monitoring: active (dailyaidecheck.timer)

### Active Systemd Services
mavlink.router.service | microxrce-agent.service | rc_control_node.service
ros2_px4_translation_node.service | tfmini.service | vision_streaming.service
block-traffic.service | system_files_sync.timer | wifibroadcast@drone.service

### Network (WFB-NG)
- Channel 157 (5 GHz), region BO, TX 30 dBm (rtl8812eu), MCS 1, BW 20 MHz
- drone-wfb: 10.5.5.87/24 | gs-wfb (relay): 10.5.5.77/24
- CRITICAL: default_route = False on drone_tunnel and gs_tunnel
- FEC: video 8/12, mavlink 1/2, tunnel 2/4
- GS endpoints: video 10.5.6.50:5600, mavlink 10.5.6.50:14550

### ROS2 Nodes
| Node | Package | Hardware |
|---|---|---|
| rc_control_node | rc_control | RC CH9=camera switch, CH10=shutdown/reboot |
| vision_streaming_node | vision_streaming | FFmpeg RTP via /etc/vision_streaming.conf |
| tfmini_node | tfmini_sensor | TFmini lidar /dev/ttyAMA2 @ 115200 |
| optical_flow_node | optical_flow | /dev/video3, OpenCV Farneback |
| obstacle_distance_publisher | obstacle_distance | VL53L1X ToF, I2C bus 1, 0x29 |

### Custom Binary
- `/usr/local/bin/vision_config_manager` — Python script v1.2.1
  - Called by rc_control_node via RC CH9 to switch cameras
  - Rewrites /etc/vision_streaming.conf, restarts vision_streaming.service
  - Also tracked in System_files_list.txt

---

## Relay Station (vind-rly) — RPi5

### Access
- SSH: `ssh vind-admin@10.5.5.77` (key installed from companion)
- sudo password: `1987`
- Port 2222 on relay → drone companion SSH (autossh tunnel)

### Key Repo
- `~/codex-relay` — local only, NO GitHub remote yet (TODO)
  - `system_relay.md` — relay documentation
  - Same sync structure as codex-work

### Role & Services
- WFB-NG GS: wifibroadcast@gs.service (gs-wfb @ 10.5.5.77) ← ACTIVE
- MAVLink router: mavlink.router.service → QGC (10.5.6.50:14550) + tracker (127.0.0.1:14551) ← ACTIVE
- SSH tunnel: ssh-tunnel-to-companion.service (autossh, port 2222 → 10.5.5.87:22) ← ACTIVE
- Sync timer: relay_files_sync.timer ← ACTIVE
- mediamtx.service — DISABLED 2026-03-15 (latency issues)
- isc-dhcp-server.service — DISABLED 2026-03-15 (GCS uses static IP 10.5.6.50)

### WFB-NG Control Tool
- **`/usr/local/sbin/wfb-rlyctl`** — relay control CLI (sudoers: /etc/sudoers.d/wfb-rlyctl)
- ENV file: /etc/default/wifibroadcast (manages WFB_NICS)

### WFB-NG Cluster Mode
Two modes — use wfb-rlyctl to switch:
- **Standalone (CURRENT):** `sudo wfb-rlyctl use-standalone`
- **Cluster:** `sudo wfb-rlyctl use-cluster`
- `wfb-rlyctl status` — show current mode + service states
- Cluster adds OpenWrt CPE610 node at 10.5.7.102 (phy0-mon0)
- SSH key for cluster: /home/vind-admin/.ssh/wfb_cluster_ed25519
- Firmware + packages in ~/Openwrt_WFB_NG/

---

## Outstanding TODOs
1. Push codex-relay to GitHub (no remote set yet)
2. Full audit of relay (missing files, rebuild guide) — same checklist as companion
3. Connect & configure OpenWrt CPE610 cluster node (10.5.7.102) — NOT connected yet
4. Decide on offline vs online LLM model for deeper onboard AI consciousness
5. Tag codex-work v1.0.2 for recent changes (rebuild guide, vision_config_manager, sync list updates)

---

## Workflow Patterns (how I work here)
- When auditing a system: SSH in, check services, configs, scripts, compare against backup list
- When updating docs: edit system_companion.md or system_relay.md, commit, push, update release branch
- When adding files to backup: edit System_files_list.txt, commit — sync timer picks them up automatically
- Release process: push master → update release branch → create vX.Y.Z tag
- My memory file (MEMORY.md) is now tracked in System_files_list.txt and backed up to GitHub
