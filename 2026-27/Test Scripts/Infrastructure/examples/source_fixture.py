"""Copy this fixture into board conftest.py only for an actual EDU36311A.

Normally use shared glv_supply instead. Other models require their own verified driver.
"""
import pytest
from backend import EDU36311A


@pytest.fixture
def board_source(board_config, connect_instrument, request):
    settings = board_config.get('instruments', {}).get('glv_supply', {})
    EDU36311A.validate_settings(settings)
    source = EDU36311A(connect_instrument('glv_supply'), settings)
    # Register before configuration so partial setup also attempts OFF.
    request.addfinalizer(source.output_off)
    source.configure()
    return source
