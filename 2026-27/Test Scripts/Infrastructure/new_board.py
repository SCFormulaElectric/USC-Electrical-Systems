"""Create a board suite: python Infrastructure/new_board.py BSPD_Test."""
import argparse
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.pycache_prefix = str(Path(__file__).resolve().parent / '.pycache')


def create_board(name: str, root: Path = ROOT) -> Path:
    """Copy a clean template and local config; never merge with an existing board."""
    reserved = {'con', 'prn', 'aux', 'nul', 'backend', 'pytest', 'pyvisa', 'pyvisa_py',
                'infrastructure', 'suites', 'board_template'}
    reserved.update(f'{prefix}{i}' for prefix in ('com', 'lpt') for i in range(1, 10))
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9 _-]*', name) or name.endswith(' ') or name.casefold() in reserved:
        raise ValueError('Use a board name starting with a letter, containing letters, digits, spaces, _ or -. Avoid reserved names.')
    suites = root/'Suites'
    template = root/'Infrastructure/board_template'
    if not (template/'bench.example.toml').is_file():
        raise FileNotFoundError(f'Board template missing: {template}')
    suites.mkdir(exist_ok=True)
    if any(p.name.casefold() == name.casefold() for p in suites.iterdir()):
        raise FileExistsError(f'A suite already exists with this name: {name}')
    target = suites/name
    shutil.copytree(template, target, ignore=shutil.ignore_patterns(
        '__pycache__', '.pytest_cache', '.pycache', '.venv', 'bench.toml', 'results'))
    shutil.copyfile(target/'bench.example.toml', target/'bench.toml')
    readme = target/'README.md'
    if readme.exists():
        readme.write_text(readme.read_text(encoding='utf-8').replace('# Board tests', f'# {name}', 1), encoding='utf-8')
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', help='Board folder name; quote names containing spaces')
    args = parser.parse_args()
    try:
        target = create_board(args.name)
    except (OSError, ValueError) as error:
        parser.exit(2, f'Could not create board: {error}\n')
    print(f'Created {target}')
    print('Edit bench.toml with actual instrument addresses, then write test_*.py procedures.')
    print('No instruments were contacted or outputs changed. Hardware tests remain opt-in.')


if __name__ == '__main__':
    main()
