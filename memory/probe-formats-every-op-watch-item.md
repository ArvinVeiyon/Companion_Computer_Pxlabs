---
name: probe-formats-every-op-watch-item
description: Open watch-item — probe_formats runs on every operation; deferred until the camera panel is exercised live
metadata: 
  node_type: memory
  type: project
  originSessionId: a33d544d-d37c-422f-911f-962fe164c33e
  modified: 2026-07-27T17:56:37.811Z
---

As of 2026-07-27: my review of commit a8cb2ae was independently verified by the user
and confirmed accurate on their side too. Out of that same review I flagged that
`probe_formats` is invoked on *every* operation rather than being cached or gated. The
user has accepted that flag as an open **watch-item**, not a bug to fix now — it stays
parked until the camera panel is exercised live.

**Why:** the cost/behaviour of probing on every op can't be judged from code alone; it
only shows up under real camera-panel traffic, so acting on it early risks optimizing
something that turns out to be harmless (or fixing it in the wrong place).

**How to apply:** don't proactively refactor or "fix" the probe_formats call path. When
the camera panel is next exercised live, raise it again and check actual probe frequency
and latency first, then decide. Related: [[vision-config-manager-setter-exception-gap]].
