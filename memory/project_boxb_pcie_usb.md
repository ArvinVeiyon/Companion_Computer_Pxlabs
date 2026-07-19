---
name: project-boxb-pcie-usb
description: "BOX-B PCIe→4x USB3.2 expansion on companion — PCIe link down, USB devices (Orbbec Gemini 336L + WFB adapter) not enumerating — OPEN"
metadata: 
  node_type: memory
  type: project
  originSessionId: cf514875-1225-439c-98e9-08753257c44a
  modified: 2026-07-19T04:14:45.369Z
---

# BOX-B PCIe→USB3.2 expansion — link training failure (OPEN, started 2026-07-19)

## Goal
Pi5 Module BOX-B case adds a PCIe→4-ch USB3.2 Gen1 controller via the Pi5 FFC PCIe
connector (PCIE1). Planned devices on it: **Orbbec Gemini 336L** depth camera (VID 2bc5)
+ one extra WFB adapter.

## Diagnosis 2026-07-19 (companion Vind-Roz, kernel 6.8.0-1048-raspi)
- Root cause located: `brcm-pcie 1000110000.pcie: link down` — the external FFC PCIe
  port never completes link training, so the BOX-B USB controller never appears in
  `lspci` and nothing behind it can enumerate. **Not a driver problem.**
- Software stack verified OK:
  - config.txt has `dtparam=pciex1` + `dtparam=pciex1_gen=2` (correct, DT status=okay)
  - `xhci_pci` module present in-kernel — no vendor driver needed for the USB controller
  - Internal PCIe (1000120000 → RP1) links fine Gen2 x4, so SoC PCIe works
- Re-probe test without reboot (re-triggers link training):
  `echo 1000110000.pcie | sudo tee /sys/bus/platform/drivers/brcm-pcie/bind`
  → still `link down` → electrical/physical issue, not boot timing.
- Note: user thought "PCIe driver installation" was needed — it isn't; xhci_pci is stock.

## Suspects (in order)
1. FFC cable orientation/seating (most common) — contacts must face correct side at
   BOTH ends, latch fully closed; cable not creased.
2. BOX-B external power — a 4-port USB3 board driving Gemini 336L + WFB adapter needs
   its own supply; if controller chip is unpowered → no link. (cf. [[project_relay2_relaystn]]
   USB power-budget lesson on RELAY-STN.)
3. Signal integrity — if 1+2 check out, test `dtparam=pciex1_gen=1` in config.txt.

## Status
- 2026-07-19: `dtparam=pciex1_gen=1` applied to config.txt on user request (backup:
  /boot/firmware/config.txt.bak-20260719). Awaiting power-cycle to test.
- 2026-07-19 ~10:20: rebooted with gen1 forced ("Forcing gen 1" confirmed in dmesg)
  → STILL `link down` at boot AND on live unbind/rebind re-probe. Gen1 test failed
  → signal-speed ruled out. Remaining suspects: FFC cable seating/orientation,
  BOX-B board power. Purely physical from here — no software steps left.
- sudo note: interactive password unavailable from CLI; NOPASSWD covers tee/cp/systemctl/
  journalctl/dmesg/reboot — edit root files via `sudo tee`/`sudo cp`.

## RESOLVED 2026-07-19 (boot 10:15:59, after user reseated FFC + verified power)
- PCIe link UP: `0000:01:00.0 VIA VL805/806 xHCI` (external FFC domain 0000), xhci_hcd bound.
  Root cause was physical (FFC seating/power) as suspected — software was never the problem.
- BOX-B USB topology: Bus 001 (USB2, VIA hub 2109:3431 4p) + Bus 002 (USB3 4p SuperSpeed).
  - Orbbec Gemini 336L (2bc5:0807) on Bus 002 @ 5 Gbps, uvcvideo bound → **/dev/video0-7**
  - WFB adapter wlx782288d993c0 (0bda:a81a) on Bus 001 port 4 @ 480M, rtl88x2eu bound, UP+in use
- User believed "USB not enumerated" — stale observation from before this boot; verify with
  `lsusb -t` (VL805 buses show as `xhci_hcd`, RP1 platform ones as `xhci-hcd`).

## Follow-ups spawned by the rebuild (state observed 2026-07-19)
- **Camera map changed — CONFIRMED OK by user 2026-07-19**: Orbbec owns /dev/video0-7;
  "LG Smart Cam" (30c9:009d, RP1 USB) = video8/9; the old front(/dev/video0)+bottom(/dev/video2)
  MJPEG cams are NOT connected anymore. vision_streaming.service streams /dev/video0 (Orbbec
  first node); user sees all cameras. [[reference_gcs_companion_interface]] camera table should
  be re-verified against this layout next time G-Control camera config is touched.
- **WFB dual-NIC RESTORED 2026-07-19 11:27 on user request**: `WFB_NICS="wlx782288d993c0 wlx782288d98f91"`
  (had been narrowed to single BOX-B NIC during rebuild, file mtime 01:01). Backup:
  /etc/default/wifibroadcast.bak-20260719-dualnic. Verified after restart: both wlx UP,
  TX antenna selector switching 0↔1 (RSSI -35/-43 dB), relay ping 13 ms 0% loss.
  Note one NIC is on BOX-B USB2 hub, the other on RP1 native USB.
- Watch VL805 power budget: Gemini 336L + WFB TX share the BOX-B board (cf. [[project_relay2_relaystn]]).
