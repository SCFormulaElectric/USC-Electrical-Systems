# Original BSPD circuit and integration audit

Audit date: 2026-10-05. Read-only sources: `Motherboard_2027/BSPD/BSPD_5.kicad_sch`, `BSPD_5.kicad_pcb`, and the sibling `Motherboard/relayBoard.kicad_sch` / `.kicad_pcb`. This is an electrical/design review; physical tests and vehicle-specific calibration are still required. The separate rules report determines which rule edition is authoritative.

## Preserved connector and output contract

J1 is the exact Molex **043045-0612** / Micro-Fit 3.0 vertical 2×3 footprint, not a generic interchangeable 6-pin connector. Its electrical pinout is:

| Pin | Net | Meaning |
|---|---|---|
| 1 | Unused | Leave unused unless the vehicle harness is deliberately changed |
| 2 | BSPD_signal | **HIGH = healthy / permit**, **LOW = fault / trip** |
| 3 | current | External analogue current-sensor output |
| 4 | brake | External analogue pressure-sensor output |
| 5 | GND | GLV/sensor signal reference |
| 6 | 12V | GLV supply |

The connector carries no sensor 5 V supply. A revision must not silently assume its local precision reference is also the external sensor supply.

## Reconstructed original topology

* U1A/U1B are LM358 op-amp sections used as comparators: current > R9 wiper and brake > R10 wiper. Both high outputs enter U7A NAND, followed by U7B NAND used as an inverter with the other input tied HIGH. This correctly implements `high_current AND hard_brake`.
* U2 and U3 check brake/current respectively for < R11 wiper (`0.5V`) and > R12 wiper (`4.5V`). U5 ORs all four sensor faults with the brake/current simultaneous condition.
* R9–R12 are four 10 kΩ trimmers across the local nominal 5 V reference. R2 = 2.7 kΩ feeds the LM4040LP-5 shunt reference from raw GLV.
* The U5 fault output drives C4 = 12 µF through R4 = 50 kΩ. R1 = 1 kΩ and D1 provide faster discharge when fault goes LOW; R3 = 5 kΩ loads the fault output to ground.
* U4A compares a raw-GLV/2 divider (R5 = R6 = 47 kΩ) against C4. U4A therefore outputs HIGH before the timer crosses GLV/2, then LOW.
* There is no local trip memory, reset delay, startup inhibit, or supply-good monitor. All sensor faults also pass through the same delay.

## Material defects and improvements

| Priority | Finding | Consequence / correction |
|---|---|---|
| Critical | No guaranteed maximum trip delay: unspecified capacitor tolerance, R4 tolerance, source droop and leakage | Replace with a bounded timer design with measured/toleranced trip time comfortably below the governing rule limit, including output/relay delay |
| Critical | R3 loads weak HEF4071B output at about 2.4 mA at 12 V, plus initial timer charging current | Fault HIGH need not approach GLV, while the timer threshold follows GLV/2; delay increases or trip becomes impossible. Remove the unnecessary heavy load, use strong logic and a defined reference |
| Critical | BSPD recovery at the motherboard can be commanded by STM32 software | Hardware relay self-hold exists, but the reset injection is software-controlled. Add persistent BSPD hardware trip memory cleared by a permitted hardware power cycle, or redesign and validate the complete reset chain |
| High | Brake/current threshold values are unknown; trimmer position is not recorded | A label does not establish 5 kW or required hard-braking detection. Replace trimmers with selected soldered resistors and a calculation/calibration record |
| High | No voltage margin around declared 0.5–4.5 V sensor range | Normal endpoint tolerances can be interpreted as sensor faults. Select fault windows from actual sensor specifications and all wiring/supply tolerances, then test disconnections individually |
| High | Local 5 V reference has little current headroom and no undervoltage lockout | Thresholds move as GLV declines; unknown logic states can permit operation. Provide adequate regulation/reference headroom and independent supply-good inhibit |
| High | No local supply bypass capacitors on U1–U5/U7 or bulk/ESD/reverse-polarity protection | Susceptible to harness transients and logic switching noise; add local bypass, inlet protection and appropriate signal clamping/current limiting |
| High | Inputs reach LM358 pins directly | A short to supply or negative transient is not limited. Choose comparators and clamps with a verified input range, fault current and unpowered-input behavior |
| Medium | No comparator hysteresis | Near thresholds, noise can chatter logic and timer. Add small, calculated hysteresis that retains safe detection thresholds |
| Medium | C1/C2 are 100 nF directly across signals; the 10 kΩ resistors are parallel pull-downs, not series filters | Effective filter time constant depends on external sensor output resistance; sensor drive stability is unspecified. Use bounded series RC filtering and verify disconnected-wire discharge |
| Medium | U4B inputs unplaced and physically floating; unused U7 inputs 8,9,12,13 floating | Increased current/noise and undefined behavior. Terminate all unused analogue/CMOS inputs; unused outputs can remain open |
| Medium | Generic component values omit manufacturer IDs, temperature grade, tolerance and LCSC codes | No controlled procurement or reproducible worst-case behavior. Add exact orderable component IDs, LCSC fields and assembly BOM/CPL |
| Medium | Board dimensions/mounting circles are freehand Edge.Cuts, with no explicit mounting keepouts | Retain the connector location/clearance and required mounting geometry; use true NPTH mounting footprints and copper/component keepouts |
| Low | Many library/property mismatches and off-grid schematic endpoints | Improve maintainability and clean ERC/library references; mismatch warnings alone do not establish wrong physical pinout |

The nominal LM358 family is specified for 0–70°C. Its inputs include ground but do not include the positive rail; normal 0.5–4.5 V inputs are within common mode at 12 V, so the normal input range is not itself a defect. A short to the positive supply needs a comparator whose behavior is expressly characterized for that condition or an input network that keeps the comparator inside its range. The HIGH output also does not reach GLV, making the motherboard gate-drive margin dependent on the selected part and GLV minimum. Primary source: [TI LM358 datasheet](https://www.ti.com/lit/ds/symlink/lm358.pdf).

## Original timing calculation and limits

Ignoring leakage, source impedance and comparator offset:

`tau = 50 kΩ × 12 µF = 0.600 s`

`Vtimer(t) = Vfault_high × (1 − exp(−t/tau))`

`Vtrip = GLV × 47k/(47k+47k) = GLV/2`

`ttrip = −tau × ln(1 − Vtrip/Vfault_high)`

For GLV = 12 V, Vtrip = 6 V:

| Actual fault HIGH | Nominal trip time |
|---|---:|
| 12.0 V (ideal rail output) | 416 ms |
| 11.5 V | 443 ms |
| 11.0 V | 473 ms |
| 10.5 V | 508 ms |
| 10.0 V | 550 ms |
| 9.0 V | 659 ms |
| 8.0 V | 832 ms |
| 7.0 V | 1.168 s |
| 6.0 V or below | Never crosses the nominal trip threshold |

Even an ideal 12 V fault output gives **524 ms** with illustrative +5% R4 and +20% C4 tolerance, before comparator/output/relay release delay. Those tolerance assumptions are a sensitivity example, not a claim that the undocumented installed components have those exact ratings. Since no exact C4/R4 part, tolerance, leakage, temperature range, or U5 manufacturer variant is specified, a valid finite worst-case upper bound cannot be established from the design files.

R3 alone draws 12 V/5 kΩ = 2.4 mA at a rail HIGH; initial R4 charging adds 0.24 mA. For comparison, the HEF4071B datasheet at VDD = 10 V guarantees HIGH source current only around 0.9 mA at output 9.5 V over the hotter specified range. It is inappropriate to assume a near-rail HIGH under the original load. Source: [Nexperia HEF4071B datasheet](https://assets.nexperia.com/documents/data-sheet/HEF4071B.pdf).

The reset path is not an exact zero-state reset. Above approximately a diode drop, the discharge time constant is roughly 1 kΩ×12 µF = 12 ms plus U5 sink impedance. Near/below the diode drop, discharge continues through 50 kΩ. Closely spaced fault pulses can retain charge and shorten the next delay. This is safer than an excessively late trip but makes the promised continuous-fault timing ambiguous and needs explicit verification.

C4 leakage is also significant: e.g. a 10 µA leakage current across 50 kΩ changes the final voltage by 0.5 V. Actual C4 leakage is unspecified. Timing supply/reference should be independent of weak logic-output swing.

## Original reference calculation

Four 10 kΩ trimmers each draw 0.5 mA from 5 V, total 2.0 mA. At GLV = 12 V, R2 feeds `(12−5)/2.7k = 2.59 mA`, leaving nominally only 0.59 mA for the shunt. At the approximately 74 µA minimum operating current listed for a 5 V LM4040-N variant, minimum GLV for nominal pot loads is `5 + 2.7k×(2.0mA+0.074mA) ≈ 10.60 V`, before resistor/pot/reference tolerances. The exact original part grade is undocumented.

Below regulation, the four trimmers form 2.5 kΩ to ground, so with no shunt conduction the nominal reference becomes `GLV × 2.5k/(2.7k+2.5k) ≈ 0.4808×GLV`. At GLV = 10 V, it is about 4.81 V, moving all four thresholds. Source: [TI LM4040-N datasheet](https://www.ti.com/lit/ds/symlink/lm4040-n.pdf).

## Motherboard relay/latch integration

The sibling motherboard's `BSPD Fault` net is J1 pin 12 and enters R5 = 12 kΩ. R8 = 12 kΩ pulls the AO3400A Q1 gate to ground. Thus:

* BSPD output sees an approximately **24 kΩ** resistive load.
* Q1 gate nominally receives **half** the BSPD output HIGH.
* HIGH permits Q1 to sink the K6 coil; LOW or disconnected BSPD wiring turns Q1 off.

K6 is HF42F/012-2HST (LCSC C165254). Coil terminals are footprint pads 1/6. Pad 1 is Q1 drain; pad 6 joins pad 3. Normally-open auxiliary contact pads 2/3 connects GLV+ to the coil's high side after pickup. A separate normally-open contact pads 4/5 is in the SDC loop. K6 pad 4 = `SDC 1`; pad 5 joins K5 pad 4. The contact chain continues through K5, K4 and K7 to `SDC 2`. This is actual relay interruption of the SDC loop; Q1's coil return being low-side does not mean the SDC itself is low-side. The vehicle harness must verify that the SDC loop is in the positive supply path.

K6 therefore **does provide a physical self-hold latch**: when Q1 turns off, K6 drops, opens its own coil supply contact, and cannot restart just because BSPD output later returns HIGH. The original board's absence of local latch must be interpreted in this integration context.

Restart supply comes through D2 from Q3 PMOS drain. Q3 is driven through R25 = 47 Ω by Q4 NMOS. Q4 gate is driven through R22 by the `Reset_Latch` net from STM32 U5 pin 3 / PC15. This is a **programmable reset injection**, shared with other safety relays. A GLV power cycle alone leaves K6 dropped until that injection occurs. A reset held continuously can defeat the auxiliary-contact self-hold behavior after the BSPD signal recovers. A persistent trip latch on the revised BSPD board can prevent a software reset from clearing its fault.

An exact reset-button location, firmware policy and high-side SDC harness arrangement are not established by the files reviewed. The BSPD output should be validated at the 24 kΩ load plus cable capacitance, at minimum/maximum GLV and during startup, brownout, power-off and disconnection. Relay release time and suppression diode delay belong in the final total trip budget.

## PCB checks and physical findings

KiCad 10.0.6 parsed and checked the original board. Its normal DRC produced **23 library warnings and 0 unconnected items**, not 23 copper-clearance defects. Schematic parity additionally reports 18 field mismatches (Description/Datasheet metadata). A stricter 0.25 mm clearance review produced 91 clearance findings and two silk-overlap findings; original routing frequently uses approximately 0.20 mm spacing. These are improvements against the stricter target, not proof that the original meets no manufacturing process.

Original board has 24 footprints, 269 track segments, 38 vias, all tracks 0.25 mm, and a bottom copper ground zone. Outer Edge.Cuts bounding box is approximately 40.11×54.33 mm with slight skew. Four 4 mm diameter mounting cutout circles are at (146.90,104.13), (146.95,55.42), (180.98,103.59), and (181.55,55.50) mm. Component/library mismatch checks should be resolved by retaining the exact connector footprint and validating its manufacturer dimensions, not by blindly changing the connector.

Original ERC produced **3 errors and 128 warnings**: the errors are missing power-drive declarations and J1 unused pin lacking an NC marker; material warnings include the unplaced/floating U4B unit and unavailable custom trimmer libraries. Many other warnings concern off-grid endpoints and embedded/library differences. ERC errors do not by themselves mean the physical GLV and GND connections are absent.

## Vehicle parameters that must be established before sign-off

1. Actual DHABS134 current-sensor **channel** and signal polarity at J1 pin 3: channel 1 ±50 A / nominal 40 mV/A, or channel 2 ±200 A / 10 mV/A. The same voltage threshold means a fourfold difference in current. Harness confirmation is necessary.
2. External sensor 5 V minimum/maximum at the sensor, ratiometric behavior, supply/ground wire-drop limits and sensor offset/gain errors over the vehicle temperature range. Local board reference and external sensor supply are distinct.
3. Actual maximum TS operating voltage (not just nominal 360 V), so the current-only power criterion can be guaranteed at the largest voltage. At nominal 360 V, 5 kW corresponds to 13.889 A; this is not a maximum-voltage calibration by itself.
4. Brake sensor manufacturer/type, full-scale pressure, transfer equation, tolerances and the measured hydraulic pressure needed to meet the event's hard-braking criterion. An arbitrary midrange brake threshold cannot establish compliance.
5. GLV operating/transient voltage range, output gate/load limits, relay coil/operate/release behavior at temperature, SDC positive-loop harness and physical power-cycle reset path.
6. Validation of every independently disconnected signal, sensor power and sensor ground wire; short-to-ground/supply; current direction; threshold extremes; uninterrupted simultaneous brake/current trip; and permitted restart behavior.

These are integration/calibration requirements. A revised PCB can make threshold selection stable and reproducible, but it cannot infer unknown vehicle values from the original trimmer footprints.

## Current-sensor tolerance supplement

The supplied DHAB S/134 identity was checked against [LEM's current manufacturer datasheet](https://www.lem.com/sites/default/files/products_datasheets/dhab_s_134.pdf). Its channel 1 is ±50 A / 40 mV/A; channel 2 is ±200 A / 10 mV/A. Both offset and gain scale with the external 4.75–5.25 V supply: `Vout = Uc/5 × (2.5 + G×I)`.

Channel 1 full-temperature offset is ±0.35 A and sensitivity error ±1.5%; its absolute-accuracy table reaches ±1.5 A at full scale. At 360 V, ideal 5 kW corresponds to 13.889 A and 3.0556 V at exactly 5 V supply. At 4.75 V, the same ideal current produces 2.9028 V. A conservative ±1.5 A error allowance lowers that to 2.8458 V before ratiometricity, noise, board attenuation and threshold errors. Therefore, a fixed 3.0556 V reference cannot guarantee the desired power threshold over the full external supply range. Harness/channel/polarity confirmation and conservative threshold calibration remain mandatory.
