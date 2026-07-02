"""Explicit registry for runner-owned read-only helper operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..envelope import diagnostic, response
from .read_only import registry_report, run_registered_helper


@dataclass(frozen=True)
class HelperEntry:
    helper_id: str
    operation: str
    script: str | None
    promotion_status: str
    comparison_mode: str
    authoritative_command: str
    out_of_scope_modes: tuple[str, ...] = ()

    def as_record(self) -> dict[str, Any]:
        return {
            "helper_id": self.helper_id,
            "operation": self.operation,
            "mode": "read_only",
            "script": self.script,
            "promotion_status": self.promotion_status,
            "comparison_mode": self.comparison_mode,
            "authoritative_command": self.authoritative_command,
            "out_of_scope_modes": list(self.out_of_scope_modes),
        }


SCRIPT_BASE = "speckit-pro/skills/speckit-autopilot/scripts"


HELPERS: dict[str, HelperEntry] = {
    "helper-registry-dispatch": HelperEntry(
        "helper-registry-dispatch",
        "helper-registry-dispatch",
        None,
        "python_authoritative",
        "registry_metadata",
        "python -m speckit_pro_runner < helper-registry-dispatch.json",
    ),
    "check-prerequisites": HelperEntry(
        "check-prerequisites",
        "check-prerequisites",
        f"{SCRIPT_BASE}/check-prerequisites.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < check-prerequisites.json",
    ),
    "detect-commands": HelperEntry(
        "detect-commands",
        "detect-commands",
        f"{SCRIPT_BASE}/detect-commands.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < detect-commands.json",
    ),
    "detect-presets": HelperEntry(
        "detect-presets",
        "detect-presets",
        f"{SCRIPT_BASE}/detect-presets.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < detect-presets.json",
    ),
    "count-markers": HelperEntry(
        "count-markers",
        "count-markers",
        f"{SCRIPT_BASE}/count-markers.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < count-markers.json",
    ),
    "validate-gate": HelperEntry(
        "validate-gate",
        "validate-gate",
        f"{SCRIPT_BASE}/validate-gate.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < validate-gate.json",
    ),
    "reviewability-gate": HelperEntry(
        "reviewability-gate",
        "reviewability-gate",
        f"{SCRIPT_BASE}/reviewability-gate.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < reviewability-gate.json",
    ),
    "estimate-reviewable-loc": HelperEntry(
        "estimate-reviewable-loc",
        "estimate-reviewable-loc",
        f"{SCRIPT_BASE}/estimate-reviewable-loc.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < estimate-reviewable-loc.json",
    ),
    "resolve-confidence-mode": HelperEntry(
        "resolve-confidence-mode",
        "resolve-confidence-mode",
        f"{SCRIPT_BASE}/resolve-confidence-mode.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < resolve-confidence-mode.json",
    ),
    "confidence-gate": HelperEntry(
        "confidence-gate",
        "confidence-gate",
        f"{SCRIPT_BASE}/confidence-gate.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < confidence-gate.json",
    ),
    "generate-spec-index-check": HelperEntry(
        "generate-spec-index-check",
        "generate-spec-index-check",
        f"{SCRIPT_BASE}/generate-spec-index.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < generate-spec-index-check.json",
        ("write", "regenerate"),
    ),
    "o5-topology": HelperEntry(
        "o5-topology",
        "o5-topology",
        f"{SCRIPT_BASE}/o5-topology.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < o5-topology.json",
    ),
    "atomicity-route": HelperEntry(
        "atomicity-route",
        "atomicity-route",
        f"{SCRIPT_BASE}/atomicity-route.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < atomicity-route.json",
        ("mutation-routing",),
    ),
    "plan-layers-feature-dir": HelperEntry(
        "plan-layers-feature-dir",
        "plan-layers-feature-dir",
        f"{SCRIPT_BASE}/plan-layers.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < plan-layers-feature-dir.json",
        ("marker-plan",),
    ),
    "validate-pr-workflow-contract": HelperEntry(
        "validate-pr-workflow-contract",
        "validate-pr-workflow-contract",
        f"{SCRIPT_BASE}/validate-pr-workflow-contract.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < validate-pr-workflow-contract.json",
        ("workflow-event-write",),
    ),
    "validate-pr-packet-read-only": HelperEntry(
        "validate-pr-packet-read-only",
        "validate-pr-packet-read-only",
        f"{SCRIPT_BASE}/validate-pr-packet.sh",
        "python_authoritative",
        "bash_reference",
        "python -m speckit_pro_runner < validate-pr-packet-read-only.json",
        ("persistence", "workflow-event-upsert", "pr-body-generation", "pr-emission", "restack"),
    ),
}


def dispatch_helper(request: Any) -> dict[str, Any]:
    entry = HELPERS.get(request.helper_id)
    if entry is None:
        return response(
            "input_error",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "unknown_helper",
                    "helper_id is not registered for runner read-only dispatch",
                    details={"helper_id": request.helper_id, "known_helpers": sorted(HELPERS)},
                    remediation_summary="Use a registered read-only helper id.",
                    remediation_actions=["Inspect helper-registry-dispatch output.", "Retry with a known helper_id and operation."],
                )
            ],
        )

    if request.operation != entry.operation:
        return response(
            "input_error",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "helper_operation_mismatch",
                    "helper operation does not match the registered read-only operation",
                    details={"helper_id": entry.helper_id, "operation": request.operation, "expected": entry.operation},
                    remediation_summary="Use the operation paired with the requested helper id.",
                    remediation_actions=[f"Set operation to {entry.operation}.", "Retry the request."],
                )
            ],
        )

    if request.mode != "read_only":
        return response(
            "input_error",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "unsupported_mode",
                    "only read_only helper mode is registered in the runner",
                    details={"helper_id": entry.helper_id, "mode": request.mode},
                    remediation_summary="Use read_only mode for runner helper dispatch.",
                    remediation_actions=["Remove mutation or write-mode requests.", "Retry with mode read_only."],
                )
            ],
        )

    if entry.helper_id == "helper-registry-dispatch":
        return response(
            "ok",
            request_id=request.request_id,
            data=registry_report(HELPERS),
        )

    return run_registered_helper(entry, request)
