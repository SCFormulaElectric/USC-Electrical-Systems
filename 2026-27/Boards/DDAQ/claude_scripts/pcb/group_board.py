"""Put every part into a named KiCad group by function (runs under KiCad's python).

python group_board.py in.kicad_pcb groups.json out.kicad_pcb out.md [--strip-routing]
groups.json is group.py's output (part -> anchor by net walk). GROUPS below names each functional block and lists
its anchor(s); OVERRIDE moves single parts whose net-walk anchor is not the part they actually serve.
--strip-routing removes all tracks/vias and the F.Cu power pours (placement-tied); the In1/In2 planes stay.
Writes a markdown table of the groups to out.md.
"""
import json
import re
import sys
import pcbnew

src, gj, out, md = sys.argv[1:5]
strip = '--strip-routing' in sys.argv

# name -> anchors (parts whose net-walk satellites join this group)
GROUPS = [
    ('J3 AMPSEAL 35 harness connector', ['J3']),
    ('Input protection: fuse, TVS, reverse-polarity FET (Q2)', ['Q2', 'F1']),
    ('12 V buck-boost LM5175 (U11) + power stage Q3-Q6, L8, R107', ['U11', 'Q3', 'Q4', 'Q5', 'Q6', 'L8']),
    ('7 V buck LMR33630 (U9) + L7', ['U9', 'L7']),
    ('5 V buck TPS563300 (U2) + inductor U6', ['U2', 'U6']),
    ('3.3 V LDO AMS1117 (U4)', ['U4']),
    ('5 V precision reference TPS7A4700 (U10)', ['U10']),
    ('Sensor supply +5V_EXC_L (U12)', ['U12']), ('Sensor supply +5V_EXC_R (U13)', ['U13']),
    ('Sensor supply +5V_EXC_C (U14)', ['U14']), ('Sensor supply +5V_WS_L (U16)', ['U16']),
    ('Sensor supply +5V_WS_R (U17)', ['U17']), ('Sensor supply +5V_WS_C (U18)', ['U18']),
    ('12 V sensor outputs OUT1/OUT2 (PTC fuses + TVS)', []),
    ('IZZE supply (F7, D23, TVS)', []),
    ('ADC ADS8688 (U5) core: decoupling, reference, EXC monitor', ['U5']),
    ('Analog front end AI0-AI7: pull-down, series R, filter C, clamps', []),
    ('Spare analog AI8/AI9 to MCU (PC5/PE8)', []),
    ('Frequency inputs FREQ1/FREQ2 (U20)', ['U20']), ('Frequency inputs FREQ3/FREQ4 (U21)', ['U21']),
    ('CAN1 transceiver (U3) + ESD + split termination JP1', ['U3']),
    ('CAN2 transceiver (U8) + choke L6 + ESD + split termination JP2', ['U8', 'L6']),
    ('MCU STM32G474 (U1) + decoupling, BOOT0, monitors', ['U1']),
    ('16 MHz crystal (X1)', ['X1']),
    ('Status LEDs CAN/FAULT/STAT', []),
    ('Node-ID jumpers JP3/JP4', []),
    ('SWD header (J5)', ['J5']),
    ('USB-C (USBC1) + ESD (U22)', ['USBC1', 'U22']),
    ('microSD (J1) + power switch Q7', ['J1', 'Q7']),
    ('IMU ISM330DHCX (U23)', ['U23']),
    ('Barometer BMP581 (U24)', ['U24']),
]
OVERRIDE = {}
for c in ('C126', 'C127', 'C128', 'C129', 'C130', 'C131', 'C132', 'C133', 'C134', 'R107', 'C124', 'C125'):
    OVERRIDE[c] = '12 V buck-boost LM5175 (U11) + power stage Q3-Q6, L8, R107'
for d, u in (('D33', 'U12'), ('D34', 'U13'), ('D35', 'U14'), ('D36', 'U16'), ('D37', 'U17'), ('D38', 'U18')):
    OVERRIDE[d] = next(n for n, a in GROUPS if a == [u])
for p in ('F3', 'F4', 'D40', 'D41'):
    OVERRIDE[p] = '12 V sensor outputs OUT1/OUT2 (PTC fuses + TVS)'
for p in ('F7', 'D23', 'D39'):
    OVERRIDE[p] = 'IZZE supply (F7, D23, TVS)'
FE = 'Analog front end AI0-AI7: pull-down, series R, filter C, clamps'
for i in range(8):
    for p in (f'R{65 + i}', f'R{73 + i}', f'C{73 + i}'):
        OVERRIDE[p] = FE
for p in ('D11', 'D12', 'D13', 'D14'):
    OVERRIDE[p] = FE
for p in ('R126', 'R127', 'C158', 'D28', 'R128', 'R129', 'C159', 'D29'):
    OVERRIDE[p] = 'Spare analog AI8/AI9 to MCU (PC5/PE8)'
for p in ('R118', 'R119', 'R120', 'R121'):
    OVERRIDE[p] = 'Frequency inputs FREQ1/FREQ2 (U20)'
for p in ('R122', 'R123', 'R124', 'R125'):
    OVERRIDE[p] = 'Frequency inputs FREQ3/FREQ4 (U21)'
for p in ('JP1', 'D1'):
    OVERRIDE[p] = 'CAN1 transceiver (U3) + ESD + split termination JP1'
for p in ('D19', 'JP2'):
    OVERRIDE[p] = 'CAN2 transceiver (U8) + choke L6 + ESD + split termination JP2'
for p in ('D30', 'D31', 'D32', 'R130', 'R131', 'R132'):
    OVERRIDE[p] = 'Status LEDs CAN/FAULT/STAT'
for p in ('JP3', 'JP4', 'R135', 'R136'):
    OVERRIDE[p] = 'Node-ID jumpers JP3/JP4'
for p in ('D20',):
    OVERRIDE[p] = 'Input protection: fuse, TVS, reverse-polarity FET (Q2)'

g = json.load(open(gj))['group']
anchor_group = {a: n for n, anchors in GROUPS for a in anchors}
member = {}
for part, anc in g.items():
    member[part] = OVERRIDE.get(part) or anchor_group.get(anc) or anchor_group.get(part)

if strip:
    text = open(src, encoding='utf-8').read()
    def drop(t, kinds):
        o, i = [], 0
        for m in re.finditer(r'\n\t\((' + '|'.join(kinds) + r')\b', t):
            if m.start() < i:
                continue
            d, j = 0, m.start() + 1
            while True:
                c = t[j]
                if c == '"':
                    j += 1
                    while t[j] != '"':
                        j += 2 if t[j] == '\\' else 1
                elif c == '(':
                    d += 1
                elif c == ')':
                    d -= 1
                    if d == 0:
                        break
                j += 1
            blk = t[m.start():j + 1]
            if m.group(1) == 'zone' and '(layer "F.Cu")' not in blk:
                continue                                  # keep plane zones on inner layers
            o.append(t[i:m.start()]); i = j + 1
        o.append(t[i:])
        return ''.join(o)
    text = drop(text, ['segment', 'via', 'arc', 'zone'])
    tmp = out + '.tmp.kicad_pcb'
    open(tmp, 'w', encoding='utf-8').write(text)
    b = pcbnew.LoadBoard(tmp)
else:
    b = pcbnew.LoadBoard(src)

fps = {f.GetReference(): f for f in b.GetFootprints()}
made, rows, missing = {}, [], []
for name, _ in GROUPS:
    refs = sorted((r for r, n in member.items() if n == name and r in fps),
                  key=lambda r: (re.match(r'[A-Z]+', r).group(), int(re.search(r'\d+', r).group())))
    if not refs:
        continue
    grp = pcbnew.PCB_GROUP(b)
    grp.SetName(name)
    b.Add(grp)
    for r in refs:
        grp.AddItem(fps[r])
    made[name] = refs
    rows.append((name, refs))
ungrouped = [r for r in fps if not any(r in v for v in made.values()) and not r.startswith('H')]
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)

with open(md, 'w') as f:
    f.write('# DDAQ placement groups\n\nEach KiCad group is one functional block: the IC/connector and the parts '
            'directly connected to it. Click a group to select it, drag to move it as a block, double-click to edit '
            'parts inside, right-click > Grouping > Ungroup to break it up.\n\n| Group | Parts |\n|---|---|\n')
    for name, refs in rows:
        f.write(f'| {name} | {", ".join(refs)} |\n')
    if ungrouped:
        f.write(f'\nNot grouped: {", ".join(sorted(ungrouped))}\n')
print('groups', len(made), 'parts grouped', sum(len(v) for v in made.values()), 'ungrouped', ungrouped)
