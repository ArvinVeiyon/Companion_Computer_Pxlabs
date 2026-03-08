# Drone Companion Computer - PX4 (Raspberry Pi)

## Key repo: ~/codex-work
- Git repo tracking system config files and documentation
- Main doc: `system_companion.md` (living reference, auto-updated by sync)
- System file backups: `System_files/` mirroring `/etc/`, `/boot/`, `/usr/local/bin/`
- Auto-sync script: `scripts/system_files_sync.sh` (rsync + git commit + annotated tag)
- File list for sync: `System_files_list.txt`
- Sync log: `logs/system_files_sync.log`

## Flight Controller
- Custom board based on Pixhawk 6X-RT design (NXP i.MX RT1176, RT11xx, dual Cortex-M7+M4)
- NOT the Holybro retail unit — own PCB
- PX4 target: px4_fmu-v6xrt
- Used on both drone and rover builds (same companion, different PX4 airframe config)

## UART Port Map (RPi5)
- ttyAMA0 → FC MAVLink (mavlink-router, 921600)
- ttyAMA4 → FC uXRCE-DDS (MicroXRCEAgent, 921600)
- ttyAMA2, ttyAMA10 → available/other

## Key Software Stack
- PX4-Autopilot: ~/PX4-Autopilot
- ROS2 workspace: ~/ros2_ws
- MAVLink router: ~/mavlink-router + /etc/mavlink-router/main.conf
- Micro-XRCE-DDS Agent: ~/Micro-XRCE-DDS-Agent
- WFB-NG (WiFi Broadcast): ~/wfb-ng + /etc/wifibroadcast.cfg
- AIDE integrity monitoring: installed, dailyaidecheck.timer active

## Tracked Systemd Services
- mavlink.router.service
- microxrce-agent.service
- rc_control_node.service
- ros2_external_node_reg.service
- ros2_px4_translation_node.service
- tfmini.service
- vision_streaming.service

## Network / Comms (WFB-NG)
- WiFi channel 157 (5 GHz), region BO, TX power 30 dBm (rtl8812eu), MCS 1, BW 20 MHz
- Drone tunnel iface: drone-wfb @ 10.5.5.87/24 | GS/relay: gs-wfb @ 10.5.5.77/24
- Relay (vind-rly): exposes port 2222 -> drone SSH via WFB tunnel (10.5.5.77)
- CRITICAL: default_route = False on both [drone_tunnel] and [gs_tunnel]
- Streams: video (udp 127.0.0.1:5602), mavlink (0.0.0.0:14550), tunnel (tun iface)
- GS endpoints: video 10.5.6.50:5600, mavlink 10.5.6.50:14550
- FEC: video 8/12, mavlink 1/2, tunnel 2/4

## Known Issues in codex-work
- Embedded git repos warning (ros2_ws submodules inside System_files)
- install.sh / bootstrap.sh are Claude Code installers that ended up in repo
- Some files not yet synced (need sudo): netplan yaml, sshd_config.d

## Auto-sync Behavior
- On boot + daily via systemd/cron
- Diffs system files, commits changes, creates annotated tag sync-YYYYMMDD-HHMM
- Appends change summary to system_companion.md ## Auto Sync Log section

## See also
- drone-companion.md for detailed notes

---

# Relay Station - vind-rly (Raspberry Pi 5)

## SSH Access
- From companion: `ssh vind-admin@10.5.5.77` (key already installed)
- sudo password: `1987`
- Port 2222 on relay → drone companion SSH (autossh tunnel)

## Key repo: ~/codex-relay (on vind-rly)
- Same structure as codex-work on companion
- Main doc: `system_relay.md`
- Sync script: `scripts/system_files_sync.sh`
- File list: `System_files_list.txt`
- Sync timer: `relay_files_sync.timer` (boot + daily)
- NO GitHub remote yet — local only for now

## Relay Role
- WFB-NG ground station (wifibroadcast@gs.service, gs-wfb @ 10.5.5.77/24)
- SSH tunnel: port 2222 → drone 10.5.5.87:22 (ssh-tunnel-to-companion.service, autossh)
- MediaMTX RTSP video relay (mediamtx.service, ~/Rtps_Server/)
- DHCP server for 10.5.6.0/24 range .50–.99 (isc-dhcp-server.service)
- P2P WiFi iface: p2p-wlan0-0 @ 10.5.6.101/24

## Key Services on Relay
- wifibroadcast@gs.service
- ssh-tunnel-to-companion.service
- mediamtx.service
- isc-dhcp-server.service
- relay_files_sync.timer

## What Was Done (to replicate for relay)
Same process as companion computer audit:
1. SSH in, collect all config files, services, scripts
2. Create ~/codex-relay with System_files_list.txt, sync script, system_relay.md
3. Enable relay_files_sync.timer (boot + daily)
4. Initial git commit done (2695911)
5. TODO: push to GitHub (no remote set yet)
6. TODO: audit relay for missing files (same checklist as companion)
7. TODO: connect & configure OpenWrt CPE610 cluster node (10.5.7.102) — NOT connected yet
   - Firmware in ~/Openwrt_WFB_NG/ on relay
   - Init: wfb-server --gen-init → scp → run on node
   - SSH key: /home/vind-admin/.ssh/wfb_cluster_ed25519
