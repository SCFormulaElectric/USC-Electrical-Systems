"""Plan removal of U1, U5, U8, D11-D18, R18 and their pin stubs/labels, keeping every other net intact."""
import json
import sys
import collections
import xml.etree.ElementTree as ET
from sch import load, find, one

sys.stdout.reconfigure(encoding='utf-8')
REMOVE = ['J2', 'J3', 'J4', 'U15', 'U19', 'C139', 'R113', 'C147', 'C143', 'R117', 'C151', 'F5', 'F6']
R = lambda v: round(float(v), 2)

root = load('backup_before_conn.kicad_sch')
pins = json.load(open('allpins2.json'))

wires, labels, ncs = [], [], []
for c in root:
    if not isinstance(c, list):
        continue
    if c[0] == 'wire':
        a, b = [(R(p[1]), R(p[2])) for p in one(c, 'pts')[1:]]
        wires.append((a, b))
    elif c[0] in ('label', 'global_label', 'hierarchical_label'):
        a = one(c, 'at')
        labels.append((c[0], c[1], (R(a[1]), R(a[2]))))
    elif c[0] == 'no_connect':
        a = one(c, 'at')
        ncs.append((R(a[1]), R(a[2])))

# old nets per pin
net = {}
for n in ET.parse('cold.xml').getroot().find('nets'):
    for x in n:
        net[(x.get('ref'), x.get('pin'))] = n.get('name')

pin_at = collections.defaultdict(list)  # point -> [(ref,pin)]
for ref, ps in pins.items():
    for pn, (_, pt) in ps.items():
        pin_at[tuple(pt)].append((ref, pn))


def on_seg(p, w):
    (x1, y1), (x2, y2) = w
    if x1 == x2 == p[0]:
        return min(y1, y2) <= p[1] <= max(y1, y2)
    if y1 == y2 == p[1]:
        return min(x1, x2) <= p[0] <= max(x1, x2)
    return p in w


removed_wires, removed_labels, removed_pwr, removed_nc, reattach = set(), set(), set(), set(), []
for ref in REMOVE:
    for pn, (_, pt) in pins[ref].items():
        pt = tuple(pt)
        oldnet = net.get((ref, pn), '')
        for l in labels:
            if l[2] == pt:
                removed_labels.add(l)
        for r2, p2 in pin_at[pt]:
            if r2.startswith('#PWR') or r2.startswith('#FLG'):
                removed_pwr.add(r2)
        if pt in ncs:
            removed_nc.add(pt)
        for w in wires:
            if pt not in w:
                continue
            q = w[1] if w[0] == pt else w[0]
            others = [w2 for w2 in wires if w2 != w and on_seg(q, w2)]
            qpins = [(r2, p2) for r2, p2 in pin_at[q] if r2 not in REMOVE]
            real_pins = [x for x in qpins if not x[0].startswith('#')]
            pwr = [x[0] for x in qpins if x[0].startswith('#')]
            qlabels = [l for l in labels if l[2] == q]
            removed_wires.add(w)
            if not others and not real_pins:
                removed_labels.update(qlabels)
                removed_pwr.update(pwr)
            else:
                reattach.append((q, oldnet, ref, pn, len(others), real_pins, [l[1] for l in qlabels], pwr))

print('wires', len(removed_wires), 'labels', len(removed_labels), 'pwr', sorted(removed_pwr), 'nc', len(removed_nc))
print('label names removed:', sorted({l[1] for l in removed_labels}))
print('reattach points (stub far end still connects to something):')
for r in reattach:
    print('  ', r)
json.dump({'wires': sorted(removed_wires), 'labels': sorted(removed_labels), 'pwr': sorted(removed_pwr),
           'nc': sorted(removed_nc), 'reattach': reattach}, open('removal2.json', 'w'))
