**The coated PCB's TS-to-GLV copper spacing passes the checked limits, but the complete VIL/RML design is not ready for release.**

Reviewed the saved schematic, PCB, project settings, and custom rules on November 7, 2026 using KiCad 10.0.4. Conformal coating is confirmed by the user. The maximum fully charged accumulator voltage remains unspecified, so this review uses the strictest PCB spacing row through 600 V. The rules basis is [Formula SAE 2027 V1.0, September 1, 2026](https://www.fsaeonline.com/cdsweb/gen/DownloadDocument.aspx?DocumentID=da79bcb4-0935-4f7b-83d7-0dbb8ce68d38). No schematic, PCB, project, or custom-rule files were changed during this review.

This report supersedes the current-status statements in the earlier `SCHEMATIC_REVIEW.md`: the dangling schematic bus entry is now gone, while the supplier corrections have been overwritten again. The electrical schematic is unchanged from the earlier circuit review.

| Check | Current result |
|---|---|
| Schematic ERC | 0 errors, 3 warnings |
| PCB DRC, with zones refilled in memory | 0 errors, 42 warnings |
| Unrouted connections | 0 |
| PCB/schematic parity | 0 reported mismatches |
| DRC after assigning all GLV nets in a temporary copy | Same 42 warnings; no isolation errors |
| Smallest projected TS-to-GLV copper gap | Approximately 6.02 mm at U1 |

**Conformal coating and isolation spacing**

EV.7.5.7 specifies **3 mm clearance and 4 mm creepage under conformal coating** in the 300–600 V row. Coating changes the creepage requirement; the clearance requirement remains 3 mm. The rule also covers traces on different layers. The uncoated creepage value in this row is 20 mm.

The independent geometry check included connected pads, tracks, vias, and filled zones on both copper layers, including their projection across layers. The closest opposing copper is at U1: its 7.62 mm row spacing minus two 0.8 mm pad radii gives **6.02 mm**. This occurs between pins 1/6 and 2/5; the unused input-side pin 3 was conservatively included as TS and has the same gap to pin 4. No closer TS-to-GLV copper pair was found. The 4 mm silkscreen strip is a visual boundary, not the measured conductor separation.

This supports the bare PCB geometry for a coated assembly through 600 V. Coating coverage, actual solder joints/leads, component insulation, and the assembled enclosure remain separate checks. Cover the intended isolation surfaces on both sides, including the U1 area; solder mask alone is not evidence of conformal coating. Retain assembly photographs and spacing evidence for EV.7.5.8.

The HIGH VOLT / LOW VOLT labels and boundary are present. The LOW VOLT label overlaps components and will be clipped, so improve its legibility before fabrication. Keep the split clear after assembly.

**Issues to resolve before release**

| Priority | Finding | Required action |
|---|---|---|
| High | No startup lamp-check control path appears in the schematic. | Implement or document an external parallel/OR path that operates both RMLs without defeating their normal voltage-controlled behavior. EV.6.3 requires synchronized continuous illumination for 2–6 seconds, starting within 1 second of GLVMS activation. |
| High | RML detection at 60 V is not guaranteed across D3/Q3/R6/U1 tolerances. VIL visibility and the below-50 V off state are also unproven. | Establish rising/falling thresholds, current and light output over component spread, temperature, and the actual supply range. EV.5.7.3 and EV.6.2.7 apply. |
| High | U2 remains NE555P in an output-feedback oscillator based on the CMOS LMC555 application. | Resolve the timer substitution and reset pull-down. Previous nominal simulation at 12 V gave 0.898 Hz and 53.12% output-high duty; EV.6.2.7 specifies 0.66–1.33 Hz and 50%. Verify the actual lamp waveform, not just the timing capacitor. |
| High | F1/F2/F3 remain generic 750 mA / 1206 symbols with no selected fuse. | Specify DC voltage, interrupt capability, current rating, and package. F1/F2 must suit the TS; F3 must suit the GLV. See EV.7.6. Do this before committing to the current footprints. |
| High, assembly-dependent | H1 is close to TS copper; Q3's tab, thermal copper, and nearby mounting region are live. | Define insulated or suitably isolated mounting hardware and enclosure construction. Do not assume grounded metal screws or standoffs are acceptable. See the measurements below. |
| Medium | Eleven GLV nets are absent from the GLV netclass, so the two custom isolation rules do not cover them. | Add these nets to GLV or use a complete domain-based rule. The present geometry passed an expanded check, but later routing could evade the current rules. |
| Open system dependency | External VIL and two RML lamp assemblies, harness, mounting, and load current are unspecified. | Identify the assemblies and verify optical performance, driver load, fuse margin, vehicle-side TS sensing, and installation. |

The detector concern is unchanged: an illustrative 60 V calculation using a 54 V D3 drop, 1.5 V optocoupler drop, and R6 at +1% leaves about 1.04 mA before Q3's drop. U1's specified maximum turn-on current is 1.6 mA. This is a missing-margin finding, not an exact switching-voltage prediction, because zener voltage varies with current. See the manufacturer sources and detailed analysis in `SCHEMATIC_REVIEW.md`.

The NE555 RESET issue is also unchanged: R8 is 1 kΩ, and the bipolar timer's specified input-current/threshold limits do not establish a guaranteed low reset level with that resistor alone. Selecting the intended CMOS timer requires coordinated symbol, model, sourcing, and footprint review.

**Mounting and thermal copper need particular attention**

- H1 is at approximately (122.5, 73.5) mm. The shortest distance from its 3.2 mm hole perimeter to TS copper is about **2.19 mm**, toward a trace on `Net-(Molex2-Pin_1)`. A metal washer or screw head extends beyond that perimeter. This measurement is not a copper-to-copper DRC error because the mounting hole has no net; it becomes relevant when conductive mounting hardware is installed.
- Q3's tab is connected to its drain. The large filled copper on both sides is also on `Net-(D3-A)`, its drain net. Copper approaches Q3's mounting-hole perimeter to about **0.25 mm**. Treat the tab, screw/washer if electrically connected, and exposed heat-spreading copper as TS conductors. Prevent a connection to chassis, GLV, or accessible metal.
- The thermal vias and copper spread heat, but do not establish a safe junction temperature. At the earlier illustrative 600 V / 5.69 mA operating point, Q3 dissipation is approximately 3.07 W. Validate the actual maximum voltage, current, cooling, coating process, and ambient temperature.
- Enclosure wiring and movable parts also need the barriers/spacing and restraint required by EV.7.5.5–.6. Passing PCB trace spacing does not sign off the enclosure.

**DRC coverage and remaining board cleanup**

`integrated_vil_rml.kicad_dru` uses `hasNetclass('TS')` against `hasNetclass('GLV')` for its 3 mm clearance / 4 mm creepage checks. TS nets are classified, but GLV currently includes only `GND`, `GLV+`, and `LED_RETURN`. These eleven GLV nets remain in Default:

`BAT+`, `Net-(D2-A)`, `Net-(D5-K)`, `Net-(D7-K)`, `Net-(Q4-D)`, `Net-(Q4-G)`, `Net-(Q5-D)`, `Net-(R10-Pad1)`, `Net-(U2-CV)`, `Net-(U2-Q)`, `Net-(U2-THR)`.

Assigning them in an isolated review copy and rerunning DRC produced no new violations. The independent projected-copper check also included all of them. Update the real project before future routing changes.

The 42 current board warnings comprise 19 silkscreen overlaps, 18 silkscreen/mask clipping warnings, four silkscreen/edge warnings, and one dangling track. The dangling segment is on B.Cu, `Net-(D5-K)`, near (193.5, 86.0) mm, length 2.1213 mm, UUID `69b96a8e-135d-4a35-8dad-982ae40b69ef`. Remove it if it is a leftover stub. These are distinct from missing electrical connections; the board has zero unrouted connections.

The three schematic warnings concern HV−/JFET_G naming and customized Q3/U2 symbols. Q3's intentional pin mapping should not be replaced blindly. Footprint-filter checks are disabled in the project, so zero DRC errors alone does not validate part selection.

The circuit still has GLV reverse-battery protection through F3/Q5/D2/R11, and PCB parity found no mismatch. Its prior nominal ±12 V check remains applicable to the unchanged circuit; it was not a transient or hardware qualification test. D2 still needs an exact purchasing part.

The selected Molex 430450212 header is listed at 600 V by [Molex](https://www.molex.com/en-us/products/part-detail/430450212); the complete mating connector and harness remain to be verified. VIL wiring remains in the TS domain even where the voltage across the LED is small. Confirm the VIL's external location and “High Voltage Present” label. RML lamp approvals/photometry and front/rear installation cannot be established from this board.

Purchasing metadata has reverted again: R6's LCSC URL points to C4382 instead of C137518; R8 links point to C17513 instead of its selected C441981. These are not new circuit changes, but must be corrected before generating purchasing outputs. R2 and D2 still have no exact sourced part.

**Evidence and limits**

Checks used `kicad-cli sch erc`, `pcb drc --schematic-parity --all-track-errors --refill-zones`, a temporary complete-netclass DRC, and KiCad copper-shape distance checks at approximately 0.001 mm search resolution. The saved copper geometry and the zone-refilled DRC both passed the reviewed isolation limits. No manufacturing outputs or design files were regenerated in the project.

Review artifacts are in `C:\Users\salty\AppData\Local\Temp\integrated-vil-rml-review`: `pcb-current-drc.json`, `schematic-current-erc.json`, `pcb-current.png`, and `pcb-isolation-audit/copper-spacing.json` / `classified-drc.json`.

Reviewed SHA-256: PCB `44ff838893afc4003c8aedd329bb81b16211d4fa542499db0ab5b119dff5d99b`; schematic `50ed825bb95b2fa379b68361af05f97ce7e81b123b2b59a18c37954f387a6480`.

Not checked physically: coating coverage/qualification, assembled clearances, insulation resistance, dielectric withstand, thermal behavior, lamp photometry, or vehicle installation. The remaining circuit and fuse findings prevent release even though the measured PCB isolation gap is adequate.
