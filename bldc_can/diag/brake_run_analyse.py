#!/usr/bin/env python3
"""Analyse a brake_run_record.py CSV -- LOADED, vehicle-side.

Answers what the motor-side analysis could not:
  1. Was the rover LOADED? esc_current at speed is the discriminator.
  2. Did the BODY move? /odom and IMU, cross-checked, never merged.
  3. Deceleration in m/s2 and STOPPING DISTANCE, braked vs coasting.

    python3 brake_run_analyse.py ~/brake_run_20260909_floor2.csv
"""
import csv
import sys

W = ['FR', 'FL', 'RR', 'RL']
DT = 0.2
BRAKE_ON = -0.9          # aux1 above this = brake commanded
NEUTRAL = 20             # ch2 within this of 1500 = throttle released


def n(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main(path):
    R = []
    for r in csv.DictReader(open(path)):
        R.append(dict(
            t=n(r['t']), ch2=n(r['ch2_us']), ch3=n(r['ch3_us']), aux1=n(r['aux1']),
            rpm=[n(r['rpm_' + w]) for w in W], amp=[n(r['amp_' + w]) for w in W],
            err=[n(r['err_' + w]) for w in W],
            ox=n(r['odom_x']), oy=n(r['odom_y']), ovx=n(r['odom_vx']),
            ax=n(r['imu_ax'])))
    print(f'{len(R)} samples, {R[-1]["t"]:.1f} s\n')

    # ---- faults ------------------------------------------------------------
    f = {}
    for r in R:
        for w, e in zip(W, r['err']):
            if e:
                f.setdefault(w, set()).add(int(e))
    print('=== esc_errorcount ===')
    print('  ' + (' '.join(f'{k}:{sorted(v)}' for k, v in f.items()) if f
                  else '0 = NONE on all four, every sample'))

    # ---- 1. LOADED? --------------------------------------------------------
    print('\n=== LOADED OR UNLOADED? esc_current is the discriminator ===')
    rest = [a for r in R if all(x == 0 for x in r['rpm'] if x is not None)
            for a in r['amp'] if a is not None]
    driving = [(abs(r['rpm'][i]), r['amp'][i]) for r in R for i in range(4)
               if r['rpm'][i] and abs(r['rpm'][i]) > 150 and r['amp'][i] is not None]
    if rest:
        print(f'  at rest      : {min(rest):+6.2f} .. {max(rest):+6.2f} A  (n={len(rest)}) = sensor noise')
    if driving:
        amps = sorted(a for _, a in driving)
        pos = [a for a in amps if a > 0]
        neg = [a for a in amps if a < 0]
        print(f'  while moving : {amps[0]:+6.2f} .. {amps[-1]:+6.2f} A  (n={len(driving)})')
        if pos:
            print(f'    driving current (positive), median {sorted(pos)[len(pos)//2]:+.2f} A, '
                  f'peak {max(pos):+.2f} A')
        if neg:
            print(f'    REGEN current (negative), median {sorted(neg)[len(neg)//2]:+.2f} A, '
                  f'peak {min(neg):+.2f} A  <- the brake pushing current back')
        print('\n  READING: unloaded wheels on stands need only a fraction of an amp to hold speed.')
        print('  Amps of the order seen here mean the motors were WORKING AGAINST A LOAD.')

    # ---- 2. DID THE BODY MOVE? --------------------------------------------
    print('\n=== DID THE BODY MOVE? two independent witnesses ===')
    ov = [abs(r['ovx']) for r in R if r['ovx'] is not None]
    ax = [r['ax'] for r in R if r['ax'] is not None]
    if ov:
        print(f'  /odom |vx|      : peak {max(ov):.3f} m/s, {sum(1 for x in ov if x > 0.05)} '
              f'samples above 0.05 m/s')
    if ax:
        rng = max(ax) - min(ax)
        print(f'  IMU accel x     : {min(ax):+.2f} .. {max(ax):+.2f} m/s2  (span {rng:.2f})')
        print('  IMU CANNOT BE FOOLED BY WHEEL SLIP. A spinning wheel on a stand produces no')
        print('  body acceleration; this span is real vehicle motion.')
    # path length from odom position
    d = 0.0
    prev = None
    for r in R:
        if r['ox'] is None:
            continue
        if prev:
            d += ((r['ox'] - prev[0]) ** 2 + (r['oy'] - prev[1]) ** 2) ** 0.5
        prev = (r['ox'], r['oy'])
    print(f'  /odom path length: {d:.1f} m   ⚠️ /odom DRIFTS at standstill (camera-gyro term) --')
    print('  treat as corroboration, not as a ruler.')

    # ---- 3. DECELERATION IN m/s2 ------------------------------------------
    print('\n=== DECELERATION (m/s2) AND STOPPING DISTANCE, from /odom ===')
    runs = {'brake': [], 'coast': []}
    i = 0
    while i < len(R) - 1:
        r = R[i]
        if (r['ovx'] is None or r['aux1'] is None or r['ch2'] is None
                or abs(r['ovx']) < 0.20 or abs(r['ch2'] - 1500) > NEUTRAL):
            i += 1
            continue
        on = r['aux1'] > BRAKE_ON
        j = i
        while j + 1 < len(R):
            b = R[j + 1]
            if (b['ovx'] is None or b['aux1'] is None or b['ch2'] is None
                    or abs(b['ch2'] - 1500) > NEUTRAL
                    or (b['aux1'] > BRAKE_ON) != on
                    or abs(b['ovx']) > abs(R[j]['ovx']) + 0.03):
                break
            j += 1
        if j - i >= 1:
            v0, v1 = abs(r['ovx']), abs(R[j]['ovx'])
            dt = (j - i) * DT
            if v0 - v1 > 0.05:
                runs['brake' if on else 'coast'].append((v0, v1, dt, (v0 - v1) / dt))
        i = j + 1 if j > i else i + 1

    for key, label in (('brake', 'BRAKED'), ('coast', 'COASTING')):
        v = runs[key]
        if not v:
            print(f'  {label:9}: NO QUALIFYING RUN CAPTURED')
            continue
        rates = sorted(x[3] for x in v)
        med = rates[len(rates) // 2]
        print(f'  {label:9}: {med:.2f} m/s2 median, {rates[-1]:.2f} peak  (n={len(v)})')
        for v0, v1, dt, a in sorted(v, key=lambda x: -x[0])[:3]:
            print(f'             {v0:.2f} -> {v1:.2f} m/s in {dt:.1f}s = {a:.2f} m/s2'
                  f'  => {v0 * v0 / (2 * a):.2f} m to stop from {v0:.2f} m/s')
    if runs['brake'] and runs['coast']:
        b = sorted(x[3] for x in runs['brake'])
        c = sorted(x[3] for x in runs['coast'])
        mb, mc = b[len(b) // 2], c[len(c) // 2]
        print(f'\n  BRAKE vs COAST: {mb:.2f} vs {mc:.2f} m/s2  => {mb / mc:.1f}x')
        for v0 in (0.9,):
            print(f'  From {v0} m/s: coast {v0*v0/(2*mc):.2f} m, braked {v0*v0/(2*mb):.2f} m'
                  f'  => saves {v0*v0/2*(1/mc - 1/mb):.2f} m')
    elif runs['brake']:
        print('\n  NO COAST BASELINE CAPTURED -- the brake cannot be scored against one.')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/home/roz/brake_run_20260909_floor2.csv')
