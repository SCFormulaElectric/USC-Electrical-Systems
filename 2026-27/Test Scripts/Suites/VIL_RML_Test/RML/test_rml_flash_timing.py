"""Measure flash frequency/duty. Both lamps connected; scope on GLV lamp return with >=50-second record."""

import pytest
from VIL_RML_Test import check_light, require

pytestmark = pytest.mark.hardware


def test_rml_flash_timing(bench):
    require(bench, 'scope')
    bench.set('glv', bench.c['glv_nominal'])
    bench.wait(7)
    for v in (60, 80, 320, 360, 404):
        bench.set('hv', v)
        check_light(bench, 'RML', bench.voltage('hv'))
        bench.flash(f'flash_{v}')
