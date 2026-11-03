# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp-server-kicad==0.21.1", "pymupdf>=1.24"]
# ///
"""kicad-batch: batched and filtered KiCad tools that sit next to mcp-server-kicad.

Every tool here takes many items per call and returns a short summary, so a layout job costs a
handful of round trips instead of hundreds. Board edits run in KiCad's own Python (pcb_worker.py),
checks and renders go through kicad-cli, and `batch` drives mcp-server-kicad's own tool functions
in-process, so schematic edits reuse that server's tested code.

Configure with the same env vars as mcp-server-kicad (KICAD_SCH_PATH, KICAD_PCB_PATH) plus
KICAD_BIN, the folder holding kicad-cli and KiCad's python (default: KiCad 10 on Windows).
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver import Image

KICAD_BIN = Path(os.environ.get("KICAD_BIN", r"C:/Program Files/KiCad/10.0/bin"))
EXE = ".exe" if sys.platform == "win32" else ""
KICAD_PY = KICAD_BIN / f"python{EXE}"
KICAD_CLI = Path(os.environ.get("KICAD_CLI_PATH", KICAD_BIN / f"kicad-cli{EXE}"))
PCB = os.environ.get("KICAD_PCB_PATH", "")
SCH = os.environ.get("KICAD_SCH_PATH", "")
WORKER = Path(__file__).with_name("pcb_worker.py")
CACHE = Path(tempfile.gettempdir()) / "kicad-batch"
CACHE.mkdir(exist_ok=True)

mcp = MCPServer(
    "kicad-batch",
    instructions=(
        "Batched, filtered KiCad tools. Prefer these over one-item-per-call tools:\n"
        "- batch: run many mcp-server-kicad tool calls (schematic or PCB) in one call\n"
        "- pcb_apply: many board edits (tracks, vias, moves, fields, zones, deletions) in one save;"
        " check=True reports only the DRC violations the edit would add\n"
        "- pcb_query: filtered board data (footprints, pads, tracks, vias, nets, zones, outline)\n"
        "- drc_summary / erc_summary: counts plus a few filtered items; only_new=True diffs against the last run\n"
        "- render: small PNG of a board region\n"
        "Writes are refused while KiCad is running (it would overwrite them on save) unless force=True."
    ),
)


def _dump(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), default=str)


def _kicad_running() -> list[str]:
    names = ("kicad", "pcbnew", "eeschema")
    try:
        if sys.platform == "win32":
            out = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True).stdout
            procs = [line.split(",")[0].strip('"').lower() for line in out.splitlines() if line]
            return sorted({p for p in procs if p.removesuffix(".exe") in names})
        out = subprocess.run(["ps", "-A", "-o", "comm="], capture_output=True, text=True).stdout
        return sorted({Path(p).name for p in out.split() if Path(p).name.lower() in names})
    except OSError:
        return []


def _guard(force: bool) -> str | None:
    running = _kicad_running()
    if running and not force:
        return _dump({"refused": f"KiCad is running ({', '.join(running)}); close it or pass force=True. "
                                 "An open editor overwrites external edits when it saves."})
    return None


def _worker(job: dict) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(job, f)
    try:
        r = subprocess.run([str(KICAD_PY), "-I", str(WORKER), f.name], capture_output=True, text=True, timeout=600)
    finally:
        os.unlink(f.name)
    out = r.stdout.split("@@RESULT@@", 1)
    if len(out) < 2:
        # pcbnew prints harmless "swig/python detected a memory leak" lines by the hundred; drop them
        noise = "swig/python detected"
        err = "\n".join(line for line in (r.stderr + r.stdout).splitlines() if noise not in line)
        return {"error": f"worker failed (exit code {r.returncode})", "stderr": err[-1500:]}
    try:
        return json.loads(out[1])
    except ValueError:
        return {"error": f"worker output cut short (exit code {r.returncode}); check the board before retrying",
                "partial": out[1][:500]}


# --- DRC / ERC ----------------------------------------------------------------------------
def _norm(v: dict, scale: float = 1.0) -> dict:
    items = v.get("items", [])
    return {
        "type": v.get("type", "?"),
        "sev": v.get("severity", ""),
        "desc": [i.get("description", "") for i in items],
        "pos": [(round(i["pos"]["x"] * scale, 2), round(i["pos"]["y"] * scale, 2)) for i in items if "pos" in i],
    }


def _key(v: dict) -> str:
    return v["type"] + "|" + "|".join(sorted(v["desc"]))


_NET = re.compile(r"\[([^\]]+)\]")


def _added(before: list[dict], after: list[dict]) -> list[dict]:
    """Violations in `after` that `before` lacks. Unconnected items are compared as counts per net,
    because DRC re-picks which pair of items it names for a missing connection on every run."""
    def split(vs):
        keyed, unc = {}, {}
        for v in vs:
            if v["type"] == "unconnected_items":
                m = _NET.search(v["desc"][0]) if v["desc"] else None
                unc.setdefault(m.group(1) if m else "?", []).append(v)
            else:
                keyed.setdefault(_key(v), []).append(v)
        return keyed, unc

    bk, bu = split(before)
    ak, au = split(after)
    out = []
    for k, lst in ak.items():
        out += lst[len(bk.get(k, [])):]
    for n, lst in au.items():
        out += lst[len(bu.get(n, [])):]
    return out


def _drc(board: str) -> list[dict]:
    out = Path(tempfile.mkdtemp()) / "drc.json"
    subprocess.run([str(KICAD_CLI), "pcb", "drc", "--format", "json", "--severity-all", "--refill-zones",
                    "--units", "mm", "-o", str(out), board], capture_output=True, text=True, timeout=600)
    d = json.loads(out.read_text(encoding="utf-8"))
    return [_norm(v) for v in d.get("violations", []) + d.get("unconnected_items", []) + d.get("schematic_parity", [])]


def _erc(sch: str) -> list[dict]:
    out = Path(tempfile.mkdtemp()) / "erc.json"
    subprocess.run([str(KICAD_CLI), "sch", "erc", "--format", "json", "--severity-all", "--units", "mm",
                    "-o", str(out), sch], capture_output=True, text=True, timeout=600)
    d = json.loads(out.read_text(encoding="utf-8"))
    vs = d.get("violations", [])
    for sheet in d.get("sheets", []):
        vs += sheet.get("violations", [])
    # kicad-cli 10.0.5 labels ERC positions "mm" but writes them divided by 100
    return [_norm(v, scale=100.0) for v in vs]


def _summarize(vs, prev_key, bbox, types, exclude_types, refs, severity, max_items, only_new):
    cache = CACHE / (hashlib.sha1(prev_key.encode()).hexdigest() + ".json")
    prev = json.loads(cache.read_text()) if cache.exists() else None
    cache.write_text(json.dumps(vs))
    total = len(vs)
    if only_new:
        if prev is None:
            return _dump({"note": "no previous run to diff against; this run is now the baseline", "total": total})
        vs = _added(prev, vs)
    ref_res = [re.compile(rf"\b{re.escape(r).replace(r'\*', r'\w*')}\b") for r in refs or []]

    def keep(v):
        if types and v["type"] not in types:
            return False
        if exclude_types and v["type"] in exclude_types:
            return False
        if severity and v["sev"] != severity:
            return False
        if bbox and not any(bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3] for x, y in v["pos"]):
            return False
        if ref_res and not any(rx.search(d) for rx in ref_res for d in v["desc"]):
            return False
        return True

    sel = [v for v in vs if keep(v)]
    counts: dict[str, int] = {}
    for v in sel:
        counts[v["type"]] = counts.get(v["type"], 0) + 1
    items = [f"{v['type']}: " + " || ".join(v["desc"]) + (f" @{v['pos'][0]}" if v["pos"] else "") for v in sel[:max_items]]
    return _dump({"total_in_report": total, "matched": len(sel), "counts": counts, "items": items})


@mcp.tool()
def drc_summary(board: str = PCB, bbox: list[float] | None = None, types: list[str] | None = None,
                exclude_types: list[str] | None = None, refs: list[str] | None = None,
                severity: str | None = None, max_items: int = 15, only_new: bool = False) -> str:
    """Run DRC (zones refilled, file not saved) and return counts by type plus at most max_items lines.

    Filters: bbox [x0,y0,x1,y1] in mm (any item position inside), types / exclude_types
    (e.g. ["silk_overlap","silk_over_copper"]), refs (designators, * allowed, e.g. ["R6*","U5"]),
    severity ("error"|"warning"). only_new=True keeps only violations absent from the previous
    drc_summary run on this board, which is the quick way to see what an edit broke."""
    return _summarize(_drc(board), "drc:" + board, bbox, types, exclude_types, refs, severity, max_items, only_new)


@mcp.tool()
def erc_summary(schematic: str = SCH, types: list[str] | None = None, exclude_types: list[str] | None = None,
                refs: list[str] | None = None, severity: str | None = None, max_items: int = 15,
                only_new: bool = False) -> str:
    """Run ERC and return counts by type plus at most max_items lines. Same filters as drc_summary."""
    return _summarize(_erc(schematic), "erc:" + schematic, None, types, exclude_types, refs, severity, max_items, only_new)


# --- board edits / queries ----------------------------------------------------------------
@mcp.tool()
def pcb_apply(ops: list[dict], board: str = PCB, dry_run: bool = False, check: bool = False,
              refill: bool = True, force: bool = False) -> str:
    """Apply many board edits in one save (mm, board coordinates, nets by NAME). Nothing is saved
    unless every op succeeds; a backup of the previous board is kept as <board>.batch-bak.

    ops (each a dict with "op"):
      track {net, layer, pts:[[x,y],...], w=0.2}      via {net, at:[x,y], size=0.6, drill=0.3}
      move {ref, at:[x,y], rot?}                      field {ref, key, value}
      ref_text {ref, at?, rot?, hide?}                edge_poly {pts, width=0.05, closed=true}
      zone {net, layer, pts, priority=0, clearance=0.3, min_width=0.25, thermal_gap=0.3, spoke=0.4}
      merge_zones {net, layer}                        zone_priority {net, layer, priority}
      delete_vias {at:[[x,y],...] | bbox, net?, tol=0.02}
      delete_tracks {bbox?, net?, layer?}  (segments fully inside bbox)
      delete_shapes {layer, bbox?, shape?} (e.g. layer "Edge.Cuts", shape "rect")

    dry_run=True validates without saving. check=True applies to a temporary copy and returns
    only the DRC violations the edit adds, without touching the board."""
    if not (dry_run or check) and (refusal := _guard(force)):
        return refusal
    job = {"board": board, "mode": "apply", "ops": ops, "refill": refill}
    if dry_run and not check:
        return _dump(_worker({**job, "save": False}))
    if check:
        # The scratch copy sits beside the board so the project's rules and library tables
        # (${KIPRJMOD}/...) resolve exactly as they do for the real board.
        src = Path(board)
        stem = src.stem + ".kb-check"
        made = []
        try:
            for ext in (".kicad_pro", ".kicad_dru", ".kicad_pcb"):
                if src.with_suffix(ext).exists():
                    dst = src.with_name(stem + ext)
                    shutil.copy(src.with_suffix(ext), dst)
                    made.append(dst)
            copy = src.with_name(stem + ".kicad_pcb")
            res = _worker({**job, "board": str(copy), "save": True})
            if not res.get("saved"):
                return _dump(res)
            added = _added(_drc(board), _drc(str(copy)))
            res["new_violations"] = len(added)
            res["new"] = [f"{v['type']}: " + " || ".join(v["desc"]) + (f" @{v['pos'][0]}" if v["pos"] else "") for v in added[:20]]
            res["saved"] = False
            return _dump(res)
        finally:
            for p in made + [src.with_name(stem + ".kicad_prl")]:
                p.unlink(missing_ok=True)
    shutil.copy(board, board + ".batch-bak")
    return _dump(_worker({**job, "save": True}))


@mcp.tool()
def pcb_query(kinds: list[str], board: str = PCB, bbox: list[float] | None = None,
              nets: list[str] | None = None, refs: list[str] | None = None, layers: list[str] | None = None,
              exclude_unconnected: bool = True, max_items: int = 200) -> str:
    """Filtered board data as compact tables ({cols, rows, total}).

    kinds: any of footprints, pads, tracks, vias, nets, zones, outline. Filters: bbox [x0,y0,x1,y1] mm,
    nets / refs as glob patterns (e.g. ["/AI*","GND"], ["R6?","U5"]), layers (e.g. ["B.Cu"]).
    'unconnected-*' nets are skipped unless exclude_unconnected=False."""
    return _dump(_worker({"board": board, "mode": "query", "query": {
        "kinds": kinds, "bbox": bbox, "nets": nets, "refs": refs, "layers": layers,
        "exclude_unconnected": exclude_unconnected, "max_items": max_items}}))


@mcp.tool()
def render(bbox: list[float] | None = None, layers: list[str] | None = None, board: str = PCB,
           width_px: int = 800) -> Image:
    """PNG of a board region (bbox [x0,y0,x1,y1] mm, default the whole outline). Keep width_px small
    (400-900): image cost grows with pixels. Default layers F.Cu, B.Cu, Edge.Cuts, F.Silkscreen."""
    import pymupdf

    layers = layers or ["F.Cu", "B.Cu", "Edge.Cuts", "F.Silkscreen"]
    if bbox is None:
        o = _worker({"board": board, "mode": "query", "query": {"kinds": ["outline"]}})["outline"]
        bbox = [o[0] - 1, o[1] - 1, o[2] + 1, o[3] + 1]
    pdf = Path(tempfile.mkdtemp()) / "board.pdf"
    subprocess.run([str(KICAD_CLI), "pcb", "export", "pdf", "--mode-single", "-l", ",".join(layers),
                    "-o", str(pdf), board], capture_output=True, text=True, timeout=300)
    k = 72 / 25.4
    page = pymupdf.open(pdf)[0]
    clip = pymupdf.Rect(bbox[0] * k, bbox[1] * k, bbox[2] * k, bbox[3] * k)
    zoom = min(width_px, 1600) / clip.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
    return Image(data=pix.tobytes("png"), format="png")


# --- batch over mcp-server-kicad ----------------------------------------------------------
_TOOLS: dict | None = None


def _tools() -> dict:
    global _TOOLS
    if _TOOLS is None:
        from mcp_server_kicad import footprint, pcb, project, schematic, symbol

        _TOOLS = {}
        for mod in (schematic, pcb, symbol, footprint, project):
            for name, tool in mod.mcp._tool_manager._tools.items():
                fn = getattr(mod, name, None)
                if callable(fn):
                    ro = bool(getattr(getattr(tool, "annotations", None), "readOnlyHint", False))
                    _TOOLS[name] = (fn, ro)
    return _TOOLS


@mcp.tool()
def batch(calls: list[dict], stop_on_error: bool = True, result_chars: int = 0, force: bool = False) -> str:
    """Run many mcp-server-kicad tool calls in one round trip, in order.

    calls: [{"tool": "set_component_property", "args": {"reference": "R1", "key": "LCSC", "value": "C21190"}}, ...]
    Any mcp-server-kicad tool name works (place_component, add_power_symbol, wire_pins_to_net, add_wires,
    move_footprint, ...); args are that tool's parameters. Returns ok/failed counts and errors; set
    result_chars > 0 to also get each call's result cut to that length."""
    tools = _tools()
    unknown = sorted({c.get("tool") for c in calls if c.get("tool") not in tools})
    if unknown:
        return _dump({"refused": f"unknown tools {unknown}", "hint": "use mcp-server-kicad tool names"})
    if any(not tools[c["tool"]][1] for c in calls) and (refusal := _guard(force)):
        return refusal
    ok, failed, results = 0, [], []
    for i, c in enumerate(calls):
        fn, _ = tools[c["tool"]]
        try:
            r = fn(**c.get("args", {}))
            ok += 1
            if result_chars:
                results.append(_dump(r)[:result_chars])
        except Exception as e:
            failed.append({"i": i, "tool": c["tool"], "error": str(e)[:300]})
            if stop_on_error:
                break
    out = {"ok": ok, "failed": failed, "not_run": len(calls) - ok - len(failed)}
    if result_chars:
        out["results"] = results
    return _dump(out)


if __name__ == "__main__":
    mcp.run(transport="stdio")
