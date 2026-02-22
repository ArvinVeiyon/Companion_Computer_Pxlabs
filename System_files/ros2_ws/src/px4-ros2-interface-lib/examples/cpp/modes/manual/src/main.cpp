// File: main.cpp
/****************************************************************************
 * Copyright (c) 2023 PX4 Development Team.
 * SPDX-License-Identifier: BSD-3-Clause
 ****************************************************************************/

#include <rclcpp/rclcpp.hpp>
#include <mode.hpp>
#include <px4_ros2/components/node_with_mode.hpp>

using MyNodeWithMode = px4_ros2::NodeWithMode<FlightModeTest>;

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<MyNodeWithMode>("example_mode_manual", true);
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
