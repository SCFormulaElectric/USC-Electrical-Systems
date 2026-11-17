"""Copy into your suite. Wire DMM across the GLV input; source is controlled manually."""
import pytest


@pytest.mark.hardware
def test_glv_voltage(dmm, board_config, record_property):
    limits = board_config['limits']
    voltage_v = dmm.read_voltage_v()
    record_property('glv_voltage_v', voltage_v)
    assert limits['glv_min_v'] <= voltage_v <= limits['glv_max_v'], f'GLV outside operating range: {voltage_v} V'
