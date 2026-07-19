---
name: codexwork-branches
description: codex-work repo has a stale origin/main alongside the active origin/master — left as-is per user decision
metadata: 
  node_type: memory
  type: project
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
---

`~/codex-work` (ArvinVeiyon/Companion_Computer_Pxlabs) has both `origin/main` and `origin/master` on GitHub, diverged with no common merge (`git merge-base --is-ancestor origin/main origin/master` → no).

- `origin/main`: last commit `6480fcf` "Add connection details for MAVLink and uXRCE-DDS", dated 2026-04-18 — nearest tag behind it is `sync-20260308-1654` (4 commits prior). Appears to be a legacy/abandoned default branch from before the repo standardized on `master`.
- `origin/master`: the actively used branch — local `master` tracks it, all `v1.x` release tags and recent `sync-*` tags live here, latest activity today.

**Why this matters:** `main` is not kept in sync and has no automated relationship to `master` — don't assume `origin/main` reflects current system state or docs.

**Decision (2026-07-11):** user chose to leave `origin/main` untouched (offered rename-to-`main-unused` or delete; declined both). Revisit only if it becomes a source of confusion (e.g. someone clones expecting `main` to be current).

**How to apply:** Always use `master` as the reference branch for this repo. Don't recommend deleting/renaming `origin/main` again unless the user raises it.
