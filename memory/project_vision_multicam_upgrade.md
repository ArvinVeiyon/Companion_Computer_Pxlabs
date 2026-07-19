---
name: project-vision-multicam-upgrade
description: "Design plan — replace front/back camera model with multi-camera + alias + primary/secondary selection, QGC-driven; companion & QGC work split with interface contract"
metadata: 
  node_type: memory
  type: project
  originSessionId: 41726602-da8e-4edf-b5e2-8b266624ecfa
---

# Vision System Upgrade: Multi-Camera with Aliases (design 2026-07-19)

**Why:** Original design assumed exactly TWO cameras (front `/dev/video0`, bottom `/dev/video2`).
After the BOX-B rebuild the platform has N cameras of different kinds (LG FPV cam, Orbbec depth
with 8 nodes, more later), `/dev/videoN` numbers shuffle per boot, and QGC's picker is hardcoded
to video0-3 with front/bottom preset buttons. User decision: **all camera control stays in QGC**;
QGC gets a dynamic camera list, user-renamable aliases, and free primary/secondary selection
instead of front/back.

**Work split:** user does QGC side on PC (repo ArvinVeiyon/PXLABS_qgroundcontrol);
companion side done here on Vind-Roz. The interface contract below is the agreement between both.

---

## 1. Interface contract (QGC ⇄ companion over existing SSH path)

All commands follow the existing pxlabs_cli pattern (see reference_gcs_companion_interface.md):
`pxlabs_cli.exe companion <action>` → SSH → command on companion → stdout back to QML.

### 1.1 `camera-list` (NEW)
Companion command: `vision_config_manager list --json`
Output: one JSON object on stdout:
```json
{
  "cameras": [
    {
      "id": "usb-EBP6415700138S077G_LG_Smart_Cam_01.00.00-video-index0",
      "dev": "/dev/video8",
      "hw_name": "LG Smart Cam",
      "alias": "FPV",
      "streamable": true,
      "formats": {"MJPG": ["1920x1080","1280x720","960x540","640x480"],
                   "YUYV": ["640x480"]},
      "role_lock": null
    },
    {
      "id": "usb-Orbbec_R__Orbbec_Gemini_336L_CPC7B53000AB-video-index0",
      "dev": "/dev/video6",
      "hw_name": "Orbbec Gemini 336L (color)",
      "alias": "NAV-COLOR",
      "streamable": true,
      "formats": {"MJPG": ["640x480","640x360"]},
      "role_lock": "autonomy"
    }
  ],
  "active": {"primary": "usb-EBP...-video-index0", "secondary": null}
}
```
Rules:
- `id` = /dev/v4l/by-id symlink basename → THE stable key for everything (survives reboots).
- Only capture-capable video nodes listed (must offer MJPG or YUYV); metadata nodes
  (LG video9, Orbbec odd nodes) and depth/IR (Z16/GREY/BA81-only) are EXCLUDED unless
  `--all` is passed. This automatically hides the 6 non-streamable Orbbec nodes that
  confused the old picker.
- `role_lock: "autonomy"` = QGC should show it greyed/warn before selecting (Orbbec is
  reserved for the phase-3 pipeline; selecting it for FPV steals the device from ROS2).
- `active` echoes what /etc/vision_streaming.conf currently points at, resolved back to ids.

### 1.2 `camera-set-alias` (NEW)
Companion command: `vision_config_manager set-alias <id> "<alias>"`
- Alias stored companion-side in `/etc/vision_cameras.yaml` (id → alias map), so every GCS
  and the RC path see the same names. Print `OK <id> = <alias>` or error.

### 1.3 `camera-apply` (UPGRADED, backward compatible)
Companion command: `vision_config_manager apply <primary-id-or-alias> [secondary-id-or-alias]`
- Accepts by-id, alias, or legacy /dev/videoN (legacy positional mode stays for old buttons).
- Resolves id/alias → current /dev/videoN at apply time (readlink of by-id symlink).
- NEW GUARD: refuse (exit 1, clear message for the QML status label) if the device has no
  MJPG/YUYV capture format — prevents the silent-black-feed failure seen 2026-07-19 when
  the conf pointed at the Orbbec depth node.
- One arg = primary only (removes [secondary]); two args = primary + secondary PiP
  (conf already supports [secondary] with pip_position/pip_size — keep those keys).
- Writes BOTH `camera_id` (stable) and `camera_name` (resolved /dev/videoN) into the conf;
  vision_streaming node prefers camera_id when present (re-resolves at service start, so a
  reboot shuffle can't break the stream even without re-applying).

### 1.4 `camera-params` (existing `set-cam-params`) — accept id/alias too, same resolution logic.

---

## 2. Companion-side work (Vind-Roz — can be implemented here)

1. **vision_config_manager v2.0** (/usr/local/bin, Python):
   - subcommands: `list [--json] [--all]`, `set-alias`, `apply`, keep `set-cam-params`,
     `set-resolution-only`, `list-details`, legacy positional mode.
   - camera discovery: walk /dev/v4l/by-id/*-video-index*, dedupe per USB device to the
     capture node, probe formats via `v4l2-ctl --list-formats-ext`.
   - alias + role_lock store: `/etc/vision_cameras.yaml`
     (e.g. `usb-Orbbec...index0: {alias: NAV-COLOR, role_lock: autonomy}`).
2. **vision_streaming node**: honor `camera_id` (resolve by-id → dev at start);
   **ffmpeg watchdog** (todos #6): reap child, on exit log ERROR + restart with backoff,
   so stream death is never silent again.
3. **rc_control** (todos #8): `camera_sw_params.yaml` / `rc_mapping.yaml` switch from
   /dev/video0//dev/video2 to aliases (e.g. CH9 low = primary FPV, mid = PiP with NAV-COLOR,
   high = spare) — resolved through the same vision_config_manager, keeping RC and QGC in sync.
4. **optical_flow nodes**: replace hardcoded /dev/video2 / /dev/video3 with a by-id param
   (currently they'd open Orbbec IR by accident).
5. sudoers: existing NOPASSWD for vision_config_manager covers the new subcommands (same binary).

## 3. QGC-side work (user, on PC — PXLABS_qgroundcontrol)

1. **pxlabs_cli.py**: add `camera-list` and `camera-set-alias` action branches (pattern:
   "Future Dev" section of reference_gcs_companion_interface.md, no C++ changes needed).
2. **FlyViewCustomLayer.qml**:
   - REMOVE hardcoded video0-3 dropdown and front/bottom/split preset buttons.
   - On camera panel open → run `companion camera-list` → parse JSON → populate list showing
     `alias (hw_name)`; mark `role_lock` cameras with a warning badge.
   - Primary selector + optional Secondary selector (PiP) → `companion camera-apply <id> [<id>]`.
   - Rename button per camera → text input → `companion camera-set-alias <id> "<name>"`.
   - Params dialog per camera driven by the `formats` map from camera-list (only offer
     resolutions the camera actually supports — LG max 1080p, Orbbec color max 640x480 MJPG).
3. Remember PXLABSRunner constraints: singleton (serialize the calls), no timeout, stateless.
4. Optional: show `active` from camera-list so the UI reflects reality after reboot shuffles.

## 4. Rollout order
A. Companion: vision_config_manager v2 + alias store (backward compatible — old QGC keeps working).
B. Companion: streaming-node watchdog + camera_id support.
C. QGC: dynamic list + alias UI + primary/secondary (drops front/back model).
D. rc_control + optical_flow migration to aliases/by-id.
E. Delete stale front/back assumptions from docs (ride along with todos #5 ch157→ch161 fix).

## 5. Current state snapshot (2026-07-19)
- FPV live: LG cam /dev/video8, 960x540 MJPG 30fps 2000K → rtp 127.0.0.1:5602 (conf applied
  via vision_config_manager, standard QGC format).
- Orbbec /dev/video0-7 (video0=depth Z16, video2/4=IR, video6=color) — reserved for autonomy.
- QGC picker still hardcoded video0-3 → currently cannot select any working camera; this
  upgrade removes that class of failure permanently.
- RULE (feedback_camera_qgc_only.md): camera selection is user's, from QGC; companion-side
  implementation here happens only on user go-ahead.
