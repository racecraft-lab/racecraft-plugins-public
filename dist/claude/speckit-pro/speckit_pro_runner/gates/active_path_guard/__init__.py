"""Active-path no-shell/no-jq guard operations.

One module per guard: path_guard (v1.0 active-path guard), runtime_guard
(v2.0 installed-runtime guard), zero_bash, repo_bash, and the python_ast
analyzer. scan holds the path the v1.0 and v2.0 guards share. This module
keeps the entry points and the source-discovery functions they call, so a
test that patches one of those names here reaches the entry points.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from ...envelope import diagnostic, is_diagnostic, response
from ...path_utils import is_relative_to
from .common import (
    MAX_SCAN_BYTES,
    RawFinding,
    SCAN_ROOTS,
    SourceFile,
    TEXT_SUFFIXES,
    bounded_findings,
    classified_counts,
    has_prohibited_script_suffix,
    invalid_scan_root_reason,
    load_case,
    normalize_path,
    read_first_line,
    resolve_repo_root,
    scan_root_entry_validation,
    is_hook_matcher_line as is_hook_matcher_line,
    workflow_run_contexts as workflow_run_contexts,
)
from .python_ast import (
    command_argv_contains_forbidden as command_argv_contains_forbidden,
)
from .path_guard import (
    PATH_GUARD_POLICY,
    base_data,
    scan_sources,
)
from .runtime_guard import (
    INSTALLED_RUNTIME_DEFAULT_CASE_FILE,
    RUNTIME_GUARD_POLICY,
    active_runtime_base_data,
    diff_scan_unavailable_finding,
    installed_runtime_active_role,
    missing_installed_runtime_scan_root_findings,
    scan_installed_runtime_sources,
    classify_installed_runtime_path as classify_installed_runtime_path,
)
from .scan import Hit, classify_hit, policy_guard_response
from .zero_bash import (
    PLUGIN_BASH_CONFINEMENT_ALLOWLIST,
    PLUGIN_BASH_CONFINEMENT_DEFAULT_CASE_FILE,
    has_prohibited_script_shebang_content,
    load_zero_bash_allowlist,
    missing_zero_bash_scan_root_findings,
    zero_bash_allowlist_findings,
    zero_bash_base_data,
    zero_bash_extensionless_scan_path,
    zero_bash_finding_record,
    zero_bash_source_findings,
    zero_bash_classification as zero_bash_classification,
)
from .repo_bash import (
    repo_bash_base_data,
    run_repo_bash_confinement,
    REPOSITORY_BASH_CONFINEMENT_ALLOWLIST_PATHS as REPOSITORY_BASH_CONFINEMENT_ALLOWLIST_PATHS,
    REPO_BASH_COMMAND_NAMES as REPO_BASH_COMMAND_NAMES,
    repo_bash_classify_native_execution as repo_bash_classify_native_execution,
    repo_bash_instruction_findings as repo_bash_instruction_findings,
    repo_bash_json_findings as repo_bash_json_findings,
    repo_bash_python_findings as repo_bash_python_findings,
    repo_bash_runtime_diagnostic_findings as repo_bash_runtime_diagnostic_findings,
    repo_bash_workflow_dispatch_path_failure as repo_bash_workflow_dispatch_path_failure,
    repo_bash_workflow_findings as repo_bash_workflow_findings,
    repo_bash_workflow_run_failure as repo_bash_workflow_run_failure,
)


__all__ = ("run_active_path_guard",)
ACTIVE_PATH_INPUT_FIELDS = {
    "active-path-guard": frozenset({"case_file", "case_id", "repo_root"}),
    "active-runtime-guard": frozenset({"case_file", "case_id", "repo_root"}),
    "classify-shell-finding": frozenset({"category", "line", "path", "repo_root", "text"}),
    "repo-bash-confinement": frozenset(
        {"allowlist_file", "case_file", "case_id", "repo_root"}
    ),
    "zero-bash-guard": frozenset({"case_file", "case_id", "repo_root"}),
}


def run_active_path_guard(entry: Any, request: Any) -> dict[str, Any]:
    repo_root_result = resolve_repo_root(request.inputs)
    if isinstance(repo_root_result, dict):
        status = "missing_prerequisite" if repo_root_result["code"] == "missing_prerequisite" else "input_error"
        data = (
            active_runtime_base_data(entry, request.operation, status)
            if request.operation == "active-runtime-guard"
            else zero_bash_base_data(entry, request.operation, status)
            if request.operation == "zero-bash-guard"
            else repo_bash_base_data(entry, request.operation, status, request.inputs)
            if request.operation == "repo-bash-confinement"
            else base_data(entry, request.operation, status)
        )
        return response(status, request_id=request.request_id, data=data, diagnostics=[repo_root_result])
    repo_root = repo_root_result

    allowed_fields = ACTIVE_PATH_INPUT_FIELDS.get(request.operation)
    if allowed_fields is not None:
        unknown_fields = sorted(set(request.inputs) - allowed_fields)
        if unknown_fields:
            diag = diagnostic(
                "unsupported_gate_inputs",
                "active-path gate received unsupported input fields",
                details={"fields": unknown_fields},
            )
            data = (
                zero_bash_base_data(entry, request.operation, "input_error")
                if request.operation == "zero-bash-guard"
                else repo_bash_base_data(entry, request.operation, "input_error", request.inputs)
                if request.operation == "repo-bash-confinement"
                else base_data(entry, request.operation, "input_error")
            )
            return response(
                "input_error",
                request_id=request.request_id,
                data=data,
                diagnostics=[diag],
            )

    if request.operation == "active-runtime-guard":
        return run_active_runtime_guard(entry, request, repo_root)

    if request.operation == "zero-bash-guard":
        return run_zero_bash_guard(entry, request, repo_root)

    if request.operation == "repo-bash-confinement":
        return run_repo_bash_confinement(entry, request, repo_root)

    if request.operation == "classify-shell-finding":
        return classify_shell_finding(entry, request, repo_root)
    if request.operation != "active-path-guard":
        diag = diagnostic("unknown_gate_operation", "active-path guard operation is not implemented", details={"operation": request.operation})
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])

    case_result = load_case(repo_root, request.inputs)
    if is_diagnostic(case_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[case_result])
    case = case_result

    source_result = source_files(repo_root, case)
    if is_diagnostic(source_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[source_result])

    findings = scan_sources(source_result, repo_root)
    return policy_guard_response(PATH_GUARD_POLICY, entry, request, findings)


def run_active_runtime_guard(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    case_result = load_case(repo_root, request.inputs, default_case_file=INSTALLED_RUNTIME_DEFAULT_CASE_FILE)
    if is_diagnostic(case_result):
        return response(
            "input_error",
            request_id=request.request_id,
            data=active_runtime_base_data(entry, request.operation, "input_error"),
            diagnostics=[case_result],
        )
    source_result = source_files(repo_root, case_result, repo_source_kind="repo_baseline")
    if is_diagnostic(source_result):
        return response(
            "input_error",
            request_id=request.request_id,
            data=active_runtime_base_data(entry, request.operation, "input_error"),
            diagnostics=[source_result],
        )
    coverage_findings = missing_installed_runtime_scan_root_findings(repo_root, case_result)
    diff_finding: RawFinding | None = None
    if (
        "files" not in case_result
        and case_result.get("scan_repo") is not False
        and case_result.get("scan_changed_sources") is not False
    ):
        changed_result = changed_repo_sources(repo_root, case_result)
        if isinstance(changed_result, RawFinding):
            diff_finding = changed_result
        else:
            source_result.extend(changed_result)
    findings = scan_installed_runtime_sources(source_result, repo_root)
    findings.extend(coverage_findings)
    if diff_finding is not None:
        findings.append(diff_finding)
    return policy_guard_response(RUNTIME_GUARD_POLICY, entry, request, findings)


def classify_shell_finding(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    raw_path = request.inputs.get("path")
    text = request.inputs.get("text", "")
    if not isinstance(raw_path, str) or not raw_path or not isinstance(text, str):
        diag = diagnostic(
            "invalid_classification_request",
            "classify-shell-finding requires string inputs.path and inputs.text",
            remediation_summary="Send a single shell finding candidate to classify.",
            remediation_actions=["Set inputs.path to a repository-relative path.", "Set inputs.text to the line or snippet to classify."],
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])
    line = request.inputs.get("line")
    if not isinstance(line, int) or line < 1:
        line = 1
    findings = scan_sources([SourceFile(normalize_path(raw_path), text, "fixture")], repo_root)
    if not findings:
        findings = [
            classify_hit(
                PATH_GUARD_POLICY,
                normalize_path(raw_path),
                "fixture",
                Hit(line, str(request.inputs.get("category") or "bash"), text.strip() or raw_path, "manual classification request", text),
            )
        ]
    blocking = [finding for finding in findings if finding.classification == "blocking_active_gate"]
    status = "expected_failure" if blocking else "ok"
    data = base_data(entry, request.operation, status)
    data.update(
        {
            "schema_version": "1.0",
            "status": status,
            "blocking_count": len(blocking),
            "classified_counts": classified_counts(findings),
            "findings": [finding.as_record() for finding in findings],
        }
    )
    if not blocking:
        return response("ok", request_id=request.request_id, data=data)
    diag = diagnostic(
        "active_path_guard_blocked",
        "classify-shell-finding found a shell-specific dependency in an active repo-local gate",
        details={"path": blocking[0].path, "category": blocking[0].category},
        remediation_summary="Remove the active shell dependency or reclassify the retained path as inactive parity evidence.",
        remediation_actions=["Inspect data.findings for the blocking_active_gate entry.", "Migrate the active path to a Python runner gate."],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def run_zero_bash_guard(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    case_result = load_case(repo_root, request.inputs, default_case_file=PLUGIN_BASH_CONFINEMENT_DEFAULT_CASE_FILE)
    if is_diagnostic(case_result):
        return response("input_error", request_id=request.request_id, data=zero_bash_base_data(entry, request.operation, "input_error"), diagnostics=[case_result])
    case = case_result

    allowlist_result = load_zero_bash_allowlist(repo_root, case)
    if is_diagnostic(allowlist_result):
        return response("input_error", request_id=request.request_id, data=zero_bash_base_data(entry, request.operation, "input_error"), diagnostics=[allowlist_result])
    allowlist = allowlist_result

    allowlist_findings = zero_bash_allowlist_findings(allowlist)
    missing_roots = missing_zero_bash_scan_root_findings(repo_root, case)
    source_result = source_files(repo_root, case, repo_source_kind="repo")
    if is_diagnostic(source_result):
        return response("input_error", request_id=request.request_id, data=zero_bash_base_data(entry, request.operation, "input_error"), diagnostics=[source_result])

    source_findings = zero_bash_source_findings(source_result, allowlist)
    findings = [*allowlist_findings, *missing_roots, *source_findings]
    blocking = [finding for finding in findings if finding.classification == "blocking_zero_bash"]
    status = "expected_failure" if blocking else "ok"
    returned_findings = bounded_findings(blocking if blocking else findings)
    data = zero_bash_base_data(entry, request.operation, status)
    data.update(
        {
            "schema_version": "2.0",
            "contract_id": "plugin-bash-confinement",
            "status": "pass" if status == "ok" else "fail",
            "blocking_count": len(blocking),
            "classified_counts": classified_counts(findings),
            "findings": [zero_bash_finding_record(finding) for finding in returned_findings],
            "total_finding_count": len(findings),
            "truncated_finding_count": max(0, len(findings) - len(returned_findings)),
            "script_file_count": sum(1 for finding in findings if finding.category == "script_file" and finding.classification == "blocking_zero_bash"),
            "scan_roots": [root for root in case.get("scan_roots", []) if isinstance(root, str)],
            "allowlist": {
                "path": case.get("allowlist_file", PLUGIN_BASH_CONFINEMENT_ALLOWLIST),
                "entry_count": len(allowlist),
                "release_readiness_excluded": all(entry.get("release_readiness_excluded") is True for entry in allowlist),
            },
        }
    )
    if status == "ok":
        return response("ok", request_id=request.request_id, data=data)

    data["gate"]["gate_status"] = "fail"
    data["gate"]["blocking"] = True
    diag = diagnostic(
        "zero_bash_guard_blocked",
        "zero-Bash guard found active shell-specific behavior",
        details={
            "blocking_count": len(blocking),
            "categories": sorted({finding.category for finding in blocking}),
            "paths": sorted({finding.path for finding in blocking})[:20],
        },
        remediation_summary="Remove active shell behavior from the scanned source and generated payload roots.",
        remediation_actions=[
            "Inspect data.findings for blocking_zero_bash entries.",
            "Remove live script files and active Bash/jq guidance from in-scope plugin surfaces.",
            "Regenerate both shipped payloads from cleaned source.",
        ],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def changed_repo_sources(repo_root: Path, case: dict[str, Any]) -> list[SourceFile] | RawFinding:
    roots = case.get("scan_roots")
    if "scan_roots" in case:
        if not isinstance(roots, list):
            return RawFinding(
                path="scan_roots",
                line=None,
                category="scan_root",
                pattern=type(roots).__name__,
                reason="configured active-runtime scan_roots must be a non-empty array",
                active_role="repository_text",
                classification="blocking_active_runtime",
                remediation="Keep active-runtime scan roots as a non-empty array of normalized repository-relative paths.",
            )
        if not roots:
            return RawFinding(
                path="scan_roots",
                line=None,
                category="scan_root",
                pattern="[]",
                reason="configured active-runtime scan_roots must include at least one root",
                active_role="repository_text",
                classification="blocking_active_runtime",
                remediation="Keep active-runtime scan roots as a non-empty array of normalized repository-relative paths.",
            )
        scan_roots = tuple(item for item in roots if isinstance(item, str) and item and invalid_scan_root_reason(item) is None)
        entries = roots
    else:
        scan_roots = SCAN_ROOTS
        entries = list(scan_roots)
    for index, root in enumerate(entries):
        root_path, root_pattern, invalid_reason = scan_root_entry_validation(index, root)
        if invalid_reason is not None:
            return RawFinding(
                path=root_path,
                line=None,
                category="scan_root",
                pattern=root_pattern,
                reason=invalid_reason,
                active_role=installed_runtime_active_role(root_path),
                classification="blocking_active_runtime",
                remediation="Keep active-runtime scan roots normalized, repository-relative, and inside the repository.",
            )
    base = review_base_ref(repo_root)
    if base is None:
        return diff_scan_unavailable_finding("active-runtime guard could not resolve a review base for changed-line scanning")
    try:
        completed = subprocess.run(
            ["git", "diff", "--unified=0", "--no-color", base, "--", *scan_roots],
            cwd=repo_root,
            text=True,
            capture_output=True,
            timeout=10,
            shell=False,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return diff_scan_unavailable_finding(f"active-runtime guard could not run git diff for changed-line scanning: {type(exc).__name__}")
    if completed.returncode not in {0, 1}:
        return diff_scan_unavailable_finding("active-runtime guard git diff changed-line scan failed")
    return diff_added_line_sources(completed.stdout, repo_root)


def review_base_ref(repo_root: Path) -> str | None:
    candidates: list[str] = []
    env_base = os.environ.get("GITHUB_BASE_REF")
    if env_base:
        candidates.extend([f"origin/{env_base}", env_base])
    candidates.append("origin/main")
    for candidate in candidates:
        if not git_ref_exists(repo_root, candidate):
            continue
        merge_base = git_stdout(repo_root, ["merge-base", "HEAD", candidate])
        return merge_base or candidate
    return None


def git_ref_exists(repo_root: Path, ref: str) -> bool:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=repo_root,
            text=True,
            capture_output=True,
            timeout=5,
            shell=False,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def git_stdout(repo_root: Path, args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            text=True,
            capture_output=True,
            timeout=5,
            shell=False,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def diff_added_line_sources(diff_text: str, repo_root: Path) -> list[SourceFile]:
    sources: list[SourceFile] = []
    current_path: str | None = None
    added_lines: list[str] = []

    def flush() -> None:
        nonlocal added_lines
        if current_path is None or not added_lines:
            added_lines = []
            return
        path = repo_root / current_path
        if path.suffix.lower() in TEXT_SUFFIXES:
            sources.append(SourceFile(current_path, "\n".join(added_lines), "repo"))
        added_lines = []

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            flush()
            current_path = None
            continue
        if line.startswith("+++ b/"):
            current_path = normalize_path(line.removeprefix("+++ b/"))
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])
    flush()
    return sources


def source_files(repo_root: Path, case: dict[str, Any], *, repo_source_kind: str = "repo") -> list[SourceFile] | dict[str, Any]:
    raw_files = case.get("files")
    if isinstance(raw_files, list):
        sources: list[SourceFile] = []
        for item in raw_files:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("content"), str):
                return diagnostic("invalid_guard_case", "active-path guard fixture files must contain path and content strings")
            sources.append(SourceFile(normalize_path(item["path"]), item["content"], "fixture"))
        return sources
    if case.get("scan_repo") is False:
        return []
    raw_roots = case.get("scan_roots")
    if "scan_roots" in case:
        if isinstance(raw_roots, list):
            valid_roots = tuple(item for item in raw_roots if isinstance(item, str) and item and invalid_scan_root_reason(item) is None)
            return scan_repo_sources(repo_root, roots=valid_roots, source_kind=repo_source_kind)
        return []
    return scan_repo_sources(repo_root, source_kind=repo_source_kind)


def scan_repo_sources(repo_root: Path, *, roots: tuple[str, ...] = SCAN_ROOTS, source_kind: str = "repo") -> list[SourceFile]:
    sources: list[SourceFile] = []
    for root in roots:
        if invalid_scan_root_reason(root) is not None:
            continue
        path = repo_root / normalize_path(root)
        if path.is_file():
            maybe_add_source(repo_root, path, sources, source_kind)
            continue
        if not path.is_dir():
            continue
        for candidate in sorted(path.rglob("*")):
            if candidate.is_file():
                maybe_add_source(repo_root, candidate, sources, source_kind)
    return sources


def maybe_add_source(repo_root: Path, path: Path, sources: list[SourceFile], source_kind: str = "repo") -> None:
    try:
        relative_path = path.relative_to(repo_root).as_posix()
    except ValueError:
        return
    if not is_relative_to(path.resolve(strict=False), repo_root.resolve(strict=False)):
        return
    if has_prohibited_script_suffix(relative_path):
        sources.append(SourceFile(relative_path, "", source_kind))
        return
    first_line = read_first_line(path)
    if has_prohibited_script_shebang_content(first_line):
        sources.append(SourceFile(relative_path, first_line, source_kind))
        return
    extensionless = zero_bash_extensionless_scan_path(relative_path)
    if path.suffix.lower() not in TEXT_SUFFIXES and not extensionless:
        return
    try:
        if extensionless:
            if has_prohibited_script_shebang_content(first_line):
                sources.append(SourceFile(relative_path, first_line, source_kind))
            return
        if path.stat().st_size > MAX_SCAN_BYTES:
            return
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    sources.append(SourceFile(relative_path, content, source_kind))
