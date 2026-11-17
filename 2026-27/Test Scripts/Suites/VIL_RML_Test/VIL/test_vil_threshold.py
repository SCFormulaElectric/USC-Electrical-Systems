"""Find VIL rising/falling thresholds. Requires DMM across HV input (hv_voltage mode)."""

import pytest
from VIL_RML_Test import threshold

pytestmark = pytest.mark.hardware


def test_vil_threshold(bench):
    threshold(bench, 'VIL')
