# DDAQ — handoff for a cloud Claude session (2026-11-02)

Read `CLAUDE_HANDOFF.txt` first (tooling background). This note covers the schematic work done on 2026-11-02 and the
next task. The PCB has NOT been updated from the schematic yet.

## State of the schematic (DDAQ/DDAQ.kicad_sch)

- MCU: STM32G474VET3 (C2970837). 16 MHz HSE crystal X1 on PF0/PF1, BOOT0 pulldown R81.
- ADC: ADS8688IDBTR on SPI1 (PA4–PA7, RST PC4). AUX_IN measures +5V_REF via 0.1% 10k/10k (EXC_MON).
  Input RC = 100 nF (1.6 kHz); filtering is done in firmware (note on sheet). PSM712 clamps D11–D14.
- CAN1 SN65 (existing), CAN2 TCAN1044AV (U8) on PB5/PB6, choke L6, PSM712 clamps.
- Power: VBAT → F1 → D20 SMBJ18CA → Q2 reverse-polarity → VIN_PROT → U11 LM5175 buck-boost → +12V_SNS
  (PGOOD → PE7); U9 LMR33630 → +7V; U2 TPS563300 (+7V in) → +5V; U10 TPS7A4700 → +5V_REF.
  Six NCV8184 trackers: +5V_EXC_L/R/C and +5V_WS_L/R/C. Fused +12V_OUT1 (pitot), +12V_OUT2 (pod/spare), IZZE_PWR.
  Rail monitors: PC2 VIN, PC3 12V, PB0 7V, PB1 5V_REF, PB2 5V.
- I/O: 4 frequency inputs → SN74LVC2G17 → TIM2 CH1–4 (PA0, PA1, PB10, PB11); spare analog AI8/AI9 → PC5/PE8;
  USBLC6-2 on USB; LEDs CAN PE0 / FAULT PE1 / STAT PE2; SWD header J5 (1 GND, 2 3.3V, 3 SWDIO, 4 SWCLK).
- Connector: single TE AMPSEAL 35 (776163-1, C412117) as J3. Pin map is in `claude_scripts/gen_conn.py` (PINMAP).
  SMF15A TVS D33–D41 on every off-board supply pin. CAN1 passes through (29/31 = H, 30/32 = L).

Every step was verified by exporting kicad-cli netlists before/after and diffing every pre-existing part's pin nets
(0 unintended changes) plus checking new parts against an intent list (`claude_scripts/data/intent*.json`).

## DONE 2026-11-03 (cloud session): barometer + IMU on SPI3

Applied with KiCad 10.0.8 kicad-cli (official `kicad/kicad:10.0.8-amd64` Docker image) + mcp-server-kicad 0.21.1 via
`kb.py batch` (`claude_scripts/gen_sensors.py` -> `batchSENS.json`, intent in `data/intent_sens.json`).
Placed at sheet x 365-530 / y 590-745 (was empty; guard check in the script).

- U23 ISM330DHCXTR (C2655101), U24 BMP581 (C5362283), C160/C162 100 nF + C161 1 uF (IMU VDD/VDD_IO),
  C163/C164 100 nF (baro VDD/VDDIO), R133/R134 10k CS pull-ups. U23 pins 2/3 -> GND, 10/11 -> no-connect.
  U1 pins 78/79/80/81/86/87/88/89 labelled as in the table below. Firmware + layout notes added as sheet text.
- Verified: netlist before/after -> 0 net changes on pre-existing parts; all 46 intended pins match; ERC adds only
  items in categories that already exist (pin_to_pin / lib_symbol_issues / footprint_link_issues for the new parts,
  pin_not_driven on R133/R134 pin 2 like the other resistors), and clears 8 pin_not_connected on U1.
- mcp-server-kicad dropped the stale legacy top-level `(symbol_instances ...)` block (KiCad 7+ ignores it; each
  symbol keeps its own `(instances ...)`). New blocks are not eeschema-formatted; KiCad will reformat on next save.

**STILL TO DO for this step (needs the user's machine, cloud network blocks easyeda/lcsc/jlcpcb/st.com):**
1. Footprints + 3D models were NOT imported (the symbols were added to `JLCImport.kicad_sym` from the captured
   importer output in `data/sym_*.txt`). Run locally:
   `python -I -X utf8 claude_scripts/bin/jlc.py import C2655101 -p 2026-27/Boards/DDAQ/DDAQ` and the same for C5362283
   (if it refuses because the symbol already exists, use its overwrite option; re-fix the ISM330 Datasheet field).
2. ISM330DHCX pins 2/3/10/11 were checked against ST's pin table from memory (SDx/SCx: VDDIO or GND; OCS_Aux: leave
   open; SDO_Aux: VDDIO or open), not against the PDF. Confirm in DS13012 Table 2.
3. Cosmetic: power symbols on adjacent sensor pins overlap and the new #PWR refs are visible -> part of "sheet tidy".

## (was NEXT TASK) add barometer + IMU on SPI3 (approved by the user)

MCU pins are free (checked against the netlist). SPI3 = AF6 on all three.

| Net                | MCU pin       |
|--------------------|---------------|
| SPI3_SCK_PC10      | U1.79 (PC10)  |
| SPI3_MISO_PC11     | U1.80 (PC11)  |
| SPI3_MOSI_PC12     | U1.81 (PC12)  |
| IMU_CS_PA15        | U1.78 (PA15)  |
| BARO_CS_PD4        | U1.86 (PD4)   |
| IMU_INT1_PD5       | U1.87 (PD5)   |
| IMU_INT2_PD6       | U1.88 (PD6)   |
| BARO_INT_PD7       | U1.89 (PD7)   |

**IMU: ISM330DHCXTR, LCSC C2655101** (industrial −40…105 °C, ±16 g, ±4000 dps, ~4.5k stock). Not imported yet.
LCSC symbol pins (in `data/sym_C2655101.txt`; its Datasheet field is junk — set it to
https://www.st.com/resource/en/datasheet/ism330dhcx.pdf):
1 SDO/SA0 → SPI3_MISO · 13 SCL → SPI3_SCK · 14 SDA → SPI3_MOSI · 12 CS → IMU_CS_PA15 ·
4 INT1 → IMU_INT1_PD5 · 9 INT2 → IMU_INT2_PD6 · 5 VDD_IO, 8 VDD → +3.3V · 6, 7 GND ·
2 SDx, 3 SCx (aux I2C master, unused) → GND · 10 OCS_AUX, 11 SDO_AUX → no-connect.
CHECK pins 2/3/10/11 against the ST datasheet pin table before wiring.
Decoupling: 100 nF on VDD and on VDD_IO, plus 1 µF on VDD.

**Barometer: BMP581, LCSC C5362283** (Bosch, ~6.9k stock). Pinout verified against datasheet BST-BMP581-DS004
Table 28, matches the LCSC symbol (`data/sym_C5362283.txt`):
1 VDDIO, 10 VDD → +3.3V · 3, 8, 9 VSS → GND · 2 SCK → SPI3_SCK · 4 SDI → SPI3_MOSI · 5 SDO → SPI3_MISO ·
6 CSB → BARO_CS_PD4 · 7 INT → BARO_INT_PD7. Decoupling: 100 nF on VDD and on VDDIO.

Also: 10k pull-ups to +3.3V on IMU_CS_PA15 and BARO_CS_PD4 (keep both deselected during MCU reset/boot).

Firmware notes to put on the sheet as a text note:
- ISM330DHCX: set CTRL4_C.I2C_disable = 1 at init (it shares the SPI bus; CS high otherwise means I2C mode).
- BMP581 switches to SPI on the first CSB falling edge; do a dummy read first.
Layout notes for later: IMU near the board mounting point / centre, axes marked on silkscreen; barometer away
from the LM5175/LMR33630/TPS563300 hot spots, and the enclosure needs a vent (membrane) over it.

### How to do it (same workflow as the previous steps)

1. Import parts into the project library: `python -I -X utf8 claude_scripts/bin/jlc.py import C2655101 -p 2026-27/Boards/DDAQ/DDAQ`
   (and C5362283). `bin/jlc.py` hard-codes the plugin dir — the plugin is github.com/jvanderberg/kicad-jlcimport;
   clone it and fix the path `D=` at the top. Then regenerate `libsyms.json` for the new symbols
   (pin number, name, x, y, angle + props incl. LCSC/Footprint) — `gen_*.py` read pin geometry from it.
2. Copy `gen_io.py` as a template (helpers `place`, `pin`, `conn`, `part2`, `ic`). Pick an empty area of the sheet
   and keep its guard check that nothing is already inside the target box. Already used by recent steps:
   x 600–880 / y 115–365 (I/O), J3 at (939.8, 228.6), TVS row x 977.9–1079.5 at y 335.28.
   Next free refs: check the netlist (U25+, R135+, C165+ after the sensor step).
3. Apply with `uv run --script claude_scripts/kb.py batch batch.json` (wraps tools/kicad-batch/server.py,
   mcp-server-kicad 0.21.1). Quirks: place_component needs `symbol_lib_path` for JLCImport symbols and leaves
   Footprint/LCSC empty (copy them with set_component_property); wire_pins_to_net makes local labels, so power
   pins use an add_wires stub + add_power_symbol (rot GND: down0/left270/right90/up180; +V: up0/left90/right270/down180).
4. Verify: `kicad-cli sch export netlist --format kicadxml` before/after, diff all pre-existing parts (expect 0),
   check new pins vs intent, `kicad-cli sch erc` — compare to the previous ERC categories.

### Cloud environment caveats
- Needs KiCad **10.x** kicad-cli (files are KiCad 10 format; do NOT save them with an older KiCad).
  Check `kicad-cli --version` before touching anything.
- All scripts and `.mcp.json` use Windows paths (`C:/Git/USC-Electrical-Systems/...`, `C:/Program Files/KiCad/10.0/bin`).
  Change the constants at the top of `kb.py`, `gen_*.py` (LIBPATH/SCH) and `bin/jlc.py`.
- The `gen_*.py` scripts read scratchpad backups (`backup_before_*.kicad_sch`) that are not committed; for a new
  step, back up the current schematic first and point the script at that copy.

## Still to do after the sensors (for the user to prioritise)
1. CAN termination solder jumpers on both buses (CAN1 is now pass-through; termination is always on today).
2. Node-ID jumpers on PC0/PC1 (labels exist, unconnected).
3. SD card-detect PD8 / power-enable PD9 (labels exist, unconnected).
4. Cleanup: J1 symbol/footprint lib points at a OneDrive path (copies in `DDAQ/footprints.pretty` and
   `2026-10-05_08-09-50.kicad_sym`); missing LCSC on J1, Q2, U2, U4; D19 symbol pin names wrong;
   NC flags on unused MCU pins; remove unused USART2 / TIM3 PWM labels; sheet tidy.
5. Check LM5175 compensation (5.1k / 27 nF / 100 pF, slope 100 pF) in TI's calculator.
6. Update PCB from schematic and re-layout (board will likely grow; AMPSEAL on one edge).
