"""Check VIL during HV decay with GLV on/off. Requires DMM in hv_voltage mode."""

import pytest
from VIL_RML_Test import shutdown

pytestmark = pytest.mark.hardware


def test_vil_shutdown(bench):
    shutdown(bench, 'VIL')
