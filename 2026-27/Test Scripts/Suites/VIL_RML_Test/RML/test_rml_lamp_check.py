"""Measure external lamp-check timing. Both lamps and external circuit; scope captures GLV startup and return."""

import pytest
from VIL_RML_Test import check_light, require
from VIL_RML_Test import lamp_check

pytestmark = pytest.mark.hardware


def test_rml_lamp_check(bench):
    require(bench, 'scope')
    for v in (0, 49, 60, 404):
        bench.set('glv', 0)
        bench.set('hv', v)
        s = bench.c['scope']
        bench.scope_setup(10, [s['lamp_channel'], s['startup_channel']], trigger=True)
        bench.scope_start()
        bench.set('glv', bench.c['glv_nominal'])
        bench.scope_wait(20)
        lamp, ref, dt = bench.paired_capture(s['lamp_channel'], s['startup_channel'], f'lamp_check_{v}')
        delay, duration = lamp_check(lamp, ref, dt, s['lamp_on_below'], s['startup_threshold'])
        bench.log('lamp_check_delay_s', delay)
        bench.log('lamp_check_duration_s', duration)
        assert 0 <= delay <= 1 and 2 <= duration <= 6
        assert bench.observe('Both lamps continuously lit during check?', ['yes', 'no']) == 'yes'
        check_light(bench, 'RML', bench.voltage('hv'))
