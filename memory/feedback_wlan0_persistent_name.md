---
name: feedback_wlan0_persistent_name
description: "Onboard brcmfmac uplink naming — MAC pin alone NOT enough (rename race vs USB WFB adapters); fix = rename to wifi0 (collision-proof), decided 2026-07-19"
metadata: 
  node_type: memory
  type: project
  originSessionId: 41726602-da8e-4edf-b5e2-8b266624ecfa
---

**Problem history (3 recurrences):** Companion onboard Wi-Fi (`brcmfmac`, internet uplink) came up as `wlan1` instead of `wlan0`, breaking netplan (keyed by name) → no internet.

- 2026-07-12: pinned to MAC via udev — WRONG MAC (belonged to a different Pi5 board; OS/SD moved boards).
- 2026-07-19 am: MAC corrected to **`2c:cf:67:47:f7:37`** (base MAC `2C:CF:67:47:F7:34` in `/proc/cmdline`). RECURRED same day.
- 2026-07-19 pm root cause: **rename collision race**, not the MAC. Boot log:
  `(udev-worker) wlan1: Failed to rename network interface 4 from 'wlan1' to 'wlan0': File exists`
  A USB rtl88x2eu WFB adapter probes first and transiently holds kernel name `wlan0`; udev tries to rename brcmfmac (`wlan1`) → `wlan0` while it's still occupied, fails, and **never retries**. One second later the USB adapter becomes `wlx…` but it's too late. Race outcome is luck per boot. A later `udevadm`/netplan re-trigger succeeds (wlan0 free by then) — which made it LOOK intermittent.

**Fix (decided 2026-07-19, user-applied via sudo):** rename onboard chip to **`wifi0`** — a name the kernel never assigns (these drivers use `wlan%d`), so the rename can never collide. systemd-documented rule: never rename into the kernel's own namespace.

```
# /etc/udev/rules.d/70-persistent-net.rules
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="2c:cf:67:47:f7:37", NAME="wifi0"
```
Plus `s/wlan0/wifi0/g` in `/etc/netplan/50-cloud-init.yaml` + `netplan generate` + reboot.
Verify after reboot: `ip -br addr show wifi0` has 192.168.1.x, and `journalctl -b | grep 'Failed to rename'` is empty.

**Why:** wifi0 carries companion internet; netplan + [[todos]] #2 (disable-uplink-during-WFB) key on the interface name.

**Lessons:**
- If naming drifts, check BOTH: (1) rule MAC vs live `cat /sys/class/net/*/address` (board swap invalidates pins — also true for `wlx…` names in [[reference_wfb_ng]]); (2) `journalctl -b | grep 'Failed to rename'` for the race.
- Do NOT add a `wlan1:`/second block to netplan as a workaround — netplan generates a `netplan-wpa-<name>.service` waiting on a never-existing device → ~90 s boot delay + failed unit.
- Netplan never renames interfaces (its `set-name` is the same racy .link mechanism). Pin by MAC in udev to a NON-kernel-namespace name.
- 2026-07-19: cloud-init network regen DISABLED via `/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg`; `/etc/netplan/50-cloud-init.yaml` (root-only 600) is the single source of truth; `/boot/firmware/network-config` seed is inert.
