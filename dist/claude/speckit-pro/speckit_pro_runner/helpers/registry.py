"""Explicit registry for runner-owned read-only helper operations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..envelope import diagnostic, response
from ..formal.helper import run_formal_helper
from ..research_preflight import run_research_broker_preflight_helper
from .archive_sweep import run_archive_sweep_helper
# The two CODEX_ names are re-exported: tests read them through the registry.
from .install import CODEX_OPTIONAL_HELPER_NAME, CODEX_REQUIRED_AGENT_NAMES, run_install_helper  # noqa: F401
from .decisions_list import run_decisions_list_helper
from .egress_authorization import run_egress_authorization_helper
from .execution_requests import run_execution_helper
from .git_write_probe import run_git_write_probe_helper
from .gate_preflight_coverage import run_gate_preflight_coverage_helper
from .g0_setup import run_g0_setup_helper
from .roadmap_freshness import run_roadmap_freshness_helper
from .readiness_record import run_readiness_record_helper
from .scaffold_answers import run_scaffold_answers_helper
from .run_finalization import run_run_finalization_helper
from .mutation import empty_mutation, run_mutation_helper, run_spec_index_write, run_sweep_apply_result
from .pr_emission import generate_pr_body, plan_commands
from .pr_packet import generate_pr_packet, validate_pr_packet_write
from .pr_split_ratification import run_pr_split_ratification_helper
from .promotion import promotion_record
from .read_only import registry_report, run_registered_helper
from .stack_manager import run_stack_manager_helper
from .uat_skeleton import generate_uat_skeleton


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


# Test-only: the request fixture each entry's `authoritative_command` names. The
# plugin does not ship `tests/`, so no emitted record or envelope carries these paths.
SCRIPT_BASE = "speckit-pro/skills/speckit-autopilot/scripts"
REQUEST_FIXTURE_BASE = "tests/speckit-pro/unit/fixtures/read-only-helpers/requests"
MUTATION_REQUEST_FIXTURE_BASE = "tests/speckit-pro/unit/fixtures/mutation-helpers/requests"
DISPATCHABLE_MUTATION_PROMOTION_STATUSES = frozenset({"golden_only", "bash_compared"})


def authoritative_request(helper_id: str) -> str:
    return f"python -m speckit_pro_runner < {REQUEST_FIXTURE_BASE}/{helper_id}.json"


def mutation_authoritative_request(helper_id: str) -> str:
    return f"python -m speckit_pro_runner < {MUTATION_REQUEST_FIXTURE_BASE}/{helper_id}.json"


def deferred_authoritative_request() -> str:
    return ""


HELPERS: dict[str, HelperEntry] = {
    "g0-setup": HelperEntry(
        "g0-setup", "g0-setup", None, "python_authoritative", "python_contract",
        authoritative_request("g0-setup"),
    ),
    "probe-git-write": HelperEntry(
        "probe-git-write", "probe-git-write", None, "python_authoritative", "python_contract",
        authoritative_request("probe-git-write"),
    ),
    "scaffold-answers": HelperEntry(
        "scaffold-answers", "scaffold-answers", None, "python_authoritative", "python_contract",
        authoritative_request("scaffold-answers"),
    ),
    "formal-doctor": HelperEntry(
        "formal-doctor", "formal-doctor", None, "python_authoritative", "python_contract",
        authoritative_request("formal-doctor"),
    ),
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
    "resolve-scaffold-worktree-placement": HelperEntry(
        "resolve-scaffold-worktree-placement",
        "resolve-scaffold-worktree-placement",
        None,
        "python_authoritative",
        "python_contract",
        authoritative_request("resolve-scaffold-worktree-placement"),
    ),
    "render-plan-repair-context": HelperEntry(
        "render-plan-repair-context",
        "render-plan-repair-context",
        None,
        "python_authoritative",
        "python_contract",
        authoritative_request("render-plan-repair-context"),
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
    # Archive Sweep enumeration: prior specs, the current target excluded, and
    # which ones have a merged pull request the helper can observe.
    "list-archive-candidates": HelperEntry(
        "list-archive-candidates",
        "list-archive-candidates",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("list-archive-candidates"),
    ),
    # Scaffold's pre-parse check: the checkout's roadmap against the remote
    # default branch, and the revision a new spec worktree is based on.
    "check-roadmap-freshness": HelperEntry(
        "check-roadmap-freshness",
        "check-roadmap-freshness",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("check-roadmap-freshness"),
    ),
    # Value-free check of the research broker's screening dependencies: the
    # typesafe-jev binary, its credential state, and the search key sources.
    "research-broker-preflight": HelperEntry(
        "research-broker-preflight",
        "research-broker-preflight",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("research-broker-preflight"),
    ),
    "render-egress-authorization": HelperEntry(
        "render-egress-authorization",
        "render-egress-authorization",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("render-egress-authorization"),
    ),
    "check-gate-preflight-coverage": HelperEntry(
        "check-gate-preflight-coverage",
        "check-gate-preflight-coverage",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("check-gate-preflight-coverage"),
    ),
    "finalize-run": HelperEntry(
        "finalize-run",
        "finalize-run",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("finalize-run"),
    ),
    "ratify-pr-split": HelperEntry(
        "ratify-pr-split",
        "ratify-pr-split",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("ratify-pr-split"),
    ),
    "resolve-claude-subagent-runtime": HelperEntry(
        "resolve-claude-subagent-runtime",
        "resolve-claude-subagent-runtime",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("resolve-claude-subagent-runtime"),
    ),
    "validate-agent-install": HelperEntry(
        "validate-agent-install",
        "validate-agent-install",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("validate-agent-install"),
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
    "preview-isolation-session": HelperEntry(
        "preview-isolation-session",
        "preview-isolation-session",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("preview-isolation-session"),
    ),
    "check-artifact-freshness": HelperEntry(
        "check-artifact-freshness",
        "check-artifact-freshness",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("check-artifact-freshness"),
    ),
    "partition-phase7-tasks": HelperEntry(
        "partition-phase7-tasks",
        "partition-phase7-tasks",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("partition-phase7-tasks"),
    ),
    "validate-task-execution": HelperEntry(
        "validate-task-execution", "validate-task-execution", None, "python_authoritative", "python_contract",
        authoritative_request("validate-task-execution"),
    ),
    "validate-execution-record": HelperEntry(
        "validate-execution-record", "validate-execution-record", None, "python_authoritative", "python_contract",
        authoritative_request("validate-execution-record"),
    ),
    "parse-consensus-categories": HelperEntry(
        "parse-consensus-categories",
        "parse-consensus-categories",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("parse-consensus-categories"),
    ),
    "aggregate-crl": HelperEntry(
        "aggregate-crl",
        "aggregate-crl",
        None,
        "python_authoritative",
        "python_only",
        authoritative_request("aggregate-crl"),
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
    "task-results": MutationEntry(
        "task-results", "task-results", ("read_only", "dry_run", "apply"), None,
        "golden_only", "fixture_semantic", mutation_authoritative_request("task-results"),
        ("frozen-batch-identities", "per-task-results", "native-tdd-observations", "partial-resume"),
    ),
    "execution-control": MutationEntry(
        "execution-control", "execution-control", ("read_only", "dry_run", "apply"), None,
        "golden_only", "fixture_semantic", mutation_authoritative_request("execution-control"),
        ("durable-budget", "nested-reservation", "native-wait", "unknown-outcome"),
    ),
    "execute-verification": MutationEntry(
        "execute-verification", "execute-verification", ("dry_run", "apply"), None,
        "golden_only", "fixture_semantic", mutation_authoritative_request("execute-verification"),
        ("copy-only-no-reuse", "isolated-command", "native-observation-required"),
    ),
    "formal-check": MutationEntry(
        "formal-check", "formal-check", ("dry_run", "apply"), None, "golden_only", "fixture_semantic",
        mutation_authoritative_request("formal-check"), ("explicit-selection", "preview-no-writes", "checkpoint-resume"),
        rollback="Preserve model inputs, inspect the checkpoint record, and rerun preview before resuming Plan.",
    ),
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
        "golden_only",
        "golden_fixture",
        mutation_authoritative_request("generate-uat-skeleton"),
        ("generate-uat-skeleton-apply",),
        ("generate-uat-skeleton",),
        "Retry the registered generate-uat-skeleton operation in dry_run mode before applying again.",
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
    "decisions-list": MutationEntry(
        "decisions-list",
        "decisions-list",
        ("read_only", "dry_run", "apply"),
        None,
        "golden_only",
        "golden_fixture",
        mutation_authoritative_request("decisions-list"),
        rollback="Appends are all-or-nothing; a refused batch writes nothing, so rerun it corrected.",
    ),
    "detect-stack-manager-plan": MutationEntry(
        "detect-stack-manager-plan",
        "detect-stack-manager-plan",
        ("dry_run",),
        None,
        "golden_only",
        "command_plan",
        mutation_authoritative_request("detect-stack-manager-plan"),
    ),
    "write-readiness-record": MutationEntry(
        "write-readiness-record", "write-readiness-record", ("dry_run", "apply"), None,
        "golden_only", "fixture_semantic", mutation_authoritative_request("write-readiness-record"),
        ("readiness-record-apply",),
        rollback="Delete the local .specify/readiness/<host>.json file; scaffold rewrites it on the next run.",
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


# Helpers with their own response contracts share one dispatch path.
SPECIAL_HELPER_HANDLERS: dict[str, Callable[[Any, Any], dict[str, Any]]] = {
    "formal-doctor": run_formal_helper,
    "research-broker-preflight": run_research_broker_preflight_helper,
    "render-egress-authorization": run_egress_authorization_helper,
    "check-gate-preflight-coverage": run_gate_preflight_coverage_helper,
    "finalize-run": run_run_finalization_helper,
    "ratify-pr-split": run_pr_split_ratification_helper,
    "list-archive-candidates": run_archive_sweep_helper,
    "check-roadmap-freshness": run_roadmap_freshness_helper,
    "scaffold-answers": run_scaffold_answers_helper,
    "g0-setup": run_g0_setup_helper,
    "probe-git-write": run_git_write_probe_helper,
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
        return response("ok", request_id=request.request_id, data=registry_report(HELPERS))
    handler = SPECIAL_HELPER_HANDLERS.get(entry.helper_id)
    if handler is not None:
        return handler(entry, request)
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

    if entry.helper_id in {"execution-control", "execute-verification", "task-results"}:
        return run_execution_helper(entry, request)

    if entry.helper_id == "decisions-list":
        return run_decisions_list_helper(entry, request)

    if entry.helper_id == "formal-check":
        return run_formal_helper(entry, request)

    if entry.helper_id == "generate-spec-index-write":
        return run_spec_index_write(entry, request)

    if entry.helper_id == "write-readiness-record":
        return run_readiness_record_helper(entry, request)

    if entry.helper_id == "sweep-apply-result":
        return run_sweep_apply_result(entry, request)

    if entry.helper_id in {"doctor-preflight", "doctor-repair", "install-codex-agents"}:
        return run_install_helper(entry, request)

    if entry.helper_id in PR_EMISSION_HANDLERS or entry.helper_id in UNWIRED_PR_EMISSION_IDS:
        return run_pr_emission_helper(entry, request)

    return run_mutation_helper(entry, request)


# The one table that routes a PR-emission helper id to its handler.
PR_EMISSION_HANDLERS: dict[str, Callable[[Any, Any], dict[str, Any]]] = {
    "generate-pr-body": generate_pr_body,
    "generate-uat-skeleton": generate_uat_skeleton,
    "pr-packet-output": generate_pr_packet,
    "validate-pr-packet-write": validate_pr_packet_write,
    "multi-pr-emission": plan_commands,
    "restack": plan_commands,
    "detect-stack-manager-plan": run_stack_manager_helper,
}
# Routed as PR emission, but deferred: promoting one needs a handler in the table above first.
UNWIRED_PR_EMISSION_IDS = frozenset({
    "final-reviewability-backstop",
    "validate-pr-workflow-contract-write",
    "relocate-process-artifacts",
    "plan-layers-marker-plan",
})


def run_pr_emission_helper(entry: MutationEntry, request: Any) -> dict[str, Any]:
    handler = PR_EMISSION_HANDLERS.get(entry.helper_id)
    if handler is None:
        return response(
            "internal_failure",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "helper_not_wired",
                    "the registry routes this helper to PR emission, but no handler is registered for it",
                    details={"helper_id": entry.helper_id},
                    remediation_summary="Add the helper to PR_EMISSION_HANDLERS before promoting it.",
                    remediation_actions=["Register a handler in helpers/registry.py.", "Retry the request."],
                )
            ],
        )
    return handler(entry, request)



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
