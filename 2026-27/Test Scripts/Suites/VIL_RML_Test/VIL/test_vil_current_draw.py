"""Characterize HV input current/power. Prewire rated HV shunt; DMM in hv_shunt mode."""

import pytest
from VIL_RML_Test import require

pytestmark = pytest.mark.hardware


def test_vil_current_draw(bench):
    require(bench, 'dmm')
    assert bench.c['dmm']['mode'] == 'hv_shunt', 'Prewire DMM across rated HV series shunt'
    bench.set('glv', 0)
    for v in (0, 25, 49, 55, 60, 80, 320, 360, 404):
        bench.set('hv', v)
        bench.wait(10)
        current = bench.dmm()/bench.c['dmm']['shunt_ohms']
        bench.log('hv_current_a', current)
        bench.log('hv_power_w', current*bench.voltage('hv'))
    bench.review('HV input power is characterization; individual component budgets require review')
