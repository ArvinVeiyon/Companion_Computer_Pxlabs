# RESUME — pick this work up after the reboot

Written 2026-09-06 before the reboot that was meant to create `can0`; updated the same night
after the reboot, which did **not**.
Read this first, then [`README.md`](README.md) for the why and [`MOTOR_MAP.md`](MOTOR_MAP.md) for the map.

---

## 🔴 BLOCKED 2026-09-06 — THE HAT HAS NO POWER. THIS IS AN OPERATOR JOB.

The reboot applied the overlay correctly and **`can0` still does not exist**:

```
mcp251x spi0.0: MCP251x didn't enter in conf mode after reset
mcp251x spi0.0: Probe failed, err=110
```

Diagnosed to the pin. **Nothing in `config.txt` can fix it — do not tune the overlay again.**

| Checked | Result |
|---|---|
| Overlay applied | ✅ live DT: `spi-max-frequency`, `can0_osc` 12 MHz, INT `<25 8>` |
| Pin mux | ✅ gpio8/9/10/11 all `function spi0` |
| SPI clock rate | ❌ **not the cause** — 1 MHz behaves *identically* to 10 MHz |
| Raw register read via kernel spidev | ❌ silent at modes 0 & 3, 100 kHz–2 MHz |
| Raw register read **bit-banged**, dw_spi unbound | ❌ silent — the RP1 controller is exonerated |
| Chip select CE1 as well as CE0 | ❌ silent |
| Is MISO driven? | ❌ **no** |

**The finding.** With MISO biased and the bias verified in debugfs:

```
CS=1 MOSI=0:  pull-up->00000000  pull-down->00000000   PINNED LOW
CS=1 MOSI=1:  pull-up->11111111  pull-down->00000000   floating
CS=0 MOSI=0:  pull-up->00000000  pull-down->00000000   PINNED LOW
CS=0 MOSI=1:  pull-up->11111111  pull-down->00000000   floating
```

MISO tracks MOSI **one way only** and **ignores CS entirely**. That is not a chip talking, and it
is not a resistive short (a short would drag MISO high against the pull-down too). It is the ESD
diodes of an **unpowered die** being back-fed from the driven pins. Every byte the bit-bang read
back fits `rx_bit[i] = tx_bit[i] OR tx_bit[i-1]` exactly — pure MOSI bleed, zero chip contribution.

⚠️ **`gpioget` on GPIO25 reads `1`, which looks like a healthy idle INT. It is the same back-feed.
Do not read it as "the hat is powered".** A bias sweep with no settling delay also lies — it
returned "MOSI is driven high" on a floating pin. Always `sleep` and always confirm from
`/sys/kernel/debug/pinctrl/.../pinconf-pins` that the pull you asked for was applied.

### ⏭ NEXT ACTION (operator, with a multimeter)

1. Meter the hat's **3.3 V** and **5 V** rails against the MCP2515's VDD pin. Header 3.3 V is pins
   1/17, 5 V is pins 2/4.
2. Check the hat is fully seated — signal pins clearly make contact, so look specifically for an
   unmade or bent **power** pin, or a power jumper/switch on the board.
3. If the rail is present at the header but absent at the chip, the hat is faulty — swap it.

Re-run the whole diagnosis afterwards, it is one command and it restores every binding it touches:

```bash
sudo python3 ~/codex-work/bldc_can/diag/spi_probe.py
```

A pass looks like `CANSTAT=0x80` in test 1. Then, and only then, continue at **Step 1** below.

---

## Where things stand

| | |
|---|---|
| Hardware | Waveshare RS485 CAN HAT rev 2.1 (12 MHz MCP2515) on `spi0.0`, INT GPIO25, wired to the VESC CAN splitter |
| Bench state | **Only REAR LEFT is powered.** The other three ESCs are switched off, on purpose, to map node IDs one at a time |
| Overlay | ✅ applied and correct as of the 09-06 reboot — but the chip is dead on the bus, see above |
| Tooling | complete, API-verified, **never run against hardware** |
| Firmware to flash | `Testing_Bin/60_mk5.bin` — **USB only, see the hard stop below** |

## The one thing you must not forget

⛔ **`Testing_Bin/60_mk5.bin` (524,280 B) MUST NOT be flashed over DroneCAN.** The app region is
512 KB but the DroneCAN staging area is only 384 KB, and `flash_helper.c:181` has no bounds check, so
the transfer programs 131,070 bytes into sector 11 — the bootloader — which is never erased.
**Result: brick, recoverable only by SWD/ST-Link.** Flash it over **USB**. `flash.py` refuses the
image; do not work around that guard. Full derivation in `README.md` §5.

## Step 1 — verify the reboot actually gave you can0

> ⚠️ 2026-09-06: this step **failed**, and the cause is the power fault at the top of this file.
> Everything from here on is still the right plan; it just cannot start yet.

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

✅ **Measured after the reboot (2026-09-06): every unit came back exactly as predicted above —
`vision_streaming` returned by itself.** The old "`vision_streaming` is disabled at boot / a reboot
kills the video" note is **withdrawn**. (`active` is still not a rate — nobody has measured the
stream itself.)

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
