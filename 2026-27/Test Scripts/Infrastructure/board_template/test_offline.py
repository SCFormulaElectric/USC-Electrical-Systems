"""Synthetic example only. Replace with this board's real acceptance logic."""
import pytest


def within_limits(measured_v, minimum_v, maximum_v):
    return minimum_v <= measured_v <= maximum_v


@pytest.mark.parametrize('measured_v,accepted', [(12.0, True), (10.0, False), (15.0, False)])
def test_synthetic_acceptance(measured_v, accepted):
    assert within_limits(measured_v, 11.0, 14.4) is accepted
