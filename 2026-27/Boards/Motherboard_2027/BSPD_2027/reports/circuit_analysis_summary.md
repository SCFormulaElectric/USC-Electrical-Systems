# R3 non-latching circuit analysis

This is an analytical model, **not SPICE or hardware validation**. It reads component roles and values from the current 66-part specification. Input SHA-256: `de4beb9c52aa1bcf60bb68d9367e5115a1cd5b356d517cc7e702f7de59afed60`.

Regenerate from the project directory with `python3 reports/analyze_circuit.py --spec circuit_spec.json`. The JSON contains assumptions, corner witnesses, independent nodal checks and conceptual traces.

## Permit behavior

`PERMIT = FAULT_OK AND POR_N`. Existing HC132 gates buffer the fault bus and directly apply the supervisor inhibit. There is no onboard trip storage or startup-memory network. Permit returns HIGH when faults clear, the timer has recovered and POR_N is HIGH; **no GLV reset is needed for BSPD permit recovery**. The user-confirmed external relay board retains the shutdown after its relay opens.

All 11 conceptual scenarios pass their segment-by-segment expectations: healthy and late-sensor startup, current alone, brake alone, sustained coincidence, recovery when either coincidence input clears, brief pulses, sensor/UV fault clearance and POR inhibit/recovery. These are model checks; relay retention is not simulated.

| Quantity | Calculated result |
|---|---:|
| Current raw rising / falling point | 2.634938 / 2.622192 V |
| Current nominal rising at exactly 5 V sensor supply | 13.494 A |
| Current raw hysteresis / channel-2 equivalent | 12.746 mV / 1.275 A |
| Current nominal fault window | 0.0990…4.8797 V |
| Brake raw rising / falling point | 1.766348 / 1.698420 V |
| Brake nominal fault window | 0.3571…4.6948 V |
| UV nominal cutoff / conservative VP range including bias | 10.7500 V / 10.3847…11.1260 V |
| Output combined load / source ratio | 15887.3 Ω / 0.87837 |
| Timer nominal / conservative model maximum | 270.33 / 399.01 ms |
| Timer + assumed 2 ms sensor/filter + 20 ms relay/output | 421.01 ms |
| Margin below 500 ms with those assumptions | 78.99 ms |
| Illustrative timer recovery from 5 V below the half-reference | 69.32 µs |

The recovery example uses an assumed 10 Ω reset-FET on-resistance; it is not a guaranteed physical recovery bound. Either C_HIGH or B_HARD clearing turns the existing FET on. The model retains charge and finite discharge, so TIMER_OK and permit recover when the capacitor crosses below threshold, rather than requiring a reset or clock.

## Tolerance limits

Analogue calculations are retained: reference drift stays correlated between timer charge source and threshold; resistor TCR may differ; comparator offset and outward bias, FET off leakage and positive X7R capacitance bounds remain included. Threshold corners exclude clamp leakage and reference load regulation. BAT54S has no guaranteed 85°C leakage figure in the referenced datasheet, so threshold corners are **not complete vehicle-release bounds**. The reset-FET, sensor/filter and suppressed-relay timing assumptions require measurement.

Raw inlet voltage is `VIN = VP + SS14 forward drop`. The minimum modeled UV cutoff, 10.3847 V at VP, exceeds the confirmed AiM 8 V minimum supply requirement without assuming a minimum diode drop. Operation at the tentative 11.5 V raw-GLV lower target requires actual diode drop below approximately 0.3740 V at the worst UV corner. Verify cold operation. The sensor sheet specifies a working range of -20 to 135 C and compensated range of -10 to 125 C; BSPD operation below -10 C still needs sensor qualification.

At Uc = 5.25 V, ideal +200 A produces 4.7250 V; the nominal high-fault boundary is 4.8797 V. The ideal +200 A point lies inside this nominal window. Sensor errors, window tolerances and overload clamping still require qualification. The minimum stated upper overload-clamp value at that rail is 4.9350 V. Ground/supply-disconnection behavior must be tested on actual sensors.

## Calibration still pending

Ideal zero-current output at maximum Uc is 2.6250 V, while ideal 5 kW output at minimum Uc is 2.5069 V at nominal 360 V TS. Their overlap prevents a fixed absolute threshold from guaranteeing both behaviors over that whole rail range. The declared TS maximum is 404 V; the power criterion uses 360 V nominal. Orion rail bounds/reference strategy and current calibration remain unresolved; J1 pin 1 is still unused. The actual sensor is AiM X05PSA02000P18, 0-2000psi with 0.5-4.5V output and 8-16V supply. The user reports 0.52V at rest and approximately 1.8V at hard braking. Its sheet specifies <+/-0.5% FS combined nonlinearity/hysteresis; this is not a complete temperature/offset/load error budget. The selected nominal brake trip is 1.766348 V raw. The modeled upper corner is 1.824350 V, which exceeds the reported approximately 1.8 V hard-brake measurement. This population therefore remains a bench starting point; validate or recalibrate before vehicle release.

The retained Microchip supervisor has 150…700 ms reset-release delay (350 ms typical), and a 4.25…4.50 V trip interval (4.375 V typical). This ordinary power supervision remains independent of fault retention.

Bench verification should check direct POR inhibition, fault clearance without GLV cycling, timer recovery after either input clears, thresholds with the actual sensors, total time to contact opening, loaded output and external relay retention. Very short LOW pulses may recover before a mechanical relay opens; measure the actual minimum release pulse. The BSPD itself deliberately retains no fault state.
