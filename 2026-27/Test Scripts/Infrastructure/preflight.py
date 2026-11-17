"""Check a board before testing; --connect only sends identity queries."""
import argparse
from pathlib import Path
import sys

sys.pycache_prefix = str(Path(__file__).resolve().parent / '.pycache')

if __name__ == '__main__':
    from backend.preflight import load_config, preflight
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path, help='Board directory, relative to current directory')
    parser.add_argument('--bench', type=Path, help='Explicit configuration override')
    parser.add_argument('--instrument', action='append', dest='names', help='Check only this name; repeat as needed')
    parser.add_argument('--connect', action='store_true', help='Query identities with @py; no output changes')
    args = parser.parse_args()
    path = args.bench or args.board/'bench.toml'
    try:
        names = preflight(load_config(path), args.names, args.connect)
    except Exception as error:
        parser.exit(2, f'Preflight failed: {error}\n')
    print('Configuration valid: '+', '.join(names))
    print('Identity checks passed; no outputs changed.' if args.connect else 'Offline check only; no devices contacted.')
