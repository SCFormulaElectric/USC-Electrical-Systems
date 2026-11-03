# Original BSPD PCB audit

Checked 2026-10-05 using KiCad CLI 10.0.6. The supplied source files were read only. Automated checks used writable copies.

## Exact connector and mechanical geometry

J1 is Molex **043045-0612**, equivalently **430450612**, LCSC **C234188**. Keep `Connector_Molex:Molex_Micro-Fit_3.0_43045-0612_2x03_P3.00mm_Vertical`. It is on the front at (149.6538, 68.9186) mm, rotated 90 degrees.

| Pin | X (mm) | Y (mm) | Original net |
|---|---:|---:|---|
| 1 | 149.6538 | 68.9186 | Unused |
| 2 | 149.6538 | 65.9186 | BSPD_signal |
| 3 | 149.6538 | 62.9186 | current |
| 4 | 152.6538 | 68.9186 | brake |
| 5 | 152.6538 | 65.9186 | GND |
| 6 | 152.6538 | 62.9186 | +12V |

Connector signal pads use 1.00 mm drills and 1.50 mm copper. Its 1.00 mm locator holes are at (153.5938, 71.9186) and (153.5938, 59.9186).

The board has two copper layers and 1.60 mm thickness. Its bounding envelope is **40.06 x 54.28 mm**. Outline vertices, in order, are (144.25, 52.58), (184.31, 52.64), (184.26, 106.75), (144.36, 106.86), (144.25, 104.82), closing to the first point. The slight skew in the outline is preserved for mechanical compatibility; straightening it requires enclosure confirmation.

Four circular `Edge.Cuts` holes have 4.00 mm diameter, centered at (146.90, 104.13), (146.95, 55.42), (180.98, 103.59), and (181.55, 55.50). They are represented as routed cutouts rather than explicit NPTH drill pads. The left holes leave only about 0.65-0.70 mm of board between the hole and outer edge. This is mechanically weak under screw torque. Stronger hole locations would require matching enclosure changes. Use insulating spacers and a copper/component keepout sized to the actual screw head or washer; the original has no hardware keepout.

## Automated checks

Original PCB DRC found **zero unconnected items and zero physical errors** under its existing rules. It reported 23 library warnings: 19 footprint mismatches and four missing potentiometer library footprints. Schematic parity produced 18 field-metadata warnings. Reports: `original_drc.json`.

Original schematic ERC found 131 violations: two power-pin-not-driven errors (GND and 12V), one unconnected J1 pin 1 error, 100 off-grid endpoint warnings, 16 symbol-library mismatches, six symbol-library issues, four footprint-link issues, one missing input-pin warning, and one missing unit warning. Use power flags and an explicit NC marker, correct unused IC inputs, and synchronize libraries. Report: `original_erc.json`.

The existing global minimum clearance, track width, and silk clearance are set to zero; copper-to-edge minimum is only 0.01 mm. The default net class uses 0.20 mm clearance. On a temporary copy, setting 0.25 mm net clearance, 0.25 mm minimum track width, 0.30 mm copper-to-edge clearance, and 0.10 mm silk clearance produced 91 clearance errors (mostly actual 0.20 mm) and two silk overlaps. These are failures against a proposed conservative margin, not failures against the original or typical JLC limits. Exact locations are in `original_drc_conservative.json`.

## Actionable improvements

- There are 24 footprints, 269 tracks all 0.25 mm wide, and 38 vias all 0.80 mm diameter with 0.40 mm drills. A single backside GND zone uses 0.50 mm clearance and thermal gaps. The existing PCB is fully routed.
- The six logic/comparator ICs have no local supply bypass capacitors. C1 and C2 filter sensor signals; C4 is the timer. Add a 100 nF capacitor at every IC supply and a short ground return, plus regulator/reference capacitors and input bulk capacitance.
- R9 through R12 are exposed three-terminal potentiometers. Replace them with fixed precision resistor dividers and documented replaceable 0805 calibration resistors so no mechanical wiper controls a safety threshold.
- Most original passives, potentiometers, the diode, TO-92 reference, and capacitors require through-hole assembly. Use 0805 passives where practical, while retaining the exact connector. A stable film timing capacitor may justify a through-hole exception.
- No LCSC or JLC fields exist in the supplied project. Values such as 5k, 50k, and 12u are insufficient procurement specifications. Assign a verified manufacturer, MPN, LCSC code, package, tolerance, power rating, and capacitor dielectric/voltage to every populated reference. Export a BOM and placement file after verification.
- Add input current limiting, sensor series resistors, Schottky clamps, reverse polarity protection, and transient protection. The original allows raw connector voltages to reach ICs directly.
- Route reference, sensor, and timer nodes compactly away from switching/current paths. Reduce long detours and ground-plane interruptions; add ground stitching near the connector and ICs.
- Add test points for protected 12V, 5V logic/reference, both sensors, thresholds, timer, latch, and permit output. Add connector pin labels and threshold configuration labels. The original only labels BSPD and component references.
- Set meaningful manufacturing rules explicitly, make polarity marks visible, preserve screw clearance, and verify silkscreen legibility.
- An LCSC number does not guarantee JLC assembly availability. The retained through-hole connector requires an assembly quote, consignment, or manual soldering.

## Primary connector sources

- [LCSC C234188, exact Molex 430450612](https://www.lcsc.com/product-detail/Others_MOLEX_43045-0612_MOLEX-43045-0612_C234188.html).
- [Molex 430450612](https://www.molex.com/ja-jp/products/part-detail/430450612): two rows, six contacts, vertical, 3.00 mm pitch, 1.60 mm PCB recommendation, 8.5 A maximum contact rating.
- [JLC exact MPN wave-solder/consignment entry C9900298442](https://jlcpcb.com/partdetail/JLCPCBAssembly-430450612/C9900298442). This is an assembly-service code, not a replacement LCSC component number.

Stock quantities are omitted because supplier pages returned conflicting cached inventory. Use the part mappings in `catalog.json` and recheck stock at ordering.
