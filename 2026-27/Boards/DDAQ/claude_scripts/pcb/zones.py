"""Add plane zones (runs under KiCad's python). python zones.py board.kicad_pcb [layer:net:priority ...]
Default: In1.Cu solid GND over the whole board (0.5 mm inside the edge). Zones follow the board outline."""
import sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
specs = sys.argv[2:] or ['In1.Cu:GND:0']
MM = pcbnew.FromMM
bb = b.GetBoardEdgesBoundingBox()
x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
for spec in specs:
    layer, net, prio = spec.split(':')
    z = pcbnew.ZONE(b)
    z.SetLayer(b.GetLayerID(layer))
    z.SetNet(b.FindNet(net))
    z.SetAssignedPriority(int(prio))
    o = z.Outline(); o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(MM(x), MM(y))
    z.SetLocalClearance(MM(0.3))
    z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.4))
    b.Add(z)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save(sys.argv[1])
print('zones', [(z.GetLayerName(), z.GetNetname()) for z in b.Zones()])
