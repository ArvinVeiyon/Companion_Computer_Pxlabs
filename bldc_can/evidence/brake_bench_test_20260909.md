# RC brake — 2026-09-09 run (LOADED, on the floor). MEASURED.

Vehicle: Vind-Roz rover. Operator drove the wheels under throttle and worked ch3; the companion
recorded over DDS throughout.

## 🔴 TEST CONDITIONS — CORRECTED TWICE. READ THIS FIRST.

**This file originally said "on stands, wheels off the ground, unloaded" as fact. That was wrong,
and the correction that replaced it was wrong too.**

1. **First error:** nobody reported stands and nothing measured it. I *suggested* stands before the
   run and then wrote my own suggestion down as an observed condition.
2. **Second error:** challenged on it, I argued from the data that the wheels must have been
   unloaded. **The headline argument was invalid** — I claimed 51.7 m of implied wheel path was
   impossible in a room with ~2 m² of floor, while the same log showed **49 direction reversals**.
   That is ~1.05 m per leg: drive a metre, brake, reverse a metre, repeat. Entirely possible, and
   exactly what brake testing in a small space looks like. The supporting indicators did not
   discriminate either — cross-wheel lockstep separates in *turns*, not in straight forward/reverse
   runs.

✅ **THE ANSWER: the operator confirmed the rover was ON THE FLOOR, LOADED, and a follow-up
instrumented run measured it directly** — `esc_current` of −12 … +8 A while moving against ±1 A of
noise at rest, with body motion witnessed independently by `/odom` and the IMU.
📄 **[`brake_floor_test_20260909.md`](brake_floor_test_20260909.md)** — that run also carries the
first real deceleration figures in m/s².

⇒ **The measurements in this file stand exactly as recorded. Only the conditions label changes, and
it changes upward: this was loaded vehicle data, not a bench run.**

⛔ **The lesson, which is the durable part:** `esc_current` was sitting unused in an `esc_status`
message this recorder was already receiving, and no vehicle-motion topic was subscribed at all. The
conditions question was answerable from the start and the recorder threw the answer away. **Log the
discriminator, do not argue about it afterwards.**

## ✅ 1. PROPORTIONALITY — CONFIRMED. First time observed.

`aux1` tracks ch3 continuously across the whole travel. The decisive evidence is a **steady hold**
(53 consecutive samples at one stick position, so there is no sampling skew between the two topics):

| ch3 held | `aux1` measured | predicted from `RC3_TRIM` 1487.5, `RC3_MIN` 1001 |
|---|---|---|
| 1212 µs | **−0.5657** | (1212 − 1487.5) / 486.5 = **−0.5663** |

Agreement to 0.0006. The brake is **proportional, not on/off**.

## ✅ 2. `RC3_TRIM` IS STILL 1487.5 — the QGC recalibration hazard did NOT fire

Solved from PX4's own piecewise map, `T = (ch3 + MIN·aux1) / (1 + aux1)`, over 118 samples:
**median 1487.0 µs**. The steady hold above independently gives the same answer.

🔑 **This matters because it was the original bug.** At `RC3_TRIM = 1001` the channel jumps to ~0
the instant the stick leaves the bottom stop, which is `brake_rel` **50 %**. It has not regressed.

**Bottom stop, n = 1303 samples: `aux1` = −1.0000** ⇒ slot 5 = 1 ⇒ `brake_rel` 0.012 % ⇒ below the
0.05 engage threshold ⇒ **brake off, no residual drag.**

## ✅ 3. Channel geometry, SOLVED (not read — MAVLink was down)

| | |
|---|---|
| `RC3_MIN` | 1001 µs (consistent throughout) |
| `RC3_TRIM` | **1487.5** µs (solved, two independent methods) |
| `RC3_MAX` | **≈ 1973 µs** (solved, n = 55). `aux1` saturates at +1.0000 from **ch3 1969 µs** upward |
| `RC3_REV` | **not reversed** — bottom stop → −1.0, top → +1.0 |

⚠️ Same overshoot as ch2: full stick reads **2000 µs against a ~1973 µs max**, so **full brake is a
saturated command**. Harmless — PX4 clamps at ±1.0 — but it means the top of the travel is dead.

## ✅ 4. `esc_errorcount` — 0 = NONE on all four, every sample

**29,805 `esc_status` messages across 303 s, all four ESCs, zero non-zero error codes.** This is the
check for a missed `timeout_reset()` in the brake path. **It passes.**

## ✅ 5. All four wheels brake, in both directions

Sustained decelerations only (≥3 consecutive samples of monotonic slowdown from |rpm| ≥ 250, with
throttle **neutral** throughout — otherwise powered decel and direction reversals contaminate the
comparison):

| wheel | braked (rpm/s, median) | coasting (rpm/s, median) | ratio |
|---|---|---|---|
| FR (10) | 432 (n=18) | 207 (n=7) ⚠️ | — |
| FL (11) | 422 (n=18) | 466 (n=11) ⚠️ | — |
| RR (12) | **429** (n=17) | **78** (n=3) | **5.5×** |
| RL (13) | **411** (n=17) | **85** (n=5) | **4.8×** |

**Braked deceleration is tight and consistent across all four: 411–432 rpm/s.** Typical stop:
~340 rpm → 0 in ≈1.0 s forward, −413 → −126 rpm in ≈0.6 s reverse.

⚠️ **FR and FL coast figures are contaminated and should not be quoted.** FL's rpm telemetry throws
single-sample spikes (375 → 1028 → 562 within 0.4 s while the other three read 235 → 346 → 347), and
FR was still settling from one. **RR and RL are the clean pair, and they give the honest number:
the brake is roughly 5× the free-spin drag.**

---

## ❌ What this run does NOT establish

* **Nothing in m/s².** Every figure here is motor-side (rpm/s), which bounds the brake but does not
  give stopping distance. ✅ **Superseded** — the follow-up run measured **0.69 m/s² braked, stopping
  in 0.30–0.50 m from ~0.8 m/s**. See [`brake_floor_test_20260909.md`](brake_floor_test_20260909.md).
* ⛔ **The "~0.30 m coast at ~0.9 m/s" figure in memory is NOT a stopping distance** and must not be
  compared against a braking number. Its source is a standoff test where the rover *contacted* the
  obstacle — 0.345 m standoff, ~0.30 m consumed, "left 0.020 m and CONTACTED". It is
  distance-before-contact. Read as a stopping distance it implies ~1.35 m/s², which would falsely
  make the brake look worse than coasting.
* **The collision reflex still only zeroes the setpoint.** It does not command the brake. That is the
  unmade change this whole feature exists to enable.
* **Disarm and RC-loss failsafe: still untested.** Brake-off is correct by construction (PX4 sends 0
  on every slot when disarmed, which is under the threshold; `NAV_RCL_ACT` = 6 disarms on RC loss)
  but nobody exercised either.
* **`UAVCAN_EC_FAIL5`: still unread.** MAVLink was down for this run.
* **`uavcan_raw_mode`: still unread off live hardware.** Needs USB + VESC Tool — the CAN path is
  dropped. Repo appconfs say 0 (`CURRENT`) on all four; unverified.
* **No firmware hash was read back** from any ESC after flashing.
* **Brake authority is not calibrated in amps.** It is `brake_rel × |lo_current_min|`, and
  `lo_current_min` is runtime-scaled, so it **fades silently with motor temperature and pack state**.
  This run was one battery state at one temperature.

## Method notes worth reusing

* **Gate the coast bucket on throttle neutral, and score sustained runs, not sample pairs.** Scored
  naively on pairs the same data says the brake is 1.1× coast — which is wrong. Single-sample rpm
  spikes and the tail of a braked stop both land in the coast bucket.
* **Prove a non-zero baseline before believing a quiet topic.** The recorder refuses to score until
  it has seen `esc_status` traffic, after a ≥2.5 s DDS discovery warm-up.
* **A hand test would have shown nothing here.** The brake is regenerative
  (`CONTROL_MODE_CURRENT_BRAKE`), so torque scales with back-EMF. Every number above exists only
  because the wheels were spinning.
* 🔴 **LOG THE DISCRIMINATOR RATHER THAN ARGUING ABOUT IT AFTERWARDS.** This recorder subscribed to
  three topics and missed `esc_current` — which was already inside the `esc_status` messages it was
  receiving — plus every vehicle-motion source. That omission is what made the test conditions
  arguable at all, and it cost two wrong claims and a release-note retraction to fix.
