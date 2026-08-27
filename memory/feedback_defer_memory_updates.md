---
name: defer_memory_updates
description: "Operator 08-22: memory bookkeeping was eating ~80% of session time — do the work first, batch memory writes at the END, and never mid-investigation"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5d7db126-77cf-4222-a04c-835bb93c5ab5
  modified: 2026-08-22T17:30:14.776Z
---

**Do the actual work first. Batch memory/index writes to the END of a session or a natural pause —
never mid-investigation, and never as a running commentary on each finding.**

**Why:** operator, 2026-08-22: *"always update memory as possible later because most of the time
updating memory consumes 80 percent of our time."* On this box a single finding was triggering a
project-file edit + an index edit + several rounds of index COMPACTION (the `MEMORY.md` size hook
fires on every edit and demands a trim), so one measurement cost many tool calls and the operator
waited through all of them for zero measurement progress.

**How to apply:**
- Hold findings in the conversation, keep measuring, then write **once** at the end.
- ⚠️ **The `MEMORY.md` size hook will nag on every edit. Do not obey it mid-task** — finish the work,
  then compact once. Editing the index repeatedly is what multiplies the cost.
- Exception that still justifies an immediate write: a **safety** fact or a **crash-recovery
  checkpoint** the next session could not reconstruct (see [[crash_recovery_checkpoint]]) — e.g. a
  retraction of something the index currently asserts as true, which would actively mislead.
- When writing at the end, prefer **one pointer line** in `MEMORY.md` + the detail in the topic file.
  See [[debug_before_documenting]] — same principle, applied to memory rather than docs.
