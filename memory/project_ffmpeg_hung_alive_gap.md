---
name: project-ffmpeg-hung-alive-gap
description: "vision_streaming ffmpeg watchdog only catches process DEATH, not a hung-but-alive ffmpeg — GS video cuts off silently"
metadata: 
  node_type: memory
  type: project
  originSessionId: 62813ffb-bde2-479e-8734-481ad4a5907b
  modified: 2026-07-26T17:55:10.613Z
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
