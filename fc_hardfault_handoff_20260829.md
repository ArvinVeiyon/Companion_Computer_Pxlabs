# FC Hardfault Campaign — Debugging Handoff (COMPANION → QGC-PC)

**Date:** 2026-08-29
**From:** COMPANION side (Vind-Roz, RPi5) — owned the SWD rig, the fault-log corpus and the analysis tooling
**To:** QGC-PC side — to write this up in the PX4 repo (`PXLABS_qgroundcontrol` docs / `PXLABS.md` in the
firmware fork) and to cut the bugfix release note
**Subject:** Intermittent hardfaults on NXP FMU-V6XRT (MIMXRT1176), 2026-08-16 → 2026-08-29, and the fix

> **Read the "Verification status" section (§9) before writing the word "fixed" anywhere.** The evidence is
> strong but the 8-hour proof bar was not yet cleared when this handoff was written, and this campaign has
> produced three prior false "fixes." Fill in §9 from the live soak before publishing.

---

## 1. One-paragraph summary

The FMU-V6XRT ran the PX4 application **XIP (execute-in-place) from external octal NOR flash over FlexSPI
at 200 MHz DDR**. The i.MX RT1176 **boot ROM does not reliably centre the FlexSPI DLL delay used to sample
the flash DQS read strobe**, so the read window was off-centre and instruction fetches failed rarely and
randomly. The CPU therefore executed instruction words that differed from what was stored in flash. This
surfaced as an intermittent, unattributable storm of UsageFault / MemManage / BusFault hardfaults — median
5.4 minutes between faults — that survived four flight-controller board swaps, two physical sites, a
companion-computer swap, a factory parameter reset and an SD card reformat. It is fixed upstream by
**PX4 PR #28141** (Peter van der Perk, NXP), which adds a boot-time DLL calibration sweep. We cherry-picked
that commit onto our v1.17.0 fork.

---

## 2. System under test

| | |
|---|---|
| Board | NXP FMU-V6XRT, MIMXRT1176DVMAA (1 GHz speed grade — read off the chip by the operator) |
| Core clock | **996 MHz measured**, not assumed — `ARM_PLL_CTRL @ 0x40C84200 = 0x200060A6` → `DIV_SELECT=166` → 24 MHz × 166 / 4 |
| App location | **XIP from external Macronix octal NOR over FlexSPI1**, app `.text` from `0x30022000` |
| Firmware | `pxlabs-v1.17.0-r2-Beta`, git `a52c38b07d`, build datetime `May 31 2026 18:19:40` |
| Also reproduces on | **stock upstream PX4 v1.17.0** ⇒ PXLABS vendor changes are not implicated |
| Companion | Raspberry Pi 5, ROS 2 Jazzy, uXRCE-DDS over UART + MAVLink |
| Debug | NXP MCU-Link (CMSIS-DAP, `1fc9:0143`), pyocd 0.45.1, target `mimxrt1170_cm7` |

---

## 3. The symptom, at scale

**62 archived `fault_*.log` files** pulled off the SD card over the campaign.

**Fault class (all 62, read from the `Type:` field — this field classifies every fault and we were not
reading it for the first week):**

| Class | Count | Handler |
|---|---|---|
| UsageFault | 39 | `imxrt_usagefault()`, `chip/imxrt_irq.c:272` |
| MemManage | 19 | `arm_memfault.c:101` |
| BusFault | 4 | `imxrt_busfault()`, `chip/imxrt_irq.c:263` |

**CFSR bits over the 48 logs that resolve against our ELF:**

| Bit | Count |
|---|---|
| `DACCVIOL` | 15 |
| `MMARVALID` | 15 |
| `UNDEFINSTR` | 11 |
| `INVSTATE` | 8 |
| `NOCP` | 8 |
| `UNALIGNED` | 3 |
| `IACCVIOL` | 2 |
| `IBUSERR` | 1 |

**Rate (measured from the 45 logs with a good clock; 17 carry a `1970-01-01` bad clock and were excluded —
including them makes the statistics garbage). Era 2026-08-16 05:01 → 2026-08-24 18:35 UTC, 38 usable
inter-fault gaps, dormancy > 12 h dropped:**

- **median 5.4 min · mean 37.8 min · p75 22.9 min · p90 73 min** — a busy hour holds ~12 faults
- longest quiet gap ever observed in the fault era: **437 min (7.3 h)**; 2nd 6.5 h; 3rd 4.8 h
- **P(quiet ≥ 1 h) = 15.8% · ≥ 2 h = 13.2% · ≥ 4 h = 7.9% · ≥ 7 h = 2.6% · ≥ 8 h = 0.0%**

**This is where the 8-hour proof bar comes from, and why it is not negotiable.** Anything shorter has
already happened *during* the fault era.

---

## 4. What was eliminated, and by what measurement

Every item below is dead **by test**, not by argument. None of these should be re-proposed.

| Suspect | How it died |
|---|---|
| **A bad board** | Faults on **4 different FC boards**, including one with a different IMU |
| **EMI from the rover** (ESCs, motors, WFB radios, CAN) | FC removed from the vehicle, taken to a **second site ~5 km away**, powered by **USB only** — and it faulted **within 10–15 min**, statistically indistinguishable from on-vehicle (median 5.4, p75 22.9). A contributing cause must move the rate when removed; this moved it by **nothing**. It has now faulted in two independent EMI environments. |
| **Power harness / FC supply rail** | Same run — not on the harness, USB-powered |
| **The charger** | Verdict withdrawn by the operator; faults continued without it |
| **The companion computer** | Companion swapped; the **worst-ever measured fault rate** followed the swap |
| **CAN / UAVCAN / ESCs** | A/B with the CAN bus disabled — victim task map shifted, fault rate did not |
| **MAVLink and the FTP log-puller** | Screened; faults continue with the puller idle |
| **PX4 parameters** | Full factory reset performed 2026-08-22; parameters restored and verified 2026-08-25; faults continued across both |
| **SD card format** | Windows reformat gave ~1 h of quiet (P = 15.8%, i.e. noise); faults returned at **full rate** — one fired within ~18 s of re-arming the catcher |
| **Thermal / no fan in the casing** | The bench run above is the largest available thermal delta — FC bare, open air, no casing, different building — and the rate did not move. Temperature survives only as a *modulator*, not a cause. |
| **The debugger itself** | SWD was first attached 2026-08-27 00:15. **All 62 logs predate it.** |
| **Speed grade / overclocking** | Operator read the part marking: `MIMXRT1176DVMAA` = 1 GHz grade. 996 MHz measured from the PLL registers is legal. |
| **Static FPU / MPU misconfiguration** | Measured **live on the running target and again at the moment of a fault**: `CPACR 0x00F00000` (CP10=CP11=0b11, FPU fully enabled), `FPCCR 0x00000000`, `CCR 0x00070200`, `MPU_CTRL 0x00000007`. NuttX's `arm_fpuconfig.c` deliberately clears ASPEN/LSPEN and force-sets `CONTROL.FPCA=1`; all 62 logs read `control:0x00000004` and `exe return:0xffffffe9`, unanimously matching that design. |
| **Corruption of the stored flash image** | Flash-vs-ELF diff over SWD at the faulting address: **0 bytes differ from the ELF, 0 bytes differ between two consecutive reads** |
| **A bad flash page / worn erase block** | **42 unique faulting PCs spanning `0x30069848` → `0x30269230` ≈ 2.1 MB of `.text`** — essentially the whole image, with only a handful of repeats. Damaged storage would cluster. This does not. |
| **`.ram_vectors` folded into `.itcmfunc` ⇒ corrupted vector fetch** | The linker-script fact is real (`script.ld:86`), the conclusion is dead. **`HFSR.VECTTBL` is never set** — n = 62 logs + 3 live catches; 61× `hfsr:0x00000000`, 1× `0x40000000` (FORCED only). Second, independent kill: the `.itcmfunc` copy happens **once at boot**, so corruption would be static and deterministic for that boot; our faults are intermittent over hours. |

---

## 5. The decisive measurement — a fault caught live over SWD

Vector catch armed via `DEMCR` (`VC_NOCPERR|VC_STATERR|VC_CHKERR|VC_MMERR|VC_BUSERR|VC_INTERR|VC_HARDERR`),
halting the core at the fault. Three faults were caught this way on 2026-08-27.

**Caught fault, `caught_20260827_010134.txt`:**

| Field | Value |
|---|---|
| `DFSR` | `0x8` = VCATCH — confirms the vector catch fired, not a coincidence |
| `CFSR` | `0x00010000` = **UsageFault: UNDEFINSTR** |
| Stacked (true) faulting `pc` | **`0x300feac6`** |
| Instruction at that address | **`vfma.f32 s0, s3, s5`** |
| Function | `sym::PredictCovariance<float>`, `predict_covariance.h:91` (EKF2 covariance, task `wq:INS0`) |
| **`CPACR` read at fault time** | **`0x00f00000`** — CP10 = CP11 = 0b11, **FPU enabled** |
| `FPCCR` / `CCR` / `MPU_CTRL` | `0x0` / `0x00070200` / `0x7` — all nominal |
| Bytes at `0x300feac0`, read live ×2 | `1e 1a d4 ed e1 1a a1 ee a2 0a dd ed 14 1a 8d ed` |
| Same bytes from the ELF | **identical** |

**An enabled FPU raised `UNDEFINSTR` on a legal, correctly-stored `vfma.f32`. That is architecturally
impossible if the core fetched and decoded what is actually in memory.**

⇒ What the core *received* differed from what is *stored*. The defect is on the **instruction fetch /
execute path**, and it is transient and invisible afterwards.

### 5.1 Why the corpus agrees — `NOCP` is the same phenomenon wearing a different CFSR bit

All **8/8** `NOCP` faults in the corpus are on **real FPU instructions** — no exceptions:

| pc | instruction | function |
|---|---|---|
| `300fe61e` | `vstr s2,[sp,#256]` | `sym::PredictCovariance<float>` |
| `300fe67e` | `vldr s9,[sp,#356]` | `sym::PredictCovariance<float>` |
| `300fe57e` | `vldr s19,[r4,#1008]` | `sym::PredictCovariance<float>` |
| `300fe47e` | `vldr s19,[r4,#148]` | `sym::PredictCovariance<float>` |
| `300fdfbe` | `vfma.f32 s20,s14,s26` | `sym::PredictCovariance<float>` |
| `300fde7e` | `vfma.f32 s6,s5,s28` | `sym::PredictCovariance<float>` |
| `301b551e` ×2 | `vmul.f64 d9,d1,d9` | `MapProjection::project` |

Two more FPU instructions faulted as `UNDEFINSTR` rather than `NOCP`: `301b550a` = `vpush {d8-d15}`
(the FP prologue of `MapProjection::project`) and `300bbb3e` = `vmov s14,r3`.

**The mechanism that explains this:** `CPACR` enables **only CP10/CP11**. VFP instructions carry a
coprocessor field in the encoding, so **corrupting a bit or two of that field turns a VFP instruction into
an access to a disabled coprocessor — which is exactly `NOCP`.** This predicts `NOCP` appears almost
exclusively on FP instructions: **measured 8/8**. The competing "the FPU was disabled" explanation requires
a wrong `CPACR`, and `CPACR` was **measured correct at the moment of the fault**.

The same story covers the rest of the corpus: mid-instruction PCs (7/48), PCs outside every executable
section (5/48), `pc = 0` and `INVSTATE` on even branch targets (8/48 null-ish) — a corrupt fetch
desynchronises decode or supplies a bad branch target.

### 5.2 The victim is exposure, not identity

`sym::PredictCovariance<float>` is not special. It is the **largest straight-line FP block in the image,
run at EKF rate**, so it takes the largest share of instruction fetches. Victim tasks across the corpus
track code density and duty cycle, not any one subsystem:

`uxrce_dds_client` 22 · `wq:INS0` 13 · `wq:uavcan` 10 · `wq:ttyS3` 4 · `mavlink_if1` 3 · `hpwork` 3 ·
`wq:nav_and_controllers` 2 · `wq:hp_default` 2. **45 of 62 faulting PCs are `0x30xxxxxx` — i.e. XIP.**

This is why the campaign was so hard to attribute: every subsystem looked guilty in turn.

---

## 6. The FlexSPI read path as we measured it

Read live over SWD from `FLEXSPI1 @ 0x400CC000` (base taken from `imxrt117x_memorymap.h:188`, not guessed):

| Register | Value | Decode |
|---|---|---|
| `MCR0` `+0x00` | `0xffffa030` | `RXCLKSRC=3` = external DQS pad ✓, `MDIS=0` (enabled) |
| `AHBCR` `+0x0c` | `0x00000078` | cacheable + bufferable + **prefetch** + read-address-optimisation all on |
| `FLSHCR0[0]` `+0x60` | `0x00010000` | 64 MB ✓ |
| `FLSHCR1[0]` `+0x70` | `0x00000021` | `TCSS=1`, `TCSH=1` ✓ matches the config block |
| `DLLCR[0]` `+0xc0` | `0x00400079` | `DLLEN=1`, `OVRDEN=0`, `SLVDLYTARGET=0xF` — NXP's recommended ≥100 MHz DQS setting |
| `STS0` `+0xe0` | `0x00000003` | sequence + arbitration idle |
| `STS1` `+0xe4` | `0x00000000` | **no latched controller errors** |
| `STS2` `+0xe8` | `0x00000b33` | `ASLVLOCK=1`, `AREFLOCK=1` ⇒ **DLL LOCKED**; **`ASLVSEL=12`, `AREFSEL=11`** |

**Boot XIP mode** (from `boards/px4/fmu-v6xrt/src/imxrt_flexspi_nor_flash.c`): Macronix octal NOR,
`serialClkFreq = 200 MHz`, **8-pad, DDR (= 400 MT/s)**, `ExternalInputFromDqsPad`, `dataValidTime = 0`,
**20 dummy cycles encoded `0x28`**. This is the most timing-critical XIP mode the part offers.

### 6.1 🔑 The load-bearing sentence — **LOCKED ≠ CENTRED**

On 2026-08-27 we looked at the table above and concluded the FlexSPI read path was **configured correctly**,
and we explicitly retracted "marginal/uncalibrated DLL" as a hypothesis. That retraction was **half right and
half wrong**, and the distinction is the whole bug:

> "Locked and per-recommendation ≠ has margin at this temperature on this board. It only kills the
> **config-defect** version of the hypothesis, not transient corruption itself."

`ASLVLOCK`/`AREFLOCK` tell you the DLL **locked**. They tell you **nothing about where in the valid read
window the sampling point landed.** A DLL can lock perfectly onto a delay that sits near the *edge* of the
window, and then a small shift with temperature or supply pushes individual reads outside it. That is
exactly the hole PR #28141 fills.

**Write this up carefully in the PX4 repo.** Anyone else debugging this will read `STS2`, see both lock bits
set, and cross the DLL off their list — as we did, for two days.

---

## 7. The upstream fix

**PX4 PR #28141** — *"calibrate FlexSPI DLL read strobe at boot"*

| | |
|---|---|
| Author | Peter van der Perk (NXP) |
| Merged | 2026-08-04 |
| Commit | `9f4bc80006caf7d5d8bcf809b4ccd046fb5eded6` (not a merge commit; parent `caa1dc03`) |
| Files changed | **one** — `boards/px4/fmu-v6xrt/src/init.c`, +217 / −13 |
| Fixes | PX4 issue **#27735** |

**Mechanism, in NXP's words:** *"the boot ROM does not always place the DLL delay used to sample the flash
DQS strobe near the centre of the valid read window."*

**What the fix does:** a RAM-resident boot routine sweeps the DLL delay setting, reads a known pattern via a
direct FlexSPI command at each setting, and **picks the midpoint of the widest passing range**. It follows
NXP's required DLL update sequence (enter stop mode, `DSB`/`ISB`, **ERR011377 post-lock settle**), falls back
to the ROM's setting if the sweep fails, stores the result in `g_dll_cal`, and **logs the chosen value from
`board_app_initialize()`**.

### 7.1 Evidence match against PX4 issue #27735

Every one of these is a point of agreement between the upstream report and our corpus:

| Their report | Ours |
|---|---|
| `cfsr 0x00010000` UNDEFINSTR quoted verbatim | identical |
| `pc 0x2fb20542` "not a valid code address" | our garbage PCs `0x2fd930d2` / `0x250330fc` — same shape, just below the `0x30000000` XIP base |
| Load-dependent: 3–6 min while streaming vs ~30 min normal | our median 5.4 min / p90 73 min |
| Victim = the busiest task (mavlink/uORB) | ours: DDS / INS0 / uavcan |
| Stored bytes match the ELF — flash is fine, the *read* is wrong | measured identically, twice |
| `pc` and `lr` both `0x30xxxxxx` | same |
| — | our 42 unique PCs over 2.1 MB with no clustering = a *global* read-margin defect |
| — | **4 boards / 2 sites / USB-only changed nothing — because the ROM's DLL placement is identical on every board.** This finally explains the single most baffling fact of the campaign. |
| Temperature as a modulator | consistent (the read window shifts with temperature) |

⚠️ **Worth recording for anyone who follows:** the #27735 reporter blamed *heap corruption / a wild write*.
NXP overruled that with the DLL diagnosis. We were one step from the same wrong turn.

### 7.2 Why our build was exposed

Our firmware is **v1.17.0, built 2026-05-31 — it predates the 2026-08-04 merge.** Since this is a boot-ROM
behaviour, **v1.16.2 is affected too**; a "v1.16.2 looked clean" observation from 2026-08-29 ran for under an
hour (P = 15.8%) and is not evidence either way.

### 7.3 Free confirmation available on the first boot

The PR **logs the chosen DLL value**. We measured this board's ROM-selected values before the fix:
**`ASLVSEL = 12`, `AREFSEL = 11`** (from `STS2 = 0x00000b33`).

**If the calibrated midpoint differs materially from 12/11, that is direct, single-boot evidence that this
board's ROM setting was off-centre** — independent of any soak. Capture the boot console line and put it in
the release note. This is the cheapest confirmation available and it should not be skipped.

---

## 8. What we tried that did *not* work — record these so they are not retried

- ⛔ **`serialClkFreq` 200 → 100 MHz: the board does not boot at all.** The test was under-specified — the
  config block's **20 dummy cycles (`0x28`) and `TCSS=1`/`TCSH=1` are tuned for 200 MHz octal DDR**. Halving
  the clock without re-deriving the dummy-cycle count breaks boot regardless of the underlying fault. Do not
  re-queue this as a one-line test.
- 🟡 **`XECC` on the FlexSPI1 XIP region is never enabled.** `IMXRT_XECC_FLEXSPI1_BASE 0x4001c000` exists,
  but **there is no XECC driver in NuttX or PX4** — only address and CCGR defines. So nothing detects or
  corrects a bit error on the XIP read path; it propagates silently into the instruction stream. This is
  *consistent* with "silent, random, no trace", but it is the **absence of a detector, not evidence that
  errors occur.** Still worth raising upstream as a hardening request.
- 🟡 **`VDD_SOC` was never scoped.** `imxrt_clockconfig()` unconditionally calls
  `imxrt_pmu_vdd1p0_buckmode_targetvoltage(dcdc_1p0bucktarget1p15v)` = 1.15 V overdrive, correct for
  `BOARD_CPU_FREQUENCY 996000000` (note that define carries a `//FIXME`). **The setpoint is verified in
  code; the actual rail under load has never been measured.** Minor cosmetic bug found alongside: the
  comment says "and wait for it to stabilise" but there is **no delay after the call** — a startup race
  only, it cannot explain faults hours into a run.

---

## 9. Verification status — **fill this in before publishing**

As of **2026-08-29 08:41 IST**:

| | |
|---|---|
| FC booted | 2026-08-29 01:11:01 |
| FC uptime | **7.5 h** |
| Reboots detected | **0** |
| New fault logs | **0** (SD card baseline at soak start: **0 — clean**) |
| Load during the window | real, not idle — camera, `/scan`, `/scan_3d`, wheel odometry all running |
| Soak instrument | `~/ros2_ws/tools/fc_soak.py`, relaunched detached 08:37:21, counting reboots + new card logs |

**Against a corpus with a 5.4-minute median gap and a 73-minute p90, 7.5 hours clean under load is strong
signal, not noise.** But the pass mark is **8 continuous hours**, and the longest quiet gap ever seen
*during* the fault era was 7.3 h. **We are just short. Confirm the 8 h before the release note says "fixed."**

### 9.1 🔴 Open item the PC side must close

**The cherry-pick is not present in the companion's copy of the tree.** In `/home/roz/PX4-Autopilot` on
branch `pxlabs-fw`:

- `git cat-file 9f4bc800…` → *could not get object info* — the commit was never fetched here
- `boards/px4/fmu-v6xrt/src/init.c` mtime is **2025-08-03**, untouched
- `HEAD` is still `a52c38b07d` (r2-Beta), and there is no build directory

The running FC reports `flight_sw_version 1.17.0`, which a cherry-pick onto v1.17.0 would also report — so
the version string does not discriminate.

**PC side: please record, in the write-up and the release note —**

1. Which tree the flashed firmware was built from, and its **git hash**
2. Confirmation that `9f4bc800` (or an equivalent backport of it) is actually in that build
3. The **DLL value logged at boot** by the new calibration routine (§7.3) — and whether it differs from
   this board's ROM values `ASLVSEL=12 / AREFSEL=11`
4. Whether the SD card was cleared as part of the flash (the card baseline is now 0; it held 3 logs on
   2026-08-25)

Then the companion side will fold the answers back into the campaign record.

---

## 10. A separate, genuine bug worth reporting upstream on its own

**Do not conflate this with the DLL issue — it is independently fixable and probably real.**

15 of the 48 resolvable faults are `DACCVIOL`, and **7 of those have `MMFAR` at a small offset from NULL:
`0x00000000, 04, 08, 0a, 0c, 14, 20`**. Almost all are in `uxrce_dds_client`, and **4 are in
`ucdr_serialize_esc_status`** at `str rX,[r4,#8]` / `bl __memcpy_veneer`. Also seen in
`ucdr_serialize_vehicle_local_position`, `ucdr_serialize_vehicle_odometry`, `ucdr_serialize_input_rc`.

This has the shape of a **null-pointer dereference in the uXRCE-DDS serializers**, confirmed at instruction
level rather than just by symbol. It is a good candidate for its own upstream issue.

---

## 11. Tooling that produced this evidence (companion side, `~/ros2_ws/tools/`)

| Tool | What it does | Notes |
|---|---|---|
| `fc_fault_resolve.py` | `addr2line` pass over all 62 logs → function + file:line + inline chain | Report: `~/ros2_ws/docs/fc_fault_resolution_20260826.md` |
| `fc_fault_catch.py` | DEMCR vector catch, halt at the fault, dump CFSR/CPACR/FPCCR/MPU + bytes-at-pc diffed against the ELF + the stacked frame | The instrument behind §5 |
| `fc_soak.py` | Counted soak, correlated against companion process state; three detectors (new card log, FC uptime drop, companion ring buffer) | The instrument behind §9 |
| `ftp_pull_faults.py` | Safe MAVLink-FTP puller for `fault_*.log` | |

**These four are currently uncommitted, on branch `fix/collision-perception-health-gate` in `~/ros2_ws`.**
If the write-up references them, say so.

### 11.1 Traps in the analysis that cost us real time — worth a paragraph in the write-up

- **The ELF trap.** 48 of 62 logs are firmware `a52c38b0…`; **14 are `f0889f3d…`, for which we have no ELF.**
  Resolving the latter against the wrong ELF yields *confident nonsense*. `Build datetime` reads
  `May 31 2026 18:19:40` on **all 62 logs across two different git hashes** — trust the **hash**, not the
  datetime.
- **ITCM is mapped at `0x00000000`,** so `addr2line` happily names a plausible function for a null `pc`
  (`0x0` → `imxrt_get_pll1g`). Those are **aliases, not the faulting code.** 8 of 48 PCs are null-ish
  (`< 0x2000`). Any check of the form "does the faulting PC land in ITCM?" is a **false-confirmation
  generator**.
- **Vector catch halts in the *handler*, not at the fault.** The halted `pc` is the first instruction of
  `exception_common` (`arm_exception.S:145`, ITCM `0x83c`), `IPSR=6`, `lr=0xffffffe9`. Checking fetch
  integrity *there* tests the wrong address — our first dump did exactly that and its "MATCH" meant nothing.
  You must **unwind the stacked exception frame** (`lr` bit 2 selects MSP/PSP, bit 4 selects
  extended/basic; frame is `r0,r1,r2,r3,r12,lr,pc,xPSR` then S0–S15 + FPSCR) to get the true faulting `pc`.
- **With a debug probe attached, an uncaught fault does not reboot — it wedges.** `SYSRESETREQ` is inhibited
  by the debug connection, so the core sits spinning in `up_systemreset()`. You must arm the vector catch
  for **every** fault class, and recover with a hardware reset (`-O reset_type=hw -c reset`); a plain reset
  does not clear it.

---

## 12. Suggested shape for the PX4-repo write-up

1. **Title it by the mechanism, not the symptom** — "FlexSPI DLL read-strobe off-centre causes intermittent
   XIP instruction-fetch faults on FMU-V6XRT". People searching will search the symptom (`UNDEFINSTR`,
   `NOCP`, `hardfault`), so put those words in the body.
2. Lead with **§5** — the live catch is the piece of evidence that makes the whole argument, and it is
   reproducible by anyone with a CMSIS-DAP probe.
3. Include **§6.1 (LOCKED ≠ CENTRED)** prominently. It is the single most useful warning in this document.
4. Include the **elimination table (§4)** — its value is telling the next person which two weeks of work
   they can skip.
5. Cross-reference **PR #28141** and **issue #27735** by number.
6. Keep **§10** (the uXRCE serializer null-deref) visibly separate so it is not lost as a footnote.
