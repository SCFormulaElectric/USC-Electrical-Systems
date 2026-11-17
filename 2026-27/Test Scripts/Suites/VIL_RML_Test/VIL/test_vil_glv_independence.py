"""Check VIL with GLV switched off/on at fixed HV. Observe the actual VIL light."""

import pytest
from VIL_RML_Test import check_light

pytestmark = pytest.mark.hardware


def test_vil_glv_independence(bench):
    for v in (60, 320, 404):
        bench.set('hv', v)
        for glv in (0, bench.c['glv_nominal'], 0):
            bench.set('glv', glv)
            check_light(bench, 'VIL', bench.voltage('hv'))
