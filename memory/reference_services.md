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

## tfmini — DISABLED on the rover 2026-07-26 (MUST RE-ENABLE FOR THE DRONE BUILD)

`systemctl disable --now tfmini` — the TFmini is a **downward-facing rangefinder for the aerial
build** (altitude aiding: ttyAMA2 @115200 → `px4_msgs/DistanceSensor` → `/fmu/in/distance_sensor` →
DDS → PX4). A ground rover has no use for it, and the sensor is not fitted on the rover.

**⚠️ RE-ENABLE WHEN SWITCHING BACK TO THE DRONE AIRFRAME:** `sudo systemctl enable --now tfmini`.
Nothing else records this dependency — the rover deliberately runs without it, so a silently missing
distance sensor on the next drone flight would look like a hardware fault.

**Why it was disabled — it was not idle, it was expensive.** With no sensor attached it burned ~38%
CPU and wrote **~214 log lines/second** (12,845 in 60 s), which thrashed the SD card. Disabling it
took `/scan` from 19.4→14.9 Hz with 267 ms worst-case gaps to a **steady 29.0 Hz, 64 ms worst case,
jitter down 9×** — while AIDE was still running. It was the main cause of camera degradation, ahead
of both AIDE and USB (USB was never at fault: Orbbec sits at full 5000 Mbps, no resets, no
over-current, `throttled=0x0`). Journal was 3.6 GB, vacuumed to 469 MB (disk 58%→52%). This node is
very likely what filled the disk before the 20.4 GB cleanup on 2026-07-21.

**The bug is still in the source** (`src/tfmini_sensor/tfmini_sensor/tfmini_node.py`) — user chose
not to fix it, disabling was enough. It returns the moment the node runs on the drone:
- line 24: `create_timer(0.005, ...)` = **200 Hz**, while the comment says 50 Hz and the line above
  says 100 Hz — three numbers, all disagreeing.
- line 71: every tick with <9 bytes waiting logs a WARNING, unthrottled → 200/sec with no sensor.
- line 66: the success path logs INFO on **every** published message → same rate once a sensor IS
  attached, just INFO instead of WARN. Fixing only the warning would not help the drone.

Fix if ever wanted: `throttle_duration_sec=5.0` on both log calls, and one honest timer rate
(the TFmini streams at 100 Hz, so 0.01). Same anti-pattern as ros2_ws todo #17
(`camera_sw_node_obsolute.py`, all 18 RC channels at INFO every 50 Hz).

## AIDE (dailyaidecheck.timer) — DAILY TIMER DISABLED 2026-07-26, package kept

`systemctl disable --now dailyaidecheck.timer`. AIDE 0.18.6 is still installed and runnable on
demand — only the unattended daily run is gone.

**Why it was delivering nothing.** `/etc/default/aide` has **`COPYNEWDB=no`**, so every run built a
fresh database and then *discarded* it. The baseline `/var/lib/aide/aide.db` was therefore frozen at
**2026-02-22** while the machine had ROS2 packages rebuilt, Nav2 + slam_toolbox installed, OrbbecSDK
compiled and kernels updated. Result: a **304,817-line** diff of entirely expected change on every
run (`aide.log` 20 MB, exit code 7). Unreadable ⇒ nobody read it ⇒ a real intrusion would have been
invisible inside it. The staleness was a *setting*, not neglect.

**What it cost.** A saturated core for **~3.5 h/day** (2026-07-26 run: 09:19 → 12:51) plus heavy SD
hashing I/O, firing whenever the timer happened to land — on 07-26 it collided with camera work.
Load 4.69 → 2.98 after disabling. SD wear matters here: the card is the companion's single point of
failure and logs have twice run away on this box.

**Reasoning for disabling rather than fixing.** File-integrity monitoring assumes a frozen
filesystem; this one is under active development, so re-baselining after every change would never
realistically happen (evidence: it didn't, for 5 months). The realistic failure modes on this
platform are power brownouts, loose FFCs, USB budget and config drift — not intrusion; the box is
reachable only over WFB + the relay tunnel. And **`system_files_sync` already covers the real need**:
it git-tracks the `/etc` files that matter, with diffs a human can actually read. (Its own weakness —
skipping entirely when the FC reports armed — is worth fixing on its own merits.)

**What was done:** run allowed to finish cleanly (`Result=success`, exit 0) → fresh 134 MB db
promoted to `aide.db` → February baseline preserved as **`/var/lib/aide/aide.db.feb22.bak`** (117 MB,
delete when comfortable) → timer disabled. So a manual run now reports real change, not 5 months of
noise: `sudo nice -19 ionice -c3 aide --check`.

**⚠️ IF EVER RE-ENABLED: set `COPYNEWDB=yes` in `/etc/default/aide` at the same time**, or the
baseline goes stale again exactly as before. Also add `Nice=19` + `IOSchedulingClass=idle` to
`dailyaidecheck.service` so it can never compete with the autonomy stack.
Accepted tradeoff of the promotion: today's filesystem is now the known-good baseline, so anything
altered between Feb and Jul is baked in — acceptable given nothing was being caught anyway.
