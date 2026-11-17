"""Copy into your suite. Reviewed GLV source fixture + DMM across GLV input required."""
import pytest


@pytest.mark.hardware
def test_glv_sweep(glv_supply, dmm, board_config, record_property):
    limits = board_config['limits']
    # Keep the procedure and acceptance criteria visible in the test.
    for target_v in (limits['glv_min_v'], limits['glv_nominal_v'], limits['glv_max_v']):
        glv_supply.set_voltage_v(target_v)
        glv_supply.output_on()
        glv_supply.wait_for_voltage_v(target_v, limits['settle_tolerance_v'], limits['settle_timeout_s'])
        measured_v = dmm.read_voltage_v()
        record_property(f'glv_at_{target_v}_v', measured_v)
        assert abs(measured_v-target_v) <= limits['settle_tolerance_v'], f'Expected {target_v} V, got {measured_v} V'
    # The fixture also attempts OFF if a preceding command/assertion raises.
    glv_supply.output_off()
