---
name: reference_gcs_companion_interface
description: "How G-Control (PXLABS QGC) talks to the companion — SSH interface, binaries called, camera mapping, future dev hooks"
metadata: 
  node_type: memory
  type: reference
  originSessionId: e79112a7-c1a7-4e17-b896-f229835ddaf4
---

# GCS ↔ Companion Interface (PXLABS G-Control)

Source: ArvinVeiyon/PXLABS_qgroundcontrol (branch: master)
Reviewed: 2026-07-10

---

## Full Call Chain

```
G-Control.exe (Windows GCS, 10.5.6.50)
  → FlyViewCustomLayer.qml  (button click)
  → PXLABSRunner.run("companion <action>")   [QML singleton]
  → PXLABSCommandRunner.cc  (QProcess wrapper)
  → pxlabs_cli.exe companion <action>        [bundled PyInstaller .exe]
  → pick_companion_host()  [TCP probe primary → fallback]
  → Paramiko SSH
      PRIMARY:  relay (10.5.5.77):2222
                └─ autossh → companion:22  [ssh-tunnel-to-companion.service on vind-rly]
      FALLBACK: companion (10.5.5.87):22   [direct WFB tunnel, if GCS has route]
  → command executes on Vind-Roz
  → stdout streamed back → QML status label
```

**RELAY IS ALWAYS IN THE MIDDLE** — `ssh-tunnel-to-companion.service` on vind-rly must be running.
SSH user on companion: `roz`
Password: from keyring / env PXLABS_COMPANION_PASSWORD

---

## Binaries Called on Companion (must exist)

| GCS Action | SSH Command on Companion |
|------------|--------------------------|
| front-switch | `sudo vision_config_manager /dev/video0` |
| bottom-switch | `sudo vision_config_manager /dev/video2` |
| split-front-bottom | `sudo vision_config_manager /dev/video0 /dev/video2` |
| split-bottom-front | `sudo vision_config_manager /dev/video2 /dev/video0` |
| camera-apply | `sudo vision_config_manager <device>` |
| camera-params | `sudo vision_config_manager set-cam-params <dev> <res> <fps> --format <fmt>` |
| capture-front | `Rozcam -i /dev/video0` |
| capture-bottom | `Rozcam -i /dev/video2` |
| reboot | `sudo systemd-run --on-active=0 systemctl reboot` |
| shutdown | `sudo systemd-run --on-active=0 systemctl poweroff` |
| ssh-terminal | opens local cmd.exe/gnome-terminal → ssh roz@10.5.5.87 |
| wifi-temp | reads `/proc/net/rtl88x2eu/<iface>/thermal_state` → `wfb-cli drone` → sysfs hwmon (3-layer fallback) |
| services refresh | `systemctl is-active + is-enabled` loop over COMPANION_SERVICES |
| services start/stop/restart | `sudo systemctl <action> <svc>` |
| services enable/disable | `sudo systemctl enable/disable --now <svc>` |

**Critical:** `vision_config_manager` and `Rozcam` are custom PXLABS binaries — must be present on companion.
Location TBD (likely `/usr/local/bin/` or custom path — verify with `which vision_config_manager`).

---

## Camera Device Mapping

**STALE SINCE 2026-07-19 BOX-B rebuild** — old front/bottom cams removed. New layout:
Orbbec Gemini 336L = /dev/video0-7 (video0=depth Z16, video2/4=IR, video6=color) — autonomy only;
LG Smart Cam = FPV = video8/9 (by-id `usb-EBP...LG_Smart_Cam...-video-index0`). videoN shuffles per boot.

```
OLD Default (swap=false):  /dev/video0 = front   /dev/video2 = bottom   ← now Orbbec depth/IR!
```

⚠️ GCS preset buttons (front-switch/bottom-switch/split) still send /dev/video0 & /dev/video2 —
pressing them now selects Orbbec depth/IR → ffmpeg dies (no MJPG) → silent black feed (no watchdog,
todos #6). `camera-apply` with an explicit device from QGC works. Fix needed in PXLABS_qgroundcontrol
presets (use by-id paths); optionally add a generic streamable-format guard in vision_config_manager.
CH9 PWM (RC) camera switching presets have the same stale-device problem — verify rc_control_node.

vision_config_manager v1.2.1 = /usr/local/bin (Python): conf /etc/vision_streaming.conf is fully
machine-managed — it rewrites camera_name from QGC's choice + probes res/fps/format via v4l2-ctl,
then restarts the service. Hand edits to the conf are temporary by design; by-id paths pass through fine.

---

## wifi-temp: 3-Layer Fallback

1. `/proc/net/rtl88x2eu/<iface>/thermal_state` — NIC driver thermal (preferred)
2. `wfb-cli drone` → grep temp — WFB stats output
3. `/sys/class/hwmon/hwmon*/temp1_input` — sysfs (value >200 → divide by 1000)
Always exits 0, prints `N/A` on failure — never crashes QML.
NIC name resolved from `WFB_NICS` in `/etc/default/wifibroadcast`.

---

## Sudo Security Pattern

All sudo calls use printf (not echo) to hide password from `ps`:
```bash
printf '%s\n' 'password' | sudo -S <command>
```
Companion sudoers must allow `roz` to run vision_config_manager, systemctl, systemd-run without TTY.

---

## PXLABSRunner Constraints (important for companion dev)

- **Singleton** — only ONE command runs at a time across all QML
- **No timeout** — if companion SSH hangs, GCS blocks until it completes or is aborted
- **Stateless** — new SSH connection per action (except wifi-temp reuses one session for 3 probes)
- **Streaming** — stdout lines arrive in real-time via `outputReady` signal → shown in status label
- **Dev mode** — if cli path ends in `.py`, prepends `python` automatically (no recompile needed for testing)

---

## Future Dev: Adding New GCS-Controllable Features

To expose a new companion capability to G-Control:

1. **Add action to `pxlabs_cli.py`** — new `if action == "my-action":` branch in `companion_actions()`
2. **Add SSH command** — whatever runs on companion via `ssh_exec()`
3. **Add QML button** in `FlyViewCustomLayer.qml` — call `PXLABSRunner.run("companion my-action")`
4. No C++ changes needed — PXLABSRunner passes args as-is

Good candidates for companion-side additions (from autonomy roadmap):
- `companion arm` / `companion disarm` — MAVLink via mavlink_shell or pymavlink
- `companion mission-status` — read ROS2 topic or MAVLink
- `companion offboard-start/stop` — trigger phase2 offboard mission node
- `companion ros2-status` — check specific ros2 node health
- `companion ai-query "question"` — route to Phi-3 via ollama CLI

---

## Services List Visible in GCS

`COMPANION_SERVICES` constant in pxlabs_cli.py — these appear in the GCS Services panel.
Likely includes: mavlink.router, microxrce-agent, vision_streaming, wifibroadcast@drone,
rc_control_node, tfmini, ollama. (Verify exact list in pxlabs_cli.py source.)
Any new companion service can be added here to make it GCS-manageable.

---

## Related Memory
- [[reference_wfb_rlyctl]] — relay-side wfb-rlyctl tool (GCS also controls relay via pxlabs_cli)
- [[ros2_nodes]] — ROS2 nodes that could be exposed as future GCS actions
- [[rover_odometry]] — future services to add to COMPANION_SERVICES
