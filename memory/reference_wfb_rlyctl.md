---
name: wfb-rlyctl relay control tool
description: CLI tool on vind-rly relay that manages WFB-NG standalone/cluster mode switching, NIC config, and service restarts
type: reference
---

# wfb-rlyctl — Relay WFB-NG Control Tool

**Location (relay):** `/usr/local/sbin/wfb-rlyctl`
**Sudoers:** `/etc/sudoers.d/wfb-rlyctl` (passwordless sudo scoped to this script)
**ENV file it manages:** `/etc/default/wifibroadcast` (sets `WFB_NICS`)
**Profile:** defaults to `gs` (override with `PROFILE=<name>`)

## Commands

| Command | Description |
|---|---|
| `wfb-rlyctl status` | Show mode, ENV file contents, both service statuses |
| `wfb-rlyctl list-nics` | List wireless interfaces (wl*/wlan*) via ip link + iw dev |
| `wfb-rlyctl get-nics` | Print current `WFB_NICS` value from ENV file |
| `sudo wfb-rlyctl set-nics <iface> [iface2...]` | Update `WFB_NICS` in ENV file + restart standalone service |
| `sudo wfb-rlyctl restart` | Restart standalone service (daemon-reload first) |
| `sudo wfb-rlyctl use-standalone` | `disable --now` cluster → `enable --now` standalone |
| `sudo wfb-rlyctl use-cluster` | `disable --now` standalone → `enable --now` cluster |

## Units managed
- Standalone: `wifibroadcast@gs.service`
- Cluster:    `wifibroadcast-cluster@gs.service`

## How this was missed
MEMORY.md recorded `wfb_modes: switch: stop one, start other` as a manual procedure,
without knowing this dedicated tool existed. Found via `find / -name 'wfb-rlyctl'` on relay.
Always probe `/usr/local/sbin/` on relay for undocumented control scripts.
