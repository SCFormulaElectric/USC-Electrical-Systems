"""Text-level fixes mcp-server-kicad has no tool for (run with KiCad closed, then verify with a netlist diff):
- D19 (ESD2CANFD24DBZRQ1) cached symbol: pin 1 "IO" -> "IO1", pin 2 "GND" -> "IO2", both power_in -> passive.
  Pin numbers are unchanged, so connectivity is unchanged; this removes the bogus ground_pin_not_ground ERC item.
- Hide the Reference field of every power symbol that shows it (the existing ones are all hidden).
Usage: python post_step2.py path/to/DDAQ.kicad_sch
"""
import re
import sys

path = sys.argv[1]
t = open(path, 'rb').read().decode('utf-8')


def block_end(s, i):
    """Index just past the s-expression that starts at s[i] == '('."""
    depth, j, n = 0, i, len(s)
    while j < n:
        c = s[j]
        if c == '"':
            j += 1
            while s[j] != '"':
                j += 2 if s[j] == '\\' else 1
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    raise ValueError('unbalanced')


# --- D19 cached symbol pins
start = t.index('(symbol "easyeda2kicad:ESD2CANFD24DBZRQ1"')
end = block_end(t, start)
sym = t[start:end]
fixed, n_pins = sym, 0
for m in list(re.finditer(r'\(pin power_in line', sym))[::-1]:
    pb = block_end(sym, m.start())
    pin = sym[m.start():pb]
    num = re.search(r'\(number "(\d+)"', pin).group(1)
    if num in ('1', '2'):
        new = pin.replace('(pin power_in line', '(pin passive line', 1)
        new = re.sub(r'\(name "[^"]*"', f'(name "IO{num}"', new, count=1)
        fixed = fixed[:m.start()] + new + fixed[pb:]
        n_pins += 1
assert n_pins == 2 or '(name "IO2"' in sym, n_pins  # 0 when already fixed
t = t[:start] + fixed + t[end:]

# --- hide power-symbol references (top-level placed symbols only; lib_symbols is skipped)
ls = t.index('(lib_symbols')
ls_end = block_end(t, ls)
out, pos, hidden = [], 0, 0
for m in re.finditer(r'\(lib_id "power:[^"]+"\)', t):
    if ls <= m.start() < ls_end:
        continue
    sym_start = t.rindex('(symbol', 0, m.start())
    sym_end = block_end(t, sym_start)
    r = t.find('(property "Reference" "#', sym_start, sym_end)
    if r < 0:
        continue
    r_end = block_end(t, r)
    prop = t[r:r_end]
    if '(hide yes)' in prop:
        continue
    at = re.search(r'\(at [^)]*\)(\r?\n)([\t ]*)', prop)
    ins = r + at.end(1)
    indent = at.group(2)
    out.append(t[pos:ins])
    out.append(f'{indent}(hide yes){at.group(1)}')
    pos = ins
    hidden += 1
out.append(t[pos:])
t = ''.join(out)
open(path, 'wb').write(t.encode('utf-8'))
print('D19 pins fixed:', n_pins, ' power refs hidden:', hidden)
