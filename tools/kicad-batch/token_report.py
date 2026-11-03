"""Where did a Claude Code session spend its tokens? Per-tool call counts and result sizes.

Usage: python token_report.py [transcript.jsonl | project-dir] [--top N]
With a project dir (default: the newest under ~/.claude/projects) the newest transcript is used.
Compare two runs of the same task before and after a tool change: calls, turns and result KB
should all drop. Cache reads dominate cost in long sessions, so turns x context size matter most.
"""

import collections
import json
import sys
from pathlib import Path


def newest(path: Path) -> Path:
    files = sorted(path.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not files:
        sys.exit(f"no transcripts under {path}")
    return files[-1]


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 20
    target = Path(args[0]) if args else Path.home() / ".claude" / "projects"
    path = target if target.is_file() else newest(target)

    calls, res, arg = collections.Counter(), collections.Counter(), collections.Counter()
    names, usage, turns = {}, collections.Counter(), 0
    for line in path.open(encoding="utf-8"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        m = e.get("message") or {}
        if e.get("type") == "assistant":
            turns += 1
            for k, v in (m.get("usage") or {}).items():
                if isinstance(v, int):
                    usage[k] += v
        content = m.get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if b.get("type") == "tool_use":
                n = b["name"].replace("mcp__", "").replace("__", ":")
                names[b["id"]] = n
                calls[n] += 1
                arg[n] += len(json.dumps(b.get("input")))
            elif b.get("type") == "tool_result":
                n = names.get(b.get("tool_use_id"), "?")
                c = b.get("content")
                res[n] += len(c) if isinstance(c, str) else len(json.dumps(c))

    print(path)
    print(f"assistant turns {turns}; " + ", ".join(f"{k} {v / 1e6:.2f}M" for k, v in usage.items() if v))
    print(f"\n{'tool':44}{'calls':>7}{'result KB':>11}{'args KB':>9}")
    for n, _ in sorted(calls.items(), key=lambda kv: -(res[kv[0]] + arg[kv[0]]))[:top]:
        print(f"{n:44}{calls[n]:7}{res[n] / 1e3:11.1f}{arg[n] / 1e3:9.1f}")
    print(f"\ntotal: {sum(calls.values())} calls, {sum(res.values()) / 1e3:.0f} KB results, {sum(arg.values()) / 1e3:.0f} KB args")


if __name__ == "__main__":
    main()
