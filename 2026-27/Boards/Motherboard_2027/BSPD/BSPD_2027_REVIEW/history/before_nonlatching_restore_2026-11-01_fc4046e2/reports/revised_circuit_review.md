# R2 non-latching circuit review

The user confirms that the separate relayboard latches the relay. R2 therefore removes U9, C13, R33, C14 and D3. It retains the power supervisor and uses existing HC132 gates to implement `PERMIT = FAULT_OK AND POR_N` without fault memory. There are 66 fitted components.

## Pin-level change

U8.4 = FAULT_OK, U8.5 = POR_N, U8.6 = PERMIT_N; U8.9 and U8.10 = PERMIT_N; U8.8 = PERMIT, driving the unchanged R34/Q2/Q3 output stage. Coincidence gate U8.1/.2/.3, the RC timer, analogue thresholds and connector pinout are unchanged. Remaining reference designators and package selections are preserved.

The two CMOS gates isolate the fault bus from transistor base loading. Connecting a 10 kΩ-pulled-up fault bus directly to the 10 kΩ base resistor would give approximately 2.85 V with a 0.7 V base assumption, reducing the healthy logic margin. The existing unused gates avoid this loading without new parts.

Power not ready or any active window, supply or timer fault yields LOW permit. When all faults clear, the timer recovers and POR_N is HIGH, permit returns HIGH automatically. The external relayboard is responsible for retaining the opened relay until its permitted reset. No board power cycle or manual reset is required to restore this BSPD signal.

## Analytical checks

`analyze_circuit.py` reads the current manifest and generates `circuit_analysis.json` and `circuit_analysis_summary.md`. Its 11 conceptual cases cover startup, late sensors, single inputs, sustained coincidence, recovery after either input clears, sensor/UV fault recovery and POR recovery. The analogue and timing calculations are retained. These are analytical/conceptual checks, not SPICE or physical relay tests.

The timer remains approximately 270.3 ms nominal and 399.0 ms at the stated conservative component corners, or 421.0 ms including assumed sensor/filter and relay budgets. Actual suppressed-relay release and minimum LOW pulse needed to open it must be measured. No onboard pulse-memory or fault-retention feature is implied.

## Existing release limits

The current-reference strategy remains unresolved for the Orion-powered ratiometric DHAB channel 2. The 28 kΩ/10 kΩ setpoint has limited nominal 5 kW margin, and voltage/sensor/temperature error qualification remains necessary. The brake threshold remains a provisional approximately 34 bar. Clamp leakage, selected 85 °C component limits, fuse coordination and physical sensor/open/short/shutdown testing remain as previously documented. Pin 1 stays unused; no reference-sense interface is added by this change.

The user-confirmed external relayboard must retain the shutdown after its relay opens, with reset behavior suitable for the complete vehicle requirements. This review does not claim that every transient LOW pulse necessarily releases a mechanical relay, or that the vehicle has completed its physical qualification.

The superseded R1 review is retained as `revised_circuit_review_R1_historical.md` for traceability only.
