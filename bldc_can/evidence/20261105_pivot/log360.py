#!/usr/bin/env python3
"""Read-only: poll COMM_GET_VALUES on all four VESCs, write CSV. Usage: log360.py SECONDS OUT.csv"""
import struct, sys, time, serial
sys.path.insert(0, '/home/roz/codex-work/bldc_can/diag')
from read_values import crc16, frame  # noqa (module body loops over argv[1:] = none)

NAMES = {10: 'FR', 11: 'FL', 12: 'RR', 13: 'RL'}
dur, out = float(sys.argv[1]), sys.argv[2]
ports = [serial.Serial(f'/dev/ttyACM{i}', 115200, timeout=0) for i in range(4)]

def get(ser):
    ser.reset_input_buffer(); ser.write(frame(bytes([4])))
    buf = bytearray(); end = time.monotonic() + 0.08
    while time.monotonic() < end:
        buf += ser.read(256)
        i = buf.find(0x02)
        if i >= 0 and len(buf) > i + 1 and len(buf) >= i + 2 + buf[i+1] + 3:
            p = bytes(buf[i+2:i+2+buf[i+1]])
            return p if p and p[0] == 4 else None
    return None

t0 = time.monotonic()
with open(out, 'w') as f:
    f.write('t,wheel,id,rpm,i_mot,i_in,duty,v_in,fault,t_fet\n')
    while time.monotonic() - t0 < dur:
        for s in ports:
            v = get(s)
            if not v: continue
            cid = v[58] if len(v) > 58 else -1
            f.write(f"{time.time():.3f},{NAMES.get(cid,'?')},{cid},"
                    f"{struct.unpack('>i', v[23:27])[0]},{struct.unpack('>i', v[5:9])[0]/100:.2f},"
                    f"{struct.unpack('>i', v[9:13])[0]/100:.2f},{struct.unpack('>h', v[21:23])[0]/1000:.3f},"
                    f"{struct.unpack('>h', v[27:29])[0]/10:.1f},{v[53]},{struct.unpack('>h', v[1:3])[0]/10:.1f}\n")
        f.flush()
        time.sleep(0.02)
print('done', out)
