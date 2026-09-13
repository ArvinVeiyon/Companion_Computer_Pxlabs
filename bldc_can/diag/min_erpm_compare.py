#!/usr/bin/env python3
"""Compare s_pid_min_erpm settings on the two things a BENCH run can actually measure.

    python3 min_erpm_compare.py RL out.png "200=a.csv" "50=b.csv" "0=c.csv"

START THRESHOLD - the smallest stick that gets the wheel moving from standstill. In the
firmware the motor only leaves its released state once the command reaches s_pid_min_erpm
(mcpwm_foc.c, mcpwm_foc_set_pid_speed), so this is the dead band at the bottom of your stick,
measured rather than predicted. Expect roughly min_erpm/9000 of stick: 2.2% at 200, 0.6% at 50,
none at 0.

ZERO-STICK DITHER - with the stick centred and the vehicle armed, how much current the motor
still draws and how much the rpm wanders. This is the thing s_pid_min_erpm=200 was set to cure
on 09-12: at 0 rpm a hall sensor gives 60-degree steps, so the speed estimate is noise and a
PID with no release band chases it.

⚠️ This says NOTHING about stopping distance. Unloaded there is no kinetic energy for the
brake to remove. That measurement needs the rover on the floor on its own mass.
"""
import csv
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RPM_TO_MS = 0.003900
ERPM_FULL = 9000.0
MOVING = 15          # rpm that counts as "the wheel started"
QUIET = 0.03         # |stick| below this counts as centred


def load(path, wheel):
    rows = []
    for r in csv.DictReader(open(path)):
        if not r['thr'] or not r.get(f'rpm_{wheel}'):
            continue
        if r.get('armed') == '0':
            continue
        cu = r.get(f'cur_{wheel}', '')
        rows.append((float(r['t']), float(r['thr']), float(r[f'rpm_{wheel}']),
                     float(cu) if cu else float('nan')))
    return rows


def start_threshold(rows, rest_needed=0.5, creep_max=0.35, max_rate=0.6):
    """Smallest |stick| that broke the wheel away from a genuine standstill.

    Three filters, each one added because the previous pass produced nonsense:
      - wheel ACTUALLY AT REST for rest_needed first, or a spin-down counts as a start;
      - stick still in the creep region, or a full-stick slam is recorded as a 100% threshold;
      - stick moving SLOWLY (<= max_rate per second) at the moment of breakaway. Without this
        the number measures how fast the operator pushed, not the release band -- which is how
        min_erpm 10 first came out at 18.4%, worse than 200, which is impossible.
    """
    thresholds = []
    rest_since = None
    for i in range(1, len(rows)):
        t, th, rpm, _ = rows[i]
        if abs(rpm) < MOVING:
            if rest_since is None:
                rest_since = t
            continue
        if rest_since is not None and (t - rest_since) >= rest_needed:
            # stick rate over the 0.3 s leading up to breakaway
            j = i
            while j > 0 and t - rows[j][0] < 0.3:
                j -= 1
            dt = t - rows[j][0]
            rate = abs(th - rows[j][1]) / dt if dt > 0 else 9e9
            if abs(th) <= creep_max and rate <= max_rate:
                thresholds.append(abs(th))
        rest_since = None
    return thresholds


def zero_stick(rows, settle=0.5):
    """Standing still, not spinning down.

    Requires stick centred AND the wheel already stopped AND both true for `settle` seconds,
    so a release that is still coasting does not get counted as dither.
    """
    ok_since, cur, rpm = None, [], []
    for t, th, r, c in rows:
        if abs(th) < QUIET and abs(r) < MOVING:
            if ok_since is None:
                ok_since = t
            elif t - ok_since >= settle:
                if c == c:
                    cur.append(abs(c))
                rpm.append(abs(r))
        else:
            ok_since = None
    if not cur:
        return None
    return {'n': len(cur), 'cur_mean': float(np.mean(cur)), 'cur_p95': float(np.percentile(cur, 95)),
            'rpm_mean': float(np.mean(rpm)), 'rpm_max': float(np.max(rpm))}


def main():
    wheel, out = sys.argv[1], sys.argv[2]
    runs = [s.split('=', 1) for s in sys.argv[3:]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
    colors = ['#00798c', '#d1495b', '#edae49', '#2e8b57']
    labels, med_thr, cur_mean = [], [], []

    for i, (label, path) in enumerate(runs):
        rows = load(path, wheel)
        if len(rows) < 50:
            print(f'min_erpm {label}: too few armed samples, skipped')
            continue
        ths = start_threshold(rows)
        z = zero_stick(rows)
        c = colors[i % len(colors)]
        labels.append(f'min_erpm {label}')

        if ths:
            med = float(np.median(ths))
            med_thr.append(med * 100)
            ax1.scatter([i] * len(ths), [t * 100 for t in ths], color=c, alpha=0.45, s=22)
            ax1.scatter([i], [med * 100], color=c, s=160, marker='_', lw=3)
            pred = float(label) / ERPM_FULL * 100 if label.replace('.', '').isdigit() else None
            if pred is not None:
                ax1.scatter([i], [pred], color='#333', marker='x', s=60, zorder=5)
        else:
            med_thr.append(float('nan'))

        cur_mean.append(z['cur_mean'] if z else float('nan'))

        print(f'\nmin_erpm {label}:')
        if ths:
            print(f'   start threshold: median {np.median(ths) * 100:.1f}% of stick '
                  f'({len(ths)} breakaways, range {min(ths) * 100:.1f}-{max(ths) * 100:.1f}%)')
            print(f'   predicted from firmware: {float(label) / ERPM_FULL * 100:.1f}%')
        else:
            print('   start threshold: NO breakaway from standstill seen -- the run needs slow '
                  'creep from rest, not full-stick steps')
        if z:
            print(f'   zero stick ({z["n"]} samples): current mean {z["cur_mean"]:.2f} A, '
                  f'p95 {z["cur_p95"]:.2f} A; rpm mean {z["rpm_mean"]:.1f}, max {z["rpm_max"]:.0f}')
        else:
            print('   zero stick: never centred long enough to measure dither')

    ax1.set_xticks(range(len(labels)))
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_ylabel('stick at breakaway (%)')
    ax1.set_title('Dead band: smallest stick that moves the wheel\n(x = firmware prediction)')
    ax1.grid(alpha=0.25, axis='y')

    ax2.bar(range(len(labels)), cur_mean, color=colors[:len(labels)], width=0.6)
    for i, v in enumerate(cur_mean):
        if v == v:
            ax2.text(i, v, f'{v:.2f} A', ha='center', va='bottom', fontsize=10)
    ax2.set_xticks(range(len(labels)))
    ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylabel('mean |current| at centred stick (A)')
    ax2.set_title('Zero-stick dither: current drawn while standing still')
    ax2.grid(alpha=0.25, axis='y')

    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f'\nwrote {out}')
    print('\nNeither panel measures stopping distance. That needs the floor.')


if __name__ == '__main__':
    main()
