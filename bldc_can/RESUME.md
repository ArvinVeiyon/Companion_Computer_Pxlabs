# RESUME — pick this work up after the reboot

Written 2026-09-06 before the reboot that was meant to create `can0`; updated the same night
after the reboot, which did **not**.
Read this first, then [`README.md`](README.md) for the why and [`MOTOR_MAP.md`](MOTOR_MAP.md) for the map.

---

## 🅿️ 2026-09-06 — CAN HAT PARKED BY OPERATOR DECISION. GOING USB INSTEAD.

**Do not resume the MCP2515 debugging below unless the hat is repaired or swapped.** It is a
hardware fault (see the diagnosis), it is not blocking the flash, and USB is the better path anyway:

* ✅ **USB was ALWAYS mandatory for `60_mk5.bin`** — the DroneCAN route bricks it (§5 of `README.md`).
  The dead hat costs us **nothing** on the flash itself.
* ✅ **USB gives a COMPLETE mcconf backup. CAN never could** — the DroneCAN param table exposes only
  8 params, no motor tune. This closes the "no config backup over CAN" gap outright.
* ✅ **USB also settles the wheel↔node map** without the one-ESC-at-a-time CAN scan: `controller_id`
  is readable directly per ESC in VESC Tool. Expect **FR=10 · FL=11 · RR=12 · RL=13**; believe the
  measurement over the table if they disagree.

### ⛔ TRAPS FOR THE USB / VESC TOOL SESSION — read before connecting

1. 🔴🔴 **DO NOT "FIX" `si_motor_poles`.** It is `14` on all four and it is a **LINKED PAIR** with
   `erpm_to_ms = 0.003900`. Changing poles in VESC Tool **silently halves `/odom`** — and odometry
   is a safety input. `erpm_to_ms` is CLOSED and tape-validated; do not re-open the scale.
2. 🔴 **FLASH ONE ESC FIRST, VERIFY, THEN THE REST.** The target branch
   `pxlabs-6.06-rover-brake-rc` is **untested by its own doc** and carries an unfixed blocker:
   `RC3_TRIM == RC3_MIN`, so lifting the stick off the stop instantly commands ~50 % brake.
   Flashing all four at once destroys the rollback in a single shot. Rollback tag
   **`v6.06.0-pxlabs-rover-r1`**.
3. ⚠️ **DO NOT change `can_mode` (it is `1` = UAVCAN on all four).** VESC Tool finding nothing on a
   CAN scan is correct behaviour in that mode, not a fault. Switching it to VESC takes DroneCAN —
   and the rover — down.
4. ✅ **Config should survive the flash:** `dcc35366` → `a75a0db` differ only in `canard_driver.c`
   plus one `.md`; `datatypes.h` / `confgenerator.*` / `conf_general.h` are byte-identical, so the
   stored-struct CRC still passes. And even in a wipe, **CAN ID and baud survive** (`g_backup`).
   You would lose the motor tune, not the bus.
5. ⏭ **Export live configs BEFORE flashing** → `configs_live/live_<WHEEL>_mcconf.xml`. Confirm
   **RL's `foc_motor_r = 0.1988`**, an outlier vs the other three (0.44–0.56) and duplicated in a
   Left-Front file — suspect, and RL is the one on the bench.
6. ⛔ **NEVER restore from `vesc_mcconf_Right_Front.xml`** — its `foc_motor_flux_linkage = 1.46287`
   is ~130× the family, a failed detection.

---

## 🔴 THIRD BOOT, 2026-09-06 18:00 — STILL BLOCKED. `err=110` → `err=19` IS NOT PROGRESS.

Measured on a fresh boot (`/proc/uptime` 192 s). `can0` absent. The dmesg line changed:

```
mcp251x spi0.0: Cannot initialize MCP2515. Wrong wiring?
mcp251x spi0.0: Probe failed, err=19          (was: "didn't enter in conf mode", err=110)
```

⚠️ **Do not read that as the chip waking up.** `err=19` (`-ENODEV`) is raised *later* in the driver
than `err=110` — the reset check passed and the `CANCTRL` power-up-default check failed. Getting past
the reset check only requires one `CANSTAT` read to come back with the config-mode bits set, and
**`0x80` turns up in noise on a floating MISO**. The error code moved because the noise moved.

The decisive test, new this boot — `diag/wrb_probe.py`, write a chosen value and read it back,
7 speeds (100 kHz…10 MHz) × 5 trials × 4 patterns:

```
write/read-back: 0 of 140 passed
```

🔑 **And the read-backs are a one-transaction LAG line.** Each speed row returns, shifted by one
slot, the values the previous row returned (`…07 1E 0B 14 00 00 02 9C…` reappearing a slot later).
That is a floating line holding charge from the preceding transfer — **zero chip contribution**,
the same class of artifact as the old MOSI back-feed, just a different coupling path.

`diag/int_probe.py` on the same boot, bias verified applied: `/INT` gpio25 and MISO gpio9 **both
still FLOATING** (pull-up→1s, pull-down→0s). Nothing is driving either pin.

✅ **CRYSTAL IS 12 MHz — operator-confirmed 09-06, matches `oscillator=12000000`. CLOSED, don't
re-open the 8-vs-12 question.** (Waveshare shipped this board with both across batches.)
⚠️ **But that only settles the NUMBER.** The overlay's `oscillator=` value is used solely for
bit-timing once the interface is up — it can never cause a probe failure. A crystal that is not
physically **oscillating** is a different fault, and it *would* kill SPI outright, because the
MCP2515's SPI state machine is clocked from its own oscillator. Software cannot tell that apart
from a missing VDD. **Still on the suspect list; needs a scope, or a hat swap.**

⛔ **The operator multimeter steps below have NOT been done yet — do them. No further software
measurement will move this.** Three boots have now produced three different failure signatures and
zero write/read-back passes; the signature varies because it is noise, and the noise is the finding.

---

## 🔴 STILL BLOCKED after the 2026-09-06 re-seat — and the signature CHANGED

The operator re-connected the hat ("it was wrongly connected") and rebooted. Re-measured on that
boot (`/proc/uptime` 449 s, probe failed at t=8.6 s of *this* boot, so the log is current):

* `can0` still absent, same `mcp251x spi0.0: … err=110`.
* **Register write/read-back: 0 of 35 passed** — 7 SPI speeds (100 kHz…10 MHz) × 5 trials, writing
  `0x5A/0xA5` to CNF1 and `0x3C/0xC3` to TXB0SIDH and reading back. Nothing we choose comes back.
  ⚠️ A single `CANSTAT=0x80` did appear at 100 kHz in one run. **It was noise, not a pass** — that is
  exactly why the read-back test exists; never accept the pass value from a single read.
* **The MOSI back-feed is GONE**, and nothing replaced it. With SPI *bound and idle* (so there is no
  MOSI activity to couple), bias verified applied:

  ```
  INT  gpio25:  pull-up->1111111111   pull-down->0000000000   FLOATING
  MISO gpio9:   pull-up->1111111111   pull-down->0000000000   FLOATING
  ```

  A powered MCP2515 drives /INT high push-pull with no interrupt pending, so it would beat the
  pull-down. Both pins simply follow the bias ⇒ **nothing is driving either pin.**
* The old CS×MOSI sweep is now **non-reproducible** — "PINNED LOW" on one run, "PINNED HIGH" on the
  next, and the bit-banged bytes are random rather than `tx[i] | tx[i-1]`. That is a high-impedance
  line holding charge from the preceding traffic, not a chip.

**Reading:** before the re-seat the pins demonstrably *reached an unpowered die* (clean ESD back-feed).
Now there is no coupling at all. So either the die is still unpowered **and** the signal pins have
lost contact, or the hat is sitting on the wrong header rows / offset by a position. Either way it is
still hardware, and still the operator's job.

⛔ **NOTHING ON THE CAN SIDE CAN FIX THIS — DON'T KEEP RE-WORKING THE BUS.** Termination and CAN H/L
polarity live **downstream of the transceiver**; the MCP2515 fails on the **SPI** side, before a CAN
frame exists. (Re-checked 09-06 after the operator switched the hat's terminator on and un-swapped
H/L: `/INT`+MISO still float, a forced re-bind still gives `err=110`.) `can0` depends **only** on
VDD + the five wires SO/SI/SCK/CS/INT. ✅ For the record the bus side is now right: **hat 120 Ω ON +
the one powered VESC = 60 Ω** is the correct 2-terminator bench bus; with all four ESCs on, keep
**exactly two** terminators, one at each physical end.
⚠️ **Re-seat with the Pi SHUT DOWN, not live** — a hot re-seat neither re-probes nor can be trusted.

⏭ **Use `diag/int_probe.py` as the first check from now on** — it needs no unbinding, runs in a
second, and answers "is anything on the other end alive?" without the back-feed ambiguity that cost a
day. `spi_probe.py` stays the deep dive.

---

## 🔴 The original 09-06 diagnosis (pre-re-seat) — THE HAT HAD NO POWER.

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

### ⏭ NEXT ACTION (operator, with a multimeter) — UPDATED after the re-seat

1. **Seating/orientation first.** The hat must sit on pin 1 of the 40-pin header, not offset by a
   pin or a row. Since the re-seat the signal pins show **no** coupling at all, which they did before.
2. Meter the hat's **3.3 V** and **5 V** rails against the MCP2515's VDD pin. Header 3.3 V is pins
   1/17, 5 V is pins 2/4. Look for an unmade or bent **power** pin, or a power jumper/switch.
3. **New:** with the hat off the Pi, buzz continuity from the hat's header pads to the MCP2515 pins —
   **21→SO, 19→SI, 23→SCK, 24→CS, 22→INT**. Contact was proven before and is not proven now.
4. If the rail is present at the header but absent at the chip, or a signal pad does not ring
   through, the hat is faulty — swap it.

Re-check afterwards — cheap test first, deep dive second:

```bash
sudo python3 ~/codex-work/bldc_can/diag/int_probe.py   # 1 s; "actively driven HIGH" = powered die
sudo python3 ~/codex-work/bldc_can/diag/spi_probe.py   # restores every binding it touches
```

⚠️ **A pass is NOT a single `CANSTAT=0x80`** — that value turns up in noise. A pass is `/INT` driven
high against a pull-down **and** a register write that reads back the value you wrote, repeatably.
Then, and only then, continue at **Step 1** below.

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
