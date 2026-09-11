# RC Input & UAVCAN ESC Output — measured configuration

Date: 2026-09-04 | Vehicle: Vind-Roz rover (4WD skid-steer) | FC: PX4 pxlabs-v1.17.0-2.1.0
Status: **all values below were READ FROM THE FC or MEASURED LIVE**, not copied from a snapshot.

> 🔑 **Read the FC, never a snapshot.** `python3 ~/ros2_ws/tools/set_param.py NAME` reads any parameter
> over MAVLink (`PARAM_REQUEST_READ`, `tcp:5760`). It does **not** wedge the link, unlike
> `mavlink_shell.py`. Writes are **RAM ONLY** until `param save`.

---

## 1. RC channel map

| Param | Value | Meaning |
|---|---|---|
| `RC_MAP_THROTTLE` | **2** | ch2 = forward/reverse throttle |
| `RC_MAP_FLTMODE` | 6 | flight-mode selector |
| `RC_MAP_ARM_SW` | 5 | arm switch |
| `RC_MAP_KILL_SW` | 12 | kill switch — ⚠️ **docs elsewhere say "ch8"; the PARAM is right, fix the docs** |
| `NAV_RCL_ACT` | 6 | disarm on RC loss |

Observed stick assignment: **ch2 = throttle, ch4 = steering, ch3 unused** (static 1001), ch1 static 1500.
**ch10 is the companion power channel** — 2014 = reboot, 1514 (middle) = shutdown, 1011 (down) = safe.
🔑 **Check ch10 before debugging any companion restart.** → `project_rc_ch10_reboots_companion`

## 2. Channel 2 (throttle) calibration — as read from the FC

| Param | Value |
|---|---|
| `RC2_MIN` | 1001.0 |
| `RC2_MAX` | **1986.0** |
| `RC2_TRIM` | 1001.0 |
| `RC2_REV` | 1.0 (not reversed) |
| `RC2_DZ` | ✅ **DOES NOT EXIST on this firmware** — settled 2026-09-10 |

### 2.1 🔑 `RC2_TRIM == RC2_MIN` is a QGC artefact, and PX4 corrects it
Do not "fix" this parameter. `rc_update.cpp` **re-centres trim to `(MIN+MAX)/2` = 1493** whenever
`TRIM == MIN`, which is the standard QGC bipolar-calibration artefact. Verified arithmetically against
live data at every intermediate stick position:

| stick | ch2 (µs) | predicted `(ch2−1493)/493` | measured `manual_control_setpoint.throttle` |
|---|---|---|---|
| neutral | 1500 | +0.014 | **+0.0142** |
| ~50% | 1748 | +0.517 | **+0.5193** |
| ~90% | 1951 | +0.929 | **+0.9290** |
| full fwd | 2000 | +1.028 | **+1.0000** (clamped) |
| full rev | 1001 | −0.998 | **−1.0000** (clamped) |

### 2.1b ✅ `RCn_DZ` does not exist here — settled 2026-09-10, with a control

`RC2_DZ` and `RC3_DZ` both return `<no reply>` **on a demonstrably healthy link** — eleven other
params read instantly in the same batch. 🔑 **The control is what makes this conclusive:** a
deliberately fake name, `RC3_NOSUCHPARAM`, produces the *identical* `<no reply>`, and `RC3_REV` read
back correctly immediately afterwards. ⇒ the response means **"no such parameter"**, not "link busy".

⛔ **Do not record these as "unknown" again, and do not keep retrying them.** `set_param.py`'s own
message ("wrong name, or the link is busy") cannot tell the two apart — **run the fake-name control
whenever you see it.**

### 2.2 ⚠️ Full stick OVERSHOOTS the calibrated range
**ch2 reads 2000 at full forward against `RC2_MAX` = 1986 — a +14 µs overshoot.** PX4 clamps the
normalised value to exactly ±1.0000, so it is harmless, but it means **full stick is a SATURATED
command**: the FMU emits its true maximum. Re-running RC calibration in QGC would widen `RC2_MAX` to
~2000 and remove the saturation, but nothing currently depends on it.

---

## 3. UAVCAN ESC output — and the full-reverse fault this configuration caused

| Param | ch1 | ch2 | ch3 | ch4 |
|---|---|---|---|---|
| `UAVCAN_EC_FUNC` | 101 | 102 | 101 | 102 |
| `UAVCAN_EC_MIN` | **110** | **110** | **110** | **110** |
| `UAVCAN_EC_MAX` | **8082** | **8082** | **8082** | **8082** |

`UAVCAN_EC_FAIL1` = −1 · `UAVCAN_ENABLE` = 3 · `UAVCAN_BITRATE` = 1000000 · `CA_R_REV` = 3 ·
`CA_AIRFRAME` = 6.
⛔ **`UAVCAN_EC_DIS1` DOES NOT EXIST** — PX4's UAVCAN_EC output block defines only min/max/failsafe.
Do not hunt for it.

### 3.1 🔴 Why MIN is 110 and MAX is 8082 — DO NOT "TIDY" THESE BACK TO 10 / 8191
**Original values 10 / 8191 made full reverse stop all four wheels.** PX4 has no disarmed parameter, so
`_disarmed_value` stays **0** and is sent whenever disarmed; the VESC fork therefore guards
**`if (raw < 100) stop`**. `MIN = 10` at full reverse also falls under that guard, and **the guard cannot
tell disarmed(0) from full-reverse(10)**. Forward (8191) is at the far end of the scale, which is why the
fault was **reverse-only**.

**The fix is deliberately symmetric:** `110 + 8082 = 8192`, so neutral lands on **exactly 4096** — the
value the VESC assumes. Raising MIN alone would put neutral at 4150 (+1.3%), which is inside the VESC's
±2% deadband but consumes 65% of it; the symmetric form removes the deadband dependence entirely.
Cost: ~1.3% of range at each end, invisible because PX4 already clamps at full stick.
⚠️ **Disarmed still sends 0, so the disarmed motor stop is unaffected.**

### 3.2 ⏭ The proper long-term fix is on the VESC side (NOT done)
The VESC should stop inferring arming from the command value and instead subscribe to
**`safety.ArmingStatus`, which PX4 already broadcasts**, after which the `<100` band can be deleted
entirely and the full range recovered at both ends.

🔴 **ORDERING HAZARD:** that `<100` band is **currently what stops the motors when disarmed**. Deleting
it before the arming subscription works would **remove the disarmed motor stop**. Do not reorder these.

Full evidence and the diagnosis method: §4 and §5 below, and the firmware work items (PX4 disarmed
param · VESC `ArmingStatus` · brake from RC · guard deletion) in
[`px4_vesc_dronecan_implementation.md`](px4_vesc_dronecan_implementation.md) §4.
⚠️ **The canonical parameter changelog is `setup_manual.md` §A7, which lives in the `ros2_ws` repo**
(`ArvinVeiyon/ros2_ws`, `docs/setup_manual.md`) — cross-repo, so there is no link here on purpose.

---

## 4. Verified behaviour (armed, on stands, 2026-09-04)

| stick | ch2 | throttle | rpm (addr 10/11/12/13) | current |
|---|---|---|---|---|
| neutral | 1500 | +0.0142 | 0 / 0 / 0 / 0 | 0.00 A |
| full forward | 2000 | +1.0000 | +1511 / +1515 / +1580 / +1534 | 3.4–4.7 A |
| full reverse **(after fix)** | 1001 | −1.0000 | −1514 / −1513 / −1568 / −1534 | 3.1–4.5 A |
| full reverse *(before fix)* | 1001 | −1.0000 | **0 / 0 / 0 / 0** | **0.00 A** |

`esc_errorcount` was **0 = NONE** on all four ESCs in every state, and pack voltage held 25.0–25.4 V
throughout. ⚠️ **Verified on stands, unloaded — not yet driven on the ground.**

---

## 5. How to re-measure any of this — no MAVLink shell required

✅ **On DDS:** `/fmu/out/input_rc` · `/fmu/out/manual_control_setpoint` · `/fmu/out/esc_status`
❌ **Not on DDS:** `rc_channels` · `actuator_outputs` · `actuator_motors` · `vehicle_status`

The entire diagnosis above was done over DDS. ⛔ **Avoid `mavlink_shell.py`** — one session per FC boot,
and it killed the GCS MAVLink link on 08-16.

🔑 **`esc_status.esc_errorcount` carries the live VESC fault code** (the VESC fills it from
`mc_interface_get_fault()`), so **fault diagnosis needs no VESC Tool**:
`0`=NONE `1`=OVER_VOLTAGE `2`=UNDER_VOLTAGE `3`=DRV `4`=ABS_OVER_CURRENT `5`=OVER_TEMP_FET
`6`=OVER_TEMP_MOTOR `7`=GATE_DRV_OV `8`=GATE_DRV_UV `9`=MCU_UV `10`=WATCHDOG_RESET.

⚠️ **Any rclpy sampler needs a ~2.5 s DDS discovery warm-up before it starts counting.** A 3 s window
returned **zero samples on healthy topics** and looked exactly like a dead link. **Always prove a
non-zero baseline** (`esc_status` runs ~100 Hz) before believing silence.

✅ **2026-09-09: the ESC address ↔ wheel map is now exercised against physically turning wheels** —
all four addresses (10/11/12/13) responded to throttle and to the brake channel simultaneously in the
brake bench test. ⚠️ **That proves all four addresses are live and independently controllable; it does
NOT prove which address is bolted to which corner.** The per-corner identity (10 = FR inverted,
11 = FL, 12 = RR, 13 = RL) still rests on the config table, not on a one-wheel-at-a-time observation.
Do not read per-corner meaning into an address until someone spins exactly one.

---

# 6. Setup procedure — configuring PX4 RC on this rover from scratch

Follow this rather than re-deriving it. Order matters in two places and both are called out.
Values are the ones this vehicle actually runs; §1–§4 above are the measured evidence for them.

### 6.0 Before you start

* 🔴 **CH10 IS THE COMPANION POWER CHANNEL. Put it DOWN (1011) before switching the TX on.**
  2014 = reboot the companion, 1514 (middle) = shut it down. Get this wrong and you will spend an
  hour debugging a "companion fault" that you caused with a switch.
* **Rover on stands, wheels off the ground.** Every step below can spin a motor.
* Know where the kill switch is: `RC_MAP_KILL_SW` = **ch12**. ⚠️ Docs elsewhere say "ch8" and are
  wrong; the param is right.
* ⚠️ **`set_param.py` writes are RAM ONLY.** Nothing survives a reboot until you run the save in §6.5.

### 6.1 Tools — and which one to use for what

| Task | Tool | Note |
|---|---|---|
| read any param | `python3 ~/ros2_ws/tools/set_param.py NAME` | MAVLink `tcp:5760`. Does **not** wedge the link |
| write a **FLOAT** param | `python3 ~/ros2_ws/tools/set_param.py NAME VALUE` | RAM only |
| write an **INT32** param | `python3 ~/codex-work/bldc_can/diag/set_param_int.py NAME VALUE` | 🔴 **`set_param.py` CANNOT do this** — see the trap below |
| commit to flash | `python3 ~/codex-work/bldc_can/diag/param_save.py` | `MAV_CMD_PREFLIGHT_STORAGE` p1=1 |
| reboot the FC | `python3 ~/codex-work/bldc_can/diag/fc_reboot.py` | over **DDS**; refuses if ARMED |
| verify behaviour | `python3 ~/codex-work/bldc_can/diag/brake_test_record.py` | DDS; logs ch3, aux1, per-ESC rpm + errorcount |

🔴 **`set_param.py` silently fails on INT32 params.** It always sends `MAV_PARAM_TYPE_REAL32`, and
`mavlink_parameters.cpp:129-131` refuses any set whose MAVLink type does not match the onboard type —
it logs "param types mismatch" and writes **nothing**, while looking like it worked. PX4 then does
`param_set(param, &set.param_value)` on the **raw 4 bytes**, so an INT32 must be sent as the
integer's **bit pattern** in the float field. That is what `set_param_int.py` does. **Every
`RC_MAP_*` and every `UAVCAN_EC_FUNC*` is INT32.**

⛔ **Do not use `mavlink_shell.py` for any of this.** One session per FC boot, sessions leak, and it
killed the GCS MAVLink link on 08-16. Recovery needed a reboot over DDS.

### 6.2 Step 1 — RC calibration in QGC (the only step that must be done in QGC)

Run QGC's RC calibration with the TX on and every switch in a known position. It writes
`RCn_MIN` / `RCn_MAX` / `RCn_TRIM` / `RCn_REV` for **every** channel.

🔴 **THEN IMMEDIATELY GO TO §6.4 AND RE-CHECK `RC3_TRIM`.** Calibration rewrites TRIM, and on this
airframe that is how the 50 %-brake bug gets reintroduced. **Every time. No exceptions.**

### 6.3 Step 2 — the channel map

All INT32 ⇒ all need `set_param_int.py`.

| Param | Value | Meaning |
|---|---|---|
| `RC_MAP_THROTTLE` | 2 | ch2 = forward/reverse |
| `RC_MAP_AUX1` | **3** | ch3 → `manual_control_setpoint.aux1` = the brake channel |
| `RC_MAP_ARM_SW` | 5 | arm |
| `RC_MAP_FLTMODE` | 6 | flight-mode selector |
| `RC_MAP_KILL_SW` | 12 | kill |
| `NAV_RCL_ACT` | 6 | disarm on RC loss |

Steering is on ch4 by observation; **read `RC_MAP_YAW` off the FC rather than assuming a value** —
it is not recorded here.

ℹ️ `RC_MAP_PITCH` is also **3**, the same channel as AUX1. Harmless on this vehicle —
`manual_control_setpoint.pitch` has no references in `src/modules/rover_differential/` — and the
drone loads a different parameter set. Logged as cleanup, not a conflict.

### 6.4 Step 3 — the brake channel (ch3), and the trap that makes it 50 % on

**Check first:**

```bash
python3 ~/ros2_ws/tools/set_param.py RC3_TRIM
python3 ~/ros2_ws/tools/set_param.py RC3_MIN
```

🔴 **If `RC3_TRIM == RC3_MIN` (both 1001), FIX IT — set `RC3_TRIM` to 1487.5** (a FLOAT, so
`set_param.py` is the right tool).

Why, from source rather than folklore: `interpolateNXY` (`Functions.hpp:201`) with `min == trim`
returns **−1.0 at exactly 1001** and **~0.0 at 1002** — a one-microsecond cliff — and
`output_limit_calc_single` (`mixer_module.cpp:568`) maps norm 0 onto the middle of `MIN…MAX` = **4096
= `brake_rel` 50 %**. So the brake comes on half-way the instant the stick leaves its stop.

🔴 **§2.1 of this document does NOT get you out of this.** "PX4 re-centres TRIM when TRIM == MIN" is
**THROTTLE-ONLY** — `rc_update.cpp:172` scopes it to `_rc.function[FUNCTION_THROTTLE]`. It never
applied to ch3. Do not generalise §2.1 to any other channel.

### 6.5 Step 4 — the UAVCAN brake output, in this order

⚠️ **`RC_MAP_AUX1` (§6.3) MUST already be set before you do this.** With slot 5 assigned while AUX1
is unmapped, `aux1` reads 0 → mid-scale → **50 % brake demand on the bus**.

```bash
python3 ~/codex-work/bldc_can/diag/set_param_int.py UAVCAN_EC_FUNC5 407
```

407 = `RC_AUX1` onto ESC slot 5 = DroneCAN RawCommand index 4 = the brake slot.

⛔ **Leave `UAVCAN_EC_MIN5` / `MAX5` at their defaults `1` / `8191`.** **DO NOT** copy the
`110 / 8082` convention from the four motor slots. That pair exists so the *bipolar* motor slots land
on a neutral of exactly 4096 and clear the VESC's `raw < 100` disarm guard (§3.1). The brake slot is
**unipolar**: its minimum must mean *off*, and `1` gives `brake_rel` 0.012 %, below the firmware's
0.05 engage threshold.

### 6.6 Step 5 — save, and only then reboot

```bash
python3 ~/codex-work/bldc_can/diag/param_save.py    # MAV_CMD_PREFLIGHT_STORAGE p1=1
```

⚠️ **This saves EVERYTHING currently in RAM**, not just your change. Run it only when RAM is
known-clean — ideally reboot the FC first, make your one set of changes, then save. Confirm the
command returned `MAV_RESULT_ACCEPTED`, then **read every value back**. A save that reports success
and a param that reads back wrong are different failures.

### 6.7 Step 6 — verify against behaviour, not against the parameter table

A param readback proves what you wrote. It does **not** prove the signal reaches the ESCs. Put the
rover on stands and record:

```bash
python3 ~/codex-work/bldc_can/diag/brake_test_record.py --seconds 120 --out ~/rc_verify.csv
python3 ~/codex-work/bldc_can/diag/brake_test_analyse.py ~/rc_verify.csv
```

What to look for:

1. `/fmu/out/input_rc` — the channel moves in µs when you move the control.
2. `/fmu/out/manual_control_setpoint` — **`aux1` sweeps −1 → +1 continuously.** ⛔ A wheel that stops
   proves only the *ends* of the chain. Only this proves it is **proportional**.
3. `/fmu/out/esc_status` — per-ESC rpm responds, and `esc_errorcount` stays **0**.

🔴 **DRIVE THE WHEELS UNDER THROTTLE WHILE YOU DO IT.** The brake is regenerative
(`CONTROL_MODE_CURRENT_BRAKE`), so its torque scales with back-EMF: **at hand-turn speed, full stick
and low stick are both ≈ nothing. A hand test tells you nothing.**

⚠️ **Any rclpy sampler needs a ~2.5 s DDS discovery warm-up before it starts counting.** A 3 s window
returns zero samples on healthy topics and looks exactly like a dead link. **Always prove a non-zero
baseline before believing silence.**

📄 **Worked example with real numbers:** `bldc_can/evidence/brake_bench_test_20260909.md`.
