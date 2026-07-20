---
name: project-l4-gemini-nav2-prereqs
description: "L4/L5 dependency audit 2026-07-20: Gemini 336L present on USB3 but NO Orbbec SDK/wrapper/udev; Nav2 + slam_toolbox not installed; 7 build deps missing"
metadata:
  type: project
---

# L4 (Gemini → /scan) + L5 (Nav2) prerequisites — audit 2026-07-20

Read-only audit of what the autonav roadmap still needs installed. Nothing installed yet — all of it
needs sudo.

## Present and good
- **Gemini 336L enumerated on USB3**: `lsusb` ID `2bc5:0807`, sysfs `/sys/bus/usb/devices/2-1`,
  **speed 5000 Mbps** (the BOX-B PCIe→USB3 board is doing its job, see [[project-boxb-pcie-usb]]).
- Device nodes free — nothing holds video0/2/4/6; `vision_streaming` is active but on the LG FPV cam,
  so no contention with the Orbbec (roles per [[project-vision-multicam-upgrade]]).
- `ros-jazzy-depthimage-to-laserscan` **2.5.1** installed.
- `ros-jazzy-image-transport`, `robot-state-publisher`, `tf2-ros`, `libusb-1.0-0-dev`,
  `libeigen3-dev` installed.
- apt reachable (simulated install succeeds).

## Missing — the actual L4/L5 work list
- **OrbbecSDK_ROS2: completely absent** — no source anywhere under `~`, and **no Orbbec udev rules**
  (`/etc/udev/rules.d` has none). Both are needed; without the udev rule the wrapper needs root to
  claim the USB device. Use the v2-main line (Gemini 330-series support incl. 336L, ROS2 Jazzy).
  Clone via SSH — companion HTTPS→GitHub hangs on IPv6:
  `git -c url."git@github.com:".insteadOf="https://github.com/" clone ...`
- **Nav2 not installed** — `ros-jazzy-navigation2` candidate **1.3.5**, plus `ros-jazzy-nav2-bringup`.
- **slam_toolbox not installed** — candidate **2.8.2**.
- Build deps missing: `nlohmann-json3-dev`, `libgflags-dev`, `ros-jazzy-camera-info-manager`,
  `ros-jazzy-diagnostic-updater`, `ros-jazzy-image-publisher`, `ros-jazzy-backward-ros`,
  `ros-jazzy-xacro`.

## Watch item
**Disk is at 82% — 46G used, 11G free of 58G** (MEMORY.md's "~63% used" is stale; growth is from the
px4_msgs/workspace rebuilds and the PX4-Autopilot clone). Nav2 + slam_toolbox + OrbbecSDK build trees
will take a chunk of that. Consider clearing `~/ros2_ws/build`+`log` for unused packages first.

Related: [[project-rover-autonav]], [[project-vision-multicam-upgrade]], [[feedback-camera-qgc-only]].
