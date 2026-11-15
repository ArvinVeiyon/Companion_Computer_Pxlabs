---
name: relay-ntp-setup
description: "Relay clock sync — DONE: companion (chrony, RTC-backed since 11-15) serves time to the relay (timesyncd) over the WFB tunnel; relay's own RTC still does not hold"
metadata: 
  node_type: memory
  type: project
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
  modified: 2026-11-15T16:30:06.787Z
---

✅ **DONE — verified live 2026-11-15.** The relay (vind-rly, 10.5.5.77) takes its time from the companion (Vind-Roz, 10.5.5.87) over the WFB tunnel. (The install date was not recorded; the 2026-07-11 attempt was aborted, it was completed some time after.)

**What is deployed:**
- **Companion = server.** `chrony` (replaced `systemd-timesyncd`), upstream = Ubuntu pools, plus `/etc/chrony/conf.d/wfb-server.conf`: `allow 10.5.5.0/24` + `local stratum 10`. Listens on UDP 123.
- **Relay = client.** Still `systemd-timesyncd` (⛔ no chrony there — `chronyc` does not exist on the relay). `/etc/systemd/timesyncd.conf.d/companion.conf`: `NTP=10.5.5.87`, `FallbackNTP=` (empty).
- **Verify from the relay:** `timedatectl timesync-status` → `Server: 10.5.5.87`, packet count rising. On 11-15: offset −3.6 ms, delay 13 ms. ⚠️ `chronyc clients` on the companion needs sudo (`501 Not authorised` without).

**Companion RTC WORKS since 2026-11-15** (battery fitted, reads 2.90 V via `vcgencmd pmic_read_adc BATT_V`, trickle charge 3.0 V). Proof: kernel line `rpi-rtc: setting system clock to …` 12 s before chrony started, no chrony step, and the journal's boot start is the real time (the three boots before all start at a bogus `11-12 00:03`). ⇒ with `local stratum 10` the companion can serve correct time to the relay **with no internet**. ⚠️ Only a ~40 s power-off was tested — long holdover unproven.

**Relay has NO RTC BATTERY — measured 2026-11-15:** `BATT_V` = 0.0017 V (companion: 2.92 V, rising from 2.90 ⇒ charging), `charging_voltage` = 0, no `rtc`/`bbat` line in its `config.txt`. Kernel at boot: `rpi-rtc: setting system clock to 1970-01-01T00:00:17`. ⇒ the fixed bogus `Aug 23 15:33` it comes up with (seen 08-28 and 11-15) is NOT the RTC — it is systemd's fallback clock floor. Wrong until it reaches the companion. Not needed while the companion link is up; to make it standalone: fit a battery + `dtparam=rtc_bbat_vchg=3000000`. ⚠️ `vcgencmd` and `dmesg` need sudo on the relay; `hwclock` is not installed.

**Relay FAN verified 2026-11-15 (tach + operator's eyes).** Off below 50 °C by design (trips 50/60/67.5/75 °C, 5 °C hysteresis; relay idles ~43 °C), spins briefly at power-on — that is NORMAL, not a fault. Forced test: ~8,000 RPM at step 4 (PWM 250), ~2,700 at step 1. 🔑 To force it: `echo 4 > /sys/class/thermal/cooling_device0/cur_state` (root) **re-sent every second** — the thermal governor steps it back down within ~2 s; RPM = `/sys/devices/platform/cooling_fan/hwmon/hwmon*/fan1_input`.

**Why:** the relay has no internet uplink at all — only the companion and GCS on 10.5.5.0/24 — so public NTP was never reachable.

**How to apply:** relay timestamps are trustworthy only AFTER its first sync with the companion; before that (or with the companion off) they are Aug-23-based — read `/proc/uptime`. `timedatectl` showing RTC = system time on the relay proves nothing (NTP writes the RTC). Related: [[relay2-relaystn]], [[this-machine]].
