# Vind-Roz Platform Memory
> Auto-loaded each session; also the Phi-3 offline prompt. Live: `~/.claude/projects/-home-roz/memory/` | Backup: `~/codex-work/memory/` → ArvinVeiyon/Companion_Computer_Pxlabs
> ⚠️ **BACKUP IS MANUAL:** `cp -p .../memory/*.md ~/codex-work/memory/` + push. **Never `rsync --delete`** (the mirror is a UNION of 2 scopes).
> ⚠️ **INDEX, NOT A STORE. One line per entry — a POINTER, not the fact.** 🔴🔴 **CAP = 24.4 KB, THE TAIL IS TRUNCATED SILENTLY.** 17.1 KB = recompaction TARGET, not the ceiling — ⛔ don't obey the hook's nag mid-task. **KEEP ≤20.4 KB**, measured with **`wc -c`** (python `len()` reads ~6% low).

## 📘 THE TWO MANUALS — READ BEFORE ASKING THE OPERATOR OR DERIVING ANYTHING
📐 **`~/ros2_ws/docs/autonav_reference.md`** — *what is TRUE and why.* §5 constants · §10 faults · §11 rules · §12 ladder · §13 dated fitness. **A bare `§N` below = this file.**
📕 **`setup_manual.md`** — *what to DO.* §C nodes (§C10: an external mode's needs come from the SETPOINT TYPE) · §D6 arming · §E2b map verification · §A7 params (`RO_*` rover-only vs `EKF2_*` **SHARED WITH THE DRONE**). ⚠️ Part A mostly UNVERIFIED.
📗 **`docs/README.md` = THE DOC INDEX, open it.** `autonomy_plan.md` M0-M4 = the ONLY mode numbering · 🗄 `ros2_architecture.md` + `roadmap.md` archived. 🔑 **Count of sources ≠ weight of evidence.**
🎯 **`docs/autonav_goal.md` = THE OPERATOR'S GOAL, 11-10, AUTHORITATIVE**: **ORDER 1-10 → top of `todos.md`.**
🔑 **Arming AutoNav: external mode, NO RC switch slot** ⇒ RC arm lands in **Manual**; arm there, then companion sends `DO_SET_MODE main=4 sub=11`. ⛔ **NEVER arm AutoNav on stands with the EKF bridge running** (self-sustaining limit cycle). → setup_manual §D6

## [MEMORY_FILES]
**feedback (RULES) — 🔴 OPEN THE FILE, THE ONE-LINER IS NOT THE RULE:** `ask_before_param_change` **(⛔ NO VEHICLE PARAM WRITE WITHOUT AN EXPLICIT YES)** · `always_push` **(commit ⇒ PUSH; →master ⛔ NOT main)** · `verify_after_editing` · `notify_before_recording` · `describe_before_executing` **(⛔ "armed" is NOT "go")** · `answer_short` · `close_todos_on_completion` · `explain_in_prose` · `defer_memory_updates` · `debug_before_documenting` · `scope_px4_params_by_control_flags` · `test_before_concluding` · `log_the_discriminator` · `independent_rulers` · `check_docs_before_measuring` · `eliminate_hypothesis_whole_family` · `crash_recovery_checkpoint` · `use_dds_not_mavlink` · `camera_qgc_only` · `dkms_arch` · `wlan0_persistent_name`
**project — ACTIVE:** `deployment_architecture` (🔑🔑 **THE PRODUCT + SENSOR DECISION — READ FIRST**) · `rover_autonav` · `esc_config_audit` (⚠️ **HARD NEUTRAL BRAKE: floor-OK 10-24 BY FEEL, never captured** · 🔑🔑 **CRAWL CATCH = THE SPEED LOOP**) · `indoor_mapping_slam` (§13-17) · `perception_3d_costmap` · `autonomy_plan_reframe` · `vesc_can_flashing` (🔴 `60_mk5.bin` OVER DRONECAN = BRICK · ⛔ CAN DROPPED · restore point `20261024_1527` · 🔴🔴 **r1 BIN ≠ r1 TAG — READ THE EMBEDDED HASH**)
**reference:** `px4_rover_control_scope` (🔴 WHICH `RO_*` REACHES WHICH MODE) · `vesc_tool_cli` (🔑 **7.01 HEADLESS, BUILT HERE** · ⛔ NEVER cross-write a wheel's mcconf) · `esc_golden_config` (🔑 `check_ours.py` · 🔴🔴 **A MAJORITY VOTE ACROSS WHEELS IS NOT A RULER**) · `esc_telemetry` · `services` · `this_machine` · `wfb_ng` · `px4_vio_collision` (🔑 **PX4 collision prevention is MULTICOPTER-ONLY**) · `gcs_companion_interface` · `uart_map` · `wfb_cfg_apply` · `wfb_rlyctl` · `known_fixes_archive` · `ros2_nodes` · `ros2_topics` · `rover_odometry` (⚠️ unprefixed file = the 09-19 PLAN; live odom facts → `esc_telemetry`)
**project — other:** `fc_hardfaults` · `rc_ch10_reboots_companion` · `l4_gemini_nav2_prereqs` · `vision_multicam_upgrade` · `l2_floortest_wheel0_reversed` · `wfb_undervoltage_dead_nic` · `external_wifi_uplink` · `gcs_link_degraded` · `relay_ntp_setup` · `relay2_relaystn` · `companion_network_degraded` · `boxb_pcie_usb` · `codexrelay_divergence` · `codexwork_token_in_remote` (🔴 PAT) · `codexwork_branches` · `rc_control_camera_retry_storm` (🔑 runaway `vision_config_manager` — burns a core) · `ros2ws_tag_cleanup` · `mavlink_shell_session_exhaustion`
🔑 **A file this index does not name does not exist at session start** — 10 of the above were unreachable until 09-19.

## [WORKING ON THIS MACHINE]
🗂️ **`$HOME` layout, the moved map, and the disk (61%, 10-29) → `this_machine`.** ⛔ `ros2_ws` + `codex-work` did NOT move.
⚠️ **sudo NEEDS the password — ⛔ NOT STORED HERE (removed 11-11): ask the operator**, then `printf '<pw>\n' | sudo -S …`. ⛔ never write it to a pushed file.
⚠️ **`pkill -f <pat>` MATCHES MY OWN SHELL** (self-kill, exit 144). Use `pgrep -x` / `pgrep -f "[p]attern"` then `kill`.
🔴 **I AM A MAJOR CPU CONSUMER:** `claude` runs 55-86% of a core. Power check `vcgencmd get_throttled` (0x0 clean).
✅ **I can read/write PX4 params myself** — `tools/set_param.py`. Don't ask the operator to read QGC.
⚠️ **ANYTHING THAT MAY RUN >30 s MUST SAY SO OR GO TO BACKGROUND** — a silent terminal reads as a dead box from the operator's chair. ⛔ never regex-sweep `~/.claude/projects/-home-roz/*.jsonl` (54 MB; one such grep took 2m11s).
📄 **Measurement hygiene · `cpu_catcher.sh` → `this_machine`.** 🔴 **EVERY NIC NAME IN THE DOCS IS STALE** (`lsusb` first). ✅ Boot clock RIGHT since 11-15 (RTC battery; older boots still wrong) · replays `ROS_DOMAIN_ID=42`, live 0.

## [CURRENT STATE]
🔑 **NO VIO IS *RUNNING*** — position = wheel ERPM + camera gyro dead reckoning; RTAB-Map CONSUMES our TF odom. 🔴 **NOT a capability gap — blocker = CPU + plate-in-frame.** ⛔ Don't say "we can't do VIO" — say what it costs. → §6
🔑 **PX4 NEVER KNOWS WHERE IT IS — BY CONFIG.** `EKF2_EV_CTRL`=**4**=VELOCITY ONLY (target **9**=pos+yaw, setup_manual §A7). ⛔ `EKF2_*` **SHARED WITH THE DRONE** ⇒ operator call. 🔑🔑 **A mission RELATIVE TO START needs NO map/relocalization ⇒ OPEN NOW; only a mission ON A SAVED MAP needs it (the 0/20 blocker).** ⛔ don't say "VIO isn't localization". → `ros2_ws/docs/px4_companion_interface.md` §9
🔴 **LOCALIZATION DEAD — 0 accepted of 20 on the map's OWN bag ⇒ pipeline fault, fails at GEOMETRY not appearance.** ⛔ never lower `Vis/MinInliers` · ⛔ don't re-map the house · ❌ the DB-param-mismatch lead is DEAD. → `indoor_mapping_slam` §17
✅ **2D GRID IS FINE** — ⛔ don't "fix" `MaxGroundHeight` (keep 0.10) or `NormalsSegmentation`.
🗺️ **GOOD ROOM MAP `rover_data/maps/house_map_v4.db`** (bag `map_run_20260809_185011`) — walls single, scale tape-verified.
✅ **GEOMETRY CLOSED 11-10 (operator): the 09/10 frame rebuild DID NOT CHANGE GEOMETRY** — footprint, track, wheelbase, `ObstacleFootprint` 32.0, T3 all STAND. ⛔ **no re-tape, don't raise it.**
🔴 **THE ROOM IS THE CONSTRAINT (~2 m² open floor)** ⇒ ⛔ **T2 CANNOT RUN IN *THIS ROOM*** (✅ PASSED IN THE CORRIDOR 09-16). ⚠️ footprint **0.73 × 0.450 m** (0.560 = a SALES QUOTATION). ⛔ `wheelbase` 0.430 is NOT the track; `RD_WHEEL_TRACK` 0.31 is CORRECT.
⛔⛔ **THE CAMERA IS MOUNTED CORRECTLY — STOP RAISING "CAMERA ROTATED"; the operator has been right every time.** ✅✅ **G0 CLOSED 09-11**, verified at a wall ⇒ ⛔ **don't re-derive the mount numbers.** → `project_rover_autonav` 09-11
✅ **"uXRCE UART REBOOTS THE COMPANION" = RC CH10, NOT A FAULT** (2014=reboot · 1514=shutdown · 1011=safe). 🔑 **CHECK CH10 BEFORE debugging a companion restart** — but a journal that just STOPS (no systemd shutdown sequence) EXONERATES IT. → `rc_ch10_reboots_companion`
🔴 **FC HEADING IS UNUSABLE — it is the EKF's FUSED YAW, not the gyro.** 2 untested suspects: `bmm350` (`EKF2_MAG_TYPE=1`) · GPS (`EKF2_GPS_CTRL=7`). ⚠️ the DRONE shares this FC and needs both. → §6
🔬 **DISPROVEN 08-09, don't re-propose:** map coverage · light/exposure · rover inside the 0.308 m depth min · camera-gyro rate-dependent scale · `yaw_source: wheels`.
✅✅ **PRODUCT SETTLED 09-21 — OPEN `deployment_architecture` BEFORE ANY SENSOR/SCOPE TALK:** mission on a **PRE-BUILT MAP** at a bounded **SITE** (not a house), GPS an **AID only**, **INDOOR FIRST**. ⛔ ladders + A1-A9 UNCHANGED. ✅ **CAMERA PRIMARY**, ⛔⛔ **NOT REPLACEABLE BY A LiDAR** (RTAB-Map fuses both). 🔑 **VIO REPLACES ENCODERS, NOT GPS ⇒ publish the MAP-RELATIVE pose.** 🔴 **NEXT = A DIAGNOSIS, NOT A PURCHASE.**
✅ **LADDERS: M0-M4=goal · L0-L5=capability · R1-R7=reqs.** ⏭⏭ THE PLAN = `todos.md` §REQUIREMENTS REALIGNMENT, gates G0-G7.
⏭ **QUEUED:** bridge `vehicle_angular_velocity` to DDS (`dds_topics.yaml:60`) — decouples odometry from the camera; needs an FC flash.

## [AUTONAV — ARMED STATE]
✅✅ **ARMED AUTONAV REPEATABLE:** reboot FC → restart bridge + autonav-mode TOGETHER (registration needs DISARMED) → verify 3 gates → arm ch5. 📏 budget ~45-60 min per bridge restart.
🔴🔴🔴 **ARMED AUTONAV IS REFUSED BY `eph` vs `COM_POS_FS_EPH`=5 m, NOT by the mode/bridge/registration** (requirements relaxed DISARMED, enforced ARMED). ⛔ **NEVER call S1/AutoNav "works" or "broken" without the `eph` at that moment.** ⏭ durable fix = LOCALIZATION; ⚠️ raising the threshold = operator call only.
⛔⛔ **PX4 WILL NOT REGISTER AN EXTERNAL MODE WHILE ARMED.** DISARM → restart the node → confirm registration → ARM. 🔴 **AN FC REBOOT WIPES IT AND THE NODE DOES NOT NOTICE.** 🔑 proof = the arming-check handshake, NOT `is-active`.
🔑🔑 **EVERY AUTONAV RUN NEEDS `rover-ekf-bridge` FIRST** (FLOOR only; stop it after). Refused ARMED without it. ⚠️ armed+idle WITH the bridge = delayed motor KICKS (limit cycle) — disarm between runs. → setup_manual §C10
⛔⛔ **THE KILL SWITCH IS `ch12`, NOT ch8** (`RC_MAP_KILL_SW`=12 · `ARM_SW`=5 · `FLTMODE`=6 · `KILLSWITCH_TH` 0.75; nothing is on ch8). ✅ fixed in all 6 moving tools. ⚠️ **PX4 KILL ≠ DISARM** — settle what S1 means before re-running.

## [MOTION / SAFETY]
✅ **REFLEX COLLISION-STOP: fail-open FIXED 08-10, 4/4** — perception-health gate BEFORE the clearance test (`min_valid_fraction` 0.35). 🔑 CUE: `BLOCK forward (BLIND)`. 🔑 **A high NaN count is NOT blindness** — the corridor filter drops everything outside 0.275 m by design. → §8
✅✅ **SPEED COMMANDS ARE HONOURED — ALL FOUR IN RPM MODE.** `RO_MAX_THR_SPEED` 0.60→**4.93**. ⛔⛔ **EVERY TORQUE-MODE RULE IS HISTORY — do not quote them.**
✅✅ **BELOW `s_pid_min_erpm` = A DUTY-0 SHORT BRAKE** ⇒ ⛔ **NEVER 0**; 🔴 regen cut on a charged pack ⇒ spin-down is SCRUB. 🔴🔴 **THE REFLEX ONLY ZEROES THE SETPOINT — a real brake ONLY at ramp 20000** ⇒ ⛔⛔ **NEVER CUT `s_pid_ramp_erpms_s`** (emergency stop AND yaw onset); ⏭ fix = the reflex COMMANDS a brake. ⛔⛔ **DON'T CHASE IT WITH `l_current_min`.** 🔑🔑 **WHEEL RPM CANNOT MEASURE A STOP — tape or `/scan`** (both brake loggers lie). ⛔ **NEVER reset hub `1-1`** (NICs + WFB). → `esc_config_audit` §THE BRAKE PATH
🔑 **A POWERED-OFF ESC IS INDISTINGUISHABLE FROM A DEAD BUS** (`online_flags` clear + `timestamp==0`). ⛔ **ASK "are they powered?" BEFORE diagnosing CAN** — 🔑 `read_values.py` `v_in` SETTLES IT.
🔴🔴 **PI 5 V: TI DC-DC @5.2 V fitted, VERIFY FAILED 11-11 (mean 4.915 V · 223 dips <4.80) ⇒ ⛔ no armed autonomy, HOLD STAYS** → `todos.md` top. 🔴 **360 DRIFT = FR+RL STALL when scrubbing**; ESCs LIVE = set `20261111_0047` (⛔⛔ ω WIZARD NEVER 2000); 🔑 STALL IS VOLTAGE-LIMITED (~19 A); NO motor thermistor. → `todos.md` pivot item
🔑 **`esc_count` IS 6.** ⛔ QGC ESC health PERMANENTLY LIT ⇒ read `esc_online_flags` over DDS. ⛔ **NEVER index `esc[]` by position — key on `esc_address`.**
🔴🔴 **10-24 OPEN: `esc_status` 0 msgs/30 s while `vehicle_status_v1` FLOWED ⇒ ESC→FC *TELEMETRY* ONLY — COMMANDS ARE FINE (RC drives).** 🔑 **NAME THE DIRECTION BEFORE BLAMING "CAN".** Use `read_values.py`. → `esc_telemetry`
🔑🔑 **"ESC 1/2" IN A PX4 MESSAGE NAMES A SIDE, NOT A WHEEL** (3/4 never appear): Motor1=**RIGHT** (addr 10+12) · Motor2=**LEFT** (11+13) — correct for a diff drive, ⛔ don't "fix" it. → `esc_telemetry`
✅✅ **ODOMETRY: `erpm_to_ms`=0.003900 ⛔ NEVER RE-OPEN THE SCALE.** 🔑🔑 **THE ERROR IS SPEED-DEPENDENT** (under-reads slow, over-reads fast, crossover ~0.25 m/s) ⇒ **QUOTE EVERY ODOM DISTANCE WITH ITS SPEED.** 🔴 `si_motor_poles` is a LINKED PAIR — "fixing" poles SILENTLY HALVES `/odom`. ✅✅ **ADDR 10=FR 11=FL 12=RR 13=RL — VERIFIED 10-24.** → `esc_telemetry`
🔑 **`esc_current` = the LOADED/UNLOADED ruler; NEGATIVE = brake engaged.** ✅ **"`/odom` DRIFTS AT STANDSTILL" IS FALSE** (retracted 09-19, `deadband_erpm` 40→5); ⚠️ unchecked ARMED.
🔴 **TRAPS THAT WILL BITE AGAIN:** a DISARMED external mode reads SELECTED but is NOT RUNNING · `/scan` does NOT come back after a scan-killing test and ⛔ does NOT track beyond ~3 m (park ~2.5 m out) · 🔴🔴 **TURN/360 STICK = ch4 → `.roll`** (ch2=throttle) · 🔴 **it is `/fmu/out/vehicle_status_v1`** — the old name reads "disarmed" while wheels spin. ⛔ **Never read a quiet topic as evidence — prove a NON-ZERO baseline first.** → §10
🔴 **08-16 I KILLED THE GCS MAVLINK LINK — ONE `mavlink_shell.py` PER FC BOOT, NEVER RETRY AN EMPTY RESULT.** Recovery = reboot over DDS. → `mavlink_shell_session_exhaustion`

## [TODOS] → memory/todos.md
✅✅ **T3 IS FINISHED — operator, 10-24** (`ObstacleFootprint.scale` **32.0**). ⏭⏭ **NEXT = THE 11-10 ORDER OF WORK (top of `todos.md`); relocalization 0/20 = DESK, IN PARALLEL.** ⚠️ the avoidance CHAIN is reusable, its odom-frame TUNING is not. ⛔ start nothing that assumes odometry is the POSITION SOURCE.
🔑 **NAV2 RULES — FULL SET IN `todos.md` + `project_rover_autonav` 09-19/20, OPEN BEFORE A RUN.** ⛔⛔ **ARMED RUNS USE `nav2_forward_flat.yaml`, never `nav2_forward.yaml`** (voxel = MAX-RATE SPIN) · ⛔⛔ **DWB reads `sim_time` + critic `scale` AT INITIALISE — a live `param set` DOES NOTHING; YAML + RESTART** · ⛔⛔ **NEVER adjudicate a run from TELEMETRY (no side sensing) — EYES OR TAPE.** ⛔⛔ **NO PIVOTS FROM REST.** 🔴 YAW UNRESOLVED, ⛔⛔ `RO_YAW_RATE_I` STAYS 0.
✅ **FC HARDFAULTS CLOSED 08-29 — ⛔ DON'T REOPEN.** 🔴 **The fw is OUR OWN BUILD ⇒ ANY reflash from upstream or `~/apps/fc_firmware` BRINGS THEM BACK — verify by GIT HASH** `a52c38b07d` (tag `pxlabs-v1.17.0-r2-Beta`). → `fc_hardfaults`
🔧 **PX4 PARAMS — READ THE FC, NEVER TRUST A SNAPSHOT.** ⛔⛔ **NEVER WRITE ONE WITHOUT AN EXPLICIT YES.** 🔴 **`RO_DECEL_LIM`=5 since 09-14, `RO_ACCEL_LIM`=−1**; they slew the MANUAL stick **and the collision reflex** ⇒ re-verify standoff after any decel change. ⚠️ `NAV_RCL_ACT`=1 ⇒ RC loss will NOT disarm. **→ `px4_rover_control_scope`** (ramp arithmetic, scope map, tooling rules)
🔑 **BOOT-CLOCK TRAP (relay; companion boots before 11-15) — `/proc/uptime` BEFORE READING A DURATION OFF A TIMESTAMP;** a GAP in a log may be a clock STEP. → `this_machine`
🔧 **10-29 SAFETY REVIEW (S1/S8/S5) ✅ DEPLOYED `ad95d70`.** ⏭ N6 kill-9 · N8 corridor gate · N9 standoff @0.35 → `todos.md` §2.
**Numbered backlog → `todos.md`** (#23/#24 never used). 🔑 **never cite a number that doesn't exist.** ⛔ **`5. Antenna tracker HW` DROPPED 09-19 — do not resurrect.**
🔴 **NO Wi-Fi fallback — remote = WFB → relay:2222**; ⚠️ eth0 `ssh roz@10.10.10.10` UNTESTED → setup_manual §E5b. **[OUTDOOR] O1-O5:** 360 lidar (TO BUY; ⛔ STL-19 GONE) · DroneCAN GPS · lidar SLAM · GPS Nav2 · outdoor safety. ⚠️ `align_mode:=HW` untested — kills the depth-glitch class, saves 71%/core.

## [FPV CAMERAS] → `docs/vision_streaming.md` (autonomy camera → setup_manual C2)
Both FPV-capable, port 6-2, **swap from QGC only**; LG Smart Cam current. ⛔ **Never key a camera by `/dev/videoN`** — only `usbcam-<vidpid>-<serial>-i<iface>`. ⛔ Do NOT modify the ffmpeg line (vetoed). ⚠️ `vision_streaming` RUNNING ≠ streaming.
## [WFB_NG] → `wfb_ng` (**PARKED — only action left is HW: reseat drone NIC-A ant0 = #22**)
**Video breaks with WFB's queue EMPTY ⇒ SUSPECT THE SOURCE.** ⚠️ the measurement METHOD cost a week — read the file first.
## [RELAY_STATION] → `relay2_relaystn`
`vind-rly` RPi5 | `ssh vind-admin@10.5.5.77` | tunnel 2222→:22 | NO RTC BATTERY; time = companion chrony → `relay_ntp_setup`. 🔴 **SD IS MARCH-VINTAGE, repo has NO REMOTE — a pull DEPLOYS NOTHING.**
## [REPOS / GCS]
📗 **`codex-work/README.md` = THE COMPANION DOC INDEX — open it before hunting for a doc.** ⚠️ distinct from `ros2_ws/docs/README.md` (autonomy side).
`codex-work` → Companion_Computer_Pxlabs, branch **master** (origin/main stale); **docs live at the ROOT — rover/DroneCAN docs belong HERE, not `ros2_ws`** | `codex-relay` on vind-rly → Relay_Station_Pxlabs | `ros2_ws` → ArvinVeiyon/ros2_ws, on `main`.
GCS: G-Control.exe → pxlabs_cli.exe → SSH relay:2222 → companion:22 | QGC: ArvinVeiyon/PXLABS_qgroundcontrol @ PXLABS-integration
🔴🔴 **2 LIVE PATs STILL UNREVOKED (08-20): `~/git_key` + a CLASSIC scope-`repo` token in `~/.claude/history.jsonl`.** ⛔ **OPERATOR MUST REVOKE IN A BROWSER.** 🔑 **NEVER PASTE A SECRET INTO A PROMPT.** → `codexwork_token_in_remote`
## [SERVICE / TROUBLESHOOTING QUICK INDEX] → detail in setup_manual C, D2, E5
**Service state → `reference_services`** (⚠️ `tfmini` DISABLED — enable for the DRONE · `rover-ekf-bridge` + `rover-nav2` DISABLED on purpose, manual start per run; 🔑 restarting `rover-nav2` IS the costmap clear). 🔴🔴 **`active` PROVES NOTHING — MEASURE RATES.**
🔑 **THE ros2 CLI IS ITSELF AN UNRELIABLE RULER** — `node list` ghosts for minutes; `echo`/`hz` can return NOTHING on a live topic. Prove dead with `pgrep`; measure with a direct rclpy subscriber. → `this_machine`
✅ **IS THE BOX ALIVE? `tail -2 /var/log/ext5v/ext5v.csv`** — stamped every 2 s, independent of tmux/Claude ⇒ a fresh row means ALIVE. Use it before ever cutting power on a silent terminal.
no_MAVLink → `ttyAMA0` + the PX4 MAVLink instance (**DDS fine ⇒ FC alive, reboot over DDS**) | no_DDS → `microxrce-agent`, `ttyAMA4` | WFB_down → `wifibroadcast@drone` | **no_video → CPU-starvation latch FIRST** | no_scan/no_cloud → **restart the camera THEN `rover-scan`/`-scan-3d`/`-odometry`, in that order — 0 Hz forever otherwise** (twice; colour dies ⇒ depth has no align target)
