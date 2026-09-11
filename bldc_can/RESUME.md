# RESUME — RC brake on the rover VESCs

Last updated 2026-09-09. Read this first, then [`README.md`](README.md) for the why and
[`MOTOR_MAP.md`](MOTOR_MAP.md) for the map.

> 🅿️ **The companion CAN-HAT integration is DROPPED (time concern) and every trace of its debugging
> has been deleted from this file.** What was changed on the companion at driver level, why it was
> abandoned, and how to finish reverting it now live in **one** place:
> [`../companion_can_driver_status.md`](../companion_can_driver_status.md).
> ⛔ **Do not reopen the MCP2515 work and do not reconstruct the diagnosis.** It was hardware, it
> never blocked the flash, and USB was always the mandatory path anyway.

---

## Where things stand

| | |
|---|---|
| ESC firmware | ✅ **All four wheels on `a75a0dbf`** (branch `pxlabs-6.06-rover-brake-rc`), **brake-tested and MEASURED loaded on the floor, 2026-09-09** |
| PX4 side | ✅ **Complete and saved to flash 2026-09-07**, every value read back after the save |
| Node ↔ wheel | FR = 10 (inverted) · FL = 11 · RR = 12 · RL = 13 |
| Flash path | **USB only** — see the hard stop below |
| Rollback | tag **`v6.06.0-pxlabs-rover-r1`**, over USB, per ESC |
| Tested on the floor? | ✅ **YES — driven, loaded, 2026-09-09. Stops in 0.30–0.50 m from ~0.8 m/s.** |

## ⛔ The one thing you must not forget

**`Testing_Bin/60_mk5.bin` (524,280 B) MUST NOT be flashed over DroneCAN.** The app region is 512 KB
but the DroneCAN staging area is only 384 KB, and `flash_helper.c:181` has no bounds check, so the
transfer programs 131,070 bytes into sector 11 — the bootloader, which is never erased. **Result:
brick, recoverable only by SWD/ST-Link.** Flash over **USB**. `flash.py` refuses the image; do not
work around that guard. Full derivation in `README.md` §5.

⚠️ `Testing_Bin/README.md` upstream still recommends the DroneCAN path and is **wrong**.

---

## ✅ 2026-09-09 — all four flashed and brake-tested (operator report)

RL was the 09-07 pilot; FR, FL and RR have since been flashed with `a75a0dbf` and exercised.

**What this changes:**

* ⛔ **THE SINGLE-ESC ROLLBACK IS GONE.** With all four on branch firmware there is no known-good ESC
  left to compare against. Rollback is now the tag, over USB, per ESC — nothing falls back on its own.
* ✅ The chain (ch3 → `aux1` → `UAVCAN_EC_FUNC5` slot 5 → RawCommand index 4) is live on every wheel,
  so the old "inert on the bus until an ESC runs `a75a0dbf`" caveat is **withdrawn**.

**What it does not change — do not assume these, ask:**

* ⚠️ Whether live mcconf backups were exported into `configs_live/` **before** each flash. That window
  has now closed for three of the four.
* ⚠️ What commit VESC Tool reported after each flash. No readback hash was recorded for any wheel.

## ✅ 2026-09-09 — TWO RECORDED RUNS, BOTH LOADED ON THE FLOOR

**Run 1** (303 s, ~30,000 `esc_status` msgs) — motor-side: proportionality, `RC3_*` geometry,
errorcount, per-wheel rpm/s. 📄 [`evidence/brake_bench_test_20260909.md`](evidence/brake_bench_test_20260909.md)
· CSV `~/brake_test_20260909.csv` · `diag/brake_test_record.py` + `diag/brake_test_analyse.py`

**Run 2** (115.8 s, six topics) — **vehicle-side: deceleration in m/s² and stopping distance.**
📄 [`evidence/brake_floor_test_20260909.md`](evidence/brake_floor_test_20260909.md)
· CSV `~/brake_run_20260909_floor2.csv` · `diag/brake_run_record.py` + `diag/brake_run_analyse.py`

🔴 **BOTH RUNS WERE ON THE FLOOR, LOADED.** Run 1 was recorded and written up as a bench/stands test
— **that was my assumption, never observed, and wrong.** Run 2 measured the conditions directly:
`esc_current` −12 … +8 A while moving against ±1 A of noise at rest, with body motion witnessed by
`/odom` and the IMU. ⛔ **The full history of that error is kept in the run-1 evidence file on
purpose — read it before trusting any conditions label.**

| Measured, run 2 (loaded) | |
|---|---|
| **Braked deceleration** | **0.69 m/s² median**, 0.94 peak (n=9) |
| **Stopping distance** | **0.30–0.50 m from ~0.8 m/s** |
| Coasting | 0.20 m/s² ⚠️ **n=2, neither ran to a stop — PROVISIONAL** |
| Brake vs coast | ≈3.4×; from 0.9 m/s saves ~1.4 m ⚠️ inherits the coast weakness |
| `esc_errorcount` | 0 = NONE on all four, under load |

| Measured, run 1 (motor-side) | |
|---|---|
| Proportionality | ✅ **Observed for the first time.** Steady hold at ch3 1212 µs → `aux1` −0.5657 measured vs −0.5663 predicted |
| `RC3_TRIM` | ✅ **Still 1487.5** (solved two ways, median 1487.0 over 118 samples) — **the QGC recalibration hazard has not fired** |
| `RC3_MAX` / `REV` | ≈ **1973 µs**, saturates from 1969 µs; **not reversed** — ⚠️ *solved from data, not read* |
| Braking, all four | ✅ 411–432 rpm/s median. ~340 rpm → 0 in ≈1.0 s fwd; −413 → −126 rpm in ≈0.6 s rev |
| vs coasting | **≈5× free-spin drag** (RR 429 vs 78 · RL 411 vs 85) |

⛔ **Do not quote the FR/FL coast figures** — FL's rpm telemetry throws single-sample spikes
(375 → 1028 → 562 in 0.4 s while the others read 235 → 346 → 347). RR and RL are the clean pair.
🔑 **Scored naively on per-sample pairs the same data says the brake is 1.1× coast — an artifact.**
You must gate on throttle-neutral and score **sustained runs**. If a reproduction gets ~1×, that is why.

⚠️ **MAVLink was DOWN for both runs** (`mavlink-routerd` up, no heartbeat on `tcp:5760`, before and
after an FC reboot) ⇒ **no PX4 param could be read or written.** Everything above is DDS or solved
from the data — which is also why `RC3_MAX`/`REV` are marked solved rather than read.

⚠️ **`/odom` DRIFTS AT STANDSTILL** — ~0.38 m of phantom travel in a minute with all four wheels at
0 rpm (the camera-gyro dead-reckoning term). Use it for **change during a run**, corroborated by the
IMU. **It is not a ruler.**

---

## ✅ The PX4 side of the brake — done and saved, 2026-09-07

**All four values were read back off the FC after `MAV_CMD_PREFLIGHT_STORAGE` (save) returned
`MAV_RESULT_ACCEPTED`.** The FC had been rebooted immediately before, so RAM was clean and the save
committed only these changes.

| Param | Was | Now | Why |
|---|---|---|---|
| `RC3_TRIM` | 1001.0 | **1487.5** | the blocker — trim was equal to `RC3_MIN` |
| `RC_MAP_AUX1` | 0 | **3** | ch3 → `manual_control_setpoint.aux1` (operator set this in QGC) |
| `UAVCAN_EC_FUNC5` | 0 | **407** | `RC_AUX1` onto ESC slot 5 = RawCommand index 4 = the brake slot |
| `UAVCAN_EC_MIN5` / `MAX5` | 1 / 8191 | **unchanged — deliberate** | see the traps |

✅ **ALL READ OFF THE FC 2026-09-10, once MAVLink came back** (it was down 09-09 across an FC reboot,
then returned on its own; cause never identified, so expect it to recur):

| Param | Reads |
|---|---|
| `RC3_MIN` / `RC3_TRIM` / `RC3_MAX` / `RC3_REV` | 1001.0 · **1487.5** · **1974.0** · 1.0 (not reversed) |
| `RC_MAP_AUX1` · `UAVCAN_EC_FUNC5` | 3 · 407 |
| `UAVCAN_EC_MIN5` / `MAX5` / **`FAIL5`** | 1 · 8191 · **0** |

🔑 **The solved values were right.** From logged `input_rc` + `manual_control_setpoint` alone I had
solved `RC3_TRIM` = 1487.0 median (1487.5 from a steady hold) and `RC3_MAX` ≈ 1973 — the FC says
**1487.5 and 1974.0**, one microsecond out. **Solving PX4's piecewise map is a sound fallback when
the link is down.**

⛔ **`RC3_DZ` and `RC2_DZ` DO NOT EXIST on this firmware** — settled 2026-09-10 with a control: a
deliberately fake name returns the identical `<no reply>` while a known-good param reads instantly on
the same link. **`set_param.py`'s "wrong name, or the link is busy" cannot tell those apart — run the
fake-name control rather than recording "unknown".**

**The step-by-step procedure for configuring PX4 RC from scratch on this vehicle** —
calibration, channel map, the brake channel, save, and verification — is
[`../rc_configuration.md`](../rc_configuration.md) **§6**. Use it rather than re-deriving.

### Why `RC3_TRIM == RC3_MIN` really commanded ~50 % brake

Derived from source, not inferred:

* `interpolateNXY` (`Functions.hpp:201`) with `x = {min, trim, max}` and `min == trim` returns
  **−1.0 at exactly 1001** and **~0.0 at 1002** — a one-microsecond discontinuity.
* `output_limit_calc_single` (`mixer_module.cpp:568`) maps a non-servo function −1…+1 linearly onto
  `MIN…MAX`, so norm 0 → **4096 → `brake_rel` 50 %**.

With `RC3_TRIM = 1487.5` the channel is continuous: ch3 at its 1001 stop → **−1.0 → slot 5 = 1 →
`brake_rel` 0.012 %**, below the firmware's 0.05 threshold ⇒ **brake off**. Mid-travel → 50 %,
top → 100 %, which is exactly the proportional behaviour the Item C spec describes.

### ⛔ Traps this exposed

1. 🔴 **`rc_configuration.md` §2.1 — "`RC2_TRIM == RC2_MIN` is a QGC artefact, PX4 corrects it, do not
   fix it" — IS THROTTLE-ONLY.** `rc_update.cpp:172` scopes that re-centring to
   `_rc.function[FUNCTION_THROTTLE]`. **It never applied to ch3, which is why the bug was real.**
   Do not generalise §2.1 to any other channel.
2. 🔴 **A QGC RC calibration REWRITES TRIM.** If ch3 is ever recalibrated, `RC3_TRIM` can land back on
   1001 and **the 50 % brake bug returns**. Re-read `RC3_TRIM` after any calibration, every time.
3. 🔴 **`ros2_ws/tools/set_param.py` CANNOT WRITE INT32 PARAMS.** It always sends
   `MAV_PARAM_TYPE_REAL32`, and `mavlink_parameters.cpp:129-131` refuses any set whose MAVLink type
   does not match the onboard type — it logs "param types mismatch" and writes **nothing**. PX4 then
   does `param_set(param, &set.param_value)` on the **raw 4 bytes**, so an INT32 must be sent as the
   integer's **bit pattern** in the float field. `RC_MAP_AUX1` and `UAVCAN_EC_FUNC5` are both INT32
   and needed a separate writer — **`diag/set_param_int.py`**. `set_param.py` is fine for floats only.
4. ⛔ **DO NOT copy the `110 / 8082` motor convention onto `MIN5`/`MAX5`.** That pair exists so the
   four *motor* slots get a neutral of exactly 4096 and dodge the VESC's `raw < 100` disarm guard. The
   brake slot is unipolar: its minimum must mean *off*, and the defaults `1 / 8191` give 0.012 %.
5. ⚠️ **Set `RC_MAP_AUX1` BEFORE `UAVCAN_EC_FUNC5`.** With slot 5 assigned while AUX1 is unmapped,
   `aux1` reads 0 → mid-scale → **50 % brake demand on the bus**.
6. 🔴 **DO NOT "fix" `si_motor_poles`.** It is `14` on all four and is a **LINKED PAIR** with
   `erpm_to_ms = 0.003900`. Changing poles in VESC Tool **silently halves `/odom`** — and odometry is
   a safety input. The scale is CLOSED and tape-validated.
7. ⚠️ **DO NOT change `can_mode`** (it is `1` = UAVCAN on all four). VESC Tool finding nothing on a CAN
   scan is correct behaviour in that mode. Switching it to VESC takes DroneCAN — and the rover — down.
8. ⛔ **NEVER restore from `vesc_mcconf_Right_Front.xml`** — its `foc_motor_flux_linkage = 1.46287` is
   ~130× the family, a failed detection.

---

## 🔑 The brake is REGENERATIVE — it does nothing at standstill, and that is not a fault

Two operator observations from the 09-07 RL test, **both expected**:

* **"The brake applies immediately whatever the throttle is doing."** Correct — `canard_driver.c:746`
  tests brake first, so brake wins over throttle.
* **"I can still turn the motor easily by hand, and full stick feels no different from low stick."**
  **Also correct, and not a defect.** `mc_interface_set_brake_current_rel` →
  `mcpwm_foc_set_brake_current` → **`CONTROL_MODE_CURRENT_BRAKE`** (`mcpwm_foc.c:832`). That brake
  makes its torque by opposing rotation, so it scales with back-EMF — **at hand-turn speed 100 % and
  10 % both come out as ≈ nothing.**

⛔ **A HAND TEST CANNOT MEASURE THIS BRAKE. Test it against a spinning wheel or it tells you nothing.**

⏭ **If a HOLDING brake is wanted, the firmware already has one:** `mc_interface_set_handbrake_rel` →
`CONTROL_MODE_HANDBRAKE`, *"open loop current vector to brake motor"* (`mc_interface.c:757`), **same
`val × |lo_current_min|` scaling**, and it holds at zero speed. One-line swap at
`canard_driver.c:747`. The better answer is probably a **hybrid** — handbrake below some ERPM, regen
above — since regen is the right thing for cutting the collision-reflex coast while moving.

### How much brake current you actually get

`brake_rel × |lo_current_min|`, where **`lo_current_min` is the runtime-scaled `l_current_min`** —
so **authority fades silently as the motor heats or the pack nears full**. From the repo configs:
`l_current_min` **−25 A** (LF −25.8) · `l_in_current_min` **−5 A** · `l_abs_current_max` 35 ·
`cc_min_current` 0.05 (the engage floor). 🔴 **The −5 A battery regen cap is probably what really
binds, not the 25 A.** ⚠️ These are the repo XMLs — **never verified against the live ESCs.**

⛔ **Do not tune `l_max_erpm_fbrake` (300) or `l_max_erpm_fbrake_cc` (1500) chasing this** — every use
is in `mcpwm.c`, the **BLDC** path, and `motor_type = 2` = **FOC**. They are dead params here.

🔑 **A SECOND, UNRELATED BRAKE IS ALREADY RUNNING ON ALL FOUR: `timeout_brake_current = 2 A` at
`timeout_msec = 300`** (`timeout.c:225-233`) — a flat, absolute 2 A applied when no CAN command
arrives for 300 ms, or the kill switch trips. **It is not a weak version of the RC brake; it is a
different mechanism.** So "coast only" was never quite true. ⚠️ All four repo appconfs have
`uavcan_raw_mode = 0` (`CURRENT`) — lower stick is **reverse**, not brake — but that has **never been
read back off a flashed unit.** If lower-stick braking is ever seen, the param has been changed live.

### Failsafe — correct by construction, NOT tested

Brake-off on disarm and on RC loss follows from: PX4 has no disarmed parameter, so `_disarmed_value`
stays **0** and is sent on every slot when disarmed, which on the brake slot is under the 0.05
threshold ⇒ off; and `NAV_RCL_ACT = 6` disarms on RC loss. **Nobody has exercised either. Do not
record it as verified.**

---

## ⏭ Open items

- [x] ~~Proportionality~~ — **observed 2026-09-09**, `aux1` continuous across the travel.
- [x] ~~`esc_status.esc_errorcount` during braking~~ — **sampled 2026-09-09, clean on all four.**
- [x] ~~Fix MAVLink~~ — **back up 2026-09-10, on its own.** ⚠️ Cause never found; may recur.
- [x] ~~`UAVCAN_EC_FAIL5`~~ — **read 2026-09-10: 0.**
- [ ] **`uavcan_raw_mode` — still never read off live hardware.** Needs USB + VESC Tool; the CAN path
      is gone. Repo appconfs say 0 (`CURRENT`) on all four, unverified.
- [x] ~~Measure the brake at speed on the floor~~ — **done 2026-09-09: 0.69 m/s², stops in
      0.30–0.50 m from ~0.8 m/s.** The room was never the blocker it was recorded as.
- [ ] 🔴 **ONE CLEAN COAST-TO-STOP.** The cheapest open item and the weakest link in every ratio
      quoted above: coast is n=2, both segments 0.4 s, neither ran to a stop. Spin up, release
      throttle to neutral with ch3 at the bottom stop, let it roll out completely, touch nothing.
- [ ] ⚠️ **Reconcile the −12.06 A regen peak against the repo `l_in_current_min` of −5 A.** Either
      the live mcconf differs from the repo XMLs or the cap is per-motor, not pack-side. Needs USB.
- [ ] **The collision reflex still only ZEROES THE SETPOINT — it does not command the brake.** Wiring
      it up is a separate, unmade change, and it is the reason this work exists.
- [ ] Decide regen vs handbrake vs hybrid at `canard_driver.c:747`.
- [ ] Export live configs over USB into `configs_live/`, per wheel. CAN exposed only 8 params and no
      motor tune, so USB is the only complete backup. RL's `foc_motor_r = 0.1988` is an outlier vs
      0.44–0.56 on the other three and is worth confirming.
- [ ] Correct `Testing_Bin/README.md` upstream — it still recommends the DroneCAN path.
- [x] ~~Fix `RC3_TRIM == RC3_MIN`~~ — done 2026-09-07 with `RC_MAP_AUX1` and `UAVCAN_EC_FUNC5`, saved.
- [x] ~~Flash one ESC over USB, verify, then the rest~~ — all four, 2026-09-09.

---

## Diagnosing the ESCs without VESC Tool

✅ **On DDS:** `/fmu/out/input_rc` · `/fmu/out/manual_control_setpoint` · `/fmu/out/esc_status`
❌ **Not on DDS:** `rc_channels` · `actuator_outputs` · `actuator_motors` · `vehicle_status`

`esc_status.esc_errorcount` carries the **live VESC fault code** (the VESC fills it from
`mc_interface_get_fault()`): `0`=NONE `1`=OVER_VOLTAGE `2`=UNDER_VOLTAGE `3`=DRV `4`=ABS_OVER_CURRENT
`5`=OVER_TEMP_FET `6`=OVER_TEMP_MOTOR `7`=GATE_DRV_OV `8`=GATE_DRV_UV `9`=MCU_UV `10`=WATCHDOG_RESET.

⛔ **Avoid `mavlink_shell.py`** — one session per FC boot, and it killed the GCS MAVLink link on 08-16.
⛔ **Never read a quiet topic as evidence.** Prove a non-zero baseline first.

## Tooling on the companion

| Script | Use |
|---|---|
| `~/ros2_ws/tools/set_param.py NAME [value]` | read/write **FLOAT** PX4 params over MAVLink `tcp:5760`. **RAM only.** |
| `diag/set_param_int.py NAME [value]` | the **INT32** writer, with readback. `set_param.py` cannot do this. |
| `diag/param_save.py` | `MAV_CMD_PREFLIGHT_STORAGE` p1=1 — the save step. Saves **everything in RAM**, so run it only when RAM is known-clean. |
| `diag/fc_reboot.py` | FC reboot over **DDS** (`VehicleCommand` 246); refuses if ARMED. |
| `flash.py` | carries the guard that **refuses `60_mk5.bin`**. Do not work around it. |
