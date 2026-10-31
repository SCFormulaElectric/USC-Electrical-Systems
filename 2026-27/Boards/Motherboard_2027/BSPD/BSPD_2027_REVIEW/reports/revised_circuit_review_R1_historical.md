# Historical R1 review — superseded by R2

The following review describes the prior onboard-latching design. It is retained only as historical evidence; use revised_circuit_review.md and circuit_analysis.json for R2.

# Independent revised-circuit review

Reviewed 2026-10-05 against the 71-part `circuit_spec.json` snapshot: 10 kΩ/10 kΩ precision signal dividers, LM2901B comparators powered from VP, 39 kΩ/10 µF timer, HC132 delayed valid-input startup clock, both HC74 sections implementing ARM_ONCE and trip memory, and HIGH-healthy transistor output. J1 pin 1 remains unused in this snapshot. Part references below belong to that snapshot; use circuit roles if subsequent revisions renumber components. Regenerated quantitative evidence is in `circuit_analysis.json` and `circuit_analysis_summary.md`, produced by `analyze_circuit.py`; their recorded spec hash identifies the exact analyzed values.

**Disposition: suitable as an engineering prototype after procurement and PCB verification; current/brake calibration and fault/temperature testing remain required before vehicle release. A fixed channel-2 voltage threshold cannot be certified over the unknown Orion sensor supply range.**

## Critical remaining findings

1. **Current threshold is still absolute rather than ratiometric.** Confirmed sensor input is LEM DHAB S/134 channel 2, 10 mV/A, with motoring raising voltage. The local REF5 is distinct from the Orion-supplied sensor rail. Across the sensor's allowed 4.75–5.25 V supply, zero-current output and the 5 kW-equivalent output overlap. No fixed resistor choice can both guarantee zero-current healthy and detect 5 kW over that complete supply range. Either obtain a sufficiently tight actual rail bound, use an authorized sense wire to the actual sensor supply, or explicitly restrict and validate the calibration conditions. J1 pin 1 has not yet been repurposed in this reviewed snapshot.
2. **The 28 kΩ/10 kΩ current divider has almost no nominal detection margin.** At exact 5 V sensor supply, it produces a nominal rising threshold around 2.635 V raw, or 13.5 A / 4.86 kW at 360 V. Comparator offset alone can exceed the remaining margin to 13.889 A. This is a bench placeholder, not a compliant final calibration.
3. **Input clamp tradeoff remains unresolved.** BAT54S gives useful negative clamping but has only a 25°C guaranteed leakage limit; its high-temperature typical leakage curves cannot establish a guaranteed channel-2 accuracy budget. Proposed BAV199 lowers leakage substantially, but its forward clamp can allow approximately −0.9 V, below the LM2901B −0.3 V absolute input limit. A 10 kΩ series resistor limits current, yet does not establish correct comparator outputs under sustained negative input or rule-compliant fault detection. Do not claim the BAV199 substitution is unconditional protection. Qualify the chosen network electrically, including negative inputs and power-off.
4. **Whole-board temperature capability is lower than the comparator rating.** LM2901B supports −40…125°C; selected LM4040AIM3 is the industrial −40…85°C grade, and MCP809T-450I/TT is also an industrial-temperature part. Set and verify the board operating range from the most restrictive selected component. Do not advertise 125°C capability merely because timer leakage was budgeted at that temperature.
5. **Hydraulic hard-brake pressure is unconfirmed.** AiM 1–5 V transfer is now reflected by the divided input, but the approximately 35 bar resistor setting is still a placeholder until the actual car's required hard-braking pressure is measured. The fixed setpoint and its upper tolerances must detect hard braking as required by the event's rules.
6. **Resolved: the valid-input startup RC loads the fault bus.** The original 10 kΩ START_RC series value allowed an early clock before guaranteed main-CLR release. It is now **47 kΩ**, giving a nominal coupled `(47k+10k)×100nF = 5.7 ms` time constant. The regenerated model gives at least **1.469 ms** between guaranteed CLR release and the earliest clock after its assumed bus-release allowance, comfortably exceeding the 45 ns recovery budget. Physical startup measurements remain necessary.

## Logic, latch, timing and output review

The LM2901B pin assignments implement the intended polarity. Low/high sensor-window outputs, undervoltage output and timer-trip output are open-collector and correctly share `FAULT_OK`. Current/brake threshold outputs are HIGH when exceeded. HC132 NAND output turns the timer-reset FET on whenever simultaneous brake/current is absent. The timer therefore charges only while both flags are asserted.

Both HC74 D inputs and asynchronous PRE inputs are tied HIGH. U9B ARM_ONCE is asynchronously cleared by POR_N and first sets HIGH on BOOT_CLK, generated from POR_N AND delayed FAULT_OK. Its Q drives U9A's clock; U9A is asynchronously cleared by FAULT_OK and supplies PERMIT. An initially late sensor can become ready and arm the board after the valid-input delay. After arming, later FAULT_OK recovery can generate BOOT_CLK edges, but ARM_ONCE already remains HIGH, so PERMIT does not receive another rising clock and remains tripped. This provides trip memory independently of the motherboard MCU reset, without simultaneous asynchronous SET/CLR assertion. Unused HC132 inputs are terminated. The Schottky POR-to-fault diode is preferable to a silicon diode for low-voltage CLR margin. Verify actual startup/brownout behavior and resolve the RC loading margin above.

The local latch rearms after its logic rail loses and recovers power. The system must establish that this restart path matches the permitted GLV power-cycle/reset behavior; an unintended local brownout should not be casually described as an authorized driver reset. The motherboard relay self-hold still requires its own reset injection after dropping.

### Timer bound

Nominal `R = 39 kΩ`, `C = 10 µF`, and trip at REF5/2 give:

`t_nom = R C ln(2) = 270.3 ms`.

Conservative positive bounds:

* R +1% → 39.39 kΩ.
* C +10% initial and +15% X7R temperature excursion → 12.65 µF.
* Reset-FET sink leakage budget 10 µA plus 50 nA conservative comparator-current allowance.
* Divider, comparator offset and reference-input bias produce approximately 2.51 V trip threshold at a nominal 5 V reference.

This gives `tau ≈ 498 ms`, final charging asymptote `5 − 39.39k×10.05µA ≈ 4.604 V`, and

`t_max ≈ tau × ln(4.604/(4.604−2.51)) ≈ 394 ms`.

A 20 ms relay/output budget leaves substantial margin below 500 ms. The reproducible model additionally allows resistor TCR of 100 ppm/°C over the tentative −20…85°C board range, correlated reference TCR, independent half-divider TCR, comparator offset and input bias. Its current timer maximum is approximately **399 ms**, or **421 ms** after assumed 2 ms sensor/filter and 20 ms relay/output budgets. DC-bias loss and normal ceramic aging decrease capacitance and make trip earlier; they do not justify ignoring positive capacitance bounds. Exact C12 dielectric/tolerance, FET temperature leakage, contamination/leakage, board-temperature range and suppressed relay release still require verification. These budgets are not physical measurements.

The chosen early nominal timing is intentional. The rules review identified that 2027's sustained-condition wording does not expressly prohibit an earlier trip; a claim of mandatory no-trip-before-500-ms would need an authoritative event interpretation.

### Output contract

The two-transistor high-side source preserves HIGH healthy / LOW fault. Local 47 kΩ default-low and the motherboard 24 kΩ input load combine to about 15.9 kΩ. Including 2.2 kΩ series resistance, the healthy BSPD output is approximately 87.8% of the source voltage; the motherboard gate receives half that. At VP ≈ 10.75 V, near the nominal undervoltage cutoff, this is roughly 4.6 V gate drive after transistor loss, adequate for the documented AO3400A relay driver under its normal operating conditions. Check this with the actual relay and minimum GLV. An output short is current-limited; its resistor power and clamp behavior must be checked against the declared continuous GLV maximum and transient budget.

## Analogue thresholds and tolerances

With nominal REF5 = 5 V:

| Role | Nominal comparator threshold | Nominal raw-signal equivalent |
|---|---:|---:|
| Current low fault, 1 MΩ/10 kΩ | 0.0495 V | 0.0990 V |
| Current high fault, 10 kΩ/9.53 kΩ | 2.4398 V | 4.8797 V |
| Brake low fault, 115 kΩ/10 kΩ | 0.4000 V | 0.8000 V |
| Brake high fault, 8.66 kΩ/10 kΩ | 2.6795 V | 5.3591 V |
| UV, 33 kΩ/10 kΩ vs REF5/2 | VP ≈ 10.750 V | Before inlet diode loss |

The brake upper fault threshold is now correctly scaled for the 1–5 V input. Valid upper-end pressure remains below the nominal 5.36 V raw fault threshold. The current window has been widened to accommodate the DHAB nominal clamping range at a qualified sensor supply. It can still reject valid saturated readings at the upper end of the unspecified Orion supply range; qualify it against actual peak current and supply bounds. A saturated channel-2 output near the sensor rail and a short to that rail are inherently difficult to distinguish with only a signal voltage.

The current 1 kΩ/4.7 MΩ positive-feedback network includes the 5 kΩ Thevenin resistance of the signal divider. Its nominal full hysteresis is about `2×(5k+1k)/4.7M×5 V = 12.8 mV` raw, approximately **1.28 A** on channel 2. It adds about 3.36 mV raw to the rising threshold with a LOW output near ground. The earlier 10 kΩ/2.2 MΩ combination would have produced approximately 6.8 A hysteresis and has been improved.

The revised UV cutoff is approximately **10.385…11.126 V at VP** with the modeled resistor/reference/offset corners and an input-bias allowance. Raw inlet voltage is `VIN = VP + SS14 forward drop`; its actual drop is unknown. The minimum cutoff remains above the AiM nominal 10 V supply requirement without relying on any minimum diode drop. To guarantee operation at the tentative 11.5 V raw-GLV lower target, the actual inlet diode drop must stay below approximately **0.374 V** at the highest modeled UV cutoff. Verify the cold loaded condition; 11.5…16 V is a proposed operating range, not an established vehicle specification.

The exact Microchip MCP809T-450 variant has a 4.25…4.50 V trip interval, 4.375 V typical, and a 150…700 ms reset-recovery interval, 350 ms typical. These values were verified from the manufacturer's table; other manufacturers’ 809 supervisor families have different specifications. Source: [Microchip MCP809/810 datasheet](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/11194c.pdf).

For the fixed local current reference, individual worst-case contributions at the present setting are approximately:

| Contribution | Approximate equivalent channel-2 error |
|---|---:|
| LM2901B full-temperature ±5.5 mV input offset | ±1.10 A |
| 10 kΩ/10 kΩ input divider, independent 0.1% values | ±0.26 A |
| 28 kΩ/10 kΩ threshold divider, independent 0.1% values | ±0.39 A |
| Bias of the three current-input paths and threshold reference | Up to approximately 0.24 A with conservative signs |
| LM4040A industrial overtemperature tolerance, ±0.75% | Approximately ±1.98 A |
| Proposed BAV199 leakage, conservative two-junction allowance | Approximately ±0.16 A |

Resistor temperature coefficients, exact reference operating-current change, PCB leakage and noise are additional. These are conservative sensitivity contributions, not a statistically justified root-sum-square budget. Their signs must be selected consistently for latest trip and earliest false trip. BAT54S full-temperature leakage cannot be replaced by its 25°C number.

The reference's initial 0.1% accuracy does not persist as 0.1% over temperature. The TI maximum temperature coefficient is 100 ppm/°C, yielding an industrial-range total tolerance of ±0.75%. Timing is substantially protected because the timer charge voltage and threshold share REF5, but fixed current and brake thresholds retain its absolute drift. Primary electronics references: [TI comparator datasheet](https://www.ti.com/lit/ds/symlink/lm339.pdf), [TI reference datasheet](https://www.ti.com/lit/ds/symlink/lm4040-n.pdf), [Nexperia BAV199](https://assets.nexperia.com/documents/data-sheet/BAV199.pdf), and [Nexperia BAT54S](https://assets.nexperia.com/documents/data-sheet/BAT54S.pdf).

## Channel-2 sensor bounds and a bench-only setting

[LEM's DHAB S/134 datasheet](https://www.lem.com/sites/default/files/products_datasheets/dhab_s_134.pdf) specifies full-temperature channel-2 offset ±1.5 A, sensitivity ±1.2%, and ±0.5% full-range linearity at 25°C, equivalent to ±1 A. Supply is 4.75–5.25 V; output is ratiometric in offset and gain. The absolute-accuracy table gives ±1.5 A at zero, ±4 A at 100 A, and ±7 A at 200 A at temperature extremes. The linearity condition must not be silently extended over temperature.

At nominal 360 V, 5 kW is 13.889 A and ideal output is 2.6389 V at 5 V supply. At 4.75 V it is 2.5069 V; zero current at 5.25 V is 2.625 V. These overlap before errors. Using decomposed errors with an explicitly assumed full-temperature ±1 A linearity allowance, conservative output normalized to a 5 V sensor rail is approximately 2.5406 V maximum at zero and 2.5860 V minimum at 13.889 A after ratiometric/noise allowance. That narrow interval leaves little room for electronics. Using a blanket ±7 A sensor bound instead almost eliminates it. Obtain calibration or a defensible operating-temperature bound rather than claiming unqualified full-temperature compliance.

For initial laboratory work with the sensor rail measured at exactly 5 V, increasing the current-set top resistor from 28 kΩ to **29 kΩ**, keeping 10 kΩ bottom, gives a nominal raw rising point around **2.567 V / 6.7 A** with present hysteresis. This deliberately conservative setting is useful for verifying timing and latch behavior. It is not a final vehicle threshold and does not solve unknown ratiometric supply variation. Record actual current, actual sensor supply, temperature and measured switching voltages; choose final resistors from the established vehicle voltage/current criterion and complete tolerance budget.

If pin 1 is expressly authorized as an actual sensor-supply sense, the reference should be high impedance, protected, buffered and itself monitored for open/short/out-of-range conditions. Use the rail **at the sensor**, including harness drops, not merely a nominal supply elsewhere. Current threshold should then use that sensed rail; the stable local reference remains appropriate for timer and independent supply/fault monitors. Available genuine TI buffer/comparator options previously verified are LM2904BIDR (LCSC C1849422) and LM2903BIDR (C2869804), both SOIC-8. A direct 5.25 V buffer must run from VP, not the 5 V logic rail, because these devices are not rail-to-rail at their positive supply. Pinout is standard 1 OUTA, 2 −A, 3 +A, 4 GND, 5 +B, 6 −B, 7 OUTB, 8 VP; comparator outputs are open collector.

For the confirmed AiM sensor, [the manufacturer's 0–2000 PSI document](https://www.aim-sportline.com/download/doc/eng/sensors/oldies/Datasheet_BrakePressure0-2000PSI_101_eng.pdf) provides 0–135 bar, 1–5 V, 10–30 V supply and 4 mA consumption. It does not supply an accuracy, temperature or output-load qualification bound. Specifications from the separate 0–100 bar product must not be transferred to this device. A nominal brake rising point of 2.0056 V raw corresponds to approximately 33.94 bar by the nominal 135 bar transfer, but this is not hydraulic or temperature qualification.

## Necessary release evidence

All 71 fitted components now have verified manufacturer/MPN/LCSC fields, and the finished layout passes ERC, DRC, connectivity and schematic-parity checks. Before changing release status, verify actual stock/assembly matching and complete: calibrated hard-brake and current thresholds; maximum voltage/current power criterion; continuous coincidence timing through physical SDC opening; each sensor/reference signal, supply and ground disconnected individually; shorts to ground/supply; negative/transient inputs; startup with active faults; fault recovery without unintended rearm; GLV cycling while external sensor supply stays on; loaded output at GLV extremes; relay suppression release time; and selected operating-temperature extremes. Record results rather than substituting ERC/DRC for functional verification.
