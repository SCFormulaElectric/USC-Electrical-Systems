"""Copy into your suite. Offline tests need no hardware marker or VISA fixtures."""
import pytest


def calculate_power_w(voltage_v: float, current_a: float) -> float:
    """Example board calculation; place reusable calculations in your board helper package."""
    return voltage_v * current_a


@pytest.mark.parametrize('voltage_v,current_a,expected_w', [(12, .1, 1.2), (14.4, .25, 3.6), (11, 0, 0)])
def test_power_calculation(voltage_v, current_a, expected_w):
    assert calculate_power_w(voltage_v, current_a) == pytest.approx(expected_w)
