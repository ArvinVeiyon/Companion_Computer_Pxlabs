#!/usr/bin/env python3
"""Diagnose an MCP2515 that the kernel driver cannot probe.

Written 2026-09-06 after `dtoverlay=mcp2515-can0` failed with

    mcp251x spi0.0: MCP251x didn't enter in conf mode after reset
    mcp251x spi0.0: Probe failed, err=110

It answers, in order:

  1. Does the chip respond to raw SPI register reads at all, at any mode/speed?
     (through the kernel spidev driver, so the RP1 dw_spi controller is in play)
  2. Same question with the SPI controller unbound and the bus bit-banged on the
     GPIOs, so the controller and its driver are out of the picture entirely.
     An independent ruler - if #1 fails and #2 works, the fault is the controller.
  3. Is MISO electrically driven, or is it just following whatever bias we apply?
     Sweeps CS and MOSI so header crosstalk is a controlled variable.

Test 3 is the one that gave the answer. Its signature to look for:

    MOSI=0 -> MISO pinned 0 against a pull-up
    MOSI=1 -> MISO follows the pull, both ways
    CS makes no difference

That asymmetry is not a chip talking and not a resistive short. It is the ESD
diodes of an UNPOWERED die being back-fed from the driven pins - i.e. the
MCP2515 is wired to the header but has no VDD. No overlay setting can fix that.

Requires root. Restores every binding it touches, including on failure.

Usage:  sudo python3 spi_probe.py [--skip-unbind]
"""
import argparse
import ctypes
import fcntl
import os
import struct
import subprocess
import sys
import time

# --- spidev ioctls -----------------------------------------------------------
SPI_IOC_MESSAGE_1 = 0x40206B00
SPI_IOC_WR_MODE   = 0x40016B01
SPI_IOC_WR_BITS   = 0x40016B03
SPI_IOC_WR_SPEED  = 0x40046B04

# --- gpio v2 uAPI ------------------------------------------------------------
GPIO_V2_GET_LINE        = 0xC250B407
GPIO_V2_LINE_GET_VALUES = 0xC010B40E
GPIO_V2_LINE_SET_VALUES = 0xC010B40F
F_INPUT, F_OUTPUT, F_PULL_UP, F_PULL_DOWN = 1 << 2, 1 << 3, 1 << 8, 1 << 9

CHIP     = "/dev/gpiochip4"          # pinctrl-rp1, the 40-pin header
CS, MISO, MOSI, SCLK = 8, 9, 10, 11  # SPI0 on the header
SPI_DEV  = "1f00050000.spi"
SPI_DRV  = "/sys/bus/platform/drivers/dw_spi_mmio"
PINCONF  = "/sys/kernel/debug/pinctrl/1f000d0000.gpio-pinctrl-rp1/pinconf-pins"

# MCP2515 opcodes
RESET, READ, WRITE, READ_STATUS = 0xC0, 0x03, 0x02, 0xA0


def sh(cmd):
    subprocess.run(cmd, shell=True, check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------- test 1 -----
def spidev_xfer(fd, tx, speed):
    tx_b = bytes(tx)
    tx_c = ctypes.create_string_buffer(tx_b, len(tx_b))
    rx_c = ctypes.create_string_buffer(len(tx_b))
    xf = struct.pack("QQIIHBBBBBB", ctypes.addressof(tx_c), ctypes.addressof(rx_c),
                     len(tx_b), speed, 0, 8, 0, 0, 0, 0, 0)
    fcntl.ioctl(fd, SPI_IOC_MESSAGE_1, xf)
    return bytes(rx_c.raw)


def test_kernel_spi():
    print("== 1. raw register reads through the kernel SPI controller ==")
    sh(f"echo spi0.0 > /sys/bus/spi/drivers/mcp251x/unbind")
    sh(f"echo spidev > /sys/bus/spi/devices/spi0.0/driver_override")
    sh(f"echo spi0.0 > /sys/bus/spi/drivers/spidev/bind")
    time.sleep(0.3)
    if not os.path.exists("/dev/spidev0.0"):
        print("   could not bind spidev to spi0.0 - skipping")
        return
    try:
        for mode in (0, 3):
            for speed in (100_000, 1_000_000, 2_000_000):
                with open("/dev/spidev0.0", "rb+", buffering=0) as fd:
                    fcntl.ioctl(fd, SPI_IOC_WR_MODE, struct.pack("B", mode))
                    fcntl.ioctl(fd, SPI_IOC_WR_BITS, struct.pack("B", 8))
                    fcntl.ioctl(fd, SPI_IOC_WR_SPEED, struct.pack("I", speed))
                    spidev_xfer(fd, [RESET], speed)
                    time.sleep(0.02)
                    st = spidev_xfer(fd, [READ, 0x0E, 0x00], speed)   # CANSTAT
                    print(f"   mode={mode} speed={speed:>9}  CANSTAT=0x{st[2]:02X}"
                          f"   (0x80 = alive and in config mode)")
    finally:
        sh("echo spi0.0 > /sys/bus/spi/drivers/spidev/unbind")
        sh("echo > /sys/bus/spi/devices/spi0.0/driver_override")


# ------------------------------------------------------------ gpio helpers ---
def open_line(chip, offsets, flags, consumer=b"spi_probe"):
    off = list(offsets) + [0] * (64 - len(offsets))
    buf = struct.pack("64I", *off) + consumer.ljust(32, b"\0")[:32]
    buf += struct.pack("QI5I", flags, 0, 0, 0, 0, 0, 0) + b"\0" * 240
    buf += struct.pack("II5Ii", len(offsets), 0, 0, 0, 0, 0, 0, 0)
    return struct.unpack("i", fcntl.ioctl(chip, GPIO_V2_GET_LINE, buf)[-4:])[0]


def get_values(fd, mask=1):
    return struct.unpack("QQ", fcntl.ioctl(fd, GPIO_V2_LINE_GET_VALUES,
                                           struct.pack("QQ", 0, mask)))[0]


def set_values(fd, bits, mask):
    fcntl.ioctl(fd, GPIO_V2_LINE_SET_VALUES, struct.pack("QQ", bits, mask))


def bias_applied(offset):
    """Never trust a bias result without checking the bias actually landed."""
    try:
        for line in open(PINCONF):
            if line.startswith(f"pin {offset} ("):
                return (int("pull up (1" in line), int("pull down (1" in line))
    except OSError:
        pass
    return (None, None)


# ---------------------------------------------------------------- test 2 -----
class BitBang:
    B_CS, B_MOSI, B_SCLK, ALL = 1, 2, 4, 7

    def __init__(self, chip):
        self.out = open_line(chip, [CS, MOSI, SCLK], F_OUTPUT)
        self.inp = open_line(chip, [MISO], F_INPUT | F_PULL_UP)
        self.st = self.B_CS
        set_values(self.out, self.st, self.ALL)

    def _w(self, bit, v):
        self.st = (self.st | bit) if v else (self.st & ~bit)
        set_values(self.out, self.st, self.ALL)

    def xfer(self, tx):
        rx = []
        self._w(self.B_CS, 0)
        for b in tx:
            v = 0
            for i in range(7, -1, -1):
                self._w(self.B_MOSI, (b >> i) & 1)
                self._w(self.B_SCLK, 1)
                v = (v << 1) | (get_values(self.inp) & 1)
                self._w(self.B_SCLK, 0)
            rx.append(v)
        self._w(self.B_CS, 1)
        self._w(self.B_MOSI, 0)
        return bytes(rx)

    def close(self):
        self.st = self.B_CS
        set_values(self.out, self.st, self.ALL)
        os.close(self.out)
        os.close(self.inp)


def is_mosi_echo(tx, rx):
    """True if every received bit is (this MOSI bit OR the previous one).

    That is what a pulled-up MISO line does when it is only capacitively /
    ESD-coupled to MOSI: it takes an extra bit time to fall, so it never shows
    a 0 that MOSI did not just hold. It is NOT a chip answering.
    """
    def bits(bs):
        return [(b >> i) & 1 for b in bs for i in range(7, -1, -1)]

    t, r = bits(tx), bits(rx)
    prev = 0
    for tb, rb in zip(t, r):
        if rb != (tb | prev):
            return False
        prev = tb
    return True


def test_bitbang(chip):
    print("\n== 2. bit-banged SPI, controller unbound (independent ruler) ==")
    print("   MISO is biased pull-up, so an undriven bit reads 1 and a driven 0")
    print("   reads 0 - 'all zeros' can no longer be confused with 'nobody home'.")
    bb = BitBang(chip)
    try:
        bb.xfer([RESET])
        time.sleep(0.05)
        for name, reg in (("CANSTAT", 0x0E), ("CANCTRL", 0x0F), ("TXB0CTRL", 0x30)):
            tx = [READ, reg, 0x00]
            r = bb.xfer(tx)
            note = "  <- just MOSI bleeding onto MISO" if is_mosi_echo(tx, r) else ""
            print(f"   READ {name:9s} -> 0x{r[2]:02X}   raw={r.hex()}{note}")
        r = bb.xfer([READ_STATUS, 0x00, 0x00])
        print(f"   READ STATUS         raw={r.hex()}")
    finally:
        bb.close()


# ---------------------------------------------------------------- test 3 -----
def test_miso_drive(chip):
    print("\n== 3. is MISO electrically driven? (CS x MOSI sweep) ==")
    ctl = open_line(chip, [CS, MOSI], F_OUTPUT)   # bit0 = CS, bit1 = MOSI
    verdicts = []
    try:
        for cs in (1, 0):
            for mosi in (0, 1):
                set_values(ctl, cs | (mosi << 1), 3)
                time.sleep(0.05)
                row = []
                for label, flag in (("pu", F_PULL_UP), ("pd", F_PULL_DOWN)):
                    fd = open_line(chip, [MISO], F_INPUT | flag)
                    time.sleep(0.05)
                    s = "".join(str(get_values(fd) & 1) for _ in range(8))
                    ok = bias_applied(MISO)
                    os.close(fd)
                    row.append((label, s, ok))
                bad = [r for r in row if r[2] not in ((1, 0), (0, 1))]
                if bad:
                    v = "BIAS DID NOT APPLY - result untrustworthy"
                elif row[0][1] == "1" * 8 and row[1][1] == "0" * 8:
                    v = "floating"
                elif row[0][1] == "0" * 8 and row[1][1] == "0" * 8:
                    v = "PINNED LOW"
                elif row[0][1] == "1" * 8 and row[1][1] == "1" * 8:
                    v = "PINNED HIGH"
                else:
                    v = "unstable"
                verdicts.append((cs, mosi, v))
                print(f"   CS={cs} MOSI={mosi}:  " +
                      "  ".join(f"{l}->{s}" for l, s, _ in row) + f"   {v}")
    finally:
        set_values(ctl, 1, 3)
        os.close(ctl)

    by_mosi = {(m, v) for _, m, v in verdicts}
    if by_mosi == {(0, "PINNED LOW"), (1, "floating")}:
        print("\n   >>> MISO tracks MOSI one way only and ignores CS entirely.")
        print("   >>> That is ESD-diode back-feed through an UNPOWERED die.")
        print("   >>> The MCP2515 is wired to the header but has no VDD.")
        print("   >>> Check the HAT's 3.3V/5V rails with a meter. Nothing in")
        print("   >>> config.txt can fix this.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-unbind", action="store_true",
                    help="skip tests 2 and 3, which unbind the SPI controller")
    args = ap.parse_args()
    if os.geteuid() != 0:
        sys.exit("needs root")

    test_kernel_spi()
    if args.skip_unbind:
        return

    sh(f"echo {SPI_DEV} > {SPI_DRV}/unbind")
    time.sleep(0.3)
    chip = os.open(CHIP, os.O_RDWR)
    try:
        test_bitbang(chip)
        test_miso_drive(chip)
    finally:
        os.close(chip)
        sh(f"echo {SPI_DEV} > {SPI_DRV}/bind")
        time.sleep(0.5)
        print("\nSPI controller rebound; mcp251x will re-probe (and fail again "
              "until the hardware fault is fixed).")


if __name__ == "__main__":
    main()
