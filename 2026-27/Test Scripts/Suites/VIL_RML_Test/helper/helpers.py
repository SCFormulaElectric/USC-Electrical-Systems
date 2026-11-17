import time
import pytest


def require(b, *names):
    missing = set(names)-b.resources.keys()
    if missing:
        pytest.fail('Missing required instruments: '+', '.join(sorted(missing)))


def check_light(b, kind, voltage):
    from .bench import number
    voltage = number(voltage)
    state = b.observe(kind+' visible state', ['off', 'on', 'flashing'])
    uncertainty = b.c['hv_uncertainty_v']
    if voltage + uncertainty < 50:
        assert state == 'off'
    elif voltage - uncertainty >= 60:
        assert state == ('on' if kind == 'VIL' else 'flashing')
    elif any(voltage - uncertainty < boundary <= voltage + uncertainty for boundary in (50, 60)):
        b.review(f'{kind} voltage uncertainty overlaps a rule boundary; illumination acceptance is inconclusive')
    return state


def threshold(b, kind):
    require(b, 'dmm')
    assert b.c['dmm']['mode'] == 'hv_voltage', 'Threshold test requires DMM across HV input'
    b.set('glv', b.c['glv_nominal'] if kind == 'RML' else 0)
    b.wait(7)
    points = [i/2 for i in range(90, 131)]
    for repeat in range(3):
        for direction in (points, points[::-1]):
            previous = None
            switch = None
            for v in direction:
                b.set('hv', v)
                b.wait(10)
                b.log('sweep_repeat', repeat)
                measured = b.voltage('hv')
                state = check_light(b, kind, measured)
                active = state != 'off'
                if previous is not None and previous[1] != active:
                    if switch is not None:
                        b.review('Multiple transitions/chatter in threshold sweep')
                    lower, upper = sorted((previous[0], measured))
                    u = b.c['hv_uncertainty_v']
                    switch = (lower-u, upper+u)
                    label = 'rising' if direction[0] < direction[-1] else 'falling'
                    b.log(label+'_switch_lower_v', switch[0])
                    b.log(label+'_switch_upper_v', switch[1])
                    if not (50 <= switch[0] <= switch[1] <= 60):
                        b.review('Threshold bracket overlaps rule boundary; finer measurement/uncertainty review required')
                previous = measured, active
            if switch is None:
                b.review('No switching transition found in threshold sweep')


def shutdown(b, kind):
    require(b, 'dmm')
    assert b.c['dmm']['mode'] == 'hv_voltage'
    for glv in ([b.c['glv_nominal'], 0] if kind == 'VIL' else [b.c['glv_nominal']]):
        b.set('glv', glv)
        b.wait(7)
        for v in (404, 320, 80, 61, 60, 59, 55, 50, 49, 25, 0):
            b.set('hv', v)
            b.wait(10)
            check_light(b, kind, b.voltage('hv'))


def soak(b, kind, points):
    b.set('glv', b.c['glv_nominal'] if kind == 'RML' else 0)
    for voltage in points:
        b.set('hv', voltage)
        start = time.monotonic()
        while True:
            b.check()
            check_light(b, kind, b.voltage('hv'))
            temperature = float(b.prompt('Highest measured component temperature C: '))
            from .bench import number
            temperature = number(temperature)
            b.log('temperature_c', temperature, 'manual')
            assert temperature < b.c['temperature_limit_c'], 'Thermal limit exceeded'
            elapsed = time.monotonic()-start
            if elapsed >= b.c['soak_seconds']:
                stable = b.observe('Temperatures stabilized?', ['yes', 'no'])
                if stable == 'yes':
                    break
            b.wait(b.c['temperature_interval_s'])
        if kind == 'VIL':
            threshold(b, kind)
        elif 'scope' in b.resources:
            b.flash(f'hot_{voltage}')
    b.review('Thermal acceptance based on attended point readings, not continuous temperature coverage')
