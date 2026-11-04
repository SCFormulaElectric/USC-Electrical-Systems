# DDAQ placement groups

Each KiCad group is one functional block: the IC/connector and the parts directly connected to it. Click a group to select it, drag to move it as a block, double-click to edit parts inside, right-click > Grouping > Ungroup to break it up.

| Group | Parts |
|---|---|
| J3 AMPSEAL 35 harness connector | J3 |
| Input protection: fuse, TVS, reverse-polarity FET (Q2) | D6, D9, D20, F1, Q2, R3, R19 |
| 12 V buck-boost LM5175 (U11) + power stage Q3-Q6, L8, R107 | C116, C117, C118, C119, C120, C121, C122, C123, C124, C125, C126, C127, C128, C129, C130, C131, C132, C133, C134, D21, D22, L8, Q3, Q4, Q5, Q6, R96, R97, R98, R99, R100, R101, R102, R103, R104, R105, R106, R107, U11 |
| 7 V buck LMR33630 (U9) + L7 | C95, C96, C97, C99, C100, C101, C102, C103, C104, C105, C106, C107, C111, L7, R88, R89, U9 |
| 5 V buck TPS563300 (U2) + inductor U6 | C3, C10, C55, C58, C67, R21, R34, R59, R60, U2, U6 |
| 3.3 V LDO AMS1117 (U4) | C68, C69, D8, R61, U4 |
| 5 V precision reference TPS7A4700 (U10) | C110, C112, C113, C114, U10 |
| Sensor supply +5V_EXC_L (U12) | C136, C144, D33, R110, U12 |
| Sensor supply +5V_EXC_R (U13) | C137, C145, D34, R111, U13 |
| Sensor supply +5V_EXC_C (U14) | C138, C146, D35, R112, U14 |
| Sensor supply +5V_WS_L (U16) | C140, C148, D36, R114, U16 |
| Sensor supply +5V_WS_R (U17) | C141, C149, D37, R115, U17 |
| Sensor supply +5V_WS_C (U18) | C142, C150, D38, R116, U18 |
| 12 V sensor outputs OUT1/OUT2 (PTC fuses + TVS) | D40, D41, F3, F4 |
| IZZE supply (F7, D23, TVS) | D23, D39, F7 |
| ADC ADS8688 (U5) core: decoupling, reference, EXC monitor | C11, C81, C82, C83, C88, C89, C90, C91, C92, C93, FB1, R82, R83, R84, U5 |
| Analog front end AI0-AI7: pull-down, series R, filter C, clamps | C73, C74, C75, C76, C77, C78, C79, C80, D11, D12, D13, D14, R65, R66, R67, R68, R69, R70, R71, R72, R73, R74, R75, R76, R77, R78, R79, R80 |
| Spare analog AI8/AI9 to MCU (PC5/PE8) | C158, C159, D28, D29, R126, R127, R128, R129 |
| Frequency inputs FREQ1/FREQ2 (U20) | C152, C153, C156, D24, D25, R118, R119, R120, R121, U20 |
| Frequency inputs FREQ3/FREQ4 (U21) | C154, C155, C157, D26, D27, R122, R123, R124, R125, U21 |
| CAN1 transceiver (U3) + ESD + split termination JP1 | C14, C15, C16, D1, JP1, R1, R4, R5, U3 |
| CAN2 transceiver (U8) + choke L6 + ESD + split termination JP2 | C19, C20, C94, D19, JP2, L6, R14, R15, R85, U8 |
| MCU STM32G474 (U1) + decoupling, BOOT0, monitors | C1, C2, C4, C5, C6, C7, C8, C9, C85, C86, C87, C98, C108, C109, C115, C135, R81, R86, R87, R90, R91, R92, R93, R94, R95, R108, R109, U1 |
| 16 MHz crystal (X1) | C12, C13, X1 |
| Status LEDs CAN/FAULT/STAT | D30, D31, D32, R130, R131, R132 |
| Node-ID jumpers JP3/JP4 | JP3, JP4, R135, R136 |
| SWD header (J5) | J5 |
| USB-C (USBC1) + ESD (U22) | R12, R13, U22, USBC1 |
| microSD (J1) + power switch Q7 | C17, C18, C165, J1, Q7, R6, R7, R8, R9, R10, R11, R137, R138 |
| IMU ISM330DHCX (U23) | C160, C161, C162, R133, U23 |
| Barometer BMP581 (U24) | C163, C164, R134, U24 |
