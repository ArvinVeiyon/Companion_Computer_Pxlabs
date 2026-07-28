# Vind-Roz Platform Memory
> Compressed semantic memory. Auto-loaded each session. Also Phi-3 system prompt (offline AI).
> Live: ~/.claude/projects/-home-roz/memory/ | Backup: ~/codex-work/memory/ → GitHub ArvinVeiyon/Companion_Computer_Pxlabs
> ⚠️ A SECOND Claude memory scope exists at `~/.claude/projects/-home-roz-codex-work/memory/` (used when cwd is ~/codex-work). It is NOT auto-loaded here — check it after any codex-work session.

## [MEMORY_FILES]
All files live in ~/.claude/projects/-home-roz/memory/ and are mirrored in ~/codex-work/memory/
- `feedback_dkms_arch.md` — rtl88x2eu DKMS ARCH fix
- `feedback_use_dds_not_mavlink.md` — RULE: talk to the FC over DDS topics, never MAVLink probing
- `feedback_camera_qgc_only.md` — RULE: cameras are selected/configured ONLY from QGC. A camera **swap** is not an exception; never hand-edit vision_streaming.conf
- `feedback_wlan0_persistent_name.md` — onboard uplink rename to wifi0 (MAC pin raced USB WFB adapters)
- `reference_wfb_ng.md` — full WFB config + the benign `rtw_mlmeext_disconnect` WARN on every restart
- `reference_wfb_rlyctl.md` (relay control tool) · `reference_wfb_cfg_apply.md` (QGC safe-apply watchdog) · `reference_uart_map.md` · `reference_services.md` · `reference_known_fixes_archive.md` · `reference_gcs_companion_interface.md` · `todos.md`
- `ros2_nodes.md` / `ros2_topics.md` — node details / full FMU↔companion DDS topic lists · `rover_odometry.md` — wheel odometry plan (params, formulas, ESC mapping)
- `project_rover_autonav.md` — **ACTIVE. NEXT = yaw tuning (#20), then L5.** Arm in **Manual** via RC → software DO_SET_MODE→AutoNav. **Hazards:** wheels-up + ekf-bridge + closed loop = limit cycle, only disarm stops it; never `pkill -f`/`pgrep -f` (self-matches). Also: ESC sleep at rest ⇒ check `esc_online_flags==15` before trusting `/odom`
- `project_l2_floortest_wheel0_reversed.md` — L2 PASS + reflex collision-stop (b38e413); wheel-0 "reversal" was a FALSE ALARM
- `project_l4_gemini_nav2_prereqs.md` — L4 DONE; Orbbec + `/scan` live, Nav2 1.3.12 + slam_toolbox 2.8.5; **as-built camera mount TF measured 07-27** ⇒ L5 unblocked
- `project_vision_multicam_upgrade.md` — phases A+B+C DONE, discovery v2.1 (usbcam sysfs ids). **REMAINING: Phase D** (rc_control + optflow → aliases) + udev cleanup
- `project_ffmpeg_hung_alive_gap.md` — ⚠️ **INTERMITTENT, NOT CLOSED (07-28).** FPV video works now. See [CAMERA_FAULT] below
- `project_wfb_undervoltage_dead_nic.md` — LIKELY FIXED 07-25 (XL4015 @5.25V, throttled 0x0); NIC d993c0 is ALIVE. **DON'T raise the pot; DO NOT set usb_max_current_enable=1.** `ext5v-report <min>` ⚠️ reads the rail UPSTREAM — blind to drops at a device's own connector
- `project_external_wifi_uplink.md` — USB RTL8821CU `wlx90de80d824d6` = PRIMARY uplink, static 192.168.1.240/24. `dtoverlay=disable-wifi` fix applied 07-26, **NOT rebooted — verify next boot**
- `project_gcs_link_degraded.md` — OPEN 07-20: downlink ~15% delivered, uplink 0/8; real cause of QGC "Unknown mode"
- `project_relay_ntp_setup.md` — relay clock fix — OPEN, regression recurred 07-11
- `project_relay2_relaystn.md` — 2nd relay RELAY-STN (RPi4). OPEN: WFB card browns out the Pi4 USB budget; fix = powered hub
- `project_companion_network_degraded.md` (IPv6 unreachable + slow bw) · `project_boxb_pcie_usb.md` (RESOLVED 07-19, FFC reseat)
- `project_codexwork_token_in_remote.md` — **SECURITY: origin URL embeds a plaintext GitHub PAT; rotate + move to SSH**
- `project_codexwork_branches.md` (origin/main stale; **auto-sync does NOT git-add NEW memory files — add manually**) · `project_codexrelay_divergence.md` (relay still behind) · `project_ros2ws_tag_cleanup.md` (semver vX.Y.Z; `main` is THE branch)

## [CAMERA_FAULT] — FPV video, 07-28 night: WORKING but NOT proven fixed → project_ffmpeg_hung_alive_gap.md
Camera stops feeding frames while still enumerated (**alive on ep0, silent on isoc**). LG reconnected + re-applied from QGC: 3 stalls in 90 s, then 9.5 min clean. **⚠️ DON'T claim "the LG is dead hardware" — I did, and it was wrong.** Two live suspects: LG internal fault vs **contact resistance on port 6-2** (re-mated ~4×; See3CAM 100 mA worked instantly, LG 500 mA needed 3 restarts). Discriminator = soak >20 min, then a reboot; if it stalls, move to bus 5/7.
**BEST DIAGNOSTIC, use FIRST:** stop the service, run `ffmpeg -loglevel verbose` by hand, read `N packets read; N frames decoded` + `*** N dup!`. **x264 dup-pads a dead camera** ⇒ GS shows a **FROZEN** picture and RTP keeps flowing — **live RTP ≠ live camera**. `unable to decode APP fields` is BENIGN.
**Trust `wfb_tx -p 0` tick delta** (0/20 s dead vs ~22-27 live). **Do NOT trust `tcpdump` lo:5602 or ffmpeg CPU ticks** — both misled me. Ruled out by test: autosuspend, resolution/bandwidth, power, WFB, watchdog. Port resets **don't cut VBUS**, so only a physical unplug clears camera state.

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
px4_msgs: release/1.17 @ 86d8239 (pinned-pxlabs-1.17) | px4-ros2-interface-lib: release/1.17 @ 4a3370f

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
**Every `wifibroadcast@` restart prints a `rtw_mlmeext_disconnect` WARN + call trace, 2× (one per NIC). BENIGN — monitor mode has no association to tear down. Don't investigate, don't patch the driver.** → reference_wfb_ng.md

## [RELAY_STATION]
hostname: vind-rly | Ubuntu 24.04.2 RPi5 | ssh vind-admin@10.5.5.77
tunnel 2222→drone 10.5.5.87:22 (autossh) | services: wifibroadcast@gs, mavlink.router, ssh-tunnel-to-companion, relay_files_sync.timer
wfb: standalone(CURRENT) vs cluster(+CPE610@10.5.7.102, not connected) | repo ~/codex-relay
NO RTC + no internet uplink → clock unreliable, see project_relay_ntp_setup.md

## [REPOS]
codex-work: ~/codex-work → Companion_Computer_Pxlabs | branch master (origin/main stale)
codex-relay: ~/codex-relay on vind-rly → Relay_Station_Pxlabs | mirror ~/codex-relay-mirror
ros2_ws: ~/ros2_ws | branch main | release release/2026-02-22

## [TODOS]
→ See memory/todos.md (full detail + commands)
**[ROVER OUTDOOR — PRIMARY TARGET] O1-O5** (after indoor L5/L6): O1 re-integrate STL-19 · O2 DroneCAN GPS · O3 lidar SLAM · O4 GPS-waypoint Nav2 · O5 outdoor safety
**Next action = #20 re-tune yaw gains** (armed yaw ~700-850 rpm vs fwd ~156), then L5. #21 gyro-yaw odometry open (highest-value accuracy win, replaces slip-prone wheel-derived yaw)
1. Fix relay clock for real (local NTP via companion) — OPEN
2. Disable drone onboard Wi-Fi wifi0 (5GHz interference with ch161) — fix staged, needs reboot verify
3. Increase WFB rx_ring_size on GS (EAGAIN crashes, 19 restarts observed)
4. Check GS TX power (uplink severely worse than downlink)
5. Antenna tracker hardware (script ready on relay port 14551, HW pending)
7. Remains: wire /scan → obstacle_distance/Nav2; #17 delete camera_sw_node_obsolute.py
8. Multicam Phase D: rc_control yamls + optical_flow → aliases/usbcam ids
9. **Vision open items:** (a) `vision_streaming_node.py:325-326` still resets `backoff_s` on the STALL path — agreed fix, unapplied; (b) pin `6-2/power/control` to `on` via udev — **hygiene only, TESTED and NOT a cause**; (c) `vision_config_manager` v2.3.0 = optional `--bitrate` + `active.settings` in `list --json` (designed, not written)
10. **Soak the FPV camera** — see [CAMERA_FAULT]; >20 min + a reboot before calling it fixed

## [AI_STACK]
online: claude CLI → Claude API | offline: Ollama phi3:mini (~3 tok/s on RPi5)
cmd: `ai` auto-routes | --online | --offline "question"
SSH login: b+Enter=bash | Enter/4s+internet=Claude | no internet=Phi-3

## [SENSORS]
TFmini: ttyAMA2 downward 0.3-12m 50Hz → distance_sensor
VL53L1X: I2C 0x29 front 20-400cm 10Hz → obstacle_distance
OptFlow: Farneback 10Hz → sensor_optical_flow (manual launch)
STL-19: ttyAMA3 360° 0.02-25m ~10Hz — **PRIMARY-TARGET SENSOR** (outdoor 360°+SLAM); unit with another team, needs returning; on re-integration **lidar OWNS `/scan`** (remap depth→`/scan_depth`)
Cameras — **FPV is currently the LG Smart Cam** `usbcam-30c9009d-01.00.00-i00` (30c9:009d, bus 6-2, **500mA**), re-applied from QGC 07-28; see [CAMERA_FAULT] for its intermittent stall. **Spare on hand: e-con See3CAM_CU135** `usbcam-2560c1d1-241D8306-i00` (2560:c1d1, sn 241D8306, **100mA**, USB3 — on 480M bus 6 it only gives ~16 fps; bus 5/7 are empty 5 Gbps). | **Orbbec Gemini 336L** = autonomy-only, alias NAV-COLOR role_lock, `usbcam-2bc50807-CPC7B53000AB-i04` (USB3 on BOX-B, ROS2 wrapper only, never ffmpeg)
**Three camera rules, all learned the hard way:** (1) **NEVER key a camera by `/dev/videoN` or `/dev/v4l/by-id`** — only `usbcam-<vidpid>-<serial>-i<iface>`. (2) **NEVER record resolution/fps/bitrate as fact** — operator-set from QGC, changes without notice; read `/etc/vision_streaming.conf` live. (3) **The Orbbec's video nodes appear/vanish with `rover-camera.service`** (wrapper running ⇒ libusb owns it, no nodes; stopped ⇒ uvcvideo makes 8, taking video0). Renumbering also comes from the Pi5's own `rpivid`/`pispbe-*` nodes (video19-37)

## [AUTONOMY_ROADMAP]
> **SOURCE OF TRUTH = `~/ros2_ws/docs/roadmap.md`.** **PRIMARY TARGET = OUTDOOR autonomous nav** (GPS waypoint, 360° avoidance); indoor L0-L4 = stepping-stone + GPS-loss fallback, not the goal
> **L0-L4 DONE, L5 (Nav2) next** → O1(STL-19)→O2(DroneCAN GPS)→O3(lidar SLAM)→O4(GPS-waypoint Nav2)→O5(outdoor safety). Interstitial: #20 yaw tuning. Aerial phases deferred (phase1 ✅ sensor pipeline; 2=mission+collision stop+RTH, 3=360° avoid, 4=SLAM, 5=CV, 6=AI brain; safety: geofence/RTH/land/failsafe)
> **Pending hw:** STL-19 lidar + DroneCAN GPS (CAN live; UAVCAN_ENABLE + EKF2_GPS_CTRL, model TBD). **Gemini 336L IS outdoor-capable** (active-stereo/global-shutter; the old "blind in sun" note was wrong)

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
