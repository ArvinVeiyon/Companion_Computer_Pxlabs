#!/usr/bin/env python3
"""Compare the RC-input -> response CURVE across runs (current mode vs RPM mode).

Two different things both get called "lag", so this measures both:

  LEFT  - the static transfer curve: stick position -> the speed you actually get, taken only
          from SETTLED samples (stick held still for >= 0.25 s), so transients don't smear it.
          This is the shape your thumb feels.
  RIGHT - the dynamic lag: cross-correlation between d(stick)/dt and d(rpm)/dt on a uniform
          20 ms grid. The peak offset is how long the wheel takes to follow the stick.

    python3 response_curve_compare.py RL out.png "label=csv" "label=csv" ...

⚠️ An UNLOADED current-mode curve saturates by construction - with no load the wheel runs to
the duty ceiling at a fraction of stick. That is physics, not a setting, and it is why the
current-mode curve here cannot be read as what the rover will do on the floor. The RPM-mode
curve does not have that problem: a closed speed loop gives the same curve loaded or not.
"""
import csv
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RPM_TO_MS = 0.003900
GRID = 0.02          # 20 ms resample
SETTLED = 0.25       # stick must be still this long to count for the static curve
STILL = 0.02         # stick "still" tolerance, in normalised units


def load(path, wheel):
    """Armed, commanded samples only.

    Runs recorded before the vehicle_status_v1 fix have an empty 'armed' column, so a
    disarmed stretch there looks like a settled stick at zero rpm and destroys the median.
    Those are caught by the physical signature instead: stick demanding something, wheel at
    zero, and NO current flowing at all means the ESC was never commanded.
    """
    t, thr, rpm, dropped = [], [], [], 0
    for r in csv.DictReader(open(path)):
        if not r['thr'] or not r.get(f'rpm_{wheel}'):
            continue
        if r.get('armed') == '0':
            dropped += 1
            continue
        th = float(r['thr'])
        rp = float(r[f'rpm_{wheel}'])
        cu = r.get(f'cur_{wheel}', '')
        cu = float(cu) if cu else 0.0
        if abs(th) > 0.05 and rp == 0 and abs(cu) < 0.3:
            dropped += 1
            continue
        t.append(float(r['t']))
        thr.append(th)
        rpm.append(rp)
    if dropped:
        print(f'   ({dropped} not-commanded samples dropped)')
    return np.array(t), np.array(thr), np.array(rpm)


def resample(t, y, grid):
    return np.interp(grid, t, y)


def static_curve(t, thr, rpm, nbins=25):
    """Median rpm per stick bin, using only settled samples."""
    keep = np.zeros(len(t), bool)
    for i in range(len(t)):
        j = i
        while j > 0 and t[i] - t[j] < SETTLED:
            j -= 1
        if j < i and np.ptp(thr[j:i + 1]) <= STILL:
            keep[i] = True
    x, y = thr[keep], rpm[keep]
    if len(x) < 20:
        return None, None, 0
    edges = np.linspace(-1, 1, nbins + 1)
    cx, cy = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (x >= a) & (x < b)
        if m.sum() >= 5:
            cx.append((a + b) / 2)
            cy.append(np.median(y[m]))
    return np.array(cx), np.array(cy), keep.sum()


def lag_seconds(t, thr, rpm, max_lag=1.0):
    grid = np.arange(t[0], t[-1], GRID)
    a = np.diff(resample(t, thr, grid))
    b = np.diff(resample(t, rpm, grid))
    a = (a - a.mean()) / (a.std() or 1)
    b = (b - b.mean()) / (b.std() or 1)
    n = int(max_lag / GRID)
    best, best_k = -9e9, 0
    for k in range(0, n):
        c = float(np.dot(a[:len(a) - k], b[k:])) / (len(a) - k)
        if c > best:
            best, best_k = c, k
    return best_k * GRID, best


def main():
    wheel = sys.argv[1]
    out = sys.argv[2]
    runs = [s.split('=', 1) for s in sys.argv[3:]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    colors = ['#00798c', '#d1495b', '#edae49', '#2e8b57']
    rows = []

    for i, (label, path) in enumerate(runs):
        t, thr, rpm = load(path, wheel)
        if len(t) < 50:
            print(f'{label}: too few armed samples, skipped')
            continue
        cx, cy, nset = static_curve(t, thr, rpm)
        lag, corr = lag_seconds(t, thr, rpm)
        c = colors[i % len(colors)]
        if cx is not None:
            # Dotted between points: with bang-bang driving only the ends are populated, and a
            # solid line there would draw a curve shape that was never measured.
            mid = int(np.sum((np.abs(cx) > 0.12) & (np.abs(cx) < 0.88)))
            ax1.plot(cx, cy, 'o:', color=c, lw=1.1, ms=7,
                     label=f'{label}  ({mid} mid-stick points)')
        ax2.bar(i, lag * 1000, color=c, width=0.6)
        ax2.text(i, lag * 1000, f'{lag * 1000:.0f} ms', ha='center', va='bottom', fontsize=10)
        rows.append((label, lag * 1000, corr, nset, cx, cy))

    lim = np.linspace(-1, 1, 50)
    ax1.plot(lim, lim * 9000 / 7.0, '--', color='#888', lw=1.2, label='perfectly linear (9000 cap)')
    ax1.axhline(0, color='#999', lw=0.8)
    ax1.axvline(0, color='#999', lw=0.8)
    ax1.set_xlabel('stick position (normalised)')
    ax1.set_ylabel(f'{wheel} mechanical rpm (settled)')
    ax1.set_title('Static response curve (points are MEASURED, dotted lines are not)')
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.25)
    sec = ax1.secondary_yaxis('right', functions=(lambda r: r * RPM_TO_MS,
                                                  lambda s: s / RPM_TO_MS))
    sec.set_ylabel('m/s')

    ax2.set_xticks(range(len(rows)))
    ax2.set_xticklabels([r[0] for r in rows], fontsize=9)
    ax2.set_ylabel('stick-to-wheel lag (ms)')
    ax2.set_title('Dynamic lag: cross-correlation peak')
    ax2.grid(alpha=0.25, axis='y')

    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f'wrote {out}\n')

    for label, lag, corr, nset, cx, cy in rows:
        print(f'{label}:')
        print(f'   lag {lag:.0f} ms (corr {corr:.2f}), {nset} settled samples')
        if cx is not None:
            for frac in (0.1, 0.25, 0.5, 0.75, 1.0):
                k = int(np.argmin(np.abs(cx - frac)))
                if abs(cx[k] - frac) < 0.12:
                    print(f'   stick {frac:>4.0%} -> {cy[k]:6.0f} rpm '
                          f'({cy[k] * RPM_TO_MS:.2f} m/s)')
        print()


if __name__ == '__main__':
    main()
