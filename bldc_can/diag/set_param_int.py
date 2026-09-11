#!/usr/bin/env python3
"""Set an INT32 PX4 parameter over MAVLink, with readback verification.

Why this exists: ros2_ws/tools/set_param.py always sends MAV_PARAM_TYPE_REAL32,
and PX4 REFUSES the write when the onboard type is INT32 --
mavlink_parameters.cpp:129-131 requires (INT32,INT32) or (FLOAT,REAL32),
otherwise it logs "param types mismatch" and sets nothing.

PX4 then does param_set(param, &set.param_value) on the RAW 4 bytes, so an
INT32 value must be sent as the BIT PATTERN in the float field, not as 407.0.

Same arm guard as set_param.py: the check must come from the AUTOPILOT's
heartbeat (component 1), not from whatever heartbeat arrives first.

    python3 set_param_int.py RC_MAP_AUX1 3
    python3 set_param_int.py RC_MAP_AUX1          # read only
"""
import argparse
import struct
import sys
import time

from pymavlink import mavutil

TYPE_INT = {1, 2, 3, 4, 5, 6}


def as_int(msg):
    return struct.unpack('<i', struct.pack('<f', msg.param_value))[0]


def read(m, name, tries=5):
    for _ in range(tries):
        m.mav.param_request_read_send(
            m.target_system, m.target_component, name.encode(), -1)
        deadline = time.time() + 1.5
        while time.time() < deadline:
            r = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=1.5)
            if r is None:
                break
            if r.param_id.strip('\x00') == name:
                return r
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name')
    ap.add_argument('value', nargs='?', type=int, default=None)
    ap.add_argument('--url', default='tcp:127.0.0.1:5760')
    args = ap.parse_args()
    name = args.name.upper()

    m = mavutil.mavlink_connection(args.url, source_system=250, source_component=190)
    print(f'connecting {args.url} ...', flush=True)
    if m.wait_heartbeat(timeout=15) is None:
        print('NO HEARTBEAT — MAVLink link down')
        return 1

    before = read(m, name)
    if before is None:
        print(f'{name}: <no reply> — wrong name, or the link is busy. '
              f'Retry; do not assume it is unset.')
        return 1

    if before.param_type not in TYPE_INT:
        print(f'{name} is type {before.param_type} (NOT int) — '
              f'use ros2_ws/tools/set_param.py for float params.')
        return 1

    print(f'{name} currently = {as_int(before)}  (type {before.param_type})')

    if args.value is None:
        return 0

    hb = None
    deadline = time.time() + 5.0
    while time.time() < deadline:
        cand = m.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        if cand is None:
            continue
        if (cand.get_srcComponent() == mavutil.mavlink.MAV_COMP_ID_AUTOPILOT1
                and cand.autopilot != mavutil.mavlink.MAV_AUTOPILOT_INVALID):
            hb = cand
            break
    if hb is None:
        print('\nREFUSING: no AUTOPILOT heartbeat (component 1) within 5 s — '
              'cannot confirm the vehicle is disarmed. Not writing.')
        return 2
    armed = bool(hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
    print(f'  arm check: autopilot {hb.get_srcSystem()}:{hb.get_srcComponent()} '
          f'base_mode=0x{hb.base_mode:02x} armed={armed}')
    if armed:
        print('\nREFUSING: vehicle is ARMED.')
        return 2

    # PX4 reads the raw 4 bytes, so send the int's bit pattern in the float field.
    bits = struct.unpack('<f', struct.pack('<i', args.value))[0]
    print(f'writing {name} = {args.value} (as INT32 bit pattern) ...')
    m.mav.param_set_send(m.target_system, m.target_component, name.encode(),
                         bits, mavutil.mavlink.MAV_PARAM_TYPE_INT32)
    time.sleep(0.5)

    after = read(m, name)
    if after is None:
        print('!! no readback — CHANGE UNCONFIRMED.')
        return 1
    got = as_int(after)
    print(f'{name} now = {got}')
    if got != args.value:
        print(f'!! MISMATCH: asked {args.value}, got {got}. Not applied.')
        return 1
    print('verified.')
    print('NOTE: RAM write. Run param_save.py to commit it to flash.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
