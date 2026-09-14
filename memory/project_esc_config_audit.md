---
name: esc_config_audit
description: "The 2026-09-14 rear-right hall-table fault, the four-way config-diff method that found it, and the candidate faults still outstanding on FL and RL. Read before blaming ESC tuning for a motion problem."
metadata:
  node_type: memory
  type: project
---

# ESC config audit — the method that finds faults tuning cannot

Full write-up with every number: **`codex-work/esc_px4_config_audit_20260914.md`**.
Tools: `bldc_can/diag/config_audit.py` · `backup_live_configs.py` · `set_mcconf_field.py` ·
`restore_rr_hall.py`. Related: [[vesc_can_flashing]], [[px4_rover_control_scope]].

## 🔑 THE METHOD — compare wheels against each other, and against August

Four identical motors on one chassis. **A value that is an outlier on one wheel, or that has moved
since the 15-Aug baseline in `configs_from_repo/` without a recorded reason, is a candidate fault.**
This is the only thing that has ever surfaced a fault of this class here — no amount of tuning or
floor measurement found it. Run `diag/config_audit.py --label <label>` whenever the rover misbehaves
in a way that is not obviously a tuning value.

⛔ **NEVER cross-write one wheel's values onto another.** `m_invert_direction` is mirrored (left 1,
right 0) and the detection results (`foc_motor_r/l`, `foc_motor_flux_linkage`, `foc_hall_table__*`,
`foc_offsets_*`) are genuinely per-motor. Restore a wheel's **own** history instead.

## ✅ FIXED 2026-09-14 — RR hall table, one rotor position at the wrong angle

`foc_hall_table__1` read **1** where both front wheels read 198/199; the other five entries had
moved only 1-3 counts (ordinary re-detection scatter). RR was the **only** wheel whose mcconf had
changed since August. Restored RR's own August values.

**Measured effect — the ruler is cross-wheel disagreement, not feel.** Share of moving samples where
a wheel's reported speed differs from the median of the other three by >100 rpm:

| | FR | FL | RR | RL |
|---|---|---|---|---|
| before | 6.0% | 10.2% | **20.2%** | 6.0% |
| after | 0.8% | 1.5% | **8.8%** | 0.3% |

Peak braking current per stop 4.9 A → 3.2 A. **Every wheel improved**, because one wheel reporting
nonsense disturbs the chassis *and* distorts the median the others are judged against.

🔑 **The symptom was: reported speed collapsing to near zero mid-drive (206 → 0 → 68 rpm in 20 ms
while the others read a steady 200), and the ESC believing it and spiking current to +15/+20 A to
correct an error that did not exist.** A torque kick on one corner, several times per stop.
⚠️ **RR is still ~6× the others at 8.8%. The bad table was the main cause, not the whole cause.**

## ⬜ STILL OPEN — candidate faults found by the same audit, not yet fixed

- 🟡 **RL FET de-rating starts late:** `l_temp_fet_start`/`_end` **85/100** against 75/90 on the
  other three. Under sustained load the others back off first. Only bites when hot.
- 🟡 **FL battery cell count:** `si_battery_cells` 6 vs 3, `si_battery_type` 1 vs 0. Feeds only the
  battery-level estimate (`mc_interface.c:1558`), **not** any control limit. Reporting only.
- 🟡 **RL motor resistance:** `foc_motor_r` **0.1988** against 0.4367-0.557. It is a detection result
  and legitimately per-motor, but 2.8× across identical motors is a lot, and it propagates into
  `foc_current_kp/ki` so RL's current loop is softer than the others. Candidate for re-running
  detection **on RL only**, on the stand.

## ✅ FIXED 2026-09-14 — FL regen cut thresholds were reversed

`l_battery_regen_cut_start`/`_end` read **25.4/25.2** where the other three read 25.2/25.4. Per
`mc_interface.c:2451-2457` the first branch wins, so **the other three cut regen above 25.3 V while
FL kept full regen to 25.5 V** — three wheels stop regen-braking and one does not, i.e. a yaw under
brake on a charged pack. No effect at the 24.8 V pack of that day. All four now 25.2/25.4.
⛔ Do not raise the thresholds themselves (4.2 V/cell).

## ⏸ PARKED — the crawl jerk, and why the stand was useless

Residual jerk at the end of a stop plus an audible on-off at ~3% throttle. **The speed estimate is
very noisy at crawl: FR's reported speed swings 0-39 rpm while the rover rolls steadily, and current
pulses to 8-14 A, on all four wheels equally.**

Suspect (UNTESTED): `foc_hall_interp_erpm` = 250 ≈ 36 mechanical rpm, and 3% throttle is 270 ERPM —
right on it. Below the threshold the firmware snaps rotor angle to the nearest hall sensor instead
of interpolating (`foc_math.c:646`) and **the switch has no hysteresis**.

🔴🔴 **TESTED ON RL ON THE STAND AND IT PROVED NOTHING, BECAUSE THE STAND DOES NOT REPRODUCE THE
SYMPTOM AT ALL** — 0-5 rpm of jitter there against 0-39 on the floor, current spread ~1-2 A against
8-14. Unloaded, the speed loop barely works. RL reverted to 250. **This needs a FLOOR run.
⛔ Do not re-test it on the stand and conclude anything.** Same lesson as the brake-current work:
no mass ⇒ no kinetic energy ⇒ the loop never has to do the thing you are trying to observe.
⛔ **Lowering `s_pid_kp` to 0.004 is not the answer** — it masks it and gives back drive authority.

## 🔧 USB — refined 2026-09-14

⛔ **A targeted `USBDEVFS_RESET` on a single wedged VESC made it WORSE** — the device dropped off the
bus entirely (`device descriptor read/64, error -110`) and only a **hub `1-1.2` reset** brought it
back. Prefer the hub reset; resolve the devnum at the moment of the reset, never from an earlier
listing. ⛔ Never reset `1-1`. 🔑 A wedge always hits the **first probe read**, so it never leaves an
ESC half-written — a failed run is safe to repeat.
🔑 **`is-active`, CAN telemetry and USB are independent rulers.** FL read online and healthy on
DroneCAN at 24.66 V while its USB refused every connection — **CAN health says nothing about USB.**
