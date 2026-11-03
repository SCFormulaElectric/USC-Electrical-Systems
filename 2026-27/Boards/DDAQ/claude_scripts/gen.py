"""Generate the kicad-batch call lists for the MCU / ADC / CAN2 swap.

batchA.json: removals and property fixes.
batchB.json: placements, wiring, labels, power symbols.
"""
import json
from sch import load, find, one

G = 2.54
rm = json.load(open('removal.json'))
syms = json.load(open('newsyms.json'))
root = load('backup_DDAQ.kicad_sch.orig')
R2 = lambda v: round(v, 2)

# ---------------------------------------------------------------- batch A: removals
KEEP_WIRES = {((541.02, 62.23), (558.8, 62.23)), ((541.02, 64.77), (558.8, 64.77))}
A = []
for ref in ['U1', 'U5', 'U8', 'R18'] + [f'D{i}' for i in range(11, 19)] + rm['pwr'] + ['#PWR0122']:
    A.append({"tool": "remove_component", "args": {"reference": ref}})
for (a, b) in rm['wires']:
    if (tuple(a), tuple(b)) in KEEP_WIRES or (tuple(b), tuple(a)) in KEEP_WIRES:
        continue
    A.append({"tool": "remove_wire", "args": {"x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1]}})
for kind, text, (x, y) in rm['labels']:
    A.append({"tool": "remove_label", "args": {"text": text, "x": x, "y": y}})
for ref in ('#PWR0123', '#PWR0126', '#PWR0127'):
    A.append({"tool": "set_component_property", "args": {"reference": ref, "key": "Value", "value": "GND"}})
# input filter caps 100nF -> 1uF, swapped in place (same pin geometry)
caps = {}
for c in find(root, 'symbol'):
    props = {p[1]: p[2] for p in find(c, 'property')}
    if props['Reference'] in [f'C{i}' for i in range(73, 81)]:
        a = one(c, 'at')
        caps[props['Reference']] = (float(a[1]), float(a[2]), int(a[3]))
for ref, (x, y, rot) in sorted(caps.items()):
    A.append({"tool": "remove_component", "args": {"reference": ref}})
    A.append({"tool": "place_component", "args": {"lib_id": "JLCImport:CL10A105KB8NNNC", "reference": ref,
                                                  "value": "CL10A105KB8NNNC", "x": x, "y": y, "rotation": rot}})
json.dump(A, open('batchA.json', 'w'), indent=0)

# ---------------------------------------------------------------- batch B: placement + wiring
B = []
pwr_n = [200]
POS = {}  # ref -> (x, y, symbol name) for pin geometry


def place(lib, ref, value, x, y, rot=0):
    B.append({"tool": "place_component", "args": {"lib_id": f"JLCImport:{lib}", "reference": ref, "value": value,
                                                  "x": x, "y": y, "rotation": rot}})
    POS[ref] = (x, y, lib, rot)


def pin_xy(ref, num):
    x, y, lib, rot = POS[ref]
    if lib in syms:
        p = [p for p in syms[lib] if p[0] == str(num)][0]
        return R2(x + p[2]), R2(y - p[3]), {0: 'left', 180: 'right'}[p[4]]
    # 2-pin passive placed at rot 270: pin1 top, pin2 bottom
    assert rot == 270
    return (x, R2(y - 5.08), 'up') if str(num) == '1' else (x, R2(y + 5.08), 'down')


DIRV = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}
ROT = {'GND': {'down': 0, 'left': 270, 'right': 90, 'up': 180},
       '+3.3V': {'up': 0, 'left': 90, 'right': 270, 'down': 180},
       '+5V': {'up': 0, 'left': 90, 'right': 270, 'down': 180}}


def power(net, ref, num, stub=G):
    x, y, side = pin_xy(ref, num)
    dx, dy = DIRV[side]
    ex, ey = R2(x + dx * stub), R2(y + dy * stub)
    B.append({"tool": "add_wires", "args": {"wires": [{"x1": x, "y1": y, "x2": ex, "y2": ey}]}})
    pwr_n[0] += 1
    B.append({"tool": "add_power_symbol", "args": {"lib_id": f"power:{net}", "reference": f"#PWR0{pwr_n[0]}",
                                                   "x": ex, "y": ey, "rotation": ROT[net][side]}})


def net(label, *pins, direction='auto'):
    B.append({"tool": "wire_pins_to_net", "args": {"pins": [{"reference": r, "pin": str(p)} for r, p in pins],
                                                   "label_text": label, "direction": direction}})


# --- U1: STM32G474VET3 in the old spot
place('STM32G474VET3', 'U1', 'STM32G474VET3', 182.88, 173.99)
U1_SIG = {15: 'GPIO1_PC0', 16: 'GPIO2_PC1', 20: 'TIM2_CH1_FREQ1_PA0', 21: 'TIM2_CH2_FREQ2_PA1',
          22: 'USART2_TX_PA2', 25: 'USART2_RX_PA3', 26: 'SPI1_CS_PA4', 27: 'SPI1_SCK_PA5', 28: 'SPI1_MISO_PA6',
          29: 'SPI1_MOSI_PA7', 30: 'ADC_RST_PC4', 47: 'TIM2_CH3_FREQ3_PB10', 50: 'TIM2_CH4_FREQ4_PB11',
          51: 'SPI2_DAT3_PB12', 52: 'SPI2_SCK_PB13', 53: 'SPI2_MISO_PB14', 54: 'SPI2_MOSI_PB15',
          55: 'SPI2_CD_PD8', 56: 'SPI2_EN_PD9', 65: 'TIM3_CH1_PWM_PC6', 66: 'TIM3_CH2_PWM_PC7', 72: 'USB-',
          73: 'USB+', 76: 'SWDIO_PA13', 77: 'SWCLK_PA14', 82: 'CANRXPD0', 83: 'CANTXPD1', 84: 'CANSTBPD2',
          85: 'CAN2STBPD3', 92: 'CAN2RXPB5', 93: 'CAN2TXPB6', 14: 'NRST', 12: 'HSE_IN', 13: 'HSE_OUT',
          95: 'BOOT0'}
for p, lab in U1_SIG.items():
    net(lab, ('U1', p))
for p in (6, 24, 49, 64, 75, 100, 36, 37):
    power('+3.3V', 'U1', p)
for p in (23, 48, 63, 74, 99, 35):
    power('GND', 'U1', p)
# far ends of the old U1 stubs that still reach parts
B.append({"tool": "add_label", "args": {"text": "HSE_IN", "x": 223.52, "y": 144.78}})
B.append({"tool": "add_label", "args": {"text": "HSE_OUT", "x": 209.55, "y": 149.86}})
B.append({"tool": "add_label", "args": {"text": "NRST", "x": 130.81, "y": 121.92}})
# BOOT0 pulldown + 3 extra 100nF for the G474's extra VDD pins (area left of U1)
place('0603WAF1002T5E', 'R81', '0603WAF1002T5E', 106.68, 256.54, 270)
net('BOOT0', ('R81', 1), direction='up')
power('GND', 'R81', 2)
for i, ref in enumerate(('C85', 'C86', 'C87')):
    place('CC0603KRX7R9BB104', ref, 'CC0603KRX7R9BB104', 119.38 + 10.16 * i, 256.54, 270)
    power('+3.3V', ref, 1)
    power('GND', ref, 2)

# --- U5: ADS8688 in free space right of the old spot
place('ADS8688IDBTR', 'U5', 'ADS8688IDBTR', 482.6, 220.98)
for p, lab in {1: 'SPI1_MOSI_PA7', 37: 'SPI1_SCK_PA5', 38: 'SPI1_CS_PA4', 36: 'SPI1_MISO_PA6',
               2: 'ADC_RST_PC4', 5: 'ADC_REFIO', 7: 'ADC_REFCAP', 10: 'EXC_MON'}.items():
    net(lab, ('U5', p))
net('AVDD', ('U5', 9))
net('AVDD', ('U5', 30))
for p, ch in {16: 0, 18: 1, 21: 2, 23: 3, 25: 4, 27: 5, 12: 6, 14: 7}.items():
    net(f'ADC_AIN{ch}', ('U5', p))
for p in (3, 4, 6, 8, 11, 13, 15, 17, 19, 20, 22, 24, 26, 28, 29, 31, 32, 33):
    power('GND', 'U5', p)
power('+3.3V', 'U5', 34)
B.append({"tool": "no_connect_pin", "args": {"reference": "U5", "pin_name": "35"}})
# ADC support parts, row below U5
row = 266.7
ADC_PARTS = [  # ref, lib, pin1 net, pin2 net
    ('C88', 'CL21A106KAYNNNE', 'ADC_REFIO', 'GND'),
    ('C89', 'CS3225X7R226K250NRL', 'ADC_REFCAP', 'GND'),
    ('C90', 'CL21A106KAYNNNE', 'AVDD', 'GND'),
    ('C91', 'CL10A105KB8NNNC', 'AVDD', 'GND'),
    ('C92', 'CL21A106KAYNNNE', '+3.3V', 'GND'),
    ('R82', '0603WAF1002T5E', '+3.3V', 'ADC_RST_PC4'),
    ('R83', 'RT0603BRD0710KL', '+5V_SNS', 'EXC_MON'),
    ('R84', 'RT0603BRD0710KL', 'EXC_MON', 'GND'),
    ('C93', 'CC0603KRX7R9BB104', 'EXC_MON', 'GND'),
]
for i, (ref, lib, n1, n2) in enumerate(ADC_PARTS):
    place(lib, ref, lib, 457.2 + 12.7 * i, row, 270)
    for pn, n in ((1, n1), (2, n2)):
        if n in ('GND', '+3.3V', '+5V'):
            power(n, ref, pn)
        else:
            net(n, (ref, pn), direction='up' if pn == 1 else 'down')
net('ADC_REFCAP', ('C11', 1), direction='up')

# --- input clamps: bridge each channel where the BAT54S sat, then 4x PSM712 (2 channels each)
ys = [254.0, 274.32, 294.64, 314.96, 335.28, 355.6, 375.92, 396.24]
B.append({"tool": "add_wires", "args": {"wires": [{"x1": 297.18, "y1": y, "x2": 320.04, "y2": y} for y in ys]}})
for i in range(4):
    ref = f'D{11 + i}'
    place('PSM712-LF-T7', ref, 'PSM712-LF-T7', 358.14, 266.7 + 40.64 * i)
    net(f'ADC_AIN{2 * i}', (ref, 1), direction='left')
    net(f'ADC_AIN{2 * i + 1}', (ref, 2), direction='left')
    power('GND', ref, 3)

# --- U8: TCAN1044AV for CAN2 (CANH/CANL pins land on the kept wires)
place('TCAN1044AVDRQ1', 'U8', 'TCAN1044AVDRQ1', 530.86, 64.77)
net('CAN2TXPB6', ('U8', 1), direction='left')
net('CAN2RXPB5', ('U8', 4), direction='left')
net('CAN2STBPD3', ('U8', 8), direction='right')
power('GND', 'U8', 2)
power('+3.3V', 'U8', 5)
# old +3.3V node by C19 becomes +5V and feeds VCC
pwr_n[0] += 1
B.append({"tool": "add_power_symbol", "args": {"lib_id": "power:+5V", "reference": f"#PWR0{pwr_n[0]}",
                                               "x": 510.54, "y": 64.77, "rotation": 90}})
B.append({"tool": "add_wires", "args": {"wires": [{"x1": 515.62, "y1": 64.77, "x2": 518.16, "y2": 64.77}]}})
place('0603WAF1002T5E', 'R85', '0603WAF1002T5E', 528.32, 96.52, 270)
net('CAN2STBPD3', ('R85', 1), direction='up')
power('GND', 'R85', 2)
place('CC0603KRX7R9BB104', 'C94', 'CC0603KRX7R9BB104', 541.02, 96.52, 270)
power('+3.3V', 'C94', 1)
power('GND', 'C94', 2)

json.dump(B, open('batchB.json', 'w'), indent=0)
print('A', len(A), 'B', len(B))
