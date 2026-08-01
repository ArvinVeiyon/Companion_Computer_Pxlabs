---
name: feedback-crash-recovery-checkpoint
description: "RULE: checkpoint memory at each finding, not at session close — a 2026-08-01 crash nearly lost 4h of work. Plus the verified procedure for reconstructing live state after a session dies."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b207e8d3-f638-4331-a8d8-7c4c291479c2
  modified: 2026-08-01T11:33:55.219Z
---

# RULE: checkpoint memory per finding, and how to recover from a lost session

## What happened (2026-08-01)
A session crashed at ~16:12. It had run since ~13:00 and produced **6 commits, a 569-line design doc,
and two files of measured calibration values** — and **memory recorded NONE of it**, because the
habit was to write memory at session close. The close never came. Recovery worked only because the
work happened to be committed to git; the **uncommitted** measured values (floor height, bumper
self-view) survived by luck alone.

**Why:** memory is written at close, but sessions do not reliably reach close. Anything not yet
written is held only in the context window, and the context window is exactly what a crash destroys.

**How to apply:** write the memory **when a finding lands**, not at the end. Specifically —
- A **measured number** that cost real effort to obtain → write it immediately, even mid-task.
- A decision that **contradicts** existing memory → write it immediately; a stale index is worse
  than a thin one, because the next session acts on it.
- Committing to git is **not** a substitute: a commit records the change, not the reasoning, the
  measurement conditions, or the caveat that makes the number trustworthy.
- At close, **verify and compact** rather than write from scratch.

## Verified state-recovery procedure (worked 2026-08-01 16:55)
Run this before touching anything — do NOT trust the memory index alone, it may be hours stale.
1. `uptime`, then `systemctl is-active` the core + autonav services.
2. `git -C ~/ros2_ws log --format='%h %ad %s' --date=format:'%m-%d %H:%M'` and
   `git status -sb` — **commit timestamps reconstruct what the lost session was doing, and in what
   order.** Compare the newest commit against what memory claims; the gap IS the undocumented work.
3. `git diff` — uncommitted changes are the most fragile artifact. Read them for measured values and
   record those in memory before doing anything else.
4. Live topic rates (`ros2 topic hz /odom /scan`) — do not infer health from service state alone.
5. Check whether a stopped service was stopped **deliberately**: `systemctl status` shows
   `signal=TERM` + a long clean `Duration` for an intentional `systemctl stop`, vs a crash/restart loop.

⚠️ **Timestamps across a reboot are unreliable on this platform** — `uptime -s`, `who -b` and service
durations gave three different answers on 08-01. Use commit times and service durations for
*ordering*, never for absolute correlation across a boot.

## The 08-01 recovery, for reference
Recovered work → [[project-perception-3d-costmap]] (the measured floor + bumper self-view) and
[[project-autonomy-plan-reframe]] (the ladder rewrite that contradicted the old "L0-L4 DONE" status).
Vehicle state → [[project-rover-autonav]].
