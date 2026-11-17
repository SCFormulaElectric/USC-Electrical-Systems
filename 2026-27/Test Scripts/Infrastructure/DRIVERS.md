# Instrument APIs and command references

Public imports: `from backend import EDU34450A, EDU36311A, instrument`.
Normally tests request dmm or glv_supply fixtures and need no driver imports.
For optional editor completion, annotate a parameter: `dmm: EDU34450A`.
No constructor opens a manager or enables an output; constructors query identity
on the supplied session. Shared connections always use pyvisa-py (@py).

## EDU34450A DMM: dmm fixture

Configuration: instruments.dmm with address, identity='EDU34450A', timeout_ms.

| Method | Result / behavior |
|---|---|
| identify() | Identity string |
| read_voltage_v() | Finite DC voltage in volts; autorange |
| query(command) | Existing raw-query compatibility escape hatch |

MEAS:VOLT:DC? selects the voltage function, autoranges, triggers and returns a
reading. It changes meter measurement configuration, not a source output. Physical
leads must already be in the correct terminals across the intended measurement
points; code cannot detect misplaced probes. No current-mode method is provided.
Measurement values reject non-finite/overload replies and check SYST:ERR?.

Command basis: Keysight EDU34450A Programming Guide, MEASure? example (page 92 in
the current indexed edition):
https://www.keysight.com/bh/en/assets/9921-01387/programming-guides/EDU34450A-Digital-Multimeter-Programming-Guide.pdf

## EDU36311A supply: glv_supply fixture

Configuration is instruments.glv_supply. Required fields:

| Field | Meaning |
|---|---|
| address, identity, timeout_ms | Connection; identity must match the actual EDU36311A |
| channel | 1, 2 or 3; channel 1 is 6 V/5 A, channels 2/3 are 30 V/1 A |
| reviewed | true only after actual board/fixture limit review |
| voltage_min_v, voltage_max_v | Approved test range; zero may always be programmed |
| current_limit_a | Positive approved current limit within channel rating |
| ovp_v | Reviewed OVP level, above the test range and within instrument capability |

The template supplies a commented example; its zero placeholders must be replaced.
Do not copy another board's current/OVP limits. Nothing infers those from an IP address.

| Method | Behavior |
|---|---|
| set_voltage_v(value) | Validate/program volts; never implicitly enables |
| output_on() | Recheck setpoint/protection and explicitly enable selected channel |
| output_off() | Remove OFF delay, attempt OFF even if delay change failed, check state |
| read_voltage_v() | Measured output volts |
| read_current_a() | Measured average output amps, not inrush/peak current |
| wait_for_voltage_v(target_v, tolerance_v, timeout_s) | Bounded measured-voltage wait |

The fixture validates settings before connection, then registers output_off before
configure. Configure attempts OFF, removes output delays, sets zero volts/current
limit/OVP, enables OCP with zero programmed OCP delay, and checks readbacks. It never
enables output. Test failure/configuration failure attempts OFF before closing the
instrument, then closes the manager. Teardown errors remain visible.

No *RST, automatic protection clear, guessed alternate commands, or enable retries.
Use exclusive bench ownership; front-panel or other-controller changes are not a
supported way to share the instrument during a test. Settings are rechecked before
enable but this is not a hardware interlock. These drivers control a selected channel,
not arbitrary synchronized supplies, Chroma HV sources, scopes, or generators.

Commands are channel-qualified VOLT/CURR/VOLT:PROT, CURR:PROT:STAT,
CURR:PROT:DEL, OUTP, OUTP:DEL:RISE/FALL, MEAS:VOLT?/MEAS:CURR? and SYST:ERR?.
Basis: Keysight EDU36311A Programming Guide, CURRent, VOLTage, OUTPut and MEASure
subsystems. Especially note that OUTP? reports configured state when delays apply:
https://www.keysight.com/us/en/assets/9921-01393/programming-guides/EDU36311A-DC-Power-Supply-Programming-Guide.pdf

## Preflight and verification limits

```sh
python Infrastructure/preflight.py Suites/My_Board --instrument dmm
python Infrastructure/preflight.py Suites/My_Board --instrument dmm --connect
```

Default preflight is offline configuration validation. --connect only queries *IDN?
and closes connections; it does not exercise measurement/protection commands, move
leads, certify wiring, or turn off an already energized bench. Omit --instrument to
check every configured generic instrument. Legacy VIL/RML config uses its own preflight.

Command syntax was checked against these manuals; fake-instrument tests verify
software behavior. Real firmware, readback resolution, trigger/protection behavior,
lead placement, stored energy and network-loss shutdown need local commissioning.
An OFF query never proves discharge; independent fixture protection remains required.
