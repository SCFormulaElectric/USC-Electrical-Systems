"""Read-only example. Replace/add board procedures after checking bench wiring."""
import pytest


@pytest.mark.hardware
def test_identity(dmm, record_property):
    identity = dmm.identify()
    record_property('instrument_identity', identity)
    assert identity, 'Instrument returned an empty identity'
