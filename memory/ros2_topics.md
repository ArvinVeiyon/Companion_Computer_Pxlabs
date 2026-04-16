---
name: ROS2 Topic Lists
description: Full FMU↔companion DDS topic lists for Vind-Roz PX4/ROS2 bridge
type: reference
originSessionId: d30954f2-0ebb-48f6-a7eb-06fd9278994d
---
## FMU → Companion (out)
/fmu/out/input_rc | vehicle_attitude | vehicle_local_position | vehicle_global_position
vehicle_gps_position | vehicle_status | vehicle_control_mode | vehicle_land_detected
vehicle_odometry | sensor_combined | battery_status | home_position
estimator_status_flags | failsafe_flags | collision_constraints | manual_control_setpoint
timesync_status | airspeed_validated | position_setpoint_triplet | event

## Companion → FMU (in)
/fmu/in/distance_sensor | obstacle_distance | sensor_optical_flow
vehicle_command | offboard_control_mode | trajectory_setpoint | manual_control_input
vehicle_attitude_setpoint | vehicle_rates_setpoint | vehicle_thrust_setpoint
vehicle_torque_setpoint | actuator_motors | actuator_servos | onboard_computer_status
goto_setpoint | rover_attitude/position/rate/steering/throttle_setpoint
arming_check_reply | register_ext_component_request | vehicle_visual_odometry
vehicle_mocap_odometry | telemetry_status | /parameter_events | /rosout
