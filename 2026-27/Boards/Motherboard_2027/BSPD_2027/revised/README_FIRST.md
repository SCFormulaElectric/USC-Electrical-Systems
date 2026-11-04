# BSPD 2027 R3 - brake sensor calibration review

Current native project: BSPD_2027.kicad_pro. Updated November 4, 2026 for AiM X05PSA02000P18, 0.5-4.5V / 0-2000psi / 8-16V supply.

R18=270k 1% C17589; R20=11.3k 1% C3016737; R22=47k 0.1% C865515. All remain 0805. External relayboard latching; no onboard latch. Output pin 2 is HIGH healthy / LOW fault, even though its user-assigned net name is BSPD_FAULT.

Use the matching SMT BOM and CPL for 65 SMT parts; procure the unchanged through-hole J1 separately. Gerber ZIP and fabrication directory are review outputs, not released for vehicle manufacture.

Nominal brake trip is approximately 1.766V raw. The conservative partial model reaches 1.824V, above the reported approximately 1.8V hard-brake measurement. Read ../DESIGN_REVIEW.md before treating this as a calibrated vehicle threshold.

ERC, PCB DRC and schematic parity pass. Existing physical qualification and current-reference holds remain. Close/reopen KiCad after an external file update so an old open tab cannot overwrite the corrected files.
