---
name: this_machine
description: "Operating quirks of the companion Pi that the two manuals do not cover — measurement hygiene, domain IDs, param access, CPU budget"
metadata: 
  node_type: memory
  type: reference
  originSessionId: ed82ad73-5296-4ccf-a23b-4d17a56b063d
  modified: 2026-08-22T02:23:00.143Z
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

## Domains, tools, access
⚠️ **Replays need `ROS_DOMAIN_ID=42`; the LIVE stack is domain 0.**
⚠️ **`fps` is INERT in QGC.**
✅ **I can read/write PX4 params myself:** `python3 ~/ros2_ws/tools/set_param.py NAME [value]`
(refuses while armed). **Don't ask the operator to read QGC.** ⚠️ writes are **RAM ONLY** —
finish with `param save`. 🔑 autopilot is `1:1`; never read vehicle state from the GCS at `255:190`.
