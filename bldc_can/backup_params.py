#!/usr/bin/env python3
"""Read and store every parameter a VESC exposes over DroneCAN, per node.

⚠️ THIS IS NOT A FULL CONFIG BACKUP AND CANNOT BE ONE.
The VESC exposes exactly 8 parameters over DroneCAN (canard_driver.c:225):
    can_baud_rate, can_status_rate_1, can_status_rate_2, can_status_msgs_r1,
    can_status_msgs_r2, can_esc_index, controller_id, ctl_dir
There is NO mcconf and NO full appconf on that interface. si_motor_poles, the FOC
constants (foc_motor_r / foc_motor_l / foc_motor_flux_linkage) and the current limits
are unreachable from CAN. Backing those up requires USB + VESC Tool, per ESC.

What this IS good for:
  * the wheel -> node ID map, captured one ESC at a time (that is what you are doing)
  * proving controller_id / can_esc_index / ctl_dir before and after a flash

Output: ~/codex-work/bldc_can/backups/params_<UTC timestamp>.json  (appended to, never overwritten)

Run:  ~/codex-work/bldc_can/venv/bin/python ~/codex-work/bldc_can/backup_params.py --label "rear left"
"""
import argparse
import datetime
import json
import os
import time

import dronecan

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
N_PARAMS = 8  # canard_driver.c:225, the whole table


def read_params(node, target, timeout=8.0):
    """Walk the parameter table by index until the node stops returning names."""
    got = {}
    pending = {"idx": 0, "done": False, "inflight": False}

    def on_response(event):
        pending["inflight"] = False
        if not event:
            pending["done"] = True
            return
        name = event.response.name.decode(errors="replace")
        if not name:
            pending["done"] = True
            return
        # value is a union; pull whichever field is populated.
        v = event.response.value
        val = None
        for field in ("integer_value", "real_value", "boolean_value", "string_value"):
            if hasattr(v, field):
                try:
                    val = getattr(v, field)
                except Exception:
                    continue
                if val is not None:
                    break
        if isinstance(val, bytes):
            val = val.decode(errors="replace")
        got[name] = val
        pending["idx"] += 1
        if pending["idx"] >= N_PARAMS:
            pending["done"] = True

    deadline = time.monotonic() + timeout
    while not pending["done"] and time.monotonic() < deadline:
        if not pending["inflight"]:
            req = dronecan.uavcan.protocol.param.GetSet.Request()
            req.index = pending["idx"]
            pending["inflight"] = True
            node.request(req, target, on_response)
        node.spin(0.1)

    return got


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iface", default="can0")
    ap.add_argument("--node-id", type=int, default=127)
    ap.add_argument("--label", default="",
                    help="which wheel is physically connected right now, e.g. 'rear left'")
    ap.add_argument("--seconds", type=float, default=6.0,
                    help="how long to listen for nodes before reading params")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    node = dronecan.make_node(args.iface, node_id=args.node_id, bitrate=1000000)
    monitor = dronecan.app.node_monitor.NodeMonitor(node)

    print("listening %.1fs for nodes on %s ..." % (args.seconds, args.iface))
    deadline = time.monotonic() + args.seconds
    while time.monotonic() < deadline:
        node.spin(0.2)

    entries = sorted(monitor.find_all(lambda _: True), key=lambda e: e.node_id)
    # Our own node does not appear in the monitor, but the FC will. Only VESCs answer
    # this parameter table, so a node returning 0 params is simply not a VESC.
    if not entries:
        print("FAIL: no DroneCAN nodes seen. Is can0 up? Run bringup.sh, then scan.py.")
        node.close()
        return 1

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    record = {
        "utc": stamp,
        "label": args.label,
        "iface": args.iface,
        "note": "PARTIAL backup: DroneCAN exposes only the 8-param table. "
                "No mcconf. Full backup requires USB + VESC Tool.",
        "nodes": {},
    }

    for e in entries:
        name = e.info.name.decode(errors="replace") if e.info is not None else ""
        print("\nnode %d (%s) -- reading params..." % (e.node_id, name or "unknown"))
        params = read_params(node, e.node_id)
        if params:
            for k, v in sorted(params.items()):
                print("    %-20s = %s" % (k, v))
        else:
            print("    (no parameters returned -- not a VESC, probably the FC)")
        record["nodes"][str(e.node_id)] = {"name": name, "params": params}

    out = os.path.join(OUT_DIR, "params_%s.json" % stamp)
    with open(out, "w") as f:
        json.dump(record, f, indent=2, sort_keys=True)
    print("\nstored: %s" % out)

    vesc_nodes = [n for n, d in record["nodes"].items() if d["params"]]
    if args.label and len(vesc_nodes) == 1:
        print("MAPPED: '%s' is node %s" % (args.label, vesc_nodes[0]))
    elif args.label and len(vesc_nodes) != 1:
        print("NOT MAPPED: %d VESCs answered, expected exactly 1 for a one-at-a-time map."
              % len(vesc_nodes))

    node.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
