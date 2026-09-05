#!/usr/bin/env python3
"""List the DroneCAN nodes visible on can0.

Expected on the rover bus:
  node 10 = RF (inverted)   node 11 = FL   node 12 = RR   node 13 = RL
  plus the FC (PX4 uavcan, normally node 1).

The VESC node ID *is* its VESC controller_id -- canard_driver.c:1421 does
canardSetLocalNodeID(&canard_ins, conf->controller_id). There is no dynamic
allocation, so a node that does not appear here is genuinely not talking.

Run:  ~/codex-work/bldc_can/venv/bin/python ~/codex-work/bldc_can/scan.py
"""
import argparse
import time

import dronecan


HEALTH = {0: "OK", 1: "WARNING", 2: "ERROR", 3: "CRITICAL"}
MODE = {0: "OPERATIONAL", 1: "INITIALIZATION", 2: "MAINTENANCE",
        3: "SOFTWARE_UPDATE", 7: "OFFLINE"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iface", default="can0")
    ap.add_argument("--node-id", type=int, default=127,
                    help="our own node ID; must not collide with 1 or 10-13")
    ap.add_argument("--seconds", type=float, default=6.0)
    args = ap.parse_args()

    node = dronecan.make_node(args.iface, node_id=args.node_id, bitrate=1000000)
    monitor = dronecan.app.node_monitor.NodeMonitor(node)

    deadline = time.monotonic() + args.seconds
    while time.monotonic() < deadline:
        node.spin(0.2)

    entries = list(monitor.find_all(lambda _: True))
    if not entries:
        print("No DroneCAN nodes seen in %.1fs." % args.seconds)
        print("If candump shows traffic but this shows nothing, the bitrate is wrong.")
        print("If candump shows nothing either, suspect termination or the crystal.")
        node.close()
        return 1

    print("%-6s %-12s %-14s %-8s %s" % ("NODE", "HEALTH", "MODE", "UPTIME", "NAME"))
    for e in sorted(entries, key=lambda x: x.node_id):
        s = e.status
        name = ""
        if e.info is not None:
            name = e.info.name.decode(errors="replace")
        print("%-6d %-12s %-14s %-8d %s" % (
            e.node_id,
            HEALTH.get(s.health, str(s.health)),
            MODE.get(s.mode, str(s.mode)),
            s.uptime_sec,
            name,
        ))

    node.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
