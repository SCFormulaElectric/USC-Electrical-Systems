**The integrated VIL/RML schematic is not ready for compliance sign-off or ordering.**

**Later recheck:** See [PCB_FSAE_REVIEW.md](PCB_FSAE_REVIEW.md) for the current schematic and PCB assessment with confirmed conformal coating. The latest saved schematic has zero ERC errors and three warnings; the dangling bus entry is gone. Supplier corrections described below have been overwritten again in the saved design. The electrical circuit is unchanged, so the functional findings below still apply; earlier supplier and ERC status statements are historical.

Reviewed `integrated_vil_rml.kicad_sch` as saved on November 7, 2026. The supplier URL corrections have since been applied to the schematic at the user's request: R6/R8 links corrected, R9/R11 URL text normalized, U2/D7/R12 missing links filled, U1's datasheet made device-specific, and affected purchasing fields cleaned. Connectivity, component values, symbol identities, and assigned footprints are unchanged. Existing user modifications were preserved. No Graphify or other coding-skill packages were used and no graphs were generated.

The rules basis is [Formula SAE 2027, Version 1.0, September 1, 2026](https://www.fsaeonline.com/cdsweb/gen/DownloadDocument.aspx?DocumentID=da79bcb4-0935-4f7b-83d7-0dbb8ce68d38), downloaded from the official Series Resources page. The folder identifies the 2026–27 season. Maximum charged TS voltage, GLV supply range, and external lamp specifications were not provided.

The companion [COMPONENT_AUDIT.csv](COMPONENT_AUDIT.csv) covers all 42 non-power symbols: 33 board electrical parts, four mounting holes, and five items excluded from the board/BOM. It records the assigned footprints, current supplier fields, verified URLs, and outstanding issues. It is an audit, not a fabrication BOM. All 28 sourced electrical parts now have whitespace-free IDs and matching JLCPCB/LCSC URL IDs. KiCad export succeeds. The latest saved schematic now has one ERC error and five warnings: a newly added, disconnected bus entry accounts for one error and two warnings; the other three warnings are unchanged. The latest editor save had also reverted the supplier corrections, so those verified property changes have been restored while preserving the new drawing content. Reload the schematic from disk before saving an older open editor copy.

The findings below prevent a clean sign-off.

| Priority | Finding | Required action |
|---|---|---|
| High | No startup lamp-check circuit or control input is present. | Implement or document an external parallel lamp-check path. It must operate both RML lamps with the other required indicators and must not block normal HV indication. See EV.6.2.7.a and EV.6.3. |
| High | D3/Q3/R6/U1 do not establish guaranteed RML turn-on by 60 V. | Rework or substantiate the detector across component tolerances, temperature, and LED aging. Check both rising and falling voltage. |
| High | U2 is NE555P, while the timing topology and notes describe the CMOS LMC555 application. | Validate or redesign the actual NE555 circuit, or select the intended CMOS timer and update its symbol, sourcing, model, and package together. Check duty cycle and reset-low operation. |
| High | F1/F2/F3 have no actual fuse MPN, supplier ID, datasheet, or voltage/interrupt rating. | Select fuses for their respective TS or GLV circuits before approving footprints. A 750 mA value and 1206 outline do not establish suitability. |
| High | The external VIL and two RML lamps are not specified. | Identify the actual lamp assemblies, their current, voltage, visibility, and required approvals. Check their operation with this driver. |
| Medium | D2 and R2 are unsourced. The R6/R8 link errors have been corrected. | Complete the missing purchasing data. |

The relevant 2027 requirements are different from the older RML rules.

| Rule | Requirement relevant to this schematic | Assessment |
|---|---|---|
| EV.5.7.1–.3 | VIL powered and controlled directly from vehicle-side TS; on at 60 V and above, clearly off below 50 V. | Appropriate supply topology if HV inputs connect after the isolation relays. Thresholds and external lamp performance remain unproven. |
| EV.6.2.6–.7 | RML powered from GLV, usual operation controlled by hardwired TS detection; 0.66–1.33 Hz at 50% duty above/equal to 60 V; off below 50 V. | Correct power/control concept. Frequency is nominally in range; duty and detector margins need work. |
| EV.6.3 | Synchronized startup lamp check begins within 1 second and stays continuously on for 2–6 seconds. | Absent from this schematic. |
| EV.7.6.1–.2 | Suitable overcurrent protection, including DC voltage and interrupt ratings. | Cannot verify unspecified fuses. |

The normal RML frequency target is therefore reasonable for **2027**. Do not change it to 2–5 Hz based on an older ruleset.

The HV detector needs a tolerance analysis, not just a nominal simulation.

The exported electrical netlist confirms this path: HV+ → F1 → D3 → Q3 → R6 → U1 input LED → HV−. Q3 also supplies the external VIL through R2 and connector LED2. The JFET gate is intentionally tied to HV−.

D3 is [BZT52C51-7-F / C177017](https://www.lcsc.com/product-detail/C177017.html). Its [manufacturer datasheet](https://www.diodes.com/_files/datasheets/ds18004.pdf) specifies a 48–54 V zener range at 5 mA. U1 is [Everlight H11L1 / C78588](https://www.lcsc.com/product-detail/C78588.html); the [H11LX datasheet](https://en.everlight.com/wp-content/plugins/ItemRelationship/product_files/pdf/H11LX.pdf) gives a 1.6 mA maximum turn-on threshold under its stated test conditions and recommends 10% drive margin for aging.

For illustration, at 60 V with a 54 V zener, 1.5 V optocoupler forward drop, and R6 at +1%, even neglecting Q3's voltage drop:

`I_U1 ≈ (60 − 54 − 1.5) / (4300 × 1.01) = 1.04 mA`

That is below 1.6 mA, before applying the recommended margin. This calculation is a tolerance warning, not an exact switching-voltage prediction: D3's voltage also depends on current and temperature. The supplied data do not guarantee the needed detector current by 60 V.

Q3 is a source-follower supply whose operating voltage also depends on device spread. Its [onsemi datasheet](https://datasheet.lcsc.com/datasheet/pdf/3eeb127c4379fe0085324c76834db665.pdf?productCode=C45082793) lists gate threshold from −14 to −6 V at the specified test point. The local SPICE model uses a nominal `vth=-10`; it does not prove all production devices behave identically. Validate optocoupler current, VIL brightness, and the below-50 V off state at the limits. The external VIL LED has no selected MPN, so its visibility and forward-voltage limits cannot currently be assessed.

There is also a thermal dependency. As an example only, with Q3's source at 10 V, a 2 V VIL LED, and a 1.15 V optocoupler LED, the two branches draw about 5.69 mA. At a hypothetical 600 V TS, Q3 dissipates about 3.07 W and D3 about 0.29 W. Confirm actual maximum voltage, load, ambient temperature, and mounting. Q3's metal case is electrically connected to its drain; its horizontal mounting must preserve insulation. These numbers do not constitute a thermal sign-off.

The timer package is correct, but its electrical substitution is unresolved.

U2's purchasing fields identify [TI NE555P / C46749](https://jlcpcb.com/partdetail/TexasInstruments-NE555P/C46749), and `Package_DIP:DIP-8_W7.62mm` matches that part. Its pin mapping is correct. The embedded library identity remains `Timer:LMC555xM`, and the description still says SOIC-8; those fields are stale.

The circuit connects pin 3 through R7 = 750 kΩ to the joined trigger/threshold pins and C4 = 1 µF. This corresponds to the [LMC555 datasheet's Figure 8-9](https://www.ti.com/lit/ds/symlink/lmc555.pdf). The ideal formula gives approximately 0.95–0.96 Hz. R7 ±1% and C4 ±5% alone give roughly 0.90–1.02 Hz; this excludes IC errors and supply effects.

Using KiCad's installed ngspice engine and the repository's `NE555.lib`, an isolated timer check with the schematic's R/C values, control-pin capacitor, and discharge pull-up/pull-down produced:

| GLV supply | Frequency | Output-high duty |
|---|---:|---:|
| 9 V | 0.867 Hz | 54.63% |
| 12 V | 0.898 Hz | 53.12% |
| 15 V | 0.906 Hz | 52.65% |

This test forced RESET high and omitted the MOSFET/lamp load and gate zener. It demonstrates nominal oscillator asymmetry; it is not a full-board or production-corner simulation. The non-rail-to-rail bipolar output and input currents mean the CMOS formula alone cannot establish 50% duty. Measure the actual lamp waveform across the specified operating range.

U2 RESET also needs attention: when Q4 is off, R8 = 1 kΩ is the only pull-down. The [NE555 datasheet](https://www.ti.com/lit/ds/symlink/ne555.pdf) specifies up to 1.5 mA RESET current at 0 V and a reset threshold as low as 0.3 V. A 1 kΩ pull-down does not establish a guaranteed low level from those limits. An active pull-down or a properly analyzed alternative is needed if retaining this timer. Simply reducing R8 also increases its enabled-state dissipation.

The supplier audit found two substantive link errors and several incomplete fields. The URL corrections in the following table have now been applied; the original data are retained here to explain the changes. D2, R2, and F1–F3 still require actual part selection.

| Reference | Original data at review | Verified correction / result |
|---|---|---|
| R6 | Value 4.3 kΩ, YAGEO RC0805FR-074K3L, ID ` C137518`; LCSC URL points to C4382. | [C137518](https://www.lcsc.com/product-detail/C137518.html) is the specified YAGEO 4.3 kΩ part. [C4382](https://www.lcsc.com/product-detail/C4382.html) is a UNI-ROYAL 5.6 kΩ resistor. Replace the LCSC URL and trim whitespace. The stored JLCPCB URL resolves correctly. |
| R8 | Panasonic ERJP06F1001V, ID ` C441981`, stated 0.5 W; JLCPCB/LCSC/Datasheet links point to C17513. | Use [JLCPCB C441981](https://jlcpcb.com/partdetail/ERJP06F1001V/C441981) and [LCSC C441981](https://www.lcsc.com/product-detail/C441981.html). The old [C17513](https://jlcpcb.com/partdetail/0805W8F1001T5E/C17513) is a UNI-ROYAL 1 kΩ, 0.125 W part. At 12 V, an enabled R8 dissipates approximately 0.144 W, so this is a meaningful power-rating mismatch. |
| R9, R11 | C17414 and 10 kΩ are correct, but the JLCPCB URL contains a capacitor MPN in its text. | The existing URL still resolves to the correct resistor by ID. Normalize to [0805W8F1002T5E/C17414](https://jlcpcb.com/partdetail/0805W8F1002T5E/C17414); this is URL cleanup, not a wrong ordered part. |
| U2 | `C46749 ` has a trailing space; LCSC URL and Datasheet are blank. | Trim ID; add [LCSC C46749](https://www.lcsc.com/product-detail/C46749.html) and the TI NE555 datasheet if NE555P remains the intended part. |
| D7 | C84256 / NCD0805R1 and its JLCPCB URL match; LCSC URL is absent. | Add [LCSC C84256](https://www.lcsc.com/product-detail/C84256.html). Manufacturer is Foshan NationStar Optoelectronics. |
| R12 | C26010 / 0805W8F3301T5E and its JLCPCB URL match; LCSC URL is absent. | Add [LCSC C26010](https://www.lcsc.com/product-detail/C26010.html). Manufacturer is UNI-ROYAL. |
| D2 | BZT52C8V2 and SOD-123 footprint, but no MPN/manufacturer/ID/supplier URLs. Datasheet points to a Diotec B-series family. | Select the actual C-series part. D5's already-verified MDD BZT52C8V2 / C173432 is a candidate with the same stated value and package, subject to the circuit's requirements. |
| R2 | 2200 Ω, 0805, with no purchasing fields. | Select the exact resistor and document tolerance/power rating. |
| F1, F2, F3 | Only 750 mA and 1206 footprint; explicitly marked unresolved. | No validated purchasing part or footprint match is possible until a fuse is selected. F3 is GLV; F1/F2 are TS, so their voltage/interrupt requirements differ. |

All 22 distinct populated C-numbers, after trimming whitespace, identify the stated MPNs. All 41 distinct stored supplier URLs were checked. The two wrong-part link groups are R6 and R8. R9/R11's misleading URL text nevertheless opens the right component. One direct JLCPCB request for C49678 was rate-limited; an independent page retrieval verified its correct identity and package. This audit verifies identity and URL targets, not inventory reservation. The stored stock quantities and October “in stock” notes are historical and should not be treated as current purchasing guarantees.

R12 and D7 now use `JLCPCB_URL`, consistent with the other sourced parts. Several `Datasheet` fields still point to product pages rather than PDFs. U1 now links directly to the device-specific H11LX PDF. D4's description incorrectly says 1500 W/DO-201AE, although its actual MPN and SOD-323 footprint match the selected PESD12VL1BA.

The footprint review found no definite package or pad-number mismatch among the parts with specified MPNs.

| References | Assigned footprint / verified package | Result |
|---|---|---|
| C1, C3, C5 | 0805 ceramic capacitor; hand-solder pads | Package matches selected MPNs. |
| C4 | 7.2 × 5.0 mm body, 5 mm pitch radial capacitor | Matches WIMA MKS2C041001F00JSSD. Manufacturer dimensions include 10 mm body height and 0.5 mm leads; assigned drills are 0.75 mm. [WIMA dimensions](https://www.wima.de/wp-content/uploads/media/e_WIMA_MKS_2.pdf). |
| D1 | SOD-523 | Matches 1N4148WT-7; pad 1 cathode, pad 2 anode. |
| D3, D5 | SOD-123 | Matches selected zeners; pad 1 cathode, pad 2 anode. Their inherited SOD-123F descriptions/filters are stale. |
| D2 | SOD-123 | Generic package plausible; unverified without an exact ordered part. |
| D4 | SOD-323 | Matches bidirectional PESD12VL1BA,115. |
| D7 | LED 0805 | Matches NCD0805R1 package; symbol uses pad 1 cathode, pad 2 anode. Assembly polarity still needs the manufacturer's package marking. |
| Q2, Q4, Q5 | SOT-23 | AO3400A/AO3401A mapping is 1 gate, 2 source, 3 drain. Correct. |
| Q3 | TO-247-3 horizontal, tab down | Electrical mapping matches: 1 gate, 2 drain/case, 3 source. Nominal lead pitch matches. The purchased part has straight leads; forming, mounting geometry, and drain-tab insulation require an assembly review. |
| U1 | DIP-6, 7.62 mm rows | H11L1 pins: 1 anode, 2 cathode, 3 NC, 4 output, 5 GND, 6 VCC. Correct. |
| U2 | DIP-8, 7.62 mm rows | Correct for NE555P, regardless of the stale SOIC/CMOS description. |
| J1 | Molex 43045-0412, 2 × 2, vertical, 3 mm pitch | Matches 430450412/C277721. [Molex specifications](https://www.molex.com/en-us/products/part-detail/430450412). |
| Molex1, Molex2, LED2 | Molex 43045-0212, 2 × 1, vertical, 3 mm pitch | Matches 430450212/C293362. Generic single-row schematic graphics do not change the physical mapping. [Molex specifications](https://www.molex.com/en-us/products/part-detail/430450212). |
| R1, R4, R6–R12 | 0805 resistor | Matches each specified MPN, including the higher-power Panasonic R8. |
| R2 | 0805 resistor | Value/package plausible; exact purchasing part missing. |
| F1–F3 | 1206 fuse | Unverified without selected fuses. |
| H1–H4 | 3.2 mm M3 mounting holes | No supplier ID is needed for a bare PCB hole. |
| D6, R3, R5, V1, V2 | No footprint | Intentionally excluded from BOM and board. Do not add manufacturing footprints just to satisfy a missing-field check. |

All 16 distinct assigned footprint files exist in KiCad 10.0.4. Every numbered schematic pin has a matching footprint pad. This verifies library assignment and package compatibility, not placement, pad modifications already made in the PCB, solder-paste design, or JLCPCB assembly acceptance.

Connector wiring in the netlist is consistent with the schematic note: J1.1 is GLV+, J1.2 is GND, J1.3 is LED_RETURN, and J1.4 is BAT+. The RML load goes between J1.1 and J1.3. Both pins of Molex1 are HV+; both pins of Molex2 are the HV return before F2. LED2.1 is the VIL cathode/return and LED2.2 is the VIL anode through R2. The external VIL wiring is in the TS domain even though the voltage across the LED is low. Document these pinouts in the harness definition.

**GLV reverse-polarity protection is implemented with the correct Q5 orientation.**

The netlist connects `J1.4 BAT+ → F3 → Q5 drain (pin 3) → Q5 source (pin 2) → GLV+ / J1.1`. J1.2 is ground. Q5 is an AO3401A P-channel MOSFET. R11 = 10 kΩ connects its gate to ground. D2 has its cathode at the source/protected output and its anode at the gate; the nominal 8.2 V zener limits the negative gate-to-source voltage. The [AO3401A datasheet](https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf) specifies a ±12 V gate-to-source absolute maximum and a 30 V drain-to-source rating.

With the battery connected correctly, Q5's body diode initially supplies the output. R11 then makes the gate lower than the source, switching on the low-resistance MOSFET channel. With a reversed battery and an initially unpowered output, the body diode is reverse-biased and Q5 remains off. This is the usual [P-channel reverse-battery protection arrangement](https://www.ti.com/lit/an/slvae57/slvae57.pdf). F3 provides overcurrent protection; it is not the component that blocks reversed voltage.

An isolated DC operating-point simulation used the repository's AO3401A model, its nominal BZT52C8V2 model, R11, a 0.01 Ω fuse placeholder, and a 100 Ω output load:

| Applied input | Protected output | Q5 gate minus source |
|---|---:|---:|
| +12 V | 11.994 V | −8.039 V |
| −12 V | Approximately 0 V | Approximately 0 V |

These results support the nominal wiring only. D2 still needs an actual selected manufacturer part, and F3 needs a specified fuse. The test did not cover component tolerances, loaded heating, transients, a charged output during reversal, or an externally powered output. Supplying J1.1 directly bypasses this protection. This stage protects the GLV input through J1.4; it does not establish reverse-polarity protection on the HV input or prevent all backfeeding.

The latest KiCad ERC reports **one error and five warnings**. A disconnected bus entry at schematic coordinates **67.31, 45.72 mm** produces the dangling-wire error and two unconnected-entry warnings. Its UUID is `4b96d2ae-4b55-473f-9ee3-3792549a6120`; delete it if accidental or connect it as intended. The remaining warnings are unchanged: HV− and JFET_G name the same net; Q3 differs from the stock simulation symbol; U2 differs from the stock LMC555 symbol. The project disables footprint-filter and SPICE-model checks, so ERC is not a clean component-validation certificate. Q3's customized G/D/S mapping is intentional and correct; replacing it with the unmodified simulation symbol could undo that mapping.

The unmodified SPICE export is not a complete simulation proof: D2 exports as `D2 __D2` without usable nodes/model, D7 references an undefined `LED` model, and both supply sources are set to zero. The timer results above came from a separate, explicit test circuit in a temporary directory, not a claimed successful full-board simulation.

The remaining verification is specific: complete the fuse and lamp selections; define maximum charged TS voltage and GLV limits; establish the 50/60 V behavior over tolerances and temperature; measure duty and reset behavior; and demonstrate the synchronized lamp check. PCB layout, creepage/clearance, external lamp photometry, vehicle mounting, and hardware tests were outside this review. The existing 4 mm creepage rule would only correspond to the conformally coated column in the 300–600 V range; coating and actual layout were not verified. Use EV.7.5.7 when the PCB is reviewed.
