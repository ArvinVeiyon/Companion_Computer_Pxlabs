---
name: project-ffmpeg-hung-alive-gap
description: "FPV camera stops feeding frames while staying enumerated. 07-30: LG proven unrecoverable by ANY software means (driver rebind, full USB re-enumeration, lowest-bandwidth mode, GStreamer — all 0 frames); See3CAM swapped in on the SAME port works. Fault is the LG or the 6-2 connector under 500 mA load. Read the 2026-07-30 section FIRST."
metadata: 
  node_type: memory
  type: project
  originSessionId: 62813ffb-bde2-479e-8734-481ad4a5907b
  modified: 2026-07-31T19:54:50.268Z
---

# ⚠️ READ THE "2026-08-01" SECTION FIRST — it is a DIFFERENT fault class from everything below.
# (07-30 supersedes 07-28-night. Those are camera/USB faults. **08-01 is NOT a camera fault at all.**)

---

# 2026-08-01 — CPU-STARVATION LATCH: black QGC video with a PERFECT camera and PERFECT radio

**Symptom:** QGC shows no picture. Camera enumerated and healthy, radio flawless, service "active",
**node logs completely silent** — no warning, no error, no restart, for over an hour.

**Mechanism.** ffmpeg lost a CPU race (rover stack: `rover-camera` 41%, `wheel_odometry` 26%,
`MicroXRCEAgent` 13%, `depthimage_to_laserscan` 9%, vs ffmpeg needing a full core), fell behind, and
**never caught up. It is a LATCH, not a steady state** — output degraded to ~3 s bursts every ~14 s,
**7-28 pkt/s against 208 healthy**, and stayed there indefinitely.
**⛔ Restarting the service does NOT clear it** — it re-enters the same load and falls behind again
within seconds (proved at 22:40). QGC shows *black* rather than stutter because with ~10 s output
gaps it rarely catches a keyframe.

**THE FIX (60 s, reversible):** `sudo systemctl stop rover-camera rover-scan rover-odometry`
→ **7 → 208 pkt/s**, and it **stays healthy after those services are restarted**. Measured both ends.

**Why ffmpeg is fragile enough to lose that race:** with `-f rtp` the muxer forces constant frame
rate, so ffmpeg **dup-pads a 15 fps camera up to 60 fps — 600 frames encoded from 151 real ones**,
4× the work for the same picture. `-fps_mode passthrough` removes the padding (149 from 150) and
halves CPU (94% → 42%). **⛔ BUT the user has VETOED any change to the ffmpeg command line
(`vision_streaming_node.py` ~lines 176-207). Do not propose `-fps_mode`, `-g 30`, `-tune
zerolatency`, `-pkt_size`, or `fps`→`-framerate` again.**

**FIX APPLIED INSTEAD (08-01, built + verified live): throughput-floor watchdog.**
`RATE_FLOOR_FPS=5.0 / RATE_WINDOW_S=20.0 / RATE_GRACE_S=30.0`, evaluated in `check_ffmpeg` after the
existing stall check; logs ERROR, kills, restarts. **Deliberately does NOT reset the backoff on this
path** (a long run ending degraded has not earned a fast retry; resetting would restart-loop every
~60 s under sustained load). Verified by `systemctl set-property --runtime vision_streaming.service
CPUQuota=5%` → fired in ~30 s: *"only 2.6 fps over the last 22s (floor 5 fps) after 216s — throughput
collapse, not a stall"*. Healthy 212 pkt/s produced **no** false trip over 75 s.
**Why the old watchdog missed it:** it only checked *liveness* — line ~257 treats ANY frame-counter
increment as progress and resets the 10 s `STALL_TIMEOUT_S`. A bursty collapse keeps ticking, so a
30× throughput loss was invisible by construction.

### ⚠️ Two measurement traps that cost hours on 08-01 — READ BEFORE DEBUGGING VIDEO
1. **Per-second samples of `video tx incoming` on 8102 land inside the burst gaps and read 0.**
   That made me wrongly declare "WFB's video listener is dead". **Always use a CUMULATIVE delta over
   ≥30 s** (`(cum_end - cum_start)/elapsed`), never per-second snapshots.
2. **A MANUALLY launched ffmpeg sending to `127.0.0.1:5602` never moves WFB's counter**, though the
   service's ffmpeg does. Cause NOT established — the socket is *not* connected (`rem_address
   0.0.0.0:0`), so that is not the reason. **⇒ NEVER A/B ffmpeg flags via the WFB counter.** Use
   ffmpeg's own `N packets read / N frames decoded / N frames encoded` summary, or the live service.

**Camera-health baseline for comparison (manual, clean):** 152 packets in 10 s = **15.2 fps**,
**0 decode errors**, speed 0.99×. ~5 `No JPEG data found` lines in the first second after any start
are **benign sensor settling**.

## 2026-08-01 close — the `fps` conf key does nothing, and why that is UNRESOLVED
User dropped the stream to **640x360** from QGC: **ffmpeg CPU 78-95% → 25.7%, load 4-6 → 2.4,
throughput still 183 pkt/s.** ~3.7× cut — this largely defuses the starvation latch above.
**⚠️ Resolution and bitrate work. `fps` does NOT:** conf said `fps = 15` while
`v4l2-ctl --get-parm` reported **30**. QGC→conf is fine; **conf→ffmpeg is the missing hop** (the key
is never added to the command). ⚠️ `bitrate` stayed 2000K ⇒ **radio load unchanged; the saving was
CPU-only.**

**⛔ USER RULE, verbatim (08-01): "do not hardcode the frame rate in the ffmpeg — it will be handled
from QGC through the config file."** A literal `-framerate 30` is FORBIDDEN.
**UNRESOLVED — ASK, do not decide alone:** does that rule also forbid passing the *conf's own* value
through (`-framerate {conf fps}` — config-driven, nothing hardcoded)? If it does, QGC's fps control
stays permanently decorative.

**🔎 CHECK THIS FIRST, before any code discussion — the user's own hypothesis:** the camera may not
*support* 15 fps at all. Run `v4l2-ctl -d /dev/video0 --list-formats-ext` and read the frame-interval
list for 640x360 MJPG. **If 15 is not offered, the setting could never work regardless of plumbing**,
and the missing hop is only half the story. User's read: "15 fps is the issue, rest are working."

---

# 2026-07-30 — LG proven unrecoverable in software; See3CAM swapped in and working

## The stall histogram — ~66% of "stalls" are NOT stalls
186 `no new frames` events since 07-25, bucketed by ffmpeg runtime at failure:

| runtime at failure | count | meaning |
|---|---|---|
| **exactly 32 s** | **97** | `STARTUP_GRACE_S`(30) + one 2 s watchdog tick, `saw_frames` never True |
| 30 / 34 / 36 s | 12 / 8 / 5 | same band |
| 38–70 s | ~30 | ambiguous |
| >100 s (130,210,252,256,310,448,566,616,722) | **9** | the only TRUE mid-stream stalls |

**A failure at 32 s with `stalled_for == runtime` means ffmpeg got ZERO frames from the very first
one.** Those are **cold-start failures**, not stalls. Only 9 of 186 events are the "streams fine
then dies" case this file was named for.

**The recovery path is the real outage amplifier.** 07-28 10:17:46 → 10:36:34 = **19 consecutive
32 s failures = 20 minutes of dead video from ONE initial glitch.** Mechanism: stall → ffmpeg wedged
in a v4l2 ioctl ignores SIGTERM → SIGKILL at 5 s → camera never gets a clean STREAMOFF → next open
yields no frames → 30 s grace → SIGKILL → repeat. At max backoff the cycle is
**30 s backoff + 32 s grace + 5 s kill ≈ 67 s per attempt.**

## ⛔ SOFTWARE USB RECOVERY DOES NOT WORK — this kills todo 8b item 3
Tested against a live-wedged LG, in escalating order. **Every one returned 0 frames:**

| test | result |
|---|---|
| `ffmpeg -c copy` (NO encoder in the pipeline) | `0 packets muxed (0 bytes)` in 20 s |
| `uvcvideo` unbind → rebind `6-2:1.0` | 0 packets |
| USB de-authorize → re-authorize (`6-2/authorized` 0→1, full re-enumeration) | 0 packets |
| retry at **640x480** (lowest isoc bandwidth) | 0 packets |
| **GStreamer** `v4l2src ! image/jpeg ! fakesink` | 0 buffers, hung |

**Do NOT build "escalate to a USB port reset after N zero-frame starts" (todo 8b item 3) — it is
measured NOT VIABLE.** Only physical VBUS removal clears the camera. The node can be made to fail
*gracefully and loudly*, but it cannot be made to self-heal on this hardware.

**Kernel is silent throughout**: zero `-71`/`-110`, no babble, no `Not enough bandwidth`, no port
reset, no xhci errors during any stall. `throttled=0x0`, core 0.85 V. The device stops filling isoc
packets and the host controller is perfectly happy. (One `uvcvideo 6-2:1.1: Failed to resubmit video
URB (-1)` appeared at 23:01, but during the unbind test — not organically.)

## The swap — and what it does NOT prove
See3CAM_CU135 fitted to the **same port 6-2**, same cable path, same bus, same host controller,
same ffmpeg command → **worked immediately**, and recovered from a mid-stream disruption on the very
next retry (something the LG never did in 5+ minutes of retries).

⚠️ **This still does not separate "LG internally faulty" from "connector 6-2 bad under load".**
See3CAM draws **100 mA**, LG draws **500 mA** — a contact-resistance fault produces exactly this
result. `ext5v-report` reads the rail UPSTREAM and is blind to a drop at the connector.
**Discriminator not yet run:** put the LG in the free port `4-1` (different host controller,
different power path) and soak. Blocked — enclosure is assembled.

## ✅ CORRECTION: the "See3CAM only does ~16 fps on 480M bus 6" note was WRONG
That claim (in MEMORY [SENSORS] and this file's lineage) is **retracted**. It was measured in a dark
room and the cause misattributed to USB 2.0 bandwidth. Measured 07-30 at 1280x720 MJPG on bus 6-2:

| exposure | fps |
|---|---|
| `auto_exposure = Auto Mode` (dark room, 23:30) | **16.6** |
| manual, `exposure_time_absolute = 50` (5 ms) | **59.4** |
| manual, `exposure_time_absolute = 10` (1 ms) | **59.6** |

**The camera does a genuine 60 fps at 720p MJPG over USB 2.0.** Long auto-exposure in low light
caps frame rate — normal camera physics, not a bus limit. The tell that should have caught this
sooner: fps was ~15-16 at 640x480, 720p **and** 1080p alike. A bandwidth limit would have made the
small resolution much faster; it didn't. **You do NOT need a blue USB3 port for full frame rate.**
Expect 60 fps outdoors/daylight, ~16 fps indoors at night. `dup_frames=0, drop_frames=0` throughout.

⚠️ **Toggling `auto_exposure` mid-stream stalls this camera for >12 s and trips the watchdog** — I
caused a false-alarm stall doing exactly that. Stop the service before touching v4l2 controls.
Also: `exposure_time_absolute` is flagged `inactive` in Auto Mode and writes to it return
`Permission denied` (a v4l2 rule, NOT sudo) — set auto→manual, write, then auto again.

## New code defects found in `vision_streaming_node.py` (all UNAPPLIED)
Verified against the live file 07-30; line numbers from that read.

1. **`-progress` has NO `frame=` key when `-c copy` is used.** Keys present in copy mode are only
   `bitrate drop_frames dup_frames out_time out_time_ms out_time_us progress speed total_size`.
   The stall watchdog exists **only because libx264 is in the pipeline**. ⚠️ **Any move to MJPEG
   passthrough would silently disable the watchdog** (`saw_frames` never True → kills a healthy
   stream every 30 s forever). If that path is ever taken, key liveness on **`out_time_us`**.
2. **`fps` in the conf is never read.** Node parses `resolution`/`bitrate`/`format` only; no
   `-framerate` is ever passed. Verified live: QGC now has `fps = 60` and the running command line
   has no `-framerate`. The QGC control does nothing and the readout is not trustworthy.
3. **No `-g` / GOP control.** x264 default `keyint` = 250 frames ≈ **8.3 s at 30 fps**. Over a lossy
   radio one lost keyframe smears/freezes for up to 8 s. Strongest candidate for what reads as
   "WFB is flaky". Fix: `-g 30` (1 s) or intra-refresh, plus `-tune zerolatency`.
4. **`frame=0` counts as progress** (`drain_progress`, ~line 257): `0 > last_frame(-1)` advances
   `last_progress_at` without setting `saw_frames`, so the 30 s grace silently becomes ~50 s.
   Observed: `no new frames for 32s after 50s`.
5. **Backoff reset on the stall path** (~lines 325-326) — still unapplied, as todo 8b(a) says.
6. **`rclpy.shutdown()` RCLError** (~line 363) fires on **every QGC camera change**, not just manual
   restarts — confirmed live during the 07-30 swap. Harmless (systemd logs `Deactivated
   successfully`) but dumps a traceback exactly when you'd be checking whether the swap worked.
7. **The `camera_name` fallback is dangerous.** `/dev/video0` did not exist for most of 07-30
   (nodes were video8/video9). If sysfs resolution ever fails, ffmpeg gets pointed at a node that
   is not the camera. It only worked after the swap **by luck**.

## Pi 5 has NO hardware H.264 encoder — encoder choice is not a lever
`v4l2h264enc` MISSING; `v4l2-ctl --list-devices` shows only `rpivid`, which is **decode-only**.
(ffmpeg lists `h264_v4l2m2m` but that is a generic wrapper with no m2m encoder device to bind.)
So H.264 is software-only either way. **GStreamer 1.24.2 is installed with every needed plugin
(`v4l2src`, `x264enc`, `rtph264pay`, `udpsink`) and offers no performance advantage** — same x264
cost. Its only real edge is surfacing device faults as bus messages instead of scraped stderr.
**Recommendation: stay with ffmpeg.** `-progress` is what makes the watchdog possible at all.
Measured CPU: LG 720p30 ≈ 84.6% of a core; See3CAM 720p16 ≈ 48.6%.

**MJPEG passthrough** (camera already emits MJPEG; you decode → yuv420p → re-encode) would drop CPU
to ~zero and is all-keyframe (no error propagation — genuinely better over a lossy link), but
720p30 MJPEG is ~8-15 Mbit/s vs the 13 Mbit/s MCS1 PHY at ~34% used — **it does not fit at 720p.**
640x480 (~3-5 Mbit/s) would. See defect 1 before attempting it.

---

**This header used to read "CLOSED — the LG unit was faulty". That verdict was WRONG and is
retracted.** The LG was later reconnected and works. What follows in this section is still useful
as *evidence*, but its conclusion is void: the swap it describes confounded camera identity with
connector condition, because the port had been mated/unmated ~4 times by then.
**Everything except the verdict — the diagnostics, the ruled-out list, the measurement lessons —
remains sound.**

**The swap, as measured** (same port 6-2, same cable, minutes apart) — real data, wrong conclusion:

| | LG Smart Cam (30c9:009d) | See3CAM_CU135 (2560:c1d1) |
|---|---|---|
| frames delivered | 38 → 5 → 0 (degrading per open) | continuous, 4400+ |
| time before stall | ~1.3 s | 73 s+, `drop=0`, no stall |
| `wfb_tx -p 0` ticks | 0 / 20 s | 27 / 15 s |
| `bMaxPower` | 500 mA | 100 mA |

**Camera in service as of the NIGHT section: back to the LG** (`usbcam-30c9009d-01.00.00-i00`).
The See3CAM_CU135 `usbcam-2560c1d1-241D8306-i00` (2560:c1d1, sn 241D8306, 100 mA) is the **on-hand
spare**. Both were **selected and applied by the user from the QGC camera page** —
`vision_config_manager` rewrote the conf and restarted the service on its own, in both directions.
**The ground-side Apply flow is verified working end to end; it is the ONLY supported way to
change cameras.**

### ⚠️ PROCESS CORRECTION — I got this wrong, don't repeat it
When the swap left the conf pointing at the dead LG id, I offered to hand-edit
`/etc/vision_streaming.conf` on the companion. **Wrong.** The user pushed back: the requirement is
that ANY camera is configurable from the ground, which is what the QGC camera button is for.
Repointing the conf is not a special case — it is exactly what Apply does. **Never propose a
companion-side conf edit as a workaround for a camera change.** → [[feedback_camera_qgc_only]]

### THE BEST SINGLE DIAGNOSTIC — reach for this FIRST next time
Stop the service and run ffmpeg by hand with `-loglevel verbose`; read the **input** summary:
```
Input stream #0:0 (video): 40 packets read (6501827 bytes); 38 frames decoded; 0 decode errors
[vost#0:0/libx264] *** 750 dup!
frame=788 ... dup=750
```
`packets read` / `frames decoded` is the camera's TRUE output, and `dup!` is how many frames x264
invented to pad the gap. This one command proved in 45 s what days of service-level debugging
could not: the camera sent 1.3 s of video and quit. **`0 decode errors` also proved the frames it
does send are perfectly valid** — the `unable to decode APP fields` warning is a benign APP-marker
complaint, NOT corruption, and was a red herring for days.
**Corollary — why the flapping looked like "no feed":** x264 keeps emitting RTP from duplicated
frames, so the GS shows a FROZEN PICTURE, not a black one, and wfb counters keep moving. A live
RTP stream does not mean a live camera.

### Measurement reliability — learned the hard way this session
- ✅ **`wfb_tx -p 0` CPU tick delta is the trustworthy signal.** 0 ticks/20 s broken vs 27 ticks/15 s
  working. It discriminated correctly every time.
- ❌ **`tcpdump -i lo udp port 5602 | wc -l` is USELESS here** — it read **0 in BOTH states**,
  including while video demonstrably flowed. `timeout` SIGTERMs tcpdump and its buffered output is
  discarded; the `-c` form needs a password not in the NOPASSWD set. I cited a 0 from it as
  evidence; that was unsound. Do not use it.
- ❌ **ffmpeg CPU ticks alone are NOT a health signal.** A stalled ffmpeg burned ~102 ticks/s
  (higher than a healthy one) spinning on x264 duplicate frames. I briefly read that as "healthy".

### Ruled out BY TEST, not by assumption — never re-chase
- **USB autosuspend.** Was `control=auto`, `runtime_status=suspended`. Pinned to `on` (→ `active`),
  retested 640x480 MJPG: **still zero frames.** Retires agreed-fix item 4 as a *cause* (still fine
  as hygiene; the pin is NOT persistent, it reverts on reboot without a udev rule).
- **Bandwidth/resolution.** Failed identically at 1280x720 MJPG, 640x480 MJPG **and 640x480 YUYV** —
  the lowest-demand mode. Kills the "only dies at high bitrate" theory.
- ~~**Cable / connector / port.**~~ **RETRACTED — see the NIGHT section.** The replacement camera
  working on the same port/cable does NOT clear them: the connector had been re-mated ~4 times, and
  the See3CAM draws 100 mA vs the LG's 500 mA. Contact resistance is still a live suspect.
- **VBUS note that explains every failed software recovery:** `echo 0/1 > .../authorized` and port
  resets **do not cut VBUS** on the Pi, so they can never clear a camera's internal state. Only a
  physical unplug does — which is why a replug bought 22 s and every software reset bought nothing.

### Open, non-blocking follow-up
**The See3CAM is throttled by its port.** It is a USB 3.0 camera on **bus 6, a 480 Mbps root hub**,
so 720p MJPG runs ~16 fps and ffmpeg duplicates most frames to pad. **Bus 5 and bus 7 are empty
5 Gbps root hubs** — moving it there should give full frame rate for free. Not urgent; video works.

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

**AGREED FIX LIST — status re-verified 2026-07-28: items 1, 2, 3 and 4 are ALL still unapplied.**
(1 confirmed in code at `vision_streaming_node.py:325-326`, which still resets `backoff_s` on the
stall path; 4 confirmed at `/sys/bus/usb/devices/6-2/power/control` = `auto`.) They were tracked
nowhere until the 07-28 audit — now filed as **todos §8b**. Note item 3's *rationale* weakened:
the 07-27 evening revert test showed SIGKILL is not the root cause of the stall, only of failed
recovery. The fixes are still wanted; the diagnosis behind them is not.

**AGREED FIX LIST (original wording):**
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

**⚠️ THIS "FINAL STATE" BLOCK IS SUPERSEDED — read the 07-27 night + late-night sections below.**
By that evening the node was moved forward again to `164420e` (sysfs capture-node fix + stall
watchdog), the **Orbbec was reconnected** and `rover-camera`/`rover-scan` restarted, and the
mount TF was measured (`f210102`). Nothing in the block below about the reverted `1551b0b` node,
the unplugged Orbbec, or "L5 blocked" is still true. Kept for the reasoning only.

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

---

## 2026-07-28 — v2.2.3 (root cause of the write failure) + OPEN TODO: bitrate control in QGC

**ROOT CAUSE of "camera resolution changes silently fail to persist" = `fs.protected_regular=2`.**
`/tmp` is 1777 (sticky, world-writable); the kernel refuses an `O_CREAT` open of a file
there whose owner differs from BOTH the dir owner and the caller. `open(path,'w')` is
`O_WRONLY|O_CREAT|O_TRUNC`, so a **roz-owned** `/tmp/vision_streaming.conf` blocked **root**
with EACCES, and `sudo cp` rewrote it *in place* preserving ownership so it never healed.
Trap is symmetric (root-owned file blocks roz) and the sticky bit stops either user
deleting the other's file. **I created the stale file** (staged a conf edit with
`> /tmp/vision_streaming.conf` as roz at 18:04). VERIFIED both directions with `sudo tee`.
Not AppArmor/chattr/ACL — the QGC side had already ruled those out.

**FIXED v2.2.3:** `staging_path()` = `tempfile.mkstemp()` per invocation (fresh 0600 file
owned by the caller, removed after `root_write`). Fixed `/tmp` path gone from all 4 write
sites incl. the camera store; the `sudo cp CONFIG_FILE TEMP_FILE` + `sudo chmod 666` dance
deleted (CONFIG_FILE is world-readable — just read it). Verified side-by-side with the
landmine present (v2.2.2 fails / v2.2.3 succeeds) and **live with the real QGC command**:
`set-cam-params /dev/video1 1280x720 30 --format MJPG` persisted to conf AND ffmpeg,
stream stayed up. codex-work `94e5ef6`.

**⚠️ DO NOT RECORD THE CAMERA MODE IN MEMORY — RULE ADDED 2026-07-28.** An earlier version of
this line asserted "now 1280x720, user confirmed KEEP"; by the time it was written the live
conf was already back to 640x480, and that wrong claim had propagated into MEMORY.md,
`COORDINATION.md:67` and `system_companion.md:28`. codex-work commit `ae9e880` is even titled
"camera stays at 1280x720" while its diff does `1280x720 → 640x480`. **Resolution/fps/bitrate
are operator-set from QGC and change without notice** ([[feedback_camera_qgc_only]]) — the user
has explicitly said they will set what they need. Read `/etc/vision_streaming.conf` or the
running ffmpeg args at the moment you need the value; never quote one from memory.

### ⚠️ OPEN TODO — add bitrate control on the QGC side (user's idea, agreed, NOT started)

**Why:** `bitrate` is not settable from QGC at all, so it never tracks a resolution change —
whatever mode the operator picks, `bitrate` stays at whatever it was. **QGC cannot set
bitrate** — `set-cam-params` takes resolution/fps/format only, and the tool's `3000K` default
only applies when the key is *missing*. Do NOT hand-edit the conf as the workaround
([[feedback_camera_qgc_only]]); add the control instead. (The original framing of this TODO —
"720p at 2000K gives 0.072 bits/pixel ⇒ soft picture" — assumed a resolution that was not
actually live. The *feature* is still wanted; the specific bits/pixel argument only applies
whenever the camera is genuinely at 720p, so re-derive it against the live mode.)

**Companion half (mine, designed not written):**
1. `set-cam-params` gains **optional** `--bitrate` (keep optional — the shipped QGC build
   calls it without, must not break). Validate `^\d+[KM]?$`.
2. `update_cam_params_config()` gains `bitrate=None`; replace the `bitrate` line in the
   target section, append if absent (same pattern as resolution/fps/format).
3. `list --json` → add `active.settings.{primary,secondary}` = current
   resolution/fps/format/bitrate read from the conf, so QGC can prefill the field.
   Additive only; existing `active.primary/secondary` keys unchanged.
4. Bump to **v2.3.0** (feature, not a fix).

**QGC half (theirs):** `--bitrate` in `pxlabs_cli.py camera-params`; `setCamParams()` in
`src/Utilities/PXLABSApi.h`; a bitrate field in `CompanionControl.qml` prefilled from
`active.settings`.

**Constraints to respect:** video FEC is **k=8/n=12 (50% overhead)** ⇒ 2000K ≈ 3 Mbps on
air; WFB is 20 MHz long-GI `-M 1`. **Radio headroom was never measured** — measure before
recommending a value. ffmpeg uses 76% of ONE core (Pi5 has 4) at 720p.

**Alternative lever, also unmeasured:** `-preset ultrafast` → `veryfast` in
`vision_streaming_node.py` gives better quality at the SAME bitrate with **zero** extra
radio load, costing CPU there is headroom for. Arguably the better first move; test one
lever at a time so a link problem is attributable.

---

## 2026-07-28 — THE FAULT IS PHYSICAL. Whole software+radio stack excluded by measurement.

GS feed died again mid-morning. **This session ended the software hunt: the camera itself stops
delivering frames on the isochronous endpoint while staying fully enumerated and responsive.**
Physical inspection of the companion-side USB connector scheduled for the evening of 07-28.

### The one test that settles it — take it FIRST next time
```
sudo systemctl stop vision_streaming            # get ffmpeg off the device
timeout 60 sudo v4l2-ctl -d <dev> --set-fmt-video=width=640,height=480,pixelformat=MJPG \
    --stream-mmap --stream-count=1800 --stream-to=/dev/null
```
Hung the full 60 s with ~0 frames. **No ffmpeg, no encoder, no RTP, no WFB in the loop** — so
none of them can be the cause. Meanwhile `v4l2-ctl --get-ctrl brightness,contrast` returns
instantly (0 / 37). **Alive on ep0, silent on isoc.** Any theory that survives must explain that.

### Ruled out THIS session, with numbers — do not re-chase
- **Undervoltage (user's hypothesis).** `ext5v-report 40`: 1134 samples @2 s spanning every one
  of the 15+ stalls. `throttled=0x0` (not even bit 16, "occurred since boot"), EXT5V **min
  5.0263 V / mean 5.1322 V**, **226 mV above the 4.80 V knee**, **0 dips <4.90 V, 0 dips <4.80 V**,
  peak core 5.37 A, peak 63.1 °C. The rail never sagged during a single stall.
  ⚠️ **BUT `ext5v-report` measures the rail UPSTREAM at the Pi input — it physically cannot see a
  drop at the camera's own connector.** It exonerates the buck/supply, NOT the connection. Do not
  quote "no undervoltage" as if it cleared the cabling.
- **WFB causing it — causation is REVERSED.** User saw "video flows → WFB degrades → video cuts →
  WFB recovers". The radio cannot stall a v4l2 capture (see the test above). The likely truth: video
  IS the dominant load (2000K + k=8/n=12 FEC ≈ 3 Mbps on-air, 20 MHz long-GI `-M 1`, **headroom
  still never measured**); load on → link looks degraded, camera dies → load gone → link looks clean.
  Radio itself healthy: both WFB NICs up, `tx_errors=0` on both, `wifibroadcast@drone` NRestarts=0.
- **Spontaneous re-enumeration / device renumbering.** `dmesg -T | grep "usb 6-2"` over the whole
  boot: the cam enumerated ONCE at 09:03:05 as **devnum 2** and there was **not one USB event on
  bus 6** until my manual reset at 09:29:38. `devnum` never changed. `/dev/video8` never vanished.
  **The cut-off involved no USB event at all.** (video8→video0 was caused BY my reset, nothing else.)
  → User's standing point, and correct: **the device number is irrelevant** — the node resolves the
  `usbcam-*` id every start and logs `conf says /dev/video1, resolved to /dev/videoN`. Never
  present renumbering as a fault.
- **A USB port reset does NOT clear the wedge.** `echo 0 | sudo tee /sys/bus/usb/devices/6-2/authorized`
  then `1` = full remove + re-enumerate; came back clean, zero URB errors — **still zero frames.**
  This retires agreed-fix item 3 (auto USB-reset escalation) as a *recovery* mechanism: it doesn't work.

### The signature that points at the connector
**Load-dependent failure**: works perfectly at enumeration/control current (~100 mA), dies at
streaming current (camera declares **`bMaxPower` 500 mA**). Classic high-resistance contact —
partial seat, corrosion, bent pin — which drops voltage locally under load and is invisible to
every monitor on this box. Consistent with **no USB disconnect events** (D+/D− keeps integrity
while VBUS sags) and with the degradation timeline: healthy 722 s run → after a camera-end replug,
only **12-15 s** per attempt (`no new frames for 12s after 24s`, `for 30s after 44s` = saw frames,
then lost them).

### Evening 07-28 plan (user doing it; companion-side connector is inside the rover)
1. **Move the camera to a different USB port — the decisive test.** Free: **bus 6 port 1**, and
   **bus 5 / bus 7** (both 5 Gbps root hubs, completely empty). Bus 1 = VIA hub (WFB NIC d993c0 +
   8821cu uplink), bus 2 = Orbbec, bus 4 = WFB NIC d98f91 — all occupied.
2. Reseat + inspect the companion-side connector (corrosion / bent pin / partial seat).
3. Eliminate any adapter / extension / pigtail in that path — at 500 mA they drop real voltage.
4. Check cable strain at the camera end.

**FALSIFIES the connector theory:** a clean reseat on a *different port* that still dies the same
way with zero USB events in `dmesg` ⇒ it is the camera's own ISP/firmware and the unit needs
swapping. No cabling work will help.

`vision_streaming` left RUNNING with its backoff, so the feed recovers by itself the moment frames
flow — no restart needed after the physical work.

### 2026-07-28 EVENING — replug done on the SAME port; fault UNCHANGED and now WORSE

User unplugged/replugged the camera (and rebooted, boot 21:58). **It is still on bus 6 port 2** —
the decisive different-port test was NOT performed. Result: no improvement.

**Measured 22:02-22:12, this boot:**
- Camera enumerates perfectly at 21:58:20, `devnum 2`, 480 Mbps, `bMaxPower 500mA`, direct on the
  **root hub — no intermediate hub** in the companion-side path (`lsusb -t`).
- **ZERO RTP on 5602** — `tcpdump -i lo udp port 5602` for 15 s = **0 packets**. Video `wfb_tx`
  (`-p 0`) burned **0 ticks/20 s** while mavlink (`-p 16`) and tunnel (`-p 32`) kept ticking.
- **Pure v4l2, ffmpeg out of the loop, ZERO frames in ALL THREE modes:** 1280x720 MJPG,
  640x480 MJPG, **and 640x480 YUYV**. Each hung the full timeout. Control transfers on ep0 stayed
  instant throughout (`brightness 0 / contrast 37`).
- **Zero uvcvideo / URB / USB errors in `dmesg` across every failed attempt.** (The only kernel
  WARN this boot is `rtw_mlmeext_disconnect` in `8812eu` at 22:06:02 — WFB NIC driver, unrelated.)
- Power clean: `throttled=0x0`, 0 dips <4.80 V, 0 dips <4.90 V.

**Autosuspend RULED OUT (fix item 4 tested, not just applied).** `/sys/bus/usb/devices/6-2/power/`
was `control=auto`, `runtime_status=suspended`. Pinned to `on` (→ `active`) and retested 640x480
MJPG: **still zero frames.** Worth pinning anyway for hygiene, but it is NOT the cause — do not
re-chase it. (The pin is not persistent; it reverts on reboot until a udev rule exists.)

**⚠️ Failure at 640x480 YUYV weakens the pure-bandwidth version of the load theory** — the lowest-
demand mode fails identically. What is still common to every failing case is that *any* streaming
mode switches the camera to its 500 mA alt-setting and powers the sensor/ISP.

**The degradation shape is the new signal — it points at the camera's own state machine.**
After the physical replug the camera DID work briefly: 22:02 event was `no new frames for 32s
after 54s` (= frames seen, then lost). Every later event is `for 30s after 30s` / `for 32s after
32s` (= `saw_frames` False, **never got frame 1**). So: **fresh physical power-on → works briefly
(22 s here, up to 722 s previously) → wedges permanently.**
**Key mechanism note:** `echo 0/1 > .../authorized` and a port reset **do not cut VBUS** on the Pi,
so they can never clear the camera's internal state — only a physical unplug does. That explains
why every software-side reset failed while the replug bought 22 s.

**REMAINING DECISIVE TESTS (in order):**
1. **Different USB port** — still the falsifier, still not done. Free: **bus 6 port 1**, **bus 5**,
   **bus 7** (both empty 5 Gbps root hubs). Bus 1 = VIA hub (WFB d993c0 + 8821cu), bus 2 = Orbbec,
   bus 4 = WFB d98f91.
2. **Different cable** — swap it independently of the port; at 500 mA a marginal cable drops real volts.
3. **Different host** — plug the camera into a laptop and stream it. This is the cleanest
   camera-vs-companion isolation and needs no rover disassembly.
If it dies the same way on another port AND another cable AND another host ⇒ **the LG Smart Cam
unit is faulty, swap it.** No cabling work will help.

`vision_streaming` left RUNNING (flapping on its backoff) so the feed returns by itself the moment
frames flow — no manual restart needed after the physical work.

### New diagnostic worth keeping: prove the radio is idle without trusting the wfb counter
The wfb API `video tx` counter is unreliable (documented above). Instead sample **wfb_tx CPU ticks**:
the video instance is the one with **`-p 0 ... -k 8 -n 12`**; mavlink is `-p 16 -k 1 -n 3`, tunnel
`-p 32 -k 2 -n 4`. During the outage the video wfb_tx burned **0 ticks in 20 s** while mavlink and
tunnel kept ticking ⇒ nothing is being handed to the radio, and the radio is alive. Cross-checks a
frozen `packets.incoming` honestly.

---

# ⚠️ 2026-07-28 NIGHT — REOPENED. MY "LG IS DEAD HARDWARE" VERDICT WAS WRONG.

The user reconnected the **LG Smart Cam** (same port 6-2, devnum 5) and re-applied it from QGC
(`camera_id` back to `usbcam-30c9009d-01.00.00-i00`). **It works.** So the closure above — and the
`✅ CLOSED / the unit was faulty` verdict — is **overturned**. Do not repeat that claim.

**What the journal actually shows (the user reported "working without any issue"):**
- 3 stalls in the first ~90 s after reconnect — 22:37:54 (`for 12s after 40s`), 22:38:34
  (`for 32s after 32s`), 22:39:04 (`for 12s after 24s`) — the identical `camera stopped feeding`
  signature.
- It settled on the 4th start (22:39:18) and then ran **9 min 22 s clean**, with video `wfb_tx -p 0`
  taking **22 ticks/20 s** = real frames on air.
- ⚠️ **9.5 min proves nothing on its own** — the LG's historical best healthy run was **722 s (12 min)**.
  A run must beat ~20 min, ideally an hour plus a reboot, before "fixed" means anything.

**Why the swap test did NOT prove what I said it proved.** I concluded "different camera works ⇒
the LG unit is faulty". But by then the connector had been mated/unmated ~4 times. **Repeated
insertion cycles wipe oxide off a marginal contact** — a classic temporary fix. So the swap
confounded *camera identity* with *connector condition*.

**TWO LIVE HYPOTHESES, still unseparated:**
- **(a)** intermittent internal fault in the LG.
- **(b)** **contact resistance on port 6-2**, temporarily cleaned by tonight's replug cycles.
  This fits the asymmetry the swap actually showed: the See3CAM draws **100 mA** and worked
  instantly and continuously; the LG draws **500 mA** and needed 3 restarts to settle. A
  high-resistance contact hurts the 500 mA device far more. **The connector theory is NOT retired.**

**How to separate them (cheapest first):**
1. **Soak the LG where it is.** >20 min beats its record; >1 h and across a reboot is real evidence.
2. If it stalls again: move the LG to **bus 5 or bus 7** (empty 5 Gbps root hubs). Works there but
   not on 6-2 ⇒ **(b)**, the port/connector.
3. Still stalls on a different port ⇒ **(a)**, the camera; the See3CAM is the on-hand spare.

**LESSON — do not repeat.** "It works now" after several variables changed at once is not a root
cause, and I stated one anyway. This file already warned about exactly that (see the 07-27
"⚠️ NOT ISOLATED — 4 variables changed at once" note) and I still did it. **When hardware starts
working after a physical intervention, report WHAT CHANGED and WHAT IS UNPROVEN — do not name a
culprit.** The diagnostics in this file remain sound; only the verdict was wrong.
