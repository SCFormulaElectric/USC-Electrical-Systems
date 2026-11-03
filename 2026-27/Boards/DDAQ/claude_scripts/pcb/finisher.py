"""Close short leftover connections after autorouting (runs under KiCad's python).

python finisher.py board.kicad_pcb drc.json out.kicad_pcb
For every unconnected pair in the DRC report (both item positions known), try in order:
  1. a straight track on a layer both ends are on,
  2. an L route (horizontal-then-vertical or vertical-then-horizontal) on such a layer,
  3. for an F.Cu-only end: a short F.Cu stub to a new via next to it, then 1/2 on an inner/bottom layer.
A candidate is accepted only if every new segment/via keeps CLEAR from every other-net pad, track and via on that
layer (own geometry check; zones are refilled afterwards and give way). Track width = 0.25 mm (power nets that
need more were already handled by pours/planes; note in LAYOUT_NOTES). Max hop length MAXLEN.
Tracks/vias are read from the board file text because this pcbnew SWIG build cannot iterate BOARD tracks.
"""
import json
import math
import re
import sys
import pcbnew

src, drcj, out = sys.argv[1:4]
CLEAR, W, VD, VDR, MAXLEN = 0.22, 0.25, 0.6, 0.3, 12.0
COPPER = ['F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu']   # routable layers (In1/In4 are planes)
MM, TO = pcbnew.FromMM, pcbnew.ToMM

text = open(src, encoding='utf-8').read()
segs, vias = [], []   # segs: (x1,y1,x2,y2,w,layer,net)  vias: (x,y,d,net)
for m in re.finditer(r'\n\t\((segment|via)\b(.*?)\n\t\)', text, re.S):
    body = m.group(2)
    g = lambda k: re.search(r'\(' + k + r' ([^)]*)\)', body)
    net = re.search(r'\(net "([^"]*)"\)', body)
    net = net.group(1) if net else ''
    if m.group(1) == 'segment':
        (x1, y1), (x2, y2) = (map(float, g('start').group(1).split())), (map(float, g('end').group(1).split()))
        lay = re.search(r'\(layer "([^"]+)"\)', body).group(1)
        segs.append((x1, y1, x2, y2, float(g('width').group(1)), lay, net))
    else:
        x, y = map(float, g('at').group(1).split()[:2])
        vias.append((x, y, float(g('size').group(1)), net))
print('parsed segments', len(segs), 'vias', len(vias))

b = pcbnew.LoadBoard(src)
pads = []  # (x0,y0,x1,y1, layers set, net)
for fp in b.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        lay = {n for n in COPPER if p.IsOnLayer(b.GetLayerID(n))}
        pads.append((TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom()), lay, p.GetNetname()))
edge = b.GetBoardEdgesBoundingBox()
EX0, EY0, EX1, EY1 = TO(edge.GetLeft()) + 0.6, TO(edge.GetTop()) + 0.6, TO(edge.GetRight()) - 0.6, TO(edge.GetBottom()) - 0.6


def pt_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L))
    return math.hypot(px - x1 - t * dx, py - y1 - t * dy)


def seg_seg(a, b2):
    return min(pt_seg(a[0], a[1], *b2[:4]), pt_seg(a[2], a[3], *b2[:4]), pt_seg(b2[0], b2[1], *a[:4]),
               pt_seg(b2[2], b2[3], *a[:4])) if not intersect(a, b2) else 0.0


def intersect(a, b2):
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    p1, p2, p3, p4 = a[:2], a[2:4], b2[:2], b2[2:4]
    return (o(p1, p2, p3) * o(p1, p2, p4) < 0) and (o(p3, p4, p1) * o(p3, p4, p2) < 0)


def seg_box(s, bx):
    # distance from segment to axis-aligned box (sampled; boxes are small)
    best = 1e9
    for k in range(21):
        x = s[0] + (s[2] - s[0]) * k / 20; y = s[1] + (s[3] - s[1]) * k / 20
        dx = max(bx[0] - x, 0, x - bx[2]); dy = max(bx[1] - y, 0, y - bx[3])
        best = min(best, math.hypot(dx, dy))
    return best


def seg_ok(s, layer, net, w=W):
    x1, y1, x2, y2 = s
    for v in (x1, x2):
        if not EX0 < v < EX1:
            return False
    for v in (y1, y2):
        if not EY0 < v < EY1:
            return False
    for t in segs:
        if t[5] == layer and t[6] != net and seg_seg(s, t[:4]) < (w + t[4]) / 2 + CLEAR:
            return False
    for v in vias:
        if v[3] != net and pt_seg(v[0], v[1], *s) < (w + v[2]) / 2 + CLEAR:
            return False
    for p in pads:
        if layer in p[4] and p[5] != net and seg_box(s, p[:4]) < w / 2 + CLEAR:
            return False
    return True


def via_ok(x, y, net):
    if not (EX0 < x < EX1 and EY0 < y < EY1):
        return False
    for t in segs:
        if t[6] != net and pt_seg(x, y, *t[:4]) < (VD + t[4]) / 2 + CLEAR:
            return False
    for v in vias:
        if math.hypot(x - v[0], y - v[1]) < (VD + v[2]) / 2 + (CLEAR if v[3] != net else 0.3):
            return False
    for p in pads:
        if p[5] != net and seg_box((x, y, x, y), p[:4]) < VD / 2 + CLEAR:
            return False
    return True


def layers_at(x, y, net):
    """Copper layers where net copper exists at (x, y) (pad, via end, or track end)."""
    L = set()
    for p in pads:
        if p[5] == net and p[0] - 0.01 <= x <= p[2] + 0.01 and p[1] - 0.01 <= y <= p[3] + 0.01:
            L |= p[4]
    for v in vias:
        if v[3] == net and math.hypot(x - v[0], y - v[1]) < v[2] / 2 + 0.01:
            L |= set(COPPER)
    for t in segs:
        if t[6] == net and pt_seg(x, y, *t[:4]) < t[4] / 2 + 0.01:
            L.add(t[5])
    return L


new_segs, new_vias = [], []


def add_seg(s, layer, net):
    segs.append((*s, W, layer, net)); new_segs.append((*s, layer, net))


def try_connect(a, bpt, net, la, lb):
    paths = [[(a[0], a[1], bpt[0], bpt[1])],
             [(a[0], a[1], bpt[0], a[1]), (bpt[0], a[1], bpt[0], bpt[1])],
             [(a[0], a[1], a[0], bpt[1]), (a[0], bpt[1], bpt[0], bpt[1])]]
    for layer in [l for l in COPPER if l in la and l in lb]:
        for path in paths:
            path = [s for s in path if (s[0], s[1]) != (s[2], s[3])]
            if all(seg_ok(s, layer, net) for s in path):
                for s in path:
                    add_seg(s, layer, net)
                return f'{layer} {len(path)}-seg'
    # F.Cu-only end a: stub + via next to it, then route on another layer
    for (p, q, lp, lq) in ((a, bpt, la, lb), (bpt, a, lb, la)):
        if lp - {'F.Cu'} or 'F.Cu' not in lp:
            continue
        for r in (0.8, 1.1, 1.5):
            for k in range(12):
                ang = 2 * math.pi * k / 12
                vx, vy = round(p[0] + r * math.cos(ang), 3), round(p[1] + r * math.sin(ang), 3)
                stub = (p[0], p[1], vx, vy)
                if not via_ok(vx, vy, net) or not seg_ok(stub, 'F.Cu', net):
                    continue
                for layer in [l for l in COPPER if l in lq and l != 'F.Cu']:
                    for path in ([(vx, vy, q[0], q[1])], [(vx, vy, q[0], vy), (q[0], vy, q[0], q[1])],
                                 [(vx, vy, vx, q[1]), (vx, q[1], q[0], q[1])]):
                        path = [s for s in path if (s[0], s[1]) != (s[2], s[3])]
                        if all(seg_ok(s, layer, net) for s in path):
                            add_seg(stub, 'F.Cu', net)
                            vias.append((vx, vy, VD, net)); new_vias.append((vx, vy, net))
                            for s in path:
                                add_seg(s, layer, net)
                            return f'stub+via+{layer}'
    return None


d = json.load(open(drcj))
done = fail = skip = 0
for u in d['unconnected_items']:
    it = u['items']
    if len(it) < 2:
        continue
    m = re.search(r'\[([^\]]+)\]', it[0]['description'])
    if not m:
        continue
    net = m.group(1)
    a = (it[0]['pos']['x'], it[0]['pos']['y']); c = (it[1]['pos']['x'], it[1]['pos']['y'])
    if math.hypot(a[0] - c[0], a[1] - c[1]) > MAXLEN or 'Zone' in it[0]['description'] or 'Zone' in it[1]['description']:
        skip += 1; continue
    la, lc = layers_at(*a, net), layers_at(*c, net)
    if not la or not lc:
        skip += 1; continue
    r = try_connect(a, c, net, la, lc)
    if r:
        done += 1
    else:
        fail += 1

for (x1, y1, x2, y2, layer, net) in new_segs:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1))); t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
    t.SetWidth(MM(W)); t.SetLayer(b.GetLayerID(layer)); t.SetNet(b.FindNet(net)); b.Add(t)
for (x, y, net) in new_vias:
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); v.SetWidth(MM(VD)); v.SetDrill(MM(VDR))
    v.SetNet(b.FindNet(net)); b.Add(v)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print(f'closed {done}, failed {fail}, skipped {skip} (too long / zone-only / position not on copper); '
      f'added {len(new_segs)} segments, {len(new_vias)} vias')
