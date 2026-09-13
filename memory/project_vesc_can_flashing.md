---
name: vesc-can-flashing
description: "RC brake on the 4 VESCs - DONE and bench-tested 09-09. Companion CAN integration DROPPED. Pointers to the three docs that hold the detail."
metadata:
  node_type: memory
  type: project
  originSessionId: b7052c6e-f42f-48fd-9d7e-c0dffff0ecc5
  modified: 2026-09-13T18:41:30.309Z
---

**POINTER FILE. The detail lives in three documents — open them, do not work from this summary.**

📕 **`~/codex-work/bldc_can/RESUME.md`** — the live state of the RC brake: what is done, the traps,
the open items. **Open this first.**
📗 **`~/codex-work/bldc_can/evidence/brake_floor_test_20260909.md`** — the LOADED floor run: m/s²,
stopping distance, and how the conditions were measured. (`brake_bench_test_20260909.md` is run 1,
motor-side; its filename says "bench" and that is WRONG — it was loaded too, see its header.)
📘 **`~/codex-work/companion_can_driver_status.md`** — what the dropped CAN work changed on this
companion at driver level, and how to finish reverting it.
📐 **`~/codex-work/rc_configuration.md` §6** — the step-by-step procedure for configuring PX4 RC on
this rover. Follow it rather than re-deriving.

## Status, 2026-09-09

✅ **RC brake DONE: all four ESCs on `a75a0dbf`, PX4 side saved to flash, and DRIVEN ON THE FLOOR
UNDER LOAD with the conditions MEASURED — 0.69 m/s², stops in 0.30–0.50 m from ~0.8 m/s.**
Proportionality confirmed, `esc_errorcount` clean on all four under load.
⚠️ **The coast baseline is n=2 and neither segment ran to a stop ⇒ every ratio derived from it
(3.4×, "saves 1.4 m") is PROVISIONAL.** One clean coast-to-stop closes it.
🅿️ **The companion CAN-HAT integration is DROPPED (time concern).** Hardware-dead on the SPI side,
overlay disabled 09-09. ⛔ **Do not reopen the MCP2515 debugging and do not re-propose SocketCAN.**

## The rules that survive — these are the ones that cost real time

🔴 **`Testing_Bin/60_mk5.bin` MUST BE FLASHED OVER USB, NEVER DRONECAN** — it overflows the 384 KB
staging area into the bootloader sector, which is never erased ⇒ **brick, SWD-only recovery**.
`flash.py` refuses it; **never work around that guard.**
🔴 **VESC Tool over SocketCAN CANNOT WORK HERE** — `can_mode=1` (UAVCAN) means a CAN scan finding
nothing is *correct behaviour*, not a fault. Switching it takes DroneCAN and the rover down.
🔑 **`esc_current` IS THE LOADED/UNLOADED RULER** — ±1 A at rest vs −12…+8 A moving. **`/odom`
DRIFTS AT STANDSTILL** (~0.38 m/min at 0 rpm, the camera-gyro term), so corroborate with the IMU.
🔴 **A HAND TEST CANNOT MEASURE THIS BRAKE.** It is regenerative (`CONTROL_MODE_CURRENT_BRAKE`), so
torque scales with back-EMF — at hand-turn speed full stick and low stick are both ≈ nothing.
🔴 **`set_param.py` CANNOT WRITE INT32 PARAMS** — it always sends REAL32, PX4 refuses the type
mismatch and writes **nothing**, silently. Use `bldc_can/diag/set_param_int.py`.
FC reboot over DDS = `diag/fc_reboot.py`.
✅✅ **09-12: `diag/param_save.py` IS NOT NEEDED — MAVLink PARAM_SET PERSISTS BY ITSELF.** `param_set`
calls `param_autosave()` (`parameters.cpp:450`); `autosave.cpp:60` writes after **300 ms**,
rate-limited to 2 s. **Proven: `RO_MAX_THR_SPEED` = 4.93 survived an FC reboot.** ⛔ **Both tools
print "this is a RAM write" — that NOTE IS WRONG, ignore it.** ⚠️ Only trap: don't reboot within
~2 s of the write.
🔴 **A QGC RC CALIBRATION REWRITES TRIM** ⇒ `RC3_TRIM` can land back on `RC3_MIN` = 1001, which
commands **50 % brake** the instant the stick leaves the stop. **Re-check it after every calibration.**
⚠️ **`rc_configuration.md` §2.1 ("TRIM==MIN is a QGC artefact, don't fix it") IS THROTTLE-ONLY** —
`rc_update.cpp:172` scopes it to `FUNCTION_THROTTLE`. Never generalise it to another channel.
⛔ **DO NOT "fix" `si_motor_poles`** (14 on all four) — it is a linked pair with `erpm_to_ms 0.003900`
and changing it in VESC Tool **silently halves `/odom`**, a safety input.
⛔ **DO NOT copy the motor slots' `110/8082` onto the brake slot** — it is unipolar; `1/8191` is right.
⛔ **NEVER restore from `vesc_mcconf_Right_Front.xml`** — `foc_motor_flux_linkage 1.46287`, ~130× the
family, a failed detection.

## Still open

🔴 **Rollback is gone as a bench comparison** — all four are on branch firmware. Rollback = tag
`v6.06.0-pxlabs-rover-r1`, over USB, per ESC.
⏭ **ONE CLEAN COAST-TO-STOP** — the cheapest open item; every ratio above depends on it.
⏭ **The collision reflex STILL ONLY ZEROES THE SETPOINT — it never commands the brake.** That unmade
change is the reason the feature exists, and 0.69 m/s² braked vs 0.20 coasting is the case for it.
⏭ **Reconcile the −12.06 A regen peak against the repo `l_in_current_min` of −5 A** (live mcconf
differs, or the cap is per-motor?). Needs USB.
⏭ Never read off live hardware: `UAVCAN_EC_FAIL5`, `uavcan_raw_mode`, and any post-flash firmware
hash. Disarm / RC-loss brake-off is correct by construction, **untested**.

See also [[rover-odometry]], [[uart-map]], [[this-machine]].

## 🔑🔑 2026-09-12 — **HOW TO REACH THE ESC CONFIG, AND WHAT `uavcan_raw_mode` OFFERS**

Read from the firmware itself: **`ArvinVeiyon/PXLABS_BLDC_VESC6_MK5`, branch
`pxlabs-6.06-rover-brake-rc`** (clones fine over SSH; the tree is NOT on this machine).

### THE FOUR RAW MODES — `datatypes.h:871`
```c
UAVCAN_RAW_MODE_CURRENT = 0,          // ← OURS. mc_interface_set_current_rel() = TORQUE
UAVCAN_RAW_MODE_CURRENT_NO_REV_BRAKE, // 1
UAVCAN_RAW_MODE_DUTY,                 // 2  mc_interface_set_duty()
UAVCAN_RAW_MODE_RPM                   // 3  mc_interface_set_pid_speed(raw * uavcan_raw_rpm_max)
```
🔑🔑 **MODE 3 IS THE FIX FOR G2 AT THE ESC END: the VESC closes its own speed loop, so PX4's
"throttle means speed" assumption becomes TRUE, and `uavcan_raw_rpm_max` IS the speed cap the
operator asked for.** The switch is at `libcanard/canard_driver.c:749`; ⛔ **the PXLABS brake block
sits IN FRONT of it and is untouched by the mode.**

### 🔴 WHERE IT CAN AND CANNOT BE SET
⛔ **NOT OVER CAN.** The UAVCAN GetSet table (`canard_driver.c:225`) exposes **exactly 8** params:
`can_baud_rate · can_status_rate_1 · can_status_rate_2 · can_status_msgs_r1 · can_status_msgs_r2 ·
can_esc_index · controller_id · ctl_dir`. **`uavcan_raw_mode` is not among them.** (🔑 `ctl_dir` IS
remotely settable — motor DIRECTION can be changed over CAN, the control MODE cannot.)
✅ **OVER UART — YES, AND IT IS ALWAYS LIVE.** `main.c:299-301` calls `app_uartcomm_start()` for
**BUILTIN and EXTRA_HEADER** *before* `app_set_configuration()`, so serial comms is up **regardless
of `app_to_use` (0 on ours)**. Default **115200** (`app_uartcomm.c:32`). Same `commands` layer as
USB ⇒ **full app+motor config access.**
⛔ **ONE CONNECTION PER ESC — THERE IS NO MULTI-DROP.** VESC CAN forwarding is gated on
`can_mode == CAN_MODE_VESC`; in `CAN_MODE_UAVCAN` the CAN process thread simply `continue`s
(`comm_can.c:1346`). Switching `can_mode` takes DroneCAN — and the rover's drive — DOWN.
⇒ **4 separate sessions: one adapter moved between them, or an FT4232H, or a UART mux.**
⚠️ On the companion only **`ttyAMA1` (GPIO0/1, needs `dtoverlay=uart1-pi5`)** is free — enough to
wire ONE ESC permanently, not four. → `reference_uart_map`

### ⛔⛔ BLE IS OFF THE TABLE ON THESE BOARDS — AND NOT SOLDERING IT WAS CORRECT
MK5 firmware moved the NRF to a **permanent UART, PC11/PC12** (`HW_UART_P_*`, 115200) and
**#if-outs the old NRF SPI block**. On MK5 the **DRV8301 gate-driver SPI took PB3/PB4** — the pins
the old HW60 used for NRF SPI. The two swapped.
🔴 **OUR BOARDS ARE WIRED THE ORIGINAL (SPI) WAY, so the module footprint sits on the DRV8301 SPI.
Populating it would put a second device on the GATE DRIVER's bus — over-current thresholds, gain and
fault readback all ride there ⇒ a MOTOR-SAFETY problem, not a comms one.** The operator left it
unsoldered; ⛔ **do not suggest fitting it.**
✅ **Consequence worth having: the permanent UART on PC11/PC12 is therefore FREE and already started
as a comm port** — if those pads are reachable it is a second wired way into each ESC, possibly
easier than the USB connector depending on the chassis.

## ✅✅ 2026-09-12 — **RPM MODE IS LIVE ON REAR LEFT (addr 13). WORKING CONFIG + THE CEILING**

Set over **USB + VESC Tool** by the operator (⛔ still impossible over CAN — the GetSet table is 8
params). **Final RL config, and the template for the other three:**

| param | value | where in VESC Tool | meaning |
|---|---|---|---|
| `uavcan_raw_mode` | **3** (RPM) | App Settings → General, UAVCAN | closed-loop speed |
| `uavcan_raw_rpm_max` | **9000** | same page | **ERPM** at full stick ⇒ 1273 rpm = 4.96 m/s = 17.9 km/h |
| `s_pid_min_erpm` | **200** | Motor Settings → PID Controllers → Speed PID | loop RELEASES below (29 rpm ≈ 0.11 m/s) |
| `s_pid_ramp_erpms_s` | **20000** | same page | setpoint slew ⇒ 2857 rpm/s ≈ **11 m/s² (1.1 g)** |

⚠️ `s_pid_min_erpm` and the ramp are **mcconf** ⇒ **"Write Motor Configuration"**, a DIFFERENT button
from the app-config write. A write to the wrong one silently no-ops — that is exactly how the first
ramp change was lost, caught only by measuring 4956 ERPM/s (= the stock 5000) off a step.

### 🔴🔴 THE MOTOR CEILING IS ~10500 ERPM — A CAP ABOVE IT IS NOT A CAP
`l_max_duty` = **0.95** (mcconf), so full duty is 94.9% and the no-load ceiling is **1504 rpm =
5.87 m/s = 21 km/h**. ⛔ **`uavcan_raw_rpm_max` above ~10500 does NOTHING** — duty pins at 0.95, the
loop goes open, and 11000 / 12000 / 20000 all give the same speed. Verified: at 20000 the operator
read 94.9% duty; at 10000, >90%; at 9000, ~90% with reserve. 🔑 **Duty is an OUTPUT, not a tuning
metric** — 13% duty at the 1400 cap was correct, not "under-tuned" (0.13 × 1504 ≈ 194 ✓).

### 🔑 HOW TO TELL WHICH MODE IS LIVE — THERE IS NO READBACK OVER CAN
- **CURRENT (0):** wheels-up speed **FLAT ~1505 rpm** from ~1/7 stick to full, ~2.0 A.
- **DUTY (2):** speed **LINEAR in stick** (0.18→235, 0.34→511, 0.50→744, 1.00→1504), regen on release.
- **RPM (3):** **clips at `rpm_max`/7**, holds it on **0.15–0.8 A**, and **resists a hand-turn at
  centre stick** (2.8 A observed) because zero is a SETPOINT, not a release.
⛔ Full stick alone cannot separate DUTY from RPM when the cap is near the ceiling — use a mid-stick
rung or the hand-turn test.

### 🔑 THREE SYMPTOMS, ONE CAUSE — and the fix
Green LED solid + residual current at rest + ~4% duty dither at zero stick = **the FOC loop stays
ENGAGED at zero** (CURRENT/DUTY release instead; hall gives 60° steps so the speed estimate at 0 rpm
is noise, and the PID chases it). **`s_pid_min_erpm` = 200 fixed it — duty settles to 0.** ⚠️ Cost:
no active zero-hold below 0.11 m/s, so that wheel free-coasts there. ⚠️ Residual **−0.05 A is the
current-sensor offset** (band is ±1 A) — not real current.

### ⏭ Open
✅ **NOT A FAULT — the operator had powered 10/11/12 OFF deliberately** while working on RL.
`esc_online_flags` = 8 (`0b00001000`) with `timestamp == 0` on the other three is what a
POWERED-DOWN ESC looks like, and it is indistinguishable from a broken CAN chain. 🔑 **ASK BEFORE
DIAGNOSING: "are the other three powered?"** — I spent the session calling it an unexplained bus
fault. 🔑 One driven wheel + three off = the "slow rotation" that was misread as a low speed cap.
⏭ `configs_live/` and `backups/` are **STILL EMPTY** — RL's appconf+mcconf were never exported, and
RL is now the reference. ⏭ Reverse plateau ran **−46…−49 vs +42** at the 300 cap (~10% asymmetric),
untested at 9000. ⏭ `l_in_current_min`, `l_current_min`, `uavcan_status_current_mode` and the fw
hash were asked for but never read back off live hardware.
⚠️ **USB access is PHYSICALLY HARD** (path blocked, tightly packed) ⇒ finish one ESC completely per
session. The **PC11/PC12 permanent UART** would avoid the cable fight if those pads are reachable.

## ✅✅✅ 2026-09-12 (later) — **ALL FOUR WHEELS MIGRATED TO RPM MODE. G2 CLOSED AT THE ESC END.**

Order done, one USB session each: **RL (13) → RR (12) → FR (10) → FL (11)**. Identical settings on
all four: `uavcan_raw_mode` 3 · `uavcan_raw_rpm_max` 9000 · `s_pid_min_erpm` 200 ·
`s_pid_ramp_erpms_s` 20000. ✅ **`RO_MAX_THR_SPEED` 0.60 → 4.93** (RAM, 09-12).

**Per-stage bench proof (each wheel measured as it was done, not assumed):**
| stage | evidence |
|---|---|
| RL alone | clips 1273 vs 1286 predicted; ramp 2898 rpm/s = 20285 ERPM/s |
| + RR | RR 1274 vs RL 1275 — was 1550 in torque mode |
| + FR | means 1051.8 / 1051.8 / 1052.3 — within 0.5 rpm |
| + FL, all four | means **985.4 / 982.6 / 986.7 / 983.5**, 0.4% spread, 499/499 positive |

🔑 **THE MIXED-MODE STATE IS THE DANGEROUS ONE — and it is VISIBLE:** with FL still on CURRENT while
three were on RPM, one wheel read **598 rpm while the other three sat at 22–35** on the same command.
⛔ **Never drive a partially-migrated set on the floor** — that is a hard yaw, not a drift.

### 🔑 DIRECTION / SIGN — SETTLED 09-12, ⛔ DON'T RE-CHASE
`m_invert_direction` is a **CLEAN MIRRORED PATTERN — both LEFT wheels 1 (FL 11, RL 13), both RIGHT
wheels 0 (FR 10, RR 12)**, consistent for the first time. (The Aug set had RR = 1, breaking the
symmetry; the Sep re-detection changed it 1→0 paired with a new `foc_hall_table`.) ✅ **The pair is net-neutral: the operator confirmed BY EYE that RR and
RL turn the SAME direction**, and all four report POSITIVE ERPM driving forward. ⇒ **`wheel_signs` in
`wheel_odometry_node` needs NO change.** 🔑 Reminder that cost a false alarm in July: **ERPM sign is
NOT a reliable indicator of physical direction** on mirrored mounts — always get an eye check.

### ⏭ Open after this
⏭ **`RO_MAX_THR_SPEED` 4.93 is a RAM write** — needs `param_save.py` or it reverts on FC reboot.
⏭ **FLOOR RUN: commanded vs measured speed under load.** Everything above is unloaded.
⏭ **First turn: four independent speed loops do not share load** — watch for scrub and turn current.
⏭ `foc_motor_r` on RL is **0.1988 Ω vs 0.44–0.56** on the other three — never re-detected.
⏭ `si_battery_cells` = 3 on RF/RR/RL but **6 on LF** (LF is right, 6S). `si_wheel_diameter` 0.083 and
`si_gear_ratio` 3 are wrong for a **6-inch direct-drive** tyre. ⛔ All cosmetic — ⛔ but do NOT
"fix" `si_motor_poles`, which is NOT cosmetic (it sets the ÷7 telemetry divisor).

## ✅✅✅ 2026-09-13 — **ALL FOUR TUNED AND FLOOR-VALIDATED. G2 CLOSED END TO END.**

🔑🔑 **The companion can now do ESC config itself, headless, over USB — no laptop, no X.**
→ **[[vesc-tool-cli]]**, and use **`~/codex-work/bldc_can/tune_esc.py`**, never raw `--setMcConf`.
📂 Every wheel's as-found and final config is in `configs_live/` (was EMPTY since August) with a
`README.md` naming the authoritative pair. ✅ **fw readback hashes finally recorded for all four**
(V6.06 / 60_MK5 / `isTestFw` 0, per-wheel UUIDs) — closes the September open item.

### The settled set — IDENTICAL on FR 10 / FL 11 / RR 12 / RL 13, each verified by readback
| param | value | was | why |
|---|---|---|---|
| `s_pid_kp` | **0.008** | 0.004 | the loop was UNDER-ASKING for current, not limited by it |
| `s_pid_min_erpm` | **50** | 200 | only replicated metric; see below |
| `l_in_current_min` | **−10** | −5 | braking ceiling — but it turned out NOT to be binding |
| `l_current_min` | ~~−25~~ → **−15** | FL was −25.8 | squared up so all four brake alike; **SOFTENED to −15 late the same evening — see below** |
| `s_pid_ramp_erpms_s` | ~~20000~~ → **2000** | stock 5000 | **SOFTENED late the same evening — see below** |
| `uavcan_raw_mode` 3 · `rpm_max` 9000 · `l_max_duty` 0.95 | unchanged | | operator wants the duty headroom for 360s |

### ✅✅ 2026-09-13, LATE — **THE BRAKE WAS SOFTENED. NEUTRAL WAS HARD-BRAKING EVERY TIME.**
Operator's complaint: **returning the stick to NEUTRAL hard-braked, every time.** Applied to all
four over USB with `tune_esc.py`, each verified by readback: **`l_current_min` −25 → −15** and
**`s_pid_ramp_erpms_s` 20000 → 2000**. Per-wheel detection values confirmed unchanged and still
distinct afterwards ⇒ no cross-write. Committed `60ed7af`.

🔑🔑 **THE MECHANISM — `l_current_min` WAS NEVER GOING TO FIX THIS.** In RPM mode neutral is not
"no torque", it is **"hold 0 ERPM" — an ACTIVE stop**, finished by the duty-zero short brake below
`s_pid_min_erpm`. **`l_current_min` caps how HARD the stop pulls; only the RAMP changes how
ABRUPTLY zero is demanded.** ⛔ Don't reach for the current limit again for a *harshness*
complaint.

🔑🔑 **WHY IT WAS 20000 — IT WAS DELIBERATE, FOR THE OPPOSITE COMPLAINT.** Set 09-12 with the
RPM-mode template when the problem was **LATE STOPS**: 20000 ⇒ ~11 m/s² (1.1 g) of setpoint slew,
deliberately beyond tyre grip so the *setpoint* would never be what limited a stop. **Stock is
5000, so 2000 is BELOW stock and reverses that call.** ⚠️ If late stops come back, this is why.
📏 At 1 m/s (~1795 true ERPM) 2000 gives ~0.9 s to a stop, ~1.1 m/s². The old 20000 gave 0.09 s —
i.e. **effectively no ramp at all**, which is exactly why it bit every time.
⚠️ **SYMMETRIC** (`foc_math.c:504`, `utils_step_towards`) ⇒ **acceleration softens identically.**

🔴🔴 **A HIDDEN DEPENDENCY THIS EXPOSED — THE REFLEX'S SAFETY RESTS ON THE RAMP BEING HIGH.** The
collision reflex **only zeroes the setpoint**, which is safe *because zeroing is instant at 20000*.
Lowering the ramp slews the **emergency** stop at the **same rate as a comfort stop** — the ESC
cannot distinguish a released stick from a detected obstacle. The ramp is back at 20000 so this is
**not currently live**, but ⛔ **treat it as a hard constraint on any future ramp reduction.**
⏭ The durable fix is for the reflex to **command a brake directly** rather than rely on setpoint
collapse (still an open item).
⛔ **The 09-13 floor figures (0.52 s / 0.19 m / 1.28 m/s²) were taken at `l_current_min` −25, now
−15, and the reflex clearance margin is sized against them. RE-MEASURE BEFORE DRIVING AT SPEED.**

### ⛔⛔ 2026-09-14 — **`l_current_min` IS NOT THE BRAKE LEVER. MEASURED. ALL CHANGES REVERTED.**
Chasing a neutral stick that hard-brakes, `l_current_min` was taken **−25 → −15 → −6** on all four.
**The operator felt NO difference at any setting.** All four are back at **−25** (readback-verified),
so the ESCs end the session in exactly the config they started it in.

🔑🔑 **WHY — FULL-RATE BENCH LOG, 99.3 Hz, 5955 samples, 9 stop events, rover ON A STAND:**
**peak braking current is only −3.5 to −4.6 A** (FR −3.47 · FL −3.49 · RR −3.79 · RL −4.59).
**Every limit tried — −25, −15, −6 — sits ABOVE that, so NONE of them ever bind.** Drive current
peaked **+11.7 to +20.3 A**, so the drive side is healthy. ⛔ **Stop reaching for `l_current_min`
for a harshness complaint.**

🔴🔴 **THE STAND DOES NOT REPRODUCE THE SYMPTOM — DO NOT DIAGNOSE THE BRAKE ON A STAND.** Those 9
stops were **1.3–2.7 s coast-downs** from ~1265 rpm with **MEAN current POSITIVE (+0.7 to +1.1 A)**
— the motor gently *driving*, not braking. With no vehicle mass there is no kinetic energy, the
speed error collapses on its own, and the loop never demands real braking current. **The hard stop
needs inertia to exist.**

⚠️⚠️ **MEASUREMENT TRAP THAT NEARLY COST THE ANSWER: `brake_run_record.py` writes its CSV on a
0.2 s timer (5 Hz) while `esc_status` arrives at ~98 Hz — it keeps ~1 sample in 20 and is BLIND to
a current spike inside a 0.4 s stop.** The 5 Hz and 99 Hz passes happened to agree here, but only
the second is evidence. ✅ **Use `diag/brake_fullrate.py`** (added 09-14, logs every message).

⏭ **STILL UNDIAGNOSED: what makes the floor stop hard.** Next step is the SAME full-rate log **on
the floor**. ⏭ The one untested ESC-side brake lever is **`foc_duty_dowmramp_kp` (50) / `_ki`
(1000)** — they appear at exactly two lines in the firmware, both inside the duty-control PI, and
for this rover the ONLY entry into duty-control is the neutral duty-0 short brake ⇒ **brake-path
only, cannot touch acceleration or yaw.** ⚠️ **UNCONFIRMED — do not tune them until a floor run
shows the short brake actually engaging.**
⛔ **CORRECTION to the 09-13 note below:** "there is NO brake-only ramp in VESC FOC" was too strong.
`cc_ramp_step_max`/`m_duty_ramp_step` really are dead (mcpwm.c/BLDC only), but `foc_duty_dowmramp_*`
were missed and ARE in the FOC brake path.

### ⛔⛔ 2026-09-13/14 — **THE RAMP WENT 20000 → 2000 → 20000. IT IS BACK AT 20000. DO NOT RE-PROPOSE 2000.**
2000 **did** fix the hard neutral brake. It was reverted the same night for two reasons:
1. **Sluggish off the line** — "takes more seconds to respond" (operator, on the floor).
2. 🔴🔴 **DECISIVE — THIS IS A DIFFERENTIAL / SKID-STEER DRIVE.** A turn **IS** a speed difference
   between the two sides, so the ramp limits **how fast the sides can DIVERGE** ⇒ it throttles
   **YAW ONSET** and **every turn goes long**. That is **control authority, not comfort** — and it
   is why the ramp cannot be used as a comfort knob on this vehicle at all. (operator, 09-13)

🔑🔑 **SYMMETRIC — PROVEN FROM SOURCE, NOT ASSUMED:** `foc_math.c:504` calls `utils_step_towards()`;
`util/utils_math.h:131` applies the **same step magnitude both ways** (`+= step` / `-= step`, no
direction test). ⇒ **no value can give a soft stop AND a snappy launch.** ⛔ Stop trying.
📏 At 1 m/s (~1795 true ERPM): **20000 = 0.09 s** (11 m/s², never binds ⇒ current/grip sets the
feel) · 5000 = 0.36 s · **2000 = 0.90 s** (1.1 m/s², binds BOTH ways — the sluggishness).

⛔⛔ **THERE IS NO BRAKE-ONLY RAMP IN VESC FOC — CHECKED AGAINST THE FIRMWARE 09-13.** The other two
ramp params in the mcconf, **`cc_ramp_step_max` and `m_duty_ramp_step`, are referenced ONLY in
`mcpwm.c` — the BLDC commutation driver.** This rover runs FOC (`mcpwm_foc.c`) ⇒ **both are DEAD
parameters here and would do nothing.** The only brake-specific levers are `l_current_min`,
`l_in_current_min` and `l_max_erpm_fbrake`, and **none shape the ONSET — only the ceiling.**
⏭ **SO THE ONLY SOFT-STOP LEVER LEFT ON THE ESC IS `l_current_min` (now −15).** Asymmetry has to
come from **PX4: `RO_ACCEL_LIM` / `RO_DECEL_LIM` are SEPARATE params** — the only way to soften the
stop while leaving launch and turn-in untouched. ⚠️ both pinned at −1 after the **08-14 wall hit**
(they slew the MANUAL STICK) ⇒ **operator call, never a quiet change.**

🔧 **USB WEDGE — AND THE ESCs CANNOT BE REPLUGGED.** 🔴🔴 **THEY ARE PERMANENTLY MOUNTED INSIDE THE
ROVER (operator, 09-14): there is NO physical replug. Recovery is software-only.**
**Symptom:** `Could not read firmware version / Could not connect` on one port while others work.
**Discriminator:** re-read a **working** port — if that succeeds, the tool, bus and build are all
exonerated and it is that device's USB endpoint. 🔑 The failure hits the **first probe read**,
before `controller_id` is resolved and long before any write ⇒ **a wedged ESC is NEVER left
half-configured.**
**Fix, in order:** ① `USBDEVFS_RESET` ioctl on the ONE wedged device (worked 09-13) → ② if ports go
dead entirely, **reset the ESC HUB `1-1.2` (214b:7260)**, which re-enumerates all four at once —
the electrical equivalent of replugging every ESC. ✅ **recovered two dead ports 09-14 with no
physical access.**
⛔⛔ **NEVER LOOP THE RESET OVER SEVERAL DEVICES USING DEVNUMS READ UP FRONT** — resetting the first
re-enumerates the bus and invalidates every other `devnum`; the stale resets then wedge MORE ports.
**That is exactly how `1-1.2.1` and `1-1.2.2` were killed 09-14** (`device not accepting address,
error -71`). One device at a time, re-reading `devnum` immediately before each — or just reset the
hub.
🔴 **DO NOT reset the hub ABOVE it (`1-1`) — both Realtek NICs and the WFB link ride on it.**
`1-1.2` is a separate downstream hub and is safe; confirm with `lsusb -t` first.
⚠️ **`ttyACM` numbering RESHUFFLES after any bus reset** (observed 09-14: ACM0 went from `1-1.2.2`
to `1-1.2.1`) ⇒ **always key on `controller_id`, never on the port name.**

### 🔑🔑 THE Kp RESULT — why RPM mode felt slower than torque mode
Bench, RL unloaded: **drive peak 12.0 A at Kp 0.004 → 20.7 A at 0.008**, against **21.1 A in
CURRENT mode**. Regen 3.7 → 7.3 A. ⇒ **The mode was never the problem. With Kp 0.004 the speed PID
simply never asked for the current.** Stick-to-wheel lag measured 60 ms (Kp 0.004) / 80 ms
(current mode) / **40 ms (Kp 0.008 — the quickest of the three)**. ⛔ **Don't switch to current
mode to "get response back"**: in CURRENT mode a centred stick is a FREE COAST, which makes the
operator's actual complaint (late stops) worse.

### 🔴🔴 FIRMWARE CORRECTION — our "free coast below `s_pid_min_erpm`" NOTE WAS WRONG
`mcpwm_foc.c` ~3330: *"Brake when set ERPM is below min ERPM"* → `control_duty = true;
duty_set = 0.0`, **gated on `CONTROL_MODE_SPEED`**. So below the threshold the ESC applies a
**duty-zero SHORT BRAKE**, not a release. ⇒ **`s_pid_min_erpm` is what FINISHES a stop**, and
taking it to 0 gives that away. Also `foc_math.c:504` — `s_pid_ramp_erpms_s` is applied by
`utils_step_towards`, so **the ramp is SYMMETRIC**: it slews the setpoint down on release exactly
as it slews up.

### The `s_pid_min_erpm` bench test (200 / 100 / 50 / 10 / 0) — and what it proved about METHOD
✅ **0 is measurably the worst** — rpm scatter at rest 0.69 and 0.63% of at-rest samples non-zero,
vs 0.00 twice at 50. **50 and 100 are INDISTINGUISHABLE**; operator chose 100, then a repeat run
at 50 replicated zero scatter twice and he settled on **50**.
🔴 **Metric traps that produced nonsense before being fixed — don't repeat them:**
- **Breakaway/dead-band is NOT measurable here.** Stiction exceeds the release band; spread WITHIN
  one setting exceeded the spread BETWEEN settings. It also silently measures **how fast the
  operator pushed the stick** — that artefact made min_erpm 10 read 18.4%, worse than 200.
- **Standing current does not replicate** (0.072 / 0.112 / 0.130 A at the same setting) — it sits
  inside the current sensor's own noise band. **Ignore it.**
- **A run's single worst sample is not a statistic.** "rpm max" gave a non-monotonic mess; std and
  "% of samples non-zero" gave a clean answer.
- ⛔ **Unloaded runs CANNOT measure braking** — peak regen unloaded was −3.7 A, below even the old
  −5 A cap, so the −10 A change was never exercised on the bench.

### ✅✅ FLOOR RESULTS, all four, 2026-09-13 — **THE LATE STOP IS FIXED**
**Straight stops, stick release only, n=5: median 0.52 s / 0.19 m / 1.28 m/s²** from 0.63–0.95 m/s.
🔑 **That is roughly HALF the distance the dedicated RC brake channel achieved on 09-09**
(0.30–0.50 m from ~0.8 m/s) — **without touching the brake lever.**
⚠️ **The regen ceiling starts to bind just under 1 m/s**: the 0.95 m/s stop drew −9.8 A against the
−10 A limit and was the worst of the five (0.93 m/s²); the four slower ones peaked −4.6…−8.6 A.
**Spin (360) stops, n=3 usable: 0.24–0.54 s, 2.6–7.2 m/s²** — about **5× harder than straight**.
Operator's words: *"regen is heavy"*, and it is real. 🔑 **NOT caused by the regen limit** — worst
across 15 spin stops was −5.6 A vs the −10 A cap. It is tyre scrub plus low chassis rotational
inertia plus the duty-zero brake.
⚠️ **Spin stops under ~0.5 m/s entry are UNMEASURABLE** with a 15 rpm "stopped" threshold — the
threshold is a large fraction of the entry speed. Only entries above ~1 m/s count.

### 🔴🔴 TRAP THAT COST A WHOLE FLOOR RUN — **THE SPIN STICK IS ch1 → `roll`, NOT yaw**
`RC_MAP_YAW` reads **4 and is a RED HERRING — nothing is on ch4** (it sat at 1500–1521 µs all run
while the sides counter-rotated 2196 times). Probed live: the 360 stick is **ch1**, arriving as
**`manual_control_setpoint.roll`**. `RC_MAP_THROTTLE`=2 → `.throttle` is correct.
🔑 **`/fmu/out/vehicle_status` DOES NOT EXIST — it is `/fmu/out/vehicle_status_v1`.** Subscribing
to the old name silently yields no arming data, and an "armed" display defaulting on `None`
reported *disarmed* while the wheels were spinning. **Two runs' dead patches were auto-disarm
(`COM_DISARM_PRFLT` 10 s) and could not be proven until this was fixed.**

### 🔧 Tools added (`bldc_can/diag/`)
`step_response_record.py` (DDS only — thr + roll + yaw + ch1/2/4/12 + 4×rpm/current + armed) ·
`step_response_analyse.py` · `step_response_plot.py` · `response_curve_compare.py` ·
`min_erpm_compare.py` · `stop_analyse.py` (straight vs spin stops, distance + decel + regen).

### ⏭ Open after this
⏭ **Operator asked to SOFTEN the brake later** — the targeted lever is **`l_current_min` −25 →
about −15** (motor braking current). ⛔ Not the ramp: the ramp is symmetric and would cost the
launch torque the hub motors need. ⛔ Not `l_in_current_min`: proven not binding in spins.
⏭ **USB HUB PLAN (agreed as the right approach):** all four ESCs on one hub to the companion, so a
change is one pass instead of four cable moves. 🔴 **Every VESC reports the SAME USB serial `304`**
⇒ `/dev/serial/by-id/` COLLIDES; key on **`by-path`** (hub port). `tune_esc.py` verifies
`controller_id` off the device regardless. ⚠️ **Ground loops are the real risk** — USB ground ties
all four ESC grounds to the companion; isolators if it bites.
⏭ **RL is the odd wheel, twice over:** `foc_motor_r` **0.1988** vs 0.4367 / 0.5215 / 0.557 — now
confirmed against all three, its current loop is tuned to a resistance the others don't share;
**re-detection is the fix**. And `l_temp_fet_start/end` **85/100 vs 75/90** on the other three, so
it derates 10 °C later. ⚠️ `si_battery_cells` FL 6 vs 3 elsewhere — FL is correct, cosmetic.
