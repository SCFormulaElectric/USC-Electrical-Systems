"""Incremental 'Update PCB from Schematic' that keeps the existing placement (runs under KiCad's python).

python sync_board.py board.kicad_pcb netlist.xml out.kicad_pcb kicad_footprint_dir NEW_GROUPS_JSON
- every pad gets the net the netlist says (new nets are created)
- parts in the netlist but not on the board are loaded from their library and dropped at the nearest free spot
  next to an anchor part, then added to that anchor's group. NEW_GROUPS_JSON maps new ref -> anchor ref.
- parts on the board but not in the netlist are reported, not deleted (board-only parts like H1-H4 stay).
"""
import json
import math
import os
import sys
import xml.etree.ElementTree as ET
import pcbnew

src, netxml, out, stddir, newmap = sys.argv[1:6]
anchor_of = json.loads(newmap)
proj = os.path.dirname(os.path.abspath(src))
LIBS = {'JLCImport': f'{proj}/JLCImport.pretty', 'SamacSys_Parts': f'{proj}/SamacSys_Parts.pretty',
        'footprints': f'{proj}/../footprints.pretty'}
MM, TO = pcbnew.FromMM, pcbnew.ToMM

b = pcbnew.LoadBoard(src)
fps = {f.GetReference(): f for f in b.GetFootprints()}
root = ET.parse(netxml).getroot()
nets = {}
for n in root.find('nets'):
    ni = b.FindNet(n.get('name'))
    if ni is None:
        ni = pcbnew.NETINFO_ITEM(b, n.get('name')); b.Add(ni)
    nets[n.get('name')] = ni
padnet = {(x.get('ref'), x.get('pin')): nets[n.get('name')] for n in root.find('nets') for x in n}


def rect(fp):
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    return TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom())


def free(r, me):
    for ref, f in fps.items():
        if ref == me:
            continue
        o = rect(f)
        if r[0] < o[2] + 0.5 and r[2] > o[0] - 0.5 and r[1] < o[3] + 0.5 and r[3] > o[1] - 0.5:
            return False
    e = b.GetBoardEdgesBoundingBox()
    return TO(e.GetLeft()) + 1 < r[0] and r[2] < TO(e.GetRight()) - 1 and TO(e.GetTop()) + 1 < r[1] and r[3] < TO(e.GetBottom()) - 1


added, changed = [], 0
groups = {g.GetName(): g for g in b.Groups()}
for c in root.find('components'):
    ref = c.get('ref')
    if ref in fps:
        continue
    lib, name = c.findtext('footprint').split(':', 1)
    fp = pcbnew.FootprintLoad(LIBS.get(lib, f'{stddir}/{lib}.pretty'), name)
    fp.SetFPIDAsString(c.findtext('footprint')); fp.SetReference(ref); fp.SetValue(c.findtext('value') or '')
    fields = c.find('fields')
    for f in (fields if fields is not None else []):
        if f.get('name') not in ('Footprint', 'Datasheet', 'Reference', 'Value') and f.text:
            fp.SetField(f.get('name'), f.text)
            fld = fp.GetField(f.get('name'))
            if fld:
                fld.SetVisible(False)
    ds = (c.findtext('datasheet') or '').strip()
    fp.SetField('Datasheet', '' if ds == '~' else ds)        # parity: footprint Datasheet must match the symbol
    if fp.GetField('Datasheet'):
        fp.GetField('Datasheet').SetVisible(False)
    if any(p.get('name') == 'exclude_from_bom' for p in c.iter('property')):
        fp.SetExcludedFromBOM(True)
    fp.SetPath(pcbnew.KIID_PATH('/' + c.find('tstamps').text.split()[0]))
    fp.SetSheetname('/'); fp.SetSheetfile('DDAQ.kicad_sch')
    fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8))); fp.Reference().SetTextThickness(MM(0.12))
    b.Add(fp); fps[ref] = fp
    a = fps[anchor_of[ref]]; ac = a.GetPosition(); ax, ay = TO(ac.x), TO(ac.y)
    done = False
    for rad in [i * 0.5 for i in range(4, 80)]:
        for k in range(max(8, int(rad * 6))):
            ang = 2 * math.pi * k / max(8, int(rad * 6))
            for rot in (0, 90):
                fp.SetOrientationDegrees(rot)
                fp.SetPosition(pcbnew.VECTOR2I(MM(round((ax + rad * math.cos(ang)) / 0.25) * 0.25),
                                               MM(round((ay + rad * math.sin(ang)) / 0.25) * 0.25)))
                if free(rect(fp), ref):
                    done = True; break
            if done:
                break
        if done:
            break
    for g in groups.values():
        if any(i.GetFriendlyName() and hasattr(i, 'GetReference') and i.GetReference() == anchor_of[ref]
               for i in g.GetItems() if isinstance(i, pcbnew.FOOTPRINT)):
            g.AddItem(fp); break
    added.append((ref, round(TO(fp.GetPosition().x), 2), round(TO(fp.GetPosition().y), 2), done))
for ref, fp in fps.items():
    for p in fp.Pads():
        ni = padnet.get((ref, p.GetNumber()))
        if ni is not None and p.GetNetname() != ni.GetNetname():
            p.SetNet(ni); changed += 1
extra = sorted(set(fps) - {c.get('ref') for c in root.find('components')})
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('added', added, 'pad nets changed', changed, 'on board but not in schematic', extra)
