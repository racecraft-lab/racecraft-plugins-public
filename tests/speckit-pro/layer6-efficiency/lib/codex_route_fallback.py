"""Deterministic Codex-local fallback and recovery simulation.

This repository-only module consumes fixture evidence. It performs no live
model discovery, service calls, production routing, or real-home writes.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import tomllib
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0.0"
OPTIONAL_HELPER = "autopilot-fast-helper.toml"
FAKE_HOME_MARKER = ".g56r-005-harness-root"
PLUGIN_REASON_ORDER = (
    "model_absent",
    "unsupported_effort",
    "capability_discovery_unavailable",
    "availability_probe_failed",
    "treatment_probe_failed",
    "non_route_treatment_mutation",
)
TERMINAL_OUTCOMES = frozenset(
    {
        "qualified_route",
        "strict_override_rejected",
        "bounded_retry_exhausted",
        "time_budget_exhausted",
        "fanout_budget_rejected",
        "context_budget_rejected",
        "cancellation_observed",
        "escalation_rejected",
        "no_safe_route",
    }
)
NON_ROUTE_TREATMENT_FIELDS = (
    "agent_identity",
    "instructions",
    "tools",
    "skills",
    "mcp_bindings",
    "sandbox",
    "mutation_policy",
    "output_contract",
)


class RosterDriftError(ValueError):
    """The bundled source roster no longer matches reviewed fixture bytes."""


def canonical_bytes(value: Any) -> bytes:
    """Return the one canonical JSON representation used by this simulation."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def content_id(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def treatment_digest(treatment: dict[str, Any]) -> str:
    """Digest every non-route treatment field while excluding model and effort."""

    missing = [field for field in NON_ROUTE_TREATMENT_FIELDS if field not in treatment]
    if missing:
        raise ValueError(f"missing non-route treatment fields: {', '.join(missing)}")
    return content_id({field: treatment[field] for field in NON_ROUTE_TREATMENT_FIELDS})


def derive_source_roster(source_root: Path, repository_root: Path) -> dict[str, Any]:
    """Bind every bundled Codex TOML to content and required/optional class."""

    members = []
    for source in sorted(source_root.glob("*.toml")):
        members.append(
            {
                "classification": "optional_helper" if source.name == OPTIONAL_HELPER else "required_core",
                "path": source.relative_to(repository_root).as_posix(),
                "sha256": "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        )
    roster_id = content_id(members)
    return {
        "source_roster_id": roster_id,
        "canonicalization": "json-sorted-keys-compact-over-path-sha256-classification-rows",
        "members": members,
    }


def validate_source_roster(current: dict[str, Any], reviewed: dict[str, Any]) -> None:
    """Fail closed when roster content, membership, classification, or ID drifts."""

    if current != reviewed:
        raise RosterDriftError("bundled Codex source roster drifted; fixture re-review required")
    helpers = [member for member in current["members"] if member["classification"] == "optional_helper"]
    if [Path(member["path"]).name for member in helpers] != [OPTIONAL_HELPER]:
        raise RosterDriftError("optional helper classification drifted; fixture re-review required")
    if current["source_roster_id"] != content_id(current["members"]):
        raise RosterDriftError("source roster identity drifted; fixture re-review required")


def validate_helper_definition(helper_path: Path) -> dict[str, str]:
    """Bind the sole optional-helper classification to its checked-in TOML."""

    if helper_path.name != OPTIONAL_HELPER:
        raise RosterDriftError("optional helper filename drifted; fixture re-review required")
    document = tomllib.loads(helper_path.read_text(encoding="utf-8"))
    expected = {
        "classification": "optional_helper",
        "model": "gpt-5.3-codex-spark",
        "name": "autopilot-fast-helper",
        "sandbox_mode": "read-only",
    }
    actual = {key: document.get(key) for key in ("model", "name", "sandbox_mode")}
    if actual != {key: expected[key] for key in actual}:
        raise RosterDriftError("optional helper TOML contract drifted; fixture re-review required")
    return expected


def prepare_fake_home(fake_home_root: Path) -> Path:
    """Create an explicitly marked harness root beneath the host temp directory."""

    root = fake_home_root.absolute()
    if root.resolve(strict=False) == Path.home().resolve():
        raise ValueError("real home cannot be used as a fake-home root")
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if not root.resolve(strict=False).is_relative_to(temporary_root):
        raise ValueError("fake-home root must be harness-created beneath the temporary directory")
    root.mkdir(parents=True, exist_ok=True)
    marker = root / FAKE_HOME_MARKER
    marker.write_text("G56R-005\n", encoding="utf-8")
    agents = root / ".codex" / "agents"
    for component in (root / ".codex", agents):
        if component.is_symlink():
            raise ValueError("symlink traversal is forbidden in the fake-home boundary")
    agents.mkdir(parents=True, exist_ok=True)
    return agents


def _agents_boundary(fake_home_root: Path, destination_override: Path | None = None) -> Path:
    root = fake_home_root.absolute()
    if not (root / FAKE_HOME_MARKER).is_file():
        raise ValueError("fake-home root lacks the harness-created marker")
    expected = root / ".codex" / "agents"
    for component in (root, root / ".codex", expected):
        if component.is_symlink():
            raise ValueError("symlink traversal is forbidden in the fake-home boundary")
    destination = destination_override.absolute() if destination_override is not None else expected
    if destination.resolve(strict=False) != expected.resolve(strict=False):
        raise ValueError("destination escapes the fake-home agents boundary")
    return expected


def state_manifest(
    agents_root: Path, classifications: dict[str, str] | None = None
) -> dict[str, Any]:
    """Identify fake-home state without absolute paths or host metadata."""

    classifications = classifications or {}
    manifest = []
    if agents_root.exists():
        for path in sorted(item for item in agents_root.rglob("*") if item.is_file()):
            relative = path.relative_to(agents_root).as_posix()
            manifest.append(
                {
                    "path": f".codex/agents/{relative}",
                    "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
                    "mode": format(os.stat(path, follow_symlinks=False).st_mode & 0o777, "04o"),
                    "role_classification": classifications.get(
                        relative,
                        "optional_helper" if Path(relative).name == OPTIONAL_HELPER else "required_core",
                    ),
                }
            )
    return {"state_id": content_id(manifest), "manifest": manifest}


def _action(kind: str, name: str, classification: str) -> dict[str, str]:
    return {
        "action": kind,
        "path": f".codex/agents/{name}",
        "role_classification": classification,
    }


def apply_fake_home(
    fake_home_root: Path,
    desired_files: dict[str, bytes],
    classifications: dict[str, str],
    *,
    failure_mode: str | None = None,
    destination_override: Path | None = None,
) -> dict[str, Any]:
    """Stage and atomically apply fixture bytes beneath one fake-home boundary."""

    agents = _agents_boundary(fake_home_root, destination_override)
    for name in desired_files:
        if Path(name).name != name or not name.endswith(".toml"):
            raise ValueError("destination escapes the fake-home agents boundary")
        if classifications.get(name) not in {"required_core", "optional_helper"}:
            raise ValueError(f"missing role classification for {name}")
    for path in agents.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlink traversal is forbidden in the fake-home boundary")

    existing_names = sorted(path.name for path in agents.glob("*.toml") if path.is_file())
    pre_classifications = {
        name: classifications.get(
            name, "optional_helper" if name == OPTIONAL_HELPER else "required_core"
        )
        for name in existing_names
    }
    snapshot = {
        name: {
            "bytes": (agents / name).read_bytes(),
            "mode": os.stat(agents / name, follow_symlinks=False).st_mode & 0o777,
        }
        for name in existing_names
    }
    pre_state = state_manifest(agents, pre_classifications)
    staged = [
        _action("stage", name, classifications[name]) for name in sorted(desired_files)
    ]
    applied: list[dict[str, str]] = []
    rolled_back: list[dict[str, str]] = []
    cleanup: list[dict[str, str]] = []
    cleanup_errors: list[str] = []
    rollback_outcome = "not_required"
    manual_remediation: list[str] = []

    if failure_mode != "before_write":
        write_names = sorted(desired_files)
        if failure_mode in {"after_first_write", "rollback_failure", "cleanup_failure", "cancellation"}:
            write_names = write_names[:1]
        for name in write_names:
            target = agents / name
            target.write_bytes(desired_files[name])
            target.chmod(0o644)
            applied.append(_action("write", name, classifications[name]))

        if failure_mode in {"after_first_write", "rollback_failure", "cleanup_failure", "cancellation"}:
            if failure_mode == "rollback_failure":
                rollback_outcome = "failed"
                manual_remediation = [
                    f"restore .codex/agents/{item['path'].rsplit('/', 1)[-1]} from the previous-known-good manifest"
                    for item in applied
                ]
            else:
                for path in sorted(agents.glob("*.toml")):
                    path.unlink()
                for name in sorted(snapshot):
                    target = agents / name
                    target.write_bytes(snapshot[name]["bytes"])
                    target.chmod(snapshot[name]["mode"])
                rolled_back = [
                    _action(
                        "restore" if item["path"].rsplit("/", 1)[-1] in snapshot else "remove",
                        item["path"].rsplit("/", 1)[-1],
                        item["role_classification"],
                    )
                    for item in applied
                ]
                rollback_outcome = "restored"
            cleanup = [
                _action("cleanup", name, classifications[name])
                for name in sorted(desired_files)
            ]
            if failure_mode == "cleanup_failure":
                cleanup_errors = ["cleanup staging area failed", "cleanup temporary copy failed"]

    final_classifications = classifications if rollback_outcome == "not_required" and applied else pre_classifications
    final_state = state_manifest(agents, final_classifications)
    writes_state = final_state["state_id"] != pre_state["state_id"]
    terminal = "qualified_route" if failure_mode is None else (
        "cancellation_observed" if failure_mode == "cancellation" else "no_safe_route"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "pre_state_id": pre_state["state_id"],
        "final_state_id": final_state["state_id"],
        "staged_actions": staged,
        "applied_actions": applied,
        "rolled_back_actions": rolled_back,
        "cleanup_actions": cleanup,
        "cleanup_errors": sorted(cleanup_errors),
        "rollback_outcome": rollback_outcome,
        "writes_state": writes_state,
        "manual_remediation": sorted(manual_remediation),
        "terminal_outcome": terminal,
    }


def _diagnostic_reasons(candidate: dict[str, Any], expected_digest: str) -> list[str]:
    flags = {
        "model_absent": not candidate.get("model_present", False),
        "unsupported_effort": not candidate.get("effort_supported", False),
        "capability_discovery_unavailable": not candidate.get("capability_discovery_available", False),
        "availability_probe_failed": not candidate.get("availability_probe", {}).get("succeeded", False),
        "treatment_probe_failed": not candidate.get("treatment_probe", {}).get("succeeded", False),
        "non_route_treatment_mutation": candidate.get("non_route_treatment_digest") != expected_digest,
    }
    reasons = [reason for reason in PLUGIN_REASON_ORDER if flags[reason]]
    declaration_rejections = {
        "inherited_model": "inherited_model_rejected",
        "inherited_effort": "inherited_effort_rejected",
        "generic_substitution": "generic_substitution_rejected",
        "unqualified_adjacent": "unqualified_adjacent_route",
    }
    rejection = declaration_rejections.get(candidate.get("declaration_source"))
    if rejection is not None:
        reasons.append(rejection)
    return reasons


def _base_report(policy: dict[str, Any], case_id: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "policy_id": policy["policy_id"],
        "source_roster_id": policy["source_roster_id"],
        "attempted_routes": [],
        "plugin_diagnostics": [],
        "service_reroute_attribution": None,
        "qualified_route": None,
        "scoring_eligible": False,
        "helper_counters": {"attempts": 0, "successes": 0, "failures": 0},
        "required_route_counters": {"attempts": 0, "successes": 0, "failures": 0},
        "budget_counters": {"retries": 0, "elapsed_units": 0, "fanout": 1, "context_units": 0, "escalations": 0},
        "terminal_outcome": "no_safe_route",
        "terminal_details": [],
    }


def _service_attribution(policy: dict[str, Any]) -> dict[str, str] | None:
    evidence = policy.get("service_reroute")
    if evidence is None:
        return None
    declared = {
        candidate["route_id"]
        for candidate in [policy["preferred_route"], *policy.get("fallback_routes", [])]
    }
    approved = (
        evidence.get("origin") == "service"
        and evidence.get("approval") == "approved"
        and evidence.get("observed_target_route") in declared
        and evidence.get("non_route_treatment_digest")
        == policy["agent"]["non_route_treatment_digest"]
    )
    return {
        "origin": "service",
        "observed_target_route": evidence.get("observed_target_route", ""),
        "approval": "approved" if approved else "unapproved",
        "scoring_effect": "eligible" if approved else "ineligible",
    }


def resolve_route(policy: dict[str, Any], *, case_id: str) -> dict[str, Any]:
    """Resolve preferred then fallback routes from deterministic fixture facts."""

    report = _base_report(policy, case_id)
    report["service_reroute_attribution"] = _service_attribution(policy)
    if policy.get("strict_override", {}).get("status") == "incompatible":
        report["terminal_outcome"] = "strict_override_rejected"
        return report

    helper_state = policy.get("helper_state")
    helper_degraded = helper_state is not None and not helper_state.get("available", False)
    if helper_degraded:
        helper_attempts = helper_state.get("helper_route_attempts", 0)
        report["helper_counters"] = {"attempts": helper_attempts, "successes": 0, "failures": 1}
        report["plugin_diagnostics"].append(
            {"route_id": "autopilot-fast-helper", "reason": "optional_helper_unavailable"}
        )
        if helper_attempts != 0 or not helper_state.get("no_helper_continuation_qualified", False):
            report["terminal_details"].append("no_helper_continuation_unqualified")
            return report

    attempted: set[str] = set()
    expected_digest = policy["agent"]["non_route_treatment_digest"]
    for candidate in [policy["preferred_route"], *policy.get("fallback_routes", [])]:
        route_id = candidate["route_id"]
        if route_id in attempted:
            report["plugin_diagnostics"].append({"route_id": route_id, "reason": "loop_rejected"})
            report["terminal_details"].append("fallback_loop")
            break
        attempted.add(route_id)
        report["attempted_routes"].append(route_id)
        reasons = _diagnostic_reasons(candidate, expected_digest)
        report["plugin_diagnostics"].extend(
            {"route_id": route_id, "reason": reason} for reason in reasons
        )
        report["required_route_counters"]["attempts"] += 1
        if not reasons:
            report["qualified_route"] = route_id
            attribution = report["service_reroute_attribution"]
            report["scoring_eligible"] = attribution is None or attribution["approval"] == "approved"
            report["required_route_counters"]["successes"] += 1
            report["terminal_outcome"] = "qualified_route"
            return report
        report["required_route_counters"]["failures"] += 1

    report["terminal_details"].append("fallback_exhausted")
    return report


def run_harness(
    policy: dict[str, Any],
    *,
    case_id: str,
    consumption: dict[str, Any],
    fake_home: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one bounded, sequential, non-recursive fixture replay."""

    if policy.get("strict_override", {}).get("status") == "incompatible":
        return resolve_route(policy, case_id=case_id)

    budgets = policy.get("budgets", {})
    counters = {
        "retries": int(consumption.get("retries", 0)),
        "elapsed_units": int(consumption.get("elapsed_units", 0)),
        "fanout": int(consumption.get("fanout", 1)),
        "context_units": int(consumption.get("context_units", 0)),
        "escalations": int(consumption.get("escalations", 0)),
    }
    terminal: str | None = None
    if counters["retries"] > budgets.get("max_retries", counters["retries"]):
        terminal = "bounded_retry_exhausted"
    elif counters["elapsed_units"] > budgets.get("max_elapsed_units", counters["elapsed_units"]):
        terminal = "time_budget_exhausted"
    elif counters["fanout"] > 1 or counters["fanout"] > budgets.get("max_fanout", 1):
        terminal = "fanout_budget_rejected"
    elif counters["context_units"] > budgets.get("max_context_units", counters["context_units"]):
        terminal = "context_budget_rejected"
    elif consumption.get("cancellation", False):
        terminal = "cancellation_observed"
    elif (
        counters["escalations"] > budgets.get("max_escalations", counters["escalations"])
        or consumption.get("human_in_loop", False)
    ):
        terminal = "escalation_rejected"

    if terminal is not None:
        report = _base_report(policy, case_id)
        report["budget_counters"] = counters
        report["terminal_outcome"] = terminal
        if terminal == "cancellation_observed" and fake_home is not None:
            report["recovery_record"] = apply_fake_home(
                fake_home["root"],
                fake_home["desired_files"],
                fake_home["classifications"],
                failure_mode="cancellation",
            )
        return report

    if consumption.get("recursive", False):
        report = _base_report(policy, case_id)
        report["budget_counters"] = counters
        report["terminal_details"].append("recursive_execution_rejected")
        return report

    report = resolve_route(policy, case_id=case_id)
    report["budget_counters"] = counters
    return report
