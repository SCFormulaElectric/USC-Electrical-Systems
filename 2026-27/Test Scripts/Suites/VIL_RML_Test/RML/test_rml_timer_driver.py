"""Drive isolated U2 RESET from EDU33212A; HV cable physically removed."""

import pytest

pytestmark = pytest.mark.hardware


def test_rml_timer_driver(bench):
    assert bench.observe('HV cable removed; Q4 disconnected from U2 pin 4; generator through 1k to isolated RESET; confirmed?', ['yes','no']) == 'yes'
    assert abs(bench.dmm()) < 1, 'HV present during LV-only injection'
    bench.set('glv', bench.c['glv_nominal'])
    bench.generator(5)
    bench.wait(7)
    bench.flash('timer_enabled')
    assert bench.observe('Both actual lamps flashing?', ['yes','no']) == 'yes'
    bench.generator(0)
    bench.wait(2)
    assert bench.observe('Both lamps now OFF?', ['yes','no']) == 'yes'
