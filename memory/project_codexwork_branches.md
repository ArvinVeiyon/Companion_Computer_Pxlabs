---
name: codexwork-branches
description: codex-work repo has a stale origin/main alongside the active origin/master — left as-is per user decision
metadata: 
  node_type: memory
  type: project
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
  modified: 2026-07-28T18:58:16.963Z
---

`~/codex-work` (ArvinVeiyon/Companion_Computer_Pxlabs) has both `origin/main` and `origin/master` on GitHub, diverged with no common merge (`git merge-base --is-ancestor origin/main origin/master` → no).

- `origin/main`: last commit `6480fcf` "Add connection details for MAVLink and uXRCE-DDS", dated 2026-04-18 — nearest tag behind it is `sync-20260308-1654` (4 commits prior). Appears to be a legacy/abandoned default branch from before the repo standardized on `master`.
- `origin/master`: the actively used branch — local `master` tracks it, all `v1.x` release tags and recent `sync-*` tags live here, latest activity today.

**Why this matters:** `main` is not kept in sync and has no automated relationship to `master` — don't assume `origin/main` reflects current system state or docs.

**Decision (2026-07-11):** user chose to leave `origin/main` untouched (offered rename-to-`main-unused` or delete; declined both). Revisit only if it becomes a source of confusion (e.g. someone clones expecting `main` to be current).

**How to apply:** Always use `master` as the reference branch for this repo. Don't recommend deleting/renaming `origin/main` again unless the user raises it.

**Memory-backup gap (found+fixed 2026-07-19, commit `3e206dd`):** the system_files_sync
auto-commit only picks up already-tracked files — newly created memory files sit untracked in
`~/codex-work/memory/` until someone `git add`s them once (10 files were missing). After writing
a NEW memory file, check `git status ~/codex-work/memory/` and add+push it. Also: mirror has a
stray `claude_memory.md` not present in live memory — left alone, not verified.

**CORRECTION 2026-07-29 — this note understated the problem. Auto-sync does not copy memory AT ALL,
new or existing.** Read `~/codex-work/scripts/system_files_sync.sh`: it rsyncs only the paths in
`System_files_list.txt`, then runs exactly
`git add System_files/ System_files_list.txt scripts/px4_mavlink.py`. `memory/` appears in neither the
rsync list nor the git add, so **live memory edits never reach the mirror by themselves** — the mirror
had drifted since 10:35 that day and still held the pre-compression long-form `MEMORY.md`.
- **Back up by hand:** `cp -p ~/.claude/projects/-home-roz/memory/*.md ~/codex-work/memory/`, then
  `git add memory/ && git commit && git push`.
- ⚠️ **Never `rsync --delete` the mirror.** It is a **UNION of two memory scopes** — 3 files
  (`probe-formats-every-op-watch-item.md`, `vision-config-manager-setter-exception-gap.md`,
  `vision-streaming-outage-2026-07-27.md`) exist there only because they belong to
  `~/.claude/projects/-home-roz-codex-work/memory/`. A mirroring delete would destroy them.
- The service also **skips entirely when the FC reports armed**, so it is unreliable during work
  sessions regardless.
