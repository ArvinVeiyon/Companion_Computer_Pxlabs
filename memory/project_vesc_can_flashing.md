---
name: vesc-can-flashing
description: "Flashing the 4 VESCs over the companion's CAN hat - VESC Tool is impossible, DroneCAN firmware update is the only path"
metadata: 
  node_type: memory
  type: project
  originSessionId: b7052c6e-f42f-48fd-9d7e-c0dffff0ecc5
  modified: 2026-09-07T18:24:28.826Z
---

**2026-09-05. Waveshare RS485 CAN HAT rev2.1 (12 MHz MCP2515, spi0.0 CE0=GPIO8, INT=GPIO25) fitted to the companion, wired to the VESC CAN splitter, to flash all four ESCs.**

🔴 **VESC TOOL OVER SOCKETCAN CANNOT WORK HERE — DO NOT TRY IT, DO NOT RE-PROPOSE IT.**
The rover app configs set `can_mode=1` = `CAN_MODE_UAVCAN`. In that mode `comm/comm_can.c:1346`
does a bare `continue` on every received frame — the VESC-native CAN protocol VESC Tool speaks is
never decoded — and `comm_can_ping()` returns false unconditionally (`comm_can.c:650`). A VESC Tool
CAN scan finds **nothing**, and that is correct behaviour, not a fault to debug.
Switching `can_mode` back to `VESC` needs USB per ESC and would take DroneCAN (and the rover) down.

✅ **THE PATH: DroneCAN firmware update, fully implemented in `libcanard/canard_driver.c`.**
ArduPilot's scheme, and the direction is inverted from what you expect: **we are the file SERVER,
the VESC is the client that pulls.** `BeginFirmwareUpdate` (:1171) → VESC erases its new-app area →
VESC issues repeated `file.Read` to us (:1022) → writes at `ofs+6` → on the final short chunk writes
size+CRC16 and sets `jump_to_bootloader` (:1095-1153) → reboots.

🔑 **NODE ID == VESC `controller_id`** (`canardSetLocalNodeID(&canard_ins, conf->controller_id)`,
`:1421`). Static, no dynamic allocation. Expected **10=RF(INV) 11=FL 12=RR 13=RL** per
[[rover-odometry]]. A node that doesn't appear is genuinely silent.
✅ **MAP SETTLED 09-06 — `FR=10 (slot 0) · FL=11 (1) · RR=12 (2) · RL=13 (3)`**, agreed by three
independent sources (the 4 current app configs' `controller_id`+`uavcan_esc_index`,
`Testing_Bin/README.md`, and [[rover-odometry]]). All four: `can_mode=1`, `can_baud_rate=3`,
`uavcan_raw_mode=0`. → **`codex-work/bldc_can/MOTOR_MAP.md`**
⚠️ **UNRESOLVED LABEL CONFLICT:** memory calls node 10 **"RF(INV)"**, but the config gives Right Front
`m_invert_direction=0` and the **other three** `=1`. Both agree RF is the odd one out; they disagree
which way. **Doesn't affect the node map — don't "tidy" it without a motion test.**
⏭ **STILL CONFIRM EMPIRICALLY:** connect **one VESC at a time**, run `scan.py`; the single node that
answers IS that wheel. **Rear left is on the bench now (expect 13).** Nothing in DroneCAN reports
physical position, so one-at-a-time is the only method. Termination stays right (hat 120Ω + 1 VESC =
60Ω); with all four on, ensure exactly **two** terminators, not five.
🗄 **Superseded:** the old `Motp_Config_Bldc/` had 43 accumulated files with only ids 11 and 13, and
two files named `appconf` that were actually `<MCConfiguration>`. **Fixed upstream in `da94056f`**
(renamed to `Motor_Config_Bldc/`, pruned to 8, re-exported). The `uavcan_esc_index=7` anomaly is gone.

🔴🔴 **`Testing_Bin/60_mk5.bin` CANNOT GO OVER DRONECAN — IT WOULD OVERWRITE THE BOOTLOADER. FLASH IT
OVER USB.** (Confirmed 09-06 against the published binary, sha256 `b971e9a7…` verified, **and the
524,280 B is NOT padding — 85,276 non-fill bytes sit past the ceiling, so it cannot be truncated**.)
**The app region is 512 KB** (`ld_eeprom_emu.ld:28-30`: `flash` 16k @0x08000000 + `flash2` 512k-48k-16
@0x0800C000 + `crcinfo` @0x0807FFF0) **but the DroneCAN staging area is only 384 KB** — sectors 8-10,
`NEW_APP_MAX_SIZE = 3*(1<<17)` = 393216 (`canard_driver.c:153`). **The app outgrew the staging area.**
`flash_helper_write_new_app_data` is `write_data(flash_addr[NEW_APP_BASE] + offset, …)` —
**`flash_helper.c:181`, NO BOUNDS CHECK** — so the transfer runs **131,070 B past the staging area
into 0x080E0000 = sector 11 = THE BOOTLOADER**, which `flash_helper_erase_new_app()` never erases
⇒ programmed into un-erased flash ⇒ **brick, recoverable only by SWD/ST-Link.**
⛔ **`Testing_Bin/README.md` RECOMMENDS THE DRONECAN PATH — that advice is unsafe at this size; it
needs correcting upstream.** ✅ `flash.py` refuses anything >393,210 B — **never work around that guard.**
🔑 **The DroneCAN path itself is sound — it is only this image's SIZE that breaks it.**

⚠️ **NO CONFIG BACKUP OVER CAN.** The DroneCAN param table (`canard_driver.c:225`) exposes only 8
params: `can_baud_rate`, `can_status_rate_1/2`, `can_status_msgs_r1/r2`, `can_esc_index`,
`controller_id`, `ctl_dir`. **No mcconf** ⇒ `si_motor_poles` and the FOC constants can ONLY be
backed up over **USB + VESC Tool, per ESC**. `backup_params.py` captures the 8 and nothing more.

🔑 **DOES A FLASH WIPE THE CONFIG? ALMOST CERTAINLY NOT — but NOT for the reason I first gave.**
⛔ **The `MCCONF_SIGNATURE` check is the WIRE protocol only** (`confgenerator.c:349`), NOT the stored
config. Stored config is a **raw struct dump in emulated EEPROM guarded by a CRC**
(`conf_general.c:436-467`): it reads `sizeof(mc_configuration)/2` half-words, and on CRC mismatch
**silently** calls `confgenerator_set_defaults_mcconf()` — a full wipe, no warning. So survival
depends on the **struct layout being byte-identical**, nothing else.
✅ **VERIFIED: `dcc35366` (release-r1 tip, what's running) → `a75a0db` (flash target) differ in only
`canard_driver.c` + one `.md`. `datatypes.h`, `confgenerator.h/.c`, `conf_general.h` are IDENTICAL
by object hash** ⇒ layout unchanged ⇒ config loads and CRC passes. (Note `05deb3e8`, cited in
`px4_vesc_dronecan_implementation.md` as the fw read, **does not exist in the repo even unshallowed**.)
✅ **EVEN IN A WIPE, CAN ID AND BAUD SURVIVE** — upstream `6fe2d789` "Persist CAN ID and CAN Baud Rate
across firmware updates" is an ancestor of the target: `conf_general_read_app_configuration` restores
`controller_id`/`can_baud_rate` from `g_backup` (`.ram4` backup area) after applying defaults. So a
wiped ESC **stays reachable at its node ID** — you'd lose the motor tune, not the bus.

⚠️ **BITRATE IS 1 Mbit AND NOT A CHOICE:** FC `UAVCAN_BITRATE=1000000` (read live) and VESC
`can_baud_rate=3` = `CAN_BAUD_1M`. 1 Mbit on MCP2515 **requires the 12 MHz crystal** (this board has
it; an 8 MHz board binds fine and then fails on the bus — a wrong crystal is NOT a bind failure).

⚠️ **SPI0 TAKES GPIO8/9 ⇒ `dtoverlay=uart3-pi5` LOSES THE PINS and `/dev/ttyAMA3` DOES NOT EXIST.**
Pre-existing (`dtparam=spi=on` was already set), so STL-19 was already dead — see [[uart-map]],
whose AMA3 row is aspirational, not live. Cost is accepted while the CAN hat is fitted.

⛔ **The target branch `pxlabs-6.06-rover-brake-rc` is UNTESTED by its own doc** ("Nothing on this
branch has been run on hardware") and has an unfixed blocker: `RC3_TRIM == RC3_MIN`, so lifting the
stick off the stop instantly commands ~50 % brake. **Flash ONE ESC first** — flashing all four
destroys the rollback in a single shot. Rollback = `v6.06.0-pxlabs-rover-r1`.

📁 **REPO CONFIG XMLs CATALOGUED 09-05 → `~/vesc_can/configs_from_repo/` (43 files, from
`Motp_Config_Bldc/`), lister `~/vesc_can/catalog_configs.py`. THEY ARE A REFERENCE SET, NOT A BACKUP
— nobody verified they match the live ESCs.** Findings:
· **Only 6 distinct appconfs and only ONE carries `controller_id=13`** (`vesc_appconf_Aug_2026.xml`);
every other appconf says **11**. ⇒ **the wheel↔node-ID map is NOT recoverable from the repo.**
· `si_motor_poles=14` **uniformly across all 36 mcconfs** — the value paired with `erpm_to_ms=0.003900`.
· **The per-wheel difference is `foc_motor_r` / `foc_motor_l` / `foc_motor_flux_linkage`** (measured
per motor). **That is what a wipe would destroy** — poles/gear/wheel-dia are common.
· **Newest coherent 4-wheel set = the `__15_Aug_26` files** (LF r=0.5215 · LR r=0.1988 · RF r=0.557 ·
RR r=0.4367). ⚠️ **LR's 0.1988 is an outlier vs the other three (0.44-0.56) and is duplicated in
`Left_Front_tested_04_may_26` — treat as suspect, verify before restoring.**
· ⛔ **`vesc_mcconf_Right_Front.xml` has `foc_motor_flux_linkage=1.46287`, ~130× the family
(0.0104-0.0116) — a failed detection. NEVER restore from that file.**
· ⚠️ `vesc_appconf_Aug_front_left_2026.xml` has `uavcan_esc_index=7` — out of range for a 4-wheel
rover on slots 0-3, and slot 4 is the new RC-brake slot. Stale file; don't load it.

**Tooling built 09-05 (all API-verified, none hardware-tested — needs the reboot):**
`~/vesc_can/bringup.sh` (can0 @ 1 Mbit, `restart-ms 100`) · `~/vesc_can/scan.py` (node list) ·
`~/vesc_can/flash.py` (file server + BeginFirmwareUpdate, size pre-flight, live progress read off
`NodeStatus.vendor_specific_status_code` = 1+kB, `:1156`). Venv `~/vesc_can_venv` (dronecan 1.0.27,
python-can 4.6.1) — deliberately NOT system python, which ROS uses.
Overlay staged in `/boot/firmware/config.txt`; backup `config.txt.bak-canhat-20260905`.

🔴🔴 **ALL OF THIS NOW LIVES IN `~/codex-work/bldc_can/` — COMMITTED AND PUSHED (`23584ac`, branch
`master`). ⏭⏭ ON ANY NEW SESSION OR AFTER THE REBOOT, OPEN `codex-work/bldc_can/RESUME.md` FIRST.**
It carries the post-reboot checklist, the service table, and the next task. `README.md` = why,
`MOTOR_MAP.md` = the map, `evidence/` = the source excerpts every claim rests on.
⚠️ Clones of `PXLABS_BLDC_VESC6_MK5` / `vesc_tool` were **scratchpad-only and are gone** — re-clone
over SSH if source is needed again. **Nothing was ever nested inside `codex-work` (verified).**

🔴🔴 **09-06 POST-REBOOT: BLOCKED ON HARDWARE — THE MCP2515 HAS NO VDD. `can0` STILL DOES NOT EXIST.**
`mcp251x spi0.0: MCP251x didn't enter in conf mode after reset / Probe failed, err=110`.
⛔ **STOP TUNING THE OVERLAY — the whole SPI-config hypothesis family is ELIMINATED**, not just one
member: overlay verified applied in the live DT (`can0_osc` 12 MHz, INT `<25 8>`, mux `function spi0`
on gpio8/9/10/11); raw register reads silent at **modes 0 and 3 × 100 kHz–2 MHz**; silent on **CE1**
as well as CE0; and silent when **bit-banged with `dw_spi_mmio` unbound**, which exonerates the RP1
controller and its driver (independent ruler).
🔑 **THE MEASUREMENT THAT SETTLED IT — MISO is not driven at all.** With the bias confirmed applied
in `pinconf-pins`: `MOSI=0 ⇒ MISO pinned 0 against a pull-up · MOSI=1 ⇒ MISO follows either pull ·
CS makes NO difference.` One-way tracking that ignores CS is **not** a chip and **not** a resistive
short (a short drags MISO high against a pull-down too) — it is **ESD-diode back-feed through an
unpowered die**. Every bit-banged byte fits `rx[i] = tx[i] OR tx[i-1]` exactly = pure MOSI bleed.
⚠️ **TRAPS THIS COST ME:** `gpioget` on GPIO25 reads **1** and looks like a healthy idle INT — it is
the same back-feed, **do NOT read it as "the hat is powered"** · a bias sweep with **no settle delay**
returned a physically impossible "pull-up→0, pull-down→1" — **always sleep, and always confirm from
`/sys/kernel/debug/pinctrl/…/pinconf-pins` that the pull you asked for actually landed.**
⏭ **NEXT = OPERATOR + MULTIMETER:** meter 3V3/5V at the MCP2515's VDD vs header pins 1/17 and 2/4;
look for an unmade/bent **power** pin or a power jumper (signal pins clearly do make contact); swap
the hat if the rail dies between header and chip. **Re-run in one command:
`sudo python3 ~/codex-work/bldc_can/diag/spi_probe.py`** (restores every binding it touches; a pass
is `CANSTAT=0x80`). Then resume at RESUME.md Step 1 — rear left still on the bench, expect node 13.
✅ **`config.txt` put BACK to `spimaxfrequency=10000000`** (the 1 MHz shot-in-the-dark is disproven,
and 1 MHz SPI is too slow to service a busy 1 Mbit bus later); backup `config.txt.bak-canhat-20260906`.

🔴🔴 **09-06 SECOND ATTEMPT — OPERATOR RE-SEATED THE HAT, REBOOTED: STILL NO `can0`, SAME err=110.**
🔑 **THE SIGNATURE CHANGED AND IT IS NOT BETTER: the MOSI back-feed is GONE and NOTHING replaced it.**
With SPI **bound and idle** (no MOSI to couple) and the bias verified: **`/INT` gpio25 AND MISO gpio9
BOTH FLOAT** (`pull-up→1s, pull-down→0s`). A powered MCP2515 drives `/INT` **high push-pull** and
would beat the pull-down ⇒ **nothing is on the other end.** ⇒ before the re-seat the pins provably
reached an *unpowered die*; now there is **no coupling at all** ⇒ **suspect SEATING/OFFSET as well as
power.** ⏭ operator: seating first, then rails, then **buzz continuity header→chip: 21→SO 19→SI
23→SCK 24→CS 22→INT.**
⛔ **NEVER ACCEPT `CANSTAT=0x80` AS THE PASS — IT TURNS UP IN NOISE** (it did, once, at 100 kHz).
✅ **THE RULER THAT SETTLES IT: WRITE A REGISTER AND READ IT BACK** (CNF1 `0x5A/0xA5`, TXB0SIDH
`0x3C/0xC3`) — a short, a float or bleed cannot return a value *we chose* at an address *we chose*.
**Scored 0/35** across 7 speeds × 5 trials. Also: the old CS×MOSI sweep is **non-reproducible now**
(PINNED LOW one run, PINNED HIGH the next) = a charge-holding hi-Z line, not a chip.
🔧 **NEW TOOL `codex-work/bldc_can/diag/int_probe.py` — RUN IT FIRST** (1 s, no unbinding, no
back-feed ambiguity); `spi_probe.py` is now the deep dive. Both documented in `RESUME.md`.

🔴🔴 **09-06 THIRD BOOT — STILL BLOCKED, AND THE OPERATOR/METER STEPS ARE STILL UNDONE.**
⛔⛔ **THE TRAP THAT WILL BITE AGAIN: `err=110` → `err=19` IS NOT PROGRESS.** dmesg now reads
`Cannot initialize MCP2515. Wrong wiring? / Probe failed, err=19` (`-ENODEV`). That is raised
**later** in the driver than err=110 — reset passed, the `CANCTRL` power-up-default check failed.
But passing reset only needs **one** `CANSTAT` read to come back with the config-mode bits, and
**`0x80` turns up in noise on a floating MISO.** ⇒ **the error code moved because the noise moved.**
🔑 **Three boots, three different signatures, zero passes — the VARYING signature IS the finding.**
✅ **`wrb_probe.py`: 0 of 140 PAIRED** (SPI modes 0 **and** 3 × 7 speeds 100 kHz–10 MHz × 5 trials)
and `int_probe.py` on the same boot still says **`/INT` + MISO BOTH FLOAT**, bias verified applied.
⛔⛔ **REFINES THE PASS CRITERION BELOW — "A VALUE WE CHOSE CAME BACK" IS *NOT* ENOUGH.** The hi-Z
line holds charge from the **previous** transfer, so a single-register write/read-back scores a FALSE
PASS whenever the held value happens to equal the value just written. **It did: v1 scored 10/280 on
provably dead hardware.** Visible as stuck-at runs in the raw rows (`C3C3`, `1E1E`, `8787`, `7878`).
✅ **THE SOUND CRITERION IS A *PAIR*: write two DIFFERENT values to two DIFFERENT registers
(CNF1 0x2A + TXB0SIDH 0x31), read BOTH, both must match.** A held line can only hold one value.
🔑 **CNF1 is config-mode-only (where RESET leaves us); TXB0SIDH is writable in ANY mode once TXREQ is
clear — keeping both means a chip that is alive but NOT in config mode still registers.**
✅ **CRYSTAL IS 12 MHz, operator-confirmed 09-06 — matches `oscillator=12000000`. 8-vs-12 CLOSED.**
⚠️ **That settles the NUMBER only.** `oscillator=` only sets bit-timing and can NEVER cause a probe
failure; a crystal that is not physically **OSCILLATING** is a different fault that WOULD kill SPI
outright (the MCP2515's SPI state machine is clocked from its own crystal) and is **indistinguishable
from missing VDD in software**. Still a suspect — scope, or swap the hat.
✅ **CHIP/WIRING RE-VERIFIED AGAINST THE LIVE DT + DATASHEET:** `compatible microchip,mcp2515`,
`reg 0` (CE0=GPIO8), `interrupts <25 8>`, `spi-max-frequency` 10 MHz (= the datasheet SPI ceiling),
`can0_osc` 12 MHz. Opcodes `RESET 0xC0 / READ 0x03 / WRITE 0x02`, regs `CANSTAT 0x0E CANCTRL 0x0F
CNF1 0x2A TXB0SIDH 0x31` all correct. 🔑 **`mcp251x` is the Linux DRIVER FAMILY name (2510/2515/
25625), not a different part — don't chase it.** ⚠️ **waveshare.com 403s automated fetches; verify
from the live DT, not the vendor page.**
🔑 **NEW SIGNATURE — A ONE-TRANSACTION LAG LINE:** each speed row returns, shifted by one slot, the
values the **previous** row returned (`…07 1E 0B 14 00 00 02 9C…` reappearing a slot later) = a hi-Z
line holding charge from the preceding transfer, **zero chip contribution**. Same class as the old
MOSI back-feed, different coupling path. ⇒ **still hardware, still upstream of anything software
reaches.** ⛔ **Do not run another software measurement until the meter has been on the board.**
🔧 **NEW TOOL `diag/wrb_probe.py`** — the documented pass criterion in one command (binds spidev,
restores `mcp251x` after). Order from now on: **`int_probe.py` → `wrb_probe.py` → `spi_probe.py`.**
Committed `codex-work@b8fddac` (NOT pushed).

✅ **09-06 SERVICES AFTER THE REBOOT — all returned exactly as predicted; `vision_streaming` came
back BY ITSELF.** ⇒ **the "`vision_streaming` is disabled at boot / a reboot kills the video" note is
WITHDRAWN.** (`active` is still not a rate — nobody measured the stream.) `rover-ekf-bridge` and
`tfmini` stayed down on purpose.

---

## 🔴 2026-09-07 — THE RC BRAKE IS LIVE ON ONE WHEEL. PX4 SIDE DONE AND SAVED.

✅ **OPERATOR FLASHED REAR LEFT with `a75a0dbf`** (the other three are untouched ⇒ **the rollback is
intact**). **Confirmed working by the operator:** raise ch3 and **only** the rear-left motor stops
while the other three keep running — which is also the cleanest possible proof that the flash took
and that the other three ignore RawCommand index 4.

✅ **PX4 SIDE COMPLETE — written, saved with `MAV_CMD_PREFLIGHT_STORAGE`, and VERIFIED to survive an
FC reboot** (the operator rebooted; all four read back unchanged):
`RC3_TRIM` **1001 → 1487.5** · `RC_MAP_AUX1` **3** (operator set it in QGC) · `UAVCAN_EC_FUNC5`
**407** = RC_AUX1 → RawCommand index 4 · `UAVCAN_EC_MIN5/MAX5` **left at 1 / 8191, deliberately**.
⛔ **DO NOT copy the motors' `110/8082` onto slot 5** — that pair exists to give the four *motor*
slots a 4096 neutral. The brake is unipolar and needs its minimum to mean OFF; 1/8191 gives 0.012 %.
⚠️ **Set `RC_MAP_AUX1` BEFORE `UAVCAN_EC_FUNC5`** — slot 5 assigned while AUX1 is unmapped makes
`aux1` read 0 = mid-scale = **50 % brake demand on the bus**.

🔑 **WHY `RC3_TRIM == RC3_MIN` REALLY MEANT 50 % BRAKE** (from source, not inferred):
`interpolateNXY` (`Functions.hpp:201`) with `min == trim` returns **−1.0 at exactly 1001 but ~0.0 at
1002** — a 1 µs discontinuity — and `output_limit_calc_single` (`mixer_module.cpp:568`) maps a
non-servo function −1…+1 onto MIN…MAX, so norm 0 → 4096 → 50 %.
🔴🔴 **THE TRAP: `rc_configuration.md` §2.1 — "TRIM==MIN is a QGC artefact, PX4 corrects it, DON'T FIX
IT" — IS THROTTLE-ONLY.** `rc_update.cpp:172` scopes that re-centring to `FUNCTION_THROTTLE`.
**Never generalise §2.1 to another channel.** ⚠️ `RC_MAP_PITCH = 3` too, but the operator loads a
**different param set for the drone**, so ch3 is free for the rover. ⚠️ **Re-check `RC3_TRIM` after
any QGC RC calibration** — calibration rewrites TRIM.

🔴🔴 **`ros2_ws/tools/set_param.py` CANNOT WRITE INT32 PARAMS — IT ALWAYS SENDS `MAV_PARAM_TYPE_REAL32`
AND PX4 REFUSES THE WRITE.** `mavlink_parameters.cpp:129-131` requires (INT32,INT32) or
(FLOAT,REAL32) and otherwise logs "param types mismatch" and **writes nothing** — it fails safe, but
it fails. PX4 then does `param_set(param, &set.param_value)` on the **raw 4 bytes**, so an INT32 must
be sent as the integer's **BIT PATTERN** in the float field, typed `MAV_PARAM_TYPE_INT32`.
**`set_param.py` is float-only; it also has no save.** ⏭ worth folding both into the real tool.
🔑 **`param save` without `mavlink_shell`:** `MAV_CMD_PREFLIGHT_STORAGE` param1=1, check the
`COMMAND_ACK`. **Reboot the FC first** so RAM==flash and the save commits only what you meant.
🔑 **FC reboot over DDS:** publish `VehicleCommand` 246 param1=1 to `/fmu/in/vehicle_command` (pattern
in `tools/dds_setmode.py`). ⚠️ **CHECK CH10 FIRST** (1011=down=safe).

🔴🔴 **THE BRAKE IS REGENERATIVE — IT DOES NOTHING AT STANDSTILL, AND THAT IS NOT A FAULT.**
`mc_interface_set_brake_current_rel` → `mcpwm_foc_set_brake_current` → **`CONTROL_MODE_CURRENT_BRAKE`**
(`mcpwm_foc.c:832`): torque comes from opposing rotation, so it scales with back-EMF ⇒ **at hand-turn
speed 100 % and 10 % both produce ≈ nothing.** ⛔ **A HAND TEST CANNOT MEASURE THIS BRAKE — the
operator's "I can still turn it easily at full stick" is EXPECTED, not a defect. Test at speed.**
⏭ **A HOLDING brake is a different call the firmware already has:** `mc_interface_set_handbrake_rel`
→ `CONTROL_MODE_HANDBRAKE`, *"open loop current vector"* (`mc_interface.c:757`), **same
`val × |lo_current_min|` scaling**, holds at zero speed. One-line swap at `canard_driver.c:747`; the
right answer is probably a **hybrid** (handbrake below some ERPM, regen above).
🔑 **BRAKE CURRENT COMES FROM THE mcconf:** `brake_rel × |lo_current_min|`, and `lo_current_min` is
the **runtime-scaled** `l_current_min` ⇒ **authority FADES silently when hot or near max pack
voltage.** Repo set: `l_current_min` **−25 A** (LF −25.8) · `l_in_current_min` **−5 A** ·
`l_abs_current_max` 35 · `cc_min_current` 0.05 (the engage floor). 🔴 **the −5 A BATTERY REGEN cap is
probably what actually binds, not the 25 A.** ⚠️ these are the REPO XMLs, **never verified live**.
⛔ **DON'T TUNE `l_max_erpm_fbrake` (300) / `_cc` (1500) — every use is in `mcpwm.c` = the BLDC path,
and `motor_type=2` = FOC.** Dead params here.
🔑 **THE OTHER BRAKE, ALREADY RUNNING ON ALL FOUR: `timeout_brake_current = 2 A` @ `timeout_msec`
300** (`timeout.c:225-233`) — a **flat, absolute** 2 A applied when no CAN command arrives for 300 ms
or the kill switch trips. **Not a weak version of the RC brake — a different mechanism.** ⚠️ so
"COAST ONLY" is not strictly true: there is always 2 A on command loss (negligible, but it is there).
⚠️ **`uavcan_raw_mode = 0` (=CURRENT, lower stick = REVERSE, not brake) in all four repo appconfs** —
if lower-stick braking is ever observed, that param has been changed live.

⏭⏭ **NEXT: the operator is testing the brake AT SPEED** (the hand test proved nothing). Then decide
regen vs handbrake vs hybrid, and only then flash the other three.
