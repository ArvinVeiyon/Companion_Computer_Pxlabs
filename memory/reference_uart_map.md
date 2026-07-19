---
name: uart-map
description: Full ttyAMA UART pin/baud mapping for Vind-Roz companion
metadata: 
  node_type: memory
  type: reference
  originSessionId: 15cc4d60-122c-4a4b-9f9b-8e1a15ef71a0
---

| ttyAMA | Use                              | Baud   | GPIO TX/RX |
|--------|----------------------------------|--------|------------|
| AMA0   | FC MAVLink → mavlink-router      | 921600 | GPIO14/15  |
| AMA2   | TFmini lidar                     | 115200 | GPIO4/5    |
| AMA3   | STL-19 LiDAR (RX-only, no PWM)   | 230400 | GPIO8/9    |
| AMA4   | FC uXRCE-DDS → MicroXRCEAgent    | 921600 | GPIO12/13  |
| AMA1   | FREE (needs dtoverlay=uart1-pi5) | —      | GPIO0/1    |
| AMA10  | Internal SoC / JST debug (BT)    | 115200 | —          |

Enabled in /boot/firmware/config.txt: uart0, uart2, uart3-pi5, uart4
