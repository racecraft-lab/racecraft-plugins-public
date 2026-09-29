#!/usr/bin/env python3
"""Fail unless every ledger row carries a verdict recorded by its owning lane.

A verdict is the string "clean" or a non-empty list of finding IDs, and the row
must also record `verdict_lane` equal to the row's `lane`. Exit 0 only when all
rows pass and the ledger matches lanes.json. Any unreadable or malformed input
fails closed.
Usage: python3 audit/coverage_check.py [--ledger PATH] [--lanes PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AUDIT = Path(__file__).resolve().parent


def load(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        print(f"FAIL: cannot read {path.name}: {exc}", file=sys.stderr)
        sys.exit(2)


def valid_verdict(v) -> bool:
    if v == "clean":
        return True
    return isinstance(v, list) and bool(v) and all(isinstance(x, str) and x for x in v)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", type=Path, default=AUDIT / "ledger.json")
    ap.add_argument("--lanes", type=Path, default=AUDIT / "lanes.json")
    args = ap.parse_args()

    rows, lanes = load(args.ledger), load(args.lanes)
    if not isinstance(rows, list) or not rows or not isinstance(lanes, list) or not lanes:
        print("FAIL: ledger or lanes is empty or not a list", file=sys.stderr)
        return 2
    owner = {}
    for lane in lanes:
        for f in lane.get("files", []):
            if f in owner:
                print(f"FAIL: {f} appears in lanes {owner[f]} and {lane.get('id')}", file=sys.stderr)
                return 2
            owner[f] = lane.get("id")

    problems, seen = [], set()
    for r in rows:
        path, lane = r.get("path"), r.get("lane")
        seen.add(path)
        if owner.get(path) != lane:
            problems.append(f"MISOWNED  {path}: ledger lane {lane!r}, lanes.json lane {owner.get(path)!r}")
        elif not valid_verdict(r.get("verdict")):
            problems.append(f"MISSING   {path} [{lane}]: no verdict")
        elif r.get("verdict_lane") != lane:
            problems.append(f"MISOWNED  {path} [{lane}]: verdict recorded by {r.get('verdict_lane')!r}")
    for f in sorted(set(owner) - seen):
        problems.append(f"NOROW     {f}: in lanes.json but not in ledger")

    if problems:
        print("\n".join(problems))
        print(f"coverage FAIL: {len(problems)} of {len(rows)} rows unreviewed or mis-owned", file=sys.stderr)
        return 1
    print(f"coverage OK: {len(rows)} rows, all reviewed by their owning lane")
    return 0


if __name__ == "__main__":
    sys.exit(main())
