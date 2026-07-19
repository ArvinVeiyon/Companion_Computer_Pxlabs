---
name: project_codexrelay_divergence
description: codex-relay (relay) master had diverged from GitHub mirror; RESOLVED 2026-07-12 — merged + relay fast-forwarded, all three aligned
metadata: 
  node_type: memory
  type: project
  originSessionId: 016f9609-44d6-43f6-8782-0e4740c25207
---

**codex-relay history split (found 2026-07-12).** The relay's `~/codex-relay` master and the GitHub `Relay_Station_Pxlabs` master diverged at commit `01f4186`:
- **GitHub-only:** `5e8343e` (system_relay.md channel 161/GCS/no-internet), `9ee8e03` (cluster config + full wifibroadcast.cfg ref), `465eac8` (release history v1.0.4) — PC-side commits the relay never got.
- **Relay-only:** `6ab6cf0` (auto-sync 2026-03-26), `0870840` (wfb-cfg-apply watchdog, see [[reference_wfb_cfg_apply]]).

`relay_git_sync.sh` fails on this: it fetches relay→`~/codex-relay-mirror` with `refs/heads/*:refs/heads/*` and gets **non-fast-forward rejected** on master (with `set -e` it aborts before pushing). Tags still fetch/push fine.

**Fix applied 2026-07-12:** in `~/codex-relay-mirror`, fetched relay master to `relay/master`, `git merge --no-ff` into mirror master (CLEAN, no conflicts — system_relay.md auto-merged), pushed → GitHub master now `58e6432`. All sync-* tags pushed incl. `sync-20260327-1206`.

**RESOLVED 2026-07-12:** relay fast-forwarded `0870840`→`58e6432` via a git bundle (relay has no internet: `git bundle create` on companion mirror `master ^0870840`, scp to relay, `git pull --ff-only <bundle> master`). Only `system_relay.md` updated (pulled in the PC-side doc edits incl. channel-161 wording — NOTE relay actually runs ch157, so that doc text is stale, cosmetic only). **relay master == mirror == GitHub == `58e6432`**; `relay_git_sync.sh` now runs clean ("Everything up-to-date"). Method (bundle transfer for the no-internet relay) is the pattern to reuse if this recurs. Unlike codex-work's still-open [[project_codexwork_branches]] split, this one is closed.
