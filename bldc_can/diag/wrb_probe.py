#!/usr/bin/env python3
"""The pass criterion: write a register, read back what we wrote.

A single CANSTAT=0x80 is NOT a pass - that value turns up in noise on a floating
MISO.  A pass is a value WE chose coming back, repeatably, at more than one clock
speed.  Writes go to CNF1 (0x2A) and TXB0SIDH (0x31), both plain R/W registers
that are writable in configuration mode, which is where the chip sits after RESET.

Binds spidev to spi0.0 for the duration and restores mcp251x afterwards.
"""
import ctypes, fcntl, os, struct, subprocess, sys, time

SPI_IOC_WR_MODE  = 0x40016B01
SPI_IOC_WR_BITS  = 0x40016B03
SPI_IOC_WR_SPEED = 0x40046B04
SPI_IOC_MESSAGE_1 = 0x40206B00

RESET, READ, WRITE = 0xC0, 0x03, 0x02
CNF1, TXB0SIDH = 0x2A, 0x31
SPEEDS = (100_000, 250_000, 500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000)
TRIALS = 5
PATTERNS = ((CNF1, 0x5A), (CNF1, 0xA5), (TXB0SIDH, 0x3C), (TXB0SIDH, 0xC3))


def sh(cmd):
    subprocess.run(cmd, shell=True, check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def xfer(fd, tx, speed):
    tx_b = bytes(tx)
    tx_c = ctypes.create_string_buffer(tx_b, len(tx_b))
    rx_c = ctypes.create_string_buffer(len(tx_b))
    msg = struct.pack("QQIIHBBBBBB", ctypes.addressof(tx_c), ctypes.addressof(rx_c),
                      len(tx_b), speed, 0, 8, 0, 0, 0, 0, 0)
    fcntl.ioctl(fd, SPI_IOC_MESSAGE_1, msg)
    return bytes(rx_c.raw)


def main():
    if os.geteuid() != 0:
        sys.exit("run me with sudo")
    sh("echo spi0.0 > /sys/bus/spi/drivers/mcp251x/unbind")
    sh("echo spidev > /sys/bus/spi/devices/spi0.0/driver_override")
    sh("echo spi0.0 > /sys/bus/spi/drivers/spidev/bind")
    time.sleep(0.3)
    if not os.path.exists("/dev/spidev0.0"):
        sys.exit("could not bind spidev to spi0.0")

    passes = total = 0
    try:
        for speed in SPEEDS:
            seen = []
            for _ in range(TRIALS):
                with open("/dev/spidev0.0", "rb+", buffering=0) as fd:
                    fcntl.ioctl(fd, SPI_IOC_WR_MODE, struct.pack("B", 0))
                    fcntl.ioctl(fd, SPI_IOC_WR_BITS, struct.pack("B", 8))
                    fcntl.ioctl(fd, SPI_IOC_WR_SPEED, struct.pack("I", speed))
                    xfer(fd, [RESET], speed)
                    time.sleep(0.02)
                    for reg, val in PATTERNS:
                        xfer(fd, [WRITE, reg, val], speed)
                        rb = xfer(fd, [READ, reg, 0x00], speed)[2]
                        total += 1
                        if rb == val:
                            passes += 1
                        seen.append(f"{val:02X}->{rb:02X}")
            print(f"   {speed:>9} Hz  " + " ".join(seen))
    finally:
        sh("echo spi0.0 > /sys/bus/spi/drivers/spidev/unbind")
        sh("echo > /sys/bus/spi/devices/spi0.0/driver_override")
        sh("echo spi0.0 > /sys/bus/spi/drivers/mcp251x/bind")

    print(f"\nwrite/read-back: {passes} of {total} passed")
    print("0 passes = nothing is answering on MISO.  Hardware, not software.")


if __name__ == "__main__":
    main()
