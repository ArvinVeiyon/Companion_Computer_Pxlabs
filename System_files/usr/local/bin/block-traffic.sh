#!/usr/bin/env bash
set -euo pipefail

IFACE="drone-wfb"
GROUP="239.255.0.1"
PORT_RANGE="7400:7500"
IPT="/usr/sbin/iptables"
LOGTAG="block-traffic"

if ! ip link show "$IFACE" &>/dev/null; then
  logger -t "$LOGTAG" "Interface $IFACE not found; no rules applied."
  exit 0
fi

add_rule() {
  if ! $IPT -C "$@" 2>/dev/null; then
    $IPT -A "$@"
    logger -t "$LOGTAG" "Added rule: $*"
  else
    logger -t "$LOGTAG" "Rule already exists: $*"
  fi
}

add_rule OUTPUT  -o "$IFACE" -d "$GROUP" -p udp --dport "$PORT_RANGE" -j DROP
add_rule FORWARD -o "$IFACE" -d "$GROUP" -p udp --dport "$PORT_RANGE" -j DROP
