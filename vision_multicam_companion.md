# Vision Multi-Camera System — Companion Side (Vind-Roz)

Implemented: **2026-07-19** &nbsp;|&nbsp; Status: **deployed & tested on companion**
Design/contract: `memory/project_vision_multicam_upgrade.md` &nbsp;|&nbsp; QGC-side work: pending (user, PXLABS_qgroundcontrol)

Replaces the fixed two-camera front/back model with N cameras identified by a
**stable id**, user-renamable **aliases**, and free **primary/secondary (PiP)**
selection — all driven from QGC.

> **v2.1 (2026-07-19 evening): identity scheme changed.** by-id basenames proved
> non-deterministic across boots (post-reboot the Orbbec's `index0` pointed at
> the depth node and the color node had *no* symlink → camera invisible,
> NAV-COLOR resolving to depth). Discovery now walks `/dev/video*` probing
> sysfs + V4L2 capabilities directly; the stable id is
> `usbcam-<vidpid>-<serial>-i<bInterfaceNumber>` (USB descriptors,
> firmware-fixed). Ids stay **opaque strings** to QGC — contract unchanged.
> Legacy by-id ids are still accepted everywhere (conf, apply, store) and the
> alias store migrates automatically (`migrate-store` ran 2026-07-19).

---

## 1. Components deployed

| Component | Version | Location | What changed |
|---|---|---|---|
| vision_config_manager | **v2.1.0** | `/usr/local/bin/vision_config_manager` | v2.1: sysfs discovery + usbcam ids + `migrate-store`; v2.0: `list/set-alias/apply` + guard; legacy modes kept |
| vision_streaming node | watchdog rev | `ros2_ws` main_dev (see git log) | ffmpeg watchdog, camera_id resolution (usbcam + legacy by-id), stderr→journal |
| camera store | new | `/etc/vision_cameras.yaml` | alias + role_lock per stable camera id |
| stream conf | extended | `/etc/vision_streaming.conf` | new optional `camera_id` key per section |
| v1 backup | v1.2.1 | `/usr/local/bin/vision_config_manager.bak.2026-07-19-v1.2.1` | rollback point |

No sudoers changes needed: v2 uses the same `sudo cp` / `sudo systemctl`
pattern as v1 and works both as root (QGC path) and as `roz` (NOPASSWD cp/systemctl).

---

## 2. Command reference (the QGC contract)

### `vision_config_manager list [--json] [--all]`
Camera inventory. Default: only **streamable** cameras (offer MJPG or YUYV) —
depth/IR/metadata nodes are filtered out automatically. `--all` adds
non-streamable capture nodes (marked). `--json` is the machine form for QGC.

Real output on the current platform (2026-07-19, v2.1 ids):
```
$ vision_config_manager list
NAV-COLOR    /dev/video6    Orbbec Gemini 336L (color)   YUYV(424x240..) MJPG(..)  lock:autonomy
             id: usbcam-2bc50807-CPC7B53000AB-i04
FPV          /dev/video8    LG Smart Cam                 MJPG(1920x1080..) YUYV(..) PRIMARY
             id: usbcam-30c9009d-01.00.00-i00
```

JSON shape (QGC parses this):
```json
{
  "cameras": [
    {
      "id":        "usbcam-30c9009d-01.00.00-i00",  // STABLE key — OPAQUE, use everywhere
      "dev":       "/dev/video8",             // current node (informational only)
      "hw_name":   "LG Smart Cam: LG Smart Cam",
      "alias":     "FPV",                     // null until user names it
      "streamable": true,
      "formats":   {"MJPG": ["1920x1080", "960x540", "..."], "YUYV": ["..."]},
      "role_lock": null                       // "autonomy" => warn/grey in UI
    }
  ],
  "active": {"primary": "<id or raw dev>", "secondary": null}
}
```
`formats` is the source of truth for the QGC resolution/fps dialog — only offer
what the camera lists (LG max 1080p; Orbbec color actually offers up to
**1280x800** MJPG/YUYV — more than the 640x480 the design assumed).

### `vision_config_manager migrate-store` (v2.1)
One-shot: rewrites legacy by-id keys in `/etc/vision_cameras.yaml` to usbcam
keys (by USB-serial match). Already run on the platform; harmless when there is
nothing to migrate. The migration also rides along automatically in memory on
every command and is persisted by any `set-alias`/`apply`.

### `vision_config_manager set-alias <id|alias|/dev/videoN> "<name>"`
Stores the alias companion-side in `/etc/vision_cameras.yaml`, keyed by stable
id — every GCS and the RC path see the same names. Alias: 1-32 chars
(letters/digits/space/`_ . -`). Prints `OK <id> = <name>`.

### `vision_config_manager apply <primary> [secondary]`
Selects the stream. Arguments may be **id, alias, or /dev/videoN** (all three
resolve to the same camera). Writes conf (+ restarts service) with:
- `camera_name` = resolved `/dev/videoN` (compat with old node),
- `camera_id`  = stable id (the new node re-resolves it at every start),
- probed live resolution/fps/format; secondary adds PiP defaults.

**Guard:** refuses (exit 1, message on stdout for the QGC status label) any
device without MJPG/YUYV — a depth/IR selection can no longer produce the
silent-black-feed failure:
```
$ vision_config_manager apply /dev/video0
Error: primary camera /dev/video0 is not streamable (offers: Z16; need one of:
MJPG, YUYV). Depth/IR nodes cannot be used for video streaming.
```
**role_lock warning:** applying a camera marked `role_lock: autonomy`
(NAV-COLOR/Orbbec) prints a WARNING that it may steal the device from ROS2.

### Legacy compatibility (old QGC buttons keep working)
`vision_config_manager /dev/videoN [/dev/videoM]` still works and now goes
through the same resolve+guard path. Old presets pointing at the removed
front/bottom cameras **error clearly instead of writing a dead config**.
`set-resolution-only`, `set-cam-params`, `list-details` also accept id/alias now.

---

## 3. Streaming node behavior (ros2_ws `a561e93`)

- **camera_id first:** at every ffmpeg (re)start the node resolves
  `camera_id` → current `/dev/videoN`. v2.1 `usbcam-*` ids resolve via sysfs
  USB descriptors (vid:pid + serial + interface); legacy by-id ids still
  resolve through `/dev/v4l/by-id`. Boot renumbering or a replug cannot break
  the stream; a mismatch with conf `camera_name` is logged.
- **Watchdog (2s):** a dead ffmpeg is reaped and logged as
  `[ERROR] FFmpeg exited with code N after Xs`, then restarted with backoff
  2s → 4s → … → 30s cap (backoff resets after 60s of stable streaming).
  Recovery is automatic as soon as the cause clears (e.g. valid camera applied).
- **ffmpeg stderr → journald** (`-loglevel error -nostats`): the real cause
  (wrong format / unplugged / busy device) is visible in
  `journalctl -u vision_streaming`.
- conf `format` key honored: `MJPG`→`mjpeg`, `YUYV`→`yuyv422` input format.

Verified live 2026-07-19 12:44 (conf deliberately pointing at the depth node):
```
Error opening input file /dev/video0.
[ERROR] ... FFmpeg exited with code 234 after 2s (camera unplugged, wrong format, or busy device — see journal).
[WARN]  ... Retrying stream in 2s.   (then 4s, 8s, ...)
```

---

## 4. Current camera map (2026-07-19, will drift — use ids!)

| Alias | id (stable, v2.1) | Node today | Role |
|---|---|---|---|
| FPV | `usbcam-30c9009d-01.00.00-i00` | /dev/video8 | live FPV feed |
| NAV-COLOR | `usbcam-2bc50807-CPC7B53000AB-i04` | /dev/video6 | autonomy (role_lock) |
| — (filtered) | `usbcam-2bc50807-CPC7B53000AB-i00-depth0` | video0 | Z16 depth, autonomy |
| — (filtered) | `…-i00-ir0` / `…-i00-cap0` | video2 / video4 | IR, not streamable |

(The Orbbec carries depth + both IR nodes on USB interface 00; they get
function-tag suffixes derived from their pixel formats, so the suffix follows
the function even if node order shuffles. Streamable cameras are always alone
on their interface → bare keys.)

Stale leftovers from the old build (harmless, cleanup later):
`/etc/udev/rules.d/99-usb-cameras.rules` still pins the REMOVED Waveshare/See3CAM
cameras to video0/video2 via SYMLINK — the mechanism the old front/back model
relied on. Remove once QGC presets are migrated.

---

## 5. QGC-side integration checklist (PC work, see design doc §3)

1. `pxlabs_cli.py`: add `camera-list` → `sudo vision_config_manager list --json`
   and `camera-set-alias` → `sudo vision_config_manager set-alias <id> "<name>"`.
2. Replace hardcoded video0-3 picker + front/bottom/split buttons with the
   dynamic list (show `alias (hw_name)`, badge `role_lock`, offer only listed
   formats/resolutions).
3. Apply: `sudo vision_config_manager apply <id> [<id>]` (id preferred over dev).
4. Show `active` from camera-list so the panel reflects reality after reboots.
5. Until this lands, the old buttons are SAFE but non-functional for the removed
   cameras (clear error in the status label instead of a dead stream).

## 6. Rollback

```
sudo cp /usr/local/bin/vision_config_manager.bak.2026-07-19-v1.2.1 /usr/local/bin/vision_config_manager
cd ~/ros2_ws && git checkout 328461f -- src/vision_streaming && colcon build --packages-select vision_streaming
sudo systemctl restart vision_streaming
```
(`/etc/vision_cameras.yaml` is ignored by v1 — safe to leave.)
