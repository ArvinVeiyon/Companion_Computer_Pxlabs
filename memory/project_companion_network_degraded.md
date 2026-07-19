---
name: companion-network-degraded
description: Companion (Vind-Roz) has broken IPv6 routing and very slow real bandwidth (~11 kB/s) — makes apt/package installs painfully slow
metadata: 
  node_type: memory
  type: project
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
---

Discovered 2026-07-11 while trying to install `chrony`: `apt-get update`/`install` hung for many minutes. Root causes found:

1. **IPv6 unreachable**: DNS for common repos (packages.ros.org, archive.ubuntu.com, download.zerotier.com) returns IPv6 addresses first, but `ping -6 2001:4860:4860::8888` → "Network is unreachable". apt/curl try IPv6, time out, then fall back to IPv4 — this adds long delays per host. Workaround: `apt-get -o Acquire::ForceIPv4=true ...` skips the IPv6 attempts.
2. **Genuinely slow IPv4 bandwidth**: even with IPv4 forced, observed throughput was ~11 kB/s (319 kB package took 28s). This is independent of the IPv6 issue and makes any apt install slow regardless.
3. Separately, the `packages.ros.org` ROS2 apt repo has an expired/missing GPG key (`NO_PUBKEY F42ED6FBAB17C654`) — unrelated to the above, just a warning during `apt-get update`, doesn't block other repos.

**Why this matters:** any future package install on companion (e.g. finishing the [[project_relay_ntp_setup]] chrony install) should expect this — either force IPv4 up front, or expect multi-minute waits, or investigate/fix the actual link speed first (this machine is Wi-Fi/cellular connected in the field, so slow bandwidth may be inherent to the connection, not a fixable bug).

**How to apply:** Before any apt operation on companion, consider `sudo apt-get -o Acquire::ForceIPv4=true install ...` to avoid IPv6 timeout overhead. If installs still take many minutes, that's the known slow link, not a hang — check `ps aux` for active apt/_apt processes actually transferring before assuming it's stuck.
