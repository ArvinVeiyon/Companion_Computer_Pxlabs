---
name: notify-before-recording
description: "Never start a data recording without telling the operator first and getting a go — he has to drive for the data to exist"
metadata:
  node_type: memory
  type: feedback
---

**Never start a recording without telling the operator first and getting an explicit go.**
Operator, 2026-09-09: *"shall we run the test — always notify me before recording."*

**Why:** on this rover the operator IS the instrument. He drives, works the sticks and decides
whether the vehicle is safe to move. A recording he does not know about captures a stationary rover
and wastes the window; worse, a recording that starts while he is mid-manoeuvre catches half a
manoeuvre and looks like data. My first attempt on 09-09 caught 120 s of nothing because he was
holding full brake at neutral throttle — I had started it without agreeing the protocol first.

**How to apply:** state the protocol (what he should do, in what order, and any safety constraint),
say the recording has NOT started, wait for the go, then start it and say plainly that it is running
and for how long. Check in partway through rather than discovering at the end that nothing was
captured. If the window runs out, ask before starting a fresh one — do not silently re-arm.

Pairs with [[test-before-concluding]] and [[log-the-discriminator]].
