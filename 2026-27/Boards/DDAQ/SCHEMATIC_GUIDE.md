# DDAQ schematic guide

A description of every component and sub-circuit on `DDAQ/DDAQ.kicad_sch`, to help reorganise the sheet for
readability. Generated from the schematic netlist on 2026-11-06 (commit after 8d21844), 286 parts. The blocks match
the PCB placement groups (`PLACEMENT_GROUPS.md`), so schematic and board use the same structure.

"Sheet (x, y)" = where the part's symbol currently sits on the E-size sheet, in mm, to help you find it.
Net names: local labels are shown without the leading `/`.

---

## 0. Big picture

```
            VBAT (J3.27)
               |
   F1 3A -> D20 TVS -> Q2 reverse-polarity  ==> VIN_PROT
               |                                   |
               |                  +----------------+-----------------+
               |                  |                                  |
        LM5175 buck-boost (U11)                              LMR33630 buck (U9)
        +12V_SNS (12.0 V)                                     +7V (7.06 V)
          |  -> F3/F4 -> +12V_OUT1/2 (pitot, pod)              |  -> F7/D23 -> IZZE_PWR
          |                                                    |
          |                       +----------------------------+------------------+
          |                       |                            |                  |
          |              TPS563300 buck (U2)          TPS7A4700 LDO (U10)   6x NCV8184 trackers
          |              +5V (4.93 V)                 +5V_REF (5.00 V)      (U12-U14, U16-U18)
          |                |   CAN VCC, monitors        |  ADC AVDD (FB1)     +5V_EXC_L/R/C
          |                |                            |  tracker reference  +5V_WS_L/R/C -> J3
          |          D42 --+--> LDO_IN <-- D43 -- USB VBUS
          |                       |
          |               TLV1117LV33 (U4) +3.3V: MCU, ADC DVDD, sensors, SD, CAN VIO, LEDs
```

Signal side: the MCU (STM32G474, U1) talks SPI1 to the 16-bit ADC (U5), SPI2 to the microSD card (J1), SPI3 to the
IMU (U23) and barometer (U24), FDCAN1/FDCAN2 through two transceivers (U3, U8), USB to the USB-C port, and timer
capture to four Schmitt-buffered frequency inputs. Everything off-board goes through one 35-pin AMPSEAL (J3).

Suggested sheet split if you go hierarchical (one A4/A3 sheet each):
1. Power input + 12 V buck-boost  2. 7 V / 5 V / 3.3 V / 5 V reference  3. Sensor supplies + 12 V/IZZE outputs
4. Connector J3 + all connector-side protection  5. Analog front end + ADC  6. Frequency inputs + spare analog
7. MCU (+ crystal, SWD, LEDs, node ID, rail monitors)  8. CAN1 + CAN2  9. USB + microSD  10. IMU + barometer.
If you stay on one sheet, the same order left-to-right / top-to-bottom reads as "power in -> rails -> MCU -> I/O".

---

## 1. Harness connector J3 (TE AMPSEAL 35, 776163-1) — sheet (940, 229)

The only off-board connector. Right-angle, panel-mount through the enclosure wall (see `LAYOUT_NOTES.md`).

| Pin | Net | Pin | Net | Pin | Net |
|---|---|---|---|---|---|
| 1 | +5V_EXC_L | 13 | AI2 | 24 | +12V_OUT1 |
| 2 | AI0 | 14 | AI3 | 25 | +12V_OUT2 |
| 3 | +5V_WS_L | 15 | AI4 | 26 | GND |
| 4 | FREQ1_IN | 16 | AI5 | 27 | VBAT (battery in) |
| 5 | GND | 17 | AI6 | 28 | GND |
| 6 | +5V_EXC_R | 18 | AI7 | 29, 31 | CAN1H (pass-through) |
| 7 | AI1 | 19 | AI8 | 30, 32 | CAN1L (pass-through) |
| 8 | +5V_WS_R | 20 | AI9 | 33 | CAN2H_BUS |
| 9 | FREQ2_IN | 21 | +5V_WS_C | 34 | CAN2L_BUS |
| 10 | IZZE_PWR | 22 | FREQ3_IN | 35 | not connected |
| 11 | GND | 23 | FREQ4_IN | | |
| 12 | +5V_EXC_C | | | | |

Readability tip: draw J3 once with net labels on every pin, and keep all connector-side protection (TVS D33-D41,
CAN ESD D1/D19) visually next to it or next to the block that owns it - not scattered.

---

## 2. Input protection — sheet around (50-120, 505-790)

| Ref | Value | Role |
|---|---|---|
| F1 | 3 A fast, Littelfuse 0451003 (Nano2) | Main fuse, VBAT -> VBAT_FUSED. Protects the car's LV harness. |
| D20 | SMBJ18CA | Bidirectional TVS on VBAT_FUSED: clamps load-dump / inductive spikes. |
| Q2 | AO3401A P-FET | Reverse-polarity protection: drain on VBAT_FUSED, source on VIN_PROT. Conducts (low loss) only with correct polarity. |
| R3 | 13 k | Pulls Q2's gate to GND so it turns on. |
| D9 | BZT52C10S 10 V Zener | Gate-source clamp for Q2 (gate max ±12 V). |
| D6 + R19 | red LED + 13 k | "Power OK" indicator on VIN_PROT. |

Output: **VIN_PROT** (protected battery, ~7-18 V) feeds the buck-boost, the 7 V buck and the VIN monitor.

---

## 3. 12 V buck-boost (LM5175, U11) — controller (279, 457), passives (50-280, 597/643)

Makes a steady **+12V_SNS** from VIN_PROT whether the battery is above or below 12 V (4-switch H-bridge).

| Ref | Value | Role |
|---|---|---|
| U11 | LM5175PWPR | Buck-boost controller (~300 kHz, CCM + hiccup). |
| Q3 | AO4264E | Buck leg high side: VIN_PROT -> SW1 (gate HD1). |
| Q4 | AO4264E | Buck leg low side: SW1 -> BB_RS (gate LD1). |
| Q5 | AO4264E | Boost leg high side / output switch: SW2 -> +12V_SNS (gate HD2). |
| Q6 | AO4264E | Boost leg low side: SW2 -> BB_RS (gate LD2). |
| L8 | 10 µH (AGA1265100) | Power inductor between SW1 and SW2. |
| R107 | 33 mΩ 2512 | Current-sense resistor in both low-side sources (BB_RS -> GND). |
| R104, R105, C121 | 100 Ω, 100 Ω, 47 pF | CS/CSG filter for the sense voltage. |
| C124, C125 + D21, D22 | 100 nF + B5819W | Bootstrap supplies for the two high-side gate drivers. |
| C122 | 4.7 µF | VCC (7.5 V gate-drive) regulator cap. |
| R98 + C116 | 10 Ω + 100 nF | RC filter for the controller's VIN pin. |
| R96 / R97 | 249 k / 53.6 k | EN/UVLO divider: turns on at 6.94 V (0.87 V hysteresis). |
| R99 | 93.1 k | MODE: CCM with hiccup current-limit protection. |
| R100 | 84.5 k | RT: switching frequency ~300 kHz. |
| C117 | 100 pF | Slope compensation. |
| C118 | 100 nF | Soft-start (~16 ms). |
| R101 + C119 + C120 | 5.1 k + 27 nF + 100 pF | Type-II loop compensation (checked against datasheet, see `CLOUD_HANDOFF.md`). |
| R102 / R103 | 280 k / 20 k | Feedback divider: 0.8 V × 15 = 12.0 V. |
| C126-C129 | 4× 10 µF 50 V 1206 | Input caps at Q3's drain (hot loop). |
| C130-C133 + C134 | 4× 10 µF 1206 + 100 µF 35 V electrolytic | Output caps at Q5's drain. |
| C123 | 1 µF | BIAS pin decoupling (BIAS = VOUT). |
| R106 | 10 k | PGOOD pull-up -> **PG_12V_PE7** (MCU). |

Readability tip: draw the H-bridge as a picture (Q3/Q4 on the left, L8 in the middle, Q5/Q6 on the right, R107
under the two low-side FETs), controller below with its passives grouped by pin function.

---

## 4. 7 V buck (LMR33630, U9) — sheet (89, 457) and (50-280, 505)

| Ref | Value | Role |
|---|---|---|
| U9 | LMR33630ADDA | 3 A synchronous buck, VIN_PROT -> **+7V**. EN tied to VIN (always on). |
| L7 | 12 µH SRR1208 | Power inductor (SW -> +7V). |
| C95 | 100 µF 35 V electrolytic | Input bulk (also serves the buck-boost input). |
| C96, C97, C101, C102 | 10 µF 1206 | Input ceramics. |
| C103 | 100 nF | High-frequency input decoupling. |
| C99 | 1 µF | VCC (internal LDO) cap. |
| C100 | 100 nF | Bootstrap cap (BOOT-SW). |
| R88 / R89 | 100 k / 16.5 k | Feedback: 1.0 V × (1 + 100/16.5) = 7.06 V. |
| C104-C107 | 4× 22 µF 1210 | Output caps. |
| C111 | 10 µF | Extra output cap on +7V. |

+7V feeds: the 5 V buck, the 5 V reference, all six sensor-supply trackers, IZZE power, the 7 V monitor.

---

## 5. 5 V buck (TPS563300, U2) — sheet (103, 720)

| Ref | Value | Role |
|---|---|---|
| U2 | TPS563300 | 3 A synchronous buck, +7V -> **+5V**. |
| U6 | 12 µH SRR1208 | Power inductor (ref "U6" because of its library symbol; it is an inductor). |
| R60 / R59 | 10 k / 10 k | EN divider from +7V (EN = 3.5 V -> enabled). |
| C3 | 100 nF | Bootstrap (BST-SW). |
| C10, C58 | 10 µF, 100 nF | Input caps. |
| R34 / R21 | 47 k / 9.1 k | Feedback: 0.8 V × (1 + 47/9.1) = 4.93 V. |
| C55, C67 | 2× 10 µF | Output caps. |
| C68 | 100 nF | Output decoupling. |

+5V feeds: both CAN transceivers' VCC, the 3.3 V LDO (through D42), the 5 V monitor.
Readability tip: rename U6 to L-something when you tidy (needs a matching PCB update; harmless).

---

## 6. 3.3 V LDO + USB/battery diode-OR (U4) — sheet (157, 767) and (400-560, 760-800)

| Ref | Value | Role |
|---|---|---|
| D42 | B5819W Schottky | Battery path: +5V -> LDO_IN. |
| D43 | B5819W Schottky | USB path: VBUS -> LDO_IN. Together a diode-OR: either source powers the 3.3 V side, neither back-feeds the other. |
| C167 | 10 µF | LDO input cap (after the diodes). |
| U4 | TLV1117LV33DCYR (C15578) | 3.3 V LDO, 90 mV dropout @ 200 mA. **VIN max 5.5 V** - only ever fed from LDO_IN. |
| C69 | 22 µF | LDO output cap. |
| D8 + R61 | yellow LED + 3 k | "3.3 V present" indicator. |
| PWR_FLAG on LDO_IN | - | ERC: tells KiCad the diode-fed net is driven. |

Note: the +3.3V symbol at U4's output is a `power:+5V` library symbol whose value was changed to "+3.3V". It works
(KiCad names the net from the value) but replace it with a real `power:+3.3V` symbol when tidying.
U4's symbol is still the library's AMS1117-3.3 graphic (same pinout); fine, or swap for a generic LDO symbol.

---

## 7. 5 V precision reference (TPS7A4700, U10) — sheet (178, 457), passives (50-105, 551)

| Ref | Value | Role |
|---|---|---|
| U10 | TPS7A4700RGWR | Ultra-low-noise LDO, +7V -> **+5V_REF**. Output set by the ANY-OUT pins: 0P4V and 3P2V grounded -> 1.4 + 0.4 + 3.2 = 5.00 V. EN tied to +7V. |
| C110 | 10 µF | Input cap. |
| C112 | 1 µF | NR (noise-reduction) cap. |
| C113, C114 | 2× 22 µF 1210 | Output caps. |

+5V_REF is the accuracy anchor: ADC analog supply (through FB1), reference input of all six trackers, EXC_MON on the
ADC, 5VREF monitor on the MCU.

---

## 8. Sensor supplies: 6 × NCV8184 tracking LDOs — sheet (559-740, 450-546), TVS at (978-1041, 335)

Each tracker copies +5V_REF onto its own protected output (accuracy + short-to-ground / short-to-battery /
reverse protection + fault isolation per harness branch). Identical circuits:

| Output | Tracker | In cap (+7V) | Output R + C (stability "ESR") | Connector TVS | J3 pin |
|---|---|---|---|---|---|
| +5V_EXC_L | U12 | C136 100 nF | R110 1 Ω + C144 1 µF (node TRK1_C) | D33 SMF15A | 1 |
| +5V_EXC_R | U13 | C137 | R111 + C145 (TRK2_C) | D34 | 6 |
| +5V_EXC_C | U14 | C138 | R112 + C146 (TRK3_C) | D35 | 12 |
| +5V_WS_L | U16 | C140 | R114 + C148 (TRK5_C) | D36 | 3 |
| +5V_WS_R | U17 | C141 | R115 + C149 (TRK6_C) | D37 | 8 |
| +5V_WS_C | U18 | C142 | R116 + C150 (TRK7_C) | D38 | 21 |

Pins per NCV8184: 1 VOUT, 4 ADJ (tied to VOUT = unity tracking), 5 VREF/ENABLE (+5V_REF), 8 VIN (+7V), 2/3/6/7 GND.
The 1 Ω in series with the 1 µF ceramic gives the regulator the output-capacitor ESR it needs for loop stability.
R110's value text "0603WAF100KT5E" is the UniRoyal part number for **1 Ω**, not 100 k.
EXC = excitation for analog sensors; WS = supply for wheel-speed / frequency sensors. L/R/C = harness branch.

---

## 9. 12 V sensor outputs and IZZE supply

| Ref | Value | Role |
|---|---|---|
| F3 | 0.5 A PTC | +12V_SNS -> **+12V_OUT1** (pitot), J3.24. |
| F4 | 0.5 A PTC | +12V_SNS -> **+12V_OUT2** (pod / spare), J3.25. |
| D40, D41 | SMF15A | TVS on the two 12 V outputs at the connector. |
| F7 | 0.1 A PTC | +7V -> IZZE_F. |
| D23 | SS14 Schottky | IZZE_F -> **IZZE_PWR** (blocks back-feed from the sensor). J3.10. |
| D39 | SMF15A | TVS on IZZE_PWR. |

---

## 10. ADC (ADS8688, U5) core — sheet (483, 221), passives (349-560, 227-267)

16-bit, 8-channel SAR ADC with programmable input ranges, on SPI1.

| Ref | Value | Role |
|---|---|---|
| U5 | ADS8688IDBTR | ADC. REFSEL# = GND -> internal 4.096 V reference. DAISY = GND (single device). |
| FB1 | 600 Ω @ 100 MHz ferrite | +5V_REF -> **AVDD** (filters the analog supply). |
| C81, C82, C90, C91 | 1 µF, 100 nF, 10 µF, 1 µF | AVDD decoupling (pins 9, 30). |
| C83, C92 | 1 µF, 10 µF | DVDD (+3.3V) decoupling (pin 34). |
| C88 | 10 µF | REFIO (reference output) cap. |
| C11, C89 | 1 µF, 22 µF | REFCAP (reference buffer) caps. |
| R83 / R84 | 10 k / 10 k, 0.1 % | **EXC_MON**: +5V_REF ÷ 2 into AUX_IN, so firmware knows the real sensor excitation (ratiometric correction). |
| C93 | 100 nF | EXC_MON filter. |
| R82 | 10 k | Pull-up on RST#/PD# (ADC_RST_PC4) so the ADC is out of reset by default. |

MCU connections: SPI1 - CS PA4, SCK PA5, MISO (SDO) PA6, MOSI (SDI) PA7; reset PC4.

---

## 11. Analog front end AI0-AI7 — sheet (274-360, 254-401), one row per channel

Identical per channel n = 0..7 (AIn from J3 -> ADC_AINn at the ADC):

| Part (channel 0 / 7) | Value | Role |
|---|---|---|
| R73 ... R80 | 100 k | Pull-down at the connector: an unplugged input reads 0 V. |
| R65 ... R72 | 1 k | Series resistor: limits fault / ESD current into the clamp. |
| C73 ... C80 | 100 nF | With the 1 k: 1.6 kHz anti-alias low-pass (more filtering in firmware). |
| D11 (ch 0/1), D12 (2/3), D13 (4/5), D14 (6/7) | PSM712 | Bidirectional clamp at the ADC pins (one part protects two channels). |

Readability tip: this block already reads well as 8 identical rows; keep it that way and label the row with the
J3 pin and the sensor it is meant for.

---

## 12. Spare analog AI8/AI9 (to the MCU's own ADC) — sheet (640-692, 315/356)

| Ref | Value | Role |
|---|---|---|
| R126 / R127 | 10 k / 15 k | AI8 divider: 0-5 V -> 0-3.0 V, open input reads 0. -> **AI8_ADC_PC5**. |
| D28 | BAT54S | Clamp to GND/+3.3V. |
| C158 | 100 nF | Filter. |
| R128 / R129, D29, C159 | same | AI9 -> **AI9_ADC_PE8**. |

---

## 13. Frequency inputs FREQ1-FREQ4 — sheet (640-762, 140-262)

Per channel (FREQ1 shown; FREQ2 = R120/R121/C153/D25, FREQ3 = R122/R123/C154/D26, FREQ4 = R124/R125/C155/D27):

| Ref | Value | Role |
|---|---|---|
| R118 | 2.2 k | Pull-up to that branch's sensor supply (+5V_WS_L/R/C) for open-collector Hall sensors. |
| R119 | 10 k | Series resistor. |
| C152 | 1 nF | With 10 k: ~16 kHz filter. |
| D24 | BAT54S | Clamp to 3.3 V / GND (5 V signal -> safe for 3.3 V logic). |
| U20 (FREQ1/2), U21 (FREQ3/4) | SN74LVC2G17 | Dual Schmitt-trigger buffers: clean edges into the timer. |
| C156, C157 | 100 nF | Buffer decoupling. |

Pull-up supplies: FREQ1 -> +5V_WS_L, FREQ2 -> +5V_WS_R, FREQ3 and FREQ4 -> +5V_WS_C.
MCU: TIM2 CH1 PA0 (FREQ1), CH2 PA1 (FREQ2), CH3 PB10 (FREQ3), CH4 PB11 (FREQ4).

---

## 14. CAN1 (TCAN1044AV, U3) — sheet (345, 57)

| Ref | Value | Role |
|---|---|---|
| U3 | TCAN1044AVDRQ1 | CAN-FD transceiver. VCC = +5V, VIO = +3.3V (logic level). |
| C15, C16 | 100 nF | VCC, VIO decoupling. |
| R1 | 10 k | Pull-down on STB -> transceiver active by default (CANSTBPD2). |
| D1 | PESD2CAN | CAN bus ESD protection. |
| R5, R4 | 60.4 Ω 1206 | Split termination legs (CAN1H, CAN1L). |
| C14 | 4.7 nF | Split-termination midpoint cap to GND (common-mode filtering). |
| JP1 | 3-pad solder jumper, **open** | Connects both legs to the midpoint. Bridge all 3 pads to terminate; open = no termination (board mid-bus, CAN1 passes through J3 29-32). |

MCU (FDCAN1): RX PD0, TX PD1, STB PD2.

## 15. CAN2 (TCAN1044AV, U8) — sheet (531, 65)

| Ref | Value | Role |
|---|---|---|
| U8 | TCAN1044AVDRQ1 | CAN-FD transceiver (VCC +5V, VIO +3.3V). |
| C19, C94 | 100 nF | VCC, VIO decoupling. |
| R85 | 10 k | STB pull-down (CAN2STBPD3). |
| L6 | ACT1210 common-mode choke | Between transceiver side (CANH/CANL) and bus side (CAN2H_BUS/CAN2L_BUS). **PCB uses a stand-in footprint.** |
| D19 | ESD2CANFD24 | CAN bus ESD (pins renamed IO1/IO2/GND). |
| R14, R15 | 60.4 Ω | Split termination legs. |
| C20 | 4.7 nF | Midpoint cap (net CAN_VREF). |
| JP2 | 3-pad solder jumper, **bridged** | Termination on by default (this board ends CAN2). |

MCU (FDCAN2): RX PB5, TX PB6, STB PD3.
Readability tip: net names CANH/CANL (CAN2 transceiver side) vs CAN1H/CAN1L are easy to confuse - consider renaming
to CAN2H_XCVR / CAN2L_XCVR.

---

## 16. MCU (STM32G474VET3, U1) — sheet (183, 174)

170 MHz Cortex-M4F, LQFP-100. Supply and housekeeping parts:

| Ref | Value | Role |
|---|---|---|
| C2, C4, C5, C6, C85, C86, C87 | 100 nF | One per VDD pin. |
| C7 | 4.7 µF | Bulk on +3.3V. |
| C8, C9 | 1 µF | VDDA / VREF+ (analog supply and ADC reference = 3.3 V). |
| C1 | 100 nF | NRST filter cap. |
| R81 | 10 k | BOOT0 pull-down: boots from flash. |
| X1 + C12, C13 | 16 MHz crystal + 2× 33 pF C0G | HSE clock (PF0/PF1). |
| J5 | 4-pin 2.54 mm header | SWD programming: 1 GND, 2 +3.3V, 3 SWDIO (PA13), 4 SWCLK (PA14). |
| D30 + R130 | yellow LED + 1 k | CAN activity LED (PE0). |
| D31 + R131 | red LED + 1 k | FAULT LED (PE1). |
| D32 + R132 | green LED + 1 k | STATUS LED (PE2). |
| R135 + JP3, R136 + JP4 | 10 k pull-up + open jumper to GND | Node ID bits 0/1 (PC0/PC1): open = 1, bridged = 0. |

Rail monitors (all into MCU ADC pins, each with a 100 nF filter cap):

| Net / MCU pin | Divider | Scale | Cap |
|---|---|---|---|
| VMON_VIN_PC2 | R86 100 k / R87 10 k from VIN_PROT | ÷ 11 (to ~36 V) | C98 |
| VMON_12V_PC3 | R108 47 k / R109 10 k from +12V_SNS | ÷ 5.7 | C135 |
| VMON_7V_PB0 | R90 20 k / R91 10 k from +7V | ÷ 3 | C108 |
| VMON_5VREF_PB1 | R94 10 k / R95 10 k from +5V_REF | ÷ 2 | C115 |
| VMON_5V_PB2 | R92 10 k / R93 10 k from +5V | ÷ 2 | C109 |

### MCU pin map (all used pins)

| Pin | Port | Net | Pin | Port | Net |
|---|---|---|---|---|---|
| 1 | PE2 | LED_STAT_PE2 | 51 | PB12 | SPI2_DAT3_PB12 (SD CS) |
| 12 | PF0 | HSE_IN | 52 | PB13 | SPI2_SCK_PB13 |
| 13 | PF1 | HSE_OUT | 53 | PB14 | SPI2_MISO_PB14 |
| 14 | NRST | NRST | 54 | PB15 | SPI2_MOSI_PB15 |
| 15 | PC0 | NODE_ID0_PC0 | 55 | PD8 | SPI2_CD_PD8 (unused label - remove) |
| 16 | PC1 | NODE_ID1_PC1 | 56 | PD9 | SD_PWR_EN_N_PD9 |
| 17 | PC2 | VMON_VIN_PC2 | 70 | PA9 | VBUS_SENSE_PA9 |
| 18 | PC3 | VMON_12V_PC3 | 72 | PA11 | USB- |
| 20 | PA0 | TIM2_CH1_FREQ1_PA0 | 73 | PA12 | USB+ |
| 21 | PA1 | TIM2_CH2_FREQ2_PA1 | 76 | PA13 | SWDIO_PA13 |
| 26 | PA4 | SPI1_CS_PA4 (ADC) | 77 | PA14 | SWCLK_PA14 |
| 27 | PA5 | SPI1_SCK_PA5 | 78 | PA15 | IMU_CS_PA15 |
| 28 | PA6 | SPI1_MISO_PA6 | 79 | PC10 | SPI3_SCK_PC10 |
| 29 | PA7 | SPI1_MOSI_PA7 | 80 | PC11 | SPI3_MISO_PC11 |
| 30 | PC4 | ADC_RST_PC4 | 81 | PC12 | SPI3_MOSI_PC12 |
| 31 | PC5 | AI8_ADC_PC5 | 82 | PD0 | CANRXPD0 |
| 32 | PB0 | VMON_7V_PB0 | 83 | PD1 | CANTXPD1 |
| 33 | PB1 | VMON_5VREF_PB1 | 84 | PD2 | CANSTBPD2 |
| 34 | PB2 | VMON_5V_PB2 | 85 | PD3 | CAN2STBPD3 |
| 38 | PE7 | PG_12V_PE7 | 86 | PD4 | BARO_CS_PD4 |
| 39 | PE8 | AI9_ADC_PE8 | 87 | PD5 | IMU_INT1_PD5 |
| 47 | PB10 | TIM2_CH3_FREQ3_PB10 | 88 | PD6 | IMU_INT2_PD6 |
| 50 | PB11 | TIM2_CH4_FREQ4_PB11 | 89 | PD7 | BARO_INT_PD7 |
| 92 | PB5 | CAN2RXPB5 | 95 | PB8 | BOOT0 |
| 93 | PB6 | CAN2TXPB6 | 97/98 | PE0/PE1 | LED_CAN_PE0 / LED_FAULT_PE1 |

Power pins: VDD 24/49/64/75/100, VSS 23/48/63/74/99, VDDA 37, VREF+ 36, VSSA 35, VBAT 6 (tied to +3.3V, no RTC battery).
35 pins are unused and carry no-connect flags.

---

## 17. USB-C — sheet (157, 384) and (478-516, 779)

| Ref | Value | Role |
|---|---|---|
| USBC1 | TYPE-C-31-M-12 | USB-C receptacle (USB 2.0 full speed; SBU unused). |
| R12, R13 | 5.1 k | CC1/CC2 pull-downs: identifies the board as a USB device (sink) so hosts supply 5 V. |
| U22 | USBLC6-2SC6 | ESD protection on D+/D-, referenced to VBUS. |
| C166 | 1 µF | VBUS bulk cap. |
| R139 / R140 | 10 k / 20 k | VBUS sense -> **VBUS_SENSE_PA9** (~3.3 V when plugged in). Firmware enables the D+ pull-up only then. |
| PWR_FLAG on VBUS | - | ERC. |

USB alone powers the 3.3 V side through D43 (section 6).

## 18. microSD (J1) + power switch — J1 (537, 154), switch (686-730, 660)

| Ref | Value | Role |
|---|---|---|
| J1 | Molex 47309-2651 | microSD socket, SPI mode on SPI2. 1 DAT2, 2 DAT3/CS (PB12), 3 CMD/MOSI (PB15), 4 VDD (SD_VDD), 5 CLK, 6 GND, 7 DAT0/MISO (PB14), 8 DAT1, G1-G4 shell GND. |
| R9 | 33 Ω | Series damping on the clock (PB13 -> pin 5). |
| R6, R7, R8, R10, R11 | 47 k to SD_VDD | Pull-ups on DAT2, CS, MOSI, MISO, DAT1 (SD spec; unused lines must not float). |
| C17, C18 | 100 nF, 10 µF | Card supply decoupling. |
| Q7 | AO3401A P-FET | High-side switch +3.3V -> **SD_VDD**, so firmware can power-cycle a hung card. |
| R137 | 100 k | Gate pull-up: card off while the MCU is in reset. |
| R138 + C165 | 10 k + 100 nF | Gate RC: ~1 ms soft start (avoids dipping +3.3V when the card's caps charge). |
| PWR_FLAG on SD_VDD | - | ERC. |

MCU: PD9 low = card on (SD_PWR_EN_N_PD9). Firmware: drive the SPI2 lines low before switching the card off.

## 19. IMU (ISM330DHCX, U23) — sheet (419, 638)

| Ref | Value | Role |
|---|---|---|
| U23 | ISM330DHCXTR | 6-axis accel/gyro, ±16 g / ±4000 dps, on SPI3. SDx/SCx (aux I²C master, unused) to GND; OCS_Aux/SDO_Aux no-connect. |
| C160, C161 | 100 nF, 1 µF | VDD decoupling. |
| C162 | 100 nF | VDD_IO decoupling. |
| R133 | 10 k | CS pull-up (IMU_CS_PA15): deselected during MCU reset. |

MCU: CS PA15, INT1 PD5, INT2 PD6. Firmware: set CTRL4_C.I2C_disable = 1 at init.

## 20. Barometer (BMP581, U24) — sheet (419, 704)

| Ref | Value | Role |
|---|---|---|
| U24 | BMP581 | Absolute pressure sensor, on SPI3. |
| C163, C164 | 100 nF | VDD and VDDIO decoupling. |
| R134 | 10 k | CS pull-up (BARO_CS_PD4). |

MCU: CS PD4, INT PD7. Firmware: one dummy read first (switches the BMP581 into SPI mode).
Shared SPI3 bus: SCK PC10, MISO PC11, MOSI PC12.

---

## 21. Things to fix or decide while tidying

1. `SPI2_CD_PD8` label on PD8 goes nowhere (card-detect not used): remove it and add a no-connect flag.
2. The +3.3V symbol at U4's output is a `power:+5V` symbol with its value changed - replace with `power:+3.3V`.
3. Inductor U6 has a "U" reference; L6's PCB footprint is a stand-in (update from your local easyeda2kicad library).
4. Net names `CANH` / `CANL` (CAN2 transceiver side) vs `CAN1H` / `CAN1L` - consider clearer names.
5. Many auto-placed parts have overlapping value / reference text (power-symbol references are hidden already).
6. If you rename nets or references, re-export and re-sync the board: tell me and I will re-run `sync_board.py` and
   the parity check so the PCB follows without moving your placement.
