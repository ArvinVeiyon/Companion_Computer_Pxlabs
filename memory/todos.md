# TODO List
> ⛔ **The old "do these AFTER a full OS backup" framing is GONE** — it had not applied for months and
> was gating nothing. **Read the REQUIREMENTS REALIGNMENT below; that is the plan.** Everything under
> the older headings is detail, not the agenda.
> 🧹 **Pruned 2026-09-10: 793 → ~540 lines.** Removed were completed items, deleted items, two
> session logs and the withdrawn "camera was rotated" claim. **Every ⛔ "do not reopen / do not
> re-propose" warning was kept** — those are what stop work being redone.

---

# 🎯 REQUIREMENTS REALIGNMENT — 2026-09-04. **READ THIS BEFORE PICKING UP ANY ITEM BELOW.**
> Why: the requirements live in `docs/rover_autonav_requirements.md` (R1-R7), the goals in
> `docs/autonomy_plan.md` (M0-M4 modes, L0-L5 layers, A1-A9 features, S/T tests) — and **this file
> tracked neither.** Most of the list below is radio/vision/hardware; **most of the unbuilt
> requirements had no todo at all.** This section is the bridge. Everything under the old headings
> stays valid as detail, but is no longer the plan.

## 0. LADDER OWNERSHIP — settled, stop re-deriving it
| Scheme | Means | Status |
|---|---|---|
| **M0-M4** (`autonomy_plan.md` §5) | **what the rover DOES for a user** — the GOAL ladder | ✅ authoritative |
| **L0-L5** (`autonomy_plan.md` App. A+B) | **capability layers we must BUILD** | ✅ authoritative |
| **R1-R7** (`rover_autonav_requirements.md` §3) | **the requirements themselves** | ✅ authoritative |
| ~~L0-L7~~ (`rover_autonav_requirements.md` §4 build order) | env-first bring-up order | 🗄 **RETIRED — it is the third scheme.** L0-L4 all closed; its L5/L6/L7 are just M2/M3/the S+T tests. Do not plan off it. |

✅ **DOC FAULT CLOSED 09-04: "the L0-L5 ladder appears TWICE in `autonomy_plan.md`" (flagged 08-10)
is NOT a duplication.** Appendix A = *what to build*, Appendix B = *definition of done*. They agree
layer-for-layer (L0 ✅ · L1 🔧 · L2-L5 ❌). Nothing to resolve, nothing to delete.

## 1. WHERE WE ACTUALLY ARE AGAINST THE REQUIREMENTS
| Req | State | The one thing blocking it |
|---|---|---|
| **R1** localization | 🔴 **DEAD** — 1213 rejected / **0 accepted** (08-16) | live `camera_info` vs the calibration inside `house_map_v4.db` → **G1** |
| **R2** perception | ✅ `/scan` · 🔧 `/scan_3d` exists but **nothing consumes it** | voxel layer + reflex `scan_topic` → **G4** |
| **R3** planning | 🔧 `nav2_forward.yaml`/`nav2_mapped.yaml` written, **never run** | the ROOM (~2 m² free vs 0.41 m² rover) → **G3** |
| **R4** control bridge | ✅ built · 🔴 **speed commands not honoured** (0.05→0.140, 0.25→~0.9) | open-loop `RO_MAX_THR_SPEED` sweep → **G2** |
| **R5** safety | ✅ 1,2,3 proven · ❌ **R5.4 stopping buffer unverified** · ❌ **R5.5 companion-crash disarm NEVER TESTED** | **G2** / **G6** |
| **R6** compute ≤2.0 cores | ❌ **never measured as a total** — and RTAB-Map + voxel go on top | **G4** gate |
| **R7** frames | ⚠️ **the MOUNT IS FINE — the LAUNCH FILE is stale** | update `cam_pitch`/`cam_roll` → **G0** |

🔑 **R1's stated acceptance ("<0.3 m over a 20 m loop") CANNOT BE RUN HERE** — same room constraint
that blocks T2. It needs a corridor or a re-scope; that is an operator decision, see **G3**.
✅ **R1 doc conflict — CLOSED 2026-09-10, it was already fixed and this note was the stale one.**
`rover_autonav_requirements.md` carries the `slam_toolbox` line **struck through** with
*"🔴 SUPERSEDED 2026-08-01 — the map/localization source is RTAB-Map, not slam_toolbox"*. Nothing to
do. ⚠️ Remaining `slam_toolbox` mentions there are in the **retired** L0-L7 ladder and in install
inventories, which are factual.

## 2. 🔴 REQUIREMENTS THAT WERE TRACKED **NOWHERE** UNTIL NOW
Not late — **never filed.** These are the actual product, and none of them is a hardware problem:
- **N1. `/rover_health` monitor (L2, A9).** Level + reason string, never a bare boolean. Every row of
  its watch-table is a failure this project already hit **and only caught by hand** (`eph` 682 m ·
  ESC doze · CPU-starvation latch · yaw 21× command). ⇒ **mandatory for unattended.**
- **N2. Supervisor / decision layer (L3).** Owns the mission above Nav2; Nav2 has no answer to
  "blocked, now what" and both its recoveries are disabled here (blind at 92°). ⇒ **L3 IS the
  unattended milestone** — the first stage that changes what the OPERATOR must do.
- **N3. Waypoint sequencer (A6).** Drive a LIST of goals. Small node. Gates M3 "patrol".
- **N4. Return to base (A8).** ⚠️ **NOT inheritable from PX4** — RTL targets a **GPS** home and on
  this rover drives there with **zero obstacle avoidance**. Must be built in N2.
- **N5. Failsafe policy decisions — design only, no hardware, nothing started:**
  `NAV_RCL_ACT=6` (**disarm**) is right for the bench and **wrong for a mission** · lost-localization
  → stop+hold **does not exist** · no-route-to-goal **does not exist** · battery-low → return
  **not configured**. → `autonomy_plan.md` §6.
- **N6. R5.5 companion-crash disarm** — PX4 offboard-timeout behaviour, never bench-tested.
- **N7. R6 total CPU budget** — measure the whole stack against ≤2.0 cores **before** adding
  RTAB-Map or the voxel layer. ⚠️ **budget for `claude` itself: 55-86% of a core.**

## 3. THE REALIGNED ORDER — gates, not a wish list. Each one unblocks the next.
**G0 — GEOMETRY TRUTH.** ⛔⛔ **THE CAMERA IS NOT ROTATED AND NEVER WAS. THE OPERATOR HAS SAID SO
REPEATEDLY AND HE IS RIGHT — STOP RAISING IT.** The 08-10 "camera physically rotated" claim was
WITHDRAWN 09-04 and re-measured 09-09: **pitch 1.436°, roll −0.447°, |g| 9.7769, sd 0.006, 12,145
samples** (`tools/cam_mount_probe.py`). That is a normal, level mount.
🔑 **What was wrong was the LAUNCH FILE, not the hardware** — it carried the 07-27 `cam_pitch`
0.0406 / `cam_roll` 0.0100 from before the camera came off and went back on the top plate.
✅✅ **G0 IS CLOSED — corrected 09-10 to `cam_pitch` 0.0251 / `cam_roll` −0.0078, and VERIFIED AT A
WALL 09-11:** 5 parkings, fit RMS 0.3-3.4 mm, **inlier fraction 1.00 at every range ⇒ no floor in
the scan**, coverage 0.80 vs the 0.35 threshold, and on operator tape at 1.12 m `/scan` read
**1.4390 vs 1.4344 predicted (4.6 mm)** ⇒ **`front_overhang` 0.337 and scale 0.9845 BOTH STAND.**
Full method, numbers and limits → `project_rover_autonav` 2026-09-11.
**G1 — LOCALIZATION ALIVE (R1).** Live `camera_info` vs `house_map_v4.db`'s calibration. 🔑 **Adjudicate
on the ACCEPTED-FIX COUNT — a changing `map→odom` with 0 accepted is drift, not health.** ⛔ Do not
re-map the house first.
**G2 — MOTION TRUTH (R4, R5.4, T1).** 🔴 **MEASURED OUT 2026-09-12 — IT IS NOW A DECISION, NOT A
TEST.** ✅ closed: the sweep (d), answered in the negative — the constant does not exist; the odometry
scale and sign; `si_motor_poles` (h); the R5.4 stopping numbers; **(b)** gate on `/scan` not `/odom`.
⬜ open: **the duty-vs-torque control decision (blocks R4)** · the brake reflex wiring (R5.4, needs the
VESC reflash) · the zero-dropout floor figure (a) · **T1 re-examined, not re-ticked**.
⛔ Gate every moving test on MEASURED speed, never the command — and on DURATION, not stick position.
→ the START HERE block above · `project_rover_autonav` 09-12.
**G3 — VENUE DECISION → M2 PROVEN.** ✅✅ **DECIDED 2026-09-14: CORRIDOR.** Open since 09-04, now
closed — run T2 there. 🔴🔴 **FIRST MEASURE THE STOP AT `RO_DECEL_LIM` 5:** the reflex's 0.69 m
clearance was sized against a 0.19 m stop, and since 09-14 the reflex rides the SAME throttle ramp
as the manual stick (it publishes a fake `ManualControlSetpoint`), so its stop is no longer the fast
one. ⚠️ `RO_SPEED_LIM` does NOT cap Manual — full stick is 4.93 m/s, which a corridor makes
reachable. Preflight = `tools/preflight_scan_check.py` (passive, mirrors the reflex sector/thresholds).
🗄 superseded options were: corridor (recommended) ·
re-scope T2 to 0.8 m · or drop this room as the M3 target. Then **T2 → T3 → T4 → T5** = M2 done.
⚠️ T3+ need turning, so **S3 (yaw open/closed) gates them.**
**G4 — 3D PERCEPTION (R2/A5) + N7.** Wire `/scan_3d` into a Nav2 `voxel_layer` and flip the reflex's
`collision.scan_topic` (#27 — **needs one low object `/scan` misses** as the proof). Measure R6 first.
**G5 — N1 `/rover_health` (L2).** Faults **INJECTED**, not waited for; 8 checkboxes in App. B.
**G6 — N2+N3+N4+N5+N6 (L3) → M3.** The unattended milestone.
**G7 — M4 outdoor.** O1-O5 + the **mission-ownership decision** (PX4 vs Nav2 — `roadmap.md` picked
Nav2; decide it consciously **before** building, it sets whether RTL is PX4's or ours).

## 4. ⏸ PARKED — real, but NOT on the requirements critical path. Do not let these set the agenda.
WFB block (**only action left is HW: reseat drone NIC-A ant0**) · vision_streaming node fixes (8b,
07-30 item 3) · camera bitrate / v2.3.0 · multicam Phase D · doc-fix items (#5 ch157→ch161, P5
kill-switch doc) · #7 aide.db · #17 delete `camera_sw_node_obsolute.py` · #14 PAT rotation
(🔴 **except the operator browser-revoke, which stays live**).

---

## ⏸ PARKED 2026-09-09 BY THE OPERATOR — brake work, resume AFTER AutoNav

The RC brake is DONE and measured (0.69 m/s², stops in 0.30–0.50 m from ~0.8 m/s, loaded, on the
floor). → `codex-work/bldc_can/evidence/brake_floor_test_20260909.md`. Three loose ends, none
blocking AutoNav:

1. **`codex-work` IS UNCOMMITTED** — 5 modified + 11 new files (both evidence docs,
   `companion_can_driver_status.md`, `rc_configuration.md` §6, four `diag/` tools, three memory
   files). **The PXLABS firmware session cannot pull any of it.** Commit + push when convenient.
2. ✅ **MAVLINK IS BACK — 2026-09-10, came back on its own.** All params read; `UAVCAN_EC_FAIL5`
   = 0, `RC3_MAX` = 1974.0, `RC3_REV` = 1.0, `RC3_TRIM` = 1487.5 (unchanged), `RO_MAX_THR_SPEED`
   = 0.6. **G2 is no longer blocked.** ⚠️ Cause never identified — it may recur.
3. **One clean coast-to-stop** — the coast baseline is n=2, neither segment ran to a stop, so the
   "3.4× better than coasting" and "saves 1.4 m" figures are PROVISIONAL. The braked figures are not.
   Two minutes: spin up, throttle to neutral with ch3 at the bottom stop, roll out untouched.

⚠️ `MEMORY.md` is **19.8 kB against its own 17 kB cap** — needs a compression pass.

## ⏭⏭ START HERE — 2026-09-12 (floor). **G2 IS MEASURED OUT. THE BLOCKER IS NOW A DECISION.**

🔴🔴 **WHAT STOPS US: PX4'S SPEED CONTROLLER CANNOT WORK AGAINST A TORQUE ACTUATOR, AND NO AMOUNT OF
MEASURING CHANGES THAT.** Proven on the floor: at a constant stick the rover accelerates for as long
as it is held, current flat. There is no throttle→speed mapping, so `RO_MAX_THR_SPEED` has no correct
value. ⛔ **Nothing above M1 is safe until this is resolved** — a planner that commands m/s to a
vehicle that integrates torque will overshoot every goal.

### ⏭ THE DECISION (operator's, one of two — I can prepare either)
**(A) MOVE THE ESCs TO DUTY MODE** so throttle means speed and PX4's model matches the hardware.
⚠️ USB + VESC Tool per ESC, all four; VESC Tool over CAN is impossible. ⚠️ Re-validates nothing else —
`erpm_to_ms`, the brake and the sign map all stand. 🔑 Cheapest path to a working `RO_MAX_THR_SPEED`.
**(B) KEEP TORQUE MODE AND REBUILD THE LOOP** — stop leaning on the feedforward, close the loop on
`/odom` velocity in the companion rather than trusting PX4's. ⚠️ More code, no reflash, and it keeps
the ESC config that the brake work already depends on.

### ✅ CLOSED BY THE FLOOR RUNS — do not re-run these
- **(d) open-loop sweep** — answered in the NEGATIVE: the constant does not exist. ⛔ Don't calibrate it.
- **odometry scale + sign** — `/scan` 3.188 m vs wheels 3.469 m = **8.1% over-read**; the addr-10 sign
  fix is confirmed by the same run. ⇒ **(h) `si_motor_poles` is SETTLED — leave it alone.**
- **R5.4 numbers** — coast **0.46 m/s²** (0.70 m from 0.8 m/s) · brake **1.44 m/s²** (0.22 m) ⇒ **3.1×**,
  both runs to a full stop. The "3.4× provisional" is superseded.
- **(b) gate on `/scan`, not `/odom`** — reinforced, with a new limit: **`/scan` does not track beyond
  ~3 m in this corridor**, so park ~2.5 m out to measure anything.

### ⬜ STILL OPEN IN G2 — the rest, in priority order
1. 🔴 **R4 is DIAGNOSED, NOT FIXED.** Blocked on the decision above. **Nothing else in G2 matters
   until it is made.**
2. 🔴 **R5.4 has its numbers but not its capability — the reflex STILL cannot brake.** `UAVCAN_EC_FUNC6`
   =301 is set and persisted, but **INERT until all four VESCs are reflashed to read RawCommand
   idx 5** (`max(idx4, idx5)`, **bounds-check `cmd.len`**). ⚠️ Pair this with (A) if (A) is chosen —
   both need the same USB session on the same four ESCs.
3. ⬜ **ESC zero-dropout (a) — floor figure still missing.** Stands gave **54 ERPM ≈ 0.21 m/s**;
   never measured under load. `field_measure.py dropout`.
4. ⚠️ **T1 NEEDS RE-EXAMINING, NOT RE-TICKING.** Its recorded pass predates all of this, and what it
   measures — sustained speed tracking within ±20% — is exactly what torque mode makes unstable.
   ⛔ Do not treat that tick as evidence until after the decision.
5. ⬜ **A second coast run** to make 0.46 m/s² n=2. Cheap, and every ratio quoted rests on it.

### 🔑 MEASUREMENT RULES EARNED TODAY — read before the next floor session
⛔ **DURATION is the control, not stick position.** 2.5 s at 0.11 gave 2.2 m/s, 3.2 m of travel, and a
stop 0.185 m from a wall — inside the standoff.
⛔ **Park ~2.5 m from a FLAT, SQUARE surface.** Gate on **jitter < 0.05 m AND spread < 0.05 m** before
driving. A sofa gave 0.074 m, then 2.069 m as the corridor flickered between two surfaces.
🔑 **A high NaN count is NOT blindness** — the corridor filter drops everything outside 0.275 m by
design. Judge on whole-scan health plus the nearest in-corridor return.
🔧 **Tooling: `tools/field_measure.py` (nine routines, suggests and never writes) + `rover_diag.py`.**
⚠️ **Five analyser defects were found by checking output against runs readable by eye — all the same
family, a confident number from data that did not support it. Distrust any unchecked analyser output.**

## 🗄 (previous) START HERE — 2026-09-12 (02:00). **RESUME G2.**
✅ **Blocker SOLVED: armed AutoNav engaged (nav_state=23).** Cause was `eph` 307 m vs `COM_POS_FS_EPH`
5 m, not the mode/bridge/registration. Full chain → `project_rover_autonav` 09-12.
**TOMORROW, IN ORDER:**
1. **Reboot the FC** → restart `rover-ekf-bridge` + `rover-autonav-mode` **together, DISARMED** →
   verify 3 gates (`local_position_invalid` false · handshake non-zero both ways · runway).
   ⚠️ `COM_DISARM_PRFLT` resets to 10 s — **ASK before changing it.** ~35 min of eph budget, no rush.
2. **Decide what S1 means first** — PX4 kill ≠ disarm. Then run it and **actually press ch12**.
3. **Then the G2 sweep — `speed_command_test.py`, NEVER RUN YET.** Needs ≥2.0 m corridor; the hall
   gives 4.17 m from the start position. ⛔ Reposition the rover back first — each 3 s run eats ~1.7 m.
4. ⏭ Wire the brake into the reflex (R5.4) — **two runs now show zeroing the setpoint leaves 100+ rpm.**
⛔ **G2 IS NOT DONE. The sweep has not been run once.**

## 🗄 (previous) START HERE — 2026-09-10. AUTONAV.

**MEASURED THIS SESSION, not assumed:** `/scan` **25.8 Hz** · `/odom` **89 Hz** · `camera_info`
**27.2 Hz, fx 304.05 @ 640×360** (the real value — 409.85 @ 848×480 is stale everywhere it appears)
· 🔴 **`/scan_3d` 0.00 Hz while `rover-scan-3d` reads `active`** — the documented trap; the camera is
fine, the node is not. Needed for G4, not for G0–G3. · `rover-ekf-bridge` correctly **inactive**.
✅ **MAVLink came back on its own 2026-09-10** after being dead through 09-09; cause never found, so
expect it to recur. **G2 is no longer blocked.**

### 🔑 RUN THE GATES IN DEPENDENCY ORDER, NOT NUMERIC ORDER: **G0 → G2 → G3**, and let **G1 wait**.
`autonomy_plan.md` §5 is explicit that **M2 needs NO map and NO localization**, and warns in its own
words that *"anything that defers M2 behind mapping work is deferring the only autonomy currently
within reach."* G1 (localization) is the deadest item on the board — **0 accepted fixes out of 20** —
and it gates **only M3**. Nothing in M2 touches it. ⇒ **Do not put localization in front of M2.**

1. ✅✅ **G0 camera geometry — CLOSED 2026-09-11. Nothing left to do here.** The mount is correct
   (measured; see the WITHDRAWN section below), `depth_to_scan.launch.py` carries the measured
   `cam_pitch` **0.0251** / `cam_roll` **−0.0078**, the 09-11 boot made them live, and they were
   **verified at a wall the same night** — fit RMS 0.3-3.4 mm, **inlier fraction 1.00 at every range
   (the real floor-in-scan test)**, coverage 0.80 vs 0.35, bearing +0.30° when squared, and on
   operator tape at **1.12 m** `/scan` read **1.4390 against 1.4344 predicted — 4.6 mm**, so
   `front_overhang` **0.337** and scale **0.9845** both survived the transform change.
   🔑 **`cam_yaw` 0.0 is now CONFIRMED rather than assumed** — gravity cannot observe yaw, so
   `cam_mount_probe.py` structurally cannot check it and only `wall_probe` can.
   ⚠️ Limits, and the one unexplained reading, are recorded in `project_rover_autonav` 2026-09-11.
2. **G2 motion truth.** Open-loop `RO_MAX_THR_SPEED` sweep (reads **0.6** today) · ESC zero-dropout ·
   **(b) gate safety on `/scan` clearance, not `/odom`** — the operator's standing next item.
   ⛔ **Gate every moving test on MEASURED speed, never the command.**
   🔑 **The brake work feeds straight in:** the standoff pass is **speed-bound by the coast**, and at
   ~0.9 m/s the rover contacted the wall with 0.020 m left. The brake now measures **0.69 m/s²,
   stopping in 0.30–0.50 m from ~0.8 m/s**. **Wiring the reflex to command the brake instead of only
   zeroing the setpoint is what lifts that speed bound** — and it now has a number behind it.
3. **G3 venue decision — OPERATOR CALL, open since 09-04.** T2 needs ~3.05 m of clearance against
   ~2 m² of open floor. **Corridor (recommended) · re-scope T2 to 0.8 m · or drop this room as the
   M3 target.** Nothing in M2 can be proven until this is answered.

⛔ **Before any armed autonomous campaign: re-confirm S1 (kill switch)** — inviolable rule 4, and it
is due anyway after the ESC firmware change. **Start `rover-ekf-bridge` first, FLOOR ONLY, stop after.**

## 🔴🔴 [WFB-NG — HIGH PRIORITY] — added 2026-07-30, WORK THIS BLOCK FIRST
> Measured, not theorised. Raw numbers: [[reference_wfb_ng]]. **Read W0 before touching anything.**

### ⚡⚡ 2026-07-31 RESOLUTION — most of this block is now CLOSED. Read this first.
A **20 min simultaneous both-ends run under full video load** settled it. Numbers: [[reference_wfb_ng]].

**THE ONLY WFB ACTION LEFT: 🔴 reseat/replace the drone's NIC-A ant0 u.FL + pigtail + antenna.**
It is ~20 dB deaf (−48.5 vs −28.3 dBm, steady over 224 samples / 20 min). The GS reads both its
antennas identical, so the defect is on the **drone's RX side** — exactly the direction that loses
packets. Re-measure via 8102 immediately after.

| CLOSED 07-31 | verdict |
|---|---|
| **W1** (GS EAGAIN socket overflow ⇒ 15% downlink) | ❌ **DEAD + DELETED.** Tested at 3.2 Mbit/s video + telemetry for 20 min: relay lost **4 video blocks of 341 057**, `wfb-server` PID 696 stable, `NRestarts=0`, zero EAGAIN. |
| **W2.1** trim MAVLink rates | ❌ **DELETED as a fix.** Downlink already delivers ~100%. Buys airtime only; cannot touch the uplink loss or CPU. |
| **W2.2** raise GS `rx_ring_size` (todo #3) | ❌ **DELETED** — nothing is overflowing. Leave at 2 MB. |
| **W2.3** re-measure 176→26 kbit/s | ✅ **DONE — it does not reproduce.** Downlink is 99.86-99.99%. |
| **W2.4 / #6** hardcoded peer `10.5.6.50` | ✅ **CORRECT.** QGC laptop on the relay's Wi-Fi Direct hotspot (`p2p-wlan0-0`, SSID `vind_rely`, ch149, relay 10.5.6.101/24). **Ping fails = Windows firewall, NOT a break.** |
| **todo #4** GS TX power | ❌ **CLOSED — already maxed at 30 dBm** (`wifi_txpower=3000`, regdom BO permits 30). Nothing to turn up. |
| **W3** antenna imbalance | 🔴 **PROMOTED TO ROOT CAUSE — and corrected: only NIC-A is bad. NIC-B is 3 dB, not 9 dB.** |

**Still open beyond the antenna:** (a) uplink GS→drone loses **13.57%** of MAVLink payload /
**5.46%** tunnel, continuous not bursty — expected to improve when the antenna is fixed, re-measure
before doing anything else; (b) relay TX to the laptop at **31 dBm on ch149** shares a chassis with
the WFB RX on ch161 — possible co-located desense, untested; (c) `journalctl -u wifibroadcast@gs`
still unread — **`vind-admin` is in `sudo` but sudo needs a password**, so journald hides the unit.

⚠️ **Method note that cost a week:** compare payload **`tx.incoming` → `rx.out`** across the two
APIs. Do NOT use `rx.all` (the drone double-counts across 4 antennas — makes 13.6% look like 2.4%),
and do NOT infer radio health from MAVLink message rates at two `tcp:5760` endpoints (that path
includes mavlink-router and PX4 stream config — it is what produced the bogus "15% downlink").

### W0. ⛔ FIRST PRINCIPLE — the drone radio is HEALTHY. Stop blaming WFB by default.
First real link measurement (07-30, WFB JSON API on `127.0.0.1:8102`):
- **0 dropped / 0 truncated / 0 fec_timeouts over 117,570 video packets** (whole session, cumulative)
- TX latency 6-35 us avg, 361 us worst | RF temps 32-39 C | `throttled=0x0`
- **~34% airtime** of a 13 Mbit/s MCS1 PHY (~367 pkt/s, ~3.9 Mbit/s injected) — headroom exists
- `mavlink tx`: offers 179 kbit/s, injects 549 kbit/s (k=1/n=3), **drops NOTHING**

**When video breaks, WFB is sitting on an EMPTY input queue.** The 07-30 session proved the FPV
outage was a dead camera while the radio was flawless. **Suspect the source before the link.**
How to check in 5 s: TCP-connect `127.0.0.1:8102`, read newline-delimited JSON, look at
`video tx . packets.incoming[0]`. If it is 0/s, the radio is fine and the camera is dead.
(Counters are `[per_second, cumulative]`. Do NOT use the `wfb-cli` TUI for this.)

### W3. 🔴🔴 RX antenna imbalance — **ROOT CAUSE, and it is ONE chain on ONE card** (rev. 07-31)
20 min / 224 samples, steady throughout ⇒ **not a fade**:

| chain | avg rssi | verdict |
|---|---|---|
| NIC-A **ant0** | **−48.5 dBm** (min −55) | 🔴 **20.2 dB down — FIX THIS** |
| NIC-A ant1 | −28.3 dBm | healthy |
| NIC-B ant256 | −35.0 dBm | 3.0 dB gap, acceptable |
| NIC-B ant257 | −32.0 dBm | healthy |

**⚠️ Corrects the 07-30 table above: NIC-B is 3 dB out, NOT 9 dB. Only NIC-A ant0 is broken.**
The GS reads **both** its own antennas identical ⇒ the defect is **entirely on the drone's RX
side** — which is exactly the direction losing packets (13.57% uplink MAVLink loss vs 0.14%
downlink). 20 dB ≈ 10× range. **Action: reseat u.FL on NIC-A ant0, check pigtail + antenna, then
re-measure on 8102.** This is the whole remaining WFB job.

### W5. MTU margin is thin (hardening, no live fault)
`radio_mtu = 1445`; ffmpeg RTP averages 1354 B and `truncated=0` over 117k packets. But ffmpeg's RTP
default `pkt_size` is **1472 (> 1445)** with no guaranteed margin. Pin `-pkt_size 1400` when the
vision-node flags are applied (session item 3).

### W6. Radio headroom is now MEASURED — unblocks the 07-28 bitrate item
That item recorded headroom as "NEVER MEASURED". It is now: **~34% airtime used of a 13 Mbit/s MCS1
PHY.** There IS room to raise video bitrate — go straight ahead; the old "trim MAVLink first"
precondition is deleted (it was never a fix). ⚠️ But note the real constraint is **CPU, not radio**:
software x264 already needs ~80-95% of a core, see `~/ros2_ws/docs/vision_streaming.md`.

---

## [WFB-NG FIXES] — ⏸ PARKED (the "after OS backup" gate no longer applies)

### 1. Fix GS clock / NTP for real (Relay station vind-rly) — RECURRED 2026-07-11
2026-03-15 fix (`timedatectl set-ntp true` + restart timesyncd) did NOT hold: relay has no RTC and no internet uplink, so `systemd-timesyncd` can never reach `ntp.ubuntu.com` (DNS/network unreachable) and clock drifts to boot-default every power cycle.
Real fix needs a **local NTP server** the relay can actually reach — companion (10.5.5.87) is reachable from relay (10.5.5.77) over the WFB tunnel and has real internet+correct time. Plan: install `chrony` on companion in server mode, allow 10.5.5.0/24, then point relay's `systemd-timesyncd` `NTP=` at 10.5.5.87.
Attempted 2026-07-11, aborted mid-install — see `project_relay_ntp_setup.md` and `project_companion_network_degraded.md`.

### 5. Fix channel reference in PXLABS_qgroundcontrol docs (local edit + push)
ARCHITECTURE.md and DEVELOPMENT.md both say `ch157` — correct value is **ch161**.
Clone repo, search `ch157` / `channel 157`, replace with `ch161` in both files, then push.
Repo: https://github.com/ArvinVeiyon/PXLABS_qgroundcontrol (branch: master)

### 8. Camera preset/RC migration — QGC half ✅ DONE, companion half = multicam Phase D
QGC presets: DONE 2026-07-19 (phase C — hardcoded video0-3 picker + front/bottom buttons
replaced by dynamic camera-list/alias UI; guard implemented in v2.0, discovery fixed v2.1).
REMAINING (Phase D, companion, go-ahead given — see project_vision_multicam_upgrade.md):
migrate to aliases/usbcam ids via v2.1 resolver:
- ros2_ws/src/rc_control/camera_sw_params.yaml:10-11 (front=/dev/video0, bottom=/dev/video2)
- ros2_ws/src/rc_control/config/rc_mapping.yaml:55-56 (same)
  → CH9 plan per design doc: low=FPV primary, mid=FPV+NAV-COLOR PiP, high=spare
- ros2_ws/src/optical_flow/optical_flow/optical_flow_node1.py:36 (/dev/video2)
- ros2_ws/src/optical_flow/optical_flow/optical_flow_node.py:36 (/dev/video3)
  → make device a ROS param (id/alias); WHICH camera optflow should use = open user
    decision (its original camera was physically removed).
  ⚠️ The "= Orbbec IR" annotations on those paths are NOT reliable — the Orbbec only owns
  /dev/videoN while `rover-camera.service` is STOPPED. With the wrapper running these paths
  hit whatever else is there (or nothing). The reason to migrate is that /dev/videoN is
  unstable, full stop — not that it specifically lands on the Orbbec.
✅ Cleanup DONE 2026-07-27: /etc/udev/rules.d/99-usb-cameras.rules **RETIRED IN PLACE**, not
deleted — the file now contains only a comment block explaining why (and a pointer to the
still-stale rc_control paths above). Repo copy restored in codex-work `b80034b` after
`d64850d` committed it empty.

### 8b. Vision open items — added 2026-07-28 (audit found these tracked NOWHERE)
From `~/ros2_ws/docs/vision_streaming.md`; all three were agreed/designed but never filed:
- **(a) backoff reset on the stall path** — `ros2_ws/src/vision_streaming/vision_streaming/
  vision_streaming_node.py:325-326` still resets `backoff_s` to 2 s after a run >60 s that
  **ended in a stall**. Longer waits are what actually recover the camera (16 s → 256 s of
  good video; 2 s → 14 s, dead), so the node earns a working delay and throws it away.
  Agreed fix = do NOT reset on the stall path. **STILL UNAPPLIED, re-verified live 07-30.**
  Item 2 of that list (settle delay with the device closed after a kill) is also unapplied.
  - **❌ CLOSED 2026-07-30 — item 3 (escalate to a USB port reset of 6-2 after N consecutive
    zero-frame starts) is NOT VIABLE. Do not build it.** Measured against a live-wedged LG:
    uvcvideo unbind/rebind → 0 frames; full USB de-authorize/re-authorize → 0 frames;
    retry at 640x480 → 0 frames; GStreamer → 0 buffers. **No software reset recovers this
    camera** — only physical VBUS removal. Replace the idea with: cap consecutive cold-start
    failures, then log a clear "camera requires physical replug" ERROR instead of looping
    silently for 20 minutes. → `~/ros2_ws/docs/vision_streaming.md`
- **(b) USB autosuspend** — `/sys/bus/usb/devices/6-2/power/control` is still `auto`
  (2000 ms). Pin to `on` via udev. "Fix regardless" per the 07-27 evening finding.
  **Priority DOWN 07-30**: hygiene only, already tested and NOT a cause, and the camera on 6-2
  has since been swapped. Do it if a udev rule is being written anyway; don't make a job of it.
- **(c) vision_config_manager v2.3.0 — bitrate control** (feature, not a fix; user's idea,
  agreed, designed, NOT started). Companion half: optional `--bitrate` on `set-cam-params`
  (MUST stay optional — the shipped QGC build calls it without); `update_cam_params_config()`
  gains `bitrate=None`; `list --json` gains `active.settings.{primary,secondary}` so QGC can
  prefill. QGC half is theirs. Constraint: video FEC is k=8/n=12 (50% overhead) and **radio
  headroom has never been measured** — measure before recommending a value. Cheaper first
  lever, also unmeasured: `-preset ultrafast` → `veryfast` (better quality at the SAME
  bitrate, zero extra radio load). Test one lever at a time.
  ⚠️ Do NOT hand-edit the conf as a workaround — [[feedback_camera_qgc_only]].

---

## [ROVER AUTONAV] — added 2026-07-20 (see project_rover_autonav.md)

### 17. Delete camera_sw_node_obsolute.py (added 2026-07-21)
`src/rc_control/camera_sw_node_obsolute.py` (node `camera_node_sw`) logged all 18 RC channels at INFO
on every ~50 Hz callback — ~950 lines/s, which is where the 18 GB of `~/.ros/log` came from. It is not
running (live `rc_control_node` is clean) but should be removed so it cannot be launched by accident.
Local edits from the April STL-19 work were saved to `~/codex-work/ldlidar_stl_local_edits_20260417.patch`
when the unused `ldlidar_stl_ros2` clone was removed the same day.

### 20. Revisit RO_YAW_RATE_P / RO_YAW_RATE_I after a real floor run (added 2026-07-21)
⚠️ **The "← NEXT ACTION" marker on this item was stale and has been removed** — it dated from
2026-07-21 and the plan has moved to the G-gates. S3 (yaw open/closed loop) is already solved.
This is a tuning refinement, not the next thing to do.
**FIELD CHECKLIST tracked at `~/ros2_ws/docs/yaw_tuning_session.md` (ros2_ws main @ 8f84bf1)** — preconditions,
bring-up, baseline-then-tune, opportunistic gyro-yaw + /scan checks, safety, teardown, results-log table.
CONFIRMED NEEDED by the L2 run: armed yaw drove wheels MUCH harder (~700-850 rpm) than forward (~156 rpm).
Those gains were tuned while `RD_WHEEL_TRACK` was 0.43 — a ~39% oversized track, which sized the
commanded wheel differential (Δv = ω × track). The allocation they were implicitly compensating for
has changed now that it is 0.31. The gyro-closed rate loop hides much of this in steady state, so
expect the difference mainly in feedforward/transient response. Re-check after a real floor run.

### 21. Use the camera IMU alongside the FC IMUs (user idea, 2026-07-21) — assess before building
The Gemini 336L has its own IMU (`/camera/accel/sample`, `/camera/gyro/sample`; enable with
`enable_accel:=true enable_gyro:=true`, now on by default in `rover-camera.service`). Ranked by
value, honestly:
1. **HIGHEST VALUE, and it does not need the camera IMU at all: replace wheel-derived yaw with
   GYRO yaw in `rover_odometry`.** Skid-steer yaw from wheel speeds is inherently bad — all four
   wheels *must* slip laterally to turn, so `(v_right − v_left)/track` systematically misestimates
   rotation no matter how perfect the track width is. The FC's gyro/EKF yaw is already on DDS
   (`vehicle_attitude`, `vehicle_angular_velocity`) and is far better. Use wheels for forward
   distance, gyro for heading. This is the standard fix for skid-steer odometry and is likely the
   single biggest accuracy win available before SLAM.
2. **Independent cross-check of FC IMU health.** The camera IMU is a genuinely independent gravity
   reference — it is what let the camera mount pitch/roll be measured tonight. Useful for sanity-
   checking accel calibration (cf. the "accel 0 inconsistency" episode), where the FC's own IMUs
   cannot arbitrate between themselves.
3. **VIO (visual-inertial odometry)** — the ambitious option: camera IMU + depth/colour for
   drift-free-ish motion estimation that survives wheel slip entirely. Real payoff for GPS-denied
   nav, but heavy on the RPi5, which already shares compute with vision streaming (`/scan` alone
   drops to ~13-19 Hz under load). Do NOT start here; revisit only after Nav2 works.
4. **Feeding the camera IMU into EKF2 as an extra IMU: not practical.** PX4 EKF2 has no external-IMU
   input path; only external *vision* pose/velocity, which is what `rover_ekf_bridge` already uses.
**Recommendation: do (1) first — it is cheap, principled and helps SLAM immediately. Keep (2) as a
diagnostic. Defer (3). Drop (4).**

### 14. Rotate the GitHub PAT embedded in the codex-work remote URL
`~/codex-work/.git/config` holds a plaintext `ghp_...` token. Rotate it and switch that remote to SSH.
See `project_codexwork_token_in_remote.md`.

---

## [ROVER OUTDOOR — PRIMARY TARGET] — added 2026-07-23 (see ros2_ws/docs/roadmap.md §4, O1-O5)
Goal: rover drives itself to a **GPS waypoint** in open outdoor space, **360° obstacle avoidance**, no
operator. Indoor GPS-denied (L0-L4 done, L5/L6 next) is the stepping-stone + GPS-loss fallback. These
outdoor tasks come AFTER the indoor brain is proven (L5+L6). Both O1 and O2 need hardware the user is fitting.

### O1. Re-integrate the STL-19 360° LiDAR (blocked on getting the unit back)
LDRobot STL-19: 360° 2D, **0.02-25 m, ~10 Hz** LaserScan; UART **ttyAMA3 @ 230400, RX-only** (lidar TX →
RPi RX, no commands); `dtoverlay=uart3-pi5`, TF `base_link→base_laser` 0.18 m (re-measure mount).
- Hardware went to another team 2026-04-17 → **need the physical unit back first**.
- Driver `ldlidar_stl_ros2` (node LD19) already in `ros2_ws/src` with BOTH upstream fixes applied
  (pthread include + hardcoded `/dev/ttyAMA3`). Local edits: `codex-work/ldlidar_stl_local_edits_20260417.patch`.
- Steps: reconnect hw → enable `ttyAMA3` → build → install/enable `ldlidar.service` (unit template in
  `codex-work/ldlidar_stl19_install_guide.md`).
- ⚠️ **`/scan` conflict**: lidar driver AND `depth_to_scan` both publish `/scan`. Fix: **lidar owns `/scan`**
  (SLAM + 360° costmap); remap depth to **`/scan_depth`** as a separate Nav2 costmap layer.

### O2. Integrate the DroneCAN GPS (blocked on module choice + fitting)
- DroneCAN/UAVCAN bus already live (VESC ESCs addr 10-13) → GPS is one more node on it.
- PX4: enable `UAVCAN_ENABLE` (GPS subclass) + set `EKF2_GPS_CTRL` to fuse GPS (**FC param path, MAVLink-only,
  not DDS**). Verify `/fmu/out/vehicle_gps_position` populates + `vehicle_global_position` goes valid.
- Nav2: outdoor GPS nav via `navsat_transform_node` (robot_localization) or Nav2 GPS waypoint follower.
- **Module make/model: TBD — user to confirm** (sets the exact DroneCAN GPS driver params).

### O3. Outdoor 2D-lidar SLAM (builds on L6)
slam_toolbox on the lidar `/scan` (2D-lidar SLAM is far better than depth-derived scan) + fold the 336L
forward depth in as a costmap layer for low/overhang obstacles the flat 2D plane misses.

### O4. Outdoor Nav2 with GPS waypoints (builds on L5)
`navsat_transform` / GPS-waypoint-follower launch config (distinct from the indoor SLAM launch); global
plan to a GPS coordinate, local costmap from lidar+depth, controller → `/cmd_vel` → autonav_mode.

### O5. Outdoor safety hardening (extends L7)
Terrain handling, dynamic obstacles, and **GPS-loss failsafe → wheel/gyro dead-reckoning + reflex stop,
never an uncontrolled state**. Caveat to design around: STL-19 is a **2D** lidar (fixed-height plane) — on
uneven terrain it can miss low obstacles or read a slope as a wall; the forward 3D 336L covers that gap.

## OPEN ITEMS RAISED 2026-07-26 (the "closed today" log has been removed)

### Opened today
1. ✅ **CLOSED 2026-09-10 — `dtoverlay=disable-wifi` verified.** `wlan0` does not exist and
   `brcmfmac` is not loaded, on a boot many reboots after the 2026-07-26 fix. Nothing further.
   *(This was the check the old "TODO #2" was waiting on; that item was itself verified 2026-08-01
   and has been removed.)*
2. **Establish what NIC RELAY-STN actually has.** `wlx90de80d824d6` is on the companion now, so the
   relay's documented uplink is gone and `.221` does not answer. See [[project_relay2_relaystn]].
   🔴 **09-03: `wlx90de80d824d6` IS NOT ON THE COMPANION EITHER — `0bda:c811` is absent from
   `lsusb`.** The companion uplink is a **TP-Link Archer T2U PLUS `2357:0120` (RTL8821AU)** =
   `wlx8c86dd5beed9`. **So that adapter is loose/elsewhere — find the physical hardware before
   planning around it.** → [[project_boxb_pcie_usb]], [[reference_this_machine]]
3. **Fit the printed camera bracket, then run the 4-step as-built check** at the foot of
   `ros2_ws/launch/depth_to_scan.launch.py` (measure to the left IR imager, re-derive pitch/roll from
   `/camera/accel/sample`, restart rover-scan, tape-measure a `/scan` return). **Blocks L5.**
4. **Crop the rover's own deck out of the depth cloud before the L5 Nav2 voxel layer** — at cam_z
   0.305 with cam_x 0 the top plate fills the bottom ~third of the frame (11.5°/83 px). Harmless for
   `/scan` (±20 px band) but Nav2 would mark a permanent obstacle around its own nose.
5. **Profile `wheel_odometry_node`** — 26.9% CPU for 100 Hz arithmetic is high, and it is in the
   autonomy path where L5 will need the headroom. Suspect the same unthrottled per-message logging
   pattern as tfmini / ros2_ws todo #17.
6. ✅ **CONFIRMED 2026-09-09/10 — the VESCs DO doze off, and it is reproducible.** Measured
   `esc_count 5, esc_online_flags 8` (bit 3 only = addr 13 rear-left) at rest, **before and after an
   FC reboot**; the other three were absent from the bus until the operator powered them for the
   brake test, after which all four reported. ⚠️ **Still UNKNOWN and still the thing that matters:
   can they sleep again WHILE ARMED?** If so `/odom` drops out under the EKF bridge, in the safety
   path. 🔑 **`esc_online_flags` is the cheap check — read it before trusting per-wheel ESC data,
   and never read a missing ESC as a silent one.**
7. **Delete `/var/lib/aide/aide.db.feb22.bak`** (117 MB) once the Feb baseline is definitely not wanted.
8. **Fix `system_files_sync`'s armed-skip** — it skips entirely when the FC reports armed, so it is
   an unreliable backstop during work sessions (this is how the WFB_NICS mitigation was lost on 07-25).

## 2026-07-28 — camera bitrate control (OPEN, agreed, not started)
Raising the camera to 1280x720 left `bitrate = 2000K`, dropping bits/pixel 0.129 → 0.072
(soft picture). QGC has no bitrate control and the conf must not be hand-edited
(QGC-only rule). Add it: companion = optional `--bitrate` on `set-cam-params` +
`active.settings` in `list --json` (→ v2.3.0); QGC = `--bitrate` through
pxlabs_cli/PXLABSApi/CompanionControl.qml. Full design + constraints (FEC k=8/n=12,
radio headroom UNMEASURED, `-preset veryfast` as a zero-radio-cost alternative) in
`~/ros2_ws/docs/vision_streaming.md`. Stopped here 2026-07-28: usage limit.

---

## OPEN ITEMS RAISED 2026-07-30 (the "closed/killed today" log has been removed)

⚠️ **One retraction worth keeping:** *"See3CAM only does ~16 fps on the 480M bus"* was **WRONG**. It
does a real **60 fps** at 720p MJPG over USB 2.0 — the 16 fps was auto-exposure in a dark room.
**You do NOT need a blue USB3 port for full frame rate.** Correct this if it resurfaces anywhere.

### Opened today
1. **Camera swap — PARTIAL SOAK PASSED, finish it after the mount is made.** See3CAM_CU135 fitted
   07-30 23:14 on port 6-2 and selected from QGC (conf `usbcam-2560c1d1-241D8306-i00`, `fps = 60`).
   **Ran 11 min 49 s continuous: 0 errors, 0 stalls, steady ~200 pkt/s / ~250 kB/s, 0 drops.**
   That **beats the LG's best-ever clean window (9.5 min)** and its 448 s from the same night.
   **Ended by a clean PHYSICAL unplug at 23:50:41, not a fault** — user removed it because it was
   dangling on its cable and is building a proper mount for it.
   **REMAINING: refit on the mount, then 20-30 min untouched + a reboot** to finish the verdict.
   ⚠️ **A packet-flow check is NOT sufficient proof** — see opened-item 9.
   ✅ **2026-07-31 — SOAK PASSED.** Refitted on 6-2 and streamed 1280x720 for a **continuous 41.8 min**
   (21:30:01 → 22:11:48, incl. a 19.8 min instrumented window; ended by a **clean service restart, not
   a fault** — `Deactivated successfully`, the usual QGC-camera-change signature):
   `vision_streaming` PID **38192** unchanged across all 40
   health samples, `NRestarts=0`, ffmpeg alive throughout, **0 errors / 0 stalls / 0 dup-padding**,
   62.6-65.3 °C, `throttled=0x0` on every sample. Downlink delivered **234 331 of 234 362** video
   packets (99.99%) end-to-end at the relay — so the picture genuinely moved, not just RTP.
   **ONLY THE REBOOT CHECK REMAINS.** (Load avg 4-7 on 4 cores from software x264 — high but stable.)
2. **Discriminate LG-faulty vs connector-6-2-bad-under-load.** The swap confounds them: See3CAM
   100 mA vs LG 500 mA. Test = put the LG in the free port **`4-1`** (different host controller and
   power path) and soak. **Blocked: enclosure is assembled.** Do it next time it's open.
3. **Apply the vision_streaming_node.py fixes** (all verified live 07-30, all unapplied):
   - `-g 30` + `-tune zerolatency` + `-pkt_size 1400` — **highest value**; x264 default keyint is
     250 frames ≈ 8.3 s at 30 fps, so one lost keyframe smears for up to 8 s over the radio.
   - wire the `fps` conf key through to `-framerate` (currently read by QGC, **never used**).
   - `frame=0` counts as progress → 30 s grace silently becomes ~50 s.
   - backoff reset on the stall path (= item 8b(a)).
   - `rclpy.shutdown()` RCLError — fires on **every QGC camera change**, dumps a traceback exactly
     when you'd be checking whether the swap worked.
   - cap consecutive cold-start failures → log "camera requires physical replug" instead of looping.
4. **🔴 WFB RX antenna imbalance** — ⚠️ these 07-30 figures are SUPERSEDED; only **NIC-A ant0** is
   bad (−48.5 vs −28.3 dBm) and NIC-B is 3 dB, not 9. See W3 above for the corrected table.
5. ❌ **DELETED 08-01 — "trim PX4 MAVLink stream rates".** It fixes nothing: downlink already
   delivers ~100%. Airtime-only, and headroom is now measured at ~34% of a 13 Mbit/s MCS1 PHY, so
   the video-bitrate item no longer depends on it.
6. **Verify the hardcoded GS peer `10.5.6.50`** in `/etc/wifibroadcast.cfg` (`gs_video` :5600,
   `gs_mavlink` :14550) — fixed IP on a subnet unrelated to the 10.5.5.0/24 tunnel. Wrong-IP
   presents as "WFB broken" while the radio is flawless. Check as part of todo #4.
7. **Boot-time clock is wrong until NTP steps it.** `systemd` claimed services started `Jul 29
   00:31`, `last -x reboot` said `Jul 25 11:36`, `uptime -s` said `Jul 30 22:41:45` — all three
   disagree on the same boot. **Journal timestamps around a boot are not trustworthy**; don't
   correlate a WFB event against a vision event across a reboot without checking. Companion has
   internet + NTP synced, so this is boot-window skew only. Related: [[project_relay_ntp_setup]].
8. **`camera_name` fallback in the conf is dangerous.** `/dev/video0` did not exist for most of
   07-30 (nodes were video8/video9). If sysfs `usbcam-*` resolution ever fails, ffmpeg is pointed
   at a node that is not the camera. Consider failing loudly instead of falling back.
9. **Verification method note (about MY checking, not a hardware bug).** A drone-side packet-flow
   check (`wfb_tx video incoming` ~200 pkt/s, 0 drops) does not by itself prove the picture is
   moving. Confirm at the GS when it matters. **No dup-padding problem has ever been observed on
   the See3CAM** — it ran 11:49 clean and the user saw a normal moving picture throughout.

---

## ✅ Historical completed/closed list — REMOVED 2026-09-10

The 2026-08-13 dump of finished items has been deleted; it was a record of work already done and was
not being read. **The one thing that was still live in it: `#21 gyro-yaw` remains OPEN** (see the
ROVER AUTONAV block above).

## 🔧 PX4 PARAMETER AUDIT — 2026-08-14
> 📄 **FULL AUDIT + CHANGE LOG: `~/ros2_ws/docs/px4_param_audit.md`** (every value as read, the
> verified-correct list, findings P1-P9, and the derivations). **Pull from there — not duplicated here.**
> Applied changes also land in `setup_manual.md` §A7, the canonical param changelog.

**Open items:** P1 `RO_MAX_THR_SPEED` 0.60 — its §A7 basis (0.58-0.60 m/s) is CONTRADICTED by the
~0.9 m/s measured 08-12; needs an **OPEN-LOOP throttle sweep** (closed-loop data cannot identify a
plant gain) · P4 `RO_SPEED_TH` −1 would kill the 0.14 floor but is **GATED ON THE ESC-DROPOUT FIX** ·
~~P5 `RC_MAP_KILL_SW`=12 vs docs "ch8"~~ ✅ **DONE 2026-09-12 — docs/tools fixed (`ros2_ws` `6506bdb`).** 🔴 **It had already cost an armed run before anyone actioned it: the operator was told to hit ch8, moved ch5 (ARM) instead, and S1 came back inconclusive.** · P6 read `si_motor_poles` ×4
in VESC Tool · P8 outdoor/M4 params · P9 not audited: `EKF2_*` (SHARED WITH DRONE), sensor/RC cal,
per-ESC output index.

⛔ **SUPERSEDED — DO NOT RE-APPLY.** `RO_DECEL_LIM` 0.5 / `RO_ACCEL_LIM` 0.3 / `RO_SPEED_LIM` 0.60
were applied, saved and reboot-verified on 08-14 — and then **CAUSED A HARD WALL HIT IN MANUAL
DRIVE the same day and were ALL THREE REVERTED.** This entry recorded step 1 and was never updated
for step 2; read as-was it invites someone to restore the crash configuration.

✅ **READ FROM FLASH 2026-08-16, DISARMED — the reverted values are what the FC actually holds:**
`RO_ACCEL_LIM` **−1.0** · `RO_DECEL_LIM` **−1.0** · `RO_SPEED_LIM` **0.70**.
🔑 **The `param save` question (old item (c)) is CLOSED.** The FC hardfaulted and rebooted **≥9
times on 08-16**; RAM-only values cannot survive that, so the revert is provably **in flash**.
The reboot loop accidentally performed the verification nobody had run.
🔴 **SUPERSEDED 2026-09-14 — `RO_DECEL_LIM` IS NOW 5, DELIBERATELY. `RO_ACCEL_LIM` STAYS −1.**
⛔ Do NOT "restore" −1 on the strength of the paragraph above. The 08-14 crash was decel **0.5**
with `RO_MAX_THR_SPEED` **0.60** — a 1.2 s powered ramp-down. That divisor is now **4.93**, so
📏 **ramp = decel ÷ `RO_MAX_THR_SPEED`**: decel 5 ÷ 4.93 = **0.99 s** at FULL throttle, and only
0.05-0.5 s at the 3-30% stick actually used. ⛔ **Never reuse an August decel figure without
redoing that division.**
🔴 They still slew the MANUAL stick **and the collision reflex** (which publishes a fake
`ManualControlSetpoint`), so ⚠️ **re-verify the 0.69 m reflex standoff after any decel change** —
it was sized against a 0.19 m stop. 🔴 And `RO_SPEED_LIM` **does not limit Manual at all**: full
stick is 4.93 m/s, not 0.70. → [[px4_rover_control_scope]], [[scope_px4_params_by_control_flags]]

⏭ **STILL OPEN: ramp-tracking is NOT verified on the vehicle** — nothing has been driven since.
Moot while both limiters are −1 (no ramp to track); it becomes live again only if they are ever
re-enabled. **Gate on MEASURED speed, never the command.**

---

## ✅ FC HARDFAULTS — CLOSED 2026-08-29. ⛔ DO NOT SWAP THE FC. DO NOT REOPEN THIS.

🔴 **The only live hazard, and it is a real one:** the firmware running is **OUR OWN BUILD** with the
NXP fix (PR #28141) cherry-picked. **Any reflash from upstream, or from `~/fc_firmware`, brings the
hardfaults back.** ⇒ **verify by GIT HASH, never by `flight_sw_version`.** Detail: `HARDFAULT.md`,
[[project_fc_hardfaults]].
⚠️ **3 fault logs are still on the SD card, so QGC re-announces them every boot.** That is cosmetic.

## 🗺️ 2D OCCUPANCY GRID — CHECKED 2026-08-16, CLOSED

✅ **The `house_map_v4` grid is roughly correct. ⛔ My earlier "unusable" call was WRONG.**
Method: `tools/grid_review.py`. ⛔ **Do NOT "fix" it:** `MaxGroundHeight` 0.28 is 3× the truth —
**keep 0.10**; and `NormalsSegmentation false` is what produced the ray-tracing spikes that got the
v5 reprocess rejected. **Changing either makes the grid worse, not better.**

### 🔴🔴 THE REAL CONSTRAINT IS THE ROOM, NOT THE MAP
**Rover footprint 0.73 × 0.56 m ≈ 0.41 m² vs ~2 m² of open floor** (≈ a 1.4 × 1.4 m clear patch).
**The rover is a FIFTH of the room's free space.** Add Nav2 inflation and there is almost nothing
to plan through.
⛔ **T2 CANNOT RUN IN THIS ROOM.** Its spec is a **clear 2 m corridor**; `t2_straight_goal_test.py`
refuses to start below `distance × 1.35 + stop_distance` ≈ **3.05 m** of clearance. It would abort
before moving. **T2 is blocked by the ROOM** (the FC no longer blocks it — hardfaults closed 08-29).
🔑 **T2 ADJUDICATES ON TAPE, NOT `/odom`:** its tolerance is 0.20 m over 2 m, but `/odom` under-reads
~24% at crawl (~0.48 m over 2 m) — **the instrument's error is more than twice the tolerance it would
be judging.** The 1.35 factor exists for the same reason: the rover really travels ~2.6 m for a 2.0 m
odom goal.
⏭ **OPEN GOAL-LEVEL DECISION (operator's):** (1) run T2 in a corridor / larger space — **recommended**,
keeps the ladder comparable · (2) re-scope T2 shorter (`--distance 0.8`), proves less · (3) reconsider
whether this room is the M3 target at all — mapped *patrol* in 2 m² is a very small mission.

## ⛔⛔ WITHDRAWN — "THE CAMERA WAS PHYSICALLY ROTATED" (claimed 2026-08-16)

**IT WAS NOT ROTATED. THE MOUNT IS AND WAS CORRECT. THE OPERATOR SAID SO REPEATEDLY AND HE WAS
RIGHT — DO NOT RAISE THIS AGAIN.** Withdrawn 2026-09-04, **re-measured 2026-09-10: pitch 1.436°,
roll −0.447°, |g| 9.7769, sd 0.006, 12,145 samples** (`tools/cam_mount_probe.py`). A normal level
mount. Every camera-referenced constant it declared "suspect" — `front_overhang` 0.337, `/scan`
scale 0.9845, the 0.345 m standoff, the gyro heading TF — **stands.**

🔑 **The only real defect was a STALE CONFIG, now fixed:** `depth_to_scan.launch.py` still carried
the 07-27 values (`cam_pitch` 0.0406, `cam_roll` 0.0100) from before the camera came off and went
back on the top plate. The remount landed ~1° different in each axis — ordinary variation. Updated
2026-09-10 to the measured values, **made live by the 2026-09-11 boot, and VERIFIED against a flat
wall that night — both constants held to 4.6 mm on tape.** ✅ **This sub-item is now CLOSED.**

### 📌 Surviving fact from the deleted 08-16 ESC experiment
⚠️ **The ESC address ↔ WHEEL-CORNER mapping has never been verified against one turning wheel.**
The operator called the removed node "right rear"; the address that left the bus was **10**, which
the docs map to right-**FRONT**. ✅ 2026-09-09 confirmed all four addresses (10/11/12/13) are live
and independently controllable, **but that does not establish which address is bolted to which
corner.** Spin exactly one wheel before trusting per-corner ESC data.

