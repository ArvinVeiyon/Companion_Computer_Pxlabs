---
name: fc_hardfaults
description: "FC hardfaults CLOSED 2026-08-29 — cause was the FlexSPI DLL read strobe, fixed by PX4 PR #28141; 2 items still open"
metadata: 
  node_type: memory
  type: project
  originSessionId: 42e05df1-d455-448f-b77b-66b31270019f
  modified: 2026-08-29T04:09:13.870Z
---

# FC HARDFAULTS — ✅ CLOSED 2026-08-29

**This file is the RESULT only.** The 1715-line debugging campaign was deliberately flushed on
2026-08-29 at the operator's instruction. **Nothing below is a live investigation — do not resume one.**

## The answer

**CAUSE:** the i.MX RT1176 **boot ROM does not CENTRE the FlexSPI DLL delay** that samples the octal-NOR
DQS read strobe. The app runs **XIP at 200 MHz octal DDR** (the most timing-critical mode the part offers),
so an off-centre sampling point made instruction fetches fail rarely and randomly ⇒ **the CPU executed
words that were not what is stored in flash.**

**FIX:** PX4 **PR #28141** (Peter van der Perk, NXP; merged 2026-08-04; commit `9f4bc80006c`; ONE file
`boards/px4/fmu-v6xrt/src/init.c`). A RAM-resident boot routine sweeps the DLL delay and picks the
**midpoint of the widest passing range**.

**SHIPPED:** flying build **`860013bab7`**, released as **`v1.17.0-2.1.0`** with `HARDFAULT.md` at the repo
root of `ArvinVeiyon/PXLABS_PX4-Autopilot`.
⛔ **`flight_sw_version` reads `1.17.0` WITH OR WITHOUT the fix — it cannot discriminate. Verify by GIT HASH.**

**PROOF (instrument-counted, `tools/fc_soak.py`):** 2026-08-29 09:11:49 IST — **480.7 min = 8.01 h, single
boot (01:11:02), 0 reboots, 0 fault logs**, card baseline clean, under real load (uXRCE-DDS + EKF2 + camera
+ `/scan` + `/scan_3d` + wheel odometry). Bar was 8 h because the fault-era distribution (38 gaps) gave
**median 5.4 min, p90 73 min, longest quiet gap ever 7.3 h, P(quiet ≥ 8 h) = 0.0%.**

## The two lessons worth carrying

🔑🔑 **`LOCKED ≠ CENTRED`.** I read FlexSPI `STS2` = both DLL lock bits set and `DLLCR 0x00400079` matching
NXP's recommended ≥100 MHz setting, called the read path "correctly configured", and **struck the DLL off
the suspect list for two days.** The lock bits say the DLL locked; they say **nothing about where in the
read window it landed.** My own caveat sentence ("locked and per-recommendation ≠ has margin at this
temperature on this board") was the load-bearing one and I under-weighted it against a table of
correct-looking registers.

🔑 **"4 FCs / 2 sites / USB-only moved the rate by NOTHING" was the CLUE, not the mystery.** I read it as
"hardware eliminated ⇒ must be our config" and never asked the right question: *what is identical across
every board?* Answer: the boot ROM. **When swapping the hardware changes nothing, suspect what the hardware
all shares.**

## ⏭ Still open — NOT covered by "resolved"

1. **`g_dll_cal` HAS NEVER BEEN READ** — the direct mechanism evidence is still missing. Symbol at
   **`0x20252774`** (BSS, 12 B) in build `860013bab7`. **The MCU-Link is UNPLUGGED** (no `1fc9:0143`, no
   `/dev/ttyACM*`). Ask the operator to reseat, then `--connect attach` (read-only, PX4 undisturbed) and
   read `g_dll_cal` + `FLEXSPI1 DLLCR/STS2 @ 0x400CC000` against the **pre-fix ROM baseline `ASLVSEL=12 /
   AREFSEL=11`** (`STS2 = 0x00000b33`, `DLLCR = 0x00400079`). ⛔ Don't accept the 57 MB ELF — the symbol
   address is enough. The PC side will fold the value into `HARDFAULT.md`.
2. **uXRCE-DDS NULL-DEREF is untouched by this.** 15 `DACCVIOL` in the corpus, 7 with `MMFAR` at small
   offsets from NULL (`0x00,04,08,0a,0c,14,20`), **4 in `ucdr_serialize_esc_status`**; also
   `ucdr_serialize_vehicle_local_position` / `_vehicle_odometry` / `_input_rc`. Its base rate was far below
   the DLL population, so **8 h of absence proves nothing about it.** Worth its own upstream issue.

## SWD rig — keep, it is what open item 1 needs

NXP MCU-Link (CMSIS-DAP, `1fc9:0143`) on the companion + **pyocd 0.45.1 in `~/pyocd-venv`** (venv; system
python untouched), target **`mimxrt1170_cm7`**, **ALWAYS `--connect attach`** (anything else resets/halts a
flying FC).
⛔ udev rule MUST be named `99-*` — a `50-*` file gets its MODE reset by `50-udev-default.rules` ⇒ "No
available debug probes". udev also preserves perms on an already-enumerated node: replug after installing.
🔑 **ONE PROBE = ONE SESSION** — a second concurrent `pyocd` call returns EMPTY OUTPUT, not an error.
🔑 Reusable attach cross-check: `ARM_PLL_CTRL 0x40C84200` must read `0x200060A6` (→ 996 MHz). Use it to
prove any attach + base address before trusting a register read.
⚠️ Probe USB is flaky — reseat the cable before blaming the target.
⛔ Only if a *catch* is ever re-armed (`tools/fc_fault_catch.py`): `--vc-all` is mandatory, because with a
probe attached an uncaught fault **cannot reboot** (SYSRESETREQ inhibited) and **wedges** in
`up_systemreset()`; cure is `pyocd ... -O reset_type=hw -c reset` (a plain reset does not work).

## Where the full record lives — go here instead of re-deriving anything

| What | Where |
|---|---|
| **The 1715-line campaign file** (all 41 sections, every eliminated suspect) | `git show e67fb32:memory/project_fc_hardfaults.md` in `~/codex-work` |
| **The write-up handoff** — symptom at scale, elimination table, live SWD catch, FlexSPI registers, #27735 match, analysis traps | `~/codex-work/fc_hardfault_handoff_20260829.md` |
| **Published record** | `HARDFAULT.md`, repo root of `ArvinVeiyon/PXLABS_PX4-Autopilot` |
| 62-log resolution report | `~/ros2_ws/docs/fc_fault_resolution_20260826.md` |
| Earlier analysis doc | `~/ros2_ws/docs/fc_hardfault_analysis.md` |
| Raw evidence | `~/fc_faults/` (62 logs), `~/fc_faults/caught/` (3 live SWD catches), `~/fc_soak/` |

⚠️ **One trap that survives in the raw logs:** 48 of the 62 are firmware `a52c38b0…`; **14 are `f0889f3d…`
and we have no ELF for them.** Resolving those against our ELF yields confident nonsense. `Build datetime`
reads identically on both — **trust the git hash, not the datetime.**
