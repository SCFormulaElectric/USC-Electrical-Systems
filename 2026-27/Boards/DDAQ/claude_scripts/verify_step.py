"""Compare two kicad-cli kicadxml netlists against intent lists.

python verify_step.py before.xml after.xml intent1.json [intent2.json ...]
- every (ref, pin) present in before.xml must keep its net name unless it appears in an intent list
- every intent (ref, pin, net) must hold in after.xml ('NC' = unconnected-*); leading '/' on local nets is ignored
- every pin of a component that is new in after.xml must be covered by an intent entry
"""
import json
import sys
import xml.etree.ElementTree as ET


def load(f):
    r = ET.parse(f).getroot()
    pins = {}
    for n in r.find('nets'):
        for x in n:
            pins[(x.get('ref'), x.get('pin'))] = n.get('name').lstrip('/')
    return pins, {c.get('ref') for c in r.find('components')}


b, rb = load(sys.argv[1])
a, ra = load(sys.argv[2])
intent = [tuple(i) for f in sys.argv[3:] for i in json.load(open(f))]
touched = {(r, p) for r, p, _ in intent}
changed = [(k, b[k], a.get(k)) for k in b if k not in touched and a.get(k) != b[k]]
bad = []
for r, p, n in intent:
    got = a.get((r, p))
    ok = got is not None and (got.startswith('unconnected-') if n == 'NC' else got == n)
    if not ok:
        bad.append((r, p, n, got))
new = sorted(ra - rb)
uncovered = [k for k in a if k[0] in new and k not in touched]
print('removed parts:', sorted(rb - ra))
print('new parts:', new)
print('unintended pin changes:', len(changed), changed[:20])
print('intent entries:', len(intent), 'mismatches:', bad)
print('new-part pins without intent:', uncovered)
sys.exit(1 if (changed or bad or uncovered or (rb - ra)) else 0)
