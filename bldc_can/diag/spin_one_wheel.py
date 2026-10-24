#!/usr/bin/env python3
"""Spin ONE VESC over its own USB port, to map node ID -> physical wheel corner.

WHY THIS EXISTS
  PX4 cannot isolate a single wheel: UAVCAN_EC_FUNC1/3 are both Motor1 (right
  pair) and FUNC2/4 are both Motor2 (left pair), so every FC-side command
  reaches two wheels. The address <-> corner mapping has therefore never been
  verified against one turning wheel (reference_esc_telemetry). Talking straight
  to one ESC over USB is the only path that moves exactly one wheel.

  PX4 is not in the loop at all: no arming, no EKF bridge, no external mode.

HOW IT STOPS
  It stops sending. The VESC's own command timeout (300 ms) then applies
  timeout_brake_current = 2 A. Killing this script stops the wheel; it does not
  leave a latched setpoint. No 0-ERPM setpoint is written.

  All four ESCs are in RPM mode (uavcan_raw_mode 3), so COMM_SET_RPM ==
  mc_interface_set_pid_speed == the same speed loop the rover drives on.
  ERPM, not mechanical rpm: mech rpm = ERPM / 7.

Usage: python3 vesc_spin.py /dev/ttyACM1 [--erpm 600] [--seconds 3]
"""
import argparse
import struct
import sys
import time

import serial

COMM_FW_VERSION = 0
COMM_GET_VALUES = 4
COMM_SET_RPM = 8

ERPM_CAP = 1500          # hard ceiling: ~214 mech rpm, ~0.84 m/s equivalent
SECONDS_CAP = 6.0


def crc16(data: bytes) -> int:
    """CRC-16/XMODEM -- poly 0x1021, init 0x0000, as bldc crc.c computes it."""
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def frame(payload: bytes) -> bytes:
    if len(payload) > 255:
        raise ValueError("short frames only")
    c = crc16(payload)
    return bytes([0x02, len(payload)]) + payload + bytes([c >> 8, c & 0xFF, 0x03])


def read_frame(ser, timeout=1.0):
    """Return one reply payload, or None."""
    deadline = time.monotonic() + timeout
    buf = bytearray()
    while time.monotonic() < deadline:
        buf += ser.read(64)
        while buf:
            if buf[0] != 0x02:
                del buf[0]
                continue
            if len(buf) < 2:
                break
            n = buf[1]
            if len(buf) < 2 + n + 3:
                break
            payload = bytes(buf[2:2 + n])
            del buf[:2 + n + 3]
            return payload
        time.sleep(0.01)
    return None


def identify(ser) -> str:
    """COMM_FW_VERSION -- proves the framing and that this port is a live VESC."""
    ser.reset_input_buffer()
    ser.write(frame(bytes([COMM_FW_VERSION])))
    reply = read_frame(ser, 1.5)
    if not reply or reply[0] != COMM_FW_VERSION:
        return ""
    major, minor = reply[1], reply[2]
    hw = reply[3:].split(b"\x00")[0].decode("ascii", "replace")
    return f"fw {major}.{minor}  hw {hw}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("port")
    ap.add_argument("--erpm", type=int, default=600)
    ap.add_argument("--seconds", type=float, default=3.0)
    args = ap.parse_args()

    if abs(args.erpm) > ERPM_CAP:
        print(f"REFUSED: |erpm| {abs(args.erpm)} over the {ERPM_CAP} cap")
        return 2
    if not 0 < args.seconds <= SECONDS_CAP:
        print(f"REFUSED: seconds must be in (0, {SECONDS_CAP}]")
        return 2

    with serial.Serial(args.port, 115200, timeout=0.1) as ser:
        ident = identify(ser)
        if not ident:
            print(f"{args.port}: NO FW REPLY -- not spinning")
            return 1
        print(f"{args.port}: {ident}")
        print(f"COMMANDING {args.erpm} ERPM ({args.erpm / 7:.0f} mech rpm) "
              f"for {args.seconds:.1f} s -- WATCH WHICH WHEEL TURNS")

        payload = bytes([COMM_SET_RPM]) + struct.pack(">i", args.erpm)
        pkt = frame(payload)
        getv = frame(bytes([COMM_GET_VALUES]))
        peak_rpm, peak_i, n = 0, 0.0, 0
        end = time.monotonic() + args.seconds
        while time.monotonic() < end:
            ser.write(pkt)
            n += 1
            if n % 6 == 0:            # sample without breaking the 20 Hz cadence
                ser.write(getv)
                v = read_frame(ser, 0.12)
                if v and v[0] == COMM_GET_VALUES and len(v) >= 29:
                    rpm = struct.unpack(">i", v[23:27])[0]
                    imot = struct.unpack(">i", v[5:9])[0] / 100
                    if abs(rpm) > abs(peak_rpm):
                        peak_rpm = rpm
                    if abs(imot) > abs(peak_i):
                        peak_i = imot
            time.sleep(0.05)          # 20 Hz, well inside the 300 ms timeout

        print(f"PEAK DURING SPIN: {peak_rpm:+d} ERPM ({peak_rpm / 7:+.0f} mech rpm), "
              f"i_mot peak {peak_i:+.2f} A")
        if abs(peak_rpm) < 50:
            print("  🔴 THE MOTOR DID NOT TURN -- commanded but no rotation measured")
        print("STOPPED SENDING -- the ESC's 300 ms command timeout brakes it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
