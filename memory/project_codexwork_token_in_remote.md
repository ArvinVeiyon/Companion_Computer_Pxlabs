---
name: project-codexwork-token-in-remote
description: "codex-work git remote URL embeds a GitHub personal access token in plaintext — rotate and move to a credential helper"
metadata:
  type: project
---

# Plaintext GitHub PATs on the companion — 2 STILL LIVE as of 2026-08-20 (noticed 2026-07-20)

`~/codex-work/.git/config` stores origin as
`https://<ghp_TOKEN>@github.com/ArvinVeiyon/Companion_Computer_Pxlabs.git` — a GitHub personal
access token in cleartext (visible to anything that reads the repo config or runs `git remote -v`,
and easy to leak into logs/screenshares/pasted output).

**Why it matters:** the token grants repo access under the user's account. It is not encrypted, not
scoped by the filesystem beyond normal file permissions, and it survives in any backup or clone of
the working tree's `.git`.

**Recommended fix (user decision, not done):**
1. Revoke/rotate the token at github.com/settings/tokens.
2. Switch the remote to SSH, which already works from the companion:
   `git -C ~/codex-work remote set-url origin git@github.com:ArvinVeiyon/Companion_Computer_Pxlabs.git`
   (SSH is the documented workaround anyway — companion HTTPS→GitHub hangs on IPv6.)
3. Or, if HTTPS is required, use a credential helper (`git config --global credential.helper store`
   with a file outside the repo, or libsecret) instead of an inline URL token.

Note `~/codex-relay` on the relay may have the same pattern — check it.

Related: [[project-codexwork-branches]], [[project-codexrelay-divergence]].


## 🔴🔴 2026-08-20 — FULL SWEEP: THREE tokens on this machine, TWO of them LIVE
Swept `~/` for `ghp_*` / `github_pat_*` and tested each against `api.github.com/user`
(⚠️ force IPv4 — companion HTTPS→GitHub hangs on IPv6):

| # | token (masked) | kind | where | status |
|---|---|---|---|---|
| A | `github_p…1Z0h` | fine-grained, 93 ch | **`~/git_key`** (root:root, was **0644 WORLD-READABLE**, dated 2025-02-08) | 🔴 **LIVE (200)** — authenticates as `ArvinVeiyon`, reads **20+ repos**: PX4-Autopilot, PXLABS_qgroundcontrol, PXLABS_BLDC_VESC6_MK5, Relay_Station_Pxlabs, Companion_Computer_Pxlabs, ros2_ws, … |
| B | `ghp_UqZD…bwbi` | classic, 40 ch | **`~/.claude/history.jsonl`** — it was **PASTED INTO A CLAUDE CODE PROMPT** | 🔴 **LIVE (200), scope `repo`** = full read/write on every public and private repo |
| C | `ghp_gJA1…Acb6` | classic, 40 ch | `~/.claude/history.jsonl` (also pasted) | ✅ dead (401) |

✅ **Done 08-20:** `chmod 600 ~/git_key` (it was world-readable to every user on the box).
⛔ **NOT done — REQUIRES A BROWSER, THERE IS NO API TO DELETE YOUR OWN PAT:**
- fine-grained → **https://github.com/settings/personal-access-tokens**
- classic → **https://github.com/settings/tokens**
🔑 **HOW TO FIND THEM IN THE LIST: both live tokens show "Last used: within the last minute"**,
because the 08-20 validity check authenticated with them. C will show much older.

✅ **Revoking them breaks NOTHING on the companion or the relay** — verified 08-20: `codex-work`
and `ros2_ws` both use SSH remotes, there is no `~/.git-credentials`, no token in any `.git/config`,
`~/.gitconfig` or `~/.bash_history`. ⚠️ Not verified for the **GCS Windows box or any CI**.

⏭ **AFTER revocation:** `sudo rm ~/git_key` · redact the 2 entries in `~/.claude/history.jsonl` ·
re-test both tokens and expect **401**.

## ✅ CLOSED 2026-08-20: the relay does NOT have this problem
`~/codex-relay` on `vind-rly` is a git repo with **NO REMOTES CONFIGURED AT ALL**, so it never
carried a token URL. No hits in its `.git/config`, and the relay has no `~/.gitconfig`,
`~/.git-credentials` or token in `~/.bash_history`. **Stop re-checking the relay.**

🔑 **LESSON: a secret pasted into a Claude Code prompt is persisted to `~/.claude/history.jsonl`
in cleartext.** Never paste a token into a prompt — reference a file path instead.
