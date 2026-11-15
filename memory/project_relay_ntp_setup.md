---
name: relay-ntp-setup
description: "Relay clock sync — DONE: companion (chrony, RTC-backed since 11-15) serves time to the relay (timesyncd) over the WFB tunnel; relay's own RTC still does not hold"
metadata: 
  node_type: memory
  type: project
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
  modified: 2026-11-15T16:22:52.604Z
---

✅ **DONE — verified live 2026-11-15.** The relay (vind-rly, 10.5.5.77) takes its time from the companion (Vind-Roz, 10.5.5.87) over the WFB tunnel. (The install date was not recorded; the 2026-07-11 attempt was aborted, it was completed some time after.)

**What is deployed:**
- **Companion = server.** `chrony` (replaced `systemd-timesyncd`), upstream = Ubuntu pools, plus `/etc/chrony/conf.d/wfb-server.conf`: `allow 10.5.5.0/24` + `local stratum 10`. Listens on UDP 123.
- **Relay = client.** Still `systemd-timesyncd` (⛔ no chrony there — `chronyc` does not exist on the relay). `/etc/systemd/timesyncd.conf.d/companion.conf`: `NTP=10.5.5.87`, `FallbackNTP=` (empty).
- **Verify from the relay:** `timedatectl timesync-status` → `Server: 10.5.5.87`, packet count rising. On 11-15: offset −3.6 ms, delay 13 ms. ⚠️ `chronyc clients` on the companion needs sudo (`501 Not authorised` without).

**Companion RTC WORKS since 2026-11-15** (battery fitted, reads 2.90 V via `vcgencmd pmic_read_adc BATT_V`, trickle charge 3.0 V). Proof: kernel line `rpi-rtc: setting system clock to …` 12 s before chrony started, no chrony step, and the journal's boot start is the real time (the three boots before all start at a bogus `11-12 00:03`). ⇒ with `local stratum 10` the companion can serve correct time to the relay **with no internet**. ⚠️ Only a ~40 s power-off was tested — long holdover unproven.

**Relay RTC still does NOT hold.** It boots at a fixed bogus `Aug 23 15:33` (seen 08-28 and again 11-15 on `/dev/rtc0`'s stamp) and is wrong until it reaches the companion. `charging_voltage` = 0; battery presence unknown (`vcgencmd` needs sudo there). Not needed while the companion link is up; if a battery is fitted it needs `dtparam=rtc_bbat_vchg=3000000` to charge.

**Why:** the relay has no internet uplink at all — only the companion and GCS on 10.5.5.0/24 — so public NTP was never reachable.

**How to apply:** relay timestamps are trustworthy only AFTER its first sync with the companion; before that (or with the companion off) they are Aug-23-based — read `/proc/uptime`. `timedatectl` showing RTC = system time on the relay proves nothing (NTP writes the RTC). Related: [[relay2-relaystn]], [[this-machine]].
