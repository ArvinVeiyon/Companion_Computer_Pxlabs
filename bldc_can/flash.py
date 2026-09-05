#!/usr/bin/env python3
"""Flash ONE VESC over DroneCAN from the companion's can0.

Why not VESC Tool: the rover's VESCs run can_mode=1 (CAN_MODE_UAVCAN), and in that
mode comm/comm_can.c:1346 does `continue` on every received frame -- the VESC-native
CAN protocol that VESC Tool speaks is never decoded. comm_can_ping() also returns
false unconditionally (comm_can.c:650). A VESC Tool CAN scan finds nothing.

What the firmware does instead (libcanard/canard_driver.c), ArduPilot-style:
  1. We send uavcan.protocol.file.BeginFirmwareUpdate  -> handle_begin_firmware_update (:1171)
     The VESC erases its reserved new-app area and replies OK.
  2. The VESC then PULLS the image from us with repeated file.Read requests (send_fw_read, :1022).
     We are the file server; it is the client.
  3. On the short final chunk it writes size+CRC16 into the first 6 bytes and sets
     jump_to_bootloader (:1095-1153), then reboots into the bootloader.

Progress is observable: node_status.vendor_specific_status_code = 1 + (bytes_read / 1024)
(canard_driver.c:1156), so we read kB-transferred straight off NodeStatus.

Run:  ~/codex-work/bldc_can/venv/bin/python ~/codex-work/bldc_can/flash.py --target 11 --bin /path/to/60_mk5.bin
"""
import argparse
import os
import time

import dronecan

# canard_driver.c:153  NEW_APP_MAX_SIZE = 3 * (1 << 17)
NEW_APP_MAX_SIZE = 393216
# handle_file_read_response writes at fw_update.ofs+6, reserving 6 bytes for size+CRC.
MAX_IMAGE_BYTES = NEW_APP_MAX_SIZE - 6

VESC_NODES = {10: "RF (inverted)", 11: "FL", 12: "RR", 13: "RL"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iface", default="can0")
    ap.add_argument("--node-id", type=int, default=127,
                    help="our own node ID; must not collide with the FC or 10-13")
    ap.add_argument("--target", type=int, required=True,
                    help="VESC node ID to flash (= its controller_id): 10 RF, 11 FL, 12 RR, 13 RL")
    ap.add_argument("--bin", required=True, help="raw application image, e.g. 60_mk5.bin")
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = ap.parse_args()

    path = os.path.abspath(args.bin)
    if not os.path.isfile(path):
        print("FAIL: no such file: %s" % path)
        return 1

    size = os.path.getsize(path)
    print("image : %s" % path)
    print("size  : %d bytes" % size)

    # Pre-flight the size. PXLABS_RC_BRAKE_TESTING.md claims the artifact is 524,280 bytes,
    # which does NOT fit -- the transfer would run off the end of the reserved area.
    if size > MAX_IMAGE_BYTES:
        print("FAIL: image is %d bytes; the VESC reserves only %d (NEW_APP_MAX_SIZE=%d minus"
              " the 6-byte size/CRC header)." % (size, MAX_IMAGE_BYTES, NEW_APP_MAX_SIZE))
        print("      Do not flash this. Check that you exported the raw app image and not a"
              " padded or packaged file.")
        return 1
    print("fits  : yes (%d bytes headroom in the %d-byte new-app area)"
          % (MAX_IMAGE_BYTES - size, NEW_APP_MAX_SIZE))

    if args.target in VESC_NODES:
        print("target: node %d = %s" % (args.target, VESC_NODES[args.target]))
    else:
        print("target: node %d (NOT one of the four known rover VESCs)" % args.target)

    if not args.yes:
        if input("Rover on stands and DISARMED? Type 'flash' to proceed: ").strip() != "flash":
            print("aborted")
            return 1

    node = dronecan.make_node(args.iface, node_id=args.node_id, bitrate=1000000)
    monitor = dronecan.app.node_monitor.NodeMonitor(node)

    # Serve the image under a short basename. handle_begin_firmware_update rejects a
    # request whose payload exceeds sizeof(fw_update.path)+1, so keep the path short.
    remote_name = "fw.bin"
    dronecan.app.file_server.FileServer(node, path_map={remote_name: path})

    print("\nwaiting for node %d to announce itself..." % args.target)
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        node.spin(0.2)
        if monitor.exists(args.target):
            break
    else:
        print("FAIL: node %d never sent NodeStatus. Run scan.py first." % args.target)
        node.close()
        return 1
    print("node %d is present." % args.target)

    state = {"accepted": None}

    def on_response(event):
        if not event:
            state["accepted"] = False
            return
        state["accepted"] = (event.response.error == 0)

    req = dronecan.uavcan.protocol.file.BeginFirmwareUpdate.Request()
    req.source_node_id = args.node_id
    req.image_file_remote_path.path = remote_name
    node.request(req, args.target, on_response)

    print("sent BeginFirmwareUpdate; the VESC now pulls the image from us.\n")

    last_kb = -1
    started = time.monotonic()
    while time.monotonic() - started < args.timeout:
        node.spin(0.2)

        if state["accepted"] is False:
            print("FAIL: node %d rejected BeginFirmwareUpdate." % args.target)
            node.close()
            return 1

        entry = monitor.get(args.target) if monitor.exists(args.target) else None
        if entry is not None:
            # canard_driver.c:1156 -- 1 + kB transferred
            kb = entry.status.vendor_specific_status_code
            if kb != last_kb and kb > 0:
                last_kb = kb
                pct = min(100.0, 100.0 * ((kb - 1) * 1024) / size)
                print("\r  %6d kB / %6.1f kB  (%5.1f%%)" % (kb - 1, size / 1024.0, pct),
                      end="", flush=True)

    print()
    print("\nTransfer window ended. The VESC sets jump_to_bootloader on the final short chunk")
    print("and reboots, so it will drop off the bus briefly. Confirm with:")
    print("  ~/codex-work/bldc_can/venv/bin/python ~/codex-work/bldc_can/scan.py")
    print("then verify the running firmware hash before flashing the next one.")
    node.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
