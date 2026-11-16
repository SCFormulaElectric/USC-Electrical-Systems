# VIL/RML fabrication refresh — HOLD for HV spacing review

Updated 2026-11-15 11:31 PST. The files in `production/` now match the current **four-layer** layout and replace the older two-layer output. The folder contains only `BOM_JLCPCB.csv`, `CPL_JLCPCB.csv`, and `RML_VIL_Gerbers.zip`.

**This revision is not cleared for production ordering.** Current saved HV spacing failures remain. Exporting the fabrication files does not resolve them.

| Current check | Result |
|---|---|
| Unconnected items | 0 |
| Schematic/PCB parity issues | 0 |
| Active PCB DRC error records | 7 (HV clearance/creepage) |
| Existing excluded PCB error records | 4, retained unchanged |
| PCB warnings | 8 (silkscreen) |
| ERC errors / warnings | 0 / 3 |
| Matched BOM / CPL parts | 30 / 30 |
| Grouped BOM rows | 23 |

The active errors represent the two Q3 pad-pair gaps of **2.95 mm against the 3 mm clearance requirement** (reported across multiple layers), and the R6/U1-area track to Heat Sink zone creepage of **3.99 mm against the 4 mm requirement**. Q3 also has existing excluded 2.95 mm creepage findings against 4 mm. These exclusions have not been added, weakened or treated as evidence of acceptable spacing. Resolve the applicable HV constraints and review the physical assembly before placing a production order.

## Assembly and sourcing updates

Per the user's confirmation, **Q3 remains excluded for manual installation**. F1 and F2 remain owner-fitted/DNP for JLCPCB. Their copper and drill holes remain in the fabrication ZIP. All three are absent from the factory BOM/CPL.

The refreshed BOM follows the current schematic selections: Q2 is DMN3404L-7 / C155257; Q4/Q5 are DMP3056L-7 / C150724; F3 is BSMD0805-050-24V / C910822; U2 is NE555DR / C7593 in SOIC-8. The PCB purchasing fields were synchronized to these existing schematic choices. D2 and R2 retain their selections from the previous assembly BOM: BZT52C8V2 / C173432 and ERJP06F2201V / C441982. R8 whitespace and supplier links were normalized to C441981. R6 was subsequently replaced, at the user’s request on 2026-11-15, with equivalent YAGEO AC0805FR-074K3L / C228865 (4.3 kΩ, ±1%, 0805, 125 mW, 150 V); its schematic/PCB purchasing fields and production BOM now agree. This sourcing change does not clear the HV spacing hold.

The visible HV+, HV− and VIL markings are preserved. Their internal PCB references now match schematic Molex1, Molex2 and LED2 so BOM, CPL, Gerber attributes and netlist agree. The refresh preserves every component/pad position, pad size/drill/net, original trace/via, zone boundary and board outline. Q3's assembly-exclusion flags and hidden metadata were updated; copper geometry and clearance rules were not changed.

## Fabrication and placement conventions

The ZIP contains four copper layers in F.Cu / In1.Cu / In2.Cu / B.Cu order, two masks, two legends, two paste layers, outline, PTH/NPTH drill files, and the Gerber job. Independent parsing recognized all layers and 160 plated / 13 nonplated drill hits. Top/bottom previews were inspected outside the production directory.

The current board is approximately 95.696 × 30.136 mm, nominal 1.6 mm thick. Native stack metadata specifies 0.035 mm copper on all four layers, 0.1 / 1.24 / 0.1 mm dielectrics, and no specified surface finish. This is the current saved stack, rather than a claim that a default JLCPCB stack matches it; select/confirm the fabrication build and finish with the supplier when the HV hold is resolved.

Gerbers, drills and CPL retain the existing absolute-coordinate convention: order X is KiCad X and order Y is negative KiCad Y. THT centroids are the centers of numbered pin arrays; SMT centers are their footprint anchors. The previously verified part-specific rotation offsets were recovered from the corresponding historical native board and applied to the current rotations. U2's new SOIC-8 uses the standard 270-degree SOIC correction. F3 is the current nonpolar PPTC footprint. Review the new JLCPCB placement preview and matched parts; the old preview predates the present placements and selected devices. Current stock was not reserved or comprehensively checked.

The three remaining ERC warnings concern HV−/JFET_G net naming and customized Q3/U2 library symbols. Circuit values, models and electrical architecture were preserved. Prior physical/functional qualification findings are not closed by fabrication-file generation.

## Evidence and backups

Current check reports, input hashes, geometry-preservation verification, rotation evidence, Gerber parsing and old production files are retained at:

`/Users/nick333/Documents/ChatGPT/FSAE/RML_VIL_Fab_Update_2026-11-15`

This status supersedes the old production README's layer count, placements, part selections and check counts. If KiCad was open during this update, close without saving its old in-memory copy and reopen the project to load the synchronized sourcing/reference fields.
