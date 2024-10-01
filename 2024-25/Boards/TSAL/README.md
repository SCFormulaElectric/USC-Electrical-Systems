# TSAL Documentation

## High-level Functionality:

TSAL = Tractive System Status Indicator

TSAL light turns on when the tractive system (high current line) is active.
The H11L1M octocoupler takes high voltage and transforms it into low voltage to be sent to 555 timer and light.
(more info needed)

## Signal i/p & o/p:

Inputs:

 - HV+: High voltage (+) signal
 - HV-: High voltage (-) signal
 - GLV+: 12 V power
 - GND

Outputs:

 - Light+: Output signal to the light

## Version Control:
v1.0

 - Added a NE555 timer at ~3 Hz to flash light
 - Removed second mosfet connected to light ground (only mosfet attached to 12 V power line now)
 - (more info needed)

