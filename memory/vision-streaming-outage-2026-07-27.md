---
name: vision-streaming-outage-2026-07-27
description: vision_streaming.service went inactive ~22:52 on 2026-07-27 and needed a manual restart
metadata: 
  node_type: memory
  type: project
  originSessionId: 24a81485-3400-416c-9ea4-bd303f99a1ca
  modified: 2026-07-27T17:46:49.412Z
---

On the night of 2026-07-27, `vision_streaming.service` went inactive at around 22:52. It was restarted manually and is active again.

**Suspected root cause** (user, same day, not confirmed): an uncaught `PermissionError` in
`update_cam_params_config()` (`vision_config_manager` line 711) while writing
`/tmp/vision_streaming.conf`, which bypassed `ensure_service_up()` and left the service down —
i.e. exactly the gap in [[vision-config-manager-setter-exception-gap]]. Evidence gathered at the
time: the conf file was `rw-rw-rw-` owned `roz:roz`, and `lsattr` showed no immutable flag, so
*why* the write failed is still unexplained.

**Why:** User reported it as a standalone fact to log; an unexplained drop plus manual recovery is the kind of event worth having on record if it recurs. The permission evidence matters because it rules out the two obvious explanations (wrong owner, immutable bit).

**How to apply:** If the stream drops again, treat this as a prior occurrence — check whether the same time window or trigger repeats, and check `journalctl` for a `PermissionError` traceback from the setter path. The fix to make first is the try/except-then-`ensure_service_up()` wrapper described in [[vision-config-manager-setter-exception-gap]], which makes the stream recover regardless of what the underlying write failure turns out to be.
