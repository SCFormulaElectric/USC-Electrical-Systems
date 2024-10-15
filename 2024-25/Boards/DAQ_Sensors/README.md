# DAQ Sensor Board Documentation

## High-level Functionality:

The DAQ sensor board takes in various sensor data, both analog and digital, and converts it to all digital signals that can be sent and processed by the main DAQ on the RPi.
This is done through various ADCs and multiplexers, which cycle through signals to be sent to the DAQ.

Sensors Needed:
 - 2 brake line sensors (PRIORITY): *MLH02KPSB06A*
 - 3 in-line temp sensors (PRIORITY): *GE-1935*
 - 2 wheel speed
 - 4 linear potentiometer sensors
 - 1 steering angle sensor (rotary potentiometer)
 - 1 GPS
 - 1 IMU/Gyro
 - ADC: *ADS122U04IPWR* (UART, 4 channel, 24-bit, 2.3V-5.5V)

## Signal i/p & o/p:

 - Pressure 1+: 5V to sensor 1
 - Pressure 1-: GND to sensor 1
 - Pressure1 out: analog output of pressure sensor 1
 - Pressure 2+: " "
 - Pressure 2-: " "
 - Pressure2 out: " "
 - Temp 1+: 5V to temp sensor 1
 - Temp 1-: GND to temp sensor 1
 - Temp 2+: " "
 - Temp 2-: " " 
 - Temp 3+: " "
 - Temp 3-: " "
 - MOSI: master out
 - MISO: master in
 - CS: chip select
 - SCLK: SPI clock
 - GPIOx: GPIO to ADC

## Version Control:
v0.1

 - Changed to one large ADC for all analog inputs -> SPI output to teensy
 - Added pressure sensors for brake lines and temp for cooling lines
