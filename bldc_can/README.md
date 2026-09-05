# BLDC / VESC flashing over CAN from the companion

Flashing the four rover VESCs over a **Waveshare RS485 CAN HAT rev 2.1** (12 MHz MCP2515 on
`spi0.0`, CE0 = GPIO8, INT = GPIO25) fitted to the companion Pi and wired to the VESC CAN splitter.

**Status 2026-09-05: tooling complete and API-verified. Nothing is hardware-tested — `can0` does not
exist yet, because the device-tree overlay is staged but the companion has not been rebooted.**

---

## 1. The headline: VESC Tool over CAN cannot work here

Do not try it, and do not treat the silence as a fault to debug.

The rover's VESCs run `can_mode = 1` (`CAN_MODE_UAVCAN`, `datatypes.h:864`). In that mode the CAN
process thread discards every received frame before decoding:

```c
/* comm/comm_can.c:1346 */
if (app_get_configuration()->can_mode == CAN_MODE_UAVCAN) {
    continue;
}
```

`comm_can_ping()` also refuses unconditionally outside `CAN_MODE_VESC` (`comm_can.c:650`). VESC Tool
speaks the VESC-native CAN protocol, so **a SocketCAN scan finds nothing, and that is correct
behaviour.** Switching `can_mode` back to `VESC` needs USB on each ESC and would take DroneCAN — and
therefore the rover — down.

## 2. The path that does work: DroneCAN firmware update

Fully implemented in `libcanard/canard_driver.c`. It is ArduPilot's scheme, and **the direction is
inverted from the intuition**: we are the file *server*, the VESC is the *client that pulls*.

```
 companion (node 127)                         VESC (node 10-13)
        |                                            |
        |---- file.BeginFirmwareUpdate ------------->|  :1171 erase new-app area
        |<--- response: ERROR_OK --------------------|
        |                                            |
        |<--- file.Read (offset 0) ------------------|  :1022 the VESC drives the transfer
        |---- 256-byte chunk ----------------------->|  :1058 writes at ofs+6
        |                        ... repeats ...     |
        |<--- file.Read (final, short) --------------|
        |---- last chunk -------------------------->|  :1095 writes size+CRC16 into first 6 bytes
        |                                            |  :1153 jump_to_bootloader = true -> reboots
```

Progress is observable without instrumentation: `node_status.vendor_specific_status_code = 1 + kB`
transferred (`canard_driver.c:1156`), which `flash.py` reads live off `NodeStatus`.

## 3. Node identity

**The DroneCAN node ID *is* the VESC `controller_id`** — `canardSetLocalNodeID(&canard_ins,
conf->controller_id)` (`canard_driver.c:1421`). Static; no dynamic allocation. A node that does not
appear is genuinely silent.

| Wheel | Node | PX4 slot | Wheel | Node | PX4 slot |
|---|---|---|---|---|---|
| Front Right | **10** | 0 | Rear Right | **12** | 2 |
| Front Left | **11** | 1 | Rear Left | **13** | 3 |

Three independent sources agree: the current app configs, `Testing_Bin/README.md`, and companion
memory. **Full detail, including per-motor FOC constants and the direction-inversion discrepancy, is
in [`MOTOR_MAP.md`](MOTOR_MAP.md).**

> **Still confirm it empirically before flashing.** Connect one ESC at a time and run `scan.py`; the
> single node that answers is that wheel. Nothing in DroneCAN reports physical position, so
> one-at-a-time power-up is the only way to bind a node ID to a wheel. Termination stays correct in
> this scheme (hat 120 Ω + the one VESC = 60 Ω). When all four are on, make sure there are exactly
> **two** terminators on the bus, not five.

## 4. Does flashing wipe the motor config?

**Almost certainly not — but the failure mode is silent, so back up over USB first anyway.**

The `MCCONF_SIGNATURE` in `confgenerator.c:349` guards the **wire** protocol, *not* stored config.
Stored config is a **raw struct dump in emulated EEPROM guarded by a CRC** (`conf_general.c:436-467`):
it reads `sizeof(mc_configuration)/2` half-words and, on CRC mismatch, silently calls
`confgenerator_set_defaults_mcconf()`. No warning, no error — just defaults.

So survival depends **only** on the struct layout being byte-identical. Verified:

| Commit | Role | `datatypes.h` / `confgenerator.h` / `confgenerator.c` / `conf_general.h` |
|---|---|---|
| `dcc35366` | release-r1 tip — what is running | identical by object hash |
| `a75a0db` | RC-brake commit — the flash target | identical by object hash |

The two differ in **`libcanard/canard_driver.c` and one `.md`, nothing else.** Layout unchanged →
CRC passes → config loads.

**Even in a wipe you do not lose the bus.** Upstream `6fe2d789` *"Persist CAN ID and CAN Baud Rate
across firmware updates"* is an ancestor of the target: `conf_general_read_app_configuration`
restores `controller_id` and `can_baud_rate` from the `.ram4` backup area *after* applying defaults
(see `evidence/6fe2d789_persist_can_id.patch`). A wiped ESC still answers at its node ID — you lose
the motor tune, not reachability.

> `05deb3e8`, cited in `../px4_vesc_dronecan_implementation.md` as the firmware that was read,
> **does not exist in `PXLABS_BLDC_VESC6_MK5` even after `git fetch --unshallow`.**

## 5. Hard limits and pre-flight checks

| Check | Value | Source |
|---|---|---|
| Bitrate | **1 Mbit, not a choice** | FC `UAVCAN_BITRATE=1000000` (read live) + VESC `can_baud_rate=3` = `CAN_BAUD_1M` |
| Crystal | **12 MHz required** for 1 Mbit on MCP2515 | this board has it; an 8 MHz board binds fine then fails *on the bus* |
| Max image | **393 210 bytes** | `NEW_APP_MAX_SIZE = 3*(1<<17)` (`canard_driver.c:153`) minus the 6-byte size/CRC header |
| Config backup over CAN | **impossible** | only 8 params exposed (`canard_driver.c:225`) |

### ⛔ STOP: `Testing_Bin/60_mk5.bin` CANNOT be flashed over DroneCAN. Use USB.

The binary is now published (`Testing_Bin/60_mk5.bin`, sha256 `b971e9a7…`, verified). It is
**524 280 bytes, and it is not padding** — 85 276 non-fill bytes sit beyond the 393 216-byte ceiling.
It cannot be truncated.

The reason it is that size is the linker script `ld_eeprom_emu.ld:28-30`:

```
flash   : org = 0x08000000, len = 16k
flash2  : org = 0x0800C000, len = 512k - 48k - 16
crcinfo : org = 0x0807FFF0, len = 8
```

The **application** region is 512 KB (0x08000000–0x0807FFFF, sectors 0–7) and the image fills it
exactly. But the **DroneCAN staging area is only 384 KB** — sectors 8, 9, 10
(`NEW_APP_BASE = 8`, `NEW_APP_SECTORS = 3`). **The app outgrew the staging area.**

`handle_file_read_response` writes each chunk at `flash_addr[NEW_APP_BASE] + ofs + 6` via
`flash_helper_write_new_app_data`, which is `write_data(flash_addr[NEW_APP_BASE] + offset, …)` —
**`flash_helper.c:181`, with no bounds check of any kind.** So:

| | |
|---|---|
| staging area | `0x08080000`–`0x080DFFFF` (393 216 B, sectors 8–10) |
| this image needs | `0x08080000`–`0x080FFFFD` (524 280 B + 6-byte header) |
| **overflow** | **131 070 bytes past the staging area** |
| **what is there** | **`0x080E0000` = sector 11 = the BOOTLOADER** |

And `flash_helper_erase_new_app()` erases sectors 8, 9, 10 only — **sector 11 is never erased**, so
those 131 070 bytes are programmed into un-erased bootloader flash.

**Consequence: flashing this image over DroneCAN corrupts the bootloader. Recovery requires SWD /
ST-Link, not CAN and not USB.**

`flash.py` refuses any image over 393 210 bytes, so it will not perform this transfer. **Do not work
around that guard.**

> `Testing_Bin/README.md` currently offers DroneCAN as an option — *"Serve this `.bin` raw; the
> firmware writes its own size+CRC header."* **That advice is unsafe for an image of this size and
> should be corrected in the firmware repo.** USB flashing is unaffected: VESC Tool's bootloader path
> writes the application region directly and never uses the staging area.

The DroneCAN path in this folder remains correct and usable — but only for an image ≤ 393 210 bytes.

> ⚠️ **The target branch `pxlabs-6.06-rover-brake-rc` is untested by its own doc** ("Nothing on this
> branch has been run on hardware") and carries an unfixed blocker: `RC3_TRIM == RC3_MIN`, so lifting
> the stick off the stop instantly commands ~50 % brake. **Flash one ESC first** — flashing all four
> destroys the rollback in a single shot. Rollback is `v6.06.0-pxlabs-rover-r1`.

## 6. What is *not* backed up, and why it matters

DroneCAN exposes exactly eight parameters (`canard_driver.c:225`): `can_baud_rate`,
`can_status_rate_1`, `can_status_rate_2`, `can_status_msgs_r1`, `can_status_msgs_r2`,
`can_esc_index`, `controller_id`, `ctl_dir`. **No mcconf.**

`configs_from_repo/` mirrors `PXLABS_BLDC_VESC6_MK5/Motor_Config_Bldc/` @ `d513e790` — **8 files, the
pruned current set** (4 app + 4 motor, one per wheel). **Per the operator these are the configs
currently loaded in the ESCs.** Provenance is stamped in `configs_from_repo/PROVENANCE.txt`; run
`catalog_configs.py` to tabulate them. Full wheel↔node map: **[`MOTOR_MAP.md`](MOTOR_MAP.md)**.

> Earlier in this work the folder was `Motp_Config_Bldc/` with 43 accumulated files, in which only
> `controller_id` 11 and 13 appeared — no app config existed for node 10 or 12, and two files named
> `appconf` were actually `<MCConfiguration>`. **That gap was closed upstream in `da94056f`** (rename
> + prune + re-export). The current set is complete and internally consistent.

### Motor configs — complete and identifiable ✅

**The current four-wheel tune is the `__15_Aug_26` set.**

| Wheel | File | `foc_motor_r` | `foc_motor_l` | `foc_motor_flux_linkage` |
|---|---|---|---|---|
| FL | `vesc_mcconf_Left_Front__15_Aug_26.xml` | 0.5215 | 0.00055165 | 0.010933 |
| RL | `vesc_mcconf_Left_Rear__15_Aug_26.xml` | **0.1988** | 0.00041032 | 0.011551 |
| FR | `vesc_mcconf_Right_Front__15_Aug_26.xml` | 0.557 | 0.00054661 | 0.011419 |
| RR | `vesc_mcconf_Right_Rear__15_Aug_26.xml` | 0.4367 | 0.00048855 | 0.010385 |

- `si_motor_poles = 14` **uniformly across all 36 motor configs** — the value paired with the ROS-side
  `erpm_to_ms = 0.003900`. Gear ratio and wheel diameter are likewise common.
- **The genuine per-wheel difference is `foc_motor_r`, `foc_motor_l`, `foc_motor_flux_linkage`** —
  measured per motor by detection. **That is exactly what a wipe would destroy**, and it is
  unreachable from CAN.
- ⚠️ **RL's `r = 0.1988` is an outlier** against the other three (0.44–0.56) and is duplicated in
  `Left_Front_tested_04_may_26.xml`. Since RL is the first ESC on the bench, **verify it against the
  live export before trusting it as the restore point.**
- ⛔ `vesc_mcconf_Right_Front.xml` has `foc_motor_flux_linkage = 1.46287`, ~130× the family
  (0.0104–0.0116) — a failed detection. **Never restore from that file.**

### App configs — complete and consistent ✅

One per wheel, each carrying an explicit node ID and PX4 slot:

| Wheel | File | `controller_id` (node) | `uavcan_esc_index` (PX4 slot) |
|---|---|---|---|
| FR | `vesc_appconf_Aug_front_Right_2026.xml` | 10 | 0 |
| FL | `vesc_appconf_Aug_front_left_2026.xml` | 11 | 1 |
| RR | `vesc_appconf_Aug_Rear_Right_2026.xml` | 12 | 2 |
| RL | `vesc_appconf_Aug_left_Rear_2026.xml` | 13 | 3 |

All four share `can_mode = 1` (`CAN_MODE_UAVCAN`), `can_baud_rate = 3` (`CAN_BAUD_1M`),
`uavcan_raw_mode = 0` (`UAVCAN_RAW_MODE_CURRENT`), `app_to_use = 0`. Node IDs and slots are distinct
and contiguous, and they agree with `Testing_Bin/README.md` and with companion memory — three
independent sources. See [`MOTOR_MAP.md`](MOTOR_MAP.md).

The earlier `uavcan_esc_index = 7` anomaly on front-left is gone; it reads `1` in the re-exported set.

### Therefore

The repo set is now a complete and coherent restore point, and §4 says a flash should not wipe
anything. **Two gaps remain that only a live export closes:**

1. **It is unverified against the hardware.** These are the configs the operator states are loaded;
   nobody has read them back off an ESC. A live export is the only thing that proves it.
2. **RL's `foc_motor_r = 0.1988` is an outlier** and RL is the ESC on the bench right now.

**So still export over USB into `configs_live/`**, per ESC, named by physical wheel
(`live_RL_mcconf.xml`, `live_RL_appconf.xml`, …) — cheap, and it turns "should be fine" into
"verified". It also independently confirms the node-ID map while each ESC is on the bench alone.

## 7. Procedure

```bash
cd ~/codex-work/bldc_can

# 0. One-time, after a fresh clone
./setup.sh
sudo apt-get install -y can-utils

# 1. Reboot required once - the overlay is staged in /boot/firmware/config.txt:
#    dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=10000000
#    Backup of the original: /boot/firmware/config.txt.bak-canhat-20260905

# 2. Bring the bus up at 1 Mbit
./bringup.sh

# 3. Prove the bus is real BEFORE trusting any tool. The FC is a live DroneCAN node;
#    if candump is silent, the problem is wiring/termination/crystal, not software.
candump -td can0 | head -20

# 4. Map wheel -> node ID, ONE ESC connected at a time
./venv/bin/python scan.py
./venv/bin/python backup_params.py --label "rear left"

# 5. Back up the full config over USB with VESC Tool -> configs_live/   (CANNOT be done over CAN)

# 6. Flash ONE ESC, then verify before touching the next
./venv/bin/python flash.py --target 13 --bin firmware/60_mk5.bin
./venv/bin/python scan.py
```

**Safety:** rover on stands, unloaded, **disarmed**. The ESC reboots into its bootloader at the end
of the transfer. Never flash with the FC armed.

## 8. Files

| Path | What |
|---|---|
| `setup.sh` | recreates `venv/` (gitignored) |
| `bringup.sh` | `can0` up at 1 Mbit with `restart-ms 100` so bus-off auto-recovers |
| `scan.py` | list DroneCAN nodes — the wheel↔ID mapping tool |
| `backup_params.py` | dump the 8 DroneCAN params per node → `backups/*.json`; `--label` records the map |
| `flash.py` | file server + `BeginFirmwareUpdate`, size pre-flight, live progress |
| `catalog_configs.py` | tabulate `configs_from_repo/` — CAN identity and motor identity |
| `MOTOR_MAP.md` | **wheel ↔ node ID ↔ PX4 slot reference**, with the empirical checklist |
| `configs_from_repo/` | the 8 current XMLs mirrored from `PXLABS_BLDC_VESC6_MK5/Motor_Config_Bldc/` @ `d513e790` |
| `configs_live/` | **real USB backups go here** (empty until exported) |
| `backups/` | `backup_params.py` output |
| `firmware/` | drop `60_mk5.bin` here (bins are gitignored) |
| `evidence/` | the firmware excerpts and the commit patch the claims above rest on |

## 9. Open items

- [ ] **Reboot the companion** so `can0` exists. `vision_streaming` and `rover-ekf-bridge` are
      disabled at boot and will not come back on their own.
- [x] ~~Obtain `60_mk5.bin`~~ — published as `Testing_Bin/60_mk5.bin`, sha256 verified.
      **⛔ It is 524 280 bytes and CANNOT go over DroneCAN — see §5. Flash it over USB.**
- [ ] **Correct `Testing_Bin/README.md` upstream** — it currently offers the DroneCAN path for an
      image that would overwrite the bootloader.
- [ ] **Export live configs over USB** into `configs_live/`, per wheel.
- [ ] Map wheel → node ID empirically, one ESC at a time — **rear left is on the bench now, expect
      node 13**. Record in `MOTOR_MAP.md`.
- [ ] Fix `RC3_TRIM` before the brake feature is meaningful.

## 10. Related

- `../px4_vesc_dronecan_implementation.md` — the PX4↔VESC diagnosis and the Item A–E spec
- `../rc_configuration.md` — RC mapping and the `UAVCAN_EC_MIN/MAX` rationale
- `ros2_ws/docs/setup_manual.md` §A7 — the canonical PX4 parameter changelog
- Firmware: `git@github.com:ArvinVeiyon/PXLABS_BLDC_VESC6_MK5.git`, branch
  `pxlabs-6.06-rover-brake-rc` (`e04bc633`), target commit `a75a0dbf`
