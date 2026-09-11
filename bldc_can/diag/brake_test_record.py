#!/usr/bin/env python3
"""Record an RC-brake bench test over DDS. No MAVLink, no VESC Tool needed.

Samples the three topics that matter and writes a CSV, printing a 5 Hz summary:

    /fmu/out/input_rc                 -> ch3 raw microseconds (the brake channel)
    /fmu/out/manual_control_setpoint  -> aux1 normalised -1..+1 (proves PROPORTIONALITY)
    /fmu/out/esc_status               -> per-ESC rpm and errorcount (proves BRAKING + no fault)

⚠️ Needs a DDS discovery warm-up before it counts. A short window returns zero samples on
healthy topics and looks exactly like a dead link -- so this refuses to start scoring until it
has seen a NON-ZERO baseline on esc_status.

    python3 brake_test_record.py --seconds 90 --out ~/brake_test.csv

ESC address -> wheel: 10 = front right (INVERTED) | 11 = front left | 12 = rear right | 13 = rear left
"""
import argparse
import csv
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

from px4_msgs.msg import InputRc, ManualControlSetpoint, EscStatus

WHEEL = {10: 'FR', 11: 'FL', 12: 'RR', 13: 'RL'}


class Recorder(Node):
    def __init__(self, path):
        super().__init__('brake_test_record')
        qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                         durability=DurabilityPolicy.VOLATILE,
                         history=HistoryPolicy.KEEP_LAST, depth=10)
        self.ch3 = None
        self.ch2 = None
        self.aux1 = None
        self.esc = {}          # addr -> (rpm, errorcount)
        self.n_rc = self.n_mcs = self.n_esc = 0
        self.seen_spin = False
        self.max_abs_rpm = 0
        self.faults = {}       # addr -> set of non-zero error codes seen

        self.f = open(path, 'w', newline='')
        self.w = csv.writer(self.f)
        self.w.writerow(['t', 'ch3_us', 'ch2_us', 'aux1',
                         'rpm_FR', 'rpm_FL', 'rpm_RR', 'rpm_RL',
                         'err_FR', 'err_FL', 'err_RR', 'err_RL'])

        self.create_subscription(InputRc, '/fmu/out/input_rc', self.on_rc, qos)
        self.create_subscription(ManualControlSetpoint,
                                 '/fmu/out/manual_control_setpoint', self.on_mcs, qos)
        self.create_subscription(EscStatus, '/fmu/out/esc_status', self.on_esc, qos)
        self.t0 = time.time()
        self.create_timer(0.2, self.tick)

    def on_rc(self, m):
        self.n_rc += 1
        if len(m.values) >= 4:
            self.ch3 = m.values[2]
            self.ch2 = m.values[1]

    def on_mcs(self, m):
        self.n_mcs += 1
        self.aux1 = m.aux1

    def on_esc(self, m):
        self.n_esc += 1
        for e in list(m.esc)[:m.esc_count]:
            addr = e.esc_address
            self.esc[addr] = (e.esc_rpm, e.esc_errorcount)
            if abs(e.esc_rpm) > self.max_abs_rpm:
                self.max_abs_rpm = abs(e.esc_rpm)
            if abs(e.esc_rpm) > 200:
                self.seen_spin = True
            if e.esc_errorcount:
                self.faults.setdefault(addr, set()).add(e.esc_errorcount)

    def row(self):
        rpm = [self.esc.get(a, (None, None))[0] for a in (10, 11, 12, 13)]
        err = [self.esc.get(a, (None, None))[1] for a in (10, 11, 12, 13)]
        return rpm, err

    def tick(self):
        t = time.time() - self.t0
        rpm, err = self.row()
        self.w.writerow([f'{t:.2f}', self.ch3, self.ch2,
                         f'{self.aux1:.4f}' if self.aux1 is not None else '',
                         *rpm, *err])
        fmt = lambda v: '----' if v is None else f'{v:5d}'
        a = '  --  ' if self.aux1 is None else f'{self.aux1:+.3f}'
        print(f'{t:6.1f}s  ch3={self.ch3 if self.ch3 is not None else "----":>5}us  '
              f'aux1={a}  rpm FR{fmt(rpm[0])} FL{fmt(rpm[1])} RR{fmt(rpm[2])} RL{fmt(rpm[3])}  '
              f'err {err[0]}/{err[1]}/{err[2]}/{err[3]}', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seconds', type=float, default=90)
    ap.add_argument('--out', default='/home/roz/brake_test.csv')
    ap.add_argument('--warmup', type=float, default=3.0)
    a = ap.parse_args()

    rclpy.init()
    n = Recorder(a.out)
    print(f'DDS warm-up {a.warmup:.1f}s ...', flush=True)
    end = time.time() + a.warmup
    while time.time() < end:
        rclpy.spin_once(n, timeout_sec=0.1)
    if n.n_esc == 0:
        print('\nNO esc_status SAMPLES AFTER WARM-UP -- do not read this as "no faults".')
        print('The link or the FC is down. Fix that first; a quiet topic is not evidence.')
        n.f.close()
        rclpy.shutdown()
        sys.exit(1)
    print(f'baseline OK: input_rc {n.n_rc}, manual_control_setpoint {n.n_mcs}, '
          f'esc_status {n.n_esc} msgs\n', flush=True)

    end = time.time() + a.seconds
    try:
        while time.time() < end:
            rclpy.spin_once(n, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass

    n.f.close()
    print('\n=== SUMMARY ===')
    print(f'samples: input_rc {n.n_rc}  manual_control_setpoint {n.n_mcs}  esc_status {n.n_esc}')
    print(f'peak |rpm| seen: {n.max_abs_rpm}')
    if not n.seen_spin:
        print('WHEELS NEVER SPUN (peak |rpm| < 200). A hand test cannot measure this brake --')
        print('it is regenerative, so torque scales with back-EMF. THIS RUN PROVES NOTHING')
        print('about braking authority. Re-run with the wheels driven under throttle.')
    else:
        print('wheels spun: OK, the run is measurable')
    if n.faults:
        for addr, codes in sorted(n.faults.items()):
            print(f'FAULT {WHEEL.get(addr, addr)} (addr {addr}): esc_errorcount {sorted(codes)}')
    else:
        print('esc_errorcount stayed 0 = NONE on every ESC for the whole run')
    print(f'CSV: {a.out}')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
