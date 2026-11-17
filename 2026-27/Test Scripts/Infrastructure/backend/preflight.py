"""Validate board connection settings; optional identity queries never alter outputs."""
from contextlib import ExitStack, closing
from pathlib import Path
import tomllib

from .instruments import EDU36311A
from .visa import instrument, resource_manager, validate_settings


def preflight(config: dict, names: list[str] | None = None, connect: bool = False) -> list[str]:
    tables = config.get('instruments', {})
    selected = names if names is not None else list(tables)
    if not selected:
        raise ValueError('No instruments configured; legacy suites must use their board-specific preflight')
    for name in selected:
        if name not in tables:
            raise ValueError(f'No instruments.{name} table')
        validate_settings(tables[name])
        if name == 'glv_supply':
            EDU36311A.validate_settings(tables[name])
    if connect:
        with ExitStack() as stack:
            manager = stack.enter_context(closing(resource_manager()))
            for name in selected:
                stack.enter_context(instrument(manager, tables[name]))
    return selected


def load_config(path: Path) -> dict:
    with path.open('rb') as f:
        return tomllib.load(f)
