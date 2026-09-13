#!/usr/bin/env python3
"""Analyse a step_response_record.py CSV: is the lag dead time, torque limit, or PID?

For every throttle STEP UP it reports, per wheel:
  dead time  - stick moved -> wheel actually started (> 20 rpm)
  slope      - fastest rise, in ERPM/s, against the configured s_pid_ramp_erpms_s
  peak amps  - if this pins at l_current_max (25 A) the wheel is TORQUE limited, not ramp limited
  settle     - held rpm vs what the stick asked for (thr * 9000/7)

    python3 step_response_analyse.py ~/step_20260913.csv
"""
import csv
import sys

ADDRS = ('FR', 'FL', 'RR', 'RL')
RPM_TO_MS = 0.003900
RPM_MAX_CMD = 9000 / 7.0
RAMP_CFG = 20000          # s_pid_ramp_erpms_s read off RL 2026-09-13
CUR_MAX = 25.0            # l_current_max
MOVE_RPM = 20             # "the wheel has started"


def load(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                t = float(r['t'])
                thr = float(r['thr']) if r['thr'] else None
            except ValueError:
                continue
            if thr is None:
                continue
            rec = {'t': t, 'thr': thr}
            for w in ADDRS:
                for k, cast in (('rpm', int), ('cur', float)):
                    v = r.get(f'{k}_{w}', '')
                    rec[f'{k}_{w}'] = cast(v) if v not in ('', None) else None
            rows.append(rec)
    return rows


def find_steps(rows, min_rise=0.08, quiet=0.3):
    """A step = thr goes from near-rest to a clearly higher hold."""
    steps = []
    for i in range(1, len(rows)):
        t0, a = rows[i - 1]['t'], rows[i - 1]['thr']
        b = rows[i]['thr']
        if abs(a) > 0.03 or b - a < min_rise:
            continue
        if steps and t0 - steps[-1][0] < quiet:
            continue
        steps.append((t0, a, b, i))
    return steps


def analyse_step(rows, i0, t0, window=3.0):
    out = {}
    end_t = t0 + window
    seg = [r for r in rows if t0 <= r['t'] <= end_t]
    if len(seg) < 5:
        return out
    thr_hold = max(r['thr'] for r in seg)
    for w in ADDRS:
        pts = [(r['t'], r[f'rpm_{w}'], r[f'cur_{w}']) for r in seg if r[f'rpm_{w}'] is not None]
        if len(pts) < 5:
            continue
        dead = None
        for t, rpm, _ in pts:
            if abs(rpm) > MOVE_RPM:
                dead = t - t0
                break
        slope = 0.0
        for j in range(len(pts) - 1):
            for k in range(j + 1, min(j + 8, len(pts))):
                dt = pts[k][0] - pts[j][0]
                if dt < 0.05:
                    continue
                s = (abs(pts[k][1]) - abs(pts[j][1])) / dt
                slope = max(slope, s)
        cur = [abs(c) for _, _, c in pts if c is not None]
        tail = [abs(rpm) for t, rpm, _ in pts if t > t0 + window * 0.6]
        out[w] = {
            'dead': dead,
            'slope_erpm': slope * 7.0,
            'accel': slope * RPM_TO_MS,
            'peak_a': max(cur) if cur else None,
            'held': sum(tail) / len(tail) if tail else None,
            'want': thr_hold * RPM_MAX_CMD,
        }
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    rows = load(sys.argv[1])
    if not rows:
        print('no usable rows -- was manual_control_setpoint publishing?')
        sys.exit(1)
    print(f'{len(rows)} samples over {rows[-1]["t"] - rows[0]["t"]:.1f}s\n')

    steps = find_steps(rows)
    if not steps:
        print('NO THROTTLE STEPS FOUND. The stick never went from rest to a clear hold,')
        print('so nothing here measures response time. Re-run with distinct steps.')
        sys.exit(1)

    torque_limited = dead_slow = 0
    for n, (t0, a, b, i0) in enumerate(steps, 1):
        res = analyse_step(rows, i0, t0)
        if not res:
            continue
        print(f'--- step {n} at t={t0:.2f}s  thr {a:+.3f} -> {b:+.3f} ---')
        for w in ADDRS:
            if w not in res:
                continue
            d = res[w]
            dead = 'never moved' if d['dead'] is None else f'{d["dead"] * 1000:4.0f} ms'
            held = '----' if d['held'] is None else f'{d["held"]:5.0f}'
            pk = '--' if d['peak_a'] is None else f'{d["peak_a"]:4.1f}'
            flag = ''
            if d['peak_a'] is not None and d['peak_a'] > CUR_MAX * 0.9:
                flag += ' [AT CURRENT LIMIT]'
                torque_limited += 1
            if d['dead'] is not None and d['dead'] > 0.25:
                flag += ' [SLOW START]'
                dead_slow += 1
            print(f'  {w}: dead {dead}  slope {d["slope_erpm"]:7.0f} ERPM/s '
                  f'({d["accel"]:.2f} m/s2)  peak {pk} A  held {held} rpm '
                  f'vs want {d["want"]:5.0f}{flag}')
        print()

    print('=== READING THIS ===')
    print(f'configured ramp {RAMP_CFG} ERPM/s = {RAMP_CFG * RPM_TO_MS / 7:.1f} m/s2 ceiling')
    if torque_limited:
        print(f'{torque_limited} wheel-steps hit the {CUR_MAX:.0f} A limit: the wheel is TORQUE')
        print('limited, so the ramp is not what you feel. Raising the ramp changes nothing;')
        print('the setpoint already runs away from the wheel and that IS the surge.')
    if dead_slow:
        print(f'{dead_slow} wheel-steps took over 250 ms to start: that is the speed PID')
        print('failing to break stiction at low error (Kp 0.004), or the s_pid_min_erpm=200')
        print('release band if the commanded rpm was under 29.')
    if not torque_limited and not dead_slow:
        print('Response tracked the command. If it still FEELS laggy, the problem is stick')
        print('scaling, not the loop: full stick is 4.93 m/s, so indoors you live in the')
        print('bottom few percent of the travel.')


if __name__ == '__main__':
    main()
