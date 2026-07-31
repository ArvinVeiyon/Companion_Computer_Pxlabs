# TODO List
> Tasks to perform AFTER full OS backup of both drone and relay station.

---

## 🔴🔴 [WFB-NG — HIGH PRIORITY] — added 2026-07-30, WORK THIS BLOCK FIRST
> Measured, not theorised. Raw numbers: [[reference_wfb_ng]]. **Read W0 before touching anything.**

### ⚡⚡ 2026-07-31 RESOLUTION — most of this block is now CLOSED. Read this first.
A **20 min simultaneous both-ends run under full video load** settled it. Numbers: [[reference_wfb_ng]].

**THE ONLY WFB ACTION LEFT: 🔴 reseat/replace the drone's NIC-A ant0 u.FL + pigtail + antenna.**
It is ~20 dB deaf (−48.5 vs −28.3 dBm, steady over 224 samples / 20 min). The GS reads both its
antennas identical, so the defect is on the **drone's RX side** — exactly the direction that loses
packets. Re-measure via 8102 immediately after.

| CLOSED 07-31 | verdict |
|---|---|
| **W1** (GS EAGAIN socket overflow ⇒ 15% downlink) | ❌ **DEAD + DELETED.** Tested at 3.2 Mbit/s video + telemetry for 20 min: relay lost **4 video blocks of 341 057**, `wfb-server` PID 696 stable, `NRestarts=0`, zero EAGAIN. |
| **W2.1** trim MAVLink rates | ❌ **DELETED as a fix.** Downlink already delivers ~100%. Buys airtime only; cannot touch the uplink loss or CPU. |
| **W2.2** raise GS `rx_ring_size` (todo #3) | ❌ **DELETED** — nothing is overflowing. Leave at 2 MB. |
| **W2.3** re-measure 176→26 kbit/s | ✅ **DONE — it does not reproduce.** Downlink is 99.86-99.99%. |
| **W2.4 / #6** hardcoded peer `10.5.6.50` | ✅ **CORRECT.** QGC laptop on the relay's Wi-Fi Direct hotspot (`p2p-wlan0-0`, SSID `vind_rely`, ch149, relay 10.5.6.101/24). **Ping fails = Windows firewall, NOT a break.** |
| **todo #4** GS TX power | ❌ **CLOSED — already maxed at 30 dBm** (`wifi_txpower=3000`, regdom BO permits 30). Nothing to turn up. |
| **W3** antenna imbalance | 🔴 **PROMOTED TO ROOT CAUSE — and corrected: only NIC-A is bad. NIC-B is 3 dB, not 9 dB.** |

**Still open beyond the antenna:** (a) uplink GS→drone loses **13.57%** of MAVLink payload /
**5.46%** tunnel, continuous not bursty — expected to improve when the antenna is fixed, re-measure
before doing anything else; (b) relay TX to the laptop at **31 dBm on ch149** shares a chassis with
the WFB RX on ch161 — possible co-located desense, untested; (c) `journalctl -u wifibroadcast@gs`
still unread — **`vind-admin` is in `sudo` but sudo needs a password**, so journald hides the unit.

⚠️ **Method note that cost a week:** compare payload **`tx.incoming` → `rx.out`** across the two
APIs. Do NOT use `rx.all` (the drone double-counts across 4 antennas — makes 13.6% look like 2.4%),
and do NOT infer radio health from MAVLink message rates at two `tcp:5760` endpoints (that path
includes mavlink-router and PX4 stream config — it is what produced the bogus "15% downlink").

### W0. ⛔ FIRST PRINCIPLE — the drone radio is HEALTHY. Stop blaming WFB by default.
First real link measurement (07-30, WFB JSON API on `127.0.0.1:8102`):
- **0 dropped / 0 truncated / 0 fec_timeouts over 117,570 video packets** (whole session, cumulative)
- TX latency 6-35 us avg, 361 us worst | RF temps 32-39 C | `throttled=0x0`
- **~34% airtime** of a 13 Mbit/s MCS1 PHY (~367 pkt/s, ~3.9 Mbit/s injected) — headroom exists
- `mavlink tx`: offers 179 kbit/s, injects 549 kbit/s (k=1/n=3), **drops NOTHING**

**When video breaks, WFB is sitting on an EMPTY input queue.** The 07-30 session proved the FPV
outage was a dead camera while the radio was flawless. **Suspect the source before the link.**
How to check in 5 s: TCP-connect `127.0.0.1:8102`, read newline-delimited JSON, look at
`video tx . packets.incoming[0]`. If it is 0/s, the radio is fine and the camera is dead.
(Counters are `[per_second, cumulative]`. Do NOT use the `wfb-cli` TUI for this.)

### W1 + W2. ❌ DELETED 2026-08-01 — the whole "GS is the bottleneck" theory was WRONG.
Everything that hung off it is gone: the EAGAIN/socket-overflow hypothesis, the `rx_ring_size`
raise, the MAVLink-rate trim as a *fix*, and the fix-order list. All disproved by the 07-31 run
(see the resolution box at the top). **Do not reconstruct them.** One-line guards only:
- **Never raise `rx_ring_size`** — nothing overflows (4 blocks lost of 341k, PID stable, 0 EAGAIN).
- **Never trim MAVLink rates to "fix" a link problem** — downlink already delivers 99.86-99.99%.
  It only ever buys *airtime* (~13% of a link at ~34% use), and it cannot touch the uplink loss
  (uplink is ~1.4 pkt/s) or CPU (mavlink-router isn't even in the top 8 processes).

### W3. 🔴🔴 RX antenna imbalance — **ROOT CAUSE, and it is ONE chain on ONE card** (rev. 07-31)
20 min / 224 samples, steady throughout ⇒ **not a fade**:

| chain | avg rssi | verdict |
|---|---|---|
| NIC-A **ant0** | **−48.5 dBm** (min −55) | 🔴 **20.2 dB down — FIX THIS** |
| NIC-A ant1 | −28.3 dBm | healthy |
| NIC-B ant256 | −35.0 dBm | 3.0 dB gap, acceptable |
| NIC-B ant257 | −32.0 dBm | healthy |

**⚠️ Corrects the 07-30 table above: NIC-B is 3 dB out, NOT 9 dB. Only NIC-A ant0 is broken.**
The GS reads **both** its own antennas identical ⇒ the defect is **entirely on the drone's RX
side** — which is exactly the direction losing packets (13.57% uplink MAVLink loss vs 0.14%
downlink). 20 dB ≈ 10× range. **Action: reseat u.FL on NIC-A ant0, check pigtail + antenna, then
re-measure on 8102.** This is the whole remaining WFB job.

### W4. ✅ DONE 2026-07-31 — GS-side evidence gathered (except the journal)
GS `rx` stats pulled from API **8103** and paired against the drone's 8102: **W1 killed, downlink
proved healthy, root cause localised to the drone antenna.** See the resolution box above.
❌ **Journal still unread**: `vind-admin` is in group `sudo` but **sudo requires a password**, so
journald returns "No entries" + an insufficient-permissions warning. Needs the password (or the
user runs `journalctl` by hand). Low value now that W1 is dead — only worth it if EAGAIN returns.

### W5. MTU margin is thin (hardening, no live fault)
`radio_mtu = 1445`; ffmpeg RTP averages 1354 B and `truncated=0` over 117k packets. But ffmpeg's RTP
default `pkt_size` is **1472 (> 1445)** with no guaranteed margin. Pin `-pkt_size 1400` when the
vision-node flags are applied (session item 3).

### W6. Radio headroom is now MEASURED — unblocks the 07-28 bitrate item
That item recorded headroom as "NEVER MEASURED". It is now: **~34% airtime used of a 13 Mbit/s MCS1
PHY.** There IS room to raise video bitrate — go straight ahead; the old "trim MAVLink first"
precondition is deleted (it was never a fix). ⚠️ But note the real constraint is **CPU, not radio**:
software x264 already needs ~80-95% of a core, see [[project_ffmpeg_hung_alive_gap]].

---

## [WFB-NG FIXES] — do after OS backup

### 1. Fix GS clock / NTP for real (Relay station vind-rly) — RECURRED 2026-07-11
2026-03-15 fix (`timedatectl set-ntp true` + restart timesyncd) did NOT hold: relay has no RTC and no internet uplink, so `systemd-timesyncd` can never reach `ntp.ubuntu.com` (DNS/network unreachable) and clock drifts to boot-default every power cycle.
Real fix needs a **local NTP server** the relay can actually reach — companion (10.5.5.87) is reachable from relay (10.5.5.77) over the WFB tunnel and has real internet+correct time. Plan: install `chrony` on companion in server mode, allow 10.5.5.0/24, then point relay's `systemd-timesyncd` `NTP=` at 10.5.5.87.
Attempted 2026-07-11, aborted mid-install — see `project_relay_ntp_setup.md` and `project_companion_network_degraded.md`.

### 2. 🔴 STILL OPEN — Disable drone onboard Wi-Fi (Drone) — FAILED VERIFICATION 2026-07-30
**Twice marked done, twice wrong.** Reboot check finally ran (boot 07-30 22:41:45): `brcmfmac` +
`brcmfmac_wcc` **still loaded**, bound via sdio, radio live as **`wlan1`** on wiphy0 at
**ch34 / 5170 MHz**. DOWN (netplan doesn't configure it) so not beaconing, but initialized.
**Root cause: wrong overlay name for this board.** `/boot/firmware/overlays/` contains BOTH
`disable-wifi.dtbo` and **`disable-wifi-pi5.dtbo`** — the Pi 5 needs the **`-pi5`** variant.
The 07-26 inline-comment fix was correct and is intact; the directive itself is just wrong.
**FIX (not applied, needs a reboot to verify):** `dtoverlay=disable-wifi-pi5`, or blacklist
`brcmfmac` at driver level (cannot be silently ignored by firmware). `rfkill` not installed.
⚠️ **Verify with `lsmod | grep brcmfmac` returning EMPTY — not `ip link show wlan0`.** The interface
renamed to `wlan1`, so a wlan0-keyed check falsely passes. Detail: project_external_wifi_uplink.md.
Uplink meanwhile = external USB RTL8821CU `wlx90de80d824d6` @ static 192.168.1.240, working.

### 3. ❌ DELETED — "increase WFB ring buffer on GS". Disproved 07-31, do not do this.
Nothing overflows: 4 video blocks lost of 341 057, `wfb-server` PID stable, `NRestarts=0`, zero
EAGAIN, under the exact video+telemetry load the theory predicted. **Leave `rx_ring_size` at 2 MB.**
(July's 19 restarts were real but are not recurring; if `EAGAIN` ever returns, get the relay journal
— still needs the sudo password.)

### 5. Fix channel reference in PXLABS_qgroundcontrol docs (local edit + push)
ARCHITECTURE.md and DEVELOPMENT.md both say `ch157` — correct value is **ch161**.
Clone repo, search `ch157` / `channel 157`, replace with `ch161` in both files, then push.
Repo: https://github.com/ArvinVeiyon/PXLABS_qgroundcontrol (branch: master)

### 4. Check GS adapter TX power — ❌ CLOSED 2026-07-31. IT IS ALREADY AT MAXIMUM.
`wifi_txpower = 3000` in `/etc/wifibroadcast.cfg`; `iw dev wlx00c0cab6db3b info` reports
**30.00 dBm**; regdom **BO** permits 30 dBm across 5735-5835 MHz. **There is no power to add.**
The downlink half of this item is also dead — it delivers ~100%, not 15% (that was a measurement
artifact, see the resolution box at the top). The uplink half is real but its cause is the **drone's
NIC-A ant0 antenna**, not GS power. → [[reference_wfb_ng]], [[project_gcs_link_degraded]]

<details><summary>original 07-20 record (superseded)</summary>
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
**⛔ UPDATE 2026-07-30 — TX power is probably NOT the answer; deprioritise it.** First real link
measurement (WFB JSON API on 8102) at **−28 dBm, 29 dB SNR on a bench link**: `mavlink rx` lost
**109 / 4884** blocks and FEC recovered only **27**. MAVLink runs **k=1/n=3 — three full copies of
every block** — so losing all three at point-blank range means **burst loss (interference or a
starved GS transmitter), NOT link budget.** More power does not fix burst loss.
**Check these first instead:** (a) the hardcoded GS peer `10.5.6.50:5600/:14550` in
`/etc/wifibroadcast.cfg` — wrong-IP looks exactly like "WFB broken"; (b) the onboard brcmfmac radio
still live at ch34 (todo #2); (c) the RX antenna imbalance below. → `reference_wfb_ng.md`
</details>

### 6. vision_streaming node: no ffmpeg watchdog — ✅ DONE 2026-07-19
Watchdog implemented + verified live (ros2_ws a561e93, multicam upgrade phase B):
child reaped, ERROR logged, restart with 2s→30s backoff. Stream death is never silent now.

### 7. Bring up Orbbec Gemini 336L autonomy pipeline — ✅ WRAPPER + /scan DONE 2026-07-21
OrbbecSDK_ROS2 built (@ec6bc22, Release) and verified live: SDK 2.9.3 over USB3.2, depth 848x480@30,
`/camera/depth/{image_raw,points}`, and **/scan @ 20-21 Hz** via `~/ros2_ws/launch/depth_to_scan.launch.py`.
Bring-up: `ros2 launch orbbec_camera gemini_330_series.launch.py`. Wrapper publishes its own TF tree
from `camera_link` — never re-publish those frames. See `project_l4_gemini_nav2_prereqs.md`.
STILL OPEN here: feeding obstacle_distance to PX4 (the original phase-3 goal) — /scan exists but is
not yet wired to PX4 or Nav2. Orbbec stays autonomy-exclusive; FPV = LG cam (see MEMORY [SENSORS]).

### 8. Camera preset/RC migration — QGC half ✅ DONE, companion half = multicam Phase D
QGC presets: DONE 2026-07-19 (phase C — hardcoded video0-3 picker + front/bottom buttons
replaced by dynamic camera-list/alias UI; guard implemented in v2.0, discovery fixed v2.1).
REMAINING (Phase D, companion, go-ahead given — see project_vision_multicam_upgrade.md):
migrate to aliases/usbcam ids via v2.1 resolver:
- ros2_ws/src/rc_control/camera_sw_params.yaml:10-11 (front=/dev/video0, bottom=/dev/video2)
- ros2_ws/src/rc_control/config/rc_mapping.yaml:55-56 (same)
  → CH9 plan per design doc: low=FPV primary, mid=FPV+NAV-COLOR PiP, high=spare
- ros2_ws/src/optical_flow/optical_flow/optical_flow_node1.py:36 (/dev/video2)
- ros2_ws/src/optical_flow/optical_flow/optical_flow_node.py:36 (/dev/video3)
  → make device a ROS param (id/alias); WHICH camera optflow should use = open user
    decision (its original camera was physically removed).
  ⚠️ The "= Orbbec IR" annotations on those paths are NOT reliable — the Orbbec only owns
  /dev/videoN while `rover-camera.service` is STOPPED. With the wrapper running these paths
  hit whatever else is there (or nothing). The reason to migrate is that /dev/videoN is
  unstable, full stop — not that it specifically lands on the Orbbec.
✅ Cleanup DONE 2026-07-27: /etc/udev/rules.d/99-usb-cameras.rules **RETIRED IN PLACE**, not
deleted — the file now contains only a comment block explaining why (and a pointer to the
still-stale rc_control paths above). Repo copy restored in codex-work `b80034b` after
`d64850d` committed it empty.

### 8b. Vision open items — added 2026-07-28 (audit found these tracked NOWHERE)
From [[project_ffmpeg_hung_alive_gap]]; all three were agreed/designed but never filed:
- **(a) backoff reset on the stall path** — `ros2_ws/src/vision_streaming/vision_streaming/
  vision_streaming_node.py:325-326` still resets `backoff_s` to 2 s after a run >60 s that
  **ended in a stall**. Longer waits are what actually recover the camera (16 s → 256 s of
  good video; 2 s → 14 s, dead), so the node earns a working delay and throws it away.
  Agreed fix = do NOT reset on the stall path. **STILL UNAPPLIED, re-verified live 07-30.**
  Item 2 of that list (settle delay with the device closed after a kill) is also unapplied.
  - **❌ CLOSED 2026-07-30 — item 3 (escalate to a USB port reset of 6-2 after N consecutive
    zero-frame starts) is NOT VIABLE. Do not build it.** Measured against a live-wedged LG:
    uvcvideo unbind/rebind → 0 frames; full USB de-authorize/re-authorize → 0 frames;
    retry at 640x480 → 0 frames; GStreamer → 0 buffers. **No software reset recovers this
    camera** — only physical VBUS removal. Replace the idea with: cap consecutive cold-start
    failures, then log a clear "camera requires physical replug" ERROR instead of looping
    silently for 20 minutes. → [[project_ffmpeg_hung_alive_gap]]
- **(b) USB autosuspend** — `/sys/bus/usb/devices/6-2/power/control` is still `auto`
  (2000 ms). Pin to `on` via udev. "Fix regardless" per the 07-27 evening finding.
  **Priority DOWN 07-30**: hygiene only, already tested and NOT a cause, and the camera on 6-2
  has since been swapped. Do it if a udev rule is being written anyway; don't make a job of it.
- **(c) vision_config_manager v2.3.0 — bitrate control** (feature, not a fix; user's idea,
  agreed, designed, NOT started). Companion half: optional `--bitrate` on `set-cam-params`
  (MUST stay optional — the shipped QGC build calls it without); `update_cam_params_config()`
  gains `bitrate=None`; `list --json` gains `active.settings.{primary,secondary}` so QGC can
  prefill. QGC half is theirs. Constraint: video FEC is k=8/n=12 (50% overhead) and **radio
  headroom has never been measured** — measure before recommending a value. Cheaper first
  lever, also unmeasured: `-preset ultrafast` → `veryfast` (better quality at the SAME
  bitrate, zero extra radio load). Test one lever at a time.
  ⚠️ Do NOT hand-edit the conf as a workaround — [[feedback_camera_qgc_only]].

---

## [ROVER AUTONAV] — added 2026-07-20 (see project_rover_autonav.md)

### 9. Set RO_SPEED_LIM — ✅ DONE 2026-07-21 (0.01 → **0.70**, saved + readback-verified)
Was THE forward-drive blocker: `DifferentialSpeedControl.cpp:119` clamped every speed setpoint to
±0.01 m/s, so 0.2 and 0.4 m/s produced identical wheel speeds. 0.70 deliberately sits *below*
`autonav_mode`'s own 0.8 m/s clamp → the FC is the binding cap; also above the ~0.58-0.60 m/s the
drivetrain actually reaches. Floor re-test is now item 18.

### 10. Restart mavlink.router — ✅ RESOLVED 2026-07-21 (companion reboot healed it)
FC heartbeat is back on `tcp:127.0.0.1:5760` (sys 1 comp 1, autopilot=12, type=10); QGC connects again.
**Lesson kept**: read params with pymavlink `PARAM_REQUEST_READ` — it does NOT re-wedge the link, unlike
`mavlink_shell.py`, which is what wedged it originally.

### 11. autonav_mode under systemd with Restart=always — ✅ DONE 2026-07-21
`rover-autonav-mode.service`, plus rover-camera / rover-scan / rover-odometry. See `reference_services.md`.

### 12. Map an RC mode channel — ✅ ALREADY DONE (verified 2026-07-21, earlier note was stale)
FC actually reads `RC_MAP_FLTMODE=6`, `RC_MAP_ARM_SW=5`, `RC_MAP_KILL_SW=8`, `NAV_RCL_ACT=6` (disarm on
RC loss). The old "RC_MAP_FLTMODE=0 / nothing mapped" record was wrong — user was right all along.
Kill/arm/disarm physically tested and working. Stick map: ch2=throttle, ch4=steer, ch3 unused.

### 13. L4/L5 installs — Orbbec SDK + Nav2 + slam_toolbox — ✅ DONE 2026-07-21
All installed: Nav2 **1.3.12** + nav2-bringup, slam_toolbox **2.8.5**, all 7 build deps, Orbbec udev
rule. Disk pressure also resolved: **85% → 49%, 29G free** after reclaiming 20.4 GB (17.85 GB of
pre-2025 `~/.ros/log` debris + 1.7 GB journal + 569 MB apt cache). SD card is fully partitioned; the
64GB-vs-58G gap is GB-vs-GiB + ext4 overhead, not lost space.

### 15. Measure the camera mount TF — ✅ DONE, **RE-MEASURED AS-BUILT 2026-07-27** (ros2_ws `f210102`)
⚠️ The 07-21 figures (`0bd5bf6`: x −0.125, y 0, z 0.420, zero rpy) are **SUPERSEDED** — the camera
was physically remounted 07-26 on a printed bracket. Current truth = the `depth_to_scan.launch.py`
defaults: **cam_x 0.00** (camera now sits ON the rotation centre), **cam_y 0.00**, **cam_z 0.305**
(0.235 plate + 0.070 bracket), **cam_pitch 0.0406** (2.33° nose down), **cam_roll 0.0100**,
range_max 5.0. Pitch/roll **measured from the camera's own IMU** (`/camera/accel/sample`) on flat
floor, not assumed. Baked in as launch defaults.
STILL OPEN from L4 acceptance: the **tape-measure range check** ("ranges correct vs tape measure" —
only rate and plausibility confirmed so far). Camera is level, so `scan_height: 40` needs no revisit.

### 16. Pin OrbbecSDK_ROS2 in git — ✅ DONE 2026-07-21 (gitignored + documented, ros2_ws b5a9408)
201 MB clone, so not vendored. Repo + exact commit `ec6bc22` + build steps recorded in
`ros2_ws/docs/third_party.md`; `src/OrbbecSDK_ROS2/` added to `.gitignore`. Promote to a real git
submodule when convenient (nice-to-have, no longer blocking a fresh workspace rebuild).

### 17. Delete camera_sw_node_obsolute.py (added 2026-07-21)
`src/rc_control/camera_sw_node_obsolute.py` (node `camera_node_sw`) logged all 18 RC channels at INFO
on every ~50 Hz callback — ~950 lines/s, which is where the 18 GB of `~/.ros/log` came from. It is not
running (live `rc_control_node` is clean) but should be removed so it cannot be launched by accident.
Local edits from the April STL-19 work were saved to `~/codex-work/ldlidar_stl_local_edits_20260417.patch`
when the unused `ldlidar_stl_ros2` clone was removed the same day.

### 18. L2 forward test ON THE FLOOR — ✅ DONE 2026-07-22 (armed, L2 RESULT: PASS)
First-ever armed floor run. All 4 wheels respond to forward+yaw, watchdog zeroes motors, auto-disarm+Hold.
Wheel-0 "reverse" was a FALSE ALARM (mirrored ESC sign; all 4 physically forward — old sign check removed).
ARM WORKFLOW LEARNED: AutoNav can't arm via RC (external mode) → arm in Manual, then software
DO_SET_MODE→AutoNav (holds). `l2_test.py --live` does this, tolerates already-armed-in-Manual start.
Full detail in [[project-l2-floortest-wheel0-reversed]]. Committed+pushed ros2_ws b38e413.

### 19. Test the kill switch INSIDE AutoNav — ✅ DONE 2026-07-22 (confirmed working armed in AutoNav)
User killed the rover mid-AutoNav (first floor attempt) before a wall — kill (ch8) latched, motors stopped.

### 20. Revisit RO_YAW_RATE_P / RO_YAW_RATE_I after the floor test — ← NEXT ACTION (added 2026-07-21)
**FIELD CHECKLIST tracked at `~/ros2_ws/docs/yaw_tuning_session.md` (ros2_ws main @ 8f84bf1)** — preconditions,
bring-up, baseline-then-tune, opportunistic gyro-yaw + /scan checks, safety, teardown, results-log table.
CONFIRMED NEEDED by the L2 run: armed yaw drove wheels MUCH harder (~700-850 rpm) than forward (~156 rpm).
Those gains were tuned while `RD_WHEEL_TRACK` was 0.43 — a ~39% oversized track, which sized the
commanded wheel differential (Δv = ω × track). The allocation they were implicitly compensating for
has changed now that it is 0.31. The gyro-closed rate loop hides much of this in steady state, so
expect the difference mainly in feedforward/transient response. Re-check after a real floor run.

### 22. Reflex collision-stop in AutoNav executor — ✅ DONE 2026-07-22/23 (ros2_ws b38e413, pushed)
Built INSIDE `autonav_mode` (single funnel to motors, can't be bypassed): ±20° front `/scan` cone, block
<0.60m / clear >0.75m hysteresis, stale-scan fail-safe, `collision.*` params, always-on edge-triggered
diagnostic. Validated passively on stands AND fired armed end-to-end (stopped ~0.59m from a real wall).
Doc: `ros2_ws/docs/rover_autonav_collision_stop.md`. This is the safety FLOOR only — real avoidance/
routing/rerouting is L5 (Nav2+slam_toolbox), still to do. Follow-up: widen cone / add side sectors with
Nav2 costmaps; armed wall-stop already proven so no separate proof run needed.

### 21a. Gyro yaw odometry — ✅ IMPLEMENTED 2026-07-21 (ros2_ws 3fdf2fc, pushed)
`rover_odometry` now takes heading from `/fmu/out/vehicle_attitude` (~92 Hz) instead of
`(v_right − v_left)/track`. New params `yaw_source` (default `gyro`, set `wheels` for A/B) and
`attitude_timeout` (0.5 s → auto-fallback to wheels, logged). Integrates yaw **deltas** not absolute
yaw (keeps /odom's own origin, sidesteps NED-vs-ENU); one sign flip since PX4 yaw is +CW from above
and ROS is +CCW; `quat_reset_counter` changes are EKF resets and those deltas are DROPPED, never
integrated; yaw baseline advances even on skipped steps so a bad dt can't become false rotation;
yaw covariance now source-dependent (0.002 gyro vs 0.02 wheels) so Nav2/SLAM weight it honestly.
**Note `/fmu/out/vehicle_angular_velocity` is NOT in this FC's dds_topics.yaml** — attitude is the
only gyro-derived source exposed.
Verified at rest: /odom 98.8 Hz, yaw drift **0.044° over 12 s**, angular.z −0.0004 rad/s.
**STILL TO VALIDATE (needs driving)**: turn the rover a known angle (e.g. 90° or 360° by floor marks)
and compare `/odom` yaw against reality; also A/B against `yaw_source:=wheels` to quantify how bad
the slip error actually was. Do this during the item-18 floor session.

### 21. Use the camera IMU alongside the FC IMUs (user idea, 2026-07-21) — assess before building
The Gemini 336L has its own IMU (`/camera/accel/sample`, `/camera/gyro/sample`; enable with
`enable_accel:=true enable_gyro:=true`, now on by default in `rover-camera.service`). Ranked by
value, honestly:
1. **HIGHEST VALUE, and it does not need the camera IMU at all: replace wheel-derived yaw with
   GYRO yaw in `rover_odometry`.** Skid-steer yaw from wheel speeds is inherently bad — all four
   wheels *must* slip laterally to turn, so `(v_right − v_left)/track` systematically misestimates
   rotation no matter how perfect the track width is. The FC's gyro/EKF yaw is already on DDS
   (`vehicle_attitude`, `vehicle_angular_velocity`) and is far better. Use wheels for forward
   distance, gyro for heading. This is the standard fix for skid-steer odometry and is likely the
   single biggest accuracy win available before SLAM.
2. **Independent cross-check of FC IMU health.** The camera IMU is a genuinely independent gravity
   reference — it is what let the camera mount pitch/roll be measured tonight. Useful for sanity-
   checking accel calibration (cf. the "accel 0 inconsistency" episode), where the FC's own IMUs
   cannot arbitrate between themselves.
3. **VIO (visual-inertial odometry)** — the ambitious option: camera IMU + depth/colour for
   drift-free-ish motion estimation that survives wheel slip entirely. Real payoff for GPS-denied
   nav, but heavy on the RPi5, which already shares compute with vision streaming (`/scan` alone
   drops to ~13-19 Hz under load). Do NOT start here; revisit only after Nav2 works.
4. **Feeding the camera IMU into EKF2 as an extra IMU: not practical.** PX4 EKF2 has no external-IMU
   input path; only external *vision* pose/velocity, which is what `rover_ekf_bridge` already uses.
**Recommendation: do (1) first — it is cheap, principled and helps SLAM immediately. Keep (2) as a
diagnostic. Defer (3). Drop (4).**

### 14. Rotate the GitHub PAT embedded in the codex-work remote URL
`~/codex-work/.git/config` holds a plaintext `ghp_...` token. Rotate it and switch that remote to SSH.
See `project_codexwork_token_in_remote.md`.

---

## [ROVER OUTDOOR — PRIMARY TARGET] — added 2026-07-23 (see ros2_ws/docs/roadmap.md §4, O1-O5)
Goal: rover drives itself to a **GPS waypoint** in open outdoor space, **360° obstacle avoidance**, no
operator. Indoor GPS-denied (L0-L4 done, L5/L6 next) is the stepping-stone + GPS-loss fallback. These
outdoor tasks come AFTER the indoor brain is proven (L5+L6). Both O1 and O2 need hardware the user is fitting.

### O1. Re-integrate the STL-19 360° LiDAR (blocked on getting the unit back)
LDRobot STL-19: 360° 2D, **0.02-25 m, ~10 Hz** LaserScan; UART **ttyAMA3 @ 230400, RX-only** (lidar TX →
RPi RX, no commands); `dtoverlay=uart3-pi5`, TF `base_link→base_laser` 0.18 m (re-measure mount).
- Hardware went to another team 2026-04-17 → **need the physical unit back first**.
- Driver `ldlidar_stl_ros2` (node LD19) already in `ros2_ws/src` with BOTH upstream fixes applied
  (pthread include + hardcoded `/dev/ttyAMA3`). Local edits: `codex-work/ldlidar_stl_local_edits_20260417.patch`.
- Steps: reconnect hw → enable `ttyAMA3` → build → install/enable `ldlidar.service` (unit template in
  `codex-work/ldlidar_stl19_install_guide.md`).
- ⚠️ **`/scan` conflict**: lidar driver AND `depth_to_scan` both publish `/scan`. Fix: **lidar owns `/scan`**
  (SLAM + 360° costmap); remap depth to **`/scan_depth`** as a separate Nav2 costmap layer.

### O2. Integrate the DroneCAN GPS (blocked on module choice + fitting)
- DroneCAN/UAVCAN bus already live (VESC ESCs addr 10-13) → GPS is one more node on it.
- PX4: enable `UAVCAN_ENABLE` (GPS subclass) + set `EKF2_GPS_CTRL` to fuse GPS (**FC param path, MAVLink-only,
  not DDS**). Verify `/fmu/out/vehicle_gps_position` populates + `vehicle_global_position` goes valid.
- Nav2: outdoor GPS nav via `navsat_transform_node` (robot_localization) or Nav2 GPS waypoint follower.
- **Module make/model: TBD — user to confirm** (sets the exact DroneCAN GPS driver params).

### O3. Outdoor 2D-lidar SLAM (builds on L6)
slam_toolbox on the lidar `/scan` (2D-lidar SLAM is far better than depth-derived scan) + fold the 336L
forward depth in as a costmap layer for low/overhang obstacles the flat 2D plane misses.

### O4. Outdoor Nav2 with GPS waypoints (builds on L5)
`navsat_transform` / GPS-waypoint-follower launch config (distinct from the indoor SLAM launch); global
plan to a GPS coordinate, local costmap from lidar+depth, controller → `/cmd_vel` → autonav_mode.

### O5. Outdoor safety hardening (extends L7)
Terrain handling, dynamic obstacles, and **GPS-loss failsafe → wheel/gyro dead-reckoning + reflex stop,
never an uncontrolled state**. Caveat to design around: STL-19 is a **2D** lidar (fixed-height plane) — on
uneven terrain it can miss low obstacles or read a slope as a wall; the forward 3D 336L covers that gap.

## [2026-07-26 SESSION — OPENED / CLOSED]

### Closed today
- ✅ **Companion doc staleness audit.** All 13 non-memory docs checked against live state; 5 had stale
  facts. Fixed + pushed: `codex-work` 3b4b41d + 880787c, `ros2_ws` 1f9ee48 + 03b8634. Biggest ones:
  PX4 firmware still recorded as v1.16.0-rc1/c5b8445 in `system_companion.md` §3 *and* the pinned-commit
  table *and* README (real: pxlabs-v1.17.0-2.0.0 @ a52c38b07d); camera identity still documented as
  `/dev/v4l/by-id` in 3 places (v2.1 replaced it with `usbcam-*` sysfs ids because by-id is not
  boot-stable); README/§18 release tables listed *content* commits instead of the commits the tags
  point at (v1.0.8 a60791f→96816fc, v1.0.9 →9e172fb, v1.1.0/v1.2.0 missing from README).
- ✅ **tfmini disabled** (drone-only sensor; was the real cause of camera degradation — 38% CPU,
  214 log lines/sec, SD thrash). `/scan` 15-19 Hz → **29 Hz**, jitter down 9×.
- ✅ **AIDE daily timer disabled**, fresh db promoted. Was `COPYNEWDB=no` ⇒ Feb-22 baseline ⇒
  304k-line diff per run, ~3.5 h/day of a core.
- ✅ **Journal vacuumed** 3.6 G → 469 M (disk 58% → 53%).
- ✅ **USB/power cleared of blame**: Orbbec at full 5000 Mbps USB3, no resets, no over-current,
  `throttled=0x0`, EXT5V 5.09 V, SoC 63 °C. The XL4015 fix is holding.
- ✅ **Camera mount geometry decided + committed** (cam_x 0 / cam_z 0.305 / range_max 5.0).

### Opened today
1. **Verify `dtoverlay=disable-wifi` after the next reboot** — fix applied 2026-07-26 (inline `#`
   comment was swallowing the overlay name) but NOT yet rebooted. Check `ip link show wlan0` (should
   not exist) + `lsmod | grep brcmfmac` (empty). **TODO #2 stays open until this passes.**
2. **Establish what NIC RELAY-STN actually has.** `wlx90de80d824d6` is on the companion now, so the
   relay's documented uplink is gone and `.221` does not answer. See [[project_relay2_relaystn]].
3. **Fit the printed camera bracket, then run the 4-step as-built check** at the foot of
   `ros2_ws/launch/depth_to_scan.launch.py` (measure to the left IR imager, re-derive pitch/roll from
   `/camera/accel/sample`, restart rover-scan, tape-measure a `/scan` return). **Blocks L5.**
4. **Crop the rover's own deck out of the depth cloud before the L5 Nav2 voxel layer** — at cam_z
   0.305 with cam_x 0 the top plate fills the bottom ~third of the frame (11.5°/83 px). Harmless for
   `/scan` (±20 px band) but Nav2 would mark a permanent obstacle around its own nose.
5. **Profile `wheel_odometry_node`** — 26.9% CPU for 100 Hz arithmetic is high, and it is in the
   autonomy path where L5 will need the headroom. Suspect the same unthrottled per-message logging
   pattern as tfmini / ros2_ws todo #17.
6. **Watch whether the VESCs doze off mid-session.** At rest only ESC 13 stays awake
   (`esc_online_flags 8`); a nudge brings all four (→15). If they can sleep again *while armed*,
   `/odom` would drop out under the EKF bridge. Unknown — check on the first long run.
7. **Delete `/var/lib/aide/aide.db.feb22.bak`** (117 MB) once the Feb baseline is definitely not wanted.
8. **Fix `system_files_sync`'s armed-skip** — it skips entirely when the FC reports armed, so it is
   an unreliable backstop during work sessions (this is how the WFB_NICS mitigation was lost on 07-25).

## 2026-07-28 — camera bitrate control (OPEN, agreed, not started)
Raising the camera to 1280x720 left `bitrate = 2000K`, dropping bits/pixel 0.129 → 0.072
(soft picture). QGC has no bitrate control and the conf must not be hand-edited
(QGC-only rule). Add it: companion = optional `--bitrate` on `set-cam-params` +
`active.settings` in `list --json` (→ v2.3.0); QGC = `--bitrate` through
pxlabs_cli/PXLABSApi/CompanionControl.qml. Full design + constraints (FEC k=8/n=12,
radio headroom UNMEASURED, `-preset veryfast` as a zero-radio-cost alternative) in
project_ffmpeg_hung_alive_gap.md. Stopped here 2026-07-28: usage limit.

---

## [2026-07-30 SESSION] — WFB-ng + vision node deep analysis
> Full detail: [[project_ffmpeg_hung_alive_gap]] (vision) and [[reference_wfb_ng]] (radio).

### Closed / killed today
- ❌ **8b item 3 (USB port-reset escalation) — KILLED, not viable.** See item 8b above.
- ✅ **07-26 opened-item 1 ("verify `dtoverlay=disable-wifi` after next reboot") — VERIFIED, and it
  FAILED.** Wrong overlay name for Pi 5. Folded back into **todo #2, which is REOPENED**.
- ✅ **"Is it ffmpeg / the node / WFB?" — ANSWERED, definitively NO to all three.** The LG camera was
  the fault. ffmpeg, libx264, GStreamer, uvcvideo, USB enumeration, isoc bandwidth, the vision node
  and WFB are all excluded by direct measurement. Stop re-litigating this.
- ✅ **Encoder-swap question (ffmpeg vs GStreamer) — SETTLED: stay with ffmpeg.** Pi 5 has **no
  hardware H.264 encoder** (`v4l2h264enc` missing; `rpivid` is decode-only), so both are software
  x264 at identical cost. ffmpeg's `-progress` is what makes the stall watchdog possible.
- ❌ **"See3CAM only does ~16 fps on the 480M bus" — RETRACTED, it was wrong.** It does a real
  **60 fps** at 720p MJPG over USB 2.0. The 16 fps was auto-exposure in a dark room. **You do NOT
  need a blue USB3 port for full frame rate.** Fix the note in MEMORY [SENSORS] if it resurfaces.

### Opened today
1. **Camera swap — PARTIAL SOAK PASSED, finish it after the mount is made.** See3CAM_CU135 fitted
   07-30 23:14 on port 6-2 and selected from QGC (conf `usbcam-2560c1d1-241D8306-i00`, `fps = 60`).
   **Ran 11 min 49 s continuous: 0 errors, 0 stalls, steady ~200 pkt/s / ~250 kB/s, 0 drops.**
   That **beats the LG's best-ever clean window (9.5 min)** and its 448 s from the same night.
   **Ended by a clean PHYSICAL unplug at 23:50:41, not a fault** — user removed it because it was
   dangling on its cable and is building a proper mount for it.
   **REMAINING: refit on the mount, then 20-30 min untouched + a reboot** to finish the verdict.
   ⚠️ **A packet-flow check is NOT sufficient proof** — see opened-item 9.
   ✅ **2026-07-31 — SOAK PASSED.** Refitted on 6-2 and streamed 1280x720 for a **continuous 41.8 min**
   (21:30:01 → 22:11:48, incl. a 19.8 min instrumented window; ended by a **clean service restart, not
   a fault** — `Deactivated successfully`, the usual QGC-camera-change signature):
   `vision_streaming` PID **38192** unchanged across all 40
   health samples, `NRestarts=0`, ffmpeg alive throughout, **0 errors / 0 stalls / 0 dup-padding**,
   62.6-65.3 °C, `throttled=0x0` on every sample. Downlink delivered **234 331 of 234 362** video
   packets (99.99%) end-to-end at the relay — so the picture genuinely moved, not just RTP.
   **ONLY THE REBOOT CHECK REMAINS.** (Load avg 4-7 on 4 cores from software x264 — high but stable.)
2. **Discriminate LG-faulty vs connector-6-2-bad-under-load.** The swap confounds them: See3CAM
   100 mA vs LG 500 mA. Test = put the LG in the free port **`4-1`** (different host controller and
   power path) and soak. **Blocked: enclosure is assembled.** Do it next time it's open.
3. **Apply the vision_streaming_node.py fixes** (all verified live 07-30, all unapplied):
   - `-g 30` + `-tune zerolatency` + `-pkt_size 1400` — **highest value**; x264 default keyint is
     250 frames ≈ 8.3 s at 30 fps, so one lost keyframe smears for up to 8 s over the radio.
   - wire the `fps` conf key through to `-framerate` (currently read by QGC, **never used**).
   - `frame=0` counts as progress → 30 s grace silently becomes ~50 s.
   - backoff reset on the stall path (= item 8b(a)).
   - `rclpy.shutdown()` RCLError — fires on **every QGC camera change**, dumps a traceback exactly
     when you'd be checking whether the swap worked.
   - cap consecutive cold-start failures → log "camera requires physical replug" instead of looping.
4. **🔴 WFB RX antenna imbalance** — ⚠️ these 07-30 figures are SUPERSEDED; only **NIC-A ant0** is
   bad (−48.5 vs −28.3 dBm) and NIC-B is 3 dB, not 9. See W3 above for the corrected table.
5. ❌ **DELETED 08-01 — "trim PX4 MAVLink stream rates".** It fixes nothing: downlink already
   delivers ~100%. Airtime-only, and headroom is now measured at ~34% of a 13 Mbit/s MCS1 PHY, so
   the video-bitrate item no longer depends on it.
6. **Verify the hardcoded GS peer `10.5.6.50`** in `/etc/wifibroadcast.cfg` (`gs_video` :5600,
   `gs_mavlink` :14550) — fixed IP on a subnet unrelated to the 10.5.5.0/24 tunnel. Wrong-IP
   presents as "WFB broken" while the radio is flawless. Check as part of todo #4.
7. **Boot-time clock is wrong until NTP steps it.** `systemd` claimed services started `Jul 29
   00:31`, `last -x reboot` said `Jul 25 11:36`, `uptime -s` said `Jul 30 22:41:45` — all three
   disagree on the same boot. **Journal timestamps around a boot are not trustworthy**; don't
   correlate a WFB event against a vision event across a reboot without checking. Companion has
   internet + NTP synced, so this is boot-window skew only. Related: [[project_relay_ntp_setup]].
8. **`camera_name` fallback in the conf is dangerous.** `/dev/video0` did not exist for most of
   07-30 (nodes were video8/video9). If sysfs `usbcam-*` resolution ever fails, ffmpeg is pointed
   at a node that is not the camera. Consider failing loudly instead of falling back.
9. **Verification method note (about MY checking, not a hardware bug).** A drone-side packet-flow
   check (`wfb_tx video incoming` ~200 pkt/s, 0 drops) does not by itself prove the picture is
   moving. Confirm at the GS when it matters. **No dup-padding problem has ever been observed on
   the See3CAM** — it ran 11:49 clean and the user saw a normal moving picture throughout.
