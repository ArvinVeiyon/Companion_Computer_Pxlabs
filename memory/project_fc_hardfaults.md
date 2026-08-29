---
name: fc_hardfaults
description: "FC hardfault campaign — CLOSED 2026-08-23: cause was the external battery charger left connected to the DC line for every test (mode off is not disconnected). ARCHIVE ONLY — do not re-open or re-suspect anything in here."
metadata: 
  node_type: memory
  type: project
  originSessionId: 96448c77-71fd-43a5-9b04-11a764db5e77
  modified: 2026-08-25T17:47:10.971Z
---

# FC hardfaults — state as of 2026-08-22 ~23:00 IST

## ⏭⏭ RESUME HERE — 2026-08-22 EVENING: **PARAM CONTAMINATION IS ELIMINATED. THE FIRMWARE IMAGE WAS NEVER ACTUALLY ROLLED BACK, AND IT IS NOW THE ONLY SUSPECT LEFT.**

### 1. ⛔ THE 11-HOUR "QUIET" IS NOT EVIDENCE — THE RIG WAS POWERED OFF
Operator **totally shut the rig down** after ~11:05 IST and switched it back on at **~22:18 IST**
(`/proc/uptime` = the only trustworthy source). ⇒ **the param-reset soak NEVER RAN; zero observation
time was accumulated.** ⛔ Do not score anything against this window.
🔑🔑 **NEW TRAP — THE BOOT-CLOCK ARTIFACT FORGES A PLAUSIBLE-LOOKING PAST.** This boot's journal
begins stamped **`2026-08-16T14:35:42`** and early units carry stamps like **`11:05:03`** until NTP
steps the clock. `systemctl show -p ExecMainStartTimestamp microxrce-agent` therefore reported
**11:05:03 with `NRestarts=0`**, which reads exactly like "the agent was up for 11 h with no FC reboot".
**It was 4 minutes old.** ⇒ **ALWAYS cross-check `cat /proc/uptime` and `journalctl --list-boots`
BEFORE reading any duration off a timestamp on this box.** (`--list-boots` shows EVERY boot starting
`2026-08-16 14:35:3x` — that is the artifact, not five boots on one day.)

### 2. ✅✅ THE OPERATOR'S PRE-RESET BACKUP ARRIVED — AND IT CLEARS THE PARAMS
Source: **`github.com/ArvinVeiyon/PXLABS_PX4-Autopilot`, branch `pxlabs-v1.17.0-dev`,
`pxlabs/Parameters/`** (public; `curl` the `raw.githubusercontent.com` URL — **`gh` is NOT installed
on this box**). All 4 files pulled to **`~/fc_param_backups/`**.
🔑🔑 **EACH FILE'S HEADER CARRIES THE FIRMWARE GIT REVISION — an ELF-INDEPENDENT FIRMWARE-IDENTITY
RECORD, and the campaign never used it.** `# Git Revision:` reads:
· `..._tested_2026-05-24` → `ef5b782a8c` · `..._tested_2026-05-29` → `3189eedaa7`
· 🔑 **`..._tested_2026-08-15` → `a52c38b07d` = THE 3-MONTH-CLEAN 2.0.0 BUILD**
· 🔑 **`..._hard-fault_2026-08-22` → `f0889f3d10` = the 2.1.0-in-disguise faulting build**
⇒ **we hold the param set from the CLEAN era and from the FAULTING era, each self-identifying.**
🔴🔴 **DIFF (numeric-tolerant, `scratchpad/pdiff.py`) — CLEAN 08-15 vs FAULTING 08-22:
937 params in common, `UAVCAN_ENABLE=3` in BOTH, and only 28 real value differences — 25 of them
`CAL_*`.** The complete NON-calibration delta is **THREE params**:
| param | 08-15 clean | 08-22 faulting | meaning |
|---|---|---|---|
| `COM_FLIGHT_UUID` | 1614 | 1638 | boot counter — noise (and its continuity says both dumps are the SAME storage lineage) |
| `LND_FLIGHT_T_LO` | 2.03898e+09 | −5.51858e+08 | flight-time accumulator — noise |
| **`SYS_HAS_MAG`** | **1** | **0** | **the ONLY functional change across the entire fault boundary** |
⇒ ✅✅ **PARAM CONTAMINATION IS ELIMINATED AS THE HARDFAULT CAUSE. The 2.1.0 migration did NOT leave a
divergent param set** — it left the vehicle's params byte-for-byte where the clean era had them,
calibration aside. ⛔ **Do not re-open it, and do not spend soak time on it.**
⚠️ **State it honestly: `SYS_HAS_MAG 1→0` is the one functional delta and is NOT tested.** It is a weak
hardfault candidate (disabling a driver removes load, it does not corrupt pointers) but it is the only
one, and 7 `CAL_MAG_*`/`SENS_MAG_*` params disappear from the faulting set alongside it.
🔑 **SEPARATE PAYOFF — this may be the FC-HEADING BUG (todo #21):** the faulting set runs
**`SYS_HAS_MAG=0` while `EKF2_MAG_TYPE=1`**, i.e. the EKF is told to use the mag as its yaw observer
while the vehicle declares it has no mag. The clean 08-15 set has **`SYS_HAS_MAG=1`**. → `autonav_reference` §6

### 3. 🔴🔴 LIVE-MEASURED: THE FIRMWARE WAS NEVER ROLLED BACK. "FIRMWARE ELIMINATED" IS WITHDRAWN.
`AUTOPILOT_VERSION` over mavlink-router `tcp:5760` (**not FTP — cheap and safe**;
`scratchpad/fwver.py`) returns **`flight_custom_version = f0889f3d1002`**, `flight_sw_version 0x11100ff`
(1.17.0-dev). ⇒ **the FC is running the FAULT-ERA build RIGHT NOW.**
⛔ **The §"ELIMINATED" entry "firmware version (rolled back) … the binary is not the variable" is
CONTRADICTED BY MEASUREMENT and is WITHDRAWN.** Whatever was believed to be a rollback, the running
image is still `f0889f3d`. ⇒ **the 2.1.0 image is not merely the last suspect standing — it is an
UNTESTED one.**
🔑 **Reusable, 10-second firmware-identity check that needs no ELF and no FTP: `fwver.py`, compare
`flight_custom_version` against the `# Git Revision:` in any QGC param file.**

### 4. ⏭ THE DECISIVE TEST — RESTORE THE CLEAN ERA EXACTLY, BOTH HALVES
**Flash `a52c38b` AND load `..._tested_2026-08-15.params`.** That reproduces the 3-months-clean
configuration end-to-end; params are now known to be a no-op, so **the flash carries the whole test.**
✅ **`..._tested_2026-08-15.params` IS A SAFE RESTORE SOURCE — verified, unlike the 05-29 file:**
`RC_MAP_KILL_SW=12` (**ch12, the S1-validated switch — NOT the 05-29 file's known-bad 8**) ·
`RC_CRSF_PRT_CFG=202` · `RC_CHAN_CNT=16` · rover gains TUNED (`RO_MAX_THR_SPEED=0.6`, `RO_SPEED_P=0.5`,
`RO_YAW_P=2`, `RO_YAW_RATE_P=0.08`) · 🔑 **`RO_ACCEL_LIM`/`RO_DECEL_LIM` = −1** (the manual-stick
safety values) · `SYS_AUTOSTART=50000` · `UXRCE_DDS_CFG=103` · `MAV_0_CONFIG=101` · `UAVCAN_ENABLE=3`.
⚠️ **NEEDS OPERATOR SIGN-OFF — THE FC IS SHARED WITH THE DRONE** (`EKF2_*` and `RC_*` are shared).
⚠️ **Pair the flash with the queued `dds_topics.yaml` additions** (`vehicle_angular_velocity`,
`cpuload`, `system_power`) — one flash, four items.
📋 **Current FC state is NEITHER configuration:** factory defaults + `SYS_AUTOSTART=50000`, and the full
restore delta from factory is **68 non-`CAL_*` params** (list: `scratchpad/differing.tsv` — RC cal/mapping,
`PWM_AUX_*`, rover gains, `BAT*`, `SENS_EN_INA228`, `UAVCAN_ENABLE`, `EKF2_EV_CTRL=4`).
⛔ **`UAVCAN_ENABLE` is still 0 ⇒ no `esc_status`. `RC_MAP_KILL_SW=0` ⇒ KILL SWITCH UNMAPPED: DO NOT ARM.**
🔑 **TOOL TRAP FOUND TONIGHT: `ros2 topic echo/list` returned NOTHING through the ROS daemon while the FC
was publishing normally — `--no-daemon` read it instantly.** Add `--no-daemon` before declaring any topic
dead; the FC link was healthy the whole time (`timesync_status` live, session created at boot).

## (superseded) RESUME NOTE — 2026-08-22 MORNING, THE PARAM-RESET SOAK (never started; see §1 above)
**Where things stand:** operator did a **QGC factory param reset (~10:22)**, then set
**`SYS_AUTOSTART=50000` and rebooted (~10:41)**. Verified back up: **commander running (sys1 HEARTBEAT
1 Hz)** · **DDS session re-established 10:44:37** · 35 `/fmu/out` topics · **814 params**.
✅ **Fault card is CLEAN (wiped 10:30 IST).** Last fault = **#36, 10:22:31 IST**. **Zero FC reboots since
10:22:34** — so nothing has faulted since the reset.
🔴🔴 **DO NOT START SCORING THE SOAK YET — IT IS NOT LOAD-COMPARABLE.** The factory reset left
**`UAVCAN_ENABLE=0`**, so **DroneCAN/ESC is DISABLED and `esc_status` is silent**. `wq:uavcan` was the
victim in **7 of 35 faults, including 3 of the last 4** — that entire subsystem is currently absent.
⇒ **A low fault count right now would be explained by missing load, not by clean params** (this
campaign's own "victim tracks whichever task is BUSY" rule). ⏭ **Set `UAVCAN_ENABLE=3` and reboot BEFORE
starting the clock**, so the only difference from the faulting configuration is the params themselves.
⛔ **SAFETY — `RC_MAP_KILL_SW=0`, THE KILL SWITCH IS UNMAPPED.** Also no accel/gyro/mag/level cal.
**Do not arm or move the rover.** The soak is disarmed and needs none of this. 🔴 **When restoring the
kill switch, use the channel the vehicle actually flew (ch12) — the `2026-05-29.params` file says
`RC_MAP_KILL_SW=8` and that is the KNOWN-BAD ch12→ch8 move memory already warns about. DO NOT copy it.**
📋 **Restore reference (from `pxlabs/Parameters/..._2026-05-29.params`, values that match the working
setup):** `SYS_AUTOSTART=50000` ✅done · `UAVCAN_ENABLE=3` ⏭ · `UXRCE_DDS_CFG=103` ✅ · `MAV_0_CONFIG=101` ✅
· `COM_RC_IN_MODE=3` ✅ · `RC_MAP_KILL_SW` → **12, not the file's 8**.
✅✅ **THE "PRE-RESET PARAM SET IS LOST" NOTE IS WITHDRAWN — THE OPERATOR HAS A PRE-RESET BACKUP AND WILL
SHARE IT.** ⇒ **the before/after diff is BACK ON, and it is the highest-value analysis available**: it
yields the exact list of params that differed from firmware default, i.e. the contamination candidate set.
📦 **Param files in `~/fc_param_backups/` (ALL post-reset; the pre-reset one is coming from the operator):**
· `fc_params_20260822_102241.params` (786) — no airframe
· `fc_params_postreset.params` (794) — no airframe
· 🔑 **`fc_params_20260822_DEFAULTS_frame50000.params` (814) — THE DIFF BASELINE.** Factory defaults **with
`SYS_AUTOSTART=50000` restored**, `UAVCAN_ENABLE=0`, no calibration. Captured 11:04 IST.
⏭ **WHEN THE OPERATOR'S BACKUP ARRIVES:** diff it against `..._DEFAULTS_frame50000.params`, ignoring
`CAL_*` (calibration, expected to differ) and device IDs. **What is left = every param the vehicle carried
that is NOT a firmware default = the 2.1.0-migration contamination candidates.** Cross-check against the
108-param diff already in `docs/fc_hardfault_analysis.md` §17.15. ⚠️ **Baseline caveat: it was taken with
`UAVCAN_ENABLE=0`, so UAVCAN params are absent from it** — re-dump after setting `UAVCAN_ENABLE=3` if the
diff needs them.
⏭ **Scoring when it does start:** baseline **4–11 faults per powered day**, median gap **16.8 min**.
Run **≥6 h and count faults**; ⛔ silence is not success (yesterday gave a clean 6.5 h).
🔑 **Detection during the soak: DDS `create_participant` only** (`journalctl -u microxrce-agent`), prove
the agent was up across the window first, and **pull the card ONCE at the end** — MAVFTP injects the
MAVLink suspect.

# (history below)
## FC hardfaults — earlier state, 2026-08-22 midday (post fault #35, IMU+FC swap)

## 🔴🔴 2026-08-22 — **FAULT #35 HIT ON A 4th FC BOARD WITH A DIFFERENT IMU. HARDWARE IS NOW COMPREHENSIVELY ELIMINATED.**
**Operator swapped the IMU board AND went back to an older FC that carries the 2.1.0 build.** Fault
**#35 = 08-22 02:32:14 UTC (08:02:14 IST), `wq:uavcan`, `cfsr=0x00010000` UNDEFINSTR, pc=`0x30189a80`.**
🔑 **RECONSTRUCTED FROM THE VALIDATED REBOOT DETECTOR** (agent up since 07:00:38 IST, `NRestarts=0`, so
the window is readable): FC reboots at **07:11:33 · 07:32:20 · 07:33:07 · 07:44:23 · 08:02:26** IST.
**07:32:20 and 07:33:07 follow faults #33/#34; 08:02:26 follows #35. 07:11:33 and 07:44:23 have NO fault
file ⇒ those two are the operator's hardware power-cycles.** #35 is after BOTH ⇒ **the fault came after
the IMU swap and the FC swap, ~18 min after the board came up.**
⇒ **DEAD AS SUSPECTS: 4 FC boards · 2 IMU boards · both SD cards · both power modules · VESC/CAN.**
⚠️ **ASK: was the IMU board-to-board CONNECTOR/cable replaced, or only the board?** If the cable was
reused it is not strictly eliminated — but it is now a very weak suspect.
🔴 **THE PARAM SET RODE ACROSS THE SWAP — MEASURED, not assumed.** On the newly-fitted FC:
`CAL_ACC0_ID=6946842`, `CAL_GYRO0_ID=6684698`, `CAL_MAG0_ID=396809`, `EKF2_IMU_CTRL=7`, `SENS_IMU_MODE=1`
— **identical to the previous board's recorded values** — and the rover gains are the tuned ones
(`RO_ACCEL_LIM`/`RO_DECEL_LIM`=−1, `RO_SPEED_TH`=0.10, `RO_MAX_THR_SPEED`=0.60), not the zeroed 05-29 set.
⇒ **PARAM CONTAMINATION SURVIVES THIS SWAP AND IS STILL THE LAST SUSPECT STANDING**, alongside the
2.1.0 firmware image itself.

## 🔴🔴 2026-08-22 ~10:22 IST — **FACTORY PARAM RESET DONE BY THE OPERATOR. FAULT #36. AND THE TEST IS NOW CONFOUNDED — READ BEFORE INTERPRETING ANYTHING.**
**Fault #36 = 08-22 04:52:31 UTC (10:22:31 IST)**, victim `uxrce_dds_client`, `cfsr=0x00000100` **IBUSERR**
(instruction FETCH failed), **pc=`0x3e3f4000` (far outside flash), lr=`0x00001a30` (near-NULL, and that
exact lr recurs in 3 earlier `uxrce_dds_client` faults)**. 🔑 **`imxrt_irq.c` line **263**, where all 35
previous faults were line **272** — a DIFFERENT exception vector, first time in the campaign.**
🔴 **ATTRIBUTION IS AMBIGUOUS AND MUST NOT BE OVERSTATED:** it fired at 10:22:31, 3 s before the reboot,
**while BOTH my 786-param MAVLink dump AND the operator's factory reset were happening in the same
~40 s window.** Either could be the trigger; the honest statement is **"a bulk MAVLink parameter
operation coincided with the fault"**, nothing sharper.
🔴🔴 **THE PRE-RESET PARAM SET WAS NEVER CAPTURED — the reset landed BEFORE my backup ran.** My two
backups (`~/fc_param_backups/fc_params_20260822_102241.params` 786p, `fc_params_postreset.params` 794p)
are **both POST-reset**. ⇒ **the before/after diff — the thing that would have named the guilty param —
is permanently lost.** ⚠️ Only partial pre-reset values survive: read live at ~10:05 → `SYS_AUTOSTART`
**50000**, `RO_ACCEL_LIM`/`RO_DECEL_LIM` −1, `RO_SPEED_TH` 0.10, `RO_MAX_THR_SPEED` 0.60,
`EKF2_IMU_CTRL` 7, `SENS_IMU_MODE` 1, `CAL_ACC0_ID` 6946842 / `CAL_GYRO0_ID` 6684698 / `CAL_MAG0_ID` 396809.
Other sources: `docs/px4_param_audit.md` (47 rows) · `~/ubuntu-server/Rover/*.params` · repo
`pxlabs/Parameters/*2026-05-{24,29}.params` (⛔ the 05-29 one is the UNSAFE pre-tuning file).
🔴🔴 **`SYS_AUTOSTART` IS NOW 0 ⇒ NO AIRFRAME ⇒ MOST OF THE VEHICLE STACK IS NOT RUNNING.** Confirmed:
no `commander` (⇒ **no MAVLink HEARTBEAT**, no `/fmu/out/vehicle_status`, no `battery_status`), no rover
modules, no ESC/`esc_status`. **MAVLink transport itself is FINE** — `sys1:comp1` still streams ATTITUDE/
HIGHRES_IMU/ODOMETRY at full rate. ⚠️ **TOOL TRAP: `set_param.py`/`dump_params.py` call `wait_heartbeat()`
and therefore FAIL with `autopilot 0:0` — this is NOT a dead link. Set `m.target_system,
m.target_component = 1,1` and skip the heartbeat wait.**
⛔⛔ **THEREFORE THE PARAM TEST AS IT NOW STANDS IS INVALID** — by this campaign's own "victim tracks
whichever task is BUSY" principle, a drop in fault rate is explained by collapsed LOAD, not clean params.
⛔ **RETRACTED — "PARAM-DUMP DURATION IS A LOAD PROXY" WAS WRONG.** I proposed gating validity on the dump
taking ~40 s again (786 params pre-reset) vs 4 s post-reset. **The ~40 s figure was never load — that dump
was INTERRUPTED BY FAULT #36 AND THE REBOOT.** A clean dump is ~3-4 s in every configuration (794 idle,
**814 with the rover airframe restored**). ⇒ **Use module presence as the load gate instead: is
`esc_status` publishing, is `vehicle_status` publishing, is `UAVCAN_ENABLE` non-zero.** ⏭ **TO MAKE IT A REAL TEST: restore
`SYS_AUTOSTART=50000` (rover airframe) and leave everything else at defaults** — same load profile, only
the tuned params removed. Then soak. ⚠️ Needs QGC/USB or the target-override tool (no heartbeat).

## 🔑🔑 2026-08-22 — **THE VICTIM TASK IS A LOAD MAP, NOT A DEFECT MAP. PROVEN BY THE CAN A/B.**
Operator ledger (08-22): the FC was replaced **and** tested with **all ESC/CAN removed**, with
**microXRCE physically disconnected**, and with **the RC CRSF UART removed** — faults continued through
all of it. **⇒ MAVLink is the ONLY companion link never removed.**
🔑 **The fault archive corroborates the rotation exactly:**
`wq:uavcan` victims — 08-16 ×3, 08-18 ×1, **none at all on 08-20 (bus physically absent)**, then
**3 of the 4 faults on 08-22 once CAN was back**. `uxrce_dds_client` 13 victims, none on 08-22.
`wq:ttyS3` (CRSF) 08-20 ×2 and again **08-22 02:02:08 — so RC was connected again today**.
⇒ **Removing a peripheral does not stop the faults, it just moves the victim to the next busiest task.**
🔴 **THEREFORE PREDICT: disconnecting MAVLink will RELOCATE the fault, not stop it.** Run the test
anyway — it is cheap and it is the last untested link — but treat "the victim changed" as **expected and
meaningless**, and judge ONLY on fault COUNT over a fixed window. A shift in victim is not progress.
⚠️ **THIS ALSO MEANS THE FAULT IS GLOBAL (heap / memory corruption), NOT IN ANY ONE DRIVER** — which is
what the un-removable suspects (2.1.0 image, 2.1.0 param set) both are.

## ⚠️⚠️ I AM INJECTING THE SUSPECT VARIABLE: `ftp_pull_faults.py` RUNS OVER MAVLINK FTP
Upstream PX4 **#22160 is "fmu-v6xrt hardfault during MAVLink-FTP log download"** (doc §17, still OPEN),
and MAVLink is now the last un-removed link. **Every fault-log pull I do is that exact operation.**
⛔ **While MAVLink is the live suspect, do NOT pull the card on a whim** — batch pulls, and record the
pull time so it can be excluded when correlating. 🔑 **The DDS `create_participant` reboot detector needs
no MAVFTP at all — prefer it, and pull the card once at the END of a window.**

## 🔴🔴 THE ELF TRAP — **DO NOT RESOLVE FAULT ADDRESSES AGAINST THE COMMITTED FIRMWARE. I DID, AND IT WAS THE WRONG BINARY.**
`~/PX4-Autopilot` commit **`f0889f3d10`** contains `pxlabs/PXLabs_Firmware/px4_fmu-v6xrt_default.elf`,
and its **build datetime matches the fault log to the second (May 31 2026 18:19:40)**. That match is a
**FALSE POSITIVE** — the running firmware is **2.1.0 built from an UNCOMMITTED dirty tree that merely
REPORTS the `f0889f3d` hash** (analysis doc §17.7). The real 2.1.0 ELF **does not exist anywhere**.
⛔ **Symbols resolved against the committed ELF are plausible but WRONG** — I produced a whole
"`ucdr_serialize_esc_status` is the top faulting function" lead this way. **It is RETRACTED.** It also
fails independently: 2.0.0 (`a52c38b`) already contained `esc_status` and ran ~2 months clean.
🔑🔑 **THE TEST THAT PROVES FIRMWARE IDENTITY — CHEAP, RUN IT BEFORE TRUSTING ANY ELF:**
compare the LIVE topic list against the committed build's yaml.
```
git show <commit>:src/modules/uxrce_dds_client/dds_topics.yaml | grep -oE "/fmu/out/[a-z_0-9]+" | sort -u > /tmp/y
ros2 topic list | grep "^/fmu/out/" | sort -u > /tmp/l && comm -23 /tmp/l /tmp/y
```
**08-22 result: live publishes `rover_attitude_status`, `rover_rate_status`, `rover_speed_status` (+ six
`_v1` variants) that `f0889f3d10` does NOT — 35 live vs 32 committed.** ⇒ running FW ≠ committed FW.
✅ **The resolution METHOD is sound and worth reusing IF a matching ELF ever exists:** `readelf -sW elf |
awk '$4=="FUNC"{print $2,$3,$8}'` → bisect on `addr & ~1` (Thumb) → `c++filt`. No ARM toolchain needed;
`readelf`/`nm` read foreign ELFs fine. ⚠️ **A task↔subsystem "coherence" check does NOT validate the
ELF** — all four committed builds scored an identical 31/35, so it cannot discriminate. Use the topic test.

## ✅ WHAT SURVIVES THE ELF PROBLEM (all read from the log TEXT, ELF-independent) — 35 faults
**Victim task:** `uxrce_dds_client` 13 · `wq:uavcan` 7 · `wq:INS0` 6 · `wq:ttyS3` 3 · `mavlink_if1` 2 ·
`hpwork` 2 · `wq:nav_and_controllers` 1 · `gps` 1. **8 distinct tasks ⇒ task-agnostic, as established.**
**Fault class:** PRECISERR+BFARVALID (data-side NULL deref) 12 · UNDEFINSTR 9 · NOCP 7 · INVSTATE 3 ·
IBUSERR 2 · IMPRECISERR 1 · UNALIGNED 1. **Mixed throughout the whole archive — a run of one class is noise.**
🔑 **7/35 faults have a `pc` OUTSIDE flash entirely** (`0x0` ×2, `0x10`, `0x1b22`, `0x1cc4`, `0x2fd930d2`,
`0x250330fc`) ⇒ **the CPU was executing at a wild/NULL address: control-flow corruption, not a bad
computation.** This is the NULL-deref root cause seen from the instruction side, and it is ELF-independent.
✅ **STACK EXHAUSTION RE-RETRACTED WITH NUMBERS:** `used==size` in 32/35 is a NuttX stack-COLORING
artifact, **not** a depth measurement. The real figure is `sp − stack_bottom`: **minimum headroom across
all 35 faults = 1096 bytes**, i.e. every fault had ≥1 KB of stack left. ⛔ Do not revisit stack size.


## ✅✅ 2026-08-22 07:37 IST — **THE SOAK QUESTION IS ANSWERED BY MAVFTP: ZERO FAULT FILES IN THE ISOLATION WINDOW.** But it is NOT the clean exoneration §"⏭" below hoped for.
Pulled the card **without `--delete` first** (per the plan below), then deleted on the operator's order.
**Card + local archive together cover every fault the FC ever wrote, so absence is real evidence here.**
🔑 **THE FAULT-FREE STRETCH IS `08-21 18:18:35 UTC → 08-22 00:49:08 UTC` = 6 h 30 m** — it CONTAINS the
whole isolation window (18:21→23:57 UTC) with **no file in it. No hardfault occurred under total isolation.**
🔴 **WHY THAT IS WEAKER THAN "FC-INTERNAL DISPROVEN": THE QUIET RAN ~52 MIN PAST THE SOAK'S END**
(stack + CAN back up 23:57 UTC, first fault not until 00:49:08). **The quiet therefore does not end when
isolation ends, so it cannot be attributed to isolation.** 52 min of full-stack quiet is unremarkable —
08-21 already produced an **89-min** full-stack fault-free stretch. ⇒ Treat this as a **NULL RESULT that
fails to incriminate the FC-internal path**, not as evidence for an external cause. The logical form
matters: §"a fault in this state = FC-internal, full stop" has **no valid contrapositive** — no fault
proves nothing about causation, it only declines to add evidence.
⚠️ **AND THE ARCHIVE HAS LONGER GAPS** (08-20 19:36 → 08-21 13:59 = 18 h) whose power state I never
recorded. **6.5 h is not demonstrably anomalous.** ⛔ Do not quote the soak as an elimination of anything.

## 🔴 FAULTS #32-#34 — first faults after the re-enable; card pulled + VERIFIED + DELETED, now clean
| # | UTC | IST | victim task | cfsr | decode | pc |
|---|---|---|---|---|---|---|
| #32 | 08-22 00:49:08 | 06:19 | `wq:uavcan` | `0x00010000` | UFSR UNDEFINSTR | `0x301f8cae` |
| #33 | 08-22 02:02:08 | 07:32 | `wq:ttyS3` | `0x00010000` | UFSR UNDEFINSTR | `0x300bb9e2` |
| #34 | 08-22 02:02:56 | 07:32 | `wq:uavcan` | `0x01000000` | **UFSR UNALIGNED — NEW, first in 34 faults** | `0x3015400c` |
**#33→#34 are 48 s apart** = the familiar burst-then-quiet shape. Victim shifts again across the burst
(`ttyS3`→`uavcan`) — more confirmation the victim tracks **whichever task is busy**, not a defective task.
🔴🔴 **`wq:uavcan` IS A VICTIM AGAIN NOW THAT THE BUS IS BACK — THIS IS NOT A REASON TO RE-SUSPECT CAN.**
The CAN family was killed by REMOVAL on 08-20 (3 faults with no bus physically present); a task-agnostic
victim distribution re-including `uavcan` the moment `uavcan` is busy again is exactly what §17.14 predicts.
⛔ Do not re-open it. ⚠️ But do state, when comparing counts, that **08-21-onward runs carry CAN load again**.
🔑 **I CHECKED WHETHER THE FAULT CLASS HAD SHIFTED (it looked like it had — 4 straight UsageFaults, no
`0x82`) AND IT HAS NOT.** A sweep of all 34 archived logs shows the class was **always** mixed:
`0x82` (BFSR PRECISERR+BFARVALID, the data-side NULL-deref signature) ×12 · `0x00080000` NOCP ×6 ·
`0x00010000` UNDEFINSTR ×8 · `0x00020000` INVSTATE ×3 · `0x100` IBUSERR ×2 · `0x400` IMPRECISERR ×1 ·
`0x01000000` UNALIGNED ×1. **So the recent UsageFault run is sampling noise, not a change of regime, and
the §17.18 NULL-deref root cause (which rests on the twelve `0x82` faults and their valid BFAR values)
stands unchallenged.** ⚠️ Sweep command worth reusing:
`for f in ~/fc_faults/fault_*.log; do grep -m1 'running task:' $f; grep -m1 'cfsr:' $f; done`

## 🔴🔴 FAULT #31 — 2026-08-21 18:18:35 UTC (23:48:35 IST) — **DURING THE STACK-OFF SOAK. THE AUTONAV-NODE HYPOTHESIS IS DEAD IN ITS STRONG FORM.**
**All rover ROS nodes had been STOPPED for 15 min** (pgrep-verified down since 18:03 UTC) when the FC
hardfaulted anyway — **33 s after a card check read clean.** Victim: **`gps`** (an 8th distinct task,
nothing to do with DDS or the companion), `cfsr=0x00010000` = **UFSR UNDEFINSTR**, `pc=0x301f9008`
(FlexSPI XIP), from `imxrt_irq.c:272`, IRQ stack barely used (0x7c). Classic instruction-side
corruption; victim-shift again — `gps` is simply what was busy with everything else idle.
⚠️ Caveats: `microxrce-agent` + `vision_streaming` were still up at the fault (operator stopped both
at **23:51 IST**), and this FC boot (post-#30, 18:00:41) did serve ~2 autonav registration attempts in
its first 3 min before the stack stop. So the test eliminated the NODES, not DDS itself.
⏭ **NEW SOAK CONDITION since 23:51 IST / 18:21 UTC: NOTHING companion-side touches the FC** — no DDS
session, no MAVFTP (poll sessions closed), only mavlink-router idling and RC. Card verified clean
18:29:29 UTC. **A fault in THIS state = FC-internal, full stop (params / IMU board / firmware bug).**
## ✅ 08-22 05:15-05:27 IST — SOAK ENDED ON OPERATOR'S ORDER ("enable autonav services"). ALL 6 RE-ENABLED. **RESULT: STILL UNKNOWN — AND THE OBVIOUS WAY TO CHECK IT IS A TRAP.**
🔴🔴 **THE REBOOT-DETECTOR WAS BLIND FOR THE ENTIRE SOAK, SO ITS SILENCE IS NOT EVIDENCE.** The detector
(§ "every hardfault reboots the FC and the companion logs a `create_participant` 4 s later") reads the
**`microxrce-agent` journal — and that agent was STOPPED at 08-21 23:51:21 with everything else**
(journal: `Stopped microxrce-agent.service`; `NRestarts=0`; next start 08-22 05:15:51 = the re-enable).
**With no agent there is no client session, so no `create_participant` line CAN be emitted no matter how
many times the FC rebooted.** I briefly recorded "ZERO FC reboots ⇒ FC-internal cause disproven" off that
silence — **RETRACTED, it was never measured.**
🔑 **GENERAL RULE THIS IS AN INSTANCE OF: the detector needs its own liveness proof, exactly like a quiet
topic.** Before reading the create_participant journal for ANY window, first prove `microxrce-agent` was
UP across that whole window (`systemctl show -p ExecMainStartTimestamp`, plus a `Stopped` grep).
✅ **DONE 08-22 07:37 — ANSWER AT THE TOP OF THIS FILE (zero files in the window; null result, not an
exoneration). The plan below is kept only because the METHOD is reusable.**
⏭ ~~**THE SOAK'S ANSWER IS STILL RECOVERABLE — the FC wrote its own fault files regardless:**~~
`tools/ftp_pull_faults.py` **WITHOUT `--delete`** (MAVFTP, independent of DDS/the agent). **Any fault file
dated in 18:21→23:45 UTC (23:51→05:15 IST) = a hardfault under TOTAL ISOLATION ⇒ FC-INTERNAL, full stop;
none = the cleanest exoneration this campaign can get.** ⚠️ filenames are UTC; a truncated stub on round 1
is normal. **This is the single highest-value measurement outstanding.**
⚠️ **THE CLEAN TEST CONDITION IS NOW OVER** — from 05:15 IST the full stack + CAN load are back, so fault
counts after this point are NOT comparable to the isolation window.
⚠️ **MY OWN AGENT STARTS ARE FALSE POSITIVES IN THE DETECTOR: 05:15:51, and a deliberate restart at
05:26:56 (session re-established 05:27:02).** Discard both windows when counting.
✅ Post-restart health, measured: FC session re-established · `esc_status` `esc_count` 4 / `esc_online_flags` 15
· `/scan` ~28 Hz · autonav **re-registered unaided at 05:27:18** (`Got RegisterExtComponentReply`) — the stack
self-heals across an agent restart. `rover-ekf-bridge` left DISABLED on purpose. Rover **DISARMED**,
`nav_state` **0 = Manual** (the feared stale 23 is NOT present). Reflex live and honest: `BLOCK forward`,
`scan_fresh=yes valid=83% bumper=0.27m` — a real obstacle inside the 0.345 m standoff, not the BLIND cue.
⚠️ `NRestarts=3` on `rover-autonav-mode` at first bring-up was ORDERING (unit up before the agent was
listening → `Registration failed` → 5 s retry), **not** a crash-loop and **not** FC reboots.
⚠️ **`ros2 topic hz` PRINTED NOTHING on a topic that was genuinely publishing** (daemon warm-up right after
the DDS restart); `echo --once` proved it live. **Don't call a topic dead off `hz` after a DDS restart.**

🔧 **08-22 ~00:0x IST FOR THE OPERATOR'S REBOOT-REPLICATION RUNS, systemctl DISABLED (survives reboots):
`microxrce-agent` + the 5 rover units** (`rover-autonav-mode`/`rover-scan`/`rover-scan-3d`/`rover-odometry`/
`rover-camera`; `rover-ekf-bridge` + `vision_streaming` were already disabled). ⏭ **RE-ENABLE ALL 6 WHEN THE
TEST ENDS** (`systemctl enable --now microxrce-agent rover-autonav-mode rover-scan rover-scan-3d rover-odometry
rover-camera`; ekf-bridge stays disabled on purpose). ⚠️ **While the agent is down: CH10 RC reboot/shutdown of the
companion is DEAD** (rc_control reads `/fmu/out/input_rc` via DDS) **and residual FC contact = mavlink-router
heartbeats + any GCS/QGC traffic + card-check MAVFTP; the FC-side `uxrce_dds_client` still RUNS (reconnect polling)
— agent-off removes the session, not the module.**
🔑 Fault #31 was pulled+deleted (2 rounds: 38 718 B stub → 44 792 B VERIFIED). Archive: `~/fc_faults/` (32 logs).

## 🔎 AUTONAV-NODE INVESTIGATION (operator asked "did the autonav node cause this, and why since 08-16?") — findings so far
- **The unit's journal history begins 08-15 21:12 IST — retention starts AT the era boundary; there is NO pre-era
  journal to compare against.** The 08-15 23:04 stop = the 2.1.0 flash window; first crash-loop storm 08-16 00:19.
- **The storms are a SYMPTOM, not the cause: the node exits with `px4_ros2::Exception: "Timeout, no request received
  from FMU (this can happen on FMU reboots)"` / `"Registration failed"`** — it crash-loops (RestartSec=5 + ~15 s
  registration timeout ⇒ one attempt per ~22 s) **whenever the FC is down/rebooting**. Fault → FC reboot → storm.
- Unit: `Restart=always`, `RestartSec=5`, `StartLimitBurst=10/300s` — a long FC outage CAN exhaust the start limit
  and leave the unit failed (fits the 08-16 14:39→16:38 silent gap with 5 faults inside it).
- Each restart attempt does hammer the FC's `uxrce_dds_client` with a fresh ext-component registration — kept as a
  possible **provocation/aggravator** (like heavy FTP), but **#31 proves the node is not NECESSARY for a fault.**

## 🔬 EARLIER SOAK PHASE (started 2026-08-21 23:33 IST / 18:03 UTC, operator's test) — ended by fault #31
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

## 19. 2026-08-23 — CARD ZEROED. 5 PREVIOUSLY-UNSEEN FAULTS PULLED FIRST (post-closure housekeeping)
- **Card had 5 fault logs NONE of which were in `~/fc_faults` yet.** All 5 backed up + `END Fault Log`-verified,
  then deleted. **Card independently re-listed = 0.** Local backups now **42 files, 39 verified**
  (the 3 unverified are the pre-existing 08-16-era incompletes, NOT these).
  Pulled: `fault_2026_08_22_19_13_35` · `fault_1970_01_01_00_04_01` · `_00_06_47` · `_00_10_17` · `_00_11_10`.
- ⛔ **CORRECTION (same day, see §20): I originally wrote here "THEY DO NOT RE-OPEN THE CHARGER VERDICT — THEY
  SUPPORT IT." THAT FRAMING IS WITHDRAWN — the operator has since retracted the charger verdict entirely.**
  The *signature* reading below still stands (electrical/bus-level); what was wrong was treating it as
  confirmation of the charger specifically. 🔑 **A signature that says "electrical" does NOT identify WHICH
  electrical source — I let the closure narrative supply that.** Crash task is **DIFFERENT EVERY TIME**
  (`uxrce_dds_client`, `wq:uavcan`, `commander`, `wq:INS0`, `uxrce_dds_client`) with **jumps to garbage PCs**
  (`pc:0x00003000`, `pc:0x200337c0`) and `cfsr:0x00020000` **INVSTATE** / memfault. Random-task + random-PC
  corruption is the signature of an **electrical/bus** cause, not a software bug in any one module.
- ⚠️ **DATING IS UNRESOLVED AND I COULD NOT RESOLVE IT.** Only one carries a real date (**08-22 19:13:35**, i.e.
  AFTER the 08-22 10:22 factory reset). The four `1970_01_01` names are **boot-relative** (4:01/6:47/10:17/11:10
  into some boot, before time sync). **FTP listing ORDER put two of the 1970 files AFTER the 08-22 19:13 file**
  ⇒ suggestive, **not proof**. ⛔ **Do NOT claim these pre-date the charger removal — nobody has established
  when the charger came off.**
- ✅ **THE CARD BEING EMPTY IS NOW THE CLEAN BASELINE the closure note asks for**: charger connector PHYSICALLY
  off → fixed-window soak → **judge on COUNT**. **Any `fault_*.log` appearing from here is post-baseline.**
  🔑 **FC wall clock was CORRECT at 19:07 (19 s off the companion), so a NEW fault gets a real 2026 name —
  a fresh `1970_*` name means it faulted early in a boot before time sync, not that it is old.**
- ⛔ **`tools/fc_fault_backup.py` IS BROKEN — DO NOT USE IT.** Two independent defects: it lists via
  `ftp.dir_contents` (**does not exist** ⇒ always "no fault logs found"), and it verifies against
  `End Fault Log` when the real trailer is **`END Fault Log`** (matched **0 of 37** backups) ⇒ it would refuse
  to delete anything. ✅ **`tools/ftp_pull_faults.py` is the correct tool** (`list_result`, ResetSessions,
  fresh connection per file, `callback=`).
- ⚠️ **MAVFTP TRUNCATES SILENTLY — 3 of 5 first-pass pulls came back SHORT** (17208/25812/12667 of ~44.8 KB)
  while the card reported full size. **The `END Fault Log` check is what caught it; it took 3 passes.**
  ⇒ **NEVER delete on a single pass, and never trust a byte count — trust the trailer.**
- ⚠️ **FW hash in all 5 logs = `a52c38b0…` (build May 31 2026)**, which MEMORY.md ties to the
  `tested_2026-08-15` param file — **not the `f0889f3d` it calls "live".** Unreconciled; don't quote either
  as the running firmware without re-checking.
- ⏭ **NOT DONE: the uncommitted-hardfault ARMING LATCH was not cleared** (`hardfault_log rearm/reset`) — it
  needs a MAVLink shell and that is one-per-FC-boot. Irrelevant while the FC is on factory params
  (**kill switch unmapped ⇒ DO NOT ARM**); do it in the same shell session as the param restore.

## 20. 2026-08-23 EVENING — CHARGER VERDICT WITHDRAWN BY THE OPERATOR. COMPANION SWAPPED. CAMPAIGN RE-OPENED
- 🔴🔴 **THE OPERATOR RETRACTED IT IN HIS OWN WORDS: "earlier i claimed the battery charger removal rectified
  but does not."** ⇒ **faults CONTINUED after the charger came off.** The §18 closure and the old MEMORY.md
  "CLOSED — charger" line are **DEAD**. ⛔ **Never cite the charger as the cause again.**
- 🔑 **THIS IS WHY THE 4 `1970_01_01` LOGS MATTERED.** §19 flagged that their dating was unresolved and refused
  to claim they pre-dated charger removal. **That caution was right** — they are now the leading candidates for
  the **post-charger-removal** faults (FC booting with no time source ⇒ epoch-stamped names, faults landing
  4:01 / 6:47 / 10:17 / 11:10 into a boot). ⚠️ Still not *proven* to be post-removal; nobody logged the removal time.
- 🔑🔑 **PROCESS LESSON — THE REAL ONE: a single-variable "the one thing never removed" story is SEDUCTIVE AND
  UNTESTED.** The charger explanation fit every prior elimination perfectly and was still wrong. **An
  explanation that accounts for all past data is not thereby confirmed — it has to survive REMOVAL of the
  variable, counted over a fixed window.** ⛔ **Do not accept the next single-variable story on fit alone.**
- ⏭ **LIVE TEST NOW: THE COMPANION HAS BEEN PHYSICALLY SWAPPED** (operator, 08-23 evening). This is the current
  hypothesis under test — note it CONTRADICTS the §18-era "companion eliminated / 10-of-10 was a base-rate trap"
  finding, so **that elimination is also no longer safe to lean on.**
- 📌 **FINGERPRINT THE BOX SO A SWAP IS DETECTABLE (this was missing and cost us):** current companion =
  **RPi5 Model B Rev 1.0, `/proc/cpuinfo` Serial `79a58c03a2b9df3a`, Revision `d04170`, machine-id
  `48e346f48a4944e39911110f0fb9fc98`, hostname `Vind-Roz`.** 🔑 **Hostname is NOT an identity — an SD-card clone
  keeps it. CHECK THE SERIAL when a hardware swap is claimed.**
- ✅ **SOAK STATE AT 19:40 08-23: FC booted `18:46:31`, UP 53 MIN CONTINUOUSLY, card 0 fault logs.**
  🔑 **A hardfault REBOOTS the FC ⇒ unbroken uptime is positive proof of no fault this boot** (better evidence
  than an empty card, which only covers since the 19:26 delete). ⇒ **all 5 logs deleted in §19 necessarily
  PRE-DATE 18:46:31 — none are from the post-swap boot.**
- ⛔ **53 MIN CLEAN IS NOT A PASS. MEASURED: 9 of 36 fault-era gaps were ≥53 min (25%); within-session median
  gap 7.1 min, overall median 17.2 min, min 0.8 min.** ⇒ **a clean hour is a 1-in-4 coincidence even at full
  fault rate. Judge on COUNT over a window of hours.**
- 🔧 **HOW TO CHECK "any fault since boot" WITHOUT A MAVLINK SHELL** (shell is one-per-FC-boot):
  FC uptime = `/fmu/out/timesync_status`: **`uptime_us = timestamp + estimated_offset`** (offset is large and
  negative; ~3.19e9 µs = 53 min here). ⚠️ **`SYSTEM_TIME` is NOT streamed and `MAV_CMD_REQUEST_MESSAGE` (512)
  did not produce it** — don't waste a pass on that. ⚠️ **DDS discovery is FLAKY: `ros2 topic echo --no-daemon`
  failed 2 of 3 tries on a live topic — RETRY BEFORE CONCLUDING** (matches the known trap).
- ⚠️ **`sensor_combined.timestamp` is NOT boot-relative here** — the uXRCE client translates it to host epoch
  (it read as a correct 2026 wall clock). **Don't use it for uptime.**

## 21. 2026-08-23 20:00-20:55 — FIRST MEASURED FAULT RATE. WORST EVER. COMPANION SWAP DID NOT FIX IT
- 🔴🔴 **22.4 FAULTS/HOUR. 8 faults in 18.7 min; gaps 2.7/3.3/1.1/6.3/0.8/0.8/3.7 min, median 2.7.**
  **2.6× WORSE than the 08-16..08-22 era (within-session median 7.1 min).** Soak over 54.6 min: **8 reboots,
  8 new fault logs.** ⇒ **the companion swap did NOT fix it, and neither did the charger removal.**
- ✅✅ **REBOOTS == FAULT LOGS, 1:1 (8/8). THIS IS THE RESULT THAT MATTERS** — it rules out power-cycles, brownouts
  and link glitches. Every reboot produced a real hardfault record. 🔑 **Two independent detectors agreeing is
  what makes the count trustworthy; ONE detector would have been arguable.**
- ✅ **COMPANION CLEARED ON POWER AND LOAD (measured across every fault): `vcgencmd get_throttled`=**`0x0`**
  (no undervoltage now or since boot), load flat ~2.0-2.7, 57 °C, `claude` ~7%.** ⇒ **the obvious mechanism for
  "companion kills FC" — rail sag / CPU storm — IS NOT PRESENT.** ⚠️ Does NOT clear the uXRCE *link* itself.
- 🔑🔑 **`rover-autonav-mode` NRestarts IS A FREE FC-FAULT COUNTER.** It dies with
  `px4_ros2::Exception: Timeout, no request received from FMU` every time the FC drops, then re-registers
  (`Registering 'AutoNav'` → `Got RegisterExtComponentReply`). **83 such events in the journal.**
  ⛔ **DIRECTION OF CAUSATION: it is a SYMPTOM, not a cause — I nearly wrote it up as a suspect.** The FMU-timeout
  wall-clock times line up gap-for-gap with the fault-log stamps (e.g. 3m19s and 1m08s gaps match exactly).
- ⚠️ **EMI/EMC WAS ASKED AND IS *NOT* SUPPORTED AS THE DRIVER — the evidence points the other way:**
  **the motors are IDLE** (rover stationary, disarmed) so the dominant rover EMI source is OFF, **yet the rate is
  the HIGHEST ever measured**. EMI should be worst under load. Rail is clean (`0x0`). 🔑 **EMI is the next
  seductive all-explaining story after the charger — treat it as UNTESTED until a window kills it.**
- ⏭ **THE CHEAP FALSIFIABLE TESTS (operator is running these MANUALLY):** at a 2.7 min median a **20-min window
  expects ~7 faults, so ZERO IS A REAL RESULT.** (1) **CAN**: `UAVCAN_ENABLE=0` (2) **RF/EMI**: stop
  `wifibroadcast@drone` (3) **uXRCE link**: stop `microxrce-agent` — ⚠️ that kills the DDS uptime feed, but the
  **MAVFTP card poll still counts faults over an independent path.**
  🔑 **THE HIGH RATE IS AN OPPORTUNITY — one window now settles what used to need hours.**
- 🔬 **LEAD (untested, do not promote to cause): DroneCAN.** `UAVCAN_ENABLE=3` is ON, **`esc_online_flags=9 ⇒ only
  2 of 4 ESCs online** (was **15**, all four, on 08-21)**, and one of the 5 earlier faults died in `wq:uavcan`.
  A half-populated bus with the driver stack live is concrete and testable, unlike diffuse EMI.
- 🔧 **TOOLING BUILT — REUSE IT:** `tools/fc_soak.py` (DDS uptime + MAVFTP card poll + 12-min ring buffer of
  companion state, dumped on every event; logs `claude` cpu because I am a known confound) ·
  `tools/fc_soak_report.py` (rate vs the historical baseline) · `tools/fc_soak_mark.sh` (window markers so a
  manual A/B has clean boundaries). Output in `~/fc_soak/` (`status.txt`, `companion.csv`, `soak_*.log`).
  ⚠️ **STOP THE SOAK BEFORE ANY BULK MAVFTP PULL** — both do `OP_ResetSessions` and will truncate each other.
- ⚠️ **Fault-log names use TWO timebases — never mix them into one gap series:** `fault_2026_*` = FC clock set;
  `fault_1970_*` = clock unset, counting from when it started. This burst is entirely `1970_*`.

## 22. 2026-08-23 ~22:00 — SESSION END STATE. SOAK LEFT RUNNING DETACHED. READ THIS FIRST NEXT TIME.
- ✅ **A SOAK IS RUNNING UNATTENDED RIGHT NOW** (started 22:00:51, detached with `setsid nohup`, so it
  survives the session). **CHECK IT BEFORE STARTING ANYTHING:** `cat ~/fc_soak/status.txt` ·
  `python3 ~/ros2_ws/tools/fc_soak_report.py` · stop with `pgrep -f "[f]c_soak.py"` then `kill <pid>`.
  ⛔ **`pkill -f fc_soak` WOULD MATCH MY OWN SHELL — use pgrep+kill.** Card baseline at start: **0 (clean)**.
- 🔑🔑 **THE MOST IMPORTANT NEW RESULT: 2 FC REBOOTS PRODUCED *ZERO* FAULT LOGS (11.6 min window, 21:41-21:53).**
  Earlier the same night it was **8 reboots → 8 fault logs, 1:1**. ⇒ **a reboot with NO fault log is a CLEAN
  reboot (operator param work / power cycle), NOT a hardfault.** 🔑 **THIS IS THE WHOLE VALUE OF TWO
  DETECTORS — a single detector would have scored those 2 as faults and invented a false signal.**
  ⚠️ **11.6 min is NOT a verdict** — at the measured 22.4/hr it expected ~4 faults, but 25% of fault-era gaps
  exceeded 53 min. **Needs 30-60 min clean before calling it a change.**
- ⚠️ **`/fmu/out/timesync_status` WENT COMPLETELY SILENT for minutes, then RECOVERED ON ITS OWN** while the FC
  was alive and heartbeating. It blinded the soak's uptime detector (`uptime samples: 0`) and the watchdog
  correctly fired a DDS-SILENT dump. ⛔ **DO NOT read a silent timesync_status as "FC dead" — cross-check the
  MAVLink heartbeat and the card.** ⏭ **UNFINISHED: I started adding a THIRD detector (a `journalctl -u
  rover-autonav-mode -f` watcher counting `no request received from FMU`) so counting survives a DDS outage —
  the edit was interrupted and `fc_soak.py` is UNCHANGED. Worth finishing.**
- 🔑 **`rover-autonav-mode` HITS SYSTEMD'S START LIMIT and lands in `failed` (seen at NRestarts 32, then again
  at 10).** It then stops generating the FMU-timeout proxy entirely, so **the proxy silently goes dead.**
  ⏭ **Recovery: `sudo systemctl reset-failed rover-autonav-mode && sudo systemctl start rover-autonav-mode`
  — a bare `start` does NOT work from `failed`.** FMU-timeout total reached **96** this session.
- 🔴🔴 **PHYSICAL STATE THE OPERATOR CHANGED — CALIBRATIONS ARE INVALID: THE ROVER IS ON A STAND, THE CAMERA HAS
  BEEN MOVED OFF ITS ORIGINAL POSITION, AND THE TOP COVER IS OFF.** `rover-odometry` locked its camera-gyro TF
  at **18:38:21, BEFORE the move** ⇒ heading source and every `/scan`-derived number (**standoff 0.345 m,
  `front_overhang` 0.337, scan scale 0.9845**) now reference a camera that is not there.
  ⛔ **HARMLESS for a stationary FC soak; NOT harmless if anything drives. Restart `rover-odometry` to re-lock
  the TF before any moving test, and re-do the wall probe.** (This compounds the 08-16 camera rotation.)
- ⛔ **`rover-ekf-bridge` DELIBERATELY LEFT STOPPED** — operator confirmed **ON A STAND**, and wheels-up +
  armed AutoNav + bridge = the self-sustaining limit cycle. **It is NOT needed for hardfault testing** (the FC
  faults independently of it and both detectors work without it). Don't "helpfully" start it.
- ✅ **Stack up at session end:** `microxrce-agent`, `rover-camera`, `rover-scan`, `rover-scan-3d`,
  `rover-odometry`, `rover-autonav-mode` all active; autonav registering cleanly
  (`collision-diag: clear, valid=79%, bumper=0.70m`). `vision_streaming` inactive.
- 🔑 **FC params were being reset by the operator around 21:45-21:55 — that is the most likely source of the 2
  clean reboots. CONFIRM THE PARAM STATE BY READING IT (`set_param.py NAME`) before interpreting any new data.**

## 23. 2026-08-23 ~23:50 — 🔴🔴 **THE FIRMWARE IS ELIMINATED. `a52c38b` HARDFAULTS. EVERY LISTED SUSPECT IS NOW DEAD.**

### 23.1 ✅✅ OPERATOR WAS RIGHT, I WAS WRONG: THE FC *IS* ON THE OLD/CLEAN BUILD
⛔ **§3's "the firmware was never rolled back / still `f0889f3d`" IS WITHDRAWN — it was measured 08-22 and
the operator flashed `a52c38b` at ~21:45-21:55 on 08-23** (that is the source of the 2 log-less "clean reboots").
🔑🔑 **BYTE-ORDER TRAP THAT PRODUCED THE WRONG READ: `flight_custom_version` COMES OFF THE WIRE REVERSED.**
Live bytes `00 00 02 7d b0 38 2c a5` → read back-to-front = **`a52c38b07d020000`** = the `# Git Revision:`
of `PXlabs_..._tested_2026-08-15.params`. ⇒ **ALWAYS REVERSE THE ARRAY BEFORE COMPARING.**
🔧 Rebuilt tool (the old scratchpad one was gone): `scratchpad/fwver.py` — also prints **board UID**.
✅ **RECORD THIS, IT NEVER EXISTED BEFORE: FC BOARD `uid = 0x1622680e82939530`,
`uid2 = 00090000000000000000829395301622680e`, `board_version 0x1d`, vendor/product `0x3643/0x001d`.**
⇒ **from now on board identity is checkable; the whole 4-board campaign had NO board-identity record.**

### 23.2 🔴🔴 THE RESULT: THE CLEAN-ERA BUILD HARDFAULTS. **DON'T PLAN ANOTHER FLASH TEST.**
**2 fresh faults pulled 23:45:30 + 23:50:11 IST (log names are UTC: `18_15_30`, `18_20_11`).**
🔑 **THE LOG ITSELF CARRIES THE GIT-HASH — ELF-INDEPENDENT, NO AMBIGUITY:**
**`FW git-hash: a52c38b07d38f6abce1adc5d58681481325c95ff`, `Build datetime: May 31 2026 18:19:40`** in BOTH.
⇒ ✅ **THE §4 "DECISIVE TEST" IS DONE — its firmware half was already in place and it FAILED to fix anything.
THE 2.1.0 IMAGE IS ELIMINATED. `f0889f3d` vs `a52c38b` IS NOT THE VARIABLE.**
⛔ **Every suspect on the ELIMINATED list plus params plus firmware is now gone. Do not re-run any of them.**

### 23.3 🔬 NEW SIGNATURE — **INSTRUCTION-FETCH CORRUPTION, NOT A NULL DEREF** (supersedes §"ROOT CAUSE 08-21")
| | fault A 18:15:30 | fault B 18:20:11 |
|---|---|---|
| task | `wq:uavcan` | `mavlink_if1` |
| site | `armv7-m/arm_memfault.c:101` | **`chip/imxrt_irq.c:272`** |
| `cfsr` | **`0x00000001` = IACCVIOL** (instruction access violation) | **`0x01000000` = UNDEFINSTR** (undefined instruction) |
| `pc` | `0x8a18303c` **garbage** | `0x30136504` **VALID XIP CODE ADDRESS** |
| `lr` | `0x30189c2b` **valid XIP** | `0x00001a30` garbage |
🔑 **BOTH FAULTS ARE THE CPU FAILING TO *FETCH/DECODE* AN INSTRUCTION — not a bad data pointer.**
🔑 **`r7 = pc|1` in fault A** ⇒ the jump target was loaded from a register already holding garbage.
🔑🔑 **THE BOARD IS i.MX RT (`imxrt_irq.c`; params are `..._NXP_...`), SO `0x30000000` IS THE FlexSPI XIP
FLASH WINDOW — CODE IS EXECUTED IN PLACE OVER A SERIAL BUS.** Fault B fetched from a *legitimate* code
address and got an *undefined instruction* back. ⇒ 🔬 **LLEAD: XIP/FlexSPI READ CORRUPTION** — fits
random victim task, random garbage PC, immunity to firmware/param/companion/CAN/power-module changes.
⚠️ **NOT PROVEN, and it must explain 4 BOARDS faulting** ⇒ look for a COMMON-MODE driver (FlexSPI clock/timing
config, the 5 V/1.8 V rail, temperature), not a bad flash chip. ⏭ **`system_power` into `dds_topics.yaml` is now
the highest-value queued item — §"The measurement gap" rail was always the XIP suspect and is STILL unmeasured.**

### 23.4 ✅ THE OPERATOR'S RATE-CONTROL ERROR — REAL, BUT A *SYMPTOM OF THE FLASH*, NOT A CAUSE
Error seen: **"Invalid configuration for rate control: Neither feed forward nor feedback is setup"**.
Source **`DifferentialRateControl.cpp:107`**: fires when
**`(RD_WHEEL_TRACK < eps || RO_MAX_THR_SPEED < eps) && RO_YAW_RATE_P < eps`**.
✅ **MEASURED LIVE 23:40: `RO_MAX_THR_SPEED = 0.0` AND `RO_YAW_RATE_P = 0.0`** (also `RO_SPEED_P=0`,
`RO_SPEED_I=0`) ⇒ **the flash wiped the tuned rover gains to factory; the condition is genuinely true.**
✅ `RO_ACCEL_LIM`/`RO_DECEL_LIM` **still −1** (the 08-14 wall-hit revert survived) · `SYS_HAS_MAG` now **1**.
🔴🔴 **OPERATIONAL CONSEQUENCE — THE ROVER WILL NOT DRIVE ARMED:** `RoverDifferential.cpp:161` sets
**`_sanity_checks_passed = false`**, and `Run()` gates **`updateActControl()`** on it ⇒ **no actuator output.**
⏭ **FIX = restore from `PXlabs_..._tested_2026-08-15.params`: `RO_MAX_THR_SPEED 0.6 · RO_YAW_RATE_P 0.08 ·
RO_SPEED_P 0.5 · RO_YAW_P 2` (all `RO_*` = ROVER-ONLY, safe for the shared drone FC), then `param save`.**
🔑🔑 **DIRECTION OF CAUSATION — THE RESTART BRINGS THE ERROR, THE ERROR DOES NOT BRING THE RESTART:**
1. **DATE KILLS IT:** faults began **08-16**, when `RO_YAW_RATE_P` was the tuned **0.08** ⇒ the condition was
   FALSE for the entire fault era. The error only became possible after tonight's flash.
2. **RATE KILLS IT:** `runSanityChecks()` runs ONLY on a param update or a control-mode CHANGE
   (`RoverDifferential.cpp:57,76`) — **not per-cycle**, so it cannot flood the event/mavlink path.
3. **TASK KILLS IT:** it lives in `rover_differential`; the two crashes are `wq:uavcan` and `mavlink_if1`.
   And `events::send()` cannot corrupt a program counter.
⇒ **it reappears after EVERY reboot until the gains are restored. Expect it; it is not a new fault source.**

### 23.5 ⚠️ HOUSEKEEPING
- 🔴 **THE 22:00 SOAK DIED AT 23:03** (`pgrep` empty) — **45+ min unobserved.** Its window scored
  **10 reboots / 3 fault logs in 62 min**, but it spans the flash so ⛔ **do not quote it as a rate.**
- ✅ **Card pulled clean at 23:50** (`ftp_pull_faults.py`, both VERIFIED, `~/fc_faults/`). ⚠️ **First attempt
  returned the 2nd log INCOMPLETE ("NO trailer") because the FC was still writing it — RE-PULL, don't trust it.**
- ⏭ **Operator declined restarting the soak (still working on the FC). Restart it once they are done —
  now that the build is `a52c38b`, every new fault counts against the clean image.**

## 24. 2026-08-24 00:15 — ✅✅ **THE ELF TRAP IS SOLVED. ALL 56 FAULTS RESOLVED TO FUNCTION NAMES.**

### 24.1 🔑🔑 THE MATCHING ELF WAS ON THIS BOX THE WHOLE TIME
**`~/fc_firmware/CLEAN_v1.17.0-2.0.0_px4_fmu-v6xrt_default.elf`** (59 MB, with `.bin` + `.px4`).
✅ **VERIFIED IDENTICAL TO THE RUNNING IMAGE — `strings` shows BOTH
`a52c38b07d38f6abce1adc5d58681481325c95ff` AND the fault log's `Build datetime: May 31 2026 / 18:19:40`.**
⇒ ⛔ **THE §"ELF TRAP" WARNING IS NOW OBSOLETE FOR `a52c38b` — resolve against THIS file, not the source tree.**
🔑 **NO ARM TOOLCHAIN IS NEEDED (none is installed): `readelf -sW <elf>` reads the symbol table of a foreign
architecture fine.** Symbols → `awk '$4=="FUNC"{print $2,$3,$8}'` → bisect the PC. ⚠️ **Thumb symbols carry
bit0 SET, so mask BOTH the symbol and the PC or every offset reads 1 too high.**
✅ **BOARD IDENTIFIED: `px4_fmu-v6xrt` (i.MX RT1176).** Linker map: **bootloader `0x30000000` +128K,
application `0x30020000` + (4M−128K) ⇒ code runs to `0x303E0000`.**

### 24.2 ⛔⛔ **I RETRACT THE "BIT-SHIFT / XIP CORRUPTION" LEAD FROM §23.3 — IT WAS THE WRONG-RULER TRAP**
I compared the fault PCs against `nxp/tropic-community` (flash `0x60000000`) and `nxp/mr-tropic`
(`0x70020000`), concluded `0x30xxxxxx` was unmapped, and "discovered" that every bad address doubled into
flash. **The real board links code AT `0x30020000`.** ⇒ **the addresses were never corrupt at all.**
🔑🔑 **THE CHECK THAT KILLED IT — PARITY, AND I SHOULD HAVE RUN IT FIRST: 40/40 PCs are EVEN and 36/36 LRs
are ODD.** That is the ARM thumb convention intact; random corruption gives ~50/50. **A "signature" that
requires the ARM calling convention to survive by luck is not a corruption signature.**
⛔ **Also retract MEMORY.md's older "jumps to garbage PCs" — 40/56 PCs resolve to real functions.**
→ this is exactly `feedback_independent_rulers`; **the linker script IS the ruler, get it from the board id.**

### 24.3 📊 WHAT THE RESOLVED FAULTS ACTUALLY SAY
**8 DIFFERENT CFSR CLASSES** — `DACCVIOL`+MMARVALID **16** · `UNDEFINSTR` **13** · **`NOCP` 10** ·
`INVSTATE` **8** · `DIVBYZERO` **3** · `IBUSERR` **3** · `IACCVIOL` **2** · `IMPRECISERR` **1**.
**VICTIM TASKS:** `uxrce_dds_client` **21** · `wq:INS0` **11** · `wq:uavcan` **9** · `mavlink_if1` **3** ·
`wq:ttyS3` **3** · others 1-2 (`gps`, `commander`, `hpwork`, `wq:SPI3`, `wq:nav_and_controllers`).
🔑 **PCs scatter over ~40 UNRELATED functions** (EKF covariance, ucdr serializers, `MapProjection`, CRSF
parsing, `memcpy`, `vsprintf`, uavcan `BitStream`, `matrix::Euler`…). 🔑🔑 **TWO ARE LOGICALLY IMPOSSIBLE:
`MulticopterRateControl::Run()` and `MissionBlock::is_mission_item_reached_or_completed()` — on a ROVER,
inside `wq:uavcan`. Neither can legitimately execute there ⇒ those PCs are WILD JUMPS into valid code.**
⇒ **NOT ONE SOFTWARE BUG. A single bug repeats in one place; this is broad state corruption.**

### 24.4 🔬 THE TWO REAL CLUSTERS — THE ONLY NON-RANDOM STRUCTURE IN 56 FAULTS
- 🔴 **`sym::PredictCovariance<float>` ×7, ALL with `cfsr=0x00080000` = `NOCP`, all in `wq:INS0`.**
  **NOCP = an FPU instruction executed while the FPU was disabled.** PredictCovariance is the 24×24
  float-heavy EKF step. ⇒ **the FPU context / `CPACR` / `CONTROL.FPCA` is being lost.** (Log shows
  `control:0x00000004` = FPCA set.) **This is specific and repeatable — the best handle we have.**
- 🔴 **`ucdr_serialize_esc_status` ×5, mostly `cfsr=0x82` = `DACCVIOL`** (MPU data-access violation).
  ⚠️ **OPEN CONTRADICTION TO CHECK: these land on 08-18/20/21/22, i.e. AFTER CAN was physically removed
  (§ELIMINATED). If `esc_status` had zero publishers, why was it being serialized at all?**
- 🔑 `wq:ttyS3` faults are all in **CRSF parsing** (`ProcessChannelData`) — consistent with victim-shift
  once CAN went away, not a new cause.

### 24.5 ⏭ WHERE THIS LEAVES THE HUNT (hardware swapping is EXHAUSTED — stop swapping)
Everything individually removed (CAN, uXRCE, RC, companion, power module, SD, IMU, 4 boards, both
firmwares) and faults continued ⇒ **look for a COMMON-MODE factor, ranked:**
1. 🔬 **DMA/cache coherency or MPU/FPU config in the firmware** — same binary on every board, so it
   survives board swaps; load-dependent, so "3 months clean then faulting" fits. **Fits the NOCP and
   DACCVIOL clusters directly.** ⏭ audit `dtcm_nocache` placement of DMA buffers on v6xrt.
2. 🔬 **The FC's own supply rail — STILL NEVER MEASURED** (`system_power` absent from `dds_topics.yaml`).
3. 🔬 **The carrier / base board.** FMUv6X-RT is a MODULE on a BASE BOARD. If 4 *modules* were swapped
   onto ONE base board, the base board is un-eliminated — **the same argument already made for the IMU.**
   ⏭ **ASK THE OPERATOR: was the base board ever changed?**

### 24.6 ✅ HOUSEKEEPING 08-24
- ✅ **CARD DELIBERATELY WIPED CLEAN AT 00:05 ON OPERATOR'S REQUEST** — both 08-23 logs verified
  (trailer present) into `~/fc_faults/` first; **56 logs / 2.4 MB archived.** Card baseline is now **0**.
- ⏭ **OPERATOR IS RUNNING A NEW ISOLATION TEST: USB DIRECT TO THE FC FOR MAVLINK, COMPANION MAVLINK
  DISCONNECTED.** ⚠️ **IT CHANGES TWO VARIABLES AT ONCE (MAVLink path *and* the FC's power source — USB
  vs vehicle rail). That makes it a great SCREEN but a poor attribution test** — if it goes quiet, split
  the two before concluding. ⚠️ **`mavlink_if1` is only 3/56 victims, so MAVLink is a WEAK suspect on the
  evidence — the operator's own doubt is correct.** 🔑 **COUNTING WITHOUT THE COMPANION MAVLINK PATH: the
  MAVFTP card poll dies, so use (a) QGC's own hardfault notice, (b) the DDS uptime detector if uXRCE stays
  connected, (c) `rover-autonav-mode` FMU-timeout journal proxy. Re-pull the card afterwards.**

## 25. 2026-08-24 00:30 — **MAVLINK ELIMINATED. EMI/DRIVE-POWER SCREEN RUNNING. RESUME HERE.**

### 25.1 ✅ MAVLINK IS ELIMINATED — OPERATOR DISCONNECTED THE COMPANION MAVLINK LINK AND IT STILL FAULTED
Fault **2026-08-23 18:45:08 UTC (00:15 IST)**, resolved against the ELF:
**task `wq:ttyS3` · `cfsr=0x00010000` UNDEFINSTR · PC `CrsfParser_TryParseCrsfPacket+0x196` ·
LR same fn `+0x76` · FW `a52c38b`.** ⇒ **victim moved to the RC/CRSF serial task — the same victim-shift
seen when CAN was removed. 4th CRSF fault.** ⛔ **Do not re-test MAVLink.**
🔑 **WHAT "COMPANION MAVLINK" ACTUALLY COVERS — ALL OF MY FC TOOLING GOES OVER `tcp:127.0.0.1:5760`:**
**`set_param.py` is MAVLINK, NOT DDS** (⚠️ contradicts the instinct from `use_dds_not_mavlink`) ·
`ftp_pull_faults.py` (MAVFTP) · `fwver.py` · `mavlink_shell.py` · **`fc_soak.py` uses DDS for uptime but
IMPORTS `ftp_pull_faults` for the card poll.** ⇒ **with companion MAVLink down I CANNOT read/write params,
pull fault logs, or check firmware — only DDS survives. Plan QGC-over-USB for param work.**

### 25.2 🔴🔴 THE FIRMWARE FLIP-FLOPPED AT LEAST 3× — AND THE FAULT LOGS DATED IT ALL ALONG
**EVERY fault log carries `FW git-hash`. Tallying all 56 (only 2 hashes, both `Build datetime May 31 2026`):**
| period | firmware | faults |
|---|---|---|
| 08-16 | `f0889f3d` | 9 |
| **08-18 → 08-21** | **`a52c38b`** | **23** |
| 08-22 early | `f0889f3d` | 5 |
| 08-22 19:13 → 08-23 | `a52c38b` | 19 |
⇒ 🔑🔑 **THE "3-MONTHS-CLEAN" BUILD WAS FAULTING FOR FOUR STRAIGHT DAYS FROM 08-18. The firmware was
eliminable a WEEK before §23 "discovered" it — the proof was in every log header and the campaign never
read that field.** ⛔ **Never anchor a conclusion to "which firmware was on" from memory or from a single
`AUTOPILOT_VERSION` read — TALLY THE HASH ACROSS THE LOGS.**
✅ **Onset date HOLDS at 08-16 05:01** (operator asked). The 17 undated `fault_1970_*` logs are NOT hidden
earlier evidence — **their archive mtimes prove they were all pulled 08-20 or later.**
✅ **NO MAVLINK CHANGE ON THE COMPANION near the boundary:** `/etc/mavlink-router/main.conf` untouched since
**2026-03-15**, `mavlink.router.service` since **2025-02-08**, no MAVLink commits in `codex-work` in August.
⏭ **LOOSE END, UNCHASED:** something modified **`/etc` at 2026-08-16 09:47** and **`/etc/sid.conf` at 10:53**
(backup `sid.conf.bak-20260816` taken 08-15 18:56) — sits exactly on the fault boundary, not MAVLink on its face.

### 25.3 ⛔ I RETRACT MY ARGUMENT AGAINST EMI — IT WAS WEAK, THE OPERATOR WAS RIGHT
**My reasoning was "motors are IDLE, so the dominant EMI source is off."** ⛔ **WRONG FRAME: powered VESCs
are SWITCHING CONVERTERS — gate drivers, the DC-DC stage and the CAN transceivers all run at zero RPM.
"Motors idle" ≠ "drives unpowered".** The MEMORY.md line "EMI NOT SUPPORTED because motors idle" is
**WITHDRAWN**; EMI from the drive electronics was never actually tested until now.
🔑🔑 **EXPERIMENT-ORDER LESSON (operator wanted to bisect front-pair/rear-pair to localise the source):
BISECTING BEFORE CONFIRMING GIVES A FALSE NEGATIVE IF THE SOURCES ARE REDUNDANT** — if either pair alone
suffices, both halves test "still faults" and you wrongly close EMI, while all-four-off would have been
quiet. ⇒ **SCREEN WITH ALL FOUR OFF FIRST; bisect ONLY after the effect is confirmed. You cannot localise
a cause you have not yet shown exists.** (Operator agreed and removed all four.)

### 25.4 🟡 LIVE TEST RUNNING UNATTENDED — CHECK THIS FIRST TOMORROW
**ALL FOUR MOTOR DRIVERS UNPOWERED.** Soak started **2026-08-24 00:31:03**, PID at start **102011**,
marker `ALL FOUR MOTOR DRIVERS UNPOWERED - EMI screen` in `~/fc_soak/marks.txt`.
**Card baseline 0 (wiped + verified). FC on `a52c38b`, uptime 2.8 min at the mark.**
⏭ **READ: `cat ~/fc_soak/status.txt` · `python3 ~/ros2_ws/tools/fc_soak_report.py`.**
⏭ **HOW TO JUDGE:** ⚠️ **rate swung wildly on 08-23 (22.4/hr early evening vs ~3/hr later) — a 10-min quiet
window is WORTHLESS. Need 30-60 min, and count REBOOTS *and* FAULT LOGS (the 2-detector rule that stopped
us scoring the operator's param reboots as faults).**
⏭ **IF QUIET → the drives are implicated: NOW bisect (front pair, then rear pair) to localise.**
⏭ **IF STILL FAULTING → the drive electronics are ELIMINATED as a whole**; fall back to §24.5's ranked
common-mode list: **(1) DMA/cache-coherency or MPU/FPU config in firmware (the `PredictCovariance`×7 `NOCP`
cluster is the best handle) (2) the FC rail, still never measured (3) the CARRIER/BASE BOARD — v6xrt is a
module on a base board; if 4 modules went onto ONE base board it is UN-ELIMINATED. ASK THE OPERATOR.**

### 25.5 ⚠️ TOOL TRAPS FOUND TONIGHT
- 🔴 **`fc_soak.py` HAS NO ARGPARSE — `python3 fc_soak.py --help` SILENTLY STARTS A FULL SOAK.** I did this
  and had to kill it. **Never probe it with `--help`; it takes no arguments.**
- 🔴 **`pgrep -f "[f]c_soak.py"` STILL SELF-MATCHED** because the *same compound command* also contained the
  literal string in a later `grep`. **The bracket trick only protects the pattern, not the rest of the line.**
  ⇒ **verify any pgrep hit with `ps -o pid,cmd -p <pid>` before believing a process exists.**
- ✅ **Fault-log archive: 57 logs / ~2.4 MB in `~/fc_faults/`.** Resolve PCs with
  `readelf -sW ~/fc_firmware/CLEAN_*.elf` → mask bit0 on symbol AND pc → bisect (§24.1).

## 26. 2026-08-25 00:00-00:40 — 🔴 **EMI SCREEN INVALID (motors were powered). 3-FAULT BURST. INSTRUCTION-LEVEL DISASSEMBLY NOW POSSIBLE — 57% ARE EXECUTION-STATE FAULTS.**

### 26.1 ⛔⛔ THE EMI SCREEN OF §25.4 NEVER RAN — DO NOT SCORE IT EITHER WAY
- **`fc_soak.py` DIED AT 00:38:49 on 08-24**, 8.1 min in (`ExternalShutdownException` — the companion
  went down at 00:38:53). `~/fc_soak/status.txt` still reads *"VERDICT: CLEAN so far, 0 reboots"* —
  🔑 **THAT FILE IS STALE FROM 00:38. It is not evidence of anything.**
- 🔴 **OPERATOR CONFIRMED (08-25): THE MOTORS WERE POWERED.** The drives were re-powered at some point
  after the 00:31 marker, so the 02:02 faults happened **with drives live**.
  ⇒ **EMI IS NEITHER TESTED NOR ELIMINATED. It is exactly where §25.3 left it.** If it is to be run,
  re-run it from scratch **with the soak verified alive** (`pgrep -f fc_soak` + a fresh status.txt mtime).

### 26.2 🔴 THE BURST — 3 faults in 68 s, 3 different tasks, 3 different classes
| time (FC RTC, verified correct) | task | class | resolved pc |
|---|---|---|---|
| 2026-08-24 02:02:14 | `wq:uavcan` | UNALIGNED | `UavcanNode::publish_node_statuses+0x10` |
| 2026-08-24 02:02:43 | `hpwork` | UNDEFINSTR | **pc=0x00000000**, lr → `devif_conn_event+0x1c` |
| 2026-08-24 02:03:22 | `wq:INS0` | NOCP | `sym::PredictCovariance<float>+0x372` |
- Archive is now **60 logs**. FC+companion power-cycled together 08-24 23:42 (operator); **no fault on
  the current boot.**
- 🔑 **Fault 1 is internally verified:** log has `r4=0x202592a7`, `r5=0x2025bd27`, and the code does
  `add.w r5,r4,#0x2a80` → **the arithmetic matches exactly**, then `ldrd r3,r2,[r5,#40]` on an odd
  address ⇒ UNALIGNED. **`this` was 0x202592a7 — an ODD C++ object pointer, which is impossible.**
- 🔑 **Fault 2 is a corrupted stacked return address:** lr points just past `bl __net_unlock_veneer`,
  and the next instruction is `ldmia.w sp!, {r4..r9,sl,pc}` — the epilogue **popped pc from the stack**.
  T-bit is SET with pc=0 ⇒ **the stack held exactly 0x00000001.**

### 26.3 ✅✅ NEW CAPABILITY — **THIS BOX CAN DISASSEMBLE THE FIRMWARE. USE IT.**
`objdump` here supports **`elf32-littlearm`** (no ARM toolchain needed, same as readelf).
```
objdump -d ~/fc_firmware/CLEAN_v1.17.0-2.0.0_px4_fmu-v6xrt_default.elf
```
- ✅ **ELF re-verified as the running image**: git hash `a52c38b…` AND build datetime `May 31 2026
  18:19:40` both present in the ELF and both match the fault-log header.
- ✅ **Mapping symbols exist (16656 `$t`, 12981 `$d`)** ⇒ objdump separates code from literal pools,
  so **instruction boundaries are authoritative, not a linear-sweep guess.**
- ⛔ **MASK BIT0 ON THE SYMBOL ADDRESS BEFORE `--start-address`** — `PredictCovariance` is listed at
  `0x300fdb0d`; starting there decodes garbage. True entry `0x300fdb0c`.
- 🔴🔴 **TOOL TRAP THAT COST ME A WRONG ANSWER: `objdump -d` emits NO LEADING SPACE for 8-hex-digit
  addresses** (`300c2914:\t…`) but pads short ones (`    1cc4:\t…`). A filter like
  `if not line[0].isspace(): continue` **silently drops the entire main .text** and every pc then
  looks "mid-instruction". **Caught it because a pc I had already decoded by hand came back MID.**

### 26.4 🔬 WHAT THE INSTRUCTION-LEVEL PASS ACTUALLY SHOWS (all 60 logs)
**Fault-class split — the headline:**
- **EXECUTION-STATE faults (UNDEFINSTR + INVSTATE + NOCP): 34/60 = 57%**
- data-access faults (DACCVIOL/UNALIGNED/IMPRECISE): 21/60 · instruction-fetch (IBUSERR/IACCVIOL): 5/60

✅ **THE NOCP CLUSTER IS CONFIRMED AT INSTRUCTION LEVEL — it is no longer an inference from the
function name.** Of 11 NOCP faults, **7 land on a genuine FPU instruction** (`vldr s19,[r4,#1008]`,
`vstr s2,[sp,#256]`, `vfma.f32 s20,s14,s26`, …), 1 on a non-FPU insn, 3 on unusable pcs.
⇒ **float code really was executing with the FPU disabled. CPACR / CONTROL.FPCA / lazy-FP state is
being lost.** Still the best handle in the whole campaign.

🔑 **All 8 INVSTATE faults are branches to EVEN (Thumb-bit-clear) targets** — `0x0` ×3, `0x10`,
`0x1a`, `0x3000`, and **two into RAM** (`0x200337c0`, `0x20035960`). Corrupted function pointers.

🔴 **7 UNDEFINSTR faults land on ORDINARY, PERFECTLY LEGAL INSTRUCTIONS** — `mov r5,r2`,
`adds r3,#1`, `ldr r3,[sp,#4]`, `strd r6,r3,[sp]`, `mov.w r9,#0`, `bl __perf_end_veneer`.
**None of these can ever raise UNDEFINSTR if the bytes fetched matched the bytes in flash.**

📊 **17/60 (28%) of fault pcs are NOT a valid instruction boundary** (mid-instruction), and 6 more are
outside the loaded image entirely.

### 26.5 ⛔ HYPOTHESIS KILLED THIS SESSION — DO NOT RE-PROPOSE
**IT-block / EPSR.IT corruption is DEAD.** It was the one mechanism that could make a plain `mov`
raise UNDEFINSTR (instructions inside a phantom IT block are UNPREDICTABLE). **Measured: IT bits are
ZERO in 59/60 faults.** Killed by its own test.
🔑 **Also measured: 0/60 faults were taken inside an ISR** (xPSR ISR# == 0 every time) — every fault is
in thread mode. Argues against an interrupt-handler defect and fits "victim = whichever task was busy".

### 26.6 ⏭ WHERE THIS POINTS — the surviving unifying mechanism
The mix (wrong pc → wild jump / pc=0 · wrong xPSR → T-bit lost · wrong FP context → NOCP · wrong
registers → odd `this`, bad pointers) is **exactly what a CORRUPTED EXCEPTION STACK FRAME produces**,
because the CPU restores pc, xPSR and the FP context **from RAM** on every exception return. That
survives board swaps, is task-agnostic, and is thread-mode-only — matching every elimination to date.
⏭ **Ranked next steps (hardware swapping is exhausted — §24.5 stands):**
1. 🔬 **DMA / cache-coherency and MPU/FPU config** — audit `dtcm_nocache` placement of DMA buffers on
   v6xrt, and the NuttX lazy-FP (`FPCCR.LSPEN`) context-switch path. **Fits the NOCP cluster directly.**
2. 🔬 **The FC's own supply rail — STILL NEVER MEASURED.** ⛔ **08-25: I tried to close this over
   MAVLink and FAILED — `POWER_STATUS` is NOT streamed by this build** (requested it explicitly via
   `SET_MESSAGE_INTERVAL`, 30 s, zero messages). The rail still needs `system_power` bridged to DDS
   (FC flash) or a scope. **Pair it with the queued `vehicle_angular_velocity` flash.**
3. 🔬 **The carrier / base board — 4 modules on ONE base board. ⏭ STILL UNASKED: was it ever changed?**

### 26.7 ✅ HOUSEKEEPING
- ✅ **3 logs pulled + VERIFIED (trailer present) into `~/fc_faults/`. NOT deleted from the card** —
  they are still there, so **QGC will keep announcing them at every boot.**
- ✅ **ROVER GAINS ARE RESTORED — todo (c) IS DONE.** Measured 08-25: `RO_MAX_THR_SPEED 0.6` ·
  `RO_YAW_RATE_P 0.08` · `RO_SPEED_P 0.5` · `RO_SPEED_I 0.1` · `RO_YAW_P 2.0` ·
  `RO_ACCEL_LIM`/`RO_DECEL_LIM` = **−1**. ⇒ the *"Invalid configuration for rate control"* message of
  §23.4 should be GONE; a QGC message seen now is something else.
- 🔑 **`mavlink-routerd` runs on the COMPANION as pid 757 on :5760, but there is NO `mavlink-router`
  systemd unit here** (`systemctl is-active` → "could not be found"). Check `ss -ltnp | grep 5760`.
- 📄 Scripts kept in the session scratchpad: boundary/instruction-class analysis over all 60 logs.

### 26.8 ⛔⛔ 2026-08-25 — **BASE BOARD ELIMINATED. OPERATOR: "ENTIRE FC IS CHANGED".**
The 4 swaps were **complete FC assemblies (module + carrier/base board)**, not modules onto one base
board. ⇒ **§24.5 suspect 3 and §25.4's open question are CLOSED. Do not ask again, do not swap again.**

🔴🔴 **THIS EXHAUSTS THE HARDWARE LIST — so the elimination LOGIC itself must now be audited, and one
elimination does not hold up:**

⚠️⚠️ **"BOTH FIRMWARES ELIMINATED" IS A FLAWED ELIMINATION.** `f0889f3d` and `a52c38b` are **both
`px4_fmu-v6xrt` builds** and therefore **share the same NuttX board-support layer**: MPU region setup,
D-cache/I-cache policy, DMA-buffer placement (`dtcm_nocache`), and FPU / lazy-stacking (`FPCCR.LSPEN`)
configuration. **A defect in that shared layer is present in BOTH images, so swapping VERSIONS never
tested it.** The firmware is eliminated only for *version-differential* defects. 🔑 **This is exactly
where §26.4's evidence points: 57% execution-state faults and an FPU that is genuinely disabled while
float code runs.**

⇒ **ONLY THREE SUSPECTS SURVIVE:**
1. 🔬 **The shared v6xrt board-support config** (MPU / cache / DMA placement / lazy-FP). Strongest fit.
2. 🔬 **The wiring harness + the FC supply rail it plugs into** — swapping the FC does NOT swap the
   cable it plugs into. **STILL NEVER MEASURED** (`POWER_STATUS` not streamed — §26.6).
3. 🔬 **EMI** — never actually tested (§26.1).

### 26.9 ⏭⏭ THE DISCRIMINATING TEST — ONE RUN SPLITS 1 FROM 2+3, NO FLASH, NO NEW HARDWARE
**Bench-soak a complete FC: USB power only, physically AWAY from the vehicle, NOTHING else plugged in**
(no harness, no drives, no CAN, no companion, no RC). Leave it ≥2 h.
- **STILL FAULTS ⇒ suspects 2 and 3 are both dead; it is the firmware's shared board-support config.**
- **GOES QUIET ⇒ it is external — then bisect: re-attach the harness/rail first, drives last.**
⚠️ **This is NOT the 08-23/24 USB test.** That one was USB-for-MAVLink **with the FC still in the
vehicle and the drives powered** (§24.6/§25.1) — it isolated the MAVLink path, never EMI or the harness.
⚠️ **JUDGE ON ≥2 h, and count REBOOTS *and* FAULT LOGS** (25-50 min to first fault; 25% of quiet gaps
were ≥53 min). **Detection with no companion: QGC's boot-time hardfault notice, then re-pull the card.**
🔑 **The FC self-loads enough on the bench** (IMUs + EKF run regardless) — `wq:INS0` is the 2nd-biggest
victim task, so the load that matters is present even with nothing attached.

### 26.10 2026-08-25 00:35 — CARD WIPED ON OPERATOR'S ORDER. **62 logs archived. THREE FLAGS.**
✅ **All backed up + trailer-verified into `~/fc_faults/` BEFORE deletion; card re-listed after = EMPTY.**
🔴🔴 **THE READ-ONLY LISTING IS UNRELIABLE — IT UNDER-REPORTED.** At 00:20 `ftp_pull_faults.py` said
**"fault logs on card: 3"**; 15 min later the `--delete` pass listed **5**, incl. two dated **08-24
18:35:14 (`uxrce_dds_client`, UNDEFINSTR, `ucdr_serialize_input_rc+0x76`)** and **18:35:49 (`wq:INS0`,
DACCVIOL+MMARVALID, `matrix::Quaternion<float>::inversed+0x32`)** — both written HOURS before the first
listing. ⛔ **NEVER trust a single listing for "card baseline 0" or a fault count — LIST TWICE.**
(The `--delete` path re-lists every round, which is why it caught them.)
🔴 **THE FC REBOOTED AT 00:05:53** (uptime 22.6 min at 00:04:59 → 30.0 min at 00:35:54, boot moved
23:42:23 → 00:05:53). ⚠️ **THIS WAS WITHIN ~50 s OF MY `SET_MESSAGE_INTERVAL`/`POWER_STATUS` PROBE —
I MAY HAVE INJECTED IT. Declare it; do not score that reboot as a spontaneous fault.** No log is stamped
00:05, so it did not commit a crashdump.
🔬 **NEW: the fault HANDLER field splits the corpus — `chip/imxrt_irq.c` 43 vs `armv7-m/arm_memfault.c`
19.** The memfault ones are **MPU MemManage** faults. 🔑 **08-24 18:35:49 faulted on a data access to
`0x301ece59` = `px4::WorkQueue::~WorkQueue+0x8` — an address in .text, i.e. a DATA ACCESS INTO THE CODE
REGION, refused by the MPU.** Fits §26.6's corrupted-pointer/exception-frame reading.

## 27. ⏭⏭ **RESUME HERE 2026-08-26 — THE OPERATOR IS RUNNING THE USB / BENCH TEST (started 08-25 ~00:40 IST)**

### 27.1 🔑🔑 BEFORE SCORING ANYTHING, ASK WHAT WAS ACTUALLY DISCONNECTED
The operator said only **"i going to run usb test"**. ⛔ **I DO NOT KNOW ITS CONFIGURATION, AND THE TEST
IS WORTHLESS UNTIL I DO** — this is the exact trap of §24.6: the 08-23/24 USB test looked decisive and
wasn't, because it changed the MAVLink path *and* the power source while the FC sat in the vehicle with
drives live. **ASK FIRST, IN THIS ORDER:**
1. **Was the FC physically OUT of the vehicle / away from the drives?** (decides EMI)
2. **Was the vehicle harness unplugged, or only the USB added?** (decides rail + harness)
3. **What stayed connected — RC/CRSF, GPS, companion, CAN?** (decides victim-task availability)
4. **How long did it run?**
⇒ **Only "FC on USB alone, off the vehicle, nothing attached" splits suspect 1 from 2+3 (§26.9).**
Anything less is a partial screen — score it as such and say which suspects it does NOT touch.

### 27.2 ✅ THE BASELINE IS CLEAN AND TRUSTWORTHY (this is the one thing that IS solid)
- **Card wiped 08-25 00:35 and RE-LISTED EMPTY.** Archive = **62 logs** in `~/fc_faults/`, all verified.
- ⛔ **LIST THE CARD TWICE tomorrow.** §26.10: a single listing under-reported 3 when 5 were present.
- **FC boot at 08-25 00:05:53** (may have been my own probe — §26.10; do not score it).

### 27.3 ⏭ HOW TO JUDGE THE RESULT
- **Detection:** re-pull the card (`ftp_pull_faults.py`, then list AGAIN); count **fault logs AND
  reboots** (2-detector rule). With no companion attached, QGC's boot-time hardfault notice is detector 2.
- ⚠️ **≥2 h before calling it quiet.** 25-50 min to first fault historically; **25% of quiet gaps were
  ≥53 min.** A 10-30 min quiet window proves NOTHING.
- **STILL FAULTS (and it was the full isolation) ⇒ rail + EMI both dead ⇒ the shared v6xrt board-support
  config (MPU / D-cache / DMA placement / lazy-FP) is the answer. Go read that code, stop testing hardware.**
- **QUIET ⇒ external. Bisect: harness/rail back FIRST, drives LAST** (§25.3: never bisect before the
  effect is confirmed).

### 27.4 📌 STATE CARRIED INTO TOMORROW
- **Hardware is EXHAUSTED — entire FCs (module+base board) ×4, IMUs, SD, power modules, CAN, companion,
  MAVLink, params all eliminated. ⛔ NEVER SWAP AGAIN.**
- **Only 3 suspects: (1) shared v6xrt board-support config (2) harness/FC rail, NEVER MEASURED
  (3) EMI, NEVER TESTED.** ⚠️ **"both firmwares eliminated" does NOT cover (1) — §26.8.**
- **Best evidence: 57% execution-state faults; NOCP ×11 with 7 confirmed on real FPU instructions
  ⇒ the FPU is genuinely disabled while float code runs.** → §26.4
- ✅ **I can disassemble the firmware now** (`objdump -d`, `elf32-littlearm`) — §26.3, incl. the
  leading-space trap.
- ✅ Rover gains restored; ⛔ `POWER_STATUS` is not streamed, so the rail cannot be closed over MAVLink.

## 28. 2026-08-25 22:20-22:45 — 🟡 **NEW LIVE SUSPECT: THE SD CARD *FORMAT* (never tested). USB TEST FAULTED. ~1 h CLEAN SINCE A WINDOWS REFORMAT — NOT YET EVIDENCE.**

### 28.1 🔑🔑 THE GAP: "BOTH SD CARDS ELIMINATED" WAS A **CARD SWAP**, NOT A REFORMAT
§135/§447 eliminated the SD **hardware** by swapping media. **The FILESYSTEM ON IT was never a variable**
— operator formatted **both** cards the same way, on a **Raspberry Pi**. A swap carries an identical
format across unchanged. ⛔ **This is the `eliminate_hypothesis_whole_family` trap: we tested the medium,
not the geometry on it.** ⇒ **SD FORMAT IS UN-ELIMINATED AND IS THE FIRST NEW VARIABLE IN DAYS.**

### 28.2 🔬 MECHANISM — fits the measured signature, and sits INSIDE suspect (1)
i.MX RT1176 USDHC DMAs into the FAT layer's buffers; the driver does D-cache clean/invalidate over those
ranges. **Cluster size / partition start that puts those buffers off a 32-byte cache-line boundary makes
`InvalidateDCache_by_Addr` discard DIRTY LINES OF NEIGHBOURING DATA** ⇒ corruption landing in whatever
task owns the adjacent bytes. **Predicts exactly §26.4: random victim task, ~40 unrelated functions,
8 CFSR classes, 57% execution-state faults, NOCP with the FPU genuinely disabled, INVSTATE to even
targets, and the 08-24 data-access-into-`.text` MPU fault.** 🔑 **Does NOT contradict suspect (1) — it
SHARPENS it: latent bug = shared v6xrt board-support cache/DMA handling; the card's format = the TRIGGER.**
🔑 Explains the USB-alone fault too: **the logger runs on USB power with nothing else attached.**

### 28.3 ✅ THE DETECTOR IS PROVEN LIVE THIS TIME (do not skip this check again)
⛔ **`fault_*.log` count = 0 is MEANINGLESS on its own** — a Windows format of a **>32 GB card defaults to
exFAT, which NuttX CANNOT MOUNT**, giving a PERMANENT FAKE "no faults". **RULED OUT BY MEASUREMENT:**
`/fs/microsd` lists **`System Volume Information`** (Windows artifact ⇒ reformat confirmed), **`log/2026-08-25/`**,
**`dataman` 128528 B**, **`parameters_backup.bson` 2866 B** ⇒ **PX4 HAS MOUNTED AND WRITTEN TO IT.**
⇒ the zero is a REAL zero. 🔑 **ALWAYS list the card ROOT, not just `fault_*`, before scoring a quiet window.**

### 28.4 ⚠️ WHAT THE EVIDENCE DOES *NOT* YET SUPPORT
- **Only ~1 h clean (operator's recollection; no timestamp).** §27.3: **25% of fault-era quiet gaps were
  ≥53 min** ⇒ ~1 h has roughly a **1-in-4 chance by luck alone**. ⛔ **NOT A PASS. Judge on hours.**
- 🔴 **CONFOUNDED: format + param restore changed TOGETHER.** Params were already dead (3-param diff),
  so format is the stronger candidate — but it is not a clean single-variable test.
- 🔴 **THE USB-TEST FAULT LOGS WERE ERASED BY THE FORMAT** — the last faults of the old era are GONE.
- 🔴 **§27.1 IS STILL UNANSWERED**: operator confirms *"connected only usb, still had hardfault"*, but
  **out-of-vehicle? harness unplugged?** is still unknown ⇒ **that fault still does NOT cleanly kill EMI/rail.**

### 28.5 ⛔ DETECTOR HOLE TODAY — AND THE FORGED TIMESTAMP CAUGHT AGAIN
`systemctl` reported `microxrce-agent` **ExecMainStartTimestamp=10:15:09, NRestarts=0** — **FORGED**;
`ps` showed **PID 758 started 22:08:28** and `/proc/uptime`=23 min. ⇒ **the agent was DOWN 10:15→22:08,
so the 12 h gap in `create_participant` is NO EVIDENCE OF QUIET.** 🔑 **`ps`/`/proc/uptime` BEAT `systemctl` here.**

### 28.6 ✅ MEASURED STATE 22:45
- `tools/fc_soak.py` **RUNNING** (3 detectors) — **FC booted 22:21:52**, card baseline **0**, reboots 0.
- **`SDLOG_MODE=0` ⇒ `.ulg` files are ARM SESSIONS, NOT BOOTS** — cannot be used as a boot detector.
  Two logs today (`16_52_00`,`16_53_19` **UTC** = 22:22/22:23 IST) = operator armed twice on RC.
- ✅ **PX4 log filenames are UTC** (16:52 UTC matched the 22:22 IST boot) ⇒ **fault_* names are UTC too.**
  ⚠️ §26.10's "written HOURS before the first listing" was therefore a TZ slip; `fault_2026_08_24_18_35_49`
  = **00:05:49 IST**, 4 s before the 00:05:53 reboot ⇒ **that reboot DID commit a crashdump and was a REAL
  spontaneous fault, not my probe.** ⛔ §26.10's "no log is stamped 00:05" is RETRACTED.
- ✅ **RC CH10 = 1011 (down/safe)**, link_quality 100 ⇒ companion will not be RC-rebooted mid-soak.
- ✅ `EKF2_EV_CTRL=4` re-read live — **valid, deliberate (bit2 = 3D velocity), NOT a fault suspect.** → §28.7

### 28.7 ✅ `EKF2_EV_CTRL = 4` IS CORRECT — CLOSED, DO NOT RE-ASK
Bitmask, bit 2 = **3D velocity** (`params_external_vision.yaml`). Set 2026-07-20; it is what makes
`v_xy_valid` true so AutoNav can arm. All other `EKF2_EV_*` = 0 is also correct (cam at origin, no delay).
⛔ **NEVER set 9** (pos+yaw) — that is the VIO target and **THERE IS NO VIO**. ⛔ **Cannot cause hardfaults**:
params eliminated by the 3-param diff, and an estimator tuning value cannot produce UNDEFINSTR/INVSTATE
across 40 unrelated functions. ⚠️ Only has effect while `rover-ekf-bridge` runs.

### 28.8 ⏭⏭ NEXT — THE FALSIFICATION TEST IS THE WHOLE POINT
1. **Let the soak run OVERNIGHT.** ≥2 h is the floor; **6-8 h+ is what makes this real.** Count logs AND reboots.
2. **Get the format's actual geometry** — the variable is cluster size + partition alignment. On a Pi:
   `sudo fdisk -l /dev/sdX` (start sector) + `sudo dosfsck -v /dev/sdX1` (cluster size, FAT type).
   **Compare Windows-format vs Pi-format.** Without this the "fix" is a black box.
3. 🔑🔑 **IF IT STAYS CLEAN, CONFIRM CAUSALLY: RE-FORMAT THE CARD PI-STYLE AND SEE IF FAULTS RETURN.**
   Correlation over one window is not cause — and this campaign has been fooled by exactly that
   (§20 charger, §25.1 USB) **three times**. ⛔ Do not close on a quiet window alone.

### 28.9 ⛔⛔ 2026-08-25 22:55 — **I RETRACT §28.2. THE SD-FORMAT / DMA-ALIGNMENT MECHANISM IS DEAD, KILLED BY THE SOURCE.**
**Operator asked "does the raspi flash tool create this issue". Checked against `~/PX4-Autopilot`. Answer: NO — that route is architecturally impossible.**
1. **`boards/px4/fmu-v6xrt/nuttx-config/nsh/defconfig`: `CONFIG_FAT_DMAMEMORY=y`, `CONFIG_GRAN=y`.**
   FAT sector buffers do NOT come from generic malloc.
2. **`platforms/nuttx/src/px4/common/board_dma_alloc.c`:** `g_dma_heap` is `__attribute__((aligned(64)))`
   and `gran_initialize(..., 7, ...)` ⇒ **128-byte granules.** Cortex-M7 line = 32 B ⇒ **every FAT/SD DMA
   buffer is cache-line aligned at both ends BY CONSTRUCTION, whatever the card's format.**
3. 🔑🔑 **`NuttX/arch/arm/src/imxrt/imxrt_usdhc.c: imxrt_dmapreflight()` EXPLICITLY GUARDS THE EXACT HAZARD
   I INVENTED** — its own comment: *"arch_flush_dcache could corrupt adjacent memory if the maddr and the
   mend+1 ... are not on ARMV7M_DCACHE_LINESIZE boundaries"*. It returns **`-EFAULT`** for any buffer not
   line-aligned at **start AND end**, and bounces unaligned RX through a dedicated aligned `priv->rxbuffer`.
⇒ **Cluster size / partition alignment / FAT type CANNOT change DMA buffer alignment.** A hostile format
produces **I/O ERRORS, NOT ARBITRARY RAM CORRUPTION** — and I/O errors are not our signature
(8 CFSR classes over ~40 unrelated functions).
🔑 **CONSEQUENCE: the SD *format* drops from "best new lead" to "UNEXPLAINED CORRELATION, MECHANISM ABSENT".**
The ~1 h quiet window is still just **1-in-4 luck** (§28.4) and now has **no theory behind it.**
⛔ **DO NOT tell the operator the card was the cause. DO NOT undo the format** (harmless; leave it, keep soaking).
✅ **Still true and still worth having: the card-swap-≠-reformat GAP (§28.1) was real** — but the gap being
open is not evidence the format was guilty. **Suspects (1)(2)(3) of §27.4 are UNCHANGED.**
⚠️ **The FAT layer's whole-sector fast path was the one bypass worth checking — it is ALSO covered, because
`dmapreflight` is applied to whatever buffer is handed down, user buffer included.**

## 29. 2026-08-25 23:05 — 🔴🔴 **§27.1 ANSWERED: THE FC FAULTED 20 km FROM THE ROVER, ON USB, OUT OF THE VEHICLE. EMI AND THE RAIL ARE BOTH DEAD. ONE SUSPECT LEFT.**

### 29.1 ✅✅ THE FULL-ISOLATION TEST OF §26.9 **WAS RUN, AND IT FAULTED**
**OPERATOR 2026-08-25:** FC **physically removed from the vehicle** and taken to **his OFFICE — a different
building ~5 km from home** — powered by **USB only**, and it **STILL HARDFAULTED.**
⚠️⚠️ **CORRECTION, RECORD IT: he first said "TESTED 20KM APART"; on being asked he clarified that was
LOOSE TALK, NOT A MEASUREMENT — the real separation is ~5 km (home → office). ⛔ DO NOT QUOTE "20 km".**
🔑 **The verdict is UNCHANGED, because the load-bearing facts were never the distance:** FC **OFF the
vehicle**, **off the harness**, **USB-powered**, **at a different site**. This is the discriminating run §26.9 asked for.
🔑🔑🔑 **AND THE RATE DID NOT CHANGE: OPERATOR SAYS IT FAULTED "WITHIN 10 MIN TO 15 MIN" AT THE OFFICE.**
That lands between the on-vehicle **median 5.4 min and p75 22.9 min** (§29.2) ⇒ **STATISTICALLY
INDISTINGUISHABLE FROM ON-VEHICLE.** ⛔ **This upgrades the elimination from "it still faulted" to "removing
the vehicle, the harness and the whole EMI environment changed the rate BY NOTHING." A contributing cause
must move the rate when removed. These did not move it at all ⇒ THEY CONTRIBUTE ZERO.**
⇒ 🔴 **SUSPECT (3) EMI — DEAD.** No rover, ESCs, motors, WFB radios or CAN anywhere near it.
🔑🔑 **STRONGER THAN A DISTANCE ARGUMENT: it has now faulted in TWO INDEPENDENT EMI ENVIRONMENTS
(home/rover and the office). A shared EMI cause would require both sites to carry the same interference
⇒ EMI gets LESS likely, not more.**
⇒ 🔴 **SUSPECT (2) HARNESS / FC RAIL — DEAD.** The FC was not plugged into the harness; power was USB.
⇒ ✅✅ **SUSPECT (1) — THE SHARED `px4_fmu-v6xrt` BOARD-SUPPORT CONFIG — IS THE LAST ONE STANDING.**
🔑 **Per §27.3 this was the pre-registered verdict: "STILL FAULTS (full isolation) ⇒ rail+EMI DEAD ⇒ it's
the SHARED v6xrt board-support config — GO READ THAT CODE, STOP TESTING HARDWARE."** ⛔ **HARDWARE IS OVER.**
⚠️ **Ask once, for the record: how long did the 20 km run last, and were RC/GPS still plugged in?** Neither
answer changes the EMI/rail verdict — the FC was off the vehicle either way.

### 29.2 📊 THE REAL FAULT-RATE DISTRIBUTION — **MEASURED FROM THE 45 DATED LOGS. USE THIS TO SCORE QUIET.**
⚠️ **17 of 62 archived logs carry a BAD CLOCK (`1970-01-01`) — EXCLUDE THEM or the stats are garbage.**
Era **2026-08-16 05:01 → 2026-08-24 18:35 UTC**, 38 usable inter-fault gaps (dormancy >12 h dropped):
- **median 5.4 min · mean 37.8 min · p75 22.9 min · p90 73 min** ⇒ in a BUSY hour ~12 faults.
- 🔑🔑 **LONGEST QUIET GAP EVER SEEN IN THE FAULT ERA = 437 min = 7.3 h** (2nd 6.5 h, 3rd 4.8 h).
- **P(quiet ≥1 h)=15.8% · ≥2 h=13.2% · ≥4 h=7.9% · ≥7 h=2.6% · ≥8 h = 0.0%**
⇒ 🔑🔑 **THE PASS MARK IS 8 HOURS CLEAN.** Below that the fault era itself produced comparable silences.
⛔ **RETRACTED: my earlier "25-50 min to first fault / 25% of gaps ≥53 min" — that conflated
time-to-first-fault-after-boot with the inter-fault gap. The measured median gap is 5.4 min.**
✅ **Operator's instinct was directionally right** ("within this time it hit with 5 faults") — a normal
hour holds several. But the tail is FAT: **1 h of quiet has occurred 16% of the time.** Not yet a pass.

### 29.3 🔴🔴 **THE TENSION THAT MUST BE RESOLVED — BOTH THINGS CANNOT BE TRUE**
**If (1) the board-support config is the cause, THE SD REFORMAT CANNOT HAVE FIXED IT** — and §28.9 already
killed every mechanism by which a card format could corrupt RAM. So exactly one of these holds:
- **(a) THE QUIET IS COINCIDENCE** (15.8% prior at 1 h) and **the faults come back.** ← default expectation
- **(b) SOMETHING ELSE CHANGED THAT WE HAVE NOT IDENTIFIED** — and it is NOT the format itself.
  ⏭ If the soak passes 8 h, **do not credit the card.** Enumerate everything that changed with it:
  param restore, `dataman` wiped, `parameters_backup.bson` rewritten, a fresh boot, RC re-paired.
⛔ **DO NOT CLOSE THIS CAMPAIGN ON A QUIET WINDOW ALONE — it has fooled us 3× (charger §20, USB §25.1, EMI §26.1).**

### 29.4 ⏭ NEXT ACTIONS, IN ORDER
1. **Soak to 8 h.** `fc_soak.py` running from 22:42 (FC booted 22:21:52, card baseline 0). Count logs AND reboots.
2. **FAULTS RETURN ⇒ campaign is settled: go read the v6xrt board-support code.** Start at the MPU/D-cache
   /DMA `dtcm_nocache` placement and lazy-FP `FPCCR.LSPEN` — **the NOCP evidence (§26.4: 7/11 on real FPU
   instructions ⇒ FPU genuinely disabled while float code runs) is the single best handle.**
   ✅ I can disassemble (`objdump -d`, §26.3) and I have `~/PX4-Autopilot` + `platforms/nuttx/NuttX` source.
3. **STILL QUIET AT 8 h ⇒ bisect what changed WITH the format (§29.3b)** — not the format.

### 29.5 ⛔⛔ **THE SOAK DIED SILENTLY — 2nd TIME. LAUNCH IT DETACHED OR IT IS WORTHLESS.**
A soak started as a normal Bash tool call **is killed when that call returns.** Run 22:42→23:05 (23 min)
then died; `status.txt` kept its last value and **looked alive**. This is what voided the 08-24 EMI
screen (§26.1, "soak died 8 min in"). ✅ **CORRECT LAUNCH:**
`cd ~/ros2_ws && setsid nohup python3 tools/fc_soak.py > ~/fc_soak/soak_detached_<date>.out 2>&1 < /dev/null &`
🔑🔑 **PROVING IT IS ALIVE — `pgrep -f "fc_soak"` SELF-MATCHES MY OWN SHELL AND THE `[f]` BRACKET TRICK FAILS
TOO** (my command line literally contains the pattern). ✅ **USE `pgrep -x python3` AND FILTER `/proc/<pid>/cmdline`:**
`for p in $(pgrep -x python3); do tr '\0' ' ' </proc/$p/cmdline | grep -q fc_soak && echo $p; done`
⛔ **NEVER score a quiet window without checking the soak's PID *and* that its .out file is still growing.**
✅ **RELAUNCHED DETACHED 23:08:18, PID 70323, card baseline 0, FC uptime 46.5 min.**

## 30. 2026-08-26 — ✅✅ **addr2line PASS OVER ALL 62 LOGS. `NOCP` IS NOW 8/8 ON A REAL FPU INSTRUCTION — UNANIMOUS.**
✅ **TOOL: `~/ros2_ws/tools/fc_fault_resolve.py`** (report → `~/ros2_ws/docs/fc_fault_resolution_20260826.md`).
✅ **THE ELF HAS FULL DWARF AND MATCHES THE LOGS** ⇒ `addr2line -e <elf> -f -C -i 0xPC` gives
**function + file:line + inline chain**, no probe, no toolchain install. This supersedes §26.3's
`readelf` symbol-table method. Run time ~4 min for 62 logs on this Pi.

### 30.1 🔴 **ONLY 48 OF 62 ARE RESOLVABLE — 14 ARE A FIRMWARE WE HAVE NO ELF FOR**
`FW git-hash` tally: **48 × `a52c38b0…` (= our ELF, = `~/PX4-Autopilot` HEAD)**, **14 × `f0889f3d…` (NO ELF)**.
The 14 are 08-16 (×9) and 08-22 00:49–04:52 (×5) ⇒ the flip is real and date-clean.
⛔ **NEVER resolve an `f0889f3d` log against this ELF — it yields confident nonsense.** The tool SKIPs them.
⏭ **Ask the operator for the `f0889f3d` build's `.elf` and 14 more logs unlock.**
⚠️ **`Build datetime` is `May 31 2026 18:19:40` on ALL 62 — identical across two different git hashes.
One of those two fields is unreliable; trust the HASH, it correlates cleanly with date.**

### 30.2 ✅ **THE `Type:` FIELD ALREADY CLASSIFIES EVERY FAULT — we were not reading it**
`chip/imxrt_irq.c:272` = `imxrt_usagefault()` PANIC · `:263` = `imxrt_busfault()` · `arm_memfault.c:101` = MemManage.
**All 62: 39 USAGE · 19 MEMMANAGE · 4 BUS.** CFSR over the 48 resolvable: USAGE 27, MEM 17, BUS 1, none 3.

### 30.3 🔬🔬 **THE HEADLINE — EVERY SINGLE NOCP IS ON AN FPU INSTRUCTION, AND THEY CLUSTER IN 2 FUNCTIONS**
| pc | instruction | function |
|---|---|---|
| `300fe61e` | `vstr s2,[sp,#256]` | `sym::PredictCovariance<float>` |
| `300fe67e` | `vldr s9,[sp,#356]` | `sym::PredictCovariance<float>` |
| `300fe57e` | `vldr s19,[r4,#1008]` | `sym::PredictCovariance<float>` |
| `300fe47e` | `vldr s19,[r4,#148]` | `sym::PredictCovariance<float>` |
| `300fdfbe` | `vfma.f32 s20,s14,s26` | `sym::PredictCovariance<float>` |
| `300fde7e` | `vfma.f32 s6,s5,s28` | `sym::PredictCovariance<float>` |
| `301b551e` ×2 | `vmul.f64 d9,d1,d9` | `MapProjection::project` |
🔑 **8/8 — no exceptions** (§26.4's "7/11" was over a set that included unresolvable logs).
🔑 **6/8 are inside ONE function, `sym::PredictCovariance<float>` (EKF2 covariance, task `wq:INS0`),
within a ~2 KB window; the other 2 are the SAME pc in `MapProjection::project`.**
🔑 **TWO MORE FPU instructions faulted as `UNDEFINSTR`, not NOCP: `301b550a` = `vpush {d8-d15}`
(MapProjection::project's FP PROLOGUE) and `300bbb3e` = `vmov s14,r3`.** ⇒ **10 faults = "an FPU
instruction refused to execute", concentrated in the two most FP-register-hungry routines in the image.**
⇒ **This is the lazy-FP / FPU-context signature. `FPCCR.LSPEN`/`ASPEN` + `CPACR` are the target.**

### 30.4 ✅ **THE `DACCVIOL` POPULATION IS A SEPARATE, ALREADY-KNOWN THING — NULL DEREF, CONFIRMED AT INSTRUCTION LEVEL**
**MMFAR = `0x00000000, 04, 08, 0a, 0c, 14, 20`** on 7 of the 15 DACCVIOL — small offsets from NULL,
almost all in `uxrce_dds_client`, **4× in `ucdr_serialize_esc_status`** at `str rX,[r4,#8]` /
`bl __memcpy_veneer`. Corroborates §17.18/§18.5 with the faulting instruction, not just the symbol.

### 30.5 ⛔⛔ **NEW TRAP — ITCM IS MAPPED AT `0x00000000`, SO addr2line NAMES A FUNCTION FOR A NULL pc**
`.itcmfunc` occupies **`0x00000000–0x00036aa8`**. A pc of `0x0` resolves to **`imxrt_get_pll1g`** and
`0x1a` to `imxrt_pll1g_ai_read` — **both are ALIASES, not the faulting code.** **8/48 pcs are NULL-ish
(`0x0` ×4, `0x10`, `0x1a`, `0x1b22`, `0x1cc4`)** = null function-pointer branches; `INVSTATE` on `pc=0`
is exactly "branch to an even target". ✅ The tool now flags anything `< 0x2000` instead of naming it.
📊 Also: **5/48 pcs are outside every executable section**, **7/48 are mid-instruction** (the "28%" figure
was over 60 logs including the 14 unresolvable — over the 48 resolvable it is 15%).

### 30.6 ⏭ **WITH THE PROBE (operator has one, offered 08-26) THE TEST IS NOW EXACT**
Halt at `imxrt_usagefault` (imxrt_irq.c:267) / `arm_memfault` and read what NO fault log records:
**`CPACR` `0xE000ED88`** (CP10/CP11 must be `0b11` each — if not, FPU genuinely disabled) ·
**`FPCCR` `0xE000EF34`** (ASPEN b31, LSPEN b30, LSPACT b0) · **`FPCAR`** · **MPU_CTRL/RNR/RBAR/RASR**.
🔑 **Best single shot: a DATA WATCHPOINT on `0xE000ED88` to catch whoever clears CPACR**
(⚠️ DWT comparators may refuse to match inside the PPB — try it, don't assume).
🔧 Needs on the companion: `gdb-multiarch` + `openocd` (both in the Ubuntu 24.04 arm64 repo, neither installed).

## 31. 2026-08-27 00:15-00:35 — ✅✅ **SWD IS UP. EVERY STATIC FPU/MPU EXPLANATION IS MEASURED AND CORRECT ⇒ DEAD.**
✅ **PROBE = NXP MCU-Link, CMSIS-DAP mode**, `1fc9:0143`, serial `VS4HD43ED5ICU`, plugged into the COMPANION
(+ its CDC-ACM appears as `/dev/ttyACM0`). ⚠️ **it enumerated twice, first try `error -71`** — if it drops
mid-session suspect the cable/hub, NOT the target.
✅ **HOST SETUP (done, reusable):** `gdb-multiarch` (apt) · **pyocd 0.45.1 in `~/pyocd-venv`** (venv, isolated —
system python + rclpy untouched) · pack `NXP.MIMXRT1176_DFP` · target id **`mimxrt1170_cm7`**.
⛔ **UDEV TRAP: name the rule `99-…`, NOT `50-…`** — `/usr/lib/udev/rules.d/50-udev-default.rules:72` runs
after a `50-` file and resets MODE to 0664, so pyocd sees "No available debug probes" as a normal user.
✅ `/etc/udev/rules.d/99-cmsis-dap.rules`. ⚠️ udev **preserves perms on an already-enumerated node** —
after installing the rule either replug or `chmod 666 /dev/bus/usb/<bus>/<dev>`.
🔑 **ALWAYS `--connect attach`** — anything else resets/halts a flying FC. Attach-mode reads are read-only
and the FC keeps running; **AHB reads of the SCS/PPB work fine while the core runs.**

### 31.1 ⛔⛔ **LIVE ON THE RUNNING FC (disarmed, `arming_state 1`): THE FPU CONFIG IS EXACTLY RIGHT. SUSPECT DEAD.**
`CPUID 0x411FC272` (Cortex-M7 r1p2) · **`CPACR 0x00F00000` ⇒ CP10=CP11=0b11, FPU FULLY ENABLED** ·
**`FPCCR 0x00000000` ⇒ ASPEN=0, LSPEN=0** · `CCR 0x00070200` (D-cache, I-cache, BP all ON; UNALIGN_TRP=0) ·
`MPU_CTRL 0x00000007` (ENABLE+HFNMIENA+PRIVDEFENA) · `MPU_TYPE` 16 regions · `CFSR 0` · `DEMCR 0x01000000`.
🔴🔴 **I BRIEFLY CALLED `FPCCR=0` THE BUG. IT IS NOT — I RETRACT IT.** `arm_fpuconfig.c` (NuttX,
armv7-m) **deliberately** clears ASPEN+LSPEN **and force-sets `CONTROL.FPCA=1` permanently** so every
exception takes the extended frame. ✅ **CONFIRMED BY THE LOGS: all 62 read `control:0x00000004` (FPCA=1)
and `exe return:0xffffffe9` (extended frame, thread, MSP) — UNANIMOUS.** Everything matches the design.
⇒ **A STATIC FPU MISCONFIGURATION CANNOT EXPLAIN THE NOCP CLUSTER (§30.3). Do not re-propose CPACR/FPCCR/
LSPEN as the root cause — it is MEASURED CORRECT on the live target.**

### 31.2 ✅ **THE PROGRAMMED IMAGE IS INTACT — flash-vs-ELF diff over SWD**
`.vectors` @ `0x30022000` (⚠️ **NOT `0x30020000` — that reads `0xffffffff`, erased padding; the old
"app at 0x30020000" is off by 0x2000**) and 4 KB of `.text` around the NOCP hotspot `0x300fdc00`:
**0 bytes differ from the ELF, and 0 bytes differ between two consecutive reads.**
⇒ **No static image corruption, no read-to-read instability.** ⚠️ **This does NOT clear a transient
fetch error at full FlexSPI speed** — debugger reads are slow AHB reads, not the instruction-fetch path
under load. ✅ `objcopy --dump-section` works on this ELF for byte-level expectations.

### 31.3 ⏭⏭ **NEXT: `~/ros2_ws/tools/fc_fault_catch.py` — DEMCR VECTOR CATCH, HALT *AT* THE FAULT**
Arms `VC_NOCPERR|VC_STATERR|VC_CHKERR|VC_MMERR|VC_BUSERR|VC_INTERR|VC_HARDERR`, polls for halt, then dumps
core regs + CFSR/MMFAR + **CPACR/FPCCR/MPU map** + **the 16 bytes AT pc diffed against the ELF** + stack.
🔑 **THE DISCRIMINATOR: if NOCP is set while CPACR still reads `0x00F00000`, the FPU was NOT disabled and
the NOCP bit itself is unexplainable by configuration ⇒ the CPU mis-decoded a correctly-stored instruction.**
⚠️⚠️ **COST — SAY IT BEFORE RUNNING: on a fault the core FREEZES instead of logging+rebooting. PX4 stops,
DDS goes silent, NO `fault_*.log` is written for a caught fault, and the FC stays dead until resumed or
power-cycled. The FC is SHARED WITH THE DRONE — drone powered off.** `--resume-after` catches repeatedly.

## 32. 2026-08-27 01:01 — 🔴🔴🔴 **A FAULT WAS CAUGHT LIVE. VERDICT: THE CPU FAULTED ON A LEGAL, CORRECTLY-STORED FPU INSTRUCTION WITH THE FPU ENABLED. CONFIGURATION AND IMAGE CORRUPTION ARE BOTH DEAD.**
✅ **`fc_fault_catch.py` WORKS.** Caught dump: `~/fc_faults/caught/caught_20260827_010134.txt`.
`DFSR 0x8` = VCATCH confirms the vector catch (not a coincidence).

### 32.1 ⛔⛔ **TOOL TRAP I HIT AND FIXED — VECTOR CATCH HALTS IN THE *HANDLER*, NOT AT THE FAULT**
The halt lands on the **first instruction of `exception_common`** (`arm_exception.S:145`, ITCM `0x83c`)
**AFTER** the exception is taken: `IPSR=6` (UsageFault), `lr=0xffffffe9` (EXC_RETURN), `psp=0`.
⛔ **The halted `pc` is the HANDLER. Checking fetch integrity there tests the WRONG ADDRESS — my first
dump did exactly that and "MATCH" meant nothing.** ✅ **FIX (now in the tool): unwind the stacked frame —
`lr` bit2 picks MSP/PSP, bit4 picks extended/basic; frame is `r0,r1,r2,r3,r12,lr,pc,xPSR` then S0-S15+FPSCR.**
🔑 **`0x0000083c` resolving to `exception_common` is REAL ITCM code, not the §30.5 null alias** — the
`<0x2000` alias rule does NOT apply above that, and NuttX's exception vectors genuinely live in ITCM.

### 32.2 🔬🔬 **THE MEASUREMENT**
| | |
|---|---|
| CFSR | `0x00010000` = **UF:UNDEFINSTR** |
| stacked (true) faulting pc | **`0x300feac6`** |
| instruction there | **`vfma.f32 s0, s3, s5`** |
| function | **`sym::PredictCovariance<float>`**, `predict_covariance.h:91` |
| **CPACR at fault time** | **`0x00f00000` — CP10=CP11=3, FPU ENABLED** |
| FPCCR / CCR / MPU_CTRL | `0x0` / `0x00070200` / `0x7` — all nominal |
| bytes at `0x300feac0`, live ×2 | `1e 1a d4 ed e1 1a a1 ee a2 0a dd ed 14 1a 8d ed` |
| same bytes from the ELF | **IDENTICAL** |
🔑🔑 **AN ENABLED FPU RAISED `UNDEFINSTR` ON A CORRECTLY-STORED, LEGAL `vfma.f32`. That is architecturally
impossible if the core fetched and decoded what is actually in memory.**
🔑 **SAME FUNCTION AS 6 OF THE 8 NOCP FAULTS (§30.3)** ⇒ **NOCP and UNDEFINSTR here are ONE phenomenon
wearing two CFSR bits, not two bugs.**

### 32.3 ✅ **WHAT THIS ELIMINATES — and what it does NOT**
⛔ **DEAD: static FPU/MPU misconfiguration** (§31.1, measured correct AT THE FAULT, not just at idle).
⛔ **DEAD: corruption of the stored image** (bytes match the ELF at the exact faulting address).
⇒ ✅ **SURVIVING: the core's INSTRUCTION-FETCH / EXECUTION path — XIP-FlexSPI timing under load,
cache maintenance, or clock/voltage margin on the fetch path.** This NARROWS §29's "board-support
config" from MPU/lazy-FP to **instruction fetch + cache + FlexSPI**.
⚠️⚠️ **HONEST LIMIT: n=1, and the byte read is a SLOW AHB read AFTER the fact. It proves the STORED image
is right; it CANNOT observe what the fetch unit actually received at that instant.** ⏭ **Catch more.**

### 32.4 ⛔⛔ **THE COST IS REAL — THE OPERATOR FELT IT. SAY THIS BEFORE EVER RE-ARMING.**
The dump does many slow SWD reads **with the core frozen** ⇒ PX4 stops for seconds ⇒ **the GCS MAVLink
link times out and DROPS, and the operator sees a FREEZE and NO hardfault** (he reported exactly this).
🔑 **A caught fault writes NO `fault_*.log` — the halt replaces it.**
⛔⛔ **AND: WITH THE PROBE ATTACHED, PX4's OWN REBOOT DOES NOT COMPLETE.** After the catch the core sat
**spinning in `up_systemreset()` (`arm_systemreset.c:65`), pc frozen at `0x301eabbe` across 3 samples** —
SYSRESETREQ issued, reset inhibited by the debug connection. ✅ **CURE: `pyocd ... -O reset_type=hw -c reset`
(nRESET). A plain `-c reset` did NOT fix it.** ⇒ **Expect to have to hw-reset the FC after every catch.**
🔑 **ONE PROBE = ONE SESSION: while `fc_fault_catch.py` holds the MCU-Link, every other `pyocd` call
returns EMPTY OUTPUT (not an error). Stop the catcher before any ad-hoc read.**
⚠️ **`ros2 topic list --no-daemon` reported 0 `/fmu/out` topics while `topic hz` on one read 99.9 Hz —
the INVERSE of the known daemon trap. ⛔ NEITHER VARIANT IS TRUSTWORTHY ALONE; confirm with `hz`/`echo`.**

## 33. 2026-08-27 08:2x — ⛔⛔ **"CATCH ONLY WHAT YOU CARE ABOUT" IS WRONG. WITH A PROBE ATTACHED YOU MUST CATCH *EVERY* FAULT CLASS.**
🔴 **PROVED BY TEST:** armed `--minimal` with only `VC_CHKERR|VC_NOCPERR` so MemManage/BusFault would
"fault, log and reboot normally". **Within ~1 min the FC was wedged at `pc=0x301eabbe` = `up_systemreset()`
again** — because **an uncaught fault CANNOT reboot either: SYSRESETREQ is inhibited by the debug
connection.** ⇒ **A fault class you don't catch doesn't reboot, it WEDGES.** ✅ **Always `--vc-all`.**
✅ **CORRECT INVOCATION (in use, PID re-check each time):**
`~/pyocd-venv/bin/python -u tools/fc_fault_catch.py --minimal --vc-all --reset-after --freq 8000000`
 · `--minimal` = capture only CFSR/CPACR/lr/xpsr + the 8-word stacked frame while frozen (7 transactions),
   then resume/reset FIRST and do addr2line/objdump/file-write AFTER. Freeze time is printed per catch.
 · `--reset-after` = **`Target.ResetType.HARDWARE`** (⛔ **NOT `.HW` — that AttributeError killed a catch
   and lost its data; the reset call is now wrapped so a reset failure can never lose a capture again**).
 · **A RESET CLEARS DEMCR ⇒ THE TOOL RE-ARMS AFTER EVERY RESET.** Forget this and it silently stops catching.
✅ **8 MHz SWD is stable on this cable** (was 2 MHz; fewer µs per transaction = shorter freeze).
🔑 **FAULT RATE THIS MORNING IS HIGH — one fired within ~18 s of arming.** ⛔ **The §29.3 "SD reformat may
have fixed it" question is ANSWERED: it did not. Faults are back at full rate.** ⇒ **§29.3(a) HOLDS.**
🔑 **RECOVERY FROM A WEDGE (memorise):** `pyocd commander -t mimxrt1170_cm7 --connect attach -f 8000000
-O reset_type=hw -c reset` — **a plain `-c reset` does NOT clear it.**

## 34. 2026-08-27 — 🔬 **CURRENT HYPOTHESIS (n=1 live catch + 48 resolved logs). NOT PROVEN — THIS IS THE FRAME, NOT A VERDICT.**
**The one fact to explain:** an ENABLED FPU raised `UNDEFINSTR` on a legal, correctly-stored `vfma.f32`
(§32.2). ⇒ **what the core RECEIVED/EXECUTED differed from what is STORED — a transient, invisible afterwards.**
🔑 **BEST HYPOTHESIS: a MARGINAL OPERATING POINT ON THE INSTRUCTION PATH, SET IN SOFTWARE** — which is
exactly why 4 FC swaps, 2 sites, EMI and the harness all failed to move it. Two candidates:
 **(a) FlexSPI XIP read marginality** (app runs XIP from external QSPI; RT1176 read-strobe/DLL + FlexSPI
 clock are timing-sensitive; marginal ⇒ rare random read errors).
 **(b) core clock vs `VDD_SOC` / DCDC setpoint mismatch** (NuttX drives the core faster than the voltage
 setpoint supports ⇒ rare instruction-level failures, load/temperature dependent).
🔑🔑 **WHY THIS BEATS "FPU WAS DISABLED" FOR THE NOCP CLUSTER:** CPACR enables **ONLY CP10/CP11**. VFP
instructions already carry a coprocessor field, so **corrupting a bit or two of that field turns a VFP
instruction into an access to a DISABLED coprocessor = NOCP.** ⇒ predicts NOCP appears **almost only on
FP instructions — measured 8/8** ✅, whereas "FPU disabled" requires a wrong CPACR and **CPACR MEASURED
CORRECT AT THE FAULT** ❌. ⇒ **`sym::PredictCovariance<float>` is not special, it is EXPOSURE** — the
largest straight-line FP block, run at EKF rate, so it takes the biggest share of instruction fetches.
✅ Same story covers mid-instruction pcs, pcs outside any section, `pc=0`, and INVSTATE-to-even-targets
(corrupt fetch desynchronises decode / supplies a bad branch target).
⚠️ **NOT the retracted 'bit-shift/XIP' lead (§26)** — different argument, resting on the live catch and the
CPACR measurement, neither of which existed then. Say this explicitly before anyone re-kills it by name.
🔑 **PROBABLY SEPARATE: the DACCVIOL/null population** (MMFAR `0x00,04,08,0a,0c,14,20`, `ucdr_serialize_
esc_status`) looks like a REAL null-pointer bug in the uXRCE serializers. **Don't conflate; may be
independently fixable.**
### 34.1 ⏭⏭ **THE DISCRIMINATOR + THE QUEUED MEASUREMENT (operator 08-27: COLLECT SAMPLES FIRST, THEN DO IT)**
🔑 **DOES ITCM-RESIDENT CODE EVER FAULT?** fetch-path ⇒ XIP `.text` only, ~never ITCM. clock/voltage ⇒ ITCM
faults too. **Every real faulting pc so far is `0x30xxxxxx` (XIP)** — suggestive, but ITCM holds little
code so exposure is low. **More catches settle it.**
⏭ **1. READ ARM PLL FREQ + DCDC/`VDD_SOC` SETPOINT OVER SWD** and check against the RT1176 datasheet
requirement for that frequency. ~5 min, non-invasive. ⛔ **needs the catcher STOPPED — one probe, one session.**
⏭ **2. Diff the board's FlexSPI init vs NXP reference** (clock rate, read-sample-clock source).
⏭ **3. If either is marginal: LOWER THE CLOCK AND SEE IF THE FAULT RATE COLLAPSES.**

## 35. 2026-08-27 09:0x — 🔴 **I WAS WRONG ABOUT THE DLL. MEASURED: THE FlexSPI READ PATH IS CONFIGURED CORRECTLY AND THE DLL IS LOCKED.**
⛔ **§34's SPECIFIC prediction ("marginal / uncalibrated FlexSPI DLL") IS FALSIFIED. Do not re-propose it.**
✅ **MEASURED LIVE (`FLEXSPI1` regs @ `0x400CC000`, base taken from `imxrt117x_memorymap.h:188`, NOT guessed):**
| reg | value | decode |
|---|---|---|
| `MCR0` `+0x00` | `0xffffa030` | **RXCLKSRC=3 = external DQS pad** ✓, MDIS=0 (enabled) |
| `AHBCR` `+0x0c` | `0x00000078` | cacheable+bufferable+**prefetch**+read-addr-opt all ON |
| `FLSHCR0[0]` `+0x60` | `0x00010000` | 64 MB ✓ |
| `FLSHCR1[0]` `+0x70` | `0x00000021` | TCSS=1 TCSH=1 ✓ matches the config block |
| `DLLCR[0]` `+0xc0` | `0x00400079` | **DLLEN=1, OVRDEN=0, SLVDLYTARGET=0xF** = NXP's recommended ≥100 MHz DQS setting |
| `STS0` `+0xe0` | `0x00000003` | seq+arb idle |
| `STS1` `+0xe4` | `0x00000000` | **no latched controller errors** |
| `STS2` `+0xe8` | `0x00000b33` | **ASLVLOCK=1, AREFLOCK=1 ⇒ DLL LOCKED**; ASLVSEL=12, AREFSEL=11 |
⚠️ **"Locked and per-recommendation" ≠ "has margin at this temperature on this board." It only kills the
CONFIG-DEFECT version of the hypothesis, not transient corruption itself.** ⛔ **But I have NO specific
configuration defect to point at any more — say so, don't dress it up.**
### 35.1 ✅ **BOOT-FLASH XIP MODE (from `boards/px4/fmu-v6xrt/src/imxrt_flexspi_nor_flash.c`)**
**Macronix octal NOR, `serialClkFreq = 200 MHz`, 8-pad, DDR (=400 MT/s), `ExternalInputFromDqsPad`,
`dataValidTime = 0`, 20 dummy cycles encoded `0x28`** ("2N in DDR mode" — hand-written comment, unverified).
**This is the most timing-critical XIP mode the part offers.** A 2nd config block (30 MHz, 1-pad,
LoopbackInternally) is the other device.
### 35.2 ✅ **VDD_SOC IS CORRECT — core-voltage hypothesis weakened**
`imxrt_clockconfig()` **unconditionally** calls `imxrt_pmu_vdd1p0_buckmode_targetvoltage(dcdc_1p0bucktarget1p15v)`
= **1.15 V overdrive**, correct for `BOARD_CPU_FREQUENCY 996000000` (⚠️ that define carries a **`//FIXME`**),
plus FBB per OCOTP fuse 7 bit 4. ⚠️ **Cosmetic bug: the comment says "and wait for it to stablise" but there
is NO delay after the call** — a startup race, cannot explain faults hours in.
⚠️ `imxrt_pmu_enable_pll_ldo()` is the **PLL** LDO, **NOT** VDD_SOC — don't mistake one for the other.
### 35.3 🟡 **NEW, UNTESTED: `XECC` FOR THE FlexSPI1 XIP REGION IS NEVER ENABLED**
`IMXRT_XECC_FLEXSPI1_BASE 0x4001c000` exists, but **there is NO XECC driver in NuttX or PX4 — only address
and CCGR defines.** ⇒ **nothing detects or corrects a bit error on the XIP read path; it propagates silently
into the instruction stream.** 🔑 **Consistent with "silent, random, no trace" — but this is ABSENCE OF A
DETECTOR, NOT EVIDENCE THAT ERRORS OCCUR. Do not quote it as proof.**
⛔ **I did NOT read the XECC registers live: the module's CCGR is almost certainly gated and a debug-AHB
access to a gated peripheral risks wedging the FC in service. Not worth it — source already says no driver.**
### 35.4 ⏭ **BOTH REMAINING TESTS NEED A FIRMWARE BUILD + FLASH (FC IS SHARED WITH THE DRONE — operator's call)**
1. **Drop `serialClkFreq` 200 MHz → 100 MHz (or SDR) and see if the fault rate collapses.** Most direct.
2. **Enable XECC on FlexSPI1** to turn silent read corruption into a *reported* ECC event.

## 36. 2026-08-27 — 📋 **FULL REVISIT + THE PLAN (operator asked). SUPERSEDES ALL EARLIER 'NEXT ACTIONS'.**
### 36.1 🔴🔴 **NEW TOP SUSPECT FOUND IN THE REVISIT: SPEED GRADE vs `BOARD_CPU_FREQUENCY 996000000 //FIXME`**
RT1176 ships as **1 GHz (DVMAA/DVMAB)** and **800 MHz (xVM8x, = the industrial-qualified grade)**. If these
boards carry an 800 MHz die clocked at 996 MHz ⇒ **explains the ENTIRE case**: rare random execution faults,
all 4 boards, both sites, temp-sensitive, immune to every elimination. The `//FIXME` (board.h:51) is ominous.
⏭ **FREE CHECK: operator reads the CHIP MARKING (`MIMXRT1176____`) + I read the ARM PLL / M7 clock root over
SWD at the next catcher pause to confirm the REAL programmed frequency.** 🔑 discriminator vs fetch-path:
**overclock ⇒ ITCM code should eventually fault too; flash-fetch ⇒ never.** (So far 0 ITCM faults anywhere.)
### 36.2 ⚠️ **HONEST HOLE IN MY OWN EVIDENCE: the "bytes MATCH" check reads AHB and BYPASSES THE I-CACHE.**
A corrupted I-cache line faults while my check still shows MATCH. **Nothing measured so far excludes the
I-cache.** (The 2 same-pc catches were on DIFFERENT boots — they don't prove a sticky line either way.)
### 36.3 ✅ Errata sheet exists and documents FlexSPI DLL/prefetch read-corruption class issues:
**IMXRT1170ACE Rev 1.6** https://www.nxp.com/docs/en/errata/IMXRT1170ACE.pdf (e.g. ERR011377 DLL-lock timing;
prefetch-abort hardfaults on some devices). Our AHBCR (0x78) HAS prefetch enabled. ⏭ desk-check it fully.
✅ **FRAM is on FlexSPI2 (`imxrt_flexspi_fram.c:179`) ⇒ param traffic CANNOT collide with FlexSPI1 XIP — that
conflict class is DEAD.**
### 36.4 ✅ CATCHES #2/#3 ARE NEAR-IDENTICAL: pc `0x30022508` `cbnz r3` in `__aeabi_uldivmod`, caller
`nxsig_timedwait` (`sig_timedwait.c:314`, ITCM `0x22ea`), r2=1e6 r12=1e9 (µs→tick divisions), r0 = the two
timeout values. **HFSR FORCED=1 + USGFAULTENA=1 ⇒ faulted inside a masked/critical section** (why these
escalate to HardFault while catch #1 was a plain UsageFault). **The 2 hottest XIP sites = the 2 hit sites ⇒
distribution tracks EXPOSURE.** ⚠️ n=3 — do NOT declare it address-specific.
### 36.5 📋 **THE ORDERED PLAN**
**Free first:** (1) chip marking + SWD PLL read → settles §36.1 · (2) errata desk-check · (3) catcher to ~10
catches for XIP/ITCM stats. **Then one flash per variable, ranked:** (4) M7 → ~700 MHz (one define, safe for
either grade) · (5) FlexSPI 200→100 MHz (one field) · (6) AHB prefetch OFF · (7) **XECC LAST — needs a NEW
DRIVER (none exists in NuttX/PX4) + flash-layout ECC data = the MOST invasive option; operator asked, was told.**
**Pass mark stays 8 h clean** (p90 gap 73 min). **Then report upstream** — px4_fmu-v6xrt is NXP's own design;
3 vector-catch dumps of an enabled FPU refusing correctly-stored instructions is an actionable NXP/PX4 report.
🔧 **SEPARATE, DO REGARDLESS: fix the `ucdr_serialize_*` null-deref (§30.4)** — real bug, ESC-status path.

### 36.6 2026-08-27 ✅✅ **MEASURED LIVE: THE CORE REALLY RUNS AT 996 MHz.** `ARM_PLL_CTRL@0x40C84200 =
0x200060a6` (loop_div 166, post_div 2 ⇒ 24/4×166 = 996 MHz), `CLOCK_ROOT0@0x40CC0000 = 0x00000400` (mux 4 =
ARM_PLL, div 1). ⇒ **§36.1 now hinges ONLY on the CHIP MARKING: 1 GHz grade (DVMAA/AB) = legal; 800 MHz grade
(xVM8x) = OVERCLOCKED 25% = probable root cause. OPERATOR: read the marking.**
### 36.7 ⛔ **PROBE USB IS FLAKY — 6 re-enumerations in ~35 min (dmesg), killed the catcher session mid-run
("No ACK"), and the interrupted reset STRANDED THE FC IN THE NXP BOOT ROM (pc 0x00223104, region 0x00200000+)
— DDS dead, core "Running" but never booting.** ✅ Cure: same `-O reset_type=hw -c reset`. 🔑 **ADD TO THE
WEDGE LIST: pc in 0x0020xxxx = BOOT ROM, not our code — don't addr2line it.** ✅ DEMCR self-cleared (the FC
reset since; DHCSR S_RESET_ST set) — no orphaned vector catch. **CATCHER OFF until the operator RESEATS the
probe cable/port; 3 catches in hand are enough for the current conclusions.**
### 36.8 ✅ **OPERATOR QUESTIONS ANSWERED 08-27:** (1) "why only after the 15th" → earliest DATEABLE log is
08-16 05:01; the 17 bad-clock logs CANNOT be dated so onset is partly an observability artifact; the decisive
fact is HIS flash history around 08-15 (§17.7 says firmware flip-flopped 3×) — asked. August heat fits the
marginal-operating-point picture either way. (2) "did esc_status cause it all / permanently change params" →
NO: esc_status serializer is 1 victim of 26+; faults continued with CAN REMOVED (§17.14 — no ESC data at all);
params were diffed (3 benign), RESTORED 08-25, faults continued ⇒ params neither cause nor carrier; a
serializer null-deref crashes the DDS task, it does not write params.

### 36.9 ⛔ 2026-08-27 — **SPEED-GRADE LEAD (§36.1) DEAD: OPERATOR READ THE MARKING — `MIMXRT1176DVMAA` = THE
1 GHz GRADE. 996 MHz IS LEGAL. Do not re-propose overclock.** Survivors, re-ranked: (1) FlexSPI XIP read-path
margin/erratum @ 200 MHz octal DDR (2) I-cache corruption (byte-check CANNOT exclude it, §36.2) (3) core-rail
(VDD_SOC) transients — we measured the SETPOINT (1.15 V), never the actual rail under load; internal DCDC,
same on all 4 boards, needs a scope. ⏭ NOW: errata desk-check → then the one-line build tests
(FlexSPI 200→100 · AHB prefetch off · core clock down as a rail-margin probe).

### 36.10 2026-08-27 ✅ **ERRATA DESK-CHECK DONE (⚠️ Rev 1.3 mirror — NXP current is Rev 1.6, GET IT, 1.3→1.6 delta is a blind spot). NO SMOKING GUN.**
Text: scratchpad `fault/errata.txt` (pdftotext of zlgmcu mirror; poppler-utils now installed).
⛔ **ERR011573** (speculative access, ARM 1013783-B): excluded — our `PRIVDEFENA=1` + privileged execution,
and its effect is a stray bus access, "execution is not directly affected". ⛔ **ERR006940** VDIV/VSQRT: **M4F
ONLY**, we run the M7. ⛔ **ERR011377** DLL-lock timing: boot-window only, our faults fire hours later.
🟡 **ERR050396** (sparse DMA write to CM7 TCM corrupts data; USB IS an affected master, NuttX stacks live in
DTCM): **possible contributor to the DACCVIOL/null cluster, CANNOT cause the XIP UNDEFINSTR phenomenon**
(data-path only, and rover faults with FC USB unused).
⇒ **FINAL SURVIVOR RANKING: (1) FlexSPI XIP read margin @200 MHz octal DDR (2) I-cache (byte-check blind to
it) (3) VDD_SOC rail under load (setpoint verified, rail never scoped).** **FREE CHECKS ARE EXHAUSTED — next
step is BUILD TESTS, one line each, 8 h pass mark: (a) `serialClkFreq` 200→100 (b) core 996→~700 (c) I-cache
off.** Operator gates flashing (FC shared with drone).

## 37. ⏭⏭ **RESUME HERE — EVENING 2026-08-27. STATE AS LEFT AT MIDDAY:**
✅ **FC HEALTHY**: booted, disarmed, `sensor_combined` 100 Hz, DDS up. **Vector catch CLEAR (DEMCR
0x01000000, verified), catcher OFF, monitor OFF.** Nothing armed ⇒ faults log + auto-reboot NORMALLY again.
⚠️ **fc_soak also OFF** (died 08-26 22:39, never restarted — card-side fault logs since then are UNCOUNTED;
list the card root TWICE when next checking, exFAT/unmountable = fake silence).
📥 **WAITING ON OPERATOR:** (1) go/no-go + timing for BUILD TEST (a) `serialClkFreq` 200→100 MHz — I can
prepare the branch first (2) errata **Rev 1.6** PDF from his NXP account (3) **probe cable RESEAT** before
any catcher re-arm (6 USB re-enums/35 min killed the last session and stranded the FC in BOOT ROM).
🗂 **Today's artifacts:** catches ×3 `~/fc_faults/caught/caught_*.txt` · log-resolution report
`~/ros2_ws/docs/fc_fault_resolution_20260826.md` · errata text `scratchpad fault/errata.txt` (Rev 1.3) ·
tools `fc_fault_resolve.py` + `fc_fault_catch.py` (both in `~/ros2_ws/tools/`, uncommitted on
`fix/collision-perception-health-gate`).
🔑 **READ §36 (plan) → §36.9/36.10 (final ranking) → §32 (the caught-fault verdict) before doing ANYTHING.**

## 38. 2026-08-28/29 — 🔴 **BUILD TEST (a) IS DEAD ON ARRIVAL · A PEER SESSION'S LINKER LEAD REFUTED · POST FILED TO THE PX4 FORUM**

### 38.1 ⛔⛔ **`serialClkFreq` 200→100 MHz DOES NOT BOOT — §36.10's TOP QUEUED ACTION IS INVALID AS WRITTEN**
**OPERATOR-CONFIRMED 08-28** (also reported independently by a peer Claude session on the PC): the 100 MHz
change was tried and **the board does not boot at all.** ⛔ **Do NOT re-queue "(a) serialClkFreq 200→100"
as a one-line test — §36.10/§37 and the MEMORY.md index were both wrong to.**
🔑 **BUT THIS DOES NOT REFUTE THE READ-MARGIN HYPOTHESIS.** The test was UNDER-SPECIFIED: per §35.1 the
config block carries **20 dummy cycles (encoded `0x28`) + TCSS=1/TCSH=1, tuned for 200 MHz octal DDR.**
Halving the clock without re-deriving the dummy-cycle count breaks boot regardless of cause.
⏭ **If retried: re-derive dummy cycles for the new clock FIRST.** Survivor #1 is still alive and unTESTED.

### 38.2 ⛔ **REFUTED BY MEASUREMENT: "v1.17.0 folded `.ram_vectors` into `.itcmfunc` ⇒ corrupted vector fetch"**
A peer session (PC, `/home/pxlabs/PX4-Autopilot`) proposed this and named the discriminator itself:
**`HFSR.VECTTBL`** (bit 1), set when a bus fault occurs fetching from the vector table.
✅ **THE FACT IS CORRECT** — verified in OUR tree: we are on `pxlabs-v1.17.0-r2-Beta` (a52c38b07d) and
`boards/px4/fmu-v6xrt/nuttx-config/scripts/script.ld:86` really does have `*(.ram_vectors)` inside the
`.itcmfunc` block (lines 80-93). **The CONCLUSION is dead.**
🔬 **MEASURED, n=62 logs + 3 live catches: `VECTTBL` IS NEVER SET.** 61× `hfsr:0x00000000`, 1× `0x40000000`
(**FORCED only**, bit 30). The catcher already prints it: `HFSR 0x40000000 FORCED=1 VECTTBL=0`.
🔑 **2nd, independent kill:** the `.itcmfunc` copy happens **ONCE AT BOOT** ⇒ corruption would be static and
deterministic for that boot. Our faults are intermittent (median gap 5.4 min) with the system running for
hours. **A corrupted vector table cannot behave like that.**
⚠️⚠️ **TRAP THE PEER ALMOST FELL INTO — WILL RECUR:** they proposed "check whether the faulting PC lands in
ITCM `0x00000000`-`0x00040000`". **IT DOES, AND IT MEANS NOTHING** — two known artifacts stack: vector catch
halts in the HANDLER not at the fault (§32.1: `pc 0x0000083c` = `exception_common`, `lr 0xffffffe9`), and
**ITCM is mapped at `0x00000000` so addr2line names a plausible function for a null/handler pc (§30.5).**
**A naive check here is a FALSE-CONFIRMATION GENERATOR.**

### 38.3 ✅ **NEW MEASUREMENT — THE FAULTING PCs DO NOT CLUSTER ⇒ NOT A BAD FLASH PAGE/SECTOR**
Extracted every XIP faulting pc across all 62 logs: **42 UNIQUE addresses, `0x30069848` → `0x30269230`
≈ 2.1 MB of `.text`** — essentially the whole application image, only a handful of repeats.
🔑 **A worn erase block / bad page / corrupted sector WOULD CLUSTER. This does not.** ⇒ points at a
**GLOBAL fetch-path** defect (read margin · prefetch · I-cache), not damaged storage at any address.
✅ Independently reinforces §34's "the victim is EXPOSURE, not identity" — scatter tracks code density.
📊 Victim tasks over the corpus: `uxrce_dds_client` 22 · `wq:INS0` 13 · `wq:uavcan` 10 · `wq:ttyS3` 4 ·
`mavlink_if1` 3 · `hpwork` 3 · `wq:nav_and_controllers` 2 · `wq:hp_default` 2. **45/62 pcs are `0x30xxxxxx`.**

### 38.4 ⚠️ **"NO FAULT ON v1.16.2" IS NOT A RESULT — THE BUILD RAN UNDER AN HOUR (operator, 08-29)**
⛔ **DO NOT let this become a remembered fact.** Our own stat: **P(quiet ≥1 h) = 15.8%** (§29.2) — a sub-hour
clean run is fully consistent with the fault being present and not yet fired. **This is precedent #4 of the
same shape** (charger §20, USB §25.1, EMI §26.1). ⏭ **To settle it: reflash v1.16.2 and soak 8 CONTINUOUS h.**
✅ **DOES hold: reproduces on STOCK UPSTREAM PX4 v1.17.0** ⇒ **our vendor changes are eliminated.**

### 38.5 🌡 **THERMAL / "NO FAN IN THE CASING" — DEAD AS A CAUSE (operator asked 08-28)**
⛔ **§29.1 ALREADY RAN THE EXPERIMENT:** FC out of the vehicle, no casing, open air, USB-only, different
building — **the largest thermal delta available, far bigger than fitting a fan — and it faulted in 10-15 min,
statistically identical to on-vehicle.** A cause must move the rate when removed; this moved it by NOTHING.
⛔ **The DEBUGGER is likewise not a cause: SWD was first attached 08-27 00:15; all 62 logs predate it.**
🟡 **What survives:** temperature is still a MODULATOR of survivors #1/#3 (§34b "load/temperature dependent",
§35 "locked ≠ has margin AT THIS TEMPERATURE"). The bench test did NOT control ambient (same city, same August).
🔬 **DIE TEMP HAS NEVER BEEN MEASURED, AND IS HARDER THAN IT LOOKS — I MIS-SOLD IT AS "READ-ONLY, 2 MIN":**
 - ✅ **Read-only recon DONE (no writes, no halt, PX4 undisturbed):** ANADIG base `0x40C84000`;
   `VDDLPSR_AI_CTRL 0x40C848E0 = 0x00010000` (RWB=1, addr 0) · `AI_WDATA 0x40C848F0 = 0` ·
   `AI_RDATA_TMPSNS 0x40C84910 = 0x0000501C` (boot/reset state, **NOT a temperature — do not decode it**).
 - ✅ **CROSS-CHECK PASSED, reusable:** `ARM_PLL_CTRL 0x40C84200 = 0x200060A6` → DIV_SELECT 166 →
   24 MHz×166/4 = **996 MHz**, matching §36.6. **Use this to prove any future attach + base address.**
 - 🔴 **THERE IS NO TMPSNS DRIVER** in NuttX rt117x or the fmu-v6xrt board support — **the sensor is powered
   down.** Getting °C needs **WRITES**: `AI_CTRL`+`AI_WDATA`+toggle `TMPSNS_AI_TOGGLE`, clear `PWD`/`PWD_FULL`
   in `CTRL1`, set `START`, poll `STATUS0.FINISH`. ⚠️ **TMPSNS carries ALARM/threshold regs that NXP's driver
   configures BEFORE power-up — powering it with reset-state thresholds could trip an alarm on a shared FC.**
 - ⛔ **STILL MISSING:** `ANADIG_TEMPSENSOR` offsets + `TEMPSNS_OTP_TRIM_VALUE` (the `Ts25c` term). NuttX's
   header does not define them. **Get the RT1170 RM or NXP's `MIMXRT1176_cm7.h` — do NOT guess these.**
 - Conversion (NXP `fsl_tempsensor.c`): `T = (-Ts21 - sqrt(Ts21² - 4·Ts22·(Ts20 + Ts25c - raw))) / (2·Ts22)`,
   `Ts20=133.6 Ts21=-5.39 Ts22=0.002`. **OCOTP fuse shadow is directly readable at `0x40CAC800`**
   ⚠️ **stride is 0x10, NOT 0x4** — a 4-byte walk returns each word 4× and looks like corruption.
 - 🔑 **Build test (b) core 996→~700 MHz is a SUPERSET of a cooling experiment** (cuts timing margin AND
   self-heating) ⇒ **prefer it over any fan/thermal work.**

### 38.6 ✅ **POSTED TO THE PX4 FORUM (operator posted it himself, 08-29)**
📄 `scratchpad/px4_forum_pack/px4_forum_post_hardfault.md` + **6 UNDEFINSTR logs** (all `a52c38b07d`, all
ELF-resolvable) + the live catch `caught_20260827_084935.txt`.
**Post asks:** UNDEFINSTR-on-XIP seen before? · v1.16.2→v1.17.0 fetch-path delta? · is 200 MHz octal DDR
marginal? · correct way to downclock XIP (dummy cycles)? · is `XECC` on the XIP region viable? · AHB prefetch off?
⏭ **WATCH FOR REPLIES — the XECC and dummy-cycle answers are the two that unblock real tests.**

## 39. 2026-08-29 — 🎯🎯 **NXP ANSWERED: PX4 PR #28141 — "calibrate FlexSPI DLL read strobe at boot". THIS IS PROBABLY OUR BUG.**
**Author Peter van der Perk (NXP). MERGED 2026-08-04 → commit `9f4bc80006caf7d5d8bcf809b4ccd046fb5eded6`
(NOT a merge commit, parent `caa1dc03`), ONE FILE: `boards/px4/fmu-v6xrt/src/init.c`, +217/−13. Fixes issue
#27735.** NXP asked the operator directly: **test v1.18-beta2 or cherry-pick it.**
🔑🔑 **MECHANISM: "the boot ROM does not always place the DLL delay used to sample the flash DQS strobe near
the CENTRE of the valid read window"** ⇒ marginal XIP instruction fetch. Fix = RAM-resident boot routine that
sweeps the DLL delay, reads a known pattern via a direct command at each setting, **picks the midpoint of the
widest passing range**, follows NXP's DLL update sequence (stop mode, DSB/ISB, **ERR011377 post-lock settle**),
falls back to the ROM setting on failure, stores it in `g_dll_cal` and **LOGS it from `board_app_initialize()`**.
🔑🔑 **THIS LANDS EXACTLY IN THE HOLE §35 LEFT OPEN.** §35 measured DLL **LOCKED**, `DLLCR 0x00400079`
per-recommendation, `STS1=0` — and I concluded the CONFIG was correct **but explicitly wrote "locked and
per-recommendation ≠ has margin at this temperature on this board."** ⇒ **LOCKED ≠ CENTRED. §35 never refuted
this; it refuted the config-defect version only. The caveat was the load-bearing sentence.**
📊 **EVIDENCE MATCH (issue #27735 vs our corpus):** `cfsr 0x00010000` **UNDEFINSTR quoted verbatim** ✓ ·
their `pc 0x2fb20542` "not a valid code address" ↔ **our garbage pcs `0x2fd930d2`/`0x250330fc` — same shape,
just below the `0x30000000` XIP base** ✓ · **load-dependent 3-6 min streaming vs ~30 min normal** ↔ our median
5.4 min / p90 73 min ✓ · victim = busiest task (theirs mavlink/uORB, ours DDS/INS0/uavcan) ✓ · stored
bytes==ELF (flash fine, the READ is wrong) ✓ · pc+lr both `0x30xxxxxx` ✓ · **§38.3 42 unique pcs over ~2.1 MB,
no clustering = global read margin** ✓ · **4 FCs/2 sites/USB-only changed NOTHING — because the ROM's DLL
placement is identical on every board** ✓✓ (this finally explains the campaign's most baffling fact) ·
temperature as a modulator (read window shifts with temp) ✓.
⚠️ **The #27735 REPORTER blamed "heap corruption / wild write". NXP overruled that with the DLL diagnosis —
we were one step from the same wrong turn.**
🔑 **Our build is v1.17.0 built May 31 2026 ⇒ PREDATES the 08-04 merge.** 🔑 **This is a BOOT-ROM issue ⇒
v1.16.2 would be affected TOO — more reason §38.4's "v1.16.2 is clean" was noise.**
⏭⏭ **PLAN — CHERRY-PICK, DO NOT JUMP TO v1.18-beta2** (beta2 changes everything else at once and would
confound the result). Single file, clean pick onto `pxlabs-fw`. ⚠️ `git fetch origin` FIRST — the commit is
not in our clone yet (`cat-file` fails). ⚠️ **OPERATOR GATES FLASHING (FC shared with the drone).**
✅✅ **FREE CONFIRMATION, INDEPENDENT OF THE SOAK — DO THIS ON THE FIRST BOOT:** the PR **logs the chosen DLL
value**. **I MEASURED THE ROM'S CURRENT VALUES ON OUR BOARD: `STS2 = 0x00000b33` → ASLVSEL=12, AREFSEL=11**
(§35). **If the calibrated midpoint differs materially from 12/11, that is direct evidence OUR board's ROM
setting was off-centre** — visible in boot output before any soak.
⛔ **PROOF BAR IS STILL 8 CONTINUOUS HOURS** (P(quiet ≥8 h)=0.0%), counting fault logs AND reboots, soak
**LAUNCHED DETACHED** (`setsid nohup …` — §29.5, it has died silently TWICE). **3 prior false "fixes."**

## 40. 2026-08-29 — 🎯 **OPERATOR REPORTS THE CHERRY-PICK FIXED IT. 7.7 h CLEAN AND COUNTING — BUT THE BUILD IS UNVERIFIED FROM HERE. HANDOFF SHIPPED TO THE PC.**
✅ **MEASURED THIS MORNING (08-29 08:37→08:47):** FC **booted 01:11:01, uptime 459 min = 7.66 h, 0 reboots**,
**SD card baseline 0 fault logs — CLEAN** (it held 3 on 08-25 ⇒ the card was cleared, presumably with the flash).
Load is REAL not idle: camera + `/scan` + `/scan_3d` + wheel odometry up, `throttled=0x0`, 51 °C.
🔑 **Against median 5.4 min / p90 73 min, 7.7 h clean under load is STRONG SIGNAL, not noise** (§29.2:
P(quiet ≥8 h)=0.0%, longest fault-era gap ever 7.3 h). ⛔ **BUT THE BAR IS 8 CONTINUOUS h AND WE WERE ~21 min SHORT
WHEN THIS WAS WRITTEN. DO NOT RECORD "SOLVED" UNTIL 480 min.** Precedent: 3 withdrawn fixes (§20 charger,
§25.1 USB, §29.3 SD reformat) were each declared on a shorter quiet window.
✅ **SOAK RELAUNCHED DETACHED 08:37:21 (pid 712835, `soak_detached_20260829.out`)** — it had been **DEAD since
08-26 22:39**, so nothing was counting during the whole quiet window. ⇒ **the 7.7 h is uptime+card evidence,
not soak-counted evidence.** Say that when quoting it.
🔴🔴 **THE BUILD IS NOT VERIFIABLE FROM THE COMPANION — THE CHERRY-PICK IS NOT IN OUR TREE.** `~/PX4-Autopilot`
on `pxlabs-fw`: **`git cat-file 9f4bc800` STILL FAILS (never fetched)**, `boards/px4/fmu-v6xrt/src/init.c`
mtime **2025-08-03 untouched**, HEAD still `a52c38b07d`, **no build dir**. ⚠️ **`flight_sw_version` reads
`1.17.0` — a cherry-pick onto v1.17.0 reports THE SAME, so the version string CANNOT discriminate.**
⇒ **The flash came from the PC's tree. 3 questions only the PC can close: (1) which tree + git hash (2) the
DLL VALUE LOGGED AT BOOT vs our ROM's `ASLVSEL=12/AREFSEL=11` (§39 free check — seconds, soak-independent)
(3) was the card cleared by the flash.**
✅ **HANDOFF WRITTEN AND PUSHED (`codex-work` `4c9ed19`, master):**
 · **`fc_hardfault_handoff_20260829.md`** — the full record for the PC to turn into PX4-repo content:
   symptom at scale, the elimination table (every suspect + the measurement that killed it), the live SWD
   catch, the FlexSPI register table, the #27735 evidence match, the analysis traps, §12 = suggested shape.
 · **`pxlabs_release_note_v1.17.0-r2.1.md`** — paste-ready `PXLABS.md` changelog + the 3 table updates +
   GitHub tag short form. **Carries two deliberate `<FILL>` fields (calibrated DLL value, soak hours)
   so it CANNOT be published as "fixed" without the evidence.**
 · **`COORDINATION.md`** — `[COMPANION]` entry with the 3 questions for the PC.
🔑 **NAMING: operator said "17.0.0 2.1.0"; fork convention (r1 / r2-Beta) ⇒ I used `pxlabs-v1.17.0-r2.1`
and flagged the alternative in the note. PC picks one and uses it in tag + OEM string + all 3 tables.**
🔑 **THE ONE WARNING PUT IN FRONT OF EVERYTHING: `LOCKED ≠ CENTRED`.** §35 read `STS2` = both DLL lock bits
set and crossed the DLL off for two days. The lock bits say it locked, NOT where in the read window it landed.
⚠️ `rover-autonav-mode` reads **failed** — operator says autonav + other services are deliberately removed
for this testing. **Not a fault, don't debug it.**

## 41. 2026-08-29 09:11 — ✅✅✅ **CAMPAIGN CLOSED. 8 h SOAK PASSED CLEAN. THE CAUSE WAS THE FlexSPI DLL READ STROBE.**
✅✅ **THE PROOF, INSTRUMENT-COUNTED (`fc_soak.py` pid 712835, verified alive + output growing — not a
status-file snapshot):** **09:11:49 IST, FC uptime 480.7 min = 8.01 h, reboots 0, new fault logs 0**,
**SINGLE BOOT 01:11:02** (one continuous window, nothing stitched), card baseline 0, under REAL load
(uXRCE-DDS + EKF2 + camera + `/scan` + `/scan_3d` + wheel odometry), `throttled=0x0`, ~51 °C.
🔑 **WHY 8 h IS THE BAR (§29.2): P(quiet ≥8 h) = 0.0%** over 38 gaps, median 5.4 min, p90 73 min, longest
quiet gap EVER in the fault era 7.3 h ⇒ **this window is outside anything the bug itself produced.**
🎯 **CAUSE: the RT1176 BOOT ROM does not CENTRE the FlexSPI DLL delay that samples the octal-NOR DQS read
strobe** ⇒ marginal XIP instruction fetch at 200 MHz octal DDR ⇒ the CPU executed words that were NOT what
is stored in flash. **FIX = PX4 PR #28141** (Peter van der Perk/NXP, merged 08-04, `9f4bc80006c`, ONE file
`boards/px4/fmu-v6xrt/src/init.c`) — RAM-resident boot sweep, picks the MIDPOINT of the widest passing range.
✅ **FLYING BUILD = `860013bab7`** (PC's tree, cherry-picked from `9f4bc80006c`). ⛔ **`flight_sw_version`
reads `1.17.0` WITH OR WITHOUT the pick — IT CANNOT DISCRIMINATE. Verify by GIT HASH only.**
✅ **PUBLISHED: `v1.17.0-2.1.0`** + `HARDFAULT.md` at the repo root of `ArvinVeiyon/PXLABS_PX4-Autopilot`
(PC side, commit `244afd0991`, branches `pxlabs-v1.17.0-2.1.0` + `-dev`). My handoff + release-note draft:
`codex-work` `4c9ed19`. ⛔ **My `r2.1` naming was SUPERSEDED — the published tag is `v1.17.0-2.1.0`.**
🔑🔑 **THE LESSON WORTH KEEPING — `LOCKED ≠ CENTRED`.** §35 read `STS2` = both DLL lock bits set and
`DLLCR 0x00400079` = NXP's recommended ≥100 MHz setting, and I struck the DLL off the list **for two days**.
The lock bits say the DLL LOCKED; they say NOTHING about WHERE IN THE READ WINDOW it landed. **§35's caveat
sentence ("locked and per-recommendation ≠ has margin at this temperature on this board") was the
load-bearing one and I under-weighted it against my own confident table of correct-looking registers.**
🔑 **2nd lesson: 4 FCs / 2 sites / USB-only changed the rate BY NOTHING — and that was the CLUE, not the
mystery.** A defect identical on every board is a defect in something identical on every board: the ROM.
I read it as "hardware is eliminated, so it must be our config" and never asked what is invariant ACROSS boards.
⏭ **STILL OPEN, DO NOT FOLD INTO "RESOLVED":**
 **(1) `g_dll_cal` NEVER READ — the direct mechanism evidence is still missing.** Symbol at **`0x20252774`**
 (BSS, 12 B) in build `860013bab7`. ⛔ **MCU-Link IS UNPLUGGED** (no `1fc9:0143`, no `/dev/ttyACM*`) — ask
 the operator to RESEAT, then `--connect attach` read of `g_dll_cal` + `FLEXSPI1 DLLCR/STS2 @0x400CC000`
 vs the ROM baseline **ASLVSEL=12 / AREFSEL=11**. ⛔ **Don't take the 57 MB ELF — the address is enough.**
 **(2) uXRCE-DDS NULL-DEREF (§30.4) IS UNTOUCHED BY THIS.** Its base rate was far below the DLL population,
 so 8 h of absence is NOT evidence it is gone. Still worth its own upstream issue.
