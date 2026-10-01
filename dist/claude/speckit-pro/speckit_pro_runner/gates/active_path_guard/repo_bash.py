"""Repository Bash-confinement guard."""

from __future__ import annotations

import ast
import json
import re
import shlex
import string
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from ...envelope import diagnostic, is_diagnostic, response
from ...path_utils import is_relative_to
from .common import (
    OS_SHELL_FUNCTION_NAMES,
    RawFinding,
    SUBPROCESS_ARGV_FUNCTION_NAMES,
    SUBPROCESS_SHELL_FUNCTION_NAMES,
    classified_counts,
    deduplicate_raw_findings,
    executable_basename,
    invalid_scan_root_reason,
    normalize_path,
    read_first_line,
    resolve_path,
    workflow_run_contexts,
)
from .python_ast import (
    call_has_shell_enabled,
    env_delegated_argvs,
    env_split_string_argvs,
    is_os_system_call,
    is_shell_backed_subprocess_call,
    is_subprocess_call,
    python_shell_aliases,
    shell_command_payload_flag,
    static_string_literal,
    subprocess_args_node,
)


REPOSITORY_BASH_CONFINEMENT_DEFAULT_CASE_FILE = "tests/speckit-pro/unit/fixtures/repository-bash-confinement/confinement-guard-cases.json"
REPOSITORY_BASH_CONFINEMENT_ALLOWLIST = "tests/speckit-pro/unit/fixtures/repository-bash-confinement/allowlist.json"
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

    findings = [repo_bash_classify_native_execution(finding) for finding in findings]
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


# Native-execution surfaces of the eval harness. These findings are fail-closed
# on an executable the AST resolver cannot follow -- a harness-generated
# launcher or a tool binary pinned by a validated runtime receipt -- not on
# evidence of a Bash dependency. A real bash/sh/jq token or Bash-family script
# suffix is detected independently and stays blocking in every path, so this
# cannot hide a genuine dependency. Deliberately separate from the canonical
# Spec Kit allowlist, which stays reserved for vendored helpers.
REPO_BASH_NATIVE_EXECUTION_PREFIXES = (
    "tests/speckit-pro/lib/native_eval_",
    "tests/speckit-pro/unit/test-native-",
)
REPO_BASH_NATIVE_EXECUTION_CLASSIFICATION = "eval_harness_native_execution"


def repo_bash_classify_native_execution(finding: RawFinding) -> RawFinding:
    """Downgrade unresolved-executable findings inside the native eval harness."""
    if finding.classification != "blocking_repo_bash":
        return finding
    if finding.category != "command_argv_subprocess" or "<dynamic" not in finding.pattern:
        return finding
    if not finding.path.startswith(REPO_BASH_NATIVE_EXECUTION_PREFIXES):
        return finding
    return replace(
        finding,
        active_role="eval_harness_native_execution",
        classification=REPO_BASH_NATIVE_EXECUTION_CLASSIFICATION,
        remediation=(
            "Keep the executable receipt-validated or harness-generated. "
            "Never introduce a shell token or Bash-family script suffix."
        ),
    )


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
                for key, value in zip(node.keys, node.values, strict=True):
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
            for key, value in zip(node.right.keys, node.right.values, strict=True):
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
