import math
import tomllib
from pathlib import Path
import pytest
from ..bench import Bench, number, timing, validate, ascii_waveform


def test_scope_block_header():
    assert ascii_waveform('#17'+'0,12,0\n') == [0, 12, 0]
    assert ascii_waveform('0,12,0\n') == [0, 12, 0]
    with pytest.raises(ValueError, match='Truncated'):
        ascii_waveform('#2990,12')


def configuration():
    path = Path(__file__).parents[2]/'bench.example.toml'
    c = tomllib.loads(path.read_text())
    c.update(reviewed=True, glv_min=10, glv_max=14, hv_current_limit=.02,
             glv_current_limit=.3, temperature_limit_c=60)
    for name in ('hv', 'glv'):
        c[name].update(address=name, commands_verified=True)
    return c


@pytest.mark.parametrize('value', ['nan', 'inf', '-inf', '9.9e37'])
def test_invalid_reading(value):
    with pytest.raises(ValueError):
        number(value)


def test_timing():
    samples = [12 if i % 100 < 50 else 0 for i in range(3300)]
    periods, duties = timing(samples, .01, 3)
    assert periods == [1]*32
    assert duties == [.5]*32


def test_missing_transitions():
    with pytest.raises(ValueError, match='30 complete'):
        timing([0]*100, .01, 3)


@pytest.mark.parametrize('key,value', [('reviewed', False), ('hv_current_limit', 0),
    ('hv_max', 405), ('glv_max', 16), ('soak_seconds', 5), ('glv_min', math.nan)])
def test_reject_configuration(key, value):
    c = configuration()
    c[key] = value
    with pytest.raises(ValueError):
        validate(c)


class Resource:
    timeout = None
    def __init__(self, identity):
        self.identity, self.writes, self.closed = identity, [], False
    def query(self, command):
        if command == '*IDN?':
            return self.identity
        if command in ('SOUR:VOLT:PROT?', 'VOLT:PROT? (@2)'):
            return '420' if '62050' in self.identity else '14.5'
        if command in ('SOUR:CURR?', 'CURR? (@2)'):
            return '.02' if '62050' in self.identity else '.3'
        if command.startswith('OUTP?'):
            return '0'
        return '0,"No error"'
    def write(self, command):
        self.writes.append(command)
    def close(self):
        self.closed = True


class Manager:
    def __init__(self, fail=False):
        self.hv = Resource('Chroma,62050E-600P')
        self.glv = Resource('Keysight,EDU36311A')
        self.fail = fail
    def open_resource(self, address):
        if address == 'glv' and self.fail:
            raise TimeoutError('connection failure')
        return getattr(self, address)


def test_cleanup_partial_setup(tmp_path):
    m = Manager(fail=True)
    b = Bench(configuration(), tmp_path, m)
    with pytest.raises(TimeoutError):
        b.connect()
    b.close()
    assert m.hv.writes[-1] == 'OUTP 0'
    assert m.hv.closed


def test_setup_order_and_limits(tmp_path):
    m = Manager()
    b = Bench(configuration(), tmp_path, m)
    try:
        b.connect()
        assert m.hv.writes[:4] == ['OUTP 0', 'OUTP 0', 'SOUR:CURR 0.02', 'SOUR:VOLT 0']
        with pytest.raises(ValueError):
            b.set('hv', 405)
    finally:
        b.close()
    assert m.hv.closed and m.glv.closed


def test_shutdown_attempts_both_on_error(tmp_path):
    m = Manager()
    b = Bench(configuration(), tmp_path, m)
    b.connect()
    def fail(command):
        raise TimeoutError('disconnected')
    m.hv.write = fail
    with pytest.raises(RuntimeError, match='shutdown failed'):
        b.close()
    assert m.glv.writes[-1] == 'OUTP 0, (@2)'
    assert m.hv.closed and m.glv.closed


@pytest.mark.parametrize('identity', ['', '   ', None])
@pytest.mark.parametrize('name', ['hv', 'glv', 'dmm', 'scope', 'generator'])
def test_invalid_identity_rejected_before_connection(tmp_path, identity, name):
    c = configuration()
    c[name].update(address=name, identity=identity)
    with pytest.raises(ValueError, match='identity'):
        Bench(c, tmp_path, Manager())


def test_delay_failure_still_attempts_off_and_closes_both_sources(tmp_path):
    m = Manager()
    b = Bench(configuration(), tmp_path, m)
    b.connect()
    original_write = m.glv.write
    def fail_delay(command):
        original_write(command)
        if command.startswith('OUTP:DEL:FALL'):
            raise TimeoutError('delay command failed')
    m.glv.write = fail_delay
    with pytest.raises(RuntimeError, match='delay command failed'):
        b.close()
    assert m.glv.writes[-2:] == ['OUTP:DEL:FALL 0, (@2)', 'OUTP 0, (@2)']
    assert m.hv.closed and m.glv.closed


def test_setup_clears_stored_glv_shutdown_delay_before_off(tmp_path):
    m = Manager()
    b = Bench(configuration(), tmp_path, m)
    try:
        b.connect()
        assert m.glv.writes[:2] == ['OUTP:DEL:FALL 0, (@2)', 'OUTP 0, (@2)']
    finally:
        b.close()
