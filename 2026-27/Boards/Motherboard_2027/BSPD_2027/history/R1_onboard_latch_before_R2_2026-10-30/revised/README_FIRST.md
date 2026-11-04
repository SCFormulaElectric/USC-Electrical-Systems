# Engineering review — not released for vehicle manufacture

Open `BSPD_2027.kicad_pro` with KiCad 10. The original connector/pinout and mounting geometry are retained.

The schematic and PCB pass ERC/DRC with zero unconnected items and zero schematic-parity issues. All 71 fitted components have LCSC numbers. This does not resolve the current-reference interface, vehicle hard-braking calibration or physical shutdown qualification. See `../DESIGN_REVIEW.md` before ordering.

Use the **SMT_REVIEW** BOM and CPL together for the 70 SMT parts. J1 is the exact Molex 430450612/C234188 through-hole connector and needs a separate assembly quote or manual soldering. The all-component BOM is retained for procurement; the all-KiCad position file records J1's pin-1 footprint anchor, not an automatic gripper centroid.

Fabrication data uses a common drill/placement origin at the board lower-left. Four 4 mm mounting cutouts are in the Edge.Cuts Gerber as routed holes; the drill file therefore lists connector/via drilling separately. The Gerber archive is review data, not a production release.
