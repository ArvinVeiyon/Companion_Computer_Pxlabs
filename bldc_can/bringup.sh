#!/usr/bin/env bash
# Bring up can0 for the Waveshare RS485 CAN HAT (rev 2.1, 12 MHz MCP2515 on spi0.0, INT=GPIO25).
#
# Bitrate is NOT a free choice: PX4 UAVCAN_BITRATE=1000000 and the VESC app configs carry
# can_baud_rate=3 (= CAN_BAUD_1M, datatypes.h:252). Both ends are 1 Mbit, so we are 1 Mbit.
#
# Requires the overlay added to /boot/firmware/config.txt on 2026-09-05 and a reboot.
set -euo pipefail

BITRATE=1000000

if ! ip link show can0 >/dev/null 2>&1; then
    echo "FAIL: can0 does not exist." >&2
    echo "  The mcp2515-can0 overlay is in /boot/firmware/config.txt but needs a reboot." >&2
    echo "  If you have already rebooted, the device did not bind - check:" >&2
    echo "    dmesg | grep -i mcp251x" >&2
    echo "  A silent bind failure here is almost always the INT pin (GPIO25) or SPI wiring," >&2
    echo "  not the crystal. A wrong crystal binds fine and then fails on the bus instead." >&2
    exit 1
fi

sudo ip link set can0 down 2>/dev/null || true
# restart-ms 100 auto-recovers from bus-off instead of staying dead silently.
sudo ip link set can0 up type can bitrate "$BITRATE" restart-ms 100

echo "=== can0 up at ${BITRATE} bps ==="
ip -details -statistics link show can0
