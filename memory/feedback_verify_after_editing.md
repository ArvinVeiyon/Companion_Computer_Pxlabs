---
name: feedback-verify-after-editing
description: "After consolidating, deleting or retracting anything, GREP twice: for what should have survived, and for the old claim. Confidence is exactly when I skip this, and exactly when it catches something."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ad6ea341-983a-41cc-b0e0-870014d63a41
  modified: 2026-08-09T17:49:20.986Z
---

# Grep after every consolidation, deletion or retraction

**The rule, in two greps:**

1. **Grep for what should have SURVIVED.** After cutting, merging or moving content, list the facts
   that must still exist and check each one is actually somewhere.
2. **Grep for the OLD CLAIM.** After retracting or correcting something, find every other copy. A
   claim made confidently gets propagated to several files; a retraction usually only gets applied
   where I happened to be editing.

Both cost one command. On 2026-08-09 each of them found something on the first run.

**Why:** *I verify when I am uncertain and skip verifying when I am confident.* But confidence means
I already reasoned it through — which is exactly when re-reading my own work cannot catch the error,
and exactly when a mechanical check can. Feeling like I know what is in a file I wrote is not the
same as grepping it.

## What this cost on 2026-08-09 — three catches, none of them mine

**Trimmed MEMORY.md 25.7 → 12.7 KB and asserted the detail was safe in the two manuals.** I had
written both manuals, so I "knew". The operator asked *"I hope the calibration and the acquired
value and error rates are in your memory."* Grepping 36 values found **three missing — including
`0.00028 °/s`, the `/odom` yaw drift that was the entire acceptance result for the heading fix.** It
was one command away from existing only in git history.

**Recorded the rover-plate contamination as conclusions, not as a recognisable symptom.** 11.8%, the
234/4 arithmetic, the fix — all captured. But the **log string lived only in a config file**, so
anyone seeing `util3d.cpp:1251 ... Ignoring ROI ratios` and grepping the docs would find nothing;
and the **visual cue** — the trail through the floor tracing the driven path, which is how the
operator actually caught it — was never written as a cue at all. Prompted by *"I hope you captured
the rover own edge created noise."*

**Retracted a claim in the docs and left it standing in the config.** I had asserted the plate marks
the driven corridor as obstacle and would wall Nav2 in, propagated it to four places, then withdrew
it only where I happened to be editing. `rtabmap_mapping.yaml` — the most-read location, and the one
that actually runs — still stated it as fact. Prompted by *"but you captured in rtabmap creation we
did."*

## How to do it

```bash
# 1. did everything survive?
for v in 0.003900 1.188 0.00028 0.170 …; do
  printf '%-12s ' "$v"; grep -lF "$v" docs/*.md src/**/*.yaml || echo MISSING
done

# 2. is the retracted claim gone everywhere?
grep -rln "the old wording" docs/ src/ tools/ ~/.claude/projects/-home-roz/memory/
```

**Retract in place, do not delete.** Mark it `WITHDRAWN, DO NOT REINSTATE` with the reason, so the
same wrong conclusion is not re-derived from the same evidence by the next reader (or by me).

**Write the recognition cue, not just the conclusion.** For any fault, record *how someone meets it
cold*: the exact log string, and the visual or behavioural symptom. A finding that cannot be
recognised has not really been captured.

Related: [[feedback-test-before-concluding]] (never publish a number I did not measure; a grep that
finds nothing proves the PATTERN absent, not the EVENT) · [[feedback-check-docs-before-measuring]]
