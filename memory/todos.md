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

### 4. Check GS adapter TX power (Relay station)
Uplink (GS→Drone) has severe packet loss (1-7 pkt/s constant) vs downlink which is fine.
Asymmetry may indicate GS TX power too low.
```bash
iw dev wlx00c0cab6db3b info
```

### 6. vision_streaming node: no ffmpeg watchdog (added 2026-07-19)
Node started ffmpeg against a bad device (Orbbec depth node, no MJPG), ffmpeg died instantly
and sat as a zombie for ~1h while the service stayed "active" — FPV feed silently dead.
Fix in vision_streaming_node: reap child, detect exit, log ERROR + retry/backoff (or exit so
systemd Restart= recovers). Repro: point camera_name at a non-MJPG node.

### 7. Bring up Orbbec Gemini 336L autonomy pipeline (phase 3 prep, added 2026-07-19)
Camera enumerated on BOX-B USB3 (video0=depth Z16, video6=color; by-id usb-Orbbec_R__...).
Install OrbbecSDK_ROS2 wrapper → publish depth/pointcloud → feed obstacle avoidance
(obstacle_distance to PX4). Orbbec is autonomy-exclusive; FPV = LG cam (see MEMORY [SENSORS]).

### 8. Update G-Control camera presets for new camera layout (added 2026-07-19)
front-switch/bottom-switch/split presets in PXLABS_qgroundcontrol (pxlabs_cli) still send
/dev/video0 & /dev/video2 = now Orbbec depth/IR → dead feed if pressed. Repoint presets to
by-id paths (LG FPV = usb-EBP...LG_Smart_Cam...-video-index0; Orbbec color index0 if ever needed).
Also check CH9 RC camera switching (rc_control_node) for the same stale devices.
Optional companion-side guard: vision_config_manager reject devices with no MJPG/YUYV format.
Can ride along with TODO #5 (same repo).
Stale-device locations found 2026-07-19 (all still reference the removed front/bottom cams):
- ros2_ws/src/rc_control/camera_sw_params.yaml:10-11 (front=/dev/video0, bottom=/dev/video2)
- ros2_ws/src/rc_control/config/rc_mapping.yaml:55-56 (same)
- ros2_ws/src/optical_flow/optical_flow/optical_flow_node1.py:36 (/dev/video2 = now Orbbec IR)
- ros2_ws/src/optical_flow/optical_flow/optical_flow_node.py:36 (/dev/video3 = now Orbbec IR)
Open question for user: with only ONE FPV cam (LG), what should RC CH9 front/bottom/split mean now?
