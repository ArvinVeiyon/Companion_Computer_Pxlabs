# Vind-Roz Platform Memory
> Compressed semantic memory. Auto-loaded each session. Also Phi-3 system prompt (offline AI).
> Live: ~/.claude/projects/-home-roz/memory/ | Backup: ~/codex-work/memory/ → GitHub ArvinVeiyon/Companion_Computer_Pxlabs
> ⚠️ **BACKUP IS MANUAL — NOTHING SYNCS MEMORY AUTOMATICALLY** (verified 07-29). `system_files_sync.sh` covers neither. Back up: `cp -p ~/.claude/projects/-home-roz/memory/*.md ~/codex-work/memory/` then git add/commit/push. **Never `rsync --delete`** — the mirror is a UNION of two scopes.
> ⚠️ A SECOND memory scope exists at `~/.claude/projects/-home-roz-codex-work/memory/` (cwd ~/codex-work). NOT auto-loaded here — check it after any codex-work session.
> ⚠️ **KEEP THIS FILE UNDER ~17 KB.** One line per entry; detail belongs in the topic files.

## [MEMORY_FILES]
All files in ~/.claude/projects/-home-roz/memory/, mirrored in ~/codex-work/memory/
- `feedback_dkms_arch.md` — rtl88x2eu DKMS ARCH fix
- `feedback_use_dds_not_mavlink.md` — RULE: talk to the FC over DDS, never MAVLink probing
- `feedback_camera_qgc_only.md` — RULE: cameras configured ONLY from QGC. A **swap** is not an exception; never hand-edit vision_streaming.conf
- `feedback_wlan0_persistent_name.md` — onboard uplink rename to wifi0. ⚠️ the udev rule is GONE as of 07-30
- `reference_wfb_ng.md` — WFB config, benign `rtw_mlmeext_disconnect` WARN, **07-30 link measurement** (radio HEALTHY; real issues = antenna imbalance, uplink burst loss, hardcoded GS peer)
- `reference_wfb_rlyctl.md` · `reference_wfb_cfg_apply.md` · `reference_uart_map.md` · `reference_services.md` · `reference_known_fixes_archive.md` · `reference_gcs_companion_interface.md` · `todos.md`
- `ros2_nodes.md` / `ros2_topics.md` — nodes / FMU↔companion DDS topics · `rover_odometry.md` — wheel odometry plan
- `project_rover_autonav.md` — **ACTIVE. 🔴 YAW RATE RUNAWAY (07-29): commanded 0.3 rad/s, actual ~6.3 (~21×). ⛔ NO armed yaw tests until fixed.** Also 🔴 `erpm_to_ms` ≥2.3× too small ⇒ /odom under-reports speed; fix before L5. Read the file for the arm workflow + 5 hazards (ekf `eph` runaway, wheels-up limit cycle, never `pkill -f`, ESC sleep, collision-stop yaw gating)
- `project_l2_floortest_wheel0_reversed.md` — L2 PASS + reflex collision-stop; wheel-0 "reversal" was a FALSE ALARM
- `project_l4_gemini_nav2_prereqs.md` — L4 DONE; Orbbec + `/scan` live, Nav2 1.3.12 + slam_toolbox 2.8.5 ⇒ L5 unblocked
- `project_vision_multicam_upgrade.md` — A+B+C DONE. **REMAINING: Phase D** (rc_control + optflow → aliases)
- `project_ffmpeg_hung_alive_gap.md` — **07-30: FPV fault CLOSED as HARDWARE (LG).** Holds the full vision-node defect list, the software-recovery-doesn't-work proof, and "Pi 5 has no HW H.264 encoder — stay with ffmpeg"
- `project_wfb_undervoltage_dead_nic.md` — LIKELY FIXED 07-25 (XL4015 @5.25V). **DON'T raise the pot; DON'T set usb_max_current_enable=1.** `ext5v-report` reads the rail UPSTREAM — blind to drops at a device's connector
- `project_external_wifi_uplink.md` — RTL8821CU `wlx90de80d824d6` = PRIMARY uplink @ 192.168.1.240. Holds the `disable-wifi-pi5` overlay story
- `project_gcs_link_degraded.md` — OPEN: downlink ~15% delivered, uplink 0/8; cause of QGC "Unknown mode". **See W1 — likely the same bug as todo #3**
- `project_relay_ntp_setup.md` — relay clock — OPEN, recurred 07-11
- `project_relay2_relaystn.md` — 2nd relay RELAY-STN (RPi4). OPEN: WFB card browns out the Pi4 USB budget; fix = powered hub
- `project_companion_network_degraded.md` · `project_boxb_pcie_usb.md` (RESOLVED 07-19, FFC reseat)
- `project_codexwork_token_in_remote.md` — **SECURITY: origin URL embeds a plaintext GitHub PAT; rotate + move to SSH**
- `project_codexwork_branches.md` (**auto-sync does NOT git-add NEW memory files — add manually**) · `project_codexrelay_divergence.md` · `project_ros2ws_tag_cleanup.md`

## [CAMERA_FAULT] — CLOSED 07-30 as a HARDWARE fault → project_ffmpeg_hung_alive_gap.md
**FPV = See3CAM_CU135** `usbcam-2560c1d1-241D8306-i00` on 6-2, applied from QGC. Partial soak PASSED: **11 min 49 s clean, 0 errors/stalls/drops** — beats the LG's best-ever 9.5 min. Ended by a **clean physical unplug, NOT a fault** (user building a proper mount). REMAINING: refit, then 20-30 min + a reboot.
**⛔ NO SOFTWARE RECOVERY EXISTS for a wedged camera — don't build one.** Against the live-wedged LG all returned 0 frames: `ffmpeg -c copy`, uvcvideo rebind, full USB de-auth/re-auth, 640x480, GStreamer. Kernel logged ZERO USB errors. Only physical VBUS removal clears it.
**Not discriminated:** LG faulty vs contact resistance on 6-2 under load (See3CAM 100 mA vs LG 500 mA). Test = LG into free port `4-1`. Blocked: enclosure assembled. **⚠️ DON'T declare the LG dead hardware — that was claimed once and was wrong.**
**BEST DIAGNOSTIC, use FIRST:** stop the service, run `ffmpeg -loglevel verbose` by hand, read `N packets read; N frames decoded` + `*** N dup!`. **x264 dup-pads a dead camera** ⇒ frozen picture with RTP still flowing — **live RTP ≠ live camera**. `unable to decode APP fields` is BENIGN.
**⚠️ Stop the service before touching v4l2 controls** — toggling `auto_exposure` mid-stream stalls the camera >12 s and trips the watchdog.

## [KNOWN_FIXES]
→ full archive: reference_known_fixes_archive.md
Most recent: camera identity fix 07-19 (usbcam sysfs ids, vision_config_manager v2.1.0→v2.2.3)
Open regression: 2026-03-15 relay NTP fix didn't hold — see project_relay_ntp_setup.md

## [IDENTITY]
role: Claude Code CLI + onboard AI for Vind-Roz drone/rover platform
user: roz / ArvinVeiyon | memory: ~/.claude/projects/-home-roz/memory/MEMORY.md
goal: continuous presence — develop, maintain, autonomize this platform

## [PLATFORM]
Vind-Roz: aerial drone + ground rover | same RPi5 companion, different PX4 airframe config
HW: RPi5 BCM2712 quad-core 8GB | 64GB SD (49% used, 29G free @07-21; fully partitioned)
OS: Ubuntu 24.04.1 LTS aarch64 | kernel 6.8.0-1048-raspi | hostname: Vind-Roz
⚠️ **Boot-time clock is WRONG until NTP steps it** — systemd/wtmp/`uptime -s` disagreed by days on the 07-30 boot. Don't correlate journals across a reboot without checking.

## [FLIGHT_CONTROLLER]
Custom Pixhawk 6X-RT (in-house PCB, NOT Holybro) | MCU: NXP i.MX RT1176 Cortex-M7+M4
PX4 **pxlabs-v1.17.0-2.0.0** | git-hash a52c38b07d | built 2026-05-31 | target px4_fmu-v6xrt
(verified via NuttShell `ver all`. Local ~/PX4-Autopilot @ c5b8445 is an upstream clone, NOT the firmware source)

## [UART_MAP]
→ full table: reference_uart_map.md
AMA0=MAVLink 921600 | AMA2=TFmini 115200 | AMA3=STL19 230400(disabled) | AMA4=DDS 921600 | AMA1=free

## [SOFTWARE_VERSIONS]
ROS2 Jazzy | Python 3.12.3 | Ollama v0.17.7 / phi3:mini | AIDE 0.18.6
mavlink-router c20337b | MicroXRCEAgent v3.0.0-2-gb9d84ac | wfb-ng 1b88185
~/PX4-Autopilot: upstream @ c5b8445 + remote `pxlabs`, branch `pxlabs-fw`=a52c38b (real FC fw source)
px4_msgs: release/1.17 @ 86d8239 | px4-ros2-interface-lib: release/1.17 @ 4a3370f
⚠️ **Pi 5 has NO hardware H.264 encoder** (`v4l2h264enc` missing; `rpivid` is decode-only) — all H.264 is software x264. GStreamer 1.24.2 is installed but offers no speed advantage; stay with ffmpeg.

## [SERVICES]
→ full detail: reference_services.md
core: mavlink.router | microxrce-agent | rc_control_node | vision_streaming | block-traffic | wifibroadcast@drone | system_files_sync.timer | ollama | ldlidar(disabled)
**AIDE `dailyaidecheck.timer` DISABLED 07-26** (`COPYNEWDB=no` ⇒ stale baseline + ~3.5h/day of a core). ⚠️ if re-enabling set `COPYNEWDB=yes` + Nice=19/IOSchedulingClass=idle
**tfmini DISABLED 07-26 — drone-only. ⚠️ MUST `systemctl enable --now tfmini` for the DRONE airframe.** Sensorless it burned 38% CPU; disabling took /scan to 29 Hz
autonav: rover-camera | rover-scan | rover-odometry | rover-autonav-mode — enabled+active; **rover-ekf-bridge installed but DISABLED on purpose** (wheels-up limit-cycle hazard; start by hand on the floor)

## [WFB_NG]
→ full detail: reference_wfb_ng.md
ch161 5GHz | drone-wfb@10.5.5.87 ↔ gs-wfb@10.5.5.77 | keys /etc/drone.key /etc/gs.key
multi-adapter TX via fwmark+tc across both wlx NICs (fixed 2026-05-10)
**Every `wifibroadcast@` restart prints a `rtw_mlmeext_disconnect` WARN + trace, 2× (one per NIC). BENIGN — monitor mode has no association to tear down. Don't investigate, don't patch the driver.**
**07-30 measured: THE RADIO IS HEALTHY.** 0 dropped / 0 truncated / 0 fec_timeouts over 117k video packets; ~34% airtime of a 13 Mbit/s MCS1 PHY. **When video breaks, WFB has an EMPTY input queue — suspect the source, not the link.** Live stats: TCP `127.0.0.1:8102`, newline-delimited JSON, counters are `[per_sec, cumulative]`; do NOT use the `wfb-cli` TUI.

## [RELAY_STATION]
hostname: vind-rly | Ubuntu 24.04.2 RPi5 | ssh vind-admin@10.5.5.77
tunnel 2222→drone 10.5.5.87:22 (autossh) | services: wifibroadcast@gs, mavlink.router, ssh-tunnel-to-companion, relay_files_sync.timer
wfb: standalone(CURRENT) vs cluster(+CPE610@10.5.7.102, not connected) | repo ~/codex-relay
NO RTC + no internet uplink → clock unreliable, see project_relay_ntp_setup.md

## [REPOS]
codex-work: ~/codex-work → Companion_Computer_Pxlabs | branch master (origin/main stale)
codex-relay: ~/codex-relay on vind-rly → Relay_Station_Pxlabs | mirror ~/codex-relay-mirror
ros2_ws: ~/ros2_ws | branch main | release release/2026-02-22

## [OPEN AT 2026-07-31 SESSION CLOSE]
1. **⏳ REBOOT PENDING** — `disable-wifi-pi5` is written to config.txt but not yet active. Onboard radio still up on ch34.
2. **⏳ Camera** — See3CAM physically removed; user is building a mount. Refit, then finish the soak (>20 min + reboot).
3. **⏳ Memory backup** — mirrored to `~/codex-work/memory/` and committed **`67c30c4`, NOT pushed** (deliberate: PAT in the remote URL). User: "keep memory only on local, decide later."
4. **⏳ UNDECIDED — user asked to "del mirror one" but deferred.** Nothing deleted. Ask what they mean before removing anything: undo `67c30c4`, empty `~/codex-work/memory/`, or something else. ⚠️ 3 mirror files (`probe-formats-*`, `vision-config-manager-setter-*`, `vision-streaming-outage-*`) come from the OTHER scope and also live in `~/.claude/projects/-home-roz-codex-work/memory/` — no permanent loss either way, but confirm first.

## [TODOS]
→ See memory/todos.md (full detail + commands)
**🔴🔴 WFB-NG IS THE ACTIVE PRIORITY (set by user 07-31).** The long-running FPV fault is CLOSED as hardware; it was never WFB or software. Vision work is parked. **Work block W0-W6 in todos.md FIRST.**
**NEXT ACTION = W4**: pull `journalctl -u wifibroadcast@gs` from the relay (`ssh vind-admin@10.5.5.77`) — that one piece of evidence decides whether todo #3 and #4 are the same bug.
**W1 (the big idea):** the GS wfb-server EAGAIN crash loop probably explains 15% downlink + 0/8 uplink commands + QGC "Unknown". The drone injects 100% of its 179 kbit/s with 0 drops ⇒ **the loss is GS-side, not the drone.** Fix order: trim PX4 MAVLink rates → raise GS rx_ring_size → re-measure → verify the hardcoded `10.5.6.50` peer → antenna imbalance → TX power LAST.
**[ROVER OUTDOOR — PRIMARY TARGET] O1-O5** (after indoor L5/L6): STL-19 · DroneCAN GPS · lidar SLAM · GPS-waypoint Nav2 · outdoor safety
**Rover next action = #20 re-tune yaw gains**, then L5. #21 gyro-yaw odometry open (biggest accuracy win)
1. Fix relay clock for real (local NTP via companion) — OPEN
2. Disable onboard Wi-Fi — **FIX APPLIED 07-30 23:48, AWAITING REBOOT.** config.txt:69 now `disable-wifi-pi5` (was `disable-wifi` = wrong overlay: bcm2835/mmc vs this board's bcm2712/sdio2). ⚠️ **verify `lsmod | grep brcmfmac` EMPTY**, NOT `ip link show wlan0` (renamed to `wlan1`, so that falsely passes). Once live there is NO onboard fallback → recover via WFB → relay:2222
3. Raise WFB rx_ring_size on GS 2MB→4-8MB — **see W1: probably the ROOT CAUSE of #4**
4. GS TX power — **⛔ DEPRIORITISED: burst loss, not link budget** (mavlink rx lost 546 with only 83 FEC-recovered despite k=1/n=3 triple redundancy, at −28 dBm)
5. Antenna tracker hardware (script ready on relay port 14551, HW pending)
7. Wire /scan → obstacle_distance/Nav2; #17 delete camera_sw_node_obsolute.py
8. Multicam Phase D: rc_control yamls + optical_flow → aliases/usbcam ids
9. Vision open items: (a) backoff reset on the STALL path — unapplied; (b) pin `6-2/power/control` to `on` — hygiene only, NOT a cause; (c) vision_config_manager v2.3.0 `--bitrate` (designed, not written)
10. **Finish the FPV camera soak** — refit on the mount, then >20 min + a reboot
22. **🔴 WFB RX antenna imbalance** — one weak chain on BOTH cards (NIC-A −46 vs −28 dB = 18 dB; NIC-B −42 vs −33). Stable ±1 dB ⇒ not a fade. Check u.FL seating / pigtails
23. **Vision node fixes, all unapplied** (user deferred 07-31 — "do it if I see a bug"): `-g 30`/`-tune zerolatency`/`-pkt_size 1400`; wire `fps` → `-framerate`; `frame=0` grace bug; backoff reset; `rclpy.shutdown()` traceback on every QGC camera change; cap cold-start retries
24. **Trim PX4 MAVLink stream rates** — 179 kbit/s → 549 kbit/s injected ≈ 13% of airtime. Headroom now MEASURED (~34% used), which unblocks the 07-28 video-bitrate item

## [AI_STACK]
online: claude CLI → Claude API | offline: Ollama phi3:mini (~3 tok/s on RPi5)
cmd: `ai` auto-routes | --online | --offline "question"
SSH login: b+Enter=bash | Enter/4s+internet=Claude | no internet=Phi-3

## [SENSORS]
TFmini: ttyAMA2 downward 0.3-12m 50Hz → distance_sensor
VL53L1X: I2C 0x29 front 20-400cm 10Hz → obstacle_distance
OptFlow: Farneback 10Hz → sensor_optical_flow (manual launch)
STL-19: ttyAMA3 360° 0.02-25m ~10Hz — **PRIMARY-TARGET SENSOR** (outdoor 360°+SLAM); unit with another team; on re-integration **lidar OWNS `/scan`** (remap depth→`/scan_depth`)
Cameras — **FPV = e-con See3CAM_CU135** `usbcam-2560c1d1-241D8306-i00` (2560:c1d1, sn 241D8306, 100mA, bus 6-2). **Does a REAL 60 fps at 720p MJPG over USB 2.0** — the old "~16 fps on bus 6" note was WRONG (it was auto-exposure in a dark room). **No blue USB3 port needed.** Expect 60 fps in daylight, ~16 indoors at night. **LG Smart Cam removed 07-30** (30c9:009d, 500mA) — see [CAMERA_FAULT]. | **Orbbec Gemini 336L** = autonomy-only, alias NAV-COLOR role_lock, `usbcam-2bc50807-CPC7B53000AB-i04` (USB3 on BOX-B, ROS2 wrapper only, never ffmpeg)
**Three camera rules, learned the hard way:** (1) **NEVER key a camera by `/dev/videoN` or `/dev/v4l/by-id`** — only `usbcam-<vidpid>-<serial>-i<iface>`. (2) **NEVER record resolution/fps/bitrate as fact** — operator-set from QGC; read `/etc/vision_streaming.conf` live. (3) **The Orbbec's video nodes appear/vanish with `rover-camera.service`**; renumbering also comes from the Pi5's own `rpivid`/`pispbe-*` nodes (video19-37)

## [AUTONOMY_ROADMAP]
> **SOURCE OF TRUTH = `~/ros2_ws/docs/roadmap.md`.** **PRIMARY TARGET = OUTDOOR autonomous nav** (GPS waypoint, 360° avoidance); indoor L0-L4 = stepping-stone + GPS-loss fallback, not the goal
> **L0-L4 DONE, L5 (Nav2) next** → O1(STL-19)→O2(DroneCAN GPS)→O3(lidar SLAM)→O4(GPS-waypoint Nav2)→O5(outdoor safety). Interstitial: #20 yaw tuning. Aerial phases deferred (phase1 ✅ sensor pipeline; 2=mission+collision stop+RTH, 3=360° avoid, 4=SLAM, 5=CV, 6=AI brain)
> **Pending hw:** STL-19 lidar + DroneCAN GPS (CAN live; UAVCAN_ENABLE + EKF2_GPS_CTRL, model TBD). **Gemini 336L IS outdoor-capable** (the old "blind in sun" note was wrong)

## [GCS_INTERFACE]
→ full detail: reference_gcs_companion_interface.md
G-Control.exe → pxlabs_cli.exe → SSH relay:2222 → companion:22 (relay always in middle)
key binaries: vision_config_manager (camera) | Rozcam (capture) | sudo via printf|sudo -S
QGC source: github.com/ArvinVeiyon/PXLABS_qgroundcontrol, branch PXLABS-integration

## [TROUBLESHOOTING]
no_MAVLink: ttyAMA0 baud/wiring, PX4 MAVLink instance config
no_DDS: microxrce-agent.service, ttyAMA4, PX4 XRCE param
no_video: vision_streaming.service, /etc/vision_streaming.conf — then [CAMERA_FAULT] above
WFB_down: wifibroadcast@drone.service, wlx* adapter, /etc/drone.key
offline_AI: ollama.service active, `ollama list` shows phi3:mini

## [COMMON_COMMANDS]
systemctl status <svc> | journalctl -u <svc> -f
ros2 topic list | ros2 topic echo /fmu/out/battery_status
wfb-cli drone | wfb-rlyctl status | sudo wfb-rlyctl use-standalone|use-cluster|set-nics <iface>
python3 ~/PX4-Autopilot/Tools/mavlink_shell.py tcp:127.0.0.1:5760
ai | ai --offline "question"
