#!/usr/bin/env python3
"""Set one or more appconf fields on ONE ESC, identified by controller_id, with readback verification.

    python3 set_appconf_field.py /dev/ttyACM0 --expect-id 11 timeout_brake_current 2

⛔ Reads the target ESC's OWN appconf, edits exactly the named fields, writes everything else back
   byte-identical. Refuses if controller_id does not match --expect-id, so a reshuffled ttyACM
   number cannot hit the wrong motor. Companion to set_mcconf_field.py.
"""
import argparse
import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import tune_esc as t

ap = argparse.ArgumentParser()
ap.add_argument('port')
ap.add_argument('pairs', nargs='+', metavar='FIELD VALUE',
                help='one or more FIELD VALUE pairs, written as ONE transaction')
ap.add_argument('--expect-id', required=True, help='controller_id this port must report')
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()
if len(a.pairs) % 2:
    sys.exit('pairs must come as FIELD VALUE')
TARGETS = dict(zip(a.pairs[::2], a.pairs[1::2]))

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
tag = '_'.join(sorted(TARGETS))[:60]
probe = t.LIVE / f'_setappfield_probe_{stamp}.xml'
cid = t.get(t.read_conf(a.port, 'App', probe), 'controller_id')
if cid != a.expect_id:
    sys.exit(f'REFUSING: {a.port} reports controller_id {cid}, expected {a.expect_id}')
wheel = t.WHEEL.get(int(cid), f'UNKNOWN_{cid}')
print(f'{a.port} = controller_id {cid} ({wheel})')

if 'controller_id' in TARGETS or 'uavcan_esc_index' in TARGETS:
    sys.exit('REFUSING: controller_id / uavcan_esc_index identify the wheel. Change those by hand.')

pre = t.LIVE / f'vesc_appconf_{wheel}_{stamp}_{tag}_pre.xml'
changes = t.apply(a.port, 'App', pre, TARGETS, a.dry_run)
if changes and not a.dry_run:
    print(f'  as-found backed up to {pre.name}')
