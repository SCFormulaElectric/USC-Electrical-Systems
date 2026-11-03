"""Step 2 (pre-PCB): CAN termination jumpers, node-ID jumpers, SD power switch, label cleanup, MCU NC flags, LCSC fields
-> batchSTEP2.json + data/intent_step2.json.

New parts go in the empty area x 585-760 / y 590-745 (guard check below). Existing-item edits are listed explicitly.
Std-lib symbols (Jumper, Transistor_FET) are loaded from STDLIB (KiCad's own .kicad_sym files; copy them out of the
KiCad install, e.g. C:/Program Files/KiCad/10.0/share/kicad/symbols).
"""
import json
import math
import os
from pathlib import Path
from sch import load, find, one

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent / 'DDAQ'
LIBPATH = os.environ.get('DDAQ_LIB', (PROJ / 'JLCImport.kicad_sym').as_posix())
STDLIB = os.environ.get('KICAD_STDLIB', 'C:/Program Files/KiCad/10.0/share/kicad/symbols')
SCH = os.environ.get('DDAQ_SCH', (PROJ / 'DDAQ.kicad_sch').as_posix())
SYMS = json.load(open(HERE / 'data' / 'libsyms.json'))
BY_LCSC = {v['lcsc']: k for k, v in SYMS.items()}
STD = {'SolderJumper_3_Open': 'Jumper', 'SolderJumper_3_Bridged123': 'Jumper', 'SolderJumper_2_Open': 'Jumper',
       'AO3401A': 'Transistor_FET'}
POWER = {'GND', '+3.3V'}
ROT = {'GND': {'down': 0, 'left': 270, 'right': 90, 'up': 180},
       '+3.3V': {'up': 0, 'left': 90, 'right': 270, 'down': 180}}
R2 = lambda v: round(v, 2)
calls, fields, placed, intent = [], [], {}, []
pwr_n = [1000]  # existing #PWR refs go up to 0914


def place(ref, key, x, y, rot=0, value=None):
    sym = BY_LCSC.get(key, key)
    if sym in STD:
        lib = STD[sym]
        args = {"lib_id": f"{lib}:{sym}", "reference": ref, "value": value or sym, "x": x, "y": y, "rotation": rot,
                "symbol_lib_path": f"{STDLIB}/{lib}.kicad_sym"}
    else:
        args = {"lib_id": f"JLCImport:{sym}", "reference": ref, "value": value or sym, "x": x, "y": y, "rotation": rot,
                "symbol_lib_path": LIBPATH}
    calls.append({"tool": "place_component", "args": args})
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


def part2(ref, lcsc, x, y, n1, n2):
    place(ref, lcsc, x, y, 270)
    conn(ref, 1, n1)
    conn(ref, 2, n2)


def ic(ref, key, x, y, nets, rot=0):
    place(ref, key, x, y, rot)
    for num, net in nets.items():
        conn(ref, num, net)


def label(text, x, y, rot=0):
    calls.append({"tool": "add_label", "args": {"text": text, "x": x, "y": y, "rotation": rot}})


def relabel(old, new, x, y, rot):
    calls.append({"tool": "remove_label", "args": {"text": old, "x": x, "y": y}})
    label(new, x, y, rot)


def text(s, x, y):
    calls.append({"tool": "add_text", "args": {"x": x, "y": y, "text": s}})


R10K, R100K, C100N = 'C25804', 'C25803', 'C14663'
BOX = (585.0, 760.0, 590.0, 745.0)

# ---------------- 1. CAN termination: split the 60R/60R midpoint, one 3-pad solder jumper per bus ----------------
# CAN1 (R5 top leg, R4 bottom leg, C14 to GND). Bus passes through J3 29-32 -> jumper OPEN by default.
for x1, y1, x2, y2 in ((393.7, 54.61, 393.7, 58.42), (393.7, 58.42, 393.7, 60.96)):
    calls.append({"tool": "remove_wire", "args": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}})
calls.append({"tool": "remove_junction", "args": {"x": 393.7, "y": 58.42}})
label('CAN1_TERM_H', 393.7, 54.61, 180)     # R5 pin 1
label('CAN1_TERM_MID', 393.7, 58.42, 180)   # C14 pin 1 wire end
label('CAN1_TERM_L', 393.7, 60.96, 180)     # R4 pin 2
intent += [('R5', '1', 'CAN1_TERM_H'), ('R4', '2', 'CAN1_TERM_L'), ('C14', '1', 'CAN1_TERM_MID')]
# CAN2 (R14 top leg, R15 bottom leg, C20 on the existing CAN_VREF label). Single connector pair -> BRIDGED by default.
for x1, y1, x2, y2 in ((576.58, 60.96, 576.58, 63.5), (576.58, 63.5, 576.58, 66.04)):
    calls.append({"tool": "remove_wire", "args": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}})
calls.append({"tool": "remove_junction", "args": {"x": 576.58, "y": 63.5}})
label('CAN2_TERM_H', 576.58, 60.96, 180)    # R14 pin 1
label('CAN2_TERM_L', 576.58, 66.04, 180)    # R15 pin 2
intent += [('R14', '1', 'CAN2_TERM_H'), ('R15', '2', 'CAN2_TERM_L'), ('C20', '2', 'CAN_VREF')]
ic('JP1', 'SolderJumper_3_Open', 601.98, 615.95, {1: 'CAN1_TERM_H', 2: 'CAN1_TERM_MID', 3: 'CAN1_TERM_L'})
ic('JP2', 'SolderJumper_3_Bridged123', 642.62, 615.95, {1: 'CAN2_TERM_H', 2: 'CAN_VREF', 3: 'CAN2_TERM_L'})
text('CAN TERMINATION (split 2x60R + 4.7nF): bridge all 3 pads to terminate.\n'
     'JP1 = CAN1, OPEN by default (bus passes through J3 29-32).\n'
     'JP2 = CAN2, BRIDGED by default (this board ends CAN2). Open = both 60R legs float.', 589.28, 632.46)

# ---------------- 2. Node ID: 10k pull-up + solder jumper to GND on PC0 / PC1 ----------------
relabel('GPIO1_PC0', 'NODE_ID0_PC0', 162.56, 146.05, 180)
relabel('GPIO2_PC1', 'NODE_ID1_PC1', 162.56, 148.59, 180)
intent += [('U1', '15', 'NODE_ID0_PC0'), ('U1', '16', 'NODE_ID1_PC1')]
for i, (r, jp, x) in enumerate((('R135', 'JP3', 596.9), ('R136', 'JP4', 627.38))):
    net = f'NODE_ID{i}_PC{i}'
    part2(r, R10K, x, 662.94, '+3.3V', net)
    ic(jp, 'SolderJumper_2_Open', x + 12.7, 678.18, {1: net, 2: 'GND'})
text('NODE ID = {PC1, PC0}: open = 1, bridged = 0 (all open = 3).', 589.28, 693.42)

# ---------------- 3. SD card power switch on PD9 (active low, ~1 ms soft start) ----------------
relabel('SPI2_EN_PD9', 'SD_PWR_EN_N_PD9', 203.2, 222.25, 0)
intent += [('U1', '56', 'SD_PWR_EN_N_PD9')]
ic('Q7', 'C15127', 685.8, 660.4, {2: '+3.3V', 3: 'SD_VDD', 1: 'SD_PWR_GATE'}, rot=180)
part2('R137', R100K, 703.58, 660.4, '+3.3V', 'SD_PWR_GATE')    # gate pull-up: card off while MCU is in reset
part2('C165', C100N, 716.28, 660.4, '+3.3V', 'SD_PWR_GATE')    # gate-source C: with R138 -> ~1 ms turn-on
part2('R138', R10K, 728.98, 660.4, 'SD_PWR_EN_N_PD9', 'SD_PWR_GATE')
# SD_VDD is fed through Q7 (passive pins): PWR_FLAG so ERC sees a source. Q7 drain stub ends at (683.26, 668.02).
calls.append({"tool": "add_wires", "args": {"wires": [{"x1": 683.26, "y1": 668.02, "x2": 678.18, "y2": 668.02}]}})
calls.append({"tool": "add_power_symbol", "args": {"lib_id": "power:PWR_FLAG", "reference": "#FLG01001",
                                                   "x": 678.18, "y": 668.02, "rotation": 0}})
# card side: J1 VDD, C17/C18 and the SPI pull-ups R6/R7/R8/R10/R11 move from +3.3V to SD_VDD
for ref, x, y in (('#PWR028', 535.94, 143.51), ('#PWR029', 532.13, 146.05), ('#PWR030', 528.2187, 148.59),
                  ('#PWR031', 508.0, 161.29), ('#PWR046', 519.43, 179.07)):
    calls.append({"tool": "remove_component", "args": {"reference": ref}})
    label('SD_VDD', x, y, 0)
intent += [('J1', '4', 'SD_VDD'), ('R6', '2', 'SD_VDD'), ('R7', '2', 'SD_VDD'), ('R8', '2', 'SD_VDD'),
           ('R10', '1', 'SD_VDD'), ('R11', '1', 'SD_VDD'), ('C17', '1', 'SD_VDD'), ('C18', '1', 'SD_VDD')]
text('SD POWER: PD9 low = card powered (Q7, ~1 ms soft start; pulled off during reset).\n'
     'Before power-off drive SPI2 SCK/MOSI/CS low (pull-ups are on SD_VDD), wait >= 100 ms before re-enabling.\n'
     'PD8 (SPI2_CD_PD8) reserved for card detect: J1 symbol/footprint has no detect-switch pins - check the\n'
     'Molex 47309-2651 drawing before wiring it.', 589.28, 718.82)

# ---------------- 4. Cleanup: unused USART2 / TIM3 labels -> NC; NC flags on all unused MCU pins ----------------
for name, x, y, sx in (('USART2_TX_PA2', 162.56, 163.83, 165.1), ('USART2_RX_PA3', 162.56, 171.45, 165.1),
                       ('TIM3_CH1_PWM_PC6', 203.2, 199.39, 200.66), ('TIM3_CH2_PWM_PC7', 203.2, 196.85, 200.66)):
    calls.append({"tool": "remove_label", "args": {"text": name, "x": x, "y": y}})
    calls.append({"tool": "remove_wire", "args": {"x1": sx, "y1": y, "x2": x, "y2": y}})
NC = [2, 3, 4, 5, 7, 8, 9, 10, 11, 19, 40, 41, 42, 43, 44, 45, 46, 57, 58, 59, 60, 61, 62, 67, 68, 69, 70, 71,
      90, 91, 94, 96, 22, 25, 65, 66]
for p in NC:
    intent.append(('U1', str(p), 'NC'))
    calls.append({"tool": "no_connect_pin", "args": {"reference": "U1", "pin_name": str(p)}})

# LCSC part numbers that were missing (J1 left blank: no verified LCSC code for Molex 47309-2651)
for ref, lcsc in (('Q2', 'C15127'), ('U4', 'C6186'), ('U2', 'C5219249')):
    fields.append({"tool": "set_component_property", "args": {"reference": ref, "key": "LCSC", "value": lcsc}})

# guard: nothing already on the sheet inside the target area
x0, x1, y0, y1 = BOX
inside = lambda x, y: x0 <= float(x) <= x1 and y0 <= float(y) <= y1
root = load(SCH)
hits = [('wire', p[1], p[2]) for w in find(root, 'wire') for p in one(w, 'pts')[1:] if inside(p[1], p[2])]
hits += [('symbol', one(s, 'at')[1], one(s, 'at')[2]) for s in find(root, 'symbol') if inside(*one(s, 'at')[1:3])]
hits += [(l[0], one(l, 'at')[1], one(l, 'at')[2]) for l in root if isinstance(l, list) and
         l[0] in ('label', 'global_label', 'text', 'no_connect', 'junction') and inside(*one(l, 'at')[1:3])]
print('occupied in target area:', hits[:10])
assert not hits, 'target area not empty'
json.dump(calls + fields, open(HERE / 'batchSTEP2.json', 'w'))
json.dump(intent, open(HERE / 'data' / 'intent_step2.json', 'w'))
print('calls', len(calls), 'fields', len(fields), 'parts', len(placed))
