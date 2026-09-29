#!/usr/bin/env python3
"""Score paired implement-executor mode runs.

Reads the frozen case catalog and a directory of run result documents, pairs
results by task across modes, and reports per-metric paired differences with
an exact sign test plus a verdict per candidate mode against ``strict``.

One result document per run, JSON, any file name under ``--results``::

    {
      "case_id": "queue-public-api",
      "mode": "strict",
      "seed": 1,
      "mutation_score": 74.0,      # 0-100, or null when the slot is unconfigured
      "wall_seconds": 412.5,       # non-negative
      "review_findings": 2,        # non-negative integer
      "gate_iterations": 1         # non-negative integer; seed is one too
    }

Exit 0 with a report on any decision (``beats``, ``loses`` or ``inconclusive``).
Exit 1 on malformed catalog or result input, including a result that is not a
JSON object and a repeated (case, mode, seed). A (case, mode) with fewer
distinct seeds than the catalog's ``repeats`` is listed under ``shortfalls`` and
printed, never scored silently. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

MODES = ("strict", "function_first", "boundary")
METRICS = {
    "mutation_score": "higher",
    "wall_seconds": "lower",
    "review_findings": "lower",
    "gate_iterations": "lower",
}
REQUIRED_RESULT_FIELDS = ("case_id", "mode", "seed", *METRICS)
DELTA_LINE_PREFIX = "- `"
NO_DELTAS = "No module or interface changes."


class InputError(ValueError):
    """The catalog or a result document cannot be trusted."""


def delta_paths(deltas: list[str]) -> list[str]:
    """Paths from ``new`` or ``changed`` delta lines; ``removed`` lines are ignored."""
    paths: list[str] = []
    for line in deltas:
        if line.strip() == NO_DELTAS:
            continue
        if not line.startswith(DELTA_LINE_PREFIX) or "` — [" not in line:
            raise InputError(f"unrecognised delta line: {line!r}")
        path, rest = line[len(DELTA_LINE_PREFIX):].split("` — [", 1)
        kind = rest.split(":", 1)[0].strip().lower()
        if kind in ("new", "changed"):
            paths.append(path.strip())
        elif kind != "removed":
            raise InputError(f"unrecognised delta kind {kind!r} in {line!r}")
    return paths


def is_boundary_task(files: list[str], deltas: list[str]) -> bool:
    """True when any task file equals or sits under a new/changed delta path."""
    targets = delta_paths(deltas)
    return any(f == t or f.startswith(t.rstrip("/") + "/") for f in files for t in targets)


def _check_catalog_shape(data: Any) -> None:
    if not isinstance(data, dict):
        raise InputError("catalog must be a JSON object")
    if data.get("schema_version") != "1.0" or not isinstance(data.get("cases"), list) or not data["cases"]:
        raise InputError("catalog must have schema_version 1.0 and a non-empty cases array")
    modes = data.get("modes")
    if not isinstance(modes, dict) or set(modes) != set(MODES):
        raise InputError(f"catalog modes must be an object keyed by exactly {', '.join(MODES)}")
    if not _is_count(data.get("repeats")) or data["repeats"] < 1:
        raise InputError("catalog repeats must be a positive integer")


def _check_case_fields(cases: list[Any]) -> None:
    if not all(isinstance(case, dict) for case in cases):
        raise InputError("every catalog case must be an object")
    ids = [case.get("id") for case in cases]
    if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
        raise InputError("case ids must be unique non-empty strings")
    for case in cases:
        for field in ("language", "task", "files", "deltas"):
            if field not in case:
                raise InputError(f"case {case['id']}: missing {field}")
        delta_paths(case["deltas"])


def load_catalog(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    _check_catalog_shape(data)
    _check_case_fields(data["cases"])
    return data


def _check_metric(name: str, metric: str, value: Any) -> None:
    if metric == "mutation_score" and value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{name}: {metric} must be a number")
    if metric == "mutation_score" and not 0 <= value <= 100:
        raise InputError(f"{name}: mutation_score must be between 0 and 100")
    if metric == "wall_seconds" and value < 0:
        raise InputError(f"{name}: wall_seconds must be non-negative")
    if metric in ("review_findings", "gate_iterations") and not _is_count(value):
        raise InputError(f"{name}: {metric} must be a non-negative integer")


def _check_result(name: str, doc: Any, case_ids: set[str]) -> None:
    if not isinstance(doc, dict):
        raise InputError(f"{name}: result must be a JSON object")
    missing = [f for f in REQUIRED_RESULT_FIELDS if f not in doc]
    if missing:
        raise InputError(f"{name}: missing {', '.join(missing)}")
    if doc["mode"] not in MODES:
        raise InputError(f"{name}: unknown mode {doc['mode']!r}")
    if doc["case_id"] not in case_ids:
        raise InputError(f"{name}: unknown case {doc['case_id']!r}")
    if not _is_count(doc["seed"]):
        raise InputError(f"{name}: seed must be a non-negative integer")
    for metric in METRICS:
        _check_metric(name, metric, doc[metric])


def load_results(directory: Path, case_ids: set[str]) -> list[dict[str, Any]]:
    results = []
    runs: set[tuple[str, str, int]] = set()
    for path in sorted(directory.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        _check_result(path.name, doc, case_ids)
        run = (doc["case_id"], doc["mode"], doc["seed"])
        if run in runs:
            raise InputError(f"{path.name}: duplicate run for case {run[0]!r}, mode {run[1]!r}, seed {run[2]}")
        runs.add(run)
        results.append(doc)
    return results


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def medians(results: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, float | None]]:
    """Median per (case, mode) per metric; a null mutation score stays null."""
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for doc in results:
        groups.setdefault((doc["case_id"], doc["mode"]), []).append(doc)
    out: dict[tuple[str, str], dict[str, float | None]] = {}
    for key, docs in groups.items():
        row: dict[str, float | None] = {}
        for metric in METRICS:
            values = [d[metric] for d in docs if d[metric] is not None]
            row[metric] = statistics.median(values) if values else None
        out[key] = row
    return out


def seed_shortfalls(catalog: dict[str, Any], results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each (case, mode) that ran fewer distinct seeds than the catalog's ``repeats``."""
    seeds: dict[tuple[str, str], set[int]] = {}
    for doc in results:
        seeds.setdefault((doc["case_id"], doc["mode"]), set()).add(doc["seed"])
    expected = catalog["repeats"]
    return [
        {"case_id": case["id"], "mode": mode, "expected": expected, "found": len(seeds.get((case["id"], mode), ()))}
        for case in catalog["cases"]
        for mode in MODES
        if len(seeds.get((case["id"], mode), ())) < expected
    ]


def sign_test_p(wins: int, losses: int) -> float | None:
    """Exact two-sided sign test; None when there are no non-tied pairs."""
    n = wins + losses
    if n == 0:
        return None
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def compare(
    per_case: dict[tuple[str, str], dict[str, float | None]],
    case_ids: list[str],
    candidate: str,
    baseline: str = "strict",
) -> dict[str, Any]:
    out: dict[str, Any] = {"candidate": candidate, "baseline": baseline, "metrics": {}}
    for metric, direction in METRICS.items():
        rows = []
        for case_id in case_ids:
            a = per_case.get((case_id, candidate), {}).get(metric)
            b = per_case.get((case_id, baseline), {}).get(metric)
            if a is None or b is None:
                continue
            diff = a - b
            better = diff > 0 if direction == "higher" else diff < 0
            rows.append({"case_id": case_id, "candidate": a, "baseline": b, "diff": diff,
                         "winner": candidate if better else (baseline if diff != 0 else "tie")})
        wins = sum(r["winner"] == candidate for r in rows)
        losses = sum(r["winner"] == baseline for r in rows)
        out["metrics"][metric] = {
            "pairs": len(rows),
            "median_diff": statistics.median(r["diff"] for r in rows) if rows else None,
            "wins": wins,
            "losses": losses,
            "p": sign_test_p(wins, losses),
            "rows": rows,
        }
    return out


def verdict(
    comparison: dict[str, Any],
    per_case: dict[tuple[str, str], dict[str, float | None]],
    *,
    alpha: float,
    mutation_tolerance: float,
    mutation_floor: float | None,
) -> str:
    m = comparison["metrics"]
    mutation = m["mutation_score"]
    if mutation["pairs"] and mutation["median_diff"] < -mutation_tolerance:
        return "loses"
    if mutation_floor is not None:
        for (_case_id, mode), row in per_case.items():
            if mode == comparison["candidate"] and row["mutation_score"] is not None and row["mutation_score"] < mutation_floor:
                return "loses"
    speed = [name for name in ("wall_seconds", "review_findings", "gate_iterations")]
    improved = [n for n in speed if m[n]["p"] is not None and m[n]["p"] <= alpha and m[n]["wins"] > m[n]["losses"]]
    worsened = [n for n in speed if m[n]["p"] is not None and m[n]["p"] <= alpha and m[n]["losses"] > m[n]["wins"]]
    if worsened:
        return "loses"
    if improved:
        return "beats"
    return "inconclusive"


def score(catalog: dict[str, Any], results: list[dict[str, Any]], *, alpha: float,
          mutation_tolerance: float, mutation_floor: float | None) -> dict[str, Any]:
    case_ids = [case["id"] for case in catalog["cases"]]
    classification = {case["id"]: ("boundary" if is_boundary_task(case["files"], case["deltas"]) else "inside")
                      for case in catalog["cases"]}
    per_case = medians(results)
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "alpha": alpha,
        "mutation_tolerance": mutation_tolerance,
        "mutation_floor": mutation_floor,
        "classification": classification,
        "runs": len(results),
        "shortfalls": seed_shortfalls(catalog, results),
        "comparisons": {},
        "verdicts": {},
    }
    for candidate in ("function_first", "boundary"):
        comparison = compare(per_case, case_ids, candidate)
        report["comparisons"][candidate] = comparison
        report["verdicts"][candidate] = verdict(
            comparison, per_case, alpha=alpha, mutation_tolerance=mutation_tolerance, mutation_floor=mutation_floor
        )
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalog", type=Path, default=Path(__file__).with_name("catalog.json"))
    parser.add_argument("--results", type=Path, required=True, help="directory of run result JSON documents")
    parser.add_argument("--report", type=Path, help="write the full JSON report here")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--mutation-tolerance", type=float, default=2.0)
    parser.add_argument("--mutation-floor", type=float, default=None,
                        help="repository mutation floor; a candidate with any case below it loses")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        catalog = load_catalog(args.catalog)
        results = load_results(args.results, {case["id"] for case in catalog["cases"]})
        report = score(catalog, results, alpha=args.alpha, mutation_tolerance=args.mutation_tolerance,
                       mutation_floor=args.mutation_floor)
    except (InputError, OSError, ValueError) as exc:
        print(f"score-executor-modes: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        args.report.write_text(text + "\n", encoding="utf-8")
    for candidate, result in report["verdicts"].items():
        print(f"{candidate} vs strict: {result}")
    for gap in report["shortfalls"]:
        print(f"shortfall: {gap['case_id']} {gap['mode']} has {gap['found']} of {gap['expected']} seeds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
