# BSPD 2027 - R3 brake sensor calibration

Updated November 4, 2026 for the user-confirmed AiM X05PSA02000P18. This is an engineering-review/bench-calibration revision. Vehicle release remains pending.

## Implemented component changes

| Reference | Previous | Installed value | Manufacturer / MPN | LCSC |
|---|---|---|---|---|
| R18 | 115k 1% | 270k 1% | UNI-ROYAL 0805W8F2703T5E | C17589 |
| R20 | 8.66k 1% | 11.3k 1% | VO SCR0805F11K3 | C3016737 |
| R22 | 40.2k 0.1% | 47k 0.1% | YAGEO RT0805BRD0747KL | C865515 |

All three retain the 0805 footprint. R19 and R21 remain 10k 1%; R23 remains 10k 0.1%. Schematic and PCB values, manufacturer fields, MPNs, LCSC fields, catalog and generator defaults are updated. BOM/CPL, position files, Gerbers, drills, the schematic PDF and analytical evidence are refreshed. The user's readable schematic layout and standard symbols are retained; the formerly off-sheet D4 subcircuit is brought into the visible output block.

## Confirmed sensor and resulting thresholds

The supplied IMG_5184.HEIC datasheet identifies AiM X05PSA02000P18: 0-2000 psi sealed gauge, 0.5-4.5V output, 8-16V supply. The sheet is preserved in reports/evidence. User measurements are approximately 0.52V raw at rest and 1.8V raw during hard braking.

| Function | Nominal result |
|---|---|
| B_THRESH reference | 0.877193V |
| Hard-brake rising, including feedback/divider loading | 1.766348V raw |
| Hard-brake falling | 1.698420V raw |
| Low sensor-fault boundary | 0.357143V raw |
| High sensor-fault boundary | 4.694836V raw |

Using the nominal sensor transfer, the rising trip is approximately 633 psi (43.7 bar). This is a calculated pressure, not a measured vehicle calibration. The 0.52V resting reading lies inside the nominal valid window.

**The conservative modeled rising corner reaches 1.824350V raw, above the user's approximately 1.8V hard-brake reading. The requested 47k setting therefore does not establish a guaranteed hard-brake detection margin. Validate repeated hard-braking measurements and the complete tolerance budget, or recalibrate, before vehicle release.** Clamp leakage, sensor transfer error, reference load effects and PCB leakage are excluded from those partial corner bounds.

The modeled high-fault boundary spans approximately 4.540-4.853V before additional bias/leakage effects. A nominal 5.0V short is above the nominal boundary; detection of every short to a varying 4.75-5.25V logic rail is not established across all modeled corners. Actual sensor supply, ground, open/short and temperature tests remain required.

## PCB correction and verification

The pre-update board had C7 moved onto current-sense copper, producing shorts, clearance/courtyard/mask violations and stale copper fills. C7 and its affected local VP/GND copper were restored to their last verified R2 geometry. Other footprint positions are preserved, including the exact Molex connector, its orientation and physical pinout. No new routing topology is introduced. Copper zones were refilled.

PCB net names and schematic symbol links are synchronized with the current schematic, including 5V, 5V_REF, CURRENT_RAW, BRAKE_RAW, High_Current and Hard_Brake. Stale Q3 simulation fields from the earlier symbol swap were removed, and its datasheet/description fields were aligned with the fitted Nexperia MMBT3906.

Fresh checks report ERC 0, PCB DRC 0, unconnected items 0 and schematic parity issues 0. All 66 fitted parts have LCSC fields; the SMT BOM and CPL reference the same 65 parts. Before/after netlists retain identical physical component-pin connections; only R18/R20/R22 values change. The four mounting cutouts remain routed Edge.Cuts circles. Gerbers, drill and placement files use the common drill/place origin (144.25, 106.86) mm.

## Retained interface and qualification holds

There is no onboard fault latch. The external relayboard retains trips and provides the permitted reset. PERMIT = FAULT_OK AND POR_N. Connector pin 2, currently named BSPD_FAULT in the user's schematic, remains HIGH healthy and LOW fault despite that net name. Pins 1/3/4/5/6 remain unused/current/brake/ground/GLV supply respectively. The exact Molex 043045-0612 / 430450612 (C234188) is retained. It is the separate through-hole procurement item.

The DHAB S/134 channel-2/Orion 5V reference uncertainty and 360V nominal / 404V maximum accumulator assumptions are unchanged. Fixed absolute current threshold guarantees, internal component failure coverage, clamp leakage, temperature, fuse coordination, total timing and loaded external relay retention still require qualification. CAD and analytical checks do not certify FSAE compliance or a production release.

The native KiCad files are the current editable design. generate_design.py retains updated component defaults but regenerates a machine-arranged schematic; running it overwrites the hand-edited presentation. Review inventory and assembly orientation in JLCPCB before ordering. Older dated R1/R2 reports are historical and are superseded by this R3 review and reports/final_validation.json.
