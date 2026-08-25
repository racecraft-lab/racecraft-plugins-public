"""Trusted launchers for feedback-sweep model calls."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .sweep_isolation import (
    BROKER_ERROR_CODES,
    BROKER_TOOL_NAMES,
    HOOK_VERSION,
    RECEIPT_RE,
    SweepSession,
    default_state_root,
)


MINIMUM_CODEX_VERSION = (0, 138, 0)
MINIMUM_CLAUDE_VERSION = (2, 1, 245)
CODEX_DISABLED_FEATURES = (
    "apps",
    "browser_use",
    "browser_use_external",
    "computer_use",
    "goals",
    "hooks",
    "image_generation",
    "in_app_browser",
    "memories",
    "multi_agent",
    "plugins",
    "recommended_plugins",
    "shell_tool",
    "skill_search",
    "tool_suggest",
    "unified_exec",
    "view_image",
    "workspace_dependencies",
)
CODEX_STAGE_PROMPTS = {
    "classifier": (
        "You must call the broker tools. Your first action must be "
        "mcp__sweep-broker__review_comment with an empty object. "
        "Do not produce analysis or a final response before that call. You cannot construct or guess "
        "the receipt. Classify that configured comment, then call "
        "mcp__sweep-broker__submit_result exactly once with one top-level result field: "
        '{"result":{"comment_id":"...","class":"...","target":null,"reason":"..."}}. '
        "Copy only the exact receipt returned by "
        "mcp__sweep-broker__submit_result into the receipt field. If a broker call fails, do not emit "
        "a receipt-shaped value."
    ),
    "perspective": (
        "Your first action must be mcp__sweep-broker__review_comment with an empty object, followed by "
        "mcp__sweep-broker__consensus_inputs with an empty object. Do not produce analysis or a final "
        "response before those calls. You cannot construct or guess the receipt. Analyze the configured "
        "perspective, then call mcp__sweep-broker__submit_result exactly once with one top-level result "
        'field: {"result":{"comment_id":"...","perspective":"...","finding":"...",'
        '"evidence":[],"escape_hatch":false}}. Copy only its exact '
        "returned receipt into the receipt field. If a broker call fails, do not emit a receipt-shaped value."
    ),
    "synthesis": (
        "Your first action must be mcp__sweep-broker__consensus_inputs with an empty object. Do not "
        "produce analysis or a final response before that call. You cannot construct or guess the receipt. "
        "Synthesize the accepted perspectives, then call mcp__sweep-broker__submit_result exactly once "
        'with one top-level result field: {"result":{"comment_id":"...","outcome":"...",'
        '"agreement":null,"basis":"...","edit":null}}. '
        "Copy only its exact returned receipt into the receipt field. If a broker call fails, do not emit "
        "a receipt-shaped value."
    ),
}
CODEX_VERSION_RE = re.compile(r"(?:codex-cli\s+)?([0-9]+)\.([0-9]+)\.([0-9]+)")
CLAUDE_VERSION_RE = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)(?:\s+\(Claude Code\))?")
CLAUDE_BROKER_TOOLS = tuple(
    f"mcp__plugin_speckit-pro_sweep-broker__{name}" for name in BROKER_TOOL_NAMES
)
CLAUDE_RECEIPT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "receipt": {
            "type": "string",
            "pattern": r"^sweep-result:v1:[0-9a-f]{64}$",
        }
    },
    "required": ["receipt"],
    "additionalProperties": False,
}


class LauncherViolation(RuntimeError):
    """An isolated model process or security prerequisite failed closed."""


def _trusted_executable(candidate: str | None, label: str) -> Path:
    if not candidate:
        raise LauncherViolation(f"{label} is unavailable")
    candidate_path = Path(candidate)
    if not candidate_path.is_absolute():
        raise LauncherViolation(f"{label} runtime path must be absolute")
    try:
        resolved = candidate_path.resolve(strict=True)
        info = resolved.stat()
    except OSError as exc:
        raise LauncherViolation(f"{label} runtime path cannot be attested") from exc
    if (
        not resolved.is_absolute()
        or not stat.S_ISREG(info.st_mode)
        or not os.access(resolved, os.X_OK)
        or stat.S_IMODE(info.st_mode) & 0o022
    ):
        raise LauncherViolation(f"{label} runtime path is unsafe")
    return resolved


def codex_executable() -> Path:
    """Resolve the exact CLI binary admitted by the isolated profile."""
    return _trusted_executable(shutil.which("codex"), "Codex")


def claude_executable() -> Path:
    """Resolve the exact Claude CLI used for the isolated sweep launcher."""
    return _trusted_executable(shutil.which("claude"), "Claude Code")


def python_executable() -> Path:
    """Resolve the exact interpreter used for the packaged broker."""
    return _trusted_executable(sys.executable, "Python")


def _toml_string(value: str) -> str:
    return json.dumps(value)


def _toml_array(values: list[str]) -> str:
    return "[" + ",".join(_toml_string(value) for value in values) + "]"


def _toml_inline_table(values: dict[str, str]) -> str:
    return "{" + ",".join(f"{key}={_toml_string(value)}" for key, value in values.items()) + "}"


def _toml_string_map(values: dict[str, str]) -> str:
    return "{" + ",".join(
        f"{_toml_string(key)}={_toml_string(value)}" for key, value in values.items()
    ) + "}"


def codex_prompt_resource(plugin_root: Path, name: str) -> Path:
    """Resolve one trusted prompt from exactly one supported plugin layout."""
    if name not in {"classifier", "analyst"}:
        raise LauncherViolation("unknown Codex sweep prompt")
    relative = Path("speckit-autopilot/references/sweep-prompts") / f"{name}.md"
    candidates = (
        plugin_root / "codex-skills" / relative,
        plugin_root / "skills" / relative,
    )
    regular: list[Path] = []
    for candidate in candidates:
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise LauncherViolation("trusted Codex sweep prompt cannot be attested") from exc
        if stat.S_ISREG(info.st_mode):
            regular.append(candidate)
    if len(regular) != 1:
        raise LauncherViolation("trusted Codex sweep prompt layout is unavailable or ambiguous")
    return regular[0]


def claude_command(
    *,
    plugin_root: Path,
    stage: str,
    perspective: str | None = None,
    max_budget_usd: str | None = None,
) -> list[str]:
    """Build one user-config-free Claude process with only Agent and broker tools."""
    if stage not in CODEX_STAGE_PROMPTS:
        raise LauncherViolation("unknown Claude sweep stage")
    if stage == "perspective" and perspective not in {"codebase", "spec-context", "domain"}:
        raise LauncherViolation("Claude perspective stage requires a closed perspective")
    if stage != "perspective" and perspective is not None:
        raise LauncherViolation("perspective is only valid on the perspective stage")
    role = "speckit-pro:sweep-classifier" if stage == "classifier" else "speckit-pro:sweep-analyst"
    exact_tools = ",".join(("Agent", *CLAUDE_BROKER_TOOLS))
    prompt = (
        f"Use the Agent tool exactly once with subagent_type {role}. Give it only this trusted "
        f"invocation context: stage={stage}"
        + (f"; perspective={perspective}" if perspective is not None else "")
        + ". The broker process already holds the opaque model-call capability. Do not call a "
        "broker tool in the parent. Set the structured receipt field to only the subagent's exact receipt."
    )
    command = [
        str(claude_executable()),
        "--print",
        "--plugin-dir",
        str(plugin_root),
        "--setting-sources",
        "",
        "--no-session-persistence",
        "--disable-slash-commands",
        "--no-chrome",
        "--permission-mode",
        "dontAsk",
        "--tools",
        exact_tools,
        "--allowedTools",
        exact_tools,
        "--json-schema",
        json.dumps(CLAUDE_RECEIPT_OUTPUT_SCHEMA, sort_keys=True, separators=(",", ":")),
        "--output-format",
        "json",
    ]
    if max_budget_usd is not None:
        command.extend(("--max-budget-usd", max_budget_usd))
    command.append(prompt)
    return command


def codex_command(
    *,
    plugin_root: Path,
    repo_root: Path,
    runtime_root: Path,
    capability: str,
    stage: str,
    perspective: str | None = None,
    state_root: Path | None = None,
    output_path: Path | None = None,
) -> list[str]:
    if stage not in CODEX_STAGE_PROMPTS:
        raise LauncherViolation("unknown Codex sweep stage")
    if stage == "perspective" and perspective not in {"codebase", "spec-context", "domain"}:
        raise LauncherViolation("Codex perspective stage requires a closed perspective")
    if stage != "perspective" and perspective is not None:
        raise LauncherViolation("perspective is only valid on the perspective stage")
    schema = plugin_root / "speckit_pro_runner" / "contracts" / "sweep-receipt-output.schema.json"
    codex_runtime = codex_executable()
    python_runtime = python_executable()
    codex_runtime_root = codex_runtime.parent.parent
    python_runtime_root = Path(sys.base_prefix).resolve(strict=True)
    isolated_runtime_root = runtime_root.resolve(strict=False)
    filesystem = {
        ":minimal": "read",
        str(codex_runtime_root): "read",
        str(python_runtime_root): "read",
        str(isolated_runtime_root): "read",
    }
    broker_args = ["-m", "speckit_pro_runner.sweep_broker"]
    broker_env = {
        "PYTHONPATH": str(plugin_root),
        "SPECKIT_SWEEP_CAPABILITY": capability,
        "SPECKIT_SWEEP_STATE_ROOT": str(default_state_root() if state_root is None else state_root),
    }
    prompt_resource = codex_prompt_resource(
        plugin_root, "classifier" if stage == "classifier" else "analyst"
    )
    try:
        trusted_prompt = prompt_resource.read_text(encoding="utf-8")
    except OSError as exc:
        raise LauncherViolation("trusted Codex sweep prompt resource is unavailable") from exc
    trusted_context = (
        f"\n\nTrusted invocation context: stage={stage}"
        + (f"; perspective={perspective}" if perspective is not None else "")
        + ". The broker process already holds the opaque model-call capability.\n"
        + CODEX_STAGE_PROMPTS[stage]
    )
    command = [
        str(codex_runtime),
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--ephemeral",
        "--strict-config",
        "--skip-git-repo-check",
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(schema),
        "-C",
        str(isolated_runtime_root),
        "-c",
        'default_permissions="sweep-broker-only"',
        "-c",
        f"permissions.sweep-broker-only.filesystem={_toml_string_map(filesystem)}",
        "-c",
        "permissions.sweep-broker-only.network.enabled=false",
        "-c",
        "web_search=\"disabled\"",
        "-c",
        f"mcp_servers.sweep-broker.command={_toml_string(str(python_runtime))}",
        "-c",
        f"mcp_servers.sweep-broker.args={_toml_array(broker_args)}",
        "-c",
        f"mcp_servers.sweep-broker.env={_toml_inline_table(broker_env)}",
        "-c",
        "mcp_servers.sweep-broker.enabled=true",
        "-c",
        "mcp_servers.sweep-broker.required=true",
        "-c",
        f"mcp_servers.sweep-broker.enabled_tools={_toml_array(list(BROKER_TOOL_NAMES))}",
        "-c",
        'mcp_servers.sweep-broker.default_tools_approval_mode="approve"',
    ]
    for feature in CODEX_DISABLED_FEATURES:
        command.extend(("--disable", feature))
    if output_path is not None:
        command.extend(("--output-last-message", str(output_path)))
    command.append(trusted_prompt + trusted_context)
    return command


def codex_event_projection(output: str) -> dict[str, Any]:
    """Project Codex JSONL into non-content broker-call telemetry."""
    calls: dict[str, dict[str, int]] = {}
    error_codes: dict[str, int] = {}
    unexpected_tools = 0
    jsonl = True
    for raw_line in output.splitlines():
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            jsonl = False
            continue
        if not isinstance(event, dict) or event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type != "mcp_tool_call":
            if item_type in {
                "command_execution",
                "file_change",
                "image_generation",
                "web_search",
            }:
                unexpected_tools += 1
            continue
        server = item.get("server")
        tool = item.get("tool")
        if server != "sweep-broker" or tool not in BROKER_TOOL_NAMES:
            unexpected_tools += 1
            continue
        counts = calls.setdefault(tool, {"completed": 0, "failed": 0})
        counts["completed"] += 1
        if item.get("error") is not None or item.get("status") in {"failed", "error"}:
            counts["failed"] += 1
            code = _codex_broker_error_code(item)
            error_codes[code] = error_codes.get(code, 0) + 1
    return {
        "jsonl": jsonl,
        "broker_calls": calls,
        "error_codes": error_codes,
        "unexpected_tools": unexpected_tools,
    }


def _codex_broker_error_code(item: dict[str, Any]) -> str:
    """Map fixed broker failures to enums without returning their text."""
    fragments: list[str] = []

    def collect(value: Any, depth: int = 0) -> None:
        if len(fragments) >= 32 or depth > 6:
            return
        if isinstance(value, str):
            fragments.append(value[:4_096])
        elif isinstance(value, dict):
            for nested in value.values():
                collect(nested, depth + 1)
        elif isinstance(value, list):
            for nested in value:
                collect(nested, depth + 1)

    collect(item.get("result"))
    collect(item.get("error"))
    normalized = " ".join(fragments).casefold()
    for code in BROKER_ERROR_CODES:
        if f"broker_error:{code}" in normalized:
            return code
    categories = (
        ("comment does not match", "comment_mismatch"),
        ("closed vocabulary", "classifier_class"),
        ("target does not match", "classifier_target"),
        ("reason is not", "classifier_reason"),
        ("fields do not match", "schema_fields"),
        ("unknown fields", "schema_fields"),
        ("malformed", "schema_fields"),
        ("invalid params", "tool_schema"),
        ("invalid request", "tool_schema"),
        ("validation", "tool_schema"),
        ("capability", "capability"),
        ("permission", "permission"),
    )
    for marker, code in categories:
        if marker in normalized:
            return code
    return "unclassified"


def verify_codex_event_trace(output: str, *, stage: str) -> dict[str, Any]:
    """Require one clean, stage-complete broker trace without exposing content."""
    required_by_stage = {
        "classifier": {"review_comment", "submit_result"},
        "perspective": {"review_comment", "consensus_inputs", "submit_result"},
        "synthesis": {"consensus_inputs", "submit_result"},
    }
    if stage not in required_by_stage:
        raise LauncherViolation("unknown Codex sweep stage")
    projection = codex_event_projection(output)
    calls = projection["broker_calls"]
    if (
        projection["jsonl"] is not True
        or projection["unexpected_tools"] != 0
        or projection["error_codes"]
        or any(counts["failed"] != 0 for counts in calls.values())
    ):
        raise LauncherViolation("isolated Codex sweep emitted an unsafe tool trace")
    for tool in required_by_stage[stage]:
        if calls.get(tool) != {"completed": 1, "failed": 0}:
            raise LauncherViolation("isolated Codex sweep omitted or repeated a required broker call")
    return projection


def _codex_version() -> tuple[int, int, int]:
    candidate = shutil.which("codex")
    executable = _trusted_executable(candidate, "Codex")
    candidate = shutil.which("codex", path=str(executable.parent))
    if _trusted_executable(candidate, "Codex") != executable:
        raise LauncherViolation("Codex runtime changed after boundary attestation")
    try:
        completed = subprocess.run(
            [candidate, "--version"],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LauncherViolation("Codex is unavailable; install Codex 0.138.0 or newer") from exc
    match = CODEX_VERSION_RE.search(completed.stdout + completed.stderr)
    if completed.returncode != 0 or match is None:
        raise LauncherViolation("Codex version could not be verified; install Codex 0.138.0 or newer")
    return tuple(int(value) for value in match.groups())


def _verify_codex_features() -> None:
    candidate = shutil.which("codex")
    executable = _trusted_executable(candidate, "Codex")
    candidate = shutil.which("codex", path=str(executable.parent))
    if _trusted_executable(candidate, "Codex") != executable:
        raise LauncherViolation("Codex runtime changed after boundary attestation")
    try:
        completed = subprocess.run(
            [candidate, "features", "list"],
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LauncherViolation("Codex feature support could not be attested") from exc
    available = {line.split()[0] for line in completed.stdout.splitlines() if line.split()}
    missing = sorted(set(CODEX_DISABLED_FEATURES) - available)
    if completed.returncode != 0 or missing:
        raise LauncherViolation("Codex cannot disable every privileged sweep surface; upgrade Codex")


def verify_codex_boundary(plugin_root: Path | None = None) -> tuple[int, int, int]:
    """Attest the non-model Codex prerequisites before private capture."""
    version = _codex_version()
    if version < MINIMUM_CODEX_VERSION:
        raise LauncherViolation("Codex permission profiles require Codex 0.138.0 or newer")
    _verify_codex_features()
    candidate = shutil.which("codex")
    executable = _trusted_executable(candidate, "Codex")
    candidate = shutil.which("codex", path=str(executable.parent))
    if _trusted_executable(candidate, "Codex") != executable:
        raise LauncherViolation("Codex runtime changed after boundary attestation")
    try:
        completed = subprocess.run(
            [candidate, "exec", "--help"],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LauncherViolation("Codex isolated-exec support could not be attested") from exc
    help_text = completed.stdout + completed.stderr
    required_flags = {
        "--ignore-user-config",
        "--ignore-rules",
        "--ephemeral",
        "--strict-config",
        "--skip-git-repo-check",
        "--output-schema",
    }
    if completed.returncode != 0 or not required_flags.issubset(set(help_text.split())):
        raise LauncherViolation("Codex lacks the required isolated-exec permission controls; upgrade Codex")
    if plugin_root is not None:
        schema = plugin_root / "speckit_pro_runner" / "contracts" / "sweep-receipt-output.schema.json"
        try:
            parsed = json.loads(schema.read_text(encoding="utf-8"))
            codex_prompt_resource(plugin_root, "classifier")
            codex_prompt_resource(plugin_root, "analyst")
            if not isinstance(parsed, dict):
                raise ValueError("trusted launcher resources are malformed")
        except (OSError, ValueError, json.JSONDecodeError, LauncherViolation) as exc:
            raise LauncherViolation("trusted Codex sweep launcher resources are unavailable") from exc
    return version


def run_codex_sweep(
    *,
    plugin_root: Path,
    repo_root: Path,
    session_id: str,
    comment_id: str,
    stage: str,
    perspective: str | None = None,
    state_root: Path | None = None,
) -> dict[str, Any]:
    verify_codex_boundary(plugin_root)
    with tempfile.TemporaryDirectory(prefix="speckit-sweep-codex-") as temporary:
        runtime_root = Path(temporary) / "runtime"
        runtime_root.mkdir(mode=0o700)
        output_path = Path(temporary) / "receipt.json"
        session = SweepSession.open(session_id, state_root=state_root)
        capability = session.issue_capability(
            comment_id,
            stage=stage,
            perspective=perspective,
        )
        command = codex_command(
            plugin_root=plugin_root,
            repo_root=repo_root,
            runtime_root=runtime_root,
            capability=capability,
            stage=stage,
            perspective=perspective,
            state_root=state_root,
            output_path=output_path,
        )
        candidate = shutil.which("codex")
        executable = _trusted_executable(candidate, "Codex")
        if executable != Path(command[0]):
            raise LauncherViolation("Codex runtime changed after boundary attestation")
        candidate = shutil.which("codex", path=str(executable.parent))
        if _trusted_executable(candidate, "Codex") != executable:
            raise LauncherViolation("Codex runtime changed after boundary attestation")
        arguments = [candidate, *command[1:]]
        try:
            completed = subprocess.run(
                arguments,
                cwd=runtime_root,
                text=True,
                capture_output=True,
                check=False,
                timeout=300,
                shell=False,
                env=os.environ.copy(),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise LauncherViolation("isolated Codex sweep invocation failed") from exc
        if completed.returncode != 0:
            raise LauncherViolation("isolated Codex sweep invocation returned a failure")
        verify_codex_event_trace(completed.stdout, stage=stage)
        try:
            parsed = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LauncherViolation("isolated Codex sweep returned no schema-valid receipt") from exc
        if not isinstance(parsed, dict) or set(parsed) != {"receipt"}:
            raise LauncherViolation("isolated Codex sweep output contains non-receipt fields")
        receipt = parsed["receipt"]
        if not isinstance(receipt, str) or RECEIPT_RE.fullmatch(receipt) is None:
            raise LauncherViolation("isolated Codex sweep output is not a receipt")
        if stage == "synthesis":
            projection = {"comment_id": comment_id, "stage": stage, "status": "receipt_ready"}
        else:
            projection = session.accept_receipt(receipt, expected_stage=stage)
        return {"receipt": receipt, **projection}


def _claude_version() -> tuple[int, int, int]:
    candidate = shutil.which("claude")
    _trusted_executable(candidate, "Claude Code")
    try:
        completed = subprocess.run(
            [candidate, "--version"],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LauncherViolation("Claude Code is unavailable; install Claude Code 2.1.245 or newer") from exc
    match = CLAUDE_VERSION_RE.search(completed.stdout + completed.stderr)
    if completed.returncode != 0 or match is None:
        raise LauncherViolation("Claude Code version could not be verified")
    return tuple(int(value) for value in match.groups())


def claude_attestation_root() -> Path:
    uid = getattr(os, "getuid", lambda: 0)()
    return Path(tempfile.gettempdir()) / f"speckit-pro-sweep-hooks-{uid}"


def claude_attestation_path(repo_root: Path) -> Path:
    digest = hashlib.sha256(str(repo_root.resolve(strict=False)).encode("utf-8")).hexdigest()
    return claude_attestation_root() / f"{digest}.json"


def verify_claude_attestation(repo_root: Path, plugin_root: Path, *, max_age_seconds: int = 24 * 60 * 60) -> None:
    path = claude_attestation_path(repo_root)
    fd = -1
    try:
        root_info = path.parent.lstat()
        uid = getattr(os, "getuid", lambda: root_info.st_uid)()
        if (
            stat.S_ISLNK(root_info.st_mode)
            or not stat.S_ISDIR(root_info.st_mode)
            or root_info.st_uid != uid
            or stat.S_IMODE(root_info.st_mode) & 0o077
        ):
            raise OSError("unsafe Claude hook attestation directory")
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != uid
            or stat.S_IMODE(info.st_mode) & 0o077
            or info.st_size > 16 * 1024
        ):
            raise OSError("unsafe Claude hook attestation record")
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            fd = -1
            record = json.load(handle)
        hooks_sha256 = hashlib.sha256((plugin_root / "hooks" / "hooks.json").read_bytes()).hexdigest()
        hook_script_sha256 = hashlib.sha256(
            (plugin_root / "scripts" / "sweep-isolation-hook.py").read_bytes()
        ).hexdigest()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise LauncherViolation("Claude sweep hook attestation is unavailable; enable and trust plugin hooks") from exc
    finally:
        if fd >= 0:
            os.close(fd)
    if (
        not isinstance(record, dict)
        or record.get("version") != HOOK_VERSION
        or record.get("hooks_sha256") != hooks_sha256
        or record.get("hook_script_sha256") != hook_script_sha256
        or record.get("repo_root") != str(repo_root.resolve(strict=False))
        or time.time() - float(record.get("created_at", 0)) > max_age_seconds
    ):
        raise LauncherViolation("Claude sweep hook attestation is stale or does not match this plugin build")


def verify_claude_boundary(repo_root: Path, plugin_root: Path) -> tuple[int, int, int]:
    """Attest Claude CLI controls and the privileged parent's loaded hooks."""
    version = _claude_version()
    if version < MINIMUM_CLAUDE_VERSION:
        raise LauncherViolation("Claude sweep isolation requires Claude Code 2.1.245 or newer")
    candidate = shutil.which("claude")
    _trusted_executable(candidate, "Claude Code")
    try:
        completed = subprocess.run(
            [candidate, "--help"],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LauncherViolation("Claude isolated-process controls could not be attested") from exc
    required_flags = {
        "--plugin-dir",
        "--setting-sources",
        "--no-session-persistence",
        "--tools",
        "--allowedTools",
        "--json-schema",
        "--output-format",
    }
    resources = (
        plugin_root / ".mcp.json",
        plugin_root / "agents/sweep-classifier.md",
        plugin_root / "agents/sweep-analyst.md",
        plugin_root / "hooks/hooks.json",
    )
    if (
        completed.returncode != 0
        or not required_flags.issubset(set((completed.stdout + completed.stderr).split()))
        or not all(path.is_file() for path in resources)
    ):
        raise LauncherViolation("Claude lacks the required isolated-process controls; upgrade Claude Code")
    verify_claude_attestation(repo_root, plugin_root)
    return version


def _run_claude_process(
    command: list[str], *, runtime_root: Path, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """Run only the isolated Claude child; kept narrow for deterministic tests."""
    candidate = shutil.which("claude")
    executable = _trusted_executable(candidate, "Claude Code")
    if executable != Path(command[0]):
        raise LauncherViolation("Claude runtime changed after boundary attestation")
    arguments = [candidate, *command[1:]]
    return subprocess.run(
        arguments,
        cwd=runtime_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=300,
        shell=False,
    )


def run_claude_sweep(
    *,
    plugin_root: Path,
    repo_root: Path,
    session_id: str,
    comment_id: str,
    stage: str,
    perspective: str | None = None,
    state_root: Path | None = None,
) -> dict[str, Any]:
    """Run one sweep call outside the privileged Claude orchestrator context."""
    verify_claude_boundary(repo_root, plugin_root)
    with tempfile.TemporaryDirectory(prefix="speckit-sweep-claude-") as temporary:
        runtime_root = Path(temporary) / "runtime"
        runtime_root.mkdir(mode=0o700)
        attestation = claude_attestation_path(runtime_root)
        session = SweepSession.open(session_id, state_root=state_root)
        capability = session.issue_capability(
            comment_id,
            stage=stage,
            perspective=perspective,
        )
        command = claude_command(
            plugin_root=plugin_root,
            stage=stage,
            perspective=perspective,
        )
        environment = os.environ.copy()
        environment["CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS"] = "1"
        environment["SPECKIT_SWEEP_CAPABILITY"] = capability
        environment["SPECKIT_SWEEP_STATE_ROOT"] = str(
            default_state_root() if state_root is None else state_root
        )
        try:
            completed = _run_claude_process(
                command,
                runtime_root=runtime_root,
                environment=environment,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise LauncherViolation("isolated Claude sweep invocation failed") from exc
        try:
            verify_claude_attestation(runtime_root, plugin_root, max_age_seconds=300)
            payload = json.loads(completed.stdout)
            structured = payload["structured_output"]
            if not isinstance(structured, dict) or set(structured) != {"receipt"}:
                raise TypeError("Claude structured output is not receipt-only")
            receipt = structured["receipt"]
            stats = payload["subagent_stats"]
        except (OSError, KeyError, AttributeError, TypeError, json.JSONDecodeError) as exc:
            raise LauncherViolation("isolated Claude sweep returned no receipt-only result") from exc
        finally:
            try:
                attestation.unlink()
            except FileNotFoundError:
                pass
        if (
            completed.returncode != 0
            or payload.get("is_error") is not False
            or payload.get("permission_denials")
            or not isinstance(stats, dict)
            or stats.get("spawned") != 1
            or stats.get("completed") != 1
            or stats.get("failed") != 0
            or RECEIPT_RE.fullmatch(receipt) is None
        ):
            raise LauncherViolation("isolated Claude sweep did not complete one receipt-only subagent")
        if stage == "synthesis":
            projection = {"comment_id": comment_id, "stage": stage, "status": "receipt_ready"}
        else:
            projection = session.accept_receipt(receipt, expected_stage=stage)
        return {"receipt": receipt, **projection}
