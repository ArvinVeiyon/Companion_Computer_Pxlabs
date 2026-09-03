---
name: this_machine
description: "Operating quirks of the companion Pi that the two manuals do not cover — measurement hygiene, domain IDs, param access, CPU budget"
metadata: 
  node_type: memory
  type: reference
  originSessionId: ed82ad73-5296-4ccf-a23b-4d17a56b063d
  modified: 2026-09-03T18:15:00.456Z
---

# Working on this machine — what the manuals do not cover

Split out of `MEMORY.md` on 2026-08-22 to keep the index under its size cap. The hardest
traps (sudo password, `pkill` self-kill, "I am a major CPU consumer") stayed in the index;
everything below lives here.

## Measurement hygiene
⚠️ **Boot clock is WRONG until NTP steps it** — don't correlate journals across a boot.
🔑 **START A PERCEPTION MEASUREMENT, THEN GO QUIET.** Commanding throughout starved the camera
on 08-09 and produced **two wrong answers**. Spikes vanish before `ps` can see them — use
**`~/ros2_ws/tools/cpu_catcher.sh`**.
⚠️ **No rate or CPU number is trustworthy without `ps -eo pid,pcpu --sort=-pcpu` first** — the
rate you measure may be reporting CPU starvation, not the thing you meant to measure.
🔑 **Prove a node dead with `pgrep`, never with `ros2 node list`** — the daemon cache showed
ghost `/camera/*` nodes for minutes after a stop (08-22).
⛔ **Never read a quiet topic as evidence — prove a NON-ZERO baseline first.** The same rule
applies to any *detector*: prove the detector itself was live across the window (the
`create_participant` FC-reboot detector was blind for the whole 08-21 soak because
`microxrce-agent` was stopped with the stack). → [[fc_hardfaults]]
🔴 **09-02: the `ros2` CLI ITSELF is an unreliable ruler here.** `ros2 topic hz /scan` and
`ros2 topic echo /scan --once` BOTH returned nothing while `rover-scan` + `rover-camera` logged
perfectly healthy and `topic list` showed the topic registered. ⛔ **`--no-daemon` is NOT a valid
flag on `topic hz`** (arg error — it exists on `list`/`echo` only), so the usual workaround does
not apply. **Result: the FPV video's `/scan` cost went UNMEASURED.** Don't call `/scan` dead on CLI
silence — reach for a ruler that isn't the ros2 CLI. → [[independent_rulers]]

## Proving `vision_streaming` is ACTUALLY streaming (not just `active`)
✅ **09-02 method, fast and decisive:** `pgrep -af "[f]fmpeg"` should show the encoder at **~110% CPU**,
and `printf '<pw>\n' | sudo -S ss -unap | grep 5602` should show **`wfb-server` bound on 5602**
receiving the RTP. Encoder live + radio path bound = genuinely streaming.
⛔ **Do NOT use `/proc/<pid>/io` `wchar`** — RTP goes out via `sendto`, which does **not** increment
it. You will see ~200 B/s (just the `-progress pipe:1` output) and wrongly conclude the stream is
dead. 🔑 The node resolves the camera by ID, so a `/dev/videoN` shift is normal and handled: it
logged "conf says `/dev/video0`, resolved to `/dev/video8`" and worked.

## Domains, tools, access
⚠️ **Replays need `ROS_DOMAIN_ID=42`; the LIVE stack is domain 0.**
⚠️ **`fps` is INERT in QGC.**
✅ **I can read/write PX4 params myself:** `python3 ~/ros2_ws/tools/set_param.py NAME [value]`
(refuses while armed). **Don't ask the operator to read QGC.** ⚠️ writes are **RAM ONLY** —
finish with `param save`. 🔑 autopilot is `1:1`; never read vehicle state from the GCS at `255:190`.

## Interfaces (09-03) — the names in the older docs are WRONG
🔑 **Uplink is `wlx8c86dd5beed9`** (static `192.168.1.240/24`, route metric 50) — measured 09-03 as
a **TP-Link Archer T2U PLUS `2357:0120` (RTL8821AU)** on driver **`rtl88xxau_wfb`**, syspath `4-2`.
🔴 **THE ADAPTER WAS SWAPPED AND NO DOC CAUGHT IT** — every doc said "RTL8821CU
`wlx90de80d824d6`"; **`0bda:c811` is not in `lsusb` at all** and that stanza is commented out in
`50-cloud-init.yaml`. **Read `ip -br addr` + `lsusb`, never a NIC name or chipset out of a doc.**
⚠️ WFB NICs are the OTHER two: `wlx782288d98f91` (`1-1.1`) / `wlx782288d993c0` (`1-1.3`),
`0bda:a81a` on `rtl88x2eu`.
🔑 **No `wlan*` at all** — `disable-wifi-pi5` overlay is live (plain `disable-wifi` is silently
ignored on a Pi 5; that is why it was twice recorded as done while the radio was still up).
✅ **`eth0` = wired recovery, added 09-03** — `ssh roz@10.10.10.10` (laptop `10.10.10.20/24`) or
`roz@Vind-Roz.local`. ⚠️ **address exists ONLY with carrier**; empty `ip -br addr show eth0` with
no cable in is CORRECT, not a fault. Judge it by `networkctl status eth0` → `routable`.
⚠️ **Cable-untested as of 09-03.** → setup_manual §E5b
