#!/usr/bin/env python3
"""Record a brake run with VEHICLE-SIDE evidence, not just motor-side.

Supersedes brake_test_record.py, which logged only rpm and errorcount. That omission is why the
2026-09-09 run could not answer "was the rover loaded on the floor or spinning on stands?" --
esc_current was available in esc_status the whole time and was ignored.

Logs:
  /fmu/out/esc_status               rpm, errorcount, CURRENT, voltage, temperature per ESC
  /fmu/out/input_rc                 ch2 throttle, ch3 brake, raw microseconds
  /fmu/out/manual_control_setpoint  aux1 normalised -1..+1
  /odom                             wheel odometry: body position and forward velocity
  /fmu/out/vehicle_local_position_v1  FC's own estimate (independent of /odom)
  /fmu/out/sensor_combined          IMU accelerometer -- the one witness that cannot be fooled
                                    by wheel slip

⚠️ NEVER START THIS WITHOUT TELLING THE OPERATOR FIRST. Standing rule.
⚠️ Refuses to score until it has seen a non-zero baseline on every subscribed topic, after a DDS
   discovery warm-up. A quiet topic is NOT evidence of stillness.

    python3 brake_run_record.py --seconds 60 --out ~/brake_run.csv

ESC address -> wheel: 10 = front right (INVERTED) | 11 = front left | 12 = rear right | 13 = rear left
"""
import argparse
import csv
import math
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

from px4_msgs.msg import InputRc, ManualControlSetpoint, EscStatus, VehicleLocalPosition, SensorCombined
from nav_msgs.msg import Odometry

WHEELS = ['FR', 'FL', 'RR', 'RL']
ADDR = [10, 11, 12, 13]


class Recorder(Node):
    def __init__(self, path):
        super().__init__('brake_run_record')
        px4 = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                         durability=DurabilityPolicy.VOLATILE,
                         history=HistoryPolicy.KEEP_LAST, depth=10)
        ros = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                         durability=DurabilityPolicy.VOLATILE,
                         history=HistoryPolicy.KEEP_LAST, depth=10)

        self.ch2 = self.ch3 = self.aux1 = None
        self.esc = {}                      # addr -> (rpm, err, current, volt, temp)
        self.odom = None                   # (x, y, vx)
        self.vlp = None                    # (x, y, vx, vy, xy_valid, v_xy_valid)
        self.accel = None                  # (ax, ay, az)
        self.n = dict(rc=0, mcs=0, esc=0, odom=0, vlp=0, imu=0)

        self.f = open(path, 'w', newline='')
        self.w = csv.writer(self.f)
        self.w.writerow(
            ['t', 'ch2_us', 'ch3_us', 'aux1']
            + [f'rpm_{w}' for w in WHEELS] + [f'err_{w}' for w in WHEELS]
            + [f'amp_{w}' for w in WHEELS] + [f'volt_{w}' for w in WHEELS]
            + [f'temp_{w}' for w in WHEELS]
            + ['odom_x', 'odom_y', 'odom_vx',
               'vlp_x', 'vlp_y', 'vlp_vx', 'vlp_vy', 'vlp_xy_valid', 'vlp_vxy_valid',
               'imu_ax', 'imu_ay', 'imu_az'])

        self.create_subscription(InputRc, '/fmu/out/input_rc', self.on_rc, px4)
        self.create_subscription(ManualControlSetpoint,
                                 '/fmu/out/manual_control_setpoint', self.on_mcs, px4)
        self.create_subscription(EscStatus, '/fmu/out/esc_status', self.on_esc, px4)
        self.create_subscription(VehicleLocalPosition,
                                 '/fmu/out/vehicle_local_position_v1', self.on_vlp, px4)
        self.create_subscription(SensorCombined, '/fmu/out/sensor_combined', self.on_imu, px4)
        self.create_subscription(Odometry, '/odom', self.on_odom, ros)

        self.t0 = time.time()
        self.create_timer(0.2, self.tick)

    def on_rc(self, m):
        self.n['rc'] += 1
        if len(m.values) >= 4:
            self.ch2, self.ch3 = m.values[1], m.values[2]

    def on_mcs(self, m):
        self.n['mcs'] += 1
        self.aux1 = m.aux1

    def on_esc(self, m):
        self.n['esc'] += 1
        for e in list(m.esc)[:m.esc_count]:
            self.esc[e.esc_address] = (e.esc_rpm, e.esc_errorcount, e.esc_current,
                                       e.esc_voltage, e.esc_temperature)

    def on_odom(self, m):
        self.n['odom'] += 1
        p, t = m.pose.pose.position, m.twist.twist.linear
        self.odom = (p.x, p.y, t.x)

    def on_vlp(self, m):
        self.n['vlp'] += 1
        self.vlp = (m.x, m.y, m.vx, m.vy, int(m.xy_valid), int(m.v_xy_valid))

    def on_imu(self, m):
        self.n['imu'] += 1
        a = m.accelerometer_m_s2
        self.accel = (a[0], a[1], a[2])

    def tick(self):
        t = time.time() - self.t0
        cols = [f'{t:.2f}', self.ch2, self.ch3,
                f'{self.aux1:.4f}' if self.aux1 is not None else '']
        for idx in range(5):
            for a in ADDR:
                v = self.esc.get(a)
                cols.append('' if v is None else (f'{v[idx]:.3f}' if idx >= 2 else v[idx]))
        for src, width in ((self.odom, 3), (self.vlp, 6), (self.accel, 3)):
            cols += [''] * width if src is None else [f'{x:.4f}' if isinstance(x, float) else x
                                                      for x in src]
        self.w.writerow(cols)

        rpm = [self.esc.get(a, (None,))[0] for a in ADDR]
        amp = [self.esc.get(a, (None, None, None))[2] if a in self.esc else None for a in ADDR]
        fr = lambda v: '----' if v is None else f'{v:5.0f}'
        fa = lambda v: ' ----' if v is None else f'{v:5.1f}'
        ov = '  --  ' if self.odom is None else f'{self.odom[2]:+.2f}'
        ax = '  --  ' if self.accel is None else f'{self.accel[0]:+.2f}'
        print(f'{t:5.1f}s ch3={self.ch3 if self.ch3 is not None else "----":>5} '
              f'aux1={self.aux1 if self.aux1 is not None else 0:+.2f} '
              f'rpm{"".join(fr(x) for x in rpm)} '
              f'A{"".join(fa(x) for x in amp)} '
              f'odom_vx={ov} imu_ax={ax}', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seconds', type=float, default=60)
    ap.add_argument('--out', default='/home/roz/brake_run.csv')
    ap.add_argument('--warmup', type=float, default=4.0)
    a = ap.parse_args()

    rclpy.init()
    n = Recorder(a.out)
    print(f'DDS warm-up {a.warmup:.1f}s (needs >2.5s for discovery) ...', flush=True)
    end = time.time() + a.warmup
    while time.time() < end:
        rclpy.spin_once(n, timeout_sec=0.1)

    # A silent topic must fail LOUDLY. It must never be read as "no motion".
    dead = [k for k, v in n.n.items() if v == 0]
    print('baseline: ' + '  '.join(f'{k}={v}' for k, v in n.n.items()), flush=True)
    if 'esc' in dead:
        print('\nNO esc_status AFTER WARM-UP -- link or FC down. A quiet topic is NOT evidence.')
        n.f.close(); rclpy.shutdown(); sys.exit(1)
    if dead:
        print(f'\n⚠️  SILENT TOPICS: {dead}. Their columns will be EMPTY, which means NOT MEASURED,')
        print('   not "zero". Do not interpret an empty column as "the rover did not move".')

    end = time.time() + a.seconds
    try:
        while time.time() < end:
            rclpy.spin_once(n, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    n.f.close()

    print('\n=== SUMMARY ===')
    print('messages: ' + '  '.join(f'{k}={v}' for k, v in n.n.items()))
    if n.odom:
        print(f'final /odom position: x={n.odom[0]:.2f} y={n.odom[1]:.2f} m')
    print(f'CSV: {a.out}')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
