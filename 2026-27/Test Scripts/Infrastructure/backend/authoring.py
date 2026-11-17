"""Static suite checks, run before pytest imports board code."""
import ast


def check_suite_hooks(suites):
    """Catch ordinary global-hook mistakes before suite modules execute; not a sandbox."""
    allowed = {'pytest_runtest_setup', 'pytest_runtest_makereport', 'pytest_terminal_summary'}
    for path in sorted(suites.rglob('conftest.py')):
        if any(part in {'.venv', '.git', 'results', '__pycache__'} for part in path.relative_to(suites).parts):
            continue
        tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                names.extend(alias.asname or alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                names.append(node.id)
            for name in names:
                if name.startswith('pytest_') and name not in allowed:
                    raise ValueError(f'{path}:{node.lineno}: {name} is not supported in suites; '
                                     'put global hooks/plugins in Infrastructure. Use local fixtures for board setup.')
