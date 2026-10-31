# R2 — non-latching BSPD permit

Open `BSPD_2027.kicad_pro` with KiCad 10. U9, C13, R33, C14 and D3 are removed. The BSPD permit signal returns HIGH when faults clear and power is ready. The separate relayboard owns fault retention and manual reset.

The same connector/pinout, outline, mounting holes and all remaining component placements are preserved. The PCB is checked with an explicit 0.50 mm copper-edge requirement. ERC, DRC, connectivity and schematic-parity checks report zero issues. All66 fitted components have LCSC numbers.

The SMT_REVIEW BOM and CPL match65 SMT parts. J1 is the exact Molex430450612/C234188 through-hole connector and requires its assembly method to be confirmed separately. Gerbers, drilling and native positions use the common lower-left origin. The four4mm mounting cutouts are in Edge.Cuts.

Engineering-review status is unchanged: the current-reference interface, measured brake threshold and physical vehicle/relay qualification remain pending. See ../DESIGN_REVIEW.md. Earlier R1 files are historical and must not be mixed with R2.
