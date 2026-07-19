---
name: relay-ntp-setup
description: "Relay clock is chronically wrong (no RTC, no internet) — plan and status of setting companion up as local NTP server for it"
metadata: 
  node_type: memory
  type: project
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
---

Relay station (vind-rly, 10.5.5.77) and companion (Vind-Roz, 10.5.5.87) both appear to have no battery-backed RTC (RTC time reads back near epoch/boot time via `timedatectl`). The relay additionally has **no internet uplink at all** (`ping 8.8.8.8` → "Network is unreachable", DNS resolution fails) — confirmed 2026-07-11. So its `systemd-timesyncd`, pointed at `ntp.ubuntu.com`, can never sync, and the clock is left wherever it booted (e.g. found stuck at 2026-03-26 on 2026-07-11, ~3.5 months off). The earlier "fix" logged 2026-03-15 (just re-enabling NTP + restarting timesyncd) only worked because the clock happened to be closer to correct at that time — it does not survive a reboot/power cycle and is not a real fix.

**Why:** relay only has network reachability to the companion and GCS over the WFB tunnel (10.5.5.0/24) — no path to public NTP servers. It needs a time source that's actually reachable.

**Plan (not yet completed):**
1. Install `chrony` on companion, configure as NTP server: `local stratum 10` (or keep polling real upstream via internet + serve), `allow 10.5.5.0/24`. This will replace `systemd-timesyncd` on companion (apt shows chrony conflicts with/removes timesyncd package).
2. On relay, repoint `systemd-timesyncd`'s `NTP=` in `/etc/systemd/timesyncd.conf` to `10.5.5.87` (companion), clear `FallbackNTPServers`, restart.
3. Verify with `timedatectl status` / `chronyc clients` (on companion) that relay is syncing.

**Status 2026-07-11:** Attempt started but aborted before any package was installed or any config changed — see [[project_companion_network_degraded]] for why (apt installs became impractically slow on companion). No changes were made to either machine; this is still an open TODO (see `todos.md` item 1).

**How to apply:** Next time this is picked up, first check companion's network health (IPv6 reachability, actual throughput) before starting the chrony install — don't repeat the same slow-network surprise. If companion's link is healthy, the chrony install + config should take a few minutes.
