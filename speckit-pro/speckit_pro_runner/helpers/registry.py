"""Explicit registry for runner-owned read-only helper operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..envelope import diagnostic, response
from .install import run_install_helper
from .mutation import run_mutation_helper
from .pr_emission import run_pr_emission_helper
from .promotion import promotion_record
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


@dataclass(frozen=True)
class MutationEntry:
    helper_id: str
    operation: str
    modes: tuple[str, ...]
    script: str | None
    promotion_status: str
    comparison_mode: str
    authoritative_command: str
    fixture_ids: tuple[str, ...] = ()
    bash_reference_ids: tuple[str, ...] = ()
    rollback: str = "Disable the helper registry entry before active cutover."

    def as_record(self) -> dict[str, Any]:
        return {
            "helper_id": self.helper_id,
            "operation": self.operation,
            "mode": "mutation",
            "modes": list(self.modes),
            "script": self.script,
            "promotion_status": self.promotion_status,
            "comparison_mode": self.comparison_mode,
            "authoritative_command": self.authoritative_command,
            "promotion": promotion_record(
                self.helper_id,
                promotion_status=self.promotion_status,
                fixture_ids=list(self.fixture_ids),
                bash_reference_ids=list(self.bash_reference_ids),
                rollback=self.rollback,
            ),
        }


SCRIPT_BASE = "speckit-pro/skills/speckit-autopilot/scripts"
REQUEST_FIXTURE_BASE = "tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests"
MUTATION_REQUEST_FIXTURE_BASE = "tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/requests"


def authoritative_request(helper_id: str) -> str:
    return f"python -m speckit_pro_runner < {REQUEST_FIXTURE_BASE}/{helper_id}.json"


def mutation_authoritative_request(helper_id: str) -> str:
    return f"python -m speckit_pro_runner < {MUTATION_REQUEST_FIXTURE_BASE}/{helper_id}.json"


def deferred_authoritative_request() -> str:
    return ""


HELPERS: dict[str, HelperEntry] = {
    "helper-registry-dispatch": HelperEntry(
        "helper-registry-dispatch",
        "helper-registry-dispatch",
        None,
        "python_authoritative",
        "registry_metadata",
        authoritative_request("helper-registry-dispatch"),
    ),
    "check-prerequisites": HelperEntry(
        "check-prerequisites",
        "check-prerequisites",
        f"{SCRIPT_BASE}/check-prerequisites.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("check-prerequisites"),
    ),
    "detect-commands": HelperEntry(
        "detect-commands",
        "detect-commands",
        f"{SCRIPT_BASE}/detect-commands.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("detect-commands"),
    ),
    "detect-presets": HelperEntry(
        "detect-presets",
        "detect-presets",
        f"{SCRIPT_BASE}/detect-presets.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("detect-presets"),
    ),
    "count-markers": HelperEntry(
        "count-markers",
        "count-markers",
        f"{SCRIPT_BASE}/count-markers.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("count-markers"),
    ),
    "validate-gate": HelperEntry(
        "validate-gate",
        "validate-gate",
        f"{SCRIPT_BASE}/validate-gate.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("validate-gate"),
    ),
    "reviewability-gate": HelperEntry(
        "reviewability-gate",
        "reviewability-gate",
        f"{SCRIPT_BASE}/reviewability-gate.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("reviewability-gate"),
    ),
    "estimate-reviewable-loc": HelperEntry(
        "estimate-reviewable-loc",
        "estimate-reviewable-loc",
        f"{SCRIPT_BASE}/estimate-reviewable-loc.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("estimate-reviewable-loc"),
    ),
    "resolve-confidence-mode": HelperEntry(
        "resolve-confidence-mode",
        "resolve-confidence-mode",
        f"{SCRIPT_BASE}/resolve-confidence-mode.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("resolve-confidence-mode"),
    ),
    "confidence-gate": HelperEntry(
        "confidence-gate",
        "confidence-gate",
        f"{SCRIPT_BASE}/confidence-gate.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("confidence-gate"),
    ),
    "generate-spec-index-check": HelperEntry(
        "generate-spec-index-check",
        "generate-spec-index-check",
        f"{SCRIPT_BASE}/generate-spec-index.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("generate-spec-index-check"),
        ("write", "regenerate"),
    ),
    "o5-topology": HelperEntry(
        "o5-topology",
        "o5-topology",
        f"{SCRIPT_BASE}/o5-topology.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("o5-topology"),
    ),
    "atomicity-route": HelperEntry(
        "atomicity-route",
        "atomicity-route",
        f"{SCRIPT_BASE}/atomicity-route.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("atomicity-route"),
        ("mutation-routing",),
    ),
    "plan-layers-feature-dir": HelperEntry(
        "plan-layers-feature-dir",
        "plan-layers-feature-dir",
        f"{SCRIPT_BASE}/plan-layers.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("plan-layers-feature-dir"),
        ("marker-plan",),
    ),
    "validate-pr-workflow-contract": HelperEntry(
        "validate-pr-workflow-contract",
        "validate-pr-workflow-contract",
        f"{SCRIPT_BASE}/validate-pr-workflow-contract.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("validate-pr-workflow-contract"),
        ("workflow-event-write",),
    ),
    "validate-pr-packet-read-only": HelperEntry(
        "validate-pr-packet-read-only",
        "validate-pr-packet-read-only",
        f"{SCRIPT_BASE}/validate-pr-packet.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("validate-pr-packet-read-only"),
        ("persistence", "workflow-event-upserts", "pr-body-generation", "pr-emission", "restack"),
    ),
}


MUTATION_HELPERS: dict[str, MutationEntry] = {
    "mutation-registry-dispatch": MutationEntry(
        "mutation-registry-dispatch",
        "mutation-registry-dispatch",
        ("read_only",),
        None,
        "golden_only",
        "registry_metadata",
        mutation_authoritative_request("mutation-registry-dispatch"),
        ("registry",),
    ),
    "mutation-foundation": MutationEntry(
        "mutation-foundation",
        "mutation-foundation",
        ("dry_run", "apply"),
        None,
        "golden_only",
        "fixture_semantic",
        mutation_authoritative_request("mutation-foundation"),
        ("dry-run-write", "apply-write", "dirty-worktree", "path-escape", "partial-failure"),
    ),
    "doctor-preflight": MutationEntry(
        "doctor-preflight",
        "doctor-preflight",
        ("read_only",),
        None,
        "golden_only",
        "fixture_semantic",
        mutation_authoritative_request("doctor-preflight"),
        ("complete-install", "missing-files", "safe-repair"),
    ),
    "doctor-repair": MutationEntry(
        "doctor-repair",
        "doctor-repair",
        ("dry_run", "apply"),
        None,
        "golden_only",
        "fixture_semantic",
        mutation_authoritative_request("doctor-repair"),
        ("safe-repair", "real-home-refusal"),
    ),
    "install-health-repair": MutationEntry(
        "install-health-repair",
        "install-health-repair",
        ("read_only",),
        None,
        "golden_only",
        "fixture_semantic",
        "python -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/requests/install-health-repair.json",
        ("trusted-missing", "trusted-stale", "unsafe-manual-remediation", "broad-reinstall-rejected"),
        rollback="Keep autoheal limited to checksum-backed fixture evidence until native install evidence is complete.",
    ),
    "install-codex-agents": MutationEntry(
        "install-codex-agents",
        "install-codex-agents",
        ("dry_run", "apply"),
        "speckit-pro/skills/speckit-scaffold-spec/scripts/install-codex-agents.sh",
        "deferred",
        "golden_fixture",
        deferred_authoritative_request(),
        rollback="Keep existing installer scripts authoritative until XPLAT-007/XPLAT-008.",
    ),
    "install-curated-set": MutationEntry(
        "install-curated-set",
        "install-curated-set",
        ("dry_run", "apply"),
        "speckit-pro/scripts/install-curated-set.sh",
        "deferred",
        "bash_reference",
        deferred_authoritative_request(),
        bash_reference_ids=("install-curated-set",),
        rollback="Keep install-curated-set.sh authoritative until install cutover.",
    ),
    "project-fixup-apply": MutationEntry(
        "project-fixup-apply",
        "project-fixup-apply",
        ("dry_run", "apply"),
        None,
        "deferred",
        "golden_fixture",
        deferred_authoritative_request(),
    ),
    "ensure-reviewability-preset": MutationEntry(
        "ensure-reviewability-preset",
        "ensure-reviewability-preset",
        ("dry_run", "apply"),
        None,
        "deferred",
        "golden_fixture",
        deferred_authoritative_request(),
    ),
    "generate-pr-body": MutationEntry(
        "generate-pr-body",
        "generate-pr-body",
        ("dry_run", "apply"),
        f"{SCRIPT_BASE}/generate-pr-body.sh",
        "golden_only",
        "golden_fixture",
        mutation_authoritative_request("generate-pr-body"),
        ("pr-body-apply",),
        ("generate-pr-body",),
        "Use generate-pr-body.sh until XPLAT-007 gate migration.",
    ),
    "generate-uat-skeleton": MutationEntry(
        "generate-uat-skeleton",
        "generate-uat-skeleton",
        ("dry_run", "apply"),
        f"{SCRIPT_BASE}/generate-uat-skeleton.sh",
        "deferred",
        "golden_fixture",
        deferred_authoritative_request(),
    ),
    "final-reviewability-backstop": MutationEntry(
        "final-reviewability-backstop",
        "final-reviewability-backstop",
        ("dry_run", "apply"),
        f"{SCRIPT_BASE}/final-reviewability-backstop.sh",
        "deferred",
        "golden_fixture",
        deferred_authoritative_request(),
    ),
    "pr-packet-output": MutationEntry(
        "pr-packet-output",
        "pr-packet-output",
        ("dry_run", "apply"),
        None,
        "deferred",
        "golden_fixture",
        deferred_authoritative_request(),
    ),
    "validate-pr-workflow-contract-write": MutationEntry(
        "validate-pr-workflow-contract-write",
        "validate-pr-workflow-contract-write",
        ("dry_run", "apply"),
        f"{SCRIPT_BASE}/validate-pr-workflow-contract.sh",
        "deferred",
        "golden_fixture",
        deferred_authoritative_request(),
    ),
    "multi-pr-emission": MutationEntry(
        "multi-pr-emission",
        "multi-pr-emission",
        ("dry_run", "apply"),
        f"{SCRIPT_BASE}/multi-pr-emission.sh",
        "golden_only",
        "command_plan",
        mutation_authoritative_request("multi-pr-emission"),
        ("fake-gh-command-capture",),
        rollback="Keep multi-pr-emission.sh authoritative for live PR work.",
    ),
    "restack": MutationEntry(
        "restack",
        "restack",
        ("dry_run", "apply"),
        f"{SCRIPT_BASE}/restack.sh",
        "deferred",
        "command_plan",
        deferred_authoritative_request(),
    ),
    "migrate-structure": MutationEntry(
        "migrate-structure",
        "migrate-structure",
        ("dry_run", "apply"),
        None,
        "deferred",
        "golden_fixture",
        deferred_authoritative_request(),
    ),
    "relocate-process-artifacts": MutationEntry(
        "relocate-process-artifacts",
        "relocate-process-artifacts",
        ("dry_run", "apply"),
        f"{SCRIPT_BASE}/relocate-process-artifacts.sh",
        "deferred",
        "json_semantic",
        deferred_authoritative_request(),
        bash_reference_ids=("relocate-process-artifacts",),
    ),
    "generate-spec-index-write": MutationEntry(
        "generate-spec-index-write",
        "generate-spec-index-write",
        ("dry_run", "apply"),
        f"{SCRIPT_BASE}/generate-spec-index.sh",
        "deferred",
        "golden_fixture",
        deferred_authoritative_request(),
    ),
    "plan-layers-marker-plan": MutationEntry(
        "plan-layers-marker-plan",
        "plan-layers-marker-plan",
        ("dry_run", "apply"),
        f"{SCRIPT_BASE}/plan-layers.sh",
        "deferred",
        "golden_fixture",
        deferred_authoritative_request(),
    ),
    "validate-pr-packet-write": MutationEntry(
        "validate-pr-packet-write",
        "validate-pr-packet-write",
        ("dry_run", "apply"),
        f"{SCRIPT_BASE}/validate-pr-packet.sh",
        "deferred",
        "golden_fixture",
        deferred_authoritative_request(),
    ),
    "detect-stack-manager-plan": MutationEntry(
        "detect-stack-manager-plan",
        "detect-stack-manager-plan",
        ("dry_run",),
        None,
        "out_of_scope",
        "command_plan",
        deferred_authoritative_request(),
    ),
}


def mutation_registry_report() -> dict[str, Any]:
    records = [entry.as_record() for entry in MUTATION_HELPERS.values()]
    return {
        "helper_count": len(records),
        "helpers": sorted(records, key=lambda record: record["helper_id"]),
        "mode": "mutation",
        "active_cutover": False,
        "mutation_modes_promoted": sorted(
            record["helper_id"]
            for record in records
            if record["promotion_status"] in {"golden_only", "bash_compared"}
        ),
    }


def dispatch_helper(request: Any) -> dict[str, Any]:
    entry = HELPERS.get(request.helper_id)
    if entry is None and request.helper_id in MUTATION_HELPERS:
        return dispatch_mutation_helper(MUTATION_HELPERS[request.helper_id], request)
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


def dispatch_mutation_helper(entry: MutationEntry, request: Any) -> dict[str, Any]:
    if request.operation != entry.operation:
        return response(
            "input_error",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "helper_operation_mismatch",
                    "helper operation does not match the registered mutation operation",
                    details={"helper_id": entry.helper_id, "operation": request.operation, "expected": entry.operation},
                    remediation_summary="Use the operation paired with the requested helper id.",
                    remediation_actions=[f"Set operation to {entry.operation}.", "Retry the request."],
                )
            ],
        )

    if request.mode not in entry.modes:
        return response(
            "input_error",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "unsupported_mode",
                    "helper mode is not registered for this mutation helper",
                    details={"helper_id": entry.helper_id, "mode": request.mode, "modes": list(entry.modes)},
                    remediation_summary="Use one of the helper's registered modes.",
                    remediation_actions=["Inspect mutation-registry-dispatch output.", "Retry with a supported mode."],
                )
            ],
        )

    if entry.helper_id == "mutation-registry-dispatch":
        return response("ok", request_id=request.request_id, data=mutation_registry_report())

    if entry.helper_id in {"doctor-preflight", "doctor-repair", "install-health-repair"}:
        return run_install_helper(entry, request)

    if entry.helper_id in {
        "generate-pr-body",
        "generate-uat-skeleton",
        "final-reviewability-backstop",
        "pr-packet-output",
        "validate-pr-workflow-contract-write",
        "multi-pr-emission",
        "restack",
        "relocate-process-artifacts",
        "generate-spec-index-write",
        "plan-layers-marker-plan",
        "validate-pr-packet-write",
        "detect-stack-manager-plan",
    }:
        return run_pr_emission_helper(entry, request)

    return run_mutation_helper(entry, request)
