"""Check RML during HV decay. DMM hv_voltage mode; both lamps connected."""

import pytest
from VIL_RML_Test import shutdown

pytestmark = pytest.mark.hardware


def test_rml_shutdown(bench):
    shutdown(bench, 'RML')
