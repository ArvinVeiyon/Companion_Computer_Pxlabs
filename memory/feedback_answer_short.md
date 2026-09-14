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

## 2026-09-12 — SAID TWICE IN ONE SESSION, AND IT WAS FAIR

Verbatim: **"you always speak a lot it hard to read all"** and **"you are over thinking it seems you wasting my time lot"**. Both came during the VESC RPM-mode migration, while the operator was at the bench with a USB cable in hand and wanted the next action.

**What I was actually doing wrong:** answering a one-line question with a structured essay — restating the safety case he had already heard, re-deriving arithmetic he could do himself, and hedging a decision that was his to make. When he set `rpm_max` to 11000 I had already given the m/s conversion once; repeating the warning read as obstruction, not care.

**How to apply — the bench mode:** while the operator is physically working on hardware, replies are **one short paragraph or a 3-line list**. Give the number, the verdict, and the next action. Save the reasoning for when he asks "why" (he does ask — `why i need headroom for what purpose`, `can you revisit how vesc rpm setting work` — and *those* deserve a full answer). 🔑 **A safety point is made ONCE, with the number; if he restates his choice, do it and stop.**

⚠️ Long-form is still right for: a config review he asked for, a from-source finding, a memory write-up. The rule is about conversational turns during hands-on work.
