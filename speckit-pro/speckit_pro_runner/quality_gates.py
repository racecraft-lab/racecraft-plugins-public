"""Validate the repository quality-gate thresholds file and recommend values.

``.specify/quality-gates.json`` is the authority for the thresholds the
COMPLEXITY, MUTATION, and DEPENDENCY_RULES slots run against, and for
permanent repository-wide skips. The JSON schema in
``contracts/quality-gates.schema.json`` documents the shape; this module
enforces the same rules with the standard library only. The operator writes
the file through the speckit-coach quality-gates flow; agents never edit it.

Usage::

    python3 -m speckit_pro_runner.quality_gates validate [path]
    python3 -m speckit_pro_runner.quality_gates recommend <crap-score report.json>

``validate`` exits 0 when the file is valid, 1 with one violation per line on
stderr. ``recommend`` prints a thresholds file body whose complexity ceiling
lets about 90 percent of the measured functions pass, or Bob's six when the
report measured nothing.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
FILE_PATH = ".specify/quality-gates.json"
THRESHOLD_FIELDS = ("complexity", "crap", "mutation_score_floor")
SLOTS = ("COMPLEXITY", "MUTATION", "DEPENDENCY_RULES")
BASIS_METHODS = ("percentile-90", "bobs-six", "shipped-default", "operator")
BOBS_SIX = 6
PASS_FRACTION = 0.9
# What the shipped table used before this file existed; kept only so
# `recommend` can fill the non-measured thresholds.
SHIPPED_DEFAULTS = {"complexity": 8, "crap": 30, "mutation_score_floor": 60}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(data: Any) -> list[str]:
    """Return every violation in ``data``; an empty list means valid."""
    problems: list[str] = []
    if not isinstance(data, dict):
        return ["top level must be an object"]
    extra = sorted(set(data) - {"schema_version", "thresholds", "skips", "basis"})
    if extra:
        problems.append("unknown top-level keys: " + ", ".join(extra))
    if data.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version must be {SCHEMA_VERSION!r}")
    thresholds = data.get("thresholds")
    if not isinstance(thresholds, dict):
        problems.append("thresholds must be an object")
    else:
        missing = [field for field in THRESHOLD_FIELDS if field not in thresholds]
        unknown = sorted(set(thresholds) - set(THRESHOLD_FIELDS))
        if missing:
            problems.append("thresholds: missing fields: " + ", ".join(missing))
        if unknown:
            problems.append("thresholds: unknown fields: " + ", ".join(unknown))
        complexity = thresholds.get("complexity")
        if "complexity" in thresholds and (not _is_int(complexity) or complexity < 1):
            problems.append("thresholds.complexity: must be an integer >= 1")
        crap = thresholds.get("crap")
        if "crap" in thresholds and (not _is_number(crap) or crap <= 0):
            problems.append("thresholds.crap: must be a number > 0")
        floor = thresholds.get("mutation_score_floor")
        if "mutation_score_floor" in thresholds and (not _is_number(floor) or not 0 <= floor <= 100):
            problems.append("thresholds.mutation_score_floor: must be a number between 0 and 100")
    skips = data.get("skips")
    if "skips" in data:
        if not isinstance(skips, dict):
            problems.append("skips must be an object keyed by slot")
        else:
            for slot, entry in skips.items():
                if slot not in SLOTS:
                    problems.append(f"skips.{slot}: must be one of {', '.join(SLOTS)}")
                    continue
                if not isinstance(entry, dict):
                    problems.append(f"skips.{slot}: must be an object")
                    continue
                unknown = sorted(set(entry) - {"reason", "recorded"})
                if unknown:
                    problems.append(f"skips.{slot}: unknown fields: " + ", ".join(unknown))
                if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
                    problems.append(f"skips.{slot}.reason: must be a non-empty string")
                if "recorded" in entry and (not isinstance(entry["recorded"], str) or not entry["recorded"].strip()):
                    problems.append(f"skips.{slot}.recorded: must be a non-empty string")
    basis = data.get("basis")
    if "basis" in data:
        if not isinstance(basis, dict):
            problems.append("basis must be an object")
        else:
            unknown = sorted(set(basis) - {"method", "measured_functions", "recorded"})
            if unknown:
                problems.append("basis: unknown fields: " + ", ".join(unknown))
            if basis.get("method") not in BASIS_METHODS:
                problems.append(f"basis.method: must be one of {', '.join(BASIS_METHODS)}")
            measured = basis.get("measured_functions")
            if "measured_functions" in basis and (not _is_int(measured) or measured < 0):
                problems.append("basis.measured_functions: must be an integer >= 0")
    return problems


def substitutions(thresholds: dict[str, Any]) -> dict[str, str]:
    """Map validated thresholds onto the discovery-table placeholders."""
    floor = thresholds["mutation_score_floor"]
    return {
        "ceiling": _plain(thresholds["crap"]),
        "complexity_ceiling": str(int(thresholds["complexity"])),
        "floor": _plain(floor),
        "survival_ceiling": _plain(100 - floor),
    }


def recommend(report: Any) -> dict[str, Any]:
    """Build a thresholds file from a lenient ``crap-score.py --report``.

    The complexity ceiling is the smallest value at which at least 90 percent
    of the measured functions pass. With nothing measured it falls back to
    Bob's six, the coached no-code default.
    """
    functions = report.get("functions", []) if isinstance(report, dict) else []
    values = sorted(int(fn["complexity"]) for fn in functions if _is_int(fn.get("complexity")))
    if values:
        index = min(len(values) - 1, max(0, math.ceil(PASS_FRACTION * len(values)) - 1))
        complexity = max(1, values[index])
        basis = {"method": "percentile-90", "measured_functions": len(values)}
    else:
        complexity = BOBS_SIX
        basis = {"method": "bobs-six", "measured_functions": 0}
    return {
        "schema_version": SCHEMA_VERSION,
        "thresholds": {
            "complexity": complexity,
            "crap": SHIPPED_DEFAULTS["crap"],
            "mutation_score_floor": SHIPPED_DEFAULTS["mutation_score_floor"],
        },
        "basis": basis,
    }


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return _is_int(value) or (isinstance(value, float) and math.isfinite(value))


def _plain(value: Any) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    usage = "usage: python3 -m speckit_pro_runner.quality_gates validate [path] | recommend <report.json>"
    if not args or args[0] not in {"validate", "recommend"}:
        print(usage, file=sys.stderr)
        return 2
    if args[0] == "validate":
        if len(args) > 2:
            print(usage, file=sys.stderr)
            return 2
        path = Path(args[1]) if len(args) == 2 else Path(FILE_PATH)
        try:
            data = load(path)
        except (OSError, ValueError) as exc:
            print(f"cannot read {path}: {exc}", file=sys.stderr)
            return 1
        problems = validate(data)
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1 if problems else 0
    if len(args) != 2:
        print(usage, file=sys.stderr)
        return 2
    try:
        report = load(Path(args[1]))
    except (OSError, ValueError) as exc:
        print(f"cannot read report: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(recommend(report), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
