---
name: describe_before_executing
description: "Operator 2026-09-19: say what a test will do BEFORE running it — I had been starting moving tests the instant he said 'armed'"
metadata:
  node_type: memory
  type: feedback
---

**State what the test does, then WAIT for the go. Do not start the moment the operator says "armed".**
Operator, 2026-09-19: *"tell me what ur doing because mostly you started immediately"*.

**Why:** during the first armed Nav2 session I treated "Armed" as a green light and fired scripts that
moved a 25 kg vehicle within a second of reading it. The operator is standing next to it with the kill
switch — he needs to know which direction it will go, how far, and what will stop it, BEFORE it moves,
not from the summary afterwards. Arming is him getting ready; it is not consent to whatever I queued.
⚠️ It also produced a real near-miss of a different kind: I twice ran a test whose plan I had only
half-stated, and when the result was strange we spent time arguing about the data instead of the test.

**How to apply:**
- Before any moving test, say in plain words: **what it commands, for how long, how far the vehicle
  travels/turns, what aborts it, and what result would count as pass or fail.** Then stop and wait.
- Queue scripts in **wait-for-arm** mode so the operator's switch is the trigger, not my timing —
  and say so, so he knows what his arming will actually start.
- ⛔ **"Armed" is not "go"** when I have not yet described what will run. Ask.
- Applies to desk changes that alter how the vehicle moves too (param writes, control-path code):
  describe, get an explicit yes, then write.

Pairs with [[notify_before_recording]] (same principle, applied to recordings) and
[[ask_before_param_change]].
