# RML 2027 procurement audit

Checked 2026-10-04 against the public JLCPCB catalog. No LCSC tool or matching installable plugin was available; direct LCSC/JLCPCB catalogs were used.

**22 of 24 electronic components have verified catalog matches with positive JLCPCB available quantities. F1 and F2 remain unresolved. Mounting holes and power symbols are excluded.**

## Selected parts

| References | Selected MPN | LCSC/JLC code | JLC available quantity |
|---|---|---|---|
| C1, C5 | CC0805KRX7R9BB104 | [C49678](https://jlcpcb.com/partdetail/CC0805KRX7R9BB104/C49678) | 16446460 |
| C3 | CL21B105KBFNNNE | [C28323](https://jlcpcb.com/partdetail/CL21B105KBFNNNE/C28323) | 1496283 |
| C4 | MKS2C041001F00JSSD | [C92673](https://jlcpcb.com/partdetail/MKS2C041001F00JSSD/C92673) | 8168 |
| D1 | 1N4148WT-7 | [C83482](https://jlcpcb.com/partdetail/1N4148WT-7/C83482) | 39614 |
| D3 | BZT52C51-7-F | [C177017](https://jlcpcb.com/partdetail/BZT52C51-7-F/C177017) | 380 |
| D4 | PESD12VL1BA,115 | [C38558](https://jlcpcb.com/partdetail/PESD12VL1BA_115/C38558) | 4995 |
| D5 | BZT52C8V2 | [C173432](https://jlcpcb.com/partdetail/BZT52C8V2/C173432) | 101083 |
| J1 | 430450412 | [C277721](https://jlcpcb.com/partdetail/430450412/C277721) | 11511 |
| Molex1, Molex2 | 430450212 | [C293362](https://jlcpcb.com/partdetail/430450212/C293362) | 13277 |
| Q2 | AO3400A | [C20917](https://jlcpcb.com/partdetail/AO3400A/C20917) | 819180 |
| Q3 | UJ3N065080K3S | [C45082793](https://jlcpcb.com/partdetail/UJ3N065080K3S/C45082793) | 6 |
| Q4 | AO3401A | [C15127](https://jlcpcb.com/partdetail/AO3401A/C15127) | 644890 |
| R1 | 0805W8F2001T5E | [C17604](https://jlcpcb.com/partdetail/0805W8F2001T5E/C17604) | 5157170 |
| R4 | 0805W8F1003T5E | [C149504](https://jlcpcb.com/partdetail/0805W8F1003T5E/C149504) | 3806172 |
| R6 | 0805W8F5601T5E | [C4382](https://jlcpcb.com/partdetail/0805W8F5601T5E/C4382) | 588786 |
| R7 | 0805W8F7503T5E | [C17817](https://jlcpcb.com/partdetail/0805W8F7503T5E/C17817) | 11176 |
| R8 | 0805W8F1001T5E | [C17513](https://jlcpcb.com/partdetail/0805W8F1001T5E/C17513) | 29645019 |
| R9 | 0805W8F1002T5E | [C17414](https://jlcpcb.com/partdetail/CC0805KRX7R9BB104/C17414) | 57804630 |
| U1 | H11L1 | [C78588](https://jlcpcb.com/partdetail/H11L1/C78588) | 3214 |
| U2 | LMC555CMX/NOPB | [C90760](https://jlcpcb.com/partdetail/LMC555CMX_NOPB/C90760) | 11858 |

Quantities are snapshots from JLCPCB’s catalog fields `canPresaleNumber` (available quantity) and `overseasStockCount` (catalog stock); the raw values and source URLs are saved in RML_2027_sourcing_evidence.json. Catalog stock is not a reservation. LCSC distributor stock can differ from JLC assembly stock.

## Changes to the copied schematic

- Added hidden LCSC, manufacturer, MPN, catalog URL, status, and available-quantity fields to matched parts.
- U2: active TI LMC555CMX/NOPB, C90760, same SOIC-8 footprint and pinout.
- U1: Everlight H11L1, C78588, replacing onsemi H11L1M. Everlight’s manufacturer catalog confirms the same DIP-6 pin functions (1 anode, 2 cathode, 3 NC, 4 output, 5 ground, 6 supply), 3–15 V supply and 1.6 mA trigger specification. The HV threshold circuit still requires qualification/redesign.
- D1: specified the Diodes Incorporated orderable 1N4148WT-7, same SOD-523.
- D3: specified Diodes Incorporated BZT52C51-7-F, C177017; D5: specified MDD BZT52C8V2, C173432. Changed both footprint assignments from SOD-123F to SOD-123 to match these packages. D3 retains the wide 48–54 V Zener range; this does not make the HV threshold compliant.
- Resistors: 0805, 1%, 0.125 W. C1/C3/C5: 0805 X7R, 50 V, 10%. C4 retains the 1 µF ±5%, 63 V WIMA film capacitor, C92673.

## Remaining procurement issues

- **F1/F2:** “750mA” and a custom FUSE_BK_PCS footprint do not identify a purchasable fuse. A selection requires maximum TS DC voltage, prospective fault current / required interruption rating, time-current characteristics, and matching physical dimensions. Do not select a lower-voltage fuse or assume two series fuses share fault voltage. No LCSC code was invented for these parts.
- **Q3:** C45082793 has only 6 available. The Qorvo listing C22433239 has zero. Reserve/confirm stock before committing the PCB. The horizontal TO-247 footprint needs JLC placement/assembly review.
- C4, U1, Q3 and the Molex headers are listed for wave soldering. JLC lists Economic and Standard support, but final through-hole placement, fixture needs and fees must be confirmed in the assembly quote. Extended components can incur loading fees.
- The matched JLC BOM deliberately excludes F1/F2. It is not a complete manufacturing BOM. All 24 components, including unresolved fuses, are in the full sourcing audit. PCB placement/CPL and PCB footprint synchronization are still required; this task changed the schematic only.

## Verification

KiCad successfully exported the schematic and netlist. All net names and component-pin connections match the pre-sourcing version. The rendered schematic was inspected. ERC retains 11 existing violations (3 errors, 8 warnings); this is not a manufacturing or FSAE compliance sign-off. The prior HV threshold problem remains unresolved.

The original RML-26_V2.kicad_sch was not edited. The copied schematic was backed up as RML-26_V2_low_side_LED.kicad_sch.before_LCSC_sourcing.
