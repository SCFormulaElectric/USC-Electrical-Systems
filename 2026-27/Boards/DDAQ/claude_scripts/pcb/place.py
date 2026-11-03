"""Outline, mounting holes and functional placement (runs under KiCad's python with pcbnew).

python place.py <in.kicad_pcb> <groups.json> <out.kicad_pcb> <kicad_footprint_dir>

Board: 120 x 100 mm rectangle, 3 mm corner radius, origin (100, 50). Anchors (ICs, connectors, power parts) get fixed
positions below (ANCHORS); every other part goes to the free spot nearest the anchor pad it shares a net with
(courtyard + CLEAR spacing, inside its block rectangle if possible, else anywhere on the board).
"""
import json
import math
import sys
import pcbnew

src, groups_json, out, stddir = sys.argv[1:5]
b = pcbnew.LoadBoard(src)
G = json.load(open(groups_json))
group = G['group']
# power-stage caps belong to the FETs, not to the rail's nearest IC
group.update({c: 'Q3' for c in ('C126', 'C127', 'C128', 'C129')})
group.update({c: 'Q5' for c in ('C130', 'C131', 'C132', 'C133', 'C134')})
MM = pcbnew.FromMM
import os
GROW = float(os.environ.get('DDAQ_GROW', '0'))   # 0 -> 120 x 100 board, 10 -> 130 x 110
X0, Y0, W, H, RAD = 100.0, 50.0, 120.0 + GROW, 100.0 + GROW, 3.0
# The anchor/block tables below were laid out for 120 x 100. GROW_X/GROW_Y open the board up: everything right of
# SPLIT_X moves right by GROW_X and everything below SPLIT_Y moves down by GROW_Y (power stage stays top-left).
GROW_X, GROW_Y, SPLIT_X, SPLIT_Y = GROW, GROW, 141.0, 86.0
gx = lambda x: x + GROW_X if x >= SPLIT_X else x
gy = lambda y: y + GROW_Y if y >= SPLIT_Y else y
CLEAR = 0.6        # extra spacing between courtyards (mm)
EDGE = 0.8         # courtyard to board edge, except edge connectors

fps = {f.GetReference(): f for f in b.GetFootprints()}

# ---------------- outline ----------------
def seg(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1))); s.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); b.Add(s)


def arc(cx, cy, sx, sy, deg):
    s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_ARC)
    s.SetCenter(pcbnew.VECTOR2I(MM(cx), MM(cy))); s.SetStart(pcbnew.VECTOR2I(MM(sx), MM(sy)))
    s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(deg, pcbnew.DEGREES_T), True)
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); b.Add(s)


x1, y1 = X0 + W, Y0 + H
seg(X0 + RAD, Y0, x1 - RAD, Y0); seg(x1, Y0 + RAD, x1, y1 - RAD)
seg(x1 - RAD, y1, X0 + RAD, y1); seg(X0, y1 - RAD, X0, Y0 + RAD)
arc(x1 - RAD, Y0 + RAD, x1 - RAD, Y0, 90); arc(x1 - RAD, y1 - RAD, x1, y1 - RAD, 90)
arc(X0 + RAD, y1 - RAD, X0 + RAD, y1, 90); arc(X0 + RAD, Y0 + RAD, X0, Y0 + RAD, 90)

# ---------------- mounting holes (board-only, M3, plated, on GND) ----------------
gnd = b.FindNet('GND')
for i, (x, y) in enumerate(((X0 + 4, Y0 + 4), (x1 - 4, Y0 + 4), (X0 + 4, y1 - 4), (x1 - 4, y1 - 4)), 1):
    h = pcbnew.FootprintLoad(f'{stddir}/MountingHole.pretty', 'MountingHole_3.2mm_M3_Pad_Via')
    h.SetReference(f'H{i}'); h.SetValue('M3'); h.SetBoardOnly(True)
    h.SetExcludedFromBOM(True); h.SetExcludedFromPosFiles(True)
    h.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    for p in h.Pads():
        p.SetNet(gnd)
    b.Add(h); fps[h.GetReference()] = h

# ---------------- anchors: ref -> (x, y, rot, block) ----------------
J3Y = y1 - (12.15 + 19.075)     # J3 courtyard (incl. housing) flush with the bottom edge
ANCHORS = {
    'J3': (160.0, J3Y, 0, None),
    # LM5175 4-switch buck-boost: Q3/Q4 = SW1 leg, Q5/Q6 = SW2 leg, L8 between, R107 in the low-side return
    # LM5175 4-switch buck-boost. Q3 (VIN->SW1) and Q4 (SW1->RS) form the buck leg, Q5 (SW2->VOUT) and Q6 (SW2->RS)
    # the boost leg. Q4/Q6 are rotated so both switch nodes face L8 and both low-side sources sit on the outer
    # corners; R107 (sense) stands under L8. Input caps hug Q3's drains, output caps hug Q5's drains.
    'L8': (125.5, 63.0, 0, 'PWR'), 'Q3': (112.0, 61.0, 90, 'PWR'), 'Q4': (112.0, 69.5, 270, 'PWR'),
    'Q5': (139.0, 61.0, 270, 'PWR'), 'Q6': (139.0, 69.5, 90, 'PWR'), 'R107': (125.5, 75.5, 270, 'PWR'),
    'U11': (125.5, 84.5, 0, 'PWR'),
    'U9': (108.0, 90.0, 0, 'PWR'), 'L7': (110.0, 103.0, 0, 'PWR'),
    'U2': (130.0, 90.0, 0, 'PWR'), 'U6': (131.0, 103.0, 0, 'PWR'),
    'Q2': (110.0, 120.0, 0, 'PIN'), 'F1': (110.0, 128.0, 90, 'PIN'),
    'U4': (147.75, 59.0, 0, 'MCU'),
    'U1': (164.0, 72.0, 0, 'MCU'), 'X1': (151.5, 74.0, 90, 'MCU'),
    'USBC1': (158.0, 54.5, 180, 'MCU'), 'U22': (158.0, 61.0, 0, 'MCU'), 'J5': (178.0, 52.6, 0, 'MCU'),
    'U5': (157.0, 96.5, 0, 'ANA'), 'U10': (143.5, 92.0, 0, 'ANA'),
    'U23': (182.0, 86.0, 0, 'SENS'), 'U24': (213.0, 64.0, 0, 'SENS'),
    'J1': (200.0, 54.4, 180, 'SD'), 'Q7': (190.0, 60.0, 0, 'SD'),
    'U3': (192.0, 75.0, 0, 'CAN'), 'U8': (206.0, 75.0, 0, 'CAN'), 'L6': (214.0, 84.0, 90, 'CAN'),
    'U20': (184.0, 99.0, 0, 'FRQ'), 'U21': (193.0, 99.0, 0, 'FRQ'),
    'U12': (206.0, 95.0, 90, 'TRK'), 'U13': (206.0, 104.0, 90, 'TRK'), 'U14': (206.0, 113.0, 90, 'TRK'),
    'U16': (206.0, 122.0, 90, 'TRK'), 'U17': (206.0, 131.0, 90, 'TRK'), 'U18': (206.0, 140.0, 90, 'TRK'),
}
BLOCKS = {  # x0, x1, y0, y1
    'PWR': (100.8, 141.0, 50.8, 111.5), 'PIN': (100.8, 121.0, 111.0, 149.2), 'MCU': (141.0, 186.0, 50.8, 90.0),
    'ANA': (134.0, 179.0, 88.0, 111.5), 'SENS': (175.0, 219.2, 50.8, 92.0), 'SD': (184.0, 219.2, 50.8, 68.0),
    'CAN': (184.0, 219.2, 66.0, 92.0), 'FRQ': (175.0, 203.0, 90.0, 111.5), 'TRK': (198.5, 219.2, 88.0, 149.2),
    'J3': (121.0, 199.0, 100.0, 112.0),
}
ANCHORS = {r: ((gx(x) if r != 'J3' else X0 + W / 2), (gy(y) if r != 'J3' else y), rot, blk)
           for r, (x, y, rot, blk) in ANCHORS.items()}
BLOCKS = {k: (gx(a), gx(b) if b < 219 else x1 - 0.8, gy(c), gy(d) if d < 149 else y1 - 0.8)
          for k, (a, b, c, d) in BLOCKS.items()}
BLOCK_OF = {r: a[3] for r, a in ANCHORS.items()}
BLOCK_OF['J3'] = 'J3'
for r in ('Q3', 'Q4', 'Q5', 'Q6', 'L8', 'R107', 'U11', 'U9', 'L7', 'U2', 'U6'):
    BLOCK_OF[r] = 'PWR'

placed = []   # (ref, x0, y0, x1, y1)


def rect_of(fp):
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    return (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))


def inside_board(r, edge_ok=False):
    m = 0.0 if edge_ok else EDGE
    if r[0] < X0 + m or r[2] > x1 - m or r[1] < Y0 + m or r[3] > y1 - m:
        return False
    # keep out of the rounded corners and the mounting holes (6.5 mm square around each)
    for hx, hy in ((X0 + 4, Y0 + 4), (x1 - 4, Y0 + 4), (X0 + 4, y1 - 4), (x1 - 4, y1 - 4)):
        if r[0] < hx + 3.6 and r[2] > hx - 3.6 and r[1] < hy + 3.6 and r[3] > hy - 3.6:
            return False
    return True


def free(r, me):
    for ref, a, c, e, d in placed:
        if ref != me and r[0] < e + CLEAR and r[2] > a - CLEAR and r[1] < d + CLEAR and r[3] > c - CLEAR:
            return False
    return True


def put(fp, x, y, rot):
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    return rect_of(fp)


errors = []
for ref, (x, y, rot, blk) in ANCHORS.items():
    fp = fps[ref]
    r = put(fp, x, y, rot)
    edge_ok = ref in ('J3', 'USBC1', 'J1', 'J5')
    if not inside_board(r, edge_ok) and not edge_ok:
        errors.append(('anchor outside', ref, [round(v, 2) for v in r]))
    if not free(r, ref):
        errors.append(('anchor overlap', ref, [round(v, 2) for v in r], [p[0] for p in placed if r[0] < p[3] and r[2] > p[1] and r[1] < p[4] and r[3] > p[2]]))
    placed.append((ref, *r))
    fp.SetLocked(False)

# ---------------- satellites ----------------
RAILS = {'GND', '+3.3V', '+5V', '+7V', '/+12V_SNS', '/VIN_PROT', '/SD_VDD'}
claimed = set()


def target(ref, anchor):
    """Anchor pad the part should sit next to: a shared signal net first, else a shared rail pad (unclaimed)."""
    fp, af = fps[ref], fps[anchor]
    mine = {p.GetNetname() for p in fp.Pads() if p.GetNetname()}
    sig = [p for p in af.Pads() if p.GetNetname() in mine and p.GetNetname() not in RAILS]
    if not sig:
        # maybe connected through another satellite already placed (e.g. RC chains): aim at that part
        for o, a in group.items():
            if a == anchor and o in fps and o != ref and any(o == pl[0] for pl in placed):
                shared = mine & {p.GetNetname() for p in fps[o].Pads()} - RAILS
                if shared:
                    c = fps[o].GetPosition(); xy = (pcbnew.ToMM(c.x), pcbnew.ToMM(c.y))
                    return xy[0], xy[1], xy, next(iter(shared))
    cands = sig or [p for p in af.Pads() if p.GetNetname() in mine and p.GetNetname() != 'GND']
    cands = [p for p in cands if (anchor, p.GetNumber()) not in claimed] or cands
    if not cands:
        c = af.GetPosition(); xy = (pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)); return xy[0], xy[1], xy, None
    ac = af.GetPosition()
    p = min(cands, key=lambda p: (p.GetPosition() - ac).EuclideanNorm())
    claimed.add((anchor, p.GetNumber()))
    pp = p.GetPosition()
    # step outward from the anchor centre so the part lands beside the pin, not on the body
    dx, dy = pcbnew.ToMM(pp.x - ac.x), pcbnew.ToMM(pp.y - ac.y)
    n = math.hypot(dx, dy) or 1
    xy = (pcbnew.ToMM(pp.x), pcbnew.ToMM(pp.y))
    return xy[0] + 1.5 * dx / n, xy[1] + 1.5 * dy / n, xy, p.GetNetname()


def pad_dist(fp, net, pxy):
    """Distance from the part's pad on `net` to the target pin (0 if no such pad)."""
    best = None
    for p in fp.Pads():
        if p.GetNetname() == net:
            q = p.GetPosition(); d = math.hypot(pcbnew.ToMM(q.x) - pxy[0], pcbnew.ToMM(q.y) - pxy[1])
            best = d if best is None else min(best, d)
    return best or 0.0


def place_near(ref, tx, ty, blk, pxy, net):
    fp = fps[ref]
    box = BLOCKS.get(blk)
    rots = (0, 90, 180, 270) if fp.GetPadCount() <= 3 else (0, 90)
    for bx, maxr in ((box, 30.0), (None, 70.0)):
        rad = 0.0
        while rad <= maxr:
            n = max(1, int(2 * math.pi * rad / 0.5))
            ring = []
            for k in range(n):
                a = 2 * math.pi * k / n
                x, y = round((tx + rad * math.cos(a)) / 0.25) * 0.25, round((ty + rad * math.sin(a)) / 0.25) * 0.25
                for rot in rots:
                    r = put(fp, x, y, rot)
                    if bx and not (r[0] >= bx[0] and r[2] <= bx[1] and r[1] >= bx[2] and r[3] <= bx[3]):
                        continue
                    if inside_board(r) and free(r, ref):
                        ring.append((pad_dist(fp, net, pxy) if net else 0.0, x, y, rot))
            if ring:
                _, x, y, rot = min(ring)
                placed.append((ref, *put(fp, x, y, rot)))
                return True
            rad += 0.5
    return False


order = sorted((p for p in group if p not in ANCHORS and p in fps),
               key=lambda p: (list(ANCHORS).index(group[p]) if group[p] in ANCHORS else 99, p))
for ref in order:
    anc = group[ref]
    tx, ty, pxy, net = target(ref, anc)
    if not place_near(ref, tx, ty, BLOCK_OF.get(anc), pxy, net):
        errors.append(('could not place', ref))

unplaced = [r for r in fps if r not in {p[0] for p in placed} and not r.startswith('H')]
for r in fps.values():
    r.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
    r.Reference().SetTextThickness(MM(0.12))
b.Save(out)
print('placed', len(placed), 'unplaced', unplaced)
print('\n'.join(map(str, errors)) or 'no errors')
