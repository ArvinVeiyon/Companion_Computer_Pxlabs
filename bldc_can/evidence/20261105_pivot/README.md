# 2026-11-05 — 360 pivot drift logs

RC driving on the floor, operator pivoting both ways with re-centres. ESC logs = USB COMM_GET_VALUES
on all four at ~43 Hz/wheel (`log360.py`, read-only); stick = `/fmu/out/manual_control_setpoint`
+ `input_rc` ch1-6 (`logrc.py`). Both stamped with `time.time()`. `cmp.py` = per-direction
stall/limit/trip comparison.

| file | kp/ki (bandwidth) | l_current_max / abs |
|---|---|---|
| `drift360_231335.csv` (no stick log, time = s from start) | ω 1000 all four | 14 / 20 |
| `run2_*_232009` | ω 1000 all four | 14 / 20 |
| `run3_w2000_*_232520` | ω 2000 all four | 14 / 20 |
| `run4_25A_*` | ORIGINAL (FR 833 · FL 833 · RR 1000 · RL 1667) | 25 / 35 |

Result: stick throttle 0.00 during every spin; FR+RL stall in the roll+ direction at all settings;
trips 11 (1000) / 17 (2000) / 0 (25 A). Spin stick = ch4 -> `roll`, throttle = ch2.
Conclusions: memory `todos.md` 11-05 pivot item.
