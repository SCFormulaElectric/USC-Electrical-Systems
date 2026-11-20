"""Assign every part to an anchor (IC / connector / big power part) for placement -> groups.json.

python group.py netlist.xml schpos.json groups.json
- anchors: refs matching ANCHOR prefixes (U, Q, J, USBC, X, L, F1) plus a few explicit ones
- a passive joins the anchor reached by the shortest walk through signal nets (rails = nets with > RAIL_N nodes,
  or named in RAILS, are not walked); ties -> nearest in schematic coordinates
- parts touching only rails (decoupling caps) join the nearest-in-schematic anchor that has a pin on that rail
"""
import collections
import json
import math
import sys
import xml.etree.ElementTree as ET

netxml, schpos, out = sys.argv[1:4]
r = ET.parse(netxml).getroot()
pos = json.load(open(schpos))
RAILS = {'GND', '+3.3V', '+5V', '+7V', '/+12V_SNS', '/VIN_PROT', '+5V_REF', '/+5V_REF', '/SD_VDD'}
RAIL_N = 12
refs = [c.get('ref') for c in r.find('components')]
anchors = {x for x in refs if x[0] in 'UQXJ' or x.startswith(('USBC', 'L', 'F1'))} - {'JP1', 'JP2', 'JP3', 'JP4'}
pin_nets = collections.defaultdict(set)
net_parts = collections.defaultdict(set)
for n in r.find('nets'):
    for x in n:
        pin_nets[x.get('ref')].add(n.get('name'))
        net_parts[n.get('name')].add(x.get('ref'))
rail = {n for n, p in net_parts.items() if len(p) > RAIL_N or n in RAILS}


def sd(a, b):
    pa, pb = pos.get(a), pos.get(b)
    return math.hypot(pa[0] - pb[0], pa[1] - pb[1]) if pa and pb else 1e9


group = {a: a for a in anchors}
for p in refs:
    if p in anchors:
        continue
    # BFS over signal nets
    seen, frontier, found, depth = {p}, [p], [], 0
    while frontier and not found and depth < 4:
        depth += 1
        nxt = []
        for q in frontier:
            for n in pin_nets[q] - rail:
                for o in net_parts[n]:
                    if o in seen:
                        continue
                    seen.add(o)
                    (found if o in anchors else nxt).append(o)
        frontier = nxt
    if found:
        group[p] = min(found, key=lambda a: sd(p, a))
        continue
    rails = pin_nets[p] & rail - {'GND'}
    cands = [a for a in anchors if pin_nets[a] & rails] or list(anchors)
    group[p] = min(cands, key=lambda a: sd(p, a))
members = collections.defaultdict(list)
for p, a in group.items():
    if p != a:
        members[a].append(p)
json.dump({'group': group, 'members': members}, open(out, 'w'), indent=0)
for a in sorted(members, key=lambda a: -len(members[a])):
    print(f'{a:6} {len(members[a]):3}  {" ".join(sorted(members[a]))[:150]}')
