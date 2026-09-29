"""v1.0 active-path guard: repo-local gate classification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...envelope import diagnostic, response
from .common import (
    CONTAINER_PREFLIGHT_WORKFLOW,
    DEFAULT_CASE_FILE,
    FORBIDDEN_CONTENT_PATTERNS,
    FORBIDDEN_PATTERNS,
    RawFinding,
    SourceFile,
    add_finding,
    classified_counts,
    direct_dispatch_line,
    is_direct_python_gate_dispatch,
    is_docs_or_workflow_tooling,
    is_hook_matcher_line,
    line_context,
    line_number_for_offset,
    normalize_path,
    repository_bash_container_preflight_dispatch_glue,
    workflow_context_for_line,
    workflow_run_contexts,
)


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
        remediation_summary="Remove the active shell dependency or reclassify the retained path as inactive parity evidence.",
        remediation_actions=["Inspect data.findings for blocking_active_gate entries.", "Migrate the active path to a Python runner gate."],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def scan_sources(sources: list[SourceFile], repo_root: Path) -> list[RawFinding]:
    findings: list[RawFinding] = []
    seen: set[tuple[str, int | None, str, str]] = set()
    for source in sources:
        path = normalize_path(source.path)
        lines = source.content.splitlines()
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
        for category, pattern, reason in FORBIDDEN_CONTENT_PATTERNS:
            for match in pattern.finditer(source.content):
                line_number = line_number_for_offset(source.content, match.start())
                context = workflow_context_for_line(workflow_contexts, line_number) or line_context(lines, line_number)
                if path == CONTAINER_PREFLIGHT_WORKFLOW:
                    context = source.content
                add_finding(
                    findings,
                    seen,
                    classify_raw_finding(path, line_number, category, match.group(0), reason, context, source.source_kind),
                )
        for number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or (stripped.startswith("#") and not path.endswith(".md")):
                continue
            if is_hook_matcher_line(path, line):
                continue
            for category, pattern, reason in FORBIDDEN_PATTERNS:
                match = pattern.search(line)
                if match is None:
                    continue
                context = workflow_context_for_line(workflow_contexts, number) or line
                if path == CONTAINER_PREFLIGHT_WORKFLOW:
                    context = source.content
                add_finding(
                    findings,
                    seen,
                    classify_raw_finding(path, number, category, match.group(0), reason, context, source.source_kind),
                )
    return findings


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


def classify_path(path: str, category: str, pattern: str, content: str, source_kind: str) -> str:
    if path.startswith(".specify/memory/"):
        return "archive_provenance"
    if path.startswith(".specify/scripts/bash/"):
        return "consumer_spec_kit_helper"
    if path.startswith("dist/"):
        return "generated_payload_mirror"
    if path.startswith("docs-site/") or path.startswith("docs/") or path in {"CLAUDE.md", "README.md"} or path.startswith("specs/"):
        return "docs_out_of_scope"
    if "/fixtures/" in path or path.endswith("bash-reference-manifest.json") or "layer7-parity/" in path:
        return "temporary_parity_evidence"
    if path.startswith("speckit-pro/codex-skills/") or path.startswith("speckit-pro/skills/") or path.startswith("speckit-pro/scripts/"):
        return "installed_runtime_cutover_surface"
    if path.startswith(".github/workflows/"):
        if path == ".github/workflows/deploy-docs.yml":
            return "docs_out_of_scope"
        if repository_bash_container_preflight_dispatch_glue(path, content):
            return "ci_dispatch_glue"
        if category == "bash" and pattern.startswith("run:") and is_direct_python_gate_dispatch(content):
            return "ci_dispatch_glue"
        if is_docs_or_workflow_tooling(content):
            return "docs_out_of_scope"
        return "blocking_active_gate"
    if source_kind == "repo" and (path.startswith("tests/speckit-pro/") or path.startswith("scripts/")):
        return "temporary_parity_evidence"
    return "blocking_active_gate"


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


def remediation_for(classification: str) -> str:
    if classification == "blocking_active_gate":
        return "Migrate the active command path to a Python runner gate before release readiness can pass."
    if classification == "ci_dispatch_glue":
        return "Keep workflow shell limited to direct Python runner dispatch."
    if classification == "installed_runtime_cutover_surface":
        return "Keep installed Claude/Codex invocation cutover deferred."
    if classification == "temporary_parity_evidence":
        return "Retain only as inactive parity evidence while promotion records remain valid."
    if classification == "archive_provenance":
        return "No code change required for archived provenance text."
    if classification == "consumer_spec_kit_helper":
        return "No runner-gate change required for vendored consumer Spec Kit helper evidence."
    if classification == "generated_payload_mirror":
        return "Do not cut over generated release payload mirrors until installed-runtime verification passes."
    return "No runner-gate change required for documentation-only text."


def base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    gate_status = "pass" if status == "ok" else "fail" if status == "expected_failure" else status
    return {
        "gate": {
            "gate_id": entry.helper_id,
            "operation": operation,
            "gate_status": gate_status,
            "promoted": status != "input_error",
            "blocking": status != "ok",
            "comparison_ids": [operation],
        },
        "artifacts": [{"path": DEFAULT_CASE_FILE, "kind": "fixture"}],
    }
