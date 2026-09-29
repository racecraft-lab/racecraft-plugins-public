#!/usr/bin/env python3
"""Run the whole-repo ripwire scans once and slice the results by lane.

Writes audit/evidence/<scan>.txt (one XML element per line, absolute path
prefixes scrubbed) and audit/evidence/by-lane/<lane-id>.md. Requires ripwire on
PATH and audit/lanes.json (run scope.py first). Run from any directory.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parent
EV = AUDIT / "evidence"

SCANS = {
    "doc-drift": ["--doc-drift", "--detail=1"],
    "clones": ["--clones", "--limit=2000"],
    "churn-decay": ["--rank-by=churn-decay", "--top-k=500"],
    "arch": ["--arch=.ripwire_arch_rules"],
    "deps": ["--deps"],
    "report": ["--report"],
    "partition": ["--pack-task=coherence and cohesion audit of the speckit-pro plugin: skills, runner, agents, tests, docs", "--partition=8"],
    "plan-lanes": ["--plan-lanes=8", "--task=coherence and cohesion audit of the speckit-pro plugin"],
}
FULL_BLOCK = {"group"}  # clone groups are useful only whole
TOKEN = re.compile(r"[A-Za-z0-9_@\[\]().+~-][A-Za-z0-9_@\[\]().+~/-]*")
OPEN = re.compile(r"^<([a-z-]+)\b[^>]*[^/]>$")


def scrub(text: str) -> str:
    text = text.replace(str(ROOT) + "/", "").replace(str(ROOT), ".")
    if re.search(r"/(Users|home|private|var/folders)/", text):
        sys.exit("absolute path survived scrubbing")
    return text


def run_scan(name: str, args: list[str]) -> str:
    p = subprocess.run(["ripwire", ".", *args], cwd=ROOT, capture_output=True, text=True)
    if p.returncode not in (0,):
        sys.exit(f"scan {name} failed (exit {p.returncode}): {p.stderr.strip()[:300]}")
    return scrub(p.stdout).replace("><", ">\n<")


def paths_in(line: str) -> set[str]:
    out = set()
    for tok in TOKEN.findall(line):
        tok = re.sub(r":\d+(-\d+)?$", "", tok)
        out.add(tok[2:] if tok.startswith("./") else tok)
    return out


def slice_lines(lines: list[str], files: set[str]) -> list[str]:
    out, i = [], 0
    while i < len(lines):
        m = OPEN.match(lines[i])
        if m and any(l == f"</{m.group(1)}>" for l in lines[i + 1:i + 400]):
            tag, j = m.group(1), i + 1
            while j < len(lines) and lines[j] != f"</{tag}>":
                j += 1
            block = lines[i + 1:j]
            hits = [l for l in block if paths_in(l) & files]
            if tag in FULL_BLOCK and hits:
                out += [lines[i], *block, lines[j]]
            elif hits or paths_in(lines[i]) & files:
                out += [lines[i], *(hits or []), lines[j]]
            i = j + 1
            continue
        if not lines[i].startswith(("<!--", "<m ")) and paths_in(lines[i]) & files:
            out.append(lines[i])
        i += 1
    return out


def main() -> None:
    lanes = json.loads((AUDIT / "lanes.json").read_text())
    EV.mkdir(exist_ok=True)
    (EV / "by-lane").mkdir(exist_ok=True)
    texts = {}
    for name, args in SCANS.items():
        texts[name] = run_scan(name, args)
        (EV / f"{name}.txt").write_text(texts[name] if texts[name].endswith("\n") else texts[name] + "\n")
        print(f"{name}: {len(texts[name].splitlines())} lines")
    for lane in lanes:
        files = set(lane["files"])
        parts = [f"# Evidence for lane `{lane['id']}` ({lane['file_count']} files)\n",
                 "Lines from the whole-repo scans that mention this lane's files. Empty section = none found, not none exists.\n"]
        for name in ("doc-drift", "clones", "churn-decay", "arch", "deps"):
            hit = slice_lines(texts[name].splitlines(), files)
            parts.append(f"\n## {name} ({len(hit)} lines)\n\n```xml\n" + "\n".join(hit) + "\n```\n")
        (EV / "by-lane" / f"{lane['id']}.md").write_text("".join(parts))


if __name__ == "__main__":
    main()
