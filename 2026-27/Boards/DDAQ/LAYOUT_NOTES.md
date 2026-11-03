# DDAQ PCB layout notes (rev for STM32G474 schematic)

Status 2026-11-03: **6-layer, routing in progress - 44 connections still unrouted, 0 clearance errors** (`layout_routed_wip.png`).
Earlier status: placement done, not routed. `DDAQ/DDAQ.kicad_pcb` was rebuilt from the schematic netlist
(scripted "Update PCB from Schematic": `claude_scripts/pcb/build_board.py`, grouping `group.py`, placement
`place.py`, planes `zones.py`). DRC: no courtyard/clearance violations, schematic parity 0, 499 unrouted
connections. Placement picture: `layout_placement.png`.

## Board
- 120 x 100 mm rectangle, 3 mm corner radius (replaces the old 63x56 + wider-bottom shape). 4 layers kept:
  F.Cu signal / In1.Cu solid GND plane / In2.Cu power + spare routing / B.Cu signal. Stackup and design rules
  unchanged (0.2 mm default track/clearance, 0.6/0.3 vias, 0.14 mm fine-pitch pad rule).
- 4x M3 plated holes (H1-H4, 4 mm from the corners, on GND, board-only footprints so a schematic sync keeps them).
- Net classes added in `DDAQ.kicad_pro`: Power_HI 0.8 mm (VBAT, VIN_PROT, buck-boost switch/sense nodes,
  +12V_SNS), Power 0.4 mm (rails, sensor supplies, gate drives), CAN 0.25 mm, USB 0.25 mm, Default 0.2 mm.

## Floorplan
- **J3 AMPSEAL 35** on the bottom edge, housing flush with the edge, pins facing in. Nothing placed under the
  housing (31 mm deep). Supplies on the inner row, AI0-AI9 middle row, VBAT/12V outs/CAN on the edge row.
- **Power (top-left quadrant)**: LM5175 H-bridge with Q3/Q4 (SW1 leg) left of L8, Q5/Q6 (SW2 leg) right,
  R107 in the low-side return, controller U11 below; LMR33630 (+7V, L7) and TPS563300 (+5V, U6) below that.
  Switchers are >= 25 mm from the ADC and on the opposite side from the barometer.
- **Input protection** (F1, D20, Q2 reverse-polarity) in the strip left of J3.
- **Analog (above the J3 AI pins)**: ADS8688 U5 with RC filter caps and PSM712 clamps at its pins on both
  sides, REF U10 beside it; 100k pull-downs next to the connector.
- **MCU centre-top**: U1 with decoupling at the supply pins, X1 at PF0/PF1, USB-C + USBLC6 ESD and the SWD
  header on the top edge; AMS1117 3.3 V regulator next to the MCU.
- **Top-right**: microSD (card inserts from the top edge), SD power switch Q7, barometer U24 (furthest from the
  switchers). IMU U23 near the board centre.
- **Right side**: CAN transceivers + ESD + choke + termination jumpers; frequency-input conditioning; the six
  NCV8184 sensor-supply trackers in a column beside J3.

## Deviations from best practice / open items
1. **L6 (CAN2 common-mode choke) uses a stand-in footprint** (`Inductor_SMD:L_CommonModeChoke_Coilank_ACM3225`,
   same pad numbers). The real one (`easyeda2kicad:FILTER-SMD_4P-L3.9-W2.5-BL`) only exists in your local library:
   copy it into `JLCImport.pretty` (or run Update PCB from Schematic locally) before routing near L6.
2. Placement is script-generated (anchors by hand, passives packed next to the pin they connect to). It needs a
   human pass, especially: buck-boost hot loops (input caps tight to Q3/Q4, output caps tight to Q5/Q6), the
   LMR33630/TPS563300 input-cap-to-GND loops, crystal load caps, and silkscreen.
3. Silkscreen references are at library default positions (199 silk overlaps) - tidy last.
4. USB D+/D- use a 0.25 mm class, not a 90-ohm controlled-impedance pair (full-speed USB, short run: acceptable).
5. Mounting holes are plated and tied to GND; change to NPTH if the enclosure must not touch GND.
6. Board size is generous (~57 % courtyard fill); shrink after routing if there is margin.
7. C19, C20, R14, R15, D19 footprints switched to KiCad standard ones (were in local-only easyeda2kicad /
   PCM_JLCPCB libraries); schematic updated to match.

## Routing status (WIP)
- In1.Cu solid GND. In2.Cu split power planes: VIN_PROT (left column), +12V_SNS (buck-boost output), +7V
  (analog/tracker band and right strip), +3.3V (MCU/digital), GND under J3.
- 293 plane fan-out vias placed by script next to GND/rail pads (`fanout.py`, locked).
- LM5175 power stage: Q4/Q6 rotated so both switch nodes face L8; input caps C126-C129 at Q3's drain, output caps
  C130-C134 at Q5's drain; F.Cu pours for BB_SW1, BB_SW2, BB_RS, VIN_PROT, +12V_SNS (`powerpour.py`).
- Signals autorouted with Freerouting 2.1 on F.Cu/B.Cu (In2 is a plane layer), 20 + 15 min. Converged at
  81 unrouted; DRC has no clearance errors; 24 dangling vias + 10 dangling stubs + 1 hole-to-hole to clean.
- Remaining unrouted: ~30 power hops (+7V, +12V_SNS, BB_*, VIN_PROT, AVDD), ~25 in the congested area between the
  power stage, the 5 V buck and the MCU/analog corner (x 140-160, y 80-100), rest scattered signals.
- Deviation: autorouted traces are not hand-quality (some long detours, many vias). Review the analog inputs and
  the crystal before fab.

## 6-layer switch (2026-11-03)
- 4 layers converged at 81 unrouted; growing the board to 130x110 made Freerouting worse (stuck at ~280-300), so
  the board went back to 120x100 and to **6 layers**: F.Cu sig / In1.Cu GND / In2.Cu sig / In3.Cu sig /
  In4.Cu split power (VIN_PROT / +12V_SNS / +7V / +3.3V / GND under J3) / B.Cu sig.
- **The stackup in the file is KiCad's default 6-layer one** (the old 4-layer stackup block was removed; the
  SWIG build cannot edit stackups). Set JLCPCB's 6-layer impedance stackup in Board Setup before ordering.
- Routing: `supervise.py` ran Freerouting unattended (restarts stalled runs, keeps the best KiCad-DRC result,
  continues from it): 56 -> 53 -> 50 -> 46 unconnected; `finisher.py` closed 2 more -> **44**.
- Remaining 44: ~23 plane/power hops (GND 10, +7V 6, +3.3V 5, +12V_SNS 2), ~8 in the LM5175 stage (BB_RS, BB_SW1,
  gate drives BB_HD2/BB_LD1/BB_LD2 - hand-route these short and wide anyway), ~13 signals (SPI1 to the ADC, CAN
  control lines, IMU CS, a frequency input). Most sit around the LM5175 controller / 5 V buck (x 140-160, y 80-100).
- Also: 6 dangling vias + 5 dangling tracks (Tools > Cleanup Tracks & Vias), silkscreen.
- Tried and rejected (notes in fanout.py): far-ring via staggering and 0.2 mm fan-out clearance both put vias
  where the router needs to escape from under the MCU/ADC and made results worse.

## Next
Route: hand-route the switcher power loops and wide power nets, then autoroute the rest (Freerouting, via
Specctra DSN; needs permission to run the jar in the cloud session), then pour GND on F/B, stitch, DRC, silk.
