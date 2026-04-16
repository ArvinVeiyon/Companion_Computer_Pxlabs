# LDRobot STL-19 LiDAR — ROS2 Installation Guide
> Platform: Raspberry Pi 5, Ubuntu 24.04 LTS, ROS2 Jazzy
> Prepared: 2026-04-17 | Vind-Roz team

---

## Hardware

**Sensor:** LDRobot STL-19 360° LiDAR
- Interface: UART (serial), 230400 baud
- Motor: internal, runs at fixed speed — no PWM control needed
- Wiring: **RX-only** from RPi side (lidar TX → RPi RX)

**UART wiring (RPi5):**
| RPi Pin | GPIO  | Direction | Connect to |
|---------|-------|-----------|------------|
| Pin 21  | GPIO9 (RX) | RPi receives | Lidar TX   |
| GND     | —     | —         | Lidar GND  |
| 5V      | —     | —         | Lidar VCC (check lidar spec, may need separate 5V supply) |

> **Note:** No TX wire needed. Do NOT connect lidar RX to RPi TX — the lidar does not accept commands.

**Enable UART3 in `/boot/firmware/config.txt`:**
```
dtoverlay=uart3-pi5
```
This maps UART3 to GPIO8/9 (Pin 24/21). Reboot after changing.

**Verify device appears:**
```bash
ls /dev/ttyAMA3
```

---

## Software

### 1. ROS2 Prerequisites
Assumes ROS2 Jazzy is installed. If not:
```bash
# Follow official ROS2 Jazzy install for Ubuntu 24.04
# https://docs.ros.org/en/jazzy/Installation.html
```

### 2. Clone the package
```bash
cd ~/ros2_ws/src
git clone https://github.com/ldrobotSensorTeam/ldlidar_stl_ros2.git
```

### 3. Apply build fix (required on GCC 14+ / Ubuntu 24.04)
The upstream package is missing a pthread header that GCC 14 no longer includes implicitly:
```bash
# Add the missing include at the top of the file
sed -i '1s/^/#include <pthread.h>\n/' \
  ~/ros2_ws/src/ldlidar_stl_ros2/ldlidar_driver/src/logger/log_module.cpp
```
Or edit manually — add `#include <pthread.h>` as the first line of `log_module.cpp`.

### 4. Apply port fix (required — upstream default is wrong)
The launch file defaults to `/dev/ttyUSB0`. The CLI `port_name:=` argument is **silently ignored** by the upstream launch file — you must edit the file directly:
```bash
sed -i "s|'/dev/ttyUSB0'|'/dev/ttyAMA3'|" \
  ~/ros2_ws/src/ldlidar_stl_ros2/launch/ld19.launch.py
```
Or edit `launch/ld19.launch.py` line ~35 manually:
```python
# Change this:
{'port_name': '/dev/ttyUSB0'},
# To this (match your actual UART device):
{'port_name': '/dev/ttyAMA3'},
```

### 5. Set UART permissions
```bash
sudo usermod -aG dialout $USER
# Log out and back in, or:
sudo chmod 666 /dev/ttyAMA3
```

### 6. Build
```bash
cd ~/ros2_ws
colcon build --packages-select ldlidar_stl_ros2
source install/setup.bash
```

---

## Running

### Manual test
```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch ldlidar_stl_ros2 ld19.launch.py
```

**Expected output:**
```
[LD19]: <port_name>: /dev/ttyAMA3
[LD19]: ldlidar node start is success
[LD19]: ldlidar communication is normal.
[LD19]: Publish topic message:ldlidar scan data.
```

**Verify topic:**
```bash
ros2 topic list | grep scan          # should show /scan
ros2 topic echo /scan --once         # should show range data
```

### systemd service (auto-start on boot)
Create `/etc/systemd/system/ldlidar.service`:
```ini
[Unit]
Description=LDRobot STL-19 LiDAR ROS2 Node
After=network.target

[Service]
User=<your_user>
ExecStart=/usr/bin/env bash -c 'source /opt/ros/jazzy/setup.bash && source /home/<your_user>/ros2_ws/install/setup.bash && ros2 launch ldlidar_stl_ros2 ld19.launch.py'
Restart=always
RestartSec=5
WorkingDirectory=/home/<your_user>/ros2_ws

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ldlidar.service
sudo systemctl start ldlidar.service
sudo systemctl status ldlidar.service
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `No such file or directory: /dev/ttyUSB0` | Port fix not applied | Edit `ld19.launch.py` line ~35 |
| `No such file or directory: /dev/ttyAMA3` | UART not enabled | Add `dtoverlay=uart3-pi5` to config.txt, reboot |
| `permission denied /dev/ttyAMA3` | User not in dialout group | `sudo usermod -aG dialout $USER` |
| Build fails: `pthread` errors | Missing include | Apply build fix (step 3) |
| `/scan` topic exists but no data | Wiring issue | Check lidar TX → RPi RX connection |
| Node crashes immediately | Wrong baud rate | Confirm 230400 in launch file |

---

## Published Topics
| Topic | Type | Rate | Description |
|-------|------|------|-------------|
| `/scan` | `sensor_msgs/LaserScan` | ~10 Hz | 360° scan, 0.02–25m range |

**TF:** `base_link` → `base_laser` (static, 0.18m height offset — adjust for your mount)

---

## Known Issues (upstream)
1. `port_name` CLI argument is ignored — must hardcode in launch file
2. Missing `#include <pthread.h>` in `log_module.cpp` — breaks build on GCC 14+
3. `static_transform_publisher` uses deprecated argument style (warning only, harmless)
