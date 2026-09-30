"""Shared staging, identity and receipt helpers for the native eval host adapters.

The Claude and Codex adapters and the public entry point in
``native_eval_adapters`` all build on these helpers: the prepared-trial record,
fixture-plan staging, git controller settings, runtime and trigger identities,
and the canonical JSON used by every digest.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
from typing import Any, Mapping, Sequence
import uuid

import native_eval_fixture_setup as fixture_setup
import native_eval_pairing
import native_eval_runner_result
import native_eval_toolchain
import native_eval_trigger
import native_eval_upstream


_CASE_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")
_SUPPORTED_REQUIRED_TOOLS = frozenset({"specify"})
_ARTIFACT_COUNT_LIMIT = 64
_GIT_RUNTIME_SCHEMA_VERSION = "native-eval-git-runtime/v1"
_CLAUDE_AUTOMATION_AUTH_VARIABLES = (
    "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
)
_CODEX_GIT_CONTROLLER_EXCLUDE = b"/.agents/\n/.codex/\n/.native-eval-tmp/\n"
_TRIGGER_MEASUREMENT_INSTRUCTIONS = {
    "claude": (
        "This is an authorized Claude Code plugin skill-selection measurement only. Do not perform the user's "
        "requested work. Evaluate the unchanged user request only against the descriptions of skills loaded from "
        "the speckit-pro-trigger plugin. If a plugin skill applies, invoke that one staged skill through Claude "
        "Code's Skill tool and follow its existing selection-attestation protocol. If no plugin skill applies, "
        "invoke the plugin's existing no-speckit-skill fallback and follow its existing protocol. Apart from that "
        "Skill invocation and reads of declared fixture files already staged in the isolated eval workspace, do "
        "not invoke tools, inspect or search the workspace or user-named project paths, edit files, or execute the "
        "requested workflow. Stop after the selection response."
    ),
    "codex": (
        "This is an authorized Codex project skill-selection measurement only. Do not perform the user's requested "
        "work. Evaluate the unchanged user request only against the descriptions of skills staged under "
        ".agents/skills. If a staged skill applies, run only one exact read of that selected staged SKILL.md and "
        "follow its existing selection-attestation protocol. If no staged skill applies, do the same for the "
        "existing no-speckit-skill fallback. Apart from that one exact staged skill read and reads of declared "
        "fixture files already staged in the isolated workspace, do not invoke tools, inspect or search project "
        "paths, edit files, or execute the requested workflow. Stop after the selection response."
    ),
}


class NativeAdapterError(RuntimeError):
    """The native adapter could not establish the requested evidence."""


@dataclass(frozen=True)
class PreparedTrial:
    command: list[str]
    cwd: Path
    environment: dict[str, str]
    host: str
    mode: str
    attempt_dir: Path
    trace_path: Path | None
    result_path: Path | None
    artifact_root: Path | None
    runtime_identity: dict[str, Any]
    trigger_stage: native_eval_trigger.TriggerStage | None = None
    stdin_path: Path | None = None

    @property
    def stdout_path(self) -> Path:
        return self.attempt_dir / "native-stdout.bin"

    @property
    def stderr_path(self) -> Path:
        return self.attempt_dir / "native-stderr.bin"

    @property
    def process_receipt_path(self) -> Path:
        return self.attempt_dir / "native-process.json"

    @property
    def git_observation_path(self) -> Path:
        return self.attempt_dir / "native-git-observation.json"

    def as_dict(self) -> dict[str, object]:
        return {
            "command": list(self.command),
            "cwd": str(self.cwd),
            "environment": {
                key: "<redacted-controller-credential>"
                if key in _CLAUDE_AUTOMATION_AUTH_VARIABLES else value
                for key, value in self.environment.items()
            },
            "host": self.host,
            "mode": self.mode,
            "attempt_dir": str(self.attempt_dir),
            "trace_path": str(self.trace_path) if self.trace_path is not None else None,
            "result_path": str(self.result_path) if self.result_path is not None else None,
            "artifact_root": str(self.artifact_root) if self.artifact_root is not None else None,
            "runtime_identity": dict(self.runtime_identity),
            "trigger_stage": self.trigger_stage.as_dict() if self.trigger_stage is not None else None,
            "stdin_path": str(self.stdin_path) if self.stdin_path is not None else None,
        }


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _resolve_executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise NativeAdapterError(f"{name} CLI is unavailable")
    try:
        resolved = Path(executable).resolve(strict=True)
    except OSError as exc:
        raise NativeAdapterError(f"{name} CLI path cannot be resolved") from exc
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise NativeAdapterError(f"{name} CLI is not executable")
    return str(resolved)


def _base_environment() -> dict[str, str]:
    return {
        key: os.environ[key]
        for key in (
            "PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE", "USER",
            "DOCKER_CONFIG",
        )
        if key in os.environ
    }


def _probe_executable_output(executable: str, argument: str, error: str) -> str:
    try:
        completed = subprocess.run(
            [executable, argument], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=_base_environment(), shell=False, check=False, timeout=10,
        )
        output = completed.stdout.decode("utf-8", errors="strict").strip()
    except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError) as exc:
        raise NativeAdapterError(error) from exc
    if completed.returncode != 0 or not output or "\n" in output:
        raise NativeAdapterError(error)
    return output


def _probe_cli_version(executable: str) -> str:
    return _probe_executable_output(
        executable, "--version", "native CLI version could not be established",
    )


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def _relocated(value: object, attempt: Path) -> object:
    token = "<attempt_dir>"
    prefix = str(attempt)
    if isinstance(value, str):
        if value == prefix or value.startswith(prefix + os.sep):
            return token + value[len(prefix):]
        # Permission overrides carry workspace paths as quoted TOML/JSON
        # strings.  Relocate only that typed path position, never arbitrary
        # source text that happens to contain the attempt path.
        quoted_prefix = '"' + json.dumps(prefix)[1:-1] + os.sep
        if quoted_prefix in value:
            return value.replace(quoted_prefix, '"' + token + os.sep)
        return value
    if isinstance(value, list):
        return [_relocated(item, attempt) for item in value]
    if isinstance(value, tuple):
        return [_relocated(item, attempt) for item in value]
    if isinstance(value, dict):
        return {key: _relocated(item, attempt) for key, item in value.items()}
    return value


def _tree_digest(
    root: Path, *, exclusions: Mapping[str, object] | None = None,
    relocation_root: Path | None = None,
) -> str:
    excluded_roots: frozenset[str] = frozenset()
    excluded_files: frozenset[str] = frozenset()
    if exclusions is not None:
        _require(isinstance(exclusions, Mapping)
                 and set(exclusions) == {"root_directories", "files"},
                 "staged tree exclusions are malformed")
        roots = exclusions["root_directories"]
        files = exclusions["files"]
        _require(isinstance(roots, list) and isinstance(files, list)
                 and all(isinstance(item, str) for item in roots + files),
                 "staged tree exclusions are malformed")
        _require(len(roots) == len(set(roots)) and len(files) == len(set(files)),
                 "staged tree exclusions are duplicated")
        _require(all(PurePosixPath(item).parts == (item,) and item not in {"", ".", ".."}
                     for item in roots),
                 "staged tree root exclusion is not canonical")
        _require(all(not PurePosixPath(item).is_absolute()
                     and "\\" not in item
                     and PurePosixPath(item).as_posix() == item
                     and all(part not in {"", ".", ".."} for part in PurePosixPath(item).parts)
                     for item in files),
                 "staged tree file exclusion is not canonical")
        excluded_roots = frozenset(roots)
        excluded_files = frozenset(files)
    relocation_source: bytes | None = None
    if relocation_root is not None:
        _require(relocation_root.is_absolute(), "staged tree relocation root must be absolute")
        relocation_source = str(relocation_root).encode("utf-8")
    digest = hashlib.sha256()
    if not root.exists():
        return digest.hexdigest()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative_value = path.relative_to(root).as_posix()
        relative_path = PurePosixPath(relative_value)
        if relative_path.parts[0] in excluded_roots or relative_value in excluded_files:
            continue
        relative = relative_value.encode("utf-8")
        status = path.lstat()
        if stat.S_ISLNK(status.st_mode):
            raise ValueError(f"staged runtime contains a symlink: {path.relative_to(root)}")
        if stat.S_ISDIR(status.st_mode):
            digest.update(b"D\0" + relative + b"\0")
        elif stat.S_ISREG(status.st_mode):
            payload = path.read_bytes()
            if relocation_source is not None:
                payload = payload.replace(relocation_source, b"<attempt_dir>")
            digest.update(b"F\0" + relative + b"\0" + payload + b"\0")
        else:
            raise ValueError(f"staged runtime contains a non-file entry: {path.relative_to(root)}")
    return digest.hexdigest()


def _write_text(path: Path, text: str, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    path.chmod(mode)


def _write_json(path: Path, value: object) -> None:
    _write_text(path, json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n")


def _stage_fixture_records(
    value: object, namespace: str, repo_root: Path, tests_root: Path, source_root: Path,
) -> list[dict[str, str]]:
    _require(isinstance(value, list), "case fixtures are malformed")
    records: list[dict[str, str]] = []
    for index, fixture in enumerate(value):
        _require(isinstance(fixture, dict) and set(fixture) == {"source", "destination"},
                 "case fixture is malformed")
        source_value, destination_value = fixture["source"], fixture["destination"]
        _require(isinstance(source_value, str) and isinstance(destination_value, str),
                 "case fixture paths are malformed")
        source_relative = PurePosixPath(source_value)
        destination = PurePosixPath(destination_value)
        _require(source_relative.parts[:2] == ("tests", "speckit-pro"),
                 "case fixture source must be under tests/speckit-pro")
        _require(not source_relative.is_absolute() and source_relative.as_posix() == source_value
                 and all(part not in {"", ".", ".."} for part in source_relative.parts),
                 "case fixture source must be canonical relative")
        _require(not destination.is_absolute() and destination.as_posix() == destination_value
                 and all(part not in {"", ".", ".."} for part in destination.parts),
                 "case fixture destination must be canonical relative")
        try:
            source = repo_root.joinpath(*source_relative.parts).resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"case fixture source is unavailable: {source_value}") from exc
        _require(source.is_relative_to(tests_root) and source.is_file(),
                 "case fixture source escaped tests/speckit-pro")
        payload = source.read_bytes()
        staged_name = f"{index:04d}.fixture"
        staged_relative = f"{namespace}/{staged_name}" if namespace else staged_name
        staged = source_root.joinpath(*PurePosixPath(staged_relative).parts)
        staged.parent.mkdir(parents=True, exist_ok=True)
        with staged.open("xb") as stream:
            stream.write(payload)
        staged.chmod(0o600)
        records.append({
            "source": staged_relative, "destination": destination.as_posix(),
            "sha256": hashlib.sha256(payload).hexdigest(),
        })
    return records


def _git_fixture_plan(
    git_fixture: object, fixtures: object,
    repo_root: Path, tests_root: Path, source_root: Path,
) -> dict[str, object]:
    _require(isinstance(git_fixture, dict) and set(git_fixture) in (
        {"recipe", "baseline"},
        {"recipe", "baseline", "worktrees"},
        {"recipe", "baseline", "feature_deletions"},
        {"recipe", "baseline", "feature_deletions", "worktrees"},
    ), "case git_fixture is malformed")
    _require(git_fixture["recipe"] == fixture_setup.GIT_FIXTURE_RECIPE,
             "case git_fixture has an unsupported recipe")
    baseline = _stage_fixture_records(
        git_fixture["baseline"], "baseline", repo_root, tests_root, source_root,
    )
    _require(bool(baseline), "case git_fixture baseline must be nonempty")
    feature = _stage_fixture_records(fixtures, "feature", repo_root, tests_root, source_root)
    feature_deletions = _git_feature_deletions(git_fixture)
    _require(bool(feature) or bool(feature_deletions),
             "case git feature overlay must be nonempty")
    git_repository = {"recipe": fixture_setup.GIT_FIXTURE_RECIPE, "baseline": baseline}
    if feature_deletions:
        git_repository["feature_deletions"] = list(feature_deletions)
    if "worktrees" in git_fixture:
        git_repository["worktrees"] = fixture_setup._worktree_records(git_fixture["worktrees"])
    return {
        "schema_version": fixture_setup.GIT_SCHEMA_VERSION,
        "source_root": "fixture-sources", "fixtures": feature,
        "git_repository": git_repository,
    }


def _stage_fixture_plan(case: Mapping[str, object], repo_root: Path, plan_dir: Path) -> tuple[dict[str, object], Path]:
    tests_root = (repo_root / "tests" / "speckit-pro").resolve(strict=True)
    source_root = plan_dir / "fixture-sources"
    source_root.mkdir(mode=0o700)
    fixtures = case.get("fixtures")
    git_fixture = case.get("git_fixture")
    if git_fixture is None:
        plan = {
            "schema_version": fixture_setup.SCHEMA_VERSION,
            "source_root": "fixture-sources",
            "fixtures": _stage_fixture_records(
                fixtures, "", repo_root, tests_root, source_root,
            ),
        }
    else:
        plan = _git_fixture_plan(
            git_fixture, fixtures, repo_root, tests_root, source_root,
        )
    plan_path = plan_dir / "fixture-plan.json"
    _write_json(plan_path, plan)
    return plan, plan_path


def _git_feature_deletions(git_fixture: Mapping[str, object]) -> list[str]:
    values = git_fixture.get("feature_deletions", [])
    _require(isinstance(values, list)
             and ("feature_deletions" not in git_fixture or bool(values))
             and all(isinstance(item, str) for item in values)
             and len(values) == len(set(values)),
             "case git_fixture feature_deletions are malformed")
    for value in values:
        deletion = PurePosixPath(value)
        _require(not deletion.is_absolute() and deletion.as_posix() == value
                 and all(part not in {"", ".", ".."} for part in deletion.parts),
                 "case git_fixture feature_deletion must be canonical relative")
    return values


def _fixture_read_witnesses(case: Mapping[str, object], plan_path: Path) -> dict[str, dict[str, object]]:
    """Bind required input reads to verified staged bytes, never later repo state."""
    required = {
        check["path"] for check in case.get("checks", [])
        if isinstance(check, Mapping) and check.get("type") == "file_access"
        and check.get("operation") == "read_file" and isinstance(check.get("path"), str)
    }
    required.update(native_eval_runner_result.request_paths(case))
    if not required:
        return {}
    plan = fixture_setup.load_plan(plan_path)
    source_root = Path(plan["source_root"]).resolve(strict=True)
    records = []
    if plan["schema_version"] == fixture_setup.GIT_SCHEMA_VERSION:
        records.extend(fixture_setup._fixture_records(
            plan["git_repository"]["baseline"], source_root, label_prefix="baseline",
        ))
    records.extend(fixture_setup._fixture_records(plan["fixtures"], source_root))
    # Feature inputs overlay the baseline in the actual fixture materializer.
    payloads = {path.as_posix(): payload for path, payload in records}
    return {
        path: {"bytes": len(payloads[path]), "sha256": hashlib.sha256(payloads[path]).hexdigest()}
        for path in sorted(required & payloads.keys())
    }


def _git_controller_exclude(
    expected_result: Mapping[str, object], *, host: str, include_upstream: bool = False,
) -> bytes:
    _require(host in {"claude", "codex"}, "Git controller host is unsupported")
    payload = _CODEX_GIT_CONTROLLER_EXCLUDE if host == "codex" else b""
    if include_upstream:
        payload += b"".join(
            f"/{relative}\n".encode("ascii")
            for relative in native_eval_upstream.expected_paths(host)
        )
    if "worktrees" in expected_result:
        payload += b"/.worktrees/\n"
    return payload


def _worktrees_match_initial(observation: Mapping[str, object]) -> bool:
    rows = observation.get("worktrees")
    return isinstance(rows, list) and all(
        isinstance(row, Mapping) and isinstance(row.get("initial"), Mapping)
        and row.get("head") == row["initial"].get("head")
        and row.get("branch") == row["initial"].get("branch")
        and isinstance(row.get("status"), Mapping) and row["status"].get("clean") is True
        for row in rows
    )


def _write_git_controller_exclude(workspace: Path, payload: bytes) -> None:
    git_directory = workspace / ".git"
    try:
        git_status = git_directory.lstat()
    except OSError as exc:
        raise NativeAdapterError("git fixture control directory is unavailable") from exc
    _require(stat.S_ISDIR(git_status.st_mode) and not stat.S_ISLNK(git_status.st_mode),
             "git fixture control directory is unsafe")
    info_directory = git_directory / "info"
    try:
        info_directory.mkdir(mode=0o700)
    except FileExistsError:
        pass  # An existing info/ is fine; the lstat check below rejects a symlink or non-directory.
    except OSError as exc:
        raise NativeAdapterError("git fixture info directory could not be created") from exc
    try:
        status = info_directory.lstat()
    except OSError as exc:
        raise NativeAdapterError("git fixture info directory is unavailable") from exc
    _require(stat.S_ISDIR(status.st_mode) and not stat.S_ISLNK(status.st_mode),
             "git fixture info directory is unsafe")
    path = info_directory / "exclude"
    try:
        status = path.lstat()
    except FileNotFoundError:
        status = None
    except OSError as exc:
        raise NativeAdapterError("git fixture controller exclude is unavailable") from exc
    _require(status is None or stat.S_ISREG(status.st_mode) and not stat.S_ISLNK(status.st_mode)
             and status.st_nlink == 1,
             "git fixture controller exclude is unsafe")
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise NativeAdapterError("git fixture controller exclude could not be created") from exc
    path.chmod(0o600)


def _git_runtime_settings(
    *, expected_result: Mapping[str, object], git_controls: Mapping[str, object],
    host: str, receipt_relative_path: str | None = None, include_upstream: bool = False,
) -> dict[str, object]:
    git_runtime = git_controls.get("git_runtime")
    _require(isinstance(git_runtime, Mapping), "git runtime identity is malformed")
    controller_exclude = _git_controller_exclude(
        expected_result, host=host, include_upstream=include_upstream,
    )
    settings: dict[str, object] = {
        "schema_version": _GIT_RUNTIME_SCHEMA_VERSION,
        "fixture_schema_version": fixture_setup.GIT_SCHEMA_VERSION,
        "recipe": fixture_setup.GIT_FIXTURE_RECIPE,
        "expected_result": dict(expected_result),
        "git_runtime": dict(git_runtime),
        "git_controls": dict(git_controls),
        "controller_info_exclude": controller_exclude.decode("ascii"),
    }
    if receipt_relative_path is not None:
        settings["receipt_relative_path"] = receipt_relative_path
    return settings


def _render_resolved_python(
    prompt: str, host: str, staged_root: Path, required_tools: tuple[str, ...],
) -> str:
    placeholder = "{{resolved_python}}"
    if placeholder not in prompt:
        return prompt
    _require(bool(required_tools),
             "resolved Python placeholder requires a staged native toolchain")
    if host == "claude":
        replacement = str(staged_root / "bin" / "python3")
    elif host == "codex":
        replacement = "python3"
    else:
        raise ValueError("resolved Python placeholder host is unsupported")
    rendered = prompt.replace(placeholder, replacement)
    _require(placeholder not in rendered,
             "resolved Python placeholder was not rendered")
    return rendered


def _required_native_tools(case: Mapping[str, object]) -> tuple[str, ...]:
    value = case.get("required_tools")
    if value is None:
        return ()
    _require(isinstance(value, list), "native case required_tools must be a list")
    _require(bool(value), "native case required_tools must be nonempty")
    _require(all(isinstance(item, str) and bool(item) for item in value),
             "native case required_tools must contain nonempty names")
    _require(len(value) == len(set(value)), "native case required_tools contains duplicates")
    unknown = sorted(set(value) - _SUPPORTED_REQUIRED_TOOLS)
    _require(not unknown, f"native case has unsupported required tools: {unknown!r}")
    return tuple(sorted(value))


def _declared_artifacts(case: Mapping[str, object], repo_root: Path) -> tuple[str, ...]:
    declared: list[str] = []
    candidates: list[object] = []
    checks = case.get("checks", [])
    _require(isinstance(checks, list), "native case checks are malformed")
    for check in checks:
        _require(isinstance(check, Mapping), "native case check is malformed")
        kind = check.get("type")
        value = (check.get("source") if kind == "text" else
                 check.get("pointer_path") if kind == "native_verification_pointer" else
                 check.get("path"))
        if kind == "text" and value == "final_text":
            continue
        if kind not in {"text", "file_exists", "json_field", "native_verification_pointer"}:
            continue
        candidates.append(value)
    if case.get("layer") == "parity":
        pair_plan = native_eval_pairing.compile_pair_plan(case, repo_root)
        pair_paths = pair_plan.get("declared_artifact_paths")
        _require(isinstance(pair_paths, list), "native pair plan artifact paths are malformed")
        candidates.extend(pair_paths)
    for value in candidates:
        _require(isinstance(value, str) and bool(value), "declared artifact path is malformed")
        relative = PurePosixPath(value)
        _require(not relative.is_absolute()
                 and "\\" not in value and value == relative.as_posix()
                 and all(part not in {"", ".", ".."} for part in relative.parts),
                 f"declared artifact path is not canonical: {value}")
        canonical = relative.as_posix()
        if canonical not in declared:
            declared.append(canonical)
    _require(len(declared) <= _ARTIFACT_COUNT_LIMIT,
             f"native case declares more than {_ARTIFACT_COUNT_LIMIT} artifacts")
    return tuple(declared)


def _runtime_identity(
    *, case: Mapping[str, object], host: str, mode: str, model: str,
    executable: str, cli_version: str, staged_root: Path, skill_root: Path,
    fixture_root: Path, settings: Mapping[str, object], attempt: Path,
    command: list[str], environment: Mapping[str, str],
    instruction_inputs: Mapping[str, object] | None = None,
    trusted_input_root: Path | None = None,
    staged_tree_exclusions: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    runtime_settings = _relocated(dict(settings), attempt)
    _require(isinstance(runtime_settings, dict), "runtime settings could not be relocated")
    explicit_activation = runtime_settings.get("claude_explicit_activation")
    if explicit_activation is not None:
        _require(isinstance(explicit_activation, dict),
                 "Claude explicit activation settings are malformed")
        prompt = explicit_activation.get("prompt")
        _require(isinstance(prompt, str), "Claude explicit activation prompt is malformed")
        attempt_prefix = str(attempt)
        relocated_prompt = prompt.replace(
            attempt_prefix + os.sep, "<attempt_dir>" + os.sep,
        )
        _require(attempt_prefix not in relocated_prompt,
                 "Claude explicit activation prompt cannot be relocated")
        explicit_activation["prompt"] = relocated_prompt
    identity: dict[str, Any] = {
        "schema_version": "native-eval-runtime/v1",
        "case_id": case["id"],
        "host": host,
        "mode": mode,
        "model": model,
        "cli_path": executable,
        "cli_version": cli_version,
        "settings": runtime_settings,
        "relocations": {"attempt_dir": "<attempt_dir>", "scope": "exact staged launch path"},
        "command_sha256": hashlib.sha256(_canonical_json(_relocated(command, attempt))).hexdigest(),
        "environment_sha256": hashlib.sha256(_canonical_json(_relocated(dict(environment), attempt))).hexdigest(),
        "staged_tree_sha256": _tree_digest(
            staged_root, exclusions=staged_tree_exclusions, relocation_root=attempt,
        ),
        "skill_catalog_sha256": _tree_digest(skill_root),
        "fixture_tree_sha256": _tree_digest(fixture_root),
        "fixture_setup_sha256": hashlib.sha256(Path(fixture_setup.__file__).read_bytes()).hexdigest(),
        "instruction_inputs": dict(instruction_inputs or {}),
        "trusted_input_tree_sha256": _tree_digest(trusted_input_root) if trusted_input_root else None,
    }
    if staged_tree_exclusions is not None:
        identity["staged_tree_exclusions"] = dict(staged_tree_exclusions)
    identity["digest"] = hashlib.sha256(_canonical_json(identity)).hexdigest()
    return identity


def _native_toolchain_identity(
    prepared: native_eval_toolchain.PreparedNativeToolchain,
) -> dict[str, object]:
    return json.loads(_canonical_json(prepared.runtime_identity))


def _merge_staged_file_exclusions(
    current: Mapping[str, object] | None, paths: tuple[str, ...],
) -> dict[str, object]:
    roots = list(current.get("root_directories", [])) if current else []
    files = list(current.get("files", [])) if current else []
    for path in paths:
        if path not in files:
            files.append(path)
    return {"root_directories": roots, "files": files}


def _prepared_upstream_integration(
    attempt: Path, value: object,
) -> native_eval_upstream.PreparedUpstreamIntegration | None:
    if value is None:
        return None
    _require(isinstance(value, dict) and set(value) == {
        "host", "source_relative", "runtime_identity",
    }, "prepared upstream integration settings are malformed")
    host = value["host"]
    relative = value["source_relative"]
    identity = value["runtime_identity"]
    path = PurePosixPath(relative) if isinstance(relative, str) else None
    _require(host in {"claude", "codex"}
             and path is not None and "\\" not in relative
             and path.as_posix() == relative
             and all(part not in {"", ".", ".."} for part in path.parts)
             and isinstance(identity, dict) and identity.get("host") == host,
             "prepared upstream integration settings are malformed")
    project = attempt.joinpath(*path.parts)
    skill_relative = ".claude/skills" if host == "claude" else ".agents/skills"
    return native_eval_upstream.PreparedUpstreamIntegration(
        host=host,
        controller_root=project.parent,
        project_root=project,
        skill_root=project.joinpath(*PurePosixPath(skill_relative).parts),
        runtime_identity=json.loads(_canonical_json(identity)),
    )


def _validate_upstream_fixture_destinations(
    fixtures: Sequence[Mapping[str, object]], host: str, identity: Mapping[str, object],
) -> None:
    skill_root = PurePosixPath(".claude/skills" if host == "claude" else ".agents/skills")
    generated = tuple(PurePosixPath(path) for path in native_eval_upstream.generated_paths(identity))
    for fixture in fixtures:
        destination_value = fixture.get("destination")
        _require(isinstance(destination_value, str), "fixture destination is malformed")
        destination = PurePosixPath(destination_value)
        overlaps_skill_root = (
            destination == skill_root
            or destination in skill_root.parents
            or skill_root in destination.parents
        )
        overlaps_generated = any(
            destination == path or destination in path.parents or path in destination.parents
            for path in generated
        )
        _require(not overlaps_skill_root and not overlaps_generated,
                 f"{host.title()} fixture destination overlaps an upstream runtime path: {destination}")


def _stage_trigger(
    case: Mapping[str, object], host_settings: Mapping[str, object], repo: Path,
    stage_root: Path, host: str, prompt: str, trial_identity: str,
) -> tuple[str, native_eval_trigger.TriggerStage | None]:
    if case.get("layer") != "trigger":
        return prompt, None
    source_name = "skills" if host == "claude" else "codex-skills"
    stage = native_eval_trigger.stage_trigger_catalog(
        host, repo / "speckit-pro" / source_name, stage_root,
        str(host_settings["skill"]), trial_identity,
    )
    rendered = prompt.replace("{{skill}}", stage.native_target)
    _require("{{" not in rendered and "}}" not in rendered,
             "native trigger prompt contains an unsupported placeholder")
    return rendered, stage


def _trigger_identity(
    stage: native_eval_trigger.TriggerStage | None, attempt: Path,
) -> dict[str, object] | None:
    if stage is None:
        return None
    serialized = _relocated(stage.as_dict(), attempt)
    _require(isinstance(serialized, dict), "native trigger stage could not be serialized")
    try:
        stage_relative = stage.stage_root.relative_to(attempt).as_posix()
    except ValueError as exc:
        raise ValueError("native trigger stage escaped its attempt") from exc
    serialized["stage_root"] = f"<attempt_dir>/{stage_relative}"
    witnesses = serialized.get("witnesses")
    _require(isinstance(witnesses, dict), "native trigger witnesses could not be serialized")
    for witness in witnesses.values():
        _require(isinstance(witness, dict)
                 and isinstance(witness.get("relative_path"), str),
                 "native trigger witness could not be serialized")
        witness["path"] = (
            f"<attempt_dir>/{stage_relative}/"
            f"{PurePosixPath(witness['relative_path']).as_posix()}"
        )
    return serialized


def _atomic_write_once(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".pending-{uuid.uuid4().hex}")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)
