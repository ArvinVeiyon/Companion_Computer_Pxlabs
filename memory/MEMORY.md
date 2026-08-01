# Vind-Roz Platform Memory
> Compressed semantic memory. Auto-loaded each session. Also Phi-3 system prompt (offline AI).
> Live: ~/.claude/projects/-home-roz/memory/ | Backup: ~/codex-work/memory/ → GitHub ArvinVeiyon/Companion_Computer_Pxlabs
> ⚠️ **BACKUP IS MANUAL — NOTHING SYNCS MEMORY AUTOMATICALLY** (07-29): `cp -p ~/.claude/projects/-home-roz/memory/*.md ~/codex-work/memory/` then git add/commit/push. **Never `rsync --delete`** — the mirror is a UNION of two scopes. A 2nd scope at `~/.claude/projects/-home-roz-codex-work/memory/` is NOT auto-loaded here — check it after any codex-work session.
> ⚠️ **KEEP UNDER 125 LINES / 17 KB.** One line per entry; detail belongs in the topic files.

## [MEMORY_FILES]
All files in ~/.claude/projects/-home-roz/memory/, mirrored in ~/codex-work/memory/
- `feedback_dkms_arch.md` (rtl88x2eu DKMS ARCH fix) · `feedback_use_dds_not_mavlink.md` (**RULE: talk to the FC over DDS, never MAVLink probing**) · `feedback_wlan0_persistent_name.md` (⚠️ udev rule GONE as of 07-30)
- `feedback_camera_qgc_only.md` — **RULE: cameras configured ONLY from QGC. A swap is not an exception; never hand-edit vision_streaming.conf**
- `feedback_crash_recovery_checkpoint.md` — **NEW 08-01. RULE: checkpoint memory PER FINDING, not at session close (a crash nearly cost 4h). + the verified post-crash state-recovery procedure**
- `reference_wfb_ng.md` — WFB config + the 07-31 definitive both-ends run (ROOT CAUSE = NIC-A ant0 ~20 dB deaf)
- `reference_wfb_rlyctl.md` · `reference_wfb_cfg_apply.md` · `reference_uart_map.md` · `reference_services.md` · `reference_known_fixes_archive.md` · `reference_gcs_companion_interface.md` · `todos.md` · `ros2_nodes.md`/`ros2_topics.md` · `rover_odometry.md`
- `project_rover_autonav.md` — **ACTIVE. 🔴 YAW RATE RUNAWAY (07-29): cmd 0.3 rad/s, actual ~6.3 (~21×). ⛔ NO armed yaw tests until fixed.** ✅ 08-01 `erpm_to_ms` FIXED (**12.2× low**; a spin-derived scale is only a LOWER BOUND) + `/odom`-at-rest FIXED. **🔴 ALL pre-08-01 speeds read 12.2× LOW.** Holds the arm workflow + 5 hazards + video-vs-autonomy CPU
- `project_perception_3d_costmap.md` — **NEW 08-01. 3D height-aware scan + Nav2 forward costmap. Holds the MEASURED floor height + the rover-sees-its-own-bumper finding. BUILT, NOT DEPLOYED, NOT VALIDATED**
- `project_autonomy_plan_reframe.md` — **NEW 08-01. Ladder re-cut by OUTCOME; contradicts "L0-L4 DONE". Q1 localization = THE WALL; L3 = the step-change**
- `project_l2_floortest_wheel0_reversed.md` (L2 PASS + collision-stop; wheel-0 "reversal" = FALSE ALARM) · `project_l4_gemini_nav2_prereqs.md` (L4 DONE; Nav2 1.3.12 + slam_toolbox 2.8.5) · `project_vision_multicam_upgrade.md` (A+B+C done, **Phase D remains**)
- `project_ffmpeg_hung_alive_gap.md` — **READ ITS 08-01 SECTION FIRST.** CPU latch, fps-key question, vision-node defects, "Pi 5 has no HW H.264 encoder"
- `project_wfb_undervoltage_dead_nic.md` — LIKELY FIXED 07-25 (XL4015 @5.25V). **DON'T raise the pot; DON'T set usb_max_current_enable=1.** `ext5v-report` reads the rail UPSTREAM
- `project_external_wifi_uplink.md` (RTL8821CU `wlx90de80d824d6` = PRIMARY uplink @ 192.168.1.240) · `project_gcs_link_degraded.md` (**downlink CLOSED ~100%; uplink 13.6% → drone antenna**)
- `project_relay_ntp_setup.md` (OPEN) · `project_relay2_relaystn.md` (RPi4 OPEN: WFB card browns out the Pi4 USB budget; fix = powered hub) · `project_companion_network_degraded.md` · `project_boxb_pcie_usb.md` (RESOLVED) · `project_codexrelay_divergence.md` · `project_ros2ws_tag_cleanup.md`
- `project_codexwork_token_in_remote.md` — **SECURITY: origin URL embeds a plaintext GitHub PAT; rotate + move to SSH** · `project_codexwork_branches.md` (**auto-sync does NOT git-add NEW memory files — add manually**)

## [VIDEO_FAULTS] — TWO DIFFERENT FAULTS. Full detail + all proofs → project_ffmpeg_hung_alive_gap.md
**FPV camera is set from QGC only.** Soak ✅ **41.8 min clean 07-31**, 99.99% delivered at the relay.
**(B) 🔴 CPU-STARVATION LATCH — CHECK THIS FIRST, it needs no hardware work.** ffmpeg loses a CPU race to the rover stack and **never recovers**: **7-28 pkt/s vs 208 healthy**, silent >1 h. **Restarting the service does NOT clear it. FIX: briefly `systemctl stop rover-camera rover-scan rover-odometry`.** Auto-caught by the watchdog (#23).
**(A) CAMERA WEDGE — looks identical.** ⛔ **NO SOFTWARE RECOVERY EXISTS — don't build one** (ffmpeg `-c copy`, uvcvideo rebind, USB de-auth, GStreamer: all 0 frames); only physical VBUS removal clears it. **🔴 the LG later ran fine on the SAME port ⇒ "LG = faulty hardware" is WRONG or intermittent.**
**⚠️ TRAPS:** per-second `video tx incoming` reads 0 inside the gaps — **use a CUMULATIVE delta over ≥30 s**; a **manually launched** ffmpeg never moves WFB's counter though the service's does — **never A/B ffmpeg flags via it. Stop the service before touching v4l2 controls.**
**BEST DIAGNOSTIC:** stop the service, run `ffmpeg -loglevel verbose` by hand, read `N packets read; N frames decoded` + `*** N dup!`. **x264 dup-pads ⇒ live RTP ≠ live camera**; confirm at the GS. Healthy = 152 packets/10 s.

## [IDENTITY]
Claude Code CLI + onboard AI for the Vind-Roz drone/rover platform | user: roz / ArvinVeiyon
goal: continuous presence — develop, maintain, autonomize this platform

## [PLATFORM]
Vind-Roz: aerial drone + ground rover, same RPi5 companion, different PX4 airframe | RPi5 BCM2712 quad-core 8GB, 64GB SD (49% used @07-21) | Ubuntu 24.04.1 aarch64, kernel 6.8.0-1048-raspi, host `Vind-Roz`
⚠️ **Boot clock is WRONG until NTP steps it** (systemd/wtmp/`uptime -s` disagreed by days on the 07-30 boot) — don't correlate journals across a reboot. ⚠️ **Only 4 cores; the rover stack + software x264 oversubscribe them** → [VIDEO_FAULTS] (B).

## [FLIGHT_CONTROLLER]
Custom Pixhawk 6X-RT (in-house PCB, NOT Holybro) | MCU: NXP i.MX RT1176 Cortex-M7+M4
PX4 **pxlabs-v1.17.0-2.0.0** | git-hash a52c38b07d | built 2026-05-31 | target px4_fmu-v6xrt (verified via NuttShell `ver all`; local ~/PX4-Autopilot @ c5b8445 is an upstream clone, NOT the fw source)

## [UART_MAP] → full table: reference_uart_map.md
AMA0=MAVLink 921600 | AMA2=TFmini 115200 | AMA3=STL19 230400(disabled) | AMA4=DDS 921600 | AMA1=free

## [SOFTWARE_VERSIONS]
ROS2 Jazzy | Python 3.12.3 | Ollama v0.17.7 / phi3:mini | AIDE 0.18.6 | wfb-ng 1b88185 | mavlink-router c20337b | MicroXRCEAgent v3.0.0-2-gb9d84ac | px4_msgs + px4-ros2-interface-lib release/1.17 @ 86d8239 / 4a3370f
~/PX4-Autopilot: upstream @ c5b8445 + remote `pxlabs`, branch `pxlabs-fw`=a52c38b (real FC fw source)
⚠️ **Pi 5 has NO hardware H.264 encoder** (`v4l2h264enc` missing; `rpivid` decode-only) — all H.264 is software x264. GStreamer 1.24.2 gives no speed advantage; stay with ffmpeg.

## [SERVICES] → full detail: reference_services.md
core: mavlink.router | microxrce-agent | rc_control_node | vision_streaming | block-traffic | wifibroadcast@drone | system_files_sync.timer | ollama | ldlidar(disabled)
**AIDE `dailyaidecheck.timer` DISABLED 07-26** (`COPYNEWDB=no` ⇒ stale baseline + ~3.5h/day of a core). ⚠️ if re-enabling: `COPYNEWDB=yes` + Nice=19/IOSchedulingClass=idle
**tfmini DISABLED 07-26 — drone-only. ⚠️ MUST `systemctl enable --now tfmini` for the DRONE airframe.** Sensorless it burned 38% CPU; disabling took /scan to 29 Hz
autonav: rover-camera | rover-scan | rover-odometry | rover-autonav-mode — enabled+active; **rover-ekf-bridge installed but DISABLED on purpose** (wheels-up limit-cycle hazard; start by hand on the floor). **These 4 are what starve ffmpeg — see [VIDEO_FAULTS] (B).**
**⚡ 08-01:** FPV video costs `/scan` **28.4 → 22.3 Hz**, worst gap **132 → 235 ms** (~¼ of the collision margin at 0.6 m/s) ⇒ don't stream FPV while driving autonomously. **🔴 `/odom` DIES AT REST — ESC doze (`esc_online_flags: 8`), NOT CPU.** ⚠️ `/odom` is RELIABLE QoS — a BEST_EFFORT subscriber reads 0 and mimics this fault exactly.

## [WFB_NG]
→ full detail: reference_wfb_ng.md
ch161 5GHz | drone-wfb@10.5.5.87 ↔ gs-wfb@10.5.5.77 | keys /etc/drone.key /etc/gs.key
multi-adapter TX via fwmark+tc across both wlx NICs (fixed 2026-05-10)
**Every `wifibroadcast@` restart prints a `rtw_mlmeext_disconnect` WARN + trace 2× (one per NIC). BENIGN — monitor mode has no association to tear down. Don't investigate, don't patch the driver.**
**Drone TX is flawless** (~34% airtime of a 13 Mbit/s MCS1 PHY). **When video breaks, WFB has an EMPTY input queue — suspect the source, not the link.** Live stats: TCP `127.0.0.1:8102` (GS 8103), newline-delimited JSON, counters `[per_sec, cumulative]`; do NOT use the `wfb-cli` TUI.
**⚡ 07-31 DEFINITIVE (both ends, full video load):** downlink **99.86-99.99%**; uplink GS→drone loses **13.57% mavlink / 5.46% tunnel**, continuous not bursty. **ROOT CAUSE = drone NIC-A ant0 −48.5 vs ant1 −28.3 dBm (20 dB deaf); GS antennas identical. NIC-B only 3 dB.** ⇒ **ONLY WFB JOB LEFT: reseat that u.FL/pigtail/antenna.** ✅ DELETED as causes: ring-buffer/EAGAIN, GS TX power (already maxed), peer `10.5.6.50` (correct — QGC laptop on the relay hotspot).
⚠️ **METHOD (cost a week):** compare payload `tx.incoming`→`rx.out` across 8102/8103. **Never `rx.all`** (drone double-counts 4 antennas: 13.6% looks like 2.4%). **Never infer radio health from MAVLink rates at two `tcp:5760` endpoints** — that produced the bogus "15% downlink".

## [RELAY_STATION]
vind-rly | Ubuntu 24.04.2 RPi5 | `ssh vind-admin@10.5.5.77` (**sudo NEEDS A PASSWORD ⇒ journalctl of other units returns "No entries"**) | repo ~/codex-relay
tunnel 2222→drone 10.5.5.87:22 (autossh) | svcs: wifibroadcast@gs, mavlink.router, ssh-tunnel-to-companion, relay_files_sync.timer | wfb standalone(CURRENT) vs cluster(+CPE610@10.5.7.102, not connected)
**Wi-Fi Direct P2P-GO `p2p-wlan0-0`, SSID `vind_rely`, ch149, relay 10.5.6.101/24 → QGC laptop 10.5.6.50** | NO RTC + no internet → clock unreliable, see project_relay_ntp_setup.md

## [REPOS]
codex-work: ~/codex-work → Companion_Computer_Pxlabs, branch master (origin/main stale) | codex-relay: ~/codex-relay on vind-rly → Relay_Station_Pxlabs (mirror ~/codex-relay-mirror)
ros2_ws: ~/ros2_ws | branch main | release release/2026-02-22

## [CURRENT STATE — 2026-08-01 19:31, verified live after a 19:19 REBOOT. Nothing broken]
**LIVE-VERIFIED:** all core + 4 autonav svcs active · `rover-ekf-bridge` inactive (correct) · **DISARMED, `nav_state:4`** · `/odom` publishing at rest ✅ (`esc_online_flags=8` doze handled, heading source GYRO) · **`/scan` 22.7 Hz, worst gap 200 ms** · load ~2.5/4 · `vision_streaming` inactive (deliberate, "no FPV while driving").
✅ **GIT BLOCKER CLEARED:** ros2_ws working tree CLEAN, `e0535f9` = origin/main, **0 ahead**. The lost-session commits + the measured calibration are all pushed. codex-work auto-synced 19:24.
🔴 **NEXT BLOCKER = `/camera/depth/points` runs only 11.1 Hz, worst gap 465 ms** (vs the 2D `/scan` it would replace at 22.7 Hz / 200 ms). **At 0.6 m/s a 465 ms gap = 28 cm of travel against a 0.35 m bumper margin ⇒ do NOT deploy `cloud_to_scan` until this is resolved.** Depth stream is configured 848×480@30 — the cloud is CPU-bound, not sensor-bound.
⚠️ **`fps` is INERT — QGC's fps control does NOTHING**; resolution + bitrate DO work. 640x360 cut ffmpeg CPU 78-95% → 25.7% (largely defuses the latch) but bitrate still 2000K ⇒ **radio load unchanged. ⛔ frame rate NEVER hardcoded in ffmpeg — it comes from QGC via the conf. 🔎 CHECK `v4l2-ctl -d /dev/video0 --list-formats-ext`: the camera may not support 15 fps at all.**
⚠️ **codex-work's last push used the plaintext PAT in its remote URL** ⇒ **#14 rotate+SSH MORE urgent.** Mirror with `cp -p`, **never `rsync --delete`** (UNION). **UNDECIDED: "del mirror one" deferred — ask first.**

## [AUTONAV TUNING 2026-08-01 → **read project_rover_autonav.md TOP SECTION, it has the detail**]
✅ `/odom`-at-rest (`bee3abe`) · ✅ **`erpm_to_ms` 0.000380→0.004633 (12.2× low!)** (`42f9aa2`) · ✅ speed loop re-validated armed
✅ **`RO_YAW_RATE_P` 2.0→0.05 + `RO_YAW_RATE_LIM` 1.57→0.5, `param save`d.** ⚠️ persistence not independently verifiable — **re-read after any FC reboot; 2.0 = runaway.** `RO_YAW_RATE_LIM` clamps the SETPOINT only — **not protection.**
📋 **MEASURE FIRST:** `RO_MAX_THR_SPEED` 3.0 likely ~2× low; it normalises the FF in BOTH speed and rate control. ~50% stick outdoors, then revisit `RO_SPEED_P/I`.
⏭ **YAW PARKED → OUTDOOR 08-02** (indoor too tight). Needs ~23-46°, NOT a 360. **Discriminator on `steering/setpoint`: ≈0.102 = OPEN loop (no gain fixes it) vs ≈0.052 = CLOSED (tuning job).** ⚠️ NO yaw evidence yet — the "OPEN LOOP" print was a degenerate sp=0 case, meaningless.
⚠️ **Depth cam sees only 92° — 268° incl. the rear is UNMEASURABLE. Never clear a spin from `/scan`.**

## [TODOS] → memory/todos.md (full detail + commands)
**🔴🔴 AUTONAV IS THE ACTIVE PRIORITY (user, 08-01 — supersedes the 07-31 WFB priority).** **NEXT = 🔴 #20 yaw-rate runaway**, then L5. #21 gyro-yaw odom open. ⚠️ Don't stream FPV while driving. **[OUTDOOR = PRIMARY TARGET] O1-O5:** STL-19 · DroneCAN GPS · lidar SLAM · GPS-waypoint Nav2 · outdoor safety
**WFB parked (not closed): #22 = the #1 WFB action, a HARDWARE job — reseat drone NIC-A ant0 u.FL/pigtail/antenna (~20 dB deaf), re-measure on 8102.** W0-W6 otherwise closed. Then re-measure uplink, then test co-located desense (relay TX 31 dBm ch149 vs WFB RX ch161).
1. Fix relay clock for real (local NTP via companion) — OPEN
2. ✅✅ **DONE + VERIFIED 08-01** — onboard Wi-Fi GONE (`lsmod|grep brcmfmac` EMPTY, **no `wlan*` iface at all**, `disable-wifi-pi5` live). 🔴 **NO onboard fallback — recovery is WFB → relay:2222 ONLY.**
3+4+24. ❌ **ALL THREE DELETED — do not re-propose.** GS `rx_ring_size` (nothing overflows; leave 2 MB), GS TX power (already maxed 30 dBm), trim PX4 MAVLink rates (fixes nothing — downlink ~100%; airtime-only).
5+7+8. Antenna tracker HW (relay :14551) · /scan → obstacle_distance/Nav2 · #17 delete camera_sw_node_obsolute.py · Multicam Phase D (rc_control + optflow → usbcam ids)
9+10. Vision open: (a) backoff reset on the STALL path; (b) pin `6-2/power/control` `on`; (c) vision_config_manager v2.3.0 `--bitrate` (designed).
14. 🔴 **Rotate the GitHub PAT + move codex-work to SSH.** 
23. ✅ **Throughput-floor watchdog LIVE + PUSHED** (`a5fb348`): FLOOR 5 fps / WINDOW 20 s / GRACE 30 s. **⛔ do NOT modify the ffmpeg command line** (`vision_streaming_node.py` ~176-207): `-g 30`/`-tune zerolatency`/`-pkt_size 1400` VETOED. Still open (non-ffmpeg): `frame=0` grace bug; `rclpy.shutdown()` traceback on every QGC camera change; cap cold-start retries

## [AI_STACK]
online: claude CLI → Claude API | offline: Ollama phi3:mini (~3 tok/s) | `ai` auto-routes (`--online`/`--offline`)
SSH login: b+Enter=bash | Enter/4s+internet=Claude | no internet=Phi-3

## [SENSORS]
TFmini: ttyAMA2 downward 0.3-12m 50Hz → distance_sensor | VL53L1X: I2C 0x29 front 20-400cm 10Hz → obstacle_distance | OptFlow: Farneback 10Hz → sensor_optical_flow (manual launch)
STL-19: ttyAMA3 360° 0.02-25m ~10Hz — **PRIMARY-TARGET SENSOR** (outdoor 360°+SLAM); unit is with another team; on re-integration **lidar OWNS `/scan`** (remap depth→`/scan_depth`)
Cameras (**both FPV-capable, both proven on port 6-2; swap from QGC only**) — **See3CAM_CU135** `usbcam-2560c1d1-241D8306-i00` (100mA): real **60 fps** 720p MJPG over USB 2.0 (old "~16 fps" note was WRONG — dark-room auto-exposure). **LG Smart Cam** `usbcam-30c9009d-01.00.00-i00` (500mA): **30 fps**, cheaper on CPU, **currently the FPV cam**. | **Orbbec Gemini 336L** = autonomy-only, NAV-COLOR role_lock, `usbcam-2bc50807-CPC7B53000AB-i04` (USB3 on BOX-B, ROS2 wrapper only, never ffmpeg)
**Three camera rules:** (1) **NEVER key a camera by `/dev/videoN` or by-id** — only `usbcam-<vidpid>-<serial>-i<iface>`. (2) **NEVER record resolution/fps/bitrate as fact** — operator-set from QGC; read the conf live. (3) **Orbbec video nodes appear/vanish with `rover-camera.service`**; renumbering also comes from the Pi5's own `rpivid`/`pispbe-*` nodes (video19-37)

## [AUTONOMY_ROADMAP] — **TWO DOCS, NOT RECONCILED → `project_autonomy_plan_reframe.md`**
> `docs/roadmap.md` (07-23) = ladder/status. **`docs/autonomy_plan.md` (08-01, NEWER) = outcome-based re-cut: L0 ✅ · L1 🔧 · L2-L5 ❌ NOT STARTED.** ⚠️ **Different L-numbers from the old "L0-L4 DONE" — don't mix the two schemes.** 🔴 **Q1 "where am I?" (localization) IS THE WALL — everything above "drive 3 m forward" is a localization problem, not an avoidance one. L3 = where the operator can leave the room.** ⚠️ PX4 RTL has NO obstacle avoidance on this rover — return-to-base must be BUILT.
> **PRIMARY TARGET = OUTDOOR autonomous nav** (GPS waypoint, 360° avoidance); indoor = stepping-stone + GPS-loss fallback → O1(STL-19)→O2(DroneCAN GPS)→O3(lidar SLAM)→O4(GPS-waypoint Nav2)→O5(outdoor safety). **Lidar+depth cam are COMPLEMENTARY: a lidar-only rover drives under a table; the depth cam physically cannot see behind.** Aerial deferred (1 ✅ sensors; 2=mission+collision stop+RTH, 3=360° avoid, 4=SLAM, 5=CV, 6=AI brain)
> **Pending hw:** STL-19 + DroneCAN GPS (CAN live; UAVCAN_ENABLE + EKF2_GPS_CTRL, model TBD). **Gemini 336L IS outdoor-capable** (old "blind in sun" note was wrong)

## [GCS_INTERFACE] → full detail: reference_gcs_companion_interface.md
G-Control.exe → pxlabs_cli.exe → SSH relay:2222 → companion:22 (relay always in middle) | binaries: vision_config_manager (camera), Rozcam (capture); sudo via printf|sudo -S
QGC source: github.com/ArvinVeiyon/PXLABS_qgroundcontrol, branch PXLABS-integration

## [TROUBLESHOOTING]
no_MAVLink: ttyAMA0 baud/wiring + PX4 MAVLink instance | no_DDS: microxrce-agent.service, ttyAMA4, PX4 XRCE param
no_video: vision_streaming.service + /etc/vision_streaming.conf → then **[VIDEO_FAULTS] above (check (B) latch FIRST — it needs no hardware work)**
WFB_down: wifibroadcast@drone.service, wlx* adapter, /etc/drone.key | offline_AI: ollama.service + `ollama list`

## [COMMON_COMMANDS]
`systemctl status <svc>` · `journalctl -u <svc> -f` · `ros2 topic echo /fmu/out/battery_status` · `wfb-rlyctl status` · `sudo wfb-rlyctl use-standalone|use-cluster|set-nics <iface>`
`python3 ~/PX4-Autopilot/Tools/mavlink_shell.py tcp:127.0.0.1:5760` · `ai --offline "question"`
