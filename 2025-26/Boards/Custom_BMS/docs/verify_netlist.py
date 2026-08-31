#!/usr/bin/env python3
"""
Verify docs/netlist_graph.json against its raw sources.

Every check re-derives from the source files with code independent of
extract_netlist.py, so a bug in the extractor cannot hide itself here.

Run:  python3 docs/verify_netlist.py     (exit 0 = all checks passed)
"""

import collections
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FW = os.path.expanduser("~/Desktop/USC-Communications-Systems/Custom_BMS")

model = json.load(open(os.path.join(HERE, "netlist_graph.json"), encoding="utf-8"))
C, N = model["components"], model["nets"]
fails = []


def check(label, ok, detail=""):
    print("%s %s%s" % ("PASS" if ok else "FAIL", label, ("  " + detail) if detail else ""))
    if not ok:
        fails.append(label)


# 1. every BOM designator is modelled
bom = set()
with open(os.path.join(ROOT, "production", "bom.csv"), encoding="utf-8-sig", newline="") as fh:
    for row in csv.DictReader(fh):
        for d in (row.get("Designator") or "").split(","):
            if d.strip():
                bom.add(d.strip())
missing = sorted(bom - set(C))
check("BOM designators all present", not missing, "%d designators, %d missing %s" % (len(bom), len(missing), missing[:5]))

# 2. counts match an independent re-parse of the IPC netlist
nets2, comps2 = collections.defaultdict(set), collections.defaultdict(dict)
with open(os.path.join(ROOT, "production", "netlist.ipc"), encoding="utf-8", errors="replace") as fh:
    for ln in fh:
        if ln[:3] not in ("317", "327"):
            continue
        net, ref, pin = ln[3:20].strip(), ln[20:26].strip(), ln[27:31].strip()
        if not ref or ref == "VIA" or not pin:
            continue
        nets2[net].add("%s.%s" % (ref, pin))
        comps2[ref][pin] = net
check("component/net counts match IPC",
      len(comps2) == len(C) and len(nets2) == len(N),
      "IPC %d/%d vs model %d/%d" % (len(comps2), len(nets2), len(C), len(N)))

# 3. every net name resolved to a real PCB net name
pcb = set()
pat = re.compile(r'\(net\s+\d+\s+"((?:[^"\\]|\\.)*)"\)')
text = open(os.path.join(ROOT, "Custom_BMS.kicad_pcb"), encoding="utf-8", errors="replace").read()
for m in pat.finditer(text):
    if m.group(1):
        pcb.add(m.group(1).replace('\\"', '"').replace("\\\\", "\\"))
unresolved = sorted(n for n in N if n not in pcb)
check("all net names are real PCB nets", not unresolved,
      "%d PCB names, %d unresolved %s" % (len(pcb), len(unresolved), unresolved[:5]))

# 4. each modelled pin's net reduces back to the IPC truncation
bad = [(r, p) for r in C for p, d in C[r]["pins"].items()
       if d["net"].upper().replace(" ", "?")[-14:] != comps2[r][p].upper()]
check("pin nets round-trip to IPC", not bad, "%d mismatches %s" % (len(bad), bad[:5]))

# 5. no modelled member is absent from the raw IPC
phantom = [m for e in N.values() for m in e["members"]
           if comps2.get(m.split(".")[0], {}).get(m.split(".")[1]) is None]
check("no phantom net members", not phantom, "%d phantom" % len(phantom))

# 6. firmware pin defines agree with hardware
h = open(os.path.join(FW, "Core", "Inc", "main.h"), encoding="utf-8", errors="replace").read()
port_net = {}
for p, d in C["U6"]["pins"].items():
    mm = re.match(r"^(P[A-H]\d+)", d["name"] or "")
    if mm:
        port_net[mm.group(1)] = d["net"]
expect = {"SPI_RDY": ("PA3", "SPI_RDY"), "SPI_nCS": ("PA4", "SPI1_nSS"),
          "nFAULT": ("PA8", "nFAULT"), "Blinky_LED": ("PB0", "Net-(U6-PB0)")}
fw_bad = []
for name, (port, net) in expect.items():
    num = re.search(r"#define\s+%s_Pin\s+GPIO_PIN_(\d+)" % name, h)
    prt = re.search(r"#define\s+%s_GPIO_Port\s+GPIO([A-H])" % name, h)
    if not num or not prt:
        fw_bad.append("%s: define missing" % name)
        continue
    got = "P%s%s" % (prt.group(1), num.group(1))
    if got != port or port_net.get(port) != net:
        fw_bad.append("%s: main.h=%s hw=%s/%s" % (name, got, port, port_net.get(port)))
check("firmware main.h agrees with hardware", not fw_bad, "; ".join(fw_bad))

print("\n%s (%d/%d checks passed)"
      % ("ALL CHECKS PASSED" if not fails else "FAILURES: %s" % fails, 6 - len(fails), 6))
sys.exit(1 if fails else 0)
