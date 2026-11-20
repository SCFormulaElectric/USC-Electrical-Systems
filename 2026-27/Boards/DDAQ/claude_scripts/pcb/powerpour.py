"""F.Cu copper pours for the LM5175 power stage (runs under KiCad's python).

python powerpour.py board.kicad_pcb
For each net in POUR, a zone on F.Cu covering the convex hull of that net's pads on the power-stage parts
(PARTS), grown by GROW mm. Zones keep normal clearance to other nets, so overlapping hulls are fine; higher
priority wins where two pours compete. Solid pad connection (no thermals) for the power parts.
"""
import sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
MM, TO = pcbnew.FromMM, pcbnew.ToMM
GROW = 0.8
PARTS = {'Q3', 'Q4', 'Q5', 'Q6', 'L8', 'R107', 'C126', 'C127', 'C128', 'C129', 'C130', 'C131', 'C132', 'C133',
         'C134'}
POUR = [('/BB_SW1', 3), ('/BB_SW2', 3), ('/BB_RS', 2), ('/VIN_PROT', 1), ('/+12V_SNS', 1)]


def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts
    def cross(o, a, b2):
        return (a[0] - o[0]) * (b2[1] - o[1]) - (a[1] - o[1]) * (b2[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


fps = {f.GetReference(): f for f in b.GetFootprints()}
made = []
for net, prio in POUR:
    pts = []
    for r in PARTS:
        for p in fps[r].Pads():
            if p.GetNetname() == net:
                bb = p.GetBoundingBox()
                x0, y0, x1, y1 = TO(bb.GetLeft()) - GROW, TO(bb.GetTop()) - GROW, TO(bb.GetRight()) + GROW, TO(bb.GetBottom()) + GROW
                pts += [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    h = hull(pts)
    if len(h) < 3:
        continue
    z = pcbnew.ZONE(b)
    z.SetLayer(pcbnew.F_Cu); z.SetNet(b.FindNet(net)); z.SetAssignedPriority(10 + prio)
    o = z.Outline(); o.NewOutline()
    for x, y in h:
        o.Append(MM(x), MM(y))
    z.SetLocalClearance(MM(0.3)); z.SetMinThickness(MM(0.3))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    b.Add(z); made.append((net, len(h)))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print('pours', made)
