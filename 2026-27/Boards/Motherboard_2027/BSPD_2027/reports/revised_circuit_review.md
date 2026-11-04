# R3 circuit review - November 4, 2026

This current review supersedes the older R1/R2 circuit snapshots. The updated sensor is AiM X05PSA02000P18, 0-2000psi, 0.5-4.5V output, 8-16V supply, established by the provided datasheet photo.

R18=270k 1% (C17589), R20=11.3k 1% (C3016737), R22=47k 0.1% (C865515). The remaining component values and physical component-pin connections are preserved. No onboard fault memory is fitted; U8 buffers PERMIT=FAULT_OK AND POR_N, and the relayboard retains trips.

Nominal brake rising/falling points are 1.766348/1.698420V raw after accounting for divider loading and hysteresis. Nominal sensor-fault boundaries are 0.357143/4.694836V raw. All are analytical values. The conservative partial rising maximum is 1.824350V, which can exceed the reported approximately 1.8V hard-brake measurement. Bench/vehicle calibration remains a release blocker.

Fresh ERC, PCB DRC, connectivity and schematic parity checks pass with zero issues. The pre-existing C7 PCB shorts were corrected by restoring its previously verified placement and local supply routing. Actual sensing, fault response, thermal behavior and external relay timing/retention remain untested by these CAD checks. See ../DESIGN_REVIEW.md and circuit_analysis_summary.md.
