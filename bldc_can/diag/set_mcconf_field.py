#!/usr/bin/env python3
"""Set ONE mcconf field on ONE ESC, identified by controller_id, with readback verification.

    python3 set_mcconf_field.py /dev/ttyACM0 --expect-id 13 foc_hall_interp_erpm 100

⛔ Reads the target ESC's OWN config, edits exactly one field, writes everything else back
   byte-identical. Never copies between wheels. Refuses if controller_id does not match
   --expect-id, so a reshuffled ttyACM number cannot hit the wrong motor.
"""
import argparse
import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import tune_esc as t

ap = argparse.ArgumentParser()
ap.add_argument('port')
ap.add_argument('field')
ap.add_argument('value')
ap.add_argument('--expect-id', required=True, help='controller_id this port must report')
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
probe = t.LIVE / f'_setfield_app_{stamp}.xml'
cid = t.get(t.read_conf(a.port, 'App', probe), 'controller_id')
if cid != a.expect_id:
    sys.exit(f'REFUSING: {a.port} reports controller_id {cid}, expected {a.expect_id}')
wheel = t.WHEEL.get(int(cid), f'UNKNOWN_{cid}')
print(f'{a.port} = controller_id {cid} ({wheel})')

pre = t.LIVE / f'vesc_mcconf_{wheel}_{stamp}_{a.field}_pre.xml'
text = t.read_conf(a.port, 'Mc', pre)
old = t.get(text, a.field)
if old is None:
    sys.exit(f'{a.field} not present in mcconf -- wrong name or wrong firmware.')
print(f'  as-found backed up to {pre.name}')
if old == a.value:
    print(f'  {a.field} already {a.value}, nothing to write')
    raise SystemExit(0)
if a.dry_run:
    print(f'  WOULD change {a.field} {old} -> {a.value}')
    raise SystemExit(0)

new_text = t.put(text, a.field, a.value)
post = t.LIVE / f'vesc_mcconf_{wheel}_{stamp}_{a.field}_post.xml'
post.write_text(new_text)
t.write_conf(a.port, 'Mc', post)

rb = t.LIVE / f'vesc_mcconf_{wheel}_{stamp}_{a.field}_readback.xml'
t.read_conf(a.port, 'Mc', rb)
if rb.read_text() != new_text:
    sys.exit('READBACK MISMATCH -- device does not hold what we sent. Do not drive.')
print(f'  {a.field}: {old} -> {a.value}  [verified on device]')
