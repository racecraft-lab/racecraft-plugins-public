"""Codex host adapter: trial staging, protected runtimes and isolation proofs.

Prepares a Codex project-mode trial, stages the protected git and Python
runtimes, and qualifies the sandbox profile with local probes before any
model launch.
"""

from __future__ import annotations

import ast
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Mapping
import uuid

import native_eval_adapter_common as adapter_common
import native_eval_fixture_setup as fixture_setup
import native_eval_git_observation
import native_eval_runtime
import native_eval_strict_json as strict_json
import native_eval_toolchain
import native_eval_upstream
import native_eval_verification


_CODEX_SKILL_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
_PROTECTED_GIT_SCHEMA_VERSION = "native-eval-protected-git/v1"
_CODEX_GIT_SUBJECT_ENVIRONMENT_SCHEMA_VERSION = "native-eval-git-subject-environment/v2"
_PYTHON_RUNTIME_SCHEMA_VERSION = "native-eval-python-runtime/v1"
_CODEX_PROJECT_CONFIG = "[agents]\nenabled = true\n"
_CODEX_READ_TOOLS = frozenset({
    "read_file", "list_files", "search_files", "read", "glob", "grep", "Read", "Glob", "Grep",
})
_CODEX_WRITE_TOOLS = frozenset({
    "write_file", "edit_file", "apply_patch", "shell", "command_execution", "file_change",
    "Write", "Edit", "Bash",
})
_CODEX_SUBAGENT_TOOLS = frozenset({
    "collaboration", "collab_tool_call", "spawn_agent", "send_input", "Agent", "Task",
})
_CODEX_HELPERS: object | None = None
_ISOLATION_CONTROL = b"native-eval-isolation-control/v1\n"
_ISOLATION_DENIAL = re.compile(
    rb"(?:operation not permitted|permission denied|access is denied)", re.IGNORECASE,
)


def _codex_helpers() -> object:
    global _CODEX_HELPERS
    if _CODEX_HELPERS is not None:
        return _CODEX_HELPERS
    path = Path(__file__).resolve().parents[1] / "layer2-trigger" / "run_codex_evals.py"
    spec = importlib.util.spec_from_file_location("native_eval_codex_helpers", path)
    if spec is None or spec.loader is None:
        raise adapter_common.NativeAdapterError("Codex isolation helpers are unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _CODEX_HELPERS = module
    return module


def _codex_skill_name(value: str) -> str:
    adapter_common._require(isinstance(value, str) and bool(value.strip()), "Codex project skill is malformed")
    name = value.rsplit(":", 1)[-1].lstrip("$")
    adapter_common._require(_CODEX_SKILL_NAME.fullmatch(name) is not None, "Codex project skill is malformed")
    return name


def _codex_native_skill_reference(payload_root: Path, skill_name: str) -> str:
    """Return the exact plugin-qualified name exposed by the staged runtime."""
    manifest = payload_root / ".codex-plugin" / "plugin.json"
    try:
        metadata = manifest.lstat()
        parsed = strict_json.loads(manifest.read_bytes(), error=ValueError)
    except (OSError, ValueError) as exc:
        raise adapter_common.NativeAdapterError("staged Codex plugin manifest is unavailable") from exc
    adapter_common._require(stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode),
             "staged Codex plugin manifest must be a regular file")
    plugin_name = parsed.get("name") if isinstance(parsed, dict) else None
    adapter_common._require(isinstance(plugin_name, str)
             and _CODEX_SKILL_NAME.fullmatch(plugin_name) is not None,
             "staged Codex plugin name is malformed")
    return f"${plugin_name}:{skill_name}"


def _codex_skill_read_witnesses(skill_root: Path) -> dict[str, dict[str, object]]:
    """Freeze exact staged Codex SKILL.md bytes for later native-read qualification."""
    try:
        root_status = skill_root.lstat()
        entries = sorted(skill_root.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        raise adapter_common.NativeAdapterError("staged Codex skill catalog cannot be inspected") from exc
    adapter_common._require(stat.S_ISDIR(root_status.st_mode) and not stat.S_ISLNK(root_status.st_mode),
             "staged Codex skill catalog must be a regular directory")
    witnesses: dict[str, dict[str, object]] = {}
    for entry in entries:
        try:
            entry_status = entry.lstat()
        except OSError as exc:
            raise adapter_common.NativeAdapterError(f"staged Codex skill cannot be inspected: {entry.name}") from exc
        adapter_common._require(stat.S_ISDIR(entry_status.st_mode) and not stat.S_ISLNK(entry_status.st_mode),
                 f"staged Codex skill entry is not a regular directory: {entry.name}")
        name = _codex_skill_name(entry.name)
        adapter_common._require(name == entry.name and name not in witnesses,
                 f"staged Codex skill name is not canonical: {entry.name}")
        skill_file = entry / "SKILL.md"
        try:
            file_status = skill_file.lstat()
        except OSError as exc:
            raise adapter_common.NativeAdapterError(f"staged Codex skill body cannot be read: {name}") from exc
        adapter_common._require(stat.S_ISREG(file_status.st_mode) and not stat.S_ISLNK(file_status.st_mode),
                 f"staged Codex skill body is not a regular file: {name}")
        try:
            payload = skill_file.read_bytes()
        except OSError as exc:
            raise adapter_common.NativeAdapterError(f"staged Codex skill body cannot be read: {name}") from exc
        try:
            text = payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise adapter_common.NativeAdapterError(f"staged Codex skill body is not UTF-8: {name}") from exc
        witnesses[name] = {
            "path": f".agents/skills/{name}/SKILL.md",
            "text": text,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    adapter_common._require(bool(witnesses), "staged Codex skill catalog is empty")
    return witnesses


def _codex_git_subject_environment(
    workspace: Path,
) -> tuple[dict[str, str], dict[str, object]]:
    """Create deterministic subject Git identity without consulting ambient config."""
    config_relative = ".codex/native-eval-git-global.config"
    hooks_relative = ".codex/native-eval-git-hooks"
    temporary_relative = ".native-eval-tmp"
    config = workspace / config_relative
    hooks = workspace / hooks_relative
    temporary = workspace / temporary_relative
    adapter_common._write_text(config, "")
    hooks.mkdir(mode=0o700)
    temporary.mkdir(mode=0o700)
    temporary_status = temporary.lstat()
    adapter_common._require(stat.S_ISDIR(temporary_status.st_mode)
             and not stat.S_ISLNK(temporary_status.st_mode)
             and stat.S_IMODE(temporary_status.st_mode) == 0o700,
             "Codex Git temporary directory is unsafe")
    values = {
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": str(config),
        "GIT_CONFIG_COUNT": "3",
        "GIT_CONFIG_KEY_0": "core.hooksPath",
        "GIT_CONFIG_VALUE_0": str(hooks),
        "GIT_CONFIG_KEY_1": "commit.gpgSign",
        "GIT_CONFIG_VALUE_1": "false",
        "GIT_CONFIG_KEY_2": "tag.gpgSign",
        "GIT_CONFIG_VALUE_2": "false",
        "GIT_AUTHOR_NAME": "Native Eval Subject",
        "GIT_AUTHOR_EMAIL": "native-eval@example.invalid",
        "GIT_COMMITTER_NAME": "Native Eval Subject",
        "GIT_COMMITTER_EMAIL": "native-eval@example.invalid",
        "GIT_AUTHOR_DATE": "2000-01-02T00:00:00 +0000",
        "GIT_COMMITTER_DATE": "2000-01-02T00:00:00 +0000",
        "GIT_TERMINAL_PROMPT": "0",
        "TMPDIR": str(temporary),
        "TMP": str(temporary),
        "TEMP": str(temporary),
    }
    identity_values = dict(values)
    identity_values["GIT_CONFIG_GLOBAL"] = config_relative
    identity_values["GIT_CONFIG_VALUE_0"] = hooks_relative
    for name in ("TMPDIR", "TMP", "TEMP"):
        identity_values[name] = temporary_relative
    identity: dict[str, object] = {
        "schema_version": _CODEX_GIT_SUBJECT_ENVIRONMENT_SCHEMA_VERSION,
        "environment": identity_values,
        "global_config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
        "hooks_directory": hooks_relative,
        "temporary_directory": {
            "path": temporary_relative,
            "mode": 0o700,
            "uid": temporary_status.st_uid,
        },
    }
    return values, identity


def _codex_protected_git_required(case: Mapping[str, object]) -> bool:
    """Select protected Git only for repository-aware native contracts."""
    if isinstance(case.get("git_fixture"), Mapping):
        return True
    checks = case.get("checks")
    return isinstance(checks, list) and any(
        isinstance(check, Mapping)
        and check.get("type") in {"native_runner_result", "native_git_final_state"}
        for check in checks
    )


def _instruction_candidates(root: Path) -> dict[str, object]:
    """Fingerprint every file that can win Codex instruction precedence."""
    candidates: list[dict[str, object]] = []
    selected: str | None = None
    for name in ("AGENTS.override.md", "AGENTS.md"):
        path = root / name
        try:
            status = path.lstat()
        except FileNotFoundError:
            candidates.append({"name": name, "state": "missing"})
            continue
        adapter_common._require(stat.S_ISREG(status.st_mode) or stat.S_ISLNK(status.st_mode),
                 f"Codex instruction candidate is not a regular file: {path}")
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise adapter_common.NativeAdapterError(f"Codex instruction candidate cannot be read: {path}") from exc
        entry: dict[str, object] = {
            "name": name,
            "state": "symlink" if stat.S_ISLNK(status.st_mode) else "file",
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        if stat.S_ISLNK(status.st_mode):
            entry["link_target_sha256"] = hashlib.sha256(os.readlink(path).encode("utf-8")).hexdigest()
        candidates.append(entry)
        if selected is None and payload:
            selected = name
            break
    return {"root": root.name, "selected": selected, "candidates": candidates}


def _codex_instruction_inputs(
    environment: Mapping[str, str], workspace: Path, *, parent_traversal_disabled: bool = False,
) -> dict[str, object]:
    codex_home_value = environment.get("CODEX_HOME")
    adapter_common._require(isinstance(codex_home_value, str) and bool(codex_home_value),
             "Codex home is unavailable for instruction fingerprinting")
    codex_home = Path(codex_home_value)
    adapter_common._require(codex_home.is_absolute(), "Codex home must be absolute for instruction fingerprinting")
    return {
        "global": _instruction_candidates(codex_home),
        "project": _instruction_candidates(workspace),
        "discovery_scope": (
            "global Codex home plus exact current directory; parent traversal disabled"
            if parent_traversal_disabled
            else "global Codex home plus non-git current directory"
        ),
    }


def _codex_permission_args(
    workspace: Path, environment: Mapping[str, str], filesystem_access: str, permission_name: str,
    *, forwarded_environment: tuple[str, ...] = (), runtime_read_roots: tuple[Path, ...] = (),
    runtime_write_roots: tuple[Path, ...] = (),
    git_metadata_access: str | None = None,
) -> list[str]:
    adapter_common._require(filesystem_access in {"read", "write"}, "Codex filesystem access is unsupported")
    adapter_common._require(git_metadata_access in {None, "write"},
             "Codex Git metadata access is unsupported")
    adapter_common._require(git_metadata_access is None or filesystem_access == "write",
             "Codex Git metadata write requires workspace write access")
    workspace_value = str(workspace.resolve())
    entries = {
        ":root": "deny", ":minimal": "read", workspace_value: filesystem_access,
        f"{workspace_value}/.agents": "read", f"{workspace_value}/.codex": "read",
        f"{workspace_value}/.git": git_metadata_access or "read",
    }
    for runtime_root in runtime_read_roots:
        runtime_value = str(runtime_root)
        adapter_common._require(runtime_root.is_absolute() and runtime_value != "/"
                 and runtime_value not in entries,
                 "Codex runtime read root is malformed")
        entries[runtime_value] = "read"
    for runtime_root in runtime_write_roots:
        runtime_value = str(runtime_root)
        adapter_common._require(runtime_root.is_absolute() and runtime_root.is_relative_to(workspace)
                 and runtime_root != workspace and runtime_value not in entries,
                 "Codex runtime write root is malformed")
        entries[runtime_value] = "write"
    filesystem = "{" + ",".join(
        f"{json.dumps(path)}={json.dumps(access)}" for path, access in entries.items()
    ) + "}"
    shell_environment = "{PATH=" + json.dumps(environment.get("PATH", ""))
    adapter_common._require(len(forwarded_environment) == len(set(forwarded_environment))
             and all(re.fullmatch(r"[A-Z][A-Z0-9_]*", name) for name in forwarded_environment),
             "Codex forwarded environment names are malformed")
    for name in forwarded_environment:
        value = environment.get(name)
        adapter_common._require(isinstance(value, str), f"Codex forwarded environment value is absent: {name}")
        shell_environment += f",{name}=" + json.dumps(value)
    shell_environment += "}"
    return [
        "--config", f'default_permissions="{permission_name}"',
        "--config", f"permissions.{permission_name}.filesystem={filesystem}",
        "--config", f"permissions.{permission_name}.network.enabled=false",
        "--config", 'approval_policy="never"',
        "--config", "allow_login_shell=false",
        "--config", 'shell_environment_policy.inherit="none"',
        "--config", "shell_environment_policy.set=" + shell_environment,
    ]


def _protected_python_runtime() -> tuple[Path, dict[str, object]]:
    """Resolve the active Python 3.11+ and its exact ``python3`` PATH entry."""
    try:
        executable = Path(sys.executable).resolve(strict=True)
        status = executable.lstat()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("protected Python runtime is unavailable") from exc
    owner = getattr(os, "getuid", lambda: status.st_uid)()
    writable_mask = stat.S_IWGRP | stat.S_IWOTH
    adapter_common._require(stat.S_ISREG(status.st_mode) and os.access(executable, os.X_OK)
             and status.st_uid in {0, owner} and not status.st_mode & writable_mask,
             "protected Python runtime ownership or mode is unsafe")
    adapter_common._require(sys.version_info[:2] >= (3, 11),
             "protected Python runtime must be Python 3.11 or newer")
    directory = executable.parent
    runtime_root = directory.parent
    try:
        directory_status = directory.lstat()
        runtime_root_status = runtime_root.lstat()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("protected Python command directory is unavailable") from exc
    adapter_common._require(stat.S_ISDIR(directory_status.st_mode) and not stat.S_ISLNK(directory_status.st_mode)
             and directory_status.st_uid in {0, owner}
             and not directory_status.st_mode & writable_mask,
             "protected Python command directory ownership or mode is unsafe")
    adapter_common._require(stat.S_ISDIR(runtime_root_status.st_mode)
             and not stat.S_ISLNK(runtime_root_status.st_mode)
             and runtime_root_status.st_uid in {0, owner}
             and not runtime_root_status.st_mode & writable_mask,
             "protected Python runtime root ownership or mode is unsafe")
    python3 = executable.parent / "python3"
    try:
        python3_status = python3.lstat()
        resolved_python3 = python3.resolve(strict=True)
    except OSError as exc:
        raise adapter_common.NativeAdapterError("protected Python runtime has no python3 command") from exc
    safe_python3_mode = (
        stat.S_ISLNK(python3_status.st_mode)
        or stat.S_ISREG(python3_status.st_mode) and not python3_status.st_mode & writable_mask
    )
    adapter_common._require((stat.S_ISREG(python3_status.st_mode) or stat.S_ISLNK(python3_status.st_mode))
             and python3_status.st_uid in {0, owner} and safe_python3_mode
             and resolved_python3 == executable and os.access(python3, os.X_OK),
             "protected python3 command does not resolve to the active Python runtime")
    try:
        payload = executable.read_bytes()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("protected Python runtime bytes cannot be read") from exc
    identity: dict[str, object] = {
        "schema_version": _PYTHON_RUNTIME_SCHEMA_VERSION,
        "executable": str(executable),
        "python3_command": "python3",
        "python3_path": str(python3),
        "python3_kind": "symlink" if stat.S_ISLNK(python3_status.st_mode) else "file",
        "python3_link_target": os.readlink(python3) if stat.S_ISLNK(python3_status.st_mode) else None,
        "version": list(sys.version_info[:3]),
        "implementation": sys.implementation.name,
        "executable_owner": status.st_uid,
        "executable_mode": stat.S_IMODE(status.st_mode),
        "directory_owner": directory_status.st_uid,
        "directory_mode": stat.S_IMODE(directory_status.st_mode),
        "runtime_root": str(runtime_root),
        "runtime_root_owner": runtime_root_status.st_uid,
        "runtime_root_mode": stat.S_IMODE(runtime_root_status.st_mode),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    return executable, identity


def _protected_git_source() -> tuple[Path, Path, dict[str, object]]:
    """Resolve a real Git binary and its exact helper directory without a shim."""
    discovered = shutil.which("git")
    adapter_common._require(isinstance(discovered, str) and bool(discovered),
             "protected Git runtime is unavailable")
    try:
        candidate = Path(discovered).resolve(strict=True)
    except OSError as exc:
        raise adapter_common.NativeAdapterError("protected Git runtime is unavailable") from exc

    error = "protected Git runtime could not be established"
    exec_path = Path(adapter_common._probe_executable_output(str(candidate), "--exec-path", error))
    adapter_common._require(exec_path.is_absolute(), "protected Git exec path is not absolute")
    try:
        exec_path = exec_path.resolve(strict=True)
    except OSError as exc:
        raise adapter_common.NativeAdapterError("protected Git exec path is unavailable") from exc
    direct_candidate = exec_path.parent.parent / "bin" / "git"
    source = direct_candidate if direct_candidate.is_file() else candidate
    try:
        source = source.resolve(strict=True)
        source_status = source.lstat()
        exec_path_status = exec_path.lstat()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("protected Git runtime is unavailable") from exc
    owner = getattr(os, "getuid", lambda: source_status.st_uid)()
    writable_mask = stat.S_IWGRP | stat.S_IWOTH
    adapter_common._require(stat.S_ISREG(source_status.st_mode) and os.access(source, os.X_OK)
             and source_status.st_uid in {0, owner}
             and not source_status.st_mode & writable_mask,
             "protected Git executable ownership or mode is unsafe")
    adapter_common._require(stat.S_ISDIR(exec_path_status.st_mode) and not stat.S_ISLNK(exec_path_status.st_mode)
             and exec_path_status.st_uid in {0, owner}
             and not exec_path_status.st_mode & writable_mask,
             "protected Git exec path ownership or mode is unsafe")
    adapter_common._require(Path(adapter_common._probe_executable_output(str(source), "--exec-path", error)
                  ).resolve(strict=True) == exec_path,
             "protected Git executable does not use the pinned exec path")
    version = adapter_common._probe_executable_output(str(source), "--version", error)
    try:
        payload = source.read_bytes()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("protected Git executable bytes cannot be read") from exc
    identity: dict[str, object] = {
        "schema_version": _PROTECTED_GIT_SCHEMA_VERSION,
        "source_executable": str(source),
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "source_owner": source_status.st_uid,
        "source_mode": stat.S_IMODE(source_status.st_mode),
        "exec_path": str(exec_path),
        "exec_path_owner": exec_path_status.st_uid,
        "exec_path_mode": stat.S_IMODE(exec_path_status.st_mode),
        "version": version,
    }
    return source, exec_path, identity


def _stage_protected_git(workspace: Path) -> tuple[Path, Path, dict[str, object]]:
    source, exec_path, identity = _protected_git_source()
    relative = PurePosixPath(".codex", "native-eval-git-bin", "git")
    launcher = workspace.joinpath(*relative.parts)
    adapter_common._require(not launcher.exists() and not launcher.is_symlink(),
             "protected Git launcher already exists")
    launcher.parent.mkdir(mode=0o700)
    try:
        shutil.copyfile(source, launcher)
        launcher.chmod(0o500)
        staged_status = launcher.lstat()
        staged_payload = launcher.read_bytes()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("protected Git launcher could not be staged") from exc
    adapter_common._require(stat.S_ISREG(staged_status.st_mode) and not stat.S_ISLNK(staged_status.st_mode)
             and staged_status.st_nlink == 1 and stat.S_IMODE(staged_status.st_mode) == 0o500
             and os.access(launcher, os.X_OK)
             and hashlib.sha256(staged_payload).hexdigest() == identity["source_sha256"],
             "protected Git launcher is unsafe")
    return launcher, exec_path, {
        **identity,
        "launcher_relative": relative.as_posix(),
        "launcher_mode": 0o500,
    }


def _verify_protected_git(workspace: Path, identity: object) -> None:
    adapter_common._require(isinstance(identity, dict) and set(identity) == {
        "schema_version", "source_executable", "source_sha256", "source_owner",
        "source_mode", "exec_path", "exec_path_owner", "exec_path_mode", "version",
        "launcher_relative", "launcher_mode",
    }, "prepared protected Git identity is malformed")
    source = Path(identity["source_executable"])
    exec_path = Path(identity["exec_path"])
    try:
        source_status = source.lstat()
        exec_path_status = exec_path.lstat()
        source_payload = source.read_bytes()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("prepared protected Git source is unavailable") from exc
    adapter_common._require(stat.S_ISREG(source_status.st_mode) and os.access(source, os.X_OK)
             and source_status.st_uid == identity["source_owner"]
             and stat.S_IMODE(source_status.st_mode) == identity["source_mode"]
             and hashlib.sha256(source_payload).hexdigest() == identity["source_sha256"]
             and stat.S_ISDIR(exec_path_status.st_mode)
             and not stat.S_ISLNK(exec_path_status.st_mode)
             and exec_path_status.st_uid == identity["exec_path_owner"]
             and stat.S_IMODE(exec_path_status.st_mode) == identity["exec_path_mode"]
             and identity["launcher_relative"] == ".codex/native-eval-git-bin/git"
             and identity["launcher_mode"] == 0o500,
             "prepared protected Git source changed after admission")
    launcher = workspace.joinpath(*PurePosixPath(identity["launcher_relative"]).parts)
    try:
        status = launcher.lstat()
        payload = launcher.read_bytes()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("prepared protected Git launcher is unavailable") from exc
    adapter_common._require(source.is_file() and exec_path.is_dir()
             and stat.S_ISREG(status.st_mode) and not stat.S_ISLNK(status.st_mode)
             and status.st_nlink == 1 and stat.S_IMODE(status.st_mode) == identity["launcher_mode"]
             and os.access(launcher, os.X_OK)
             and hashlib.sha256(payload).hexdigest() == identity["source_sha256"],
             "prepared protected Git launcher changed after admission")


def _verify_codex_git_subject_environment(
    prepared: adapter_common.PreparedTrial, settings: Mapping[str, object],
) -> None:
    git_subject = settings.get("git_subject_environment")
    adapter_common._require(isinstance(git_subject, dict) and set(git_subject) == {
        "schema_version", "environment", "global_config_sha256",
        "hooks_directory", "temporary_directory",
    } and git_subject.get("schema_version")
             == _CODEX_GIT_SUBJECT_ENVIRONMENT_SCHEMA_VERSION
             and isinstance(git_subject.get("environment"), dict)
             and git_subject.get("hooks_directory") == ".codex/native-eval-git-hooks",
             "prepared Git subject environment is malformed")
    expected_environment = dict(git_subject["environment"])
    expected_environment["GIT_CONFIG_GLOBAL"] = str(
        prepared.cwd / ".codex/native-eval-git-global.config"
    )
    expected_environment["GIT_CONFIG_VALUE_0"] = str(
        prepared.cwd / ".codex/native-eval-git-hooks"
    )
    for name in ("TMPDIR", "TMP", "TEMP"):
        expected_environment[name] = str(prepared.cwd / ".native-eval-tmp")
    expected_git_names = {
        name for name in expected_environment if name.startswith("GIT_")
    }
    expected_git_names.add("GIT_EXEC_PATH")
    mismatched = sorted(
        name for name, value in expected_environment.items()
        if prepared.environment.get(name) != value
    )
    unexpected_git = sorted(
        {name for name in prepared.environment if name.startswith("GIT_")}
        - expected_git_names
    )
    adapter_common._require(not mismatched and not unexpected_git,
             "prepared Git subject environment changed after admission: "
             + ", ".join([*mismatched, *unexpected_git]))
    config = prepared.cwd / ".codex/native-eval-git-global.config"
    hooks = prepared.cwd / ".codex/native-eval-git-hooks"
    temporary = prepared.cwd / ".native-eval-tmp"
    temporary_identity = git_subject.get("temporary_directory")
    try:
        temporary_status = temporary.lstat()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("prepared Git temporary directory is unavailable") from exc
    adapter_common._require(config.is_file() and not config.is_symlink()
             and hashlib.sha256(config.read_bytes()).hexdigest()
             == git_subject.get("global_config_sha256")
             and hooks.is_dir() and not hooks.is_symlink()
             and not any(hooks.iterdir())
             and temporary_identity == {
                 "path": ".native-eval-tmp", "mode": 0o700,
                 "uid": temporary_status.st_uid,
             }
             and stat.S_ISDIR(temporary_status.st_mode)
             and not stat.S_ISLNK(temporary_status.st_mode)
             and stat.S_IMODE(temporary_status.st_mode) == 0o700,
             "prepared Git subject controls changed after admission")


def _is_broad_temporary_root(path: Path) -> bool:
    candidates = {Path(tempfile.gettempdir())}
    if os.name == "posix":
        candidates.update({Path("/tmp"), Path("/private/tmp"), Path("/var/tmp"), Path("/private/var/tmp")})
    for candidate in candidates:
        try:
            temporary = candidate.resolve(strict=True)
        except OSError:
            continue
        if path == temporary or path.is_relative_to(temporary):
            return True
    return False


def _real_canonical_directory(path: Path, label: str) -> Path:
    adapter_common._require(path.is_absolute(), f"{label} must be absolute")
    try:
        status = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise adapter_common.NativeAdapterError(f"{label} is unavailable") from exc
    adapter_common._require(stat.S_ISDIR(status.st_mode) and not stat.S_ISLNK(status.st_mode),
             f"{label} must be a real directory")
    adapter_common._require(resolved == path, f"{label} must not contain symlink or noncanonical components")
    return resolved


def _run_codex_sandbox_probe(
    command: list[str], *, cwd: Path, environment: Mapping[str, str],
) -> subprocess.CompletedProcess[bytes]:
    """Run one provider-free command through the selected native Codex sandbox."""
    try:
        return subprocess.run(
            command, cwd=cwd, env=dict(environment), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise adapter_common.NativeAdapterError(f"Codex native sandbox probe could not start: {exc}") from exc


def _sandbox_probe_command(
    executable: str, permission_name: str, permission_args: list[str], workspace: Path,
    program: str, target: Path | None = None, *, arguments: tuple[str, ...] = (),
) -> list[str]:
    adapter_common._require((target is None) != (not arguments),
             "Codex native sandbox probe arguments are malformed")
    command_arguments = list(arguments) if target is None else ["--", str(target)]
    return [
        executable, "sandbox", "-P", permission_name, *permission_args,
        "-C", str(workspace), program, *command_arguments,
    ]


def _require_probe_result(
    completed: subprocess.CompletedProcess[bytes], *, label: str,
    expected_payload: bytes | None = None, expected_prefix: bytes | None = None,
    denied: bool = False,
) -> None:
    adapter_common._require(expected_payload is None or expected_prefix is None,
             f"Codex native sandbox {label} probe expectation is ambiguous")
    adapter_common._require(isinstance(completed, subprocess.CompletedProcess)
             and isinstance(completed.returncode, int)
             and isinstance(completed.stdout, bytes)
             and isinstance(completed.stderr, bytes),
             f"Codex native sandbox {label} probe returned malformed evidence")
    if (completed.returncode == 71 and
            b"sandbox-exec: sandbox_apply: Operation not permitted" in completed.stderr):
        raise adapter_common.NativeAdapterError(
            "Codex native sandbox cannot initialize inside an outer macOS sandbox; "
            "relaunch the native-eval controller outside the outer sandbox"
        )
    if denied:
        adapter_common._require(completed.returncode != 0 and not completed.stdout
                 and _ISOLATION_DENIAL.search(completed.stderr) is not None,
                 f"Codex native sandbox did not enforce {label} denial")
        return
    output_matches = (completed.stdout.startswith(expected_prefix)
                      if expected_prefix is not None else completed.stdout == expected_payload)
    adapter_common._require(completed.returncode == 0 and output_matches,
             f"Codex native sandbox failed the {label} control")


def _write_exclusive_probe(path: Path, payload: bytes) -> tuple[int, int, str]:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    adapter_common._require(nofollow != 0, "platform cannot safely qualify Codex native isolation")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow
    descriptor = os.open(path, flags, 0o600)
    try:
        written = os.write(descriptor, payload)
        adapter_common._require(written == len(payload), "native isolation probe write was incomplete")
        metadata = os.fstat(descriptor)
    except BaseException:
        try:
            path.unlink()
        except OSError as cleanup:
            raise adapter_common.NativeAdapterError("native isolation probe cleanup failed") from cleanup
        raise
    finally:
        os.close(descriptor)
    return metadata.st_dev, metadata.st_ino, hashlib.sha256(payload).hexdigest()


def _require_unchanged_probe(
    path: Path, expected: tuple[int, int, str], payload: bytes, label: str,
) -> None:
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0))
        metadata = os.fstat(descriptor)
        adapter_common._require(stat.S_ISREG(metadata.st_mode) and (metadata.st_dev, metadata.st_ino) == expected[:2],
                 f"Codex native sandbox {label} probe changed during qualification")
        observed = os.read(descriptor, len(payload) + 1)
    except OSError as exc:
        raise adapter_common.NativeAdapterError(f"Codex native sandbox {label} probe changed during qualification") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    adapter_common._require(observed == payload and hashlib.sha256(observed).hexdigest() == expected[2],
             f"Codex native sandbox {label} probe changed during qualification")


@contextmanager
def _temporary_isolation_probes(attempts: Path, staging: Path):
    private_payload = ("native-eval-private-" + uuid.uuid4().hex + "\n").encode("ascii")
    sibling_payload = ("native-eval-sibling-" + uuid.uuid4().hex + "\n").encode("ascii")
    private_probe = attempts / f".native-isolation-{uuid.uuid4().hex}"
    sibling_root = staging / f".native-isolation-{uuid.uuid4().hex}"
    sibling_workspace = sibling_root / "workspace"
    sibling_probe = sibling_workspace / "private.txt"
    created: list[tuple[Path, str]] = []
    try:
        private_identity = _write_exclusive_probe(private_probe, private_payload)
        created.append((private_probe, "file"))
        sibling_root.mkdir(mode=0o700)
        created.append((sibling_root, "directory"))
        sibling_workspace.mkdir(mode=0o700)
        created.append((sibling_workspace, "directory"))
        sibling_identity = _write_exclusive_probe(sibling_probe, sibling_payload)
        created.append((sibling_probe, "file"))
        yield (
            private_probe, private_payload, private_identity,
            sibling_probe, sibling_payload, sibling_identity,
        )
    finally:
        cleanup_errors: list[OSError] = []
        for path, kind in reversed(created):
            try:
                path.unlink() if kind == "file" else path.rmdir()
            except FileNotFoundError:
                pass
            except OSError as exc:
                cleanup_errors.append(exc)
        if cleanup_errors and sys.exc_info()[0] is None:
            raise adapter_common.NativeAdapterError("Codex native isolation probe cleanup failed") from cleanup_errors[0]


def _remove_exact_probe_entry(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    try:
        if stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode):
            path.rmdir()
        else:
            path.unlink()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("Codex native isolation write-probe cleanup failed") from exc


def _qualify_codex_git_metadata(
    *, executable: str, workspace: Path, environment: Mapping[str, str],
    permission_args: list[str], permission_name: str, filesystem_access: str,
    directory_maker: str, git_metadata_access: str | None,
) -> dict[str, str] | None:
    adapter_common._require(git_metadata_access in {None, "write"},
             "Codex Git metadata access is unsupported")
    adapter_common._require(git_metadata_access is None or filesystem_access == "write",
             "Codex Git metadata write requires workspace write access")
    git_metadata = workspace / ".git"
    if git_metadata_access == "write":
        try:
            git_metadata_status = git_metadata.lstat()
        except OSError as exc:
            raise adapter_common.NativeAdapterError("Codex Git metadata control is unavailable") from exc
        adapter_common._require(stat.S_ISDIR(git_metadata_status.st_mode)
                 and not stat.S_ISLNK(git_metadata_status.st_mode),
                 "Codex Git metadata control must be a directory")
    if not git_metadata.is_dir() or git_metadata.is_symlink():
        return None

    git_write = git_metadata / f".native-isolation-write-{uuid.uuid4().hex}"
    denied = git_metadata_access != "write"
    try:
        completed = _run_codex_sandbox_probe(
            _sandbox_probe_command(
                executable, permission_name, permission_args, workspace,
                directory_maker, git_write,
            ), cwd=workspace, environment=environment,
        )
        try:
            target_status = git_write.lstat()
        except FileNotFoundError:
            target_status = None
        if denied:
            _require_probe_result(completed, label="git-metadata-write", denied=True)
            adapter_common._require(target_status is None,
                     "Codex native sandbox created the denied git-metadata-write control")
        else:
            adapter_common._require(completed.returncode == 0 and target_status is not None
                     and stat.S_ISDIR(target_status.st_mode)
                     and not stat.S_ISLNK(target_status.st_mode),
                     "Codex native sandbox failed the git-metadata-write control")
    finally:
        _remove_exact_probe_entry(git_write)
    return {"name": "git-metadata-write", "outcome": "denied" if denied else "allowed"}


_SHARED_CHECKER_MODULE = "native_eval_adapter_common"


@dataclass(frozen=True)
class _CheckerSource:
    source: str
    nodes: dict[str, ast.AST]
    kinds: dict[str, str]
    import_bindings: dict[str, dict[str, object]]


def _checker_source(path: Path) -> _CheckerSource:
    """Index one module's top-level imports, helpers, classes and constants."""
    try:
        source = path.read_bytes().decode("utf-8", errors="strict")
        module = ast.parse(source, filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError) as exc:
        raise adapter_common.NativeAdapterError("Codex native isolation checker source is unavailable") from exc

    table = _CheckerSource(source, {}, {}, {})
    for node in module.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                table.nodes[bound] = node
                table.kinds[bound] = "import"
                table.import_bindings[bound] = {
                    "kind": "import", "module": alias.name, "name": None,
                    "as": alias.asname, "level": 0, "bound": bound,
                }
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound = alias.asname or alias.name
                table.nodes[bound] = node
                table.kinds[bound] = "import"
                table.import_bindings[bound] = {
                    "kind": "import", "module": node.module, "name": alias.name,
                    "as": alias.asname, "level": node.level, "bound": bound,
                }
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            table.nodes[node.name] = node
            table.kinds[node.name] = "helper"
        elif isinstance(node, ast.ClassDef):
            table.nodes[node.name] = node
            table.kinds[node.name] = "class"
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    table.nodes[target.id] = node
                    table.kinds[target.id] = "constant"
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            table.nodes[node.target.id] = node
            table.kinds[node.target.id] = "constant"
    return table


def _checker_dependencies(table: _CheckerSource, name: str) -> tuple[set[str], set[str]]:
    """Return the local names and the shared-module attributes one node loads."""
    local: set[str] = set()
    shared: set[str] = set()
    for child in ast.walk(table.nodes[name]):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load) and child.id in table.nodes:
            local.add(child.id)
        elif isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name):
            binding = table.import_bindings.get(child.value.id)
            if binding is not None and binding["module"] == _SHARED_CHECKER_MODULE \
                    and not child.attr.startswith("__"):
                shared.add(child.attr)
    return local, shared


def _checker_component(table: _CheckerSource, name: str) -> dict[str, object]:
    node = table.nodes[name]
    binding = table.import_bindings.get(name) if table.kinds[name] == "import" else None
    if binding is not None:
        payload = adapter_common._canonical_json(binding)
    else:
        segments = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            segments.extend(ast.get_source_segment(table.source, item) for item in node.decorator_list)
        segments.append(ast.get_source_segment(table.source, node))
        if any(segment is None for segment in segments):
            raise adapter_common.NativeAdapterError("Codex native isolation checker source mapping failed")
        payload = "\n".join(segment for segment in segments if segment is not None).encode("utf-8")
    component: dict[str, object] = {
        "kind": table.kinds[name], "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    if binding is not None:
        component["binding"] = binding
    return component


def _checker_closure(
    table: _CheckerSource, roots: set[str], prefix: str,
) -> tuple[dict[str, dict[str, object]], set[str]]:
    """Hash the closure of ``roots`` in one module and name the shared attributes it reaches."""
    if roots - table.nodes.keys():
        raise adapter_common.NativeAdapterError("Codex native isolation checker closure is incomplete")
    selected: set[str] = set()
    shared: set[str] = set()
    pending = sorted(roots)
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        selected.add(name)
        local, attributes = _checker_dependencies(table, name)
        shared |= attributes
        pending.extend(sorted(local - selected))
    components = {prefix + name: _checker_component(table, name) for name in sorted(selected)}
    return components, shared


def _isolation_checker_identity() -> dict[str, object]:
    """Hash the exact local source closure that qualifies Codex isolation.

    The closure starts in this module and follows every ``adapter_common``
    attribute it loads into the shared adapter module, so a change to a shared
    helper the checker relies on changes the digest too.
    """
    components, shared = _checker_closure(
        _checker_source(Path(__file__)),
        {"_isolation_checker_identity", "_qualify_codex_isolation"}, "",
    )
    shared_components, _ = _checker_closure(
        _checker_source(Path(adapter_common.__file__)),
        shared | {"NativeAdapterError"}, _SHARED_CHECKER_MODULE + ".",
    )
    unsigned: dict[str, object] = {
        "schema_version": "native-eval-isolation-checker/v1",
        "components": dict(sorted({**components, **shared_components}.items())),
    }
    return {
        **unsigned,
        "digest": hashlib.sha256(adapter_common._canonical_json(unsigned)).hexdigest(),
    }


def _qualify_codex_isolation(
    *, executable: str, workspace: Path, environment: Mapping[str, str],
    permission_args: list[str], permission_name: str, filesystem_access: str,
    evidence_root: str | Path | None, repo_root: Path, attempt: Path,
    runtime_executable: Path | None = None, runtime_version: tuple[int, int] | None = None,
    toolchain_probe: tuple[Path, str] | None = None,
    git_probe: Path | None = None,
    git_metadata_access: str | None = None,
) -> dict[str, object]:
    """Qualify the exact local profile without contacting a model provider."""
    adapter_common._require(evidence_root is not None,
             "Codex native trials require an explicit non-temporary evidence_root")
    evidence = _real_canonical_directory(Path(evidence_root), "evidence_root")
    adapter_common._require(not _is_broad_temporary_root(evidence),
             "Codex native evidence_root must be outside broad temporary storage")
    staging = _real_canonical_directory(evidence / "staging", "evidence_root staging directory")
    attempts = _real_canonical_directory(evidence / "attempts", "evidence_root attempts directory")
    adapter_common._require(attempt.parent == staging and attempt.name not in {"", ".", ".."},
             "Codex attempt_dir must be one direct child of evidence_root/staging")
    attempt = _real_canonical_directory(attempt, "Codex staging attempt")
    adapter_common._require(workspace.parent == attempt, "Codex workspace escaped its reserved staging attempt")
    workspace = _real_canonical_directory(workspace, "Codex workspace")
    repo_root = _real_canonical_directory(repo_root, "repo_root")
    control = workspace / ".codex" / "native-eval-isolation-control.txt"
    control_status = control.lstat()
    adapter_common._require(stat.S_ISREG(control_status.st_mode) and not stat.S_ISLNK(control_status.st_mode),
             "Codex native isolation control is unavailable")
    control_identity = (
        control_status.st_dev, control_status.st_ino,
        hashlib.sha256(_ISOLATION_CONTROL).hexdigest(),
    )
    _require_unchanged_probe(control, control_identity, _ISOLATION_CONTROL, "workspace-read")
    reader = "/bin/cat" if Path("/bin/cat").is_file() else adapter_common._resolve_executable("cat")
    directory_maker = "/bin/mkdir" if Path("/bin/mkdir").is_file() else adapter_common._resolve_executable("mkdir")
    repo_probe = repo_root / "speckit-pro" / ".claude-plugin" / "plugin.json"
    try:
        repo_status = repo_probe.lstat()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("Codex repository isolation probe is unavailable") from exc
    adapter_common._require(stat.S_ISREG(repo_status.st_mode) and not stat.S_ISLNK(repo_status.st_mode),
             "Codex repository isolation probe must be a regular file")
    directory_identities = {}
    for path in (evidence, staging, attempts, attempt, workspace, repo_root):
        metadata = path.lstat()
        directory_identities[path] = (metadata.st_dev, metadata.st_ino)

    checks: list[dict[str, object]] = []
    with _temporary_isolation_probes(attempts, staging) as probes:
        (private_probe, private_payload, private_identity,
         sibling_probe, sibling_payload, sibling_identity) = probes
        specifications = (
            ("workspace-read", reader, control, _ISOLATION_CONTROL, False),
            ("private-evidence", reader, private_probe, None, True),
            ("sibling-staging", reader, sibling_probe, None, True),
            ("repository-source", reader, repo_probe, None, True),
        )
        for label, program, target, payload, denied in specifications:
            completed = _run_codex_sandbox_probe(
                _sandbox_probe_command(
                    executable, permission_name, permission_args, workspace, program, target,
                ), cwd=workspace, environment=environment,
            )
            _require_probe_result(completed, label=label, expected_payload=payload, denied=denied)
            checks.append({"name": label, "outcome": "denied" if denied else "allowed"})
            if target == control:
                _require_unchanged_probe(target, control_identity, _ISOLATION_CONTROL, label)
            elif target == private_probe:
                _require_unchanged_probe(target, private_identity, private_payload, label)
            elif target == sibling_probe:
                _require_unchanged_probe(target, sibling_identity, sibling_payload, label)

        if filesystem_access in {"read", "write"}:
            ordinary_write = workspace / f".native-isolation-write-{uuid.uuid4().hex}"
            for label, target, denied in (
                ("workspace-write", ordinary_write, filesystem_access == "read"),
                ("staged-skills-write", workspace / ".agents" / f".native-isolation-{uuid.uuid4().hex}", True),
                ("staged-config-write", workspace / ".codex" / f".native-isolation-{uuid.uuid4().hex}", True),
            ):
                created = False
                try:
                    completed = _run_codex_sandbox_probe(
                        _sandbox_probe_command(
                            executable, permission_name, permission_args, workspace,
                            directory_maker, target,
                        ), cwd=workspace, environment=environment,
                    )
                    try:
                        target_status = target.lstat()
                    except FileNotFoundError:
                        target_status = None
                    created = target_status is not None
                    if denied:
                        _require_probe_result(completed, label=label, denied=True)
                        adapter_common._require(not created,
                                 f"Codex native sandbox created the denied {label} control")
                    else:
                        adapter_common._require(completed.returncode == 0 and target_status is not None
                                 and stat.S_ISDIR(target_status.st_mode)
                                 and not stat.S_ISLNK(target_status.st_mode),
                                 "Codex native sandbox failed the workspace-write control")
                finally:
                    _remove_exact_probe_entry(target)
                checks.append({"name": label, "outcome": "denied" if denied else "allowed"})

        git_metadata_probe = _qualify_codex_git_metadata(
            executable=executable, workspace=workspace, environment=environment,
            permission_args=permission_args, permission_name=permission_name,
            filesystem_access=filesystem_access, directory_maker=directory_maker,
            git_metadata_access=git_metadata_access,
        )
        if git_metadata_probe is not None:
            checks.append(git_metadata_probe)

        adapter_common._require((runtime_executable is None) == (runtime_version is None),
                 "Codex protected runtime probe inputs are incomplete")
        if runtime_executable is not None and runtime_version is not None:
            runtime_output = f"{runtime_version[0]}.{runtime_version[1]}\n".encode("ascii")
            completed = _run_codex_sandbox_probe(
                _sandbox_probe_command(
                    executable, permission_name, permission_args, workspace,
                    str(runtime_executable),
                    arguments=(
                        "-I", "-S", "-c",
                        "import sys;print(f'{sys.version_info.major}.{sys.version_info.minor}')",
                    ),
                ), cwd=workspace, environment=environment,
            )
            _require_probe_result(
                completed, label="protected-python-runtime", expected_payload=runtime_output,
            )
            checks.append({"name": "protected-python-runtime", "outcome": "allowed"})

        if toolchain_probe is not None:
            tool_executable, expected_version = toolchain_probe
            adapter_common._require(tool_executable.is_absolute()
                     and tool_executable.is_relative_to(workspace)
                     and isinstance(expected_version, str)
                     and bool(expected_version)
                     and "\n" not in expected_version and "\r" not in expected_version,
                     "Codex native toolchain probe is malformed")
            completed = _run_codex_sandbox_probe(
                _sandbox_probe_command(
                    executable, permission_name, permission_args, workspace,
                    str(tool_executable), arguments=("--version",),
                ), cwd=workspace, environment=environment,
            )
            _require_probe_result(
                completed, label="native-tool-specify",
                expected_payload=f"{expected_version}\n".encode("utf-8"),
            )
            checks.append({"name": "native-tool-specify", "outcome": "allowed"})

        if git_probe is not None:
            adapter_common._require(git_probe.is_absolute() and git_probe.is_relative_to(workspace),
                     "Codex protected Git probe is malformed")
            git_metadata = workspace / ".git"
            repository_probe = git_metadata.is_dir() and not git_metadata.is_symlink()
            arguments = (
                ("rev-parse", "--is-inside-work-tree")
                if repository_probe else ("--version",)
            )
            completed = _run_codex_sandbox_probe(
                _sandbox_probe_command(
                    executable, permission_name, permission_args, workspace,
                    str(git_probe), arguments=arguments,
                ), cwd=workspace, environment=environment,
            )
            _require_probe_result(
                completed, label="protected-git-runtime",
                expected_payload=b"true\n" if repository_probe else None,
                expected_prefix=None if repository_probe else b"git version ",
            )
            checks.append({"name": "protected-git-runtime", "outcome": "allowed"})

    for path, expected in directory_identities.items():
        try:
            observed = path.lstat()
        except OSError as exc:
            raise adapter_common.NativeAdapterError("Codex native isolation directory changed during qualification") from exc
        adapter_common._require(stat.S_ISDIR(observed.st_mode) and not stat.S_ISLNK(observed.st_mode)
                 and (observed.st_dev, observed.st_ino) == expected,
                 "Codex native isolation directory changed during qualification")

    checker_identity = _isolation_checker_identity()
    return {
        "schema_version": "native-eval-isolation-qualification/v1", "status": "qualified",
        "scope": "workspace-plus-runtime-minimal", "evidence_root": str(evidence),
        "permission_profile": permission_name,
        "permission_policy_sha256": hashlib.sha256(
            adapter_common._canonical_json(adapter_common._relocated(permission_args, attempt))
        ).hexdigest(),
        "checker_sha256": checker_identity["digest"], "checker_identity": checker_identity,
        "reader": reader, "directory_maker": directory_maker, "probes": checks,
    }


def _prepare_codex(
    case: Mapping[str, object], prompt: str, host_settings: Mapping[str, object],
    repo: Path, attempt: Path, model: str, trial_identity: str,
    evidence_root: str | Path | None,
) -> adapter_common.PreparedTrial:
    helpers = _codex_helpers()
    candidate = helpers.codex_executable()
    executable = str(Path(candidate).resolve(strict=True)) if Path(candidate).is_absolute() else adapter_common._resolve_executable("codex")
    cli_version = adapter_common._probe_cli_version(executable)
    workspace = attempt / "workspace"
    workspace.mkdir(mode=0o700)
    input_dir = attempt / "staged-inputs"
    input_dir.mkdir(mode=0o700)
    plan, plan_path = adapter_common._stage_fixture_plan(case, repo, input_dir)
    fixture_read_witnesses = adapter_common._fixture_read_witnesses(case, plan_path)
    required_tools = adapter_common._required_native_tools(case)
    adapter_common._require(not required_tools or case.get("layer") != "trigger",
             "trigger measurements cannot stage an upstream tool integration")
    prompt = adapter_common._render_resolved_python(prompt, "codex", workspace, required_tools)
    for fixture in plan["fixtures"]:
        destination = PurePosixPath(fixture["destination"])
        reserved = {".agents", ".codex", ".codex-trigger-runtime"}
        if required_tools:
            reserved.add(".claude")
        adapter_common._require(destination.parts[0] not in reserved,
                 f"Codex fixture destination overlaps a runtime control path: {destination}")
    git_result: dict[str, object] | None = None
    staged_tree_exclusions: dict[str, object] | None = None
    if plan["schema_version"] == fixture_setup.GIT_SCHEMA_VERSION:
        materialized = fixture_setup.materialize_workspace(
            fixture_setup.load_plan(plan_path), workspace.resolve(),
        )
        adapter_common._require(isinstance(materialized, dict), "git fixture returned a malformed result")
        git_result = {"schema_version": fixture_setup.GIT_SCHEMA_VERSION, **materialized}
        adapter_common._write_git_controller_exclude(
            workspace, adapter_common._git_controller_exclude(
                git_result, host="codex", include_upstream=bool(required_tools),
            ),
        )
        staged_tree_exclusions = {"root_directories": [".git"], "files": []}
    isolation_control = workspace / ".codex" / "native-eval-isolation-control.txt"
    isolation_control.parent.mkdir(mode=0o700)
    adapter_common._write_text(isolation_control, _ISOLATION_CONTROL.decode("ascii"))
    prepared_toolchain: native_eval_toolchain.PreparedNativeToolchain | None = None
    prepared_upstream: native_eval_upstream.PreparedUpstreamIntegration | None = None
    if required_tools:
        prepared_toolchain = native_eval_toolchain.prepare_native_toolchain(
            workspace, required_tools=required_tools,
        )
        upstream_controller = attempt / "upstream-controller"
        upstream_controller.mkdir(mode=0o700)
        prepared_upstream = native_eval_upstream.prepare_upstream_integration(
            upstream_controller, host="codex", toolchain=prepared_toolchain,
        )
        adapter_common._validate_upstream_fixture_destinations(
            plan["fixtures"], "codex", prepared_upstream.runtime_identity,
        )
    runtime_stage: native_eval_runtime.CodexRuntimeStage | None = None
    agent_registration_args: list[str] = []
    agent_registrations: list[dict[str, str]] = []
    if case.get("layer") == "trigger":
        prompt, trigger_stage = adapter_common._stage_trigger(
            case, host_settings, repo, workspace, "codex", prompt, trial_identity,
        )
        skill_root = workspace / ".agents" / "skills"
    else:
        runtime_stage = native_eval_runtime.stage_codex_runtime(
            repo, attempt / "runtime-build", workspace,
        )
        adapter_common._require(runtime_stage.payload_root == workspace / ".agents"
                 and runtime_stage.agent_root == workspace / ".codex" / "agents"
                 and runtime_stage.pythonpath == str(runtime_stage.payload_root),
                 "canonical Codex runtime returned paths outside the staged workspace")
        adapter_common._require(runtime_stage.proof.get("schema_version") == native_eval_runtime.SCHEMA_VERSION
                 and runtime_stage.proof.get("pythonpath_relative") == ".agents"
                 and runtime_stage.runtime_identity.startswith("sha256:"),
                 "canonical Codex runtime returned malformed identity evidence")
        adapter_common._write_text(workspace / ".codex" / "config.toml", _CODEX_PROJECT_CONFIG)
        materializations = runtime_stage.proof.get("materializations")
        adapter_common._require(isinstance(materializations, list),
                 "canonical Codex runtime omitted agent materializations")
        for materialization in materializations:
            adapter_common._require(isinstance(materialization, dict),
                     "canonical Codex agent materialization is malformed")
            name = materialization.get("name")
            destination_value = materialization.get("destination_path")
            adapter_common._require(isinstance(name, str) and _CODEX_SKILL_NAME.fullmatch(name) is not None
                     and isinstance(destination_value, str),
                     "canonical Codex agent registration is malformed")
            destination = PurePosixPath(destination_value)
            adapter_common._require(destination == PurePosixPath(".codex", "agents", f"{name}.toml"),
                     "canonical Codex agent registration path is malformed")
            role_file = workspace.joinpath(*destination.parts).resolve()
            adapter_common._require(role_file.is_file(),
                     f"canonical Codex agent registration is missing: {name}")
            agent_registrations.append({"name": name, "path": destination.as_posix()})
            agent_registration_args.extend([
                "--config",
                f"agents.{name}.config_file={json.dumps(str(role_file))}",
            ])
        if prepared_upstream is not None:
            native_eval_upstream.stage_upstream_integration(prepared_upstream, workspace)
            staged_tree_exclusions = adapter_common._merge_staged_file_exclusions(
                staged_tree_exclusions,
                native_eval_upstream.volatile_manifest_paths(prepared_upstream.runtime_identity),
            )
        skill_root = runtime_stage.payload_root / "skills"
        trigger_stage = None
    skill_read_witnesses = (
        _codex_skill_read_witnesses(skill_root) if trigger_stage is None else None
    )
    skill = host_settings.get("skill")
    if skill is None:
        discovered: set[Path] = set()
        for root in helpers.skill_source_roots():
            discovered.update(helpers._canonical_skill_files(root))
        disabled_skills = tuple(sorted(discovered, key=str))
    else:
        skill_name = _codex_skill_name(skill)
        target_skill = skill_root / skill_name / "SKILL.md"
        adapter_common._require(target_skill.is_file(), f"Codex skill is unavailable in the staged catalog: {skill_name}")
        if runtime_stage is not None:
            prompt = prompt.replace(
                "{{skill}}", _codex_native_skill_reference(runtime_stage.payload_root, skill_name),
            )
        disabled_skills = helpers.enumerate_non_target_skills(target_skill)
    if git_result is None:
        fixture_setup.populate_workspace(fixture_setup.load_plan(plan_path), workspace.resolve())
    isolation_args = helpers.skill_isolation_args(disabled_skills)
    environment = dict(helpers.codex_environment(workspace))
    runtime_settings: dict[str, object] | None = None
    protected_python: Path | None = None
    protected_python_version: tuple[int, int] | None = None
    runtime_read_roots: tuple[Path, ...] = ()
    forwarded_environment: list[str] = []
    if runtime_stage is not None:
        protected_python, python_identity = _protected_python_runtime()
        protected_python_version = tuple(python_identity["version"][:2])
        runtime_root_value = python_identity.get("runtime_root")
        adapter_common._require(isinstance(runtime_root_value, str)
                 and Path(runtime_root_value) == protected_python.parent.parent,
                 "protected Python runtime root identity is malformed")
        runtime_read_roots = (Path(runtime_root_value),)
        original_path = environment.get("PATH", "")
        protected_directory = str(protected_python.parent)
        remaining_path = [
            entry for entry in original_path.split(os.pathsep)
            if entry and entry != protected_directory
        ]
        environment["PATH"] = os.pathsep.join([protected_directory, *remaining_path])
        environment["PYTHONPATH"] = runtime_stage.pythonpath
        environment["PYTHONSAFEPATH"] = "1"
        forwarded_environment.extend(("PYTHONPATH", "PYTHONSAFEPATH"))
        runtime_settings = {
            "schema_version": native_eval_runtime.SCHEMA_VERSION,
            "runtime_identity": runtime_stage.runtime_identity,
            "proof": json.loads(adapter_common._canonical_json(runtime_stage.proof)),
            "pythonpath_relative": ".agents",
            "python": python_identity,
            "agent_registrations": agent_registrations,
        }
    git_settings: dict[str, object] | None = None
    git_subject_settings: dict[str, object] | None = None
    protected_git: Path | None = None
    protected_git_settings: dict[str, object] | None = None
    if git_result is not None:
        git_controls = fixture_setup.snapshot_git_repository_controls(workspace)
        adapter_common._require(fixture_setup.inspect_git_repository(workspace, git_controls)
                 == git_result["git_repository"],
                 "git fixture semantic receipt changed during preparation")
        if "worktrees" in git_result:
            worktree_observation = native_eval_git_observation.observe_registered_worktrees(
                workspace, git_controls, git_result["git_repository"], git_result["worktrees"],
            )
            adapter_common._require(adapter_common._worktrees_match_initial(worktree_observation),
                     "git fixture worktrees changed during preparation")
        git_settings = adapter_common._git_runtime_settings(
            expected_result=git_result,
            git_controls=git_controls,
            host="codex",
            include_upstream=bool(required_tools),
        )
    runtime_write_roots: tuple[Path, ...] = ()
    if _codex_protected_git_required(case):
        environment = {
            name: value for name, value in environment.items()
            if not name.startswith("GIT_") and name not in {"TMPDIR", "TMP", "TEMP"}
        }
        git_environment, git_subject_settings = _codex_git_subject_environment(workspace)
        environment.update(git_environment)
        forwarded_environment.extend(git_environment)
        protected_git, git_exec_path, protected_git_settings = _stage_protected_git(workspace)
        environment["GIT_EXEC_PATH"] = str(git_exec_path)
        forwarded_environment.append("GIT_EXEC_PATH")
        protected_git_directory = str(protected_git.parent)
        environment["PATH"] = os.pathsep.join([
            protected_git_directory,
            *(entry for entry in environment.get("PATH", "").split(os.pathsep)
              if entry and entry != protected_git_directory),
        ])
        source_git = Path(protected_git_settings["source_executable"])
        runtime_read_roots = tuple(dict.fromkeys([
            *runtime_read_roots, git_exec_path, source_git,
        ]))
        runtime_write_roots = (workspace / ".native-eval-tmp",)
    if prepared_toolchain is not None:
        environment.update(prepared_toolchain.environment)
        existing_path = [entry for entry in environment.get("PATH", "").split(os.pathsep) if entry]
        tool_paths = [str(entry) for entry in prepared_toolchain.path_entries]
        environment["PATH"] = os.pathsep.join([
            *tool_paths,
            *(entry for entry in existing_path if entry not in tool_paths),
        ])
        runtime_read_roots = tuple(dict.fromkeys([
            *runtime_read_roots, *prepared_toolchain.readonly_roots,
        ]))
        forwarded_environment.extend(
            name for name in prepared_toolchain.environment
            if name not in forwarded_environment
        )
    requested_tools = host_settings.get("allowed_tools")
    adapter_common._require(isinstance(requested_tools, list)
             and all(isinstance(tool, str) and tool for tool in requested_tools),
             "Codex allowed_tools are malformed")
    known_tools = _CODEX_READ_TOOLS | _CODEX_WRITE_TOOLS | _CODEX_SUBAGENT_TOOLS
    unknown_tools = sorted(set(requested_tools) - known_tools)
    adapter_common._require(not unknown_tools, "Codex case requests an unsupported filesystem/tool profile: " + ", ".join(unknown_tools))
    filesystem_access = "write" if set(requested_tools) & _CODEX_WRITE_TOOLS else "read"
    permission_name = "native-eval-write" if filesystem_access == "write" else "native-eval-read"
    permission_args = _codex_permission_args(
        workspace, environment, filesystem_access, permission_name,
        forwarded_environment=tuple(forwarded_environment),
        runtime_read_roots=runtime_read_roots,
        runtime_write_roots=runtime_write_roots,
        git_metadata_access=case.get("git_metadata_access"),
    )
    nested = case["resource_class"] == "nested"
    recorded_session = nested or case.get("layer") != "trigger"
    session_args = ([] if recorded_session else ["--ephemeral"]) + (
        ["--enable", "multi_agent"] if nested else ["--disable", "multi_agent"]
    )
    trigger_instruction = adapter_common._TRIGGER_MEASUREMENT_INSTRUCTIONS["codex"] if trigger_stage is not None else None
    trigger_instruction_args = (
        ["--config", "developer_instructions=" + json.dumps(trigger_instruction)]
        if trigger_instruction is not None else []
    )
    project_root_markers = [".codex"] if runtime_stage is not None else []
    command = [
        executable, "exec", "--json", *session_args, "--strict-config",
        "--ignore-user-config", "--ignore-rules", "--model", model,
        "--skip-git-repo-check",
        *permission_args,
        "--config",
        "project_root_markers=" + json.dumps(project_root_markers, separators=(",", ":")),
        "--config", "tools.update_plan.enabled=true",
        *agent_registration_args, *trigger_instruction_args,
        "--cd", str(workspace.resolve()), *isolation_args, prompt,
    ]
    isolation_qualification = _qualify_codex_isolation(
        executable=executable, workspace=workspace, environment=environment,
        permission_args=permission_args, permission_name=permission_name,
        filesystem_access=filesystem_access, evidence_root=evidence_root,
        repo_root=repo, attempt=attempt,
        runtime_executable=protected_python, runtime_version=protected_python_version,
        toolchain_probe=(
            prepared_toolchain.launchers["specify"],
            prepared_toolchain.runtime_identity["tools"]["specify"]["version"],
        ) if prepared_toolchain is not None else None,
        git_probe=protected_git,
        git_metadata_access=case.get("git_metadata_access"),
    )
    protected_control_trees = {
        ".agents": adapter_common._tree_digest(workspace / ".agents"),
        ".codex": adapter_common._tree_digest(workspace / ".codex"),
    }
    settings = {
        "user_config_ignored": True, "rules_ignored": True,
        "ephemeral": not recorded_session, "recorded_session": recorded_session,
        "multi_agent_enabled": nested,
        "native_rollout_supplement_required": recorded_session,
        "native_skill_injection_capture_required": recorded_session and trigger_stage is None,
        "project_instructions_isolated": False,
        "instruction_inputs_fingerprinted": True,
        "project_instruction_parent_traversal": False,
        "project_root_markers": project_root_markers,
        "global_instructions_disabled": False,
        "update_plan_enabled": True,
        "filesystem": f"workspace-{filesystem_access}-plus-runtime-minimal", "network": False,
        "filesystem_capability_enforced": True, "literal_tool_allowlist_enforced": False,
        "isolation_qualification": isolation_qualification,
        "protected_control_trees": protected_control_trees,
        "approval_policy": "never",
        "login_shell": False, "shell_environment_inherit": "none",
        "allowed_tools": requested_tools,
        **({"git_metadata_access": case["git_metadata_access"]}
           if "git_metadata_access" in case else {}),
        "timeout_seconds": case["timeout_seconds"], "resource_class": case.get("resource_class"),
        "declared_artifacts": list(adapter_common._declared_artifacts(case, repo)),
        "verification_record_directories": list(
            native_eval_verification.record_directories(case)
        ),
        "trigger_stage": adapter_common._trigger_identity(trigger_stage, attempt),
        **({
            "required_tools": list(required_tools),
            "native_toolchain": adapter_common._native_toolchain_identity(prepared_toolchain),
            "upstream_integration": {
                "host": "codex",
                "source_relative": prepared_upstream.project_root.relative_to(attempt).as_posix(),
                "runtime_identity": json.loads(adapter_common._canonical_json(prepared_upstream.runtime_identity)),
            },
            "upstream_skill_witnesses": native_eval_upstream.skill_witnesses(
                prepared_upstream.runtime_identity
            ),
        } if prepared_toolchain is not None else {}),
        **({"codex_runtime": runtime_settings} if runtime_settings is not None else {}),
        **({"fixture_read_witnesses": fixture_read_witnesses} if fixture_read_witnesses else {}),
        **({"git_fixture": git_settings} if git_settings is not None else {}),
        **({"git_subject_environment": git_subject_settings}
           if git_subject_settings is not None else {}),
        **({"protected_git": protected_git_settings}
           if protected_git_settings is not None else {}),
        **({"skill_read_witnesses": skill_read_witnesses}
           if skill_read_witnesses is not None else {}),
        **({"trigger_measurement_instruction": {
            "text": trigger_instruction,
            "bytes": len(trigger_instruction.encode("utf-8")),
            "sha256": hashlib.sha256(trigger_instruction.encode("utf-8")).hexdigest(),
        }, "trigger_tool_exposure_runtime_qualification_required": True}
           if trigger_instruction is not None else {}),
    }
    instruction_inputs = _codex_instruction_inputs(
        environment, workspace, parent_traversal_disabled=True,
    )
    identity = adapter_common._runtime_identity(
        case=case, host="codex", mode="project", model=model, executable=executable,
        cli_version=cli_version, staged_root=workspace, skill_root=skill_root,
        fixture_root=input_dir / "fixture-sources", settings=settings, attempt=attempt,
        command=command, environment=environment, instruction_inputs=instruction_inputs,
        staged_tree_exclusions=staged_tree_exclusions,
    )
    return adapter_common.PreparedTrial(command, workspace, dict(environment), "codex", "project", attempt,
                         attempt / "trace.jsonl", None, workspace, identity, trigger_stage)
