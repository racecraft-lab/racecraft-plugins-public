"""v1.0 active-path guard: repo-local gate classification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import (
    DEFAULT_CASE_FILE,
    RawFinding,
    SourceFile,
    is_direct_python_gate_dispatch,
    is_docs_or_workflow_tooling,
    repository_bash_container_preflight_dispatch_glue,
)
from .scan import GuardPolicy, scan_with_policy


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


def path_guard_script_file(path: str) -> tuple[str, str] | None:
    if path.endswith(".sh"):
        return "*.sh", ".sh file retained in scanned scope"
    return None


PATH_GUARD_POLICY = GuardPolicy(
    schema_version="1.0",
    contract_id=None,
    blocking_classification="blocking_active_gate",
    bound_findings=False,
    base_data=base_data,
    active_role=active_role,
    classify=classify_path,
    remediations={
        "blocking_active_gate": "Migrate the active command path to a Python runner gate before release readiness can pass.",
        "ci_dispatch_glue": "Keep workflow shell limited to direct Python runner dispatch.",
        "installed_runtime_cutover_surface": "Keep installed Claude/Codex invocation cutover deferred.",
        "temporary_parity_evidence": "Retain only as inactive parity evidence while promotion records remain valid.",
        "archive_provenance": "No code change required for archived provenance text.",
        "consumer_spec_kit_helper": "No runner-gate change required for vendored consumer Spec Kit helper evidence.",
        "generated_payload_mirror": "Do not cut over generated release payload mirrors until installed-runtime verification passes.",
    },
    default_remediation="No runner-gate change required for documentation-only text.",
    script_file=path_guard_script_file,
    line_context_window=False,
    bare_line_context=lambda path, line: False,
    blocked_code="active_path_guard_blocked",
    blocked_message="active-path guard found shell-specific dependencies in active repo-local gates",
    blocked_summary="Remove the active shell dependency or reclassify the retained path as inactive parity evidence.",
    blocked_actions=("Inspect data.findings for blocking_active_gate entries.", "Migrate the active path to a Python runner gate."),
)


def scan_sources(sources: list[SourceFile], repo_root: Path) -> list[RawFinding]:
    return scan_with_policy(PATH_GUARD_POLICY, sources)
