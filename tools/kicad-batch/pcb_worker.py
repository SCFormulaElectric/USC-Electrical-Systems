"""Board-side half of kicad-batch. Runs under KiCad's bundled Python (it needs pcbnew).

Usage: python.exe -I pcb_worker.py job.json
The job is {"board": path, "mode": "apply" | "query", ...}; one JSON object is printed to stdout.
All coordinates are millimetres in board coordinates, nets are referred to by name (net numbers
shift on a KiCad 10 board after edits), and nothing is saved unless every op succeeded.
"""

import fnmatch
import json
import os
import sys

import pcbnew
from pcbnew import FromMM as mm
from pcbnew import ToMM

V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))  # noqa: E731
r3 = lambda v: round(ToMM(v), 3)  # noqa: E731


SHAPES = {"segment": pcbnew.SHAPE_T_SEGMENT, "rect": pcbnew.SHAPE_T_RECT, "arc": pcbnew.SHAPE_T_ARC,
          "circle": pcbnew.SHAPE_T_CIRCLE, "poly": pcbnew.SHAPE_T_POLY}


# Items removed from the board stay referenced here until the process exits. If their SWIG
# wrappers were garbage-collected, the C++ objects would be freed while the board still points at
# them, and later iteration, connectivity or the zone filler would crash.
GRAVE = []


def inside(bbox, x, y):
    return bbox is None or (bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3])


class Ops:
    def __init__(self, board):
        self.b = board
        self.fps = {f.GetReference(): f for f in board.GetFootprints()}
        self.created = []  # (item, requested net, label) for the net check after all ops

    def net(self, name):
        n = self.b.FindNet(name)
        if n is None:
            raise ValueError(f"no net named {name!r}")
        return n

    def layer(self, name):
        lid = self.b.GetLayerID(name)
        if lid < 0:
            raise ValueError(f"no layer named {name!r}")
        return lid

    def fp(self, ref):
        if ref not in self.fps:
            raise ValueError(f"no footprint {ref!r}")
        return self.fps[ref]

    # --- additions -------------------------------------------------------------------
    def track(self, net, layer, pts, w=0.2):
        n, lid = self.net(net), self.layer(layer)
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(V(x1, y1))
            t.SetEnd(V(x2, y2))
            t.SetWidth(mm(w))
            t.SetLayer(lid)
            t.SetNet(n)
            self.b.Add(t)
            self.created.append((t, net, f"track {layer} ({x1},{y1})-({x2},{y2})"))
        return len(pts) - 1

    def via(self, net, at, size=0.6, drill=0.3):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(V(*at))
        v.SetWidth(mm(size))
        v.SetDrill(mm(drill))
        v.SetNet(self.net(net))
        self.b.Add(v)
        self.created.append((v, net, f"via ({at[0]},{at[1]})"))
        return 1

    def edge_poly(self, pts, width=0.05, closed=True):
        pts = list(pts) + ([pts[0]] if closed else [])
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            s = pcbnew.PCB_SHAPE(self.b)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetLayer(pcbnew.Edge_Cuts)
            s.SetStart(V(x1, y1))
            s.SetEnd(V(x2, y2))
            s.SetWidth(mm(width))
            self.b.Add(s)
        return len(pts) - 1

    def zone(self, net, layer, pts, priority=0, clearance=0.3, min_width=0.25, thermal_gap=0.3, spoke=0.4):
        z = pcbnew.ZONE(self.b)
        z.SetLayer(self.layer(layer))
        z.SetNet(self.net(net))
        o = z.Outline()
        o.NewOutline()
        for x, y in pts:
            o.Append(mm(x), mm(y))
        z.SetAssignedPriority(priority)
        z.SetLocalClearance(mm(clearance))
        z.SetMinThickness(mm(min_width))
        z.SetThermalReliefGap(mm(thermal_gap))
        z.SetThermalReliefSpokeWidth(mm(spoke))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        self.b.Add(z)
        return 1

    # --- changes ---------------------------------------------------------------------
    def move(self, ref, at, rot=None):
        f = self.fp(ref)
        f.SetPosition(V(*at))
        if rot is not None:
            f.SetOrientationDegrees(rot)
        return 1

    def field(self, ref, key, value):
        f = self.fp(ref)
        if key == "Value":
            f.SetValue(value)
        elif key == "Reference":
            raise ValueError("rename parts in the schematic, not on the board")
        else:
            f.SetField(key, value)
        return 1

    def ref_text(self, ref, at=None, rot=None, hide=None):
        t = self.fp(ref).Reference()
        if rot is not None:
            t.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        if at is not None:
            t.SetPosition(V(*at))
        if hide is not None:
            t.SetVisible(not hide)
        return 1

    def merge_zones(self, net, layer):
        lid = self.layer(layer)
        zs = [z for z in self.b.Zones() if z.GetNetname() == net and z.GetLayer() == lid and not z.GetIsRuleArea()]
        if len(zs) < 2:
            raise ValueError(f"need 2+ {net} zones on {layer}, found {len(zs)}")
        keep = zs[0]
        for z in zs[1:]:
            keep.Outline().BooleanAdd(z.Outline())
            self.b.Remove(z)
            GRAVE.append(z)
        keep.Outline().Simplify()
        return len(zs) - 1

    def zone_priority(self, net, layer, priority):
        lid = self.layer(layer)
        zs = [z for z in self.b.Zones() if z.GetNetname() == net and z.GetLayer() == lid]
        if not zs:
            raise ValueError(f"no {net} zone on {layer}")
        for z in zs:
            z.SetAssignedPriority(priority)
        return len(zs)

    # --- deletions (each needs a filter, so a typo cannot wipe the board) -------------
    def delete_vias(self, at=None, bbox=None, net=None, tol=0.02):
        if at is None and bbox is None:
            raise ValueError("delete_vias needs at or bbox")
        hit = []
        for t in self.b.GetTracks():
            if not isinstance(t, pcbnew.PCB_VIA) or (net and t.GetNetname() != net):
                continue
            x, y = r3(t.GetPosition().x), r3(t.GetPosition().y)
            if at is not None and any(abs(x - ax) <= tol and abs(y - ay) <= tol for ax, ay in at):
                hit.append(t)
            elif at is None and inside(bbox, x, y):
                hit.append(t)
        for t in hit:
            self.b.Remove(t)
        GRAVE.extend(hit)
        return len(hit)

    def delete_tracks(self, bbox=None, net=None, layer=None):
        if bbox is None and net is None:
            raise ValueError("delete_tracks needs bbox or net")
        lid = self.layer(layer) if layer else None
        hit = []
        for t in self.b.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA) or (net and t.GetNetname() != net) or (lid is not None and t.GetLayer() != lid):
                continue
            s, e = t.GetStart(), t.GetEnd()
            if inside(bbox, r3(s.x), r3(s.y)) and inside(bbox, r3(e.x), r3(e.y)):
                hit.append(t)
        for t in hit:
            self.b.Remove(t)
        GRAVE.extend(hit)
        return len(hit)

    def delete_shapes(self, layer, bbox=None, shape=None):
        lid = self.layer(layer)
        hit = []
        for d in self.b.GetDrawings():
            if not isinstance(d, pcbnew.PCB_SHAPE) or d.GetLayer() != lid:
                continue
            if shape and d.GetShape() != SHAPES[shape.lower()]:
                continue
            bb = d.GetBoundingBox()
            if bbox is None or (inside(bbox, r3(bb.GetLeft()), r3(bb.GetTop())) and inside(bbox, r3(bb.GetRight()), r3(bb.GetBottom()))):
                hit.append(d)
        for d in hit:
            self.b.Remove(d)
        GRAVE.extend(hit)
        return len(hit)


def apply(job):
    b = pcbnew.LoadBoard(job["board"])
    ops = Ops(b)
    done, errors, counts = 0, [], {}
    for i, op in enumerate(job.get("ops", [])):
        op = dict(op)
        kind = op.pop("op", None)
        fn = getattr(ops, kind or "", None)
        if kind is None or kind.startswith("_") or not callable(fn) or kind in ("net", "layer", "fp"):
            errors.append(f"op {i}: unknown op {kind!r}")
            continue
        try:
            counts[kind] = counts.get(kind, 0) + fn(**op)
            done += 1
        except Exception as e:  # report every bad op, then refuse to save
            errors.append(f"op {i} ({kind}): {e}")
    if job.get("refill") and not errors:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    # KiCad's connectivity silently gives a new track or via the net of any other-net copper it
    # overlaps, which would hide a short. Rebuild it here and refuse the edit if any net moved.
    # (Refill first: a stale zone fill would otherwise claim items the new pour would avoid.)
    if ops.created and not errors:
        b.BuildConnectivity()
        for item, want, label in ops.created:
            if item.GetNetname() != want:
                hint = "" if job.get("refill") else " (zone fill may be stale; try refill=true)"
                errors.append(f"{label} touches copper of net {item.GetNetname()!r}, not {want!r}{hint}")
    saved = bool(job.get("save")) and not errors
    if saved:
        b.Save(job.get("save_as") or job["board"])
    return {"applied": done, "items": counts, "errors": errors[:20], "saved": saved}


def query(job):
    b = pcbnew.LoadBoard(job["board"])
    q = job.get("query", {})
    bbox, nets, refs, layers = q.get("bbox"), q.get("nets"), q.get("refs"), q.get("layers")
    skip_nc = q.get("exclude_unconnected", True)
    netok = lambda n: (not nets or any(fnmatch.fnmatchcase(n, p) for p in nets)) and not (skip_nc and n.startswith("unconnected-"))  # noqa: E731
    refok = lambda r: not refs or any(fnmatch.fnmatchcase(r, p) for p in refs)  # noqa: E731
    lay = lambda lid: b.GetLayerName(lid)  # noqa: E731
    layok = lambda name: not layers or name in layers  # noqa: E731
    out = {}
    for kind in q.get("kinds", ["footprints"]):
        rows = []
        if kind == "footprints":
            for f in b.GetFootprints():
                x, y = r3(f.GetPosition().x), r3(f.GetPosition().y)
                if refok(f.GetReference()) and inside(bbox, x, y):
                    rows.append([f.GetReference(), f.GetValue(), x, y, round(f.GetOrientationDegrees(), 2), "B" if f.IsFlipped() else "F"])
            out[kind] = {"cols": ["ref", "value", "x", "y", "rot", "side"], "rows": rows}
        elif kind == "pads":
            for f in b.GetFootprints():
                if not refok(f.GetReference()):
                    continue
                for p in f.Pads():
                    x, y = r3(p.GetPosition().x), r3(p.GetPosition().y)
                    if inside(bbox, x, y) and netok(p.GetNetname() or ""):
                        bb = p.GetBoundingBox()
                        rows.append([f.GetReference(), p.GetNumber(), p.GetNetname(), x, y, r3(bb.GetWidth()), r3(bb.GetHeight())])
            out[kind] = {"cols": ["ref", "pad", "net", "x", "y", "bbox_w", "bbox_h"], "rows": rows}
        elif kind in ("tracks", "vias"):
            for t in b.GetTracks():
                is_via = isinstance(t, pcbnew.PCB_VIA)
                if is_via != (kind == "vias") or not netok(t.GetNetname()):
                    continue
                if is_via:
                    x, y = r3(t.GetPosition().x), r3(t.GetPosition().y)
                    if inside(bbox, x, y):
                        rows.append([t.GetNetname(), x, y, r3(t.GetWidth(pcbnew.F_Cu)), r3(t.GetDrillValue())])
                else:
                    s, e, ln = t.GetStart(), t.GetEnd(), lay(t.GetLayer())
                    if layok(ln) and (inside(bbox, r3(s.x), r3(s.y)) or inside(bbox, r3(e.x), r3(e.y))):
                        rows.append([t.GetNetname(), ln, r3(t.GetWidth()), r3(s.x), r3(s.y), r3(e.x), r3(e.y)])
            out[kind] = {"cols": ["net", "x", "y", "size", "drill"] if kind == "vias" else ["net", "layer", "w", "x1", "y1", "x2", "y2"], "rows": rows}
        elif kind == "nets":
            pads = {}
            for p in b.GetPads():
                pads[p.GetNetname()] = pads.get(p.GetNetname(), 0) + 1
            for n in b.GetNetsByName().keys():
                n = str(n)
                if n and netok(n):
                    rows.append([n, pads.get(n, 0)])
            out[kind] = {"cols": ["net", "pads"], "rows": sorted(rows)}
        elif kind == "zones":
            for z in b.Zones():
                bb = z.GetBoundingBox()
                if netok(z.GetNetname()) and layok(lay(z.GetLayer())):
                    rows.append([z.GetNetname(), lay(z.GetLayer()), z.GetAssignedPriority(), r3(bb.GetLeft()), r3(bb.GetTop()), r3(bb.GetRight()), r3(bb.GetBottom())])
            out[kind] = {"cols": ["net", "layer", "priority", "x0", "y0", "x1", "y1"], "rows": rows}
        elif kind == "outline":
            bb = b.GetBoardEdgesBoundingBox()
            out[kind] = [r3(bb.GetLeft()), r3(bb.GetTop()), r3(bb.GetRight()), r3(bb.GetBottom())]
        else:
            out[kind] = f"unknown kind {kind!r}"
            continue
        if isinstance(out[kind], dict):
            limit = q.get("max_items", 200)
            out[kind]["total"] = len(rows)
            out[kind]["rows"] = out[kind]["rows"][:limit]
    return out


if __name__ == "__main__":
    job = json.load(open(sys.argv[1], encoding="utf-8"))
    res = apply(job) if job.get("mode") == "apply" else query(job)
    sys.stdout.write("@@RESULT@@" + json.dumps(res, separators=(",", ":")))
    sys.stdout.flush()
    # Skip interpreter teardown: freeing the SWIG wrappers of removed items (GRAVE) can crash
    # pcbnew after the work is done, and the result has already been written.
    os._exit(0)
