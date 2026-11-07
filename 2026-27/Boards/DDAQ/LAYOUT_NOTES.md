# DDAQ PCB layout notes (rev for STM32G474 schematic)

Status 2026-11-04: **placement being reworked by hand - routing cleared.** The board has every part in a named KiCad group (IC + the parts directly connected to it, see `PLACEMENT_GROUPS.md`); tracks, vias and the F.Cu power pours were removed, the In1 GND / In2 power planes kept. Last routed versions: 4-layer J3-at-edge, 49 unrouted (commit d364040); 6-layer v1, 44 unrouted (branch `ddaq/pcb-6L-v1`).
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

## J3 AMPSEAL 776163-1 mounting (from TE customer drawing 776163 rev K1 + application spec 114-16016 rev S3,
## both in `datasheets/`)
- Panel-mount header: the mating shroud (~19.3 mm) goes **through the enclosure wall**; the flange's silicone
  gasket seals against the inside face of a 2-5 mm panel; 4x 2.5 mm thread-forming screws (Delta PT), cross
  pattern 0.3-0.4 N-m then 0.6-0.8 N-m; header flush to the panel before final torque. Panel cut-out
  60.0-60.5 x 24.2-25.2 mm, R6.6-6.8 corners; screw holes 4x 3.0-3.3 mm on 63.4 x 18.1 mm; sealing surface
  flat within 0.5, Ra <= 0.4 (ISO 1302).
- **PCB edge = 9 mm from the centreline of the two 2.85 mm peg holes** (Fig. 13a), i.e. J3 footprint y = +9.5
  (middle pin row at y = 0, pegs at y = +0.5). Two notches in the edge under the flange's lower screw bosses
  (bosses at x = +/-33.2, 8 mm deep behind the flange); notch size taken from the figure (~6.5 x 6 mm, not
  dimensioned by TE - check against a sample).
- **Current board is wrong here**: its edge is at y = +31.2 (whole shroud on the PCB, ~21.7 mm too far out).
- Footprint fixed to TE's layout: pin holes 1.9 mm drill (1.75 +/-0.1 after plating; was 2.0), retention-peg
  holes 2.85 mm NPTH (was 3.0). Board thickness 1.57 mm (TE).

## J3 at the board edge, re-route (2026-11-03, current board)
- Board stays 120 x 100. J3 moved to TE's edge rule (PCB edge 9 mm from the peg centreline) with the shroud
  overhanging the bottom edge and two edge notches under the flange's lower screw bosses. The freed ~22 mm went to
  moving the analog section, 7 V / 5 V bucks, frequency inputs, IMU and the lower parts of the MCU/CAN blocks down
  16 mm, opening a band through the old congestion (`place.py`, `DDAQ_J3EDGE=1`).
- **4 layers** (F sig / In1 GND / In2 split power / B sig): supervised Freerouting 66 -> 58 -> 53, finisher -> **49**.
  (Before the move, 4 layers stalled at 81.)
- 6 layers on the same placement: four Freerouting runs in a row stalled at pass 1-3 (195-379), so the time went
  to 4 layers instead. The 6-layer v1 (old J3 position) reached 44.
- Remaining 49 are spread out (no single hot spot): GND 8, +3.3V 6, +12V_SNS 3, +7V 2, LM5175 stage 4 (BB_RS,
  BB_SW1, BB_HD2), the rest single signals (SPI1 to the ADC, SPI3, CAN2 control, crystal HSE_OUT, CAN1 term, ...).
  Plus 16 dangling vias / 10 dangling tracks to clean (Tools > Cleanup Tracks & Vias) and silkscreen.

## USB bench power + VBUS sense (2026-11-04)
- D42/D43 (B5819W) diode-OR +5V and USB VBUS into the 3.3 V LDO U4 (new net LDO_IN, 10 uF C167 after the diodes).
  USB alone powers only the 3.3 V side (MCU, SD, IMU, baro, LEDs); no back-feed either way. C166 1 uF on VBUS,
  PWR_FLAGs on LDO_IN and VBUS. VBUS sense: R139 10k / R140 20k to PA9 (pin 70, was NC).
- Placement: added next to U4 and USBC1 by `sync_board.py` (keeps all other placement), inside their groups.
- U4 changed from AMS1117-3.3 to **TI TLV1117LV33DCYR (LCSC C15578)**: same SOT-223 pinout (1 GND, 2 OUT + tab,
  3 IN), dropout 90 mV @ 200 mA / 230 mV @ 500 mA (datasheet SBVS160C) -> ~1 V margin from the ~4.4-4.6 V LDO_IN.
  VIN max 5.5 V (6 V abs): only ever fed from +5V or VBUS through the diodes - never connect it to +7V.
- Board fields re-synced to the schematic (Datasheet on all footprints, JP1-JP4 excluded from BOM); DRC schematic
  parity now clean except the known L6 stand-in footprint. (Earlier "parity clean" checks were run without the
  schematic file present and so did not compare fields.)

## LM5175 buck-boost removed (2026-11-07)
- The 12 V sensor outputs did not need a regulated 12 V from a ~12.9 V battery, so U11 and its 41 parts (Q3-Q6, L8,
  R96-R107, C116-C134, D21, D22) plus the 12 V monitor R108/R109/C135 are gone (schematic 286 -> 244 parts).
  F3/F4 now feed +12V_OUT1/2 from VIN_PROT; PC3 and PE7 have no-connect flags.
- Board: footprints and the LM5175 group deleted; the In2.Cu +12V_SNS plane region was reassigned to VIN_PROT
  (it joins the VIN_PROT column on its left). The freed area (top-left, about x 119-141 / y 50-86) is open for the
  manual floorplan.
- Check: the pitot sensor (and whatever uses OUT2) must accept the raw battery range plus surges up to the SMBJ18CA
  clamp (~29 V for a short time).
- Fixed at the same time: commit 36059ec had reset `DDAQ.kicad_pro` to defaults (net classes, design rules,
  track/via presets, ERC pin map lost). Restored from b25fa1b; net-class patterns for the deleted nets dropped.
