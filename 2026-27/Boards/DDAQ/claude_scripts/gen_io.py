"""Frequency inputs x4, spare MCU-ADC analog x2, USB ESD, status LEDs, SWD header -> batchIO.json + intent_io.json."""
import json
import math
from sch import load, find, one

LIBPATH = 'C:/Git/USC-Electrical-Systems/2026-27/Boards/DDAQ/DDAQ/JLCImport.kicad_sym'
SCH = 'C:/Git/USC-Electrical-Systems/2026-27/Boards/DDAQ/DDAQ/DDAQ.kicad_sch'
SYMS = json.load(open('libsyms.json'))
BY_LCSC = {v['lcsc']: k for k, v in SYMS.items()}
POWER = {'GND', '+3.3V', '+5V'}
ROT = {'GND': {'down': 0, 'left': 270, 'right': 90, 'up': 180},
       '+3.3V': {'up': 0, 'left': 90, 'right': 270, 'down': 180}}
R2 = lambda v: round(v, 2)
calls, fields, placed, intent = [], [], {}, []
pwr_n = [700]


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


def part2(ref, lcsc, x, y, n1, n2):
    place(ref, lcsc, x, y, 270)
    conn(ref, 1, n1)
    conn(ref, 2, n2)


def ic(ref, lcsc, x, y, nets):
    place(ref, lcsc, x, y)
    for num, net in nets.items():
        conn(ref, num, net)


R1K, R2K2, R10K, R15K, C1N, C100N = 'C21190', 'C4190', 'C25804', 'C22809', 'C44369', 'C14663'
r = iter(range(118, 200))
c = iter(range(152, 250))
d = iter(range(24, 60))

# --- frequency inputs: pull-up to the channel's own protected 5 V, 10k + BAT54S clamp to 3.3 V + 1 nF (16 kHz),
#     Schmitt buffer (SN74LVC2G17, 3.3 V) into TIM2 input capture
TIM = ['TIM2_CH1_FREQ1_PA0', 'TIM2_CH2_FREQ2_PA1', 'TIM2_CH3_FREQ3_PB10', 'TIM2_CH4_FREQ4_PB11']
for k in range(4):
    y = 139.7 + 40.64 * k
    n_in, n_f = f'FREQ{k + 1}_IN', f'FREQ{k + 1}_F'
    part2(f'R{next(r)}', R2K2, 640.08, y, f'+5V_WS{k + 1}', n_in)
    part2(f'R{next(r)}', R10K, 652.78, y, n_in, n_f)
    ic(f'D{next(d)}', 'C8592', 671.83, y, {1: 'GND', 2: '+3.3V', 3: n_f})
    part2(f'C{next(c)}', C1N, 692.15, y, n_f, 'GND')
ic('U20', 'C10429', 734.06, 160.02, {1: 'FREQ1_F', 6: TIM[0], 3: 'FREQ2_F', 4: TIM[1], 2: 'GND', 5: '+3.3V'})
ic('U21', 'C10429', 734.06, 241.3, {1: 'FREQ3_F', 6: TIM[2], 3: 'FREQ4_F', 4: TIM[3], 2: 'GND', 5: '+3.3V'})
part2(f'C{next(c)}', C100N, 762.0, 175.26, '+3.3V', 'GND')
part2(f'C{next(c)}', C100N, 762.0, 256.54, '+3.3V', 'GND')

# --- spare analog on MCU ADC: 10k/15k divider (0-5 V -> 0-3.0 V, open wire reads 0), BAT54S clamp, 100 nF
for j, (n_in, n_adc) in enumerate((('AI8', 'AI8_ADC_PC5'), ('AI9', 'AI9_ADC_PE8'))):
    y = 314.96 + 40.64 * j
    part2(f'R{next(r)}', R10K, 640.08, y, n_in, n_adc)
    part2(f'R{next(r)}', R15K, 652.78, y, n_adc, 'GND')
    ic(f'D{next(d)}', 'C8592', 671.83, y, {1: 'GND', 2: '+3.3V', 3: n_adc})
    part2(f'C{next(c)}', C100N, 692.15, y, n_adc, 'GND')

# --- USB ESD (USBLC6-2: 1/6 = line 1, 3/4 = line 2, 5 = VBUS, 2 = GND)
ic('U22', 'C7519', 820.42, 152.4, {1: 'USB+', 6: 'USB+', 3: 'USB-', 4: 'USB-', 5: 'VBUS', 2: 'GND'})

# --- status LEDs (MCU sources ~1.3 mA through 1k)
for i, (lcsc, net, a, k) in enumerate((('C2287', 'LED_CAN_PE0', 1, 2), ('C2286', 'LED_FAULT_PE1', 1, 2),
                                       ('C2289', 'LED_STAT_PE2', 2, 1))):
    x = 800.1 + 15.24 * i
    rr, dd = f'R{next(r)}', f'D{next(d)}'
    part2(rr, R1K, x, 228.6, net, f'{dd}_A')
    place(dd, lcsc, x, 254.0, 270)
    conn(dd, a, f'{dd}_A')
    conn(dd, k, 'GND')

# --- SWD header 1x4 2.54 mm: 1 GND, 2 3.3V, 3 SWDIO, 4 SWCLK
ic('J5', 'C2691448', 825.5, 314.96, {1: 'GND', 2: '+3.3V', 3: 'SWDIO_PA13', 4: 'SWCLK_PA14'})

# --- MCU pins
for p, net in {31: 'AI8_ADC_PC5', 39: 'AI9_ADC_PE8', 97: 'LED_CAN_PE0', 98: 'LED_FAULT_PE1', 1: 'LED_STAT_PE2'}.items():
    intent.append(('U1', str(p), net))
    calls.append({"tool": "wire_pins_to_net", "args": {"pins": [{"reference": "U1", "pin": str(p)}], "label_text": net}})

# guard: nothing already on the sheet inside the target area
root = load(SCH)
hits = []
for w in find(root, 'wire'):
    for p in one(w, 'pts')[1:]:
        if 600 <= float(p[1]) <= 880 and 115 <= float(p[2]) <= 365:
            hits.append(('wire', p[1], p[2]))
for s in find(root, 'symbol'):
    a = one(s, 'at')
    if 600 <= float(a[1]) <= 880 and 115 <= float(a[2]) <= 365:
        hits.append(('symbol', a[1], a[2]))
for l in [x for x in root if isinstance(x, list) and x[0] in ('label', 'global_label', 'text')]:
    a = one(l, 'at')
    if 600 <= float(a[1]) <= 880 and 115 <= float(a[2]) <= 365:
        hits.append(('label', l[1], a[1], a[2]))
print('occupied in target area:', hits[:10])
json.dump(calls + fields, open('batchIO.json', 'w'))
json.dump(intent, open('intent_io.json', 'w'))
print('calls', len(calls), 'fields', len(fields), 'parts', len(placed))
