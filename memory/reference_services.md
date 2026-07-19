---
name: services
description: "Full systemd service map for companion (mavlink, DDS, sensors, video, WFB)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
---

last verified: 2026-05-09 — mavlink.router + microxrce-agent both active, FC client connected, DDS topics negotiated

mavlink.router.service   → FC MAVLink↔GCS via ttyAMA0 | cfg: /etc/mavlink-router/main.conf
                          TCP:5760(GCS) UDP:192.168.1.100:14550 UDP:127.0.0.1:14550(WFB)
                          NOTE: config endpoint named "serial-AMA4" but device is /dev/ttyAMA0 — section name ≠ device path, normal
microxrce-agent.service  → uXRCE-DDS FC↔ROS2 via ttyAMA4 @ 921600 | dep: mavlink.router
                          client_key: 0x00000001 — FC negotiates topics/publishers/datawriters on startup
rc_control_node.service  → RC CH9=camera switch | CH10=shutdown(1514)/reboot(2014) hold 2s
tfmini.service           → TFmini → /fmu/in/distance_sensor @ 50Hz
vision_streaming.service → FFmpeg dual-cam RTP→WFB-NG | cfg: /etc/vision_streaming.conf
                          CH9 PWM: front=1012(video0) bottom=1514(video2) split=2014(PiP)
block-traffic.service    → block DDS multicast on drone-wfb iface
wifibroadcast@drone      → WFB-NG drone profile
system_files_sync.timer  → auto-backup boot+daily | armed check: tcp:127.0.0.1:5760
ollama.service           → Phi-3 Mini local LLM
ldlidar.service          → STL-19 → /scan (DISABLED 2026-04-17: hardware moved to other team, pkg kept in ros2_ws)
