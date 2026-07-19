---
name: project-ros2ws-tag-cleanup
description: "ros2_ws semver tag scheme (v1.1.0 baseline) — cleanup + branch consolidation DONE 2026-07-19, working branch = main"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5ff45709-5e20-4964-9bd8-fce6f3bc03f0
  modified: 2026-07-19T15:31:19.316Z
---

# ros2_ws tag scheme + cleanup — DONE 2026-07-19

## Version control scheme (ACTIVE)
- Annotated semver tags only: `vX.Y.Z` (no `_tested`/`_tetsed` suffixes — test status goes in the tag message).
- Baseline: **v1.1.0** on `5bace1b` (main_dev, 2026-07-19: vision_streaming v2.1 usbcam sysfs ids + ffmpeg watchdog).
- Create with `git tag -a vX.Y.Z -m "..."` then `git push origin vX.Y.Z`.
- Unmerged-but-kept work goes under `archive/*` tags, not branches.

## Cleanup executed 2026-07-19 (local + origin, verified identical)
- Final tags: `v1.0.0`, `v1.0.2` (retag of v1.0.2_tetsed/switch @1b90874, side commit), `v1.0.3` (retag of v1.0.3_tested @b15fe24), `v1.1.0`, `release-20260222`, `archive/tfmini-2025-09-09` (@739c6fc, unmerged tfmini branch tip), `archive/rov-ext-sep07` (@f65efef, unmerged rov_ext WIP).
- Final branches: `main`, `release/2026-02-22` only.
- Deleted tags: Drone_Tested, Rover_tfmini, Rover_collsion_tested_10_seb_2025(+_updated), collision_free_Roll_NT_10_sep_25, switch, v1.0.1_tetsed (dup of v1.0.0), v1.0.2_tetsed, v1.0.3_tested.
- Deleted branches (local + origin where they existed): Drone_Tested, Rover_tfmini, tfmini-improve, rover_tfmini_dev, rescue/now, rescue/rebase-sep07, rescue/rov-work, recover/sep07, backup/pre-pull-2025-09-07, test_v1.0.2, v1.0.2_tetsed.
- All deleted refs verified reachable from main_dev or preserved via retag/archive before deletion — nothing orphaned.

## Branch consolidation — DONE 2026-07-19 (user chose "keep either one")
- `main` fast-forwarded cabefb5→5bace1b and is now THE single working branch; `main_dev` deleted local+origin.
- Kept `main` (not main_dev) because GitHub default branch = main and no API token on companion (SSH-only) to change it; gh CLI not installed.
- origin/HEAD → main. Any old docs/scripts referencing main_dev must use main.

Related: [[project-codexwork-branches]], [[project-vision-multicam-upgrade]] (source of v1.1.0 content).
