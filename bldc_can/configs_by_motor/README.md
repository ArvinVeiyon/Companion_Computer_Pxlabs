# `configs_by_motor/` — golden ESC configs, labelled by the MOTOR that is fitted

Created 2026-10-20, when **FL was upgraded to a 350 W motor.** Operator: the new motor is
**physically identical to the 250 W units — same 14 poles, same 3:1 gearing — only the power rating
differs.** The wheels no longer all carry the same motor, so a config is named by the motor it
belongs to, not by the wheel alone.

**Layout — one subfolder per motor generation, so the old set stays separate:**

```
350W_14pole_geared/   FL only, fitted 2026-10-20
250W_14pole_geared/   FR, RR, RL as fitted, plus FL-OLD (the motor that came off)
```

**Naming:** `<WHEEL>_<WATTS>_<POLES>pole_<DRIVE>_<YYYYMMDD>_<mcconf|appconf>.xml`
A wheel moves to the new subfolder when its motor is swapped; its old file stays where it is.

These are **copies**, one per wheel per motor generation. ⛔ **The dated history in
`configs_live/` was deliberately NOT renamed** — those filenames are cited by name in
`README.md`, `RESUME.md`, `MOTOR_MAP.md`, `esc_px4_config_audit_20260914.md`,
`diag/restore_rr_hall.py` and four memory files. Renaming them in place would break every one of
those references. This directory is the labelled view; `configs_live/` stays the archive.

## What is fitted right now

| wheel | motor | poles | `foc_motor_r` | `foc_motor_l` | flux linkage | `l_current_max` | I²R at 15 A |
|---|---|---|---|---|---|---|---|
| **FL** | **350 W** | 14 | 0.4722 Ω | 545 µH | ⚠️ 0.027215 | **14 A** | **106 W** |
| FR | 250 W | 14 | 0.5570 Ω | 547 µH | 0.011419 | 25 A | 125 W |
| RR | 250 W | 14 | 0.4367 Ω | 489 µH | 0.010385 | 25 A | 98 W |
| RL | 250 W | 14 | 0.1988 Ω | 410 µH | 0.011551 | 25 A | 45 W |

✅ **The new motor is electrically the same part.** Its inductance measured 545 µH against the old
FL's 552 µH, 1.3% apart, and its resistance 0.4722 Ω sits inside the family's 0.199-0.557 spread.
⇒ **`si_motor_poles` is 14 and `erpm_to_ms` = 0.003900 still holds for FL** (reported rpm is
electrical rpm over pole pairs, so it is on the same scale as the other three).

🔴 **It is an old-winding-class motor, so the 350 W rating does not fix the heating.** At the 15 A
seen in turns it dissipates ~106 W, against RL's 45 W. Only RL's 0.1988 Ω winding runs cool —
→ `esc_config_audit` memory, 2026-09-19.

## ⚠️ FL's 2026-10-20 detection run is not trustworthy

Three signs it was configured differently from the family. Nothing here is fixed yet.

1. **`si_motor_poles` came back 30, with `si_gear_ratio` 1 and `si_wheel_diameter` 0.165.** These
   are preset values from VESC Tool's Detect-All-FOC dialog, not measurements — picking a motor in
   its list writes the pole count straight from the preset (`detectallfocdialog.cpp:230`) and the
   direct-drive tickbox forces the pulley ratio to 1:1. **Poles corrected to 14 on device
   2026-10-20.** `si_gear_ratio` 1 and `si_wheel_diameter` 0.165 are still the preset values — they
   feed only VESC Tool's speed display, no control path, so they were left alone.
2. **Flux linkage 0.027215 Wb is 2.5× the family's 0.0104-0.0116.** For an electrically identical
   motor that is a bad measurement, not a different magnet. `foc_observer_gain` is derived from it
   (the firmware stores 1000/λ², which checks out on all five files), so 1.35e6 is ~6× out of
   family too. **MTPA is enabled on all four wheels, so flux linkage is in the live control path.**
   Old FL's values for reference if they are ever applied: λ 0.010933, observer gain 8.37e6.
3. **The current loop sits at half the family's bandwidth.** `foc_current_kp`/`foc_motor_l` is 1000
   on FL and exactly 2000 on the other three; `foc_current_ki`/`foc_motor_r` says the same. At
   bandwidth 2000 FL would be kp 1.0908, ki 944.4 from its own R and L.

⚠️ **The hall table came out of that same run** (66/199/33/133/99/167, a cyclic shift from old FL's
199/134/166/65/33/99). A wrong hall table is the fault class that bit RR in September, so it should
be re-detected and diffed against the other three before trusting it.
🔴 **A re-detect cannot be done from here** — the headless CLI has no detection or measurement
routines, only config read/write. It needs VESC Tool with a display, over USB, on the stand.

## Limits as set on FL, 2026-10-20

`l_current_max` 14 · `l_current_min` −14 · `l_abs_current_max` 20 · `l_in_current_max` 15 ·
`foc_temp_comp_base_temp` 25. Operator's choice; the other three are 25/−25/35/20.
⚠️ 14 A is below the 15-19 A the wheels drew to break away in a turn in September, so FL may be the
corner that stalls at the start of a turn. Conservative on heat, short on torque.

## What is per-motor and what is rover tune

**Per-motor — came from detection, never copy between wheels:** `foc_motor_r`, `foc_motor_l`,
`foc_motor_ld_lq_diff`, `foc_motor_flux_linkage`, `foc_observer_gain`, `foc_current_kp/ki`,
`foc_hall_table__*`, `foc_offsets_*`, and the wizard inputs `si_motor_poles`, `si_gear_ratio`,
`si_wheel_diameter`. `m_invert_direction` is mirrored by side (left 1, right 0).

**Rover tune — same on every wheel, must survive any re-detection:** `s_pid_kp` 0.008,
`s_pid_min_erpm` 50, `s_pid_ramp_erpms_s` 20000, `foc_hall_interp_erpm` 250, `foc_sensor_mode` 2,
`foc_sl_erpm` 3000, `l_watt_max` 350, `l_temp_fet_start/end` 75/90 (RL is 85/100, outstanding),
`m_motor_temp_sens_type` 8.

⚠️ **Running the FOC detection wizard wipes part of the rover tune.** On FL on 2026-10-20 it reset
`l_current_max/min` to 10/−10, `l_abs_current_max` to 30.11 and `foc_temp_comp_base_temp` to 0.
After any detection, re-apply the tune and diff against the file in this directory.

## Restoring one

```
python3 ../diag/set_mcconf_field.py /dev/ttyACM0 --expect-id 11 <field> <value>   # one or more pairs
```
It reads the ESC's own config, edits only the named fields, writes the rest back byte-identical and
aborts on a readback mismatch. ⛔ Never `--setMcConf` a whole file from one wheel onto another.

## Open on FL

- Re-detect on the stand with VESC Tool and a display: flux linkage, observer gain, hall table,
  current-loop bandwidth. Diff against the other three afterwards.
- `timeout_brake_current` is 0 in FL's app config where the other three are 2, so on a control-link
  timeout three wheels brake and FL coasts.
- App config otherwise needed nothing: `can_mode` 1, `uavcan_raw_mode` 3, `uavcan_raw_rpm_max` 9000,
  `controller_id` 11, `uavcan_esc_index` 1 all survived the motor swap.
