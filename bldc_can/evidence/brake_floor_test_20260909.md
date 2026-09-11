# RC brake — LOADED FLOOR TEST, 2026-09-09. MEASURED.

Vehicle: Vind-Roz rover, **on the floor, under its own weight, driven** — operator-attested and now
**confirmed by measurement** (§1). This supersedes the conditions attached to
[`brake_bench_test_20260909.md`](brake_bench_test_20260909.md), which were my assumption and wrong.

Raw data `~/brake_run_20260909_floor2.csv` · recorder `diag/brake_run_record.py` ·
analysis `diag/brake_run_analyse.py`

```
115.8 s | 579 rows @ 5 Hz | six topics: input_rc, manual_control_setpoint, esc_status,
                            /odom, vehicle_local_position_v1, sensor_combined
```

---

## ✅ 1. THE ROVER WAS LOADED. Measured, not inferred.

`esc_current` — the discriminator that the first run failed to log — settles it:

| Condition | Current |
|---|---|
| Wheels stationary | **−1.00 … +1.68 A** (n=1748) — sensor noise |
| Wheels turning | **−12.06 … +8.18 A** (n=301) |
| driving (positive) | median **+5.16 A**, peak +8.18 A |
| regen (negative) | median **−3.56 A**, peak **−12.06 A** — the brake pushing current back |

**Unloaded wheels on stands need a fraction of an amp to hold speed.** Amps of this order mean the
motors were working against a real load.

**And the body moved**, on two independent witnesses:

* `/odom` peak **0.943 m/s**, 118 samples above 0.05 m/s
* IMU accelerometer x spanning **−3.33 … +3.57 m/s²**. 🔑 **The IMU cannot be fooled by wheel slip** —
  a wheel spinning on a stand produces no body acceleration.

⚠️ `/odom` **drifts at standstill** (the camera-gyro dead-reckoning term — measured ~0.38 m of phantom
travel in a minute with all four wheels at 0 rpm). Use it for change *during* a run, corroborated by
the IMU. **It is not a ruler.**

## ✅ 2. Deceleration and stopping distance — the numbers that actually matter

Throttle released to neutral, sustained decay runs, measured from `/odom`:

| | median | peak | n |
|---|---|---|---|
| **BRAKED** | **0.69 m/s²** | 0.94 m/s² | 9 |
| **COASTING** | **0.20 m/s²** | 0.20 m/s² | **2** ⚠️ |

Braked stops, worked through:

```
0.85 -> 0.03 m/s in 1.0 s = 0.81 m/s2   =>  0.44 m to stop from 0.85 m/s
0.83 -> 0.00 m/s in 1.2 s = 0.69 m/s2   =>  0.50 m to stop from 0.83 m/s
0.76 -> 0.00 m/s in 0.8 s = 0.94 m/s2   =>  0.30 m to stop from 0.76 m/s
```

**⇒ The brake stops the rover in 0.30–0.50 m from ~0.8 m/s.** That figure is well sampled and solid.

**Brake ≈ 3.4× the coasting deceleration.** Extrapolated to 0.9 m/s: coast ~2.00 m, braked ~0.59 m,
a saving of **~1.4 m**.

🔴 **TREAT THE COAST FIGURE AND EVERYTHING DERIVED FROM IT AS PROVISIONAL.** n = 2, both segments
only 0.4 s long, and **neither ran to a stop** — the rover was still doing 0.63 m/s when each ended.
The 3.4× ratio and the 1.4 m saving inherit that weakness. **The braked number does not** — it stands
on 9 runs, three of them to a complete stop.

⏭ **To close it: one clean coast-to-stop.** Spin up, release throttle to neutral with the brake stick
fully down, and let it roll out completely without touching anything.

## ✅ 3. `esc_errorcount` — 0 = NONE on all four, every sample

Clean again, now under **load** rather than free-spinning. Combined with the earlier run, the
missed-`timeout_reset()` check has passed in both conditions.

---

## ⛔ A trap this exposed — do not repeat my mistake

Memory records **"coast ~0.30 m at ~0.9 m/s"**, and read naively that implies ~1.35 m/s², which would
be *twice* the deceleration the brake achieves — i.e. the brake makes things worse. **That reading is
wrong.** The source describes a standoff test where the rover *contacted the obstacle*: 0.345 m
standoff, ~0.30 m consumed, "left 0.020 m and CONTACTED". **It is a distance-before-contact, not a
stopping distance.** The rover never stopped in 0.30 m; it ran out of clearance.

🔑 **Do not compare it against a braking figure.** The only sound comparison is a coast-to-stop
measured the same way as the braked runs above.

## What is still open

* **The coast baseline** (above) — the single cheapest thing that would firm up the headline.
* **The collision reflex still only zeroes the setpoint.** It does not command the brake. Everything
  measured here is the *manual* brake on ch3. Wiring the reflex to it is the unmade change, and these
  numbers are the argument for making it.
* **One battery state, one temperature.** Authority is `brake_rel × |lo_current_min|` with
  `lo_current_min` runtime-scaled, so it **fades silently** as motors heat or the pack fills. The
  −12.06 A regen peak sits against a repo `l_in_current_min` of **−5 A**, which is worth checking:
  either the live config differs from the repo XMLs, or the cap is per-motor rather than pack-side.
* **`uavcan_raw_mode`, `UAVCAN_EC_FAIL5`, post-flash firmware hashes** — still never read.
