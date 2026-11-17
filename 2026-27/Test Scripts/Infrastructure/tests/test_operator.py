import threading
import pytest

from backend import monitored_input


def test_operator_text_is_returned_while_monitor_runs(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda question: 'yes')
    checks = []
    assert monitored_input('Ready?', check=lambda: checks.append(True), timeout_s=1) == 'yes'
    assert checks


def test_prompt_timeout_and_monitor_failure_abort(monkeypatch):
    release = threading.Event()
    monkeypatch.setattr('builtins.input', lambda question: release.wait(1))
    try:
        with pytest.raises(TimeoutError):
            monitored_input('Ready?', check=lambda: None, timeout_s=.01)
        def fault(): raise RuntimeError('overcurrent')
        with pytest.raises(RuntimeError, match='overcurrent'):
            monitored_input('Ready?', check=fault, timeout_s=1)
    finally:
        release.set()


def test_console_errors_propagate(monkeypatch):
    def no_console(question): raise EOFError('console closed')
    monkeypatch.setattr('builtins.input', no_console)
    with pytest.raises(EOFError): monitored_input('Ready?', check=lambda: None, timeout_s=1)
