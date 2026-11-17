import math
import pytest

from backend import EDU34450A, EDU36311A
from backend.instruments import reading


def settings():
    # Synthetic offline limits; never a certification of a real fixture.
    return dict(reviewed=True, channel=2, voltage_min_v=11., voltage_max_v=14.4,
                current_limit_a=.2, ovp_v=14.8)


class FakeSession:
    def __init__(self, model='EDU36311A'):
        self.model = model
        self.commands = []
        self.values = {'VOLT': 0., 'CURR': 1., 'VOLT:PROT': 33.,
                       'CURR:PROT:STAT': 0., 'CURR:PROT:DEL': 5., 'OUTP': 0.}
        self.fail_write = None
        self.error = '0,"No error"'
        self.closed = False

    def query(self, command):
        self.commands.append(command)
        if command == '*IDN?': return f'KEYSIGHT,{self.model},SERIAL,FW'
        if command == 'SYST:ERR?': return self.error
        if command == 'MEAS:VOLT:DC?': return '12.0'
        key = command.removesuffix(' (@2)').removesuffix('?')
        if key == 'MEAS:VOLT': return str(self.values['VOLT'])
        if key == 'MEAS:CURR': return '.05'
        return str(self.values[key])

    def write(self, command):
        self.commands.append(command)
        if command.startswith(str(self.fail_write)):
            raise OSError('simulated cable fault')
        key, value = command.removesuffix(', (@2)').split(' ', 1)
        self.values[key] = float(value)


def test_dmm_typed_measurement_and_raw_compatibility():
    session = FakeSession('EDU34450A')
    dmm = EDU34450A(session)
    assert dmm.read_voltage_v() == 12
    assert 'EDU34450A' in dmm.query('*IDN?')


@pytest.mark.parametrize('value', ['nan', 'inf', '9.9e37', True])
def test_invalid_measurement(value):
    with pytest.raises(ValueError): reading(value)


def test_dmm_error_is_not_a_valid_reading():
    session = FakeSession('EDU34450A')
    dmm = EDU34450A(session)
    session.error = '-113,"Undefined header"'
    with pytest.raises(RuntimeError, match='Instrument error'):
        dmm.read_voltage_v()


def test_model_mismatch_sends_no_output_commands():
    session = FakeSession('OTHER')
    with pytest.raises(ValueError): EDU36311A(session, settings())
    assert session.commands == ['*IDN?']


@pytest.mark.parametrize('key,value', [('reviewed',False), ('channel',True), ('channel',4),
    ('voltage_max_v',31), ('current_limit_a',0), ('current_limit_a',2),
    ('ovp_v',14), ('voltage_min_v',math.nan)])
def test_supply_limits_fail_before_io(key, value):
    config = settings()
    config[key] = value
    session = FakeSession()
    with pytest.raises(ValueError): EDU36311A(session, config)
    assert not session.commands


def test_supply_never_implicitly_enables_and_reads_measured_units():
    session = FakeSession()
    supply = EDU36311A(session, settings())
    supply.configure()
    supply.set_voltage_v(12)
    assert 'OUTP 1, (@2)' not in session.commands
    assert session.values['CURR'] == .2
    assert session.values['VOLT:PROT'] == 14.8
    assert session.values['CURR:PROT:STAT'] == 1
    assert session.values['CURR:PROT:DEL'] == 0
    supply.output_on()
    assert supply.read_voltage_v() == 12
    assert supply.read_current_a() == .05
    supply.output_off()
    assert session.values['OUTP'] == 0


def test_cannot_enable_before_configuration_or_exceed_board_limits():
    session = FakeSession()
    supply = EDU36311A(session, settings())
    with pytest.raises(RuntimeError): supply.output_on()
    supply.configure()
    previous = list(session.commands)
    with pytest.raises(ValueError): supply.set_voltage_v(15)
    assert session.commands == previous


def test_external_protection_change_blocks_enable():
    session = FakeSession()
    supply = EDU36311A(session, settings())
    supply.configure()
    session.values['CURR'] = 1
    with pytest.raises(RuntimeError, match='current_limit_a'):
        supply.output_on()
    assert 'OUTP 1, (@2)' not in session.commands


def test_rounded_up_current_limit_is_not_silently_accepted():
    session = FakeSession()
    supply = EDU36311A(session, settings())
    supply.configure()
    session.values['CURR'] = .2004
    with pytest.raises(RuntimeError, match='current_limit_a'):
        supply.output_on()
    assert 'OUTP 1, (@2)' not in session.commands


def test_shutdown_still_sends_off_if_delay_command_fails():
    session = FakeSession()
    supply = EDU36311A(session, settings())
    session.fail_write = 'OUTP:DEL:FALL'
    with pytest.raises(RuntimeError, match='shutdown failed'):
        supply.output_off()
    assert 'OUTP 0, (@2)' in session.commands


def test_settle_timeout_is_bounded(monkeypatch):
    session = FakeSession()
    supply = EDU36311A(session, settings())
    ticks = iter([0, 2])
    monkeypatch.setattr('backend.instruments.time.monotonic', lambda: next(ticks))
    with pytest.raises(TimeoutError): supply.wait_for_voltage_v(12, .1, 1)
