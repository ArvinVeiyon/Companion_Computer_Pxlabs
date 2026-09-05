# RESUME — pick this work up after the reboot

Written 2026-09-06, immediately before the reboot that creates `can0`.
Read this first, then [`README.md`](README.md) for the why and [`MOTOR_MAP.md`](MOTOR_MAP.md) for the map.

---

## Where things stand

| | |
|---|---|
| Hardware | Waveshare RS485 CAN HAT rev 2.1 (12 MHz MCP2515) on `spi0.0`, INT GPIO25, wired to the VESC CAN splitter |
| Bench state | **Only REAR LEFT is powered.** The other three ESCs are switched off, on purpose, to map node IDs one at a time |
| Overlay | **staged, not yet active** — needs the reboot |
| Tooling | complete, API-verified, **never run against hardware** |
| Firmware to flash | `Testing_Bin/60_mk5.bin` — **USB only, see the hard stop below** |

## The one thing you must not forget

⛔ **`Testing_Bin/60_mk5.bin` (524,280 B) MUST NOT be flashed over DroneCAN.** The app region is
512 KB but the DroneCAN staging area is only 384 KB, and `flash_helper.c:181` has no bounds check, so
the transfer programs 131,070 bytes into sector 11 — the bootloader — which is never erased.
**Result: brick, recoverable only by SWD/ST-Link.** Flash it over **USB**. `flash.py` refuses the
image; do not work around that guard. Full derivation in `README.md` §5.

## Step 1 — verify the reboot actually gave you can0

```bash
ip -details link show can0          # THE check. Must exist.
dmesg | grep -i mcp251x             # if can0 is missing, look here
```

⚠️ **Do not** use `lsmod | grep mcp251x` as the test — the module can load without the device binding.
⚠️ **Boot-clock trap:** this box's journal restamps early boot. Check `/proc/uptime` before reading
any duration off a timestamp.

If `can0` is missing, the usual cause is the INT pin (GPIO25) or SPI wiring, **not** the crystal —
a wrong crystal binds fine and fails on the bus instead.

Rollback if needed: `/boot/firmware/config.txt.bak-canhat-20260905`.

## Step 2 — bring the bus up and prove it is real

```bash
cd ~/codex-work/bldc_can
./bringup.sh                        # can0 @ 1 Mbit, restart-ms 100
candump -td can0 | head -20         # the FC is a live DroneCAN node - you should see traffic
```

**Never read a quiet topic as evidence.** If `candump` is silent, the fault is wiring / termination /
bitrate — do not proceed to the python tools and conclude anything from their silence.

## Step 3 — map rear left (the actual next task)

```bash
./venv/bin/python scan.py                              # expect exactly ONE VESC node
./venv/bin/python backup_params.py --label "rear left"
```

**Expected: node 13.** Record the result in `MOTOR_MAP.md` (Measured column + the log table) and
commit. If a different ID appears, **believe the measurement** and correct the table.

Then repeat per wheel as each ESC is switched on: FR→10, FL→11, RR→12.

## Step 4 — still outstanding

- [ ] Export live configs over USB into `configs_live/`, per wheel (`live_RL_mcconf.xml`, …).
      CAN exposes only 8 params — USB is the only complete backup. RL's `foc_motor_r = 0.1988`
      is an outlier and RL is on the bench now, so it is worth confirming.
- [ ] Correct `Testing_Bin/README.md` upstream — it currently recommends the DroneCAN path.
- [ ] Fix `RC3_TRIM == RC3_MIN` before the RC brake feature means anything.
- [ ] Flash one ESC over USB, verify, then the rest. Rollback tag `v6.06.0-pxlabs-rover-r1`.

---

## What the reboot will change on this box

State captured immediately before rebooting (uptime was 1.2 h, `get_throttled=0x0`):

| Unit | Was | Enabled at boot? | Action after reboot |
|---|---|---|---|
| `vision_streaming` | active | **enabled** | should return by itself — **verify, don't assume** |
| `microxrce-agent` | active | enabled | returns |
| `mavlink.router` | active | enabled | returns |
| `rover-scan` / `-scan-3d` / `-odometry` | active | enabled | return |
| `rover-ekf-bridge` | inactive | disabled | **stays down on purpose** (wheels-up limit cycle). Start only for an AutoNav run, on the floor |
| `tfmini` | inactive | disabled | stays down; must be enabled for the drone |

> `vision_streaming` reads `enabled` here, which **contradicts the older note that it is disabled at
> boot and that a reboot kills the video.** Trust the measurement after the reboot, not the note.

⚠️ **`active` proves nothing — measure rates.** On 09-04 all six units read `active` while depth,
colour and `/scan` were all 0.0 Hz. If `/scan` or the cloud is dead, restart the **camera** first,
then `rover-scan` / `-scan-3d` / `-odometry` — they stay at 0 Hz forever otherwise.

⚠️ **Clock is wrong until NTP steps it.**

⚠️ **RC CH10 drives companion power:** `2014` = reboot, `1514` (middle) = shutdown, `1011` (down) =
safe. At capture time the **TX was off** (all 18 channels `0`, `link_quality: -1`), so nothing will
fire during this reboot — **but when you switch the TX back on, make sure CH10 is down first**, or
the companion will shut down and it will look like a fault.

ℹ️ `/dev/ttyAMA3` (STL-19 lidar) does not exist and will not come back: SPI0 claims GPIO8/9, so
`dtoverlay=uart3-pi5` loses the pins. **This was already true before the CAN HAT** — `dtparam=spi=on`
was set long before. Not caused by this work, and accepted while the hat is fitted.

## Reboot

```bash
printf '1987\n' | sudo -S reboot
```
