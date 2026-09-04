"""Active-path no-shell/no-jq guard operations."""

from __future__ import annotations

import ast
import copy
import json
import os
import re
import shlex
import string
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, is_diagnostic, response
from ..path_utils import find_repo_root, is_relative_to

DEFAULT_CASE_FILE = "tests/speckit-pro/unit/fixtures/runner-gates/active-path-guard-cases.json"
INSTALLED_RUNTIME_DEFAULT_CASE_FILE = "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json"
PLUGIN_BASH_CONFINEMENT_DEFAULT_CASE_FILE = "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/zero-bash-guard-cases.json"
PLUGIN_BASH_CONFINEMENT_ALLOWLIST = "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/allowlist.json"
REPOSITORY_BASH_CONFINEMENT_DEFAULT_CASE_FILE = "tests/speckit-pro/unit/fixtures/repository-bash-confinement/confinement-guard-cases.json"
REPOSITORY_BASH_CONFINEMENT_ALLOWLIST = "tests/speckit-pro/unit/fixtures/repository-bash-confinement/allowlist.json"
CONTAINER_PREFLIGHT_WORKFLOW = ".github/workflows/container-preflight.yml"
REPOSITORY_BASH_CONFINEMENT_ALLOWLIST_PATHS = frozenset(
    {
        ".specify/extensions/git/scripts/bash/auto-commit.sh",
        ".specify/extensions/git/scripts/bash/create-new-feature.sh",
        ".specify/extensions/git/scripts/bash/git-common.sh",
        ".specify/extensions/git/scripts/bash/initialize-repo.sh",
        ".specify/extensions/verify/scripts/bash/load-config.sh",
        ".specify/scripts/bash/check-prerequisites.sh",
        ".specify/scripts/bash/common.sh",
        ".specify/scripts/bash/create-new-feature.sh",
        ".specify/scripts/bash/resolve-template.sh",
        ".specify/scripts/bash/setup-plan.sh",
        ".specify/scripts/bash/setup-tasks.sh",
    }
)
REPO_BASH_SCRIPT_SUFFIXES = (".sh", ".bash")
REPO_BASH_COMMAND_NAMES = frozenset({"bash", "bash.exe", "jq", "jq.exe"})
REPO_BASH_SHEBANG_NAMES = frozenset({"bash", "bash.exe", "sh", "sh.exe"})
REPO_BASH_WORKFLOW_PREFIX = ".github/workflows/"
REPO_BASH_WORKFLOW_SUFFIXES = frozenset({".yaml", ".yml"})
REPO_BASH_WORKFLOW_DYNAMIC_PATH = re.compile(r"[$`*?\[\]{}]|%[^%\r\n]+%")
REPO_BASH_ACTIVE_INSTRUCTION_FILES = frozenset(
    {
        ".claude/claude-security-guidance.md",
        ".github/copilot-instructions.md",
        ".specify/extensions/speckit-utils/commands/doctor.md",
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
        "speckit-pro/README.md",
    }
)
REPO_BASH_ACTIVE_INSTRUCTION_PREFIXES = (
    ".claude/agents/",
    ".claude/skills/",
    "docs-site/src/content/docs/",
    "docs-site/src/data/",
)
REPO_BASH_RUNTIME_OUTPUT_KEYS = frozenset(
    {
        "actions",
        "error",
        "message",
        "remediation",
        "remediation_actions",
        "remediation_summary",
        "rollback",
        "stderr_line",
        "summary",
    }
)
REPO_BASH_SCRIPT_REFERENCE = re.compile(
    r"(?<![\w*])(?P<path>(?:\.{0,2}/)?(?:\.?[A-Za-z0-9_][A-Za-z0-9_.-]*/)*"
    r"[A-Za-z0-9_][A-Za-z0-9_.-]*\.(?:sh|bash))(?![\w-])",
    re.IGNORECASE,
)
REPO_BASH_DIRECT_COMMAND = re.compile(
    r"(?:^|[`'\"(:=]\s*)(?P<command>bash|bash\.exe|jq|jq\.exe|sh|sh\.exe)\s+(?P<argument>[^\s`'\")]+)",
    re.IGNORECASE,
)
REPO_BASH_ACTIONABLE_TOOL = re.compile(
    r"\b(?:execute|install|invoke|require|requires|required|run|use|uses|using)\s+"
    r"(?:an?\s+|the\s+|external\s+)*(?P<command>bash|bash\.exe|jq|jq\.exe|sh|sh\.exe)\b",
    re.IGNORECASE,
)
REPO_BASH_NON_ACTIONABLE_CONTEXT = re.compile(
    r"\b(?:archive|archived|avoid|block|blocked|blocking|deprecated|deleted|does\s+not|do\s+not|earlier|"
    r"former|formerly|historical|history|inactive|legacy|mention|mentions|must\s+not|never|no\s+longer|"
    r"not\s+require|prior|prohibit|prohibited|provenance|remove|removed|retired|without|zero[- ]bash)\b",
    re.IGNORECASE,
)
REPO_BASH_EXPLICIT_DIRECTIVE = re.compile(
    r"^\s*(?:(?:[-*+]\s+)|(?:\d+[.)]\s+))?(?:\*\*|`)?"
    r"(?:execute|install|invoke|require|requires|required|run|use|uses|using)\b",
    re.IGNORECASE,
)
REPO_BASH_MODAL_DIRECTIVE = re.compile(
    r"\b(?:can|could|must|need(?:s)?\s+to|shall|should|will|would)\s+"
    r"(?:execute|install|invoke|require|run|use)\b",
    re.IGNORECASE,
)
REPO_BASH_WRAPPED_NEGATIVE = re.compile(
    r"\b(?:can|could|did|do|does|must|need|shall|should|will|would)\s+not\s*$|"
    r"\b(?:no\s+longer|never|without)\s*$",
    re.IGNORECASE,
)
REPO_BASH_FIXTURE_PREFIXES = (
    "tests/speckit-pro/unit/fixtures/",
)
REPO_BASH_RESOLUTION_MAX_DEPTH = 12
REPO_BASH_RESOLUTION_MAX_ITEMS = 64
REPO_BASH_RESOLUTION_MAX_STRING = 4096
PLUGIN_BASH_CONFINEMENT_REQUIRED_SCAN_ROOTS = frozenset(
    {
        "speckit-pro",
        "scripts/build-plugin-payloads.py",
        "dist/claude/speckit-pro",
        "dist/codex/speckit-pro",
        "README.md",
    }
)
PROHIBITED_SCRIPT_SUFFIXES = (".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd")
PROHIBITED_COMMAND_NAMES = {"bash", "bash.exe", "jq", "jq.exe", "wsl", "wsl.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe"}
SHELL_RUNTIME_COMMAND_NAMES = {"sh", "sh.exe", "zsh", "zsh.exe"}
SHELL_COMMAND_NAMES = {"sh", "sh.exe", "bash", "bash.exe", "zsh", "zsh.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe"}
SUBPROCESS_ARGV_FUNCTION_NAMES = {"run", "Popen", "call", "check_call", "check_output"}
SUBPROCESS_SHELL_FUNCTION_NAMES = {"getoutput", "getstatusoutput"}
OS_SHELL_FUNCTION_NAMES = {"system", "popen"}
SHELL_RUNTIME_TOKEN_PATTERN = r"(?:[A-Za-z]:[\\/])?(?:[^\s\"'`,\]\[]+[\\/])?(?:sh|zsh)(?:\.exe)?"
TEXT_SUFFIXES = frozenset({".json", ".md", ".py", ".ps1", ".bat", ".cmd", ".sh", ".bash", ".zsh", ".toml", ".txt", ".yaml", ".yml"})
HARD_RUNTIME_CATEGORIES = frozenset(
    {
        "script_file",
        "shell_command_wrapper",
        "shell_runtime",
        "shell_true",
        "os_system",
        "command_string_subprocess",
        "command_argv_subprocess",
    }
)
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
    ("shell_true", re.compile(r"[\"']?shell[\"']?\s*[:=]\s*true", re.IGNORECASE), "shell=True subprocess execution"),
    ("os_system", re.compile(r"\bos\.system\s*\("), "os.system shell execution"),
    (
        "command_string_subprocess",
        re.compile(r"\bsubprocess\.(?:run|Popen|call|check_call|check_output)\(\s*[\"']"),
        "command-string subprocess execution",
    ),
    (
        "shell_command_wrapper",
        re.compile(
            r"(?:[\"'](?:[^\"']*[\\/])?(?:sh|zsh|bash|powershell|pwsh)(?:\.exe)?[\"']\s*,\s*"
            r"(?:(?:[\"'](?!-[A-Za-z]*c[A-Za-z]*[\"'])--?[A-Za-z][A-Za-z0-9-]*[\"']\s*,\s*)"
            r"(?:[\"'](?!-)[^\"']+[\"']\s*,\s*)?){0,6}[\"']-[A-Za-z]*c[A-Za-z]*[\"'])|"
            r"(?<![\w-])(?:[A-Za-z]:[\\/])?(?:[^\s\"'`]+[\\/])?(?:sh|zsh|bash|powershell|pwsh)(?:\.exe)?\s+"
            r"(?:(?!-[A-Za-z]*c[A-Za-z]*\b)--?[A-Za-z][A-Za-z0-9-]*\s+(?:(?!-)\S+\s+)?){0,6}-[A-Za-z]*c[A-Za-z]*\b",
            re.IGNORECASE,
        ),
        "shell command wrapper dependency",
    ),
    (
        "shell_runtime",
        re.compile(
            rf"(?:\[[ \t]*[\"']{SHELL_RUNTIME_TOKEN_PATTERN}[\"'][ \t]*\])|"
            rf"(?:^[ \t]*(?:[\w-]*command|cmd|argv|args|runtime)[ \t]*[:=][ \t]*(?:\[[^\]\n]*)?[\"']?{SHELL_RUNTIME_TOKEN_PATTERN}[\"']?(?=[ \t]*(?:,|\]|$)))|"
            rf"(?:^[ \t]*(?:allowed-tools|tools[ \t]*=|tools:)[ \t]*[^\n]*?(?<![\w./-]){SHELL_RUNTIME_TOKEN_PATTERN}(?![\w-]))|"
            rf"(?:(?<!do not )(?<!don't )(?<!must not )(?<!never )\b(?:run|use|require|requires|execute|invoke|call|install)[ \t]+[\"']?{SHELL_RUNTIME_TOKEN_PATTERN}[\"']?\b)|"
            r"(?:[\"'](?:[^\"']*[\\/])?(?:sh|zsh)(?:\.exe)?[\"']\s*,)|"
            r"(?:[\"'](?:[^\"']*[\\/])?env(?:\.exe)?[\"']\s*,\s*[\"'](?:sh|zsh)(?:\.exe)?[\"'])|"
            r"(?<![\w./-])(?:[A-Za-z]:[\\/])?(?:[^\s\"'`,]+[\\/])?(?:sh|zsh)(?:\.exe)?\s+(?!-[A-Za-z]*c[A-Za-z]*\b)[^\s#]+",
            re.IGNORECASE | re.MULTILINE,
        ),
        "Unix shell runtime dependency",
    ),
    ("jq", re.compile(r"(?<![\w-])jq(?![\w-])|--jq\b", re.IGNORECASE), "jq command dependency"),
    ("bash", re.compile(r"^#!.*\bbash\b|\bbash\b", re.IGNORECASE), "Bash dependency"),
    ("script_file", re.compile(r"(?<![\w./-])[^\"'`\s<>)\]]+\.(?:sh|bash|zsh|ps1|bat|cmd)\b", re.IGNORECASE), "script path dependency"),
    ("shell_parsing", re.compile(r"\|.*\b(?:grep|sed|awk)\b|\b(?:grep|sed|awk)\b.*\|", re.IGNORECASE), "shell parsing pipeline"),
    (
        "shell_interpolation",
        re.compile(
            r"\$\(|"
            r"\$\{?SHELL\}?|"
            r"`[^`]*(?:"
            r"\bbash\b|\bgit\s+bash\b|\bwsl(?:\.exe)?\b|\bpowershell\b|\bpwsh\b|"
            r"(?<![\w-])jq(?![\w-])|--jq\b|[^`\"'\s]+\.(?:sh|bash|zsh|ps1|bat|cmd)\b|"
            r"\|\s*(?:grep|sed|awk)\b|\b(?:grep|sed|awk)\s*\|"
            r")[^`]*`",
            re.IGNORECASE,
        ),
        "shell command substitution",
    ),
)
FORBIDDEN_CONTENT_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "shell_command_wrapper",
        re.compile(
            r"[\"'](?:[^\"']*[\\/])?(?:sh|zsh|bash|powershell|pwsh)(?:\.exe)?[\"'][ \t]*,[ \t]*\r?\n"
            r"(?:(?:[ \t]*[\"'](?!-[A-Za-z]*c[A-Za-z]*[\"'])--?[A-Za-z][A-Za-z0-9-]*[\"'][ \t]*,[ \t]*\r?\n)"
            r"(?:[ \t]*[\"'](?!-)[^\"']+[\"'][ \t]*,[ \t]*\r?\n)?){0,6}"
            r"[ \t]*[\"']-[A-Za-z]*c[A-Za-z]*[\"']",
            re.IGNORECASE,
        ),
        "shell command wrapper dependency",
    ),
    (
        "shell_command_wrapper",
        re.compile(
            r"^[ \t]*-[ \t]*[\"']?(?:[^\s\"'`]+[\\/])?(?:sh|zsh|bash|powershell|pwsh)(?:\.exe)?[\"']?[ \t]*(?:\r?\n)+"
            r"(?:(?:[ \t]*-[ \t]*[\"']?(?!-[A-Za-z]*c[A-Za-z]*[\"']?)--?[A-Za-z][A-Za-z0-9-]*[\"']?[ \t]*(?:\r?\n)+)"
            r"(?:[ \t]*-[ \t]*[\"']?(?!-)[^\r\n\"']+[\"']?[ \t]*(?:\r?\n)+)?){0,6}"
            r"[ \t]*-[ \t]*[\"']?-[A-Za-z]*c[A-Za-z]*[\"']?",
            re.IGNORECASE | re.MULTILINE,
        ),
        "shell command wrapper dependency",
    ),
    (
        "shell_runtime",
        re.compile(
            rf"^[ \t]*(?:[\w-]*command|cmd|argv|args|runtime)[ \t]*:[ \t]*(?:\r?\n)+"
            rf"[ \t]*-[ \t]*[\"']?{SHELL_RUNTIME_TOKEN_PATTERN}[\"']?[ \t]*(?:\r?\n|$)",
            re.IGNORECASE | re.MULTILINE,
        ),
        "Unix shell runtime dependency",
    ),
    (
        "shell_runtime",
        re.compile(
            rf"[\"'](?:[\w-]*command|cmd|argv|args|runtime)[\"'][ \t]*:[ \t]*\[[ \t]*(?:\r?\n)?"
            rf"[ \t]*[\"']{SHELL_RUNTIME_TOKEN_PATTERN}[\"'][ \t]*(?:,?[ \t]*(?:\r?\n)?[ \t]*\])",
            re.IGNORECASE,
        ),
        "Unix shell runtime dependency",
    ),
    (
        "shell_runtime",
        re.compile(
            r"[\"'](?:[^\"']*[\\/])?(?:sh|zsh)(?:\.exe)?[\"'][ \t]*,[ \t]*\r?\n"
            r"[ \t]*[\"'](?!-[A-Za-z]*c[A-Za-z]*[\"'])[^\"']+[\"']",
            re.IGNORECASE,
        ),
        "Unix shell runtime dependency",
    ),
    (
        "shell_runtime",
        re.compile(
            r"^[ \t]*-[ \t]*[\"']?(?:[^\s\"'`]+[\\/])?(?:sh|zsh)(?:\.exe)?[\"']?[ \t]*(?:\r?\n)+"
            r"[ \t]*-[ \t]*[\"']?(?!-[A-Za-z]*c[A-Za-z]*[\"']?)[^\r\n\"']+[\"']?",
            re.IGNORECASE | re.MULTILINE,
        ),
        "Unix shell runtime dependency",
    ),
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
    "installed_runtime_cutover_surface",
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
class StaticAssignment:
    value: list[str] | str | bool
    line: int
    column: int


@dataclass(frozen=True)
class PartialStaticAssignment:
    value: list[str | None]
    line: int
    column: int


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


@dataclass(frozen=True)
class RepoBashStaticResolution:
    kind: str
    scalar: str | None = None
    argv: tuple[str | None, ...] = ()


@dataclass(frozen=True)
class RepoBashBindingEvent:
    kind: str
    line: int
    column: int
    context: ast.AST
    arguments: tuple[ast.AST, ...]


@dataclass(frozen=True)
class RepoBashGuidanceString:
    line: int
    value: str
    complete: bool


@dataclass(frozen=True)
class RepoBashGuidanceResolution:
    kind: str
    values: tuple[RepoBashGuidanceString, ...] = ()


@dataclass(frozen=True)
class RepoBashShellBindingEvent:
    name: str
    category: str | None
    line: int
    column: int
    dominates: bool


REPO_BASH_UNKNOWN_RESOLUTION = RepoBashStaticResolution("unknown")
REPO_BASH_NONE_RESOLUTION = RepoBashStaticResolution("none")
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
    return guard_response(entry, request, findings)


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


def run_repo_bash_confinement(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    """Run the live tracked-file Bash confinement scan."""
    allowlist_result = load_repo_bash_allowlist(repo_root, request.inputs)
    if is_diagnostic(allowlist_result):
        return response(
            "input_error",
            request_id=request.request_id,
            data=repo_bash_base_data(entry, request.operation, "input_error", request.inputs),
            diagnostics=[allowlist_result],
        )
    allowlist = allowlist_result

    tracked_result = repo_bash_tracked_paths(repo_root)
    if is_diagnostic(tracked_result):
        data = repo_bash_base_data(entry, request.operation, "missing_prerequisite", request.inputs)
        data["allowlist"] = repo_bash_allowlist_summary(request.inputs, allowlist)
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            data=data,
            diagnostics=[tracked_result],
        )

    tracked_paths = tracked_result
    tracked_path_set = set(tracked_paths)
    missing_allowlisted_paths = sorted(REPOSITORY_BASH_CONFINEMENT_ALLOWLIST_PATHS - tracked_path_set)
    if missing_allowlisted_paths:
        data = repo_bash_base_data(entry, request.operation, "input_error", request.inputs)
        data.update(
            {
                "allowlist": repo_bash_allowlist_summary(request.inputs, allowlist),
                "enumeration": {
                    "active_instruction_values": "not_inspected",
                    "runtime_diagnostic_values": "not_inspected",
                    "source": "git ls-files -z",
                    "workflow_run_values": "not_inspected",
                    "tracked_file_count": len(tracked_paths),
                },
            }
        )
        return response(
            "input_error",
            request_id=request.request_id,
            data=data,
            diagnostics=[
                diagnostic(
                    "invalid_allowlist",
                    "repository Bash allowlist references canonical paths missing from the tracked tree",
                    details={"missing": missing_allowlisted_paths},
                    remediation_summary="Restore the canonical vendored Spec Kit helpers or update the specification first.",
                    remediation_actions=[
                        "Restore every missing canonical helper from the pinned Spec Kit source.",
                        "Do not use a stale allowlist to represent files absent from the tracked tree.",
                    ],
                )
            ],
        )

    findings: list[RawFinding] = []
    for path in tracked_paths:
        findings.extend(
            repo_bash_path_findings(
                repo_root,
                path,
                allowlist,
                tracked_paths=tracked_path_set,
            )
        )

    blocking = [finding for finding in findings if finding.classification == "blocking_repo_bash"]
    status = "expected_failure" if blocking else "ok"
    data = repo_bash_base_data(entry, request.operation, status, request.inputs)
    data.update(
        {
            "schema_version": "2.0",
            "contract_id": "repository-bash-confinement",
            "status": "fail" if blocking else "pass",
            "blocking_count": len(blocking),
            "classified_counts": classified_counts(findings),
            "findings": [repo_bash_finding_record(finding) for finding in findings],
            "total_finding_count": len(findings),
            "truncated_finding_count": 0,
            "script_file_count": sum(
                finding.category == "script_file" and finding.classification == "blocking_repo_bash"
                for finding in findings
            ),
            "enumeration": {
                "active_instruction_values": "inspected",
                "runtime_diagnostic_values": "inspected",
                "source": "git ls-files -z",
                "workflow_run_values": "inspected",
                "tracked_file_count": len(tracked_paths),
            },
            "allowlist": repo_bash_allowlist_summary(request.inputs, allowlist),
        }
    )
    if not blocking:
        return response("ok", request_id=request.request_id, data=data)

    diag = diagnostic(
        "repo_bash_confinement_blocked",
        "repository Bash confinement found non-allowlisted Bash behavior",
        details={
            "blocking_count": len(blocking),
            "categories": sorted({finding.category for finding in blocking}),
            "paths": sorted({finding.path for finding in blocking})[:20],
        },
        remediation_summary="Remove repo-local Bash behavior or restore the exact vendored Spec Kit allowlist.",
        remediation_actions=[
            "Inspect data.findings for blocking_repo_bash entries.",
            "Port executable behavior to Python and keep each workflow run value to one approved direct dispatch.",
            "Do not broaden or substitute the canonical repository Bash allowlist.",
        ],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def load_repo_bash_allowlist(repo_root: Path, inputs: dict[str, Any]) -> list[dict[str, Any]] | dict[str, Any]:
    raw = inputs.get("allowlist_file", REPOSITORY_BASH_CONFINEMENT_ALLOWLIST)
    if not isinstance(raw, str) or not raw:
        return diagnostic("invalid_allowlist", "repository Bash allowlist path must be a non-empty string")
    path = resolve_path(raw, repo_root)
    root = repo_root.resolve(strict=False)
    if not is_relative_to(path.resolve(strict=False), root):
        return diagnostic("invalid_allowlist", "repository Bash allowlist must stay inside the repository")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return diagnostic(
            "invalid_allowlist",
            "repository Bash allowlist could not be loaded",
            details={"allowlist_file": raw, "error": type(exc).__name__},
        )
    if not isinstance(document, dict) or set(document) != {"schema_version", "contract_id", "entries"}:
        return diagnostic("invalid_allowlist", "repository Bash allowlist has unsupported top-level fields")
    if document.get("schema_version") != "2.0" or document.get("contract_id") != "repository-bash-confinement":
        return diagnostic("invalid_allowlist", "repository Bash allowlist identity must be repository-bash-confinement schema 2.0")
    expected_paths = REPOSITORY_BASH_CONFINEMENT_ALLOWLIST_PATHS
    expected_count = len(expected_paths)
    entries = document.get("entries")
    if not isinstance(entries, list) or len(entries) != expected_count:
        return diagnostic(
            "invalid_allowlist",
            f"repository Bash allowlist must contain exactly {expected_count} entries",
            details={
                "expected_entry_count": expected_count,
                "actual_entry_count": len(entries) if isinstance(entries, list) else None,
            },
        )

    expected_fields = {"path", "categories", "reason", "scope", "release_readiness_excluded"}
    normalized_entries: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != expected_fields:
            return diagnostic("invalid_allowlist", "repository Bash allowlist entries have unsupported fields")
        path_value = entry.get("path")
        categories = entry.get("categories")
        reason = entry.get("reason")
        if not isinstance(path_value, str) or invalid_scan_root_reason(path_value) is not None:
            return diagnostic("invalid_allowlist", "repository Bash allowlist paths must be repository-relative")
        normalized_path = normalize_path(path_value)
        if (
            entry.get("scope") != "vendored_specify_helper"
            or entry.get("release_readiness_excluded") is not True
            or not isinstance(categories, list)
            or not categories
            or any(not isinstance(category, str) or not category for category in categories)
            or len(set(categories)) != len(categories)
            or not isinstance(reason, str)
            or not reason.strip()
        ):
            return diagnostic("invalid_allowlist", "repository Bash allowlist entry contract is invalid")
        normalized_entry = dict(entry)
        normalized_entry["path"] = normalized_path
        normalized_entries.append(normalized_entry)

    actual_paths = [entry["path"] for entry in normalized_entries]
    if len(set(actual_paths)) != len(actual_paths) or set(actual_paths) != expected_paths:
        return diagnostic(
            "invalid_allowlist",
            (
                "repository Bash allowlist must equal the exact canonical "
                f"{expected_count}-path set"
            ),
            details={
                "expected_entry_count": expected_count,
                "actual_entry_count": len(actual_paths),
                "missing": sorted(expected_paths - set(actual_paths)),
                "unexpected": sorted(set(actual_paths) - expected_paths),
            },
        )
    return normalized_entries


def repo_bash_allowlist_summary(inputs: dict[str, Any], allowlist: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "path": inputs.get("allowlist_file", REPOSITORY_BASH_CONFINEMENT_ALLOWLIST),
        "entry_count": len(allowlist),
        "release_readiness_excluded": bool(allowlist)
        and all(entry.get("release_readiness_excluded") is True for entry in allowlist),
    }


def repo_bash_tracked_paths(repo_root: Path) -> list[str] | dict[str, Any]:
    argv = ["git", "ls-files", "-z"]
    try:
        completed = subprocess.run(
            argv,
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return diagnostic(
            "missing_prerequisite",
            "repository Bash confinement could not run git ls-files",
            details={"argv": argv, "error": type(exc).__name__},
            remediation_summary="Install Git and run the guard from a source checkout.",
            remediation_actions=["Make git available on PATH.", "Retry from the repository root."],
        )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip() if isinstance(completed.stderr, bytes) else str(completed.stderr).strip()
        return diagnostic(
            "missing_prerequisite",
            "repository Bash confinement requires a readable Git index",
            details={"argv": argv, "returncode": completed.returncode, "stderr": stderr[:240]},
            remediation_summary="Run the guard from a Git source checkout with a readable index.",
            remediation_actions=["Confirm git status succeeds.", "Retry the same guard request."],
        )
    stdout = completed.stdout if isinstance(completed.stdout, bytes) else str(completed.stdout).encode()
    return [normalize_path(item.decode("utf-8", errors="surrogateescape")) for item in stdout.split(b"\0") if item]


def repo_bash_path_findings(
    repo_root: Path,
    tracked_path: str,
    allowlist: list[dict[str, Any]],
    *,
    tracked_paths: set[str] | None = None,
) -> list[RawFinding]:
    path = normalize_path(tracked_path)
    if invalid_scan_root_reason(path) is not None:
        return [
            repo_bash_raw_finding(
                path,
                None,
                "path_confinement",
                path,
                "tracked path is not confined to the repository",
                allowlisted=False,
            )
        ]

    allowlisted = path in {entry["path"] for entry in allowlist}
    suffix = Path(path).suffix.lower()
    if suffix in REPO_BASH_SCRIPT_SUFFIXES:
        return [
            repo_bash_raw_finding(
                path,
                1,
                "script_file",
                suffix,
                "tracked Bash-family script suffix",
                allowlisted=allowlisted,
            )
        ]

    content_path = repo_bash_content_path(repo_root, path)
    if content_path is None:
        return []
    first_line = read_first_line(content_path)
    if repo_bash_shebang(first_line):
        return [
            repo_bash_raw_finding(
                path,
                1,
                "script_file",
                first_line.strip()[:120],
                "tracked file has a Bash/POSIX-sh shebang",
                allowlisted=allowlisted,
            )
        ]

    if not repo_bash_invocation_scan_path(path):
        return []
    try:
        content = content_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    if path.startswith(REPO_BASH_WORKFLOW_PREFIX) and Path(path).suffix.lower() in REPO_BASH_WORKFLOW_SUFFIXES:
        return repo_bash_workflow_findings(
            path,
            content,
            tracked_paths or set(),
            repo_root=repo_root,
        )
    if Path(path).suffix.lower() == ".py":
        findings = repo_bash_python_findings(path, content)
        if repo_bash_runtime_diagnostic_scan_path(path):
            findings.extend(repo_bash_runtime_diagnostic_findings(path, content))
        return findings
    if Path(path).name.lower() in {"hooks.json", "package.json"}:
        return repo_bash_json_findings(path, content)
    if repo_bash_active_instruction_scan_path(path):
        return repo_bash_instruction_findings(path, content)
    return []


def repo_bash_content_path(repo_root: Path, tracked_path: str) -> Path | None:
    root = repo_root.resolve(strict=False)
    candidate = repo_root / tracked_path
    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError):
        return None
    if not is_relative_to(resolved, root) or not resolved.is_file():
        return None
    return resolved


def repo_bash_invocation_scan_path(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized.startswith(REPO_BASH_FIXTURE_PREFIXES) or "/fixtures/" in normalized:
        return False
    if Path(normalized).name.lower().endswith("-baseline.txt"):
        return False
    if normalized.startswith(REPO_BASH_WORKFLOW_PREFIX):
        return Path(normalized).suffix.lower() in REPO_BASH_WORKFLOW_SUFFIXES
    return (
        Path(normalized).suffix.lower() == ".py"
        or Path(normalized).name.lower() in {"hooks.json", "package.json"}
        or repo_bash_active_instruction_scan_path(normalized)
    )


def repo_bash_active_instruction_scan_path(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized in REPO_BASH_ACTIVE_INSTRUCTION_FILES:
        return True
    if not normalized.startswith(REPO_BASH_ACTIVE_INSTRUCTION_PREFIXES):
        return False
    suffix = Path(normalized).suffix.lower()
    if normalized.startswith(".claude/agents/"):
        return suffix == ".md" and len(Path(normalized).parts) == 3
    if normalized.startswith(".claude/skills/"):
        return suffix == ".md" and Path(normalized).name == "SKILL.md" and len(Path(normalized).parts) == 4
    return suffix in {".md", ".mdx", ".ts"}


def repo_bash_runtime_diagnostic_scan_path(path: str) -> bool:
    normalized = normalize_path(path)
    return normalized.startswith("speckit-pro/speckit_pro_runner/") and normalized.endswith(".py")


def repo_bash_shebang(content: str) -> bool:
    try:
        first_line = content.splitlines()[0].strip()
    except IndexError:
        return False
    if not first_line.startswith("#!"):
        return False
    try:
        argv = shlex.split(first_line[2:].strip())
    except ValueError:
        argv = first_line[2:].strip().split()
    if not argv:
        return False
    if executable_basename(argv[0]) == "env":
        return any(
            delegated and executable_basename(delegated[0]) in REPO_BASH_SHEBANG_NAMES
            for delegated in env_delegated_argvs(["env", *argv[1:]])
        )
    return executable_basename(argv[0]) in REPO_BASH_SHEBANG_NAMES


def repo_bash_raw_finding(
    path: str,
    line: int | None,
    category: str,
    pattern: str,
    reason: str,
    *,
    allowlisted: bool = False,
) -> RawFinding:
    return RawFinding(
        path=path,
        line=line,
        category=category,
        pattern=pattern,
        reason=reason,
        active_role="vendored_specify_helper" if allowlisted else "repository",
        classification="vendored_specify_helper" if allowlisted else "blocking_repo_bash",
        remediation=(
            "Keep this exact vendored helper release-readiness excluded."
            if allowlisted
            else "Remove the Bash-family file or active bash/jq invocation."
        ),
    )


def repo_bash_finding_record(finding: RawFinding) -> dict[str, Any]:
    record = finding.as_record()
    if finding.classification == "vendored_specify_helper":
        record["release_readiness_excluded"] = True
    return record


def repo_bash_instruction_findings(
    path: str,
    content: str,
    *,
    line_offset: int = 0,
    active_role: str = "active_instruction",
    category_prefix: str = "instruction",
) -> list[RawFinding]:
    """Find active shell guidance while preserving negative and vendored prose."""
    lines = content.splitlines()
    findings: list[RawFinding] = []
    for index, line in enumerate(lines):
        line_number = line_offset + index + 1
        non_actionable = repo_bash_instruction_non_actionable(lines, index)

        script_matches = list(REPO_BASH_SCRIPT_REFERENCE.finditer(line))
        blocking_script_reference = False
        for match in script_matches:
            target = repo_bash_instruction_target(match.group("path"))
            if target in REPOSITORY_BASH_CONFINEMENT_ALLOWLIST_PATHS or non_actionable:
                continue
            blocking_script_reference = True
            findings.append(
                repo_bash_instruction_finding(
                    path,
                    line_number,
                    f"{category_prefix}_script_path",
                    match.group("path"),
                    "active instruction references a retired or non-allowlisted shell helper",
                    active_role=active_role,
                )
            )

        if non_actionable or blocking_script_reference:
            continue
        for match in REPO_BASH_DIRECT_COMMAND.finditer(line):
            command = executable_basename(match.group("command"))
            argument = repo_bash_instruction_target(match.group("argument"))
            if command in {"bash", "sh"} and argument in REPOSITORY_BASH_CONFINEMENT_ALLOWLIST_PATHS:
                continue
            findings.append(
                repo_bash_instruction_finding(
                    path,
                    line_number,
                    f"{category_prefix}_command",
                    f"{match.group('command')} {match.group('argument')}",
                    "active instruction requires a Bash/POSIX-sh or external jq command",
                    active_role=active_role,
                )
            )
            break
        else:
            match = REPO_BASH_ACTIONABLE_TOOL.search(line)
            if match is not None:
                findings.append(
                    repo_bash_instruction_finding(
                        path,
                        line_number,
                        f"{category_prefix}_command",
                        match.group(0),
                        "active instruction requires a Bash/POSIX-sh or external jq command",
                        active_role=active_role,
                    )
                )
    return deduplicate_raw_findings(findings)


def repo_bash_instruction_non_actionable(lines: list[str], index: int) -> bool:
    line = lines[index]
    local_context = REPO_BASH_SCRIPT_REFERENCE.sub("<script>", line)
    if (
        REPO_BASH_NON_ACTIONABLE_CONTEXT.search(local_context) is not None
        or re.search(r"\bshould\s+not\b", local_context, re.IGNORECASE) is not None
    ):
        return True

    directive = (
        REPO_BASH_EXPLICIT_DIRECTIVE.search(line) is not None
        or REPO_BASH_MODAL_DIRECTIVE.search(line) is not None
    )
    direct_command = REPO_BASH_DIRECT_COMMAND.search(line) is not None
    previous = lines[index - 1].strip() if index > 0 else ""
    if directive:
        return REPO_BASH_WRAPPED_NEGATIVE.search(previous) is not None
    if direct_command:
        if REPO_BASH_WRAPPED_NEGATIVE.search(previous) is not None:
            return True
        return (
            REPO_BASH_NON_ACTIONABLE_CONTEXT.search(previous) is not None
            and re.search(r"[.!?:;]\s*$", previous) is None
        )

    start = max(0, index - 1)
    end = min(len(lines), index + 2)
    adjacent_context = REPO_BASH_SCRIPT_REFERENCE.sub("<script>", " ".join(lines[start:end]))
    return REPO_BASH_NON_ACTIONABLE_CONTEXT.search(adjacent_context) is not None


def repo_bash_instruction_finding(
    path: str,
    line: int,
    category: str,
    pattern: str,
    reason: str,
    *,
    active_role: str,
) -> RawFinding:
    return RawFinding(
        path=path,
        line=line,
        category=category,
        pattern=pattern[:240],
        reason=reason,
        active_role=active_role,
        classification="blocking_repo_bash",
        remediation="Replace the instruction with the current Python runner or direct cross-platform command.",
    )


def repo_bash_instruction_target(raw: str) -> str:
    normalized = normalize_path(raw)
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def repo_bash_runtime_diagnostic_findings(path: str, content: str) -> list[RawFinding]:
    """Inspect only AST fields that can be emitted as operator guidance."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return [
            repo_bash_instruction_finding(
                path,
                1,
                "runtime_diagnostic_parse",
                "<syntax error>",
                "runner source could not be parsed for runtime diagnostic guidance",
                active_role="runtime_diagnostic",
            )
        ]

    findings: list[RawFinding] = []
    for scope in repo_bash_scopes(tree):
        nodes = list(repo_bash_scope_nodes(scope))
        assignments = repo_bash_runtime_assignments(tree, scope, nodes)
        expressions: list[ast.AST] = []
        for node in nodes:
            if isinstance(node, ast.keyword) and node.arg in REPO_BASH_RUNTIME_OUTPUT_KEYS:
                expressions.append(node.value)
            elif isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if isinstance(key, ast.Constant) and key.value in REPO_BASH_RUNTIME_OUTPUT_KEYS:
                        expressions.append(value)
            elif isinstance(node, ast.Call) and repo_bash_call_name(node.func) == "diagnostic" and len(node.args) >= 2:
                expressions.append(node.args[1])
            elif isinstance(node, ast.Call) and repo_bash_call_name(node.func) == "MutationEntry" and len(node.args) >= 10:
                expressions.append(node.args[9])

        for expression in expressions:
            resolution = repo_bash_guidance_resolution(
                expression,
                assignments,
                expression,
                set(),
            )
            for guidance in resolution.values:
                emitted = repo_bash_instruction_findings(
                    path,
                    guidance.value,
                    line_offset=max(0, guidance.line - 1),
                    active_role="runtime_diagnostic",
                    category_prefix="runtime_instruction",
                )
                findings.extend(emitted)
                if (
                    not guidance.complete
                    and not emitted
                    and repo_bash_dynamic_guidance_can_hide_forbidden(guidance.value)
                ):
                    findings.append(
                        repo_bash_instruction_finding(
                            path,
                            guidance.line,
                            "runtime_instruction_dynamic",
                            guidance.value,
                            "dynamic runtime guidance can hide a forbidden shell instruction",
                            active_role="runtime_diagnostic",
                        )
                    )
    return deduplicate_raw_findings(findings)


def repo_bash_runtime_assignments(
    tree: ast.AST,
    scope: ast.AST,
    scope_nodes: list[ast.AST],
) -> dict[str, list[RepoBashBindingEvent]]:
    module_assignments = repo_bash_assignment_nodes(list(repo_bash_scope_nodes(tree)))
    if scope is tree:
        return module_assignments

    local_assignments = repo_bash_assignment_nodes(scope_nodes)
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        local_names = repo_bash_shadowed_names(scope)
        merged = {
            name: list(events)
            for name, events in module_assignments.items()
            if name not in local_names
        }
    else:
        merged = {name: list(events) for name, events in module_assignments.items()}
    for name, events in local_assignments.items():
        merged.setdefault(name, []).extend(events)
        merged[name].sort(key=lambda event: (event.line, event.column))
    return merged


def repo_bash_guidance_resolution(
    node: ast.AST | None,
    assignments: dict[str, list[RepoBashBindingEvent]],
    context: ast.AST,
    resolving: set[str],
    depth: int = 0,
) -> RepoBashGuidanceResolution:
    if node is None:
        return RepoBashGuidanceResolution("collection")
    if depth >= REPO_BASH_RESOLUTION_MAX_DEPTH or len(resolving) >= REPO_BASH_RESOLUTION_MAX_DEPTH:
        return repo_bash_dynamic_guidance(node)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return repo_bash_scalar_guidance(node, node.value, complete=True)
        if node.value is None or isinstance(node.value, (bool, int, float)):
            return repo_bash_scalar_guidance(node, str(node.value), complete=True)
        return repo_bash_dynamic_guidance(node)
    if isinstance(node, ast.Name):
        if node.id in resolving:
            return repo_bash_dynamic_guidance(node)
        position = (getattr(context, "lineno", 0), getattr(context, "col_offset", 0))
        events = [
            event
            for event in assignments.get(node.id, [])
            if (event.line, event.column) <= position
        ]
        assignment_indexes = [index for index, event in enumerate(events) if event.kind == "assign"]
        if not assignment_indexes:
            return repo_bash_dynamic_guidance(node)
        assignment_index = assignment_indexes[-1]
        assignment = events[assignment_index]
        current = repo_bash_guidance_resolution(
            assignment.arguments[0],
            assignments,
            assignment.context,
            resolving | {node.id},
            depth + 1,
        )
        for event in events[assignment_index + 1 :]:
            current = repo_bash_apply_guidance_event(
                current,
                event,
                assignments,
                resolving | {node.id},
                depth + 1,
            )
        return current
    if isinstance(node, ast.NamedExpr):
        return repo_bash_guidance_resolution(
            node.value,
            assignments,
            context,
            resolving,
            depth + 1,
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return repo_bash_add_guidance(
            repo_bash_guidance_resolution(
                node.left,
                assignments,
                context,
                resolving,
                depth + 1,
            ),
            repo_bash_guidance_resolution(
                node.right,
                assignments,
                context,
                resolving,
                depth + 1,
            ),
            node,
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        template = repo_bash_guidance_resolution(
            node.left,
            assignments,
            context,
            resolving,
            depth + 1,
        )
        positional: list[RepoBashGuidanceResolution] = []
        mapping: dict[str, RepoBashGuidanceResolution] = {}
        if isinstance(node.right, ast.Tuple):
            positional = [
                repo_bash_guidance_resolution(
                    value,
                    assignments,
                    context,
                    resolving,
                    depth + 1,
                )
                for value in node.right.elts[:REPO_BASH_RESOLUTION_MAX_ITEMS]
            ]
        elif isinstance(node.right, ast.Dict):
            for key, value in zip(node.right.keys, node.right.values):
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                    return repo_bash_dynamic_guidance(node)
                mapping[key.value] = repo_bash_guidance_resolution(
                    value,
                    assignments,
                    context,
                    resolving,
                    depth + 1,
                )
        else:
            positional = [
                repo_bash_guidance_resolution(
                    node.right,
                    assignments,
                    context,
                    resolving,
                    depth + 1,
                )
            ]
        return repo_bash_percent_guidance(template, positional, mapping, node)
    if isinstance(node, ast.JoinedStr):
        current = repo_bash_scalar_guidance(node, "", complete=True)
        for value in node.values:
            if isinstance(value, ast.FormattedValue):
                part = repo_bash_guidance_resolution(
                    value.value,
                    assignments,
                    context,
                    resolving,
                    depth + 1,
                )
                if part.kind != "scalar" or len(part.values) != 1:
                    part = repo_bash_dynamic_guidance(value)
            else:
                part = repo_bash_guidance_resolution(
                    value,
                    assignments,
                    context,
                    resolving,
                    depth + 1,
                )
            current = repo_bash_add_guidance(current, part, node)
        return current
    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        values: list[RepoBashGuidanceString] = []
        for element in node.elts[:REPO_BASH_RESOLUTION_MAX_ITEMS]:
            resolved = repo_bash_guidance_resolution(
                element,
                assignments,
                context,
                resolving,
                depth + 1,
            )
            values.extend(resolved.values)
            if len(values) >= REPO_BASH_RESOLUTION_MAX_ITEMS:
                break
        return RepoBashGuidanceResolution(
            "collection",
            tuple(values[:REPO_BASH_RESOLUTION_MAX_ITEMS]),
        )
    if isinstance(node, ast.Dict):
        values: list[RepoBashGuidanceString] = []
        for value in node.values[:REPO_BASH_RESOLUTION_MAX_ITEMS]:
            resolved = repo_bash_guidance_resolution(
                value,
                assignments,
                context,
                resolving,
                depth + 1,
            )
            values.extend(resolved.values)
            if len(values) >= REPO_BASH_RESOLUTION_MAX_ITEMS:
                break
        return RepoBashGuidanceResolution(
            "collection",
            tuple(values[:REPO_BASH_RESOLUTION_MAX_ITEMS]),
        )
    if isinstance(node, (ast.IfExp, ast.BoolOp)):
        branches = (
            [node.body, node.orelse]
            if isinstance(node, ast.IfExp)
            else list(node.values[:REPO_BASH_RESOLUTION_MAX_ITEMS])
        )
        values: list[RepoBashGuidanceString] = []
        for branch in branches:
            values.extend(
                repo_bash_guidance_resolution(
                    branch,
                    assignments,
                    context,
                    resolving,
                    depth + 1,
                ).values
            )
        return RepoBashGuidanceResolution(
            "collection",
            tuple(values[:REPO_BASH_RESOLUTION_MAX_ITEMS]),
        )
    if isinstance(node, ast.Call):
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "format"
            and not any(keyword.arg is None for keyword in node.keywords)
        ):
            template = repo_bash_guidance_resolution(
                node.func.value,
                assignments,
                context,
                resolving,
                depth + 1,
            )
            positional = [
                repo_bash_guidance_resolution(
                    argument,
                    assignments,
                    context,
                    resolving,
                    depth + 1,
                )
                for argument in node.args[:REPO_BASH_RESOLUTION_MAX_ITEMS]
            ]
            keywords = {
                keyword.arg: repo_bash_guidance_resolution(
                    keyword.value,
                    assignments,
                    context,
                    resolving,
                    depth + 1,
                )
                for keyword in node.keywords[:REPO_BASH_RESOLUTION_MAX_ITEMS]
                if keyword.arg is not None
            }
            return repo_bash_format_guidance(template, positional, keywords, node)
        if isinstance(node.func, ast.Name) and node.func.id == "str" and len(node.args) == 1:
            return repo_bash_guidance_resolution(
                node.args[0],
                assignments,
                context,
                resolving,
                depth + 1,
            )
    return repo_bash_dynamic_guidance(node)


def repo_bash_apply_guidance_event(
    current: RepoBashGuidanceResolution,
    event: RepoBashBindingEvent,
    assignments: dict[str, list[RepoBashBindingEvent]],
    resolving: set[str],
    depth: int,
) -> RepoBashGuidanceResolution:
    def resolve(node: ast.AST) -> RepoBashGuidanceResolution:
        return repo_bash_guidance_resolution(
            node,
            assignments,
            event.context,
            resolving,
            depth + 1,
        )

    if event.kind == "augadd" and len(event.arguments) == 1:
        return repo_bash_add_guidance(current, resolve(event.arguments[0]), event.context)
    if event.kind in {"append", "extend"} and len(event.arguments) == 1:
        if current.kind != "collection":
            return repo_bash_dynamic_guidance(event.context)
        added = resolve(event.arguments[0])
        return RepoBashGuidanceResolution(
            "collection",
            (*current.values, *added.values)[:REPO_BASH_RESOLUTION_MAX_ITEMS],
        )
    if event.kind == "insert" and len(event.arguments) == 2:
        if current.kind != "collection":
            return repo_bash_dynamic_guidance(event.context)
        index = repo_bash_static_integer(event.arguments[0])
        added = resolve(event.arguments[1])
        if index is None:
            return repo_bash_dynamic_guidance(event.context)
        values = list(current.values)
        normalized_index = max(0, min(index if index >= 0 else len(values) + index, len(values)))
        values[normalized_index:normalized_index] = added.values
        return RepoBashGuidanceResolution(
            "collection",
            tuple(values[:REPO_BASH_RESOLUTION_MAX_ITEMS]),
        )
    return repo_bash_dynamic_guidance(event.context)


def repo_bash_guidance_item(
    resolution: RepoBashGuidanceResolution,
    node: ast.AST,
) -> RepoBashGuidanceString:
    if resolution.kind == "scalar" and len(resolution.values) == 1:
        return resolution.values[0]
    return RepoBashGuidanceString(
        line=getattr(node, "lineno", 1),
        value="<dynamic>",
        complete=False,
    )


def repo_bash_format_guidance(
    template: RepoBashGuidanceResolution,
    positional: list[RepoBashGuidanceResolution],
    keywords: dict[str, RepoBashGuidanceResolution],
    node: ast.AST,
) -> RepoBashGuidanceResolution:
    template_item = repo_bash_guidance_item(template, node)
    output: list[str] = []
    complete = template_item.complete
    automatic_index = 0
    try:
        fields = list(string.Formatter().parse(template_item.value))
    except ValueError:
        return repo_bash_dynamic_guidance(node)
    for literal, field_name, format_spec, conversion in fields:
        output.append(literal)
        if field_name is None:
            continue
        if field_name == "":
            index = automatic_index
            automatic_index += 1
            resolution = positional[index] if index < len(positional) else repo_bash_dynamic_guidance(node)
        elif field_name.isdecimal():
            index = int(field_name)
            resolution = positional[index] if index < len(positional) else repo_bash_dynamic_guidance(node)
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", field_name):
            resolution = keywords.get(field_name, repo_bash_dynamic_guidance(node))
        else:
            resolution = repo_bash_dynamic_guidance(node)
        item = repo_bash_guidance_item(resolution, node)
        output.append(item.value)
        complete = complete and item.complete and not format_spec and conversion is None
    return repo_bash_scalar_guidance(node, "".join(output), complete=complete)


def repo_bash_percent_guidance(
    template: RepoBashGuidanceResolution,
    positional: list[RepoBashGuidanceResolution],
    mapping: dict[str, RepoBashGuidanceResolution],
    node: ast.AST,
) -> RepoBashGuidanceResolution:
    template_item = repo_bash_guidance_item(template, node)
    field_pattern = re.compile(
        r"%(?:\((?P<key>[^)]+)\))?[#0\- +]*(?:\d+|\*)?(?:\.(?:\d+|\*))?"
        r"[hlL]?(?P<conversion>[diouxXeEfFgGcrsa%])"
    )
    output: list[str] = []
    complete = template_item.complete
    cursor = 0
    positional_index = 0
    for match in field_pattern.finditer(template_item.value):
        literal = template_item.value[cursor : match.start()]
        if "%" in literal:
            return repo_bash_dynamic_guidance(node)
        output.append(literal)
        cursor = match.end()
        if match.group("conversion") == "%":
            output.append("%")
            continue
        key = match.group("key")
        if key is not None:
            resolution = mapping.get(key, repo_bash_dynamic_guidance(node))
        else:
            resolution = (
                positional[positional_index]
                if positional_index < len(positional)
                else repo_bash_dynamic_guidance(node)
            )
            positional_index += 1
        item = repo_bash_guidance_item(resolution, node)
        output.append(item.value)
        complete = complete and item.complete and "*" not in match.group(0)
    tail = template_item.value[cursor:]
    if "%" in tail:
        return repo_bash_dynamic_guidance(node)
    output.append(tail)
    if cursor == 0:
        return repo_bash_dynamic_guidance(node)
    return repo_bash_scalar_guidance(node, "".join(output), complete=complete)


def repo_bash_scalar_guidance(
    node: ast.AST,
    value: str,
    *,
    complete: bool,
) -> RepoBashGuidanceResolution:
    if len(value) > REPO_BASH_RESOLUTION_MAX_STRING:
        value = value[: REPO_BASH_RESOLUTION_MAX_STRING - len("<dynamic>")] + "<dynamic>"
        complete = False
    return RepoBashGuidanceResolution(
        "scalar",
        (
            RepoBashGuidanceString(
                line=getattr(node, "lineno", 1),
                value=value,
                complete=complete,
            ),
        ),
    )


def repo_bash_dynamic_guidance(node: ast.AST) -> RepoBashGuidanceResolution:
    return repo_bash_scalar_guidance(node, "<dynamic>", complete=False)


def repo_bash_add_guidance(
    left: RepoBashGuidanceResolution,
    right: RepoBashGuidanceResolution,
    node: ast.AST,
) -> RepoBashGuidanceResolution:
    if left.kind == "collection" and right.kind == "collection":
        return RepoBashGuidanceResolution(
            "collection",
            (*left.values, *right.values)[:REPO_BASH_RESOLUTION_MAX_ITEMS],
        )
    if left.kind != "scalar" or right.kind != "scalar" or len(left.values) != 1 or len(right.values) != 1:
        return repo_bash_dynamic_guidance(node)
    left_value = left.values[0]
    right_value = right.values[0]
    return repo_bash_scalar_guidance(
        node,
        left_value.value + right_value.value,
        complete=left_value.complete and right_value.complete,
    )


def repo_bash_dynamic_guidance_can_hide_forbidden(value: str) -> bool:
    if "<dynamic>" not in value:
        return False
    static_context = value.replace("<dynamic>", "")
    if REPO_BASH_NON_ACTIONABLE_CONTEXT.search(static_context) is not None:
        return False
    directive = REPO_BASH_EXPLICIT_DIRECTIVE.search(value)
    if directive is not None and value.find("<dynamic>", directive.end()) >= 0:
        return True
    if re.search(
        r"^\s*<dynamic>\s+(?:--?[A-Za-z0-9]|(?:bash|jq|sh)(?:\.exe)?\b|[^\s]+\.(?:sh|bash)\b)",
        value,
        re.IGNORECASE,
    ):
        return True
    return re.search(
        r"<dynamic>[^.!?\n]{0,80}(?:(?:bash|jq|sh)(?:\.exe)?\b|[^\s]+\.(?:sh|bash)\b)",
        value,
        re.IGNORECASE,
    ) is not None


def deduplicate_raw_findings(findings: list[RawFinding]) -> list[RawFinding]:
    records: dict[tuple[str, int | None, str, str], RawFinding] = {}
    for finding in findings:
        records[(finding.path, finding.line, finding.category, finding.pattern)] = finding
    return list(records.values())


def repo_bash_workflow_findings(
    path: str,
    content: str,
    tracked_paths: set[str],
    *,
    repo_root: Path | None = None,
) -> list[RawFinding]:
    """Inspect executable workflow run values without scanning YAML prose."""
    findings: list[RawFinding] = []
    for start, _end, context in workflow_run_contexts(content):
        value = repo_bash_workflow_run_value(context)
        if value is None:
            findings.append(
                repo_bash_workflow_finding(
                    path,
                    start,
                    "workflow_dispatch",
                    context,
                    "workflow run value could not be parsed",
                )
            )
            continue

        shell = repo_bash_workflow_shell(content, start)
        if shell == "python":
            dispatch_path = repo_bash_python_shell_dispatch_path(value)
            dispatch_failure = (
                repo_bash_workflow_dispatch_path_failure(
                    dispatch_path,
                    tracked_paths,
                    repo_root=repo_root,
                )
                if dispatch_path is not None
                else "workflow shell: python value must directly dispatch one Python file"
            )
            if dispatch_failure is None:
                continue
            findings.append(
                repo_bash_workflow_finding(
                    path,
                    start,
                    "workflow_dispatch",
                    value,
                    dispatch_failure,
                )
            )
            continue
        if shell not in {None, "bash"}:
            findings.append(
                repo_bash_workflow_finding(
                    path,
                    start,
                    "workflow_dispatch",
                    value,
                    f"workflow run value uses unsupported shell {shell}",
                )
            )
            continue

        failure = repo_bash_workflow_run_failure(
            value,
            tracked_paths,
            repo_root=repo_root,
        )
        if failure is None:
            continue
        category, reason = failure
        findings.append(repo_bash_workflow_finding(path, start, category, value, reason))
    return findings


def repo_bash_workflow_run_value(context: str) -> str | None:
    lines = context.splitlines()
    if not lines:
        return None
    first = lines[0].strip()
    match = re.fullmatch(r"(?:-\s+)?run:\s*(.*)", first)
    if match is None:
        return None
    scalar = match.group(1).strip()
    if not re.fullmatch(r"[|>][+-]?", scalar):
        return scalar or None
    body = lines[1:]
    nonempty = [line for line in body if line.strip()]
    if not nonempty:
        return ""
    indent = min(len(line) - len(line.lstrip(" ")) for line in nonempty)
    return "\n".join(line[indent:] if line.strip() else "" for line in body).strip()


def repo_bash_workflow_shell(content: str, run_line: int) -> str | None:
    lines = content.splitlines()
    index = run_line - 1
    if index < 0 or index >= len(lines):
        return None
    run_indent = len(lines[index]) - len(lines[index].lstrip(" "))
    step_start = index if lines[index].lstrip(" ").startswith("- ") else 0
    if step_start != index:
        for candidate in range(index - 1, -1, -1):
            line = lines[candidate]
            stripped = line.lstrip(" ")
            indent = len(line) - len(stripped)
            if stripped.startswith("- ") and indent < run_indent:
                step_start = candidate
                break
    step_line = lines[step_start]
    step_indent = len(step_line) - len(step_line.lstrip(" "))
    step_end = len(lines)
    for candidate in range(step_start + 1, len(lines)):
        line = lines[candidate]
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        if stripped.startswith("- ") and indent <= step_indent:
            step_end = candidate
            break
    for line_number, line in enumerate(lines[step_start:step_end], start=step_start):
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        if line_number != step_start and indent != step_indent + 2:
            continue
        match = re.match(r"^\s*(?:-\s+)?shell:\s*([^\s#]+)", line)
        if match is not None:
            return match.group(1).strip('"\'').lower()
    return None


def repo_bash_python_shell_dispatch_path(value: str) -> str | None:
    try:
        tree = ast.parse(value)
    except SyntaxError:
        return None
    if len(tree.body) != 2 or not isinstance(tree.body[0], ast.Import) or not isinstance(tree.body[1], ast.Expr):
        return None
    imported = tree.body[0].names
    if len(imported) != 1 or imported[0].name != "runpy" or imported[0].asname is not None:
        return None
    call = tree.body[1].value
    if (
        not isinstance(call, ast.Call)
        or not isinstance(call.func, ast.Attribute)
        or not isinstance(call.func.value, ast.Name)
        or call.func.value.id != "runpy"
        or call.func.attr != "run_path"
        or len(call.args) != 1
        or len(call.keywords) != 1
        or call.keywords[0].arg != "run_name"
    ):
        return None
    target = call.args[0]
    run_name = call.keywords[0].value
    if (
        not isinstance(target, ast.Constant)
        or not isinstance(target.value, str)
        or not isinstance(run_name, ast.Constant)
        or run_name.value != "__main__"
        or invalid_scan_root_reason(target.value) is not None
        or Path(target.value).suffix.lower() != ".py"
    ):
        return None
    return normalize_path(target.value)


def repo_bash_workflow_dispatch_path_failure(
    raw_path: str,
    tracked_paths: set[str],
    *,
    repo_root: Path | None = None,
) -> str | None:
    if invalid_scan_root_reason(raw_path) is not None:
        return "workflow Python dispatch target must be repository-relative and confined"
    if REPO_BASH_WORKFLOW_DYNAMIC_PATH.search(raw_path) is not None:
        return "workflow Python dispatch target must not use shell expansion or glob syntax"
    path = normalize_path(raw_path)
    if Path(path).suffix.lower() != ".py":
        return "workflow Python dispatch target must be a Python file"
    if path not in tracked_paths:
        return "workflow Python dispatch target must be tracked"
    if repo_root is not None and repo_bash_content_path(repo_root, path) is None:
        return "workflow Python dispatch target must resolve to a file inside the repository"
    return None


def repo_bash_workflow_run_failure(
    value: str,
    tracked_paths: set[str],
    *,
    repo_root: Path | None = None,
) -> tuple[str, str] | None:
    executable_lines = [
        line.strip()
        for line in value.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    command = "\n".join(executable_lines)
    if not command:
        return "workflow_dispatch", "workflow run value has no direct command"
    active_text, has_substitution = repo_bash_active_shell_text(command)
    if "<<" in active_text:
        return "workflow_heredoc", "workflow run value uses a heredoc"
    if has_substitution:
        return "workflow_shell_logic", "workflow run value uses command substitution"
    if len(executable_lines) != 1:
        return "workflow_shell_logic", "workflow run value contains more than one direct command"

    if re.fullmatch(
        r"echo\s+(?:'[^'\r\n]*'|\"[^\"\r\n]*\")\s*>>\s*\"\$(?:GITHUB_OUTPUT|GITHUB_STEP_SUMMARY)\"",
        command,
    ):
        return None

    if re.search(
        r"(?i)(?:^|\s)(?:set\s+-|if\b|then\b|elif\b|else\b|fi\b|for\b|while\b|until\b|"
        r"case\b|esac\b|select\b|function\b|do\b|done\b)",
        active_text,
    ) or re.search(
        r"&&|\|\||(?<!\|)\|(?!\|)|(?<!&)&(?!&)|;|[(){}]|>",
        active_text,
    ):
        return "workflow_shell_logic", "workflow run value contains shell control logic"

    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()<>{}")
        lexer.whitespace_split = True
        lexer.commenters = ""
        argv = list(lexer)
    except ValueError:
        return "workflow_dispatch", "workflow run value is not a parseable direct command"
    while argv and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", argv[0]):
        argv.pop(0)
    if not argv:
        return "workflow_dispatch", "workflow run value has no executable"

    redirected_input: str | None = None
    input_redirects = list(re.finditer(r"(?<!<)<(?!<)", active_text))
    if input_redirects:
        if len(input_redirects) != 1 or len(argv) < 3 or argv[-2] != "<":
            return "workflow_shell_logic", "workflow input redirection must be one trailing tracked JSON path"
        redirected_input = normalize_path(argv[-1])
        argv = argv[:-2]

    if repo_bash_workflow_argv_contains_forbidden(argv):
        return "workflow_forbidden_command", "workflow run value invokes bash, jq, or a Bash-family script"

    executable = executable_basename(argv[0])
    if executable in {"python", "python3"}:
        runner_dispatch = len(argv) >= 3 and argv[1:3] == ["-m", "speckit_pro_runner"]
        script_dispatch = len(argv) >= 2 and not argv[1].startswith("-")
        if not runner_dispatch and not script_dispatch:
            return "workflow_dispatch", "workflow Python command must dispatch a script or speckit_pro_runner"
        if script_dispatch:
            dispatch_failure = repo_bash_workflow_dispatch_path_failure(
                argv[1],
                tracked_paths,
                repo_root=repo_root,
            )
            if dispatch_failure is not None:
                return "workflow_dispatch", dispatch_failure
        if redirected_input is None:
            return None
        if (
            not runner_dispatch
            or invalid_scan_root_reason(redirected_input) is not None
            or Path(redirected_input).suffix.lower() != ".json"
            or redirected_input not in tracked_paths
        ):
            return "workflow_untracked_input", "workflow runner input redirection must reference tracked JSON"
        return None

    if redirected_input is not None:
        return "workflow_shell_logic", "workflow input redirection is limited to the Python runner"
    if executable in {"pnpm", "corepack"}:
        return None
    if executable == "actionlint" or normalize_path(argv[0]).endswith("/actionlint"):
        return None
    return "workflow_dispatch", "workflow run value is not an approved direct Python, pnpm, corepack, or actionlint dispatch"


def repo_bash_active_shell_text(command: str) -> tuple[str, bool]:
    """Mask quoted and escaped literals while retaining active shell syntax."""
    characters = list(command)
    active = list(command)
    quote: str | None = None
    has_substitution = False
    index = 0
    while index < len(characters):
        character = characters[index]
        if quote == "'":
            active[index] = " "
            if character == "'":
                quote = None
            index += 1
            continue
        if quote == '"':
            active[index] = " "
            if character == "\\" and index + 1 < len(characters):
                active[index + 1] = " "
                index += 2
                continue
            if character == '"':
                quote = None
            elif character == "`" or (
                character == "$" and index + 1 < len(characters) and characters[index + 1] == "("
            ):
                has_substitution = True
            index += 1
            continue
        if character == "\\" and index + 1 < len(characters):
            active[index] = " "
            active[index + 1] = " "
            index += 2
            continue
        if character in {"'", '"'}:
            quote = character
            active[index] = " "
        elif character == "`" or (
            character == "$" and index + 1 < len(characters) and characters[index + 1] == "("
        ):
            has_substitution = True
        index += 1
    return "".join(active), has_substitution


def repo_bash_workflow_argv_contains_forbidden(argv: list[str]) -> bool:
    if not argv:
        return False
    executable = executable_basename(argv[0])
    if executable in REPO_BASH_COMMAND_NAMES or executable in {"sh", "sh.exe"}:
        return True
    if Path(normalize_path(argv[0])).suffix.lower() in REPO_BASH_SCRIPT_SUFFIXES:
        return True
    if repo_bash_argv_contains_forbidden(list(argv)):
        return True
    if executable == "env":
        return any(
            repo_bash_workflow_argv_contains_forbidden(delegated)
            for delegated in env_delegated_argvs(argv)
        )
    if executable in {"command", "exec"}:
        return repo_bash_workflow_argv_contains_forbidden(argv[1:])
    return False


def repo_bash_workflow_finding(
    path: str,
    line: int,
    category: str,
    pattern: str,
    reason: str,
) -> RawFinding:
    return RawFinding(
        path=path,
        line=line,
        category=category,
        pattern=pattern.strip().replace("\n", " ")[:120],
        reason=reason,
        active_role="workflow_run_value",
        classification="blocking_repo_bash",
        remediation="Replace the run value with one approved direct dispatch or exact GitHub output append.",
    )


def repo_bash_python_findings(path: str, content: str) -> list[RawFinding]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    aliases = python_shell_aliases(tree)
    imported_which_aliases = repo_bash_which_aliases(tree)
    imported_sys_aliases = repo_bash_sys_aliases(tree)
    wrappers = repo_bash_subprocess_wrappers(tree, aliases)
    module_shell_events = repo_bash_shell_binding_events(tree)
    module_shell_bindings = repo_bash_apply_shell_binding_events(
        {"os": "os_modules", "subprocess": "subprocess_modules"},
        module_shell_events,
    )
    findings: list[RawFinding] = []
    for scope in repo_bash_scopes(tree):
        nodes = list(repo_bash_scope_nodes(scope))
        assignments = repo_bash_assignment_nodes(nodes)
        local_shell_events = module_shell_events if scope is tree else repo_bash_shell_binding_events(scope)
        shadowed = repo_bash_shadowed_names(scope)
        which_aliases = tuple(aliases - shadowed for aliases in imported_which_aliases)
        sys_aliases = tuple(aliases - shadowed for aliases in imported_sys_aliases)
        for node in nodes:
            if not isinstance(node, ast.Call):
                continue
            call_aliases = repo_bash_effective_shell_aliases(
                tree,
                scope,
                node,
                module_shell_events,
                module_shell_bindings,
                local_shell_events,
            )
            category: str | None = None
            args_node: ast.AST | None = None
            direct_subprocess = False
            if is_os_system_call(node.func, call_aliases):
                category = "os_system"
                args_node = subprocess_args_node(node)
            elif is_shell_backed_subprocess_call(node.func, call_aliases) or is_subprocess_call(node.func, call_aliases):
                direct_subprocess = is_subprocess_call(node.func, call_aliases)
                category = "shell_true" if call_has_shell_enabled(node) else "command_argv_subprocess"
                args_node = subprocess_args_node(node)
            else:
                wrapper = repo_bash_call_name(node.func)
                parameter_index = wrappers.get(wrapper) if wrapper else None
                if parameter_index is not None and len(node.args) > parameter_index:
                    category = "command_argv_subprocess"
                    args_node = node.args[parameter_index]
            if category is None or args_node is None:
                continue

            pattern: str | None
            if direct_subprocess:
                executable_node = repo_bash_subprocess_executable_node(node)
                if executable_node is not None:
                    executable = repo_bash_static_resolution(
                        executable_node,
                        assignments,
                        node,
                        which_aliases,
                        sys_aliases,
                        set(),
                    )
                    if executable.kind != "none":
                        pattern = repo_bash_executable_override_pattern(executable)
                        if pattern is None:
                            continue
                    else:
                        pattern = None
                else:
                    pattern = None
            else:
                pattern = None

            if pattern is None:
                value = repo_bash_static_resolution(
                    args_node,
                    assignments,
                    node,
                    which_aliases,
                    sys_aliases,
                    set(),
                )
                pattern = repo_bash_subprocess_resolution_pattern(value, fail_closed=category != "os_system")
            if pattern is None:
                continue
            unresolved = "<dynamic" in pattern
            findings.append(
                repo_bash_raw_finding(
                    path,
                    getattr(node, "lineno", None),
                    category,
                    pattern,
                    (
                        "Python subprocess executable cannot be statically resolved Bash-free"
                        if unresolved
                        else "Python execution path invokes bash or jq"
                    ),
                )
            )
    return findings


def repo_bash_scopes(tree: ast.AST) -> list[ast.AST]:
    return [
        tree,
        *[
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))
        ],
    ]


def repo_bash_scope_nodes(scope: ast.AST):
    stack = [scope]
    while stack:
        node = stack.pop()
        yield node
        children = list(ast.iter_child_nodes(node))
        for child in reversed(children):
            if child is not scope and isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            stack.append(child)


def repo_bash_shell_binding_events(scope: ast.AST) -> list[RepoBashShellBindingEvent]:
    events: list[RepoBashShellBindingEvent] = []
    nodes = list(repo_bash_scope_nodes(scope))
    node_set = set(nodes)
    parents = {
        child: parent
        for parent in nodes
        for child in ast.iter_child_nodes(parent)
        if child in node_set
    }

    def dominates(node: ast.AST) -> bool:
        current = node
        while current is not scope:
            parent = parents.get(current)
            if parent is None:
                break
            if isinstance(parent, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.Match)):
                return False
            current = parent
        return True

    def add(name: str, category: str | None, node: ast.AST) -> None:
        events.append(
            RepoBashShellBindingEvent(
                name=name,
                category=category,
                line=getattr(node, "lineno", 0),
                column=getattr(node, "col_offset", 0),
                dominates=dominates(node),
            )
        )

    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                module = alias.name.split(".", 1)[0]
                category = (
                    "os_modules"
                    if module == "os"
                    else "subprocess_modules"
                    if module == "subprocess"
                    else None
                )
                add(bound, category, node)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                bound = alias.asname or alias.name
                category = None
                if node.module == "os" and alias.name in OS_SHELL_FUNCTION_NAMES:
                    category = "os_system_functions"
                elif node.module == "subprocess" and alias.name in SUBPROCESS_ARGV_FUNCTION_NAMES:
                    category = "subprocess_functions"
                elif node.module == "subprocess" and alias.name in SUBPROCESS_SHELL_FUNCTION_NAMES:
                    category = "subprocess_shell_functions"
                add(bound, category, node)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            add(node.id, None, node)

        for child in ast.iter_child_nodes(node):
            if child is not scope and isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                add(child.name, None, child)

    events.sort(key=lambda event: (event.line, event.column))
    return events


def repo_bash_apply_shell_binding_events(
    initial: dict[str, str],
    events: list[RepoBashShellBindingEvent],
    position: tuple[int, int] | None = None,
) -> dict[str, str]:
    bindings = dict(initial)
    for event in events:
        if position is not None and (event.line, event.column) > position:
            break
        if event.category is None:
            if not event.dominates:
                continue
            bindings.pop(event.name, None)
        else:
            bindings[event.name] = event.category
    return bindings


def repo_bash_effective_shell_aliases(
    tree: ast.AST,
    scope: ast.AST,
    context: ast.AST,
    module_events: list[RepoBashShellBindingEvent],
    module_bindings: dict[str, str],
    local_events: list[RepoBashShellBindingEvent],
) -> dict[str, set[str]]:
    position = (getattr(context, "lineno", 0), getattr(context, "col_offset", 0))
    if scope is tree:
        bindings = repo_bash_apply_shell_binding_events(
            {"os": "os_modules", "subprocess": "subprocess_modules"},
            module_events,
            position,
        )
    elif isinstance(scope, ast.ClassDef):
        class_position = (getattr(scope, "lineno", 0), getattr(scope, "col_offset", 0))
        bindings = repo_bash_apply_shell_binding_events(
            {"os": "os_modules", "subprocess": "subprocess_modules"},
            module_events,
            class_position,
        )
        bindings = repo_bash_apply_shell_binding_events(bindings, local_events, position)
    else:
        bindings = dict(module_bindings)
        local_names = {event.name for event in local_events}
        if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            local_names.update(
                argument.arg
                for argument in [*scope.args.posonlyargs, *scope.args.args, *scope.args.kwonlyargs]
            )
            if scope.args.vararg is not None:
                local_names.add(scope.args.vararg.arg)
            if scope.args.kwarg is not None:
                local_names.add(scope.args.kwarg.arg)
        for name in local_names:
            bindings.pop(name, None)
        bindings = repo_bash_apply_shell_binding_events(bindings, local_events, position)

    aliases = {
        "os_modules": set[str](),
        "os_system_functions": set[str](),
        "subprocess_modules": set[str](),
        "subprocess_functions": set[str](),
        "subprocess_shell_functions": set[str](),
    }
    for name, category in bindings.items():
        aliases[category].add(name)
    return aliases


def repo_bash_assignment_nodes(nodes: list[ast.AST]) -> dict[str, list[RepoBashBindingEvent]]:
    assignments: dict[str, list[RepoBashBindingEvent]] = {}

    def add_event(name: str, kind: str, context: ast.AST, *arguments: ast.AST) -> None:
        assignments.setdefault(name, []).append(
            RepoBashBindingEvent(
                kind=kind,
                line=getattr(context, "lineno", 0),
                column=getattr(context, "col_offset", 0),
                context=context,
                arguments=tuple(arguments),
            )
        )

    for node in nodes:
        targets: list[ast.expr] = []
        value: ast.AST | None = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        if value is not None:
            for target in targets:
                if isinstance(target, ast.Name):
                    add_event(target.id, "assign", node, value)
                elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                    add_event(target.value.id, "setitem", node, target.slice, value)
        if isinstance(node, ast.AugAssign):
            kind = "augadd" if isinstance(node.op, ast.Add) else "unknown"
            if isinstance(node.target, ast.Name):
                add_event(node.target.id, kind, node, node.value)
            elif isinstance(node.target, ast.Subscript) and isinstance(node.target.value, ast.Name):
                subscript_kind = "setitem_augadd" if isinstance(node.op, ast.Add) else "unknown"
                add_event(node.target.value.id, subscript_kind, node, node.target.slice, node.value)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.attr in {"append", "clear", "extend", "insert", "pop", "remove", "reverse", "sort"}
        ):
            kind = node.func.attr if not node.keywords else "unknown"
            add_event(node.func.value.id, kind, node, *node.args)
    for events in assignments.values():
        events.sort(key=lambda event: (event.line, event.column))
    return assignments


def repo_bash_static_resolution(
    node: ast.AST,
    assignments: dict[str, list[RepoBashBindingEvent]],
    context: ast.AST,
    which_aliases: tuple[set[str], set[str]],
    sys_aliases: tuple[set[str], set[str]],
    resolving: set[str],
    depth: int = 0,
) -> RepoBashStaticResolution:
    if depth >= REPO_BASH_RESOLUTION_MAX_DEPTH or len(resolving) >= REPO_BASH_RESOLUTION_MAX_DEPTH:
        return REPO_BASH_UNKNOWN_RESOLUTION

    literal = static_string_literal(node)
    if literal is not None:
        if len(literal) > REPO_BASH_RESOLUTION_MAX_STRING:
            return REPO_BASH_UNKNOWN_RESOLUTION
        return RepoBashStaticResolution("scalar", scalar=literal)
    if isinstance(node, ast.Constant) and node.value is None:
        return REPO_BASH_NONE_RESOLUTION
    if (
        isinstance(node, ast.Attribute)
        and node.attr == "executable"
        and isinstance(node.value, ast.Name)
        and node.value.id in sys_aliases[0]
    ):
        return RepoBashStaticResolution("scalar", scalar="python")
    if isinstance(node, ast.NamedExpr):
        return repo_bash_static_resolution(
            node.value,
            assignments,
            context,
            which_aliases,
            sys_aliases,
            resolving,
            depth + 1,
        )
    if isinstance(node, ast.Starred):
        return repo_bash_static_resolution(
            node.value,
            assignments,
            context,
            which_aliases,
            sys_aliases,
            resolving,
            depth + 1,
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = repo_bash_static_resolution(
            node.left,
            assignments,
            context,
            which_aliases,
            sys_aliases,
            resolving,
            depth + 1,
        )
        right = repo_bash_static_resolution(
            node.right,
            assignments,
            context,
            which_aliases,
            sys_aliases,
            resolving,
            depth + 1,
        )
        return repo_bash_add_resolutions(left, right)
    if isinstance(node, (ast.List, ast.Tuple)):
        values: list[str | None] = []
        for element in node.elts:
            if len(values) >= REPO_BASH_RESOLUTION_MAX_ITEMS:
                values[-1:] = [None]
                break
            value = repo_bash_static_resolution(
                element.value if isinstance(element, ast.Starred) else element,
                assignments,
                context,
                which_aliases,
                sys_aliases,
                resolving,
                depth + 1,
            )
            if isinstance(element, ast.Starred):
                if value.kind == "argv":
                    values.extend(value.argv)
                elif value.kind == "scalar" and value.scalar is not None:
                    values.extend(value.scalar)
                else:
                    values.append(None)
            else:
                values.append(value.scalar if value.kind == "scalar" else None)
            values = list(repo_bash_bounded_argv(values))
        return RepoBashStaticResolution("argv", argv=tuple(values))
    if isinstance(node, ast.Name):
        if node.id in resolving:
            return REPO_BASH_UNKNOWN_RESOLUTION
        return repo_bash_name_resolution(
            node.id,
            assignments,
            context,
            which_aliases,
            sys_aliases,
            resolving | {node.id},
            depth + 1,
        )
    if isinstance(node, ast.Call):
        if repo_bash_command_source_call(node.func, which_aliases) and node.args:
            value = repo_bash_static_resolution(
                node.args[0],
                assignments,
                context,
                which_aliases,
                sys_aliases,
                resolving,
                depth + 1,
            )
            if value.kind == "scalar" and value.scalar is not None:
                if (
                    repo_bash_trusted_which_call(node.func, which_aliases)
                    or executable_basename(value.scalar) in REPO_BASH_COMMAND_NAMES
                ):
                    return value
            return REPO_BASH_UNKNOWN_RESOLUTION
        if isinstance(node.func, ast.Name) and node.func.id in {"list", "tuple"} and len(node.args) == 1:
            value = repo_bash_static_resolution(
                node.args[0],
                assignments,
                context,
                which_aliases,
                sys_aliases,
                resolving,
                depth + 1,
            )
            if value.kind == "argv":
                return value
            if value.kind == "scalar" and value.scalar is not None:
                return RepoBashStaticResolution("argv", argv=repo_bash_bounded_argv(value.scalar))
        if isinstance(node.func, ast.Name) and node.func.id == "str" and len(node.args) == 1:
            value = repo_bash_static_resolution(
                node.args[0],
                assignments,
                context,
                which_aliases,
                sys_aliases,
                resolving,
                depth + 1,
            )
            if value.kind == "scalar":
                return value
        return REPO_BASH_UNKNOWN_RESOLUTION
    if isinstance(node, ast.Subscript):
        value = repo_bash_static_resolution(
            node.value,
            assignments,
            context,
            which_aliases,
            sys_aliases,
            resolving,
            depth + 1,
        )
        index = node.slice.value if isinstance(node.slice, ast.Constant) else None
        if value.kind == "argv" and isinstance(index, int) and -len(value.argv) <= index < len(value.argv):
            item = value.argv[index]
            return RepoBashStaticResolution("scalar", scalar=item) if item is not None else REPO_BASH_UNKNOWN_RESOLUTION
        return REPO_BASH_UNKNOWN_RESOLUTION
    if isinstance(node, ast.IfExp):
        return repo_bash_merge_alternative_resolutions(
            [
                repo_bash_static_resolution(
                    branch,
                    assignments,
                    context,
                    which_aliases,
                    sys_aliases,
                    resolving,
                    depth + 1,
                )
                for branch in (node.body, node.orelse)
            ]
        )
    if isinstance(node, ast.BoolOp):
        return repo_bash_merge_alternative_resolutions(
            [
                repo_bash_static_resolution(
                    value,
                    assignments,
                    context,
                    which_aliases,
                    sys_aliases,
                    resolving,
                    depth + 1,
                )
                for value in node.values[:REPO_BASH_RESOLUTION_MAX_ITEMS]
            ]
        )
    return REPO_BASH_UNKNOWN_RESOLUTION


def repo_bash_name_resolution(
    name: str,
    assignments: dict[str, list[RepoBashBindingEvent]],
    context: ast.AST,
    which_aliases: tuple[set[str], set[str]],
    sys_aliases: tuple[set[str], set[str]],
    resolving: set[str],
    depth: int,
) -> RepoBashStaticResolution:
    position = (getattr(context, "lineno", 0), getattr(context, "col_offset", 0))
    events = [event for event in assignments.get(name, []) if (event.line, event.column) <= position]
    assignment_indexes = [index for index, event in enumerate(events) if event.kind == "assign"]
    if not assignment_indexes:
        if name in sys_aliases[1]:
            return RepoBashStaticResolution("scalar", scalar="python")
        return REPO_BASH_UNKNOWN_RESOLUTION

    assignment_index = assignment_indexes[-1]
    assignment = events[assignment_index]
    current = repo_bash_static_resolution(
        assignment.arguments[0],
        assignments,
        assignment.context,
        which_aliases,
        sys_aliases,
        resolving,
        depth + 1,
    )
    for event in events[assignment_index + 1 :]:
        current = repo_bash_apply_binding_event(
            current,
            event,
            assignments,
            which_aliases,
            sys_aliases,
            resolving,
            depth + 1,
        )
    return current


def repo_bash_apply_binding_event(
    current: RepoBashStaticResolution,
    event: RepoBashBindingEvent,
    assignments: dict[str, list[RepoBashBindingEvent]],
    which_aliases: tuple[set[str], set[str]],
    sys_aliases: tuple[set[str], set[str]],
    resolving: set[str],
    depth: int,
) -> RepoBashStaticResolution:
    def resolve(node: ast.AST) -> RepoBashStaticResolution:
        return repo_bash_static_resolution(
            node,
            assignments,
            event.context,
            which_aliases,
            sys_aliases,
            resolving,
            depth + 1,
        )

    if event.kind == "augadd" and len(event.arguments) == 1:
        return repo_bash_add_resolutions(current, resolve(event.arguments[0]))
    if event.kind in {"setitem", "setitem_augadd"} and len(event.arguments) == 2:
        if current.kind != "argv":
            return REPO_BASH_UNKNOWN_RESOLUTION
        index = repo_bash_static_integer(event.arguments[0])
        values = list(current.argv)
        if index is None or not -len(values) <= index < len(values):
            return REPO_BASH_UNKNOWN_RESOLUTION
        normalized_index = index % len(values)
        replacement = resolve(event.arguments[1])
        if event.kind == "setitem_augadd":
            existing = values[normalized_index]
            left = (
                RepoBashStaticResolution("scalar", scalar=existing)
                if existing is not None
                else REPO_BASH_UNKNOWN_RESOLUTION
            )
            replacement = repo_bash_add_resolutions(left, replacement)
        values[normalized_index] = replacement.scalar if replacement.kind == "scalar" else None
        return RepoBashStaticResolution("argv", argv=repo_bash_bounded_argv(values))
    if current.kind != "argv":
        return REPO_BASH_UNKNOWN_RESOLUTION

    values = list(current.argv)
    if event.kind == "append" and len(event.arguments) == 1:
        item = resolve(event.arguments[0])
        values.append(item.scalar if item.kind == "scalar" else None)
    elif event.kind == "extend" and len(event.arguments) == 1:
        extension = resolve(event.arguments[0])
        if extension.kind == "argv":
            values.extend(extension.argv)
        elif extension.kind == "scalar" and extension.scalar is not None:
            values.extend(extension.scalar)
        else:
            values.append(None)
    elif event.kind == "insert" and len(event.arguments) == 2:
        index = repo_bash_static_integer(event.arguments[0])
        if index is None:
            return REPO_BASH_UNKNOWN_RESOLUTION
        item = resolve(event.arguments[1])
        values.insert(index, item.scalar if item.kind == "scalar" else None)
    elif event.kind == "clear" and not event.arguments:
        values.clear()
    elif event.kind == "pop" and len(event.arguments) <= 1:
        index = -1 if not event.arguments else repo_bash_static_integer(event.arguments[0])
        if index is None or not -len(values) <= index < len(values):
            return REPO_BASH_UNKNOWN_RESOLUTION
        values.pop(index)
    elif event.kind == "remove" and len(event.arguments) == 1:
        item = resolve(event.arguments[0])
        if item.kind != "scalar" or item.scalar not in values:
            return REPO_BASH_UNKNOWN_RESOLUTION
        values.remove(item.scalar)
    elif event.kind == "reverse" and not event.arguments:
        values.reverse()
    elif event.kind == "sort" and not event.arguments and None not in values:
        values.sort()
    else:
        return REPO_BASH_UNKNOWN_RESOLUTION
    return RepoBashStaticResolution("argv", argv=repo_bash_bounded_argv(values))


def repo_bash_static_integer(node: ast.AST) -> int | None:
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, (ast.UAdd, ast.USub))
        and isinstance(node.operand, ast.Constant)
        and type(node.operand.value) is int
    ):
        return node.operand.value if isinstance(node.op, ast.UAdd) else -node.operand.value
    return None


def repo_bash_add_resolutions(
    left: RepoBashStaticResolution,
    right: RepoBashStaticResolution,
) -> RepoBashStaticResolution:
    if left.kind == "scalar" and right.kind == "scalar":
        value = (left.scalar or "") + (right.scalar or "")
        if len(value) <= REPO_BASH_RESOLUTION_MAX_STRING:
            return RepoBashStaticResolution("scalar", scalar=value)
        return REPO_BASH_UNKNOWN_RESOLUTION
    if left.kind == "argv" and right.kind == "argv":
        return RepoBashStaticResolution("argv", argv=repo_bash_bounded_argv((*left.argv, *right.argv)))
    if left.kind == "argv" and right.kind == "unknown":
        return RepoBashStaticResolution("argv", argv=repo_bash_bounded_argv((*left.argv, None)))
    if left.kind == "unknown" and right.kind == "argv":
        return RepoBashStaticResolution("argv", argv=repo_bash_bounded_argv((None, *right.argv)))
    return REPO_BASH_UNKNOWN_RESOLUTION


def repo_bash_bounded_argv(values: Any) -> tuple[str | None, ...]:
    argv = tuple(values)
    if len(argv) <= REPO_BASH_RESOLUTION_MAX_ITEMS:
        return argv
    return (*argv[: REPO_BASH_RESOLUTION_MAX_ITEMS - 1], None)


def repo_bash_merge_alternative_resolutions(
    resolutions: list[RepoBashStaticResolution],
) -> RepoBashStaticResolution:
    if not resolutions:
        return REPO_BASH_UNKNOWN_RESOLUTION
    for resolution in resolutions:
        if resolution.kind == "scalar" and resolution.scalar is not None:
            if repo_bash_command_text_contains_forbidden(resolution.scalar):
                return resolution
        elif resolution.kind == "argv" and None not in resolution.argv:
            if repo_bash_argv_contains_forbidden(list(resolution.argv)):
                return resolution
    if all(resolution == resolutions[0] for resolution in resolutions[1:]):
        return resolutions[0]
    if all(resolution.kind == "scalar" for resolution in resolutions):
        return resolutions[0]
    if all(resolution.kind == "argv" and None not in resolution.argv for resolution in resolutions):
        return resolutions[0]
    return REPO_BASH_UNKNOWN_RESOLUTION


def repo_bash_subprocess_executable_node(node: ast.Call) -> ast.AST | None:
    for keyword in node.keywords:
        if keyword.arg == "executable":
            return keyword.value
    return None


def repo_bash_executable_override_pattern(resolution: RepoBashStaticResolution) -> str | None:
    if resolution.kind == "unknown":
        return "<dynamic executable>"
    if resolution.kind != "scalar" or resolution.scalar is None:
        return None
    if executable_basename(resolution.scalar) in REPO_BASH_COMMAND_NAMES:
        return f"executable={resolution.scalar}"[:120]
    return None


def repo_bash_subprocess_resolution_pattern(
    resolution: RepoBashStaticResolution,
    *,
    fail_closed: bool,
) -> str | None:
    if resolution.kind == "unknown":
        return "<dynamic executable>" if fail_closed else None
    if resolution.kind == "scalar" and resolution.scalar is not None:
        if repo_bash_command_text_contains_forbidden(resolution.scalar):
            return resolution.scalar[:120]
        return None
    if resolution.kind == "argv" and repo_bash_argv_contains_forbidden(list(resolution.argv)):
        return " ".join(item if item is not None else "<dynamic>" for item in resolution.argv)[:120]
    return None


def repo_bash_which_aliases(tree: ast.AST) -> tuple[set[str], set[str]]:
    modules: set[str] = set()
    functions: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "shutil":
                    modules.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "shutil":
            for alias in node.names:
                if alias.name == "which":
                    functions.add(alias.asname or alias.name)
    imports = repo_bash_import_bindings(tree)
    modules = {name for name in modules if imports.get(name) == [("shutil", None)]}
    functions = {name for name in functions if imports.get(name) == [("shutil", "which")]}
    return modules, functions


def repo_bash_sys_aliases(tree: ast.AST) -> tuple[set[str], set[str]]:
    modules: set[str] = set()
    executables: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "sys":
                    modules.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "sys":
            for alias in node.names:
                if alias.name == "executable":
                    executables.add(alias.asname or alias.name)
    imports = repo_bash_import_bindings(tree)
    modules = {name for name in modules if imports.get(name) == [("sys", None)]}
    executables = {name for name in executables if imports.get(name) == [("sys", "executable")]}
    return modules, executables


def repo_bash_import_bindings(tree: ast.AST) -> dict[str, list[tuple[str | None, str | None]]]:
    """Return every import binding per local name in source order.

    A trusted sys/shutil alias is safe only when it has exactly one import
    binding. Any competing import remains fail-closed instead of inheriting
    trust from an earlier binding.
    """
    bindings: dict[str, list[tuple[str | None, str | None]]] = {}
    nodes = sorted(
        (node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))),
        key=lambda node: (getattr(node, "lineno", 0), getattr(node, "col_offset", 0)),
    )
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.split(".", 1)[0]
                bindings.setdefault(local_name, []).append((alias.name, None))
        else:
            for alias in node.names:
                if alias.name == "*":
                    continue
                local_name = alias.asname or alias.name
                bindings.setdefault(local_name, []).append((node.module, alias.name))
    return bindings


def repo_bash_shadowed_names(scope: ast.AST) -> set[str]:
    nodes = list(repo_bash_scope_nodes(scope))
    names = {
        node.id
        for node in nodes
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        names.update(argument.arg for argument in [*scope.args.posonlyargs, *scope.args.args, *scope.args.kwonlyargs])
        if scope.args.vararg is not None:
            names.add(scope.args.vararg.arg)
        if scope.args.kwarg is not None:
            names.add(scope.args.kwarg.arg)
    for node in nodes:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(child.name)
    return names


def repo_bash_command_source_call(func: ast.expr, which_aliases: tuple[set[str], set[str]]) -> bool:
    modules, functions = which_aliases
    if isinstance(func, ast.Name):
        return func.id in functions or func.id == "cmd_path"
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "which"
        and isinstance(func.value, ast.Name)
        and func.value.id in modules
    )


def repo_bash_trusted_which_call(func: ast.expr, which_aliases: tuple[set[str], set[str]]) -> bool:
    modules, functions = which_aliases
    if isinstance(func, ast.Name):
        return func.id in functions
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "which"
        and isinstance(func.value, ast.Name)
        and func.value.id in modules
    )


def repo_bash_subprocess_wrappers(tree: ast.AST, aliases: dict[str, set[str]]) -> dict[str, int]:
    wrappers: dict[str, int] = {}
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        parameter_names = [argument.arg for argument in function.args.args]
        for node in repo_bash_scope_nodes(function):
            if not isinstance(node, ast.Call):
                continue
            if not (
                is_subprocess_call(node.func, aliases)
                or is_shell_backed_subprocess_call(node.func, aliases)
                or is_os_system_call(node.func, aliases)
            ):
                continue
            args_node = subprocess_args_node(node)
            if isinstance(args_node, ast.Name) and args_node.id in parameter_names:
                wrappers[function.name] = parameter_names.index(args_node.id)
                break
    return wrappers


def repo_bash_call_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    return None


def repo_bash_argv_contains_forbidden(argv: list[str | None]) -> bool:
    if not argv:
        return False
    if argv[0] is None:
        return True
    executable = executable_basename(argv[0])
    if executable in REPO_BASH_COMMAND_NAMES:
        return True
    if executable == "env":
        return repo_bash_env_argv_contains_forbidden(argv)
    if executable in {"command", "exec"}:
        return repo_bash_argv_contains_forbidden(argv[1:])
    if executable in {"sh", "sh.exe", "zsh", "zsh.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe"}:
        for index, item in enumerate(argv[1:], start=1):
            if item is not None and shell_command_payload_flag(item):
                if index + 1 >= len(argv) or argv[index + 1] is None:
                    return True
                return repo_bash_command_text_contains_forbidden(argv[index + 1])
    if executable in {"cmd", "cmd.exe"}:
        for index, item in enumerate(argv[1:], start=1):
            if item is not None and item.lower() in {"/c", "/k"}:
                payload = argv[index + 1 :]
                if not payload or any(part is None for part in payload):
                    return True
                return repo_bash_command_text_contains_forbidden(" ".join(part for part in payload if part is not None))
    return False


def repo_bash_env_argv_contains_forbidden(argv: list[str | None]) -> bool:
    index = 1
    while index < len(argv):
        item = argv[index]
        if item is None:
            return True
        if item in {"-S", "--split-string"}:
            if index + 1 >= len(argv) or argv[index + 1] is None:
                return True
            return any(repo_bash_argv_contains_forbidden(delegated) for delegated in env_split_string_argvs(argv[index + 1]))
        if item.startswith("-S") and item != "-S":
            return any(repo_bash_argv_contains_forbidden(delegated) for delegated in env_split_string_argvs(item[2:].strip()))
        if item.startswith("--split-string="):
            return any(
                repo_bash_argv_contains_forbidden(delegated)
                for delegated in env_split_string_argvs(item.split("=", 1)[1])
            )
        if item in {"-u", "--unset", "-C", "--chdir"}:
            index += 2
            continue
        if item.startswith("--unset=") or item.startswith("--chdir="):
            index += 1
            continue
        if item.startswith("-") or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", item):
            index += 1
            continue
        return repo_bash_argv_contains_forbidden(argv[index:])
    return False


def repo_bash_command_text_contains_forbidden(command: str) -> bool:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()
    segment: list[str] = []
    for token in [*tokens, ";"]:
        if token in {";", "&&", "||", "|", "&", "(", ")"}:
            if repo_bash_command_segment_contains_forbidden(segment):
                return True
            segment = []
        else:
            segment.append(token)
    return False


def repo_bash_command_segment_contains_forbidden(segment: list[str]) -> bool:
    index = 0
    while index < len(segment) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", segment[index]):
        index += 1
    while index < len(segment) and executable_basename(segment[index]) in {"env", "command", "exec"}:
        command = executable_basename(segment[index])
        index += 1
        while index < len(segment) and (
            segment[index].startswith("-")
            or (command == "env" and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", segment[index]))
        ):
            index += 1
    return index < len(segment) and repo_bash_argv_contains_forbidden(segment[index:])


def repo_bash_json_findings(path: str, content: str) -> list[RawFinding]:
    try:
        document = json.loads(content)
    except json.JSONDecodeError:
        return []
    named_values: list[tuple[str, Any]] = []
    name = Path(path).name.lower()
    if name == "hooks.json":
        named_values.extend(repo_bash_hook_command_values(document))
        category = "hooks_json_command"
    elif name == "package.json":
        scripts = document.get("scripts") if isinstance(document, dict) else None
        if isinstance(scripts, dict):
            named_values.extend((str(key), value) for key, value in scripts.items())
        category = "package_json_script"
    else:
        return []
    findings: list[RawFinding] = []
    for key, value in named_values:
        if not repo_bash_json_command_contains_forbidden(value):
            continue
        findings.append(
            repo_bash_raw_finding(
                path,
                None,
                category,
                f"{key}: {value}"[:120],
                "structural JSON command invokes bash or jq",
            )
        )
    return findings


def repo_bash_hook_command_values(value: Any) -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "command":
                found.append((key, child))
            else:
                found.extend(repo_bash_hook_command_values(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(repo_bash_hook_command_values(child))
    return found


def repo_bash_json_command_contains_forbidden(value: Any) -> bool:
    if isinstance(value, str):
        return repo_bash_command_text_contains_forbidden(value)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return repo_bash_argv_contains_forbidden(list(value))
    return False


def zero_bash_source_findings(sources: list[SourceFile], allowlist: list[dict[str, Any]]) -> list[RawFinding]:
    findings: list[RawFinding] = []
    seen: set[tuple[str, int | None, str, str]] = set()
    for source in sources:
        path = normalize_path(source.path)
        if has_prohibited_script_suffix(path):
            finding = RawFinding(
                path=path,
                line=1,
                category="script_file",
                pattern=Path(path).suffix,
                reason="script file retained in in-scope plugin, payload, or cache surface",
                active_role=zero_bash_active_role(path),
                classification=zero_bash_classification(path, "script_file", Path(path).suffix, source.content, allowlist),
                remediation=zero_bash_remediation(path),
            )
            add_finding(findings, seen, finding)
            continue
        if not zero_bash_text_scan_path(path):
            continue
        if has_prohibited_script_shebang_content(source.content):
            first_line = source.content.splitlines()[0] if source.content.splitlines() else "#!"
            finding = RawFinding(
                path=path,
                line=1,
                category="script_file",
                pattern=first_line[:120],
                reason="shell script shebang retained in in-scope plugin, payload, or cache surface",
                active_role=zero_bash_active_role(path),
                classification=zero_bash_classification(path, "script_file", first_line, source.content, allowlist),
                remediation=zero_bash_remediation(path),
            )
            add_finding(findings, seen, finding)
            continue
        if Path(path).suffix.lower() == ".py":
            for finding in python_shell_execution_findings(path, source.content, allowlist):
                add_finding(findings, seen, finding)
            continue
        lines = source.content.splitlines()
        for category, pattern, reason in FORBIDDEN_CONTENT_PATTERNS:
            if not zero_bash_scans_category(path, category):
                continue
            for match in pattern.finditer(source.content):
                line_number = line_number_for_offset(source.content, match.start())
                context = line_context(lines, line_number)
                finding = RawFinding(
                    path=path,
                    line=line_number,
                    category=category,
                    pattern=match.group(0)[:120],
                    reason=reason,
                    active_role=zero_bash_active_role(path),
                    classification=zero_bash_classification(
                        path,
                        category,
                        match.group(0),
                        context,
                        allowlist,
                        declaration_line=match.group(0),
                    ),
                    remediation=zero_bash_remediation(path),
                )
                add_finding(findings, seen, finding)
        for number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or (stripped.startswith("#") and not stripped.startswith("#!") and not path.endswith(".md")):
                continue
            for category, pattern, reason in FORBIDDEN_PATTERNS:
                if not zero_bash_scans_category(path, category):
                    continue
                match = pattern.search(line)
                if match is None:
                    continue
                context = line_context(lines, number)
                finding = RawFinding(
                    path=path,
                    line=number,
                    category=category,
                    pattern=match.group(0)[:120],
                    reason=reason,
                    active_role=zero_bash_active_role(path),
                    classification=zero_bash_classification(
                        path,
                        category,
                        match.group(0),
                        context,
                        allowlist,
                        declaration_line=line,
                    ),
                    remediation=zero_bash_remediation(path),
                )
                add_finding(findings, seen, finding)
    return findings


def zero_bash_classification(
    path: str,
    category: str,
    pattern: str,
    content: str,
    allowlist: list[dict[str, Any]],
    *,
    declaration_line: str | None = None,
) -> str:
    if zero_bash_allowlisted(path, category, allowlist):
        return "historical_allowlist"
    if category in HARD_RUNTIME_CATEGORIES and not zero_bash_historical_path(path):
        return "blocking_zero_bash"
    line_text = declaration_line or content
    if category != "script_file" and zero_bash_active_guidance(line_text):
        return "blocking_zero_bash"
    if category != "script_file" and installed_runtime_agent_tool_declaration(path, line_text):
        return "blocking_zero_bash" if zero_bash_active_tool_declaration(line_text) else "tool_declaration"
    if category != "script_file" and zero_bash_negative_policy_exception(content):
        return "negative_policy"
    if zero_bash_historical_path(path):
        return "historical_allowlist"
    return "blocking_zero_bash"


def zero_bash_negative_policy_exception(content: str) -> bool:
    lowered = content.lower()
    clauses = [clause.strip() for clause in re.split(r"[.!?;\n]+", lowered) if clause.strip()]
    if any(zero_bash_active_shell_invocation(clause) and not zero_bash_negative_policy_clause(clause) for clause in clauses):
        return False
    return any(zero_bash_negative_policy_clause(clause) for clause in clauses)


def zero_bash_active_tool_declaration(content: str) -> bool:
    for line in content.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if not lowered:
            continue
        restricted = re.match(r"^(?:disallowedtools:|disallowed-tools:|denied-tools:|forbidden-tools:)\s*(?P<value>.+)$", lowered)
        if restricted is not None:
            if zero_bash_shell_marker_present(restricted.group("value")):
                return True
            continue
        declaration = re.match(r"^(?:allowed-tools:|tools\s*=|tools:)\s*(?P<value>.+)$", lowered)
        if declaration is not None and zero_bash_shell_marker_present(declaration.group("value")):
            return True
        if re.match(r"^-\s*(?:bash|sh|zsh|powershell|pwsh|jq)\b", lowered):
            return True
    return False


def zero_bash_negative_policy_clause(clause: str) -> bool:
    if not zero_bash_shell_marker_present(clause):
        return False
    if zero_bash_clause_has_contrast_active_invocation(clause):
        return False
    if re.search(r"\b(?:do not|don't|must not|never)\s+skip\b", clause):
        return False
    if re.search(r"\b(?:do not|don't|must not|never)\s+run\b.*\b(?:without|unless|until)\b", clause):
        return False
    if re.search(r"\b(?:do not|don't|must not|never)\s+(?:use|require|depend(?:\s+on)?|execute|invoke|call|install|add)\b", clause):
        return True
    if re.search(r"\b(?:deny|denies|denied|disallow|disallowed|forbid|forbidden|prohibit|prohibited)\b", clause):
        return True
    if re.search(r"\b(?:do not|don't|must not|never)\s+run\s+", clause) and zero_bash_direct_shell_command_after_run(clause):
        return True
    if zero_bash_active_shell_invocation(clause):
        return False
    if re.search(
        r"\b(?:not\s+(?:require|use|depend)|no live|without\s+(?:requiring|using|depending)|avoid\s+(?:requiring|using|depending)|forbidden|refuse|instead of|rather than)\b",
        clause,
    ):
        return True
    if any(marker in clause for marker in ("zero-bash", "bash-free", "shell-free")) and not zero_bash_active_shell_invocation(clause):
        return True
    return False


def zero_bash_clause_has_contrast_active_invocation(clause: str) -> bool:
    segments = re.split(r"\b(?:but|however|nevertheless|then)\b|;", clause)
    if len(segments) < 2:
        return False
    return any(zero_bash_active_shell_invocation(segment.strip()) for segment in segments[1:])


def zero_bash_direct_shell_command_after_run(clause: str) -> bool:
    match = re.search(r"\brun\s+(?P<target>[^\s`\"']+)", clause)
    if match is None:
        return False
    return zero_bash_shell_command_token(match.group("target"))


def zero_bash_active_shell_invocation(clause: str) -> bool:
    return bool(
        re.search(
            r"\b(?:run|use|execute|invoke|call|require|install)\s+(?:\$[{]?shell[}]?|bash(?:\.exe)?(?!-)|jq(?:\.exe)?(?!-)|wsl(?:\.exe)?(?!-)|powershell(?:\.exe)?(?!-)|pwsh(?:\.exe)?(?!-)|[^\s`\"']+\.(?:sh|ps1|bat|cmd))\b",
            clause,
        )
    )


def zero_bash_shell_command_token(token: str) -> bool:
    normalized = executable_basename(token)
    if normalized in PROHIBITED_COMMAND_NAMES:
        return True
    return has_prohibited_script_suffix(token)


def zero_bash_active_guidance(content: str) -> bool:
    lowered = content.lower()
    for clause in re.split(r"[.!?;\n,]+", lowered):
        normalized = clause.strip()
        if not normalized or not zero_bash_shell_marker_present(normalized):
            continue
        if zero_bash_negative_policy_exception(normalized):
            continue
        if re.search(r"\b(?:run|use|execute|invoke|call|require|install)\b", normalized):
            return True
    return False


def zero_bash_shell_marker_present(lowered: str) -> bool:
    if "$(" in lowered or "$shell" in lowered or "${shell}" in lowered or any(command in lowered.split() for command in PROHIBITED_COMMAND_NAMES):
        return True
    if any(suffix in lowered for suffix in PROHIBITED_SCRIPT_SUFFIXES):
        return True
    return any(marker in lowered for marker in ("git bash", "wsl", "powershell", "pwsh", "jq", "bash"))


def zero_bash_text_scan_path(path: str) -> bool:
    path = normalize_path(path)
    if zero_bash_historical_path(path) or path.endswith("CHANGELOG.md"):
        return False
    if path.startswith("tests/"):
        return False
    if path.startswith(("speckit-pro/", "dist/claude/speckit-pro/", "dist/codex/speckit-pro/")):
        return Path(path).suffix.lower() in TEXT_SUFFIXES or zero_bash_extensionless_scan_path(path)
    if path.startswith(("dist/claude/speckit-pro/agents/", "dist/codex/speckit-pro/codex-agents/")):
        return True
    if path.startswith(("speckit-pro/hooks/", "dist/claude/speckit-pro/hooks/")):
        return True
    return path in {
        "speckit-pro/codex-hooks.json",
        "dist/codex/speckit-pro/codex-hooks.json",
        "speckit-pro/README.md",
        "dist/claude/speckit-pro/README.md",
        "dist/codex/speckit-pro/README.md",
        "README.md",
    }


def zero_bash_scans_category(path: str, category: str) -> bool:
    if Path(path).suffix.lower() == ".py":
        return category in {"os_system", "shell_true", "command_string_subprocess", "command_argv_subprocess"}
    if any(part in path for part in ("/references/", "/templates/", "/contracts/")):
        return True
    return True


def python_shell_execution_findings(path: str, content: str, allowlist: list[dict[str, Any]]) -> list[RawFinding]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    aliases = python_shell_aliases(tree)
    command_assignments = python_static_command_assignments(tree)
    bool_assignments = python_static_bool_assignments(tree)
    partial_command_assignments = python_partial_command_assignments(tree, command_assignments)
    findings: list[RawFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        category = ""
        reason = ""
        pattern = ""
        if is_os_system_call(node.func, aliases):
            category = "os_system"
            reason = "os shell execution"
            pattern = os_shell_call_pattern(node.func)
        elif is_shell_backed_subprocess_call(node.func, aliases):
            category = "command_string_subprocess"
            reason = "shell-backed subprocess execution"
            pattern = subprocess_call_pattern(node.func)
        elif is_subprocess_call(node.func, aliases):
            if call_has_shell_enabled(node, bool_assignments):
                category = "shell_true"
                reason = "shell=True subprocess execution"
                pattern = shell_keyword_pattern(node, bool_assignments)
            elif call_has_command_string(node, command_assignments):
                category = "command_string_subprocess"
                reason = "command-string subprocess execution"
                pattern = "subprocess command string"
            else:
                argv_pattern = command_argv_subprocess_pattern(node, command_assignments, partial_command_assignments)
                if argv_pattern is not None:
                    category = "command_argv_subprocess"
                    reason = "argv subprocess invokes shell-specific command"
                    pattern = argv_pattern
        if not category:
            continue
        line_no = getattr(node, "lineno", None)
        findings.append(
            RawFinding(
                path=path,
                line=line_no if isinstance(line_no, int) else None,
                category=category,
                pattern=pattern,
                reason=reason,
                active_role=zero_bash_active_role(path),
                classification=zero_bash_python_classification(path, category, allowlist),
                remediation=zero_bash_remediation(path),
            )
        )
    return findings


def python_static_command_assignments(tree: ast.AST) -> dict[str, list[StaticAssignment]]:
    assignments: dict[str, list[StaticAssignment]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = static_command_value(node.value)
            if value is None:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(
                        StaticAssignment(value=value, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0))
                    )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            value = static_command_value(node.value)
            if value is not None:
                assignments.setdefault(node.target.id, []).append(
                    StaticAssignment(value=value, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0))
                )
    return assignments


def python_static_bool_assignments(tree: ast.AST) -> dict[str, list[StaticAssignment]]:
    assignments: dict[str, list[StaticAssignment]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = static_bool_value(node.value)
            if value is None:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(
                        StaticAssignment(value=value, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0))
                    )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            value = static_bool_value(node.value)
            if value is not None:
                assignments.setdefault(node.target.id, []).append(
                    StaticAssignment(value=value, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0))
                )
    return assignments


def python_partial_command_assignments(
    tree: ast.AST,
    static_assignments: dict[str, list[StaticAssignment]],
) -> dict[str, list[PartialStaticAssignment]]:
    assignments: dict[str, list[PartialStaticAssignment]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = partial_static_string_argv(node.value, static_assignments, node)
            if value is None:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(
                        PartialStaticAssignment(value=value, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0))
                    )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            value = partial_static_string_argv(node.value, static_assignments, node)
            if value is not None:
                assignments.setdefault(node.target.id, []).append(
                    PartialStaticAssignment(value=value, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0))
                )
    return assignments


def python_shell_aliases(tree: ast.AST) -> dict[str, set[str]]:
    aliases = {
        "os_modules": {"os"},
        "os_system_functions": set[str](),
        "subprocess_modules": {"subprocess"},
        "subprocess_functions": set[str](),
        "subprocess_shell_functions": set[str](),
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name
                if alias.name == "os":
                    aliases["os_modules"].add(bound)
                elif alias.name == "subprocess":
                    aliases["subprocess_modules"].add(bound)
        elif isinstance(node, ast.ImportFrom):
            if node.module == "os":
                for alias in node.names:
                    if alias.name in OS_SHELL_FUNCTION_NAMES:
                        aliases["os_system_functions"].add(alias.asname or alias.name)
            elif node.module == "subprocess":
                for alias in node.names:
                    if alias.name in SUBPROCESS_ARGV_FUNCTION_NAMES:
                        aliases["subprocess_functions"].add(alias.asname or alias.name)
                    elif alias.name in SUBPROCESS_SHELL_FUNCTION_NAMES:
                        aliases["subprocess_shell_functions"].add(alias.asname or alias.name)
    return aliases


def is_os_system_call(func: ast.expr, aliases: dict[str, set[str]]) -> bool:
    if isinstance(func, ast.Attribute) and func.attr in OS_SHELL_FUNCTION_NAMES and isinstance(func.value, ast.Name):
        return func.value.id in aliases["os_modules"]
    return isinstance(func, ast.Name) and func.id in aliases["os_system_functions"]


def os_shell_call_pattern(func: ast.expr) -> str:
    if isinstance(func, ast.Attribute):
        return f"os.{func.attr}("
    if isinstance(func, ast.Name):
        return f"{func.id}("
    return "os shell execution"


def is_shell_backed_subprocess_call(func: ast.expr, aliases: dict[str, set[str]]) -> bool:
    if isinstance(func, ast.Attribute) and func.attr in SUBPROCESS_SHELL_FUNCTION_NAMES and isinstance(func.value, ast.Name):
        return func.value.id in aliases["subprocess_modules"]
    return isinstance(func, ast.Name) and func.id in aliases["subprocess_shell_functions"]


def subprocess_call_pattern(func: ast.expr) -> str:
    if isinstance(func, ast.Attribute):
        return f"subprocess.{func.attr}("
    if isinstance(func, ast.Name):
        return f"{func.id}("
    return "subprocess shell execution"


def is_subprocess_call(func: ast.expr, aliases: dict[str, set[str]]) -> bool:
    if isinstance(func, ast.Attribute) and func.attr in SUBPROCESS_ARGV_FUNCTION_NAMES and isinstance(func.value, ast.Name):
        return func.value.id in aliases["subprocess_modules"]
    return isinstance(func, ast.Name) and func.id in aliases["subprocess_functions"]


def call_has_shell_enabled(node: ast.Call, assignments: dict[str, list[StaticAssignment]] | None = None) -> bool:
    for keyword in node.keywords:
        if keyword.arg != "shell":
            continue
        if shell_keyword_is_statically_false(keyword.value, assignments or {}, node):
            return False
        return True
    return False


def shell_keyword_pattern(node: ast.Call, assignments: dict[str, list[StaticAssignment]] | None = None) -> str:
    for keyword in node.keywords:
        if keyword.arg != "shell":
            continue
        if isinstance(keyword.value, ast.Name):
            assignment = latest_static_assignment(keyword.value.id, assignments or {}, node)
            if assignment is not None:
                return f"shell={keyword.value.id} ({assignment.value})"
            return f"shell={keyword.value.id}"
        if isinstance(keyword.value, ast.Constant):
            return f"shell={keyword.value.value!r}"
        return "shell=<dynamic>"
    return "shell=True"


def shell_keyword_is_statically_false(
    value: ast.AST,
    assignments: dict[str, list[StaticAssignment]],
    node: ast.AST,
) -> bool:
    bool_value = static_bool_value(value)
    if bool_value is False:
        return True
    if not isinstance(value, ast.Name):
        return False
    assignment = latest_static_assignment(value.id, assignments, node)
    return assignment is not None and assignment.value is False


def static_bool_value(node: ast.AST | None) -> bool | None:
    if isinstance(node, ast.Constant):
        if node.value is True:
            return True
        if node.value is False or node.value == 0:
            return False
    return None


def call_has_command_string(node: ast.Call, assignments: dict[str, list[StaticAssignment]] | None = None) -> bool:
    return isinstance(static_subprocess_arg_value(node, assignments or {}), str)


def command_argv_subprocess_pattern(
    node: ast.Call,
    assignments: dict[str, list[StaticAssignment]] | None = None,
    partial_assignments: dict[str, list[PartialStaticAssignment]] | None = None,
) -> str | None:
    args_node = subprocess_args_node(node)
    if isinstance(args_node, ast.Name):
        prior_pattern = prior_forbidden_argv_assignment_pattern(
            args_node.id,
            assignments or {},
            partial_assignments or {},
            node,
        )
        if prior_pattern is not None:
            return prior_pattern
    value = static_subprocess_arg_value(node, assignments or {})
    if not isinstance(value, list):
        partial_argv = partial_static_subprocess_argv(node, partial_assignments or {}, assignments or {})
        if partial_argv is None or not partial_command_argv_contains_forbidden(partial_argv):
            return None
        return " ".join(item if item is not None else "<dynamic>" for item in partial_argv)[:120]
    argv = value
    if command_argv_contains_forbidden(argv):
        return " ".join(argv)[:120]
    if executable_basename(argv[0]) == "env":
        for delegated_argv in env_delegated_argvs(argv):
            if command_argv_contains_forbidden(delegated_argv):
                return " ".join(argv)[:120]
    return None


def prior_forbidden_argv_assignment_pattern(
    name: str,
    assignments: dict[str, list[StaticAssignment]],
    partial_assignments: dict[str, list[PartialStaticAssignment]],
    node: ast.AST,
) -> str | None:
    call_position = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
    for assignment in assignments.get(name, []):
        if (assignment.line, assignment.column) > call_position or not isinstance(assignment.value, list):
            continue
        if command_argv_contains_forbidden(assignment.value):
            return " ".join(assignment.value)[:120]
    for assignment in partial_assignments.get(name, []):
        if (assignment.line, assignment.column) > call_position:
            continue
        if partial_command_argv_contains_forbidden(assignment.value):
            return " ".join(item if item is not None else "<dynamic>" for item in assignment.value)[:120]
    return None


def static_subprocess_arg_value(node: ast.Call, assignments: dict[str, list[StaticAssignment]]) -> list[str] | str | None:
    args_node = subprocess_args_node(node)
    if isinstance(args_node, ast.Name):
        assignment = latest_static_assignment(args_node.id, assignments, node)
        return assignment.value if assignment is not None else None
    return static_command_value(args_node)


def partial_static_subprocess_argv(
    node: ast.Call,
    assignments: dict[str, list[PartialStaticAssignment]],
    static_assignments: dict[str, list[StaticAssignment]],
) -> list[str | None] | None:
    args_node = subprocess_args_node(node)
    if isinstance(args_node, ast.Name):
        assignment = latest_partial_static_assignment(args_node.id, assignments, node)
        return assignment.value if assignment is not None else None
    return partial_static_string_argv(args_node, static_assignments, node)


def latest_partial_static_assignment(
    name: str,
    assignments: dict[str, list[PartialStaticAssignment]],
    node: ast.AST,
) -> PartialStaticAssignment | None:
    call_position = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
    candidates = [
        assignment
        for assignment in assignments.get(name, [])
        if (assignment.line, assignment.column) <= call_position
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda assignment: (assignment.line, assignment.column))


def latest_static_assignment(name: str, assignments: dict[str, list[StaticAssignment]], node: ast.AST) -> StaticAssignment | None:
    call_position = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
    candidates = [
        assignment
        for assignment in assignments.get(name, [])
        if (assignment.line, assignment.column) <= call_position
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda assignment: (assignment.line, assignment.column))


def subprocess_args_node(node: ast.Call) -> ast.AST | None:
    if node.args:
        return node.args[0]
    for keyword in node.keywords:
        if keyword.arg == "args":
            return keyword.value
    return None


def command_argv_contains_forbidden(argv: list[str], *, depth: int = 0) -> bool:
    if not argv:
        return False
    if executable_basename(argv[0]) in PROHIBITED_COMMAND_NAMES | SHELL_RUNTIME_COMMAND_NAMES:
        return True
    if any(has_prohibited_script_suffix(item) for item in argv):
        return True
    if shell_c_payload_has_forbidden_command(argv):
        return True
    if executable_basename(argv[0]) == "env" and depth < 4:
        for delegated_argv in env_delegated_argvs(argv):
            if command_argv_contains_forbidden(delegated_argv, depth=depth + 1):
                return True
    joined = " ".join(item.lower() for item in argv)
    if "git bash" in joined:
        return True
    return False


def partial_command_argv_contains_forbidden(argv: list[str | None], *, depth: int = 0) -> bool:
    if not argv:
        return False
    executable = argv[0]
    if executable is not None and executable_basename(executable) in PROHIBITED_COMMAND_NAMES | SHELL_RUNTIME_COMMAND_NAMES:
        return True
    if any(item is not None and has_prohibited_script_suffix(item) for item in argv):
        return True
    if executable is not None and executable_basename(executable) in SHELL_COMMAND_NAMES:
        return any(item is not None and shell_command_payload_flag(item) for item in argv[1:])
    if executable is not None and executable_basename(executable) == "env" and depth < 4:
        return partial_env_delegation_contains_forbidden(argv, depth=depth)
    return False


def static_command_value(node: ast.AST | None) -> list[str] | str | None:
    argv = static_string_argv(node)
    if argv is not None:
        return argv
    return static_command_string(node)


def static_string_argv(node: ast.AST | None) -> list[str] | None:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return None
    argv: list[str] = []
    for element in node.elts:
        value = static_string_literal(element)
        if value is None:
            return None
        argv.append(value)
    return argv or None


def partial_static_string_argv(
    node: ast.AST | None,
    assignments: dict[str, list[StaticAssignment]] | None = None,
    context_node: ast.AST | None = None,
) -> list[str | None] | None:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return None
    argv = [partial_static_string_value(element, assignments or {}, context_node or node) for element in node.elts]
    return argv if any(item is not None for item in argv) else None


def partial_static_string_value(
    node: ast.AST,
    assignments: dict[str, list[StaticAssignment]],
    context_node: ast.AST,
) -> str | None:
    value = static_string_literal(node)
    if value is not None:
        return value
    if not isinstance(node, ast.Name):
        return None
    candidates = [
        assignment
        for assignment in assignments.get(node.id, [])
        if isinstance(assignment.value, str)
        and (assignment.line, assignment.column) <= (getattr(context_node, "lineno", 0), getattr(context_node, "col_offset", 0))
    ]
    if not candidates:
        return None
    unsafe_values = [assignment.value for assignment in candidates if scalar_static_value_can_hide_forbidden_argv(assignment.value)]
    if unsafe_values:
        return unsafe_values[0]
    if len(candidates) == 1:
        return candidates[0].value
    return None


def static_command_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.JoinedStr):
        return static_string_literal(node) or "f-string subprocess command"
    return static_string_literal(node)


def static_string_literal(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if not isinstance(node, ast.JoinedStr):
        return None
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
            continue
        if isinstance(value, ast.FormattedValue) and isinstance(value.value, ast.Constant):
            parts.append(str(value.value.value))
            continue
        return None
    return "".join(parts)


def shell_c_payload_has_forbidden_command(argv: list[str]) -> bool:
    if executable_basename(argv[0]) not in SHELL_COMMAND_NAMES:
        return False
    for index, item in enumerate(argv[1:], start=1):
        if not shell_command_payload_flag(item) or index + 1 >= len(argv):
            continue
        return True
    return False


def shell_command_payload_flag(item: str) -> bool:
    return bool(re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", item))


def scalar_static_value_can_hide_forbidden_argv(value: str) -> bool:
    if executable_basename(value) in PROHIBITED_COMMAND_NAMES | SHELL_RUNTIME_COMMAND_NAMES or has_prohibited_script_suffix(value):
        return True
    if "git bash" in value.lower():
        return True
    return any(command_argv_contains_forbidden(delegated_argv) for delegated_argv in env_split_string_argvs(value))


def partial_env_delegation_contains_forbidden(argv: list[str | None], *, depth: int = 0) -> bool:
    index = 1
    while index < len(argv):
        item = argv[index]
        if item is None:
            return True
        if item in {"-S", "--split-string"}:
            if index + 1 >= len(argv):
                return False
            payload = argv[index + 1]
            if payload is None:
                return True
            return any(command_argv_contains_forbidden(delegated_argv) for delegated_argv in env_split_string_argvs(payload))
        if item.startswith("-S") and item != "-S":
            return any(command_argv_contains_forbidden(delegated_argv) for delegated_argv in env_split_string_argvs(item[2:].strip()))
        if item.startswith("--split-string="):
            return any(command_argv_contains_forbidden(delegated_argv) for delegated_argv in env_split_string_argvs(item.split("=", 1)[1]))
        if item in {"-u", "--unset", "-C", "--chdir"}:
            index += 2
            continue
        if item.startswith("--unset=") or item.startswith("--chdir="):
            index += 1
            continue
        if item.startswith("-"):
            index += 1
            continue
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", item):
            index += 1
            continue
        return partial_command_argv_contains_forbidden(argv[index:], depth=depth + 1)
    return False


def env_delegated_argvs(argv: list[str]) -> list[list[str]]:
    delegated: list[list[str]] = []
    index = 1
    while index < len(argv):
        item = argv[index]
        if item in {"-S", "--split-string"}:
            if index + 1 < len(argv):
                delegated.extend(env_split_string_argvs(argv[index + 1]))
            index += 2
            continue
        if item.startswith("-S") and item != "-S":
            delegated.extend(env_split_string_argvs(item[2:].strip()))
            index += 1
            continue
        if item.startswith("--split-string="):
            delegated.extend(env_split_string_argvs(item.split("=", 1)[1]))
            index += 1
            continue
        if item in {"-u", "--unset", "-C", "--chdir"}:
            index += 2
            continue
        if item.startswith("--unset=") or item.startswith("--chdir="):
            index += 1
            continue
        if item.startswith("-"):
            index += 1
            continue
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", item):
            index += 1
            continue
        delegated.append(argv[index:])
        break
    return delegated


def env_split_string_argvs(payload: str) -> list[list[str]]:
    try:
        tokens = shlex.split(payload)
    except ValueError:
        tokens = payload.split()
    if not tokens:
        return []
    return env_delegated_argvs(["env", *tokens])


def has_prohibited_script_suffix(path: str) -> bool:
    return Path(normalize_path(path)).suffix.lower() in PROHIBITED_SCRIPT_SUFFIXES


def executable_basename(path: str) -> str:
    return Path(normalize_path(path)).name.lower()


def zero_bash_python_classification(path: str, category: str, allowlist: list[dict[str, Any]]) -> str:
    if zero_bash_allowlisted(path, category, allowlist):
        return "historical_allowlist"
    if zero_bash_historical_path(path):
        return "historical_allowlist"
    return "blocking_zero_bash"


def zero_bash_active_role(path: str) -> str:
    if path.startswith("dist/"):
        return "generated_payload"
    if path.startswith("speckit-pro/skills/") or path.startswith("speckit-pro/codex-skills/"):
        return "installed_skill"
    if path.startswith("speckit-pro/agents/") or path.startswith("speckit-pro/codex-agents/"):
        return "installed_agent"
    if path.startswith("speckit-pro/hooks/") or path == "speckit-pro/codex-hooks.json":
        return "installed_hook"
    return "plugin_source"


def zero_bash_historical_path(path: str) -> bool:
    return path.startswith((".specify/memory/", "docs/ai/specs/.process/"))


def zero_bash_allowlisted(path: str, category: str, allowlist: list[dict[str, Any]]) -> bool:
    if not zero_bash_historical_path(path):
        return False
    for entry in allowlist:
        entry_path = entry.get("path")
        categories = entry.get("categories")
        if entry_path != path:
            continue
        if entry.get("release_readiness_excluded") is not True:
            return False
        if isinstance(categories, list) and categories and category not in categories:
            continue
        return True
    return False


def zero_bash_remediation(path: str) -> str:
    return "Remove active shell guidance or move historical prose into a release-readiness-excluded allowlist entry."


def zero_bash_finding_record(finding: RawFinding) -> dict[str, Any]:
    record = finding.as_record()
    if finding.path.startswith("dist/claude/"):
        surface = "claude_payload"
    elif finding.path.startswith("dist/codex/"):
        surface = "codex_payload"
    elif finding.path.startswith("speckit-pro/"):
        surface = "plugin_source"
    else:
        surface = "repository"
    record["surface"] = surface
    return record


def load_zero_bash_allowlist(repo_root: Path, case: dict[str, Any]) -> list[dict[str, Any]] | dict[str, Any]:
    raw = case.get("allowlist_file", PLUGIN_BASH_CONFINEMENT_ALLOWLIST)
    if not isinstance(raw, str) or not raw:
        return diagnostic("invalid_allowlist", "zero-Bash allowlist path must be a non-empty string")
    path = resolve_path(raw, repo_root)
    if not is_relative_to(path.resolve(strict=False), repo_root.resolve(strict=False)):
        return diagnostic("invalid_allowlist", "zero-Bash allowlist must stay inside the repository")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return diagnostic("invalid_allowlist", "zero-Bash allowlist could not be loaded", details={"allowlist_file": raw, "error": type(exc).__name__})
    if document.get("schema_version") != "2.0":
        return diagnostic("invalid_allowlist", "zero-Bash allowlist schema_version must be 2.0")
    if document.get("contract_id") != "plugin-bash-confinement":
        return diagnostic("invalid_allowlist", "zero-Bash allowlist contract_id must be plugin-bash-confinement")
    entries = document.get("entries")
    if not isinstance(entries, list):
        return diagnostic("invalid_allowlist", "zero-Bash allowlist must contain an entries array")
    valid_entries: list[dict[str, Any]] = []
    allowed_entry_fields = {
        "path",
        "line_start",
        "line_end",
        "categories",
        "reason",
        "scope",
        "release_readiness_excluded",
    }
    for entry in entries:
        if not isinstance(entry, dict):
            return diagnostic("invalid_allowlist", "zero-Bash allowlist entries must be objects")
        if not isinstance(entry.get("path"), str) or not entry.get("path"):
            return diagnostic("invalid_allowlist", "zero-Bash allowlist entries require path")
        if entry.get("release_readiness_excluded") is not True:
            return diagnostic("invalid_allowlist", "zero-Bash allowlist entries must be excluded from release readiness")
        normalized_entry = dict(entry)
        reason = normalized_entry.get("reason")
        scope = normalized_entry.get("scope")
        categories = normalized_entry.get("categories")
        normalized_path = normalize_path(str(normalized_entry["path"]))
        line_start = normalized_entry.get("line_start")
        line_end = normalized_entry.get("line_end")
        extra_fields = sorted(set(normalized_entry) - allowed_entry_fields)
        if extra_fields:
            normalized_entry["_invalid_reason"] = "zero-Bash allowlist entries contain unsupported fields"
        elif normalized_path.startswith("/") or any(part == ".." for part in normalized_path.split("/")):
            normalized_entry["_invalid_reason"] = "zero-Bash allowlist paths must be repository-relative and must not traverse"
        elif line_start is not None and (not isinstance(line_start, int) or line_start < 1):
            normalized_entry["_invalid_reason"] = "zero-Bash allowlist line_start must be an integer greater than or equal to 1"
        elif line_end is not None and (not isinstance(line_end, int) or line_end < 1):
            normalized_entry["_invalid_reason"] = "zero-Bash allowlist line_end must be an integer greater than or equal to 1"
        elif isinstance(line_start, int) and isinstance(line_end, int) and line_end < line_start:
            normalized_entry["_invalid_reason"] = "zero-Bash allowlist line_end must be greater than or equal to line_start"
        elif not isinstance(reason, str) or not reason.strip():
            normalized_entry["_invalid_reason"] = "zero-Bash allowlist entries require a non-empty reason"
        elif not isinstance(scope, str) or not scope.strip():
            normalized_entry["_invalid_reason"] = "zero-Bash allowlist entries require a non-empty scope"
        elif not isinstance(categories, list) or not categories or any(not isinstance(category, str) or not category for category in categories):
            normalized_entry["_invalid_reason"] = "zero-Bash allowlist entries require a non-empty categories array of strings"
        elif len(set(categories)) != len(categories):
            normalized_entry["_invalid_reason"] = "zero-Bash allowlist categories must be unique"
        elif not zero_bash_historical_path(normalized_path):
            normalized_entry["_invalid_reason"] = "zero-Bash allowlist entries must be limited to historical process evidence"
        valid_entries.append(normalized_entry)
    return valid_entries


def zero_bash_allowlist_findings(allowlist: list[dict[str, Any]]) -> list[RawFinding]:
    findings: list[RawFinding] = []
    for entry in allowlist:
        invalid_reason = entry.get("_invalid_reason")
        if not isinstance(invalid_reason, str) or not invalid_reason:
            continue
        path = normalize_path(str(entry.get("path") or "allowlist"))
        findings.append(
            RawFinding(
                path=path,
                line=None,
                category="allowlist",
                pattern="allowlist",
                reason=invalid_reason,
                active_role="zero_bash_allowlist",
                classification="blocking_zero_bash",
                remediation="Keep zero-Bash allowlist entries historical, category-scoped, and release-readiness excluded.",
            )
        )
    return findings


def missing_zero_bash_scan_root_findings(repo_root: Path, case: dict[str, Any]) -> list[RawFinding]:
    if isinstance(case.get("files"), list):
        return []
    roots = case.get("scan_roots")
    if not isinstance(roots, list):
        return [
            RawFinding(
                path="scan_roots",
                line=None,
                category="scan_root",
                pattern="scan_roots",
                reason="zero-Bash guard requires explicit scan roots",
                active_role="zero_bash_guard",
                classification="blocking_zero_bash",
                remediation="Declare source and generated payload roots in the guard case.",
            )
        ]
    if not roots:
        return [
            RawFinding(
                path="scan_roots",
                line=None,
                category="scan_root",
                pattern="[]",
                reason="zero-Bash guard requires at least one scan root",
                active_role="zero_bash_guard",
                classification="blocking_zero_bash",
                remediation="Declare source and generated payload roots in the guard case.",
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
                    active_role="zero_bash_guard",
                    classification="blocking_zero_bash",
                    remediation="Keep zero-Bash scan roots normalized, repository-relative, and inside the repository.",
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
                reason="configured zero-Bash scan root is missing",
                active_role="zero_bash_guard",
                classification="blocking_zero_bash",
                remediation="Restore the scan root or update the promoted zero-Bash fixture.",
            )
        )
    configured_roots = {
        normalize_path(str(root)).rstrip("/")
        for root in roots
        if isinstance(root, str) and root and invalid_scan_root_reason(root) is None
    }
    for required_root in sorted(PLUGIN_BASH_CONFINEMENT_REQUIRED_SCAN_ROOTS):
        if any(required_root == root or required_root.startswith(f"{root}/") for root in configured_roots):
            continue
        findings.append(
            RawFinding(
                path=required_root,
                line=None,
                category="scan_root",
                pattern=required_root,
                reason="zero-Bash guard requires source and generated payload scan roots",
                active_role="zero_bash_guard",
                classification="blocking_zero_bash",
                remediation="Declare source, generated payload, payload builder, and README roots in the promoted zero-Bash guard case.",
            )
        )
    return findings


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


def active_runtime_guard_response(entry: Any, request: Any, findings: list[RawFinding]) -> dict[str, Any]:
    blocking = [finding for finding in findings if finding.classification == "blocking_active_runtime"]
    status = "expected_failure" if blocking else "ok"
    returned_findings = bounded_findings(findings)
    data = active_runtime_base_data(entry, request.operation, status)
    data.update(
        {
            "schema_version": "2.0",
            "contract_id": "installed-plugin-release",
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


def bounded_findings(findings: list[RawFinding]) -> list[RawFinding]:
    blocking = [finding for finding in findings if finding.classification == "blocking_active_runtime"]
    if blocking:
        return blocking[:25]
    return findings[:25]


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


def scan_installed_runtime_sources(sources: list[SourceFile], repo_root: Path) -> list[RawFinding]:
    findings: list[RawFinding] = []
    seen: set[tuple[str, int | None, str, str]] = set()
    for source in sources:
        path = normalize_path(source.path)
        lines = source.content.splitlines()
        workflow_contexts = workflow_run_contexts(source.content) if path.startswith(".github/workflows/") else []
        if has_prohibited_script_suffix(path):
            add_finding(
                findings,
                seen,
                classify_installed_runtime_raw_finding(
                    path,
                    1,
                    "script_file",
                    Path(path).suffix,
                    "script file retained in scanned scope",
                    source.content,
                    source.source_kind,
                ),
            )
        if path.startswith(".github/workflows/") and is_direct_python_gate_dispatch(source.content):
            line = direct_dispatch_line(source.content)
            add_finding(
                findings,
                seen,
                classify_installed_runtime_raw_finding(
                    path,
                    line,
                    "bash",
                    "run: python -m speckit_pro_runner",
                    "workflow shell dispatches a Python gate",
                    source.content,
                    source.source_kind,
                ),
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
                    classify_installed_runtime_raw_finding(path, line_number, category, match.group(0), reason, context, source.source_kind),
                )
        for number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or (stripped.startswith("#") and not path.endswith(".md")):
                continue
            for category, pattern, reason in FORBIDDEN_PATTERNS:
                match = pattern.search(line)
                if match is None:
                    continue
                context = workflow_context_for_line(workflow_contexts, number) or line_context(lines, number)
                if path == CONTAINER_PREFLIGHT_WORKFLOW:
                    context = source.content
                if installed_runtime_agent_tool_declaration(path, line):
                    context = line
                add_finding(
                    findings,
                    seen,
                    classify_installed_runtime_raw_finding(path, number, category, match.group(0), reason, context, source.source_kind),
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


def classify_installed_runtime_raw_finding(
    path: str,
    line: int | None,
    category: str,
    pattern: str,
    reason: str,
    content: str,
    source_kind: str,
) -> RawFinding:
    role = installed_runtime_active_role(path)
    classification = classify_installed_runtime_path(path, category, pattern, content, source_kind)
    return RawFinding(
        path=path,
        line=line,
        category=category,
        pattern=pattern[:120],
        reason=reason,
        active_role=role,
        classification=classification,
        remediation=installed_runtime_remediation_for(classification),
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


def classify_installed_runtime_path(path: str, category: str, pattern: str, content: str, source_kind: str) -> str:
    if path.startswith(".specify/memory/"):
        return "archive_provenance"
    if path.startswith(".specify/scripts/bash/"):
        return "upstream_spec_kit_helper"
    if path.startswith("tests/") or "/fixtures/" in path or "layer8-parity/" in path:
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


def repository_bash_container_preflight_dispatch_glue(path: str, content: str) -> bool:
    """Recognize the exact CI-only workflow without allowing shell helpers back in."""
    if path != CONTAINER_PREFLIGHT_WORKFLOW:
        return False
    required_markers = (
        "permissions: {}",
        "container-preflight-linux-amd64",
        "container-preflight-linux-arm64",
        "python3 -m speckit_pro_runner",
        "-m speckit_pro_runner",
        "actions/upload-artifact@v7",
    )
    if not all(marker in content for marker in required_markers):
        return False
    if re.search(r"(?i)(?<![\w-])jq(?![\w-])", content):
        return False
    if re.search(r"(?i)\.(?:sh|bash|zsh|ps1|bat|cmd)\b", content):
        return False
    return re.search(
        r"(?im)(?:^|[;&|])[ \t]*(?:bash|bash\.exe|sh|sh\.exe|zsh|zsh\.exe|"
        r"powershell|powershell\.exe|pwsh|pwsh\.exe)\b[ \t]+",
        content,
    ) is None


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
    if lowered_path.endswith("speckit_pro_runner/gates/active_path_guard.py"):
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
    if lowered_path.endswith("speckit_pro_runner/gates/active_path_guard.py"):
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


def installed_runtime_remediation_for(classification: str) -> str:
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


def line_context(lines: list[str], number: int, *, radius: int = 3) -> str:
    start = max(number - radius - 1, 0)
    end = min(number + radius, len(lines))
    return "\n".join(lines[start:end])


def line_number_for_offset(content: str, offset: int) -> int:
    return content.count("\n", 0, max(offset, 0)) + 1


def workflow_run_contexts(content: str) -> list[tuple[int, int, str]]:
    contexts: list[tuple[int, int, str]] = []
    lines = content.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        match = re.fullmatch(r"(?:-\s+)?run:\s*(.*)", stripped)
        if match is None:
            index += 1
            continue
        scalar = match.group(1).strip()
        if not scalar:
            index += 1
            continue
        start = index + 1
        indent = len(line) - len(line.lstrip(" "))
        block = [line]
        end = start
        if re.fullmatch(r"[|>][+-]?", scalar):
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
        "docs-quality",
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
    if any(marker in lowered for marker in {"docs-quality", "docs validation", "validation_mode", "should_validate_docs", "--mode docs"}):
        return True
    return any(marker in lowered for marker in markers) and not any(marker in lowered for marker in plugin_markers)


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
            "comparison_ids": [operation],
        },
        "artifacts": [{"path": DEFAULT_CASE_FILE, "kind": "fixture"}],
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
            "comparison_ids": [f"installed-plugin-release-{operation}"],
        },
        "artifacts": [
            {"path": INSTALLED_RUNTIME_DEFAULT_CASE_FILE, "kind": "fixture"},
        ],
    }


def zero_bash_base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    gate_status = "pass" if status == "ok" else "fail"
    return {
        "gate": {
            "gate_id": entry.helper_id,
            "operation": operation,
            "gate_status": gate_status,
            "promoted": status != "input_error",
            "blocking": status != "ok",
            "comparison_ids": [f"plugin-bash-confinement-{operation}"],
        },
        "artifacts": [
            {"path": PLUGIN_BASH_CONFINEMENT_DEFAULT_CASE_FILE, "kind": "fixture"},
            {"path": PLUGIN_BASH_CONFINEMENT_ALLOWLIST, "kind": "allowlist"},
        ],
        "schema_version": "2.0",
        "contract_id": "plugin-bash-confinement",
        "status": "pass" if status == "ok" else "fail",
        "blocking_count": 0 if status == "ok" else 1,
        "classified_counts": {},
        "findings": [],
        "total_finding_count": 0,
        "truncated_finding_count": 0,
        "script_file_count": 0,
        "scan_roots": [],
        "allowlist": {
            "path": PLUGIN_BASH_CONFINEMENT_ALLOWLIST,
            "entry_count": 0,
            "release_readiness_excluded": False,
        },
    }


def repo_bash_base_data(
    entry: Any,
    operation: str,
    status: str,
    inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    passing = status == "ok"
    inspection_state = "inspected" if passing else "not_inspected"
    allowlist_path = (inputs or {}).get("allowlist_file", REPOSITORY_BASH_CONFINEMENT_ALLOWLIST)
    if not isinstance(allowlist_path, str) or not allowlist_path:
        allowlist_path = REPOSITORY_BASH_CONFINEMENT_ALLOWLIST
    return {
        "gate": {
            "gate_id": entry.helper_id,
            "operation": operation,
            "gate_status": "pass" if passing else "fail",
            "promoted": status not in {"input_error", "missing_prerequisite"},
            "blocking": not passing,
            "comparison_ids": ["repository-bash-confinement"],
        },
        "artifacts": [
            {"path": REPOSITORY_BASH_CONFINEMENT_DEFAULT_CASE_FILE, "kind": "fixture"},
            {"path": REPOSITORY_BASH_CONFINEMENT_ALLOWLIST, "kind": "allowlist"},
        ],
        "schema_version": "2.0",
        "contract_id": "repository-bash-confinement",
        "status": "pass" if passing else "fail",
        "blocking_count": 0 if passing else 1,
        "classified_counts": {},
        "findings": [],
        "total_finding_count": 0,
        "truncated_finding_count": 0,
        "script_file_count": 0,
        "enumeration": {
            "active_instruction_values": inspection_state,
            "runtime_diagnostic_values": inspection_state,
            "source": "git ls-files -z",
            "workflow_run_values": inspection_state,
            "tracked_file_count": 0,
        },
        "allowlist": {
            "path": allowlist_path,
            "entry_count": len(REPOSITORY_BASH_CONFINEMENT_ALLOWLIST_PATHS) if passing else 0,
            "release_readiness_excluded": passing,
        },
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


def resolve_path(raw: str, root: Path) -> Path:
    path = Path(raw.replace("\\", "/"))
    return path if path.is_absolute() else root / path


def normalize_path(raw: str) -> str:
    path = raw.replace("\\", "/")
    return path[2:] if path.startswith("./") else path


def invalid_scan_root_reason(raw: str) -> str | None:
    root = normalize_path(raw)
    if not root:
        return "configured scan root must be non-empty"
    if Path(root).is_absolute() or re.match(r"^[A-Za-z]:", root) or root.startswith("~"):
        return "configured scan root must be repository-relative"
    parts = [part for part in root.split("/") if part and part != "."]
    if any(part == ".." for part in parts):
        return "configured scan root must not traverse outside the repository"
    return None


def scan_root_entry_validation(index: int, raw: object) -> tuple[str, str, str | None]:
    if not isinstance(raw, str):
        return f"scan_roots[{index}]", type(raw).__name__, "configured scan root must be a non-empty string"
    if not raw:
        return f"scan_roots[{index}]", "", "configured scan root must be a non-empty string"
    return raw, raw, invalid_scan_root_reason(raw)


def zero_bash_extensionless_scan_path(path: str) -> bool:
    normalized = normalize_path(path)
    if Path(normalized).suffix:
        return False
    return normalized.startswith(
        (
            "speckit-pro/",
            "dist/claude/speckit-pro/",
            "dist/codex/speckit-pro/",
        )
    )


def has_prohibited_script_shebang(path: Path) -> bool:
    return has_prohibited_script_shebang_content(read_first_line(path))


def read_first_line(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return handle.readline(4096)
    except (OSError, UnicodeDecodeError):
        return ""


def has_prohibited_script_shebang_content(content: str) -> bool:
    try:
        first_line = content.splitlines()[0]
    except IndexError:
        return False
    return bool(re.search(r"^#!.*\b(?:bash|sh|zsh|powershell|pwsh)\b", first_line, re.IGNORECASE))
