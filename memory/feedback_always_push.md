---
name: always_push
description: "Operator 10-24: ALWAYS push after committing — never leave a commit local and never ask for permission to push"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc8d3692-ce3b-48a6-903a-d258d166f8b7
  modified: 2026-10-24T17:18:42.314Z
---

**After committing, PUSH. Every time, without asking.** Operator, 2026-10-24, verbatim:
*"Alway push"* — a standing instruction, not a one-off approval.

**Why:** a commit that sits local is invisible to him. He had asked *"this config pushed?"* about the
350 W ESC config-set promotion, I had committed it locally and stopped to ask permission, and the
answer to his question was "no" purely because I had waited. On this setup the git remote **is** the
record — he reads state from GitHub, works across machines (the clean r1 firmware build is happening
on a PC), and a local-only commit silently breaks that. Asking "want me to push?" costs a round trip
during bench work and never has a different answer. See [[answer_short]] — same failure, a question
where an action was wanted.

**How to apply:**
- Commit ⇒ push, in the same breath. Report it as one outcome ("committed and pushed `<sha>`").
- ⚠️ **Still verify the push LANDED** — `git log --oneline -1 origin/<branch>` after. A fetch once
  showed `origin/master` unchanged while I believed the work was published.
- ⚠️ **Branch matters here:** `codex-work` → `origin/master`; **`origin/main` is STALE**, do not
  push there. `ros2_ws` → `main`. → the REPOS section of `MEMORY.md`
- 🔑 **This does NOT widen to anything else outward-facing.** It authorises `git push` to these
  known remotes. It is not blanket permission to open a PR, publish, or write a vehicle param —
  [[ask_before_param_change]] is untouched.
- 🔑 Memory files have their own manual mirror step (`cp -p` to `~/codex-work/memory/`) and this rule
  covers pushing that mirror too.
