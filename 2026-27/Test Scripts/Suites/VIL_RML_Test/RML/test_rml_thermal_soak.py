"""Attend RML thermal soaks. Both lamps; isolated temperature measurement, scope for hot timing recheck."""

import pytest
from VIL_RML_Test import soak

pytestmark = pytest.mark.hardware


def test_rml_thermal_soak(bench):
    soak(bench, 'RML', (60, 320, 404))
