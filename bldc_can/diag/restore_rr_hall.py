#!/usr/bin/env python3
"""Restore Rear Right's OWN 15-Aug hall table (2026-09-14).

WHY: RR is the only wheel whose mcconf changed since August. Entry 1 went 199 -> 1, a ~280 deg
error on one of the six rotor positions, while entries 2-6 moved only 1-3 counts (normal
re-detection scatter). Measured consequence: RR's reported speed collapses to near zero mid-drive
in 20.2% of moving samples (FR/RL 6.0%, FL 10.2%), and its current spikes to +20 A in the same
sample as the loop corrects an error that is not real.

⛔ This is NOT a cross-write. These six values come from RR's own configs_from_repo baseline
   (vesc_mcconf_Right_Rear__15_Aug_26.xml). Nothing from another wheel is used.
⛔ Only foc_hall_table__1..6 are touched. Every other field is written back byte-identical.

Restoring the full August SET rather than just entry 1: the six values are a self-consistent
detection that the rover actually ran on. Patching one value into the newer five would be a
combination that has never been tested.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import tune_esc as t

AUG = {'foc_hall_table__1': '199', 'foc_hall_table__2': '132', 'foc_hall_table__3': '166',
       'foc_hall_table__4': '66',  'foc_hall_table__5': '32',  'foc_hall_table__6': '99'}
RR_ID = '12'

port = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyACM0'
live = t.LIVE
stamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M')

app_probe = live / f'_rrhall_app_{stamp}.xml'
app_text = t.read_conf(port, 'App', app_probe)
cid = t.get(app_text, 'controller_id')
if cid != RR_ID:
    sys.exit(f'REFUSING: {port} is controller_id {cid}, not RR ({RR_ID}).')
print(f'{port} is controller_id {cid} = RR')

pre = live / f'vesc_mcconf_RR_{stamp}_hallpre.xml'
text = t.read_conf(port, 'Mc', pre)
print(f'  as-found backed up to {pre.name}')

changes = [(k, t.get(text, k), v) for k, v in AUG.items() if t.get(text, k) != v]
if not changes:
    print('  hall table already at the August values, nothing to write')
    raise SystemExit(0)

new_text = text
for k, _, v in changes:
    if t.get(text, k) is None:
        sys.exit(f'{k} missing from mcconf -- aborting.')
    new_text = t.put(new_text, k, v)

post = live / f'vesc_mcconf_RR_{stamp}_hallpost.xml'
post.write_text(new_text)
t.write_conf(port, 'Mc', post)

rb = live / f'vesc_mcconf_RR_{stamp}_hallreadback.xml'
t.read_conf(port, 'Mc', rb)
if rb.read_text() != new_text:
    sys.exit('READBACK MISMATCH -- device does not hold what we sent. Do not drive.')

for k, o, v in changes:
    print(f'  {k}: {o} -> {v}  [verified on device]')
print('\nRR hall table restored to its 15-Aug values.')
