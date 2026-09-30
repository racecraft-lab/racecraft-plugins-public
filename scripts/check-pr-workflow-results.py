#!/usr/bin/env python3
"""Evaluate the PR Checks detect, test, artifact, and Go sentinel results."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import superseded_run as _superseded_run  # noqa: E402


class WorkflowResultError(RuntimeError):
    """Raised when a required PR Checks dependency did not pass."""


def check_workflow_results(
    detect_result: str,
    test_result: str,
    artifact_result: str,
    go_result: str,
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
    if go_result not in {"success", "skipped"}:
        raise WorkflowResultError(
            f"Go module checks failed or were cancelled (result: {go_result})."
        )
    return (
        "Plugin tests passed or were skipped "
        f"(result: {test_result}); artifacts consistent (result: {artifact_result}); "
        f"Go module checks passed or were skipped (result: {go_result})."
    )


def main(
    argv: Sequence[str] | None = None,
    superseded: Callable[[], str | None] = _superseded_run.superseded_notice,
) -> int:
    if argv:
        print("::error::check-pr-workflow-results.py does not accept arguments", file=sys.stderr)
        return 1
    results = [
        os.environ.get(name, "")
        for name in ("DETECT_RESULT", "TEST_RESULT", "ARTIFACT_RESULT", "GO_RESULT")
    ]
    try:
        message = check_workflow_results(*results)
    except WorkflowResultError as error:
        # A same-commit newer run reports the verdict; do not leave a red
        # context beside it. Anything short of proof keeps the failure.
        notice = superseded() if "cancelled" in results else None
        if notice is not None:
            print(f"::notice::{notice}")
            return 0
        print(f"::error::{error}", file=sys.stderr)
        return 1
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
