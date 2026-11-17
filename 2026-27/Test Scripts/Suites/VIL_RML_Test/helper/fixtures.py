import datetime
import os
import tomllib
from pathlib import Path

import pytest

from .bench import Bench
from .preflight import preflight


def config_path(config):
    override = config.getoption('--bench')
    return Path(override).resolve() if override else Path(__file__).resolve().parents[1] / 'bench.toml'


def pytest_runtest_setup(item):
    if 'hardware' not in item.keywords or not item.config.getoption('--hardware'):
        return
    path = config_path(item.config)
    if not path.exists():
        pytest.fail(f'Missing {path}. Run helper/setup_bench.py to discover and configure the bench.')
    with path.open('rb') as f:
        config = tomllib.load(f)
    try:
        required = preflight(config, item.originalname)
    except (KeyError, ValueError) as e:
        pytest.fail(f'Preflight: {e}', pytrace=False)
    item._bench_config = config
    item._bench_required = required


@pytest.fixture
def bench(request):
    if request.config.getoption('capture') != 'no':
        pytest.fail('Hardware observations require pytest -s')
    import pyvisa
    bench_path = config_path(request.config)
    config = request.node._bench_config
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    root = Path(config['results_dir'])
    if not root.is_absolute():
        root = bench_path.parent / root
    root.mkdir(parents=True, exist_ok=True)
    lock = root/'.hardware.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        pytest.fail(f'Hardware locked: {lock}. Inspect bench before removing stale lock.')
    os.close(fd)
    rm = b = None
    try:
        rm = pyvisa.ResourceManager('@py')
        b = Bench(config, root/(stamp+'_'+request.node.name), rm, request.node._bench_required)
        request.node.user_properties.append(('result_directory', str(b.directory)))
        b.connect(request.node._bench_required)
        yield b
    finally:
        try:
            if b:
                try:
                    b.close()
                except BaseException:
                    b.summary('ERROR')
                    raise
                status = getattr(request.node, '_procedure_status', 'ERROR')
                b.summary(status)
                request.node.user_properties.append(('acceptance_status',
                    'NEEDS_REVIEW' if status == 'PASS' and b.review_reasons else status))
        finally:
            try:
                if rm:
                    rm.close()
            finally:
                lock.unlink()


def pytest_runtest_makereport(item, call):
    if call.when == 'call':
        item._procedure_status = 'FAIL' if call.excinfo else 'PASS'
    if 'hardware' in item.keywords and call.excinfo and not call.excinfo.errisinstance(pytest.skip.Exception):
        item.session.shouldstop = 'Hardware fault: inspect fixture before another run'


def pytest_terminal_summary(terminalreporter):
    for report in terminalreporter.stats.get('passed', []):
        if 'hardware' in report.keywords and report.nodeid.startswith('Suites/VIL_RML_Test/'):
            terminalreporter.write_line(f'{report.nodeid}: procedure completed; consult summary.json for acceptance and review items')
