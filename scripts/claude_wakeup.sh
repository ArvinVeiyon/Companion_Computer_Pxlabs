#!/usr/bin/env bash
# Claude Wake-Up Script — runs on SSH login to brief Claude with current system state
# Called from ~/.bashrc on interactive SSH sessions

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Vind-Roz Companion — $(date '+%Y-%m-%d %H:%M:%S')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Services status
echo ""
echo "[ Services ]"
services=(mavlink.router microxrce-agent rc_control_node tfmini vision_streaming ros2_px4_translation_node block-traffic)
for svc in "${services[@]}"; do
    status=$(systemctl is-active ${svc}.service 2>/dev/null)
    if [ "$status" = "active" ]; then
        echo "  ✔ ${svc}"
    else
        echo "  ✘ ${svc} ($status)"
    fi
done

# WFB tunnel
echo ""
echo "[ Network ]"
wfb_ip=$(ip addr show drone-wfb 2>/dev/null | grep 'inet ' | awk '{print $2}')
if [ -n "$wfb_ip" ]; then
    echo "  ✔ WFB tunnel: $wfb_ip"
else
    echo "  ✘ WFB tunnel: down"
fi

relay_ping=$(ping -c1 -W1 10.5.5.77 2>/dev/null | grep -c '1 received')
if [ "$relay_ping" = "1" ]; then
    echo "  ✔ Relay (vind-rly): reachable"
else
    echo "  ✘ Relay (vind-rly): unreachable"
fi

# Last sync
echo ""
echo "[ Last Auto-Sync ]"
last_sync=$(tail -3 ~/codex-work/logs/system_files_sync.log 2>/dev/null | grep -E 'sync (start|complete|no changes)' | tail -1)
echo "  ${last_sync:-no log found}"

# Git status
echo ""
echo "[ codex-work ]"
cd ~/codex-work
unpushed=$(git log origin/main..master --oneline 2>/dev/null | wc -l)
echo "  Branch: $(git branch --show-current) | Unpushed commits: $unpushed"
echo "  Last commit: $(git log --oneline -1)"

echo ""
echo "[ AI Mode ]"
if curl -s --max-time 3 --head https://api.anthropic.com > /dev/null 2>&1; then
    echo "  ◉ Online  — Claude API available (type: ai)"
else
    if systemctl is-active --quiet ollama && ollama list 2>/dev/null | grep -q "phi3"; then
        echo "  ◎ Offline — Phi-3 Mini ready (type: ai)"
    else
        echo "  ✘ Offline — Phi-3 Mini not ready (run: ollama pull phi3:mini)"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
