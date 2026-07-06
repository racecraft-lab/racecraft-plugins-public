"""Release-readiness gate operations for XPLAT-007 US2."""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from ..envelope import diagnostic, response

PROMOTION_RECORD = "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json"
DEFAULT_CASE_FILE = "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/release-readiness-cases.json"
XPLAT_008_RELEASE_CASE_FILE = "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/release-readiness-cases.json"
XPLAT_008_PROMOTION_RECORD = "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/promotion-records.json"
XPLAT008_CHECK_IDS = {
    "active-runtime-guard",
    "bundled-agents",
    "dist-determinism",
    "hooks",
    "install-health-repair",
    "payload-completeness",
    "public-claims",
    "release-packet-traceability",
    "runner-files",
    "runner-invocations",
    "trust-metadata",
    "uat-matrix",
    "update-proof",
    "version-sync",
}
XPLAT008_BLOCKER_CLASSES = {
    "active_shell_runtime_dependency",
    "incomplete_payload",
    "incomplete_uat_evidence",
    "missing_bundled_agent",
    "missing_hook",
    "missing_runner_file",
    "missing_runner_invocation",
    "missing_traceability",
    "missing_trust_metadata",
    "nondeterministic_dist",
    "stale_metadata",
    "unsafe_public_claim",
    "unsafe_repair_claim",
}
VALID_STATUS = {"pass", "fail"}
EVIDENCE_STATUS = {"pass", "fail", "blocked"}
REPAIR_ACTION_TYPES = {"autoheal_refresh", "manual_remediation"}
REPAIR_STATUS = {"completed", "skipped", "blocked"}
RUNNER_OPERATIONS = {"preflight", "scaffold", "status", "autopilot-dry-run", "doctor", "update", "autoheal"}
PAYLOAD_RESULT_KEYS = {
    "payload_surface",
    "plugin_version",
    "runner_version",
    "expected_files",
    "actual_files",
    "missing_paths",
    "extra_paths",
    "mismatched_paths",
    "path_leaks",
    "file_tree_hash",
    "status",
}
PAYLOAD_FILE_KEYS = {"path", "source_path", "kind", "transform", "sha256", "byte_count", "required"}
PAYLOAD_FILE_KINDS = {"manifest", "skill", "agent", "hook", "runner", "install_guidance", "trust_metadata", "checksum", "version_metadata", "docs"}
PAYLOAD_FILE_TRANSFORMS = {"none", "claude_guard_strip", "codex_overlay", "path_normalization", "manifest_rewrite"}
XPLAT008_REQUIRED_UAT_ROWS = (
    ("claude", "windows"),
    ("claude", "macos"),
    ("claude", "linux"),
    ("codex", "windows"),
    ("codex", "macos"),
    ("codex", "linux"),
)
RELEASE_OPERATIONS = (
    "detect-changed-plugin",
    "aggregate-suite-results",
    "check-marketplace-version-sync",
    "validate-pr-title",
    "validate-workflow-contract",
    "check-payload-evidence",
    "parse-release-pr-payload-sync",
    "check-post-release-drift",
)

__all__ = ("run_release_gate",)


def run_release_gate(entry: Any, request: Any) -> dict[str, Any]:
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        diag = diagnostic(
            "missing_prerequisite",
            "could not locate repository root for release-readiness gate request",
            remediation_summary="Run the gate from a SpecKit Pro source checkout.",
            remediation_actions=["Change to the repository root.", "Retry the same runner request."],
        )
        return response("missing_prerequisite", request_id=request.request_id, data=base_data(entry, request.operation, "missing_prerequisite"), diagnostics=[diag])

    if request.operation == "release-readiness-xplat008":
        return release_readiness_xplat008(entry, request, repo_root)

    case_result = load_release_case(repo_root, request.inputs)
    if is_diagnostic(case_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[case_result])
    case = case_result

    if request.inputs.get("xplat_008_cutover_allowed") is not False:
        diag = diagnostic(
            "xplat_008_cutover_refused",
            "XPLAT-007 release readiness must not claim XPLAT-008 cutover surfaces",
            remediation_summary="Keep XPLAT-008 cutover surfaces as explicit handoff items.",
            remediation_actions=["Set xplat_008_cutover_allowed to false.", "Defer active invocation and public release cutover to XPLAT-008."],
            deferred_to="XPLAT-008",
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])

    if request.operation == "release-readiness":
        return release_readiness(entry, request, case)
    if request.operation not in RELEASE_OPERATIONS:
        diag = diagnostic(
            "unknown_gate_operation",
            "release gate operation is not implemented by the release module",
            details={"operation": request.operation},
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])

    check, extra = build_check(request.operation, case)
    status = "ok" if check["status"] == "pass" else "expected_failure"
    data = base_data(entry, request.operation, status)
    data["release_check"] = check
    data.update(extra)
    if status == "ok":
        return response("ok", request_id=request.request_id, data=data)
    data["gate"]["gate_status"] = "fail"
    data["gate"]["blocking"] = True
    diag = diagnostic(
        "release_check_failed",
        "release-readiness check blocked the fixture case",
        details={"check_id": check["check_id"], "case_id": case.get("case_id"), "evidence": check["evidence"]},
        remediation_summary="Fix the blocking release-readiness evidence before release.",
        remediation_actions=["Inspect data.release_check.evidence.", "Retry the same runner request after updating fixtures or source evidence."],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def release_readiness(entry: Any, request: Any, case: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for operation in RELEASE_OPERATIONS:
        check, _extra = build_check(operation, case)
        checks.append(check)

    required = [item for item in case.get("_required_promotion_operations", []) if isinstance(item, str)]
    present = [item for item in case.get("promotion_records", []) if isinstance(item, str)]
    missing = sorted(set(required) - set(present))
    checks.append(
        check_record(
            "promotion-records",
            not missing,
            [f"promotion_record_count={len(present)}", *[f"missing={item}" for item in missing]],
        )
    )

    active_guard = active_path_guard_summary(case)
    checks.append(
        check_record(
            "active-path-guard-summary",
            active_guard["status"] == "ok" and active_guard["blocking_count"] == 0,
            [f"status={active_guard['status']}", f"blocking_count={active_guard['blocking_count']}"],
        )
    )

    blocking_count = sum(1 for check in checks if check["blocking"])
    readiness = {
        "schema_version": "1.0",
        "status": "pass" if blocking_count == 0 else "fail",
        "checks": checks,
        "blocking_count": blocking_count,
        "promotion_record_count": len(present),
        "test_payload_evidence_ids": sorted(payload_evidence_ids(case)),
        "install_verification_ids": sorted(install_verification_ids(case)),
        "active_path_guard_summary": active_guard,
        "xplat_008_handoff_items": xplat_008_handoff_items(case),
    }

    status = "ok" if blocking_count == 0 else "expected_failure"
    data = base_data(entry, request.operation, status)
    data["release_readiness"] = readiness
    if status == "ok":
        return response("ok", request_id=request.request_id, data=data)

    data["gate"]["gate_status"] = "fail"
    data["gate"]["blocking"] = True
    diag = diagnostic(
        "release_readiness_blocked",
        "release readiness aggregate has blocking checks",
        details={"case_id": case.get("case_id"), "blocking_count": blocking_count},
        remediation_summary="Resolve the blocking release-readiness checks before release.",
        remediation_actions=["Inspect data.release_readiness.checks.", "Retry after refreshing the stale or missing evidence."],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def release_readiness_xplat008(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    case_result = load_xplat008_release_case(repo_root, request.inputs)
    if is_diagnostic(case_result):
        return response("input_error", request_id=request.request_id, data=xplat008_base_data(entry, request.operation, "input_error"), diagnostics=[case_result])
    case = case_result

    live_gate_evidence_disabled = case.get("use_live_gate_evidence") is False
    live_evidence = {} if live_gate_evidence_disabled else live_xplat008_gate_evidence(repo_root)
    payload_evidence_records = [
        *normalize_payload_results(case.get("payload_results")),
        *normalize_payload_results(live_evidence.get("payload_results")),
    ]
    payload_results = project_payload_results(payload_evidence_records)
    uat_rows = normalize_uat_rows(case.get("uat_rows"))
    repair_actions = normalize_repair_actions(case.get("repair_actions"))
    public_claim_results = normalize_public_claim_results(case.get("public_claim_results"))
    runner_invocations = [
        *normalize_runner_invocations(case.get("runner_invocations")),
        *normalize_runner_invocations(live_evidence.get("runner_invocations")),
    ]
    traceability = normalize_traceability(case.get("traceability"))
    checks = [
        *normalize_xplat008_checks(case.get("checks")),
        *normalize_xplat008_checks(live_evidence.get("checks")),
    ]
    if live_gate_evidence_disabled:
        checks.append(
            xplat008_check(
                "active-runtime-guard",
                "active_shell_runtime_dependency",
                False,
                "Live XPLAT-008 release gate evidence is mandatory for release readiness.",
                ["use_live_gate_evidence=false"],
            )
        )

    checks.extend(
        computed_xplat008_checks(
            payload_evidence_records,
            uat_rows,
            repair_actions,
            public_claim_results,
            runner_invocations,
            traceability,
        )
    )
    checks.extend(
        validate_xplat008_evidence_contracts(
            payload_results,
            uat_rows,
            repair_actions,
            public_claim_results,
            runner_invocations,
            traceability,
        )
    )
    checks = collapse_checks(checks)
    blocking_count = sum(1 for check in checks if check["blocking"])

    readiness = {
        "schema_version": "1.0",
        "feature_id": "XPLAT-008",
        "status": "pass" if blocking_count == 0 else "fail",
        "blocking_count": blocking_count,
        "checks": checks,
        "payload_results": payload_results,
        "uat_rows": uat_rows,
        "repair_actions": repair_actions,
        "public_claim_results": public_claim_results,
        "runner_invocations": runner_invocations,
        "evidence_refs": {
            "payload_results": ["tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/payload-completeness-cases.json"],
            "uat_matrix": "specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/uat-matrix.md",
            "install_health": ["tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/install-health-repair-cases.json"],
            "public_claims": ["tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/release-readiness-cases.json"],
            "runner_invocations": ["tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/runner-invocation-cases.json"],
        },
        "traceability": traceability,
    }

    status = "ok" if blocking_count == 0 else "expected_failure"
    data = xplat008_base_data(entry, request.operation, status)
    data["release_readiness"] = readiness
    if status == "ok":
        return response("ok", request_id=request.request_id, data=data)

    data["gate"]["gate_status"] = "fail"
    data["gate"]["blocking"] = True
    diag = diagnostic(
        "release_readiness_xplat008_blocked",
        "XPLAT-008 release readiness has blocking checks",
        details={"case_id": case.get("case_id"), "blocking_count": blocking_count},
        remediation_summary="Resolve XPLAT-008 payload, public-claim, UAT, repair, and traceability blockers before release.",
        remediation_actions=["Inspect data.release_readiness.checks.", "Retry the XPLAT-008 release-readiness request after updating evidence."],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def live_xplat008_gate_evidence(repo_root: Path) -> dict[str, Any]:
    from . import active_path_guard, payloads as payload_gate
    from ..helpers import install as install_helper

    evidence: dict[str, Any] = {"checks": [], "payload_results": [], "runner_invocations": []}

    active_response = active_path_guard.run_active_runtime_guard(
        SimpleNamespace(helper_id="active-path-guard"),
        SimpleNamespace(
            operation="active-runtime-guard",
            request_id="xplat-008-release-readiness:active-runtime-guard",
            mode="read_only",
            inputs={
                "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/active-runtime-guard-cases.json",
                "case_id": "final-current-implementation",
            },
        ),
        repo_root,
    )
    active_data = active_response.get("data") if isinstance(active_response, dict) else {}
    active_blocking = active_response.get("status") != "ok" if isinstance(active_response, dict) else True
    active_count = active_data.get("blocking_count") if isinstance(active_data, dict) else None
    evidence["checks"].append(
        xplat008_check(
            "active-runtime-guard",
            "active_shell_runtime_dependency",
            not active_blocking and active_count == 0,
            "Live active-runtime guard completed for current release surfaces.",
            [
                f"live_status={active_response.get('status', 'missing') if isinstance(active_response, dict) else 'missing'}",
                f"blocking_count={active_count if isinstance(active_count, int) else 'unknown'}",
            ],
        )
    )

    payload_response = payload_gate.payload_completeness_xplat008(
        SimpleNamespace(helper_id="payload-gate"),
        SimpleNamespace(
            operation="payload-completeness",
            request_id="xplat-008-release-readiness:payload-completeness",
            mode="read_only",
            inputs={
                "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/payload-completeness-cases.json",
                "case_id": "current-committed-dist",
            },
        ),
        repo_root,
    )
    payload_data = payload_response.get("data") if isinstance(payload_response, dict) else {}
    payload_results = payload_data.get("payload_completeness") if isinstance(payload_data, dict) else None
    if isinstance(payload_results, list):
        evidence["payload_results"].extend(item for item in payload_results if isinstance(item, dict))
    evidence["checks"].append(
        xplat008_check(
            "payload-completeness",
            "incomplete_payload",
            isinstance(payload_response, dict) and payload_response.get("status") == "ok",
            "Live payload completeness gate completed for committed Claude and Codex payloads.",
            [f"live_status={payload_response.get('status', 'missing') if isinstance(payload_response, dict) else 'missing'}"],
        )
    )

    runner_case = install_helper.runner_invocation_case(
        repo_root,
        {
            "case_file": "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/runner-invocation-cases.json",
            "case_id": "live-host-runtime-info",
        },
    )
    if is_diagnostic(runner_case):
        evidence["checks"].append(
            xplat008_check(
                "runner-invocations",
                "missing_runner_invocation",
                False,
                "Live runner invocation evidence could not be loaded.",
                [str(runner_case.get("code"))],
            )
        )
    else:
        runner_record, _diagnostics = install_helper.runner_invocation_record(
            runner_case,
            "xplat-008-release-readiness:runner-invocation",
            repo_root,
        )
        evidence["runner_invocations"].append(runner_record)

    return evidence


def normalize_xplat008_checks(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    checks: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        raw_check_id = item.get("check_id")
        raw_blocker_class = item.get("blocker_class")
        raw_status = item.get("status")
        raw_evidence = item.get("evidence")
        malformed = (
            raw_check_id not in XPLAT008_CHECK_IDS
            or raw_blocker_class not in XPLAT008_BLOCKER_CLASSES
            or raw_status not in VALID_STATUS
            or not isinstance(raw_evidence, list)
        )
        check_id = raw_check_id if raw_check_id in XPLAT008_CHECK_IDS else "release-packet-traceability"
        blocker_class = raw_blocker_class if raw_blocker_class in XPLAT008_BLOCKER_CLASSES else "missing_traceability"
        status = "fail" if malformed else raw_status
        evidence = [str(evidence) for evidence in raw_evidence if isinstance(evidence, (str, int, float))] if isinstance(raw_evidence, list) else []
        if malformed:
            evidence.append("malformed_check_record")
        checks.append(
            {
                "check_id": check_id,
                "blocker_class": blocker_class,
                "status": status,
                "blocking": malformed or status == "fail" or item.get("blocking") is True,
                "message": str(item.get("message") or item.get("check_id") or "release readiness check"),
                "evidence": evidence,
            }
        )
    return checks


def validate_xplat008_evidence_contracts(
    payload_results: list[dict[str, Any]],
    uat_rows: list[dict[str, Any]],
    repair_actions: list[dict[str, Any]],
    public_claim_results: list[dict[str, Any]],
    runner_invocations: list[dict[str, Any]],
    traceability: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for index, item in enumerate(payload_results):
        problems = malformed_payload_result_fields(item)
        if problems:
            checks.append(malformed_evidence_check("payload-completeness", "incomplete_payload", "payload", index, problems))
    for index, item in enumerate(uat_rows):
        problems = malformed_uat_row_fields(item)
        if problems:
            checks.append(malformed_evidence_check("uat-matrix", "incomplete_uat_evidence", "uat", index, problems))
    for index, item in enumerate(repair_actions):
        problems = malformed_repair_action_fields(item)
        if problems:
            checks.append(malformed_evidence_check("install-health-repair", "unsafe_repair_claim", "repair", index, problems))
    for index, item in enumerate(public_claim_results):
        problems = malformed_public_claim_fields(item)
        if problems:
            checks.append(malformed_evidence_check("public-claims", "unsafe_public_claim", "public_claim", index, problems))
    for index, item in enumerate(runner_invocations):
        problems = malformed_runner_invocation_fields(item)
        if problems:
            checks.append(malformed_evidence_check("runner-invocations", "missing_runner_invocation", "runner_invocation", index, problems))
    for index, item in enumerate(traceability):
        problems = malformed_traceability_fields(item)
        if problems:
            checks.append(malformed_evidence_check("release-packet-traceability", "missing_traceability", "traceability", index, problems))
    return checks


def malformed_evidence_check(check_id: str, blocker_class: str, record_type: str, index: int, problems: list[str]) -> dict[str, Any]:
    return xplat008_check(
        check_id,
        blocker_class,
        False,
        f"Malformed XPLAT-008 {record_type} evidence record.",
        [f"malformed_{record_type}_record:index={index}", *[f"missing_or_invalid={problem}" for problem in problems]],
    )


def malformed_payload_result_fields(item: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    require_enum(item, "payload_surface", {"claude", "codex"}, problems)
    require_enum(item, "status", VALID_STATUS, problems)
    require_pattern(item, "plugin_version", r"^[0-9]+\.[0-9]+\.[0-9]+$", problems)
    require_string(item, "runner_version", problems)
    require_sha256(item, "file_tree_hash", problems)
    for key in ("missing_paths", "extra_paths", "mismatched_paths", "path_leaks"):
        require_string_list(item, key, problems)
    for key in ("expected_files", "actual_files"):
        require_list(item, key, problems)
    if isinstance(item.get("expected_files"), list) and not item.get("expected_files"):
        problems.append("expected_files")
    validate_payload_file_records(item, "expected_files", problems)
    validate_payload_file_records(item, "actual_files", problems)
    return problems


def validate_payload_file_records(item: dict[str, Any], key: str, problems: list[str]) -> None:
    records = item.get(key)
    if not isinstance(records, list):
        return
    for index, record in enumerate(records):
        prefix = f"{key}[{index}]"
        if not isinstance(record, dict):
            problems.append(prefix)
            continue
        path = record.get("path")
        kind = record.get("kind")
        sha256 = record.get("sha256")
        required = record.get("required")
        if not valid_contract_path(path):
            problems.append(f"{prefix}.path")
        if kind not in PAYLOAD_FILE_KINDS:
            problems.append(f"{prefix}.kind")
        if not isinstance(sha256, str) or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
            problems.append(f"{prefix}.sha256")
        if not isinstance(required, bool):
            problems.append(f"{prefix}.required")
        if "source_path" in record and not isinstance(record.get("source_path"), str):
            problems.append(f"{prefix}.source_path")
        if "transform" in record and record.get("transform") not in PAYLOAD_FILE_TRANSFORMS:
            problems.append(f"{prefix}.transform")
        byte_count = record.get("byte_count")
        if "byte_count" in record and (not isinstance(byte_count, int) or byte_count < 0):
            problems.append(f"{prefix}.byte_count")


def malformed_uat_row_fields(item: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    require_enum(item, "product", {"claude", "codex"}, problems)
    require_enum(item, "platform", {"windows", "macos", "linux"}, problems)
    require_enum(item, "status", VALID_STATUS, problems)
    require_string(item, "operator", problems)
    require_pattern(item, "date", r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", problems)
    require_string(item, "host_version", problems)
    require_string(item, "plugin_version_or_latest_tag", problems)
    for key in (
        "install_result",
        "bundled_agent_verification",
        "first_use",
        "scaffold_status",
        "autopilot_dry_run",
        "latest_tag_update",
        "incomplete_install_repair",
    ):
        require_enum(item, key, VALID_STATUS, problems)
    require_string(item, "installed_cache_path", problems)
    require_string(item, "evidence_link", problems)
    evidence_link = item.get("evidence_link")
    if isinstance(evidence_link, str) and re.search(r"<a\s", evidence_link, flags=re.IGNORECASE):
        problems.append("evidence_link")
    runner_ids = item.get("runner_invocation_ids")
    require_list(item, "runner_invocation_ids", problems)
    if isinstance(runner_ids, list) and (not runner_ids or any(not isinstance(value, str) or not value for value in runner_ids)):
        problems.append("runner_invocation_ids")
    for key in ("expected_result", "actual_result", "operator_notes"):
        require_string(item, key, problems)
    if not isinstance(item.get("interpreter_resolution"), dict):
        problems.append("interpreter_resolution")
    return problems


def malformed_repair_action_fields(item: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    require_string(item, "action_id", problems)
    require_string(item, "finding_id", problems)
    require_enum(item, "action_type", REPAIR_ACTION_TYPES, problems)
    require_string(item, "target_path", problems)
    require_enum(item, "status", REPAIR_STATUS, problems)
    require_string(item, "message", problems)
    require_string_list(item, "manual_steps", problems)
    if not isinstance(item.get("digest_verified"), bool):
        problems.append("digest_verified")
    action_type = item.get("action_type")
    source_path = item.get("source_path")
    if action_type == "autoheal_refresh":
        if not isinstance(source_path, str) or not source_path:
            problems.append("source_path")
        if item.get("digest_verified") is not True:
            problems.append("digest_verified")
        if item.get("status") != "completed":
            problems.append("status")
    elif action_type == "manual_remediation":
        if source_path is not None:
            problems.append("source_path")
        if item.get("digest_verified") is not False:
            problems.append("digest_verified")
        if item.get("status") != "blocked":
            problems.append("status")
        if not isinstance(item.get("manual_steps"), list) or not item.get("manual_steps"):
            problems.append("manual_steps")
    elif "source_path" not in item:
        problems.append("source_path")
    return problems


def malformed_public_claim_fields(item: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    require_string(item, "claim_id", problems)
    require_string(item, "surface", problems)
    require_string(item, "claim_text_or_pattern", problems)
    require_string(item, "classification", problems)
    require_enum(item, "status", EVIDENCE_STATUS, problems)
    require_string_list(item, "evidence", problems)
    return problems


def malformed_runner_invocation_fields(item: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    require_string(item, "request_id", problems)
    require_enum(item, "product", {"claude", "codex"}, problems)
    require_enum(item, "platform", {"windows", "macos", "linux"}, problems)
    require_string(item, "surface_path", problems)
    require_enum(item, "operation", RUNNER_OPERATIONS, problems)
    require_enum(item, "status", EVIDENCE_STATUS, problems)
    if not isinstance(item.get("interpreter_resolution"), dict):
        problems.append("interpreter_resolution")
    invocation = item.get("invocation")
    if not isinstance(invocation, dict):
        problems.append("invocation")
    else:
        argv = invocation.get("argv")
        if not isinstance(argv, list) or any(not isinstance(value, str) or not value for value in argv):
            problems.append("invocation.argv")
        elif "-m" not in argv or "speckit_pro_runner" not in argv:
            problems.append("invocation.argv")
        if invocation.get("stdin_mode") != "single_json_request":
            problems.append("invocation.stdin_mode")
        if invocation.get("stdout_mode") != "single_json_response":
            problems.append("invocation.stdout_mode")
        if invocation.get("stderr_mode") != "diagnostics_only":
            problems.append("invocation.stderr_mode")
        if invocation.get("shell_used") is not False:
            problems.append("invocation.shell_used")
    runner_request = item.get("runner_request")
    if not isinstance(runner_request, dict):
        problems.append("runner_request")
    else:
        if runner_request.get("operation") != "runtime-info":
            problems.append("runner_request.operation")
        if runner_request.get("mode") != "read_only":
            problems.append("runner_request.mode")
        if not isinstance(runner_request.get("inputs"), dict):
            problems.append("runner_request.inputs")
    runner_response = item.get("runner_response")
    if item.get("status") == "pass" and (not isinstance(runner_response, dict) or runner_response.get("status") != "ok"):
        problems.append("runner_response")
    require_diagnostic_list(item, "diagnostics", problems)
    return problems


def malformed_traceability_fields(item: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    require_pattern(item, "requirement_id", r"^(FR|SC)-[0-9]{3}$", problems)
    require_string_list(item, "changed_files", problems)
    require_string_list(item, "verification_evidence", problems)
    return problems


def require_string(item: dict[str, Any], key: str, problems: list[str]) -> None:
    if not isinstance(item.get(key), str) or not item.get(key):
        problems.append(key)


def require_pattern(item: dict[str, Any], key: str, pattern: str, problems: list[str]) -> None:
    value = item.get(key)
    if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
        problems.append(key)


def require_sha256(item: dict[str, Any], key: str, problems: list[str]) -> None:
    require_pattern(item, key, r"^[0-9a-f]{64}$", problems)


def require_list(item: dict[str, Any], key: str, problems: list[str]) -> None:
    if not isinstance(item.get(key), list):
        problems.append(key)


def require_string_list(item: dict[str, Any], key: str, problems: list[str]) -> None:
    values = item.get(key)
    if not isinstance(values, list):
        problems.append(key)
        return
    if any(not isinstance(value, str) or not value for value in values):
        problems.append(key)


def require_diagnostic_list(item: dict[str, Any], key: str, problems: list[str]) -> None:
    values = item.get(key)
    if not isinstance(values, list):
        problems.append(key)
        return
    for index, value in enumerate(values):
        prefix = f"{key}[{index}]"
        if not isinstance(value, dict):
            problems.append(prefix)
            continue
        if value.get("severity") not in {"info", "warning", "error"}:
            problems.append(f"{prefix}.severity")
        if not isinstance(value.get("code"), str) or not value.get("code"):
            problems.append(f"{prefix}.code")
        if not isinstance(value.get("message"), str) or not value.get("message"):
            problems.append(f"{prefix}.message")


def require_enum(item: dict[str, Any], key: str, allowed: set[str], problems: list[str]) -> None:
    if item.get(key) not in allowed:
        problems.append(key)


def valid_contract_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    first_segment = value.split("/", 1)[0]
    return not (value.startswith("/") or ".." in value.split("/") or ":" in first_segment)


def computed_xplat008_checks(
    payload_results: list[dict[str, Any]],
    uat_rows: list[dict[str, Any]],
    repair_actions: list[dict[str, Any]],
    public_claim_results: list[dict[str, Any]],
    runner_invocations: list[dict[str, Any]],
    traceability: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payload_failures = [
        str(item.get("payload_surface") or "unknown-payload")
        for item in payload_results
        if item.get("status") != "pass"
    ]
    payload_surfaces = {item.get("payload_surface") for item in payload_results if item.get("status") == "pass"}
    uat_failures = [f"{item.get('product')}:{item.get('platform')}" for item in uat_rows if item.get("status") != "pass"]
    uat_keys = [
        (item.get("product"), item.get("platform"))
        for item in uat_rows
        if isinstance(item.get("product"), str) and isinstance(item.get("platform"), str)
    ]
    uat_key_set = set(uat_keys)
    required_uat = set(XPLAT008_REQUIRED_UAT_ROWS)
    missing_uat = sorted(required_uat - uat_key_set)
    unexpected_uat = sorted(uat_key_set - required_uat)
    duplicate_uat = sorted(key for key in uat_key_set if uat_keys.count(key) > 1)
    uat_complete = len(uat_rows) == len(required_uat) and not missing_uat and not unexpected_uat and not duplicate_uat
    repair_failures = [
        str(item.get("action_id") or "unknown-repair-action")
        for item in repair_actions
        if item.get("action_type") == "manual_remediation" or item.get("status") == "blocked"
    ]
    claim_failures = [
        str(item.get("claim_id") or "unknown-public-claim")
        for item in public_claim_results
        if item.get("status") != "pass"
    ]
    runner_failures = [
        str(item.get("request_id") or "unknown-runner-invocation")
        for item in runner_invocations
        if item.get("status") != "pass"
    ]
    missing_traceability = not traceability
    return [
        xplat008_check(
            "payload-completeness",
            "incomplete_payload",
            {"claude", "codex"} <= payload_surfaces and not payload_failures,
            "Payload completeness covers Claude and Codex generated payloads.",
            [
                f"surfaces={','.join(sorted(str(item) for item in payload_surfaces)) if payload_surfaces else 'none'}",
                f"failing_payloads={','.join(payload_failures) if payload_failures else 'none'}",
            ],
        ),
        xplat008_check(
            "uat-matrix",
            "incomplete_uat_evidence",
            uat_complete and not uat_failures,
            "Native UAT matrix has exactly six passing product/platform rows.",
            [
                f"rows={len(uat_rows)}",
                f"missing_rows={','.join(f'{product}:{platform}' for product, platform in missing_uat) if missing_uat else 'none'}",
                f"unexpected_rows={','.join(f'{product}:{platform}' for product, platform in unexpected_uat) if unexpected_uat else 'none'}",
                f"duplicate_rows={','.join(f'{product}:{platform}' for product, platform in duplicate_uat) if duplicate_uat else 'none'}",
                f"failing_rows={','.join(uat_failures) if uat_failures else 'none'}",
            ],
        ),
        xplat008_check(
            "install-health-repair",
            "unsafe_repair_claim",
            not repair_failures,
            "Install-health repair evidence contains no unsafe repair claims.",
            [f"blocked_repairs={','.join(repair_failures) if repair_failures else 'none'}"],
        ),
        xplat008_check(
            "public-claims",
            "unsafe_public_claim",
            bool(public_claim_results) and not claim_failures,
            "Public claims are backed by implemented controls.",
            [f"blocked_claims={','.join(claim_failures) if claim_failures else 'none'}"],
        ),
        xplat008_check(
            "runner-invocations",
            "missing_runner_invocation",
            bool(runner_invocations) and not runner_failures,
            "Installed runner invocation evidence is present and passing.",
            [
                f"count={len(runner_invocations)}",
                f"failing_runner_invocations={','.join(str(item) for item in runner_failures) if runner_failures else 'none'}",
            ],
        ),
        xplat008_check(
            "release-packet-traceability",
            "missing_traceability",
            not missing_traceability,
            "Release packet maps requirements to changed files and verification evidence.",
            [f"traceability_count={len(traceability)}"],
        ),
    ]


def collapse_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    collapsed: dict[str, dict[str, Any]] = {}
    for check in checks:
        check_id = str(check.get("check_id") or "release-packet-traceability")
        check["check_id"] = check_id
        check.setdefault("blocker_class", "missing_traceability")
        check.setdefault("message", check_id)
        check.setdefault("evidence", [])
        check["blocking"] = check.get("blocking") is True or check.get("status") == "fail"
        check["status"] = "fail" if check["blocking"] else "pass"
        existing = collapsed.get(check_id)
        if existing is None:
            collapsed[check_id] = check
            continue
        existing["evidence"].extend(check["evidence"])
        if check["blocking"]:
            existing["status"] = "fail"
            existing["blocking"] = True
            existing["message"] = check["message"]
            existing["blocker_class"] = check["blocker_class"]
    return list(collapsed.values())


def xplat008_check(check_id: str, blocker_class: str, ok: bool, message: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "blocker_class": blocker_class,
        "status": "pass" if ok else "fail",
        "blocking": not ok,
        "message": message,
        "evidence": evidence,
    }


def normalize_payload_results(raw: Any) -> list[dict[str, Any]]:
    return normalize_evidence_records(raw, "payload")


def project_payload_results(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    projected_by_surface: dict[str, dict[str, Any]] = {}
    for item in records:
        surface = item.get("payload_surface")
        if surface not in {"claude", "codex"}:
            continue
        projected_by_surface[surface] = project_payload_result(item)
    return [projected_by_surface[surface] for surface in ("claude", "codex") if surface in projected_by_surface]


def project_payload_result(item: dict[str, Any]) -> dict[str, Any]:
    projected = {key: copy.deepcopy(value) for key, value in item.items() if key in PAYLOAD_RESULT_KEYS}
    for key in ("expected_files", "actual_files"):
        value = projected.get(key)
        if isinstance(value, list):
            projected[key] = [project_payload_file_record(record) if isinstance(record, dict) else record for record in value]
    return projected


def project_payload_file_record(record: dict[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(value) for key, value in record.items() if key in PAYLOAD_FILE_KEYS}


def synthetic_payload_result(surface: str, status: str) -> dict[str, Any]:
    file_record = {
        "path": ".claude-plugin/plugin.json" if surface == "claude" else ".codex-plugin/plugin.json",
        "kind": "manifest",
        "sha256": "1" * 64,
        "required": True,
    }
    return {
        "payload_surface": surface,
        "plugin_version": "2.17.0",
        "runner_version": "0.1.0",
        "expected_files": [file_record],
        "actual_files": [file_record] if status == "pass" else [],
        "missing_paths": [] if status == "pass" else [file_record["path"]],
        "extra_paths": [],
        "mismatched_paths": [],
        "path_leaks": [],
        "file_tree_hash": "2" * 64,
        "status": status,
    }


def normalize_uat_rows(raw: Any) -> list[dict[str, Any]]:
    return normalize_evidence_records(raw, "uat")


def default_uat_row(product: str, platform: str, status: str) -> dict[str, Any]:
    return {
        "product": product,
        "platform": platform,
        "operator": "fixture",
        "date": "2026-07-05",
        "host_version": f"{platform}-fixture",
        "plugin_version_or_latest_tag": "2.17.0",
        "installed_cache_path": f"fixture/{product}/{platform}/speckit-pro",
        "interpreter_resolution": {"accepted": True, "minimum_version": "3.11"},
        "runner_invocation_ids": [f"xplat-008-runner-invocation-{product}-{platform}"],
        "install_result": status,
        "bundled_agent_verification": status,
        "first_use": status,
        "scaffold_status": status,
        "autopilot_dry_run": status,
        "latest_tag_update": status,
        "incomplete_install_repair": status,
        "expected_result": "Installed runtime uses Python runner without shell fallback.",
        "actual_result": "Fixture row passed." if status == "pass" else "Fixture row failed.",
        "evidence_link": f"specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/uat/{product}-{platform}.md",
        "operator_notes": "Fixture evidence for release gate coverage.",
        "status": status,
    }


def normalize_repair_actions(raw: Any) -> list[dict[str, Any]]:
    return normalize_evidence_records(raw, "repair")


def normalize_public_claim_results(raw: Any) -> list[dict[str, Any]]:
    return normalize_evidence_records(raw, "public_claim")


def normalize_runner_invocations(raw: Any) -> list[dict[str, Any]]:
    return normalize_evidence_records(raw, "runner_invocation")


def normalize_traceability(raw: Any) -> list[dict[str, Any]]:
    return normalize_evidence_records(raw, "traceability")


def normalize_evidence_records(raw: Any, record_type: str) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    records: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            records.append(item)
        else:
            records.append({"__malformed_record_type": record_type, "__raw_type": type(item).__name__})
    return records


def build_check(operation: str, case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if operation == "detect-changed-plugin":
        changed_files = [item for item in case.get("changed_files", []) if isinstance(item, str)]
        changed = any(is_plugin_change(path) for path in changed_files)
        expected = case.get("expected_changed_plugin")
        ok = expected is None or (isinstance(expected, bool) and changed == expected)
        return check_record(operation, ok, [f"changed_plugin={str(changed).lower()}"]), {
            "changed_plugin": {"changed": changed, "changed_files": changed_files}
        }

    if operation == "aggregate-suite-results":
        suite_results = [item for item in case.get("suite_results", []) if isinstance(item, dict)]
        failures = [str(item.get("suite")) for item in suite_results if item.get("status") != "ok"]
        summary = {"total": len(suite_results), "passed": len(suite_results) - len(failures), "failed": len(failures)}
        return check_record(operation, not failures, [f"failed={','.join(failures) if failures else 'none'}"]), {"suite_results": {"summary": summary, "results": suite_results}}

    if operation == "check-marketplace-version-sync":
        versions = case.get("marketplace_versions", {})
        values = [value for value in versions.values() if isinstance(value, str)] if isinstance(versions, dict) else []
        ok = bool(values) and len(set(values)) == 1
        return check_record(operation, ok, [f"versions={','.join(values)}"]), {"marketplace_versions": versions if isinstance(versions, dict) else {}}

    if operation == "validate-pr-title":
        title = str(case.get("pr_title", ""))
        ok = re.match(r"^(feat|fix|chore|docs|test|refactor)\([a-z0-9-]+\): .+", title) is not None
        return check_record(operation, ok, [title or "missing title"]), {"pr_title": title}

    if operation == "validate-workflow-contract":
        contract = case.get("workflow_contract", {})
        ok = isinstance(contract, dict) and contract.get("uses_runner") is True and contract.get("uses_shell") is False
        operations = contract.get("operations", []) if isinstance(contract, dict) else []
        return check_record(operation, ok, [f"uses_runner={contract.get('uses_runner') if isinstance(contract, dict) else None}", f"uses_shell={contract.get('uses_shell') if isinstance(contract, dict) else None}"]), {
            "workflow_contract": {"operations": operations, "uses_runner": bool(isinstance(contract, dict) and contract.get("uses_runner") is True)}
        }

    if operation == "check-payload-evidence":
        payloads = [item for item in case.get("payload_evidence", []) if isinstance(item, dict)]
        stale = [str(item.get("evidence_id")) for item in payloads if item.get("stale") is True or item.get("release_payload_cutover") is not False]
        return check_record(operation, not stale and bool(payloads), [f"stale={','.join(stale) if stale else 'none'}"]), {"payload_evidence": payloads}

    if operation == "parse-release-pr-payload-sync":
        body = str(case.get("release_pr_body", ""))
        expected_ids = payload_evidence_ids(case)
        missing = [item for item in expected_ids if item not in body]
        return check_record(operation, not missing and bool(expected_ids), [f"missing={','.join(missing) if missing else 'none'}"]), {
            "release_pr_payload_sync": {"payload_ids": sorted(set(expected_ids) - set(missing)), "missing_payload_ids": missing}
        }

    if operation == "check-post-release-drift":
        drift = case.get("post_release", {})
        ok = isinstance(drift, dict) and drift.get("drift") is False and drift.get("current_version") == drift.get("expected_version")
        return check_record(operation, ok, [json.dumps(drift, sort_keys=True, separators=(",", ":")) if isinstance(drift, dict) else "invalid"]), {
            "post_release_drift": drift if isinstance(drift, dict) else {}
        }

    return check_record(operation, False, ["unknown operation"]), {}


def check_record(check_id: str, ok: bool, evidence: list[str]) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "pass" if ok else "fail",
        "blocking": not ok,
        "evidence": evidence,
    }


def is_plugin_change(path: str) -> bool:
    plugin_prefixes = (
        "speckit-pro/",
        ".claude-plugin/",
        ".codex-plugin/",
        "tests/speckit-pro/",
    )
    ignored_prefixes = (
        "specs/",
        "docs-site/",
        "docs/",
    )
    if path.startswith(ignored_prefixes):
        return False
    return path.startswith(plugin_prefixes)


def payload_evidence_ids(case: dict[str, Any]) -> list[str]:
    return [
        str(item.get("evidence_id"))
        for item in case.get("payload_evidence", [])
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
    ]


def install_verification_ids(case: dict[str, Any]) -> list[str]:
    return [
        str(item.get("verification_id"))
        for item in case.get("install_verifications", [])
        if isinstance(item, dict) and isinstance(item.get("verification_id"), str)
    ]


def active_path_guard_summary(case: dict[str, Any]) -> dict[str, Any]:
    guard = case.get("active_path_guard", {})
    if not isinstance(guard, dict):
        return {"status": "input_error", "blocking_count": 1}
    status = guard.get("status") if guard.get("status") in {"ok", "expected_failure", "input_error"} else "input_error"
    blocking_count = guard.get("blocking_count")
    if not isinstance(blocking_count, int) or blocking_count < 0:
        blocking_count = 1
    return {"status": status, "blocking_count": blocking_count}


def xplat_008_handoff_items(case: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in case.get("xplat_008_handoff_items", []):
        if not isinstance(item, dict):
            continue
        items.append(
            {
                "item_id": str(item.get("item_id")),
                "category": str(item.get("category")),
                "owner_spec": "XPLAT-008",
                "required_before_public_claim": item.get("required_before_public_claim") is not False,
            }
        )
    return items


def load_release_case(repo_root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("case_file", DEFAULT_CASE_FILE)
    if not isinstance(raw, str) or not raw:
        return diagnostic("invalid_case_file", "case_file must be a non-empty string")
    path = resolve_path(raw, repo_root)
    if not is_relative_to(path.resolve(strict=False), repo_root.resolve(strict=False)):
        return diagnostic("invalid_case_file", "case_file must stay inside the repository")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return diagnostic(
            "invalid_case_file",
            "release readiness case fixture could not be loaded",
            details={"case_file": raw, "error": type(exc).__name__},
        )

    cases = document.get("cases")
    if not isinstance(cases, list):
        return diagnostic("invalid_case_file", "release readiness case fixture must contain cases")
    case_id = inputs.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        case_id = "ready"
    selected = next((item for item in cases if isinstance(item, dict) and item.get("case_id") == case_id), None)
    if selected is None:
        return diagnostic("unknown_fixture_case", "release readiness fixture case was not found", details={"case_id": case_id})

    base = copy.deepcopy(document.get("base_case", {}))
    if not isinstance(base, dict):
        base = {}
    overrides = selected.get("overrides")
    if isinstance(overrides, dict):
        deep_merge(base, overrides)
    base["case_id"] = case_id
    base["expected_status"] = selected.get("expected_status")
    base["_required_promotion_operations"] = [
        item for item in document.get("required_promotion_operations", []) if isinstance(item, str)
    ]
    github_context = inputs.get("github_context")
    if isinstance(github_context, dict) and github_context.get("enabled") is True:
        live_overrides = github_context_overrides(repo_root, github_context)
        if is_diagnostic(live_overrides):
            return live_overrides
        deep_merge(base, live_overrides)
    return base


def load_xplat008_release_case(repo_root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("case_file", XPLAT_008_RELEASE_CASE_FILE)
    if not isinstance(raw, str) or not raw:
        return diagnostic("invalid_case_file", "case_file must be a non-empty string")
    path = resolve_path(raw, repo_root)
    if not is_relative_to(path.resolve(strict=False), repo_root.resolve(strict=False)):
        return diagnostic("invalid_case_file", "case_file must stay inside the repository")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return diagnostic(
            "invalid_case_file",
            "XPLAT-008 release-readiness case fixture could not be loaded",
            details={"case_file": raw, "error": type(exc).__name__},
        )

    cases = document.get("cases")
    if not isinstance(cases, list):
        return diagnostic("invalid_case_file", "XPLAT-008 release readiness fixture must contain cases")
    case_id = inputs.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        case_id = "ready"
    selected = next((item for item in cases if isinstance(item, dict) and item.get("case_id") == case_id), None)
    if selected is None:
        return diagnostic("unknown_fixture_case", "XPLAT-008 release readiness fixture case was not found", details={"case_id": case_id})

    base = copy.deepcopy(document.get("base_case", {}))
    if not isinstance(base, dict):
        base = {}
    overrides = selected.get("overrides")
    if isinstance(overrides, dict):
        deep_merge(base, overrides)
    base["case_id"] = case_id
    base["expected_status"] = selected.get("expected_status")
    return base


def github_context_overrides(repo_root: Path, context: dict[str, Any]) -> dict[str, Any]:
    title_env = str(context.get("title_env") or "TITLE")
    title = os.environ.get(title_env, "")
    if not title:
        return diagnostic(
            "missing_github_context",
            "live release-readiness request could not read the PR title environment variable",
            details={"title_env": title_env},
            remediation_summary="Provide the GitHub PR title to the runner request environment.",
            remediation_actions=[f"Set {title_env} before dispatching the release-readiness runner gate."],
        )

    changed_files = github_changed_files(repo_root, context)
    if is_diagnostic(changed_files):
        return changed_files

    overrides: dict[str, Any] = {
        "pr_title": title,
        "changed_files": changed_files,
        "expected_changed_plugin": any(is_plugin_change(path) for path in changed_files),
    }
    workflow_contract = context.get("workflow_contract")
    if isinstance(workflow_contract, dict):
        overrides["workflow_contract"] = copy.deepcopy(workflow_contract)
    return overrides


def github_changed_files(repo_root: Path, context: dict[str, Any]) -> list[str] | dict[str, Any]:
    fixture_files = context.get("changed_files")
    if isinstance(fixture_files, list) and all(isinstance(item, str) for item in fixture_files):
        return list(fixture_files)

    base_ref_env = str(context.get("base_ref_env") or "BASE_REF")
    base_ref = os.environ.get(base_ref_env) or str(context.get("base_ref") or "main")
    diff_range = f"origin/{base_ref}...HEAD"
    completed = subprocess.run(
        ["git", "diff", "--name-only", diff_range],
        cwd=repo_root,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        return diagnostic(
            "github_changed_files_unavailable",
            "live release-readiness request could not determine changed files",
            details={"base_ref": base_ref, "stderr": completed.stderr[-400:]},
            remediation_summary="Fetch the base ref before dispatching the release-readiness runner gate.",
            remediation_actions=["Use actions/checkout with fetch-depth: 0.", f"Ensure origin/{base_ref} is available."],
        )
    return [line for line in completed.stdout.splitlines() if line]


def deep_merge(target: dict[str, Any], overrides: dict[str, Any]) -> None:
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    gate_status = "pass"
    if status in {"expected_failure", "subprocess_failure"}:
        gate_status = "fail"
    elif status == "missing_prerequisite":
        gate_status = "skipped"
    elif status == "input_error":
        gate_status = "input_error"
    return {
        "gate": {
            "gate_id": entry.helper_id,
            "operation": operation,
            "gate_status": gate_status,
            "promoted": status != "input_error",
            "blocking": status != "ok",
            "comparison_ids": [f"us2-{operation}"],
            "promotion_record": PROMOTION_RECORD,
        },
        "artifacts": [{"path": PROMOTION_RECORD, "kind": "fixture"}],
    }


def xplat008_base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    data = base_data(entry, operation, status)
    data["gate"]["comparison_ids"] = ["xplat-008-release-readiness"]
    data["gate"]["promotion_record"] = XPLAT_008_PROMOTION_RECORD
    data["artifacts"] = [
        {"path": XPLAT_008_PROMOTION_RECORD, "kind": "promotion_record"},
        {"path": XPLAT_008_RELEASE_CASE_FILE, "kind": "fixture"},
    ]
    return data


def find_repo_root(start: Path) -> Path | None:
    candidates = [start, *start.parents] if start.is_dir() else [start.parent, *start.parent.parents]
    for candidate in candidates:
        if (candidate / "speckit-pro" / "speckit_pro_runner").is_dir() and (candidate / "tests" / "speckit-pro").is_dir():
            return candidate.resolve(strict=False)
    return None


def resolve_path(raw: str, repo_root: Path) -> Path:
    path = Path(raw.replace("\\", "/"))
    return path if path.is_absolute() else repo_root / path


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def is_diagnostic(value: Any) -> bool:
    return isinstance(value, dict) and value.get("source") == "runner" and "code" in value
