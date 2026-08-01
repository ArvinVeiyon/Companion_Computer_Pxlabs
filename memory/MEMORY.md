# Vind-Roz Platform Memory
> Auto-loaded each session; also the Phi-3 offline system prompt. Live: ~/.claude/projects/-home-roz/memory/ | Backup: ~/codex-work/memory/ → GitHub ArvinVeiyon/Companion_Computer_Pxlabs
> ⚠️ **BACKUP IS MANUAL:** `cp -p ~/.claude/projects/-home-roz/memory/*.md ~/codex-work/memory/` then git add/commit/push. **Never `rsync --delete`** — the mirror is a UNION of two scopes. A 2nd scope at `~/.claude/projects/-home-roz-codex-work/memory/` is NOT auto-loaded — check it after any codex-work session.
> ⚠️ **KEEP UNDER 125 LINES / 17 KB.** One line per entry; detail belongs in the topic files.

## [MEMORY_FILES]
- `feedback_dkms_arch.md` (rtl88x2eu DKMS ARCH) · `feedback_use_dds_not_mavlink.md` (**RULE: FC over DDS, never MAVLink probing**) · `feedback_wlan0_persistent_name.md` (⚠️ udev rule GONE 07-30) · `feedback_crash_recovery_checkpoint.md` (**RULE: checkpoint memory PER FINDING** + post-crash recovery)
- `feedback_camera_qgc_only.md` — **RULE: cameras configured ONLY from QGC; never hand-edit vision_streaming.conf** (FPV cams only, NOT the Orbbec)
- `reference_wfb_ng.md` · `reference_wfb_rlyctl.md` · `reference_wfb_cfg_apply.md` · `reference_uart_map.md` · `reference_services.md` · `reference_known_fixes_archive.md` · `reference_gcs_companion_interface.md` · `todos.md` · `ros2_nodes.md`/`ros2_topics.md` · `rover_odometry.md`
- `project_rover_autonav.md` — **ACTIVE. YAW RATE RUNAWAY: cmd 0.3 rad/s, actual ~6.3 (~21×). ⛔ NO armed yaw tests until fixed.** **ALL pre-08-01 speeds read 12.2× LOW.** Arm workflow + 5 hazards
- `project_perception_3d_costmap.md` — **ACTIVE. `/scan_3d` deployed + rate fixed; measured floor height, near-field self-view, camera-mount analysis. Reflex NOT switched yet**
- `project_autonomy_plan_reframe.md` — ladder re-cut by OUTCOME; contradicts "L0-L4 DONE". Q1 localization = THE WALL
- `project_l2_floortest_wheel0_reversed.md` (wheel-0 "reversal" = FALSE ALARM) · `project_l4_gemini_nav2_prereqs.md` · `project_vision_multicam_upgrade.md` (**Phase D remains**) · `project_ffmpeg_hung_alive_gap.md` (**READ ITS 08-01 SECTION FIRST**)
- `project_wfb_undervoltage_dead_nic.md` — LIKELY FIXED 07-25 (XL4015 @5.25V). **DON'T raise the pot; DON'T set usb_max_current_enable=1.** `ext5v-report` reads the rail UPSTREAM
- `project_external_wifi_uplink.md` (RTL8821CU `wlx90de80d824d6` = PRIMARY uplink @192.168.1.240) · `project_gcs_link_degraded.md` · `project_relay_ntp_setup.md` · `project_relay2_relaystn.md` (RPi4: WFB card browns out the Pi4 USB budget; fix = powered hub) · `project_companion_network_degraded.md` · `project_boxb_pcie_usb.md` · `project_codexrelay_divergence.md` · `project_ros2ws_tag_cleanup.md`
- `project_rc_control_camera_retry_storm.md` — 🔴 **NEW 08-01. `rc_control_node` respawns `sudo vision_config_manager /dev/video0` at 95 Hz forever when it fails (2181 fails/10 min, ~100% of a core, blocks the RC callback). THIS is the "runaway" blamed twice on a stray process. Killing it never works — TX cam switch to neutral stops it.**
- `project_codexwork_token_in_remote.md` — **SECURITY: origin URL embeds a plaintext GitHub PAT; rotate + move to SSH** · `project_codexwork_branches.md` (**auto-sync does NOT git-add NEW memory files — add manually**)

## [VIDEO_FAULTS] — TWO DIFFERENT FAULTS. Full detail + proofs → project_ffmpeg_hung_alive_gap.md
**(B) 🔴 CPU-STARVATION LATCH — CHECK FIRST, no hardware work.** ffmpeg loses a CPU race and **never recovers** (7-28 pkt/s vs 208). **A service restart does NOT clear it. FIX: briefly `systemctl stop rover-camera rover-scan rover-odometry`.**
**(A) CAMERA WEDGE — looks identical.** ⛔ **NO SOFTWARE RECOVERY EXISTS — don't build one**; only physical VBUS removal clears it. **🔴 "LG = faulty hw" is WRONG or intermittent — it later ran fine on the SAME port.**
**⚠️ TRAPS:** `video tx incoming` reads 0 inside gaps — **use a CUMULATIVE delta over ≥30 s**; a **manually launched** ffmpeg never moves WFB's counter — **never A/B flags via it. Stop the service before touching v4l2 controls.**

## [IDENTITY]
Claude Code CLI + onboard AI for the Vind-Roz drone/rover platform | user: roz / ArvinVeiyon | goal: continuous presence — develop, maintain, autonomize this platform

## [PLATFORM]
Vind-Roz: aerial drone + ground rover, same RPi5 companion, different PX4 airframe | RPi5 BCM2712 quad-core 8GB, 64GB SD | Ubuntu 24.04.1 aarch64, kernel 6.8.0-1048-raspi, host `Vind-Roz`
⚠️ **Boot clock is WRONG until NTP steps it** — don't correlate journals across a reboot. ⚠️ **Only 4 cores; the rover stack + software x264 oversubscribe them** → [VIDEO_FAULTS] (B).
⚠️ **No rate/CPU measurement on this box is trustworthy without `ps -eo pid,pcpu --sort=-pcpu` first** — a "7.5 Hz cloud" reading turned out to be a runaway `vision_config_manager` at 72.7%.

## [FLIGHT_CONTROLLER]
Custom Pixhawk 6X-RT (in-house PCB, NOT Holybro) | MCU: NXP i.MX RT1176 Cortex-M7+M4
PX4 **pxlabs-v1.17.0-2.0.0** | git-hash a52c38b07d | built 2026-05-31 | target px4_fmu-v6xrt (via NuttShell `ver all`; local ~/PX4-Autopilot @ c5b8445 is an upstream clone, NOT the fw source)

## [UART_MAP] → reference_uart_map.md
AMA0=MAVLink 921600 | AMA2=TFmini 115200 | AMA3=STL19 230400(disabled) | AMA4=DDS 921600 | AMA1=free

## [SOFTWARE_VERSIONS]
ROS2 Jazzy | Python 3.12.3 | Ollama v0.17.7 / phi3:mini | AIDE 0.18.6 | wfb-ng 1b88185 | mavlink-router c20337b | MicroXRCEAgent v3.0.0-2-gb9d84ac | px4_msgs + px4-ros2-interface-lib release/1.17 @ 86d8239 / 4a3370f | Orbbec wrapper+SDK 2.9.3 | ~/PX4-Autopilot: upstream @ c5b8445 + remote `pxlabs`, branch `pxlabs-fw`=a52c38b (real FC fw source)
⚠️ **Pi 5 has NO hardware H.264 encoder** (`v4l2h264enc` missing; `rpivid` decode-only) — all H.264 is software x264. GStreamer 1.24.2 gives no speed advantage; stay with ffmpeg.

## [SERVICES] → reference_services.md
core: mavlink.router | microxrce-agent | rc_control_node | vision_streaming | block-traffic | wifibroadcast@drone | system_files_sync.timer | ollama | ldlidar(disabled)
**AIDE `dailyaidecheck.timer` DISABLED 07-26** (stale baseline + ~3.5h/day of a core). If re-enabling: `COPYNEWDB=yes` + Nice=19/IOSchedulingClass=idle
**tfmini DISABLED 07-26 — drone-only. ⚠️ MUST `systemctl enable --now tfmini` for the DRONE airframe.** Sensorless it burned 38% CPU.
autonav: rover-camera | rover-scan | **rover-scan-3d (NEW)** | rover-odometry | rover-autonav-mode — enabled+active; **rover-ekf-bridge installed but DISABLED on purpose** (wheels-up limit-cycle hazard; start by hand on the floor).
**⚡ FPV video costs `/scan` 28.4 → 22.3 Hz** ⇒ don't stream FPV while driving autonomously. **🔴 `/odom` DIES AT REST — ESC doze (`esc_online_flags: 8`), NOT CPU.** ⚠️ `/odom` is RELIABLE QoS — a BEST_EFFORT subscriber reads 0 and mimics this fault exactly.
🔴 **A CAMERA RESTART CAN COME UP HALF-DEAD** — back "active", params answering, gyro/accel streaming, **no error logged, but depth & color never started**; `/scan` + both depth topics silently dead. A 2nd restart fixed it. **VERIFY EVERY camera restart:** `journalctl -u rover-camera --since -1min | grep "depth Frame - Width"` (absent = half-dead) **AND a topic rate. `systemctl is-active` does NOT catch this.**

## [PERCEPTION 08-01] → **full detail + all numbers: project_perception_3d_costmap.md**
✅ **Cloud rate fixed:** `point_cloud_decimation_filter_factor:=3` (systemd drop-in on `rover-camera`). Cloud **10.0 → 23.2 Hz**, worst gap **1066 → 301 ms**, msg **3.37 → 0.37 MB**. ⚠️ **`ros2 param set` on it silently does NOTHING** — live lever is the **service** `/camera/set_point_cloud_decimation`.
✅ **`cloud_to_scan` deployed as `rover-scan-3d.service`, PARALLEL.** Publishes **`/scan_3d`, not `/scan`, and NO TF** (`base_link->camera_link` comes only from `rover-scan`) ⇒ **⛔ NEVER repoint `rover-scan.service` at it.** **`/scan_3d` 29.2 Hz / 99 ms worst** vs `/scan` 23.5 Hz / 233 ms.
🔴 **DO NOT SWITCH THE REFLEX YET — `/scan_3d` puts 18-24 beams < 0.60 m, inside the 0.687 m reflex threshold ⇒ the rover would refuse to move.** `range_min=0.40` misses them because scan range = **√(x²+y²)**.
🔴🔴 **THE "ROVER SEES ITS OWN BUMPER" FINDING IS OVERTURNED (two-pose test 20:36): they are ROOM objects, not the rover.** Moved pose ⇒ beams 41→24 and the rigid ones shifted 1-4° and ~4 cm; rigid vehicle structure would be IDENTICAL. ⇒ **`range_min=0.40` is clipping REAL obstacles; re-derive it from the 0.308 m sensor near limit.** ⇒ **no self-occlusion to design around.**
📐 **CAMERA MOUNT: LEAVE IT CENTRE** — (0,0,0.305), pitch 2.33°, 33.7 cm behind the bumper. Setback keeps a bumper-contact obstacle (slant 0.454 m) outside the 0.308 m near limit; the near blind zone is set by VFOV, so moving forward drags it along rather than shrinking it.
❌ **Height-band validation attempt 1 (20:35) INCONCLUSIVE — not a pass.** Only 1.5-2.25 m of floor sampled; "safe at 6.55 m" was a 3-point extrapolation from NEGATIVE p5 values, under load 6.45. **Redo with ≥4 m genuinely clear and the retry storm stopped.**

## [WFB_NG] → reference_wfb_ng.md
ch161 5GHz | drone-wfb@10.5.5.87 ↔ gs-wfb@10.5.5.77 | keys /etc/drone.key /etc/gs.key | multi-adapter TX via fwmark+tc across both wlx NICs
**Every `wifibroadcast@` restart prints `rtw_mlmeext_disconnect` WARN + trace 2×. BENIGN. Don't investigate, don't patch the driver.**
**Drone TX is flawless. When video breaks, WFB has an EMPTY input queue — suspect the source, not the link.** Live stats: TCP `127.0.0.1:8102` (GS 8103), newline-delimited JSON; do NOT use the `wfb-cli` TUI.
**⚡ 07-31 DEFINITIVE:** downlink 99.86-99.99%; uplink loses 13.57% mavlink. **ROOT CAUSE = drone NIC-A ant0 −48.5 vs ant1 −28.3 dBm (20 dB deaf)** ⇒ **ONLY WFB JOB LEFT: reseat that u.FL/pigtail/antenna.** ✅ DELETED as causes: ring-buffer/EAGAIN, GS TX power, peer `10.5.6.50`.
⚠️ **METHOD (cost a week):** compare payload `tx.incoming`→`rx.out` across 8102/8103. **Never `rx.all`** (drone double-counts 4 antennas). **Never infer radio health from MAVLink rates at two `tcp:5760` endpoints.**

## [RELAY_STATION]
vind-rly | Ubuntu 24.04.2 RPi5 | `ssh vind-admin@10.5.5.77` (**sudo NEEDS A PASSWORD ⇒ journalctl of other units returns "No entries"**) | repo ~/codex-relay | tunnel 2222→drone 10.5.5.87:22 (autossh)
svcs: wifibroadcast@gs, mavlink.router, ssh-tunnel-to-companion, relay_files_sync.timer | wfb standalone(CURRENT) vs cluster(+CPE610@10.5.7.102, not connected)
**Wi-Fi Direct P2P-GO `p2p-wlan0-0`, SSID `vind_rely`, ch149, relay 10.5.6.101/24 → QGC laptop 10.5.6.50** | NO RTC + no internet → clock unreliable → project_relay_ntp_setup.md

## [REPOS]
codex-work: ~/codex-work → Companion_Computer_Pxlabs, branch master (origin/main stale) | codex-relay: ~/codex-relay on vind-rly → Relay_Station_Pxlabs (mirror ~/codex-relay-mirror) | ros2_ws: ~/ros2_ws, branch main, release release/2026-02-22

## [CURRENT STATE — 2026-08-01 20:10, live-verified. Nothing broken]
All core + **5** autonav svcs active · `rover-ekf-bridge` inactive (correct) · **DISARMED, `nav_state:4`** · `/odom` publishing at rest ✅ · `/scan` 23.5 Hz · `/scan_3d` 29.2 Hz · load ~2.4/4 · `vision_streaming` inactive (deliberate). **ros2_ws CLEAN, `e0535f9` = origin/main, 0 ahead.**
⚠️ **`fps` is INERT — QGC's fps control does NOTHING**; resolution + bitrate DO work. 640x360 cut ffmpeg CPU 78-95% → 25.7% but bitrate still 2000K ⇒ **radio load unchanged. ⛔ frame rate NEVER hardcoded in ffmpeg — it comes from QGC via the conf.**
⚠️ **codex-work's last push used the plaintext PAT in its remote URL** ⇒ **#14 more urgent.** **UNDECIDED: "del mirror one" deferred — ask first.**

## [AUTONAV TUNING 08-01] → **project_rover_autonav.md TOP SECTION has the detail**
✅ `/odom`-at-rest (`bee3abe`) · ✅ **`erpm_to_ms` 0.000380→0.004633 (12.2× low!)** (`42f9aa2`) · ✅ speed loop re-validated armed
✅ **`RO_YAW_RATE_P` 2.0→0.05 + `RO_YAW_RATE_LIM` 1.57→0.5, `param save`d.** ⚠️ **re-read after any FC reboot; 2.0 = runaway.** `RO_YAW_RATE_LIM` clamps the SETPOINT only — **not protection.**
📋 **MEASURE FIRST:** `RO_MAX_THR_SPEED` 3.0 likely ~2× low; it normalises the FF in BOTH speed and rate control. ~50% stick outdoors, then revisit `RO_SPEED_P/I`.
⏭ **YAW PARKED → OUTDOOR 08-02.** Needs ~23-46°, NOT a 360. **Discriminator on `steering/setpoint`: ≈0.102 = OPEN loop (no gain fixes it) vs ≈0.052 = CLOSED.** ⚠️ NO yaw evidence yet — the "OPEN LOOP" print was a degenerate sp=0 case.
⚠️ **Depth cam sees only 92° — 268° incl. the rear is UNMEASURABLE. Never clear a spin from `/scan`.**

## [TODOS] → memory/todos.md (full detail + commands)
**🔴🔴 AUTONAV IS THE ACTIVE PRIORITY (user, 08-01 — supersedes the 07-31 WFB priority). NEXT = 🔴 #20 yaw-rate runaway**, then L5. #21 gyro-yaw odom open. **[OUTDOOR = PRIMARY TARGET] O1-O5:** STL-19 · DroneCAN GPS · lidar SLAM · GPS-waypoint Nav2 · outdoor safety
**WFB parked (not closed): #22 = the #1 WFB action, a HARDWARE job — reseat drone NIC-A ant0 antenna, re-measure on 8102.** W0-W6 closed. Then re-measure uplink, then test co-located desense.
1. Relay clock via local NTP · 2. ✅ onboard Wi-Fi GONE 🔴 **NO onboard fallback — recovery is WFB → relay:2222 ONLY** · 14. 🔴 **Rotate the GitHub PAT + move codex-work to SSH**
3+4+24. ❌ **ALL THREE DELETED — do not re-propose.** GS `rx_ring_size`, GS TX power (maxed 30 dBm), trim PX4 MAVLink rates (airtime-only).
5+7+8+9+10. Antenna tracker HW (relay :14551) · /scan → obstacle_distance/Nav2 · #17 delete camera_sw_node_obsolute.py · Multicam Phase D · vision: backoff reset on STALL, pin `6-2/power/control` `on`, `--bitrate`
23. ✅ **Throughput-floor watchdog LIVE** (`a5fb348`). **⛔ do NOT modify the ffmpeg command line** (`vision_streaming_node.py` ~176-207): `-g 30`/`-tune zerolatency`/`-pkt_size 1400` VETOED.
25. 🔴 **NEW: fix the rc_control camera retry storm** (latch the ATTEMPT not the success, add backoff, get the blocking spawn out of the RC callback, key by usbcam id not `/dev/video0`) → its memory file

## [AI_STACK]
online: claude CLI → Claude API | offline: Ollama phi3:mini (~3 tok/s) | `ai` auto-routes | SSH login: b+Enter=bash | Enter/4s+internet=Claude | no internet=Phi-3

## [SENSORS]
TFmini: ttyAMA2 down 0.3-12m 50Hz → distance_sensor | VL53L1X: I2C 0x29 front 20-400cm 10Hz → obstacle_distance | OptFlow: Farneback 10Hz → sensor_optical_flow (manual)
STL-19: ttyAMA3 360° 0.02-25m ~10Hz — **PRIMARY-TARGET SENSOR**; with another team; on re-integration **lidar OWNS `/scan`** (remap depth→`/scan_depth`)
Cameras (**both FPV-capable, both proven on port 6-2; swap from QGC only**) — **See3CAM_CU135** `usbcam-2560c1d1-241D8306-i00` (100mA): real **60 fps** 720p MJPG. **LG Smart Cam** `usbcam-30c9009d-01.00.00-i00` (500mA): **30 fps**, cheaper on CPU, **currently the FPV cam**. | **Orbbec Gemini 336L** = autonomy-only, `usbcam-2bc50807-CPC7B53000AB-i04` (USB3 on BOX-B, ROS2 wrapper only, never ffmpeg); depth 848×480@30 configured but delivers ~15 Hz; min valid depth 0.308 m
**Three camera rules:** (1) **NEVER key a camera by `/dev/videoN` or by-id** — only `usbcam-<vidpid>-<serial>-i<iface>`. (2) **NEVER record resolution/fps/bitrate as fact** — operator-set from QGC; read the conf live. (3) **Orbbec video nodes appear/vanish with `rover-camera.service`**; renumbering also from the Pi5's own `rpivid`/`pispbe-*` nodes

## [AUTONOMY_ROADMAP] — **TWO DOCS, NOT RECONCILED → project_autonomy_plan_reframe.md**
> `docs/roadmap.md` (07-23) = ladder/status. **`docs/autonomy_plan.md` (08-01, NEWER) = outcome re-cut: L0 ✅ · L1 🔧 · L2-L5 NOT STARTED.** **Different L-numbers — don't mix the schemes.** 🔴 **Q1 "where am I?" IS THE WALL — everything above "drive 3 m forward" is a localization problem, not an avoidance one. L3 = operator can leave the room.** PX4 RTL has NO obstacle avoidance here — return-to-base must be BUILT.
> **PRIMARY TARGET = OUTDOOR nav**; indoor = stepping-stone + GPS-loss fallback → O1(STL-19)→O2(DroneCAN GPS)→O3(lidar SLAM)→O4(GPS-waypoint Nav2)→O5(outdoor safety). **Lidar+depth cam COMPLEMENTARY: a lidar-only rover drives under a table; the depth cam cannot see behind.** Aerial deferred.
> **Pending hw:** STL-19 + DroneCAN GPS (CAN live; UAVCAN_ENABLE + EKF2_GPS_CTRL). **Gemini 336L IS outdoor-capable** (old "blind in sun" note was wrong)

## [GCS_INTERFACE] → reference_gcs_companion_interface.md
G-Control.exe → pxlabs_cli.exe → SSH relay:2222 → companion:22 (relay always in middle) | binaries: vision_config_manager (camera), Rozcam (capture); sudo via printf|sudo -S | QGC source: github.com/ArvinVeiyon/PXLABS_qgroundcontrol, branch PXLABS-integration

## [TROUBLESHOOTING]
no_MAVLink: ttyAMA0 baud/wiring + PX4 MAVLink instance | no_DDS: microxrce-agent.service, ttyAMA4, PX4 XRCE param | WFB_down: wifibroadcast@drone.service, wlx* adapter, /etc/drone.key | offline_AI: ollama.service + `ollama list`
no_video: vision_streaming.service + /etc/vision_streaming.conf → then **[VIDEO_FAULTS] (check (B) latch FIRST)** | no_scan/no_cloud: **check the half-dead camera restart first** → [SERVICES]

## [COMMON_COMMANDS]
`journalctl -u <svc> -f` · `wfb-rlyctl status` · `sudo wfb-rlyctl use-standalone|use-cluster|set-nics <iface>` · `python3 ~/PX4-Autopilot/Tools/mavlink_shell.py tcp:127.0.0.1:5760` · `ai --offline "q"`
