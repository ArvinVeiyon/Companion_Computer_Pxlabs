#!/usr/bin/env python3
"""Reboot the FC over DDS (VehicleCommand 246), not MAVLink.

Refuses to send if the FC reports ARMED. Modelled on tools/dds_setmode.py.
"""
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import VehicleCommand, VehicleStatus

ARMING_STATE_ARMED = 2


class Reboot(Node):
    def __init__(self):
        super().__init__('fc_reboot')
        qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                         durability=DurabilityPolicy.TRANSIENT_LOCAL,
                         history=HistoryPolicy.KEEP_LAST, depth=5)
        self.pub = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', qos)
        self.sub = self.create_subscription(VehicleStatus, '/fmu/out/vehicle_status_v1',
                                            self.cb, qos)
        self.nav = None
        self.arm = None

    def cb(self, msg):
        self.nav, self.arm = msg.nav_state, msg.arming_state

    def send(self):
        m = VehicleCommand()
        m.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        m.command = VehicleCommand.VEHICLE_CMD_PREFLIGHT_REBOOT_SHUTDOWN
        m.param1 = 1.0          # 1 = reboot autopilot
        m.target_system, m.target_component = 1, 1
        m.source_system, m.source_component = 1, 1
        m.from_external = True
        self.pub.publish(m)


rclpy.init()
n = Reboot()
t0 = time.time()
while time.time() - t0 < 4:
    rclpy.spin_once(n, timeout_sec=0.2)

print(f"before: nav_state={n.nav} arming_state={n.arm}")

if n.arm == ARMING_STATE_ARMED:
    print("REFUSING: FC reports ARMED. Disarm first.")
else:
    n.send()
    print("sent VEHICLE_CMD_PREFLIGHT_REBOOT_SHUTDOWN param1=1")

n.destroy_node()
rclpy.shutdown()
