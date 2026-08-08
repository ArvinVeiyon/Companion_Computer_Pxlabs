---
name: feedback-test-before-concluding
description: "Operator rule (2026-08-08, said repeatedly): state a conclusion or a number only after testing it. No eyeballed figures, no plausibility arguments, no 'should be'."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8d7de6f0-47ae-45c1-8bd3-37d746977bb1
  modified: 2026-08-08T05:35:19.852Z
---

# Conclude after testing, never from assumption

The operator's words: *"come to conclusion after testing not assumption."* Said after a session in
which I did it three times in a row.

**Why:** on this platform an untested conclusion does not just cost a retraction — it gets written
into `docs/` and into this memory dir and then steers the next session's work. Two of the three
slips below would have sent effort at the wrong subsystem for days. The operator has to be able to
read a stated finding as a measured fact, or the whole memory is worthless.

**How to apply:**
1. **Never publish a number I did not measure.** I wrote "walls 0.3–0.5 m thick and doubled" from
   looking at a rendered image. Measured two ways: **median 0.10 m** (2 cells, the grid floor);
   the thick tail was furniture. That single sentence had already told the operator to go tune the
   pose graph — the wrong subsystem entirely.
2. **"Validated" ≠ "works".** I called the map "Nav2-loadable" after checking origin/flip/colours
   with my own rasteriser. Only when I actually ran `nav2_map_server` was it *tested*. If a real
   consumer exists, run it — analysis of the file is not a substitute for loading the file.
3. **Settle ambiguity by MECHANISM, not plausibility.** I flip-flopped twice on the PGM colour
   table by arguing which reading "made more sense for a room". What ended it was a mechanism with
   only one possible direction: ray tracing can *only ever add empty cells*, so whichever value
   grows is free. Look for the one-directional test.
4. **Say which tier a claim is on** when reporting: measured live · read from source · recalled from
   memory · assumed. Do not let the tiers blur together in one paragraph.
5. Applies to *my own* prior findings too — re-check before building on them.
6. **Record provenance of decisions, not just the decision.** The operator corrected me for writing
   "operator decided" about the camera mount: they had *accepted my recommendation*. Those are not
   the same and must not be flattened — an operator preference is settled, whereas a recommendation
   I made is only as good as its basis and must be **reopened if that basis is falsified**. Write
   which one it was, and what it rests on.

Sibling rules, same family: [[check-docs-before-measuring]] (grep the docs before deriving) ·
[[eliminate-hypothesis-whole-family]] (dump every candidate before ruling one out).
→ [[indoor-mapping-slam]]

## 2026-08-08 — I declared a failure from the ABSENCE of a success string

Localization: I grepped for `Accepted loop closure|Loop closure detected|Global loop closure`,
got 0 against 1466 rejections, and reported **"localization has never relocalized"** — into memory,
as a headline blocker. It was wrong. RTAB-Map had localized successfully, and logged it as

    [WARN] Rtabmap.cpp:3772::process() Localization was good, but waiting for
           another one to be more accurate (RGBD/MaxOdomCacheSize>0)

**one line after the last rejection** — different wording, different severity, no "accepted"
anywhere in it. Three hours of silence that I read as "still failing" was actually "succeeded, now
waiting for corroboration it can never get, because the rover never moves."

🔑 **A grep that finds nothing proves my PATTERN was absent, not that the EVENT was.** Before
concluding a thing never happened: enumerate what the success path actually PRINTS (read the
source, or dump every distinct message type in the log), don't guess its wording.
🔑 **Silence is not a negative result** — a component that goes quiet may have succeeded and
changed state. Ask what state it is in, not just what it failed to emit.
