#!/usr/bin/env python3
"""One-off, 2026-10-20: restore FL's appconf IDENTITY after RR's appconf was applied to it.

    python3 diag/restore_fl_identity.py /dev/ttyACM0 [--dry-run]

set_appconf_field.py REFUSES controller_id / uavcan_esc_index on purpose -- those two fields
are what tell PX4 which wheel it is talking to, so they must never move by accident. This
script is the deliberate exception, and it earns it by refusing unless the MCCONF on the board
is unmistakably FL's:

    l_current_max 14   (the other three wheels are 25)
    si_wheel_diameter 0.165 + si_gear_ratio 1   (the 350 W wizard presets, FL only)
    m_invert_direction 1   (RR is 0)
    foc_hall_table__1 0    (RR is 1)

If that fingerprint does not match, the board is not FL and writing ID 11 into it would put two
nodes on address 11. Readback is compared field by field, numerically where both sides parse as
numbers, so an exponent reformat (8370000 -> 8.37e+06) is not reported as a mismatch.
"""
import argparse
import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import tune_esc as t

FL_MC_FINGERPRINT = {'l_current_max': '14', 'si_wheel_diameter': '0.165', 'si_gear_ratio': '1',
                     'm_invert_direction': '1', 'foc_hall_table__1': '0'}
RESTORE = {'controller_id': '11', 'uavcan_esc_index': '1'}

ap = argparse.ArgumentParser()
ap.add_argument('port')
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')

mc_probe = t.LIVE / f'_restore_fl_identity_mc_{stamp}.xml'
mc = t.read_conf(a.port, 'Mc', mc_probe)
bad = {k: t.get(mc, k) for k, v in FL_MC_FINGERPRINT.items() if t.get(mc, k) != v}
if bad:
    sys.exit('REFUSING: mcconf on this board is not FL\'s.\n'
             + '\n'.join(f'  {k}: found {bad[k]}, FL has {FL_MC_FINGERPRINT[k]}' for k in bad))
print('mcconf fingerprint matches FL on all 5 fields')

pre = t.LIVE / f'vesc_appconf_FL_{stamp}_identity_pre.xml'
app = t.read_conf(a.port, 'App', pre)
print(f'  as-found backed up to {pre.name}')
print(f'  on device now: controller_id {t.get(app, "controller_id")}, '
      f'uavcan_esc_index {t.get(app, "uavcan_esc_index")}')

changes = [(k, t.get(app, k), v) for k, v in RESTORE.items() if t.get(app, k) != v]
if not changes:
    print('  already FL identity, nothing to write')
    raise SystemExit(0)
for k, o, v in changes:
    print(f'  {"WOULD set" if a.dry_run else "setting"} {k}: {o} -> {v}')
if a.dry_run:
    raise SystemExit(0)

new_text = app
for k, _, v in changes:
    new_text = t.put(new_text, k, v)
post = t.LIVE / f'vesc_appconf_FL_{stamp}_identity_post.xml'
post.write_text(new_text)
t.write_conf(a.port, 'App', post)

rb_path = t.LIVE / f'vesc_appconf_FL_{stamp}_identity_readback.xml'
rb = t.read_conf(a.port, 'App', rb_path)
for k, _, v in changes:
    got = t.get(rb, k)
    if got != v:
        sys.exit(f'READBACK MISMATCH: {k} reads {got}, sent {v}. Do not power the CAN bus.')
    print(f'  {k} = {got}  [verified on device]')
print('FL identity restored. Verify all four addresses appear exactly once before driving.')
