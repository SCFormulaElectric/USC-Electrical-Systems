# Charging Documentation

## High-level Functionality:

Top box (of the schematic) includes all components internal to the car. Bottom box includes all components that will be mounted on the charging cart.

## Signal i/p & o/p:

Inputs:

 - (please add)

Outputs:

 - (please add)

## Version Control:
v1.0

 - Charger updated to include changed pinouts from new boards
 - Rectifier changed to only push 2 A of current (no longer needed to power cooling)
 - Accumulator elements updated from new schematic and connections are remade

## Relevant Rules

Rules: 
EV.8.2.1 The Charger must be galvanically isolated (AC) input to (DC) output.

EV.8.2.2 If the Charger housing is conductive it must be connected to the earth ground of the AC input.

EV.8.2.3 All connections of the Charger(s) must be isolated and covered.

EV.8.2.4 The Charger connector(s) must incorporate a feature to let the connector become live only when correctly connected to the Accumulator.

EV.8.2.7 The Charger must include a Charger Shutdown Button which is:
a. A push-pull or push-rotate emergency stop switch

EV.8.3.1 The Charging Shutdown Circuit consists of:
a. Charger Shutdown Button EV.8.2.7
b. Battery Management System (BMS) EV.7.3
c. Insulation Monitoring Device (IMD) EV.7.6

EV.8.3.2 The BMS and IMD parts of the Charging Shutdown Circuit must:
a. Be designed as Normally Open contacts
b. Have completely independent circuits to Open the Charging Shutdown Circuit.
Design of the respective circuits must make sure that a failure cannot result in electrical
power being fed back into the Charging Shutdown Circuit.

EV.8.4 Charging Shutdown Circuit Operation

EV.8.4.1 When Charging, the BMS and IMD must:
a. Monitor the Accumulator
b. Open the Charging Shutdown Circuit if a fault is detected.

EV.8.4.2 When the Charging Shutdown Circuit Opens:
a. All current flow to the Accumulator must stop immediately
b. The voltage in the Tractive System must be Low Voltage T.9.1.2 in five seconds or less
c. The Charger must be turned off
d. The Charger must stay disabled until manually reset
