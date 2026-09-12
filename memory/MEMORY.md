# Vind-Roz Platform Memory
> Auto-loaded each session; also the Phi-3 offline prompt. Live: `~/.claude/projects/-home-roz/memory/` | Backup: `~/codex-work/memory/` → ArvinVeiyon/Companion_Computer_Pxlabs
> ⚠️ **BACKUP IS MANUAL:** `cp -p .../memory/*.md ~/codex-work/memory/` + push. **Never `rsync --delete`** (the mirror is a UNION of 2 scopes).
> ⚠️ **INDEX, NOT A STORE. One line per entry — leave a POINTER, not the fact.** 🔑 Judge by that, not by line count. **Read limit ~17 KB; anything past it is SILENTLY DROPPED.** Compacted 09-12 (25.2→17 KB).

## 📘 THE TWO MANUALS — READ BEFORE ASKING THE OPERATOR OR DERIVING ANYTHING
📐 **`~/ros2_ws/docs/autonav_reference.md`** — *what is TRUE and why.* §5 constants+methods · §10 faults · §11 rules · §12 ladder · §13 dated fitness. **A bare `§N` below = this file.**
📕 **`setup_manual.md`** — *what to DO.* §C nodes (§C10: an external mode's needs come from the SETPOINT TYPE) · §D6 arming AutoNav · §E2b map verification · §A7 param changelog (`RO_*` rover-only vs `EKF2_*` **SHARED WITH THE DRONE**). ⚠️ Part A mostly UNVERIFIED.
📗 **`docs/README.md` = THE DOC INDEX, open it.** `autonomy_plan.md` M0-M4 = the ONLY mode numbering · ⚠️ `ros2_architecture.md` STALE · 🗄 `roadmap.md` archived. 🔑 **Count of sources ≠ weight of evidence** (08-10: the lone dissenting doc was right).
🔑 **Arming AutoNav: external mode, NO RC switch slot** ⇒ RC arm lands in **Manual**; arm there, then companion sends `DO_SET_MODE main=4 sub=11`. ⛔ **NEVER arm AutoNav on stands with the EKF bridge running** (self-sustaining limit cycle). → setup_manual §D6

## [MEMORY_FILES]
**feedback (RULES) — 🔴 OPEN THE FILE, THE ONE-LINER IS NOT THE RULE:** `ask_before_param_change` **(⛔ NEVER WRITE A VEHICLE PARAM WITHOUT AN EXPLICIT YES; reading is free)** · `verify_after_editing` **(grep TWICE: the OLD CLAIM *and* what SURVIVED)** · `notify_before_recording` · `answer_short` · `explain_in_prose` · `defer_memory_updates` · `debug_before_documenting` · `scope_px4_params_by_control_flags` · `test_before_concluding` · `log_the_discriminator` · `independent_rulers` · `check_docs_before_measuring` · `eliminate_hypothesis_whole_family` · `crash_recovery_checkpoint` · `use_dds_not_mavlink` · `camera_qgc_only` · `dkms_arch` · `wlan0_persistent_name`
**reference:** `esc_telemetry` (🔴 `esc_errorcount` = COUNT not code · slots 5+6 = BRAKES · **ESCs in CURRENT/TORQUE mode** · QGC ESC health dead as a detector) · `px4_vio_collision` (✅ our bridge IS on the PX4 navigation interface; 🔴 the collision/planner half is MC-ONLY) · `this_machine` (**incl. the 09-12 `$HOME` layout**) · `rover_odometry` · `services` · `wfb_ng` · `wfb_rlyctl` · `wfb_cfg_apply` · `uart_map` · `known_fixes_archive` · `gcs_companion_interface` · `ros2_nodes`/`ros2_topics` · `todos.md`
**project — ACTIVE:** `rover_autonav` · `indoor_mapping_slam` (§13-17) · `perception_3d_costmap` · `autonomy_plan_reframe` · `vesc_can_flashing` (POINTER FILE: 🔴 `60_mk5.bin` OVER DRONECAN = BRICK, USB ONLY · VESC Tool over CAN IMPOSSIBLE · 🅿️ companion CAN integration DROPPED, ⛔ don't re-debug the MCP2515 · ⏭ `codex-work/bldc_can/RESUME.md`)
**project — other:** `fc_hardfaults` · `rc_ch10_reboots_companion` · `l4_gemini_nav2_prereqs` · `vision_multicam_upgrade` · `l2_floortest_wheel0_reversed` · `wfb_undervoltage_dead_nic` · `external_wifi_uplink` · `gcs_link_degraded` · `relay_ntp_setup` · `relay2_relaystn` · `companion_network_degraded` · `boxb_pcie_usb` · `codexrelay_divergence` · `codexwork_token_in_remote` (🔴 PAT) · `codexwork_branches`
🗑 **Moved out of this index 09-12:** `$HOME` reorg → `this_machine` · full param audit → `project_rover_autonav`.

## [WORKING ON THIS MACHINE]
🗂️ **`$HOME` layout, the moved map, and the 85%-full disk → `this_machine`.** ⛔ `ros2_ws` + `codex-work` did NOT move.
⚠️ **sudo NEEDS the password:** `printf '1987\n' | sudo -S …`
⚠️ **`pkill -f <pat>` MATCHES MY OWN SHELL** (self-kill, exit 144). Use `pgrep -x` / `pgrep -f "[p]attern"` then `kill`.
🔴 **I AM A MAJOR CPU CONSUMER:** `claude` runs 55-86% of a core. Power check `vcgencmd get_throttled` (0x0 clean).
✅ **I can read/write PX4 params myself** — `tools/set_param.py`. Don't ask the operator to read QGC.
📄 **Measurement hygiene · `cpu_catcher.sh` · "prove the DETECTOR was live" → `this_machine`.** 🔴 **EVERY NIC NAME IN THE DOCS IS STALE** (`lsusb` first). ⚠️ Boot clock WRONG until NTP steps it. ⚠️ Replays `ROS_DOMAIN_ID=42`, live 0.

## [CURRENT STATE]
🔑 **THERE IS NO VIO, AND NEVER WAS** — position = wheel ERPM + camera gyro dead reckoning; RTAB-Map CONSUMES our TF odom. **Don't propose adding VIO.** → §6
🔑 **PX4 NEVER KNOWS WHERE IT IS, BY DESIGN** — the bridge sends VELOCITY only. ⚠️ Always state the bridge's state when quoting `v_xy_valid`.
🔴 **LOCALIZATION DEAD — 0 accepted of 20 on the map's OWN bag ⇒ pipeline fault, fails at GEOMETRY not appearance.** ⛔ never lower `Vis/MinInliers` · ⛔ don't re-map the house · ❌ the DB-param-mismatch lead is DEAD. 🔴 `fx` = **304.05 @640×360**. → `indoor_mapping_slam` §17
✅ **2D GRID IS FINE** — ⛔ don't "fix" `MaxGroundHeight` (keep 0.10) or `NormalsSegmentation`.
🗺️ **GOOD ROOM MAP `rover_data/maps/house_map_v4.db`** (bag `map_run_20260809_185011`) — walls single, scale tape-verified.
🔴 **THE REAL CONSTRAINT IS THE ROOM: ~2 m² open floor vs a 0.73×0.56 m rover.** ⛔ **T2 CANNOT RUN HERE** (needs ~3.05 m). ⏭ operator venue call: corridor · re-scope · drop this room as M3.
⛔⛔ **THE CAMERA IS MOUNTED CORRECTLY — STOP RAISING "CAMERA ROTATED"; the operator has been right every time.** ✅✅ **G0 CLOSED 09-11** — verified at a wall; `cam_pitch` 0.0251 / `cam_roll` −0.0078 / `front_overhang` 0.337 / scale 0.9845 ⇒ ⛔ **don't re-derive.** 🔑 only `wall_probe` can see yaw. → `project_rover_autonav` 09-11
✅ **"uXRCE UART REBOOTS THE COMPANION" = RC CH10, NOT A FAULT** (2014=reboot · 1514=shutdown · 1011=safe). 🔑 **CHECK CH10 BEFORE debugging any companion restart.** → `rc_ch10_reboots_companion`
🔴 **FC HEADING IS UNUSABLE — it is the EKF's FUSED YAW, not the gyro.** 2 untested suspects: `bmm350` (`EKF2_MAG_TYPE=1`) · GPS (`EKF2_GPS_CTRL=7`). ⚠️ the DRONE shares this FC and needs both. → §6
🔬 **DISPROVEN 08-09, don't re-propose:** map coverage · light/exposure (⚠️ tested in DAYLIGHT) · rover inside the 0.308 m depth min · camera-gyro rate-dependent scale · `yaw_source: wheels`.
✅ **LADDERS: M0-M4=goal · L0-L5=capability · R1-R7=reqs.** ⏭⏭ THE PLAN = `todos.md` §REQUIREMENTS REALIGNMENT, gates G0-G7.
⏭ **QUEUED:** bridge `vehicle_angular_velocity` to DDS (`dds_topics.yaml:60`) — would decouple odometry from the camera; needs an FC flash, pair with other FC work.

## [AUTONAV — ARMED STATE]
✅✅ **09-12 ARMED AUTONAV ENGAGED (nav_state=23), FIRST TIME. REPEATABLE:** reboot FC → restart `rover-ekf-bridge` + `rover-autonav-mode` TOGETHER (registration needs DISARMED) → verify 3 gates → arm ch5. 📏 `eph` ~0.002 m/s ⇒ **~35 min of budget, not a race.** → `project_rover_autonav` 09-12
🔴🔴🔴 **ARMED AUTONAV IS REFUSED BY `eph` vs `COM_POS_FS_EPH`=5 m, NOT by the mode/bridge/registration.** PX4 relaxes requirements DISARMED, enforces them ARMED. ⛔ **NEVER call S1/AutoNav "works" or "broken" without the `eph` at that moment.** ⏭ the durable fix is LOCALIZATION feeding position. ⚠️ raising the threshold disables a real failsafe — operator call only.
⛔⛔ **PX4 WILL NOT REGISTER AN EXTERNAL MODE WHILE ARMED.** DISARM → restart the node → confirm registration → ARM. 🔴 **AN FC REBOOT WIPES IT AND THE NODE DOES NOT NOTICE.** 🔑 proof = the arming-check handshake counts, NOT `is-active`. ⚠️ `COM_DISARM_PRFLT`=10 s auto-disarms an idle armed rover.
🔑🔑 **EVERY AUTONAV RUN NEEDS `rover-ekf-bridge` FIRST** (FLOOR only — the limit-cycle hazard is wheels-UP; stop it after). Without it the mode is refused ARMED, accepted DISARMED. → setup_manual §C10
⛔⛔ **THE KILL SWITCH IS `ch12`, NOT ch8** (`RC_MAP_KILL_SW`=12 · `ARM_SW`=5 · `FLTMODE`=6 · `KILLSWITCH_TH` 0.75; nothing is on ch8). 🔴 It cost a real armed run 09-12. ✅ fixed in all 6 moving tools (`6506bdb`).
⬜ **S1 = INCONCLUSIVE, NOT FAILED** — ch12 was never pressed. ⚠️ **The criterion is also suspect: PX4 KILL ≠ DISARM.** Settle what S1 means before re-running.

## [MOTION / SAFETY]
✅ **REFLEX COLLISION-STOP: fail-open FIXED 08-10, 4/4 validations** — perception-health gate BEFORE the clearance test (`min_valid_fraction` 0.35). 🔑 CUE: `BLOCK forward (BLIND)`. 🔑 **A high NaN count is NOT blindness — the corridor filter drops everything outside 0.275 m by design.** → §8/§12
🔴🔴 **SPEED COMMANDS ARE NOT HONOURED — SAFETY-CRITICAL.** 🔴🔴 **09-12 PROVEN ON THE FLOOR: AT A CONSTANT STICK THE ROVER NEVER SETTLES — it accelerates for as long as you hold it (ERPM 82→564 at flat 2.7 A). THE OVERSPEED IS AN INTEGRAL, NOT A RATIO — ⛔ STOP QUOTING "5.5×".** Throttle is TORQUE ⇒ `RO_MAX_THR_SPEED` describes a relationship that DOESN'T EXIST; ⛔ don't calibrate it. **DURATION is the control** (2.5 s at 0.11 → 2.2 m/s, 3.2 m, stopped 0.185 m from a wall). → `project_rover_autonav` 09-12
🔴🔴 **COMMANDING 0.0 m/s DOES NOT STOP THE ROVER** — measured twice, 100+ rpm after zero; stopped only by DDS force-disarm.
✅✅ **BRAKE vs COAST — MEASURED 09-12, BOTH TO A FULL STOP, same floor: brake **1.44 m/s²** (0.22 m from 0.8 m/s) vs coast **0.46 m/s²** (0.70 m) ⇒ **3.1×**.** The old "3.4× PROVISIONAL" is superseded. 🔴 **THE BRAKE TAKES ~0.3 s TO BITE** (0.14 m of the 0.925 m stop happened before it engaged). 🔑 regen capped at **−4.99 A ⇒ `l_in_current_min` −5 A IS the binding limit**; authority FADES as it slows. ⛔⛔ **ZERO THROTTLE = FREE COAST — 1.78 m from 1.40 m/s**, which is why the standoff is SPEED-BOUND.
🔴 **THE REFLEX STILL CANNOT BRAKE — but the path is now open.** Slot 5 = RC passthrough, unreachable from software. ✅ **09-12 operator set `UAVCAN_EC_FUNC6`=301 (`Peripheral_via_Actuator_Set1`) + MIN/MAX/FAIL, persisted.** ⏭ **INERT until all 4 VESCs are reflashed to read RawCommand idx 5.** ⛔ −1.0=off, 0.0≈50% brake, value LATCHES. → `reference_esc_telemetry` · `project_rover_autonav` 09-12
🔑 **`esc_count` IS 6 (09-12).** ⛔ QGC ESC health PERMANENTLY LIT ⇒ read `esc_online_flags` over DDS. ⛔ **NEVER index `esc[]` by position — key on `esc_address`.** ⛔ `UAVCAN_EC_MIN1..4`=110 / `MAX1..4`=8082 DELIBERATE.
✅✅ **ODOMETRY: `erpm_to_ms`=0.003900 VALIDATED ON THE FLOOR 09-12 — `/scan` 3.188 m vs wheels 3.469 m = 8.1% over-read ⇒ ⛔ NEVER RE-OPEN THE SCALE; the ~10× conflict is DEAD.** 🔴 **THE ADDR-10 SIGN FIX IS CONFIRMED BY THAT RUN — the old `-1` would have read HALF.** (🔴 `si_motor_poles` is a LINKED PAIR — "fixing" poles SILENTLY HALVES `/odom`.) **ADDR 10=RF 11=FL 13=RL 12=RR.** ⚠️ slip grows with acceleration (13% hard). → §5/§10/§13 · `project_rover_autonav` 09-12
🔑 **`esc_current` = the LOADED/UNLOADED ruler, and NEGATIVE current is the proof the brake engaged** · `/odom` DRIFTS AT STANDSTILL ⇒ corroborate with `sensor_combined`.
🔴 **TRAPS THAT WILL BITE AGAIN:** a DISARMED external mode reads SELECTED but is NOT RUNNING · never quote "last scan → wheels stopped" as reflex latency · `/scan` does NOT come back after a scan-killing test. ⛔ **Never read a quiet topic as evidence — prove a NON-ZERO baseline first.** 🔴 **09-12: `/scan` ALSO DOES NOT TRACK BEYOND ~3 m** (the 0.275 m corridor spans ±4° there) — **park ~2.5 m out to measure.** → §10
🔴 **08-16 I KILLED THE GCS MAVLINK LINK — ONE `mavlink_shell.py` PER FC BOOT, NEVER RETRY AN EMPTY RESULT.** Recovery = reboot over DDS. → `mavlink_shell_session_exhaustion`

## [TODOS] → memory/todos.md
⏭⏭ **FOCUS (operator): AUTONAV.** The plan is `todos.md` §REQUIREMENTS REALIGNMENT + START HERE. 🔑 **GATES IN DEPENDENCY ORDER G0→G2→G3, NOT numerically** — M2 needs no map/localization, so G1 gates only M3. **G0** ✅ 09-11. **G2** = the loaded throttle ladder (⚠️ REFRAMED 09-12) + ESC zero-dropout. **G3** = ⏭ **OPERATOR VENUE CALL, gates G2 too** (needs ≥2 m corridor).
✅ **FC HARDFAULTS CLOSED 08-29 — ⛔ DON'T REOPEN.** 🔴 **ONLY LIVE HAZARD: the fw is OUR OWN BUILD ⇒ ANY reflash from upstream or `~/apps/fc_firmware` BRINGS THEM BACK — verify by GIT HASH, not `flight_sw_version`.** Flashed `a52c38b07d`, protected by **tag** `pxlabs-v1.17.0-r2-Beta` (⚠️ the `-dev` branch was force-pushed). → `fc_hardfaults`
🔧 **PX4 PARAMS — READ THE FC, NEVER TRUST A SNAPSHOT** (values + RCA → `px4_param_audit.md` · RC procedure → `rc_configuration.md` §6 · **full 09-12 audit → `project_rover_autonav`**). 🔴 **KEEP `RO_ACCEL_LIM`/`RO_DECEL_LIM` AT −1 — they SLEW THE MANUAL STICK** (08-14 = a wall hit); ⚠️ but −1 also guarantees waypoint overshoot in auto. ⚠️ **`set_param.py` = MAVLink, RAM-ONLY, FLOAT-ONLY; INT32 → `diag/set_param_int.py` · save → `param_save.py` · reboot → `fc_reboot.py`** (QGC writes persist). 🔑 **`<no reply>` = WRONG NAME far more often than "busy" — PROVE IT WITH A FAKE-NAME CONTROL.** 🔴 **`NAV_RCL_ACT` reads 1 (Hold), NOT 6 — RC loss will NOT disarm.**
🔑 **BOOT-CLOCK TRAP: this box's journal restamps early boot** — `ExecMainStartTimestamp` + `NRestarts=0` forged a convincing "up 11 h" on a 4-minute-old service. **CHECK `/proc/uptime` BEFORE READING ANY DURATION OFF A TIMESTAMP.**
**Numbered backlog → `todos.md`** (⚠️ `5. Antenna tracker HW` is ONLY there). 🔴 **NO Wi-Fi fallback — remote = WFB → relay:2222**; ⚠️ 09-03 eth0 wired `ssh roz@10.10.10.10`, UNTESTED → setup_manual §E5b · ⏭ **#27:** reflex `/scan_3d` is a param (`collision.scan_topic`), still `/scan` — needs ONE low object `/scan` misses · #25 still keys `/dev/video0`.
**[OUTDOOR] O1-O5:** STL-19 · DroneCAN GPS · lidar SLAM · GPS Nav2 · outdoor safety. **WFB parked: #22 = HARDWARE, reseat drone NIC-A ant0.**
⚠️ **`align_mode:=HW` untested** — would kill the depth-glitch class, save 71%/core. ⚠️ Orbbec clone is GITIGNORED — a re-clone RESTORES #26 (patch `codex-work 16665f5`).

## [FPV CAMERAS] → `docs/vision_streaming.md` (autonomy camera → setup_manual C2)
Both FPV-capable, port 6-2, **swap from QGC only**; LG Smart Cam is current. ⛔ **Never key a camera by `/dev/videoN`** — only `usbcam-<vidpid>-<serial>-i<iface>`. ⚡ FPV video costs `/scan` 28.4→22.3 Hz. ⛔ Do NOT modify the ffmpeg line (vetoed). ⚠️ `vision_streaming` RUNNING ≠ streaming.
## [WFB_NG] → `reference_wfb_ng.md` (**PARKED — only action left is HW: reseat drone NIC-A ant0**)
**Drone TX is flawless — when video breaks WFB's input queue is EMPTY: SUSPECT THE SOURCE.** ⚠️ the measurement METHOD cost a week — read the file before measuring anything radio.
## [RELAY_STATION] → `relay2_relaystn`
`vind-rly` RPi5 | `ssh vind-admin@10.5.5.77` (sudo needs a password) | tunnel 2222→drone :22 | NO RTC | old SD card @ `70ef6aa`. ✅ 08-28 closed: relay MAVLink + the cluster-wipe loop. ⛔ no Pi Zero 2 W relay · never `wfb-rlyctl use-cluster` · use `disable`, `mask` FAILS here. 🔑 ping to the QGC laptop is a FALSE NEGATIVE (use `ip neigh`) · a repo pull DEPLOYS NOTHING.
## [REPOS / GCS]
`codex-work` → Companion_Computer_Pxlabs, branch **master** (origin/main stale); **docs live at the ROOT — rover/DroneCAN docs belong HERE, not `ros2_ws`** | `codex-relay` on vind-rly → Relay_Station_Pxlabs | `ros2_ws` → ArvinVeiyon/ros2_ws, on `main`.
GCS: G-Control.exe → pxlabs_cli.exe → SSH relay:2222 → companion:22 | QGC: ArvinVeiyon/PXLABS_qgroundcontrol @ PXLABS-integration
🔴🔴 **2 LIVE PATs STILL UNREVOKED (08-20): `~/git_key` + a CLASSIC scope-`repo` token in `~/.claude/history.jsonl`.** ⛔ **OPERATOR MUST REVOKE IN A BROWSER.** ✅ Revoking breaks nothing (all remotes SSH). 🔑 **NEVER PASTE A SECRET INTO A PROMPT.** → `codexwork_token_in_remote`
## [SERVICE / TROUBLESHOOTING QUICK INDEX] → detail in setup_manual C, D2, E5
**Service state → `reference_services`** (AIDE timer OFF · ⚠️ `tfmini` DISABLED — MUST enable for the DRONE · `rover-ekf-bridge` DISABLED on purpose). 🔴🔴 **`active` PROVES NOTHING — 09-04 and again 09-12 all units read `active` while depth/`/scan`/`/odom` were 0.0 Hz. MEASURE RATES, NEVER `is-active`.**
🔑 **THE ros2 CLI IS ITSELF AN UNRELIABLE RULER** — `node list` ghosts for minutes; `echo`/`hz` can return NOTHING on a live topic. Prove dead with `pgrep`; measure with a direct rclpy subscriber. → `this_machine`
no_MAVLink → `ttyAMA0` + the PX4 MAVLink instance (**DDS fine ⇒ FC alive, reboot over DDS**) | no_DDS → `microxrce-agent`, `ttyAMA4` | WFB_down → `wifibroadcast@drone` | **no_video → CPU-starvation latch FIRST** | no_scan/no_cloud → **restart the camera THEN `rover-scan`/`-scan-3d`/`-odometry`, in that order — 0 Hz forever otherwise** (09-04, again 09-12: the colour stream died ⇒ depth registration had no align target ⇒ every depth frame was dropped)
