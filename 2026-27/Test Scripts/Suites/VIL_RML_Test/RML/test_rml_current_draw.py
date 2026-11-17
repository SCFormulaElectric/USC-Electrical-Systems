"""Measure standby, ON/OFF, average and sampled startup current using a low-side LV shunt."""

import pytest
from VIL_RML_Test import require
from VIL_RML_Test import current_statistics

pytestmark = pytest.mark.hardware


def test_rml_current_draw(bench):
    require(bench, 'dmm')
    assert bench.c['dmm']['mode'] == 'glv_shunt', 'Prewire DMM across LV current shunt'
    s = bench.c['scope']
    bench.scope_setup(2, [s['current_channel'], s['startup_channel']], trigger=True)
    bench.scope_start()
    bench.set('glv', bench.c['glv_nominal'])
    bench.scope_wait(10)
    startup, dt = bench.waveform(s['current_channel'], 'startup_current', acquire=False)
    bench.log('startup_sample_interval_s', dt)
    bench.log('startup_sampled_peak_a', max(startup)/bench.c['dmm']['shunt_ohms'])
    bench.review('Startup peak is sampled and bandwidth-limited; compare scope resolution against transient duration')
    bench.wait(7)
    for v in (0, 80):
        bench.set('hv', v)
        for _ in range(30):
            bench.log('glv_current_a', bench.dmm()/bench.c['dmm']['shunt_ohms'])
            bench.wait(.2)
    bench.scope_setup(50, [s['current_channel'], s['lamp_channel']])
    bench.scope_start()
    bench.scope_wait()
    shunt, lamp, dt = bench.paired_capture(s['current_channel'], s['lamp_channel'], 'flashing_current')
    stats = current_statistics([v/bench.c['dmm']['shunt_ohms'] for v in shunt], lamp, s['lamp_on_below'])
    for name,value in stats.items():
        bench.log('glv_'+name, value)
    bench.review('Current measurements require component budget/thermal review; not a compliance assertion')
