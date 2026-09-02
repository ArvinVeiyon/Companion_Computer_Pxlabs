---
name: fc_hardfaults
description: "FC hardfaults CLOSED 2026-08-29 — cause was the FlexSPI DLL read strobe, fixed by PX4 PR #28141; all local evidence deleted 2026-09-02, record lives in HARDFAULT.md"
metadata: 
  node_type: memory
  type: project
  originSessionId: b80d31dc-3854-48b9-81c3-8a01be477e0a
  modified: 2026-09-01T19:42:16.789Z
---

# FC HARDFAULTS — ✅ CLOSED 2026-08-29. **DO NOT REOPEN.**

**This file is the RESULT only.** The campaign file, the 62 raw fault logs, the soak data, both
analysis docs and all 8 tools were **deleted 2026-09-02 at the operator's instruction.**
**Nothing below is a live investigation. Do not start one, and do not try to reconstruct one.**

## ⏭ RESUME HERE 2026-09-03 — THE PURGE IS ONLY HALF DONE

**The operator asked TWICE (09-02) to cut this down to "what resolved it and how" — RCA/analysis
narrative is NOT wanted. Pass 1 ran; pass 2 was interrupted before executing. Finish it.**

**⏭ STILL TO DELETE (found on the 2nd sweep, all confirmed hardfault-RCA only):**
- `~/fc_faults_backup_20260821_220223` — 1.2 MB, 27 fault logs
- `~/fc_faults_ftp` — empty dir
- `~/fc_firmware` — 62 MB, the **PRE-FIX** `CLEAN_v1.17.0-2.0.0` bin/elf/px4. ✅ **VERIFIED
  RECOVERABLE** from `pxlabs/pxlabs-v1.17.0-2.0.0` → `pxlabs/PXLabs_Firmware/*.{bin,elf,map,px4}`.
  🔑 It is the FAULTY build — keeping it is a reflash hazard, not an asset.
- `~/pyocd-venv` — 77 MB, the SWD analysis rig (its catch tools are already gone ⇒ orphaned)
- `/etc/udev/rules.d/99-cmsis-dap.rules` — inert once the venv goes (needs sudo)

**⛔ DO NOT DELETE — these are NOT hardfault RCA (judgment call, flag it if the operator disagrees):**
`~/fc_param_backups` (192 KB, 7 PX4 param files — MEMORY.md actively cites these) ·
`~/fc_ulogs` (11 MB, 13 flight logs — general vehicle data).

**⏭ THEN TRIM THE PROSE** in this file, `MEMORY.md` and `todos.md` §"FC HARDFAULTS" down to:
symptom signature → cause → fix → how to verify the fix is in → pointer to `HARDFAULT.md`.
**Cut the two lessons, the open-items section and the SWD rig block** unless the operator says keep.

**⏭ ONE GIT DECISION STILL OPEN (operator's call, do not act unasked):**
1. ✅ **DONE 2026-09-02** — `ros2_ws` deletions **COMMITTED** as `68f6280` on
   `fix/collision-perception-health-gate` (4 files, 1400 deletions), then **ff-merged to `main` and
   PUSHED** — all four refs at `68f6280`. The deletions net to zero against old main (added and
   removed on the same branch), so no trace of the evidence survives in the merged tree.
2. `codex-work`: the memory edits + the deleted handoff are **uncommitted and unpushed** (backup is
   manual by design). The **1715-line campaign file still lives in git history at `e67fb32`** — only
   a history rewrite removes it.

## The answer

**CAUSE:** the i.MX RT1176 **boot ROM does not CENTRE the FlexSPI DLL delay** that samples the
octal-NOR DQS read strobe. The app runs **XIP at 200 MHz octal DDR** (the most timing-critical mode
the part offers), so an off-centre sampling point made instruction fetches fail rarely and randomly
⇒ **the CPU executed words that were not what is stored in flash.**

**FIX:** PX4 **PR #28141** (Peter van der Perk, NXP; merged 2026-08-04; ONE file
`boards/px4/fmu-v6xrt/src/init.c`). A RAM-resident boot routine sweeps the DLL delay and picks the
**midpoint of the widest passing range**.

**SHIPPED:** flying build **`860013bab7`**, released as **`v1.17.0-2.1.0`**.
⛔ **`flight_sw_version` reads `1.17.0` WITH OR WITHOUT the fix — it cannot discriminate.
VERIFY BY GIT HASH.**

**PROOF:** 2026-08-29 — **8.01 h on a single boot, 0 reboots, 0 fault logs**, under real load
(uXRCE-DDS + EKF2 + camera + `/scan` + `/scan_3d` + wheel odometry). The bar was 8 h because the
fault-era distribution gave **median 5.4 min, p90 73 min, longest-ever quiet gap 7.3 h,
P(quiet ≥ 8 h) = 0.0%**.

## The two lessons worth carrying

🔑🔑 **`LOCKED ≠ CENTRED`.** FlexSPI `STS2` showed both DLL lock bits set and `DLLCR 0x00400079`
matched NXP's recommended ≥100 MHz setting, so I called the read path "correctly configured" and
**struck the DLL off the suspect list for two days.** The lock bits say the DLL locked; they say
**nothing about where in the read window it landed.**

🔑 **"4 FCs / 2 sites / USB-only moved the rate by NOTHING" was the CLUE, not the mystery.** I read
it as "hardware eliminated ⇒ must be our config" and never asked: *what is identical across every
board?* Answer: the boot ROM. **When swapping the hardware changes nothing, suspect what the
hardware all shares.**

## ⚠️ Two things "resolved" did NOT cover — now un-evidenced by choice

1. **`g_dll_cal` was never read** — direct mechanism evidence was never captured. Still reachable
   via SWD if it ever matters (symbol `0x20252774` in build `860013bab7`; MCU-Link + `pyocd` in
   `~/pyocd-venv`, target `mimxrt1170_cm7`, **always `--connect attach`** — anything else resets a
   flying FC). ⚠️ The catch tooling is deleted and the probe is unplugged.
2. **A uXRCE-DDS NULL-DEREF was seen in the same corpus and is untouched by this fix** (`DACCVIOL`
   at small offsets from NULL, several in `ucdr_serialize_esc_status`). Its base rate was far below
   the DLL population, so **the 8 h soak proves nothing about it.** ⚠️ **The 62-log corpus that
   evidenced it is deleted** — if it ever recurs, it starts from zero.

## The only surviving record

**`HARDFAULT.md`** at the repo root of **`ArvinVeiyon/PXLABS_PX4-Autopilot`**, branch/tag
**`pxlabs-v1.17.0-2.1.0`** (`244afd0`). 191 lines: symptom at scale, the full ruled-out table, the
live SWD catch signature, the soak numbers, and the open items. **Go there — do not re-derive.**

Related: [[debug_before_documenting]], [[test_before_concluding]], [[independent_rulers]].
