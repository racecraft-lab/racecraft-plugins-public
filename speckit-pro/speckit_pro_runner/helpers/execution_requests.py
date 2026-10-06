"""Runner envelope adapters shared by mutation helpers: execution-control and its siblings, and repository-contained requests."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any, NamedTuple

from ..envelope import diagnostic, response
from ..execution_control import execution_control
from ..task_results import task_results
from ..trusted_io import canonicalize_inputs, resolve_repo_root, validate_bounded_inputs
from ..verification_records import execute_verification
from .run_finalization import finalize_run


def run_execution_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Existing runner envelope adapter; apply remains a host-authorized action."""
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    error = validate_bounded_inputs(entry.helper_id, request.inputs, root)
    if error:
        return response("input_error", request_id=request.request_id, diagnostics=[error])
    inputs = canonicalize_inputs(entry.helper_id, request.inputs, root)
    try:
        handlers: dict[str, Callable[[Path, dict[str, Any], str], dict[str, Any]]] = {
            "execution-control": partial(execution_control, finalizer=finalize_run),
            "execute-verification": execute_verification, "task-results": task_results}
        result = handlers[entry.helper_id](root, inputs, request.mode)
    except (ValueError, OSError, TypeError) as exc:
        return response("input_error", request_id=request.request_id,
                        diagnostics=[diagnostic("invalid_execution_request", str(exc))])
    # A deferral refuses the dispatch, so it is an expected failure just like a checkpoint.
    failed = (result.get("helper_exit_code") == 1 if entry.helper_id == "task-results"
              else result.get("disposition") in {"checkpoint_required", "defer"})
    status = "expected_failure" if failed else "ok"
    result.update(helper_id=entry.helper_id, operation=entry.operation, mode=request.mode,
                  promotion_status=entry.promotion_status)
    return response(status, request_id=request.request_id, data=result)


class Refusal(NamedTuple):
    """How a helper explains a request it refuses: a diagnostic code, a summary and up to three actions."""

    code: str
    summary: str
    actions: list[str]


def run_contained_helper(entry: Any, request: Any, work: Callable[[Path, dict[str, Any], str], dict[str, Any]],
                         refusal: Refusal) -> dict[str, Any]:
    """Resolve the repository root and run `work` on it; a refused request is an input error, with nothing written."""
    try:
        root = resolve_repo_root(request.inputs)
        if isinstance(root, dict):
            return response("input_error", request_id=request.request_id, diagnostics=[root])
        data = work(root, request.inputs, request.mode)
    except (ValueError, OSError) as error:
        explained = diagnostic(refusal.code, str(error), remediation_summary=refusal.summary,
                               remediation_actions=refusal.actions)
        return response("input_error", request_id=request.request_id, diagnostics=[explained])
    identity = {"helper_id": entry.helper_id, "operation": entry.operation, "mode": request.mode}
    return response("ok", request_id=request.request_id, data={**data, **identity})
