#!/usr/bin/env python3
"""The pass criterion: write TWO registers, read BOTH back, in one trial.

A single CANSTAT=0x80 is NOT a pass - that value turns up in noise on a floating
MISO.  But "a value we chose came back" is NOT enough either, and that is a trap
that bit this script on its first version: the dead line holds charge from the
PREVIOUS transfer, so if it happens to be holding 0xC3 when we ask for the 0xC3
we just wrote, a single-register test scores a false pass.  That is exactly how
v1 scored 10/280 on hardware that is provably dead.

So the criterion is a PAIR: write A to CNF1 and B to TXB0SIDH with A != B, then
read both.  A held or bleeding line can only ever hold ONE value, so it cannot
return two different chosen values at two chosen addresses in the same trial.

CNF1 (0x2A) is writable only in configuration mode, which is where RESET leaves
us; TXB0SIDH (0x31) is writable in any mode once TXREQ is clear, which it is
after RESET.  Keeping both means a chip that is alive but not in config mode
still registers.

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
MODES = (0, 3)          # the MCP2515 supports SPI (0,0) and (1,1) ONLY - datasheet 12.0
TRIALS = 5
# Each PAIR writes two DIFFERENT values to two different registers, then reads both.
# Both must match for the pair to count - see the module docstring.
PAIRS = (((CNF1, 0x5A), (TXB0SIDH, 0xC3)),
         ((CNF1, 0xA5), (TXB0SIDH, 0x3C)))


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
        for mode in MODES:
            for speed in SPEEDS:
                seen = []
                for _ in range(TRIALS):
                    with open("/dev/spidev0.0", "rb+", buffering=0) as fd:
                        fcntl.ioctl(fd, SPI_IOC_WR_MODE, struct.pack("B", mode))
                        fcntl.ioctl(fd, SPI_IOC_WR_BITS, struct.pack("B", 8))
                        fcntl.ioctl(fd, SPI_IOC_WR_SPEED, struct.pack("I", speed))
                        xfer(fd, [RESET], speed)
                        time.sleep(0.02)
                        for pair in PAIRS:
                            for reg, val in pair:              # write both first,
                                xfer(fd, [WRITE, reg, val], speed)
                            got = []
                            for reg, _ in pair:                # then read both back
                                got.append(xfer(fd, [READ, reg, 0x00], speed)[2])
                            ok = all(g == v for g, (_, v) in zip(got, pair))
                            total += 1
                            passes += ok
                            seen.append("".join(f"{v:02X}" for _, v in pair) + "->"
                                        + "".join(f"{g:02X}" for g in got)
                                        + ("*" if ok else ""))
                print(f"   mode={mode} {speed:>9} Hz  " + " ".join(seen))
    finally:
        sh("echo spi0.0 > /sys/bus/spi/drivers/spidev/unbind")
        sh("echo > /sys/bus/spi/devices/spi0.0/driver_override")
        sh("echo spi0.0 > /sys/bus/spi/drivers/mcp251x/bind")

    print(f"\npaired write/read-back: {passes} of {total} passed")
    print("0 = nothing is answering on MISO.  Hardware, not software.")
    print("Anything >0 here is real - a held line cannot return two chosen")
    print("values at two chosen addresses in one trial.  Re-run to confirm.")


if __name__ == "__main__":
    main()
