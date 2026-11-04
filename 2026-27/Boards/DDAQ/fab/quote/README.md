# Gerbers for JLCPCB price comparison only - NOT for ordering

Both boards are incomplete (unrouted connections, no silkscreen cleanup, L6 stand-in footprint). Use these
zips only to compare bare-board prices; the price depends on size, layer count, quantity and options, not on
whether the routing is finished.

| Zip | Source | Layers | Size | Notes |
|---|---|---|---|---|
| `DDAQ_6L_gerbers.zip` | commit 82d2343 (branch `ddaq/pcb-6L-v1`) | 6 | 120 x 100 mm | J3 housing on the board (old position), 44 unrouted |
| `DDAQ_4L_gerbers.zip` | commit d364040 (`ddaq/g474-schematic-rev`) | 4 | 120 x 100 mm, 2 edge notches | J3 at TE's edge position, 49 unrouted |

Exported with KiCad 10.0.8 `kicad-cli` (Gerber X2 + Excellon, PTH/NPTH separate). For a like-for-like quote
pick the same options for both: 1.6 mm, HASL or ENIG, same quantity, same min hole/trace (0.3 mm via drill,
0.15 mm min track/space). The 6-layer file uses KiCad's default stackup; on JLCPCB choose their standard
6-layer stackup (or the impedance-controlled one if you want it).
