# Reproducible analytical circuit evidence

This is an analytical model, **not SPICE or hardware validation**. It reads the latest circuit spec by component role. Reviewed input SHA-256: `67ea7045ebc8a6039644aa422d1717b1aef2d9e36b36187bd29e2365fc639948`; parts: 71.

Regenerate with `python3 reports/analyze_circuit.py --spec circuit_spec.json` from the review directory. The JSON records all assumptions, corner witnesses, sources and conceptual traces.

| Quantity | Calculated result |
|---|---:|
| Current raw rising / falling point | 2.634938 / 2.622192 V |
| Current nominal rising at exact5V supply | 13.494 A |
| Current raw hysteresis / channel2 equivalent | 12.746 mV / 1.275 A |
| Brake raw rising / falling point | 2.005614 / 1.937679 V |
| Brake nominal fault window | 0.8000…5.3591 V |
| UV nominal cutoff / conservative VP range including bias | 10.7500 V / 10.3847…11.1260 V |
| Output combined load / source ratio | 15887.3 Ω / 0.87837 |
| Timer nominal / conservative model max | 270.33 / 399.01 ms |
| Timer + assumed2ms sensor/filter +20ms relay/output | 421.01 ms |
| Margin below500ms with those assumptions | 78.99 ms |
| Delayed BOOT clock after FAULT_OK release, model envelope | 1.479…10.156 ms |
| Worst guaranteed CLR release to BOOT clock margin | 1468.79 µs |
| Passes analytical startup recovery budget | True |

The timer keeps reference drift correlated between its charge source and half-reference threshold. Independent resistor temperature coefficients are conservatively allowed to differ; matched TCR is not silently assumed. Comparator bias is outward for this PNP-input family. Threshold corner tables exclude clamp leakage and reference load regulation, which remain explicit qualification items. The selected BAT54S has no guaranteed85°C leakage figure in the referenced datasheet, so these threshold corners are **not complete release bounds**.

Raw inlet voltage obeys `VIN = VP + SS14 forward drop`. The UV minimum including the input-bias allowance is 10.3847V atVP, above the AiM nominal10Vminimum without assuming any minimumdiode drop. For guaranteed operation at the tentative11.5VrawGLVminimum, the actual inletdiode drop must remain below 0.3740V at the worstUVcorner. Verify that cold,loaded condition;11.5…16V is a tentativeoperatingrange. The confirmedAiM datasheet doesnotstateaccuracy,temperature oroutputloadlimits, so the board'stentative−20…85°Cscope is notsensorqualification.

At Uc=5.25V, ideal +200A produces 4.7250V, above the current high-fault window 4.8797V. The circuit therefore does not cover the full +200A sensor range across the full allowed supply range; overload also faults unconditionally. Adjust the window only after fault-disconnection requirements and peak-current behavior are established.

Even ideal zero-current at maximumUc is 2.6250V, while ideal5kW at minimumUc is 2.5069V. The overlap proves that a fixed absolute threshold cannot guarantee both behaviors. Current release remains blocked pending a defensible sensor-rail strategy; reusing pin1 has not been approved in this snapshot.

The conceptual traces verify healthy startup, individual input conditions, coincidence trip, immediate sensor fault, fault persistence, initially late sensor readiness, and brownout. BOOT_CLK sets ARM_ONCE only once per POR cycle; later FAULT_OK recovery creates BOOT edges but does not create a new ARM_CLK edge. A recovered long brownout resets ARM_ONCE and can rearm PERMIT. The external relay latch still drops; the complete reset chain must be tested and shown to meet the permitted reset method. Passing an idealized trace is not physical qualification. The coupled RC corner calculation checks the main latch CLR release separately. The selected Microchip MCP809T-450 has a 150…700ms recovery reset delay (350ms typical) and4.25…4.50V trip interval (4.375V typical); similarly named TI devices have different limits.

Required bench evidence: measure threshold rising/falling points with actual sensor supply and hydraulic pressure; test every signal/supply/ground/reference disconnection separately; test shorts, negative inputs and sensor power remaining on while GLV is off; scope FAULT_OK/ARM_CLK/PERMIT on slow startup and brownout; measure total time to SDC-contact opening with installed suppression; test the declared temperature and GLV extremes; save calibrated resistor values and results before vehicle release.
