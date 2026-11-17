"""Offline checks for suite-authoring guardrails and the source recipe."""
import importlib.util
from pathlib import Path
import subprocess

import pytest
from backend.authoring import check_suite_hooks
from install import install

INFRA = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('code', [
    'def pytest_collection_modifyitems(items): pass',
    'from somewhere import pytest_sessionstart',
    'pytest_plugins = ["anything"]',
    'from somewhere import hook as pytest_collection_modifyitems',
])
def test_global_hooks_rejected_before_import(tmp_path, code):
    (tmp_path/'conftest.py').write_text(code)
    with pytest.raises(ValueError, match='conftest.py:1:'):
        check_suite_hooks(tmp_path)


def test_local_fixtures_and_existing_hooks_allowed(tmp_path):
    (tmp_path/'conftest.py').write_text('def bench(): pass\ndef pytest_terminal_summary(reporter): pass')
    check_suite_hooks(tmp_path)


def test_installer_combines_requirements_and_checks(tmp_path, monkeypatch):
    for name in ('Board B', 'Board_A'):
        path = tmp_path/'Suites'/name
        path.mkdir(parents=True)
        (path/'requirements.txt').touch()
    calls = []
    monkeypatch.setattr(subprocess, 'run', lambda command, **kw: calls.append((command, kw)))
    install(tmp_path)
    assert calls[0][0][2:4] == ['pip', 'install']
    assert calls[0][0][4:] == ['-r', str(tmp_path/'Infrastructure/requirements.txt'),
        '-r', str(tmp_path/'Suites/Board B/requirements.txt'),
        '-r', str(tmp_path/'Suites/Board_A/requirements.txt')]
    assert calls[1][0][-2:] == ['pip', 'check']
    assert all(kwargs == {'check': True} for _, kwargs in calls)


def test_installer_propagates_failure(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])
    monkeypatch.setattr(subprocess, 'run', fail)
    with pytest.raises(subprocess.CalledProcessError):
        install(tmp_path)


@pytest.mark.parametrize('failure', ['none', 'setup', 'assertion', 'shutdown'])
def test_source_recipe_cleanup(failure, monkeypatch):
    spec = importlib.util.spec_from_file_location('source_recipe', INFRA/'examples/source_fixture.py')
    recipe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recipe)
    events = []
    class Source:
        @staticmethod
        def validate_settings(settings): events.append('validate')
        def __init__(self, session, settings): pass
        def configure(self):
            events.append('configure')
            if failure == 'setup': raise RuntimeError('setup')
        def output_off(self):
            events.append('off')
            if failure == 'shutdown': raise RuntimeError('shutdown')
    monkeypatch.setattr(recipe, 'EDU36311A', Source)
    finalizers = []
    class Request:
        def addfinalizer(self, callback): finalizers.append(callback)
    def exercise():
        try:
            recipe.board_source.__wrapped__({}, lambda name: object(), Request())
            if failure == 'assertion': raise AssertionError('measurement')
        finally:
            try:
                for callback in reversed(finalizers): callback()
            finally:
                events.append('connection_closed')
    if failure == 'none': exercise()
    else:
        with pytest.raises((RuntimeError, AssertionError), match=failure if failure != 'assertion' else 'measurement'):
            exercise()
    assert events == ['validate', 'configure', 'off', 'connection_closed']
