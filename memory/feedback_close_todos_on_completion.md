---
name: close_todos_on_completion
description: "Operator 10-30: the moment a todo is done, REMOVE it or mark it ✅ DONE <date> with HOW it was done — never leave finished work listed as open"
metadata:
  node_type: memory
  type: feedback
  originSessionId: c8689599-e542-4d96-aac5-41eebd68fc99
  modified: 2026-10-29T18:56:16.634Z
---

**When a todo is completed, close it in `todos.md` IN THE SAME SESSION — either delete the entry, or
mark it `✅ DONE <date> — <how>` with the evidence: commit hash, command/measurement that proved it,
or "operator, by feel/tape".** A done item must never still read as open.

**Why:** operator, 2026-10-30: *"some time we failed to remove done work."* A sweep that day found
finished work still listed as open or wrong: unpushed codex-work (already pushed), the See3CAM soak
(camera since replaced), the GS-peer check (already answered), front/rear ESC mapping "NOT proven"
(proven 10-24), PAT "switch to SSH" (already SSH), the LiDAR driver "already in src" (deleted in April).
A fresh session trusts `todos.md` first, so a stale open item causes repeated work and wrong advice.

**How to apply:**
- Closing = verify on the machine first (file gone, commit pushed, value read back) — then edit the entry.
- Prefer **mark with detail** when the item carries a lesson or a ⛔ rule worth keeping; **remove** when
  it is plain bookkeeping. Never delete a ⛔ "do not reopen" warning while closing.
- Partially done ⇒ say which part is done and what is left, on the item itself.
- Update every other place that cites the item (the `todos.md` §1 table, §4 parked line, `MEMORY.md`)
  in the same edit. Numbers are the contract — keep the number, change the status.
- This is the one memory write NOT deferred by [[defer_memory_updates]]: it is part of finishing the task.
