# PX4 ↔ VESC DroneCAN — Diagnosis and Implementation Spec

Status: 2026-09-04. Full-reverse stop **diagnosed and fixed by parameter** (bench-verified).
Firmware work below is **specified, not implemented** — to be done from the Windows/WSL side.

Sources read: `PXLABS_PX4-Autopilot` @ `244afd0991` (`pxlabs-v1.17.0-dev`) and
`PXLABS_BLDC_VESC6_MK5/bldc` @ `05deb3e8` (`pxlabs-release-6.06-rover-r1`). Line numbers refer to those commits.

---

## 1. Protocol — nothing to port

UAVCAN v0 was renamed **DroneCAN**. UAVCAN v1 was renamed **Cyphal** (incompatible).

| Stack | Directory | Protocol |
|---|---|---|
| VESC | `libcanard/` | DroneCAN (v0) |
| PX4 | `src/drivers/uavcan/` (DSDL in `libdronecan/`) | DroneCAN (v0) |
| PX4 | `src/drivers/cyphal/` | Cyphal (v1) — separate, unused here |

Both firmwares already speak the same protocol. **Stay on DroneCAN v0.** Do not port Cyphal into VESC.

---

## 2. Root cause of "stops at full throttle" (verified)

The stop is at **full reverse**, not forward. Captured armed on stands: all four ESCs 0 rpm, **0.00 A**, fault code **0**, 25.3 V steady, 600 samples. The VESC declines the command; it is not failing.

Chain:

1. **PX4 sends 0 when disarmed.** `src/drivers/uavcan/module.yaml:36` — the `UAVCAN_EC` block defines only `min`, `max`, `failsafe`. There is **no `disarmed` param**; `UAVCAN_EC_DIS1` does not exist. `_disarmed_value` stays at constructor default 0 (`mixer_module.cpp:635`) and `esc.cpp:101–123` sends it unconditionally.
2. **`CA_R_REV = 3`** makes Motor1/2 reversible → throttle −1…+1 maps onto `MIN…MAX`, neutral ≈ midpoint. In that scheme **0 = full reverse**. A disarmed rover would drive backwards.
3. **The VESC fork guards against that** — `libcanard/canard_driver.c:682`:
   ```c
   if (raw < 100) { raw_val = 0.0f; }   // "PX4 sends 0 when disarmed"
   ```
   Full reverse armed sent `UAVCAN_EC_MIN1 = 10` → also < 100 → stop.

Measured turn-on threshold: ch2 = **1011–1015 µs** on all four ESCs (predicted 1012–1016 before measurement).

Ruled out with evidence: int14 overflow (`math::interpolate` clamps at MAX; RC overshoots 2000 vs `RC2_MAX` 1986 but PX4 emits exactly +1.0), reversed channel (`RC2_REV=1`, `UAVCAN_EC_REV=0`), neutral mismatch, VESC current/voltage fault, load dependence, single bad ESC.

---

## 3. Parameter fix — APPLIED, do not revert

| Param | Before | After |
|---|---|---|
| `UAVCAN_EC_MIN1…4` | 10 | **110** |
| `UAVCAN_EC_MAX1…4` | 8191 | **8082** |

`110 + 8082 = 8192` → neutral **exactly 4096**, no reliance on the VESC ±0.02 deadband. Peak command 0.973 at each end (~2.7 % of max current; invisible unloaded). Disarmed still sends 0, so the guard still stops the motors.

Verified: full reverse −1514/−1513/−1568/−1534 rpm; neutral-armed 0 rpm / 0.00 A (identical to pre-fix baseline). **Bench only** — not yet driven on ground. Recorded in `ros2_ws/docs/rc_configuration.md` and `setup_manual.md §A7`.

**These values must stay until Item B below is landed and verified.** After that, Item D restores `10 / 8191`.

---

## 4. Implementation items

### Item A — PX4: add a disarmed value to the UAVCAN ESC block  *(trivial, safe first)*

**File:** `src/drivers/uavcan/module.yaml`, `UAVCAN_EC` block (line ~36).

```yaml
    - param_prefix: UAVCAN_EC
      group_label: 'ESCs'
      channel_label: 'ESC'
      standard_params:
        disarmed: { min: 0, max: 8191, default: 0 }     # <-- ADD THIS LINE
        min: { min: 0, max: 8191, default: 1 }
        max: { min: 0, max: 8191, default: 8191 }
        failsafe: { min: 0, max: 8191 }
      num_channels: 8
```

No C++ change: `mixer_module.cpp:120` and `:170` already resolve `${prefix}_DIS<n>` generically. Default 0 preserves existing behaviour for every other vehicle.

**After flashing:** set `UAVCAN_EC_DIS1…4 = 4096`. A disarmed rover then sends neutral instead of full reverse.

**Verify:** disarmed on stands, `/fmu/out/esc_status` → 0 rpm / 0.00 A. (With the VESC guard still present this looks identical to before — the point is it removes the *reason* for the guard.)

---

### Item B — VESC: subscribe to `safety.ArmingStatus`  *(the proper interlock; land before Item D)*

**What PX4 already sends:** `src/drivers/uavcan/arming_status.cpp` broadcasts `uavcan.equipment.safety.ArmingStatus` at **10 Hz**. One byte: `status = 0` (DISARMED) or `255` (FULLY_ARMED). Kill and lockdown also send 0. DSDL ID **1100**.

**B1. Generate the C header.** VESC's existing headers in `libcanard/dsdl/uavcan/` were produced by `dronecan_dsdlc`. Generate `uavcan/equipment/safety/ArmingStatus.h` the same way from the DroneCAN DSDL repo (`uavcan/equipment/safety/1100.ArmingStatus.uavcan`). Use the generated `UAVCAN_EQUIPMENT_SAFETY_ARMINGSTATUS_ID` and `_SIGNATURE` — the signature is a computed hash; do not hand-type it.

**B2. Accept the frame** — `canard_driver.c`, `shouldAcceptTransfer()` (line ~1263), add to the `switch (data_type_id)`:
```c
case UAVCAN_EQUIPMENT_SAFETY_ARMINGSTATUS_ID:
    *out_data_type_signature = UAVCAN_EQUIPMENT_SAFETY_ARMINGSTATUS_SIGNATURE;
    return true;
```
(If there is a second CAN interface block — the file has two `shouldAcceptTransfer` instances at ~115 and ~1263 — add to both.)

**B3. Dispatch** — `onTransferReceived()` (line ~1219), add:
```c
case UAVCAN_EQUIPMENT_SAFETY_ARMINGSTATUS_ID:
    handle_arming_status(ins, transfer);
    break;
```

**B4. Handler + state** — near the other `static` handlers:
```c
static volatile bool     px4_armed        = false;
static volatile systime_t px4_armed_time  = 0;
#define PX4_ARMING_TIMEOUT_MS 500   // 5 missed messages at 10 Hz

static void handle_arming_status(CanardInstance *ins, CanardRxTransfer *transfer) {
    (void)ins;
    uavcan_equipment_safety_ArmingStatus msg;
    if (uavcan_equipment_safety_ArmingStatus_decode(transfer, transfer->payload_len, &msg, NULL) >= 0) {
        px4_armed      = (msg.status == UAVCAN_EQUIPMENT_SAFETY_ARMINGSTATUS_STATUS_FULLY_ARMED);
        px4_armed_time = chVTGetSystemTimeX();
    }
}

static inline bool px4_is_armed(void) {
    return px4_armed &&
           (ST2MS(chVTTimeElapsedSinceX(px4_armed_time)) < PX4_ARMING_TIMEOUT_MS);
}
```
(Check the exact decode function signature in the generated header — VESC's other handlers use `_decode_internal(transfer, len, &msg, &tmp, 0)`; mirror whichever form the generator emits.)

**B5. Gate the command** — `handle_esc_raw_command()`, immediately after `raw_val` is computed and before `switch (conf->uavcan_raw_mode)` (line ~718):
```c
if (!px4_is_armed()) {
    raw_val = 0.0f;
}
```

**Why the timeout matters:** if PX4 or the bus dies, ArmingStatus stops arriving and the VESC treats that as disarmed. Link loss becomes a stop, not a runaway. This is strictly stronger than the `raw < 100` guard.

**Verify (bench, before Item D):**
1. Armed, stick anywhere → wheels respond as today.
2. Disarm with the stick held at full forward → wheels stop within 100 ms.
3. Disarm with stick at full reverse → wheels stop.
4. Armed, then unplug CAN from the FMU → wheels stop within ~500 ms.
5. `esc_status.esc_errorcount` stays 0 throughout.

---

### Item C — Brake from RC  *(independent of A/B; the feature you actually want)*

Today `uavcan_raw_mode` gives **either** reverse (`CURRENT`) **or** brake (`CURRENT_NO_REV_BRAKE`) on the lower stick — not both. Brake needs its own channel. Use a spare slot in the RawCommand array PX4 already sends: no PX4 code, no new DSDL, no new message.

**C1. PX4 — parameters only**

| Param | Value | Effect |
|---|---|---|
| `RC_MAP_AUX1` | your brake switch/knob channel | maps the RC input |
| `UAVCAN_EC_FUNC5` | **407** (`RC_AUX1`) | passes it through to ESC slot 5 |
| `UAVCAN_EC_MIN5` | 0 | switch low → 0 |
| `UAVCAN_EC_MAX5` | 8191 | switch high → 8191 |

`esc.cpp:109–121` resizes the array to the highest configured slot, so every RawCommand now carries a 5th element = brake demand, seen by all four VESCs. Output function ids: Motor1 = 101, Servo1 = 201, RC_AUX1…6 = 407…412 (`src/lib/mixer_module/output_functions.yaml`).

**C2. VESC — read the brake slot** in `handle_esc_raw_command()`. Start with a compile-time define; promote to an `app_configuration` param (with the VESC Tool XML update) once proven.

```c
#define UAVCAN_BRAKE_SLOT       4      // 0-based index into cmd.cmd.data[] == UAVCAN_EC_FUNC5
#define UAVCAN_BRAKE_THRESHOLD  0.05f  // below this, brake is "off"
```
After `raw_val` is computed (and after the Item B arming gate), before `switch (conf->uavcan_raw_mode)`:
```c
float brake_rel = 0.0f;
if (cmd.cmd.len > UAVCAN_BRAKE_SLOT) {
    int16_t b = cmd.cmd.data[UAVCAN_BRAKE_SLOT];
    if (b < 0) b = 0;
    brake_rel = (float)b / 8191.0f;
}

if (brake_rel > UAVCAN_BRAKE_THRESHOLD) {
    // Brake wins over throttle. Apply and skip the raw-mode switch.
    mc_interface_set_brake_current_rel(brake_rel);
    timeout_reset();
    return;   // or goto the existing tail after the switch — match the function's structure
}
```
Two-position switch → off / full brake. Three-position or knob → proportional (mid = 4096 = 50 %).

**Interactions:**
- Disarmed: PX4 sends 0 on slot 5 → brake off; Item B gate (or the existing guard) stops the motor.
- Brake must win over throttle when both are non-zero; the early return above guarantees it.
- Slot 5 is shared by all four ESCs — correct for a rover.

**Verify (bench):** armed, stick forward, flip brake → wheels stop and `esc_current` shows brake current; release → wheels resume. Repeat in reverse. Disarmed with brake on → 0 rpm / 0.00 A.

**Why not `actuator.ArrayCommand`:** it's the standard servo message and would also carry steering later — but VESC handles zero actuator messages today, so it means a new handler *and* new DSDL headers. The RawCommand slot rides on the path that already works (~30 lines). If ArrayCommand is added for steering later, brake can move to it.

---

### Item D — VESC: delete the `raw < 100` guard  *(ONLY after Item B is bench-verified)*

**Order is safety-critical.** The band is currently the **only** thing stopping the motors when disarmed. Deleting it before Item B lands leaves a disarmed rover driving backwards.

`canard_driver.c:675–698` — replace the entire rover-vs-standard heuristic with the plain standard mapping:
```c
// Standard DroneCAN: signed int14, -8192..8191, 0 = neutral.
// Neutral offset (4096) is handled by PX4's MIN/MAX; arming by ArmingStatus (Item B).
raw_val = ((float)raw - 4096.0f) / 4095.0f;
if (raw_val >  1.0f) raw_val =  1.0f;
if (raw_val < -1.0f) raw_val = -1.0f;
if (raw_val > -0.02f && raw_val < 0.02f) raw_val = 0.0f;   // keep the neutral deadband
```
Then restore PX4 `UAVCAN_EC_MIN1…4 = 10` (or 1) and `UAVCAN_EC_MAX1…4 = 8191` — full ±1.0 range returns. Re-run the Item B verification list plus a full-reverse capture.

---

### Item E — Backlog (not needed for the rover to work)

| Where | Change | Effort |
|---|---|---|
| PX4 | Map `msg.power_rating_pct` → `esc_report.esc_power` beside `esc.cpp:140–144` (currently dropped) | trivial |
| VESC | Broadcast `power.BatteryInfo` — header already vendored in `libcanard/dsdl/uavcan/equipment/power/`, never used; mirror the `esc.Status` broadcast at `canard_driver.c:506`. PX4's `sensors/battery.hpp` consumes it with no change | small |
| Both | Translate `mc_interface_get_fault()` codes → `EscReport.failures` bitmask (OVER_CURRENT, OVER_VOLTAGE, MOTOR_OVER_TEMPERATURE, MOTOR_STUCK). Today the code is squeezed into `esc_errorcount` | medium |
| VESC | `actuator.ArrayCommand` handler → steering servo on the VESC's servo output | medium |
| PX4 | Clamp `outputs[i]` to `[0, 8191]` before the `static_cast<int>` at `esc.cpp:110` — defensive only, the mixer already clamps | trivial |
| PX4 | Consume `vesc.RTData` (20-field vendor telemetry VESC already broadcasts at `canard_driver.c:576`) | large |

Not needed: `esc.RPMCommand` publisher in PX4 — VESC's `UAVCAN_RAW_MODE_RPM` already gives closed-loop speed via RawCommand, scaled by `uavcan_raw_rpm_max`.

---

## 5. Order of work

1. **Item A** (PX4 yaml line) — safe, cannot make anything move.
2. **Item C** (brake) — independent, can go any time.
3. **Item B** (ArmingStatus) — bench-verify all five checks.
4. **Item D** (delete guard, restore MIN/MAX) — only after 3 passes.

Items A and B are defence in depth: A removes the reason for the guard, B replaces it with something that also catches link loss.

---

## 6. Still open — physical

- Drive on the ground. All results above are on stands, unloaded.
- Verify ESC node → wheel map (10 = RF inverted, 11 = FL, 13 = RL, 12 = RR) against a turning wheel. Did not matter today (all four behaved identically); it will the first time one doesn't.
- Recalibrate RC in QGC: ch2 reads 2000 µs vs `RC2_MAX` 1986, and `RC2_TRIM` is stored as 1001 (PX4 re-centres it via `rc_update.cpp:170–184`). Harmless today, but stale.
- Read `uavcan_raw_mode` from VESC Tool. With Items B–D done, it decides whether the lower stick is reverse (`CURRENT`) or brake (`CURRENT_NO_REV_BRAKE`). With Item C, use `CURRENT` — reverse on the stick, brake on the switch.

---

## 7. Message compatibility matrix (reference)

| DroneCAN message | PX4 | VESC | Status |
|---|---|---|---|
| `esc.RawCommand` | TX | RX | working (guard issue above) |
| `esc.Status` | RX | TX | working; `power_rating_pct` dropped |
| `esc.RPMCommand` | — | RX | not needed (RPM mode via RawCommand) |
| `protocol.NodeStatus` / `GetNodeInfo` / `param.GetSet` / `RestartNode` / `file.BeginFirmwareUpdate` | ✓ | ✓ | working |
| `safety.ArmingStatus` | TX | — | **Item B** |
| `power.BatteryInfo` | RX | DSDL only | Item E |
| `actuator.ArrayCommand` | TX | — | Item E (steering) |
| `indication.LightsCommand` | TX | — | n/a |
| `vesc.RTData` | — | TX | Item E |

Full analysis with captures: https://claude.ai/code/artifact/67883264-6de5-431f-b726-66ecc6a7ed48
