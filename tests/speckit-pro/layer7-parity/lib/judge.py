#!/usr/bin/env python3
"""Deterministic Layer-7 parity judge.

The judge owns only local comparison arms for already-extracted values;
the runner compares whole files itself. Prose-level semantic judgment is
left as an explicit skipped warning so Layer 7 never makes a live model call
from this utility.
"""

from __future__ import annotations

from typing import Any


COMPARISON_ARMS = ("exact", "tolerance-1")
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


def judge_values(value_a: str, value_b: str, tolerance: str, *, field: str = "field") -> ComparisonResult:
    """Compare two already-extracted values under ``tolerance``."""
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
