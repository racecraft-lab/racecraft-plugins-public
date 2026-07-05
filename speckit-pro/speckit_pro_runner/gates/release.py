"""Release-readiness gate operations for XPLAT-007 US2."""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response

PROMOTION_RECORD = "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json"
DEFAULT_CASE_FILE = "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/release-readiness-cases.json"
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
