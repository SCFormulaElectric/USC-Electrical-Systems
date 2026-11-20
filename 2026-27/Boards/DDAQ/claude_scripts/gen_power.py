"""Generate kicad-batch calls for the DDAQ power tree (spec: 8-18 V in, 12 V buck-boost sensor rail,
7 V pre-regulator, precision 5 V, per-pin protected 5 V outputs, rail monitoring).

Writes batchP.json. Pin geometry comes from the JLCImport library (libsyms.json)."""
import json
import math

LIBPATH = 'C:/Git/USC-Electrical-Systems/2026-27/Boards/DDAQ/DDAQ/JLCImport.kicad_sym'
SYMS = json.load(open('libsyms.json'))
BY_LCSC = {v['lcsc']: k for k, v in SYMS.items()}
POWER = {'GND', '+3.3V', '+5V'}
ROT = {'GND': {'down': 0, 'left': 270, 'right': 90, 'up': 180},
       '+3.3V': {'up': 0, 'left': 90, 'right': 270, 'down': 180},
       '+5V': {'up': 0, 'left': 90, 'right': 270, 'down': 180}}
R2 = lambda v: round(v, 2)

calls, fields, placed = [], [], {}
pwr_n = [500]


def place(ref, lcsc, x, y, rot=0):
    sym = BY_LCSC[lcsc]
    calls.append({"tool": "place_component", "args": {"lib_id": f"JLCImport:{sym}", "reference": ref, "value": sym,
                                                      "x": x, "y": y, "rotation": rot, "symbol_lib_path": LIBPATH}})
    for k, v in SYMS[sym]['props'].items():
        if v:
            fields.append({"tool": "set_component_property", "args": {"reference": ref, "key": k, "value": v}})
    placed[ref] = (sym, x, y, rot)


def pin(ref, num):
    sym, X, Y, rot = placed[ref]
    p = [p for p in SYMS[sym]['pins'] if p[0] == str(num)][0]
    t = math.radians(rot)
    c, s = round(math.cos(t)), round(math.sin(t))
    x, y = p[2], -p[3]
    px, py = R2(X + x * c + y * s), R2(Y - x * s + y * c)
    a = math.radians(p[4])
    dx, dy = round(math.cos(a)), -round(math.sin(a))
    bx, by = dx * c + dy * s, -dx * s + dy * c  # into body
    side = {(-1, 0): 'left', (1, 0): 'right', (0, -1): 'up', (0, 1): 'down'}[(-bx, -by)]
    return px, py, side


def conn(ref, num, net):
    if net == 'NC':
        calls.append({"tool": "no_connect_pin", "args": {"reference": ref, "pin_name": str(num)}})
        return
    if net in POWER:
        x, y, side = pin(ref, num)
        dx, dy = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}[side]
        ex, ey = R2(x + dx * 2.54), R2(y + dy * 2.54)
        calls.append({"tool": "add_wires", "args": {"wires": [{"x1": x, "y1": y, "x2": ex, "y2": ey}]}})
        pwr_n[0] += 1
        calls.append({"tool": "add_power_symbol", "args": {"lib_id": f"power:{net}", "reference": f"#PWR0{pwr_n[0]}",
                                                           "x": ex, "y": ey, "rotation": ROT[net][side]}})
        return
    calls.append({"tool": "wire_pins_to_net", "args": {"pins": [{"reference": ref, "pin": str(num)}], "label_text": net}})


def part2(ref, lcsc, x, y, n1, n2):
    """2-pin part, vertical: pin 1 on top."""
    rot = 0 if BY_LCSC[lcsc].startswith('MVK') else 270
    place(ref, lcsc, x, y, rot)
    conn(ref, 1, n1)
    conn(ref, 2, n2)


def ic(ref, lcsc, x, y, nets):
    place(ref, lcsc, x, y)
    for num, net in nets.items():
        conn(ref, num, net)


def row(y, parts, x0=50.8):
    for i, p in enumerate(parts):
        part2(p[0], p[1], x0 + 12.7 * i, y, p[2], p[3])


C100N, C1U, C4U7, C10U25, C10U50, C22U, C100U = 'C14663', 'C15849', 'C19666', 'C15850', 'C5449000', 'C2918511', 'C350012'
R1, R10, R100, R1K, R5K1, R10K, R16K5, R20K, R47K, R53K6, R84K5, R93K1, R100K, R249K, R280K = (
    'C22936', 'C22859', 'C22775', None, 'C23186', 'C25804', 'C22812', 'C4184', 'C25819', 'C23074', 'C23118',
    'C23266', 'C25803', 'C22918', 'C22970')

# ---------------- ICs (y = 457.2 band)
ic('U9', 'C2866787', 88.9, 457.2, {1: 'GND', 2: 'VIN_PROT', 3: 'VIN_PROT', 4: 'NC', 5: '7V_FB', 6: '7V_VCC',
                                   7: '7V_BOOT', 8: '7V_SW', 9: 'GND'})
ic('U10', 'C114839', 177.8, 457.2, {1: '+5V_REF', 20: '+5V_REF', 3: '+5V_REF', 2: 'NC', 17: 'NC', 18: 'NC', 19: 'NC',
                                    4: 'NC', 5: 'NC', 8: 'NC', 9: 'NC', 11: 'NC', 12: 'NC', 6: 'GND', 10: 'GND',
                                    7: 'GND', 13: '+7V', 14: 'REF_NR', 15: '+7V', 16: '+7V', 21: 'GND'})
ic('U11', 'C113356', 279.4, 457.2, {1: 'BB_EN', 2: 'BB_VIN', 3: 'VIN_PROT', 4: 'BB_MODE', 5: 'GND', 6: 'BB_RT',
                                    7: 'BB_SLOPE', 8: 'BB_SS', 9: 'BB_COMP', 10: 'GND', 11: 'BB_FB', 12: '+12V_SNS',
                                    13: '+12V_SNS', 14: '+12V_SNS', 15: 'BB_CSG', 16: 'BB_CS', 17: 'PG_12V_PE7',
                                    18: 'BB_SW2', 19: 'BB_HD2', 20: 'BB_BT2', 21: 'BB_LD2', 22: 'GND', 23: 'BB_VCC',
                                    24: '+12V_SNS', 25: 'BB_LD1', 26: 'BB_BT1', 27: 'BB_HD1', 28: 'BB_SW1', 29: 'GND'})
for i, (ref, s, g, d) in enumerate([('Q3', 'BB_SW1', 'BB_HD1', 'VIN_PROT'), ('Q4', 'BB_RS', 'BB_LD1', 'BB_SW1'),
                                    ('Q5', 'BB_SW2', 'BB_HD2', '+12V_SNS'), ('Q6', 'BB_RS', 'BB_LD2', 'BB_SW2')]):
    ic(ref, 'C334232', 360.68 + 45.72 * i, 457.2, {1: s, 2: s, 3: s, 4: g, 5: d, 6: d, 7: d, 8: d})

# ---------------- protected 5 V outputs: NCV8184 trackers on +5V_REF
outs = [f'+5V_EXC{i}' for i in range(1, 5)] + [f'+5V_WS{i}' for i in range(1, 5)]
for k, net in enumerate(outs):
    X, Y = 571.5 + 76.2 * (k % 4), 449.58 + 71.12 * (k // 4)
    ic(f'U{12 + k}', 'C150044', X, Y, {1: net, 4: net, 2: 'GND', 3: 'GND', 6: 'GND', 7: 'GND',
                                       5: '+5V_REF', 8: '+7V'})
    part2(f'C{136 + k}', C100N, X - 12.7, Y + 25.4, '+7V', 'GND')
    part2(f'R{110 + k}', R1, X, Y + 25.4, net, f'TRK{k + 1}_C')
    part2(f'C{144 + k}', C1U, X + 12.7, Y + 25.4, f'TRK{k + 1}_C', 'GND')

# ---------------- passive rows
row(505.46, [
    ('D20', 'C78413', 'VBAT_FUSED', 'GND'), ('C95', C100U, 'VIN_PROT', 'GND'),
    ('C96', C10U50, 'VIN_PROT', 'GND'), ('C97', C10U50, 'VIN_PROT', 'GND'),
    ('R86', R100K, 'VIN_PROT', 'VMON_VIN_PC2'), ('R87', R10K, 'VMON_VIN_PC2', 'GND'), ('C98', C100N, 'VMON_VIN_PC2', 'GND'),
    ('C101', C10U50, 'VIN_PROT', 'GND'), ('C102', C10U50, 'VIN_PROT', 'GND'), ('C103', C100N, 'VIN_PROT', 'GND'),
    ('C99', C1U, '7V_VCC', 'GND'), ('C100', C100N, '7V_BOOT', '7V_SW'), ('L7', 'C1329356', '7V_SW', '+7V'),
    ('C104', C22U, '+7V', 'GND'), ('C105', C22U, '+7V', 'GND'), ('C106', C22U, '+7V', 'GND'), ('C107', C22U, '+7V', 'GND'),
    ('R88', R100K, '+7V', '7V_FB'), ('R89', R16K5, '7V_FB', 'GND'),
    ('R90', R20K, '+7V', 'VMON_7V_PB0'), ('R91', R10K, 'VMON_7V_PB0', 'GND'), ('C108', C100N, 'VMON_7V_PB0', 'GND')])
row(551.18, [
    ('C110', C10U25, '+7V', 'GND'), ('C111', C10U25, '+7V', 'GND'), ('C112', C1U, 'REF_NR', 'GND'),
    ('C113', C22U, '+5V_REF', 'GND'), ('C114', C22U, '+5V_REF', 'GND'),
    ('R94', R10K, '+5V_REF', 'VMON_5VREF_PB1'), ('R95', R10K, 'VMON_5VREF_PB1', 'GND'), ('C115', C100N, 'VMON_5VREF_PB1', 'GND'),
    ('R92', R10K, '+5V', 'VMON_5V_PB2'), ('R93', R10K, 'VMON_5V_PB2', 'GND'), ('C109', C100N, 'VMON_5V_PB2', 'GND'),
    ('F3', 'C70077', '+12V_SNS', '+12V_OUT1'), ('F4', 'C70077', '+12V_SNS', '+12V_OUT2'),
    ('F5', 'C70077', '+12V_SNS', '+12V_OUT3'), ('F6', 'C70077', '+12V_SNS', '+12V_OUT4'),
    ('F7', 'C70055', '+7V', 'IZZE_F'), ('D23', 'C2480', 'IZZE_PWR', 'IZZE_F')])  # SS14: pin1 K, pin2 A
row(596.9, [
    ('R96', R249K, 'VIN_PROT', 'BB_EN'), ('R97', R53K6, 'BB_EN', 'GND'), ('R98', R10, 'VIN_PROT', 'BB_VIN'),
    ('C116', C100N, 'BB_VIN', 'GND'), ('R99', R93K1, 'BB_MODE', 'GND'), ('R100', R84K5, 'BB_RT', 'GND'),
    ('C117', 'C1635', 'BB_SLOPE', 'GND'), ('C118', C100N, 'BB_SS', 'GND'), ('R101', R5K1, 'BB_COMP', 'BB_CZ'),
    ('C119', 'C107086', 'BB_CZ', 'GND'), ('C120', 'C1635', 'BB_COMP', 'GND'), ('R102', R280K, '+12V_SNS', 'BB_FB'),
    ('R103', R20K, 'BB_FB', 'GND'), ('R104', R100, 'BB_CS', 'BB_RS'), ('R105', R100, 'BB_CSG', 'GND'),
    ('C121', 'C94904', 'BB_CS', 'BB_CSG'), ('R106', R10K, '+3.3V', 'PG_12V_PE7'), ('C122', C4U7, 'BB_VCC', 'GND'),
    ('C123', C1U, '+12V_SNS', 'GND')])
row(642.62, [
    ('C124', C100N, 'BB_BT1', 'BB_SW1'), ('C125', C100N, 'BB_BT2', 'BB_SW2'),
    ('D21', 'C8598', 'BB_BT1', 'BB_VCC'), ('D22', 'C8598', 'BB_BT2', 'BB_VCC'),  # B5819W: pin1 K(-), pin2 A(+)
    ('R107', 'C2985721', 'BB_RS', 'GND'), ('L8', 'C54570625', 'BB_SW1', 'BB_SW2'),
    ('C126', C10U50, 'VIN_PROT', 'GND'), ('C127', C10U50, 'VIN_PROT', 'GND'), ('C128', C10U50, 'VIN_PROT', 'GND'),
    ('C129', C10U50, 'VIN_PROT', 'GND'), ('C130', C10U50, '+12V_SNS', 'GND'), ('C131', C10U50, '+12V_SNS', 'GND'),
    ('C132', C10U50, '+12V_SNS', 'GND'), ('C133', C10U50, '+12V_SNS', 'GND'), ('C134', C100U, '+12V_SNS', 'GND'),
    ('R108', R47K, '+12V_SNS', 'VMON_12V_PC3'), ('R109', R10K, 'VMON_12V_PC3', 'GND'), ('C135', C100N, 'VMON_12V_PC3', 'GND')])

# ---------------- MCU monitor pins
for p, net in {17: 'VMON_VIN_PC2', 18: 'VMON_12V_PC3', 32: 'VMON_7V_PB0', 33: 'VMON_5VREF_PB1', 34: 'VMON_5V_PB2',
               38: 'PG_12V_PE7'}.items():
    calls.append({"tool": "wire_pins_to_net", "args": {"pins": [{"reference": "U1", "pin": str(p)}], "label_text": net}})

json.dump(calls + fields, open('batchP.json', 'w'))
print('calls', len(calls), 'fields', len(fields), 'parts', len(placed))
