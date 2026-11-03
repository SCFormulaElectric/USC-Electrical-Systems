# BSPD 2027 — R2 external-relayboard latch

Updated October 30, 2026 at the user's direction. **The BSPD signal is now non-latching. Fault retention and manual reset belong to the separate relayboard.**

This remains an engineering-review revision. The earlier current-reference, hard-brake calibration and physical vehicle-qualification holds remain open; this change does not modify those settings.

## Implemented change

Removed the entire onboard fault-memory and startup-arming block:

| Removed reference | Function |
|---|---|
| U9 | 74HC74 dual flip-flop implementing trip memory and ARM_ONCE |
| C13 | U9 bypass capacitor |
| R33, C14 | Startup-arming RC |
| D3 | Supervisor diode-OR, redundant with direct logic gating |

The remaining U8 gates implement:

`PERMIT = FAULT_OK AND POR_N`

U8 gate 2 is NAND(FAULT_OK, POR_N); gate 3 inverts its output. These gates buffer the comparator fault bus so it does not supply the output transistor's base current. There is no clock, ARM_ONCE, flip-flop or retained fault signal on this board.

| Condition | BSPD pin 2 |
|---|---|
| Power supervision not ready | LOW |
| Sensor-window, undervoltage or timer fault active | LOW |
| Power ready and all fault conditions clear | HIGH |
| Fault clears after a previous trip | Returns HIGH; the external relayboard retains the opened relay according to its reset logic |

The power supervisor remains as a power/startup inhibit. Comparator hysteresis and the coincidence timer remain for signal conditioning and event timing; neither stores a fault requiring manual reset.

## Retained circuit and interface

All remaining reference designators, component values and packages are preserved. All 66 fitted components have manufacturer MPNs and LCSC numbers. J1 remains the exact Molex 043045-0612 / 430450612, LCSC C234188.

| J1 pin | Function |
|---|---|
| 1 | Unused |
| 2 | HIGH healthy / LOW fault, automatically recovering when faults clear |
| 3 | DHAB S/134 channel-2 analogue input |
| 4 | AiM X05SNP13520 brake-pressure input |
| 5 | GLV ground |
| 6 | GLV supply |

The original outline, mounting positions, connector position/orientation and remaining component placements are retained. The PCB is checked with an explicit 0.50 mm copper-edge clearance; other project constraints are preserved. Three inherited perimeter segments are moved locally to satisfy that existing edge rule.

The brake/current coincidence path is unchanged: U8 gate 1 permits RC charging only while both threshold comparators assert. Q1 discharges the timer when either condition clears. The 39 kΩ / 10 µF timer has an ideal nominal delay of approximately 270 ms; the current analytical evidence recalculates its tolerance budget. Sensor and supply faults bypass that coincidence delay.

The output stage, 2.2 kΩ current limit, clamp and HIGH-healthy polarity are unchanged. No relayboard or relay-reset circuitry is edited by this change. The user-confirmed external relayboard handles relay trip retention.

## Verification and manufacturing data

Current ERC, DRC, connectivity, schematic-parity, component-field and assembly results are recorded in `reports/final_validation.json` and associated reports. These distinguish CAD/analytical checks from physical tests.

The SMT BOM and CPL are regenerated together for 65 SMT parts. The all-component BOM includes the separate through-hole J1, which may require a JLC assembly quote, consignment or manual soldering. Gerbers, drill files and positions share the lower-left origin `(144.25, 106.86) mm`. The four 4 mm mounting cutouts remain routed circles in Edge.Cuts.

The earlier latched revision is retained in the delivered history folder for comparison. Its schematic, BOM and fabrication files must not be mixed with R2.

## Unchanged qualification items

- DHAB S/134 channel 2 increases during motoring and is powered by Orion BMS 2. At 360 V nominal, 5 kW corresponds to 13.8889 A and ideally 2.638889 V at a 5.000 V sensor supply. Ratiometric supply uncertainty still prevents an unconditional fixed-threshold guarantee. Pin 1 has not been repurposed; the reference-interface proposal remains separate.
- AiM X05SNP13520 is 0–135 bar / 1–5 V with 10–30 V power. The approximately 34 bar setting remains provisional until actual hard-braking pressure and tolerances are established.
- End-to-end sensor-fault, timing, supply, temperature and relay tests remain necessary. Verify that the relayboard captures the LOW interval and retains the opened relay until its permitted manual reset. Very brief LOW transients are not guaranteed to release a mechanical relay.
- The external normally-open contacts, high-side shutdown path, independent shutdown operation and driver/reset restrictions remain vehicle integration requirements. Removing the signal latch does not change those responsibilities.
- Prior limitations on clamp leakage, the 85 °C selected-component ceiling, fuse coordination and internal component failure coverage still apply. ERC/DRC do not establish exhaustive fault tolerance or vehicle compliance.

See `reports/revised_circuit_review.md` and `reports/circuit_analysis_summary.md` for the current review and analytical evidence. Historical original-design findings remain in `reports/original_circuit_audit.md` and `reports/original_pcb_audit.md`.
