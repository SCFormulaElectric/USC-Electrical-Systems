"""IMU (ISM330DHCX) + barometer (BMP581) on SPI3 -> batchSENS.json + data/intent_sens.json.

Run from anywhere; paths are relative to this file unless DDAQ_SCH / DDAQ_LIB are set (point DDAQ_SCH at a
backup copy of the schematic taken before the step, as the other gen_*.py scripts do).
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
POWER = {'GND', '+3.3V'}
ROT = {'GND': {'down': 0, 'left': 270, 'right': 90, 'up': 180},
       '+3.3V': {'up': 0, 'left': 90, 'right': 270, 'down': 180}}
R2 = lambda v: round(v, 2)
calls, fields, placed, intent = [], [], {}, []
pwr_n = [800]


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


def nc(ref, num):
    intent.append((ref, str(num), 'NC'))
    calls.append({"tool": "no_connect_pin", "args": {"reference": ref, "pin_name": str(num)}})


def part2(ref, lcsc, x, y, n1, n2):
    place(ref, lcsc, x, y, 270)
    conn(ref, 1, n1)
    conn(ref, 2, n2)


R10K, C100N, C1U = 'C25804', 'C14663', 'C15849'
SCK, MISO, MOSI = 'SPI3_SCK_PC10', 'SPI3_MISO_PC11', 'SPI3_MOSI_PC12'
BOX = (355.0, 560.0, 580.0, 745.0)  # x0, x1, y0, y1 (mm)

# --- IMU: ISM330DHCX, SPI mode 3 wiring. Aux I2C master (SDx/SCx) unused -> GND, OCS_Aux / SDO_Aux -> NC
place('U23', 'C2655101', 419.1, 637.54)
for num, net in {1: MISO, 13: SCK, 14: MOSI, 12: 'IMU_CS_PA15', 4: 'IMU_INT1_PD5', 9: 'IMU_INT2_PD6',
                 5: '+3.3V', 8: '+3.3V', 6: 'GND', 7: 'GND', 2: 'GND', 3: 'GND'}.items():
    conn('U23', num, net)
nc('U23', 10)
nc('U23', 11)
part2('C160', C100N, 464.82, 640.08, '+3.3V', 'GND')   # VDD
part2('C161', C1U, 477.52, 640.08, '+3.3V', 'GND')     # VDD bulk
part2('C162', C100N, 490.22, 640.08, '+3.3V', 'GND')   # VDD_IO

# --- CS pull-ups: both sensors deselected while the MCU is in reset / boot
part2('R133', R10K, 513.08, 640.08, '+3.3V', 'IMU_CS_PA15')
part2('R134', R10K, 528.32, 640.08, '+3.3V', 'BARO_CS_PD4')

# --- Barometer: BMP581
place('U24', 'C5362283', 419.1, 703.58)
for num, net in {2: SCK, 4: MOSI, 5: MISO, 6: 'BARO_CS_PD4', 7: 'BARO_INT_PD7',
                 1: '+3.3V', 10: '+3.3V', 3: 'GND', 8: 'GND', 9: 'GND'}.items():
    conn('U24', num, net)
part2('C163', C100N, 464.82, 706.12, '+3.3V', 'GND')   # VDD
part2('C164', C100N, 477.52, 706.12, '+3.3V', 'GND')   # VDDIO

# --- MCU pins (SPI3 = AF6)
for p, net in {79: SCK, 80: MISO, 81: MOSI, 78: 'IMU_CS_PA15', 86: 'BARO_CS_PD4',
               87: 'IMU_INT1_PD5', 88: 'IMU_INT2_PD6', 89: 'BARO_INT_PD7'}.items():
    intent.append(('U1', str(p), net))
    calls.append({"tool": "wire_pins_to_net", "args": {"pins": [{"reference": "U1", "pin": str(p)}], "label_text": net}})

# --- notes
calls.append({"tool": "add_text", "args": {"x": 365.76, "y": 591.82, "text":
    "IMU + BAROMETER (SPI3: PC10 SCK / PC11 MISO / PC12 MOSI, AF6)"}})
calls.append({"tool": "add_text", "args": {"x": 365.76, "y": 726.44, "text":
    "Firmware:\n"
    "- ISM330DHCX: set CTRL4_C.I2C_disable = 1 at init (shares the SPI bus; CS high otherwise = I2C mode).\n"
    "- BMP581 switches to SPI on the first CSB falling edge: do one dummy read first.\n"
    "Layout:\n"
    "- IMU near the board mounting point / centre; mark X/Y/Z axes on silkscreen.\n"
    "- Barometer away from the LM5175 / LMR33630 / TPS563300 hot spots; enclosure needs a vent membrane over it."}})

# guard: nothing already on the sheet inside the target area
x0, x1, y0, y1 = BOX
inside = lambda x, y: x0 <= float(x) <= x1 and y0 <= float(y) <= y1
root = load(SCH)
hits = []
for w in find(root, 'wire'):
    for p in one(w, 'pts')[1:]:
        if inside(p[1], p[2]):
            hits.append(('wire', p[1], p[2]))
for s in find(root, 'symbol'):
    a = one(s, 'at')
    if inside(a[1], a[2]):
        hits.append(('symbol', a[1], a[2]))
for l in [x for x in root if isinstance(x, list) and x[0] in ('label', 'global_label', 'text', 'no_connect', 'junction')]:
    a = one(l, 'at')
    if inside(a[1], a[2]):
        hits.append((l[0], a[1], a[2]))
print('occupied in target area:', hits[:10])
assert not hits, 'target area not empty'
json.dump(calls + fields, open(HERE / 'batchSENS.json', 'w'))
json.dump(intent, open(HERE / 'data' / 'intent_sens.json', 'w'))
print('calls', len(calls), 'fields', len(fields), 'parts', len(placed))
