#!/usr/bin/env python3
"""Convert global GND labels to standard power:GND symbols without moving wires.

The existing text is preserved outside the replaced labels and added library entry.
Power symbols have no footprint, BOM entry, or placement entry. The script refuses
to overwrite the input. Validate the result with KiCad ERC and netlist comparison.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import uuid


TOKENS = re.compile(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]')


def children(source):
    depth = 0
    start = None
    for token in TOKENS.finditer(source):
        value = token.group()
        if value == '(':
            depth += 1
            if depth == 2:
                start = token.start()
        elif value == ')':
            if depth == 2:
                yield start, token.end(), source[start:token.end()]
            depth -= 1
    if depth:
        raise ValueError('Unbalanced source')


def tag(source):
    return next(TOKENS.finditer(source[1:])).group()


def form(source, name):
    return next((text for _, _, text in children(source) if tag(text) == name), None)


def quoted(source, name):
    text = form(source, name)
    return json.loads(list(TOKENS.finditer(text))[2].group())


def coordinates(source, name='at'):
    text = source if tag(source) == name else form(source, name)
    return [float(t.group()) for t in list(TOKENS.finditer(text))[2:-1]]


def number(value):
    return format(value, '.8f').rstrip('0').rstrip('.')


def convert(source, library):
    objects = list(children(source))
    labels = [(a, b, text) for a, b, text in objects
              if re.match(r'\(global_label\s+"GND"(?=\s|\))', text)]
    if not labels:
        raise ValueError('No global GND labels found; input may already be converted')
    root_id = quoted(source, 'uuid')
    lib_a, lib_b, lib_text = next(x for x in objects if tag(x[2]) == 'lib_symbols')
    if re.search(r'\(symbol\s+"power:GND"', lib_text):
        raise ValueError('Existing power:GND definition requires explicit review')
    ground = next(text for _, _, text in children(library)
                  if re.match(r'\(symbol\s+"GND"(?=\s|\))', text))
    ground = ground.replace('(symbol "GND"', '(symbol "power:GND"', 1)
    assert re.search(r'\(power\s+global\)', ground)
    pin = next(text for _, _, text in children(
        next(text for _, _, text in children(ground) if text.startswith('(symbol "GND_1_1"')))
        if tag(text) == 'pin')
    assert coordinates(pin)[:2] == [0, 0]
    assert re.search(r'\(length\s+0\)', pin)

    wires = []
    for _, _, text in objects:
        if tag(text) != 'wire':
            continue
        pts = form(text, 'pts')
        wires.append([coordinates(p, 'xy') for _, _, p in children(pts)])
    refs = set(re.findall(r'\(property\s+"Reference"\s+"([^"]+)"', source))
    changes = [(lib_a, lib_b, lib_text[:-1] + '\n\t\t' + ground + '\n\t)')]
    records = []
    counter = 1
    for a, b, label in labels:
        x, y, _ = coordinates(label)
        old_id = quoted(label, 'uuid')
        # A downward symbol can touch the next pin's wire in dense IC pin rows.
        # Face away from the existing wire at those positions; the connection
        # point remains identical and the GND text stays outside the wire.
        crowded = False
        for points in wires:
            if len(points) != 2:
                continue
            (x1, y1), (x2, y2) = points
            if abs(y1 - y2) < 1e-8 and y + .3 < y1 <= y + 4.6:
                if max(x1, x2) >= x - 1.5 and min(x1, x2) <= x + 1.5:
                    crowded = True
        angle = 0
        if crowded:
            neighbors = [other for points in wires if len(points) == 2
                         for here, other in [(points[0], points[1]), (points[1], points[0])]
                         if abs(here[0] - x) < 1e-8 and abs(here[1] - y) < 1e-8]
            angle = 270 if any(p[0] > x for p in neighbors) else 90
        while f'#PWR{counter:03}' in refs:
            counter += 1
        reference = f'#PWR{counter:03}'
        refs.add(reference)
        counter += 1
        symbol_id = str(uuid.uuid5(uuid.UUID(old_id), 'standard-power:GND'))
        pin_id = str(uuid.uuid5(uuid.UUID(symbol_id), 'pin:1'))
        value_x, value_y = ((x + 4.6, y) if angle == 90 else
                            (x - 4.6, y) if angle == 270 else (x, y + 3.81))
        replacement = f'''(symbol
\t\t(lib_id "power:GND")
\t\t(at {number(x)} {number(y)} {angle})
\t\t(unit 1)
\t\t(in_bom no)
\t\t(on_board no)
\t\t(in_pos_files no)
\t\t(uuid "{symbol_id}")
\t\t(property "Reference" "{reference}" (at {number(x)} {number(y + 6.35)} {angle})
\t\t\t(effects (font (size 1 1)) (hide yes)))
\t\t(property "Value" "GND" (at {number(value_x)} {number(value_y)} {angle})
\t\t\t(effects (font (size 1 1))))
\t\t(pin "1" (uuid "{pin_id}"))
\t\t(instances (project "BSPD_2027"
\t\t\t(path "/{root_id}" (reference "{reference}") (unit 1))))
\t)'''
        changes.append((a, b, replacement))
        records.append({'reference': reference, 'x_mm': x, 'y_mm': y,
                        'angle_deg': angle, 'old_label_uuid': old_id,
                        'new_symbol_uuid': symbol_id})
    converted = source
    for a, b, text in sorted(changes, reverse=True):
        converted = converted[:a] + text + converted[b:]
    # Every pre-existing top-level object other than those labels/library cache
    # must be byte-identical, including all physical symbols and wire geometry.
    old_unchanged = [text for _, _, text in objects
                     if tag(text) != 'lib_symbols' and
                     not re.match(r'\(global_label\s+"GND"(?=\s|\))', text)]
    new_unchanged = [text for _, _, text in children(converted)
                     if tag(text) != 'lib_symbols' and
                     not re.match(r'\(symbol\s+\(lib_id\s+"power:GND"', text)]
    assert old_unchanged == new_unchanged
    assert len(re.findall(r'\(lib_id\s+"power:GND"', converted)) == len(labels)
    return converted, {
        'converted_labels': len(labels), 'net_name': 'GND',
        'standard_symbol': 'power:GND',
        'other_existing_objects_byte_identical': True,
        'anchor_positions_unchanged': True,
        'orientation_counts': dict(collections.Counter(r['angle_deg'] for r in records)),
        'before_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'after_sha256': hashlib.sha256(converted.encode()).hexdigest(),
        'placements': records,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--library', type=Path, default=Path(
        '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/power.kicad_sym'))
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    if args.input.resolve() == args.output.resolve():
        p.error('Input and output must differ')
    converted, report = convert(args.input.read_text(), args.library.read_text())
    args.output.write_text(converted)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'placements'}, indent=2))


if __name__ == '__main__':
    main()
