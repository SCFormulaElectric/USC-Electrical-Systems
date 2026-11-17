"""Check lamp/controller disconnection recovery. Manual wiring changes only after de-energization and discharge verification."""

import pytest

pytestmark = pytest.mark.hardware


def test_rml_fault_recovery(bench):
    for fault in ('first lamp open', 'second lamp open', 'lamp-check controller disconnected', 'normal wiring'):
        bench.set('hv', 0)
        bench.set('glv', 0)
        bench.observe('Verify discharge, configure '+fault+'; complete?', ['yes'])
        bench.set('glv', bench.c['glv_nominal'])
        bench.set('hv', 80)
        bench.wait(7)
        assert bench.observe('All connected lamps flashing normally?', ['yes', 'no']) == 'yes'
