"""Read-only instrument discovery. Never sends output-control commands."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def discover(rm, addresses=()):
    found = []
    candidates = set(addresses)
    for pattern in ('TCPIP?*::INSTR', 'USB?*::INSTR'):
        try:
            candidates.update(rm.list_resources(pattern))
        except Exception as e:
            found.append({'interface': pattern, 'error': str(e)})
    for address in sorted(candidates):
        try:
            with rm.open_resource(address) as r:
                r.timeout = 2000
                r.write_termination = '\n'
                r.read_termination = '\n'
                identity = r.query('*IDN?').strip()
            found.append({'address': address, 'identity': identity})
        except Exception as e:
            found.append({'address': address, 'error': str(e)})
    return found


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backend', default='@py', choices=['@py'], help='pyvisa-py only (default: @py)')
    p.add_argument('--write-config', action='store_true', help='Create bench.toml with uniquely matched addresses; never overwrite')
    p.add_argument('--address', action='append', default=[], help='Explicit VISA address when discovery is blocked; repeat for each instrument')
    args = p.parse_args()
    import pyvisa
    try:
        with closing(pyvisa.ResourceManager(args.backend)) as rm:
            found = discover(rm, args.address)
    except Exception as e:
        p.exit(2, f'pyvisa-py unavailable: {e}\nInstall requirements.txt; USB also needs libusb/WinUSB. LAN needs no vendor VISA.\n')
    print(json.dumps(found, indent=2))
    if not found:
        print('No instruments discovered. Check connections, VISA drivers and LAN discovery; explicit VISA addresses also work.')
    if args.write_config:
        template = (ROOT/'bench.example.toml').read_text()
        c = tomllib.loads(template)
        for name in ('hv','glv','dmm','scope','generator'):
            matches = [r for r in found if c[name]['identity'].upper() in r.get('identity','').upper()]
            if len(matches) == 1:
                section = template.index('['+name+']')
                pos = template.index('address = ""', section)
                template = template[:pos]+template[pos:].replace('address = ""', 'address = '+json.dumps(matches[0]['address']),1)
        path = ROOT/'bench.toml'
        with path.open('x', encoding='utf-8') as f:
            f.write(template)
        print(f'Created {path}. Limits and command verification still require review. No outputs were changed.')


if __name__ == '__main__':
    main()
