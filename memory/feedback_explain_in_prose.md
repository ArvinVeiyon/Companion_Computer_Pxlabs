---
name: explain_in_prose
description: "When EXPLAINING a problem, write plain connected prose — tables, file:line citations and bold-fragment shorthand are unreadable as conversation"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-07T18:38:27.357Z
  originSessionId: a2526389-c2da-49f3-9da1-3e77a00d97fb
---

**When the operator asks what something MEANS or what the ISSUE IS, answer in plain flowing
prose — short sentences that follow on from each other, one idea per paragraph.** Said 2026-09-07
during the RC-brake work: *"first explain me clearly what is current issue. you sentence are hard to
understand no continuation."*

**What triggered it:** I had answered a question about weak braking with comparison tables, `file:line`
citations (`mcpwm_foc.c:832`), symbol names as nouns (`CONTROL_MODE_CURRENT_BRAKE`), and bold
fragments scattered mid-sentence. Every fact was right and the whole thing was unreadable. The reply
that worked replaced all of it with: here is what you are seeing · here is why it happens · so is
anything broken · here is what we still do not know · here is the decision you need to make.

**Why:** the operator reads English as a second language, and the dense telegraphic style these memory
files and the project docs use is a *storage* format, not a *speaking* format. Bold-everywhere
destroys sentence flow rather than adding emphasis, and a symbol name or a line number mid-sentence
forces a context switch that breaks the thread. "No continuation" is precise feedback: the sentences
did not connect into an argument.

**How to apply:** explaining a diagnosis, a mechanism, or a why ⇒ **prose, no tables, no citations,
minimal bold.** Name the thing in ordinary words first ("a regenerative brake"), and only give the
symbol if he needs it to go look. Tables and `file:line` are still right in the written deliverables
— `RESUME.md`, memory files, commit messages — where they are being stored and scanned, not read
aloud. Keep [[answer_short]] in force: this is about the SHAPE of an explanation, not licence to
write more. If a table genuinely fits the data (a params before/after list), it can stay — the
failure was using tables to carry *reasoning*.

Related: [[answer_short]] (reply LENGTH), [[debug_before_documenting]].
