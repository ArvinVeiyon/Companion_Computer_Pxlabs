---
name: services
description: "Full systemd service map for companion (mavlink, DDS, sensors, video, WFB)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
  modified: 2026-07-21T18:36:46.315Z
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

## ROVER AUTONAV STACK — added 2026-07-21 (replaces the old manual `setsid` bring-up)
Installer kept at scratchpad `install_rover_units.sh`; all units are User=roz, WorkingDirectory
/home/roz/ros2_ws, Restart=always RestartSec=5, ExecStart sources /opt/ros/jazzy + ws install.
rover-camera.service      → Orbbec Gemini 336L wrapper, **IMU enabled**
                            (gemini_330_series.launch.py enable_accel:=true enable_gyro:=true)
                            IMU is what lets camera mount pitch/roll be MEASURED, keep it on.
rover-scan.service        → depth→/scan + base_link→camera_link TF (launch/depth_to_scan.launch.py)
                            Wants= (not Requires=) rover-camera so a camera restart doesn't hard-kill it.
                            Takes ~20-25 s after camera start before /scan appears — "does not appear
                            to be published yet" right after boot is normal, not a fault.
rover-odometry.service    → VESC ERPM → /odom + odom→base_link TF (~100 Hz)
rover-autonav-mode.service→ px4_ros2 custom mode "AutoNav". Restart=always also covers the known
                            4 s "no request from FMU" watchdog abort that recurs without a trigger.
rover-ekf-bridge.service  → /odom → EKF2 EV velocity. **INSTALLED BUT `disabled` — DO NOT ENABLE.**
                            Deliberate: with wheels off the ground it feeds EKF2 motion the vehicle
                            isn't achieving → self-sustaining front/back limit cycle in any
                            closed-loop mode (see project_rover_autonav). Start by hand ONLY once the
                            rover is on the floor: `sudo systemctl start rover-ekf-bridge`.
                            NOTE: AutoNav cannot arm at all while this is stopped (no v_xy_valid).
All four boot units verified active + topics flowing 2026-07-21. sudo needs a password (printf|sudo -S).
