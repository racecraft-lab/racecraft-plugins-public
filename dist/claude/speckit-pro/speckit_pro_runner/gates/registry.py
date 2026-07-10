"""Explicit registry for planned XPLAT-007 gate operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..envelope import diagnostic, response
from .payloads import run_payload_gate
from .release import run_release_gate
from .suite import run_suite_gate
from .active_path_guard import run_active_path_guard
from ..helpers.install import run_runner_invocation_gate


REQUEST_BASE = "tests/speckit-pro/unit/fixtures/runner-gates/requests"
XPLAT_008_REQUEST_BASE = "tests/speckit-pro/unit/fixtures/installed-plugin-release/requests"


@dataclass(frozen=True)
class GateOperation:
    helper_id: str
    operation: str
    group: str
    modes: tuple[str, ...]
    module: str
    prior_gate: str | None
    request_fixture: str
    story: str
    active_role: str
    implemented: bool = False
    promotion_status: str = "planned"

    def as_record(self) -> dict[str, Any]:
        return {
            "helper_id": self.helper_id,
            "operation": self.operation,
            "group": self.group,
            "modes": list(self.modes),
            "module": self.module,
            "prior_gate": self.prior_gate,
            "request_fixture": self.request_fixture,
            "story": self.story,
            "active_role": self.active_role,
            "implemented": self.implemented,
            "promotion_status": self.promotion_status,
        }


def request_fixture(name: str) -> str:
    return f"{REQUEST_BASE}/{name}.json"


def xplat_008_request_fixture(name: str) -> str:
    return f"{XPLAT_008_REQUEST_BASE}/{name}.json"


GATE_OPERATIONS: tuple[GateOperation, ...] = (
    GateOperation(
        "runner-invocation",
        "runner-invocation",
        "runtime",
        ("read_only",),
        "speckit_pro_runner.helpers.install",
        None,
        xplat_008_request_fixture("runner-invocation"),
        "US1",
        "active_installed_runtime",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "suite-gate",
        "run-default-suite",
        "suite",
        ("read_only",),
        "speckit_pro_runner.gates.suite",
        "tests/speckit-pro/run-all.sh",
        request_fixture("run-default-suite"),
        "US1",
        "active_test_gate",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "suite-gate",
        "run-layer",
        "suite",
        ("read_only",),
        "speckit_pro_runner.gates.suite",
        "tests/speckit-pro/run-all.sh --layer",
        request_fixture("run-layer"),
        "US1",
        "active_test_gate",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "suite-gate",
        "run-toolchain-preflight",
        "suite",
        ("read_only",),
        "speckit_pro_runner.gates.suite",
        "tests/speckit-pro/check-toolchain.sh",
        request_fixture("run-toolchain-preflight"),
        "US1",
        "active_test_gate",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "suite-gate",
        "run-ai-evals",
        "suite",
        ("read_only",),
        "speckit_pro_runner.gates.suite",
        "tests/speckit-pro/layer2-trigger/run-trigger-evals.sh",
        request_fixture("run-ai-evals"),
        "US1",
        "active_eval_gate",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "suite-gate",
        "run-integration-suite",
        "suite",
        ("read_only",),
        "speckit_pro_runner.gates.suite",
        "tests/speckit-pro/layer7-integration/run-all-fixtures.sh",
        request_fixture("run-integration-suite"),
        "US1",
        "active_test_gate",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "suite-gate",
        "run-parity-suite",
        "suite",
        ("read_only",),
        "speckit_pro_runner.gates.suite",
        "tests/speckit-pro/layer8-parity/run-parity-fixtures.sh",
        request_fixture("run-parity-suite"),
        "US1",
        "active_test_gate",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "payload-gate",
        "payload-completeness",
        "payload",
        ("read_only", "dry_run", "apply"),
        "speckit_pro_runner.gates.payloads",
        "scripts/build-plugin-payloads.py",
        xplat_008_request_fixture("payload-completeness"),
        "US2",
        "active_payload_gate",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "payload-gate",
        "build-test-payload-evidence",
        "payload",
        ("read_only", "dry_run", "apply"),
        "speckit_pro_runner.gates.payloads",
        "scripts/build-plugin-payloads.py",
        request_fixture("test-payload-evidence"),
        "US2",
        "active_payload_gate",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "install-verification",
        "refresh-local-plugin-fixture",
        "install",
        ("read_only", "dry_run"),
        "speckit_pro_runner.gates.payloads",
        "scripts/refresh-local-plugin.sh",
        request_fixture("install-verification"),
        "US2",
        "active_install_verification",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "install-verification",
        "verify-install",
        "install",
        ("read_only",),
        "speckit_pro_runner.gates.payloads",
        "scripts/refresh-local-plugin.sh",
        request_fixture("install-verification"),
        "US2",
        "active_install_verification",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "release-readiness",
        "release-readiness-xplat008",
        "release",
        ("read_only",),
        "speckit_pro_runner.gates.release",
        ".github/workflows/release.yml",
        xplat_008_request_fixture("release-readiness"),
        "US2",
        "active_release_readiness",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "release-readiness",
        "uat-matrix",
        "release",
        ("read_only",),
        "speckit_pro_runner.gates.release",
        None,
        xplat_008_request_fixture("uat-matrix"),
        "US4",
        "active_uat_release_gate",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "release-readiness",
        "detect-changed-plugin",
        "release",
        ("read_only",),
        "speckit_pro_runner.gates.release",
        ".github/workflows/pr-checks.yml",
        request_fixture("release-readiness"),
        "US2",
        "active_release_readiness",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "release-readiness",
        "aggregate-suite-results",
        "release",
        ("read_only",),
        "speckit_pro_runner.gates.release",
        ".github/workflows/pr-checks.yml",
        request_fixture("release-readiness"),
        "US2",
        "active_release_readiness",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "release-readiness",
        "check-marketplace-version-sync",
        "release",
        ("read_only",),
        "speckit_pro_runner.gates.release",
        "scripts/sync-marketplace-versions.sh",
        request_fixture("release-readiness"),
        "US2",
        "active_release_readiness",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "release-readiness",
        "validate-pr-title",
        "release",
        ("read_only",),
        "speckit_pro_runner.gates.release",
        ".github/workflows/pr-checks.yml",
        request_fixture("release-readiness"),
        "US2",
        "active_release_readiness",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "release-readiness",
        "validate-workflow-contract",
        "release",
        ("read_only",),
        "speckit_pro_runner.gates.release",
        ".github/workflows/pr-checks.yml",
        request_fixture("release-readiness"),
        "US2",
        "active_release_readiness",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "release-readiness",
        "check-payload-evidence",
        "release",
        ("read_only",),
        "speckit_pro_runner.gates.release",
        ".github/workflows/release.yml",
        request_fixture("release-readiness"),
        "US2",
        "active_release_readiness",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "release-readiness",
        "parse-release-pr-payload-sync",
        "release",
        ("read_only",),
        "speckit_pro_runner.gates.release",
        ".github/workflows/release.yml",
        request_fixture("release-readiness"),
        "US2",
        "active_release_readiness",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "release-readiness",
        "check-post-release-drift",
        "release",
        ("read_only",),
        "speckit_pro_runner.gates.release",
        ".github/workflows/release.yml",
        request_fixture("release-readiness"),
        "US2",
        "active_release_readiness",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "release-readiness",
        "release-readiness",
        "release",
        ("read_only",),
        "speckit_pro_runner.gates.release",
        ".github/workflows/release.yml",
        request_fixture("release-readiness"),
        "US2",
        "active_release_readiness",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "active-path-guard",
        "active-path-guard",
        "guard",
        ("read_only",),
        "speckit_pro_runner.gates.active_path_guard",
        None,
        request_fixture("classify-shell-finding"),
        "US3",
        "active_repo_helper",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "active-path-guard",
        "active-runtime-guard",
        "guard",
        ("read_only",),
        "speckit_pro_runner.gates.active_path_guard",
        None,
        xplat_008_request_fixture("active-runtime-guard"),
        "US1",
        "active_installed_runtime_guard",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "active-path-guard",
        "zero-bash-guard",
        "guard",
        ("read_only",),
        "speckit_pro_runner.gates.active_path_guard",
        None,
        "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/requests/zero-bash-guard.json",
        "US3",
        "active_zero_bash_guard",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "active-path-guard",
        "repo-bash-confinement",
        "guard",
        ("read_only",),
        "speckit_pro_runner.gates.active_path_guard",
        None,
        "tests/speckit-pro/unit/fixtures/repository-bash-confinement/requests/repo-bash-confinement.json",
        "US3",
        "active_repo_bash_confinement",
        implemented=True,
        promotion_status="python_authoritative",
    ),
    GateOperation(
        "active-path-guard",
        "classify-shell-finding",
        "guard",
        ("read_only",),
        "speckit_pro_runner.gates.active_path_guard",
        None,
        request_fixture("active-path-guard"),
        "US3",
        "active_repo_helper",
        implemented=True,
        promotion_status="python_authoritative",
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


def gate_registry_report() -> dict[str, Any]:
    groups = sorted({entry.group for entry in GATE_OPERATIONS})
    return {
        "schema_version": "1.0",
        "feature_id": "XPLAT-007+XPLAT-008+XPLAT-009+XPLAT-010",
        "promotion_status": "mixed",
        "active_cutover": False,
        "groups": groups,
        "gate_helper_ids": sorted(GATE_HELPER_IDS),
        "operation_count": len(GATE_OPERATIONS),
        "operations": [entry.as_record() for entry in sorted(GATE_OPERATIONS, key=lambda item: (item.group, item.operation))],
    }


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
            remediation_summary="Use a planned XPLAT-007 gate operation.",
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
                "story": entry.story,
                "promotion_status": entry.promotion_status,
            },
            remediation_summary="Implement the matching XPLAT-007 user-story task before executing this gate.",
            remediation_actions=["Keep existing Bash gates authoritative.", "Add the user-story fixture before enabling execution."],
            deferred_to=f"XPLAT-007 {entry.story}",
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
    promotion_record = "tests/speckit-pro/unit/fixtures/runner-gates/promotion-records.json"
    return {
        "gate": {
            "gate_id": gate_id,
            "operation": operation,
            "gate_status": "input_error",
            "promoted": False,
            "blocking": True,
            "comparison_ids": [],
            "promotion_record": promotion_record,
        },
        "artifacts": [
            {
                "path": promotion_record,
                "kind": "fixture",
            }
        ],
    }
