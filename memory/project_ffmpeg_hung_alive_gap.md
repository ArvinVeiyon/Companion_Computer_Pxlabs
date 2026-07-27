---
name: project-ffmpeg-hung-alive-gap
description: "vision_streaming ffmpeg watchdog only catches process DEATH, not a hung-but-alive ffmpeg — GS video cuts off silently"
metadata: 
  node_type: memory
  type: project
  originSessionId: 62813ffb-bde2-479e-8734-481ad4a5907b
  modified: 2026-07-27T12:07:47.322Z
---

2026-07-26: GS video cut off with **no service error and no restart**. Root cause: the
LG Smart Cam (`/dev/video0`, usb 6-2, 480Mbps) stopped delivering UVC frames; `ffmpeg`
stayed **alive but stalled** — all x264 threads parked in `futex_wait_queue`, `/dev/video0`
still open on fd 3, CPU fell from ~34% of a core to ~0.5%, and **zero** RTP left for
`127.0.0.1:5602`.

**The gap:** the ffmpeg watchdog added 2026-07-19 (a561e93, see [[reference_services]])
restarts ffmpeg only when the process *exits*. A hung-alive ffmpeg slips straight past it,
so the stream dies silently and stays dead.

**FIXED 2026-07-26** in `vision_streaming_node.py` (built, NOT yet committed) — liveness is
now judged by ffmpeg's own progress counter, not by the process being alive:
- ffmpeg gains `-progress pipe:1 -stats_period 1`; stdout is a **non-blocking** pipe that
  `drain_progress()` empties every 2s tick. **Draining is mandatory** — let the 64K pipe
  fill and ffmpeg blocks writing to it, manufacturing the exact stall being watched for.
- Stall = `frame=` counter frozen for `STALL_TIMEOUT_S`(10s); `STARTUP_GRACE_S`(30s) applies
  until the first frame, since opening a UVC camera is slow.
- Recovery escalates SIGTERM → SIGKILL. **The escalation is required, not defensive**:
  in test a stalled ffmpeg ignored SIGTERM and only died on SIGKILL (it is blocked in a
  read/ioctl). `stop_streaming()` uses the same path so shutdown can't hang forever.
- Verified empirically before writing it: `-progress` emits `frame=N` ~1/s on a live source
  and goes **completely silent** on a stalled input (0 bytes in 10s) — that silence is the
  detection signal. Harness: healthy 20s run = 0 restarts (no false positive); fifo that
  feeds then freezes with the pipe held open = detected in 10s via the stall path.
  Careful with such a test: if the writer closes the fifo, ffmpeg gets EOF and **exits**,
  which exercises the old death path and silently proves nothing.

**How to diagnose fast (all non-root):**
- `python3` → connect `127.0.0.1:8102` (drone wfb API), read the `"video tx"` JSON line.
  `packets.incoming[0] == 0` and `tx_ant_stats == []` ⇒ no video reaching wfb at all.
  Compare against `"mavlink tx"` / `"tunnel tx"` — if those have live counters the radio
  link is fine and the fault is upstream of wfb.
- ffmpeg live vs stalled: `awk '{print $14+$15}' /proc/<pid>/stat` twice 10s apart.
  `ps %CPU` is a **lifetime average** and will look healthy — do not trust it.
- `/proc/net/udp`, port 5602 = hex `15E2`: frozen `drops` + `rx_queue=0` ⇒ nothing arriving.

**Two red herrings ruled out, don't re-chase them:**
1. `wlx782288d993c0` showing 0 pkt/s TX is **NORMAL**, not the dead-NIC problem from
   [[project_wfb_undervoltage_dead_nic]]. `/etc/wifibroadcast.cfg` has `mirror=False`,
   `use_qdisc=False`, `fwmark=0`, so wfb_tx selects **one best NIC** and sends everything
   through it. Both cards were in monitor mode, ch161, 30dBm, `throttled=0x0`, 0 rail dips.
2. NIC `tx_dropped` climbing on the active card was **my own SSH-over-tunnel traffic**,
   not video.

Orbbec Gemini 336L is unaffected: it binds via OrbbecSDK/libusb, **not** uvcvideo, so it
correctly has **no `/dev/videoN`** node — that absence is not a fault. → [[project_l4_gemini_nav2_prereqs]]

Recovery: `sudo systemctl restart vision_streaming` (needs a real sudo tty — the CLI
cannot do it unattended). If the camera itself is wedged, a USB port reset of 6-2 is next.

---

## 2026-07-27 — SEQUEL: the fix's recovery path now flaps the GS feed. **OPEN, agreed to fix later today 07-27.**

User reported "WFB camera feed on and off on GS". **Not the radio.** It is the new
watchdog restarting ffmpeg ~1×/min: **59 ffmpeg starts in 67 min** this boot
(boot 0, 08:26:23). Each cycle = 30-60 s of black then video back.

**The watchdog is HONEST — do not suspect false positives.** Verified: during the
reported stall 09:36:51→09:37:23 an ffmpeg was alive the whole time and wfb
`video tx` `packets.incoming` sat frozen at **119142 for 60 s**. Zero RTP produced.
Only ever ONE ffmpeg alive (no orphan duplicates).

**Ruled out** (don't re-chase): radio link (video tx dropped=0/truncated=0, incoming
climbing when healthy); **power** (`ext5v-report`: mean 5.131 V, min 5.017 V, 0 dips
<4.90 V, throttled=0x0, peak 4.97 A); thermal (60 °C); Orbbec/USB contention (Orbbec
is bus 2 @5 Gbps usbfs, LG cam alone on bus 6 @480 Mbps); `vision_config_manager
list --json` polling every 60 s from G-Control (the healthy 256 s run spanned four
of those calls unharmed).

**Diagnosis — the SIGKILL recovery is re-wedging the camera.** Event shapes tell it:
- first event of the boot `no new frames for 12s after 42s` = saw frames then lost
  them ⇒ a **real** mid-stream camera stall (the original fault, still unfixed).
- nearly every event after is `for 32s after 32s` = `saw_frames` False, ffmpeg opened
  `/dev/video8` and **never got frame 1** (the `STARTUP_GRACE_S`=30 path). That is a
  wedged UVC device, not a camera dying every 60 s.
The OLD code never sent SIGKILL to an ffmpeg holding a live v4l2 stream; `kill_ffmpeg()`
does. Corroborating kernel line: `uvcvideo 6-2:1.1: Failed to resubmit video URB (-1)`,
and `[udp] bind failed: Address already in use` on 5602 (old proc still holding on).

**Backoff bug makes it self-sustaining** — longer waits are what actually recover:
16 s → 256 s of good video; 30 s → 38 s; 2 s → 14 s, dead. But
`vision_streaming_node.py:314` resets `backoff_s` to 2 s after any run >`STABLE_RUNTIME_S`
(60 s) **including a run that ended in a stall** ⇒ it earns a working delay then throws
it away.

**⚠️ "It worked well before the code change" is only half true.** Boot -1 (old code,
21:45→23:26) started ffmpeg **once** and it lived 101 min — but the old code was blind
to hung-alive ffmpeg, so that proves the *process* lived, NOT that video flowed. The
flapping *cadence* is genuinely new; the camera stall itself is not.

**⚠️ SUPERSEDED BY THE 07-27 EVENING TEST BELOW — the "SIGKILL re-wedges the camera"
theory is NOT the root cause. Read the 07-27 evening section first.**

**AGREED FIX LIST (not yet applied):**
1. `vision_streaming_node.py:314` — do NOT reset backoff on the stall path.
2. Add a settle delay with the device closed after any kill (2 s backoff is far too
   short for the camera to be released).
3. Escalate to a **USB port reset of 6-2** after N consecutive zero-frame starts —
   reopening a wedged UVC node can never fix it.
4. (user/root) `/sys/bus/usb/devices/6-2/power/control` = `auto` (2000 ms) → pin to
   `on` via udev.
Commit 1-3 together with yesterday's still-uncommitted watchdog fix in
`~/ros2_ws/src/vision_streaming/`.

**Still-separate underlying cause of the real stall** — untested: `/etc/vision_streaming.conf`
was changed 2026-07-26 17:47 to **960x540**, but the mode the user applied from QGC was
**1280x720** (a native sensor mode; 960x540 is enumerated but odd). Retest at 1280x720
**from QGC only** ([[feedback_camera_qgc_only]]), then cable/port. Camera is
`/dev/video8` this boot (`video9` = its metadata node).

---

## 2026-07-27 evening — CONTROLLED REVERT TEST: the code is exonerated, the camera stalls on its own

Reverted `vision_streaming_node.py` to **`5bace1b`** (death-only watchdog, no `-progress`,
no `kill_ffmpeg`, no SIGKILL — keeps sysfs `resolve_usbcam_id`) and rebuilt. This is
essentially the code that ran fine for months. **It stalls identically.**

Measured on the reverted code (service restart 17:31:20):
- 17:31:22 ffmpeg up on `/dev/video8`; real video flowed end-to-end for ~2.5 min —
  **2469 wfb packets / 12 s, 2.86 MB = 1.9 Mbps** (matches the 2000K bitrate), encoder
  ~45% of a core.
- Then frames stopped. ffmpeg **alive** at 4:37 runtime, **9 CPU ticks + 0 wfb packets
  over 20 s**; `video tx` totals frozen, `tx_ant_stats []`.

**Conclusions that overturn the 07-27 morning diagnosis:**
1. The stall is **NOT caused by the watchdog or by SIGKILL** — it reproduces with neither
   present. SIGKILL-wedging is real but only explains why *recovery* failed.
2. Old code = **one permanently dead feed** (no stall detection). New code = visible
   flapping. Same fault, different presentation. User's "I never had this before" is about
   presentation, not cause.
3. **DON'T repeat this revert as a fix** — it makes the failure silent again.

**Prime suspect now = the resolution change.** conf history from codex-work git:
`07-25 22:52 = 1280x720` (last known-good) → `07-26 16:59 = 960x540` → symptoms begin
07-26. 960x540 is also what emits `mjpeg ... unable to decode APP fields: Invalid data`
at every stream start. Not proof (960x540 appears on 07-11 too) but cheapest test:
**set 1280x720 from QGC only** ([[feedback_camera_qgc_only]]), then watch for >5 min.

**Camera hardware is NOT dead** — proven while wedged: USB still enumerated
(`devnum=2` unchanged, 480 Mbps, 500 mA), **all control transfers on ep0 work instantly**
(every v4l2 control reads back sane values), but the **isoc streaming endpoint delivers
zero frames** — `v4l2-ctl` (not ffmpeg) hung 25 s at both 960x540 and 1280x720. **Zero
kernel uvc/URB errors throughout.** So: alive on ep0, silent on isoc, host controller
happy ⇒ wedged UVC streaming state, not a failed sensor. Marginal cable/connector is
still open for the *initial* stall.

Secondary, fix regardless: `/sys/bus/usb/devices/6-2/power/control` = `auto` @2000 ms —
pin to `on`.

**Gotcha for future measurement:** ffmpeg CPU is **bursty** — a single 8 s sample caught
an idle gap and made a healthy encoder look stalled. Sample **≥20 s**, and cross-check
against the wfb `video tx` `incoming` total delta. Healthy ≈ 900 ticks / ~3500 pkts per 20 s.

State left: node = `5bace1b` in the working tree + index (**HEAD untouched at `2bc841e`**;
`git checkout HEAD -- src/vision_streaming/...` restores the stall watchdog), rebuilt and
installed. Note `install/` is a real copy, not symlink-install ⇒ **always `colcon build`
after editing**. Proposed next build: `2bc841e` minus the SIGKILL escalation (SIGTERM only).

---

## 2026-07-27 late — CONFIRMED BUG: `vision_config_manager` can't write resolution; + final state

**CONFIRMED (this is why "resolution is stuck at 960x540" and QGC changes did nothing):**
`/usr/local/bin/vision_config_manager:575` in `update_resolution_only_config()`:
```python
if "camera_name" in line and device in line:   # in_target
```
The section is matched by **substring of the device path**. The conf's `camera_name` was the
stale pre-Orbbec `/dev/video0` while the camera was `/dev/video8`→`/dev/video0`→`/dev/video1`.
Match fails ⇒ `in_target` never true ⇒ resolution line never replaced, the fallback append at
:582 never fires ⇒ **the file is rewritten byte-identical** (mtime updates, value doesn't),
it prints "updated successfully", then restarts the service at :592. Same
`device in line` pattern in `update_cam_params_config()` (:594). **Fix = match on the stable
`camera_id`, and refresh the stale `camera_name` as a side effect.** NOT fixed by any
vision_streaming node change — different program. → [[project_vision_multicam_upgrade]]

**Consequence:** 960x540 was un-changeable, so "is the resolution the problem?" was never
actually testable. Fix the manager before retesting 1280x720.

**Device numbering — the Orbbec is NOT the cause.** Full v4l2 map taken 2026-07-27:
`video0/1` (later `video1/2`) = **LG Smart Cam, bus 6-2, the ONLY USB video nodes**;
`video19..video37` = **Pi5 on-chip `rpivid` + `pispbe-*` on the `axi` bus** (not cameras).
**Orbbec Gemini 336L has NO `/dev/videoN` at all** (OrbbecSDK/libusb, not uvcvideo) — it
cannot collide with the LG cam at the v4l2 layer. Renumbering comes from the Pi's own ISP
nodes claiming low numbers at boot + USB rebinds. **Corrects the old MEMORY.md claim that
Orbbec owns `video0=depth Z16, video2/4=IR` — that is wrong.**

**NOPASSWD sudo available to `roz`** (from `sudo -n -l`) — no password needed for:
`systemctl {stop,start,restart} vision_streaming`, `cp /tmp/vision_streaming.conf
/etc/vision_streaming.conf`, `tee /etc/vision_streaming.conf`, `cat /etc/vision_streaming.conf`,
`v4l2-ctl`, `dmesg`, `vision_config_manager`, plus `/usr/bin/{systemctl,journalctl,tee,cp}`.
Earlier sessions wrongly assumed the CLI could not restart the service unattended.

**FINAL STATE 2026-07-27 18:19 — user confirms video feed working:**
- node reverted to **`1551b0b`** (the original 125-line version, NO watchdog at all) — built
  and installed. HEAD still `2bc841e`; `git checkout HEAD -- src/vision_streaming/...` restores.
- `/etc/vision_streaming.conf` `camera_name` `/dev/video0`→**`/dev/video1`** (user-authorised;
  the original node has no id resolution and `/dev/video0` did not exist ⇒ would have failed
  instantly with no retry).
- **Orbbec physically unplugged**, `rover-camera` + `rover-scan` stopped. ⚠️ restore with
  `sudo systemctl start rover-camera rover-scan` — **L5/Nav2 work is blocked until then**.
- Verified healthy: cpu ~978-1223 ticks/20s, single ffmpeg, 0 restarts.

**⚠️ NOT ISOLATED — 4 variables changed at once** (Orbbec unplugged, node reverted, conf
device fixed, camera USB-rebound earlier). "It works now" does not identify which one
mattered. Longest pre-fix healthy runs were 5-9 min, so a short good run is NOT proof.

**Risk now:** with `1551b0b` there is **no watchdog and stderr goes to /dev/null** ⇒ a stall
is silent and permanent, no journal error, until a manual `systemctl restart
vision_streaming`. Also `camera_name` **goes stale again on any reboot/replug** that
renumbers the cam (was video8 at boot, video0, now video1) — re-point it or the feed dies.

**Still-open suspect, untested:** `probe_formats()` (NEW in the 2026-07-19 v2 rewrite;
`vision_config_manager:125`, called from `cmd_list`→`discover_cameras`) runs
`v4l2-ctl --list-formats-ext` against the **live streaming** device every time G-Control
polls `list --json`. One trial killed a healthy stream (cpu 984→8); the control run was
invalid (SIGTERM doesn't kill a wedged ffmpeg). **Keep the camera page CLOSED while soaking.**

**Measurement lessons:** ffmpeg CPU is bursty — sample **≥20 s** (healthy ≈1100 ticks/20s,
stalled <30). The wfb `video tx` counter is **unreliable** — it froze across samples and its
`dropped` field underflowed to 4294967409; cross-check, don't trust it alone. `rchar`/`wchar`
in `/proc/<pid>/io` are **useless** for v4l2 (mmap, not read()).

---

## 2026-07-27 night — QGC "Command failed (exit 1)" SOLVED + Orbbec node behaviour

**ROOT CAUSE of the QGC resolution error.** `PXLABS_qgroundcontrol/tools/pxlabs_cli.py:707`
(`camera-params`) defaults the device: `device = getattr(args, "device", "/dev/video0")`,
then sends `sudo vision_config_manager set-cam-params {device} {res} {fps} --format {fmt}`.
`/dev/video0` was the **Orbbec** at that moment, not the LG cam (video1). Chain:
`resolve_camera` lets the raw path through (Orbbec's `usb_identity` is None so it isn't in
the camera list, and the `/dev/` branch returns `None, real, None` without erroring) ->
`set_cam_params` -> `control_service('stop')` -> `v4l2-ctl --set-fmt-video pixelformat=MJPG`
on a depth node **fails** (`check=True`) -> `sys.exit(1)` -> `control_service('restart')`
never runs. **15 min of dead video, 19:33:35 -> 19:48.** G-Control shows only
"Command failed (exit 1)"; the real message is discarded even though the CLI appends `2>&1`.
**Fix on the QGC side: pass the camera id/alias, never the `/dev/video0` default.**

**⚠️ The Orbbec's /dev/videoN nodes APPEAR AND DISAPPEAR depending on `rover-camera`.**
Wrapper RUNNING => OrbbecSDK/libusb claims the device, uvcvideo detaches, **no Orbbec
video nodes** (only LG video1/video2). Wrapper STOPPED + camera plugged => uvcvideo binds
and creates **8 nodes** (video0, video3-7, video8-9), and the Orbbec takes **video0**.
This is why the same question got opposite answers hours apart -- both observations were
correct for their moment. **Never key anything on /dev/videoN; the map is a function of
service state, not just boot order.** (Supersedes the MEMORY.md edit claiming the Orbbec
never has video nodes -- that was only true while rover-camera was running/unplugged.)

**vision_config_manager v2.2.1 installed** (backups: `.bak.2026-07-27-v2.1.0`,
`.bak.2026-07-27-v2.2.0`; codex-work `af4d0d8`). Both setters stop the service *before*
work that can `sys.exit(1)` -- a pre-existing trap that v2.2.0 (mine) widened by adding a
new exit on the same side of the stop. Now: the conf-section check runs BEFORE the stop,
and both setters are wrapped at the call site so `SystemExit` triggers `ensure_service_up()`
before re-raising. **Verified live:** `set-cam-params /dev/video19 ...` prints
"no section ... matches; nothing done, stream untouched" and the stream keeps running
(same ffmpeg pid). Under v2.1.0/v2.2.0 that command took the feed down.

**Also confirmed:** `resolve_camera()` calls `discover_cameras()` first, so **every** QGC
camera operation -- not just `list` -- probes every video node with `--list-formats-ext`,
including the live streaming one. `probe_formats` remains the unfixed stall suspect and
runs on far more paths than first thought.

**Ruled out tonight:** the `Pixel Format` regex in `set_resolution_only` (matches real
v4l2-ctl output fine).

**STATE:** new node `164420e` running (capture-node-by-sysfs-index fix + stall watchdog),
**34+ min continuous, 0 stalls, 1 start** -- the cleanest run of the day. Orbbec connected,
rover-camera + rover-scan up, measured mount TF live (`f210102`). QGC source cloned for
reference at github.com/ArvinVeiyon/PXLABS_qgroundcontrol.

---

## 2026-07-27 late night — v2.2.2 + ⚠️ MEMORY IS SPLIT ACROSS TWO CLAUDE SCOPES

**v2.2.2 — the v2.2.1 guard was too narrow (found by the QGC-side Claude, not here).**
Both setters were wrapped with `except SystemExit:` only, so a `PermissionError`,
`OSError` or bare subprocess failure after `control_service('stop')` propagated past
`ensure_service_up()` and left the service down. **Real outage: 22:52:35 → 22:55:34,
3 min of dead video, manual restart.** Now `except BaseException`. Verified for
SystemExit/PermissionError/OSError, and live-tested (`set-cam-params /dev/video19`
refused, same ffmpeg pid throughout). Backup `.bak.2026-07-27-v2.2.1`; codex-work `d4b3c55`.

**⚠️ There is a SECOND Claude memory scope on this box:**
`~/.claude/projects/-home-roz-codex-work/memory/` (used when Claude Code runs with cwd
`~/codex-work`). **I do not load it** — my scope is `-home-roz`. It held three files that
existed nowhere else and were not in git:
`vision-streaming-outage-2026-07-27.md`, `vision-config-manager-setter-exception-gap.md`
(the v2.2.2 bug), `probe-formats-every-op-watch-item.md`. Now mirrored into
`~/codex-work/memory/` and pushed. **Check that directory when work has been done from
the codex-work cwd, or findings will be invisible here.**

**probe_formats decision (user-accepted, from that scope):** parked as a WATCH-ITEM, not
a bug to fix. **Do NOT proactively refactor the probe_formats call path.** Raise it again
only when the camera panel is exercised live, measure actual probe frequency/latency
first, then decide.

**QGC side is fixed and pushed:** `PXLABS_qgroundcontrol` `a8cb2ae` on branch
**PXLABS-integration** — removes every `/dev/videoN` default (`camera-apply`,
`camera-query`, `camera-params`, argparse), `shlex.quote()`s interpolated values, gates
the camera Apply button until inventory is loaded, and surfaces captured stdout/stderr
instead of "exit 1" — the last was the SAME copy-pasted bug in **five** settings pages
(CompanionControl, ConnectionControl, PXLABSSettings, RelayControl, WFBConfig).
Verified from here: `shlex`+`sys` imported, file compiles.
