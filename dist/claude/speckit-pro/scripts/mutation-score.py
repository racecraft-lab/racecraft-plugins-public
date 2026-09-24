#!/usr/bin/env python3
"""Mutation-score floor: read a StrykerJS JSON report and compare it to a floor.

StrykerJS fails a run only when the project's own ``thresholds.break`` is set;
its default is ``null``, which never fails, and the thresholds have no
command-line form. The MUTATION slot therefore chains this script after the
run so the floor from ``.specify/quality-gates.json`` is enforced the same way
on every project.

The report follows the mutation-testing-report-schema that Stryker's ``json``
reporter writes (default ``reports/mutation/mutation.json``). The score matches
mutation-testing-metrics: detected (Killed + Timeout) over valid (detected +
Survived + NoCoverage), times 100. Ignored, Pending, CompileError, and
RuntimeError mutants are not valid and do not count. The floor check uses the
exact ratio; the printed score is truncated to two decimals so it never shows
a failing score as reaching the floor.

Exit 0 when the score reaches the floor, 1 when it is below, 2 when the report
is missing, unreadable, malformed, or holds no valid mutants. A report with
nothing to score is never a pass. This script reads whatever file is at the
path; the chained ``&&`` only proves the mutation run before it exited 0.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

DEFAULT_REPORT = "reports/mutation/mutation.json"
DETECTED = frozenset({"Killed", "Timeout"})
UNDETECTED = frozenset({"Survived", "NoCoverage"})
NOT_VALID = frozenset({"Ignored", "Pending", "CompileError", "RuntimeError"})


class ReportError(Exception):
    """The report is missing or cannot be scored."""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", default=DEFAULT_REPORT, help=f"Stryker JSON report (default {DEFAULT_REPORT})")
    parser.add_argument("--floor", type=float, required=True, help="minimum mutation score in percent, 0 to 100")
    return parser.parse_args(argv)


def count(report: Any) -> tuple[int, int]:
    """Return (detected, valid) mutant counts for a parsed report."""
    files = report.get("files") if isinstance(report, dict) else None
    if not isinstance(files, dict):
        raise ReportError("report has no 'files' object")
    detected = valid = 0
    for name, entry in files.items():
        mutants = entry.get("mutants") if isinstance(entry, dict) else None
        if not isinstance(mutants, list):
            raise ReportError(f"files[{name!r}].mutants is not a list")
        for mutant in mutants:
            status = mutant.get("status") if isinstance(mutant, dict) else None
            if status in DETECTED:
                detected += 1
                valid += 1
            elif status in UNDETECTED:
                valid += 1
            elif status not in NOT_VALID:
                raise ReportError(f"files[{name!r}] has a mutant with unknown status {status!r}")
    return detected, valid


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not math.isfinite(args.floor) or not 0 <= args.floor <= 100:
        print("mutation-score: --floor must be between 0 and 100", file=sys.stderr)
        return 2
    try:
        try:
            report = json.loads(Path(args.report).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ReportError(f"cannot read {args.report}: {exc}") from exc
        detected, valid = count(report)
        if valid == 0:
            raise ReportError(f"{args.report} holds no valid mutants to score")
    except ReportError as exc:
        print(f"mutation-score: {exc}; the mutation floor cannot pass without a scored report", file=sys.stderr)
        return 2
    score = Fraction(detected * 100, valid)
    shown = math.floor(score * 100) / 100
    summary = {"report": args.report, "floor": args.floor, "score": shown, "detected": detected, "valid": valid}
    print(json.dumps(summary, sort_keys=True))
    if score < Fraction(str(args.floor)):
        print(f"mutation-score: score {shown:g} is below the floor {args.floor:g} ({detected} of {valid} valid mutants detected)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
