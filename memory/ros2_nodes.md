---
name: ROS2 Node Details
description: Full ROS2 node package paths, pub/sub topics, hardware params, and configs for Vind-Roz companion
type: reference
originSessionId: d30954f2-0ebb-48f6-a7eb-06fd9278994d
---
## rc_control_node
pkg: rc_control | src: ros2_ws/src/rc_control/rc_control/rc_control_node.py
config: ros2_ws/src/rc_control/config/rc_mapping.yaml
sub: /fmu/out/input_rc (px4_msgs/InputRc, BEST_EFFORT)
CH9: camera switch (±50 PWM) | CH10: shutdown(1514)/reboot(2014) hold 2s

## vision_streaming_node
pkg: vision_streaming | src: ros2_ws/src/vision_streaming/vision_streaming/vision_streaming_node.py
config: /etc/vision_streaming.conf | switcher: /usr/local/bin/vision_config_manager (v1.2.1)
dual cam: /dev/video0 primary + /dev/video2 secondary (1280x720 MJPEG 2000K each)
FFmpeg: libx264 ultrafast yuv420p | PiP: 240x180 bottom-right
→ RTP 127.0.0.1:5602 → WFB-NG → GS 10.5.6.50:5600

## tfmini_node
pkg: tfmini_sensor | src: ros2_ws/src/tfmini_sensor/tfmini_sensor/tfmini_node.py
hw: /dev/ttyAMA2 @ 115200 | pub: /fmu/in/distance_sensor @ 50Hz
range: 0.3–12.0m | downward-facing | FOV 3.6° | device_id=1987

## optical_flow_node
pkg: optical_flow | src: ros2_ws/src/optical_flow/optical_flow/optical_flow_node.py
hw: /dev/video3 640x480 | algorithm: OpenCV Farneback dense flow
sub: /fmu/in/distance_sensor (altitude) + /fmu/out/sensor_combined (gyro)
pub: /fmu/in/sensor_optical_flow @ 10Hz | NO systemd service — manual launch only

## obstacle_distance_publisher
pkg: obstacle_distance | src: ros2_ws/src/obstacle_distance/obstacle_distance_node.py
hw: VL53L1X ToF (I2C bus 1, addr 0x29, long-distance mode 3)
pub: /fmu/in/obstacle_distance @ 10Hz
coverage: front sector only — indices 0–5 of 72-element array (5° increment, 20–400cm)

## ldlidar_stl_ros2_node
pkg: ldlidar_stl_ros2 | src: ros2_ws/src/ldlidar_stl_ros2/
service: ldlidar.service | node name: LD19
hw: /dev/ttyAMA3 @ 230400 | pub: /scan (LaserScan) ~10Hz | TF: base_link→base_laser (0.18m)
FIXES (both required on this platform):
  1. Add `#include <pthread.h>` to ldlidar_driver/src/logger/log_module.cpp (GCC 14+ build fail)
  2. Hardcode `/dev/ttyAMA3` in launch/ld19.launch.py line 35 — CLI port_name arg silently ignored

## rov_collision_stop
src: ros2_ws/src/rov_collision_stop/src/main.cpp (C++)
function: emergency collision stop for rover mode

## other_pkgs (no active service)
arm_drone, collision_manual_mode, rov_ext, rov_manual,
px4_ros_com, px4-ros2-interface-lib, px4_msgs
