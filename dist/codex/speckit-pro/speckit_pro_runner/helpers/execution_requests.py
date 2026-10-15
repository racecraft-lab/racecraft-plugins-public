"""Runner envelope adapters shared by mutation helpers: execution-control and its siblings, and repository-contained requests."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any, NamedTuple

from ..autopilot_state import mirror_execution_result
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
    warnings: list[dict[str, Any]] = []
    if entry.helper_id == "execution-control" and request.mode == "apply":
        # The ledger change is already durable; a state-mirror failure must not hide it or its run_id.
        try:
            mirror_execution_result(root, inputs["workflow_file"], result)
        except (ValueError, OSError, TypeError) as exc:
            warnings.append(diagnostic("state_mirror_not_refreshed", str(exc), severity="warning",
                                       remediation_summary="Repair autopilot-state.json, then refresh it with action=status mode=apply.",
                                       remediation_actions=["Keep the applied result; repair autopilot-state.json, then "
                                                            "call execution-control action=status mode=apply."]))
    # A deferral refuses the dispatch, so it is an expected failure just like a checkpoint.
    failed = (result.get("helper_exit_code") == 1 if entry.helper_id == "task-results"
              else result.get("disposition") in {"checkpoint_required", "defer"})
    status = "expected_failure" if failed else "ok"
    result.update(helper_id=entry.helper_id, operation=entry.operation, mode=request.mode,
                  promotion_status=entry.promotion_status)
    return response(status, request_id=request.request_id, data=result, diagnostics=warnings)


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
