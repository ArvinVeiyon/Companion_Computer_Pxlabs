---
name: feedback-check-docs-before-measuring
description: "Read the repo's own dimension/config docs BEFORE deriving vehicle geometry from sensor data. On 2026-08-01 an hour was lost and a wrong conclusion published because ground-to-top-plate was already documented."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 93b64ead-3e68-486d-b34f-783134bfb9b6
  modified: 2026-08-01T15:53:01.576Z
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
