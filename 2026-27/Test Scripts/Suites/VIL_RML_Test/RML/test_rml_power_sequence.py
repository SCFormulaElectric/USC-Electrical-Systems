"""Check repeated GLV-first/HV-first startup. Both lamps and external lamp-check circuit connected."""

import pytest
from VIL_RML_Test import check_light

pytestmark = pytest.mark.hardware


def test_rml_power_sequence(bench):
    for order in (('glv', 'hv'), ('hv', 'glv')):
        for _ in range(10):
            bench.set('hv', 0)
            bench.set('glv', 0)
            for name in order:
                bench.set(name, 80 if name == 'hv' else bench.c['glv_nominal'])
            bench.wait(7)
            check_light(bench, 'RML', bench.voltage('hv'))
    bench.set('hv', 0)
    bench.wait(7)
    check_light(bench, 'RML', bench.voltage('hv'))
    bench.set('hv', 80)
    bench.wait(7)
    check_light(bench, 'RML', bench.voltage('hv'))
    bench.set('glv', 0)
    bench.set('glv', bench.c['glv_nominal'])
    bench.wait(7)
    check_light(bench, 'RML', bench.voltage('hv'))
    bench.review('True simultaneous startup requires an additional verified common-trigger fixture; sequential VISA writes do not establish it')
