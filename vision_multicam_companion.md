# Vision Multi-Camera System — Companion Side (Vind-Roz)

Implemented: **2026-07-19** &nbsp;|&nbsp; Status: **deployed & tested on companion**
Design/contract: `memory/project_vision_multicam_upgrade.md` &nbsp;|&nbsp; QGC-side work: **see §4c — 3 REQUIRED fixes in PXLABS_qgroundcontrol** (updated 2026-07-27)

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
| vision_config_manager | **v2.2.2** | `/usr/local/bin/vision_config_manager` | v2.2.2: setter guard widened to BaseException; v2.2.1: setter can't strand the stream; v2.2.0: conf section matched by `camera_id` (see 4c); v2.1: sysfs discovery + usbcam ids + `migrate-store`; v2.0: `list/set-alias/apply` + guard; legacy modes kept |
| vision_streaming node | `164420e` | `ros2_ws` main | capture node picked by sysfs `index` (not lowest videoN); stall watchdog; camera_id resolution; stderr→journal |
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

## 3. Streaming node behavior (ros2_ws `164420e`)

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

## 4. Current camera map (2026-07-19 — ALREADY DRIFTED, see 4b; use ids!)

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

## 4b. ⚠️ /dev/videoN IS NOT STABLE — READ THIS BEFORE TOUCHING CAMERA CODE

**The Orbbec's `/dev/video*` nodes appear and disappear depending on whether
`rover-camera.service` is running.**

| `rover-camera` | What exists |
|---|---|
| **running** | OrbbecSDK claims the device over libusb, uvcvideo detaches → Orbbec has **NO** `/dev/videoN`. Only the LG cam (2 nodes). |
| **stopped** (camera plugged) | uvcvideo binds → Orbbec creates **8 nodes**, and it takes **`/dev/video0`**. |

On top of that, node numbers are handed out from the lowest free slot, so the LG
cam alone was **video8 → video0 → video1** inside one evening (2026-07-27). The
Pi5's own `rpivid` + `pispbe-*` nodes (video19-37) also compete for numbers.

**Rule: never key anything on `/dev/videoN`.** Use the stable
`usbcam-<vidpid>-<serial>-i<iface>` id, or an alias. Code that hardcodes or
defaults to a device path will fail intermittently and look random.

---

## 4c. Companion fixes 2026-07-27 (v2.2.0 / v2.2.1) + REQUIRED QGC-SIDE CHANGES

### What broke (real incident: 15 min of dead video, 19:33→19:48)

QGC sent `set-cam-params /dev/video0 …` — the CLI's **default** device. At that
moment `/dev/video0` was the **Orbbec**, not the LG cam. Chain:

1. `resolve_camera()` lets a raw `/dev/` path through (the Orbbec's
   `usb_identity` is `None`, so it isn't in the camera list, and the `/dev/`
   branch returns the path without erroring).
2. `set_cam_params()` calls `control_service('stop')` → **stream goes down**.
3. `v4l2-ctl --set-fmt-video pixelformat=MJPG` on an Orbbec **depth** node fails
   (`check=True`) → `sys.exit(1)`.
4. `control_service('restart')` is never reached → feed stays dead, silently.

G-Control displayed only `ERROR: Command failed (exit 1)`; the actual message
was discarded.

### Fixed on the companion (no QGC change needed for these)

- **v2.2.0** — `update_resolution_only_config()` / `update_cam_params_config()`
  matched the conf section with `if "camera_name" in line and device in line:`,
  i.e. by substring of the device path. Once `camera_name` went stale the match
  failed, the file was rewritten **byte-identical**, and it still printed
  "updated successfully" and restarted the stream. **Every resolution/format
  change from QGC silently did nothing** while appearing to work. Both writers
  now resolve the section via the stable `camera_id`, fall back to
  `camera_name`, error visibly when nothing matches, and refresh the stale
  `camera_name` as they write.
- **v2.2.1** — the section check moved **before** `control_service('stop')`, and
  both setters are wrapped so a failure triggers `ensure_service_up()`
  before re-raising.
- **v2.2.2** — that wrapper originally caught only `SystemExit`, so a
  `PermissionError` / `OSError` / bare subprocess failure after the stop still
  stranded the service (real outage 2026-07-27 22:52→22:55, 3 min down, manual
  restart). Now `except BaseException`. Caught by the QGC-side review, not by
  me — verified against `SystemExit`, `PermissionError` and `OSError`. A bad device now costs nothing: it prints
  `Error: no section in /etc/vision_streaming.conf matches <dev>; nothing done,
  stream untouched.` and the stream keeps running. Verified live.

### ✅ REQUIRED on the QGC side (`ArvinVeiyon/PXLABS_qgroundcontrol`)

1. **`tools/pxlabs_cli.py` `camera-params`** —
   `device = getattr(args, "device", "/dev/video0")`. **Delete the fallback.**
   Make `--device` required and fail with a clear message. Audit the other
   `getattr(..., "/dev/videoN")` defaults in that file too.
2. **`src/UI/AppSettings/CompanionControl.qml` `_deviceKey()`** — the happy path
   correctly returns `c.id || c.dev`, but when `_cameras` is empty it falls
   through to `deviceCombo.currentText`, which can be a stale device path.
   Disable Apply until a real camera is selected instead.
3. **Surface the companion's stderr on failure.** The CLI already appends
   `2>&1`, so the text is captured — but the UI shows only "exit 1". Printing
   the captured output would have identified this incident in seconds.
4. *(already tracked as B4 in `BUG_FIX.md`)* `shlex.quote()` the interpolated
   `device`/`resolution`/`fps`/`format` at the same call site.

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
# to v2.2.0 (keeps camera_id matching, drops the stop-guard):
sudo cp /usr/local/bin/vision_config_manager.bak.2026-07-27-v2.2.0 /usr/local/bin/vision_config_manager
# to v2.1.0 (WARNING: restores the silent no-op — QGC changes appear to work but don't):
sudo cp /usr/local/bin/vision_config_manager.bak.2026-07-27-v2.1.0 /usr/local/bin/vision_config_manager
# to v1.2.1 (pre-multicam):
sudo cp /usr/local/bin/vision_config_manager.bak.2026-07-19-v1.2.1 /usr/local/bin/vision_config_manager
cd ~/ros2_ws && git checkout 328461f -- src/vision_streaming && colcon build --packages-select vision_streaming
sudo systemctl restart vision_streaming
```
(`/etc/vision_cameras.yaml` is ignored by v1 — safe to leave.)
