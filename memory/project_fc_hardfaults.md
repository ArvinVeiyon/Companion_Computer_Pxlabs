---
name: fc_hardfaults
description: "FC hardfault campaign — NOT stack exhaustion (that is retracted); it is instruction-side memory corruption, and after every hardware/firmware/CAN/power elimination the ONLY suspect left is param contamination dated 08-15"
metadata: 
  node_type: memory
  type: project
  originSessionId: 96448c77-71fd-43a5-9b04-11a764db5e77
  modified: 2026-08-20T18:03:24.605Z
---

# FC hardfaults — state as of 2026-08-20

📕 **Full evidence and reasoning: `~/ros2_ws/docs/fc_hardfault_analysis.md` §17.13-§17.15. READ IT before acting.**
This file is the pointer-level summary; the doc is the record.

## ⛔ THE HEADLINE WAS WRONG — RETRACTED 08-20
**It is NOT stack exhaustion.** Across all **20** logs the stack watermark reads FULL, but **sp at
the moment of the fault is only 4-15 % deep**. A real overflow faults with sp *at* the guard —
that never happens once. The watermark reading full means **the colouring was destroyed by
corruption**, not consumed. ⛔ **Raising the `uxrce_dds_client` stack will NOT fix this** (PX4
#22323 is not our mode); keep it only as free headroom if flashing anyway.

**The fault classes are instruction-side:** UNDEFINSTR ×4 · INVSTATE ×2 (both with **`pc = 0x00000000`**,
i.e. branched through a null pointer) · IBUSERR · NOCP ×5 · DACCVIOL ×6, spread over **six unrelated
tasks**, and **every faulting pc sits in the `0x30xxxxxx` FlexSPI XIP region**. That is corrupted
code fetches and corrupted pointers — the NXP RT1176 XIP class. The fault-capture struct itself is
sometimes trashed (mmfsr/bfsr reading `0xbbd7b352`, `0xffffffff`).

🔑 **BURST SHAPE: the first fault lands ~25-32 min after power-on, then they repeat every ~3 min.**
Something accumulates. **Any soak shorter than ~45-60 min proves nothing.**

## ✅ ELIMINATED — BY TEST OR BY DATE. DO NOT RE-SUSPECT ANY OF THESE
- **3 FC boards** (FC #1, the loaner, FC #2) — all fault identically. ⛔ **NEVER SWAP THE FC AGAIN.**
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
broken.** Expect `uxrce_dds_client` to dominate future logs for that reason alone.

## 🔴 THE ONLY SUSPECT LEFT: PARAM CONTAMINATION
2.1.0's param migration ran **08-15**, params live in FC storage, and **rolling firmware back does
NOT roll params back** — so the restored build now runs with a param set the clean era never had.
`wq:INS0` (the EKF/INS queue) being a repeat faulter fits a contaminated EKF set.

⏭ **THE TEST — this is now the whole investigation:** factory-reset params → load the repo set
`PXlabs_Differential_Rover_NXP_tested_2026-05-29.params` → soak **≥60 min**. ⚠️ **Re-set
`UXRCE_DDS_CFG`/serial after the reset or DDS will not come back.**
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
- Archive: **`~/fc_faults/` (20 logs)**. Card was emptied and verified clean 08-20 23:0x.
- 🔴 One `mavlink_shell.py` per FC boot — see [[mavlink_shell_session_exhaustion]].
- Related: [[rc_ch10_reboots_companion]] (check CH10 before blaming any reboot).
