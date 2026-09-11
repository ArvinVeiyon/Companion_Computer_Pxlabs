#!/usr/bin/env python3
"""Commit PX4's RAM parameters to flash (MAV_CMD_PREFLIGHT_STORAGE, param1=1).

set_param.py writes are RAM-only; this is the save step. NOT mavlink_shell --
that has wedged the FC's MAVLink link on this vehicle before.

Saves EVERYTHING currently in RAM, so only run when RAM is known-clean
(e.g. straight after a reboot plus the one change you meant to make).
"""
import sys
import time

from pymavlink import mavutil

m = mavutil.mavlink_connection('tcp:127.0.0.1:5760',
                               source_system=250, source_component=190)
print('connecting tcp:127.0.0.1:5760 ...', flush=True)
if m.wait_heartbeat(timeout=15) is None:
    print('NO HEARTBEAT — MAVLink link down')
    sys.exit(1)

m.mav.command_long_send(
    m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_PREFLIGHT_STORAGE, 0,
    1, 0, 0, 0, 0, 0, 0)          # param1 = 1 -> write parameters to storage
print('sent MAV_CMD_PREFLIGHT_STORAGE param1=1 (save)')

deadline = time.time() + 8
while time.time() < deadline:
    ack = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=2)
    if ack is None:
        continue
    if ack.command == mavutil.mavlink.MAV_CMD_PREFLIGHT_STORAGE:
        name = mavutil.mavlink.enums['MAV_RESULT'][ack.result].name
        print(f'COMMAND_ACK: result={ack.result} ({name})')
        sys.exit(0 if ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED else 1)

print('!! no COMMAND_ACK for PREFLIGHT_STORAGE — SAVE UNCONFIRMED.')
sys.exit(1)
