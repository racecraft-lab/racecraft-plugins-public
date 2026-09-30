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


def toml_inline_table(values: dict[str, str]) -> str:
    return "{" + ",".join(f"{key}={toml_string(value)}" for key, value in values.items()) + "}"


def toml_string_map(values: dict[str, str]) -> str:
    return "{" + ",".join(f"{toml_string(key)}={toml_string(value)}" for key, value in values.items()) + "}"


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


def codex_broker_command(
    *,
    codex_runtime: Path,
    python_runtime: Path,
    runtime_root: Path,
    server: str,
    broker_module: str,
    broker_env: dict[str, str],
    enabled_tools: Sequence[str],
    output_schema: Path,
    prompt: str,
    output_path: Path | None = None,
) -> list[str]:
    """Build one user-config-free ``codex exec`` that reaches only ``server``.

    The permission profile reads only the Codex and Python runtimes and the
    empty runtime directory, disables the network, and approves exactly the
    ``enabled_tools`` of the one broker.
    """
    profile = f"{server}-only"
    isolated_runtime_root = runtime_root.resolve(strict=False)
    filesystem = {
        ":minimal": "read",
        str(codex_runtime.parent.parent): "read",
        str(Path(sys.base_prefix).resolve(strict=True)): "read",
        str(isolated_runtime_root): "read",
    }
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
        str(output_schema),
        "-C",
        str(isolated_runtime_root),
        "-c",
        f'default_permissions="{profile}"',
        "-c",
        f"permissions.{profile}.filesystem={toml_string_map(filesystem)}",
        "-c",
        f"permissions.{profile}.network.enabled=false",
        "-c",
        'web_search="disabled"',
        "-c",
        f"mcp_servers.{server}.command={toml_string(str(python_runtime))}",
        "-c",
        f"mcp_servers.{server}.args={toml_array(['-m', broker_module])}",
        "-c",
        f"mcp_servers.{server}.env={toml_inline_table(broker_env)}",
        "-c",
        f"mcp_servers.{server}.enabled=true",
        "-c",
        f"mcp_servers.{server}.required=true",
        "-c",
        f"mcp_servers.{server}.enabled_tools={toml_array(enabled_tools)}",
        "-c",
        f'mcp_servers.{server}.default_tools_approval_mode="approve"',
    ]
    for feature in CODEX_DISABLED_FEATURES:
        command.extend(("--disable", feature))
    if output_path is not None:
        command.extend(("--output-last-message", str(output_path)))
    command.append(prompt)
    return command
