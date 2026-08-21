---
name: fc_hardfaults
description: "FC hardfault campaign — NOT stack exhaustion (that is retracted); it is instruction-side memory corruption, and after every hardware/firmware/CAN/power elimination the ONLY suspect left is param contamination dated 08-15"
metadata: 
  node_type: memory
  type: project
  originSessionId: 96448c77-71fd-43a5-9b04-11a764db5e77
  modified: 2026-08-21T18:06:28.254Z
---

# FC hardfaults — state as of 2026-08-21 late

## 🔬 RUNNING NOW: STACK-OFF SOAK (started 2026-08-21 23:33 IST / 18:03 UTC, operator's test)
**Question: do faults continue with the ROS/autonav stack down?**
- ✅ **STOPPED (all inactive, pgrep-verified, not just `is-active`):** `rover-autonav-mode`,
  `rover-scan`, `rover-scan-3d`, `rover-odometry`, `rover-camera`, `rover-ekf-bridge`.
- ⚠️ **`vision_streaming` RESTARTED AT 23:36:13 IST at operator request** — so the soak is "autonav/perception off,
  FPV video ON". ✅ **This time it is REALLY streaming** (ffmpeg alive, `/dev/video8` via `usbcam-30c9009d-01.00.00-i00`,
  RTP→127.0.0.1:5602) — unlike the 08-20 "up but not streaming" state.
- ⚠️ **`microxrce-agent` DELIBERATELY LEFT UP** — kept for observability (FC-reboot detector, below) and
  because MAVFTP fault-polling runs over `tcp:5760`, independent of DDS. ⇒ **this soak is "no ROS nodes",
  NOT "nothing talking to the FC"** — and **fault #30's victim was `uxrce_dds_client`, still the busy task.**
- ✅ Card emptied + re-listed clean at 18:03 UTC. Non-zero baseline proven: `/fmu/out/input_rc` **100.3 Hz**.
- 🔑 **BAR FOR THIS TEST IS NOT 90 MIN — IT IS ~89 MIN, ALREADY SET TONIGHT WITH THE STACK UP**
  (20:14→21:43 IST, full stack, zero faults). A stack-off quiet stretch must clearly EXCEED that to mean
  anything. Judge on **fault COUNT over a fixed window**, never on "it's been quiet".
- 🔑🔑 **FC-REBOOT DETECTOR (found 08-21, no MAVFTP needed):** every hardfault reboots the FC, and the reboot
  shows up on the companion **4 s later** as BOTH a `create_participant` line in `journalctl -u microxrce-agent`
  AND a `Started rover-autonav-mode.service`. Verified against faults #28 (19:29:47+4 s) and #29 (20:13:48+4 s).
  ⚠️ **Not valid while the agent/stack is being restarted by hand** (a companion-side restart makes the same line),
  and ⛔ **the timesync `estimated_offset` is NOT FC boot time — it re-anchors on DDS session restart. Don't read uptime off it.**

## 🔴 FAULT #30 — 2026-08-21 18:00:36 UTC (23:30:36 IST), `uxrce_dds_client`
`cfsr=0x00000082` = **DACCVIOL + MMARVALID** ⇒ **MMFAR = `0x0000000c` = NULL + 0x0c.**
`pc=0x301625e2` (valid FlexSPI XIP), `sp=0x20035888` **user stack Valid, nowhere near the guard**.
⇒ **Extends the NULL+small-offset family to 11 of 12 valid faulting addresses** (+0,+4,+8,+0x0a,+0x0c,+0x10,+17,+32,−1,−28).
**Confirms the unchecked-failed-allocation read again; kills stack exhaustion again.**
🔑 Landed **~24 min after the stack came back up** (23:06 IST) and ~7 min after `vision_streaming` restarted (23:23:59).
⚠️ It took **TWO pull rounds** — first came down as a 21 988 B stub, second VERIFIED at 44 793 B. **Never delete off round 1.**

## ⏭ EARLIER RESUME NOTE (session ended 08-20 ~19:35 UTC, operator called it a night)
Two agreed actions, **neither started**:
1. **Sample `sess103/log101.ulg` (78.8 MB) header + tail** — the only possible long-window
   `ram_usage` trace (45-90 min if it closed cleanly). ✅ Tool is **written and ready**:
   `scratchpad/ftp_chunk.py` (raw FILE_TRANSFER_PROTOCOL offset reads; pymavlink's `cmd_get`
   can only read from offset 0). Pull first ~400 KB for cpuload's `ADD_LOGGED_MSG` id, then the
   last ~400 KB, and scan the tail for `msg_size=18, type='D'` records (payload =
   `uint64 timestamp, float load, float ram_usage`). ⚠️ **If the pull size < 78 805 073, that log is
   itself fault-terminated (§18.1) and there is no trace to get.**
2. **Delete only the 9 byte-verified ULogs from the card; KEEP `sess103/log101.ulg`.**
🔴 **Faults were coming every ~7 min and the rover was ARMED when we stopped** — expect a pile of
new `fault_*.log` on the card tomorrow; pull+delete them first with `ftp_pull_faults.py --delete`.

📕 **Full evidence and reasoning: `~/ros2_ws/docs/fc_hardfault_analysis.md` §17.13-§17.16. READ IT before acting.**
This file is the pointer-level summary; the doc is the record.

## ⛔ THE HEADLINE WAS WRONG — RETRACTED 08-20
**It is NOT stack exhaustion.** Across all **21** logs the stack watermark reads FULL, but **sp at
the moment of the fault is only 4-29 % deep**. A real overflow faults with sp *at* the guard —
that never happens once. The watermark reading full means **the colouring was destroyed by
corruption**, not consumed. ⛔ **Raising the `uxrce_dds_client` stack will NOT fix this** (PX4
#22323 is not our mode); keep it only as free headroom if flashing anyway.

## 🔴🔴 ROOT CAUSE SIGNATURE (2026-08-21): NULL-POINTER DEREFERENCE
🔑 **PX4 MISNAMES two fault-log fields: `mmfsr`/`bfsr` actually hold MMFAR/BFAR — the FAULTING
ADDRESS** (`board_crashdump.c:337`). Read them only when CFSR bit 7 (MMARVALID) / bit 15 (BFARVALID)
is set. ⛔ **My "the capture struct is trashed" claim is RETRACTED — those values were the evidence.**
**6 of the 7 faults that captured a valid address dereferenced NULL + a small offset:
`+4`, `+8`, `+17`, `+32`, `-1`, `-28`** (the last two are the `container_of`/list-entry pattern);
the 7th was a wild pointer. **Random corruption does not produce that cluster — `ptr->field` with a
NULL `ptr` does.** The two `pc=0x00000000` faults are the same bug calling a NULL function pointer.
⇒ **This is a SOFTWARE defect (an unchecked NULL), not an electrical/XIP fault** — which is why
every board/SD/power/CAN/companion swap changed nothing.
🔑🔑 **FAULT #25 (08-20 19:14:58 UTC, `mavlink_if1`) IS THE STRONGEST EVIDENCE YET — CAUGHT IN THE ACT:**
DACCVIOL + **MMARVALID**, **MMFAR = `0x00000000`** (offset ZERO), `r0=0` (the destination arg),
`r1=0x10` (a length), `r6=0x10101010` (a word-fill pattern), `pc=0x00001cc4` = **ITCM, where
`memcpy`/`memset` live**. ⇒ **a block copy/fill into a NULL destination = an allocation that returned
NULL and was never checked.** Fault #26 adds **MMFAR = `0x0000000a`**. ⇒ the §17.18 table is now
**9 valid addresses, 8 of them NULL + a small offset** (+0, +4, +8, +10, +17, +32, −1, −28).
⚠️ #25 hit while I ran sustained MAVFTP — **do NOT promote that to "FTP causes faults"** (§17.12
already falsified companion correlation; #22-24 happened with nothing touching the FC). It is
**victim-shift + a load-dependent allocation site**. ⏭ but heavy FTP is now a candidate **provocation**
test for on-demand reproduction.
🔴 **LEADING MECHANISM: heap exhaustion / a failing allocation whose NULL return is unchecked.** It
alone explains task-agnostic victims, the 25-50 min delay to the first fault, the burst-then-quiet
shape (reboot resets the heap), survival across every swap, and the 08-15 date (2.1.0 added topics
and modules = more RAM).
⛔⛔ **THE ULog `ram_usage` TEST IS DEAD — IMPOSSIBLE BY CONSTRUCTION (08-20, §18.1). DO NOT RE-QUEUE IT.**
Two structural blockers: **`SDLOG_MODE=0` ⇒ PX4 logs ONLY WHILE ARMED** (every fault was at idle), and
**a fault-terminated ULog HAS NO DATA IN IT** — PX4 preallocates the `.ulg` and writes through a RAM
buffer, so a hardfault leaves the FAT size intact but only the ~21 KB header written. 🔑 **A size
mismatch between the FTP listing and the pull IS the fault-terminated signature** (measured 3×,
identical byte count on every retry: 441 809→20 793, 1 153 661→25 812, 2 544 919→21 988).
✅ Cleanly-closed logs say heap **plateaus at 23.4 % and is FLAT to 4 dp** — but the longest window is
**4.7 min armed** vs faults at 17-50 min, and **`ram_usage` cannot see FRAGMENTATION**. ⇒ heap hypothesis
NOT killed; **fragmentation is now the leading variant**, invisible to that metric.
⏭ **REPLACEMENT TEST: add `cpuload` to `dds_topics.yaml`** (`grep -c cpuload` = 0 today) and bag
`/fmu/out/cpuload` on the companion, where the crash cannot eat it. **Joins the queued
`vehicle_angular_velocity` + `system_power` — one flash, FOUR items.**

**The fault classes are instruction-side:** UNDEFINSTR ×4 · INVSTATE ×2 (both with **`pc = 0x00000000`**,
i.e. branched through a null pointer) · IBUSERR · NOCP ×5 · DACCVIOL ×7, spread over **SEVEN
unrelated tasks** (`uxrce_dds_client`, `wq:INS0`, `wq:uavcan`, `wq:nav_and_controllers`,
`mavlink_if1`, `hpwork`, `wq:ttyS3`), and **every faulting pc sits in the `0x30xxxxxx` FlexSPI XIP
region**. That is corrupted
code fetches and corrupted pointers — the NXP RT1176 XIP class. The fault-capture struct itself is
sometimes trashed — mmfsr/bfsr reading `0xbbd7b352`, `0xffffffff`, `0xffffffe4` (impossible for
8-bit fields) in three separate logs.

🔑🔑 **TIMING — READ THIS BEFORE JUDGING ANY SOAK.** Faults come in **bursts (~3 min apart)**
separated by **long quiet gaps: a 50.6-minute gap occurred naturally on 08-20 with no
intervention**, and fault #21 landed at 50.6 min of uptime. ⛔ **A quiet stretch under ~90 min is
NOT evidence of a fix** — the 41-min clean run on 08-20 looked encouraging and meant nothing.
**Soak ≥90 min and judge on fault COUNT over a fixed window, never on "it's been quiet a while".**

## ✅ ELIMINATED — BY TEST OR BY DATE. DO NOT RE-SUSPECT ANY OF THESE
- **3 FC boards** (FC #1, the loaner, FC #2) — all fault identically. ⛔ **NEVER SWAP THE FC AGAIN.**
  🔴🔴 **BUT OPERATOR 08-20: THE SAME OLD IMU SENSOR BOARD WAS CARRIED ACROSS ALL THREE SWAPS.**
  ⇒ **"3 boards eliminated" IS NOT "the FC hardware is eliminated".** On an FMUv6X-class board the
  IMU module is a **separate, detachable board on a board-to-board connector**, and that module —
  plus its connector — is a **SURVIVING CONSTANT that has never been changed.** It now sits
  alongside param contamination as an un-eliminated suspect, and it is the better fit for
  **`wq:INS0` being a repeat faulter** (fault #22 tonight). ⛔ **Do not cite the board swaps as
  covering the sensor board.**
- **Both SD cards.**
- **Firmware version** (rolled back) **and the binary itself** — operator 08-20: the restored build
  is the **old custom build that ran ~3 months clean**, not a fresh rebuild. The binary is not the variable.
- **VESC / CAN entirely** — operator removed all CAN interfaces from the motor controllers *before*
  the 08-20 boot, and it still faulted 3× that evening. Confirmed from PX4's side: `/fmu/out/esc_status`
  declared but **zero messages** against a live `/fmu/out/input_rc` **100.2 Hz** baseline.
  ⇒ **the §12/§13/§14 CAN-load family is dead as a trigger, by removal.** It survives only as bus *margin*.
- **Both power modules** — the new one went in **Mon 2026-08-17**, which is **1-2 days AFTER the
  fault era began** (2.1.0 flashed Sat 08-15; nine faults Sun 08-16). Ledger: **9 faults on the old
  module, 12+ on the new** ⇒ not the trigger, and it fixed nothing.
- **The companion, completely** — steady traffic (§16.3) and bursty FTP/shell/DDS load (§17.12).
  🔑 The 10/10 "every fault inside a Claude session" correlation was a **BASE-RATE TRAP**: with faults
  every 3-6 min and near-continuous debugging, overlap was guaranteed. A controlled soak falsified it.
  08-20 confirms it again — 3 faults with the normal stack up and no Claude, FTP or shell at all.

🔑 **VICTIM-SHIFT IS NOT PROGRESS.** With CAN gone `wq:uavcan` stopped faulting — because it is now
idle, not because anything was fixed. **The faulting task tracks which task is BUSY, not which is
broken.** ✅ **Confirmed 08-20 23:35: fault #21 hit `wq:ttyS3`, a serial work queue — a brand-new
victim, exactly where the load moved once CAN went away.**

## 🔴 THE ONLY SUSPECT LEFT: PARAM CONTAMINATION
2.1.0's param migration ran **08-15**, params live in FC storage, and **rolling firmware back does
NOT roll params back** — so the restored build now runs with a param set the clean era never had.
`wq:INS0` (the EKF/INS queue) being a repeat faulter fits a contaminated EKF set.

⛔⛔ **THE OBVIOUS TEST IS UNSAFE — DO NOT LOAD `PXlabs_..._tested_2026-05-29.params`.** Diffed it
against the live FC 08-20 (read-only): it is a **PRE-TUNING** snapshot. Loading it **zeroes every
rover gain** (`RO_SPEED_P`/`RO_YAW_P`/`RO_YAW_RATE_P`/`RO_MAX_THR_SPEED` are all 0 in it), **moves
`RC_MAP_KILL_SW` from ch12 to ch8** — the S1-validated kill switch would no longer be the operator's
switch — and flips the receiver SBUS↔CRSF (likely total RC loss). Any param test must be
**selective**, preserving the RC/kill-switch and rover-gain blocks.
🔑 **And the diff shows NO smoking gun:** 108 differ, 42 are `CAL_*`/device-ID (expected, FC #2
fitted 08-18); the live-only params are firmware artifacts (`COM_MODE*_HASH`, `_HASH_CHECK`) and the
file-only ones are the VESC/DroneCAN node params, absent because CAN was removed.
🔑 **The hypothesis itself is now in doubt: FC #2 was fitted 08-18, AFTER 2.1.0's 08-15 migration**,
and a new board has its own param storage (`COM_FLIGHT_UUID` live 75 vs 1141 in the file).
⏭ **ASK THE OPERATOR FIRST (a question, not a wipe): how were FC #2's params loaded on 08-18 — a
QGC backup, and from when? this repo file? by hand?** That decides whether contamination could even
have crossed the board swap. Soak **≥90 min** whenever a test does run. ⚠️ **Any reset must re-set `UXRCE_DDS_CFG`/serial or DDS will not come back.**
⚠️⚠️ **NEEDS OPERATOR SIGN-OFF FIRST — THIS FC IS SHARED WITH THE DRONE.** A factory wipe is not
rover-only; the drone's own `EKF2_*` set must be planned for before anything is erased.

## 🔴 The measurement gap
**The FC's own 5 V rail has never been measured and is currently unobservable.** PX4 does not stream
`POWER_STATUS` (60 s of requesting extended-status returned nothing), and `system_power` is **not in
`dds_topics.yaml`**. Battery is fine and steady (25.086 V ±6 mV at idle) but that is the pack, not
the rail the XIP mechanism would care about. The only route today is `listener system_power` in a
MAVLink shell — ⛔ **don't spend the one-shell-per-boot on it casually.**
⏭ **Add `system_power` to `dds_topics.yaml` alongside the queued `vehicle_angular_velocity`
(line 60) on the next flash** — one flash, three items, rail margin becomes continuously visible.

## Tooling and traps
- ✅ **Puller: `~/ros2_ws/tools/ftp_pull_faults.py`.** `--delete` does list → pull → **verify** →
  delete **with a fresh listing every round**. 🔑 **Never delete off a stale listing** — that is how
  4 logs were lost on 08-19, and on 08-20 one log came down truncated **three times** before completing.
- 🔑 Fault filenames are **UTC** (IST = +5:30). Trailer is **`END Fault Log`, uppercase**.
- 🔑 **A hardfault ALWAYS writes `fault_*.log`** — no file means no hardfault.
- 🔴 `fc_fault_backup.py` is broken twice over (`list_result`, trailer case). Don't reach for it.
- 🔑 `f0889f3d` in a fault log = **"2.1.0 in disguise"** (dirty-tree build, stale version string;
  that source is UNRECORDED anywhere). `a52c38b` = the 3-month-clean 2.0.0 build.
- Archive: **`~/fc_faults/` (30 logs)**. Card emptied + verified clean again **08-21 22:0x local** (round-2 re-list
  returned 0). Snapshot of the pre-pull 27 in `~/fc_faults_backup_20260821_220223/`.
  ⚠️ 3 logs are permanently INCOMPLETE (no `END Fault Log` trailer, 23-34 KB not ~44.8 KB):
  `fault_2026_08_16_05_01_15`, `_05_02_42`, `_09_53_36`. **They are already off the card — cannot be re-pulled.**
- 🔴🔴 **#28-#29, 08-21 (UTC 13:59:47 + 14:43:48, 44 min apart) — BOTH ARE INSTRUCTION-FETCH FAULTS,
  i.e. a CALL THROUGH A CORRUPTED FUNCTION POINTER, not a data deref:**
  - #28 `wq:nav_and_controllers`, `cfsr=0x00000100` = **BFSR IBUSERR**, `pc=0x250330fc` **and `r3=0x250330fd`**
    ⇒ `pc = r3 & ~1`: an **indirect call through the garbage pointer sitting in r3**.
  - #29 `hpwork`, `cfsr=0x00020000` = **UFSR INVSTATE**, `pc=0x00000010` (**NULL+0x10**), `lr=0x3007a235`
    (valid FlexSPI flash) ⇒ **called a NULL function pointer from good code.**
  - 🔑 **Extends the NULL+small-offset family to 10-of-11 valid faulting addresses.** Confirms the
    §17.13 read: **instruction-side corruption / unchecked failed allocation**, NOT stack exhaustion.
  - 🔑 **Faulting task moved AGAIN** (`nav_and_controllers`, `hpwork` — not `wq:INS0`). **Victim shifts
    with whoever is busy; do NOT read a task name as the defective component.** ⇒ this neither
    supports nor clears the IMU-board suspect — **`vehicle_imu_status` `error_count` is still the test.**
  - ⚠️ **These faults are from 08-21 with CAN RETURNED.** Do NOT score them against the 08-20 no-bus
    runs — different test condition. CAN stays eliminated on the 08-20 evidence regardless.
- **ULogs: `~/fc_ulogs/`, 9 of 10 session logs pulled.** Not pulled: `sess103/log101.ulg` **78.8 MB**
  (~51 min at the measured **25 KB/s** MAVFTP rate). ⚠️ 3 of them are fault-killed ~21 KB stubs (§18.1).
- ⚠️ **Which link `ttyS3` serves is NOT RECORDED** anywhere. `UXRCE_DDS_CFG=103` (DDS on TELEM3),
  `MAV_0_CONFIG=101`, `MAV_1_CONFIG=102`, `GPS_1_CONFIG=201`; the ttySN→port mapping is
  board-specific and unconfirmed. Confirm it next time a MAVLink shell is open anyway.
- ✅ **08-21 CHECKED: NO COMPANION SERVICE WAS ADDED OR CHANGED DURING THE FAULT ERA. Closed — don't re-run this.**
  Fault era began **08-15/16**; the **newest unit on the box is `rover-scan-3d.service`, 2026-08-01** — 2 weeks earlier.
  Additions per the operator's own `/etc/sid.conf` changelog: the **6 rover units on 22/07 + 01/08**, and the last
  functional edit was the `rover-camera` drop-in `10-point-cloud-decimation.conf` on **08-08**. In 08-13..08-17 there
  were **no new units, no user units, no cron, no apt/dpkg installs.** Only unit-tree activity on 08-16 was **snapd
  refreshing its own `.mount`** (00:24, with a daemon-reload); a 15:56 dir-mtime bump had **NO daemon-reload**, so
  nothing was enabled/disabled into effect. ⇒ **independent support that the companion is not the trigger**
  (its 10/10 correlation was a base-rate trap). ⚠️ Limits: mtimes prove last-modification, not that a unit never
  existed and was removed; and a service can change BEHAVIOUR via config without its unit file moving.
- 🔑 **`/etc/sid.conf` = the operator's system changelog (v1.3→v2.2), with a `.bak-<date>` per edit.** It is the
  authoritative "what changed when" record for the companion — **read it before reconstructing any timeline from
  file timestamps.** Not in the two manuals; not auto-synced by me.
- 🔴 One `mavlink_shell.py` per FC boot — see [[mavlink_shell_session_exhaustion]].
- Related: [[rc_ch10_reboots_companion]] (check CH10 before blaming any reboot).
