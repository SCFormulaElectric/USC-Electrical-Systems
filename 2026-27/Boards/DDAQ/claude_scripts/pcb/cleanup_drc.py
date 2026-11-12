"""Remove offending/dangling tracks and vias listed in a KiCad DRC json (text-level edit of the board).
python cleanup_drc.py board.kicad_pcb drc.json out.kicad_pcb [types...]"""
import json, math, re, sys
src, drcj, out = sys.argv[1:4]
TYPES = set(sys.argv[4:]) or {'via_dangling', 'track_dangling'}
t = open(src, encoding='utf-8').read()
d = json.load(open(drcj))
targets = []   # (kind, net, layer|None, x, y)
for v in d['violations']:
    if v['type'] not in TYPES:
        continue
    for it in v['items']:
        m = re.match(r'(Track|Via) \[([^\]]*)\](?: on ([A-Za-z0-9.]+))?', it['description'])
        if not m:
            continue
        if v['type'] in ('clearance', 'copper_edge_clearance') and m.group(2) in ('GND',):
            continue
        targets.append((m.group(1), m.group(2), m.group(3), it['pos']['x'], it['pos']['y']))
def segdist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L))
    return math.hypot(px - (x1 + u * dx), py - (y1 + u * dy))
removed = []
def keep(m):
    blk = m.group(0)
    net = re.search(r'\(net "([^"]*)"\)', blk); net = net.group(1) if net else ''
    if blk.lstrip().startswith('(via'):
        x, y = map(float, re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', blk).groups())
        for k, n, l, px, py in targets:
            if k == 'Via' and n == net and math.hypot(px - x, py - y) < 0.02:
                removed.append(('via', net, x, y)); return ''
    else:
        x1, y1 = map(float, re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', blk).groups())
        x2, y2 = map(float, re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', blk).groups())
        lay = re.search(r'\(layer "([^"]+)"\)', blk).group(1)
        for k, n, l, px, py in targets:
            if k == 'Track' and n == net and l == lay and segdist(px, py, x1, y1, x2, y2) < 0.02:
                removed.append(('seg', net, x1, y1)); return ''
    return blk
t2 = re.sub(r'\n\t\((?:segment|via)\n.*?\n\t\)', keep, t, flags=re.S)
open(out, 'w', encoding='utf-8').write(t2)
print('targets', len(targets), 'removed', len(removed), removed[:12])
