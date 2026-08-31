#!/usr/bin/env python3
"""
Extract a component/pin/net model for the Custom_BMS board.

Sources (all read-only):
  Custom_BMS.kicad_sch      root sheet -> sheet names, sheet files, domain boxes
  <sheet>.kicad_sch         symbol instances, lib_symbols (pin names), labels
  production/netlist.ipc    IPC-D-356 -> exact pin-level connectivity
  production/bom.csv        values + LCSC part numbers

Outputs:
  docs/netlist_graph.json   machine-readable graph
  docs/NETLIST.md           human reference

Why two connectivity sources: the .kicad_sch files store wires as geometry, so
deriving nets from them means tracing coordinates. The IPC-D-356 export already
carries exact pin->net membership, so it is used as the connectivity backbone and
the schematics supply everything IPC loses (full net names, values, sheet).

IPC-D-356 net-name quirk (verified against the raw bytes of this file):
  - the net-name field is 14 chars (cols 4-17), padded to col 20
  - long names are truncated keeping the RIGHTMOST 14 chars
  - names are upper-cased and spaces become '?'  ("/BMS Chips/TSREF" -> "MS?CHIPS/TSREF")
Full names are therefore recovered by matching that same transform against the
label set harvested from the schematics.

Run:  python3 docs/extract_netlist.py
"""

import csv
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ROOT_SCH = os.path.join(ROOT, "Custom_BMS.kicad_sch")
PCB = os.path.join(ROOT, "Custom_BMS.kicad_pcb")
IPC = os.path.join(ROOT, "production", "netlist.ipc")
BOM = os.path.join(ROOT, "production", "bom.csv")

# Domain split is documented by the two rectangles + text on the root sheet.
DOMAIN = {
    "Power": "LV (Motherboard)",
    "MCU": "LV (Motherboard)",
    "Comms Interfaces": "LV (Motherboard)",
    "BMS Chips": "HV (Daughterboard)",
    "Cell Balancing": "HV (Daughterboard)",
    "Cell Tap Filters": "HV (Daughterboard)",
}

warnings = []


def warn(msg):
    warnings.append(msg)
    print("WARN: " + msg, file=sys.stderr)


# --------------------------------------------------------------------------
# S-expression parser
# --------------------------------------------------------------------------

TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()]+')


def parse_sexp(text):
    """Parse KiCad S-expression text into nested lists. Quoted strings keep a
    leading \\x00 marker so they can be told apart from bare atoms."""
    stack = [[]]
    for m in TOKEN.finditer(text):
        tok = m.group(0)
        if tok == "(":
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif tok == ")":
            if len(stack) > 1:
                stack.pop()
        elif tok[0] == '"':
            stack[-1].append("\x00" + tok[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        else:
            stack[-1].append(tok)
    return stack[0]


def s(x):
    """Value of a node as a plain string (strips the quoted-string marker)."""
    return x[1:] if isinstance(x, str) and x.startswith("\x00") else x


def is_list(x):
    return isinstance(x, list)


def head(node):
    return node[0] if is_list(node) and node and isinstance(node[0], str) else None


def find_all(node, tag):
    """Recursively yield every sub-list whose head is `tag`."""
    if not is_list(node):
        return
    if head(node) == tag:
        yield node
    for child in node:
        if is_list(child):
            yield from find_all(child, tag)


def prop(node, name):
    """Value of a (property "name" "value") child."""
    for p in node:
        if is_list(p) and head(p) == "property" and len(p) >= 3 and s(p[1]) == name:
            return s(p[2])
    return None


# --------------------------------------------------------------------------
# IPC-D-356 connectivity
# --------------------------------------------------------------------------

def ipc_key(name):
    """Apply KiCad's IPC net-name transform: upper-case, space -> '?', keep the
    rightmost 14 characters."""
    t = name.upper().replace(" ", "?")
    return t[-14:]


def read_pcb_nets(path):
    """Full, untruncated net names declared in the .kicad_pcb as (net N "name").
    Read with a targeted regex rather than a full parse - the PCB file is large
    and nothing else is needed from it."""
    names = set()
    pat = re.compile(r'\(net\s+\d+\s+"((?:[^"\\]|\\.)*)"\)')
    text = open(path, encoding="utf-8", errors="replace").read()
    for m in pat.finditer(text):
        n = m.group(1).replace('\\"', '"').replace("\\\\", "\\")
        if n:
            names.add(n)
    return names


def read_pcb_values(path):
    """refdes -> Value as stored on the PCB footprint. The fabrication BOM is
    generated from these, so a disagreement with the schematic means the board
    would be built with the PCB's value, not the schematic's."""
    text = open(path, encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r'\(property\s+"Reference"\s+"([^"]+)"', text):
        v = re.search(r'\(property\s+"Value"\s+"([^"]*)"', text[m.end():m.end() + 2000])
        if v:
            out[m.group(1)] = v.group(1)
    return out


def read_ipc(path):
    nets = defaultdict(list)      # ipc_name -> ["U6.23", ...]
    comps = defaultdict(dict)     # refdes -> {pin: ipc_name}
    via_nets = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line[:3] not in ("317", "327"):
                continue
            net = line[3:20].strip()
            ref = line[20:26].strip()
            pin = line[27:31].strip()
            if ref == "VIA":
                via_nets.add(net)
                continue
            if not ref or not pin:
                continue
            nets[net].append("%s.%s" % (ref, pin))
            comps[ref][pin] = net
    return nets, comps, via_nets


# --------------------------------------------------------------------------
# Schematic harvest
# --------------------------------------------------------------------------

def read_root(path):
    tree = parse_sexp(open(path, encoding="utf-8", errors="replace").read())
    sheets = []
    for sh in find_all(tree, "sheet"):
        name = prop(sh, "Sheetname")
        fil = prop(sh, "Sheetfile")
        if name and fil:
            sheets.append({"name": name, "file": fil, "domain": DOMAIN.get(name, "?")})
    return sheets


def read_sheet(path, sheet_name):
    """Return symbols, lib pin maps, and labels for one sheet."""
    tree = parse_sexp(open(path, encoding="utf-8", errors="replace").read())

    # lib_symbols: lib_id -> {pin_number: pin_name}
    libpins = {}
    for libsec in find_all(tree, "lib_symbols"):
        for sym in libsec:
            if not is_list(sym) or head(sym) != "symbol":
                continue
            lib_id = s(sym[1])
            pins = {}
            for pin in find_all(sym, "pin"):
                num = name = None
                for c in pin:
                    if is_list(c) and head(c) == "name" and len(c) > 1:
                        name = s(c[1])
                    elif is_list(c) and head(c) == "number" and len(c) > 1:
                        num = s(c[1])
                if num is not None:
                    pins[num] = name if name is not None else ""
            libpins[lib_id] = pins

    # placed symbol instances (top level of the sheet only)
    symbols = {}
    for sym in tree[0] if tree and is_list(tree[0]) else []:
        if not is_list(sym) or head(sym) != "symbol":
            continue
        ref = prop(sym, "Reference")
        if not ref or ref.startswith("#"):   # #PWR / #FLG are power/flag symbols
            continue
        lib_id = None
        for c in sym:
            if is_list(c) and head(c) == "lib_id" and len(c) > 1:
                lib_id = s(c[1])
        symbols[ref] = {
            "ref": ref,
            "value": prop(sym, "Value"),
            "footprint": prop(sym, "Footprint"),
            "lib_id": lib_id,
            "sheet": sheet_name,
            "datasheet": prop(sym, "Datasheet"),
            "description": prop(sym, "Description"),
        }

    labels = {"global": set(), "local": set()}
    for tag, key in (("global_label", "global"), ("label", "local"),
                     ("hierarchical_label", "hier")):
        for lb in find_all(tree, tag):
            if len(lb) > 1 and isinstance(lb[1], str):
                if key == "hier":
                    warn("unexpected hierarchical_label %r in %s" % (s(lb[1]), sheet_name))
                else:
                    labels[key].add(s(lb[1]))
    return symbols, libpins, labels


# --------------------------------------------------------------------------
# BOM
# --------------------------------------------------------------------------

def read_bom(path):
    out = {}
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh):
            desigs = [d.strip() for d in (row.get("Designator") or "").split(",")]
            for d in desigs:
                if d:
                    out[d] = {
                        "value": (row.get("Value") or "").strip(),
                        "footprint": (row.get("Footprint") or "").strip(),
                        "lcsc": (row.get("LCSC Part #") or "").strip(),
                    }
    return out


# --------------------------------------------------------------------------
# Net classification
# --------------------------------------------------------------------------

POWER_NETS = {"+3.3V", "+5V", "+12V", "GND", "LV_GND", "VBAT", "CELL_TOP"}


def classify(full, members):
    if full in POWER_NETS or re.match(r"^[+-]?\d+(\.\d+)?V$", full):
        return "power"
    if full.startswith("NET-("):
        return "auto"          # KiCad-generated name; no label in schematic
    if re.match(r"^VC\d+$", full):
        return "cell-sense"
    if re.match(r"^CB\d+$", full):
        return "cell-balance"
    if re.match(r"^CELL\d+[+-]$", full):
        return "cell-tap"
    if "COM" in full.upper():
        return "daisy-chain"
    if "CAN" in full.upper():
        return "can"
    if full.upper().startswith("SPI"):
        return "spi"
    return "signal"


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    sheets = read_root(ROOT_SCH)
    print("root sheet: %d sub-sheets" % len(sheets))

    all_syms, all_libpins, sheet_labels = {}, {}, {}
    for sh in sheets:
        p = os.path.join(ROOT, sh["file"])
        if not os.path.exists(p):
            warn("missing sheet file %s" % sh["file"])
            continue
        syms, libpins, labels = read_sheet(p, sh["name"])
        for ref, d in syms.items():
            if ref in all_syms:
                warn("duplicate refdes %s (%s and %s)" % (ref, all_syms[ref]["sheet"], sh["name"]))
            else:
                all_syms[ref] = d
        all_libpins.update(libpins)
        sheet_labels[sh["name"]] = labels
        print("  %-18s %3d symbols  %2d global  %2d local"
              % (sh["name"], len(syms), len(labels["global"]), len(labels["local"])))

    nets_ipc, comps_ipc, via_nets = read_ipc(IPC)
    print("IPC: %d components, %d nets" % (len(comps_ipc), len(nets_ipc)))
    bom = read_bom(BOM)
    print("BOM: %d designators" % len(bom))
    pcb_values = read_pcb_values(PCB)
    print("PCB: %d footprint values" % len(pcb_values))

    # ---- resolve IPC truncations against the PCB's full net names ----
    # Custom_BMS.kicad_pcb declares every net untruncated as (net N "name"),
    # so it is the authoritative source; no reconstruction/guessing needed.
    pcb_names = read_pcb_nets(PCB)
    print("PCB: %d net names" % len(pcb_names))

    by_key = defaultdict(set)
    for full in pcb_names:
        by_key[ipc_key(full)].add(full)

    resolved, unresolved = {}, []
    for n in nets_ipc:
        exact = by_key.get(ipc_key(n), set())
        if len(exact) == 1:
            resolved[n] = next(iter(exact))
        elif len(exact) > 1:
            pick = sorted(exact, key=lambda c: (-len(c), c))[0]
            resolved[n] = pick
            warn("net %r maps to several PCB names %s (picked %r)" % (n, sorted(exact), pick))
        else:
            resolved[n] = n
            unresolved.append(n)
            warn("net %r has no matching PCB net name (kept truncated)" % n)

    # cross-check: every schematic label should surface as a real net.
    # A local label that shares a wire with a global label is absorbed into the
    # global net (KiCad keeps the stronger name) - that is expected, not a fault.
    resolved_set = set(resolved.values())
    merged = []
    for sh_name, labels in sheet_labels.items():
        for g in labels["global"]:
            if g not in resolved_set:
                warn("global label %r on sheet %s has no net in the PCB netlist" % (g, sh_name))
        for l in labels["local"]:
            if "/%s/%s" % (sh_name, l) in resolved_set:
                continue
            if l in resolved_set:
                merged.append((sh_name, l))       # absorbed by the global of the same name
            else:
                warn("local label %r on sheet %s has no net in the PCB netlist" % (l, sh_name))
    for sh_name, l in merged:
        print("  info: local label %r on %s merged into global net %r" % (l, sh_name, l))

    # ---- assemble model ----
    components = {}
    value_mismatches = []
    for ref in sorted(set(list(comps_ipc) + list(all_syms))):
        sym = all_syms.get(ref, {})
        b = bom.get(ref, {})
        lib_id = sym.get("lib_id")
        pinmap = all_libpins.get(lib_id, {}) if lib_id else {}
        pins = {}
        for pin, netname in sorted(comps_ipc.get(ref, {}).items(),
                                   key=lambda kv: (len(kv[0]), kv[0])):
            pins[pin] = {"name": pinmap.get(pin), "net": resolved.get(netname, netname)}
        sheet = sym.get("sheet")
        sch_val = sym.get("value")
        pcb_val = pcb_values.get(ref)
        components[ref] = {
            "ref": ref,
            "value": sch_val or b.get("value"),
            "pcb_value": pcb_val,
            "footprint": sym.get("footprint") or b.get("footprint"),
            "lcsc": b.get("lcsc"),
            "lib_id": lib_id,
            "sheet": sheet,
            "domain": DOMAIN.get(sheet) if sheet else None,
            "pin_count": len(pins),
            "pins": pins,
        }
        # The fabrication BOM comes from the PCB, so a mismatch means the board
        # would be built with the PCB value and the schematic edit lost.
        if sheet and sch_val and pcb_val and sch_val.strip() != pcb_val.strip():
            value_mismatches.append({"ref": ref, "sheet": sheet,
                                     "schematic": sch_val, "pcb": pcb_val})
            warn("value mismatch %s: schematic=%r but PCB/BOM=%r"
                 % (ref, sch_val, pcb_val))
        if ref not in all_syms:
            warn("component %s is in the PCB netlist but not in any schematic sheet" % ref)
        if ref not in comps_ipc:
            warn("component %s is in the schematic but has no pads in the PCB netlist" % ref)

    nets_out = {}
    for n, members in nets_ipc.items():
        full = resolved.get(n, n)
        entry = nets_out.setdefault(full, {
            "name": full, "ipc_name": n, "class": classify(full, members),
            "members": [], "sheets": set(), "has_vias": n in via_nets,
        })
        entry["members"].extend(sorted(members))
        for m in members:
            sh = components.get(m.split(".")[0], {}).get("sheet")
            if sh:
                entry["sheets"].add(sh)
    for e in nets_out.values():
        e["members"] = sorted(set(e["members"]))
        e["sheets"] = sorted(e["sheets"])
        e["pin_count"] = len(e["members"])

    model = {
        "board": "Custom_BMS",
        "source": {
            "root_schematic": os.path.basename(ROOT_SCH),
            "connectivity": "production/netlist.ipc (IPC-D-356, derived from the PCB)",
            "note": "Net names reconstructed from schematic labels; see module docstring.",
        },
        "sheets": sheets,
        "counts": {
            "components": len(components),
            "nets": len(nets_out),
            "ipc_components": len(comps_ipc),
            "ipc_nets": len(nets_ipc),
        },
        "components": components,
        "nets": nets_out,
        "value_mismatches": value_mismatches,
        "warnings": warnings,
    }

    out = os.path.join(HERE, "netlist_graph.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(model, fh, indent=1, sort_keys=True)
    print("\nwrote %s" % out)
    print("  components=%d nets=%d warnings=%d"
          % (len(components), len(nets_out), len(warnings)))
    return model


if __name__ == "__main__":
    main()
