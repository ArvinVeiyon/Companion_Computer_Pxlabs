# Release Note — `pxlabs-v1.17.0-r2.1` (bugfix)

**Prepared by:** COMPANION side, 2026-08-29
**For:** QGC-PC side to paste into `PXLABS.md` in the firmware fork and to publish with the tag
**Companion evidence pack:** `fc_hardfault_handoff_20260829.md` (same directory)

> **Naming:** the operator asked for "17.0.0 2.1.0". The fork's existing convention is `r1`, `r2-Beta`, so
> the next bugfix reads **`pxlabs-v1.17.0-r2.1`**. If you prefer the literal `pxlabs-v1.17.0-2.1.0`, rename
> consistently in the tag, the OEM version string and all three tables below — but pick one and use it
> everywhere.

> ⚠️ **Two fields below are marked `<FILL>`. Do not publish until they are filled** — see §"Before you
> publish" at the end. This campaign produced three prior false "fixes"; the release note is where that
> either gets caught or gets baked in.

---

## A. Changelog entry — paste at the top of the `## Changelog` section in `PXLABS.md`

```markdown
### pxlabs-v1.17.0-r2.1 — 2026-08-29 (Bugfix)

**Fixes the intermittent hardfault storm on FMU-V6XRT.** Cherry-picks upstream PX4 PR #28141
(`9f4bc80006caf7d5d8bcf809b4ccd046fb5eded6`, Peter van der Perk / NXP, merged 2026-08-04, fixes PX4
issue #27735) onto the r2-Beta base. Single file: `boards/px4/fmu-v6xrt/src/init.c` (+217 / -13).

- **Root cause:** the i.MX RT1176 boot ROM does not reliably place the FlexSPI DLL delay — used to sample
  the octal-NOR DQS read strobe — near the **centre** of the valid read window. The application runs XIP
  from that flash at 200 MHz octal DDR (400 MT/s), the most timing-critical mode the part offers. With the
  sampling point off-centre, individual instruction fetches returned wrong data, so the CPU executed
  instruction words that differed from what was stored in flash.
- **Symptom this removes:** intermittent UsageFault / MemManage / BusFault hardfaults with no attributable
  owner — median 5.4 minutes between faults, p90 73 minutes. Faults appeared as `UNDEFINSTR` and `NOCP` on
  legal, correctly-stored FPU instructions, as PCs landing mid-instruction or outside any executable
  section, and as `INVSTATE` on `pc = 0`. The apparent "victim" tracked whichever task was busiest
  (`uxrce_dds_client`, `wq:INS0`, `wq:uavcan`), not any real defect in those modules.
- **The fix:** a RAM-resident boot routine sweeps the DLL delay, reads a known pattern via a direct FlexSPI
  command at each setting, and selects the **midpoint of the widest passing range**. It follows NXP's DLL
  update sequence (stop mode, DSB/ISB, ERR011377 post-lock settle), falls back to the ROM setting if the
  sweep fails, and logs the chosen value from `board_app_initialize()`.
- **Boot-log confirmation on this board:** ROM-selected values before the fix were `ASLVSEL=12 / AREFSEL=11`
  (FlexSPI1 `STS2 = 0x00000b33`). Calibrated value after the fix: `<FILL: value logged at boot>`.
- **Verification:** `<FILL: N>` hours continuous clean soak under active load (camera, lidar scan, 3D scan,
  wheel odometry, uXRCE-DDS), zero reboots, zero new fault logs. Pass mark is **8 continuous hours** —
  derived from the measured fault-era distribution, in which P(quiet >= 8 h) = 0.0% and the longest quiet
  gap ever observed was 7.3 h.
- **Affects all earlier PXLABS releases on this board,** including `pxlabs-v1.17.0-r1`, `-r2-Beta`, and the
  v1.16.x line. It is a boot-ROM behaviour, not a PX4 regression: the fault also reproduces on **stock
  upstream PX4 v1.17.0**, so no PXLABS modification is implicated.
- No functional, parameter or DDS-topic changes. `esc_status` DDS publication and all r2-Beta behaviour are
  carried forward unchanged.
- OEM version string updated to `pxlabs-v1.17.0-r2.1`.

**Known issue, unrelated to the above and still open:** null-pointer dereference in the uXRCE-DDS
serializers. 15 `DACCVIOL` faults in the corpus, 7 with `MMFAR` at small offsets from NULL
(`0x00, 04, 08, 0a, 0c, 14, 20`), 4 of them in `ucdr_serialize_esc_status` at `str rX,[r4,#8]` /
`bl __memcpy_veneer`; also seen in `ucdr_serialize_vehicle_local_position`,
`ucdr_serialize_vehicle_odometry` and `ucdr_serialize_input_rc`. Tracked separately — the DLL fix is not
expected to remove these.
```

---

## B. Table updates in `PXLABS.md`

### B.1 `## Repository Information`

| Property | Change to |
|----------|-----------|
| Latest Stable | `pxlabs-v1.17.0-r2.1` |
| Latest Stable Tag | `pxlabs-v1.17.0-r2.1` (2026-08-29) |
| Hardware Verified | `Yes — 2026-08-29 (hardfault fix, <FILL: N> h soak)` |

Leave `Latest Beta`, `Development`, `Upstream Base`, `Target Board`, `Upstream Repo` and `Maintainer` as they
are.

### B.2 `## Branch & Tag Structure` — add one row above `pxlabs-v1.17.0-r2-Beta`

```markdown
| `pxlabs-v1.17.0-r2.1` | Branch + Tag | **Current stable** — FlexSPI DLL read-strobe calibration (PX4 #28141); fixes the FMU-V6XRT hardfault storm |
```

And demote the previous stable row's bold "**Current stable**" marker on `pxlabs-v1.17.0-r1`.

### B.3 `## PXLABS Modifications (v1.17.0)` → `### Board Configuration`

Add:

```markdown
- **FlexSPI DLL read-strobe calibration at boot** (cherry-picked from upstream PX4 PR #28141) — sweeps the
  DLL delay and selects the centre of the valid read window instead of trusting the boot ROM's placement.
  Required on this board: the ROM's setting was off-centre and caused intermittent XIP instruction-fetch
  faults. See `boards/px4/fmu-v6xrt/src/init.c`.
```

---

## C. Short form — for the GitHub release / tag description

```
pxlabs-v1.17.0-r2.1 — Hardfault fix (FMU-V6XRT)

Fixes the intermittent hardfault storm on the NXP FMU-V6XRT by cherry-picking upstream
PX4 PR #28141 (9f4bc800, NXP): calibrate the FlexSPI DLL read strobe at boot.

The i.MX RT1176 boot ROM does not reliably centre the DLL delay used to sample the octal
NOR DQS strobe. With the application running XIP at 200 MHz octal DDR, an off-centre
sampling point caused rare, random instruction-fetch errors — the CPU executed words that
differed from what was stored in flash. Symptoms were UsageFault/MemManage/BusFault
hardfaults with no attributable owner, median 5.4 min apart, blamed in turn on EMI, the
power harness, the charger, the SD card, parameters and four separate FC boards, none of
which were involved.

The fix sweeps the DLL delay at boot, picks the midpoint of the widest passing range, and
logs the chosen value.

Verified: <FILL: N> h continuous clean soak under load, zero reboots, zero fault logs.
Affects all earlier releases on this board, and stock upstream PX4 v1.17.0.
No functional or parameter changes.

Full debugging record: fc_hardfault_handoff_20260829.md
```

---

## D. Before you publish — the two `<FILL>` fields, and why they matter

**1. `<FILL: value logged at boot>` — the calibrated DLL value.**
PR #28141 logs the value it chooses from `board_app_initialize()`. This board's ROM values were measured
before the fix as **`ASLVSEL = 12`, `AREFSEL = 11`**. If the calibrated midpoint differs materially from
those, **that single boot line is direct evidence that this board's ROM setting was off-centre** — proof
that is independent of any soak, available in seconds. If it comes back identical to 12/11, say so plainly
in the note, because then the soak is carrying the entire argument on its own.

**2. `<FILL: N>` — soak hours.**
The pass mark is **8 continuous hours** with zero reboots and zero new fault logs, under real load, with the
soak process verified alive and its output file still growing. This number comes from the measured fault-era
distribution: P(quiet >= 1 h) = 15.8%, >= 4 h = 7.9%, >= 8 h = 0.0%, longest observed quiet gap 7.3 h.

**Anything under 8 h has already happened during the fault era and proves nothing.** Three previous
"fixes" in this campaign — the charger, the USB-only bench test, the SD card reformat — were each declared
on a quiet window shorter than this and each was withdrawn.

**3. Also confirm before publishing** (the companion cannot see this — the cherry-pick is not present in the
companion's copy of the tree):

- which tree the flashed firmware was built from, and its git hash
- that `9f4bc800` is genuinely in that build
- whether the SD card was cleared as part of the flash

At the time of writing, the FC had **7.5 h clean** (booted 2026-08-29 01:11:01, zero reboots, card baseline
clean, under active load) with the soak still running. Strong, and just short of the bar.
