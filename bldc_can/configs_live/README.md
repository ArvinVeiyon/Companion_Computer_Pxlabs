# configs_live — configs read OFF the hardware

⚠️ **Everything here was read back from a real ESC. Nothing here is hand-written or aspirational.**
Empty until 2026-09-13; the August files in `../configs_from_repo/` are a different thing and are
NOT a substitute (they predate the RPM-mode migration).

## THE AUTHORITATIVE FILES

| wheel | addr | motor config | app config |
|---|---|---|---|
| **RL** | 13 | `vesc_mcconf_RL_FINAL_20260913.xml` | `vesc_appconf_RL_FINAL_20260913.xml` |
| FR | 10 | — not yet pulled | — |
| FL | 11 | — not yet pulled | — |
| RR | 12 | — not yet pulled | — |

RL firmware, read from the device: **V6.06, Hw 60_MK5, isTestFw 0, UUID …51 35 32 30 34 35 38**.
That closes the September open item where no post-flash readback hash was ever recorded.

## RL's settled values, 2026-09-13

| param | value | why |
|---|---|---|
| `uavcan_raw_mode` | 3 (RPM) | keeps speed regulation; in CURRENT mode a centred stick is a free coast |
| `uavcan_raw_rpm_max` | 9000 | unchanged — operator wants the duty headroom for 360s |
| `s_pid_kp` | **0.008** | was 0.004. Bench: drive current 12.0 → 20.7 A, matching current mode's 21.1 A |
| `s_pid_min_erpm` | **50** | was 200. Only replicated metric: rpm scatter at rest, 0.00 twice at 50 vs 0.36 at 100, 0.69 at 0 |
| `l_in_current_min` | **−10** | was −5. Battery-side regen ceiling = braking authority. ⏭ STILL UNTESTED UNDER LOAD |
| `l_current_min` | **−15** | was −25, softened 2026-09-13 (late evening): braking pulled harder than wanted. ⏭ floor figures at −25 are STALE |
| `s_pid_ramp_erpms_s` | **20000** | ⛔⛔ **LEAVE IT. Tried 2000 on 2026-09-13 and REVERTED the same night.** 2000 did soften the neutral hard-brake but went SLUGGISH off the line, and — decisive — 🔴 **this is a DIFFERENTIAL drive: the ramp limits how fast the two sides can DIVERGE, so it throttles YAW ONSET and every turn goes long.** ⚠️ SYMMETRIC by construction (`utils_step_towards`, same step both ways) ⇒ it can never give a soft stop with a snappy launch |
| `s_pid_kd`, `s_pid_ki` | 0.0001 / 0.004 | unchanged — one variable at a time |

## ⛔ Do not repeat these dead ends

- **`s_pid_min_erpm` 0 is wrong.** Worst dither measured (0.69 rpm scatter, 0.63% of at-rest
  samples non-zero), and it gives up the duty-zero brake — `mcpwm_foc.c`, *"Brake when set ERPM
  is below min ERPM"*, gated on `CONTROL_MODE_SPEED`. That brake is what finishes a stop.
- **Our old note that min_erpm 200 causes a free coast below 0.11 m/s is WRONG.** The firmware
  brakes there. Corrected 2026-09-13 by reading the source.
- **The dead-band / breakaway metric is not usable.** Stiction is bigger than the release band;
  spread *within* one setting exceeded the spread *between* settings. It also silently measures
  how fast the operator pushed the stick unless you filter on stick rate.
- **Standing current does not replicate** — 0.072 / 0.112 / 0.130 A across three runs at the same
  setting. It sits inside the current sensor's own noise band. Ignore it.
- **Unloaded runs cannot measure braking.** Peak regen unloaded was −3.7 A, below even the old
  −5 A cap, so the −10 A change was never exercised. Stopping distance needs the floor.

## Reading the other files

Each `tune_esc.py` run leaves a timestamped triplet: `_pre` (as-found, before any write),
`_post` (what was sent), `_readback` (what the device held afterwards). `_pre` files are the
backups — keep them. The rest are the experiment trail from 2026-09-13 and can be deleted once
this is in git.

## ⛔ Never cross-write configs between wheels

The mcconf carries per-motor detection results — `foc_hall_table`, `foc_motor_r`,
`foc_motor_flux_linkage`, `foc_offsets_*` — and `m_invert_direction`, which is **mirrored**
(left wheels 1, right wheels 0). `tune_esc.py` reads each ESC's own config and edits only the
target values for this reason. → `../MOTOR_MAP.md`
