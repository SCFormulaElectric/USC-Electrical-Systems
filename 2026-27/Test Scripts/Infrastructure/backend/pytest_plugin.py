"""Shared opt-in policy and fixtures; no dependency on a particular board."""
from pathlib import Path
from contextlib import ExitStack
import tomllib

import pytest

from .visa import instrument, resource_manager, validate_settings
from .instruments import EDU34450A, EDU36311A

ROOT = Path(__file__).resolve().parents[2]
SUITES = ROOT / 'Suites'


def pytest_addoption(parser):
    parser.addoption('--hardware', action='store_true', help='Explicitly enable hardware tests')
    parser.addoption('--bench', help='Override selected board bench.toml (relative to current directory)')


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    if config.getoption('--hardware') and hasattr(config, 'workerinput'):
        raise pytest.UsageError('Do not run physical instruments in parallel workers')
    boards = {Path(item.path).resolve().relative_to(SUITES).parts[0]
              for item in items if Path(item.path).resolve().is_relative_to(SUITES)}
    if config.getoption('--bench') and len(boards) > 1:
        raise pytest.UsageError('--bench requires one board; selected: ' + ', '.join(sorted(boards)) +
                                '. Select Suites/<board> explicitly.')
    config._hardware_items = {item.nodeid for item in items if item.get_closest_marker('hardware')}
    config._hardware_outcomes = {}
    if not config.getoption('--hardware'):
        for item in items:
            if item.get_closest_marker('hardware'):
                item.add_marker(pytest.mark.skip(reason='Hardware disabled; select a board/test and pass --hardware'))


def pytest_runtest_makereport(item, call):
    if item.get_closest_marker('hardware'):
        outcomes = item.config._hardware_outcomes
        if call.excinfo:
            status = 'skipped' if call.excinfo.errisinstance(pytest.skip.Exception) else 'failed'
            if outcomes.get(item.nodeid) != 'failed':
                outcomes[item.nodeid] = status
        elif call.when == 'call':
            outcomes[item.nodeid] = 'passed'
    if item.get_closest_marker('hardware') and call.excinfo and not call.excinfo.errisinstance(pytest.skip.Exception):
        item.session.shouldstop = 'Hardware procedure failed; inspect the bench before another hardware run'


@pytest.fixture
def board_config(request):
    """Load the selected top-level board folder's local bench.toml."""
    override = request.config.getoption('--bench')
    if override:
        path = Path(override).resolve()
    else:
        relative = Path(request.node.path).resolve().relative_to(SUITES)
        path = SUITES / relative.parts[0] / 'bench.toml'
    if not path.is_file():
        pytest.fail(f'Missing {path}. Copy this board\'s bench.example.toml to bench.toml and set addresses.', pytrace=False)
    try:
        with path.open('rb') as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        pytest.fail(f'Invalid {path}: {e}', pytrace=False)


@pytest.fixture
def connect_instrument(board_config, request):
    """Connect by TOML name; pytest closes every connection after the test."""
    connections = ExitStack()
    manager = None

    def connect(name):
        nonlocal manager
        settings = board_config.get('instruments', {}).get(name, {})
        try:
            validate_settings(settings)
        except ValueError as error:
            pytest.fail(f'Configure instruments.{name}: {error}', pytrace=False)
        if manager is None:
            manager = request.getfixturevalue('visa_rm')
            # Register after the manager, even when the factory is called in a test body.
            request.node.addfinalizer(connections.close)
        return connections.enter_context(instrument(manager, settings))

    return connect


@pytest.fixture
def dmm(connect_instrument) -> EDU34450A:
    """Typed EDU34450A API, configured by instruments.dmm."""
    return EDU34450A(connect_instrument('dmm'))


@pytest.fixture
def glv_supply(board_config, connect_instrument, request) -> EDU36311A:
    """Reviewed EDU36311A channel; output-OFF cleanup registered before configuration."""
    settings = board_config.get('instruments', {}).get('glv_supply', {})
    EDU36311A.validate_settings(settings)
    supply = EDU36311A(connect_instrument('glv_supply'), settings)
    request.addfinalizer(supply.output_off)
    supply.configure()
    return supply


@pytest.fixture
def visa_rm(request):
    """Create the @py manager only for explicitly enabled hardware tests."""
    if not request.node.get_closest_marker('hardware'):
        pytest.fail('Tests using visa_rm must be marked @pytest.mark.hardware', pytrace=False)
    if not request.config.getoption('--hardware'):
        pytest.skip('Hardware disabled; pass --hardware')
    manager = resource_manager()
    try:
        yield manager
    finally:
        manager.close()


def pytest_terminal_summary(terminalreporter):
    config = terminalreporter.config
    selected = getattr(config, '_hardware_items', set())
    outcomes = getattr(config, '_hardware_outcomes', {})
    counts = {status: list(outcomes.values()).count(status) for status in ('passed', 'failed', 'skipped')}
    pending = len(selected - outcomes.keys())
    terminalreporter.write_line('Hardware procedures: ' + ', '.join(f'{n} {key}' for key, n in counts.items()) +
                               f', {pending} not executed. Counts are execution, not board acceptance.')
    if not counts['passed'] and not counts['failed']:
        terminalreporter.write_line('No hardware procedures executed.')
