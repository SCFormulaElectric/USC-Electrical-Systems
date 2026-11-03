# GND symbol conversion - November 1, 2026

Replaced 46 global GND labels with the installed standard `power:GND` symbol at the exact same electrical anchors. References are hidden, and the power symbols are excluded from the BOM, board and placement outputs. The 12 crowded pin-row placements face outward; the other 34 point downward.

Fresh KiCad XML netlists before and after have identical records for all 71 existing physical components and identical connections on all 41 nets (202 component-pin entries). Wires, existing components, sourcing fields and PCB files were not edited. The refreshed PDF was rendered and visually checked.

ERC has zero errors before and after. The same pre-existing warning remains: `hardware_trip_latch` (U9) is missing from the external Review symbol library, although its cached schematic definition remains present.

## Pre-existing local revision discrepancy

Before this conversion, the local schematic already contained the fully connected R1 latch block: U9, C13, C14, R33 and D3. It differs from the previously pushed 66-part non-latching R2 commit `6017215`. The local PCB file also differs from that commit. This GND-only edit preserves the local circuit; it does not restore R2 or reconcile those differences.

The existing DESIGN_REVIEW, BOM/CPL, Gerbers, release validation reports and root SHA256_MANIFEST describe the earlier R2 delivery and are not revalidated by this cosmetic edit. Do not interpret this ground-symbol report as a release of the current local circuit with those manufacturing outputs. The root manifest is left intact to avoid concealing the pre-existing differences.

The before/after XML netlists, ERC reports and `ground_symbol_conversion.json` record this conversion. `ground_symbol_update_hashes.json` covers only the files delivered by this GND-only update. The pre-conversion schematic/PDF and supporting project files are backed up under the local history folder when installed. No remote repository update is part of this edit.
