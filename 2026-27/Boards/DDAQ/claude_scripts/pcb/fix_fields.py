import sys, xml.etree.ElementTree as ET, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); r = ET.parse(sys.argv[2]).getroot()
fps = {f.GetReference(): f for f in b.GetFootprints()}
ds = bom = 0
for c in r.find('components'):
    fp = fps.get(c.get('ref'))
    if fp is None:
        continue
    d = (c.findtext('datasheet') or '').strip()
    d = '' if d == '~' else d
    if fp.GetFieldText('Datasheet') != d:
        fp.SetField('Datasheet', d); f = fp.GetField('Datasheet'); f.SetVisible(False); ds += 1
    excl = any(p.get('name') == 'exclude_from_bom' for p in c.iter('property'))
    if excl != fp.IsExcludedFromBOM():
        fp.SetExcludedFromBOM(excl); bom += 1
b.Save(sys.argv[1]); print('datasheet fields set', ds, ' BOM flags fixed', bom)
