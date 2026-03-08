#!/usr/bin/env bash
set -euo pipefail

repo_root="/home/roz/codex-work"
dest="$repo_root/System_files"
list="$repo_root/System_files_list.txt"
log="$repo_root/logs/system_files_sync.log"
md_file="$repo_root/system_companion.md"

mkdir -p "$dest" "$(dirname "$log")"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
run_as_roz() {
  if [ "$(id -u)" -eq 0 ]; then
    su -s /bin/bash roz -c "$*"
  else
    bash -c "$*"
  fi
}

echo "[$(ts)] sync start" >> "$log"

rsync -rlptD --relative --ignore-missing-args \
  --chown=roz:roz \
  --files-from="$list" / "$dest" >> "$log" 2>&1

cd "$repo_root"

run_as_roz "git add System_files/ System_files_list.txt scripts/px4_mavlink.py" >> "$log" 2>&1 || true
if run_as_roz "git diff --cached --quiet"; then
  echo "[$(ts)] no changes" >> "$log"
  exit 0
fi

change_summary="$(run_as_roz "git diff --cached --name-status" | sed 's/^/- /')"
timestamp="$(date '+%Y-%m-%d %H:%M')"

if ! run_as_roz "grep -q '^## Auto Sync Log' \"$md_file\""; then
  run_as_roz "printf '\\n## Auto Sync Log\\n' >> \"$md_file\""
fi
run_as_roz "printf '**%s**\\n%s\\n' \"$timestamp\" \"$change_summary\" >> \"$md_file\""

run_as_roz "git add \"$md_file\"" >> "$log" 2>&1 || true

run_as_roz "git -c user.name=\"auto-sync\" -c user.email=\"auto-sync@local\" commit -m \"Auto-sync: ${timestamp}\"" >> "$log" 2>&1

tag_name="sync-$(date '+%Y%m%d-%H%M')"
run_as_roz "git tag -a \"$tag_name\" -m \"Auto-sync changes:\n${change_summary}\"" >> "$log" 2>&1

echo "[$(ts)] sync complete" >> "$log"
