# Discharge 2027 ordering files

These exports use the saved November 5, 2026 KiCad board. Use `Discharge_2027_Gerbers.zip` for the two-layer, 1.6 mm board. It contains both copper, mask and silkscreen layers, top paste, the board profile, and separate plated and non-plated drill files.

| Assembly option | BOM | Component placement list |
|---|---|---|
| Assemble 12 components, with R6/R7 hand fitted | `BOM_JLCPCB.csv` | `CPL_JLCPCB.csv` |
| Assemble D1 only and hand-place the through-hole parts | `BOM_SMT_ONLY.csv` | `CPL_SMT_ONLY.csv` |

R6 and R7 are DNP for JLCPCB assembly and are excluded from both assembly CSV files. The owner will fit the original Vishay AC07000001502JAC00 TSMP resistors after assembly.

All populated components mount on top. The CPL uses millimeters and the same unshifted origin as the Gerbers and drills. J1–J5 use the midpoint of the two solder leads to match the C122431 model in the JLCEDA/EasyEDA official library. This point is 5.465 mm inward from the KiCad housing center along each connector’s mating axis. Other components use package body centers. Mechanical holes and logos are excluded. `Procurement.csv` provides manufacturer part numbers and supplier links. Confirm availability and through-hole assembly support for the quoted parts, and check D1 orientation, K1 pin locations, and the resistor lead forming in the assembly review.

KiCad 10.0.6 reported zero schematic ERC violations, zero PCB DRC errors, and zero unconnected items. It reported 11 silkscreen warnings (connector outline clipping and the K1 outline touching a boundary marking) and 15 schematic parity warnings (field differences and the coil supply named `/SDC` on the schematic and `/COIL_12V` on the PCB). The coil supply connects D1.1, J3.1 and K1.1 in both files.

The files are for fabrication and assembly review. Verify the assembled insulation and perform shutdown timing and maximum-voltage endurance tests before vehicle use.
