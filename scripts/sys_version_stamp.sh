#!/usr/bin/env bash
# sys_version_stamp.sh — regenerate the machine-readable header of /etc/sys_version.
#
# /etc/sys_version is the SD-image changelog for this companion computer. It is hand-written
# below the AUTOGEN markers and machine-stamped above them. This script only ever rewrites
# the block between the markers; the changelog underneath is never touched.
#
# The file was called /etc/sid.conf until 10/10/2026. A compat symlink remains at that path.
#
# Usage:
#   sys_version_stamp.sh                      # print the stamp to stdout, write nothing
#   sudo sys_version_stamp.sh --write         # replace the AUTOGEN block in place
#   sudo sys_version_stamp.sh --write --set-version 2.3
#   sys_version_stamp.sh --diff               # show what --write would change
#
# Every field is best-effort: anything unreadable is stamped UNREAD rather than left blank,
# so a missing value can never be mistaken for a known-good one.

set -euo pipefail

TARGET="${SYS_VERSION_FILE:-/etc/sys_version}"
BEGIN='# >>> AUTOGEN sys_version_stamp.sh — DO NOT EDIT BELOW THIS LINE <<<'
END='# >>> END AUTOGEN — hand-written changelog follows <<<'

mode="print"
set_version=""

while [ $# -gt 0 ]; do
  case "$1" in
    --write)        mode="write" ;;
    --diff)         mode="diff" ;;
    --set-version)  set_version="${2:?--set-version needs a value}"; shift ;;
    -h|--help)      sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)              echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

# ---------------------------------------------------------------- helpers

# Current version: explicit flag wins, else carry forward whatever the file already says.
current_version() {
  if [ -n "$set_version" ]; then
    printf '%s' "$set_version"
    return
  fi
  if [ -r "$TARGET" ]; then
    local v
    v=$(grep -m1 -iE '^[[:space:]]*sys version[[:space:]]*=' "$TARGET" 2>/dev/null \
        | sed 's/.*=[[:space:]]*//' | tr -d '\r') || true
    [ -n "${v:-}" ] && { printf '%s' "$v"; return; }
  fi
  printf 'UNREAD'
}

# "branch @ hash (tag) [N uncommitted]" — the branch and the dirty count matter as much as the
# hash: this image has shipped from a non-main branch with uncommitted edits before.
repo_state() {
  local dir="$1"
  [ -d "$dir/.git" ] || { printf 'UNREAD (no git tree at %s)' "$dir"; return; }
  local branch hash tag dirty
  branch=$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo UNREAD)
  hash=$(git -C "$dir" rev-parse --short=10 HEAD 2>/dev/null || echo UNREAD)
  tag=$(git -C "$dir" describe --tags --abbrev=0 2>/dev/null || echo 'no tag')
  dirty=$(git -C "$dir" status --porcelain 2>/dev/null | wc -l)
  printf '%s @ %s (last tag: %s)' "$branch" "$hash" "$tag"
  if [ "$dirty" -gt 0 ]; then
    printf ' [%s UNCOMMITTED — this image does NOT match any commit]' "$dirty"
  else
    printf ' [clean]'
  fi
}

# Units that start on boot on WHATEVER airframe this companion is bolted to. The drone needs
# tfmini enabled and the rover-* units disabled; the rover needs the reverse. Stamping the
# actual state keeps the before-flight revert checklist honest.
unit_states() {
  local u s found=0
  for u in rover-odometry rover-camera rover-scan rover-scan-3d rover-autonav-mode \
           rover-ekf-bridge rover-nav2 tfmini ldlidar ext5v-logger \
           microxrce-agent mavlink.router vision_streaming; do
    # is-enabled exits non-zero for a disabled unit while still printing "disabled",
    # so the exit status must be discarded and the verdict taken from stdout only.
    s=$(systemctl is-enabled "${u}.service" 2>/dev/null) || true
    [ -z "$s" ] && continue
    printf '#   %-22s %s\n' "$u" "$s"
    found=1
  done
  [ "$found" -eq 0 ] && printf '#   UNREAD (systemctl gave no answer)\n'
  return 0
}

# ---------------------------------------------------------------- build the stamp

build_stamp() {
  local ver os kernel model ros root_free
  ver=$(current_version)
  os=$( . /etc/os-release 2>/dev/null && printf '%s' "${PRETTY_NAME:-UNREAD}" )
  kernel=$(uname -r 2>/dev/null || echo UNREAD)
  model=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo UNREAD)
  ros="${ROS_DISTRO:-$(ls -1 /opt/ros 2>/dev/null | head -1)}"
  root_free=$(df -h / 2>/dev/null | awk 'NR==2 {print $4" free of "$2" ("$5" used)"}')

  printf '%s\n' "$BEGIN"
  printf 'sys version = %s\n' "$ver"
  printf 'Date = %s\n' "$(date '+%d/%m/%Y %H:%M')"
  printf '#\n'
  printf '# Stamped by codex-work/scripts/sys_version_stamp.sh. Re-run it before cutting an image.\n'
  printf '# Everything above the END marker is generated; the changelog below it is hand-written.\n'
  printf '#\n'
  printf '# --- host ---\n'
  printf '#   hostname             %s\n' "$(hostname 2>/dev/null || echo UNREAD)"
  printf '#   model                %s\n' "$model"
  printf '#   os                   %s\n' "$os"
  printf '#   kernel               %s\n' "$kernel"
  printf '#   ros distro           %s\n' "${ros:-UNREAD}"
  printf '#   root filesystem      %s\n' "${root_free:-UNREAD}"
  printf '#\n'
  printf '# --- repositories (the image is only as identified as these are) ---\n'
  printf '#   ros2_ws              %s\n' "$(repo_state /home/roz/ros2_ws)"
  printf '#   codex-work           %s\n' "$(repo_state /home/roz/codex-work)"
  printf '#\n'
  printf '# --- NOT ON THIS CARD, so not stamped here ---\n'
  printf '#   PX4 params, FC firmware and ESC config all live off-card. An image clone captures\n'
  printf '#   none of them. Records: px4_param_audit.md, pxlabs_release_note_v1.17.0-r2.1.md,\n'
  printf '#   esc_px4_config_audit_20260914.md. To know a param, READ THE FC.\n'
  printf '#\n'
  printf '# --- units enabled at boot (one image, two airframes — check before flight) ---\n'
  unit_states
  printf '%s\n' "$END"
}

# ---------------------------------------------------------------- emit

stamp=$(build_stamp)

case "$mode" in
  print)
    printf '%s\n' "$stamp"
    ;;

  diff|write)
    [ -r "$TARGET" ] || { echo "cannot read $TARGET" >&2; exit 1; }

    # Split the existing file: keep everything after the END marker. A file that has never been
    # stamped has no markers, so its whole body is the changelog and the stamp goes on top.
    if grep -qF "$END" "$TARGET"; then
      body=$(sed "1,/$(printf '%s' "$END" | sed 's/[][\.*^$/]/\\&/g')/d" "$TARGET")
    else
      # First run: drop the two legacy header lines, keep the rest verbatim.
      body=$(grep -vE '^[[:space:]]*(sys version[[:space:]]*=|Date[[:space:]]*=)' "$TARGET")
    fi

    new=$(printf '%s\n%s\n' "$stamp" "$body")

    if [ "$mode" = "diff" ]; then
      diff -u "$TARGET" <(printf '%s\n' "$new") && echo "(no change)"
      exit 0
    fi

    [ "$(id -u)" -eq 0 ] || { echo "--write needs root: sudo $0 --write" >&2; exit 1; }

    cp -p "$TARGET" "${TARGET}.bak-$(date '+%Y%m%d-%H%M%S')"
    tmp=$(mktemp "${TARGET}.XXXXXX")
    printf '%s\n' "$new" > "$tmp"
    chmod 0644 "$tmp"
    chown root:root "$tmp"
    mv "$tmp" "$TARGET"           # atomic replace, so a power cut cannot truncate the changelog
    echo "stamped $TARGET (backup alongside it)"
    ;;
esac
