# kicad-batch

An MCP server that sits next to [mcp-server-kicad](https://pypi.org/project/mcp-server-kicad/) and
cuts the number of round trips and the size of results when Claude works on a KiCad project.
mcp-server-kicad does one item per call and returns full reports; a single layout job on the DDAQ
board took ~950 tool calls and ~2.3 MB of results. These tools take lists and return summaries.

| Tool | Does | Replaces |
|---|---|---|
| `batch` | runs many mcp-server-kicad tool calls (schematic or PCB) in one call | hundreds of `set_component_property`, `place_component`, `add_power_symbol`, ... calls |
| `pcb_apply` | many board edits in one save: tracks, vias, moves, fields, reference text, outline, zones, zone merge/priority, deletions | `add_trace`/`add_via`/`move_footprint` one at a time, plus the edits mcp-server-kicad cannot do (delete vias, zones, outline shapes) |
| `pcb_apply(check=True)` | applies to a scratch copy and returns only the DRC violations the edit adds | draw → run full DRC → read it all → fix |
| `pcb_query` | footprints / pads / tracks / vias / nets / zones / outline as compact tables, filtered by box, net and ref patterns, layer | full `list_pcb_*` dumps |
| `drc_summary`, `erc_summary` | counts by type plus a few filtered lines; `only_new=True` diffs against the previous run | 50–110 KB DRC/ERC reports |
| `render` | small PNG of a board region | exporting and reading whole-page PDFs |

## Safety

- Writes are refused while KiCad (kicad / pcbnew / eeschema) is running, because an open editor
  overwrites external edits when it saves. Pass `force=True` only for files KiCad does not have open.
- `pcb_apply` saves only if every op succeeded, and keeps the previous board as `<board>.batch-bak`.
- After the edits it rebuilds connectivity and refuses the save if any new track or via changed
  net. KiCad silently gives new copper the net of any other-net copper it overlaps, which would
  otherwise turn a short into a "dangling via" warning.
- Deletions need a filter (position, box or net), so a typo cannot clear the board.

## Setup

Needs KiCad 10 (its bundled Python provides `pcbnew`) and [uv](https://docs.astral.sh/uv/).
Add to the project's `.mcp.json` next to the `kicad` server:

```json
"kicad-batch": {
  "command": "uv",
  "args": ["run", "--script", "C:/Git/USC-Electrical-Systems/tools/kicad-batch/server.py"],
  "env": {
    "KICAD_SCH_PATH": "<project>/<name>.kicad_sch",
    "KICAD_PCB_PATH": "<project>/<name>.kicad_pcb",
    "KICAD_OUTPUT_DIR": "<project>",
    "KICAD_BIN": "C:/Program Files/KiCad/10.0/bin"
  }
}
```

`KICAD_BIN` defaults to KiCad 10's Windows install folder.

## Files

- `server.py` — the MCP server (dependencies declared inline; `uv run --script` installs them).
- `pcb_worker.py` — board edits and queries; runs under KiCad's own Python.
- `token_report.py` — per-tool calls and result sizes for a Claude Code session transcript, to
  measure a change: `python token_report.py ~/.claude/projects/<project-dir>`.

## Known KiCad quirks handled here

- kicad-cli 10.0.5 labels ERC positions "mm" but writes them divided by 100; `erc_summary` rescales.
- DRC re-picks which item pair it names for a missing connection on every run, so diffs compare
  unconnected items as counts per net.
- Nets are referred to by name: a KiCad 10 board renumbers nets as it is edited.
