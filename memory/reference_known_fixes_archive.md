---
name: known-fixes-archive
description: "Chronological archive of resolved platform fixes (DKMS, kernel, services, WFB config)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
---

- rtl88x2eu DKMS: ARCH=aarch64 vs arm64 mismatch → fix in dkms.conf (see feedback_dkms_arch.md)
- auto-upgrades disabled 2026-03-15: unattended-upgrades + apt timers off (manual updates only)
- kernel upgraded 2026-03-09 by unattended-upgrades: 1018→1048-raspi (caused WFB-NG outage)
- tfmini.service 2026-03-15: removed invalid `Environment="source ..."` lines
- relay NTP fixed 2026-03-15: was 21d behind — timedatectl set-ntp true (NOTE: did not hold, recurred 2026-07-11 — see project_relay_ntp_setup.md)
- relay isc-dhcp-server + mediamtx disabled 2026-03-15: GCS static IP, mediamtx→latency
- ldlidar build fix 2026-04-17: added `#include <pthread.h>` to ldlidar_driver/src/logger/log_module.cpp (GCC 14+)
- ldlidar port fix 2026-04-17: hardcoded `/dev/ttyAMA3` in launch/ld19.launch.py line 35 — CLI port_name arg silently ignored by upstream
- WFB_NICS syntax fix 2026-05-10: /etc/default/wifibroadcast had two separate quoted strings instead of one — fixed to `WFB_NICS="wlx782288d993c0 wlx782288d98f91"` (both NICs present and UP)
