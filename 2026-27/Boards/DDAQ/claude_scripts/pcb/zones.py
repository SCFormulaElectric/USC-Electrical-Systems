"""Plane zones (runs under KiCad's python). python zones.py board.kicad_pcb
In1.Cu: solid GND over the whole board.
In2.Cu: split power layer - polygons per rail (REGIONS), 0.6 mm gaps between regions.
"""
import sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.FromMM
bb = b.GetBoardEdgesBoundingBox()
X0, Y0, X1, Y1 = (pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
G = 0.3  # half gap between regions
# Region boundaries for the 130 x 110 board (J3 courtyard x 126.4-203.6, top y 121.9; trackers in x > 208)
VX, PX, BY, AY, JY, TX = 119, 151, 96, 102, 122, 208
REGIONS = [  # (layer, net, polygon)
    ('In1.Cu', 'GND', [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]),
    ('In2.Cu', '/VIN_PROT', [(X0, Y0), (VX - G, Y0), (VX - G, Y1), (X0, Y1)]),
    ('In2.Cu', '/+12V_SNS', [(VX + G, Y0), (PX - G, Y0), (PX - G, BY - G), (VX + G, BY - G)]),
    ('In2.Cu', '/+7V', [(VX + G, BY + G), (PX + G, BY + G), (PX + G, AY + G), (X1, AY + G), (X1, Y1), (TX + G, Y1),
                        (TX + G, JY - G), (VX + G, JY - G)]),
    ('In2.Cu', '+3.3V', [(PX + G, Y0), (X1, Y0), (X1, AY - G), (PX + G, AY - G)]),
    ('In2.Cu', 'GND', [(VX + G, JY + G), (TX - G, JY + G), (TX - G, Y1), (VX + G, Y1)]),
]
for layer, net, poly in REGIONS:
    z = pcbnew.ZONE(b)
    z.SetLayer(b.GetLayerID(layer))
    z.SetNet(b.FindNet(net))
    z.SetAssignedPriority(0)
    o = z.Outline(); o.NewOutline()
    for x, y in poly:
        o.Append(MM(x), MM(y))
    z.SetLocalClearance(MM(0.3)); z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.4))
    b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print('zones', [(z.GetNetname(), b.GetLayerName(z.GetFirstLayer())) for z in b.Zones()])
