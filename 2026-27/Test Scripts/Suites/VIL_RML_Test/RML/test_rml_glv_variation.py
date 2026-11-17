"""Check reviewed GLV endpoints and power-loss recovery. Scope on lamp return; both lamps connected."""

import pytest
from VIL_RML_Test import check_light, require

pytestmark = pytest.mark.hardware


def test_rml_glv_variation(bench):
    require(bench, 'scope')
    bench.set('hv', 80)
    for v in (bench.c['glv_min'], bench.c['glv_nominal'], bench.c['glv_max']):
        bench.set('glv', v)
        bench.wait(7)
        if v:
            check_light(bench, 'RML', bench.voltage('hv'))
            bench.flash(f'glv_{v}')
    # Below the operating range characterize extinction; require correct recovery.
    down = [i/2 for i in range(int(bench.c['glv_min']*2), -1, -1)]
    for v in down + down[::-1]:
        bench.set('glv', v)
        bench.wait(.5)
        bench.log('brownout_glv_v', bench.voltage('glv'))
    bench.set('glv', bench.c['glv_nominal'])
    bench.wait(7)
    check_light(bench, 'RML', bench.voltage('hv'))
    bench.flash('brownout_recovered')
