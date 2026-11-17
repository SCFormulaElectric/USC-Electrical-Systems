"""Copy into your suite. This example is an UNPOWERED visual inspection; use -s."""
import pytest


@pytest.mark.hardware
def test_visual_inspection(request, record_property):
    if request.config.getoption('capture') != 'no':
        pytest.fail('Manual observation requires -s')
    observation = input('With the board de-energized, does solder inspection pass? [yes/no]: ').strip().lower()
    record_property('inspection_source', 'manual')
    record_property('inspection_observation', observation)
    assert observation == 'yes', f'Inspection did not pass: {observation!r}'
