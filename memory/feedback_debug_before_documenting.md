---
name: debug_before_documenting
description: Operator 2026-08-20 — too much of each session goes into docs/memory upkeep instead of debugging; document only what changes a decision, and never let memory housekeeping preempt live work
metadata: 
  node_type: memory
  type: feedback
---

# Debug first. Document the delta, not the journey. — operator, 2026-08-20

**Operator:** *"we always spend a lot of time updating documentation instead of debugging the
issue — the last one I spent for documentation only."* This is a repeated pattern, not a one-off.

**Why:** the docs exist to stop repeated mistakes, but they have started consuming the session they
were meant to protect. A finding that is never tested is worth less than a test that is never
written up.

**How to apply:**
- ⛔ **Never spend turns on memory-size housekeeping while there is live work.** On 2026-08-20 ~7
  tool calls went to golfing `MEMORY.md` under a byte target because a hook kept warning. The hook
  is a background chore — do it once, briefly, or when asked. It is not the operator's goal.
- ✍️ **Write only what changes a future decision:** a retraction, a safety trap, a closed suspect,
  a corrected instruction. Skip narrative, per-fault tables, and restating what the diff shows.
- 📏 **Length ceiling: a finding gets a few lines, not a section with tables.** Long form is for
  something load-bearing being overturned.
- 🔬 **When a task ends, prefer the next MEASUREMENT over the next paragraph.** Example that worked:
  instead of writing up the param hypothesis again, diffing live params against the reference file
  took minutes and proved the planned test would have zeroed the rover's gains and moved the kill
  switch — that catch was worth more than any amount of restating.
- ✅ Still always worth writing: **a corrected instruction that is now known-dangerous.**

Related: [[test_before_concluding]], [[verify_after_editing]], [[fc_hardfaults]].
