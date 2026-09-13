#!/usr/bin/env python3
"""Measure how long, and how far, the rover takes to stop after the stick is released.

    python3 stop_analyse.py ~/floor_360_20260913.csv [out.png]

A STOP EVENT is: a stick (throttle OR yaw) held away from centre with the wheels actually
turning, then returned to centre, followed by the wheels coming to rest. For each one:

    entry speed   mean |wheel speed| at release, m/s (rpm * 0.003900)
    stop time     release -> all four wheels under 15 rpm
    distance      integral of wheel speed over that time -- for a straight stop this is metres
                  travelled; for a SPIN it is wheel travel, not ground distance
    peak regen    most negative current during the stop. If it pins near l_in_current_min the
                  brake is at its ceiling and the setting is what limits you.

⚠️ Straight stops and spin stops are reported separately. They are not comparable: in a spin
the wheels fight each other and the chassis has rotational inertia, so the numbers mean
different things.
"""
import csv
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

WHEELS = ('FR', 'FL', 'RR', 'RL')
RPM_TO_MS = 0.003900
CENTRED = 0.05        # |stick| below this is released
ACTIVE = 0.10         # |stick| above this is a real command
STOPPED = 15          # rpm below which a wheel counts as stopped
MIN_ENTRY = 40        # rpm: ignore releases that were barely moving
IN_MIN = -10.0


def load(path):
    rows = []
    for r in csv.DictReader(open(path)):
        if not r['thr'] or r.get('armed') == '0':
            continue
        rpm, cur = [], []
        for w in WHEELS:
            v = r.get(f'rpm_{w}', '')
            c = r.get(f'cur_{w}', '')
            rpm.append(float(v) if v else np.nan)
            cur.append(float(c) if c else np.nan)
        rows.append({'t': float(r['t']),
                     'thr': float(r['thr']),
                     # roll is the TURN axis on this rover (ch1), not yaw -- probed 2026-09-13
                     'turn': float(r['roll']) if r.get('roll') else (
                         float(r['yaw']) if r.get('yaw') else 0.0),
                     'rpm': np.array(rpm), 'cur': np.array(cur)})
    return rows


def find_stops(rows, max_stop=6.0):
    stops = []
    for i in range(1, len(rows)):
        prev, cur = rows[i - 1], rows[i]
        cmd_prev = max(abs(prev['thr']), abs(prev['turn']))
        cmd_now = max(abs(cur['thr']), abs(cur['turn']))
        if not (cmd_prev > ACTIVE and cmd_now < CENTRED):
            continue
        speed = np.nanmean(np.abs(prev['rpm']))
        if not (speed > MIN_ENTRY):
            continue
        kind = 'spin' if abs(prev['turn']) > abs(prev['thr']) else 'straight'
        t0 = cur['t']
        dist, t_stop, peak = 0.0, None, 0.0
        for j in range(i, len(rows)):
            r = rows[j]
            if r['t'] - t0 > max_stop:
                break
            if max(abs(r['thr']), abs(r['turn'])) > ACTIVE:
                break            # drove again before stopping: not a clean stop
            dt = r['t'] - rows[j - 1]['t']
            dist += np.nanmean(np.abs(r['rpm'])) * RPM_TO_MS * dt
            peak = min(peak, float(np.nanmin(r['cur'])) if np.any(~np.isnan(r['cur'])) else 0.0)
            if np.all(np.abs(r['rpm'])[~np.isnan(r['rpm'])] < STOPPED):
                t_stop = r['t'] - t0
                break
        if t_stop:
            stops.append({'t0': t0, 'kind': kind, 'entry': speed * RPM_TO_MS,
                          'time': t_stop, 'dist': dist, 'peak': peak,
                          'decel': speed * RPM_TO_MS / t_stop})
    return stops


def main():
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else path.rsplit('.', 1)[0] + '_stops.png'
    rows = load(path)
    if not rows:
        sys.exit('no armed samples -- was it armed?')
    print(f'{len(rows)} armed samples over {rows[-1]["t"] - rows[0]["t"]:.1f}s')

    stops = find_stops(rows)
    if not stops:
        print('\nNO CLEAN STOPS FOUND. A stop needs: stick away from centre with the wheels '
              'turning, then centred, then left alone until the wheels rest.')
        sys.exit(1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
    for kind, color in (('straight', '#00798c'), ('spin', '#d1495b')):
        sel = [s for s in stops if s['kind'] == kind]
        if not sel:
            continue
        ax1.scatter([s['entry'] for s in sel], [s['dist'] for s in sel],
                    color=color, s=70, label=f'{kind} (n={len(sel)})')
        ax2.scatter([s['entry'] for s in sel], [s['decel'] for s in sel], color=color, s=70)
        print(f'\n{kind.upper()} STOPS ({len(sel)}):')
        for s in sel:
            print(f'   t={s["t0"]:6.1f}s  from {s["entry"]:.2f} m/s  '
                  f'stopped in {s["time"]:.2f} s / {s["dist"]:.2f} m  '
                  f'({s["decel"]:.2f} m/s2)  peak regen {s["peak"]:+.1f} A')
        print(f'   median: {np.median([s["time"] for s in sel]):.2f} s, '
              f'{np.median([s["dist"] for s in sel]):.2f} m, '
              f'{np.median([s["decel"] for s in sel]):.2f} m/s2')
        pinned = [s for s in sel if s['peak'] <= IN_MIN * 0.9]
        if pinned:
            print(f'   {len(pinned)}/{len(sel)} hit the {IN_MIN:.0f} A regen ceiling -- '
                  f'braking is LIMITED BY l_in_current_min, raising it would stop shorter')
        else:
            print(f'   none reached the {IN_MIN:.0f} A ceiling (worst '
                  f'{min(s["peak"] for s in sel):+.1f} A) -- the regen limit is NOT what is '
                  f'holding you back')

    ax1.set_xlabel('speed at release (m/s)')
    ax1.set_ylabel('wheel distance to stop (m)')
    ax1.set_title('Stopping distance')
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.25)
    ax2.set_xlabel('speed at release (m/s)')
    ax2.set_ylabel('mean deceleration (m/s2)')
    ax2.set_title('Deceleration  (Sept RC-brake reference: 1.44, coast: 0.46)')
    ax2.axhline(1.44, ls='--', color='#666', lw=1.2)
    ax2.axhline(0.46, ls=':', color='#666', lw=1.2)
    ax2.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f'\nwrote {out}')
    print('\n⚠️ Spin numbers are WHEEL travel, not ground distance. Do not read them as metres '
          'across the floor.')


if __name__ == '__main__':
    main()
