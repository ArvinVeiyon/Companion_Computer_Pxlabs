#!/usr/bin/env python3
"""Read-only COMM_GET_VALUES from each VESC on USB: v_in, rpm, currents, temps.

v_in is the discriminator between "board alive on USB 5V, pack OFF" and
"pack ON" -- a motor cannot spin in the first state, and the CAN transceiver
may be unpowered, which is exactly the esc_status silence we are seeing.
"""
import struct, sys, time, serial

def crc16(d):
    c = 0
    for b in d:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c

def frame(p):
    c = crc16(p)
    return bytes([0x02, len(p)]) + p + bytes([c >> 8, c & 0xFF, 0x03])

def read_frame(ser, t=1.5):
    end = time.monotonic() + t
    buf = bytearray()
    while time.monotonic() < end:
        buf += ser.read(128)
        while buf:
            if buf[0] != 0x02:
                del buf[0]; continue
            if len(buf) < 2: break
            n = buf[1]
            if len(buf) < 2 + n + 3: break
            pay = bytes(buf[2:2+n]); del buf[:2+n+3]
            return pay
        time.sleep(0.01)
    return None

for port in sys.argv[1:]:
    try:
        with serial.Serial(port, 115200, timeout=0.1) as ser:
            ser.reset_input_buffer()
            ser.write(frame(bytes([0])))            # COMM_FW_VERSION
            fw = read_frame(ser)
            fwtxt = f"{fw[1]}.{fw[2]} {fw[3:].split(b'0x00'.replace(b'0x00',b'\x00'))[0].decode('ascii','replace')}" if fw else "no reply"
            ser.reset_input_buffer()
            ser.write(frame(bytes([4])))            # COMM_GET_VALUES
            v = read_frame(ser)
            if not v or v[0] != 4:
                print(f"{port}: fw {fwtxt} | GET_VALUES no reply"); continue
            tfet  = struct.unpack('>h', v[1:3])[0] / 10
            tmot  = struct.unpack('>h', v[3:5])[0] / 10
            imot  = struct.unpack('>i', v[5:9])[0] / 100
            iin   = struct.unpack('>i', v[9:13])[0] / 100
            duty  = struct.unpack('>h', v[21:23])[0] / 1000
            rpm   = struct.unpack('>i', v[23:27])[0]
            vin   = struct.unpack('>h', v[27:29])[0] / 10
            print(f"{port}: fw {fwtxt} | V_IN {vin:6.1f} V | rpm {rpm:+6d} | "
                  f"i_mot {imot:+6.2f} A | i_in {iin:+6.2f} A | duty {duty:+.3f} | "
                  f"T_fet {tfet:.1f}C T_mot {tmot:.1f}C")
    except Exception as ex:
        print(f"{port}: ERROR {ex}")
