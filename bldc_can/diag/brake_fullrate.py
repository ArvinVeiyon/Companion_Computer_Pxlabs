#!/usr/bin/env python3
"""Full-rate ESC brake logger. Records EVERY esc_status message, not a 5 Hz sample.

brake_run_record.py writes its CSV on a 0.2 s timer while esc_status arrives at ~98 Hz, so it
keeps ~1 sample in 20 and cannot see a braking current spike inside a 0.4 s stop. This records
every message, then reports the peak braking current per stop event.

    python3 brake_fullrate.py --seconds 60

⚠️ Refuses to score until it has seen a NON-ZERO baseline on esc_status -- a quiet topic is not
evidence of stillness.
"""
import argparse
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import EscStatus

WHEEL = {10: 'FR', 11: 'FL', 12: 'RR', 13: 'RL'}

ap = argparse.ArgumentParser()
ap.add_argument('--seconds', type=float, default=60.0)
a = ap.parse_args()

qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                 durability=DurabilityPolicy.VOLATILE,
                 history=HistoryPolicy.KEEP_LAST, depth=50)

rclpy.init()
n = Node('brake_fullrate')
samples = []   # (t, {wheel: (rpm, amp)})


def cb(msg):
    d = {}
    for e in list(msg.esc)[:msg.esc_count]:
        w = WHEEL.get(e.esc_address)
        if w:
            d[w] = (e.esc_rpm, e.esc_current)
    if d:
        samples.append((time.time(), d))


n.create_subscription(EscStatus, '/fmu/out/esc_status', cb, qos)

print(f"recording {a.seconds:.0f}s at full rate -- spin up and centre the stick, several times")
t0 = time.time()
while time.time() - t0 < a.seconds:
    rclpy.spin_once(n, timeout_sec=0.05)

n.destroy_node()
rclpy.shutdown()

if not samples:
    print("NO esc_status MESSAGES -- topic silent, nothing measured.")
    raise SystemExit(1)

span = samples[-1][0] - samples[0][0]
print(f"\n{len(samples)} samples over {span:.1f}s = {len(samples)/span:.1f} Hz")

W = ('FR', 'FL', 'RR', 'RL')
moved = [s for s in samples if any(abs(s[1].get(w, (0, 0))[0]) > 5 for w in W)]
print(f"samples with motion: {len(moved)}")
if not moved:
    print("WHEELS NEVER TURNED -- cannot score.")
    raise SystemExit(1)

print("\nper wheel over the whole run:")
for w in W:
    amps = [s[1][w][1] for s in samples if w in s[1]]
    rpms = [abs(s[1][w][0]) for s in samples if w in s[1]]
    print(f"  {w}: max|rpm|={max(rpms):7.0f}  PEAK BRAKING={min(amps):+7.2f} A  peak drive={max(amps):+7.2f} A")

# stop events: mean speed above 300 falling below 20
sp = [(s[0] - samples[0][0], sum(abs(s[1].get(w, (0, 0))[0]) for w in W) / 4.0,
       sum(s[1].get(w, (0, 0))[1] for w in W) / 4.0) for s in samples]
evs = []
i = 0
while i < len(sp):
    if sp[i][1] > 300:
        pk = i
        while i < len(sp) and sp[i][1] > 20:
            if sp[i][1] > sp[pk][1]:
                pk = i
            i += 1
        if i < len(sp):
            evs.append((pk, i))
    i += 1

print(f"\n{len(evs)} stop events:")
for pk, end in evs:
    seg = sp[pk:end + 1]
    amps = [x[2] for x in seg]
    print(f"  from {sp[pk][1]:6.0f} rpm | stop {sp[end][0]-sp[pk][0]:5.2f}s | "
          f"peak brake {min(amps):+6.2f} A | mean {sum(amps)/len(amps):+6.2f} A | n={len(seg)}")
