"""Zero-bash plugin confinement guard."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from ...envelope import diagnostic
from ...path_utils import is_relative_to
from .common import (
    FORBIDDEN_CONTENT_PATTERNS,
    FORBIDDEN_PATTERNS,
    HARD_RUNTIME_CATEGORIES,
    PROHIBITED_COMMAND_NAMES,
    PROHIBITED_SCRIPT_SUFFIXES,
    RawFinding,
    SourceFile,
    TEXT_SUFFIXES,
    add_finding,
    executable_basename,
    has_prohibited_script_suffix,
    invalid_scan_root_reason,
    is_hook_matcher_line,
    line_context,
    line_number_for_offset,
    normalize_path,
    resolve_path,
    scan_root_entry_validation,
)
from .python_ast import (
    call_has_command_string,
    call_has_shell_enabled,
    command_argv_subprocess_pattern,
    is_os_system_call,
    is_shell_backed_subprocess_call,
    is_subprocess_call,
    os_shell_call_pattern,
    python_partial_command_assignments,
    python_shell_aliases,
    python_static_bool_assignments,
    python_static_command_assignments,
    shell_keyword_pattern,
    subprocess_call_pattern,
)
from .runtime_guard import (
    installed_runtime_agent_tool_declaration,
)


PLUGIN_BASH_CONFINEMENT_DEFAULT_CASE_FILE = "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/zero-bash-guard-cases.json"
PLUGIN_BASH_CONFINEMENT_ALLOWLIST = "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/allowlist.json"
PLUGIN_BASH_CONFINEMENT_REQUIRED_SCAN_ROOTS = frozenset(
    {
        "speckit-pro",
        "scripts/refresh-release-artifacts.py",
        "dist/claude/speckit-pro",
        "dist/codex/speckit-pro",
        "README.md",
    }
)


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
            if is_hook_matcher_line(path, line):
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


def has_prohibited_script_shebang_content(content: str) -> bool:
    try:
        first_line = content.splitlines()[0]
    except IndexError:
        return False
    return bool(re.search(r"^#!.*\b(?:bash|sh|zsh|powershell|pwsh)\b", first_line, re.IGNORECASE))
