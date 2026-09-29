"""Codex isolation arguments shared by the Layer 2 and Layer 3 launchers.

Both layers start ``codex exec`` inside a staged fixture with the same host
skills, connected servers and features switched off. Keeping the feature list,
the skill and server override builders and the skill-root walk here stops the
two launchers from drifting apart.
"""
from __future__ import annotations

import json
import os
import pathlib
import stat
import subprocess
import sys
from typing import Mapping, Sequence

DISABLED_FEATURES = (
    "plugins", "apps", "browser_use", "computer_use", "hooks",
    "skill_mcp_dependency_install", "memories", "unbounded_connection_retries",
)


def canonical_skill_files(root: pathlib.Path) -> set[pathlib.Path]:
    """Enumerate one root, following symlinked directories without allowing cycles."""
    try:
        root_status = root.stat()
    except FileNotFoundError:
        return set()
    except OSError as exc:
        raise OSError(f"could not inspect Codex skill root {root}: {exc}") from exc
    if not stat.S_ISDIR(root_status.st_mode):
        raise ValueError(f"Codex skill root is not a directory: {root}")

    pending = [root.resolve(strict=True)]
    visited: set[tuple[int, int]] = set()
    skills: set[pathlib.Path] = set()
    while pending:
        directory = pending.pop()
        try:
            canonical_directory = directory.resolve(strict=True)
            directory_status = canonical_directory.stat()
            identity = (directory_status.st_dev, directory_status.st_ino)
            if identity in visited:
                continue
            visited.add(identity)
            with os.scandir(canonical_directory) as entries:
                children = list(entries)
        except OSError as exc:
            raise OSError(f"could not inspect Codex skill root {directory}: {exc}") from exc
        for entry in children:
            try:
                if entry.name == "SKILL.md":
                    if not entry.is_file(follow_symlinks=True):
                        raise ValueError(f"Codex skill path is not a file: {entry.path}")
                    skills.add(pathlib.Path(entry.path).resolve(strict=True))
                elif entry.is_dir(follow_symlinks=True):
                    pending.append(pathlib.Path(entry.path))
            except OSError as exc:
                raise OSError(f"could not inspect Codex skill path {entry.path}: {exc}") from exc
    return skills


def fixture_permission_args(
    profile: str,
    workspace: pathlib.Path,
    writable: Sequence[pathlib.Path] = (),
) -> list[str]:
    """Use the reviewed native fixture-only policy, without legacy sandbox flags."""
    resolved_workspace = workspace.resolve()
    grants = [f"{json.dumps(str(resolved_workspace))}=\"read\""]
    grants.extend(f"{json.dumps(str(path))}=\"write\"" for path in writable)
    filesystem = '{":root"="deny",":minimal"="read",' + ",".join(grants) + "}"
    return [
        "-c", f'default_permissions="{profile}"',
        "-c", f"permissions.{profile}.filesystem={filesystem}",
        "-c", f"permissions.{profile}.network.enabled=false",
        "-c", 'approval_policy="never"',
        "-c", "allow_login_shell=false",
    ]


def mcp_list_command(cli: str, permission_args: Sequence[str]) -> list[str]:
    """Build the local, non-initializing ``mcp list`` inventory command."""
    command = [cli, "mcp", "list", "--json"]
    for feature in DISABLED_FEATURES:
        command.extend(["--disable", feature])
    command.extend(["-c", 'web_search="disabled"', *permission_args])
    return command


def read_mcp_server_names(
    command: Sequence[str],
    *,
    cwd: pathlib.Path,
    env: Mapping[str, str],
    timeout: int,
    executable: str | None,
) -> tuple[str, ...]:
    """Read configured names locally; never initialize servers or retain their config."""
    try:
        completed = subprocess.run(
            list(command), cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=timeout, env=dict(env),
            executable=executable, shell=False, check=False,
        )
        if completed.returncode != 0:
            raise ValueError("Codex MCP inventory command failed")
        inventory = json.loads(completed.stdout)
        if not isinstance(inventory, list):
            raise ValueError("Codex MCP inventory is not a list")
        names = [item.get("name") if isinstance(item, dict) else None for item in inventory]
        if any(not isinstance(name, str) or not name.strip() for name in names):
            raise ValueError("Codex MCP inventory omitted a server name")
        if len(set(names)) != len(names):
            raise ValueError("Codex MCP inventory contains duplicate server names")
        return tuple(sorted(names))
    except (OSError, subprocess.TimeoutExpired, UnicodeError, json.JSONDecodeError) as exc:
        # Config values, endpoints and credential-bearing diagnostics are not evidence.
        raise ValueError("Codex MCP inventory could not be read locally") from exc


def skill_isolation_args(
    disabled_skills: Sequence[pathlib.Path],
    disabled_mcp_servers: Sequence[str] = (),
    *,
    ignore_user_config: bool = True,
) -> list[str]:
    """Build process-local session overrides without mutating saved configuration."""
    entries = ",".join(
        f"{{path={json.dumps(str(path))},enabled=false}}"
        for path in disabled_skills
    )
    args = [
        "--disable", "plugins",
        "-c", "skills.bundled.enabled=false",
        "-c", f"skills.config=[{entries}]",
    ]
    for feature in DISABLED_FEATURES[1:]:
        args.extend(["--disable", feature])
    # Even disabled entries need a transport when exec ignores user config.
    # A TOML table preserves exact names; the CLI does not unquote dotted -c keys.
    # No original endpoints or credentials are copied into these disabled entries.
    # Diagnostics load user config: do not mix a local transport into an existing
    # HTTP transport. They prove disabled entries, not exec's effective registry.
    disabled_entry = (
        f'{{enabled=false,command={json.dumps(sys.executable)},args=["-c","raise SystemExit(1)"]}}'
        if ignore_user_config else "{enabled=false}"
    )
    servers = ",".join(f"{json.dumps(name)}={disabled_entry}" for name in disabled_mcp_servers)
    args.extend(["-c", f"mcp_servers={{{servers}}}", "-c", 'web_search="disabled"'])
    return args
