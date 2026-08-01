---
name: feedback-check-docs-before-measuring
description: "Read the repo's own dimension/config docs BEFORE deriving vehicle geometry from sensor data. On 2026-08-01 an hour was lost and a wrong conclusion published because ground-to-top-plate was already documented."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 93b64ead-3e68-486d-b34f-783134bfb9b6
  modified: 2026-08-01T15:56:24.544Z
---

# Check the existing docs before measuring the vehicle from scratch

**RULE: before deriving any vehicle geometry from sensor data, read what the repo already records.**
Specifically `~/ros2_ws/docs/rover_autonav_requirements.md` (physical dimensions),
`docs/rover_autonav_collision_stop.md` (overhang + thresholds), and the **comments** in
`launch/depth_to_scan.launch.py` (what each `cam_*` value is composed of).

**Why:** on 2026-08-01 I spent ~1 h deciding whether a dense near-field return was the rover or the
room. I read the live TF `base_link->camera_link = (0,0,0.305)` and quoted it repeatedly, but never
checked **what 0.305 was made of**, and never opened the requirements doc. Both already said it:
- `docs/rover_autonav_requirements.md:75` — **ground to top plate 0.235 m**, plate 0.730 × 0.450 m
- `launch/depth_to_scan.launch.py:50` — **`cam_z 0.305` = 0.235 plate + 0.070 bracket**
The measured near band was **z mean 0.231 m** — a 4 mm match to the documented plate. The question was
answerable in five minutes. Instead I measured from scratch, **published a wrong reversal**
("it's room objects, not the rover"), and the user had to identify it twice.
Also missed: `front_overhang = 0.337 m` is not an abstract "bumper plane", it is **the front edge of
that same top plate**, measured against a wall over 178 scans on 07-28.

## 🔴 THE WORSE HALF: IT WAS ALREADY IN MEMORY, AND THE INDEX HID IT
`project_l4_gemini_nav2_prereqs.md` (2026-07-26) **already contained the entire finding**:
> "Hard floor is 17 mm … below that the rover's own deck appears in `/scan` as a permanent obstacle
> ~0.35 m ahead and the reflex collision-stop never releases."
> "**FOV vs the deck (user asked):** the deck IS in frame … the bottom ~third of the depth image is
> rover. Harmless for `/scan` … **Must be cropped for the L5 Nav2 voxel layer, which consumes the full
> cloud, or Nav2 marks a permanent obstacle round its own nose.**"
It even predicted that a **full-cloud** consumer (which `cloud_to_scan` is) would need the crop, and
explained why the old 2D `/scan` never saw the plate. **The user had asked about it before.**
**I never opened it, because its MEMORY.md index line said only `(Nav2 1.3.12 + slam_toolbox 2.8.5)`.**
⇒ **RULE: a memory file's index line must name its most LOAD-BEARING content, not the topic it was
created for.** Package versions are the least useful thing in that file. When adding a major finding
to an existing memory file, **update its MEMORY.md line too** — an unopened file is a lost file.
⇒ **RULE: before investigating any physical/geometry question, grep the WHOLE memory dir, not just the
files whose index lines sound relevant:** `grep -rniE "<dimension|part name>" ~/.claude/projects/-home-roz/memory/`

**How to apply:**
1. **Grep the docs for the dimension first** — `grep -rniE "plate|mount|overhang|bumper" docs/` — then
   measure to CONFIRM the documented value, not to discover it from nothing.
2. **Read the comments around a config value**, not just the value. `cam_z 0.305` carried its own
   derivation one line above the parameter.
3. When a measurement matches a documented number to a few mm, **say so explicitly** — that agreement
   is much stronger evidence than either source alone.
4. **The operator usually knows the hardware.** The user said "top plate" early; I argued the geometry
   said otherwise and was wrong. Treat their physical identification as strong evidence and go looking
   for why the data would support it, before contradicting it.

See [[project-perception-3d-costmap]] for the finding itself and the separate filter-population error
that made the reversal possible.
