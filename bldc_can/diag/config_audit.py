#!/usr/bin/env python3
"""Four-way ESC config audit: wheel-vs-wheel, and each wheel vs its 15-Aug baseline.

    python3 diag/config_audit.py --label FINAL_20260914

This is the method that caught the rear right hall table on 2026-09-14: RR's foc_hall_table__1
read 1 where both front wheels read 198/199, and RR was the only wheel whose config had moved
since August. Nothing else here has ever surfaced a fault of that kind, so it is worth running
whenever the rover misbehaves in a way that is not obviously a tuning value.

⛔ This tool REPORTS. It never writes to an ESC, and it must never be used to copy one wheel's
values onto another -- the per-motor detection results below are genuinely per-motor.
"""
import argparse
import pathlib
import re
import sys

LIVE = pathlib.Path(__file__).resolve().parent.parent / 'configs_live'
REPO = pathlib.Path(__file__).resolve().parent.parent / 'configs_from_repo'
WHEELS = ('FR', 'FL', 'RR', 'RL')
AUG = {'FR': 'Right_Front', 'FL': 'Left_Front', 'RR': 'Right_Rear', 'RL': 'Left_Rear'}

# Fields that SHOULD differ between wheels. Flagging these is noise, not signal.
PER_MOTOR = re.compile(
    r'^(foc_motor_r|foc_motor_l|foc_motor_ld_lq_diff|foc_motor_flux_linkage|'
    r'foc_hall_table__\d|foc_offsets_voltage__\d|foc_offsets_voltage_undriven__\d|'
    r'foc_offsets_current__\d|foc_temp_comp_base_temp|foc_encoder_offset|'
    r'si_motor_poles_dummy)$')
MIRRORED = {'m_invert_direction'}                       # left wheels 1, right wheels 0
IDENTITY = {'controller_id', 'uavcan_esc_index', 'can_esc_index'}


def fields(path):
    txt = path.read_text()
    return dict(re.findall(r'<([A-Za-z0-9_]+)>([^<]*)</\1>', txt))


def load(label, kind):
    out = {}
    for w in WHEELS:
        p = LIVE / f'vesc_{kind}_{w}_{label}.xml'
        if not p.exists():
            sys.exit(f'missing {p} -- run diag/backup_live_configs.py --label {label} first')
        out[w] = fields(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--label', required=True)
    a = ap.parse_args()

    for kind in ('mcconf', 'appconf'):
        live = load(a.label, kind)
        keys = sorted(set().union(*(d.keys() for d in live.values())))
        print(f'\n{"="*78}\n{kind.upper()} -- wheel vs wheel ({len(keys)} fields)\n{"="*78}')
        expected, suspect = [], []
        for k in keys:
            vals = {w: live[w].get(k) for w in WHEELS}
            if len(set(vals.values())) == 1:
                continue
            row = f'  {k:36} ' + ' '.join(f'{w}={vals[w]}' for w in WHEELS)
            if PER_MOTOR.match(k) or k in MIRRORED or k in IDENTITY:
                expected.append(row)
            else:
                suspect.append(row)
        print(f'\n-- fields that differ and are EXPECTED to ({len(expected)}) --')
        for r in expected:
            print(r)
        print(f'\n-- fields that differ and are NOT expected to ({len(suspect)}) --')
        print('\n'.join(suspect) if suspect else '  (none)')

    # Against the August baseline
    print(f'\n{"="*78}\nMCCONF -- each wheel vs its own 15-Aug baseline\n{"="*78}')
    live = load(a.label, 'mcconf')
    for w in WHEELS:
        base = REPO / f'vesc_mcconf_{AUG[w]}__15_Aug_26.xml'
        if not base.exists():
            print(f'\n{w}: no August baseline at {base.name}')
            continue
        old = fields(base)
        moved = [(k, old[k], live[w][k]) for k in sorted(old)
                 if k in live[w] and old[k] != live[w][k]]
        print(f'\n{w}: {len(moved)} field(s) changed since 15 Aug')
        for k, o, n in moved:
            print(f'    {k:36} {o:>14} -> {n}')


if __name__ == '__main__':
    main()
