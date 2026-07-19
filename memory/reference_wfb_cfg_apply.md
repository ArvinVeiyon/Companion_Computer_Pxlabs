---
name: reference_wfb_cfg_apply
description: wfb-cfg-apply — WFB safe-config-apply watchdog with auto-rollback on companion + relay (QGC-driven)
metadata: 
  node_type: memory
  type: reference
  originSessionId: 016f9609-44d6-43f6-8782-0e4740c25207
---

**`/usr/local/sbin/wfb-cfg-apply`** (755 root:root, byte-identical on companion + relay, sha256 `cbaae331…`) — safe `wifibroadcast.cfg` apply with automatic rollback. The recovery net behind QGC's *Settings → WFB Config*; every ground-side config push runs through it so a bad RF setting can't permanently kill the link. Installed by the PXLABS G-Control/QGC project 2026-07-11.

**Flow:** sanity-check new cfg (`[common]`/`[base]`/`[video]`; refuses if target is `/etc/wifibroadcast.cfg` itself — callers stage to `/tmp/wfb-new.cfg`) → back up `/etc/wifibroadcast.cfg` → `.bak` → install → restart the ACTIVE WFB unit → background watchdog (`nohup`+`disown`, survives SSH drop) waits up to `timeout` s for `/run/wfb-cfg-confirm` (ground touches it once reachable again); no confirm → restore `.bak` + restart. Log: `/var/log/wfb-cfg-apply.log`.

**Active-unit auto-detect:** only running template instances `wifibroadcast@*` / `wifibroadcast-cluster@*`; oneshot `wifibroadcast.service` excluded. Companion → `wifibroadcast@drone`. Relay → `wifibroadcast@gs` (standalone, CURRENT) or `wifibroadcast-cluster@gs` (cluster).

**Invocation:** `sudo wfb-cfg-apply <new-cfg-path> [timeout]`, by `pxlabs_cli` over SSH. Commands: `wfb-config set` (one side), `set-both` (relay first then companion; neither confirmed until both applied, any failure rolls both back), `restore-default` (applies `/etc/wifibroadcast.cfg.default`).
**Timeouts:** single-side 60s; set-both → relay N (60/120 for channel/bw), companion 2N+60 (180/300). Channel/bandwidth = TIER2 danger (both ends must match, `--danger-ack`); MCS/TXpower/STBC/LDPC/FEC = TIER1.

**`/etc/wifibroadcast.cfg.default`** = QGC "Restore Default" baseline — DEVICE-SPECIFIC (companion 5443B vs relay 5580B, different content — do NOT cross-copy).

**Tracked in repos (2026-07-12):** both `System_files/usr/local/sbin/wfb-cfg-apply` + `System_files/etc/wifibroadcast.cfg.default` added to each `System_files_list.txt`. Restore rsync runs as root with `-p` → script restores as 755 root:root automatically. Companion tag `v1.2.0` (pushed to GitHub master + tag); relay release tag **`v1.0.5`** → commit `992b565` (relay's first-ever git v-tag; changelog row cites the same commit; branch tip `70ef6aa` = the align-doc commit on top, v1.0.4-style) + `sync-20260327-1206`→`992b565` (relay clock wrong, see [[project_relay_ntp_setup]]) — pushed to GitHub via merge-reconcile, see [[project_codexrelay_divergence]]. Docs: companion `system_companion.md` §7, relay `system_relay.md` §9/§12.
**Source of record = the devices.** PC reference copy: `tools/reference/wfb-cfg-apply` + `WFB_CONFIG_EDITOR.md` in QGC repo `ArvinVeiyon/PXLABS_qgroundcontrol` (branch `PXLABS-integration`). See [[reference_wfb_ng]], [[reference_wfb_rlyctl]].
