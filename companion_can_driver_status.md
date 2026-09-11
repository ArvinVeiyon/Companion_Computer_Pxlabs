# Companion CAN integration — DROPPED. Driver-level record and revert.

Date: 2026-09-09 | Machine: Vind-Roz companion (RPi5, `vind-roz`) | Status: **DROPPED — time concern**

> **What this file is for.** The MCP2515 CAN-HAT integration on the companion is abandoned. This is
> the only record that survives it: **what got changed on this box below the application level, what
> that cost us, how to undo it, and where the work it was meant to serve actually ended up.**
> Everything else about the hat — three boots of SPI probing, bias sweeps, back-feed analysis — is
> deleted on purpose. Do not reconstruct it.

---

## 1. Why it was dropped

Two independent reasons, either one sufficient:

1. **The hat is hardware-dead on the SPI side.** `can0` never appeared across three boots. Register
   write/read-back: **0 of 140 passed**. `/INT` (GPIO25) and MISO (GPIO9) both float under a bias
   sweep, so nothing on the other end is driving either pin. The reads that did come back were a
   one-transaction lag line — charge held on a floating pin, zero chip contribution. Fixing it means
   a scope, a re-work, or a new hat.
2. **It was never on the critical path.** The firmware it existed to deliver —
   `Testing_Bin/60_mk5.bin` — **must not go over DroneCAN at all**: the app region is 512 KB against
   a 384 KB staging area and `flash_helper.c:181` has no bounds check, so the transfer programs
   131,070 bytes into sector 11, the bootloader, which is never erased. That is a brick recoverable
   only by SWD. USB was always mandatory.

**And the USB route has since finished the job** (§4). The hat would have bought nothing.

⛔ **Do not reopen the MCP2515 debugging.** It is a hardware fault, it is not blocking anything, and
the diagnosis is closed.

---

## 2. What was changed on this companion, below the application level

Everything in this table is **still present on the box** unless the Reverted column says otherwise.

| # | Change | Where | Reverted? |
|---|---|---|---|
| 1 | `dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=10000000` | `/boot/firmware/config.txt` | ✅ **commented out 2026-09-09** — takes effect at the **next boot** |
| 2 | `mcp251x` + `can_dev` kernel modules auto-loaded by that overlay | kernel | ✅ follows #1 at next boot; still loaded in the running kernel |
| 3 | `can-utils` 2023.03-1 installed (`candump`, `cansend`, `ip link` CAN support) | apt | ❌ left in place — harmless, ~1 MB, useful if CAN ever returns |
| 4 | venv at `bldc_can/venv` with `dronecan`, `python-can`, `wrapt`, `packaging` | `~/codex-work/bldc_can/venv` | ❌ left in place — self-contained, touches nothing system-wide |
| 5 | Diagnostic + tooling scripts (`scan.py`, `flash.py`, `backup_params.py`, `bringup.sh`, `diag/*`) | `~/codex-work/bldc_can/` | ❌ kept, see §5 — three of them are **not** CAN work and are in daily use |

**Nothing else was touched.** Specifically: no systemd unit references `can0`, `/etc/modules` is
empty, no udev rule, no network config, no change to any running service.

### 2.1 ⚠️ The one real collateral cost — and it is NOT caused by this work

`/dev/ttyAMA3` (STL-19 lidar) does not exist. SPI0 claims GPIO8/9, so `dtoverlay=uart3-pi5` loses its
pins and never probes.

🔑 **Reverting the CAN overlay will NOT bring `ttyAMA3` back.** The pin conflict comes from
`dtparam=spi=on` at `config.txt:12`, which predates the CAN hat by months. Removing the CAN overlay
is not enough; you would have to disable SPI entirely, and that is a separate decision with its own
blast radius. **Do not remove `dtparam=spi=on` as part of undoing this.**

### 2.2 Revert, completed and remaining

Done 2026-09-09: the overlay line in `/boot/firmware/config.txt` is commented out and reduced to a
two-line pointer at this file. **It applies at the next boot; nothing was rebooted to make it so.**

Full backups if you want the pre-hat file wholesale:

```
/boot/firmware/config.txt.bak-canhat-20260905      # BEFORE the hat - the clean one
/boot/firmware/config.txt.bak-canhat-20260906
/boot/firmware/config.txt.bak-canhat-20260906-10mhz
```

Optional, only if you want the box completely clean:

```bash
printf '1987\n' | sudo -S apt-get remove can-utils     # item 3
rm -rf ~/codex-work/bldc_can/venv                      # item 4
```

Physical: the hat can come off the 40-pin header whenever convenient. **Shut the Pi down first — a
hot re-seat neither re-probes nor can be trusted.**

---

## 3. What we learned that outlives the hat

Worth keeping, because it applies to any future CAN attempt on this vehicle:

* **`can_mode = 1` (UAVCAN) on all four VESCs.** VESC Tool finding nothing on a CAN scan is *correct
  behaviour in that mode*, not a fault. ⛔ Switching it to VESC mode takes DroneCAN — and the rover —
  down.
* **DroneCAN exposes only 8 params per ESC, and no motor tune.** CAN could never have produced a
  complete mcconf backup. **USB is the only complete backup path.**
* **Bus side is correct for the bench:** hat 120 Ω on + one powered VESC = 60 Ω. With all four ESCs
  connected, keep **exactly two** terminators, one at each physical end.
* ⛔ **CAN-side fixes cannot cure an SPI-side failure.** Termination and H/L polarity live downstream
  of the transceiver; the MCP2515 failed before a CAN frame existed. That confusion cost a day.
* ✅ **You do not need a CAN link to diagnose the ESCs.** `esc_status.esc_errorcount` carries the live
  VESC fault code, and `input_rc` / `manual_control_setpoint` / `esc_status` are all on DDS ⇒ full ESC
  diagnosis with **no VESC Tool and no `mavlink_shell`**. Codes: 0 NONE · 1 OVER_VOLTAGE ·
  2 UNDER_VOLTAGE · 3 DRV · 4 ABS_OVER_CURRENT · 5 OVER_TEMP_FET · 6 OVER_TEMP_MOTOR ·
  7 GATE_DRV_OV · 8 GATE_DRV_UV · 9 MCU_UV · 10 WATCHDOG_RESET.

---

## 4. Current status of the driver-level upgrade the hat was meant to serve

**The upgrade is DONE, over USB, without the hat.**

| Layer | State |
|---|---|
| VESC ESC firmware | ✅ **All four wheels flashed with `a75a0dbf`** (branch `pxlabs-6.06-rover-brake-rc`) **and brake-tested — operator, 2026-09-09.** RL was the 09-07 pilot. |
| PX4 side | ✅ **Complete and saved to flash 2026-09-07**, all four params read back after the save returned `MAV_RESULT_ACCEPTED`. |
| Node ↔ wheel map | FR = 10 (inverted) · FL = 11 · RR = 12 · RL = 13 |
| Rollback | Tag **`v6.06.0-pxlabs-rover-r1`**, over **USB**, per ESC. 🔴 **With all four on branch firmware there is no known-good ESC left to diff against — the single-ESC rollback is gone.** |

Detail, traps and the open items live in [`bldc_can/RESUME.md`](bldc_can/RESUME.md). The short form:

* The RC brake is **regenerative** (`CONTROL_MODE_CURRENT_BRAKE`), so it makes torque by opposing
  rotation. ⛔ **A hand test cannot measure it.** Full stick and low stick both feel like nothing at
  hand-turn speed, and that is correct.
* A **holding** brake exists in the same firmware (`mc_interface_set_handbrake_rel`,
  `CONTROL_MODE_HANDBRAKE`) and is a one-line swap at `canard_driver.c:747`. Undecided.
* Still open: proportionality has never been observed on `/fmu/out/manual_control_setpoint`; nothing
  has been measured **at speed on the floor**; and the collision reflex still only **zeroes the
  setpoint** — it does not command the brake. That last one is the reason this work exists.

---

## 5. ⛔ Do not delete these three scripts when cleaning up

They were written for the CAN effort but are **general FC tooling and are in use**:

| Script | What it does | Why it must survive |
|---|---|---|
| `bldc_can/diag/set_param_int.py` | writes INT32 PX4 params over MAVLink | 🔴 `ros2_ws/tools/set_param.py` **cannot write INT32 at all** — it always sends REAL32 and PX4 refuses the type mismatch silently. This is the only INT32 writer we have. |
| `bldc_can/diag/param_save.py` | `MAV_CMD_PREFLIGHT_STORAGE` p1=1 | the save step; `set_param.py` writes are RAM-only. Avoids `mavlink_shell`, which wedged the GCS link on 08-16. |
| `bldc_can/diag/fc_reboot.py` | FC reboot over DDS (`VehicleCommand` 246) | refuses if ARMED; the safe reboot path when MAVLink is unavailable. |

The genuinely CAN-only ones — `scan.py`, `bringup.sh`, `diag/spi_probe.py`, `diag/int_probe.py`,
`diag/wrb_probe.py` — can go whenever, but they cost nothing and `flash.py` still carries the
**guard that refuses `60_mk5.bin`**, which is worth keeping around on principle.
