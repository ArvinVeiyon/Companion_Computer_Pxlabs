---
name: vesc-can-flashing
description: "Flashing the 4 VESCs over the companion's CAN hat - VESC Tool is impossible, DroneCAN firmware update is the only path"
metadata: 
  node_type: memory
  type: project
  originSessionId: b7052c6e-f42f-48fd-9d7e-c0dffff0ecc5
  modified: 2026-09-05T19:45:14.195Z
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

✅ **09-06 SERVICES AFTER THE REBOOT — all returned exactly as predicted; `vision_streaming` came
back BY ITSELF.** ⇒ **the "`vision_streaming` is disabled at boot / a reboot kills the video" note is
WITHDRAWN.** (`active` is still not a rate — nobody measured the stream.) `rover-ekf-bridge` and
`tfmini` stayed down on purpose.
