"""Plane fan-out: a short stub + via next to every SMD pad on a plane net (runs under KiCad's python).

python fanout.py board.kicad_pcb
- plane nets: GND (In1, everywhere) and each In2 rail inside its own In2 region (pads outside their region are
  left for the router)
- for each pad, try via positions 0.9-2.2 mm out from the pad centre in 16 directions (outward from the part
  first); a spot is accepted when the via keeps CLEAR from every other-net pad, track and via (bounding-box
  test, conservative) and stays inside the board
- stub width = net class track width (capped at 0.5 mm for small pads); vias 0.6/0.3 (0.8/0.4 for Power_HI)
- new items are locked so the autorouter keeps them
"""
import math
import sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
MM, TO = pcbnew.FromMM, pcbnew.ToMM
CLEAR = 0.25
import os
PWR_LAYER = os.environ.get('DDAQ_PWR_LAYER', 'In2.Cu')
ZONES = {}  # net -> list of power-layer zone outlines
for z in b.Zones():
    if b.GetLayerName(z.GetFirstLayer()) == PWR_LAYER:
        ZONES.setdefault(z.GetNetname(), []).append(z.Outline())
PLANE_NETS = {'GND'} | set(ZONES)
edge = b.GetBoardEdgesBoundingBox()
EX0, EY0, EX1, EY1 = TO(edge.GetLeft()) + 1.0, TO(edge.GetTop()) + 1.0, TO(edge.GetRight()) - 1.0, TO(edge.GetBottom()) - 1.0

obst = []  # (x0, y0, x1, y1, netname, kind)
for fp in b.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        obst.append((TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom()), p.GetNetname(), 'pad'))
    # keep vias out of courtyards of other parts' bodies only where pads are; body itself is fine (via under part)


def box_dist(x, y, o):
    dx = max(o[0] - x, 0, x - o[2]); dy = max(o[1] - y, 0, y - o[3])
    return math.hypot(dx, dy)


def seg_box_dist(x1, y1, x2, y2, o, steps=6):
    return min(box_dist(x1 + (x2 - x1) * k / steps, y1 + (y2 - y1) * k / steps, o) for k in range(steps + 1))


def in_region(net, x, y):
    if net == 'GND':
        return True
    return any(o.Contains(pcbnew.VECTOR2I(MM(x), MM(y))) for o in ZONES.get(net, []))


VIAS = []  # (x, y, diameter) of every via placed here


def via_ok(x, y, d):
    return all(math.hypot(x - a, y - c) >= (d + e) / 2 + 0.3 for a, c, e in VIAS)


added = skipped = 0
fails = []
for fp in b.GetFootprints():
    c = fp.GetPosition(); cx, cy = TO(c.x), TO(c.y)
    for p in fp.Pads():
        net = p.GetNetname()
        if net not in PLANE_NETS or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or not p.IsOnLayer(pcbnew.F_Cu):
            continue
        q = p.GetPosition(); px, py = TO(q.x), TO(q.y)
        ebb = p.GetBoundingBox()
        ew, eh = TO(ebb.GetWidth()), TO(ebb.GetHeight())
        if net == 'GND' and ew >= 2.5 and eh >= 2.5:
            nx, ny = max(1, int((ew - 0.8) // 1.2) + 1), max(1, int((eh - 0.8) // 1.2) + 1)
            for i in range(nx):
                for j in range(ny):
                    vx = px - (nx - 1) * 0.6 + i * 1.2; vy = py - (ny - 1) * 0.6 + j * 1.2
                    if not via_ok(vx, vy, 0.6):
                        continue
                    VIAS.append((vx, vy, 0.6))
                    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy)))
                    v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3)); v.SetNet(p.GetNet()); v.SetLocked(True); b.Add(v)
                    added += 1
            continue
        if not in_region(net, px, py):
            skipped += 1
            continue
        nc = p.GetNetClassName() if hasattr(p, 'GetNetClassName') else ''
        hi = 'Power_HI' in str(nc)
        vd, vdr = (0.8, 0.4) if hi else (0.6, 0.3)
        bb = p.GetBoundingBox(); pw = min(TO(bb.GetWidth()), TO(bb.GetHeight()))
        tw = max(0.25, min(0.5, pw * 0.8))
        base = math.atan2(py - cy, px - cx) if (px, py) != (cx, cy) else 0.0
        done = False
        # near rings only: far vias (2.6+ mm) around fine-pitch ICs block the router's signal escape (tried:
        # pass-1 unrouted went 189 -> 344)
        for r in (0.9, 1.2, 1.5, 1.8, 2.2):
            for k in range(16):
                a = base + (k // 2 + 1) * (math.pi / 8) * (1 if k % 2 else -1) if k else base
                vx, vy = px + r * math.cos(a), py + r * math.sin(a)
                vx, vy = round(vx / 0.05) * 0.05, round(vy / 0.05) * 0.05
                if not (EX0 < vx < EX1 and EY0 < vy < EY1) or not in_region(net, vx, vy) or not via_ok(vx, vy, vd):
                    continue
                ok = True
                for o in obst:
                    if o[4] == net:
                        continue
                    if box_dist(vx, vy, o) < vd / 2 + CLEAR or seg_box_dist(px, py, vx, vy, o) < tw / 2 + CLEAR:
                        ok = False; break
                if not ok:
                    continue
                n = p.GetNet()
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(q); t.SetEnd(pcbnew.VECTOR2I(MM(vx), MM(vy))); t.SetWidth(MM(tw))
                t.SetLayer(pcbnew.F_Cu); t.SetNet(n); t.SetLocked(True); b.Add(t)
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy))); v.SetWidth(MM(vd)); v.SetDrill(MM(vdr))
                v.SetNet(n); v.SetLocked(True); b.Add(v)
                obst.append((vx - vd / 2, vy - vd / 2, vx + vd / 2, vy + vd / 2, net, 'via'))
                VIAS.append((vx, vy, vd))
                for kk in range(5):  # stub as obstacle samples
                    sx, sy = px + (vx - px) * kk / 4, py + (vy - py) * kk / 4
                    obst.append((sx - tw / 2, sy - tw / 2, sx + tw / 2, sy + tw / 2, net, 'trk'))
                added += 1; done = True
                break
            if done:
                break
        if not done:
            fails.append(f'{fp.GetReference()}.{p.GetNumber()}({net})')
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print('vias added', added, 'pads outside their In2 region (left to router)', skipped, 'no room', len(fails))
print(' '.join(fails[:60]))
