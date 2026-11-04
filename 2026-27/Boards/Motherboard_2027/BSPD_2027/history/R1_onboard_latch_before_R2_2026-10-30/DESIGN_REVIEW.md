# BSPD 2027 design review and implemented revision

**Status: engineering review; not released for vehicle manufacture.** The circuit and PCB changes below are implemented in the editable KiCad revision. Vehicle compliance cannot yet be claimed: the DHAB channel-2 reference interface, measured hard-braking pressure, and physical shutdown tests remain unresolved.

The original files are preserved in `original/`. The new project is `revised/BSPD_2027.kicad_pro`; its schematic, PCB, symbol library, BOM and placement data belong together. The original PCB must not be paired with the new schematic.

## Vehicle facts and sources

The user confirmed a 360 V nominal / 404 V maximum accumulator, LEM DHAB S/134 **channel 2**, increasing output for motoring current, current-sensor power from an Orion BMS 2, and an AiM X05SNP13520 brake sensor. The original connector and its pinout are retained, with an external high-side shutdown relay.

The 2027 V1 rules were verified against the [official SAE download](https://www.fsaeonline.com/cdsweb/gen/DownloadDocument.aspx?DocumentID=da79bcb4-0935-4f7b-83d7-0dbb8ce68d38). The repository PDF matches it byte-for-byte: SHA256 `f71df5552e341dab1b58f1ff47212e7281953d66b9c41833de8347560913ed0e`. Relevant provisions are EV.8.7 (BSPD), EV.8.1–8.2 (shutdown), T.4.3 (BSE) and EV.7.6 (fusing).

The [LEM datasheet](https://www.lem.com/sites/default/files/products_datasheets/dhab_s_134.pdf) gives channel-2 nominal offset 2.5 V and sensitivity 10 mV/A at 5 V supply, with ratiometric output. The [AiM datasheet](https://www.aim-sportline.com/download/doc/eng/sensors/oldies/Datasheet_BrakePressure0-2000PSI_101_eng.pdf) identifies X05SNP13520 as 0–135 bar, 1–5 V output, 10–30 V supply, 4 mA consumption. It does not provide sufficient accuracy, temperature or load limits to establish a complete worst-case pressure threshold.

Drive evidence and the conflicting historical sensor records are retained in [brake_sensor_evidence.md](reports/brake_sensor_evidence.md). The user-confirmed 135 bar sensor takes precedence over the older 100 bar document. Historical injected 2 V or 3 V tests are not a measured wheel-lock or hard-braking calibration.

## Original defects and their disposition

| Finding | Consequence | Revision / remaining action |
|---|---|---|
| Four mechanically adjustable trimmers with unspecified settings | Vibration, wiper failure, drift and untraceable thresholds | All four removed. Soldered resistor networks set the current, brake and fault-window thresholds. |
| LM358 devices used as comparators | Op-amp overload recovery and output behavior were not specified for the required logic operation | Replaced with industrial LM2901B comparators; explicit pull-ups and logic supply are provided. |
| Undefined 0.5/4.5 V window for the installed AiM 1–5 V sensor | Valid pressure above about 118 bar could be reported as a wiring fault | Brake signal is scaled by precision resistors; revised nominal raw-input window is approximately 0.8–5.36 V. |
| Current sensor channel, slope and supply omitted from the old design | A voltage setting could represent the wrong current / power | Confirmed channel 2 and 360 V nominal. The reference problem below remains a release blocker. |
| Absolute current window / reference with externally powered ratiometric sensor | Supply variation can cause missed 5 kW events or false faults, including valid high-current readings | Quantified; requires tighter supply qualification or a ratiometric hardware interface. Current pinout is retained pending that decision. |
| Original 50 kΩ / 12 µF timer with undefined capacitance, leakage and output loading | No defensible shutdown-time bound | Replaced with 39 kΩ / 10 µF timing, precision half-reference comparison, and active discharge. The analysis intentionally budgets an earlier trip. |
| Sensor wiring failures pass through the same timer as brake/current coincidence | Unnecessary delay of fault shutdown | Sensor-window and supply faults directly clear the hardware latch. Only brake/current coincidence is delayed. |
| No onboard trip memory; motherboard reset driven by STM32 | Reset behavior depends on vehicle electronics | Added a hardware trip latch. Fault recovery or MCU reset cannot restore the permit within the same uninterrupted GLV cycle. |
| A single POR-time clock could precede Orion sensor-rail startup | Valid startup could remain permanently inhibited | Uses both flip-flops: arm once on the first stable valid sensor state, then retain that arm history until power loss. |
| Floating unused CMOS inputs and omitted unused op-amp unit | Uncontrolled switching, excess supply current and undefined behavior | All remaining unused logic inputs are tied to defined rails; unused outputs are explicitly unconnected. |
| Missing local IC supply decoupling | Susceptibility to conducted noise and local supply transients | Local bypassing, input bulk capacitance and a separate logic rail are installed. |
| No intentional threshold hysteresis | Chatter near a threshold | Resistor feedback adds bounded hysteresis; current and brake behavior are calculated from their source resistance. |
| Direct sensor inputs without series protection | Input damage / interaction with other signal users during a wiring fault | Series resistors, defined open-circuit bias, filtering and rail clamps added. Clamp leakage remains part of physical qualification. |
| No board-level input fuse, reverse-polarity protection or TVS | Fault current and supply transients could damage the circuit | Added DC-rated 250 mA fuse, reverse diode and 18 V TVS. Source fault current and surge energy must still be checked. |
| Weak, unprotected op-amp permit output | Uncertain motherboard gate drive and output-fault behavior | Replaced by a transistor source stage, default-low bias, series current limiting and an output clamp. |
| PCB project allowed zero minimum clearance and 0.01 mm copper-edge spacing | Original “clean DRC” was not a meaningful manufacturing qualification | New rules use 0.25 mm track / clearance, 0.70 mm vias with 0.30 mm drill, and 0.30 mm copper-edge clearance. |
| Copper/component placement near mounting hardware | Possible shorts or mechanical damage | 3.7 mm copper/pad/via exclusion radii are implemented around the original mounting positions; qualify the actual hardware and connector clearance. |
| No LCSC sourcing fields | Ambiguous BOM and assembly matching | Every fitted component has manufacturer MPN, LCSC number and source URL in the schematic/BOM; PCB metadata is synchronized. |

Detailed independent reports: [original circuit audit](reports/original_circuit_audit.md), [original PCB audit](reports/original_pcb_audit.md), and [revised circuit review](reports/revised_circuit_review.md).

## Connector and shutdown interface

**J1 remains Molex 043045-0612 / 430450612, LCSC C234188**, using the original Micro-Fit 3.0 2×3 vertical footprint, position and orientation.

| Pin | Function |
|---|---|
| 1 | Unused, as originally assigned |
| 2 | BSPD permit: HIGH = healthy/permit, LOW = trip |
| 3 | DHAB S/134 channel-2 analogue signal |
| 4 | AiM brake-pressure analogue signal |
| 5 | GLV ground |
| 6 | GLV supply |

Pin 2 is a **control signal**, not a series shutdown-current terminal. It must control a dedicated normally-open relay whose contacts interrupt the high side of the isolation/precharge relay coils. The sibling motherboard has a K6 relay and an approximately 24 kΩ input divider. Its physical installation, contact rating and independent high-side path still require vehicle verification.

The external relay must remain open after a trip until an authorized person at the vehicle performs a manual reset. The driver, TSMS and shutdown buttons must not clear the trip. The BSPD supply must remain live when the shutdown circuit opens; otherwise its volatile latch is cleared. A permitted external GLV cycle can clear the onboard latch, but an MCU reset alone cannot do so. Brownout/recovery and a held motherboard reset must be tested against the actual external relay latch.

## Implemented latch and timing

`FAULT_OK` is a wired-AND permit from the sensor windows, undervoltage and timer comparator. Any fault immediately clears flip-flop A. At startup, flip-flop B waits for power supervision and a stable valid input state, then changes once from 0 to 1 to clock A healthy. B remains 1 after subsequent faults, so returning to a valid input state makes no new arming edge. A therefore stays tripped until a GLV cycle.

The timer charges only while current and brake comparators are simultaneously high. Its MOSFET actively discharges the capacitor whenever either condition is absent. Nominal time to the half-reference is:

`t = ln(2) × 39 kΩ × 10 µF ≈ 270 ms`.

The upper timing calculation includes positive capacitance tolerance, X7R temperature increase, resistor tolerance / temperature, reset-FET off leakage, comparator input bias and offset, and divider mismatch. DC-bias capacitance loss and ageing make this timer earlier, rather than later. The calculation reserves an external-relay release budget; that budget is **not a measured release time**.

The startup RC uses 47 kΩ. With the 10 kΩ fault-bus pull-up, this prevents the capacitor from holding the latch-clear input in its undefined logic region at the earliest arming edge. Replacing this resistor with 10 kΩ would reintroduce the independently identified startup race. The two-stage latch model covers delayed sensor startup, faults and recovery, pulses, power loss and reset within its ideal digital assumptions.

Undervoltage is measured on the protected supply, with a nominal cutoff of **10.75 V**. This conservatively inhibits the circuit below the AiM sensor's 10 V minimum supply. Actual GLV range, diode drop, reference drift and divider tolerance must be checked; low-voltage operation below this cutoff is intentionally inhibited.

This is an intentionally conservative earlier trip to ensure the circuit has opened by a sustained 500 ms event. EV.8.7.2 does not explicitly prohibit an earlier trip; that interpretation is not a separate SAE approval. Confirm actual transient immunity and complete shutdown time on the vehicle. The latest numerical results and model limitations are in `reports/`.

## Current reference: release blocker

The applicable current is **5000 / 360 = 13.8889 A**, using nominal accumulator voltage, not 404 V maximum. At a 5.000 V sensor supply, the ideal channel-2 output is **2.638889 V**.

The sensor output follows:

`Vout = (Uc / 5) × (2.5 + 0.010 × I)`.

| Supply Uc | Ideal zero-current output | Ideal 5 kW output |
|---|---:|---:|
| 4.75 V | 2.375 V | 2.506944 V |
| 5.00 V | 2.500 V | 2.638889 V |
| 5.25 V | 2.625 V | 2.770833 V |

The lowest 5 kW output is below the highest zero-current output. Consequently an absolute resistor/reference threshold cannot both maintain healthy zero-current operation and guarantee 5 kW detection across that supply range. Sensor error, reference drift, comparator offset and clamp leakage further reduce the margin. Orion's public documentation does not establish a tighter numerical bound for its current-sensor 5 V output.

The fitted current resistors are a **bench calibration starting point**, not a certified 5 kW threshold. The fixed upper current window also needs qualification at the maximum valid current and sensor supply; it can reject a legitimate high-current or saturated output. Do not regard the default values as final vehicle calibration.

The preferred adaptation is to sense the actual sensor supply at high impedance and derive a ratiometric current threshold and fault window. Reusing previously unused pin 1 would retain the connector and all existing functions on pins 2–6, but requires a new sense wire and an approved interface change. This change is **not implemented in the retained-pinout revision**. Alternatively, provide a qualified tighter Orion rail bound and calibrate the actual sensor over the required vehicle temperature range. Orion's warning against additional sensor-wire loads/taps also requires the shared signal interface to be qualified or buffered.

## Brake setting and calibration

For the confirmed sensor, the nominal conversion is:

`P_bar = 33.75 × (Vraw − 1)`.

The selected brake resistor network starts around **34 bar**, including nominal hysteresis / loading. This is provisional. Measure the actual pressure and voltage corresponding to hard braking before wheel lock, on the installed hydraulic circuit. Confirm front/rear circuit choice, braking under expected aero and tyre conditions, sensor error and hydraulic behavior. The older mechanical estimate in Drive is not a release calibration.

Set thresholds by replacing the specified soldered resistor values and updating the BOM, schematic and PCB fields together. Use qualified precision parts of the same package. No potentiometer, switch with moving contacts, or firmware setting is used. A resistor value should be accepted only after the complete sensor and comparator transfer path has been measured.

## Manufacturing and sourcing

The revised PCB retains the original approximately 40.06 × 54.28 mm outline and four 4 mm mounting cutouts. Final ERC, DRC, connectivity and schematic-parity checks each report zero issues. A separate assembly check confirms no via drill intersects an SMD solder pad. All 71 populated parts have synchronized LCSC/MPN fields. The PCB has 75 vias with 0.70 mm diameter / 0.30 mm drill and no track narrower than 0.25 mm. The refreshed KiCad connector footprint retains mating/pad positions; its nominal pin drill is 1.02 mm versus the original 1.00 mm. The design uses top-side SMT parts and the exact through-hole connector. A 1.6 mm board is appropriate for the connector's published footprint; verify the mating enclosure and mounting stack.

Use `BSPD_2027_JLCPCB_BOM_SMT_REVIEW.csv` with `BSPD_2027_JLCPCB_CPL_SMT_REVIEW.csv` for the 70 SMT parts. The separate connector procurement file identifies the exact through-hole J1. `BSPD_2027_JLCPCB_BOM_REVIEW.csv` records all 71 components with JLC-compatible BOM columns. `BSPD_2027_detailed_BOM.csv` records each component and its catalog source. Placement and fabrication files, when exported, are engineering-review data. Check JLC's assembly preview for rotation, package orientation, MPN and pin 1 before ordering. LCSC identification does not imply current JLC assembly stock: the exact Molex connector may require quoted through-hole assembly, consignment or manual soldering.

The fuse is Littelfuse 0451.250MRL, LCSC C151116. Its 32 V DC interrupt capability is 300 A. Verify that actual prospective GLV fault current is within that rating or coordinate appropriate upstream protection. The TVS pulse rating does not itself prove survival of arbitrary GLV transients or automotive load dump. The selected reference and supervisor limit this component selection to **85 °C maximum ambient**, subject to thermal rise; no 125 °C board qualification is claimed.

The layout preview may omit a body where a bundled connector or fuse 3D model is unavailable; their sourced footprints and BOM entries remain present. The original design credits Arda Caliskan and Manny Gimenez.

## Residual component failure modes

The revision does not establish redundant, single-fault-tolerant coverage of every internal component. A shorted timing capacitor or reset-FET drain/source can prevent the timer from charging; a shorted output PNP or permit wire to GLV can hold the external permit high; and a comparator or latch stuck in its healthy state can mask a fault. These are concrete circuit failure modes that ERC/DRC cannot evaluate. End-to-end functional testing detects many of them at test time, but does not prove immunity to later failures. An independent redundant detection/driver path would require additional design and qualification.

A single analogue voltage window also cannot identify every physically incorrect reading that remains inside the legitimate signal range. Qualify the specified open/ground/supply wiring faults and separately establish the sensor, harness and external shutdown architecture's failure coverage. The mathematical model and this CAD review are not evidence of exhaustive fault coverage.

## Required physical verification before release

1. Resolve the current-reference interface and demonstrate 5 kW-equivalent current detection with the actual DHAB sensor, including supply and temperature extremes and healthy zero-current / regeneration cases.
2. Establish measured hard-braking pressure and select resistor values with sufficient error margin before wheel lock.
3. Test each sensor signal open, short to ground and short to its supply; disconnect sensor supply and ground separately. Confirm the complete circuit latches out, rather than only a comparator LED or test voltage.
4. Measure shutdown contact opening for sustained brake/current coincidence, intermittent pulses and sensor faults. Include relay flyback suppression and the actual shutdown load in the timing measurement.
5. Verify cold startup, delayed Orion rail startup, supply ramps, brownouts, fault recovery, held external reset and MCU reset. Driver-accessible controls must not restore a BSPD trip.
6. Confirm high-side normally-open contact placement, contact ratings, independent shutdown operation, absence of power feedback, and loss-of-GLV shutdown.
7. Provide the mandatory complete BSPD/current-sensor test using an external current wire/coil. Provide accessible **4 mm shrouded banana jacks**, neither red nor black, labeled **CS+** and **CS−**, on the vehicle or an adapter/breakout. Voltage injection alone is insufficient for that complete sensor test.
8. Complete fabrication/assembly preview, actual fuse coordination, sensor aggregate load checks, temperature, vibration and EMI verification, then release a final BOM with calibrated resistor values.

These are necessary checks tied to the known circuit and vehicle interface, not evidence that they have already passed. ERC/DRC and arithmetic validation do not certify the completed vehicle.
