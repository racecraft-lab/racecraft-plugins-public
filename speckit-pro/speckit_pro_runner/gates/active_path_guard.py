"""Active-path no-shell/no-jq guard operations for XPLAT-007 US3."""

from __future__ import annotations

import copy
import json
import re
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response

PROMOTION_RECORD = "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json"
DEFAULT_CASE_FILE = "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/active-path-guard-cases.json"
XPLAT_008_PROMOTION_RECORD = "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/active-runtime-guard-cases.json"
XPLAT_008_DEFAULT_CASE_FILE = "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/active-runtime-guard-cases.json"
TEXT_SUFFIXES = frozenset({".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"})
SCAN_ROOTS = (
    "tests/speckit-pro",
    "scripts",
    "speckit-pro/skills",
    "speckit-pro/codex-skills",
    "speckit-pro/scripts",
    ".github/workflows",
    ".specify/memory",
    ".specify/scripts/bash",
    "dist/claude",
    "dist/codex",
    "CLAUDE.md",
    "docs-site/src/content/docs/contribute-and-release.md",
)
MAX_SCAN_BYTES = 512 * 1024

FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("git_bash", re.compile(r"\bgit\s+bash\b", re.IGNORECASE), "Git Bash dependency"),
    ("wsl", re.compile(r"\b(?:wsl|wsl\.exe)\b", re.IGNORECASE), "WSL dependency"),
    ("powershell_helper", re.compile(r"\b(?:powershell|pwsh)\b|\.ps1\b", re.IGNORECASE), "PowerShell helper dependency"),
    ("shell_true", re.compile(r"shell\s*=\s*True|[\"']shell[\"']\s*:\s*true"), "shell=True subprocess execution"),
    ("os_system", re.compile(r"\bos\.system\s*\("), "os.system shell execution"),
    (
        "command_string_subprocess",
        re.compile(r"\bsubprocess\.(?:run|Popen|call|check_call|check_output)\(\s*[\"']"),
        "command-string subprocess execution",
    ),
    ("jq", re.compile(r"(?<![\w-])jq(?![\w-])|--jq\b", re.IGNORECASE), "jq command dependency"),
    ("bash", re.compile(r"^#!.*\bbash\b|\bbash\b", re.IGNORECASE), "Bash dependency"),
    ("script_file", re.compile(r"(?:^|\s|[\"'])[^\"'\s]+\.sh\b"), ".sh script path dependency"),
    ("shell_parsing", re.compile(r"\|.*\b(?:grep|sed|awk)\b|\b(?:grep|sed|awk)\b.*\|", re.IGNORECASE), "shell parsing pipeline"),
    ("shell_interpolation", re.compile(r"\$\(|`[^`]+`"), "shell command substitution"),
)

CLASSIFICATIONS = (
    "blocking_active_gate",
    "blocking_active_runtime",
    "ci_dispatch_glue",
    "temporary_parity_evidence",
    "archive_provenance",
    "consumer_spec_kit_helper",
    "upstream_spec_kit_helper",
    "generated_payload_mirror",
    "xplat_008_cutover_surface",
    "source_checkout_helper",
    "docs_non_runtime",
    "test_fixture",
    "docs_out_of_scope",
)

__all__ = ("run_active_path_guard",)


@dataclass(frozen=True)
class SourceFile:
    path: str
    content: str
    source_kind: str


@dataclass(frozen=True)
class RawFinding:
    path: str
    line: int | None
    category: str
    pattern: str
    reason: str
    active_role: str
    classification: str
    remediation: str

    def as_record(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "line": self.line,
            "category": self.category,
            "pattern": self.pattern,
            "reason": self.reason,
            "active_role": self.active_role,
            "classification": self.classification,
            "remediation": self.remediation,
        }


def run_active_path_guard(entry: Any, request: Any) -> dict[str, Any]:
    repo_root_result = resolve_repo_root(request.inputs)
    if isinstance(repo_root_result, dict):
        status = "missing_prerequisite" if repo_root_result["code"] == "missing_prerequisite" else "input_error"
        data = (
            active_runtime_base_data(entry, request.operation, status)
            if request.operation == "active-runtime-guard"
            else base_data(entry, request.operation, status)
        )
        return response(status, request_id=request.request_id, data=data, diagnostics=[repo_root_result])
    repo_root = repo_root_result

    if request.operation == "active-runtime-guard":
        return run_active_runtime_guard(entry, request, repo_root)

    if request.inputs.get("xplat_008_cutover_allowed") is not False:
        diag = diagnostic(
            "xplat_008_cutover_refused",
            "active-path guard must not claim XPLAT-008 cutover surfaces",
            remediation_summary="Keep active Claude/Codex invocation and public release cutover deferred.",
            remediation_actions=["Set xplat_008_cutover_allowed to false.", "Record remaining cutover work as XPLAT-008 handoff evidence."],
            deferred_to="XPLAT-008",
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])

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
    return guard_response(entry, request, findings)


def run_active_runtime_guard(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    case_result = load_case(repo_root, request.inputs, default_case_file=XPLAT_008_DEFAULT_CASE_FILE)
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
    diff_finding: RawFinding | None = None
    if "files" not in case_result and case_result.get("scan_repo") is not False:
        changed_result = changed_repo_sources(repo_root, case_result)
        if isinstance(changed_result, RawFinding):
            diff_finding = changed_result
        else:
            source_result.extend(changed_result)
    findings = scan_sources_xplat008(source_result, repo_root)
    if diff_finding is not None:
        findings.append(diff_finding)
    return active_runtime_guard_response(entry, request, findings)


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
            classify_raw_finding(
                normalize_path(raw_path),
                line,
                str(request.inputs.get("category") or "bash"),
                text.strip() or raw_path,
                "manual classification request",
                text,
                "fixture",
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
        remediation_summary="Remove the active shell dependency or reclassify the retained path as inactive parity/XPLAT-008 evidence.",
        remediation_actions=["Inspect data.findings for the blocking_active_gate entry.", "Migrate the active path to a Python runner gate."],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def guard_response(entry: Any, request: Any, findings: list[RawFinding]) -> dict[str, Any]:
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
        "active-path guard found shell-specific dependencies in active repo-local gates",
        details={
            "blocking_count": len(blocking),
            "categories": sorted({finding.category for finding in blocking}),
            "paths": sorted({finding.path for finding in blocking})[:20],
        },
        remediation_summary="Remove the active shell dependency or reclassify the retained path as inactive parity/XPLAT-008 evidence.",
        remediation_actions=["Inspect data.findings for blocking_active_gate entries.", "Migrate the active path to a Python runner gate."],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def active_runtime_guard_response(entry: Any, request: Any, findings: list[RawFinding]) -> dict[str, Any]:
    blocking = [finding for finding in findings if finding.classification == "blocking_active_runtime"]
    status = "expected_failure" if blocking else "ok"
    returned_findings = bounded_findings(findings, request.inputs)
    data = active_runtime_base_data(entry, request.operation, status)
    data.update(
        {
            "schema_version": "1.0",
            "feature_id": "XPLAT-008",
            "status": status,
            "blocking_count": len(blocking),
            "classified_counts": classified_counts(findings),
            "findings": [finding.as_record() for finding in returned_findings],
            "total_finding_count": len(findings),
            "truncated_finding_count": max(0, len(findings) - len(returned_findings)),
        }
    )
    if not blocking:
        return response("ok", request_id=request.request_id, data=data)

    diag = diagnostic(
        "active_runtime_guard_blocked",
        "active-runtime guard found prohibited shell-only behavior in installed-runtime surfaces",
        details={
            "blocking_count": len(blocking),
            "categories": sorted({finding.category for finding in blocking}),
            "paths": sorted({finding.path for finding in blocking})[:20],
        },
        remediation_summary="Move active installed-runtime behavior to argv-only Python runner invocation.",
        remediation_actions=[
            "Inspect data.findings for blocking_active_runtime entries.",
            "Use a resolved Python 3.11+ executable with -m speckit_pro_runner and JSON stdin/stdout.",
        ],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def bounded_findings(findings: list[RawFinding], inputs: dict[str, Any]) -> list[RawFinding]:
    raw_limit = inputs.get("max_findings", 25)
    limit = raw_limit if isinstance(raw_limit, int) and raw_limit > 0 else 25
    blocking = [finding for finding in findings if finding.classification == "blocking_active_runtime"]
    if blocking:
        return blocking[:limit]
    return findings[:limit]


def classified_counts(findings: list[RawFinding]) -> dict[str, int]:
    counts = {classification: 0 for classification in CLASSIFICATIONS}
    for finding in findings:
        counts[finding.classification] = counts.get(finding.classification, 0) + 1
    return {key: value for key, value in counts.items() if value > 0}


def scan_sources(sources: list[SourceFile], repo_root: Path) -> list[RawFinding]:
    findings: list[RawFinding] = []
    seen: set[tuple[str, int | None, str, str]] = set()
    for source in sources:
        path = normalize_path(source.path)
        workflow_contexts = workflow_run_contexts(source.content) if path.startswith(".github/workflows/") else []
        if path.endswith(".sh"):
            add_finding(findings, seen, classify_raw_finding(path, 1, "script_file", "*.sh", ".sh file retained in scanned scope", source.content, source.source_kind))
        if path.startswith(".github/workflows/") and is_direct_python_gate_dispatch(source.content):
            line = direct_dispatch_line(source.content)
            add_finding(
                findings,
                seen,
                classify_raw_finding(path, line, "bash", "run: python -m speckit_pro_runner", "workflow shell dispatches a Python gate", source.content, source.source_kind),
            )
        for number, line in enumerate(source.content.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for category, pattern, reason in FORBIDDEN_PATTERNS:
                match = pattern.search(line)
                if match is None:
                    continue
                context = workflow_context_for_line(workflow_contexts, number) or line
                add_finding(
                    findings,
                    seen,
                    classify_raw_finding(path, number, category, match.group(0), reason, context, source.source_kind),
                )
    return findings


def scan_sources_xplat008(sources: list[SourceFile], repo_root: Path) -> list[RawFinding]:
    findings: list[RawFinding] = []
    seen: set[tuple[str, int | None, str, str]] = set()
    for source in sources:
        path = normalize_path(source.path)
        workflow_contexts = workflow_run_contexts(source.content) if path.startswith(".github/workflows/") else []
        if path.endswith(".sh"):
            add_finding(
                findings,
                seen,
                classify_xplat008_raw_finding(path, 1, "script_file", "*.sh", ".sh file retained in scanned scope", source.content, source.source_kind),
            )
        if path.startswith(".github/workflows/") and is_direct_python_gate_dispatch(source.content):
            line = direct_dispatch_line(source.content)
            add_finding(
                findings,
                seen,
                classify_xplat008_raw_finding(
                    path,
                    line,
                    "bash",
                    "run: python -m speckit_pro_runner",
                    "workflow shell dispatches a Python gate",
                    source.content,
                    source.source_kind,
                ),
            )
        for number, line in enumerate(source.content.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for category, pattern, reason in FORBIDDEN_PATTERNS:
                match = pattern.search(line)
                if match is None:
                    continue
                context = workflow_context_for_line(workflow_contexts, number) or line
                add_finding(
                    findings,
                    seen,
                    classify_xplat008_raw_finding(path, number, category, match.group(0), reason, context, source.source_kind),
                )
    return findings


def add_finding(findings: list[RawFinding], seen: set[tuple[str, int | None, str, str]], finding: RawFinding) -> None:
    key = (finding.path, finding.line, finding.category, finding.pattern)
    if key in seen:
        return
    seen.add(key)
    findings.append(finding)


def classify_raw_finding(
    path: str,
    line: int | None,
    category: str,
    pattern: str,
    reason: str,
    content: str,
    source_kind: str,
) -> RawFinding:
    role = active_role(path)
    classification = classify_path(path, category, pattern, content, source_kind)
    return RawFinding(
        path=path,
        line=line,
        category=category,
        pattern=pattern[:120],
        reason=reason,
        active_role=role,
        classification=classification,
        remediation=remediation_for(classification),
    )


def classify_xplat008_raw_finding(
    path: str,
    line: int | None,
    category: str,
    pattern: str,
    reason: str,
    content: str,
    source_kind: str,
) -> RawFinding:
    role = xplat008_active_role(path)
    classification = classify_xplat008_path(path, category, pattern, content, source_kind)
    return RawFinding(
        path=path,
        line=line,
        category=category,
        pattern=pattern[:120],
        reason=reason,
        active_role=role,
        classification=classification,
        remediation=xplat008_remediation_for(classification),
    )


def classify_path(path: str, category: str, pattern: str, content: str, source_kind: str) -> str:
    if path.startswith(".specify/memory/"):
        return "archive_provenance"
    if path.startswith(".specify/scripts/bash/"):
        return "consumer_spec_kit_helper"
    if path.startswith("dist/"):
        return "generated_payload_mirror"
    if path.startswith("docs-site/") or path.startswith("docs/") or path in {"CLAUDE.md", "README.md"} or path.startswith("specs/"):
        return "docs_out_of_scope"
    if "/fixtures/" in path or path.endswith("bash-reference-manifest.json") or "layer8-parity/" in path:
        return "temporary_parity_evidence"
    if path.startswith("speckit-pro/codex-skills/") or path.startswith("speckit-pro/skills/") or path.startswith("speckit-pro/scripts/"):
        return "xplat_008_cutover_surface"
    if path.startswith(".github/workflows/"):
        if path == ".github/workflows/deploy-docs.yml":
            return "docs_out_of_scope"
        if category == "bash" and pattern.startswith("run:") and is_direct_python_gate_dispatch(content):
            return "ci_dispatch_glue"
        if is_docs_or_workflow_tooling(content):
            return "docs_out_of_scope"
        return "blocking_active_gate"
    if source_kind == "repo" and (path.startswith("tests/speckit-pro/") or path.startswith("scripts/")):
        return "temporary_parity_evidence"
    return "blocking_active_gate"


def classify_xplat008_path(path: str, category: str, pattern: str, content: str, source_kind: str) -> str:
    if path.startswith(".specify/memory/"):
        return "archive_provenance"
    if path.startswith(".specify/scripts/bash/"):
        return "upstream_spec_kit_helper"
    if path.startswith("tests/") or "/fixtures/" in path or "layer8-parity/" in path:
        return "test_fixture"
    if path.startswith("speckit-pro/") and any(part in path for part in ("/scripts/", "/references/", "/templates/")):
        return "source_checkout_helper"
    if path.startswith(".github/workflows/"):
        if path == ".github/workflows/deploy-docs.yml" or is_docs_or_workflow_tooling(content):
            return "docs_non_runtime"
        if category == "bash" and pattern.startswith("run:") and is_direct_python_gate_dispatch(content):
            return "ci_dispatch_glue"
        return "blocking_active_runtime"
    if path in {"speckit-pro/codex-hooks.json", "speckit-pro/hooks/hooks.json"}:
        return "blocking_active_runtime"
    if path.startswith("dist/") and not path.endswith(("README.md", "CHANGELOG.md", "LICENSE")):
        if source_kind == "repo_baseline" and xplat008_dist_source_checkout_surface(path):
            return "source_checkout_helper"
        if source_kind == "repo_baseline" and xplat008_source_checkout_helper_reference(path, content):
            return "source_checkout_helper"
        if source_kind in {"repo", "repo_baseline"} and xplat008_repo_surface_exception(category, pattern, content):
            return "source_checkout_helper"
        return "blocking_active_runtime"
    if path.startswith("speckit-pro/skills/") or path.startswith("speckit-pro/codex-skills/"):
        if source_kind == "repo_baseline":
            return "source_checkout_helper"
        if source_kind == "repo" and xplat008_repo_surface_exception(category, pattern, content):
            return "source_checkout_helper"
        return "blocking_active_runtime" if source_kind in {"fixture", "repo"} else "source_checkout_helper"
    if path.startswith("speckit-pro/agents/") or path.startswith("speckit-pro/codex-agents/"):
        if source_kind == "repo_baseline":
            return "source_checkout_helper"
        if source_kind == "repo" and xplat008_repo_surface_exception(category, pattern, content):
            return "source_checkout_helper"
        return "blocking_active_runtime" if source_kind in {"fixture", "repo"} else "source_checkout_helper"
    if path in {"README.md", "speckit-pro/README.md"} or path.startswith("docs-site/src/content/docs/"):
        return "blocking_active_runtime" if source_kind == "fixture" else "docs_non_runtime"
    return "source_checkout_helper"


def active_role(path: str) -> str:
    if path.startswith(".github/workflows/"):
        return "active_ci_workflow"
    if path.startswith("tests/speckit-pro/"):
        return "repo_local_test_gate"
    if path.startswith("scripts/"):
        return "repo_local_release_helper"
    if "/scripts/" in path and path.startswith("speckit-pro/"):
        return "installed_plugin_helper"
    if path.startswith("docs-site/") or path.startswith("docs/"):
        return "documentation"
    if path.startswith(".specify/"):
        return "specify_provenance"
    if path.startswith("dist/"):
        return "generated_payload"
    return "repository_text"


def xplat008_active_role(path: str) -> str:
    if path.startswith(".github/workflows/"):
        return "release_gate"
    if path.startswith("dist/"):
        return "generated_payload"
    if path.startswith("speckit-pro/skills/") or path.startswith("speckit-pro/codex-skills/"):
        return "installed_skill"
    if path.startswith("speckit-pro/agents/") or path.startswith("speckit-pro/codex-agents/"):
        return "installed_agent"
    if path in {"speckit-pro/codex-hooks.json", "speckit-pro/hooks/hooks.json"}:
        return "installed_hook"
    if path.startswith(".specify/scripts/bash/"):
        return "upstream_spec_kit_helper"
    if path.startswith("tests/"):
        return "test_fixture"
    if path.startswith(".specify/memory/"):
        return "archive_provenance"
    if path.startswith("docs-site/") or path in {"README.md", "speckit-pro/README.md"}:
        return "install_guidance"
    return "repository_text"


def xplat008_repo_surface_exception(category: str, pattern: str, content: str) -> bool:
    if category == "shell_interpolation" and pattern.startswith("`"):
        return not xplat008_backtick_requires_shell(pattern, content)
    lowered = content.lower()
    return any(
        marker in lowered
        for marker in (
            "do not ",
            "must not ",
            "never ",
            "not require",
            "not add",
            "without requiring",
            "without adding",
            "without using",
            "avoid ",
            "refuse",
            "forbidden",
            "specific command-language requirement",
        )
    )


def xplat008_source_checkout_helper_reference(path: str, content: str) -> bool:
    lowered_path = path.lower()
    lowered = content.lower()
    if any(part in lowered_path for part in ("/references/", "/templates/", "/contracts/", "/scripts/")):
        return True
    markers = (
        "allowed-tools:",
        "claude_plugin_root",
        "<skill_scripts>",
        "source-checkout",
        "source checkout",
        "speckit-pro/skills/",
        "speckit-pro/codex-skills/",
        "tests/speckit-pro/",
        ".specify/",
        "docs/ai/specs/",
        "docs-site/",
        ".sh",
        "deterministic bash scripts",
        " is missing",
    )
    return any(marker in lowered for marker in markers)


def xplat008_dist_source_checkout_surface(path: str) -> bool:
    lowered = path.lower()
    return any(part in lowered for part in ("/skills/", "/agents/", "/codex-agents/", "/scripts/"))


def xplat008_backtick_requires_shell(pattern: str, content: str) -> bool:
    shell_markers = ("bash", "git bash", "wsl", "wsl.exe", "powershell", "pwsh", "jq", ".sh", "grep", "sed", "awk")
    lowered_pattern = pattern.lower()
    if not any(marker in lowered_pattern for marker in shell_markers):
        return False
    lowered_content = content.lower()
    requirement_markers = ("run ", "execute ", "invoke ", "call ", "use ", "require ", "must ", "should ")
    return any(marker in lowered_content for marker in requirement_markers)


def remediation_for(classification: str) -> str:
    if classification == "blocking_active_gate":
        return "Migrate the active command path to a Python runner gate before release readiness can pass."
    if classification == "ci_dispatch_glue":
        return "Keep workflow shell limited to direct Python runner dispatch."
    if classification == "xplat_008_cutover_surface":
        return "Keep installed Claude/Codex invocation cutover deferred to XPLAT-008."
    if classification == "temporary_parity_evidence":
        return "Retain only as inactive parity evidence while promotion records remain valid."
    if classification == "archive_provenance":
        return "No code change required for archived provenance text."
    if classification == "consumer_spec_kit_helper":
        return "No XPLAT-007 change required for vendored consumer Spec Kit helper evidence."
    if classification == "generated_payload_mirror":
        return "Do not cut over generated release payload mirrors until XPLAT-008."
    return "No XPLAT-007 gate change required for documentation-only text."


def xplat008_remediation_for(classification: str) -> str:
    if classification == "blocking_active_runtime":
        return "Replace the installed-runtime shell dependency with argv-only Python runner invocation."
    if classification == "ci_dispatch_glue":
        return "Keep CI glue limited to direct Python runner dispatch."
    if classification == "archive_provenance":
        return "No change required for historical archive text."
    if classification == "upstream_spec_kit_helper":
        return "No change required for upstream consumer Spec Kit helper evidence."
    if classification == "test_fixture":
        return "No change required for fixture or parity evidence."
    if classification == "source_checkout_helper":
        return "Keep source-checkout helper references out of installed-runtime instructions."
    if classification == "docs_non_runtime":
        return "No change required for non-runtime docs prose."
    return "No active-runtime change required."


def is_direct_python_gate_dispatch(content: str) -> bool:
    if "speckit_pro_runner" not in content:
        return False
    forbidden = (
        " jq",
        "\tjq",
        "bash ",
        ".sh",
        " for ",
        "\nfor ",
        "\nwhile ",
        " grep ",
        " sed ",
        " awk ",
        "$(",
        "scripts/build-plugin-payloads",
        "scripts/sync-marketplace-versions",
        "tests/speckit-pro/run-all",
        "tests/speckit-pro/check-toolchain",
    )
    lowered = content.lower()
    return not any(item in lowered for item in forbidden)


def direct_dispatch_line(content: str) -> int | None:
    for number, line in enumerate(content.splitlines(), start=1):
        if "speckit_pro_runner" in line:
            return number
    return None


def workflow_run_contexts(content: str) -> list[tuple[int, int, str]]:
    contexts: list[tuple[int, int, str]] = []
    lines = content.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped.startswith("run:"):
            index += 1
            continue
        start = index + 1
        indent = len(line) - len(line.lstrip(" "))
        block = [line]
        end = start
        if stripped in {"run: |", "run: >"}:
            next_index = index + 1
            while next_index < len(lines):
                next_line = lines[next_index]
                next_stripped = next_line.strip()
                next_indent = len(next_line) - len(next_line.lstrip(" "))
                if next_stripped and next_indent <= indent:
                    break
                block.append(next_line)
                end = next_index + 1
                next_index += 1
            index = next_index
        else:
            index += 1
        contexts.append((start, end, "\n".join(block)))
    return contexts


def workflow_context_for_line(contexts: list[tuple[int, int, str]], line: int) -> str | None:
    for start, end, context in contexts:
        if start <= line <= end:
            return context
    return None


def is_docs_or_workflow_tooling(content: str) -> bool:
    lowered = content.lower()
    markers = (
        "docs-site",
        "pnpm --dir docs-site",
        "actionlint",
        "playwright",
        "corepack",
        "doc-010",
        "docs validation",
        "--mode docs",
        "validation_mode",
        "should_validate_docs",
        "upload docs-site",
        "reference:check",
        "validate:quality",
    )
    plugin_markers = (
        "tests/speckit-pro/run-all",
        "scripts/build-plugin-payloads",
        "scripts/sync-marketplace-versions",
        ".claude-plugin/plugin.json",
    )
    if any(marker in lowered for marker in {"doc-010", "docs validation", "validation_mode", "should_validate_docs", "--mode docs"}):
        return True
    return any(marker in lowered for marker in markers) and not any(marker in lowered for marker in plugin_markers)


def changed_repo_sources(repo_root: Path, case: dict[str, Any]) -> list[SourceFile] | RawFinding:
    roots = case.get("scan_roots")
    scan_roots = tuple(item for item in roots if isinstance(item, str) and item) if isinstance(roots, list) else SCAN_ROOTS
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


def diff_scan_unavailable_finding(reason: str) -> RawFinding:
    return RawFinding(
        path=".git",
        line=None,
        category="diff_scan",
        pattern="git diff",
        reason=reason,
        active_role="release_gate",
        classification="blocking_active_runtime",
        remediation="Restore changed-line diff scanning or provide explicit active-runtime guard files before release readiness can pass.",
    )


def review_base_ref(repo_root: Path) -> str | None:
    candidates: list[str] = []
    env_base = os.environ.get("GITHUB_BASE_REF")
    if env_base:
        candidates.extend([f"origin/{env_base}", env_base])
    candidates.append("origin/main")
    for candidate in candidates:
        if not git_ref_exists(repo_root, candidate):
            continue
        merge_base = git_stdout(repo_root, ["git", "merge-base", "HEAD", candidate])
        return merge_base or candidate
    return None


def git_ref_exists(repo_root: Path, ref: str) -> bool:
    return subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=repo_root,
        text=True,
        capture_output=True,
        timeout=5,
        shell=False,
        check=False,
    ).returncode == 0


def git_stdout(repo_root: Path, argv: list[str]) -> str:
    completed = subprocess.run(
        argv,
        cwd=repo_root,
        text=True,
        capture_output=True,
        timeout=5,
        shell=False,
        check=False,
    )
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
        if path.suffix in TEXT_SUFFIXES:
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
    if isinstance(raw_roots, list) and all(isinstance(item, str) and item for item in raw_roots):
        return scan_repo_sources(repo_root, roots=tuple(raw_roots), source_kind=repo_source_kind)
    return scan_repo_sources(repo_root, source_kind=repo_source_kind)


def scan_repo_sources(repo_root: Path, *, roots: tuple[str, ...] = SCAN_ROOTS, source_kind: str = "repo") -> list[SourceFile]:
    sources: list[SourceFile] = []
    for root in roots:
        path = repo_root / root
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
    if path.suffix not in TEXT_SUFFIXES:
        return
    try:
        if path.stat().st_size > MAX_SCAN_BYTES:
            return
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    sources.append(SourceFile(path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix(), content, source_kind))


def load_case(repo_root: Path, inputs: dict[str, Any], *, default_case_file: str = DEFAULT_CASE_FILE) -> dict[str, Any]:
    raw = inputs.get("case_file", default_case_file)
    if not isinstance(raw, str) or not raw:
        return diagnostic("invalid_case_file", "case_file must be a non-empty string")
    path = resolve_path(raw, repo_root)
    if not is_relative_to(path.resolve(strict=False), repo_root.resolve(strict=False)):
        return diagnostic("invalid_case_file", "case_file must stay inside the repository")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return diagnostic("invalid_case_file", "active-path guard case fixture could not be loaded", details={"case_file": raw, "error": type(exc).__name__})
    cases = document.get("cases")
    if not isinstance(cases, list):
        return diagnostic("invalid_case_file", "active-path guard fixture must contain cases")
    case_id = inputs.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        case_id = "final-current-implementation"
    selected = next((item for item in cases if isinstance(item, dict) and item.get("case_id") == case_id), None)
    if selected is None:
        return diagnostic("unknown_fixture_case", "active-path guard fixture case was not found", details={"case_id": case_id})
    return copy.deepcopy(selected)


def base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    gate_status = "pass" if status == "ok" else "fail" if status == "expected_failure" else status
    return {
        "gate": {
            "gate_id": entry.helper_id,
            "operation": operation,
            "gate_status": gate_status,
            "promoted": status != "input_error",
            "blocking": status != "ok",
            "comparison_ids": [f"us3-{operation}"],
            "promotion_record": PROMOTION_RECORD,
        },
        "artifacts": [{"path": PROMOTION_RECORD, "kind": "fixture"}, {"path": DEFAULT_CASE_FILE, "kind": "fixture"}],
    }


def active_runtime_base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    gate_status = "pass" if status == "ok" else "fail" if status == "expected_failure" else status
    return {
        "gate": {
            "gate_id": entry.helper_id,
            "operation": operation,
            "gate_status": gate_status,
            "promoted": status != "input_error",
            "blocking": status != "ok",
            "comparison_ids": [f"xplat-008-{operation}"],
            "promotion_record": XPLAT_008_PROMOTION_RECORD,
        },
        "artifacts": [
            {"path": XPLAT_008_PROMOTION_RECORD, "kind": "fixture"},
            {"path": XPLAT_008_DEFAULT_CASE_FILE, "kind": "fixture"},
        ],
    }


def resolve_repo_root(inputs: dict[str, Any]) -> Path | dict[str, Any]:
    raw = inputs.get("repo_root", ".")
    if not isinstance(raw, str) or not raw:
        return diagnostic("invalid_repo_root", "repo_root must be a non-empty string")
    root = resolve_path(raw, Path.cwd()).resolve(strict=False)
    found = find_repo_root(root)
    if found is None:
        return diagnostic(
            "missing_prerequisite",
            "could not locate repository root for active-path guard request",
            remediation_summary="Run the guard from a SpecKit Pro source checkout.",
            remediation_actions=["Change to the repository root.", "Retry the same runner request."],
        )
    return found


def find_repo_root(start: Path) -> Path | None:
    candidates = [start, *start.parents] if start.is_dir() else [start.parent, *start.parent.parents]
    for candidate in candidates:
        if (candidate / "speckit-pro" / "speckit_pro_runner").is_dir() and (candidate / "tests" / "speckit-pro").is_dir():
            return candidate.resolve(strict=False)
    return None


def resolve_path(raw: str, root: Path) -> Path:
    path = Path(raw.replace("\\", "/"))
    return path if path.is_absolute() else root / path


def normalize_path(raw: str) -> str:
    path = raw.replace("\\", "/")
    return path[2:] if path.startswith("./") else path


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def is_diagnostic(value: Any) -> bool:
    return isinstance(value, dict) and value.get("source") == "runner" and "code" in value
