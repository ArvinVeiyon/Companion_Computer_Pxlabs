---
name: vision-config-manager-setter-exception-gap
description: "Pending fix — vision_config_manager setters only guard SystemExit, so a PermissionError still strands vision_streaming.service down"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7beb91da-2163-4bab-b1f6-dcdb580bff99
  modified: 2026-07-27T17:46:58.408Z
---

Reported by the user (PC/G-Control side) on **2026-07-27**: `set-cam-params` via
G-Control raised an **uncaught `PermissionError`** in `update_cam_params_config()`
(around line 711) while writing `/tmp/vision_streaming.conf`. Because the v2.2.1
guard wraps only `SystemExit`, `ensure_service_up()` never ran and
`vision_streaming.service` was left **inactive**. The user restarted it manually;
feed is back.

**Why:** v2.2.1's safety net was written for the `sys.exit(1)` path
(`v4l2-ctl --check=True` failure). Any non-`SystemExit` exception raised after
`control_service('stop')` still leaves the stream down silently — the exact class
of failure v2.2.1 was meant to eliminate. This makes the claim in
`vision_multicam_companion.md` §4c ("both setters are wrapped so any `SystemExit`
triggers `ensure_service_up()` before re-raising") true-but-insufficient; the doc
needs correcting alongside the code.

**How to apply:** wrap the write in `update_cam_params_config()` (and audit
`update_resolution_only_config()` and any other setter that calls
`control_service('stop')`) in try/except-then-`ensure_service_up()` — catching
`BaseException`/`Exception`, not just `SystemExit` — then re-raise. Same pattern
as the other setters — so that *any* exception there restores the stream, not
just the currently-caught ones.

Also worth checking why `/tmp/vision_streaming.conf` was unwritable. The earlier
guess here — a root-owned temp file left by a QGC-path run with the CLI running
as `roz` — does **not** hold: the user checked and the file was `rw-rw-rw-`
owned `roz:roz` with no immutable flag per `lsattr`. Cause of the write failure
remains unconfirmed. This is now the suspected root cause of the 22:52 outage in
[[vision-streaming-outage-2026-07-27]]. Related: [[vision-multicam-companion-doc]].
