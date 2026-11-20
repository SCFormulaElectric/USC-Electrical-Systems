"""Replace J2/J3/J4 with one AMPSEAL 35 (776163-1), cut trackers to L/R/chassis, 12V outputs to 2, add supply TVS.
Writes batchC.json + intent_conn.json."""
import json
import math
from sch import load, find, one

LIBPATH = 'C:/Git/USC-Electrical-Systems/2026-27/Boards/DDAQ/DDAQ/JLCImport.kicad_sym'
SYMS = json.load(open('libsyms.json'))
BY_LCSC = {v['lcsc']: k for k, v in SYMS.items()}
ROT = {'GND': {'down': 0, 'left': 270, 'right': 90, 'up': 180}, '+12V': {'up': 0, 'left': 90, 'right': 270, 'down': 180}}
R2 = lambda v: round(v, 2)
rm = json.load(open('removal2.json'))
root = load('backup_before_conn.kicad_sch')
calls, fields, placed, intent = [], [], {}, []
pwr_n = [900]

# ---- removals
for ref in ['J2', 'J3', 'J4', 'U15', 'U19', 'C139', 'R113', 'C147', 'C143', 'R117', 'C151', 'F5', 'F6'] + rm['pwr']:
    calls.append({"tool": "remove_component", "args": {"reference": ref}})
for a, b in rm['wires']:
    calls.append({"tool": "remove_wire", "args": {"x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1]}})
removed_lab = {(l[1], tuple(l[2])) for l in rm['labels']}
for kind, text, (x, y) in rm['labels']:
    calls.append({"tool": "remove_label", "args": {"text": text, "x": x, "y": y}})

# ---- rename supply nets to per-branch names
REN = {'+5V_EXC1': '+5V_EXC_L', '+5V_EXC2': '+5V_EXC_R', '+5V_EXC3': '+5V_EXC_C', '+5V_EXC4': None,
       '+5V_WS1': '+5V_WS_L', '+5V_WS2': '+5V_WS_R', '+5V_WS3': '+5V_WS_C', '+5V_WS4': '+5V_WS_C'}
for c in root:
    if isinstance(c, list) and c[0] == 'label' and c[1] in REN:
        a = one(c, 'at')
        x, y, rot = round(float(a[1]), 2), round(float(a[2]), 2), int(float(a[3]))
        if (c[1], (x, y)) in removed_lab:
            continue
        assert REN[c[1]], f'leftover {c[1]} label at {x},{y}'
        calls.append({"tool": "remove_label", "args": {"text": c[1], "x": x, "y": y}})
        calls.append({"tool": "add_label", "args": {"text": REN[c[1]], "x": x, "y": y, "rotation": rot}})
# CAN2 bus side of the common-mode choke (was J4)
calls.append({"tool": "add_label", "args": {"text": "CAN2H_BUS", "x": 633.73, "y": 64.77}})
calls.append({"tool": "add_label", "args": {"text": "CAN2L_BUS", "x": 633.73, "y": 67.31}})


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
    a = math.radians(p[4])
    dx, dy = round(math.cos(a)), -round(math.sin(a))
    bx, by = dx * c + dy * s, -dx * s + dy * c
    return R2(X + x * c + y * s), R2(Y - x * s + y * c), {(-1, 0): 'left', (1, 0): 'right', (0, -1): 'up', (0, 1): 'down'}[(-bx, -by)]


def conn(ref, num, net):
    intent.append((ref, str(num), net))
    if net == 'NC':
        calls.append({"tool": "no_connect_pin", "args": {"reference": ref, "pin_name": str(num)}})
    elif net in ('GND', 'VBAT'):
        x, y, side = pin(ref, num)
        dx, dy = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}[side]
        ex, ey = R2(x + dx * 2.54), R2(y + dy * 2.54)
        calls.append({"tool": "add_wires", "args": {"wires": [{"x1": x, "y1": y, "x2": ex, "y2": ey}]}})
        pwr_n[0] += 1
        lib = 'GND' if net == 'GND' else '+12V'
        calls.append({"tool": "add_power_symbol", "args": {"lib_id": f"power:{lib}", "reference": f"#PWR0{pwr_n[0]}",
                                                           "x": ex, "y": ey, "rotation": ROT[lib][side]}})
        if net == 'VBAT':  # same trick as the existing VBAT symbol: power:+12V with Value VBAT
            calls.append({"tool": "set_component_property", "args": {"reference": f"#PWR0{pwr_n[0]}", "key": "Value", "value": "VBAT"}})
    else:
        calls.append({"tool": "wire_pins_to_net", "args": {"pins": [{"reference": ref, "pin": str(num)}], "label_text": net}})


# ---- AMPSEAL 35 pin map: left corner, right corner, chassis, power/CAN
PINMAP = ['+5V_EXC_L', 'AI0', '+5V_WS_L', 'FREQ1_IN', 'GND',
          '+5V_EXC_R', 'AI1', '+5V_WS_R', 'FREQ2_IN', 'IZZE_PWR', 'GND',
          '+5V_EXC_C', 'AI2', 'AI3', 'AI4', 'AI5', 'AI6', 'AI7', 'AI8', 'AI9', '+5V_WS_C', 'FREQ3_IN', 'FREQ4_IN',
          '+12V_OUT1', '+12V_OUT2', 'GND',
          'VBAT', 'GND', 'CAN1H', 'CAN1L', 'CAN1H', 'CAN1L', 'CAN2H_BUS', 'CAN2L_BUS', 'NC']
assert len(PINMAP) == 35
place('J3', 'C412117', 939.8, 228.6)
for i, net in enumerate(PINMAP, 1):
    conn('J3', i, net)

# ---- TVS on every off-board supply pin (SMF15A: 15 V standoff, pin 1 = cathode)
for i, net in enumerate(['+5V_EXC_L', '+5V_EXC_R', '+5V_EXC_C', '+5V_WS_L', '+5V_WS_R', '+5V_WS_C', 'IZZE_PWR',
                         '+12V_OUT1', '+12V_OUT2']):
    ref = f'D{33 + i}'
    place(ref, 'C151294', 977.9 + 12.7 * i, 335.28, 270)
    conn(ref, 1, net)
    conn(ref, 2, 'GND')

json.dump(calls + fields, open('batchC.json', 'w'))
json.dump(intent, open('intent_conn.json', 'w'))
print('calls', len(calls), 'fields', len(fields))
