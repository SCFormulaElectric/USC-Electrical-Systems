# BSPD 2027 — production files refreshed November 15, 2026

The three files in JLCPCB_Production_2026-11-14 now reflect the latest saved routing, component positions and reduced reference designators, including the green power LED and red fault/startup-inhibit LED circuits. J1 is now Molex 43045-0613 / 430450613, JLCPCB C505220, with gold-plated mating contacts. The compatible original 43045-0612 footprint is retained.

BOM/CPL: 73 fitted parts, including J1 and D5, D6, Q4, R40–R43. Bare test pads and mounting holes are excluded. J1 remains included for through-hole assembly; confirm factory acceptance and placement in the JLCPCB preview. Purchasing fields are supplied, but stock is not reserved.

Checks: 0 DRC violations, 0 unconnected items, 0 schematic-parity issues, and 0 ERC violations. Gerber ZIP includes four copper layers and separate plated/nonplated drills. Routing and component placement were preserved; copper fills were refreshed. Older REVIEW exports elsewhere are historical.

The red LED follows fault/startup inhibit and is non-latching. Prior calibration and prototype/vehicle qualification remain necessary. These file checks do not replace hardware testing.

## U1 assembly placement correction

The production CPL overrides U1 to X = 26.760 mm, Y = 49.165 mm, rotation = 270 degrees (top). This includes the requested 180-degree rotation and an upward 0.75 mm shift estimated from the JLC preview. Verify lead-to-pad alignment in the updated assembly preview. Preserve these corrections when regenerating the CPL; the PCB footprint and Gerbers were not moved.
