import pytest
from backend.preflight import preflight


def test_offline_preflight_never_opens_manager(monkeypatch):
    def forbidden(): pytest.fail('Offline preflight must not access VISA')
    monkeypatch.setattr('backend.preflight.resource_manager', forbidden)
    config = {'instruments': {'dmm': {'address':'example','identity':'EDU34450A'}}}
    assert preflight(config) == ['dmm']


def test_missing_address_rejected_before_connect(monkeypatch):
    def forbidden(): pytest.fail('Invalid settings must not access VISA')
    monkeypatch.setattr('backend.preflight.resource_manager', forbidden)
    with pytest.raises(ValueError, match='address'):
        preflight({'instruments': {'dmm': {'identity':'EDU34450A'}}}, connect=True)


def test_readonly_connect_only_queries_identities(monkeypatch):
    events = []
    class Session:
        def query(self, command):
            assert command == '*IDN?'
            return 'KEYSIGHT,EDU34450A'
        def close(self): events.append('session_closed')
    class Manager:
        def open_resource(self, address, **kwargs): return Session()
        def close(self): events.append('manager_closed')
    monkeypatch.setattr('backend.preflight.resource_manager', Manager)
    preflight({'instruments': {'dmm': {'address':'example','identity':'EDU34450A'}}}, connect=True)
    assert events == ['session_closed','manager_closed']
