---
name: vesc-can-flashing
description: "RC brake on the 4 VESCs - DONE and bench-tested 09-09. Companion CAN integration DROPPED. Pointers to the three docs that hold the detail."
metadata:
  node_type: memory
  type: project
  originSessionId: b7052c6e-f42f-48fd-9d7e-c0dffff0ecc5
  modified: 2026-09-09T17:24:47.147Z
---

**POINTER FILE. The detail lives in three documents — open them, do not work from this summary.**

📕 **`~/codex-work/bldc_can/RESUME.md`** — the live state of the RC brake: what is done, the traps,
the open items. **Open this first.**
📗 **`~/codex-work/bldc_can/evidence/brake_floor_test_20260909.md`** — the LOADED floor run: m/s²,
stopping distance, and how the conditions were measured. (`brake_bench_test_20260909.md` is run 1,
motor-side; its filename says "bench" and that is WRONG — it was loaded too, see its header.)
📘 **`~/codex-work/companion_can_driver_status.md`** — what the dropped CAN work changed on this
companion at driver level, and how to finish reverting it.
📐 **`~/codex-work/rc_configuration.md` §6** — the step-by-step procedure for configuring PX4 RC on
this rover. Follow it rather than re-deriving.

## Status, 2026-09-09

✅ **RC brake DONE: all four ESCs on `a75a0dbf`, PX4 side saved to flash, and DRIVEN ON THE FLOOR
UNDER LOAD with the conditions MEASURED — 0.69 m/s², stops in 0.30–0.50 m from ~0.8 m/s.**
Proportionality confirmed, `esc_errorcount` clean on all four under load.
⚠️ **The coast baseline is n=2 and neither segment ran to a stop ⇒ every ratio derived from it
(3.4×, "saves 1.4 m") is PROVISIONAL.** One clean coast-to-stop closes it.
🅿️ **The companion CAN-HAT integration is DROPPED (time concern).** Hardware-dead on the SPI side,
overlay disabled 09-09. ⛔ **Do not reopen the MCP2515 debugging and do not re-propose SocketCAN.**

## The rules that survive — these are the ones that cost real time

🔴 **`Testing_Bin/60_mk5.bin` MUST BE FLASHED OVER USB, NEVER DRONECAN** — it overflows the 384 KB
staging area into the bootloader sector, which is never erased ⇒ **brick, SWD-only recovery**.
`flash.py` refuses it; **never work around that guard.**
🔴 **VESC Tool over SocketCAN CANNOT WORK HERE** — `can_mode=1` (UAVCAN) means a CAN scan finding
nothing is *correct behaviour*, not a fault. Switching it takes DroneCAN and the rover down.
🔑 **`esc_current` IS THE LOADED/UNLOADED RULER** — ±1 A at rest vs −12…+8 A moving. **`/odom`
DRIFTS AT STANDSTILL** (~0.38 m/min at 0 rpm, the camera-gyro term), so corroborate with the IMU.
🔴 **A HAND TEST CANNOT MEASURE THIS BRAKE.** It is regenerative (`CONTROL_MODE_CURRENT_BRAKE`), so
torque scales with back-EMF — at hand-turn speed full stick and low stick are both ≈ nothing.
🔴 **`set_param.py` CANNOT WRITE INT32 PARAMS** — it always sends REAL32, PX4 refuses the type
mismatch and writes **nothing**, silently. Use `bldc_can/diag/set_param_int.py`. Save =
`diag/param_save.py`; FC reboot over DDS = `diag/fc_reboot.py`.
🔴 **A QGC RC CALIBRATION REWRITES TRIM** ⇒ `RC3_TRIM` can land back on `RC3_MIN` = 1001, which
commands **50 % brake** the instant the stick leaves the stop. **Re-check it after every calibration.**
⚠️ **`rc_configuration.md` §2.1 ("TRIM==MIN is a QGC artefact, don't fix it") IS THROTTLE-ONLY** —
`rc_update.cpp:172` scopes it to `FUNCTION_THROTTLE`. Never generalise it to another channel.
⛔ **DO NOT "fix" `si_motor_poles`** (14 on all four) — it is a linked pair with `erpm_to_ms 0.003900`
and changing it in VESC Tool **silently halves `/odom`**, a safety input.
⛔ **DO NOT copy the motor slots' `110/8082` onto the brake slot** — it is unipolar; `1/8191` is right.
⛔ **NEVER restore from `vesc_mcconf_Right_Front.xml`** — `foc_motor_flux_linkage 1.46287`, ~130× the
family, a failed detection.

## Still open

🔴 **Rollback is gone as a bench comparison** — all four are on branch firmware. Rollback = tag
`v6.06.0-pxlabs-rover-r1`, over USB, per ESC.
⏭ **ONE CLEAN COAST-TO-STOP** — the cheapest open item; every ratio above depends on it.
⏭ **The collision reflex STILL ONLY ZEROES THE SETPOINT — it never commands the brake.** That unmade
change is the reason the feature exists, and 0.69 m/s² braked vs 0.20 coasting is the case for it.
⏭ **Reconcile the −12.06 A regen peak against the repo `l_in_current_min` of −5 A** (live mcconf
differs, or the cap is per-motor?). Needs USB.
⏭ Never read off live hardware: `UAVCAN_EC_FAIL5`, `uavcan_raw_mode`, and any post-flash firmware
hash. Disarm / RC-loss brake-off is correct by construction, **untested**.

See also [[rover-odometry]], [[uart-map]], [[this-machine]].
