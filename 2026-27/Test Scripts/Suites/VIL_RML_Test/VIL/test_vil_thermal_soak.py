"""Attend VIL thermal soaks and hot threshold rechecks. DMM hv_voltage mode; isolated temperature measurement."""

import pytest
from VIL_RML_Test import soak

pytestmark = pytest.mark.hardware


def test_vil_thermal_soak(bench):
    soak(bench, 'VIL', (49, 55, 320, 404))
