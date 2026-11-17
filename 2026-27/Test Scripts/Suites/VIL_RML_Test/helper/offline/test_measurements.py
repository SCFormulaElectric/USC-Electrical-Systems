import json
import pytest
from ..analysis import lamp_check, current_statistics
from ..bench import Bench
from ..preflight import preflight, requirements
from .test_bench import configuration, Manager


def test_startup_excludes_unpowered_low_return():
    ref = [0]*100 + [12]*900
    lamp = [0]*100 + [12]*20 + [0]*300 + [12]*580
    delay, duration = lamp_check(lamp, ref, .01, 3, 6)
    assert delay == pytest.approx(.2)
    assert duration == pytest.approx(3)


def test_startup_already_on_at_glv_edge():
    delay, duration = lamp_check([0]*400+[12]*600, [0]*100+[12]*900, .01, 3, 6)
    assert delay == 0
    assert duration == pytest.approx(3)


def test_startup_needs_complete_window():
    with pytest.raises(ValueError, match='did not end'):
        lamp_check([0]*100, [0]*10+[12]*90, .01, 3, 6)


def test_current_split():
    stats = current_statistics([.02,.12,.12,.02], [12,0,0,12], 3)
    assert stats['on_a'] == pytest.approx(.12)
    assert stats['off_a'] == pytest.approx(.02)
    assert stats['average_a'] == pytest.approx(.07)


def test_preflight_missing_scope_no_visa():
    c = configuration()
    with pytest.raises(ValueError, match='scope:.*address'):
        preflight(c, 'test_rml_flash_timing')


def test_preflight_wrong_wiring():
    c = configuration()
    c['dmm']['address'] = 'meter'
    with pytest.raises(ValueError, match='hv_shunt'):
        preflight(c, 'test_vil_current_draw')


def test_timer_never_requires_hv_connection():
    assert 'hv' not in requirements('test_rml_timer_driver')


def test_results_separate_characterization(tmp_path):
    b = Bench(configuration(), tmp_path, Manager())
    b.review('Manual thermal readings')
    b.close()
    b.summary('PASS')
    result = json.loads((tmp_path/'summary.json').read_text())
    assert result['procedure_status'] == 'PASS'
    assert result['acceptance_status'] == 'NEEDS_REVIEW'


def test_prompt_keeps_polling(tmp_path, monkeypatch):
    b = Bench(configuration(), tmp_path, Manager())
    calls = []
    b.check = lambda: calls.append(True)
    monkeypatch.setattr('builtins.input', lambda prompt: 'yes')
    try:
        assert b.prompt('Ready?') == 'yes'
        assert calls
    finally:
        b.close()


def test_scope_acquisition_monitors_sources(tmp_path):
    b = Bench(configuration(), tmp_path, Manager())
    class Scope:
        replies = iter(['0','1','0,"No error"'])
        def query(self, cmd): return next(self.replies)
        def close(self): pass
    b.resources['scope'] = Scope()
    checks = []
    b.check = lambda: checks.append(True)
    try:
        b.scope_wait()
        assert len(checks) == 2
    finally:
        b.close()


def test_backend_is_pyvisa_py():
    pyvisa = pytest.importorskip('pyvisa')
    pytest.importorskip('pyvisa_py')
    rm = pyvisa.ResourceManager('@py')
    try:
        assert type(rm.visalib).__module__.startswith('pyvisa_py')
    finally:
        rm.close()


def test_reject_vendor_backend():
    from ..bench import validate
    c = configuration()
    c['visa_backend'] = '@ivi'
    with pytest.raises(ValueError, match='pyvisa-py'):
        validate(c)


def test_discovery_closes_resources_and_only_queries_identity():
    from ..setup_bench import discover
    class Instrument:
        closed = False
        def __enter__(self): return self
        def __exit__(self, *args): self.closed = True
        def query(self, command):
            assert command == '*IDN?'
            return 'KEYSIGHT,EDU34450A,serial,firmware'
    instrument = Instrument()
    class RM:
        def list_resources(self, pattern):
            if pattern.startswith('USB'):
                raise RuntimeError('USB driver missing')
            return ('TCPIP0::192.0.2.1::inst0::INSTR',)
        def open_resource(self, address): return instrument
    found = discover(RM())
    assert instrument.closed
    assert len(found) == 2
    assert 'identity' in found[1]


def test_legacy_imports_share_the_implementation():
    from backend import ascii_waveform, current_statistics, pulse_timing, pulse_window, reading
    from ..bench import number, ascii_waveform as legacy_ascii, timing
    from ..analysis import current_statistics as legacy_current, pulse_window as legacy_window
    assert number is reading
    assert legacy_ascii is ascii_waveform
    assert timing is pulse_timing
    assert legacy_current is current_statistics
    assert legacy_window is pulse_window


@pytest.mark.parametrize('kind', ['VIL', 'RML'])
@pytest.mark.parametrize('voltage', [50, 60])
def test_boundary_observation_requires_review(tmp_path, kind, voltage):
    from ..helpers import check_light
    b = Bench(configuration(), tmp_path, Manager())
    b.observe = lambda *args: 'off'
    try:
        assert check_light(b, kind, voltage) == 'off'
        b.summary('PASS')
        assert json.loads((tmp_path/'summary.json').read_text())['acceptance_status'] == 'NEEDS_REVIEW'
    finally:
        b.close()


@pytest.mark.parametrize('kind,state,voltage', [('VIL','off',61), ('RML','on',61), ('VIL','on',49)])
def test_unambiguous_wrong_light_state_fails(tmp_path, kind, state, voltage):
    from ..helpers import check_light
    b = Bench(configuration(), tmp_path, Manager())
    b.observe = lambda *args: state
    try:
        with pytest.raises(AssertionError): check_light(b, kind, voltage)
    finally:
        b.close()


def test_timer_preflight_and_connection_do_not_need_hv(tmp_path):
    c = configuration()
    c.pop('hv')
    c['hv_current_limit'] = 0
    for name in ('dmm', 'scope', 'generator'):
        c[name]['address'] = name
    c['generator'].update(commands_verified=True, injection_fixture_verified=True)
    required = preflight(c, 'test_rml_timer_driver')
    opened = []
    class Device:
        def __init__(self, name): self.name = name
        def query(self, command):
            if command == '*IDN?': return c[self.name]['identity']
            if command == 'FUNC?': return 'VOLT:DC'
            if command == 'CURR? (@2)': return str(c['glv_current_limit'])
            if command == 'VOLT:PROT? (@2)': return str(c['glv_ovp'])
            if command.startswith('OUTP?'): return '0'
            return '0,"No error"'
        def write(self, command): pass
        def close(self): pass
    class LVManager:
        def open_resource(self, address):
            assert address != 'hv'
            opened.append(address)
            return Device(address)
    b = Bench(c, tmp_path, LVManager(), required)
    try:
        b.connect(required)
        assert set(opened) == required
        assert b.sources == ('glv',)
    finally:
        b.close()
