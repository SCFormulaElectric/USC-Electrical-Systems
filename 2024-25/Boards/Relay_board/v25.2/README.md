# Relay Board Documentation

Note: updated_relay_draft is the current active schematic and PCB

## High-level Functionality:

The relay board take the various fault signals (BSPD, IMD, and BMS) and will both activate the shit down circuits (SDC1 & SDC2) and turn on the red LED in a blinking fashion in the event of a fault. In the event of no faults, the green LED will remain on. 

## Signal i/p & o/p:

Inputs:

 - BAT: 12V Battery power
 - BSPD Fault: (active low fault, push pull)
 - IMD Fault: (active low fault, open collector w/ pull-down resistor 2.2k)
 - BMS Fault: (active high fault, open drain w/ pull-up resistor)
 - Precharge: software fault signal that comes from the PIC12 on the precharge board
 - SDC1: Shut down circuit input signal
 - SDC2: Shutdown circuit output signal
 - Reset: Used to clear faults in BSPD, IMD, BMS, Precharge

Outputs:

 - Green LED On: Power the green LED when no faults present
 - Red LED Flashing: power red LED in blinking fashion to turn on in the event of a fault
 - SDC2: Shut down circuit signal 2, no faults = 12V (high), fault = floating

## Version Control:
v25.0

 - Schematic updated to meet 2024-25 rules
 - Changed mosfet logic to match usage with TSAL lights
 - Updated PCB to fit new mosfets and include a ground plane

v25.1
 - Removed unnecessary pullup resistor on BSPD signal
 - Removed unnecessary diodes on fault logic

v25.2
 - Corrected the pull-up pull-down swap on BMS / IMD signals
 - Swapped MOSFETs to increase the max Vgs from +/- 8V to +/- 12V
 - Added voltage regulator to prevent MOSFETs from being exposed to >12V
 - Added PIC12 to do fault logic and blinking of red LED
 - Sized up the current ratings of the relays from 2A to 5A (Inrush current on a single isolation relay is 4A)


