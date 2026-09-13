---
name: vesc-tool-cli
description: "VESC Tool 7.01 is BUILT ON THE COMPANION and runs headless — full ESC config read/write over USB from the Pi, no laptop, no X server"
metadata: 
  node_type: memory
  type: reference
  originSessionId: b8919666-0419-4c4f-88ea-cd8bff5f8e34
  modified: 2026-09-13T08:13:37.191Z
---

**As of 2026-09-13 the companion can read and write any ESC setting itself, over USB, with no GUI
and no laptop.** This replaces "the operator must do it in VESC Tool on another machine".

## The binary

`/home/roz/vesc_tool_build/build/lin/vesc_tool_7.01` — VESC Tool **7.01**, built from
`ArvinVeiyon/vesc_tool` (master, `dc53c658`). Source tree at `~/vesc_tool_build`.

🔑 **`--offscreen` is the whole trick** — "Use offscreen QPA so that X is not required for the
CLI-mode". **This box has NO X server installed at all**, and it does not need one.

```
vesc_tool_7.01 --offscreen --vescPort /dev/ttyACM0 --getMcConf  out.xml
vesc_tool_7.01 --offscreen --vescPort /dev/ttyACM0 --setMcConf  in.xml
vesc_tool_7.01 --offscreen --vescPort /dev/ttyACM0 --getAppConf out.xml
vesc_tool_7.01 --offscreen --vescPort /dev/ttyACM0 --setAppConf in.xml
vesc_tool_7.01 --offscreen --vescPort /dev/ttyACM0 --queryDeviceFwParams   # fw + UUID
vesc_tool_7.01 --offscreen --version
```
Also available: `--tcpServer [port]` (hold the USB link here, connect a GUI VESC Tool over the
network), `--canFwd`, `--uploadFirmware`, `--uploadLisp`, `--bridgeAppData`.

⚠️ Writes print a **"configuration is from a different firmware and/or VESC Tool version"**
warning even on a config just read off that same device — our build self-reports as a test
version (`VT_IS_TEST_VERSION=1`). **Cosmetic**: readbacks were byte-identical every time.
⚠️ "Could not load package archive resource" on every invocation — harmless.

## Rebuilding it

```
qmake -config release "CONFIG += release_lin build_original" && make -j3
```
🔴 **The one blocker: `qtbase5-private-dev`** — without it the build dies on
`QtGui/qpa/qplatformwindow.h: No such file or directory`. Other deps (all apt, Qt 5.15.13):
`qtbase5-dev qtdeclarative5-dev qtquickcontrols2-5-dev libqt5serialport5-dev qtconnectivity5-dev
qtpositioning5-dev libqt5gamepad5-dev libqt5svg5-dev qttools5-dev libqt5opengl5-dev`.
~20 min at `-j3` on this Pi. ⚠️ `make` exiting 0 in a wrapper is NOT proof — **check the binary
exists**; the first attempt "succeeded" while the build had failed.

## Connecting

🔑 **A VESC's USB only enumerates when the board is POWERED** — no `/dev/ttyACM0` means check
power before suspecting the cable. Appears as `0483:5740`. `roz` is in `dialout`, so no sudo.
⛔ **One ESC per session — there is no multi-drop.** CAN forwarding is gated on
`can_mode == CAN_MODE_VESC` and ours is UAVCAN. Move the cable, one wheel at a time.
✅ Leaving USB connected while driving is harmless (both ends ride on the rover) — USB and the
DroneCAN control path are independent. Keep the cable clear of the wheels.

## ⛔ Use the wrapper, not raw setMcConf

**`~/codex-work/bldc_can/tune_esc.py`** — reads the connected ESC's OWN config, edits only the
target values, writes, reads back, and **aborts on any mismatch**. It identifies the wheel from
`controller_id` and backs up the as-found config first.

🔴 **NEVER write one wheel's mcconf to another wheel.** It carries per-motor detection results
(`foc_hall_table`, `foc_motor_r`, `foc_motor_flux_linkage`, `foc_offsets_*`) and
`m_invert_direction`, which is **mirrored: left wheels 1, right wheels 0**. Cross-writing
reverses a wheel or gives it a failed detection.

See also [[vesc-can-flashing]], [[rover-odometry]], [[this-machine]].
