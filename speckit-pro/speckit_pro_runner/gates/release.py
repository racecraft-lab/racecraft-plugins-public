"""Release-readiness gate operations."""

from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from ..envelope import diagnostic, is_diagnostic, response
from ..path_utils import find_repo_root
from .gate_response import gate_base_data

INSTALLED_RELEASE_CHECK_IDS = {
    "active-runtime-guard",
    "payload-completeness",
    "runner-invocations",
    "version-sync",
    "zero-bash-guard",
    "repo_bash_confinement",
}
INSTALLED_RELEASE_BLOCKER_CLASSES = {
    "active_shell_runtime_dependency",
    "active_zero_bash_dependency",
    "active_repo_bash_dependency",
    "incomplete_payload",
    "missing_runner_invocation",
    "stale_metadata",
}
VALID_STATUS = {"pass", "fail"}
EVIDENCE_STATUS = {"pass", "fail", "blocked"}
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
    "script_file_count",
    "file_tree_hash",
    "status",
}
PAYLOAD_FILE_KEYS = {"path", "source_path", "kind", "transform", "sha256", "byte_count", "required"}
PAYLOAD_FILE_KINDS = {"manifest", "skill", "agent", "hook", "runner", "install_guidance", "trust_metadata", "checksum", "version_metadata", "docs"}
PAYLOAD_FILE_TRANSFORMS = {"none", "claude_guard_strip", "codex_overlay", "path_normalization", "manifest_rewrite"}
RELEASE_INPUT_FIELDS = {
    "installed-release-readiness": frozenset(),
    "validate-pr-title": frozenset({"title_env"}),
}

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

    allowed_fields = RELEASE_INPUT_FIELDS.get(request.operation)
    if allowed_fields is not None:
        unknown_fields = sorted(set(request.inputs) - allowed_fields)
        if unknown_fields:
            diag = diagnostic(
                "unsupported_gate_inputs",
                "release gate received unsupported input fields",
                details={"fields": unknown_fields},
            )
            return response(
                "input_error",
                request_id=request.request_id,
                data=base_data(entry, request.operation, "input_error"),
                diagnostics=[diag],
            )

    if request.operation == "installed-release-readiness":
        return installed_release_readiness(entry, request, repo_root)
    if request.operation != "validate-pr-title":
        diag = diagnostic(
            "unknown_gate_operation",
            "release gate operation is not implemented by the release module",
            details={"operation": request.operation},
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])
    title_env = request.inputs.get("title_env", "TITLE")
    if not isinstance(title_env, str) or not title_env:
        diag = diagnostic("invalid_title_env", "title_env must be a non-empty string")
        return response(
            "input_error",
            request_id=request.request_id,
            data=base_data(entry, request.operation, "input_error"),
            diagnostics=[diag],
        )
    title = os.environ.get(title_env, "")
    check = check_record(
        "validate-pr-title",
        re.match(r"^(feat|fix|chore|docs|test|refactor)\([a-z0-9-]+\): .+", title) is not None,
        [title or "missing title"],
    )
    status = "ok" if check["status"] == "pass" else "expected_failure"
    data = base_data(entry, request.operation, status)
    data["release_check"] = check
    data["pr_title"] = title
    if status == "ok":
        return response("ok", request_id=request.request_id, data=data)
    data["gate"]["gate_status"] = "fail"
    data["gate"]["blocking"] = True
    diag = diagnostic(
        "release_check_failed",
        "pull-request title does not satisfy the release contract",
        details={"check_id": check["check_id"], "evidence": check["evidence"]},
        remediation_summary="Use the required Conventional Commit title format.",
        remediation_actions=["Set the PR title to <type>(<lowercase-scope>): <description>.", "Retry the same runner request."],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def installed_release_readiness(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    live_evidence = live_installed_release_gate_evidence(repo_root)
    payload_evidence_records = normalize_payload_results(live_evidence.get("payload_results"))
    payload_results = project_payload_results(payload_evidence_records)
    runner_invocations = normalize_runner_invocations(live_evidence.get("runner_invocations"))
    checks = normalize_installed_release_checks(live_evidence.get("checks"))

    checks.extend(
        computed_installed_release_checks(
            payload_evidence_records,
            runner_invocations,
        )
    )
    checks.extend(
        validate_installed_release_evidence_contracts(
            payload_results,
            runner_invocations,
        )
    )
    checks = collapse_checks(checks)
    blocking_count = sum(1 for check in checks if check["blocking"])

    readiness = {
        "schema_version": "2.0",
        "contract_id": "installed-plugin-release",
        "status": "pass" if blocking_count == 0 else "fail",
        "blocking_count": blocking_count,
        "checks": checks,
        "payload_results": payload_results,
        "runner_invocations": runner_invocations,
    }

    status = "ok" if blocking_count == 0 else "expected_failure"
    data = installed_release_base_data(entry, request.operation, status)
    data["release_readiness"] = readiness
    if status == "ok":
        return response("ok", request_id=request.request_id, data=data)

    data["gate"]["gate_status"] = "fail"
    data["gate"]["blocking"] = True
    diag = diagnostic(
        "installed_release_readiness_blocked",
        "installed-plugin release readiness has blocking checks",
        details={"blocking_count": blocking_count},
        remediation_summary="Resolve the live installed-plugin release blockers before release.",
        remediation_actions=["Inspect data.release_readiness.checks.", "Retry the installed-release-readiness request after updating evidence."],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def live_installed_release_gate_evidence(repo_root: Path) -> dict[str, Any]:
    from . import active_path_guard, payloads as payload_gate
    from ..helpers import install as install_helper

    evidence: dict[str, Any] = {"checks": [], "payload_results": [], "runner_invocations": []}

    active_response = active_path_guard.run_active_runtime_guard(
        SimpleNamespace(helper_id="active-path-guard"),
        SimpleNamespace(
            operation="active-runtime-guard",
            request_id="installed-release-readiness:active-runtime-guard",
            mode="read_only",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
                "case_id": "final-current-implementation",
            },
        ),
        repo_root,
    )
    active_data = active_response.get("data") if isinstance(active_response, dict) else {}
    active_blocking = active_response.get("status") != "ok" if isinstance(active_response, dict) else True
    active_count = active_data.get("blocking_count") if isinstance(active_data, dict) else None
    evidence["checks"].append(
        installed_release_check(
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

    zero_bash_response = active_path_guard.run_zero_bash_guard(
        SimpleNamespace(helper_id="active-path-guard"),
        SimpleNamespace(
            operation="zero-bash-guard",
            request_id="installed-release-readiness:zero-bash-guard",
            mode="read_only",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/zero-bash-guard-cases.json",
                "case_id": "final-current-implementation",
            },
        ),
        repo_root,
    )
    zero_bash_data = zero_bash_response.get("data") if isinstance(zero_bash_response, dict) else {}
    zero_bash_blocking = zero_bash_response.get("status") != "ok" if isinstance(zero_bash_response, dict) else True
    zero_bash_count = zero_bash_data.get("blocking_count") if isinstance(zero_bash_data, dict) else None
    evidence["checks"].append(
        installed_release_check(
            "zero-bash-guard",
            "active_zero_bash_dependency",
            not zero_bash_blocking and zero_bash_count == 0,
            "Live plugin Bash-confinement guard completed for source and Claude/Codex payloads.",
            [
                f"zero_bash_status={zero_bash_response.get('status', 'missing') if isinstance(zero_bash_response, dict) else 'missing'}",
                f"zero_bash_blocking_count={zero_bash_count if isinstance(zero_bash_count, int) else 'unknown'}",
            ],
        )
    )

    repo_bash_response = active_path_guard.run_repo_bash_confinement(
        SimpleNamespace(helper_id="active-path-guard"),
        SimpleNamespace(
            operation="repo-bash-confinement",
            request_id="repository-bash-confinement:release-readiness:repo-bash-confinement",
            mode="read_only",
            inputs={
                "allowlist_file": "tests/speckit-pro/unit/fixtures/repository-bash-confinement/allowlist.json",
            },
        ),
        repo_root,
    )
    repo_bash_data = repo_bash_response.get("data") if isinstance(repo_bash_response, dict) else {}
    repo_bash_blocking = repo_bash_response.get("status") != "ok" if isinstance(repo_bash_response, dict) else True
    repo_bash_count = repo_bash_data.get("blocking_count") if isinstance(repo_bash_data, dict) else None
    repo_bash_allowlist = repo_bash_data.get("allowlist") if isinstance(repo_bash_data, dict) else {}
    evidence["checks"].append(
        installed_release_check(
            "repo_bash_confinement",
            "active_repo_bash_dependency",
            not repo_bash_blocking and repo_bash_count == 0,
            "Live repository Bash confinement completed for the tracked source tree.",
            [
                f"repo_bash_status={repo_bash_response.get('status', 'missing') if isinstance(repo_bash_response, dict) else 'missing'}",
                f"repo_bash_blocking_count={repo_bash_count if isinstance(repo_bash_count, int) else 'unknown'}",
                f"allowlist_release_readiness_excluded={repo_bash_allowlist.get('release_readiness_excluded') if isinstance(repo_bash_allowlist, dict) else 'unknown'}",
            ],
        )
    )

    payload_response = payload_gate.installed_plugin_payload_completeness(
        SimpleNamespace(helper_id="payload-gate"),
        SimpleNamespace(
            operation="payload-completeness",
            request_id="installed-release-readiness:payload-completeness",
            mode="read_only",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/payload-completeness-cases.json",
                "case_id": "current-committed-dist",
            },
        ),
        repo_root,
    )
    payload_data = payload_response.get("data") if isinstance(payload_response, dict) else {}
    payload_results = payload_data.get("payload_completeness") if isinstance(payload_data, dict) else None
    if isinstance(payload_results, list):
        evidence["payload_results"].extend(item for item in payload_results if isinstance(item, dict))

    runner_case = install_helper.runner_invocation_case(
        repo_root,
        {
            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/runner-invocation-cases.json",
            "case_id": "live-host-runtime-info",
        },
    )
    if is_diagnostic(runner_case):
        evidence["checks"].append(
            installed_release_check(
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
            "installed-release-readiness:runner-invocation",
            repo_root,
        )
        evidence["runner_invocations"].append(runner_record)

    evidence["checks"].append(live_version_sync_check(repo_root))
    return evidence


def live_version_sync_check(repo_root: Path) -> dict[str, Any]:
    sources = (
        ("speckit-pro/.claude-plugin/plugin.json", ("version",)),
        ("speckit-pro/.codex-plugin/plugin.json", ("version",)),
        (".claude-plugin/marketplace.json", ("plugins", "speckit-pro", "version")),
        (".agents/plugins/marketplace.json", ("plugins", "speckit-pro", "version")),
        (".release-please-manifest.json", ("speckit-pro",)),
        ("speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json", ("plugin_version",)),
    )
    versions = [(path, live_version_value(repo_root / path, selector)) for path, selector in sources]
    values = [value for _path, value in versions]
    synchronized = (
        all(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value or "") is not None for value in values)
        and len(set(values)) == 1
    )
    return installed_release_check(
        "version-sync",
        "stale_metadata",
        synchronized,
        "Current source, marketplace, release, and runner versions are synchronized.",
        [f"{path}={value or 'missing'}" for path, value in versions],
    )


def live_version_value(path: Path, selector: tuple[str, ...]) -> str | None:
    try:
        current: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None
    for key in selector:
        if key == "speckit-pro" and isinstance(current, list):
            current = next(
                (item for item in current if isinstance(item, dict) and item.get("name") == key),
                None,
            )
        elif isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current if isinstance(current, str) and current else None


def normalize_installed_release_checks(raw: Any) -> list[dict[str, Any]]:
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
            raw_check_id not in INSTALLED_RELEASE_CHECK_IDS
            or raw_blocker_class not in INSTALLED_RELEASE_BLOCKER_CLASSES
            or raw_status not in VALID_STATUS
            or not isinstance(raw_evidence, list)
        )
        check_id = raw_check_id if raw_check_id in INSTALLED_RELEASE_CHECK_IDS else "payload-completeness"
        blocker_class = raw_blocker_class if raw_blocker_class in INSTALLED_RELEASE_BLOCKER_CLASSES else "incomplete_payload"
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


def validate_installed_release_evidence_contracts(
    payload_results: list[dict[str, Any]],
    runner_invocations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for index, item in enumerate(payload_results):
        problems = malformed_payload_result_fields(item)
        if problems:
            checks.append(malformed_evidence_check("payload-completeness", "incomplete_payload", "payload", index, problems))
    for index, item in enumerate(runner_invocations):
        problems = malformed_runner_invocation_fields(item)
        if problems:
            checks.append(malformed_evidence_check("runner-invocations", "missing_runner_invocation", "runner_invocation", index, problems))
    return checks


def malformed_evidence_check(check_id: str, blocker_class: str, record_type: str, index: int, problems: list[str]) -> dict[str, Any]:
    return installed_release_check(
        check_id,
        blocker_class,
        False,
        f"Malformed installed-plugin {record_type} evidence record.",
        [f"malformed_{record_type}_record:index={index}", *[f"missing_or_invalid={problem}" for problem in problems]],
    )


def malformed_payload_result_fields(item: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    require_enum(item, "payload_surface", {"claude", "codex"}, problems)
    require_enum(item, "status", VALID_STATUS, problems)
    require_pattern(item, "plugin_version", r"^[0-9]+\.[0-9]+\.[0-9]+$", problems)
    require_string(item, "runner_version", problems)
    require_sha256(item, "file_tree_hash", problems)
    script_file_count = item.get("script_file_count")
    if type(script_file_count) is not int or script_file_count < 0:
        problems.append("script_file_count")
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


def computed_installed_release_checks(
    payload_results: list[dict[str, Any]],
    runner_invocations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payload_failures = [
        str(item.get("payload_surface") or "unknown-payload")
        for item in payload_results
        if item.get("status") != "pass"
    ]
    payload_script_failures = [
        f"{item.get('payload_surface') or 'unknown-payload'}:script_file_count={item.get('script_file_count')}"
        for item in payload_results
        if item.get("script_file_count") != 0
    ]
    payload_surfaces = {item.get("payload_surface") for item in payload_results if item.get("status") == "pass"}
    runner_failures = [
        str(item.get("request_id") or "unknown-runner-invocation")
        for item in runner_invocations
        if item.get("status") != "pass"
    ]
    return [
        installed_release_check(
            "payload-completeness",
            "incomplete_payload",
            {"claude", "codex"} <= payload_surfaces and not payload_failures and not payload_script_failures,
            "Payload completeness covers Claude and Codex generated payloads.",
            [
                f"surfaces={','.join(sorted(str(item) for item in payload_surfaces)) if payload_surfaces else 'none'}",
                f"failing_payloads={','.join(payload_failures) if payload_failures else 'none'}",
                f"scripted_payloads={','.join(payload_script_failures) if payload_script_failures else 'none'}",
            ],
        ),
        installed_release_check(
            "runner-invocations",
            "missing_runner_invocation",
            bool(runner_invocations) and not runner_failures,
            "Installed runner invocation evidence is present and passing.",
            [
                f"count={len(runner_invocations)}",
                f"failing_runner_invocations={','.join(str(item) for item in runner_failures) if runner_failures else 'none'}",
            ],
        ),
    ]


def collapse_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    collapsed: dict[str, dict[str, Any]] = {}
    for check in checks:
        check_id = check["check_id"]
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


def installed_release_check(check_id: str, blocker_class: str, ok: bool, message: str, evidence: list[str]) -> dict[str, Any]:
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


def normalize_runner_invocations(raw: Any) -> list[dict[str, Any]]:
    return normalize_evidence_records(raw, "runner_invocation")


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


def check_record(check_id: str, ok: bool, evidence: list[str]) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "pass" if ok else "fail",
        "blocking": not ok,
        "evidence": evidence,
    }


def base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    return gate_base_data(entry, operation, status)


def installed_release_base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    data = base_data(entry, operation, status)
    data["gate"]["comparison_ids"] = ["installed-plugin-release-readiness"]
    return data
