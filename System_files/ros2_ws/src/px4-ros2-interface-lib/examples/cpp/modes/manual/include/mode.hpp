#pragma once

#include <px4_ros2/components/mode.hpp>
#include <px4_msgs/msg/manual_control_setpoint.hpp>
#include <px4_ros2/control/setpoint_types/experimental/rates.hpp>
#include <px4_ros2/control/setpoint_types/experimental/attitude.hpp>
#include <px4_ros2/control/peripheral_actuators.hpp>
#include <Eigen/Eigen>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/qos.hpp>

static constexpr float kPi = static_cast<float>(M_PI);
static const std::string kName = "My Manual Mode";

class FlightModeTest : public px4_ros2::ModeBase {
public:
  explicit FlightModeTest(rclcpp::Node &node)
    : ModeBase(node, kName)
  {
    // Publish ManualControlSetpoint into the FMU input topic
    _pub = node.create_publisher<px4_msgs::msg::ManualControlSetpoint>(
      "/fmu/in/manual_control_input", rclcpp::SensorDataQoS());

    // Subscribe to PX4's outgoing stick setpoints
    _sub = node.create_subscription<px4_msgs::msg::ManualControlSetpoint>(
      "/fmu/out/manual_control_setpoint", rclcpp::SensorDataQoS(),
      [this](const px4_msgs::msg::ManualControlSetpoint::SharedPtr msg) {
        // replay into PX4 input
        _pub->publish(*msg);
        // cache for setpoint logic
        _latest = *msg;
      });

    // Create setpoint interfaces
    _rates  = std::make_shared<px4_ros2::RatesSetpointType>(*this);
    _att    = std::make_shared<px4_ros2::AttitudeSetpointType>(*this);
    _periph = std::make_shared<px4_ros2::PeripheralActuatorControls>(*this);

    // allow running with translation node if needed
    setSkipMessageCompatibilityCheck();
  }

  void onActivate() override {
    RCLCPP_INFO(node().get_logger(), "%s activated", kName.c_str());
  }

  void onDeactivate() override {
    RCLCPP_INFO(node().get_logger(), "%s deactivated", kName.c_str());
  }

  void updateSetpoint(float dt) override {
    // grab cached sticks
    float roll     = _latest.roll;
    float pitch    = _latest.pitch;
    float yaw      = _latest.yaw;
    float throttle = _latest.throttle;
    float aux1     = _latest.aux1;

    bool rates_mode = fabsf(roll) > 0.1f || fabsf(pitch) > 0.1f;
    float yaw_rate  = yaw * (kPi / 180.0f) * 120.0f;
    Eigen::Vector3f thrust{0.0f, 0.0f, -throttle};

    if (rates_mode) {
      Eigen::Vector3f rates_vec{
        roll   * 500.0f * (kPi / 180.0f),
       -pitch  * 500.0f * (kPi / 180.0f),
        yaw_rate
      };
      _rates->update(rates_vec, thrust);

    } else {
      static float yaw_accum = 0.0f;
      yaw_accum += yaw_rate * dt;
      Eigen::AngleAxisf aa(yaw_accum, Eigen::Vector3f::UnitZ());
      Eigen::Quaternionf qd(aa);
      _att->update(qd, thrust, yaw_rate);
    }

    // forward auxiliary channel
    _periph->set(aux1);
  }

private:
  rclcpp::Publisher<px4_msgs::msg::ManualControlSetpoint>::SharedPtr   _pub;
  rclcpp::Subscription<px4_msgs::msg::ManualControlSetpoint>::SharedPtr _sub;
  px4_msgs::msg::ManualControlSetpoint _latest{};
  std::shared_ptr<px4_ros2::RatesSetpointType>        _rates;
  std::shared_ptr<px4_ros2::AttitudeSetpointType>     _att;
  std::shared_ptr<px4_ros2::PeripheralActuatorControls> _periph;
};
