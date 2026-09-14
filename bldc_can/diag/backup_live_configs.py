#!/usr/bin/env python3
"""Read mcconf AND appconf off every ESC over USB and save them with a shared label.

    python3 diag/backup_live_configs.py --label FINAL_20260914

⚠️ THIS is the real config backup. backup_params.py reads only the 8 parameters the VESC
exposes over DroneCAN (canard_driver.c:225) -- no mcconf, no full appconf -- so it can never
stand in for this. USB + VESC Tool, one ESC at a time, is the only complete route.

Files are keyed on the controller_id read from the device, never on the ttyACM number, which
reshuffles after any USB hub reset.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import tune_esc as t

ap = argparse.ArgumentParser()
ap.add_argument('--label', required=True)
ap.add_argument('--ports', nargs='*', default=['/dev/ttyACM0', '/dev/ttyACM1',
                                               '/dev/ttyACM2', '/dev/ttyACM3'])
a = ap.parse_args()

seen, failed = {}, []
for port in a.ports:
    probe = t.LIVE / f'_backup_probe_{a.label}.xml'
    try:
        app_text = t.read_conf(port, 'App', probe)
    except SystemExit as e:
        failed.append((port, str(e).strip().splitlines()[-1] if str(e).strip() else 'read failed'))
        continue
    cid = t.get(app_text, 'controller_id')
    wheel = t.WHEEL.get(int(cid), f'UNKNOWN_{cid}')
    if wheel in seen:
        failed.append((port, f'duplicate controller_id {cid} ({wheel}) -- already read on {seen[wheel]}'))
        continue
    app_path = t.LIVE / f'vesc_appconf_{wheel}_{a.label}.xml'
    mc_path = t.LIVE / f'vesc_mcconf_{wheel}_{a.label}.xml'
    app_path.write_text(app_text)
    t.read_conf(port, 'Mc', mc_path)
    seen[wheel] = port
    print(f'{port}: controller_id {cid} = {wheel}  -> {mc_path.name} / {app_path.name}')
    probe.unlink(missing_ok=True)

print()
for port, why in failed:
    print(f'FAILED {port}: {why}')
missing = [w for w in ('FR', 'FL', 'RR', 'RL') if w not in seen]
if missing:
    sys.exit(f'INCOMPLETE BACKUP -- missing {", ".join(missing)}. '
             f'Reset hub 1-1.2 and re-run; do NOT treat this as a backup.')
print('All four wheels captured.')
