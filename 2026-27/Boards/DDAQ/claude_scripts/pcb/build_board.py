"""Scripted 'Update PCB from Schematic' for a fresh layout (runs under KiCad's python with pcbnew).

python build_board.py <template.kicad_pcb> <netlist.xml> <out.kicad_pcb> <kicad_footprint_dir>

- keeps the template's stackup, design rules and net classes; removes every footprint, track, zone and drawing
- loads each schematic part's footprint (project libs, then KiCad std libs), sets ref/value/fields and the
  schematic link (KIID path) so a later GUI 'Update PCB from Schematic' matches by UUID
- assigns pad nets from the netlist
STANDIN: parts whose footprint library is not available here get a stand-in footprint with the same pad numbers;
their FPID is the stand-in's, so a GUI update on a machine with the real library swaps them in place.
"""
import os
import sys
import xml.etree.ElementTree as ET
import pcbnew

tpl, netxml, out, stddir = sys.argv[1:5]
proj = os.path.dirname(os.path.abspath(tpl))
LIBS = {'JLCImport': f'{proj}/JLCImport.pretty', 'SamacSys_Parts': f'{proj}/SamacSys_Parts.pretty',
        'footprints': f'{proj}/../footprints.pretty'}
STANDIN = {'easyeda2kicad:FILTER-SMD_4P-L3.9-W2.5-BL': 'Inductor_SMD:L_CommonModeChoke_Coilank_ACM3225'}

STRIP = ('footprint', 'segment', 'via', 'arc', 'zone', 'gr_line', 'gr_rect', 'gr_arc', 'gr_circle', 'gr_poly',
         'gr_curve', 'gr_text', 'gr_text_box', 'dimension', 'group', 'image', 'target', 'net', 'generated')


def strip_board(text):
    """Drop every top-level item listed in STRIP (pcbnew's Tracks() is not iterable in this SWIG build)."""
    out, i, n = [], 0, len(text)
    depth = 0
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while text[j] != '"':
                j += 2 if text[j] == '\\' else 1
            out.append(text[i:j + 1]); i = j + 1; continue
        if c == '(':
            if depth == 1:
                k = i + 1
                while text[k] not in ' \t\r\n()':
                    k += 1
                if text[i + 1:k] in STRIP:
                    d, j = 0, i
                    while True:
                        if text[j] == '"':
                            j += 1
                            while text[j] != '"':
                                j += 2 if text[j] == '\\' else 1
                        elif text[j] == '(':
                            d += 1
                        elif text[j] == ')':
                            d -= 1
                            if d == 0:
                                break
                        j += 1
                    i = j + 1
                    while i < n and text[i] in ' \t\r\n':
                        i += 1
                    continue
            depth += 1
        elif c == ')':
            depth -= 1
        out.append(c); i += 1
    return ''.join(out)


clean = out + '.template.kicad_pcb'
open(clean, 'w', encoding='utf-8').write(strip_board(open(tpl, encoding='utf-8').read()))
b = pcbnew.LoadBoard(clean)
os.remove(clean)

root = ET.parse(netxml).getroot()
nets = {}
for n in root.find('nets'):
    ni = pcbnew.NETINFO_ITEM(b, n.get('name'))
    b.Add(ni)
    nets[n.get('name')] = ni
padnet = {}
for n in root.find('nets'):
    for x in n:
        padnet[(x.get('ref'), x.get('pin'))] = nets[n.get('name')]

missing, standins = [], []
for c in root.find('components'):
    ref, val, fpid = c.get('ref'), c.findtext('value'), c.findtext('footprint')
    if fpid in STANDIN:
        standins.append((ref, fpid, STANDIN[fpid]))
        fpid = STANDIN[fpid]
    lib, name = fpid.split(':', 1)
    path = LIBS.get(lib, f'{stddir}/{lib}.pretty')
    if not os.path.isfile(f'{path}/{name}.kicad_mod'):
        missing.append((ref, fpid))
        continue
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        missing.append((ref, fpid))
        continue
    fp.SetFPIDAsString(fpid)
    fp.SetReference(ref)
    fp.SetValue(val or '')
    fields = c.find('fields')
    if fields is not None:
        for f in fields:
            k = f.get('name')
            if k in ('Footprint', 'Datasheet', 'Reference', 'Value') or not f.text:
                continue
            fp.SetField(k, f.text)
            fld = fp.GetField(k)
            if fld:
                fld.SetVisible(False)
    tst = c.find('tstamps')
    uid = (tst.text if tst is not None else c.findtext('tstamp')).split()[0]
    fp.SetPath(pcbnew.KIID_PATH(f'/{uid}'))
    sp = c.find('sheetpath')
    fp.SetSheetname(sp.get('names') if sp is not None else '/')
    fp.SetSheetfile('DDAQ.kicad_sch')
    b.Add(fp)
    for pad in fp.Pads():
        ni = padnet.get((ref, pad.GetNumber()))
        if ni is not None:
            pad.SetNet(ni)
    # parts excluded from BOM / position files in the schematic stay excluded
    for p in c.iter('property'):
        if p.get('name') == 'exclude_from_bom':
            fp.SetExcludedFromBOM(True)

b.BuildConnectivity()
b.Save(out)
print('footprints', len(list(b.GetFootprints())), 'nets', len(nets), 'missing', missing, 'standins', standins)
