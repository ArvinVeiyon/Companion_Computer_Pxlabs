#!/usr/bin/env python3
"""READ-ONLY. Compare whichever ESC is on USB against ours.json and report only what deviates.

    python3 diag/check_ours.py /dev/ttyACM0            # default port
    python3 diag/check_ours.py /dev/ttyACM0 --expect FL # refuse if it is not that wheel

Writes nothing to the ESC, ever. It identifies the board by controller_id, archives the pair it
read into configs_live/, and prints four sections:

  FUNCTIONAL   fields that change how the wheel drives and are off our value -> fix these
  COSMETIC     VESC-Tool-display-only fields off our value -> tidy whenever
  CURRENT LOOP foc_current_kp/ki against this board's own measured L and R at our bandwidth
  WIZARD       detection output, for the record. Never judged, never restored from a file.
"""
import argparse
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import tune_esc as t

HERE = pathlib.Path(__file__).resolve().parent.parent
OURS = json.loads((HERE / 'ours.json').read_text())

ap = argparse.ArgumentParser()
ap.add_argument('port', nargs='?', default='/dev/ttyACM0')
ap.add_argument('--expect', help='wheel name this board must report (FR/FL/RR/RL)')
a = ap.parse_args()

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
app = t.read_conf(a.port, 'App', t.LIVE / f'_check_ours_app_{stamp}.xml')
cid = t.get(app, 'controller_id')
if cid not in OURS['per_wheel']:
    sys.exit(f'controller_id {cid} is not one of 10/11/12/13 -- identity is wrong, stop here.')
spec = OURS['per_wheel'][cid]
wheel = spec['wheel']
if a.expect and a.expect.upper() != wheel:
    sys.exit(f'REFUSING: board reports {wheel} (controller_id {cid}), you expected {a.expect.upper()}')

mc_path = t.LIVE / f'vesc_mcconf_{wheel}_{stamp}_check_READONLY.xml'
app_path = t.LIVE / f'vesc_appconf_{wheel}_{stamp}_check_READONLY.xml'
mc = t.read_conf(a.port, 'Mc', mc_path)
app_path.write_text(app)
print(f'{a.port} = controller_id {cid} -> {wheel}, {spec["motor"]} motor')
print(f'  archived {mc_path.name} and {app_path.name}')

func, cosm = [], []
for k, v in {**OURS['shared_mc'], **OURS['shared_mc_other'],
             **{k: v for k, v in spec.items() if k.startswith(('l_', 'm_'))}}.items():
    got = t.get(mc, k)
    if got != v:
        func.append((k, got, v, 'mcconf'))
for k, v in {**OURS['shared_app'], **OURS['shared_app_other']}.items():
    got = t.get(app, k)
    if got != v:
        func.append((k, got, v, 'appconf'))
for k in ('uavcan_esc_index',):
    got = t.get(app, k)
    if got != spec[k]:
        func.append((k, got, spec[k], 'appconf'))
for k, v in OURS['cosmetic_mc'].items():
    got = t.get(mc, k)
    if got != v:
        cosm.append((k, got, v, 'mcconf'))

print(f'\nFUNCTIONAL deviations: {len(func)}')
for k, got, want, which in func:
    print(f'  {which}  {k:28s} is {str(got):>12s}   ours {str(want):>12s}')
print(f'COSMETIC deviations: {len(cosm)}')
for k, got, want, which in cosm:
    print(f'  {which}  {k:28s} is {str(got):>12s}   ours {str(want):>12s}')

bw = OURS['bandwidth']
L, R = float(t.get(mc, 'foc_motor_l')), float(t.get(mc, 'foc_motor_r'))
kp, ki = t.get(mc, 'foc_current_kp'), t.get(mc, 'foc_current_ki')
print(f'\nCURRENT LOOP at our bandwidth {bw} rad/s, from this board\'s own L and R:')
print(f'  foc_current_kp  is {kp:>10s}   should be {L * bw:.4f}')
print(f'  foc_current_ki  is {ki:>10s}   should be {R * bw:.2f}')
print(f'  bandwidth actually on the board: kp/L = {float(kp) / L:.0f}, ki/R = {float(ki) / R:.0f}')

lam = float(t.get(mc, 'foc_motor_flux_linkage'))
print('\nWIZARD output (for the record, never restored from a file):')
print(f'  R {R}  L {L}  ld_lq_diff {t.get(mc, "foc_motor_ld_lq_diff")}')
print(f'  flux_linkage {lam}  observer_gain {t.get(mc, "foc_observer_gain")}'
      f'   (1000/lambda^2 = {1000 / lam ** 2:.0f})')
print('  hall  ' + ' '.join(f'{t.get(mc, f"foc_hall_table__{i}"):>4s}' for i in range(8)))
if lam in (0.1, 0.0) or abs(lam - 0.1) < 1e-9:
    print('  🔴 flux_linkage is the 0.1 DEFAULT -- the lambda step did not measure. Re-run it with'
          ' the CAN lead off and the wheel free.')
import re
ROOTS = {'MCConfiguration', 'APPConfiguration'}
mc_fields = set(re.findall(r'<([A-Za-z0-9_]+)>', mc)) - ROOTS
app_fields = set(re.findall(r'<([A-Za-z0-9_]+)>', app)) - ROOTS
mc_known = (set(OURS['shared_mc']) | set(OURS['shared_mc_other']) | set(OURS['cosmetic_mc'])
            | set(OURS['wizard_mc']) | {k for k in spec if k.startswith(('l_', 'm_'))})
app_known = set(OURS['shared_app']) | set(OURS['shared_app_other']) | {'controller_id',
                                                                      'uavcan_esc_index'}
unk = sorted((mc_fields - mc_known) | (app_fields - app_known))
print(f'\nCOVERAGE: {len(mc_fields)} mcconf + {len(app_fields)} appconf fields, '
      f'{len(unk)} unaccounted for' + (': ' + ', '.join(unk) if unk else ''))
print('READ-ONLY: nothing was written to this ESC.')
