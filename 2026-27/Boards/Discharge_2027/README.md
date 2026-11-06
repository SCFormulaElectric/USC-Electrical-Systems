# Discharge 2027 — KiCad schematic starter

Open **Discharge_2027.kicad_pro** in KiCad 10. The schematic and its local libraries are self-contained. The PCB contains the discharge layout and the four TSMP footprints staged outside the board outline. Move and route the staged footprints before fabrication.

## Circuit and selected parts

HV+ → R1 → R2 → R3 → R4 → R5 → K1 NC contact → HV−.
Removing K1 coil power closes the discharge path. Applying 12 V opens it. The external shutdown/coil driver must remove power when discharge is required. This board does not implement that system logic or precharge. D1 provides coil transient suppression; select the external driver to tolerate its clamp voltage and verify relay release timing.

| References | Part | LCSC | Quantity |
|---|---|---|---:|
| R1–R5 | C&B/RESI PWWR0013F1K20K9, 1.2 kΩ, 13.5 W at 70 °C, ±1% | [C20417234](https://www.lcsc.com/product-detail/C20417234.html) | 5 |
| R6–R7 | Vishay AC07000001502JAC00, 15 kΩ, 7 W at 40 °C, ±5% | [C1366628](https://www.lcsc.com/product-detail/C1366628.html) | 2 |
| K1 | MiRelay HVR1B12-05, Form B NC, 12 V / 30 mA coil | [C52754156](https://www.lcsc.com/product-detail/C52754156.html) | 1 |
| J1–J5 | Molex 43045-0200, Micro-Fit 3.0, right angle 2-position PCB header | [C122431](https://www.lcsc.com/product-detail/C122431.html) | 5 |

The resistor bank is **6.0 kΩ**, not 7.5 kΩ. This gives timing margin for the 320 µF inverter. The five 1.2 kΩ parts are in series; do not change their arrangement to parallel.

## Connector pinout

| Header | Pin 1 | Pin 2 |
|---|---|---|
| J1 — HV+ | HV+ | HV+ |
| J2 — HV− | HV− | HV− |
| J3 — coil | +12 V coil supply | Coil return |
| J4 — remote TSMP+ jack | TSMP+ | TSMP+ |
| J5 — remote TSMP− jack | TSMP− | TSMP− |

J1 and J2 each use both positions for one potential. Neither is an HV+/HV− pair. The identical headers are mechanically interchangeable: prevent HV/LV or polarity cross-connection through harness routing, segregation, labeling and the final mechanical design. The selected 43045-0200 is specified at 600 V by Molex; use a matching contact/housing/wire combination rated for the application. Mating harness components are not included in the board BOM.

## Relay footprint and pin numbering

The manufacturer's drawing is explicitly a **TOP VIEW**, and does not print pin numbers. This project assigns local numbers consistently in both its symbol and footprint:

| Project pad | Function | X (mm) | Y (mm) |
|---|---|---:|---:|
| 1 | Coil + | 0 | 0 |
| 2 | Coil − | 0 | 7.62 |
| 3 | NC contact A | 35.56 | 0 |
| 4 | NC contact B | 35.56 | 10.16 |

Coil pins are at the left in top view. Contact A/B are non-polarized. Body nominal 40 × 15 × 13.5 mm; 0.8 mm leads; project drill 1.2 mm. The body rectangle is centered over the two contact rows with the left coil pair aligned as shown in the source drawing. Verify an actual relay and the supplied source drawing before freezing the footprint. Do not replace this symbol or footprint with a generic four-pin relay footprint based on numbering alone. The datasheet's 15 kV static coil-to-contact dielectric test is not a PCB clearance specification.

The RESI discharge footprint keeps the 55.88 mm lead pitch and 1.2 mm drills for its 0.8 mm leads. The nominal body is 49.5 mm long and 9.5 mm in diameter. It requires forming the axial leads. Verify purchased part dimensions and assembly lead forming with the assembler. The Molex footprint is copied from the KiCad 10 standard library with its pad geometry unchanged. The project-local STEP models for the resistor, relay and Molex header are visual approximations based on the nominal dimensions and footprint geometry. The modeled resistor standoff and lead bends represent one possible assembly. The TVS uses KiCad’s standard SMB package model. KiCad library license: https://www.kicad.org/libraries/license/ .

## TSMP branches

HV+ → R6 → J4 → remote TSMP+ jack. HV− → R7 → J5 → remote TSMP− jack. Connect J1 and J2 to the inverter supply rails and use the specified remote shrouded TSMP jacks. Keep the two resistor paths directly measurable for inspection.

R6 and R7 share a 35.56 mm horizontal footprint with 1.2 mm plated drills. The Vishay G204 G24071931502J7B000 from DigiKey or Mouser is an alternate for the same holes. The project’s approximate STEP model depicts the AC07. For 404 V and a worst-case TSMP short of 5.73 W across the pair, the AC07 has a 5.8 W continuous rating at 70 °C local ambient. Verify the mounted parts’ temperature near the discharge bank.

## Calculations and remaining design work

Design input: 404 V maximum, either 280 µF OR 320 µF on the vehicle side of the AIRs. These are alternative inverters, not two connected simultaneously. Include all other bus capacitance in the final total.

With R = 6000 Ω: initial current = 67.3 mA; initial total resistor power = 27.20 W; equal nominal sharing = 5.44 W and 80.8 V per resistor. Total rated power = 67.5 W at 70 °C ambient, subject to the manufacturer's temperature derating and the final mounting/cooling conditions.

For ideal RC discharge, t = R × C × ln(404/60):

| Capacitance | Nominal 404 V → 60 V | +20% C and +1% R |
|---|---:|---:|
| 280 µF | 3.204 s | 3.883 s |
| 320 µF | 3.662 s | 4.438 s |

The tolerance case is an explicit design assumption, not a verified inverter capacitance specification. Times exclude shutdown, relay/clamp and measurement delays, other connected capacitance, resistor temperature coefficient and component failures. At 320 µF, stored energy at 404 V is 26.11 J. If the bank is held across a live 404 V bus for 15 s it dissipates about 408 J total, 81.6 J per resistor nominally. Validate sustained fault heating as well as a normal discharge pulse. A shorted/bypassed resistor changes dissipation and must be considered in the system review.

Before release: confirm the exact 2027 rules for your event, actual capacitance/tolerance, shutdown behavior and required discharge/fault duration; complete thermal and voltage derating checks; choose board construction and enforce applicable HV-to-LV clearance/creepage, slots and connector placement; validate the external coil driver/clamp; route the PCB, add its outline/mounting/labels, then run DRC and ERC. No compliance certification is implied by this starter. The project has no custom spacing constraints yet; schematic connectivity verification is not an insulation or safety verification.

## Ordering and sources

Each schematic component contains Manufacturer, Manufacturer Part Number, LCSC, LCSC Part #, LCSC URL and Datasheet fields. `ordering/BOM_JLCPCB.csv` is a grouped JLC-format starter BOM; `ordering/Procurement.csv` adds quantities and clickable source links. The original nine board parts are through-hole; D1 is SMT. LCSC availability does not guarantee JLCPCB assembly availability. Confirm relay/resistor sourcing, wave/manual assembly, lead forming, height and cost in the live JLC quote. Do not submit the starter as a turnkey order. Gerbers and CPL are intentionally absent until layout is complete.

- Relay source and footprint drawing: https://www.reed-relay.com/product/high-voltage-reed-relays/hvr-high-voltage-reed-relays/reed-relay-hvr1b12-05/ . Original source PDF is in `docs/HVR1B12-05.pdf`.
- RESI PWWR family datasheet: https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5781/PWWR.pdf .
- Vishay TSMP datasheets: https://www.vishay.com/docs/28730/ac_ac-at_ac-ni.pdf and https://www.vishay.com/docs/21002/g200.pdf .
- Molex exact part specification: https://www.molex.com/en-us/products/part-detail/0430450200?display=pdf&download=true .
- JLC connector listing: https://jlcpcb.com/partdetail/Molex-430450200/C122431 .
- JLC assembly scope: https://jlcpcb.com/help/article/pcb-assembly-faqs .
- JLC ordering workflow: https://jlcpcb.com/help/article/how-do-i-place-a-pcba-order .

Part lookup and schematic creation: 2026-10-30. Prices, stock, availability and assembly support must be checked when quoting.

## Coil suppression — revision 0.2

D1 is **LRC SMBJ18CA**, LCSC/JLCPCB **C5383039**, an SMB / DO-214AA bidirectional TVS directly across COIL_12V and COIL_RETURN. Either physical orientation is electrically valid. Use the **CA bidirectional** version; a unidirectional A version would behave like a plain diode for flyback and slow release.

- JLCPCB part and ordering/specification source: https://jlcpcb.com/partdetail/LRC-SMBJ18CA/C5383039 . Listed for SMT, Economic and Standard assembly. Quote the mixed SMT/through-hole board; fixture/process charges may apply.
- Rated standoff is **18 V**, breakdown **20–22.1 V**, maximum pulse clamp **29.2 V at 20.6 A**, and pulse power **600 W for the specified 10/1000 µs waveform**. The actual clamp at the relay's roughly 30–33 mA turn-off current is lower than the high-current clamp rating; do not assume an exact 18 V clamp.
- This design assumes a **12 V GLV system with normal coil supply no greater than 16 V**, not a 24 V coil supply. D1 remains off in normal operation. It allows a higher reverse coil voltage at turn-off than a plain diode to promote faster NC-contact closure.
- Recommend an external low-side MOSFET/transistor rated **at least 60 V VDS/VCE**. Its stress is **V_supply + V_TVS + wiring overshoot**: approximately 45.2 V using a 16 V supply and the published 29.2 V pulse clamp. The driver remains external and is not selected here. Confirm the actual driver and its internal clamps; a parallel ordinary flyback diode or a lower-voltage internal clamp would bypass this fast-release behavior.
- Place D1 close to K1 coil pins with a small loop and no HV connection. D1 is coil suppression, not protection across the 404 V contact circuit. Verify both high-side shutdown interruption and low-side driver turn-off, worst-case voltage/temperature, driver peak voltage, TVS pulse energy/repetition and measured NC contact closure delay. Relay coil inductance is not published, so pulse energy and release time cannot be certified from available data alone. Include that delay in the total discharge budget.
- A TVS short would load the external coil supply/driver; a TVS open would remove suppression. Include both in system fault analysis and driver protection. Move and route the staged TSMP parts before any manufacturing release.

The drawing edits already saved in KiCad before this change are retained. D1 and its footprint are added without regenerating the existing schematic or PCB placement.
