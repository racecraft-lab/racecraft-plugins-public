"""Shared building blocks for the isolated ``codex exec`` launchers.

The feedback sweep and the artifact preview each run one model call in a Codex
process that reaches exactly one broker and nothing else. They share the
runtime attestation, the prompt-resource resolver, and the command shape; each
launcher supplies only its broker, its tools, its schema, and its prompt.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


# Every Codex feature that could reach beyond the one configured broker.
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


class LauncherViolation(RuntimeError):
    """An isolated model process or security prerequisite failed closed."""


def trusted_executable(candidate: str | None, label: str) -> Path:
    """Resolve an absolute, regular, executable file that no one else may write."""
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
    return trusted_executable(shutil.which("codex"), "Codex")


def python_executable() -> Path:
    """Resolve the exact interpreter used for the packaged broker."""
    return trusted_executable(sys.executable, "Python")


def toml_string(value: str) -> str:
    return json.dumps(value)


def toml_array(values: Sequence[str]) -> str:
    return "[" + ",".join(toml_string(value) for value in values) + "]"


def toml_table(values: dict[str, str], *, quote_keys: bool = False) -> str:
    """One TOML inline table; ``quote_keys`` for keys such as paths that are not bare words."""
    key = toml_string if quote_keys else str
    return "{" + ",".join(f"{key(name)}={toml_string(value)}" for name, value in values.items()) + "}"


def trusted_prompt_resource(plugin_root: Path, relative: Path, label: str) -> Path:
    """Resolve one trusted prompt from exactly one supported plugin layout.

    A source checkout keeps Codex-only prompts under ``codex-skills``; a built
    payload moves them under ``skills``. Exactly one regular file must exist.
    """
    regular: list[Path] = []
    for candidate in (plugin_root / "codex-skills" / relative, plugin_root / "skills" / relative):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise LauncherViolation(f"trusted Codex {label} prompt cannot be attested") from exc
        if stat.S_ISREG(info.st_mode):
            regular.append(candidate)
    if len(regular) != 1:
        raise LauncherViolation(f"trusted Codex {label} prompt layout is unavailable or ambiguous")
    return regular[0]


@dataclass(frozen=True)
class CodexBroker:
    """The one MCP broker an isolated Codex process may reach, and its result schema."""

    server: str
    module: str
    env: dict[str, str]
    tools: Sequence[str]
    output_schema: Path


@dataclass(frozen=True)
class CodexRuntimes:
    """The attested Codex CLI and the interpreter that runs the broker."""

    codex: Path
    python: Path


def _permission_args(profile: str, runtimes: CodexRuntimes, runtime_root: Path) -> list[str]:
    """A profile that reads only the two runtimes and the empty runtime directory, offline."""
    filesystem = {
        ":minimal": "read",
        str(runtimes.codex.parent.parent): "read",
        str(Path(sys.base_prefix).resolve(strict=True)): "read",
        str(runtime_root): "read",
    }
    return [
        "-c",
        f'default_permissions="{profile}"',
        "-c",
        f"permissions.{profile}.filesystem={toml_table(filesystem, quote_keys=True)}",
        "-c",
        f"permissions.{profile}.network.enabled=false",
        "-c",
        'web_search="disabled"',
    ]


def _broker_args(broker: CodexBroker, python_runtime: Path) -> list[str]:
    """Register the one required broker and approve exactly its tools."""
    prefix = f"mcp_servers.{broker.server}"
    settings = (
        f"command={toml_string(str(python_runtime))}",
        f"args={toml_array(['-m', broker.module])}",
        f"env={toml_table(broker.env)}",
        "enabled=true",
        "required=true",
        f"enabled_tools={toml_array(broker.tools)}",
        'default_tools_approval_mode="approve"',
    )
    return [argument for setting in settings for argument in ("-c", f"{prefix}.{setting}")]


def codex_broker_command(
    broker: CodexBroker,
    runtimes: CodexRuntimes,
    runtime_root: Path,
    prompt: str,
    output_path: Path | None = None,
) -> list[str]:
    """Build one user-config-free ``codex exec`` that reaches only ``broker``."""
    isolated_runtime_root = runtime_root.resolve(strict=False)
    command = [
        str(runtimes.codex),
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
        str(broker.output_schema),
        "-C",
        str(isolated_runtime_root),
        *_permission_args(f"{broker.server}-only", runtimes, isolated_runtime_root),
        *_broker_args(broker, runtimes.python),
    ]
    for feature in CODEX_DISABLED_FEATURES:
        command.extend(("--disable", feature))
    if output_path is not None:
        command.extend(("--output-last-message", str(output_path)))
    command.append(prompt)
    return command
