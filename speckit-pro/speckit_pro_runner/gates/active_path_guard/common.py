"""Shared types, constants, and path helpers for the active-path guard family."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...envelope import diagnostic
from ...path_utils import find_repo_root, is_relative_to


DEFAULT_CASE_FILE = "tests/speckit-pro/unit/fixtures/runner-gates/active-path-guard-cases.json"
CONTAINER_PREFLIGHT_WORKFLOW = ".github/workflows/container-preflight.yml"
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
    "eval_harness_native_execution",
    "docs_out_of_scope",
)


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


def deduplicate_raw_findings(findings: list[RawFinding]) -> list[RawFinding]:
    records: dict[tuple[str, int | None, str, str], RawFinding] = {}
    for finding in findings:
        records[(finding.path, finding.line, finding.category, finding.pattern)] = finding
    return list(records.values())


def has_prohibited_script_suffix(path: str) -> bool:
    return Path(normalize_path(path)).suffix.lower() in PROHIBITED_SCRIPT_SUFFIXES


def executable_basename(path: str) -> str:
    return Path(normalize_path(path)).name.lower()


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


HOOK_MANIFEST_NAMES = frozenset({"hooks.json", "codex-hooks.json"})
_HOOK_MATCHER_LINE_RE = re.compile(r'^\s*"matcher"\s*:\s*"[^"]*"\s*,?\s*$')


def is_hook_matcher_line(path: str, line: str) -> bool:
    """A hook manifest's ``matcher`` field names the tool a hook filters on.

    Naming the shell tool there is not a shell dependency: the value is a
    regex the host matches against tool names, never a command. Without this
    exemption a PreToolUse hook that filters on the shell tool would have to
    register without a matcher and run on every tool call. The exemption is
    exactly one field of the two hook manifests; scripts, prose, commands, and
    every other field stay under the full scan.
    """
    return Path(path).name in HOOK_MANIFEST_NAMES and _HOOK_MATCHER_LINE_RE.match(line) is not None


def add_finding(findings: list[RawFinding], seen: set[tuple[str, int | None, str, str]], finding: RawFinding) -> None:
    key = (finding.path, finding.line, finding.category, finding.pattern)
    if key in seen:
        return
    seen.add(key)
    findings.append(finding)


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


def read_first_line(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return handle.readline(4096)
    except (OSError, UnicodeDecodeError):
        return ""
