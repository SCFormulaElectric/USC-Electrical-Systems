"""Read-only Ethernet discovery: python Infrastructure/discover.py [VISA_ADDRESS ...]."""
import argparse
from contextlib import closing
import json

from .visa import resource_manager


def discover(manager, addresses=()):
    candidates = set(addresses) if addresses else set(manager.list_resources('TCPIP?*::INSTR'))
    found = []
    for address in sorted(candidates):
        try:
            with closing(manager.open_resource(address, open_timeout=2000)) as session:
                session.timeout = 2000
                session.write_termination = '\n'
                session.read_termination = '\n'
                identity = session.query('*IDN?').strip()
            found.append({'address': address, 'identity': identity})
        except Exception as error:
            found.append({'address': address, 'error': str(error)})
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('addresses', nargs='*', help='Explicit addresses if multicast discovery is blocked')
    args = parser.parse_args()
    try:
        with closing(resource_manager()) as manager:
            found = discover(manager, args.addresses)
    except Exception as error:
        parser.exit(2, f'Discovery failed: {error}\nCheck requirements, network access and instrument remote settings.\n')
    print(json.dumps(found, indent=2))
    if not found:
        print('No Ethernet instruments discovered. Try explicit VISA addresses from their network settings.')


if __name__ == '__main__':
    main()
