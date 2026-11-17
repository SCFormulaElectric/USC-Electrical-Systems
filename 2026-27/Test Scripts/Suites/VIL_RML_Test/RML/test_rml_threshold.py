"""Find RML rising/falling thresholds after lamp check. DMM in hv_voltage mode; both lamps connected."""

import pytest
from VIL_RML_Test import threshold

pytestmark = pytest.mark.hardware


def test_rml_threshold(bench):
    threshold(bench, 'RML')
