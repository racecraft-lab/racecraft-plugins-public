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
      "wall_seconds": 412.5,
      "review_findings": 2,
      "gate_iterations": 1
    }

Exit 0 with a report on any decision, including ``inconclusive``. Exit 1 on
malformed catalog or result input. Standard library only.
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


def load_catalog(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0" or not isinstance(data.get("cases"), list) or not data["cases"]:
        raise InputError("catalog must have schema_version 1.0 and a non-empty cases array")
    if set(data.get("modes", {})) != set(MODES):
        raise InputError(f"catalog modes must be exactly {', '.join(MODES)}")
    ids = [case.get("id") for case in data["cases"]]
    if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
        raise InputError("case ids must be unique non-empty strings")
    for case in data["cases"]:
        for field in ("language", "task", "files", "deltas"):
            if field not in case:
                raise InputError(f"case {case['id']}: missing {field}")
        delta_paths(case["deltas"])
    return data


def load_results(directory: Path, case_ids: set[str]) -> list[dict[str, Any]]:
    results = []
    for path in sorted(directory.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        missing = [f for f in REQUIRED_RESULT_FIELDS if f not in doc]
        if missing:
            raise InputError(f"{path.name}: missing {', '.join(missing)}")
        if doc["mode"] not in MODES:
            raise InputError(f"{path.name}: unknown mode {doc['mode']!r}")
        if doc["case_id"] not in case_ids:
            raise InputError(f"{path.name}: unknown case {doc['case_id']!r}")
        for metric in METRICS:
            value = doc[metric]
            if metric == "mutation_score" and value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise InputError(f"{path.name}: {metric} must be a number")
        results.append(doc)
    return results


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
        for (case_id, mode), row in per_case.items():
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
