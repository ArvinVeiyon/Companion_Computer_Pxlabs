---
name: feedback-ask-before-param-change
description: "NEVER write a PX4 (or any vehicle) parameter without the operator's explicit permission first — announcing it is not asking."
metadata:
  node_type: memory
  type: feedback
---

⛔⛔ **NEVER CHANGE A VEHICLE PARAMETER WITHOUT ASKING FIRST. ANNOUNCING IS NOT ASKING.**
Operator instruction, 2026-09-12: *"do not change any parameter without my permission."*

**Why:** parameters are the vehicle's safety envelope, and the operator owns it. On 2026-09-12 I
raised `COM_DISARM_PRFLT` 10 → 60 s to remove a timing race during an S1 attempt. I said what I was
doing and why, and it was RAM-only and reversible — **and it was still wrong, because I never asked.**
The operator is the one accountable for the machine; a heads-up removes his chance to say no.
🔑 This is the same class of mistake as the 08-14 `RO_ACCEL_LIM`/`RO_DECEL_LIM` change that slewed the
manual stick and put the rover into a wall — a defensible-sounding parameter edit with a consequence
the operator did not agree to.

**How to apply:**
- **Reading is free.** `set_param.py NAME` with no value, `dump_params.py`, `rtabmap-info` — never ask.
- **Writing needs an explicit yes**, every time. Say which parameter, from what to what, why, whether
  it is RAM-only, and how it gets restored. Then **wait**.
- Do not treat "go ahead" on a *test* as consent to change *parameters* for that test. Different thing.
- ⚠️ **RAM-only is not a licence.** It still changes the live vehicle's behaviour for the whole run.
- If a parameter genuinely blocks progress, **say so and stop** — offer it as an option and let the
  operator choose. Never as a fait accompli.
- Restore anything you were given permission to change, and **say** that you restored it.

**Related:** [[feedback_notify_before_recording]] (operator is the instrument — get a GO) ·
[[feedback_scope_px4_params_by_control_flags]] (which params can even matter) ·
[[feedback_test_before_concluding]]
