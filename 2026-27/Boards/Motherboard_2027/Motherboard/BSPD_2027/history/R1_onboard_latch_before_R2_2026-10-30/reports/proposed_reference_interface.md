# Proposed Orion reference interface — approval pending

**This is a concrete option for a future revision. The primary 71-part design still leaves J1 pin 1 unused. No CAD or harness change has been made.** The proposal preserves the exact Molex connector and the existing functions of pins 2–6; it assigns pin 1 to a high-impedance measurement of the actual Orion 5 V supply at the DHAB sensor.

## Proposed connections

| Connection | Proposed function |
|---|---|
| J1.1 | Actual DHAB supply sense, `UC_RAW`; a sense wire, not a new sensor power source |
| J1.2–6 | Existing permit, current signal, brake signal, ground and GLV remain assigned as before |
| Added OPA2197 channel A | Unity buffer of protected `UC_RAW`, producing `UC_BUF` |
| Added OPA2197 channel B | Unity buffer of protected current signal, producing `I_BUF` |
| Existing current comparator | Compare buffered current directly against a fraction of `UC_BUF`, avoiding the existing half-signal offset penalty |
| Added LM2903B | Absolute window on the sensed supply; either comparator pulls `FAULT_OK` LOW |

Use genuine TI **OPA2197IDR**, SOIC-8, [LCSC C139363](https://www.lcsc.com/product-detail/Precision-Op-Amps_TI-OPA2197IDR_C139363.html), powered from protected VP and ground, with local 100 nF bypass. Standard pins are 1 OUTA, 2 −A, 3 +A, 4 ground, 5 +B, 6 −B, 7 OUTB, 8 VP. Its two followers have − inputs tied to their respective outputs. At normal VP, both 5 V and current inputs remain comfortably below the upper input crossover region. The [TI datasheet](https://www.ti.com/lit/ds/symlink/opa197.pdf) specifies 100 µV maximum room-temperature offset and 2.5 µV/°C maximum drift in that region; budget approximately 250 µV per buffer over the tentative −20…85°C board range. Room-temperature bias is pA-scale; the full-temperature SOIC limit is 5 nA, not pA.

As an initial protected-input topology, use the same 10 kΩ series / 1 MΩ pull-down network on both buffer inputs, with small RC filtering. Both acquire the known attenuation `a = 1M/(1M+10k) = 0.990099`; matching the networks makes it cancel in their ratio. Specify ratio accuracy and tracking, including temperature. Protection must limit fault current and avoid back-powering local rails when GLV is off. A low-leakage clamp is an accuracy choice, not proof of safe negative-input operation; qualify pin voltages, injection current and amplifier recovery before selecting it.

## Ratiometric current setting and fault window

For channel 2, nominally `Vsignal/Uc = (2.5 + 0.010 I)/5`. Because `I_BUF ≈ a Vsignal` and `UC_BUF ≈ a Uc`, set:

`Vcurrent_threshold = K × UC_BUF`, with `K = (2.5 + 0.010 Iset)/5`.

For an illustrative conservative **6.5 A** setting, `K = 0.513`. A 9.49 kΩ top / 10 kΩ bottom divider gives K ≈ 0.513084, or 6.54 A before hysteresis. Feed the current comparator from the buffered signal through 1 kΩ and retain approximately 4.7 MΩ feedback: its low source impedance reduces the previous roughly 1.28 A hysteresis to about 0.1 A. Select matched ratio networks or resistors with specified ratio tolerance and tracking, rather than assuming equal 100 ppm/°C coefficients track perfectly.

This is a calibration example, not an exact 5 kW setpoint. The existing illustrative sensor-error model has a roughly **45 mV raw-voltage gap** between worst healthy zero-current and worst 13.889 A at nominal 360 V. Direct comparison reduces the LM2901B offset contribution from about 11 mV to 5.5 mV raw, while the precision buffers and ratio tracking preserve more of that gap. Recalculate against the **actual maximum TS voltage** and qualified sensor/board errors; 6.5 A may still need adjustment. LEM's linearity limit is specified at 25°C, so extending it over temperature remains an assumption requiring manufacturer evidence or physical qualification.

Make current fault limits track the same supply:

* LOW fault: `I_BUF < 0.02 × UC_BUF`.
* HIGH fault: `I_BUF > 0.98 × UC_BUF`.

This allows the DHAB's specified nominal clamp fractions 0.04…0.96 while distinguishing ground and supply shorts near 0 and 1. Use 49.9 kΩ / 1.02 kΩ dividers for approximate fractions 0.02003 and 0.97997. At Uc = 5.25 V, the upper threshold tracks to about 5.145 V, allowing the specified upper clamp around 5.04 V instead of the primary design's fixed 4.695 V cutoff. Comparator offset, clamp tolerances, noise, buffer errors and wiring drops must fit the guard bands. Supply-short detection cannot be inferred merely from an ideal ratio calculation.

## Sense-wire supervision and loading

Add **LM2903BIDR**, SOIC-8, LCSC **C2869804**, powered from VP. Divide UC_BUF by two and compare it with local REF5-derived thresholds. A practical conservative starting window is approximately **4.856…5.153 V actual Uc**, accounting for the common 0.990099 attenuation: 10.8 kΩ / 10 kΩ gives the LOW threshold; 9.60 kΩ / 10 kΩ gives the HIGH threshold. Use accurate, specified tracking networks and recalculate all absolute monitor corners. The deliberately narrower window can detect rail excursions before leaving the sensor's 4.75…5.25 V operating range; it may reject an otherwise nominally allowed edge condition. Both outputs join FAULT_OK, so an open sense wire pulled LOW, ground short or GLV short prevents initial arming and trips an armed board.

Each external input sees about 1.01 MΩ: supply-sense loading is approximately **5 µA**, and idle current-signal loading about **2.5 µA**, plus input/clamp leakage. The primary current signal presently drives about 20 kΩ, roughly 125 µA at 2.5 V. The buffers supply the internal dividers: the reference buffer needs approximately **0.5 mA** for the proposed threshold/window networks; current-buffer DC load is much smaller. The amplifier's approximately 2 mA total typical quiescent current comes from VP, not Orion's sensed rail.

After authorization, complete component sourcing and new CAD/BOM/CPL checks, then qualify actual supply and ground drops, independently open/short every new and existing wire, test power-off/back-powering and late sensor startup, calibrate current over the declared temperature range, and measure SDC opening/reset behavior. The confirmed AiM sensor still needs hydraulic and environmental qualification. This proposal resolves the missing supply reference architecture; it does not certify the car.
