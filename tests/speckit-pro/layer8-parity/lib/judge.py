#!/usr/bin/env python3
"""Deterministic Layer-8 parity judge.

The judge owns only local comparison arms. Prose-level semantic judgment is
left as an explicit skipped warning so Layer 8 never makes a live model call
from this utility.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


COMPARISON_ARMS = ("byte-identical", "exact", "tolerance-1")
SKIPPED_ARMS = ("semantic-equivalent",)
SUPPORTED_TOLERANCES = COMPARISON_ARMS + SKIPPED_ARMS


class ComparisonResult:
    """Structured result for one parity comparison."""

    def __init__(
        self,
        status: str,
        tolerance: str,
        reason: str,
        field: str = "field",
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.status = status
        self.tolerance = tolerance
        self.reason = reason
        self.field = field
        self.detail = detail

    @property
    def matched(self) -> bool:
        return self.status == "pass"

    @property
    def skipped(self) -> bool:
        return self.status == "skip"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "matched": self.matched,
            "skipped": self.skipped,
            "tolerance": self.tolerance,
            "field": self.field,
            "reason": self.reason,
        }
        if self.detail:
            payload["detail"] = self.detail
        return payload


def judge_values(value_a: str, value_b: str, tolerance: str, *, field: str = "field") -> ComparisonResult:
    """Compare two already-extracted values under ``tolerance``."""
    if tolerance == "byte-identical":
        if value_a.encode("utf-8") == value_b.encode("utf-8"):
            return ComparisonResult("pass", tolerance, "values are byte-identical", field)
        return ComparisonResult("fail", tolerance, "values differ at byte-identical tolerance", field)

    if tolerance == "exact":
        if value_a == value_b:
            return ComparisonResult("pass", tolerance, "values match exactly", field)
        return ComparisonResult("fail", tolerance, "exact tolerance failed; values differ", field)

    if tolerance == "tolerance-1":
        return _judge_tolerance_one(value_a, value_b, field)

    if tolerance == "semantic-equivalent":
        return ComparisonResult(
            "skip",
            tolerance,
            "semantic-equivalent comparison skipped; deterministic judge supports only local comparison arms",
            field,
        )

    raise ValueError(f"unknown tolerance type: {tolerance}")


def judge_files(path_a: str | Path, path_b: str | Path, tolerance: str, *, field: str = "field") -> ComparisonResult:
    """Compare two files under ``tolerance``."""
    file_a = Path(path_a)
    file_b = Path(path_b)
    if not file_a.is_file() or not file_b.is_file():
        return ComparisonResult(
            "fail",
            tolerance,
            "missing artifact on one or both paths",
            field,
            {"path_a": file_a.as_posix(), "path_b": file_b.as_posix()},
        )

    if tolerance == "byte-identical":
        data_a = file_a.read_bytes()
        data_b = file_b.read_bytes()
        if data_a == data_b:
            return ComparisonResult("pass", tolerance, "files are byte-identical", field)
        return ComparisonResult(
            "fail",
            tolerance,
            "byte-identical tolerance failed; files differ",
            field,
            {"bytes_a": len(data_a), "bytes_b": len(data_b)},
        )

    value_a = file_a.read_text(encoding="utf-8")
    value_b = file_b.read_text(encoding="utf-8")
    return judge_values(value_a, value_b, tolerance, field=field)


def _judge_tolerance_one(value_a: str, value_b: str, field: str) -> ComparisonResult:
    left = value_a.strip()
    right = value_b.strip()
    try:
        number_a = int(left)
        number_b = int(right)
    except ValueError:
        return ComparisonResult(
            "fail",
            "tolerance-1",
            "tolerance-1 requires numeric values",
            field,
            {"value_a": left, "value_b": right},
        )

    diff = abs(number_a - number_b)
    status = "pass" if diff <= 1 else "fail"
    reason = f"numeric difference is {diff}"
    return ComparisonResult(
        status,
        "tolerance-1",
        reason,
        field,
        {"value_a": number_a, "value_b": number_b, "difference": diff},
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare two Layer-8 parity values or files.")
    parser.add_argument("tolerance", choices=SUPPORTED_TOLERANCES)
    parser.add_argument("value_a_file")
    parser.add_argument("value_b_file")
    parser.add_argument("--field", default="field")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = judge_files(args.value_a_file, args.value_b_file, args.tolerance, field=args.field)
    except UnicodeDecodeError as exc:
        result = ComparisonResult("fail", args.tolerance, f"failed to decode input as UTF-8: {exc}", args.field)
    except ValueError as exc:
        print(f"judge: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), sort_keys=True))
    if result.status == "skip":
        print(f"WARNING: {result.reason}", file=sys.stderr)
        return 0
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
