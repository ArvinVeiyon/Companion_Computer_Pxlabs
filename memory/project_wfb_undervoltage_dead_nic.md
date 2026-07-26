---
name: project-wfb-undervoltage-dead-nic
description: LIKELY FIXED 2026-07-25 eve — XL4015 module @5.25V raised EXT5V 4.65-4.84V → ~5.00-5.09V, throttled=0x0, "dead" NIC d993c0 now 0 TX drops; ext5v-logger.service watching for load-transient dips
metadata: 
  node_type: memory
  type: project
  originSessionId: bb65f25d-0178-47c8-a2a3-6585b3e81df2
  modified: 2026-07-25T18:03:29.578Z
---

**LIKELY FIXED 2026-07-25 ~22:55 IST — power module replaced. Confirmation pending an armed run.**

## RESOLUTION 2026-07-25 evening: XL4015 buck @ 5.25 V

User replaced the companion power module with an **XL4015 buck set to 5.25 V output**. Measured after the swap (uptime 7 min, idle-ish load):

| | before (11:08) | after |
|---|---|---|
| EXT5V_V | 4.65–4.84 V | **4.969–5.093 V**, mean ~5.02 |
| get_throttled | 0x50000 | **0x0** — no sticky bits, clean since boot |
| dmesg undervoltage | 76/26 min | **zero this boot** |

**The "dead" NIC was never dead.** `WFB_NICS` is back to BOTH adapters (the 11:08 single-NIC edit did not survive the reboot — either `system_files_sync` restored it or it was re-added by hand; not established which). `wlx782288d993c0`, the one at 99.8 % TX drop this morning, now shows **0 tx_dropped across ~200k packets**. So the correction in §2 below — "brownout theory is WEAK, that NIC is probably faulty" — **was wrong**; the brownout really was killing it. TX diversity is restored without any hardware swap.

### The ~155 mV "drop" is an ADC OFFSET, not a wiring loss — DO NOT chase it
> **Correction.** An earlier reading of this (~0.25 V lost in cable, ~100 mΩ, "re-crimp the leads") was **WRONG**. It came from a single-point assumption (setpoint − measured = IR drop) instead of from the load correlation. Superseded by the evidence below.

Final state: XL4015 trimmed to **5.20 V under load, DMM-confirmed at the module output terminals**; Pi PMIC reports **5.045 V mean**. Gap ≈ 155 mV = **3.0 %**.

**Evidence it is not a real drop** (266 logged samples, core current 1.67–5.97 A):
- Regression `EXT5V vs VDD_CORE_A` slope = **+6.2 mV/A** (SE ≈ 2.2). Rail is FLAT — slightly rising — across a 4 A core swing (~0.83 A of input-current swing).
- **Resistance excluded**: 155 mV at 2.5 A ⇒ 62 mΩ, which must sag with load. It doesn't. Real series R is <20 mΩ (copper wire + crimps are fine).
- **Diode / ideal-diode FET excluded**: a Schottky would lose ~30 mV across that current swing ⇒ slope ≈ −7 mV/A. Measured +6.2 ± 2.2 ⇒ ~6σ the wrong way. (User's hypothesis was "is it the RasPi diode?" — answer: no.)
- **Pot changes don't propagate**: split at 23:06, BEFORE mean 5.0461 V (n=194) vs AFTER 5.0424 V (n=72), same 3.55 A mean load. −3.7 mV against sd ≈ 29 mV = noise.
- No passive element gives a fixed, current-independent 155 mV. An ADC reference offset does.
- `HDMI_V` tracks EXT5V (~5.02) at only 21 mA — but it senses DOWNSTREAM of the cable, so it does **not** discriminate ADC-offset from cable-loss. Only rules out anything internal to the Pi.

**Unconfirmed, the one test that would close it**: DMM at **GPIO pin 2/4 (5 V) → pin 6 (GND)** while running. ~5.19 V ⇒ ADC reads 3 % low, nothing wrong (expected). ~5.02 V ⇒ a real load-independent drop, which nothing ordinary explains — investigate the physical path then.

**Rules going forward:**
- **Do not raise the pot further.** 5.20 V actual is in spec (5 V ±5 % ⇒ 4.75–5.25) and near the top. Chasing the Pi's displayed 5.20 would put the real rail at ~5.37 V, out of spec.
- **Keep using the as-read thresholds** (healthy 5.0–5.1, knee 4.80) — the PMIC makes its own throttle/UV decisions on its own offset measurement, so as-read is the operative scale. Its 4.80 trip ≈ 4.95 V real.
- Reconciles the morning: 4.65–4.84 as-read ≈ 4.79–4.99 actual — genuinely marginal, PMIC really was tripping. The XL4015 moved it from actually-marginal to actually-fine.

### Watchdog installed — `ext5v-logger.service`
Because the failure mode is load-transient driven and every reading so far is at light load (nothing armed, VESCs idle), a logger now runs to catch dips during real runs.
- `/usr/local/bin/ext5v-logger` — 2 s samples → `/var/log/ext5v/ext5v.csv`; columns: EXT5V, VDD_CORE A/V, 3V3_SYS, temp, arm clock, throttled, **plus tx_dropped/tx_packets for every wlx NIC** (that correlation is the point). Warnings for rail <4.90 V or throttled≠0x0 go to `/var/log/ext5v/events.log`.
- `/usr/local/bin/ext5v-report [minutes]` — min/mean/max, headroom above 4.80 V, peak core current, dip counts, new TX drops in window, recent events.
- systemd unit enabled (survives reboot), `Restart=always`, `Nice=10`; logrotate at `/etc/logrotate.d/ext5v` (daily, 7, maxsize 50M, restarts service to rewrite CSV header).

**NEXT ACTION: after the next armed floor run, `ext5v-report 30`.** Verdict criteria — if `dips <4.80V` stays 0 and new TX drops stay 0 under VESC load, close this issue. If dips appear, the wiring impedance is the remaining fault, not the module.

### Who reverted WFB_NICS — investigated 2026-07-25 eve: NOT system_files_sync
The single-NIC mitigation was **manually undone after ~11 minutes**, not lost to a reboot or the sync timer.

Forensics (mtime = content write, ctime = inode change):
- `/etc/default/wifibroadcast` mtime **2026-07-19 11:27:46**, ctime **2026-07-25 11:19:28**; byte-identical (md5 73a53a05…) to `wifibroadcast.bak-20260725-993c0`, whose ctime is 11:07:24 and whose mtime is the same 07-19 stamp ⇒ backup made with `cp -p`.
- ctime moving without mtime, onto content identical to that backup, = **`cp -p` restore of the backup over the live file**.
- Timeline: 11:07:24 backup → 11:08:05 edit + service restart → **11:19:28 restore** → 11:19:34 restart (6 s later). Reboot at 11:34 was AFTER, irrelevant.

**`system_files_sync` exonerated** — `rsync --files-from=$list / $repo_root/System_files`: source `/`, dest the REPO. It only reads /etc and git-commits; it never writes to /etc. Also its 10:42 and 11:40 runs both logged `drone is ARMED — skipping sync` and did nothing, and the repo copy last changed 2026-07-19 13:26 (still dual-NIC — the single-NIC state was never captured).

Who did it is unrecoverable: `~/.bash_history` last flushed 10:00 (shell died without clean exit, consistent with the recorded `pkill -f` self-kills), root history empty.

**Two takeaways:** (1) `/etc/default` edits do NOT silently revert on reboot — the sync timer is safe to leave enabled. (2) **`system_files_sync` SKIPS ENTIRELY whenever the FC reports armed** (twice on 2026-07-25) — do not rely on it as a backup during active work sessions.

---
### (superseded) mitigation of 2026-07-25 11:08 — was live only 11:08:05–11:19:28

## Mitigation applied 2026-07-25 11:08
`/etc/default/wifibroadcast` → `WFB_NICS="wlx782288d98f91"` (was both NICs). Backup at `/etc/default/wifibroadcast.bak-20260725-993c0`. Restarted `wifibroadcast@drone`. **That file is the ONLY place WLANS is defined** — the unit builds `--wlans ${WFB_NICS}`; `/etc/wifibroadcast.cfg` does not name NICs.

Result over 15 s: `tx_packets +5086, tx_dropped +0` (was 96% dropped). Zero "packets dropped" lines and zero antenna-switch flapping in the journal since restart. Remaining log noise is single-packet **rx** loss (uplink GS→drone) = the separate [[project-gcs-link-degraded]] issue, unchanged by this.

**Now running single-adapter — no TX diversity.** Restore both NICs only after the power fix, and re-test d993c0 then; it may recover once the rail is stable.

## STILL OPEN: the brownout itself
After the change: **11 undervoltage events in 3 min**, `throttled=0x50000` unchanged. Removing the NIC from WFB's list does NOT unpower it — d993c0 is still enumerated and UP, still drawing. Load did fall 6.2 → 3.8. **Fixes 1/2/4 below are still required.**

Symptom: WFB link intermittently disconnects. Two independent, linked causes — both measured, not inferred.

## 1. Adapter `wlx782288d993c0` is effectively dead (immediate cause)
Cumulative this boot: `tx_packets=148`, `tx_dropped=83099` (**99.8% of injected frames dropped**), `rx_packets=716` vs the healthy twin's 57941.
Live 5s delta: d993c0 `+38 tx / +962 dropped`; d98f91 `+633 tx / +0 dropped`.
Config is IDENTICAL on both (monitor, ch161, 30 dBm, carrier=1, operstate=up) → this is power/hardware, not config.

wfb-server runs `--wlans wlx782288d993c0 wlx782288d98f91`, so **wlan 0 = the dead one**. `AntStatsAndSelector` keeps switching TX onto it every 2-6s ("Switch TX wlan 1 -> 0, RSSI -47 -> -44"), and every switch dumps video/mavlink/tunnel packets (video tx 72-165 dropped per burst). **That flapping IS the user-visible intermittent disconnect.**

## 2. 5V rail brownout (underlying cause) — **ANALYSIS CORRECTED 2026-07-25 by user**

> **CORRECTION.** The original USB-draw arithmetic below (~3.0 A) was WRONG. User pointed out both WFB NICs are externally powered; verified: the VIA Labs hub is **SELF-POWERED** (`lsusb -v -d 2109:3431` → `bmAttributes 0xe0` = Self Powered, ganged power switching). Devices behind it do NOT draw from the Pi rail. **Real Pi-rail USB load ≈ 1.9 A declared** (Orbbec 896 + LG cam 500 + 8821CU 500), all on direct root ports.
>
> **The USB config limit is NOT the cause.** `usb_max_current_enable=0` confirmed (budget 600 mA), but exceeding that limit produces *over-current* events + port power-down — dmesg has **ZERO** over-current messages. `Undervoltage detected` comes from the PMIC watching the **input** rail sag, a different mechanism.
>
> **Real cause = inadequate 5 V supply path.** Measured `EXT5V_V` = **4.65–4.84 V**, inversely tracking `VDD_CORE_A` (2.7–4.9 A). Healthy is 5.0–5.1 V; Pi 5 trips ~4.8 V, so it sits below the line most of the time. Fix is PSU/cable/BEC — official 27W 5A brick, suspect the USB-C cable first (thin/long = classic sag), or if fed from a rover BEC raise setpoint to 5.1–5.2 V and check gauge/crimps.
>
> **DO NOT set `usb_max_current_enable=1`** while the rail is at 4.7 V — it permits MORE draw from a supply that already can't hold 5 V. Makes it worse.
>
> **Knock-on: the "brownout killed d993c0" theory is WEAK.** That NIC is externally powered behind a self-powered hub, so it's more likely genuinely faulty, or its own power-injection feed / antenna is bad. Check that NIC's external feed and swap it before writing it off.

### (original, partly-wrong reasoning kept for context)
`vcgencmd get_throttled` = **0x50000** (bit16 under-voltage HAS occurred + bit18 throttling HAS occurred; low bits clear = not throttling at that instant).
Undervoltage events per boot — this is the smoking gun that it is NEW:
- boot 0 (26 min): **76 events** · boot -1 (35 min): 1 · boot -2 (6 days): 0 · boot -3: 0

Declared USB draw ≈ **3.0 A** (VIA hub 100mA + 2×500mA WFB + Orbbec 896mA + LG cam 500mA + RTL8821CU 500mA) against the **Pi5 default 600mA USB budget** (1.6A only with a detected 5A/PD PSU). `usb_max_current_enable` is **absent** from /boot/firmware/config.txt. Simultaneously `VDD_CORE_A = 4.24 A` with load average 6.2 on 4 cores (autonav stack + ffmpeg + wfb_tx all competing; wfb_tx alone 36% CPU).
No explicit USB over-current in dmesg. Temp fine (59.8°C).

**Both WFB adapters hang off the same BUS-POWERED VIA Labs hub (bus 001, declares 100mA for itself)** — classic brownout topology. Same failure mode as [[project-relay2-relaystn]] (WFB card browning out the Pi4 USB budget; fix there was a powered hub).

Trigger: the RTL8821CU uplink (`wlx90de80d824d6`, bus 006) went LIVE this boot — see [[project-external-wifi-uplink]]. It was merely enumerated in boot -2 (0 undervoltage); it is now associated + transmitting at 20 dBm on ch8 2.4GHz.

## Fixes, ranked
1. **Powered USB hub for the two WFB adapters** — the real fix.
2. 5A/27W PSU + add `usb_max_current_enable=1` to config.txt (600mA → 1.6A budget).
3. Interim: drop `wlx782288d993c0` from the WLANS list so WFB stops flapping onto a dead NIC — single-adapter but stable. Requires a WFB restart (drops the link briefly).
4. Shed CPU load (VDD_CORE 4.24 A is half the problem).

## Side observation
`dtoverlay=disable-wifi` IS present in config.txt (line 65) and the Pi rebooted after, but `wlan0` (2c:cf:67:47:f7:37, a Raspberry Pi MAC) **still enumerates** — DOWN, but iw reports it parked on ch34/5170MHz. The overlay did not fully take. Contradicts the "radio gone" claim in [[project-external-wifi-uplink]]; worth re-verifying.
