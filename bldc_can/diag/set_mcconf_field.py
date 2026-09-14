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
ap.add_argument('pairs', nargs='+', metavar='FIELD VALUE',
                help='one or more FIELD VALUE pairs, written as ONE transaction so a '
                     'related pair (e.g. regen_cut_start/_end) is never half-applied')
ap.add_argument('--expect-id', required=True, help='controller_id this port must report')
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()
if len(a.pairs) % 2:
    sys.exit('pairs must come as FIELD VALUE')
TARGETS = dict(zip(a.pairs[::2], a.pairs[1::2]))

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
probe = t.LIVE / f'_setfield_app_{stamp}.xml'
cid = t.get(t.read_conf(a.port, 'App', probe), 'controller_id')
if cid != a.expect_id:
    sys.exit(f'REFUSING: {a.port} reports controller_id {cid}, expected {a.expect_id}')
wheel = t.WHEEL.get(int(cid), f'UNKNOWN_{cid}')
print(f'{a.port} = controller_id {cid} ({wheel})')

tag = '_'.join(sorted(TARGETS))[:60]
pre = t.LIVE / f'vesc_mcconf_{wheel}_{stamp}_{tag}_pre.xml'
text = t.read_conf(a.port, 'Mc', pre)
print(f'  as-found backed up to {pre.name}')
for k in TARGETS:
    if t.get(text, k) is None:
        sys.exit(f'{k} not present in mcconf -- wrong name or wrong firmware.')
changes = [(k, t.get(text, k), v) for k, v in TARGETS.items() if t.get(text, k) != v]
if not changes:
    print('  already at target, nothing to write')
    raise SystemExit(0)
if a.dry_run:
    for k, o, v in changes:
        print(f'  WOULD change {k} {o} -> {v}')
    raise SystemExit(0)

new_text = text
for k, _, v in changes:
    new_text = t.put(new_text, k, v)
post = t.LIVE / f'vesc_mcconf_{wheel}_{stamp}_{tag}_post.xml'
post.write_text(new_text)
t.write_conf(a.port, 'Mc', post)

rb = t.LIVE / f'vesc_mcconf_{wheel}_{stamp}_{tag}_readback.xml'
t.read_conf(a.port, 'Mc', rb)
if rb.read_text() != new_text:
    sys.exit('READBACK MISMATCH -- device does not hold what we sent. Do not drive.')
for k, o, v in changes:
    print(f'  {k}: {o} -> {v}  [verified on device]')
