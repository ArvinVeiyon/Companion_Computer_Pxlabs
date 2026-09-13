#!/usr/bin/env python3
"""Plot RC input against wheel rpm and current from a step_response_record.py CSV.

Top panel  - what the stick ASKED for (thr * 9000/7 mechanical rpm) vs what each wheel DID.
             The gap between the two is the lag, in rpm and in time.
Bottom     - per-wheel current. On release, NEGATIVE current is the brake working; the value
             it pins at is the regen ceiling set by l_in_current_min.

    python3 step_response_plot.py ~/step_20260913.csv [out.png]
"""
import csv
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

WHEELS = ('FR', 'FL', 'RR', 'RL')
RPM_MAX_CMD = 9000 / 7.0      # uavcan_raw_rpm_max at full stick, mechanical rpm
RPM_TO_MS = 0.003900
IN_MIN = -10.0                # l_in_current_min written to RL 2026-09-13


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else '/home/roz/step_response.csv'
    out = sys.argv[2] if len(sys.argv) > 2 else path.rsplit('.', 1)[0] + '.png'
    # 'current' = uavcan_raw_mode 0, where the stick is TORQUE and converting it to an rpm
    # setpoint would be a lie. Plot it as stick fraction on its own axis instead.
    torque_mode = len(sys.argv) > 3 and sys.argv[3].startswith('cur')

    t, thr = [], []
    rpm = {w: [] for w in WHEELS}
    cur = {w: [] for w in WHEELS}
    with open(path) as f:
        for r in csv.DictReader(f):
            if not r['thr']:
                continue
            t.append(float(r['t']))
            thr.append(float(r['thr']))
            for w in WHEELS:
                v = r.get(f'rpm_{w}', '')
                rpm[w].append(int(v) if v else float('nan'))
                c = r.get(f'cur_{w}', '')
                cur[w].append(float(c) if c else float('nan'))

    if not t:
        print('no usable samples')
        sys.exit(1)

    live = [w for w in WHEELS if any(v == v for v in rpm[w])]
    print(f'{len(t)} samples, {t[-1] - t[0]:.1f}s, wheels reporting: {", ".join(live) or "none"}')

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True,
                                   gridspec_kw={'height_ratios': [2, 1]})

    if torque_mode:
        axs = ax1.twinx()
        axs.plot(t, thr, color='#111', lw=2.2, label='stick (torque command)', zorder=5)
        axs.set_ylabel('stick fraction (torque)')
        axs.set_ylim(-1.15, 1.15)
        axs.legend(loc='upper left', fontsize=9)
    else:
        ax1.plot(t, [v * RPM_MAX_CMD for v in thr], color='#111', lw=2.2,
                 label='commanded (stick)', zorder=5)
    colors = {'FR': '#d1495b', 'FL': '#edae49', 'RR': '#00798c', 'RL': '#2e8b57'}
    for w in live:
        ax1.plot(t, rpm[w], color=colors[w], lw=1.4, label=f'{w} actual')
    ax1.axhline(0, color='#999', lw=0.8)
    ax1.set_ylabel('mechanical rpm')
    ax1.set_title('RC input vs wheel response  --  ' + ('CURRENT mode (raw_mode 0): stick is TORQUE'
                  if torque_mode else 'RPM mode (raw_mode 3): full stick = 1286 rpm = 4.93 m/s'))
    ax1.legend(loc='upper right', ncol=2, fontsize=9)
    ax1.grid(alpha=0.25)
    sec = ax1.secondary_yaxis('right', functions=(lambda r: r * RPM_TO_MS,
                                                  lambda s: s / RPM_TO_MS))
    sec.set_ylabel('m/s')

    for w in live:
        ax2.plot(t, cur[w], color=colors[w], lw=1.3, label=w)
    ax2.axhline(0, color='#999', lw=0.8)
    ax2.axhline(IN_MIN, color='#d1495b', ls='--', lw=1.2,
                label=f'l_in_current_min {IN_MIN:.0f} A (regen ceiling)')
    ax2.set_ylabel('motor current (A)')
    ax2.set_xlabel('seconds')
    ax2.legend(loc='lower right', ncol=3, fontsize=9)
    ax2.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f'wrote {out}')

    for w in live:
        vals = [c for c in cur[w] if c == c]
        if vals:
            print(f'  {w}: peak drive {max(vals):+.1f} A, peak regen {min(vals):+.1f} A')


if __name__ == '__main__':
    main()
