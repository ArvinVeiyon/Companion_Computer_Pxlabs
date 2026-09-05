#!/usr/bin/env python3
"""Catalog the VESC config XMLs in ~/codex-work/bldc_can/configs_from_repo/.

These are the configs committed to PXLABS_BLDC_VESC6_MK5 under Motp_Config_Bldc/.
They are a REFERENCE SET, not a backup of what is currently on the ESCs -- nobody has
verified they match the live hardware, and the filenames are unreliable (see below).

Prints an appconf table (CAN identity) and an mcconf table (motor identity), so you can
see which files are actually distinct and which wheel each one claims to be.

Run:  python3 ~/codex-work/bldc_can/catalog_configs.py
"""
import glob
import hashlib
import os
import xml.etree.ElementTree as ET

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs_from_repo")

# CAN identity + the DroneCAN-relevant fields.
APP_FIELDS = ["controller_id", "can_baud_rate", "can_mode", "uavcan_esc_index",
              "uavcan_raw_mode", "app_to_use", "can_status_rate_hz"]

# si_motor_poles is first on purpose: it is one half of the linked pair with the ROS-side
# erpm_to_ms=0.003900. Changing poles silently halves /odom.
MC_FIELDS = ["si_motor_poles", "motor_type", "si_gear_ratio", "si_wheel_diameter",
             "l_current_max", "l_in_current_max", "foc_motor_r", "foc_motor_l",
             "foc_motor_flux_linkage", "foc_sensor_mode"]


def grab(path, fields):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return None, str(exc)
    out = {}
    for f in fields:
        el = root.iter(f)
        v = next(el, None)
        out[f] = v.text.strip() if v is not None and v.text else ""
    return out, None


def table(paths, fields, title):
    rows = []
    for p in sorted(paths):
        vals, err = grab(p, fields)
        if err:
            rows.append((os.path.basename(p), {f: "PARSE-ERR" for f in fields}, ""))
            continue
        if not any(vals.values()):
            continue  # not this kind of file
        digest = hashlib.sha256(open(p, "rb").read()).hexdigest()[:8]
        rows.append((os.path.basename(p), vals, digest))

    if not rows:
        return
    print("\n=== %s (%d files) ===" % (title, len(rows)))
    w = max(len(r[0]) for r in rows)
    hdr = "%-*s %-8s " % (w, "FILE", "SHA") + " ".join("%-16s" % f[:16] for f in fields)
    print(hdr)
    print("-" * len(hdr))
    for name, vals, digest in rows:
        print("%-*s %-8s " % (w, name, digest) + " ".join("%-16s" % vals[f][:16] for f in fields))

    # Which files are byte-identical duplicates?
    seen = {}
    for name, _, digest in rows:
        seen.setdefault(digest, []).append(name)
    dupes = {d: n for d, n in seen.items() if len(n) > 1}
    if dupes:
        print("\n  byte-identical groups:")
        for d, names in dupes.items():
            print("    %s: %s" % (d, ", ".join(names)))


def main():
    paths = glob.glob(os.path.join(DIR, "*.xml"))
    if not paths:
        print("no XMLs in %s" % DIR)
        return 1
    table(paths, APP_FIELDS, "APP CONFIGS - CAN identity")
    table(paths, MC_FIELDS, "MOTOR CONFIGS - motor identity")
    print("\nNOTE: filenames lie. vesc_appconf_Tested_RL_11_Apr_26.xml and")
    print("      vesc_appconf_Aug_front_left_2026.xml BOTH carry controller_id=11 --")
    print("      the '11' in the RL filename is the April date, not the node ID.")
    print("      Map wheel -> node ID empirically with scan.py, one ESC at a time.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
