"""Import a Freerouting session into the board, add GND pours on F/B, refill (runs under KiCad's python).
python import_ses.py board.kicad_pcb routed.ses"""
import sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
ok = pcbnew.ImportSpecctraSES(b, sys.argv[2])
print('import', ok)
MM = pcbnew.FromMM
bb = b.GetBoardEdgesBoundingBox()
pts = [(bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())]
have = {(z.GetFirstLayer(), z.GetNetname()) for z in b.Zones()}
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    if (layer, 'GND') in have:
        continue
    z = pcbnew.ZONE(b)
    z.SetLayer(layer); z.SetNet(b.FindNet('GND')); z.SetAssignedPriority(0)
    o = z.Outline(); o.NewOutline()
    for x, y in pts:
        o.Append(x, y)
    z.SetLocalClearance(MM(0.3)); z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.4))
    b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print('done')
