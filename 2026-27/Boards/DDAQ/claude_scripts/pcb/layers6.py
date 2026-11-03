"""Convert the board to 6 copper layers (runs under KiCad's python). python layers6.py board.kicad_pcb
Stackup: F.Cu signal / In1.Cu GND plane / In2.Cu signal / In3.Cu signal / In4.Cu split power / B.Cu signal."""
import sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
b.SetCopperLayerCount(6)
ds = b.GetDesignSettings()
enabled = b.GetEnabledLayers()
for name in ('In3.Cu', 'In4.Cu'):
    enabled.addLayer(b.GetLayerID(name))
b.SetEnabledLayers(enabled)
for name, kind in (('In1.Cu', pcbnew.LT_POWER), ('In2.Cu', pcbnew.LT_SIGNAL), ('In3.Cu', pcbnew.LT_SIGNAL),
                   ('In4.Cu', pcbnew.LT_POWER)):
    b.SetLayerType(b.GetLayerID(name), kind)
b.Save(sys.argv[1])
# the SWIG build does not expose BOARD_STACKUP: drop the old 4-layer (stackup ...) block and let KiCad rebuild
# its default 6-layer stackup on the next load/save
t = open(sys.argv[1], encoding='utf-8').read()
i = t.find('(stackup')
if i >= 0:
    d, j = 0, i
    while True:
        if t[j] == '(':
            d += 1
        elif t[j] == ')':
            d -= 1
            if d == 0:
                break
        j += 1
    t = t[:i] + t[j + 1:]
    open(sys.argv[1], 'w', encoding='utf-8').write(t)
b = pcbnew.LoadBoard(sys.argv[1])
b.Save(sys.argv[1])
print('copper layers', b.GetCopperLayerCount(), [(b.GetLayerName(l), b.GetLayerType(l)) for l in b.GetEnabledLayers().CuStack()])
