---
name: answer_short
description: "Operator wants SHORT answers — one line for status/progress replies, not paragraphs"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 42e05df1-d455-448f-b77b-66b31270019f
  modified: 2026-08-29T03:29:55.427Z
---

**Keep replies SHORT. For a status check or a "did it pass yet" question, ONE LINE is the whole answer** — the number and the verdict. No restating the plan, no re-explaining caveats already agreed, no re-listing what is ready to send. Said verbatim 2026-08-29 ("just one line is enough") after several long status updates during the FC hardfault soak.

**Why:** the operator is watching a running test and wants the reading, not a report. Long replies bury the one number he asked for, and re-stating a caveat he has already accepted (e.g. "8 h is the bar") reads as arguing rather than answering. He had already said "not need assume 8 hour it will pass" — a signal to stop hedging — and I still wrote several paragraphs.

**How to apply:** status/progress question ⇒ one line, lead with the measurement. Expand ONLY when asked, when something FAILED, or when a new decision is actually needed. Long-form is still right for deliverables (handoffs, release notes, [[defer_memory_updates]] batches) — this rule is about conversational replies, not documents.

Distinct from [[defer_memory_updates]] (when to write memory) — this is about reply LENGTH.
