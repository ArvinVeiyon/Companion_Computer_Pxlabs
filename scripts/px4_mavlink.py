#!/usr/bin/env python3
"""
PX4 MAVLink utility — connect via mavlink-router TCP:5760
Usage:
  python3 px4_mavlink.py monitor        # live STATUSTEXT / SYS_STATUS
  python3 px4_mavlink.py ls [path]      # list SD card directory
  python3 px4_mavlink.py rm-faults      # delete all fault_*.log from SD card
  python3 px4_mavlink.py shell <cmd>    # run NuttShell command
"""

import sys
import time
from pymavlink import mavutil

HOST = 'tcp:127.0.0.1:5760'


def connect():
    print(f"Connecting to {HOST}...")
    mav = mavutil.mavlink_connection(HOST, autoreconnect=False)
    mav.wait_heartbeat(timeout=8)
    print(f"Connected: sysid={mav.target_system} compid={mav.target_component}")
    return mav


def send_shell(mav, cmd):
    b = (cmd + '\n').encode()
    mav.mav.serial_control_send(
        mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL,
        mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE |
        mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND |
        mavutil.mavlink.SERIAL_CONTROL_FLAG_MULTI,
        0, 0, len(b), list(b) + [0] * (70 - len(b))
    )


def read_shell(mav, timeout=4):
    out = ''
    deadline = time.time() + timeout
    while time.time() < deadline:
        msg = mav.recv_match(type='SERIAL_CONTROL', blocking=True, timeout=0.5)
        if msg and msg.count > 0:
            out += bytes(msg.data[:msg.count]).decode(errors='replace')
    return out


def cmd_monitor(mav, duration=30):
    mav.mav.request_data_stream_send(
        mav.target_system, mav.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_ALL, 1, 1
    )
    print(f"Monitoring for {duration}s (Ctrl+C to stop)...\n")
    deadline = time.time() + duration
    while time.time() < deadline:
        msg = mav.recv_match(blocking=True, timeout=1)
        if msg is None:
            continue
        t = msg.get_type()
        if t == 'STATUSTEXT':
            sev = {0:'EMERG',1:'ALERT',2:'CRIT',3:'ERR',4:'WARN',5:'NOTICE',6:'INFO',7:'DEBUG'}.get(msg.severity, str(msg.severity))
            print(f"[{sev}] {msg.text.strip()}")
        elif t == 'SYS_STATUS':
            print(f"[SYS] voltage={msg.voltage_battery}mV load={msg.load/10:.1f}%")
        elif t == 'HEARTBEAT':
            print(f"[HB] type={msg.type} autopilot={msg.autopilot} mode={msg.custom_mode}")


def cmd_ls(mav, path='/fs/microsd'):
    send_shell(mav, f'ls {path}')
    time.sleep(0.5)
    out = read_shell(mav, 4)
    # strip ANSI / NSH prompt clutter
    import re
    out = re.sub(r'\x1b\[[^m]*m|\x1b\[K', '', out)
    print(out)


def cmd_rm_faults(mav):
    # find fault logs
    send_shell(mav, 'ls /fs/microsd')
    time.sleep(0.5)
    out = read_shell(mav, 4)

    import re
    out = re.sub(r'\x1b\[[^m]*m|\x1b\[K', '', out)
    fault_files = [line.strip() for line in out.splitlines() if line.strip().startswith('fault_') and line.strip().endswith('.log')]

    if not fault_files:
        print("No fault logs found.")
        return

    print(f"Found {len(fault_files)} fault log(s):")
    for f in fault_files:
        print(f"  {f}")

    for f in fault_files:
        send_shell(mav, f'rm /fs/microsd/{f}')
        time.sleep(0.3)
        result = read_shell(mav, 2)
        if 'failed' in result.lower() or 'error' in result.lower():
            print(f"FAIL: {f}")
        else:
            print(f"OK:   {f}")

    print("\nDone. Preflight crash dump warning should clear on next boot.")


def cmd_shell(mav, command):
    send_shell(mav, command)
    time.sleep(0.5)
    out = read_shell(mav, 5)
    import re
    out = re.sub(r'\x1b\[[^m]*m|\x1b\[K', '', out)
    print(out)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    mav = connect()

    if cmd == 'monitor':
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        cmd_monitor(mav, duration)
    elif cmd == 'ls':
        path = sys.argv[2] if len(sys.argv) > 2 else '/fs/microsd'
        cmd_ls(mav, path)
    elif cmd == 'rm-faults':
        cmd_rm_faults(mav)
    elif cmd == 'shell':
        if len(sys.argv) < 3:
            print("Usage: shell <command>")
            sys.exit(1)
        cmd_shell(mav, ' '.join(sys.argv[2:]))
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
