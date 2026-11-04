"""USB bench power: diode-OR (+5V | VBUS) into the 3.3 V LDO, VBUS bulk cap, VBUS sense on PA9
-> batchUSB.json + data/intent_usb.json.   New parts in the empty area x 400-560 / y 755-800 (guard check).
"""
import json
import math
import os
from pathlib import Path
from sch import load, find, one

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent / 'DDAQ'
LIBPATH = os.environ.get('DDAQ_LIB', (PROJ / 'JLCImport.kicad_sym').as_posix())
SCH = os.environ.get('DDAQ_SCH', (PROJ / 'DDAQ.kicad_sch').as_posix())
SYMS = json.load(open(HERE / 'data' / 'libsyms.json'))
BY_LCSC = {v['lcsc']: k for k, v in SYMS.items()}
POWER = {'GND', '+3.3V', '+5V'}
ROT = {'GND': {'down': 0, 'left': 270, 'right': 90, 'up': 180},
       '+3.3V': {'up': 0, 'left': 90, 'right': 270, 'down': 180},
       '+5V': {'up': 0, 'left': 90, 'right': 270, 'down': 180}}
R2 = lambda v: round(v, 2)
calls, fields, placed, intent = [], [], {}, []
pwr_n = [1100]   # existing #PWR refs go up to 01007


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
    if net in POWER:
        x, y, side = pin(ref, num)
        dx, dy = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}[side]
        ex, ey = R2(x + dx * 2.54), R2(y + dy * 2.54)
        calls.append({"tool": "add_wires", "args": {"wires": [{"x1": x, "y1": y, "x2": ex, "y2": ey}]}})
        pwr_n[0] += 1
        calls.append({"tool": "add_power_symbol", "args": {"lib_id": f"power:{net}", "reference": f"#PWR0{pwr_n[0]}",
                                                           "x": ex, "y": ey, "rotation": ROT[net][side]}})
    else:
        calls.append({"tool": "wire_pins_to_net", "args": {"pins": [{"reference": ref, "pin": str(num)}], "label_text": net}})


def part2(ref, lcsc, x, y, n1, n2, rot=270):
    place(ref, lcsc, x, y, rot)
    conn(ref, 1, n1)
    conn(ref, 2, n2)


def label(text, x, y, rot=0):
    calls.append({"tool": "add_label", "args": {"text": text, "x": x, "y": y, "rotation": rot}})


def flag(net, ref, x, y):
    """PWR_FLAG on a net: a label and the flag's pin at the same point (net is only diode/connector fed)."""
    label(net, x, y)
    calls.append({"tool": "add_power_symbol", "args": {"lib_id": "power:PWR_FLAG", "reference": ref,
                                                       "x": x, "y": y, "rotation": 0}})


B5819W, C1U, C10U, R10K, R20K = 'C8598', 'C15849', 'C15850', 'C25804', 'C4184'
BOX = (400.0, 560.0, 755.0, 800.0)

# --- U4 input moves from +5V to LDO_IN: replace the +5V symbol on its VI wire with an LDO_IN label
calls.append({"tool": "remove_component", "args": {"reference": "#PWR039"}})
label('LDO_IN', 144.78, 763.27, 0)
intent.append(('U4', '3', 'LDO_IN'))

# --- diode-OR: B5819W pin 2 = anode (+), pin 1 = cathode (-); rot 180 puts the anode on the left
part2('D42', B5819W, 424.18, 772.16, 'LDO_IN', '+5V', rot=180)    # battery path: +5V -> LDO_IN
part2('D43', B5819W, 424.18, 784.86, 'LDO_IN', 'VBUS', rot=180)   # USB path: VBUS -> LDO_IN
part2('C167', C10U, 449.58, 778.51, 'LDO_IN', 'GND')              # LDO input cap after the diodes
flag('LDO_IN', '#FLG01101', 462.28, 767.08)
# --- VBUS: bulk cap at the connector side, sense divider to PA9 (5.0 V -> 3.33 V)
part2('C166', C1U, 477.52, 778.51, 'VBUS', 'GND')
flag('VBUS', '#FLG01102', 490.22, 767.08)
part2('R139', R10K, 502.92, 778.51, 'VBUS', 'VBUS_SENSE_PA9')
part2('R140', R20K, 515.62, 778.51, 'VBUS_SENSE_PA9', 'GND')
calls.append({"tool": "remove_no_connect", "args": {"reference": "U1", "pin_name": "70"}})
calls.append({"tool": "wire_pins_to_net", "args": {"pins": [{"reference": "U1", "pin": "70"}], "label_text": "VBUS_SENSE_PA9"}})
intent.append(('U1', '70', 'VBUS_SENSE_PA9'))
intent += [('USBC1', 'A4B9', 'VBUS'), ('USBC1', 'B4A9', 'VBUS'), ('U22', '5', 'VBUS')]

calls.append({"tool": "add_text", "args": {"x": 403.86, "y": 760.73, "text":
    "USB BENCH POWER (3.3 V side only) + VBUS SENSE"}})
calls.append({"tool": "add_text", "args": {"x": 403.86, "y": 795.02, "text":
    "D42/D43 diode-OR: battery (+5V) or USB VBUS feeds the 3.3 V LDO (U4); neither can back-feed the other.\n"
    "USB alone runs only the 3.3 V side (MCU, SD, IMU, baro, LEDs). Firmware: detect it from the rail monitors\n"
    "(PC2 VIN, PB2 5V) and skip ADC / CAN / sensor-supply init. Enable the USB D+ pull-up only while PA9 sees VBUS.\n"
    "LDO headroom ~4.6 V in vs AMS1117 dropout ~1.1 V: OK, tight at low VBUS - a low-dropout 3.3 V LDO would add margin."}})

x0, x1, y0, y1 = BOX
inside = lambda x, y: x0 <= float(x) <= x1 and y0 <= float(y) <= y1
root = load(SCH)
hits = [('wire', p[1], p[2]) for w in find(root, 'wire') for p in one(w, 'pts')[1:] if inside(p[1], p[2])]
hits += [('symbol', *one(s, 'at')[1:3]) for s in find(root, 'symbol') if inside(*one(s, 'at')[1:3])]
hits += [(l[0], *one(l, 'at')[1:3]) for l in root if isinstance(l, list) and
         l[0] in ('label', 'global_label', 'text', 'no_connect', 'junction') and inside(*one(l, 'at')[1:3])]
print('occupied in target area:', hits[:10])
assert not hits, 'target area not empty'
json.dump(calls + fields, open(HERE / 'batchUSB.json', 'w'))
json.dump(intent, open(HERE / 'data' / 'intent_usb.json', 'w'))
print('calls', len(calls), 'fields', len(fields), 'parts', len(placed))
