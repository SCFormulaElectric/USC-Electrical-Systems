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
REGIONS = [  # (layer, net, polygon)
    ('In1.Cu', 'GND', [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]),
    ('In2.Cu', '/VIN_PROT', [(X0, Y0), (119 - G, Y0), (119 - G, Y1), (X0, Y1)]),
    ('In2.Cu', '/+12V_SNS', [(119 + G, Y0), (141 - G, Y0), (141 - G, 86 - G), (119 + G, 86 - G)]),
    ('In2.Cu', '/+7V', [(119 + G, 86 + G), (141 + G, 86 + G), (141 + G, 92 + G), (198 + G, 92 + G), (198 + G, 92 + G),
                        (X1, 92 + G), (X1, Y1), (198 + G, Y1), (198 + G, 112 - G), (119 + G, 112 - G)]),
    ('In2.Cu', '+3.3V', [(141 + G, Y0), (X1, Y0), (X1, 92 - G), (141 + G, 92 - G)]),
    ('In2.Cu', 'GND', [(119 + G, 112 + G), (198 - G, 112 + G), (198 - G, Y1), (119 + G, Y1)]),
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
