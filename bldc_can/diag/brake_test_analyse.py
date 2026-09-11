#!/usr/bin/env python3
"""Analyse a brake_test_record.py CSV.

Answers the three questions the release note needs:
  1. Is aux1 PROPORTIONAL to ch3, and does the bottom stop read -1.0 (brake OFF)?
     Fits RC3_TRIM / RC3_MAX from the data, since the params may not be readable over MAVLink.
  2. How hard does each wheel decelerate UNDER BRAKE vs COASTING?
  3. Did esc_errorcount ever leave 0?

    python3 brake_test_analyse.py ~/brake_test_20260909.csv
"""
import csv
import sys

WHEELS = ['FR', 'FL', 'RR', 'RL']
BRAKE_ON = -0.9        # aux1 above this = brake commanded (bottom stop is -1.0)
DT = 0.2


def num(s):
    if s is None or s == '':
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main(path):
    rows = list(csv.DictReader(open(path)))
    R = []
    for r in rows:
        R.append(dict(
            t=num(r['t']), ch3=num(r['ch3_us']), ch2=num(r['ch2_us']), aux1=num(r['aux1']),
            rpm=[num(r[f'rpm_{w}']) for w in WHEELS],
            err=[num(r[f'err_{w}']) for w in WHEELS]))
    print(f'{len(R)} samples, {R[-1]["t"]:.1f} s\n')

    # ---- 3. faults first: it gates everything else -------------------------
    faults = {}
    for r in R:
        for w, e in zip(WHEELS, r['err']):
            if e:
                faults.setdefault(w, set()).add(int(e))
    print('=== esc_errorcount ===')
    if faults:
        for w, c in faults.items():
            print(f'  FAULT {w}: codes {sorted(c)}')
    else:
        print('  0 = NONE on all four, every sample. No missed timeout_reset() signature.')

    # ---- 1. proportionality ------------------------------------------------
    print('\n=== ch3 -> aux1 (steady samples only: ch3 unchanged from previous) ===')
    steady = []
    for a, b in zip(R, R[1:]):
        if a['ch3'] is not None and a['ch3'] == b['ch3'] and b['aux1'] is not None:
            steady.append((b['ch3'], b['aux1']))
    if not steady:
        print('  none -- every sample was mid-sweep')
    else:
        agg = {}
        for c, x in steady:
            agg.setdefault(c, []).append(x)
        for c in sorted(agg):
            v = agg[c]
            print(f'  ch3 {c:6.0f} us  ->  aux1 {sum(v)/len(v):+.4f}   (n={len(v)})')
        # fit TRIM/MAX from the two most separated steady points above the stop
        above = [(c, x) for c, x in steady if x > -0.9]
        if len(above) >= 2:
            lo = min(above, key=lambda p: p[0])
            hi = max(above, key=lambda p: p[0])
            if hi[1] != lo[1]:
                span = (hi[0] - lo[0]) / (hi[1] - lo[1])
                trim = lo[0] - lo[1] * span
                print(f'\n  fitted RC3_TRIM ~= {trim:.0f} us, RC3_MAX ~= {trim + span:.0f} us')
                print('  (RC3_TRIM must NOT be 1001 -- that is the 50%-brake-at-the-stop bug)')
    # Solve PX4's own piecewise map for RC3_TRIM, assuming RC3_MIN = 1001.
    #   below trim:  aux1 = (ch3 - T) / (T - MIN)   =>   T = (ch3 + MIN*aux1) / (1 + aux1)
    # Samples taken mid-sweep are skewed (input_rc and manual_control_setpoint are sampled
    # independently), so scatter is expected -- the MEDIAN is the answer, not the spread.
    MIN = 1001.0
    est = []
    for r in R:
        c, x = r['ch3'], r['aux1']
        if c is None or x is None:
            continue
        if MIN + 5 < c < 1450 and -0.99 < x < -0.05:
            est.append((c + MIN * x) / (1 + x))
    if est:
        est.sort()
        med = est[len(est) // 2]
        print(f'\n  RC3_TRIM solved from the map: median {med:.1f} us  (n={len(est)}, '
              f'range {est[0]:.0f}-{est[-1]:.0f})')
        print(f'  1487.5 = the fixed value | 1001 = the 50%-brake bug')
    # RC3_MAX, same idea above trim: aux1 = (ch3 - T)/(MAX - T)
    T = 1487.5
    est2 = [T + (r['ch3'] - T) / r['aux1']
            for r in R
            if r['ch3'] and r['aux1'] and T + 100 < r['ch3'] < 1960 and 0.2 < r['aux1'] < 0.99]
    if est2:
        est2.sort()
        print(f'  RC3_MAX  solved (assuming TRIM 1487.5): median {est2[len(est2)//2]:.0f} us '
              f'(n={len(est2)})')
    sat = [r['ch3'] for r in R if r['aux1'] is not None and r['aux1'] >= 0.9999 and r['ch3']]
    if sat:
        print(f'  aux1 saturates at +1.0000 from ch3 {min(sat):.0f} us upward')

    bottom = [r['aux1'] for r in R if r['ch3'] == 1001 and r['aux1'] is not None]
    if bottom:
        print(f'\n  bottom stop (ch3=1001): aux1 min {min(bottom):+.4f} max {max(bottom):+.4f}'
              f'  (n={len(bottom)})')
        print('  -1.0000 => slot5 = 1 => brake_rel 0.012% => BELOW the 0.05 threshold => BRAKE OFF')

    # ---- 2. deceleration: braked vs coasting -------------------------------
    # SUSTAINED RUNS, not sample pairs. A single pair catches rpm-telemetry spikes and the
    # tail of a braked stop, and both land in the wrong bucket -- that is how a working brake
    # ends up looking like 1.1x coast. A run must be >=3 samples of monotonic slowdown from a
    # real speed, with throttle neutral throughout and the brake state unchanged.
    print('\n=== sustained decelerations (>=3 samples, from |rpm|>=250, throttle neutral) ===')
    runs = {w: {'brake': [], 'coast': []} for w in WHEELS}
    for i, w in enumerate(WHEELS):
        j = 0
        while j < len(R) - 1:
            a = R[j]
            if (a['aux1'] is None or a['ch2'] is None or a['rpm'][i] is None
                    or abs(a['ch2'] - 1500) > 20 or abs(a['rpm'][i]) < 250):
                j += 1
                continue
            on = a['aux1'] > BRAKE_ON
            k = j
            while k + 1 < len(R):
                b = R[k + 1]
                if (b['aux1'] is None or b['ch2'] is None or b['rpm'][i] is None
                        or abs(b['ch2'] - 1500) > 20
                        or (b['aux1'] > BRAKE_ON) != on
                        or abs(b['rpm'][i]) > abs(R[k]['rpm'][i]) + 5):
                    break
                k += 1
            n = k - j
            if n >= 2:
                drop = abs(a['rpm'][i]) - abs(R[k]['rpm'][i])
                if drop > 0:
                    runs[w]['brake' if on else 'coast'].append(
                        (drop / (n * DT), abs(a['rpm'][i]), n * DT))
            j = k + 1 if k > j else j + 1

    print(f'  {"wheel":6} {"BRAKED rpm/s":>26}   {"COASTING rpm/s":>26}')
    for w in WHEELS:
        out = []
        for key in ('brake', 'coast'):
            v = runs[w][key]
            if v:
                rates = sorted(x[0] for x in v)
                out.append(f'{rates[len(rates)//2]:6.0f} med, {rates[-1]:5.0f} max (n={len(v):2d})')
            else:
                out.append('              no runs')
        print(f'  {w:6} {out[0]:>26}   {out[1]:>26}')
    ab = sorted(x[0] for w in WHEELS for x in runs[w]['brake'])
    ac = sorted(x[0] for w in WHEELS for x in runs[w]['coast'])
    if ab and ac:
        mb, mc = ab[len(ab)//2], ac[len(ac)//2]
        print(f'\n  MEDIAN: braked {mb:.0f} rpm/s vs coasting {mc:.0f} rpm/s'
              f'  =>  brake is {mb/mc:.1f}x the coast deceleration')
    elif ab:
        print(f'\n  braked median {ab[len(ab)//2]:.0f} rpm/s over {len(ab)} runs.')
        print('  NO CLEAN COAST RUN IN THIS DATA -- every sustained slowdown had brake commanded,')
        print('  so the brake CANNOT be scored against a baseline yet. Spin up, then release')
        print('  throttle to neutral with ch3 AT THE BOTTOM STOP and let it run down untouched.')

    print('\n--- per-sample pairs (noisier, kept for comparison) ---')
    braked, coast = {w: [] for w in WHEELS}, {w: [] for w in WHEELS}
    for a, b in zip(R, R[1:]):
        if a['aux1'] is None or b['aux1'] is None:
            continue
        # THROTTLE MUST BE NEUTRAL AT BOTH ENDS. Without this the "coast" bucket fills
        # with powered decel and direction reversals, which are not coasting at all --
        # they read as huge decel rates and make the brake look useless.
        if a['ch2'] is None or b['ch2'] is None:
            continue
        if abs(a['ch2'] - 1500) > 20 or abs(b['ch2'] - 1500) > 20:
            continue
        on = a['aux1'] > BRAKE_ON and b['aux1'] > BRAKE_ON
        off = a['aux1'] <= BRAKE_ON and b['aux1'] <= BRAKE_ON
        if not (on or off):
            continue
        for i, w in enumerate(WHEELS):
            ra, rb = a['rpm'][i], b['rpm'][i]
            if ra is None or rb is None:
                continue
            if abs(ra) < 100:                      # only score from a real speed
                continue
            if abs(rb) >= abs(ra):                 # only falling
                continue
            rate = (abs(ra) - abs(rb)) / DT
            (braked if on else coast)[w].append(rate)

    print(f'  {"wheel":6} {"BRAKED rpm/s":>22}   {"COASTING rpm/s":>22}')
    for w in WHEELS:
        bb, cc = braked[w], coast[w]
        bs = f'{sum(bb)/len(bb):7.0f} avg, {max(bb):5.0f} peak (n={len(bb):3d})' if bb else '            no data'
        cs = f'{sum(cc)/len(cc):7.0f} avg, {max(cc):5.0f} peak (n={len(cc):3d})' if cc else '            no data'
        print(f'  {w:6} {bs:>22}   {cs:>22}')
    allb = [x for w in WHEELS for x in braked[w]]
    allc = [x for w in WHEELS for x in coast[w]]
    if allb and allc:
        mb, mc = sum(allb)/len(allb), sum(allc)/len(allc)
        print(f'\n  all wheels: braked {mb:.0f} rpm/s vs coasting {mc:.0f} rpm/s'
              f'  =>  brake is {mb/mc:.1f}x the coast decel' if mc else '')
    elif allb and not allc:
        print('\n  NO COAST REFERENCE in this run: every deceleration had brake commanded.')
        print('  Spin up and release throttle with ch3 at the bottom stop to get the baseline.')

    print('\n  NOTE: rpm/s on stands is UNLOADED. It bounds the brake, it does not predict')
    print('  stopping distance on the floor, where the rover carries its own mass.')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/home/roz/brake_test_20260909.csv')
