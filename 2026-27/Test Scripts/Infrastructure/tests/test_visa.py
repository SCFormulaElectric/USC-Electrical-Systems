from types import SimpleNamespace
import sys

import pytest

from backend.visa import instrument, resource_manager


class Session:
    closed = False
    def query(self, command):
        assert command == '*IDN?'
        return 'KEYSIGHT,EDU34450A,SERIAL,FW'
    def close(self):
        self.closed = True


class Manager:
    def __init__(self):
        self.session = Session()
        self.opened = False
    def open_resource(self, address, **kwargs):
        self.opened = True
        return self.session


def test_always_uses_py_backend(monkeypatch):
    seen = []
    monkeypatch.setitem(sys.modules, 'pyvisa', SimpleNamespace(ResourceManager=lambda backend: seen.append(backend)))
    resource_manager()
    assert seen == ['@py']


def test_instrument_closes_after_test_failure():
    manager = Manager()
    with pytest.raises(RuntimeError):
        with instrument(manager, {'address':'TCPIP0::example::inst0::INSTR', 'identity':'EDU34450A'}) as session:
            assert session.timeout == 5000
            raise RuntimeError('measurement failed')
    assert manager.session.closed


def test_wrong_identity_closes_connection():
    manager = Manager()
    with pytest.raises(ValueError, match='Expected'):
        with instrument(manager, {'address':'example', 'identity':'different model'}):
            pytest.fail('Must not yield mismatched instrument')
    assert manager.session.closed


@pytest.mark.parametrize('settings', [
    {'identity':'meter'},
    {'address':'example'},
    {'address':'example','identity':'meter','timeout_ms':float('nan')},
    {'address':'example','identity':'meter','timeout_ms':0},
])
def test_invalid_config_never_opens_instrument(settings):
    manager = Manager()
    with pytest.raises(ValueError):
        with instrument(manager, settings):
            pytest.fail('Invalid settings must not open instrument')
    assert not manager.opened


def test_discovery_queries_and_closes_without_output_commands():
    from backend.discover import discover
    manager = Manager()
    found = discover(manager, ['TCPIP0::example::inst0::INSTR'])
    assert found[0]['identity'].startswith('KEYSIGHT')
    assert manager.session.closed
