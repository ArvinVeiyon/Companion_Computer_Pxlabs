# TODO List
> Tasks to perform AFTER full OS backup of both drone and relay station.

---

## [WFB-NG FIXES] — do after OS backup

### 1. Fix GS clock / NTP for real (Relay station vind-rly) — RECURRED 2026-07-11
2026-03-15 fix (`timedatectl set-ntp true` + restart timesyncd) did NOT hold: relay has no RTC and no internet uplink, so `systemd-timesyncd` can never reach `ntp.ubuntu.com` (DNS/network unreachable) and clock drifts to boot-default every power cycle.
Real fix needs a **local NTP server** the relay can actually reach — companion (10.5.5.87) is reachable from relay (10.5.5.77) over the WFB tunnel and has real internet+correct time. Plan: install `chrony` on companion in server mode, allow 10.5.5.0/24, then point relay's `systemd-timesyncd` `NTP=` at 10.5.5.87.
Attempted 2026-07-11, aborted mid-install — see `project_relay_ntp_setup.md` and `project_companion_network_degraded.md`.

### 2. Disable drone onboard Wi-Fi (wifi0, ex-wlan0) during WFB-NG operation (Drone)
Onboard uplink renamed wlan0 → `wifi0` on 2026-07-19 (see feedback_wlan0_persistent_name.md).
`wifi0` connected to "Nilan" 5GHz AP — possible interference with WFB-NG on ch 157.
First verify channel:
```bash
iw dev wifi0 link | grep freq
```
If 5GHz, disable:
```bash
sudo ip link set wifi0 down
```
Consider making this persistent (disable wifi0 in netplan or add pre-start to wifibroadcast service).

### 3. Increase WFB ring buffer on GS OR reduce drone video bitrate (Relay station)
Root cause: GS wfb-server crashes with BlockingIOError EAGAIN (socket buffer overflow).
19 service restarts observed → each causes "New session detected" + decrypt errors + uplink loss spikes.
Option A — increase rx_ring_size in /etc/wifibroadcast.cfg on relay (currently 2MB, try 4-8MB).
Option B — reduce drone video bitrate in /etc/vision_streaming.conf.

### 5. Fix channel reference in PXLABS_qgroundcontrol docs (local edit + push)
ARCHITECTURE.md and DEVELOPMENT.md both say `ch157` — correct value is **ch161**.
Clone repo, search `ch157` / `channel 157`, replace with `ch161` in both files, then push.
Repo: https://github.com/ArvinVeiyon/PXLABS_qgroundcontrol (branch: master)

### 4. Check GS adapter TX power (Relay station) — NOW MEASURED, WORSE THAN THOUGHT (2026-07-20)
Uplink is not merely lossy, it is **dead for commands**: 8 MAVLink commands injected at the relay
reached the drone **0 times** (a sniffer on the companion router confirmed zero arrivals), while the
identical test on the companion locally succeeded 6/6. Downlink also delivers only **~15%** of offered
telemetry (176 kbit/s offered → 26 kbit/s at the relay, uniform thinning across every message type).
This is the real cause of QGC showing "Unknown <number>" instead of mode names, and it blocks all
QGC-side arming/mode/param work. Full detail + next diagnostic steps: `project_gcs_link_degraded.md`.
Asymmetry may still indicate GS TX power too low.
```bash
iw dev wlx00c0cab6db3b info
```

### 6. vision_streaming node: no ffmpeg watchdog — ✅ DONE 2026-07-19
Watchdog implemented + verified live (ros2_ws a561e93, multicam upgrade phase B):
child reaped, ERROR logged, restart with 2s→30s backoff. Stream death is never silent now.

### 7. Bring up Orbbec Gemini 336L autonomy pipeline (phase 3 prep, added 2026-07-19)
Camera enumerated on BOX-B USB3 (video0=depth Z16, video6=color; stable id
usbcam-2bc50807-CPC7B53000AB-i04 for color — by-id is dead, see multicam v2.1).
Install OrbbecSDK_ROS2 wrapper → publish depth/pointcloud → feed obstacle avoidance
(obstacle_distance to PX4). Orbbec is autonomy-exclusive; FPV = LG cam (see MEMORY [SENSORS]).

### 8. Camera preset/RC migration — QGC half ✅ DONE, companion half = multicam Phase D
QGC presets: DONE 2026-07-19 (phase C — hardcoded video0-3 picker + front/bottom buttons
replaced by dynamic camera-list/alias UI; guard implemented in v2.0, discovery fixed v2.1).
REMAINING (Phase D, companion, go-ahead given — see project_vision_multicam_upgrade.md):
migrate to aliases/usbcam ids via v2.1 resolver:
- ros2_ws/src/rc_control/camera_sw_params.yaml:10-11 (front=/dev/video0, bottom=/dev/video2)
- ros2_ws/src/rc_control/config/rc_mapping.yaml:55-56 (same)
  → CH9 plan per design doc: low=FPV primary, mid=FPV+NAV-COLOR PiP, high=spare
- ros2_ws/src/optical_flow/optical_flow/optical_flow_node1.py:36 (/dev/video2 = Orbbec IR)
- ros2_ws/src/optical_flow/optical_flow/optical_flow_node.py:36 (/dev/video3 = Orbbec IR)
  → make device a ROS param (id/alias); WHICH camera optflow should use = open user
    decision (its original camera was physically removed).
Then cleanup: delete /etc/udev/rules.d/99-usb-cameras.rules (dormant pins for removed cams).

---

## [ROVER AUTONAV] — added 2026-07-20 (see project_rover_autonav.md)

### 9. Set RO_SPEED_LIM — THE forward-drive blocker, one param  ← highest value / lowest effort
`RO_SPEED_LIM` is **0.01 m/s**, and `DifferentialSpeedControl.cpp:119` clamps every speed setpoint to
±that. This is why AutoNav forward produced identical output at 0.2 and 0.4 m/s and only one wheel
crept. Manual RC drives all four wheels fine, so nothing is wrong with the hardware.
```
param set RO_SPEED_LIM 1.0     # just above autonav_mode's own 0.8 m/s clamp; 3.0 = RO_MAX_THR_SPEED
param save
```
Then re-run the forward test **on the floor** (a wheels-up bench cannot close the speed loop).

### 10. Restart mavlink.router — FC heartbeat lost from tcp:5760 (2026-07-20)
Several `mavlink_shell.py` sessions wedged the MAVLink path: the FC heartbeat is gone from
`tcp:127.0.0.1:5760`, only a GCS-type heartbeat (sys 255) remains, and param reads stopped answering.
**DDS is unaffected** so autonav work continues, but **QGC cannot connect** until this is cleared.
```
sudo systemctl restart mavlink.router
```
Verify: a heartbeat from sys 1 comp 1 reappears on tcp:5760.

### 11. Run autonav_mode as a systemd service with Restart=always
The px4_ros2 4 s FMU watchdog has aborted the node repeatedly, including with no MAVLink load. Without
supervision an abort silently drops the custom mode and the FC falls back to Hold.

### 12. Map an RC mode channel (RC_MAP_FLTMODE is 0)
No mode channel is assigned on the FC, so AutoNav cannot be selected from the transmitter at all —
only by DDS/GCS command. Set `RC_MAP_FLTMODE=<channel>` + `COM_FLTMODEx=100` (External Mode 1) in QGC.
Observed stick mapping (2026-07-20): ch2 = forward/reverse throttle, ch4 = steering, ch3 unused.

### 13. L4/L5 installs — Orbbec SDK + Nav2 + slam_toolbox (all sudo)
Nothing is installed yet; the Gemini 336L itself is fine (USB3, 5000 Mbps, device nodes free).
See `project_l4_gemini_nav2_prereqs.md` for the full list. Watch disk: **82% used, 11G free**.

### 14. Rotate the GitHub PAT embedded in the codex-work remote URL
`~/codex-work/.git/config` holds a plaintext `ghp_...` token. Rotate it and switch that remote to SSH.
See `project_codexwork_token_in_remote.md`.
