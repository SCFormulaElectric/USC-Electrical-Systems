import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); print('import', pcbnew.ImportSpecctraSES(b, sys.argv[2]))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[3])
