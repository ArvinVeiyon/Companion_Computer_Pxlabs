#!/usr/bin/env python3
"""Apply the agreed speed-loop tuning to ONE ESC over USB, safely and idempotently.

    python3 tune_esc.py                 # act on whatever is on /dev/ttyACM0
    python3 tune_esc.py --dry-run       # read and report, change nothing

⛔ THIS NEVER COPIES ONE WHEEL'S CONFIG ONTO ANOTHER. Each ESC's own mcconf/appconf is read
off the device, exactly two motor values are edited, and everything else is written back
byte-identical. That matters: the mcconf carries per-motor detection results -- foc_hall_table,
foc_motor_r, foc_motor_flux_linkage, foc_offsets_* -- and m_invert_direction, which is MIRRORED
(left wheels 1, right wheels 0). Cross-writing them is how a wheel gets a failed detection.

Targets (agreed 2026-09-13, proven on RL):
    s_pid_kp          0.008   (was 0.004 -- the loop was under-asking for current, drive peak
                               12.0 A -> 20.7 A, regen 3.7 A -> 7.3 A on the bench)
    l_in_current_min  -10     (was -5 -- battery-side regen ceiling, i.e. braking authority)
    s_pid_min_erpm    50      (was 200. Bench test on RL across 200/100/50/10/0, 2026-09-13.
                               The ONLY metric that replicated is rpm scatter at standstill:
                               50 gave exactly 0.00 in two independent runs, 100 gave 0.36 in
                               one, 0 gave 0.69. Standing CURRENT did not replicate -- 0.072 /
                               0.112 / 0.130 across three runs at 50 -- so ignore it, it sits
                               inside the current sensor's own noise band.
                               ⛔ Do NOT take it to 0: worst dither measured, AND it gives up
                               the duty-zero brake, which is gated on the speed setpoint being
                               under this threshold (mcpwm_foc.c, "Brake when set ERPM is below
                               min ERPM"). That brake is what finishes a stop.
                               ⚠️ The dead-band/breakaway metric was NOT usable at any setting:
                               stiction is larger than the release band and the spread within
                               one setting exceeded the spread between settings.)
    l_current_min     -25     (motor-side braking current. ⛔⛔ DO NOT CHASE THE HARD NEUTRAL BRAKE
                               WITH THIS -- IT IS NOT THE LEVER. MEASURED 2026-09-14.
                               Taken -25 -> -15 -> -6 chasing a neutral stick that hard-braked; the
                               operator reported NO FELT DIFFERENCE at any setting, and the bench
                               run explains why:
                               🔑🔑 ON A STAND, PEAK BRAKING CURRENT IS ONLY -3.5 to -4.6 A across
                               all four wheels (full-rate log, 99.3 Hz, 9 stop events). Every limit
                               tried -- -25, -15, -6 -- sits ABOVE that, so NONE OF THEM EVER BIND.
                               Drive current peaked +11.7 to +20.3 A, so the drive side is fine.
                               ⚠️ MEASURE AT FULL RATE: brake_run_record.py writes its CSV on a
                               0.2 s timer (5 Hz) while esc_status arrives at ~98 Hz, so it keeps
                               ~1 sample in 20 and CANNOT see a spike inside a 0.4 s stop. The
                               5 Hz pass and the 99 Hz pass happened to agree here, but only the
                               second one is evidence. Use diag/brake_fullrate.py.
                               🔴 THE STAND DOES NOT REPRODUCE THE SYMPTOM: those stops were
                               1.3-2.7 s coast-downs from ~1265 rpm with MEAN current POSITIVE
                               (+0.7 to +1.1 A) -- the motor gently driving, not braking. With no
                               vehicle mass there is no kinetic energy, the speed error collapses
                               on its own, and the controller never demands real braking current.
                               ⏭ THE HARD STOP IS STILL UNDIAGNOSED. It needs a FLOOR run with
                               diag/brake_fullrate.py to catch the peak current with inertia behind
                               it. Until then the duty-0 short-brake theory (see s_pid_min_erpm) is
                               UNCONFIRMED -- do not tune foc_duty_dowmramp_kp/ki on the strength
                               of it.
                               🔑 -25 is also the squaring-up of FL's -25.8 detection artifact so
                               all four brake identically. ALL FOUR MOVE TOGETHER or braking yaws.
                               ⚠️ The 09-13 floor figures 0.52 s / 0.19 m / 1.28 m/s² are the ONLY
                               floor brake data and predate all of this; the collision reflex's
                               0.69 m forward clearance is sized against them.)
    s_pid_ramp_erpms_s 20000  (setpoint slew. ⛔⛔ LEAVE IT HERE. Tried 20000 -> 2000 on 2026-09-13
                               to soften the brake and REVERTED the same evening.
                               ⛔⛔ 2000 WAS REJECTED ON THE FLOOR: it did soften the stop, but the
                               rover went SLUGGISH OFF THE LINE -- "takes more seconds to respond".
                               🔴🔴 AND THE REAL REASON IT CANNOT BE LOWERED: THIS IS A
                               DIFFERENTIAL (SKID-STEER) DRIVE. A turn IS a speed difference
                               between the two sides, so the ramp limits how fast the sides can
                               DIVERGE -- it throttles YAW ONSET, not just forward acceleration.
                               A slow ramp means every turn goes long. That is control authority,
                               not comfort. (operator, 2026-09-13)
                               🔑🔑 THE RAMP IS SYMMETRIC -- PROVEN, NOT ASSUMED: foc_math.c:504
                               calls utils_step_towards(), and util/utils_math.h:131 applies the
                               SAME step magnitude in both directions (+= step / -= step, no
                               direction test). ONE number for both. ⛔ It CANNOT give a soft stop
                               AND a snappy launch. Stop trying to tune asymmetry into it.
                               📏 At 1 m/s (~1795 true ERPM): 20000 = 0.09 s (11 m/s², never binds,
                               so current/grip sets the feel) · 5000 = 0.36 s · 2000 = 0.90 s
                               (1.1 m/s², BINDS BOTH WAYS -- the sluggishness).
                               🔑 WHY 20000: set 2026-09-12 with the RPM-mode template for the
                               OPPOSITE complaint, LATE STOPS -- deliberately beyond tyre grip so
                               the SETPOINT never limits a stop. Stock is 5000.
                               🔑 In RPM mode neutral is not "no torque", it is "hold 0 ERPM" -- an
                               ACTIVE stop. l_current_min caps how hard it pulls; only this ramp
                               changes how abruptly zero is DEMANDED, and it cannot be lowered.
                               ⛔ cc_ramp_step_max and m_duty_ramp_step are NOT usable brake ramps
                               -- referenced ONLY in mcpwm.c, the BLDC driver; this rover runs FOC,
                               so both are DEAD parameters here.
                               ⏭ THE ONE UNTESTED ESC-SIDE BRAKE LEVER IS foc_duty_dowmramp_kp (50)
                               / _ki (1000): they appear at exactly two lines in the firmware, both
                               inside the duty-control PI, and for this rover the ONLY way into
                               duty-control is the duty-0 short brake at neutral -- so they are
                               brake-path-only and cannot touch acceleration or yaw. ⚠️ UNTESTED
                               AND UNCONFIRMED: the stand run could not show the short brake at all
                               (see l_current_min). Get a FLOOR measurement first.
                               ⏭ Asymmetry needs PX4: RO_ACCEL_LIM / RO_DECEL_LIM are SEPARATE
                               params, the only way to soften the stop while leaving the launch
                               and the turn-in alone. ⚠️ Both pinned at -1 because they slew the
                               MANUAL STICK and that caused a wall hit 2026-08-14 -- operator
                               call, not a quiet change.)
    uavcan_raw_mode   3       (RPM; left alone if already 3)

Every write is verified by reading the config back and diffing. A mismatch aborts.

ESC address -> wheel: 10 = FR | 11 = FL | 12 = RR | 13 = RL
"""
import argparse
import datetime
import pathlib
import re
import shutil
import subprocess
import sys

VESC_TOOL = '/home/roz/vesc_tool_build/build/lin/vesc_tool_7.01'
LIVE = pathlib.Path('/home/roz/codex-work/bldc_can/configs_live')
WHEEL = {10: 'FR', 11: 'FL', 12: 'RR', 13: 'RL'}

TARGET_MC = {'s_pid_kp': '0.008', 'l_in_current_min': '-10', 's_pid_min_erpm': '50',
             'l_current_min': '-25', 's_pid_ramp_erpms_s': '20000'}
TARGET_APP = {'uavcan_raw_mode': '3'}

# Values that must already match across the set. Not changed here -- only reported, because a
# difference means that ESC never got the September migration and needs a look, not a silent fix.
EXPECT_MC = {'si_motor_poles': '14', 'l_max_duty': '0.95',
             'l_current_max': '25'}
EXPECT_APP = {'uavcan_raw_rpm_max': '9000', 'can_mode': '1'}


def run(args, timeout=180):
    r = subprocess.run([VESC_TOOL, '--offscreen'] + args,
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout + r.stderr


def read_conf(port, which, path):
    out = run(['--vescPort', port, f'--get{which}Conf', str(path)])
    if 'Saved XML' not in out:
        sys.exit(f'FAILED to read {which}Conf from {port}:\n{out}')
    return path.read_text()


def get(text, key):
    m = re.search(rf'<{key}>([^<]*)</{key}>', text)
    return m.group(1) if m else None


def put(text, key, value):
    return re.sub(rf'<{key}>[^<]*</{key}>', f'<{key}>{value}</{key}>', text, count=1)


def write_conf(port, which, path):
    out = run(['--vescPort', port, f'--set{which}Conf', str(path)])
    if 'write OK' not in out:
        sys.exit(f'FAILED to write {which}Conf to {port}:\n{out}')


def apply(port, which, path_pre, targets, dry):
    """Read-modify-write-verify one config. Returns list of (key, old, new) actually changed."""
    text = read_conf(port, which, path_pre)
    changes = [(k, get(text, k), v) for k, v in targets.items() if get(text, k) != v]
    for k, _, v in changes:
        if get(text, k) is None:
            sys.exit(f'{k} not present in {which}Conf -- wrong firmware? Aborting.')
    if not changes:
        print(f'  {which}Conf: already at target, nothing to write')
        return []
    if dry:
        for k, o, v in changes:
            print(f'  {which}Conf: WOULD change {k} {o} -> {v}')
        return changes

    new_text = text
    for k, _, v in changes:
        new_text = put(new_text, k, v)
    path_post = pathlib.Path(str(path_pre).replace('_pre.xml', '_post.xml'))
    path_post.write_text(new_text)

    write_conf(port, which, path_post)
    path_rb = pathlib.Path(str(path_pre).replace('_pre.xml', '_readback.xml'))
    read_conf(port, which, path_rb)
    if path_rb.read_text() != new_text:
        sys.exit(f'READBACK MISMATCH on {which}Conf -- the device does NOT hold what we sent.\n'
                 f'Compare {path_post} against {path_rb}. Aborting; do not drive.')
    for k, o, v in changes:
        print(f'  {which}Conf: {k} {o} -> {v}  [verified on device]')
    return changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='/dev/ttyACM0')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--min-erpm', help='override s_pid_min_erpm (experiment: 200 / 50 / 0)')
    a = ap.parse_args()

    if a.min_erpm is not None:
        TARGET_MC['s_pid_min_erpm'] = a.min_erpm
        EXPECT_MC.pop('s_pid_min_erpm', None)
        print(f'\n*** s_pid_min_erpm overridden to {a.min_erpm} for this run ***')

    if not pathlib.Path(VESC_TOOL).exists():
        sys.exit(f'vesc_tool not built at {VESC_TOOL}')
    if not pathlib.Path(a.port).exists():
        sys.exit(f'{a.port} does not exist. Is the ESC powered? Its USB only enumerates '
                 f'when the board has power.')
    LIVE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')

    tmp = LIVE / f'_probe_app_{stamp}.xml'
    app_text = read_conf(a.port, 'App', tmp)
    cid = get(app_text, 'controller_id')
    wheel = WHEEL.get(int(cid), f'UNKNOWN_{cid}')
    print(f'\nconnected ESC: controller_id {cid} = {wheel}\n')
    if wheel.startswith('UNKNOWN'):
        sys.exit('controller_id is not one of 10/11/12/13. Wrong device -- aborting.')

    app_pre = LIVE / f'vesc_appconf_{wheel}_{stamp}_pre.xml'
    mc_pre = LIVE / f'vesc_mcconf_{wheel}_{stamp}_pre.xml'
    shutil.move(tmp, app_pre)
    mc_text = read_conf(a.port, 'Mc', mc_pre)
    print(f'  backed up as-found config to {mc_pre.name} / {app_pre.name}')

    odd = [(k, get(mc_text, k), v) for k, v in EXPECT_MC.items() if get(mc_text, k) != v]
    odd += [(k, get(app_text, k), v) for k, v in EXPECT_APP.items() if get(app_text, k) != v]
    if odd:
        print('\n  ⚠ values that differ from the rest of the set (NOT changed by this tool):')
        for k, o, v in odd:
            print(f'      {k}: {o}  (others: {v})')

    print()
    apply(a.port, 'Mc', mc_pre, TARGET_MC, a.dry_run)
    apply(a.port, 'App', app_pre, TARGET_APP, a.dry_run)

    print(f'\n{wheel} done.' if not a.dry_run else f'\n{wheel}: dry run, nothing written.')
    print('Remaining wheels must get the same treatment before driving -- a mixed set is a '
          'hard yaw, not a drift.')


if __name__ == '__main__':
    main()
