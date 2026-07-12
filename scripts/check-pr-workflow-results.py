#!/usr/bin/env python3
"""Evaluate the PR Checks detect, test, and artifact sentinel results."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence


class WorkflowResultError(RuntimeError):
    """Raised when a required PR Checks dependency did not pass."""


def check_workflow_results(
    detect_result: str,
    test_result: str,
    artifact_result: str,
) -> str:
    if detect_result in {"failure", "cancelled"}:
        raise WorkflowResultError(
            f"Detect job did not succeed (result: {detect_result}). Workflow is broken."
        )
    if test_result not in {"success", "skipped"}:
        raise WorkflowResultError(
            f"Plugin tests failed or were cancelled (result: {test_result})."
        )
    if artifact_result not in {"success", "skipped"}:
        raise WorkflowResultError(
            f"Generated artifacts drift from source (result: {artifact_result})."
        )
    return (
        "Plugin tests passed or were skipped "
        f"(result: {test_result}); artifacts consistent (result: {artifact_result})."
    )


def main(argv: Sequence[str] | None = None) -> int:
    if argv:
        print("::error::check-pr-workflow-results.py does not accept arguments", file=sys.stderr)
        return 1
    try:
        message = check_workflow_results(
            os.environ.get("DETECT_RESULT", ""),
            os.environ.get("TEST_RESULT", ""),
            os.environ.get("ARTIFACT_RESULT", ""),
        )
    except WorkflowResultError as error:
        print(f"::error::{error}", file=sys.stderr)
        return 1
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
