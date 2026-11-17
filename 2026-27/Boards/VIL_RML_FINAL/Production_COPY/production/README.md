# RML/VIL prototype fabrication and assembly package

Updated November 11, 2026 from Aric's `b29836a93021807e1f17e996493914bdbb5db771` project plus the saved local edits and the direct-solder F1/F2 revision. The files in this folder correspond to the adjacent `integrated_vil_rml.kicad_pcb` and schematic.

| Upload | File |
|---|---|
| PCB fabrication | `RML_VIL_Gerbers.zip` |
| Parts matching | `BOM_JLCPCB.csv` |
| Top-side placement | `CPL_JLCPCB.csv` |

The package has two copper layers, 1.6 mm board thickness, and the existing approximately 95.696 x 30.136 mm outline. Gerbers and plated/non-plated drill files use absolute board coordinates. CPL coordinates are millimetres with negative board Y, and preserve the previously verified JLCPCB part-specific assembly rotations.

## Direct-solder F1/F2 revision

F1 and F2 use project-local `RML_Fuses:Fuse_Eaton_PCTron_P5.08mm`, for an Eaton PC-Tron radial fuse soldered directly to the PCB. The body outline is 8.89 x 4.67 mm; lead spacing is 5.08 mm; plated holes are 0.9 mm with 1.8 mm pads. The reference part is 750 mA `PCB-3/4-R`, rated 450 VDC. The BK/PCS holder is not used. See the [Eaton PC-Tron datasheet](https://www.eaton.com/content/dam/eaton/products/electronic-components/resources/data-sheet/eaton-pc-tron-subminiature-radial-leaded-fuses-data-sheet.pdf).

F1 is at (121, 84.25) mm and F2 at (126.5, 84.25) mm, both rotated 90 degrees. D3 moved from (130.5, 82) to (132, 82) mm to accommodate the fuse bodies. Local HV routing and connector reference-label positions were adjusted. Electrical pad-net membership and the board outline are unchanged. The prior saved R6 move to (148, 89.5) mm is included in these outputs.

**F1, F2 and Q3 remain excluded from JLCPCB assembly.** F1/F2 are also marked DNP in the schematic and PCB. The four new fuse lead holes are included in fabrication. The BOM and CPL contain the same 30 populated references across 23 BOM groups. The BOM's component selections are unchanged; R6 remains C137518 locally. The earlier JLCPCB draft-only substitution of C228865 is not a BOM substitution in this package. Conformal coating and the excluded parts are installed by the owner.

The fuse value is retained at the user's request. DC interruption suitability, protection coordination, upstream branch protection, and assembled vibration performance remain engineering checks; this footprint update is not a protection or vehicle-compliance sign-off.

## Placement conventions

The connector origins use the centers of their numbered pin arrays. The keyed orientations remain those verified in the earlier JLCPCB preview.

| Connector | LCSC code | Mid X (mm) | Mid Y (mm) | Rotation (degrees) |
|---|---|---:|---:|---:|
| J1 | C277721 | 208.94 | -84 | 90 |
| LED2 | C293362 | 165 | -93.5 | 90 |
| Molex1 | C293362 | 130.5 | -93.5 | 90 |
| Molex2 | C293362 | 130.5 | -74.5 | 270 |

F3 is the separate populated GLV fuse, Reomax R12.000.0.5 / C5383189 (500 mA). It is not changed by the F1/F2 revision.

## Verification and order status

KiCad 10.0.6 checks: zero PCB errors, zero unconnected items, zero schematic parity issues, and zero ERC errors. There are 38 PCB warnings (18 silkscreen overlaps, 15 silkscreen/copper conflicts, four silkscreen/edge warnings, and one pre-existing dangling track) and three existing schematic warnings. The project-local fuse footprint matches the PCB copies.

Gerbers, drill files, and CPL were regenerated for this revision. The BOM/CPL reference sets match and exclude F1/F2/Q3. The previous JLCPCB draft and placement preview predate this revision: upload the new Gerber ZIP and CPL and verify the updated preview before ordering. No order or payment was submitted.

The previous PCB, schematic, and production files are retained in this project's `.history` folder before replacement.
