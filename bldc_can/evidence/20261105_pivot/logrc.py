#!/usr/bin/env python3
"""Read-only: log manual_control_setpoint + raw RC ch1-6 to CSV. Usage: logrc.py SECONDS OUT.csv"""
import sys, time, rclpy
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import ManualControlSetpoint, InputRc
dur, out = float(sys.argv[1]), sys.argv[2]
qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                 history=HistoryPolicy.KEEP_LAST, depth=5)
rclpy.init(); n = rclpy.create_node('rc_drift_logger')
f = open(out, 'w'); f.write('t,src,roll,pitch,yaw,throttle,ch1,ch2,ch3,ch4,ch5,ch6\n')
rc = [0]*6
def on_rc(m): rc[:] = list(m.values[:6])
def on_mc(m):
    f.write(f"{time.time():.3f},{m.data_source},{m.roll:.3f},{m.pitch:.3f},{m.yaw:.3f},{m.throttle:.3f},"
            + ",".join(map(str, rc)) + "\n")
n.create_subscription(InputRc, '/fmu/out/input_rc', on_rc, qos)
n.create_subscription(ManualControlSetpoint, '/fmu/out/manual_control_setpoint', on_mc, qos)
end = time.time() + dur
while time.time() < end: rclpy.spin_once(n, timeout_sec=0.1)
f.close(); print('done', out)
