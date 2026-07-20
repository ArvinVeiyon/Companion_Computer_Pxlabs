---
name: project-codexwork-token-in-remote
description: "codex-work git remote URL embeds a GitHub personal access token in plaintext — rotate and move to a credential helper"
metadata:
  type: project
---

# codex-work remote URL contains a plaintext PAT — OPEN (noticed 2026-07-20)

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
