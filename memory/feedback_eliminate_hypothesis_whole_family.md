---
name: eliminate-hypothesis-whole-family
description: Never close a hypothesis on a subset of its parameters — dump the WHOLE family in one command and read them together.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3d2afe7a-6695-4390-92a2-ad91c7476c89
  modified: 2026-08-07T20:05:02.584Z
---

# When eliminating a hypothesis, dump the WHOLE parameter family in ONE command

**Rule: before writing "X is not the cause", enumerate every parameter that could implement X —
in a single command, read side by side. Confirming the first one or two that support the
conclusion you are already forming is not elimination.**

**Why:** 2026-08-07. Asked "is the rover's top plate masked out?", I checked `Kp/RoiRatios` and
`Vis/RoiRatios`, found both set to `0.0 0.0 0.0 0.35`, and wrote *"plate masking is present — not
the cause."* RTAB-Map has **three** independent ROI settings for three consumers: keypoints,
visual registration, and the occupancy grid. `Grid/DepthRoiRatios` was still `0.0 0.0 0.0 0.0`.
I had seen that exact line hours earlier in a dump where I was hunting `Grid/Footprint*` and read
it as another zero in a column of zeros. **The two facts never appeared in the same output.**

The operator caught it — *"you missing something important that is why you stuck"* — not me.

**The error was not the missed line.** It was treating "is the plate masked?" as one yes/no.
The right question names the consumer: *masked for WHICH path?* A config comment saying
*"leaving it in poisons matching"* names **one** of three paths; do not read it as covering the
subject generally.

**How to apply:**
- `grep -iE "roi|mask|footprint|threshold"` the whole parameter dump — search by *concept*, not by
  the specific names you expect. Then read them together in one output.
- State the consumer in the conclusion: not "masking is on" but "masking is on for keypoints and
  visual registration; the grid path is unset."
- Two supporting data points is not a survey. If a system has N places to configure something,
  find N before concluding.

⚠️ **Postscript — the correction cuts both ways.** Having found the gap, I then claimed it was
"the black cluster in the middle of every map." A 6-point sweep showed it changes the map by
~0.1%. **A real gap is not automatically a significant one — measure the effect before asserting
it.** → [[indoor-mapping-slam]] · [[check-docs-before-measuring]]
