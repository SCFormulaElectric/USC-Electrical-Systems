"""pyvisa-py connections, without instrument-specific output control."""
from contextlib import contextmanager
import math


def resource_manager():
    import pyvisa
    return pyvisa.ResourceManager('@py')


def validate_settings(settings: dict) -> None:
    """Validate connection settings without importing PyVISA or opening a manager."""
    if not isinstance(settings, dict):
        raise ValueError('Instrument settings must be a TOML table')
    for key in ('address', 'identity'):
        if not isinstance(settings.get(key), str) or not settings[key].strip():
            raise ValueError(f'Set instrument {key} in board bench.toml')
    timeout = settings.get('timeout_ms', 5000)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Instrument timeout_ms must be positive and finite')


@contextmanager
def instrument(manager, settings):
    """Open, identify, yield, close. Never enable/reset/configure a source here."""
    validate_settings(settings)
    address = settings['address'].strip()
    identity = settings['identity'].strip()
    timeout = settings.get('timeout_ms', 5000)
    session = manager.open_resource(address, open_timeout=int(timeout))
    try:
        session.timeout = int(timeout)
        session.write_termination = settings.get('write_termination', '\n')
        session.read_termination = settings.get('read_termination', '\n')
        actual = session.query('*IDN?').strip()
        if identity.casefold() not in actual.casefold():
            raise ValueError(f'Expected {identity!r} at {address}, received {actual!r}')
        yield session
    finally:
        session.close()
