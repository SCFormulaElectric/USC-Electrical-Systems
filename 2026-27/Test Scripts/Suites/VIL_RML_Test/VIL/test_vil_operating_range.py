"""Check continuous VIL indication from 60 to 404 V. Observe the actual VIL light."""

import pytest
from VIL_RML_Test import check_light

pytestmark = pytest.mark.hardware


def test_vil_operating_range(bench):
    bench.set('glv', 0)
    for v in (60, 80, 320, 360, 404):
        bench.set('hv', v)
        bench.wait(10)
        check_light(bench, 'VIL', bench.voltage('hv'))
