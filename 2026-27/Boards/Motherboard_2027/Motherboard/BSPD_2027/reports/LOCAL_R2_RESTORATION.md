# Local non-latching R2 restoration - November 1, 2026

Restored the coherent schematic, PCB, project settings, sourcing and manufacturing package from pushed commit 6017215, retaining the ground-symbol conversion. Removed U9, C13, C14, R33 and D3. U8 implements PERMIT = FAULT_OK AND POR_N. Fault retention remains the external relayboard responsibility.

66 physical components remain. Fresh KiCad ERC: 0 violations. PCB DRC: 0 violations, 0 unconnected items, 0 schematic parity issues. Before/after ground conversion netlists have identical R2 connections. The 43 remaining GND anchors use standard symbols. Existing vehicle calibration and physical qualification holds remain.

Close and reopen the KiCad project after installation. An already-open old schematic or PCB can overwrite the corrected files if saved. The previous local files are backed up in history. This restoration does not push additional changes to GitHub.
