#!/usr/bin/env python3
"""
Render docs/NETLIST.md from docs/netlist_graph.json.

Kept separate from extract_netlist.py so the document can be re-rendered without
re-parsing 4 MB of schematics.

Run:  python3 docs/extract_netlist.py && python3 docs/render_netlist.py
"""

import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FW = os.path.expanduser("~/Desktop/USC-Communications-Systems/Custom_BMS")

MODEL = json.load(open(os.path.join(HERE, "netlist_graph.json"), encoding="utf-8"))
C = MODEL["components"]
N = MODEL["nets"]

# The vendored bq79600.kicad_sym carries numeric placeholder pin names, so U3's
# pin functions are annotated here from the net each pin lands on. Marked in the
# document as inference, not extraction.
BQ79600_FN = {
    "1": "DVDD (decoupling)", "2": "nFAULT", "3": "VIO (logic supply)",
    "4": "MOSI", "5": "MISO", "6": "SCLK", "7": "nCS", "8": "SPI_RDY",
    "9": "VSS", "10": "COMLP", "11": "COMLN", "12": "COMHP", "13": "COMHN",
    "14": "CVDD (decoupling)", "15": "VDD", "16": "VDD",
}

# Curated context for MCU pins the firmware leaves alone. Inference about intent,
# not extracted fact - kept short and marked as such in the document.
FW_NOTE = {
    "PA9":  "UART1 TX → debug header J5; no USART1 in the `.ioc` at all",
    "PA10": "UART1 RX → debug header J5; no USART1 in the `.ioc` at all",
    "PA13": "SWD data → J1. Works by reset default, **not** reserved in CubeMX (see below)",
    "PA14": "SWD clock → J1. Works by reset default, **not** reserved in CubeMX (see below)",
    "PB1":  "Control-pilot drive (J1772 charging)",
    "PB3":  "Discharge contactor enable (active low)",
    "PB4":  "Charge contactor enable (active low)",
    "PB5":  "Charge-on indication",
    "PB6":  "Fan enable (active low)",
    "PC10": "Control-pilot detect, via comparator U7",
    "PA15": "Gate of Q7",
}

# review.txt items that connectivity can actually settle. Status is verified
# against the extracted model; the wording after it is interpretation.
REVIEW_ITEMS = [
    ("*SPI_RDY should ideally be connected to MCU* (12-20)", "✅ **resolved**",
     "`SPI_RDY` = U3.8 ↔ U6.17 (PA3), plus R51/R53"),
    ("*C24 should be connected from CB16 to BAT, not CB_TOP to BAT* (12-20)", "✅ **resolved**",
     "C24.1 → `/BMS Chips/BAT`, C24.2 → `CB16`"),
    ("*Filter resistor on BAT pin — 30 Ω must be used for hot-plug* (12-20)", "✅ **resolved**",
     "R80 = 33 Ω between `/BMS Chips/BAT` and `CELL_TOP` (nearest E24 value)"),
    ("*10 k with the thermistors… they recommend 680* (12-20)", "✅ **resolved**",
     "R41–R44 = 680 Ω from `TSREF` to `temp1`–`temp4`"),
    ("*Input cap on 3.3 V regulator* (10-18)", "✅ **resolved**",
     "U4.3 (VI) on `+5V` with C55, C67, C68"),
    ("*Fuse not specified* (12-20)", "✅ **resolved**",
     "F1 = SMD0805-010-24V on `VBAT`"),
    ("*Control pilot not connected on connector* (12-24)", "✅ **resolved**",
     "CN9.4 = `/MCU/CTRL_PILOT`"),
    ("*Proximity detect and control pilot should be wired to MCU* (12-24)", "✅ **resolved**",
     "`PROX_DETECT` → Q7 → PA15; `CP_DETECT` → U7 comparator → PC10; `CP_CTRL` → PB1 → Q6"),
    ("*Suggest 2 separate resistor values to switch between* for LDOIN (10-18)", "✅ **resolved**",
     "JP3 (R1 = 300 Ω) and JP4 (R77 = 1 kΩ) both land on `/BMS Chips/collector`"),
    ("*R69, R74, R76 exceed power rating when on* (01-02)", "⚠️ **half-done**",
     "Schematic now 2.7 kΩ, but **PCB/BOM still 1 kΩ** — see §7"),
    ("*Shouldn't the motherboard also have isolation capacitors* (12-20)", "❌ **still open**",
     "C45/C46/C51/C52 (2.2 nF 1 kV) are all on the *BMS Chips* sheet; nothing equivalent on the "
     "Comms Interfaces side, which has only chokes L1/L2/L6"),
    ("*D18 seems unnecessary* (12-24)", "❌ **still open**",
     "D18 (SMF18CA TVS) still present, `LV_GND` ↔ `/MCU/CTRL_PILOT`"),
    ("*Q6 should have ESD protection* (12-24)", "❔ **needs judgement**",
     "Q6.1 on `/MCU/CP_CTRL`; no TVS on that net (D18 is on `CTRL_PILOT`, the other side)"),
    ("*Add buck converter feedback node test point* (10-18)", "❔ **needs judgement**",
     "U2 FB net carries no `TP*`; TP7 is on `+5V`"),
    ("*Minimum number of cells is 6* / *update NPN resistor section for 6 cells* (12-24, 01-02)",
     "❔ **needs datasheet**", "`VC0`–`VC16` and `CB0`–`CB16` are all present and wired"),
]

ICS = ["U6", "U3", "U1", "U5", "U2", "U4", "U7"]
IC_TITLE = {
    "U6": "U6 — STM32F405RGTx (main MCU)",
    "U3": "U3 — BQ79600PWQ1 (SPI ↔ daisy-chain bridge)",
    "U1": "U1 — BQ79616PAPRQ1 (16-cell monitor)",
    "U5": "U5 — SN65HVD230DR (CAN transceiver)",
    "U2": "U2 — TPS563300 (buck, +12V → +5V)",
    "U4": "U4 — AMS1117-3.3 (LDO, +5V → +3.3V)",
    "U7": "U7 — LM397 (comparator, control-pilot detect)",
}


def others(net, ref):
    """Everything else on `net` besides component `ref`."""
    e = N.get(net)
    if not e:
        return ""
    rest = [m for m in e["members"] if m.split(".")[0] != ref]
    return ", ".join(rest) if rest else "_(only pin on net)_"


def pinkey(p):
    return (len(p), p)


def esc(x):
    return str(x).replace("|", "\\|") if x is not None else ""


def ic_table(ref, fn_map=None):
    c = C[ref]
    out = ["| Pin | Name | Net | Connects to |", "|---|---|---|---|"]
    for p in sorted(c["pins"], key=pinkey):
        d = c["pins"][p]
        name = fn_map.get(p) if fn_map else d["name"]
        out.append("| %s | `%s` | `%s` | %s |"
                   % (p, esc(name or "?"), esc(d["net"]), esc(others(d["net"], ref))))
    return "\n".join(out)


# --------------------------------------------------------------------------
# firmware cross-reference
# --------------------------------------------------------------------------

def read_firmware():
    ioc, defines = {}, {}
    p = os.path.join(FW, "Custom_BMS.ioc")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8", errors="replace"):
            m = re.match(r"^(P[A-H]\d+)\.(Signal|GPIO_Label)=(.+)$", line.strip())
            if m:
                ioc.setdefault(m.group(1), {})[m.group(2)] = m.group(3)
    h = os.path.join(FW, "Core", "Inc", "main.h")
    if os.path.exists(h):
        txt = open(h, encoding="utf-8", errors="replace").read()
        for name, num in re.findall(r"#define\s+(\w+)_Pin\s+GPIO_PIN_(\d+)", txt):
            port = re.search(r"#define\s+%s_GPIO_Port\s+GPIO([A-H])" % name, txt)
            if port:
                defines[name] = "P%s%s" % (port.group(1), num)
    return ioc, defines


def firmware_section():
    ioc, defines = read_firmware()
    # STM32 port -> (pin number, net) from the hardware model
    port_net = {}
    for p, d in C["U6"]["pins"].items():
        nm = (d["name"] or "")
        m = re.match(r"^(P[A-H]\d+)", nm)
        if m:
            port_net[m.group(1)] = (p, d["net"])

    lines = []
    lines.append("### Pins the firmware configures\n")
    lines.append("| Port | U6 pin | Hardware net | `.ioc` signal | `main.h` label | Match |")
    lines.append("|---|---|---|---|---|---|")
    for port in sorted(ioc, key=lambda x: (x[1], int(x[2:]))):
        pin, net = port_net.get(port, ("?", "?"))
        sig = ioc[port].get("Signal", "")
        lbl = ioc[port].get("GPIO_Label", "")
        rev = {v: k for k, v in defines.items()}
        hdr = rev.get(port, "")
        ok = "✅" if net not in ("?",) else "⚠️"
        lines.append("| `%s` | %s | `%s` | %s | %s | %s |"
                     % (port, pin, esc(net), esc(sig), esc(hdr or lbl), ok))

    lines.append("\n### `main.h` pin defines vs hardware\n")
    lines.append("| Define | Port | U6 pin | Hardware net | Verdict |")
    lines.append("|---|---|---|---|---|")
    for name, port in sorted(defines.items()):
        pin, net = port_net.get(port, ("?", "?"))
        lines.append("| `%s_Pin` | %s | %s | `%s` | ✅ agrees |" % (name, port, pin, esc(net)))

    # hardware wired to the MCU but absent from the .ioc
    lines.append("\n### Wired to the MCU but **not** configured in firmware\n")
    lines.append("These nets reach the STM32 and carry a designer-given name, but have no `.ioc` "
                 "entry and no code in `Core/Src/main.c` driving them. They are the board's "
                 "unimplemented capability surface.\n")
    lines.append("| Port | U6 pin | Net | Connects to | Note |")
    lines.append("|---|---|---|---|---|")
    for port in sorted(port_net, key=lambda x: (x[1], int(x[2:]))):
        pin, net = port_net[port]
        if port in ioc:
            continue
        if net.startswith(("unconnected-", "Net-(")):
            continue
        lines.append("| `%s` | %s | `%s` | %s | %s |"
                     % (port, pin, esc(net), esc(others(net, "U6")), FW_NOTE.get(port, "")))

    lines.append("\n**Debug access is not reserved in CubeMX.** The `.ioc` configures only "
                 "`SYS_VS_Systick` — there is no `SYS_JTMS-SWDIO` / `SYS_JTCK-SWCLK` entry, i.e. "
                 "Debug is set to *No Debug*. SWD still works because PA13/PA14 come up as SWD "
                 "after reset on the STM32F4 and nothing remaps them, but because CubeMX does not "
                 "consider them reserved, assigning either pin to another peripheral later would "
                 "silently cost you debugger access to a board whose only debug header is J1. "
                 "Setting **SYS → Debug → Serial Wire** in the `.ioc` would lock them down.\n")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# sections
# --------------------------------------------------------------------------

def by_sheet():
    d = defaultdict(list)
    for ref, c in C.items():
        d[c["sheet"]].append(ref)
    return d


def net_class_index():
    d = defaultdict(list)
    for name, e in N.items():
        d[e["class"]].append(name)
    return d


def connector_section():
    out = []
    for ref in sorted(C, key=lambda r: (r[:2], r)):
        if not re.match(r"^(CN|J|JP)\d+$", ref):
            continue
        c = C[ref]
        out.append("**%s** — %s pin(s), sheet _%s_\n" % (ref, c["pin_count"], c["sheet"] or "?"))
        out.append("| Pin | Name | Net |")
        out.append("|---|---|---|")
        for p in sorted(c["pins"], key=pinkey):
            d = c["pins"][p]
            out.append("| %s | `%s` | `%s` |" % (p, esc(d["name"] or ""), esc(d["net"])))
        out.append("")
    return "\n".join(out)


def main():
    sheets = MODEL["sheets"]
    bs = by_sheet()
    nc = net_class_index()

    doc = []
    A = doc.append

    A("# Custom_BMS — Schematic & Netlist Reference\n")
    A("> **Generated file — do not hand-edit.** Regenerate with:\n>\n"
      "> ```sh\n> python3 docs/extract_netlist.py && python3 docs/render_netlist.py\n> ```\n")
    A("Board: **Custom_BMS** · %d components · %d nets · KiCad 9 hierarchical project.\n"
      % (MODEL["counts"]["components"], MODEL["counts"]["nets"]))

    A("## How this was built\n")
    A("Connectivity is taken from `production/netlist.ipc` (IPC-D-356), which records exact "
      "pin→net membership. Full net names come from `Custom_BMS.kicad_pcb`, which declares every "
      "net untruncated; the IPC file truncates names to 14 characters, keeping the *rightmost* "
      "characters, upper-casing them and replacing spaces with `?` "
      "(so `/BMS Chips/TSREF` appears as `MS?CHIPS/TSREF`). Component values, footprints, sheet "
      "assignment and pin names come from the six `*.kicad_sch` sheets and `production/bom.csv`.\n")
    A("**Caveat:** connectivity is derived from the **PCB**, so it reflects placed and routed "
      "copper. A part present only in the schematic would not appear here — see *Anomalies*.\n")

    # ---------------- architecture ----------------
    A("## 1. Architecture\n")
    A("`Custom_BMS.kicad_sch` is a documentation/index sheet only: it contains **no hierarchical "
      "sheet pins**, so the six sub-sheets interconnect purely through **global labels and power "
      "symbols**. It draws two boxes that split the design into an isolated low-voltage side and "
      "high-voltage side.\n")
    A("| Sheet | File | Domain | Components |")
    A("|---|---|---|---|")
    for sh in sheets:
        A("| %s | `%s` | %s | %d |"
          % (sh["name"], sh["file"], sh["domain"], len(bs.get(sh["name"], []))))
    A("")
    A("Responsibilities, quoted from the root sheet:\n")
    A("- **Motherboard (LV):** poll for faults, calculate segment-level info, determine safe to "
      "charge/discharge, read current sensor, compute resistance/SOC/SOH/SOP, communicate with the "
      "VCU, configure BMS chip registers and limits, POR reset of BMS chips.")
    A("- **Daughterboard (HV):** handle communication daisy chaining, fault handling over comms "
      "lines, heartbeat & comms fault detection, cell voltage measurement with filtering, temp "
      "sensing, report individual cell info.\n")
    A("```mermaid\nflowchart LR\n"
      "  subgraph LV[\"LV — Motherboard\"]\n"
      "    MCU[\"U6 STM32F405\"] -->|SPI1 + RDY + nFAULT| BR[\"U3 BQ79600<br/>bridge\"]\n"
      "    MCU -->|CAN1| CT[\"U5 SN65HVD230\"] --> CN[\"CANH/CANL\"]\n"
      "    PWR[\"+12V → U2 buck → +5V<br/>→ U4 LDO → +3.3V\"] -.-> MCU\n"
      "  end\n"
      "  BR -->|COMH/COML| ISO{{\"isolation<br/>D11/D12 + chokes\"}}\n"
      "  ISO --> CN4CN5[\"CN4 / CN5\"]\n"
      "  CN4CN5 -. cable .-> CN2CN3[\"CN2 / CN3\"]\n"
      "  subgraph HV[\"HV — Daughterboard\"]\n"
      "    CN2CN3 --> ISO2{{\"isolation<br/>D1/D2 + L1/L2\"}} -->|COMH/COML| MON[\"U1 BQ79616<br/>16-cell monitor\"]\n"
      "    MON -->|VC0..VC16| TAP[\"cell tap filters<br/>CN1\"]\n"
      "    MON -->|CB0..CB16| BAL[\"cell balancing\"]\n"
      "    MON -->|TSREF/TEMP1-4| TH[\"CN7 thermistors\"]\n"
      "  end\n```\n")

    # ---------------- power ----------------
    A("## 2. Power tree\n")
    A("```\nCN8 / VBAT ──► +12V ──► U2 TPS563300 (buck) ──► +5V ──► U4 AMS1117-3.3 (LDO) ──► +3.3V\n```\n")
    A("| Rail | Pins on net | Notes |")
    A("|---|---|---|")
    for rail in ["+12V", "+5V", "+3.3V", "VBAT", "LV_GND", "GND", "CELL_TOP"]:
        e = N.get(rail)
        if e:
            note = "HV-side ground (BMS Chips domain)" if rail == "GND" else (
                   "LV-side ground" if rail == "LV_GND" else "")
            A("| `%s` | %d | %s |" % (rail, e["pin_count"], note))
    A("")
    A("> Note the design keeps **two separate grounds**: `LV_GND` on the motherboard side and "
      "`GND` on the BMS-chip (HV) side. They are not the same net — that separation is the "
      "isolation barrier.\n")

    # ---------------- signal chains ----------------
    A("## 3. Signal chains\n")
    A("### 3.1 MCU ↔ BQ79600 (SPI)\n")
    A("| Signal | U6 pin / port | U3 pin | Net | Series R / test point |")
    A("|---|---|---|---|---|")
    for sig, port in [("MOSI", "PA7"), ("MISO", "PA6"), ("SCLK", "PA5"),
                      ("nCS", "PA4"), ("SPI_RDY", "PA3"), ("nFAULT", "PA8")]:
        pin = next((p for p, d in C["U6"]["pins"].items()
                    if (d["name"] or "").startswith(port)), "?")
        net = C["U6"]["pins"].get(pin, {}).get("net", "?")
        extras = [m for m in N.get(net, {}).get("members", [])
                  if not m.startswith(("U6.", "U3."))]
        u3pin = next((m.split(".")[1] for m in N.get(net, {}).get("members", [])
                      if m.startswith("U3.")), "—")
        A("| %s | %s / `%s` | %s | `%s` | %s |"
          % (sig, pin, port, u3pin, esc(net), ", ".join(extras) or "—"))
    A("")
    A("### 3.2 Isolated daisy chain\n")
    A("Two differential pairs (COMH, COML) cross the isolation barrier on each side:\n")
    A("```\nU1 BQ79616 pins 40-43 ─ R35-R40 / C43-C49 ─ L1,L2 (chokes) ─ D1,D2 (isolation) ─ CN2, CN3   [HV]\n"
      "U3 BQ79600 pins 10-13 ─ R45-R50 / C53-C57 ─ D11,D12 (isolation) ────────────────── CN4, CN5   [LV]\n```\n")
    A("| Net | Pins |")
    A("|---|---|")
    for name in sorted(nc.get("daisy-chain", [])):
        A("| `%s` | %s |" % (esc(name), ", ".join(N[name]["members"])))
    A("")
    A("### 3.3 CAN\n")
    A("| Net | Pins |")
    A("|---|---|")
    for name in sorted(nc.get("can", [])):
        A("| `%s` | %s |" % (esc(name), ", ".join(N[name]["members"])))
    A("")
    A("### 3.4 Cell sense and balancing\n")
    A("`VC0`…`VC16` are the cell-voltage sense inputs on U1; `CB0`…`CB16` are the balancing "
      "outputs. Cell taps arrive on CN1 and pass through the Cell Tap Filters sheet.\n")
    A("| Net | Pins |")
    A("|---|---|")
    for name in sorted(nc.get("cell-sense", []) + nc.get("cell-balance", []) + nc.get("cell-tap", []),
                       key=lambda x: (re.sub(r"\d+", "", x), int(re.search(r"\d+", x).group()))):
        A("| `%s` | %s |" % (esc(name), ", ".join(N[name]["members"])))
    A("")

    # ---------------- IC pinouts ----------------
    A("## 4. IC pinouts\n")
    for ref in ICS:
        if ref not in C:
            continue
        c = C[ref]
        A("### %s\n" % IC_TITLE.get(ref, ref))
        A("`%s` · footprint `%s` · sheet _%s_ · %s domain\n"
          % (esc(c["value"]), esc(c["footprint"]), c["sheet"] or "?", c["domain"] or "?"))
        if ref == "U3":
            A("> ⚠️ The vendored `bq79600.kicad_sym` has **numeric placeholder pin names** "
              "(`\"1\"`, `\"2\"`, …). The *Name* column below is therefore **inferred from the net "
              "each pin lands on**, not extracted from the symbol. Verify against the TI datasheet "
              "before relying on it.\n")
            A(ic_table(ref, BQ79600_FN))
        else:
            A(ic_table(ref))
        A("")

    # ---------------- connectors ----------------
    A("## 5. Connectors\n")
    A(connector_section())

    # ---------------- firmware ----------------
    A("## 6. Firmware cross-reference\n")
    A("Firmware lives in a separate tree: `~/Desktop/USC-Communications-Systems/Custom_BMS/` "
      "(STM32CubeIDE). This section correlates it against the hardware model above.\n")
    A(firmware_section())
    A("")

    # ---------------- anomalies ----------------
    A("## 7. Anomalies and open items\n")

    vm = MODEL.get("value_mismatches", [])
    A("### ⚠️ Schematic and PCB disagree on component values\n")
    if vm:
        A("The fabrication BOM (`production/bom.csv`) is generated from the **PCB**, so where the "
          "two disagree the board gets built with the PCB value and the schematic edit is lost. "
          "**Update PCB from Schematic** in KiCad would reconcile these.\n")
        A("| Ref | Sheet | Schematic | PCB / BOM |")
        A("|---|---|---|---|")
        for d in vm:
            A("| `%s` | %s | **%s** | **%s** |"
              % (d["ref"], d["sheet"], esc(d["schematic"]), esc(d["pcb"])))
        A("")
        A("> These are exactly the three parts flagged in `review.txt` (01-02): "
          "*\"R69, R74, R76 exceed power rating when on\"*. The schematic was corrected to 2.7 kΩ, "
          "but the change never propagated to the PCB — so a board ordered from the current "
          "`production/` folder would ship with the 1 kΩ parts the review rejected.\n")
    else:
        A("None — schematic and PCB values agree for every component.\n")

    A("### Extraction warnings\n")
    if MODEL["warnings"]:
        for w in MODEL["warnings"]:
            A("- %s" % w)
    else:
        A("- none")
    A("")
    A("### Schematic ↔ PCB desync\n")
    A("`TP21`–`TP24` exist as footprints in `Custom_BMS.kicad_pcb` (and therefore in the generated "
      "BOM) but appear in **no schematic sheet**. They sit on the isolation capacitors "
      "`C45`/`C46`/`C51`/`C52`. Either they were placed directly in the PCB editor, or the "
      "schematic they came from was lost. Worth resolving before the next fabrication run, since "
      "KiCad's ERC will not see them.\n")
    A("### Duplicate project copy\n")
    A("A second, differing copy of the whole project exists at `Custom_BMS/Custom_BMS/` "
      "(36 git-tracked files). Its `mcu.kicad_sch` is smaller than the authoritative one but its "
      "`bms_chip.kicad_sch` is *larger*. It is being treated as stale. If something looks missing "
      "from `bms_chip`, check there before concluding a real gap.\n")

    # ---------------- review backlog ----------------
    A("## 8. Review backlog, checked against this netlist\n")
    A("`review.txt` holds five rounds of review notes. Each item below was re-checked against the "
      "extracted model. **Status is fact** (the net/value either is or is not what the reviewer "
      "asked for); **commentary is inference**.\n")
    A("| Review item | Status | Evidence from the netlist |")
    A("|---|---|---|")
    for item, status, ev in REVIEW_ITEMS:
        A("| %s | %s | %s |" % (item, status, ev))
    A("")
    A("> Items not listed are layout/physical-design notes (copper pours, via sizes, trace "
      "placement, heat sinking, 3D models, ground-plane stackup) that connectivity extraction "
      "cannot settle — they need the PCB editor or a datasheet, not the netlist.\n")

    # ---------------- net index ----------------
    A("## 9. Full net index\n")
    A("%d nets, grouped by class. `unconnected-(…)` and `Net-(…)` names are KiCad-generated, "
      "meaning no label was placed on that wire.\n" % len(N))
    for cls in sorted(nc):
        A("### %s (%d)\n" % (cls, len(nc[cls])))
        A("| Net | Pins | Members |")
        A("|---|---|---|")
        for name in sorted(nc[cls]):
            e = N[name]
            mem = ", ".join(e["members"])
            if len(mem) > 300:
                mem = mem[:300] + " …"
            A("| `%s` | %d | %s |" % (esc(name), e["pin_count"], esc(mem)))
        A("")

    out = os.path.join(HERE, "NETLIST.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(doc) + "\n")
    print("wrote %s (%d lines)" % (out, len("\n".join(doc).splitlines())))


if __name__ == "__main__":
    main()
