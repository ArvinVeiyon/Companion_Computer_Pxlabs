#!/usr/bin/env python3
"""Record throttle-step response over DDS: commanded speed vs what the wheels actually did.

Answers the "why does it feel laggy" question with numbers instead of opinion. Samples on
every esc_status message (no fixed tick) so the rise is resolved properly:

    /fmu/out/manual_control_setpoint  -> throttle -1..+1 (the COMMAND)
    /fmu/out/input_rc                 -> ch2 raw us (throttle, RC_MAP_THROTTLE=2) + ch12 kill
    /fmu/out/esc_status               -> per-ESC rpm, current, errorcount (the RESPONSE)

Structure reused from brake_test_record.py, including its warm-up rule: a quiet topic is NOT
evidence, so this refuses to score until it has seen a non-zero baseline on esc_status.

    python3 step_response_record.py --seconds 120 --out ~/step_20260913.csv

Then: python3 step_response_analyse.py ~/step_20260913.csv

ESC address -> wheel: 10 = FR | 11 = FL | 12 = RR | 13 = RL
rpm here is MECHANICAL (esc_rpm); ERPM = rpm * 7. Speed m/s = rpm * 0.003900.
"""
import argparse
import csv
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

from px4_msgs.msg import InputRc, ManualControlSetpoint, EscStatus, VehicleStatus

ADDRS = (10, 11, 12, 13)
WHEEL = {10: 'FR', 11: 'FL', 12: 'RR', 13: 'RL'}
RPM_TO_MS = 0.003900          # validated on the floor 2026-09-12
RPM_MAX_CMD = 9000 / 7.0      # uavcan_raw_rpm_max 9000 ERPM -> 1286 mechanical rpm at full stick


class Recorder(Node):
    def __init__(self, path):
        super().__init__('step_response_record')
        qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                         durability=DurabilityPolicy.VOLATILE,
                         history=HistoryPolicy.KEEP_LAST, depth=10)
        self.thr = None            # normalised throttle command
        self.yaw = None            # normalised yaw command (unused on this rover)
        self.roll = None           # THE TURN/SPIN AXIS on this rover: ch1 -> roll.
                                   # Probed 2026-09-13: ch4/yaw never moves, RC_MAP_YAW=4
                                   # is a red herring. 360s come from roll.
        self.ch1 = None
        self.ch2 = None
        self.ch4 = None
        self.ch12 = None
        self.n_rc = self.n_mcs = self.n_esc = 0
        self.armed = None
        self.max_abs_rpm = 0
        self.faults = {}
        self.last_print = 0.0

        self.f = open(path, 'w', newline='')
        self.w = csv.writer(self.f)
        self.w.writerow(['t', 'thr', 'roll', 'yaw', 'ch1_us', 'ch2_us', 'ch4_us', 'ch12_us', 'armed',
                         *[f'rpm_{WHEEL[a]}' for a in ADDRS],
                         *[f'cur_{WHEEL[a]}' for a in ADDRS],
                         *[f'err_{WHEEL[a]}' for a in ADDRS]])

        self.create_subscription(InputRc, '/fmu/out/input_rc', self.on_rc, qos)
        self.create_subscription(ManualControlSetpoint,
                                 '/fmu/out/manual_control_setpoint', self.on_mcs, qos)
        self.create_subscription(EscStatus, '/fmu/out/esc_status', self.on_esc, qos)
        self.create_subscription(VehicleStatus, '/fmu/out/vehicle_status_v1', self.on_vs, qos)
        self.t0 = time.time()

    def on_vs(self, m):
        self.armed = 1 if m.arming_state == 2 else 0

    def on_rc(self, m):
        self.n_rc += 1
        if len(m.values) >= 12:
            self.ch1 = m.values[0]        # the spin stick
            self.ch2 = m.values[1]
            self.ch4 = m.values[3]        # RC_MAP_YAW = 4: the spin stick
            self.ch12 = m.values[11]

    def on_mcs(self, m):
        self.n_mcs += 1
        self.thr = m.throttle
        self.yaw = m.yaw
        self.roll = m.roll

    def on_esc(self, m):
        self.n_esc += 1
        rpm, cur, err = {}, {}, {}
        for e in list(m.esc)[:m.esc_count]:
            a = e.esc_address
            if a not in ADDRS:
                continue
            rpm[a] = e.esc_rpm
            cur[a] = e.esc_current
            err[a] = e.esc_errorcount
            self.max_abs_rpm = max(self.max_abs_rpm, abs(e.esc_rpm))
            if e.esc_errorcount:
                self.faults.setdefault(a, set()).add(e.esc_errorcount)

        t = time.time() - self.t0
        self.w.writerow([f'{t:.3f}',
                         '' if self.thr is None else f'{self.thr:.4f}',
                         '' if self.roll is None else f'{self.roll:.4f}',
                         '' if self.yaw is None else f'{self.yaw:.4f}',
                         self.ch1 if self.ch1 is not None else '',
                         self.ch2 if self.ch2 is not None else '',
                         self.ch4 if self.ch4 is not None else '',
                         self.ch12 if self.ch12 is not None else '',
                         '' if self.armed is None else self.armed,
                         *[rpm.get(a, '') for a in ADDRS],
                         *[f'{cur[a]:.2f}' if a in cur else '' for a in ADDRS],
                         *[err.get(a, '') for a in ADDRS]])

        if t - self.last_print >= 0.5:
            self.last_print = t
            want = 0.0 if self.thr is None else self.thr * RPM_MAX_CMD
            got = rpm.get(13)
            fmt = lambda v: '----' if v is None else f'{v:5d}'
            c = lambda a: '  -- ' if a not in cur else f'{cur[a]:+5.1f}'
            print(f'{t:6.1f}s  thr={0.0 if self.thr is None else self.thr:+.3f} '
                  f'roll={0.0 if self.roll is None else self.roll:+.3f} '
                  f'want={want:6.0f}rpm  got RL{fmt(got)}  '
                  f'FR{fmt(rpm.get(10))} FL{fmt(rpm.get(11))} RR{fmt(rpm.get(12))}  '
                  f'A {c(13)}  {"?" if self.armed is None else ("ARMED" if self.armed else "disarmed")}',
                  flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seconds', type=float, default=120)
    ap.add_argument('--out', default='/home/roz/step_response.csv')
    ap.add_argument('--warmup', type=float, default=3.0)
    a = ap.parse_args()

    rclpy.init()
    n = Recorder(a.out)
    print(f'DDS warm-up {a.warmup:.1f}s ...', flush=True)
    end = time.time() + a.warmup
    while time.time() < end:
        rclpy.spin_once(n, timeout_sec=0.1)
    if n.n_esc == 0:
        print('\nNO esc_status SAMPLES AFTER WARM-UP -- this is NOT "no faults".')
        print('The link, the FC, or ESC power is down. A quiet topic is not evidence.')
        n.f.close()
        rclpy.shutdown()
        sys.exit(1)
    print(f'baseline OK: input_rc {n.n_rc}  manual_control_setpoint {n.n_mcs}  '
          f'esc_status {n.n_esc}\n', flush=True)
    print('DRIVE NOW. Wanted: (1) several clean throttle STEPS from rest to a held position,')
    print('(2) a slow creep at the very bottom of the stick, (3) a release back to centre.\n',
          flush=True)

    end = time.time() + a.seconds
    try:
        while time.time() < end:
            rclpy.spin_once(n, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass

    n.f.close()
    print('\n=== SUMMARY ===')
    print(f'samples: input_rc {n.n_rc}  manual_control_setpoint {n.n_mcs}  esc_status {n.n_esc}')
    print(f'peak |rpm|: {n.max_abs_rpm}  ({n.max_abs_rpm * RPM_TO_MS:.2f} m/s)')
    if n.max_abs_rpm < 50:
        print('WHEELS BARELY MOVED -- this run cannot measure response. Re-run and drive it.')
    if n.faults:
        for addr, codes in sorted(n.faults.items()):
            print(f'  {WHEEL[addr]} (addr {addr}) errorcount: {sorted(codes)}')
    else:
        print('esc_errorcount: 0 on all four')
    print(f'\nCSV: {a.out}')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
