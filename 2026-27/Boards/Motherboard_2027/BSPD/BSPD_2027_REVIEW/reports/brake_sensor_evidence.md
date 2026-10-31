# Brake pressure sensor evidence from Google Drive

Reviewed 2026-10-05. Read-only investigation; no Google Drive content was modified.

## Finding

The connected USC Drive contains two conflicting historical brake-sensor specifications. The user subsequently confirmed that the installed sensor is **AiM X05SNP13520**; that current-hardware statement takes precedence over the conflicting historical image. The user also confirmed that the BSPD receives **LEM DHAB S/134 channel 2**, powered by the **Orion BMS 2 +5 V sensor supply**, with positive motoring current increasing the raw sensor voltage. The original BSPD connector and pin assignment must be retained; its interface has no sensor-supply measurement pin.

An approved pressure setting for the BSPD hard-brake threshold remains unknown. Treat brake-threshold resistor values as configurable until actual vehicle hard-brake calibration is supplied or measured. The historical 0-100 bar image must not be used to calibrate this confirmed 0-135 bar sensor.

## Source 1: brake/pedal documentation, 0-100 bar image

[Brake & Throttle Pedal Documentation and Rules](https://docs.google.com/document/d/1NKPcEko7eD3jknwXDXmA_BsPQE_4zGnkbYm3zHdsjBg/edit?usp=drivesdk), last modified 2024-10-10 UTC. The native document was read through the Drive connector and exported read-only to PDF to inspect the embedded sensor-specification image. The image appears on PDF page 5; ordinary text extraction omits its technical content.

The image specifies:

| Characteristic | Embedded specification |
|---|---|
| Supply | 8-16 V |
| Output | 0.5-4.5 V |
| Endpoints | 500 mV at 0 bar; 4500 mV at 100 bar |
| Nominal transfer function, derived | Vout = 0.5 V + 0.040 V/bar * pressure |
| Accuracy | Less than +/-0.5% FS, combined nonlinearity and hysteresis |
| Current consumption | Less than 10 mA |
| Temperature | -20 to 135 C |
| Sealing, thread, cable | IP66, M10, 400 mm |
| Connector | Four-pin circular diagram |
| Pin 1 | White, analog signal |
| Pin 2 | Black, ground |
| Pin 3 | Red, +Vb |
| Pin 4 | Not connected |

No manufacturer or part number is visible in the embedded image itself. It matches the technical table and connector drawing in the manufacturer-authored [AiM 0-100 bar M10 datasheet](https://support.aimshop.com/product-documentation/car-sensors/pdf/Pressure/100MData.pdf), which identifies sensor **X05PSA00100B10** and kit **X05PSA00100B10K**. That matching document identifies a four-pin Binder 719 male connector and specifies the connector view from the solder termination side. The model attribution is an inference from the matching specification image, not proof of a purchase or current installation.

## Source 2: BSPD log, different sensor link

[BSPD Truth Table and Testing Log](https://docs.google.com/spreadsheets/d/12bYt0Q9hgvJAWCvAaxwRDCmT8IjlrA6l6iJC9UEWg10/edit?usp=drivesdk), last modified 2025-01-07 UTC. Its first table contains a "Brake Pinout" hyperlink to the official [AiM 0-2000 PSI / 0-135 bar datasheet](https://www.aim-sportline.com/download/doc/eng/sensors/oldies/Datasheet_BrakePressure0-2000PSI_101_eng.pdf).

That linked manufacturer document identifies **X05SNP13520**. Page 10 (printed page 9) specifies 1-5 V output, 10-30 V supply, 4 mA consumption, 0-135 bar/0-2000 PSI measurement range and M10x1 thread. Pins are 1 white pressure signal, 2 black ground, 3 red supply, 4 not connected. Nominal slope derived using the stated 0-135 bar range is 4/135 = 0.02963 V/bar; do not treat its rounded bar range as a precision calibration.

This conflicts materially with Source 1: different full-scale pressure, offset, slope, supply range and maximum valid output. The user-confirmed X05SNP13520 matches Source 2. A 4.7 V upper fault window suitable for the 0.5-4.5 V model would reject valid high-pressure signals from the installed 1-5 V model. A 5 V sensor supply satisfies neither historical brake-sensor specification.

## Threshold evidence and limitations

The BSPD log has one test table with brake/current thresholds of **3 V**, fault boundaries **0.5/4.5 V**, and nominal voltage stimuli of 1/3.5 V. A later table uses **2 V** brake/current thresholds and 1/2.5 V stimuli. The log describes these as tunable potentiometer settings for the tests. It does not provide pressure measurements or establish either voltage as a hard-brake threshold for the current vehicle.

For comparison only:

| Voltage threshold | 0-100 bar, 0.5-4.5 V model | 0-135 bar, 1-5 V model |
|---|---:|---:|
| 2 V | 37.5 bar | 33.75 bar |
| 3 V | 62.5 bar | 67.5 bar |

These are derived conversions, not recommended calibration settings.

[2026 BSPD Test Procedure](https://docs.google.com/document/d/1xxFnBtNKMjqENtrPnmoNceGAgSmygA4ID2Jfk9o0c9s/edit?usp=drivesdk), last modified 2025-10-24 UTC, contains a plan to tune and test using the actual brake/current sensors and build an actual-sensor harness. It contains no recorded sensor model, pressure calibration or completed test result.

[Driver Interface.pptx](https://docs.google.com/presentation/d/1FQuqSWL5Uglf8r29I6ih7wTkYKI6QG5-/edit?usp=drivesdk), last modified 2026-06-18 UTC, states **estimated** lockup at 2 G with aero loading: front line pressure **4859 kPa = 48.59 bar**, rear **5377 kPa = 53.77 bar**, and one pressure sensor per master cylinder. Those estimates are not a BSPD calibration. In particular, reusing a 3 V threshold from either historical model would correspond to pressure above these estimated lockup values.

[Master Harness](https://docs.google.com/spreadsheets/d/1rUv01bypye8vxZWuGw8i3BbfvdVDmIRQmwz4ZnqKsr0/edit?usp=drivesdk), last modified 2026-09-25 UTC, records two brake signals PDL_BRK 1 / PDL_BRK 2 routed to VCU/BSPD and separate brake power lines. It gives no model, pressure transfer function or hard-brake setpoint.

## Additional scope checked

Searches covered brake, BSPD, BSE, pressure, sensor, AiM, X05 and ESF. The current ESF folder contains precharge resistor and ready-to-move-light references, with no brake sensor specification. The 2026 ESF datasheet folder has no brake sensor reference. ESF_Template_2026.xlsx is an unfilled template. The 2026-27 BSPD onboarding document repeats the need for actual-sensor calibration and gives only an illustrative pack-current example. Leads Meetings 26-27 mentions brake pressure data collection and brake bias tuning, without a sensor model or calibrated hard-brake threshold.

## Release evidence still needed

1. The user confirmed X05SNP13520. Record its installed label and verify the actual sensor supply meets 10-30 V.
2. Verify pressure/signal endpoints on the installed sensor, wiring and BSPD input; include signal loading and return offset.
3. Obtain an actual vehicle hard-brake pressure threshold and corresponding signal voltage. Include sensor tolerance and pressure/circuit loading effects.
4. Select and solder fixed precision threshold resistors for that evidence-backed setting, then document measured threshold and hysteresis.
5. Exercise sensor disconnection, short to ground, short to supply, power loss and the 2027 complete current-sensor test through actual shutdown-circuit interruption.

The original connector can be retained. Brake-sensor identity is now user-confirmed; the remaining brake uncertainty is hard-brake pressure calibration and measured electrical behavior.

## Orion BMS 2 supply evidence and current-input constraint

The official [Orion BMS 2 wiring manual](https://www.orionbms.com/manuals/pdf/orionbms2_wiring_manual.pdf), revision 1.1, printed pages 38-40, confirms the current-sensor +5 V output and dual raw analog signals. It gives no numeric tolerance, load/temperature regulation specification, or guaranteed fault-state voltage for that +5 V output. Page 39 recommends short sensor leads and advises against additional loads or taps on those wires. A BSPD connection therefore needs a demonstrated sufficiently high input impedance and controlled fault loading; its raw-signal sharing must not compromise the BMS sensor inputs.

The official [P0AC0 fault-code document](https://www.orionbms.com/faultcodes/DTC%20P0AC0%20-%20Current%20Sensor%20Fault.pdf), revision 1.1, identifies subcode 5 for the sensor +5 V source fault and says an unacceptable sensor-supply voltage causes a fault. It does not give numerical voltage boundaries or response time.

The official [Orion BMS 2 operational manual](https://www.orionbms.com/manuals/pdf/orionbms2_operational_manual.pdf), printed pages 59 and 62-63, describes degraded current-sensor failsafe operation. The BMS may continue protecting cells through voltage-based operation while current-dependent functions are disabled. Thus the mere existence of P0AC0 does not establish an independent shutdown on sensor supply failure. Do not rely on it to replace the BSPD input-fault detector. The guarantee and behavior must be established through a verified hardware protection path and actual vehicle tests.

The official [Orion BMS 2 specification sheet](https://www.orionbms.com/downloads/documents/orionbms2_specifications.pdf) likewise omits a sensor +5 V output tolerance. Its cell-voltage measurement accuracy is not the sensor-supply accuracy.

### Derived supply-error consequence

The official [LEM DHAB S/134 datasheet](https://www.lem.com/sites/default/files/products_datasheets/dhab_s_134.pdf), 10 October 2025 version 2, specifies channel 2 at 10 mV/A and 2.5 V zero-current offset for a 5 V supply. Both are ratiometric: Vout = (Uc/5) * (2.5 V + 0.010 V/A * I). Its valid supply range is 4.75-5.25 V. These are the sensor's permitted supply bounds, not a published Orion regulator tolerance.

For the parent design's 360 V nominal pack assumption, 5 kW corresponds to 13.8889 A:

| Condition | Raw channel 2 voltage, before sensor errors |
|---|---:|
| 5 kW, 5.00 V sensor supply | 2.63889 V |
| 5 kW, 4.75 V sensor supply | 2.50694 V |
| Zero current, 5.25 V sensor supply | 2.62500 V |

Therefore a fixed absolute threshold cannot distinguish zero current from the 5 kW condition across that entire supply range. This overlap exists before adding LEM offset, gain, linearity, ratiometricity and noise errors or board/reference errors. It is a consequence of the confirmed low-sensitivity channel and unavailable supply-sense wire, not something precision threshold resistors alone can correct.

For this exact interface, release requires a tighter, verified Orion supply bound together with the full error budget, or an evidence-backed hardware/interface adaptation. Nominal 5 V, a one-time room-temperature reading, and a BMS software fault code do not establish the bound over supply/load/temperature and faults.

### FSAE threshold and timing interpretation

Official 2027 V1 EV.8.7.2 requires shutdown for simultaneous hard braking and current equivalent to 5 kW at nominal voltage lasting more than 0.5 s. It does not expressly forbid trips somewhat below 5 kW or before 0.5 s. A conservative threshold and a timer whose worst-case total response remains below 500 ms are reasonable engineering interpretations of the one-sided required shutdown behavior, provided ordinary braking with low/zero power remains usable and demonstrated. These statements are interpretations, not a published SAE clarification authorizing arbitrary lower settings. No current official clarification explicitly defining permitted undershoot or an exact no-trip boundary was found.

The 5 kW value must remain the physical verification boundary. Document any deliberate detection margin and measured trip current rather than presenting an arbitrary voltage setting as an exact 5 kW threshold. Input open/short faults bypass the simultaneous-condition timing path.
