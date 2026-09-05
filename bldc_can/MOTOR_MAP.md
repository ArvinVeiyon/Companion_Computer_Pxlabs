# Motor ↔ node ID map

Reference for which physical wheel is which DroneCAN node, and which PX4 ESC slot drives it.

**Status: DOCUMENTED FROM CONFIG, NOT YET MEASURED.** The empirical column is blank because `can0`
does not exist yet — the CAN HAT overlay is staged in `/boot/firmware/config.txt` but the companion
has not been rebooted. Fill it in with `scan.py` before flashing anything.

---

## The map

`controller_id` **is** the DroneCAN node ID — `canardSetLocalNodeID(&canard_ins,
conf->controller_id)` (`libcanard/canard_driver.c:1421`). Static; no dynamic allocation.

| Wheel | Short | Node ID | PX4 slot (`uavcan_esc_index`) | PX4 param | `m_invert_direction` | Measured |
|---|---|---|---|---|---|---|
| Front Right | FR | **10** | 0 | `UAVCAN_EC_FUNC1` | **0** | ☐ |
| Front Left | FL | **11** | 1 | `UAVCAN_EC_FUNC2` | 1 | ☐ |
| Rear Right | RR | **12** | 2 | `UAVCAN_EC_FUNC3` | 1 | ☐ |
| Rear Left | RL | **13** | 3 | `UAVCAN_EC_FUNC4` | 1 | ☐ |

Common to all four: `can_mode = 1` (`CAN_MODE_UAVCAN`), `can_baud_rate = 3` (`CAN_BAUD_1M`),
`uavcan_raw_mode = 0` (`UAVCAN_RAW_MODE_CURRENT`), `app_to_use = 0`, `si_motor_poles = 14`,
`si_gear_ratio = 3`, `si_wheel_diameter = 0.083`.

### Sources — three independent, and they agree

1. **`configs_from_repo/vesc_appconf_Aug_*_2026.xml`** — the four current app configs, each carrying
   an explicit `controller_id` and `uavcan_esc_index`.
2. **`Testing_Bin/README.md`** in the firmware repo — "Node IDs are 10 (front right), 11 (front
   left), 12 (rear right), 13 (rear left)."
3. **Companion memory** (`rover_odometry`) — `ADDR 10=RF 11=FL 12=RR 13=RL`.

### One unresolved discrepancy

Memory records node 10 as **"RF(INV)"** — Right Front, inverted. The config says Right Front is the
only wheel with **`m_invert_direction = 0`**; the other three are `1`. Both agree RF is the odd one
out, but they disagree on which way the label points. **Not resolved here.** It does not affect the
node-ID map, and it must not be "tidied" without a motion test — see the standing rule that
`si_motor_poles` ↔ `erpm_to_ms` is a linked pair and that changing motor config silently corrupts
`/odom`.

---

## Per-wheel motor identity

`foc_motor_r`, `foc_motor_l` and `foc_motor_flux_linkage` are measured per motor by detection and are
**the only genuinely per-wheel values**. They are unreachable over CAN and are what a config wipe
would destroy.

| Wheel | Node | File | `foc_motor_r` | `foc_motor_l` | `foc_motor_flux_linkage` |
|---|---|---|---|---|---|
| FR | 10 | `vesc_mcconf_Right_Front__15_Aug_26.xml` | 0.557 | 0.00054661 | 0.011419 |
| FL | 11 | `vesc_mcconf_Left_Front__15_Aug_26.xml` | 0.5215 | 0.00055165 | 0.010933 |
| RR | 12 | `vesc_mcconf_Right_Rear__15_Aug_26.xml` | 0.4367 | 0.00048855 | 0.010385 |
| RL | 13 | `vesc_mcconf_Left_Rear__15_Aug_26.xml` | **0.1988** | 0.00041032 | 0.011551 |

⚠️ **RL's `foc_motor_r = 0.1988` is an outlier** — the other three sit in 0.44–0.56, and the same
value appears in a historical `Left_Front` export. RL is the ESC currently on the bench, so **confirm
it against a live USB export before treating it as the restore point.**

---

## Confirming it empirically — one ESC at a time

This is the method in progress: **only rear left is powered; the other three are switched off.**
Exactly one node should answer.

```bash
cd ~/codex-work/bldc_can
./bringup.sh                      # needs the reboot first

# prove the bus is real before trusting any tool
candump -td can0 | head -20

./venv/bin/python scan.py
./venv/bin/python backup_params.py --label "rear left"
```

`scan.py` lists every node that answers. With one ESC powered, **exactly one VESC node should
appear** (the FC will also be present if it is powered — it is a DroneCAN node too, but it returns no
VESC parameters, so `backup_params.py` distinguishes them).

**Expected result for the current bench state: node `13`.**

If a different node ID appears, the config-derived map above is wrong for this wheel — **believe the
measurement, not the table**, and correct this file.

Record each result by ticking the Measured column and committing:

| Date | Wheel powered | Node seen | Matches table? |
|---|---|---|---|
| | rear left | | |
| | | | |
| | | | |
| | | | |

---

## Why the map cannot be read off the bus with all four connected

Nothing in DroneCAN reports physical position. `GetNodeInfo` returns the firmware name, not a wheel.
The only parameters exposed are the eight in `canard_driver.c:225`, and none of them encodes
location. **One-at-a-time power-up is the only way to bind a node ID to a physical wheel** short of
spinning a motor and watching which one moves — which is not an option on stands with the reflex and
limit-cycle hazards in play.
