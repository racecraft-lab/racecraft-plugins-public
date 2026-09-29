"""v2.0 installed-runtime guard: installed plugin surface classification."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import (
    RawFinding,
    SourceFile,
    has_prohibited_script_suffix,
    is_direct_python_gate_dispatch,
    is_docs_or_workflow_tooling,
    normalize_path,
    repository_bash_container_preflight_dispatch_glue,
    scan_root_entry_validation,
)
from .scan import GuardPolicy, scan_with_policy


# The guard's own modules name every token it detects. Each module is exempt
# by exact path, so a new file in this package is scanned until it is listed.
GUARD_SOURCE_PATHS = tuple(
    f"speckit_pro_runner/gates/active_path_guard/{module}.py"
    for module in ("__init__", "common", "path_guard", "python_ast", "repo_bash", "runtime_guard", "scan", "zero_bash")
)


INSTALLED_RUNTIME_DEFAULT_CASE_FILE = "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json"


def classify_installed_runtime_path(path: str, category: str, pattern: str, content: str, source_kind: str) -> str:
    if path.startswith(".specify/memory/"):
        return "archive_provenance"
    if path.startswith(".specify/scripts/bash/"):
        return "upstream_spec_kit_helper"
    if path.startswith("tests/") or "/fixtures/" in path or "layer7-parity/" in path:
        return "test_fixture"
    if installed_runtime_payload_script_detector_reference(path, content):
        return "source_checkout_helper"
    if installed_runtime_agent_tool_declaration(path, content):
        return "source_checkout_helper"
    if path.startswith("speckit-pro/") and any(part in path for part in ("/scripts/", "/references/", "/templates/")):
        return "source_checkout_helper"
    if path.startswith(".github/workflows/"):
        if path == ".github/workflows/deploy-docs.yml" or is_docs_or_workflow_tooling(content):
            return "docs_non_runtime"
        if repository_bash_container_preflight_dispatch_glue(path, content):
            return "ci_dispatch_glue"
        if category == "bash" and pattern.startswith("run:") and is_direct_python_gate_dispatch(content):
            return "ci_dispatch_glue"
        return "blocking_active_runtime"
    if path in {"speckit-pro/codex-hooks.json", "speckit-pro/hooks/hooks.json"}:
        return "blocking_active_runtime"
    if installed_runtime_installed_runtime_requirement_without_source_context(path, content):
        return "blocking_active_runtime"
    if path.startswith("dist/") and not path.endswith(("README.md", "CHANGELOG.md", "LICENSE")):
        if "/scripts/" in path:
            return "blocking_active_runtime"
        if "/speckit_pro_runner/" in path and source_kind in {"repo", "repo_baseline"} and installed_runtime_source_checkout_helper_reference(path, content):
            return "source_checkout_helper"
        if source_kind == "repo_baseline" and installed_runtime_baseline_source_checkout_helper_reference(path, content):
            return "source_checkout_helper"
        if source_kind in {"repo", "repo_baseline"} and (
            (source_kind == "repo" and installed_runtime_changed_source_checkout_helper_reference(path, content))
            or installed_runtime_repo_surface_exception(category, pattern, content)
        ):
            return "source_checkout_helper"
        return "blocking_active_runtime"
    if path.startswith("speckit-pro/skills/") or path.startswith("speckit-pro/codex-skills/"):
        if source_kind == "repo_baseline" and (
            installed_runtime_baseline_source_checkout_helper_reference(path, content)
            or installed_runtime_repo_surface_exception(category, pattern, content)
        ):
            return "source_checkout_helper"
        if source_kind == "repo" and (
            installed_runtime_changed_source_checkout_helper_reference(path, content)
            or installed_runtime_repo_surface_exception(category, pattern, content)
        ):
            return "source_checkout_helper"
        return "blocking_active_runtime" if source_kind in {"fixture", "repo", "repo_baseline"} else "source_checkout_helper"
    if path.startswith("speckit-pro/agents/") or path.startswith("speckit-pro/codex-agents/"):
        if source_kind == "repo_baseline" and (
            installed_runtime_baseline_source_checkout_helper_reference(path, content)
            or installed_runtime_repo_surface_exception(category, pattern, content)
        ):
            return "source_checkout_helper"
        if source_kind == "repo" and (
            installed_runtime_changed_source_checkout_helper_reference(path, content)
            or installed_runtime_repo_surface_exception(category, pattern, content)
        ):
            return "source_checkout_helper"
        return "blocking_active_runtime" if source_kind in {"fixture", "repo", "repo_baseline"} else "source_checkout_helper"
    if path in {"README.md", "speckit-pro/README.md"} or path.startswith("docs-site/src/content/docs/"):
        if (
            source_kind in {"fixture", "repo", "repo_baseline"}
            and installed_runtime_installed_runtime_guidance_path(path)
            and installed_runtime_install_guidance_requires_shell(category, pattern, content)
        ):
            return "blocking_active_runtime"
        return "docs_non_runtime"
    return "source_checkout_helper"


def installed_runtime_active_role(path: str) -> str:
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


def installed_runtime_repo_surface_exception(category: str, pattern: str, content: str) -> bool:
    lowered = content.lower()
    has_negative_context = any(
        marker in lowered
        for marker in (
            "do not add",
            "must not ",
            "never ",
            "not require",
            "not add",
            "without requiring",
            "without adding",
            "without using",
            "avoid requiring",
            "avoid using",
            "avoid adding",
            "refuse",
            "forbidden",
            "not installed-runtime",
            "source-checkout",
            "maintainer-only",
            "maintainer shell",
            "specific command-language requirement",
            "contributor path",
            "source files",
            "source tree",
            "validation suite",
            "default suite",
            "structural validation",
            "structural-only changes",
            "while iterating",
            "local repository evidence",
            "spec kit's official docs",
            "spec kit installation guide",
            "specify init",
            "codex first-install guidance",
        )
    )
    if category == "shell_interpolation" and pattern.startswith("`"):
        return has_negative_context or not installed_runtime_backtick_requires_shell(pattern, content)
    return has_negative_context


def installed_runtime_install_guidance_requires_shell(category: str, pattern: str, content: str) -> bool:
    return not installed_runtime_repo_surface_exception(category, pattern, content)


def installed_runtime_installed_runtime_guidance_path(path: str) -> bool:
    if path in {"README.md", "speckit-pro/README.md"}:
        return True
    if path.startswith("docs-site/src/content/docs/install/"):
        return True
    return path == "docs-site/src/content/docs/troubleshooting.md"


def installed_runtime_agent_tool_declaration(path: str, content: str) -> bool:
    if not any(part in path for part in ("/agents/", "/codex-agents/", "/skills/", "/codex-skills/")):
        return False
    if "\n" in content or "\r" in content:
        return False
    if installed_runtime_likely_active_runtime_requirement(content) and not installed_runtime_repo_surface_exception("bash", "Bash", content):
        return False
    lines = [line.strip().lower() for line in content.splitlines() if line.strip()]
    tool_items = {"- bash", "- grep", "- glob", "- read", "- write", "- edit", "- websearch", "- webfetch"}
    for stripped in lines:
        declaration = re.match(r"^(?:allowed-tools:|disallowedtools:|tools\s*=|tools:)\s*(?P<value>[a-z0-9_, -]*)$", stripped)
        if declaration is not None:
            return True
        if stripped in tool_items:
            return True
        if re.match(r"^-\s+use\s+`(?:bash|grep|glob|read|write|edit|websearch|webfetch)`", stripped):
            return True
    return False


def installed_runtime_source_checkout_helper_reference(path: str, content: str) -> bool:
    lowered_path = path.lower()
    lowered = content.lower()
    if lowered_path.endswith(GUARD_SOURCE_PATHS):
        return True
    if installed_runtime_payload_script_detector_reference(path, content):
        return True
    if any(part in lowered_path for part in ("/references/", "/templates/", "/contracts/", "/scripts/")):
        return True
    markers = (
        "installed_runtime_likely_active_runtime_requirement",
        "installed_runtime_generated_payload_helper_context",
        "allowed-tools:",
        "tools:",
        "bash(",
        "grep(",
        "glob(",
        "```bash",
        "command -v",
        "uv tool install",
        "operator",
        "official speckit cli",
        "spec kit cli",
        "skipped when",
        "not on `path`",
        "not on path",
        "forbidden_patterns",
        "bash dependency",
        "shell=true subprocess execution",
        "manual classification request",
        "workflow shell dispatches a python gate",
        "is_direct_python_gate_dispatch",
        "blocking_active_gate",
        "re.match(",
        "argv-list subprocesses",
        "argv array",
        "existing bash gates authoritative",
        "existing bash workflow",
        "zero-bash-guard",
        "zero_bash_guard",
        "zero_bash_status",
        "zero_bash_blocking_count",
        "repo-bash-confinement",
        "repo_bash_confinement",
        "plugin-bash-confinement",
        "required_absent",
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


def installed_runtime_payload_script_detector_reference(path: str, content: str) -> bool:
    lowered_path = path.lower()
    if not lowered_path.endswith("speckit_pro_runner/gates/payloads.py"):
        return False
    lowered = content.lower()
    if "payload_has_shell_shebang" in lowered or "payload_script_file_count" in lowered:
        return True
    return "first_line = handle.readline" in lowered and "re.search" in lowered and "first_line" in lowered


def installed_runtime_changed_source_checkout_helper_reference(path: str, content: str) -> bool:
    lowered_path = path.lower()
    if any(part in lowered_path for part in ("/references/", "/templates/", "/contracts/", "/scripts/")):
        return True
    if path.startswith("dist/") and installed_runtime_generated_payload_helper_reference(path, content):
        return True
    return installed_runtime_explicit_source_checkout_context(content)


def installed_runtime_generated_payload_helper_reference(path: str, content: str) -> bool:
    lowered_path = path.lower()
    if not any(part in lowered_path for part in ("/skills/", "/codex-skills/", "/agents/", "/codex-agents/")):
        return False
    if installed_runtime_explicit_source_checkout_context(content):
        return True
    if installed_runtime_likely_active_runtime_requirement(content):
        return False
    if installed_runtime_generated_payload_helper_context(content):
        return True
    return installed_runtime_baseline_source_checkout_helper_reference(path, content)


def installed_runtime_generated_payload_helper_context(content: str) -> bool:
    lowered = content.lower()
    if ".sh" not in lowered and "bash" not in lowered and "jq" not in lowered:
        return False
    markers = (
        "exec_command",
        "<skill_scripts>",
        "script path:",
        "provided in your prompt",
        "generated runbook",
        "skeleton",
        "advisory",
        "fail-open",
    )
    helper_scripts = (
        "aggregate-crl.sh",
        "atomicity-route.sh",
        "check-prerequisites.sh",
        "confidence-gate.sh",
        "count-markers.sh",
        "create-new-feature.sh",
        "detect-commands.sh",
        "detect-presets.sh",
        "detect-stack-manager.sh",
        "estimate-spec-size.sh",
        "estimate-reviewable-loc.sh",
        "final-reviewability-backstop.sh",
        "generate-pr-body.sh",
        "generate-spec-index.sh",
        "generate-uat-skeleton.sh",
        "migrate-structure.sh",
        "multi-pr-emission.sh",
        "o5-topology.sh",
        "parse-consensus-categories.sh",
        "plan-layers.sh",
        "relocate-process-artifacts.sh",
        "resolve-confidence-mode.sh",
        "restack.sh",
        "reviewability-gate.sh",
        "validate-agent-install.sh",
        "validate-autopilot-phase-coverage.py",
        "validate-gate.sh",
        "validate-pr-packet.sh",
        "validate-pr-workflow-contract.sh",
        "validate-uat-runbook.sh",
    )
    return any(marker in lowered for marker in markers) or any(script in lowered for script in helper_scripts)


def installed_runtime_likely_active_runtime_requirement(content: str) -> bool:
    lowered = content.lower()
    markers = (
        "command -v",
        "git bash or wsl",
        "require git bash",
        "requires git bash",
        "require wsl",
        "requires wsl",
        "require jq",
        "requires jq",
        "install jq",
        "run bash",
        "execute bash",
        "invoke bash",
        "call bash",
        "use bash",
    )
    return any(marker in lowered for marker in markers)


def installed_runtime_installed_runtime_requirement_without_source_context(path: str, content: str) -> bool:
    if not installed_runtime_installed_runtime_surface(path):
        return False
    lowered_path = path.lower()
    if lowered_path.endswith(GUARD_SOURCE_PATHS):
        return False
    if any(part in lowered_path for part in ("/references/", "/templates/", "/contracts/", "/scripts/")):
        return False
    if installed_runtime_explicit_source_checkout_context(content) or installed_runtime_official_spec_kit_cli_context(content):
        return False
    return installed_runtime_likely_active_runtime_requirement(content)


def installed_runtime_official_spec_kit_cli_context(content: str) -> bool:
    lowered = content.lower()
    markers = (
        "official speckit cli",
        "official spec kit cli",
        "speckit cli",
        "spec kit cli",
        "command -v specify",
        "uv tool install specify-cli",
    )
    return any(marker in lowered for marker in markers)


def installed_runtime_installed_runtime_surface(path: str) -> bool:
    if path.startswith("dist/") and not path.endswith(("README.md", "CHANGELOG.md", "LICENSE")):
        return True
    if path in {"speckit-pro/codex-hooks.json", "speckit-pro/hooks/hooks.json"}:
        return True
    return path.startswith(
        (
            "speckit-pro/skills/",
            "speckit-pro/codex-skills/",
            "speckit-pro/agents/",
            "speckit-pro/codex-agents/",
        )
    )


def installed_runtime_explicit_source_checkout_context(content: str) -> bool:
    lowered = content.lower()
    markers = (
        "source-checkout",
        "source checkout",
        "source tree",
        "maintainer-only",
        "maintainer shell",
        "not installed-runtime",
    )
    return any(marker in lowered for marker in markers)


def installed_runtime_baseline_source_checkout_helper_reference(path: str, content: str) -> bool:
    lowered_path = path.lower()
    if any(part in lowered_path for part in ("/references/", "/templates/", "/contracts/", "/scripts/")):
        return True
    if installed_runtime_generated_payload_helper_context(content):
        return True
    lowered = content.lower()
    markers = (
        "allowed-tools:",
        "tools:",
        "bash(",
        "grep(",
        "glob(",
        "operator",
        "official speckit cli",
        "spec kit cli",
        "skipped when",
        "not on `path`",
        "not on path",
        "forbidden_patterns",
        "bash dependency",
        "shell=true subprocess execution",
        "manual classification request",
        "workflow shell dispatches a python gate",
        "is_direct_python_gate_dispatch",
        "blocking_active_gate",
        "re.match(",
        "argv-list subprocesses",
        "argv array",
        "existing bash gates authoritative",
        "existing bash workflow",
        "zero-bash-guard",
        "zero_bash_guard",
        "zero_bash_status",
        "zero_bash_blocking_count",
        "repo-bash-confinement",
        "repo_bash_confinement",
        "plugin-bash-confinement",
        "required_absent",
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
        "deterministic bash scripts",
        " is missing",
    )
    return any(marker in lowered for marker in markers)


def installed_runtime_backtick_requires_shell(pattern: str, content: str) -> bool:
    shell_markers = ("bash", "git bash", "wsl", "wsl.exe", "powershell", "pwsh", "$shell", "shell", "jq", ".sh", "grep", "sed", "awk")
    lowered_pattern = pattern.lower()
    if not any(marker in lowered_pattern for marker in shell_markers):
        return False
    lowered_content = content.lower()
    requirement_markers = ("run ", "execute ", "invoke ", "call ", "use ", "require ", "must ", "should ")
    return any(marker in lowered_content for marker in requirement_markers)


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


def missing_installed_runtime_scan_root_findings(repo_root: Path, case: dict[str, Any]) -> list[RawFinding]:
    roots = case.get("scan_roots")
    if "scan_roots" not in case:
        return []
    if not isinstance(roots, list):
        return [
            RawFinding(
                path="scan_roots",
                line=None,
                category="scan_root",
                pattern=type(roots).__name__,
                reason="configured active-runtime scan_roots must be a non-empty array",
                active_role="repository_text",
                classification="blocking_active_runtime",
                remediation="Keep active-runtime scan roots as a non-empty array of normalized repository-relative paths.",
            )
        ]
    if not roots:
        return [
            RawFinding(
                path="scan_roots",
                line=None,
                category="scan_root",
                pattern="[]",
                reason="configured active-runtime scan_roots must include at least one root",
                active_role="repository_text",
                classification="blocking_active_runtime",
                remediation="Keep active-runtime scan roots as a non-empty array of normalized repository-relative paths.",
            )
        ]
    findings: list[RawFinding] = []
    for index, root in enumerate(roots):
        root_path, root_pattern, invalid_reason = scan_root_entry_validation(index, root)
        if invalid_reason is not None:
            findings.append(
                RawFinding(
                    path=root_path,
                    line=None,
                    category="scan_root",
                    pattern=root_pattern,
                    reason=invalid_reason,
                    active_role=installed_runtime_active_role(root_path),
                    classification="blocking_active_runtime",
                    remediation="Keep active-runtime scan roots normalized, repository-relative, and inside the repository.",
                )
            )
            continue
        root = str(root)
        if (repo_root / normalize_path(root)).exists():
            continue
        findings.append(
            RawFinding(
                path=root,
                line=None,
                category="scan_root",
                pattern=root,
                reason="configured active-runtime scan root is missing",
                active_role=installed_runtime_active_role(root),
                classification="blocking_active_runtime",
                remediation="Restore the active-runtime scan root or remove it from the promoted final-current fixture.",
            )
        )
    return findings


def active_runtime_base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    gate_status = "pass" if status == "ok" else "fail" if status == "expected_failure" else status
    return {
        "gate": {
            "gate_id": entry.helper_id,
            "operation": operation,
            "gate_status": gate_status,
            "promoted": status != "input_error",
            "blocking": status != "ok",
            "comparison_ids": [f"installed-plugin-release-{operation}"],
        },
        "artifacts": [
            {"path": INSTALLED_RUNTIME_DEFAULT_CASE_FILE, "kind": "fixture"},
        ],
    }


def runtime_guard_script_file(path: str) -> tuple[str, str] | None:
    if has_prohibited_script_suffix(path):
        return Path(path).suffix, "script file retained in scanned scope"
    return None


RUNTIME_GUARD_POLICY = GuardPolicy(
    schema_version="2.0",
    contract_id="installed-plugin-release",
    blocking_classification="blocking_active_runtime",
    bound_findings=True,
    base_data=active_runtime_base_data,
    active_role=installed_runtime_active_role,
    classify=classify_installed_runtime_path,
    remediations={
        "blocking_active_runtime": "Replace the installed-runtime shell dependency with argv-only Python runner invocation.",
        "ci_dispatch_glue": "Keep CI glue limited to direct Python runner dispatch.",
        "archive_provenance": "No change required for historical archive text.",
        "upstream_spec_kit_helper": "No change required for upstream consumer Spec Kit helper evidence.",
        "test_fixture": "No change required for fixture or parity evidence.",
        "source_checkout_helper": "Keep source-checkout helper references out of installed-runtime instructions.",
        "docs_non_runtime": "No change required for non-runtime docs prose.",
    },
    default_remediation="No active-runtime change required.",
    script_file=runtime_guard_script_file,
    line_context_window=True,
    bare_line_context=installed_runtime_agent_tool_declaration,
    blocked_code="active_runtime_guard_blocked",
    blocked_message="active-runtime guard found prohibited shell-only behavior in installed-runtime surfaces",
    blocked_summary="Move active installed-runtime behavior to argv-only Python runner invocation.",
    blocked_actions=(
        "Inspect data.findings for blocking_active_runtime entries.",
        "Use a resolved Python 3.11+ executable with -m speckit_pro_runner and JSON stdin/stdout.",
    ),
)


def scan_installed_runtime_sources(sources: list[SourceFile], repo_root: Path) -> list[RawFinding]:
    return scan_with_policy(RUNTIME_GUARD_POLICY, sources)
