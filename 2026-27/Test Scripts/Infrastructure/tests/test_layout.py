"""Exercise real pytest discovery in temporary, isolated multi-board projects."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]


def project(tmp_path):
    (tmp_path/'Infrastructure').mkdir()
    (tmp_path/'Suites').mkdir()
    for name in ('pytest.ini', 'run.py'):
        shutil.copyfile(ROOT/'Infrastructure'/name, tmp_path/'Infrastructure'/name)
    shutil.copytree(ROOT/'Infrastructure/backend', tmp_path/'Infrastructure/backend', ignore=shutil.ignore_patterns('__pycache__'))
    for board in ('Board_A_Test', 'Board B Test'):
        suite = tmp_path/'Suites'/board
        shutil.copytree(ROOT/'Infrastructure/board_template', suite, ignore=shutil.ignore_patterns('__pycache__'))
        (suite/'bench.toml').write_text(f'name = "{board}"\n')
        (suite/'test_config.py').write_text(
            'def test_config(board_config):\n'
            f'    assert board_config["name"] == "{board}"\n')
    # Importing PyVISA in a default run would be an unintended hardware-access path.
    (tmp_path/'Infrastructure/pyvisa.py').write_text('raise RuntimeError("Unexpected VISA access")\n')
    return tmp_path


def run(cwd, *args):
    env = dict(os.environ)
    env.pop('PYTEST_ADDOPTS', None)
    root = cwd if (cwd/'Infrastructure').exists() else cwd.parents[1]
    targets = list(args) if args else (['.'] if cwd != root else ['Suites'])
    return subprocess.run([sys.executable, str(root/'Infrastructure/run.py'), '-q', *targets], cwd=cwd,
        env=env, capture_output=True, text=True, timeout=30)


def test_two_boards_same_test_names_and_local_configs(tmp_path):
    result = run(project(tmp_path))
    assert result.returncode == 0, result.stdout+result.stderr
    assert '8 passed, 2 skipped' in result.stdout


def test_run_from_inside_board_folder(tmp_path):
    result = run(project(tmp_path)/'Suites/Board_A_Test')
    assert result.returncode == 0, result.stdout+result.stderr
    assert '4 passed, 1 skipped' in result.stdout


def test_invalid_hardware_config_fails_before_visa(tmp_path):
    result = run(project(tmp_path), '--hardware', 'Suites/Board_A_Test/test_identity.py')
    assert result.returncode != 0
    assert 'Configure instruments.dmm' in result.stdout
    assert 'Unexpected VISA access' not in result.stdout+result.stderr


def test_explicit_config_override(tmp_path):
    root = project(tmp_path)
    config = root/'alternate.toml'
    config.write_text('name = "Board_A_Test"\n')
    result = run(root, 'Suites/Board_A_Test/test_config.py', '--bench', str(config))
    assert result.returncode == 0, result.stdout+result.stderr


@pytest.mark.parametrize('failure', [False, True])
def test_connection_factory_has_no_imports_and_closes_before_manager(tmp_path, failure):
    root = project(tmp_path)
    suite = root/'Suites/Board_A_Test'
    (suite/'bench.toml').write_text('[instruments.dmm]\naddress="example"\nidentity="EDU34450A"\n')
    (suite/'test_factory.py').write_text(
        'import pytest\n'
        '@pytest.mark.hardware\n'
        'def test_factory(connect_instrument):\n'
        '    dmm = connect_instrument("dmm")\n'
        '    assert "EDU34450A" in dmm.query("*IDN?")\n'
        + ('    raise RuntimeError("measurement failed")\n' if failure else ''))
    (root/'Infrastructure/pyvisa.py').write_text(
        'from pathlib import Path\n'
        'log = Path(__file__).with_name("events.txt")\n'
        'def event(text):\n'
        '    with log.open("a") as f: f.write(text+"\\n")\n'
        'class Resource:\n'
        '    def query(self, command): return "KEYSIGHT,EDU34450A,SERIAL,FW"\n'
        '    def close(self): event("instrument_closed")\n'
        'class ResourceManager:\n'
        '    def __init__(self, backend): assert backend == "@py"\n'
        '    def open_resource(self, address, **kwargs): return Resource()\n'
        '    def close(self): event("manager_closed")\n')
    result = run(root, '--hardware', 'Suites/Board_A_Test/test_factory.py')
    assert result.returncode == (2 if failure else 0), result.stdout+result.stderr
    assert (root/'Infrastructure/events.txt').read_text().splitlines() == ['instrument_closed', 'manager_closed']


def test_worked_examples_remain_offline_by_default(tmp_path):
    root = project(tmp_path)
    suite = root/'Suites/Board_A_Test'
    for example in (ROOT/'Infrastructure/examples').glob('test_*.py'):
        shutil.copyfile(example, suite/example.name)
    result = run(root, 'Suites/Board_A_Test')
    assert result.returncode == 0, result.stdout+result.stderr
    assert '7 passed, 4 skipped' in result.stdout


@pytest.mark.parametrize('during_setup', [False, True])
def test_supply_fixture_off_precedes_connection_close_on_failure(tmp_path, during_setup):
    root = project(tmp_path)
    suite = root/'Suites/Board_A_Test'
    (suite/'bench.toml').write_text('[instruments.glv_supply]\naddress="example"\nidentity="EDU36311A"\n')
    (root/'Infrastructure/pyvisa.py').write_text(
        'from pathlib import Path\n'
        'log = Path(__file__).with_name("events.txt")\n'
        'def event(text):\n'
        '    with log.open("a") as f: f.write(text+"\\n")\n'
        'class Resource:\n'
        '    def query(self, command): return "KEYSIGHT,EDU36311A,SERIAL,FW"\n'
        '    def close(self): event("instrument_closed")\n'
        'class ResourceManager:\n'
        '    def __init__(self, backend): assert backend == "@py"\n'
        '    def open_resource(self, address, **kwargs): return Resource()\n'
        '    def close(self): event("manager_closed")\n')
    # Exercise the real fixture finalizer registration independently of SCPI unit tests.
    (suite/'conftest.py').write_text(
        'import pytest\n'
        '@pytest.fixture(autouse=True)\n'
        'def fake_driver(monkeypatch):\n'
        '    from pyvisa import event\n'
        '    import backend.pytest_plugin as plugin\n'
        '    class Supply:\n'
        '        @staticmethod\n'
        '        def validate_settings(settings): pass\n'
        '        def __init__(self, *args): pass\n'
        '        def configure(self):\n'
        '            event("configure")\n'
        + ('            raise RuntimeError("setup failed")\n' if during_setup else '')
        + '        def output_off(self): event("output_off")\n'
        '    monkeypatch.setattr(plugin, "EDU36311A", Supply)\n')
    (suite/'test_supply.py').write_text(
        'import pytest\n@pytest.mark.hardware\n'
        'def test_supply(glv_supply):\n    raise RuntimeError("test failed")\n')
    result = run(root, '--hardware', 'Suites/Board_A_Test/test_supply.py')
    assert result.returncode != 0, result.stdout+result.stderr
    assert (root/'Infrastructure/events.txt').read_text().splitlines() == [
        'configure', 'output_off', 'instrument_closed', 'manager_closed']


def test_multiboard_override_rejected_before_setup(tmp_path):
    root = project(tmp_path)
    result = run(root, 'Suites', '--bench', 'Suites/Board_A_Test/bench.toml')
    assert result.returncode != 0
    assert '--bench requires one board' in result.stdout + result.stderr
    assert 'Unexpected VISA access' not in result.stdout + result.stderr


def test_board_collection_hook_cannot_hide_sibling(tmp_path):
    root = project(tmp_path)
    (root/'Suites/Board_A_Test/conftest.py').write_text(
        'def pytest_collection_modifyitems(items): items.clear()')
    result = run(root)
    assert result.returncode != 0
    assert 'Suite authoring check failed' in result.stdout + result.stderr


def test_offline_summary_is_explicit(tmp_path):
    result = run(project(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'No hardware procedures executed.' in result.stdout
    assert '0 passed, 0 failed, 2 skipped, 0 not executed' in result.stdout


@pytest.mark.parametrize('failure', ['none', 'setup', 'call', 'teardown'])
def test_hardware_summary_counts_and_interruption(tmp_path, failure):
    root = project(tmp_path)
    suite = root/'Suites/Board_A_Test'
    # Fake procedures never open VISA.
    (suite/'conftest.py').write_text(
        'import pytest\n@pytest.fixture\ndef stage():\n' +
        ('    raise RuntimeError("setup")\n' if failure == 'setup' else '') +
        '    yield\n' + ('    raise RuntimeError("teardown")\n' if failure == 'teardown' else ''))
    (suite/'test_simulated.py').write_text(
        'import pytest\npytestmark = pytest.mark.hardware\n'
        'def test_a(stage):\n' + ('    assert False\n' if failure == 'call' else '    pass\n') +
        'def test_b(): pass\n')
    result = run(root, 'Suites/Board_A_Test/test_simulated.py', '--hardware')
    assert result.returncode == (0 if failure == 'none' else 2), result.stdout + result.stderr
    expected = '2 passed, 0 failed, 0 skipped, 0 not executed' if failure == 'none' else '0 passed, 1 failed, 0 skipped, 1 not executed'
    assert expected in result.stdout
