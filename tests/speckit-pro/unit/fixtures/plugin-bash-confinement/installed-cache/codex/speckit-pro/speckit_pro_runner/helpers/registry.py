"""Explicit registry for runner-owned read-only helper operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..envelope import diagnostic, response
from .install import CODEX_OPTIONAL_HELPER_NAME, CODEX_REQUIRED_AGENT_NAMES, run_install_helper
from .mutation import empty_mutation, run_mutation_helper, run_spec_index_write, run_sweep_apply_result
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
    mutation_operation: str | None = None
    mutation_operation_deferred: bool = False

    def as_record(self) -> dict[str, Any]:
        record = {
            "helper_id": self.helper_id,
            "operation": self.operation,
            "mode": "read_only",
            "python_operation": self.operation,
            "promotion_status": self.promotion_status,
            "comparison_mode": self.comparison_mode,
            "authoritative_command": self.authoritative_command,
            "out_of_scope_modes": list(self.out_of_scope_modes),
        }
        if self.script is not None:
            record["inactive_provenance"] = {"prior_script": self.script}
        return record


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
        record = {
            "helper_id": self.helper_id,
            "operation": self.operation,
            "mode": "mutation",
            "modes": list(self.modes),
            "python_operation": self.operation if self.authoritative_command else None,
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
        if self.script is not None:
            record["inactive_provenance"] = {"prior_script": self.script}
        return record


SCRIPT_BASE = "speckit-pro/skills/speckit-autopilot/scripts"
REQUEST_FIXTURE_BASE = "tests/speckit-pro/unit/fixtures/read-only-helpers/requests"
MUTATION_REQUEST_FIXTURE_BASE = "tests/speckit-pro/unit/fixtures/mutation-helpers/requests"
DISPATCHABLE_MUTATION_PROMOTION_STATUSES = frozenset({"golden_only", "bash_compared"})
CODEX_MANAGED_HELPER_PROVENANCE_KEYS = (
    "helper_name",
    "destination",
    "installer_id",
    "source_roster_id",
    "manifest_id",
    "destination_digest",
)


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
    "resolve-workflow-binding": HelperEntry(
        "resolve-workflow-binding",
        "resolve-workflow-binding",
        None,
        "python_authoritative",
        "python_contract",
        authoritative_request("resolve-workflow-binding"),
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
    "estimate-spec-size": HelperEntry(
        "estimate-spec-size",
        "estimate-spec-size",
        None,
        "python_authoritative",
        "bash_reference",
        authoritative_request("estimate-spec-size"),
    ),
    "resolve-confidence-mode": HelperEntry(
        "resolve-confidence-mode",
        "resolve-confidence-mode",
        f"{SCRIPT_BASE}/resolve-confidence-mode.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("resolve-confidence-mode"),
    ),
    # New behaviour with no deleted `.sh` predecessor, so there is no prior script
    # to record and no bash reference to compare against.
    "resolve-autopilot-stage": HelperEntry(
        "resolve-autopilot-stage",
        "resolve-autopilot-stage",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("resolve-autopilot-stage"),
    ),
    "sweep-pr-feedback": HelperEntry(
        "sweep-pr-feedback",
        "sweep-pr-feedback",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("sweep-pr-feedback"),
    ),
    "sweep-isolation-session": HelperEntry(
        "sweep-isolation-session",
        "sweep-isolation-session",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("sweep-isolation-session"),
    ),
    "check-artifact-freshness": HelperEntry(
        "check-artifact-freshness",
        "check-artifact-freshness",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("check-artifact-freshness"),
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
        mutation_operation="generate-spec-index-write",
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
        mutation_operation="plan-layers-marker-plan",
        mutation_operation_deferred=True,
    ),
    "validate-pr-workflow-contract": HelperEntry(
        "validate-pr-workflow-contract",
        "validate-pr-workflow-contract",
        f"{SCRIPT_BASE}/validate-pr-workflow-contract.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("validate-pr-workflow-contract"),
        ("workflow-event-write",),
        mutation_operation="validate-pr-workflow-contract-write",
        mutation_operation_deferred=True,
    ),
    "validate-pr-packet-read-only": HelperEntry(
        "validate-pr-packet-read-only",
        "validate-pr-packet-read-only",
        f"{SCRIPT_BASE}/validate-pr-packet.sh",
        "python_authoritative",
        "bash_reference",
        authoritative_request("validate-pr-packet-read-only"),
        ("workflow-event-upserts", "pr-body-generation", "pr-emission", "restack"),
        mutation_operation="validate-pr-packet-write",
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
    "sweep-apply-result": MutationEntry(
        "sweep-apply-result",
        "sweep-apply-result",
        ("dry_run", "apply"),
        None,
        "golden_only",
        "fixture_semantic",
        mutation_authoritative_request("sweep-apply-result"),
        ("receipt-gated-apply", "replay-refusal", "stale-head-refusal"),
        rollback="Restore the one touched artifact from the amendment commit before retrying.",
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
        "python -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/install-health-repair.json",
        ("trusted-missing", "trusted-stale", "unsafe-manual-remediation", "broad-reinstall-rejected"),
        rollback="Keep autoheal limited to checksum-backed fixture evidence until native install evidence is complete.",
    ),
    "install-codex-agents": MutationEntry(
        "install-codex-agents",
        "install-codex-agents",
        ("dry_run", "apply"),
        None,
        "golden_only",
        "golden_fixture",
        mutation_authoritative_request("install-codex-agents"),
        ("dry-run-refresh", "stale-overwrite", "no-op", "rollback", "invalid-source", "unsafe-destination"),
        bash_reference_ids=("install-codex-agents",),
        rollback="Retry in dry_run mode and preserve the previous same-named Codex agent files before applying again.",
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
        rollback="Keep install-curated-set deferred until a Python runner implementation is promoted.",
    ),
    "project-fixup-apply": MutationEntry(
        "project-fixup-apply",
        "project-fixup-apply",
        ("dry_run", "apply"),
        "speckit-pro/skills/speckit-coach/scripts/project-fixup.sh",
        "deferred",
        "golden_fixture",
        deferred_authoritative_request(),
    ),
    "ensure-reviewability-preset": MutationEntry(
        "ensure-reviewability-preset",
        "ensure-reviewability-preset",
        ("dry_run", "apply"),
        "speckit-pro/skills/speckit-coach/scripts/ensure-reviewability-preset.sh",
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
        "Retry the registered generate-pr-body operation in dry_run mode before applying again.",
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
        "golden_only",
        "golden_fixture",
        mutation_authoritative_request("pr-packet-output"),
        ("pr-packet-output-apply",),
        rollback="Retry the registered pr-packet-output operation in dry_run mode before applying again.",
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
        rollback="Keep live PR mutation deferred; use the registered multi-pr-emission operation only for command-plan capture.",
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
        f"{SCRIPT_BASE}/migrate-structure.sh",
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
        "golden_only",
        "golden_fixture",
        mutation_authoritative_request("generate-spec-index-write"),
        ("current", "stale", "error", "write", "idempotence", "marker-safety"),
        rollback="Restore touched SPEC-MOC.md and roadmap-MOC files from version control before retrying.",
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
        "golden_only",
        "golden_fixture",
        mutation_authoritative_request("validate-pr-packet-write"),
        ("validate-pr-packet-write-apply",),
        ("validate-pr-packet",),
        "Retry validate-pr-packet-write from a clean worktree; apply mode reruns read-only validation before persisting.",
    ),
    "detect-stack-manager-plan": MutationEntry(
        "detect-stack-manager-plan",
        "detect-stack-manager-plan",
        ("dry_run",),
        f"{SCRIPT_BASE}/detect-stack-manager.sh",
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
            if record["promotion_status"] in DISPATCHABLE_MUTATION_PROMOTION_STATUSES
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

    if entry.promotion_status not in DISPATCHABLE_MUTATION_PROMOTION_STATUSES:
        return blocked_promotion_response(entry, request)

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

    if entry.helper_id == "generate-spec-index-write":
        return run_spec_index_write(entry, request)

    if entry.helper_id == "sweep-apply-result":
        return run_sweep_apply_result(entry, request)

    if entry.helper_id in {"doctor-preflight", "doctor-repair", "install-health-repair", "install-codex-agents"}:
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
        "plan-layers-marker-plan",
        "validate-pr-packet-write",
        "detect-stack-manager-plan",
    }:
        return run_pr_emission_helper(entry, request)

    return run_mutation_helper(entry, request)


def blocked_promotion_response(entry: MutationEntry, request: Any) -> dict[str, Any]:
    mutation = empty_mutation(request.mode)
    mutation["mutation_status"] = "blocked"
    return response(
        "expected_failure",
        request_id=request.request_id,
        data={
            "helper_id": entry.helper_id,
            "operation": entry.operation,
            "mode": request.mode,
            "promotion_status": entry.promotion_status,
            "comparison_mode": entry.comparison_mode,
            "writes_state": False,
            "mutation": mutation,
        },
        diagnostics=[
            diagnostic(
                "helper_not_promoted",
                "helper promotion status blocks runner mutation dispatch",
                details={
                    "helper_id": entry.helper_id,
                    "operation": entry.operation,
                    "mode": request.mode,
                    "promotion_status": entry.promotion_status,
                },
                remediation_summary="Use only promoted mutation helpers for runner dispatch.",
                remediation_actions=[
                    "Inspect mutation-registry-dispatch output before retrying.",
                    entry.rollback,
                ],
            )
        ],
    )
