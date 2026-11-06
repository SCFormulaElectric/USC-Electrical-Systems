# Ordering files — starter only

`BOM_JLCPCB.csv` uses Comment, Designator, Footprint and LCSC Part # columns. It contains 5 resistors, 1 normally closed relay, 3 headers and 1 bidirectional TVS. `Procurement.csv` provides manufacturer part numbers, quantities, LCSC links and datasheet links.

The relay, resistors and headers are through-hole; D1 is SMT. Obtain a JLCPCB quote for these exact parts and assembly process; LCSC listing alone does not guarantee turnkey assembly support. A substitute must preserve NC behavior, switching/insulation ratings, coil behavior, power/thermal ratings and footprint.

No Gerbers or CPL are supplied because placement and routing are unfinished. After completing the board, re-export its BOM and placement data, check pin 1/orientation and compare the quoted parts against these fields. See the project README for design limits and remaining checks.
