#!/usr/bin/env bash
# relay_git_sync.sh — Pull codex-relay from relay and push to GitHub
# Run manually on companion: bash ~/codex-work/scripts/relay_git_sync.sh
# Relay has no internet — companion acts as gateway.
# Preserves full relay git history and tags.

set -euo pipefail

RELAY_USER="vind-admin"
RELAY_HOST="10.5.5.77"
RELAY_REPO="codex-relay"
MIRROR_DIR="$HOME/codex-relay-mirror"
REMOTE_URL="git@github.com:ArvinVeiyon/Relay_Station_Pxlabs.git"
LOG_PREFIX="[relay-git-sync]"

echo "$LOG_PREFIX Starting relay→GitHub sync at $(date '+%Y-%m-%d %H:%M:%S')"

# --- Connectivity check ---
if ! ping -c1 -W2 "$RELAY_HOST" &>/dev/null; then
  echo "$LOG_PREFIX ERROR: relay $RELAY_HOST unreachable — aborting."
  exit 1
fi

# --- Fetch new commits from relay via SSH ---
echo "$LOG_PREFIX Fetching from relay $RELAY_HOST:$RELAY_REPO ..."
git -C "$MIRROR_DIR" fetch "ssh://${RELAY_USER}@${RELAY_HOST}/${RELAY_REPO}" \
  'refs/heads/*:refs/heads/*' \
  'refs/tags/*:refs/tags/*' \
  --update-head-ok

# --- Push to GitHub ---
echo "$LOG_PREFIX Pushing to GitHub ..."
git -C "$MIRROR_DIR" push "$REMOTE_URL" master --tags

echo "$LOG_PREFIX Done. Latest commits:"
git -C "$MIRROR_DIR" log --oneline -5
