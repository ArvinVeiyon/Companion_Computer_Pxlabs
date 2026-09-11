---
name: log-the-discriminator
description: "Record the measurement that would settle the question, instead of arguing the question afterwards from data that cannot answer it"
metadata:
  node_type: memory
  type: feedback
---

**Log the measurement that discriminates, and never write a suggested condition down as an
observed one.**

**Why:** 2026-09-09 cost two wrong public claims and a release-note retraction on someone else's
repo. I suggested "put it on stands" before a brake test, then recorded my own suggestion as an
observed condition in the evidence file. Challenged, I argued from the data that the wheels must
have been unloaded — and the headline argument was arithmetically wrong (51.7 m of wheel path in a
small room, while the same log showed 49 direction reversals ⇒ ~1.05 m per leg, entirely possible).
The rover had been **on the floor, loaded**, the whole time. `esc_current` was sitting inside the
`esc_status` messages the recorder was already receiving and would have settled it in one line
(±1 A at rest vs −12…+8 A moving), and no vehicle-motion topic was subscribed at all.

**How to apply:**
- Before recording, ask "what measurement would make this question unarguable?" and log **that**,
  plus one independent witness. Motor-side data cannot answer a vehicle-side question.
- Label every claim **measured**, **inferred**, or **operator-attested**. Never let one drift into
  another between documents.
- When the operator questions a condition, that is **evidence**, not a request for explanation. He
  was in the room; the written report was not.
- When an inference contradicts direct testimony, re-check the arithmetic before defending it.
- A quiet or empty column means **not measured**, never "zero".

Pairs with [[notify-before-recording]], [[test-before-concluding]], [[independent-rulers]].
