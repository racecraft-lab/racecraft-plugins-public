"""Explicit registry for runner gate operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..envelope import diagnostic, response
from .payloads import run_payload_gate
from .release import run_release_gate
from .suite import run_suite_gate
from .active_path_guard import run_active_path_guard
from ..helpers.install import run_runner_invocation_gate


INSTALLED_RELEASE_READINESS_OPERATION = "installed-release-readiness"


@dataclass(frozen=True)
class GateOperation:
    helper_id: str
    operation: str
    group: str
    modes: tuple[str, ...]
    implemented: bool = True


GATE_OPERATIONS: tuple[GateOperation, ...] = (
    GateOperation(
        "runner-invocation",
        "runner-invocation",
        "runtime",
        ("read_only",),
    ),
    GateOperation(
        "suite-gate",
        "run-default-suite",
        "suite",
        ("read_only",),
    ),
    GateOperation(
        "suite-gate",
        "run-layer",
        "suite",
        ("read_only",),
    ),
    GateOperation(
        "suite-gate",
        "run-toolchain-preflight",
        "suite",
        ("read_only",),
    ),
    GateOperation(
        "suite-gate",
        "run-integration-suite",
        "suite",
        ("read_only",),
    ),
    GateOperation(
        "suite-gate",
        "run-parity-suite",
        "suite",
        ("read_only",),
    ),
    GateOperation(
        "payload-gate",
        "payload-completeness",
        "payload",
        ("read_only", "dry_run", "apply"),
    ),
    GateOperation(
        "payload-gate",
        "build-test-payload-evidence",
        "payload",
        ("read_only", "dry_run", "apply"),
    ),
    GateOperation(
        "install-verification",
        "refresh-local-plugin-fixture",
        "install",
        ("read_only", "dry_run"),
    ),
    GateOperation(
        "install-verification",
        "verify-install",
        "install",
        ("read_only",),
    ),
    GateOperation(
        "release-readiness",
        INSTALLED_RELEASE_READINESS_OPERATION,
        "release",
        ("read_only",),
    ),
    GateOperation(
        "release-readiness",
        "validate-pr-title",
        "release",
        ("read_only",),
    ),
    GateOperation(
        "active-path-guard",
        "active-path-guard",
        "guard",
        ("read_only",),
    ),
    GateOperation(
        "active-path-guard",
        "active-runtime-guard",
        "guard",
        ("read_only",),
    ),
    GateOperation(
        "active-path-guard",
        "zero-bash-guard",
        "guard",
        ("read_only",),
    ),
    GateOperation(
        "active-path-guard",
        "repo-bash-confinement",
        "guard",
        ("read_only",),
    ),
    GateOperation(
        "active-path-guard",
        "classify-shell-finding",
        "guard",
        ("read_only",),
    ),
)

GATE_HELPER_IDS = frozenset(entry.helper_id for entry in GATE_OPERATIONS)
_OPERATIONS_BY_NAME = {entry.operation: entry for entry in GATE_OPERATIONS}
_OPERATIONS_BY_HELPER = {
    helper_id: tuple(entry for entry in GATE_OPERATIONS if entry.helper_id == helper_id)
    for helper_id in sorted(GATE_HELPER_IDS)
}


def all_gate_operations() -> tuple[GateOperation, ...]:
    return GATE_OPERATIONS


def is_gate_helper_id(helper_id: str) -> bool:
    return helper_id in GATE_HELPER_IDS


def dispatch_gate(request: Any) -> dict[str, Any]:
    entry = _OPERATIONS_BY_NAME.get(request.operation)
    if entry is None:
        return _gate_input_error(
            request,
            "unknown_gate_operation",
            "gate operation is not registered",
            details={
                "helper_id": request.helper_id,
                "operation": request.operation,
                "known_operations": _known_operations(request.helper_id),
            },
            remediation_summary="Use a registered runner gate operation.",
            remediation_actions=["Inspect the gate registry metadata.", "Retry with a known gate operation for this helper_id."],
        )

    if entry.helper_id != request.helper_id:
        return _gate_input_error(
            request,
            "gate_operation_mismatch",
            "gate operation is registered under a different helper id",
            entry=entry,
            details={
                "helper_id": request.helper_id,
                "operation": request.operation,
                "expected_helper_id": entry.helper_id,
            },
            remediation_summary="Use the helper_id paired with the requested gate operation.",
            remediation_actions=[f"Set helper_id to {entry.helper_id}.", "Retry the request."],
        )

    if request.mode not in entry.modes:
        return _gate_input_error(
            request,
            "unsupported_gate_mode",
            "gate operation does not support the requested mode",
            entry=entry,
            details={
                "helper_id": request.helper_id,
                "operation": request.operation,
                "mode": request.mode,
                "supported_modes": list(entry.modes),
            },
            remediation_summary="Use one of the modes declared by the gate registry.",
            remediation_actions=[f"Set mode to {entry.modes[0]}.", "Retry the request."],
        )

    if not entry.implemented:
        return _gate_input_error(
            request,
            "gate_operation_not_implemented",
            "gate operation is planned but not implemented in this foundation marker",
            entry=entry,
            details={
                "helper_id": entry.helper_id,
                "operation": entry.operation,
                "group": entry.group,
            },
            remediation_summary="Implement the requested runner gate before executing it.",
            remediation_actions=["Add the gate implementation.", "Retry the request after enabling the operation."],
        )

    if entry.group == "suite":
        return run_suite_gate(entry, request)
    if entry.group in {"payload", "install"}:
        return run_payload_gate(entry, request)
    if entry.group == "release":
        return run_release_gate(entry, request)
    if entry.group == "runtime":
        return run_runner_invocation_gate(entry, request)
    if entry.group == "guard":
        return run_active_path_guard(entry, request)

    return response("internal_failure", request_id=request.request_id)


def _known_operations(helper_id: str) -> list[str]:
    return sorted(entry.operation for entry in _OPERATIONS_BY_HELPER.get(helper_id, ()))


def _gate_input_error(
    request: Any,
    code: str,
    message: str,
    *,
    entry: GateOperation | None = None,
    details: dict[str, Any],
    remediation_summary: str,
    remediation_actions: list[str],
    deferred_to: str | None = None,
) -> dict[str, Any]:
    return response(
        "input_error",
        request_id=request.request_id,
        data=_gate_error_data(request, entry=entry),
        diagnostics=[
            diagnostic(
                code,
                message,
                details=details,
                remediation_summary=remediation_summary,
                remediation_actions=remediation_actions,
                deferred_to=deferred_to,
            )
        ],
    )


def _gate_error_data(request: Any, *, entry: GateOperation | None) -> dict[str, Any]:
    operation = entry.operation if entry is not None else request.operation
    gate_id = entry.helper_id if entry is not None and entry.helper_id == request.helper_id else request.helper_id
    return {
        "gate": {
            "gate_id": gate_id,
            "operation": operation,
            "gate_status": "input_error",
            "promoted": False,
            "blocking": True,
            "comparison_ids": [],
        },
    }
