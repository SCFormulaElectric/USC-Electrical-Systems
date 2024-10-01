# Relay Board Documentation

Note: updated_relay_draft is the current active schematic and PCB

## High-level Functionality:

The relay board take the various fault signals (BSPD, IMD, and BMS) and will both activate the shit down circuits (SDC1 & SDC2) and turn on the red LED in the event of a fault. In the event of no faults, the green LED will remain on. No blinking is required for the red LED since the old TSAL light, which are now using for this, has an embedded blinkning feature.

## Signal i/p & o/p:

Inputs:

 - 12 V: power
 - BSPD Fault: (active low fault)
 - IMD Fault: (active low fault)
 - BMS Fault: (active high fault)
 - Reset: ??

Outputs:

 - Green LED On: Send signal to green LED to turn on when no faults present
 - Red LED Flashing: Send signal to red LED to turn on in the event of a fault
 - SDC1: Shut down circuit signal 1
 - SDC2: Shut down circuit signal 2

## Version Control:
v1.0

 - Schematic updated to meet 2024-25 rules
 - Changed mosfet logic to match usage with TSAL lights
 - Updated PCB to fit new mosfets and include a ground plane

 v1.1
 - Removed unnecessary pullup resistor on BSPD signal
 - Removed unnecessary diodes on fault logic
