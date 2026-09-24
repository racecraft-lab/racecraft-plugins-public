"""Populate a native-evaluation workspace from a sealed fixture plan."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Mapping


SCHEMA_VERSION = "native-eval-fixtures/v1"
GIT_SCHEMA_VERSION = "native-eval-fixtures/v2"
GIT_FIXTURE_RECIPE = "baseline-feature-origin-main/v1"
GIT_COMMAND_TIMEOUT_SECONDS = 30
GIT_CONTROLS_SCHEMA_VERSION = "native-eval-git-controls/v1"
_GIT_RESERVED_ROOTS = frozenset({".agents", ".claude", ".codex", ".git"})


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _relative_path(value: object, label: str) -> PurePosixPath:
    _require(isinstance(value, str) and bool(value), f"{label} must be nonempty text")
    _require("\\" not in value, f"{label} must use repository-style separators")
    path = PurePosixPath(value)
    _require(
        not path.is_absolute()
        and path.as_posix() == value
        and all(part not in {"", ".", ".."} for part in path.parts),
        f"{label} must be a canonical relative path",
    )
    return path


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    _require(len(pairs) == len({key for key, _value in pairs}), "fixture plan contains a duplicate JSON key")
    return dict(pairs)


def load_plan(path: str | Path) -> dict[str, Any]:
    """Read a strict fixture plan without accepting duplicate object keys."""
    plan_path = Path(path)
    try:
        value = json.loads(plan_path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"fixture plan could not be read: {exc}") from exc
    _require(isinstance(value, dict), "fixture plan must be an object")
    source_root = value.get("source_root")
    if isinstance(source_root, str) and not Path(source_root).is_absolute():
        relative = _relative_path(source_root, "fixture source_root")
        value["source_root"] = str(plan_path.resolve(strict=True).parent.joinpath(*relative.parts))
    return value


def _safe_parent(workspace: Path, destination: PurePosixPath) -> Path:
    current = workspace
    for part in destination.parts[:-1]:
        current = current / part
        try:
            status = current.lstat()
        except FileNotFoundError:
            current.mkdir(mode=0o700)
            status = current.lstat()
        _require(not stat.S_ISLNK(status.st_mode), f"fixture destination parent is a symlink: {destination}")
        _require(stat.S_ISDIR(status.st_mode), f"fixture destination parent is not a directory: {destination}")
    return current


def _source_root_and_workspace(plan: Mapping[str, object], workspace: str | Path) -> tuple[Path, Path]:
    source_root_value = plan["source_root"]
    _require(isinstance(source_root_value, str) and Path(source_root_value).is_absolute(),
             "fixture source_root must be absolute")
    try:
        source_root = Path(source_root_value).resolve(strict=True)
    except OSError as exc:
        raise ValueError("fixture source_root is unavailable") from exc
    _require(source_root.is_dir(), "fixture source_root must be a directory")

    return source_root, _workspace_directory(workspace)


def _workspace_directory(workspace: str | Path) -> Path:
    target = Path(workspace)
    _require(target.is_absolute(), "fixture workspace must be absolute")
    _require(not target.is_symlink(), "fixture workspace must not be a symlink")
    try:
        target = target.resolve(strict=True)
    except OSError as exc:
        raise ValueError("fixture workspace is unavailable") from exc
    _require(target.is_dir(), "fixture workspace must be a directory")
    return target


def _fixture_records(
    fixtures: object,
    source_root: Path,
    *,
    label_prefix: str = "fixture",
) -> list[tuple[PurePosixPath, bytes]]:
    _require(isinstance(fixtures, list),
             "fixture plan fixtures must be a list" if label_prefix == "fixture" else f"{label_prefix} fixtures must be a list")
    destinations: list[PurePosixPath] = []
    records: list[tuple[PurePosixPath, bytes]] = []
    for index, fixture in enumerate(fixtures):
        label = f"{label_prefix} {index + 1}"
        _require(isinstance(fixture, dict) and set(fixture) == {"source", "destination", "sha256"},
                 f"{label} has malformed fields")
        source_name = _relative_path(fixture["source"], f"{label} source")
        destination = _relative_path(fixture["destination"], f"{label} destination")
        digest = fixture["sha256"]
        _require(isinstance(digest, str) and len(digest) == 64
                 and all(character in "0123456789abcdef" for character in digest),
                 f"{label} digest is malformed")
        source = source_root.joinpath(*source_name.parts)
        _require(not source.is_symlink(), f"{label} source must not be a symlink")
        try:
            resolved_source = source.resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"{label} source is unavailable") from exc
        _require(resolved_source.is_relative_to(source_root), f"{label} source escaped its staged root")
        _require(resolved_source.is_file(), f"{label} source is unavailable")
        try:
            payload = resolved_source.read_bytes()
        except OSError as exc:
            raise ValueError(f"{label} source is unavailable") from exc
        _require(hashlib.sha256(payload).hexdigest() == digest, f"{label} digest does not match staged bytes")
        destinations.append(destination)
        records.append((destination, payload))

    _require(len(destinations) == len(set(destinations)), "fixture destinations contain duplicates")
    for index, left in enumerate(destinations):
        for right in destinations[index + 1:]:
            overlap = left.parts == right.parts[:len(left.parts)] or right.parts == left.parts[:len(right.parts)]
            _require(not overlap, "fixture destinations overlap")
    return records


def _write_records(
    target: Path,
    records: list[tuple[PurePosixPath, bytes]],
    *,
    replace: frozenset[PurePosixPath] = frozenset(),
) -> list[str]:
    copied: list[str] = []
    for destination, payload in records:
        parent = _safe_parent(target, destination)
        output = parent / destination.name
        flags = os.O_WRONLY
        if destination in replace:
            flags |= os.O_TRUNC
        else:
            flags |= os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(output, flags, 0o600)
        except FileExistsError as exc:
            raise ValueError(f"fixture destination already exists: {destination}") from exc
        except FileNotFoundError as exc:
            raise ValueError(f"fixture baseline destination is unavailable: {destination}") from exc
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
        except Exception:
            if destination not in replace:
                try:
                    output.unlink()
                except OSError:
                    pass
            raise
        copied.append(destination.as_posix())
    return copied


def _feature_deletion_paths(
    value: object,
    baseline: list[tuple[PurePosixPath, bytes]],
    feature: list[tuple[PurePosixPath, bytes]],
) -> list[PurePosixPath]:
    """Validate explicit file deletions applied only to the feature overlay."""
    _require(isinstance(value, list) and bool(value),
             "git fixture feature_deletions must be a nonempty list")
    paths = [_relative_path(item, "git fixture feature deletion") for item in value]
    _require(len(paths) == len(set(paths)),
             "git fixture feature_deletions contain duplicates")
    baseline_paths = {path for path, _payload in baseline}
    feature_paths = {path for path, _payload in feature}
    for path in paths:
        _require(path.parts[0].casefold() not in _GIT_RESERVED_ROOTS,
                 "git fixture feature deletion targets a reserved runtime path")
        _require(path in baseline_paths,
                 "git fixture feature deletion must name an exact baseline file")
        _require(path not in feature_paths,
                 "git fixture feature deletion conflicts with a feature fixture")
    for index, left in enumerate(paths):
        for right in paths[index + 1:]:
            overlap = (left.parts == right.parts[:len(left.parts)]
                       or right.parts == left.parts[:len(right.parts)])
            _require(not overlap, "git fixture feature_deletions overlap")
    return paths


def _apply_feature_deletions(target: Path, paths: list[PurePosixPath]) -> list[str]:
    """Delete validated baseline files without following symlinks or escaping the workspace."""
    deleted: list[str] = []
    for path in paths:
        parent = _safe_parent(target, path)
        candidate = parent / path.name
        try:
            status = candidate.lstat()
        except OSError as exc:
            raise ValueError(f"git fixture feature deletion is unavailable: {path}") from exc
        _require(stat.S_ISREG(status.st_mode) and not stat.S_ISLNK(status.st_mode),
                 f"git fixture feature deletion is not a regular file: {path}")
        try:
            candidate.unlink()
        except OSError as exc:
            raise ValueError(f"git fixture feature deletion failed: {path}") from exc
        deleted.append(path.as_posix())
    return deleted


def _git_environment(config_path: Path) -> dict[str, str]:
    """Create a small environment which deliberately excludes every inherited GIT_* value."""
    path = os.environ.get("PATH")
    _require(isinstance(path, str) and bool(path), "fixture git PATH is unavailable")
    return {
        "PATH": path,
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": str(config_path),
        "GIT_AUTHOR_NAME": "Native Eval Fixture",
        "GIT_AUTHOR_EMAIL": "native-eval@example.invalid",
        "GIT_COMMITTER_NAME": "Native Eval Fixture",
        "GIT_COMMITTER_EMAIL": "native-eval@example.invalid",
        "GIT_AUTHOR_DATE": "2000-01-01T00:00:00 +0000",
        "GIT_COMMITTER_DATE": "2000-01-01T00:00:00 +0000",
    }


def _same_git_executable(git: str, executable: str) -> bool:
    """True when the pinned git resolves identically to the discovered git."""
    candidate = git if os.path.isabs(git) else shutil.which(git)
    return candidate is not None and str(Path(candidate).resolve()) == str(Path(executable).resolve())


def _run_git(git: str, workspace: Path, environment: dict[str, str], arguments: list[str], label: str) -> str:
    executable = shutil.which("git")
    _require(
        isinstance(executable, str) and _same_git_executable(git, executable),
        f"git fixture {label} executable does not match the pinned git runtime",
    )
    try:
        completed = subprocess.run(
            [executable, *arguments], cwd=workspace, env=environment, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=GIT_COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"git fixture {label} timed out") from exc
    if completed.returncode != 0:
        raise ValueError(f"git fixture {label} failed")
    try:
        return completed.stdout.decode("utf-8", "strict").strip()
    except UnicodeDecodeError as exc:
        raise ValueError(f"git fixture {label} returned invalid output") from exc


def _git_repository(workspace: Path) -> dict[str, object]:
    git = _git_executable()
    temporary = tempfile.TemporaryDirectory(prefix="native-eval-git-")
    temporary_root = Path(temporary.name)
    config = temporary_root / "config"
    template = temporary_root / "template"
    hooks = temporary_root / "hooks"
    config.write_text("", encoding="utf-8")
    template.mkdir(mode=0o700)
    hooks.mkdir(mode=0o700)
    environment = _git_environment(config)
    _run_git(git, workspace, environment, ["init", "--quiet", "--initial-branch=main", f"--template={template}", "."], "init")
    _run_git(git, workspace, environment, ["add", "--all"], "stage baseline")
    _run_git(git, workspace, environment, ["-c", f"core.hooksPath={hooks}", "-c", "maintenance.auto=false", "commit", "--quiet", "--no-gpg-sign", "-m", "native-eval baseline"], "commit baseline")
    baseline_commit = _run_git(git, workspace, environment, ["rev-parse", "HEAD"], "read baseline commit")
    baseline_tree = _run_git(git, workspace, environment, ["rev-parse", "HEAD^{tree}"], "read baseline tree")
    _run_git(git, workspace, environment, ["update-ref", "refs/remotes/origin/main", baseline_commit], "set origin/main")
    _run_git(git, workspace, environment, ["switch", "--quiet", "-c", "feature"], "create feature branch")
    return {"git": git, "environment": environment, "hooks": hooks, "temporary": temporary,
            "baseline_commit": baseline_commit, "baseline_tree": baseline_tree}


def _git_executable() -> str:
    git = shutil.which("git")
    _require(isinstance(git, str) and bool(git), "git executable is unavailable")
    try:
        resolved = Path(git).resolve(strict=True)
        status = resolved.stat()
    except OSError as exc:
        raise ValueError("git executable is unavailable") from exc
    _require(stat.S_ISREG(status.st_mode), "git executable is unavailable")
    return str(resolved)


def git_runtime_identity() -> dict[str, str]:
    """Identify the exact helper executable and source used for Git preparation."""
    git = _git_executable()
    with tempfile.TemporaryDirectory(prefix="native-eval-git-identity-") as temporary:
        config = Path(temporary) / "config"
        config.write_text("", encoding="utf-8")
        version = _run_git(git, Path.cwd(), _git_environment(config), ["--version"], "read version")
    _require(bool(version), "git executable returned an empty version")
    try:
        helper_bytes = Path(__file__).read_bytes()
    except OSError as exc:
        raise ValueError("fixture helper identity is unavailable") from exc
    return {"path": git, "version": version, "helper_sha256": hashlib.sha256(helper_bytes).hexdigest()}


def _finish_git_repository(workspace: Path, state: dict[str, object]) -> dict[str, object]:
    git = state["git"]
    environment = state["environment"]
    hooks = state["hooks"]
    _require(isinstance(git, str) and isinstance(environment, dict) and isinstance(hooks, Path), "git fixture state is malformed")
    _run_git(git, workspace, environment, ["add", "--all"], "stage feature")
    executable = shutil.which("git")
    _require(
        isinstance(executable, str) and _same_git_executable(git, executable),
        "git fixture semantic diff executable does not match the pinned git runtime",
    )
    try:
        diff = subprocess.run([executable, "diff", "--cached", "--quiet", "origin/main", "--"], cwd=workspace, env=environment,
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                              timeout=GIT_COMMAND_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        raise ValueError("git fixture semantic diff check timed out") from exc
    _require(diff.returncode in {0, 1}, "git fixture semantic diff check failed")
    _require(diff.returncode == 1, "git fixture recipe requires a nonempty semantic diff")
    _run_git(git, workspace, environment, ["-c", f"core.hooksPath={hooks}", "-c", "maintenance.auto=false", "commit", "--quiet", "--no-gpg-sign", "-m", "native-eval feature"], "commit feature")
    receipt = _read_git_receipt(workspace, git, environment)
    baseline_commit = state["baseline_commit"]
    baseline_tree = state["baseline_tree"]
    _require(isinstance(baseline_commit, str) and isinstance(baseline_tree, str), "git fixture state is malformed")
    _require(receipt["baseline_commit"] == baseline_commit and receipt["baseline_tree"] == baseline_tree,
             "git fixture receipt invariants failed")
    return receipt


def _read_git_receipt(workspace: Path, git: str, environment: dict[str, str]) -> dict[str, object]:
    baseline_commit = _run_git(git, workspace, environment, ["rev-parse", "origin/main"], "read origin/main")
    baseline_tree = _run_git(git, workspace, environment, ["rev-parse", "origin/main^{tree}"], "read baseline tree")
    head = _run_git(git, workspace, environment, ["rev-parse", "HEAD"], "read feature commit")
    tree = _run_git(git, workspace, environment, ["rev-parse", "HEAD^{tree}"], "read feature tree")
    parent = _run_git(git, workspace, environment, ["rev-parse", "HEAD^"], "read feature parent")
    branch = _run_git(git, workspace, environment, ["symbolic-ref", "--short", "HEAD"], "read branch")
    clean = not _run_git(git, workspace, environment, ["status", "--porcelain=v1"], "check clean")
    executable = shutil.which("git")
    _require(
        isinstance(executable, str) and _same_git_executable(git, executable),
        "git fixture semantic receipt executable does not match the pinned git runtime",
    )
    try:
        diff = subprocess.run([executable, "diff", "--quiet", "origin/main", "--"], cwd=workspace, env=environment,
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                              timeout=GIT_COMMAND_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        raise ValueError("git fixture semantic receipt check timed out") from exc
    _require(diff.returncode in {0, 1}, "git fixture semantic receipt check failed")
    _require(
        branch == "feature" and clean and parent == baseline_commit and head != baseline_commit
        and tree != baseline_tree and diff.returncode == 1,
        "git fixture receipt invariants failed",
    )
    return {
        "schema_version": "native-eval-git-fixture/v1",
        "recipe": GIT_FIXTURE_RECIPE,
        "baseline_commit": baseline_commit,
        "baseline_tree": baseline_tree,
        "feature_commit": head,
        "feature_tree": tree,
        "origin_main": baseline_commit,
        "head": head,
        "branch": branch,
        "clean": clean,
        "nonempty_diff": True,
    }


def _regular_git_control_bytes(workspace: Path) -> tuple[bytes, bytes]:
    git_dir = workspace / ".git"
    try:
        git_status = git_dir.lstat()
    except OSError as exc:
        raise ValueError("git fixture control directory is unavailable") from exc
    _require(stat.S_ISDIR(git_status.st_mode) and not stat.S_ISLNK(git_status.st_mode),
             "git fixture control directory is unsafe")
    try:
        paths = list(git_dir.rglob("*"))
    except OSError as exc:
        raise ValueError("git fixture control paths are unavailable") from exc
    for path in paths:
        try:
            _require(not stat.S_ISLNK(path.lstat().st_mode), "git fixture control paths contain a symlink")
        except OSError as exc:
            raise ValueError("git fixture control paths are unavailable") from exc
    for forbidden in (git_dir / "commondir", git_dir / "objects" / "info" / "alternates"):
        try:
            forbidden.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ValueError("git fixture control paths are unavailable") from exc
        raise ValueError("git fixture control paths contain a redirect")

    def read_regular(path: Path, label: str) -> bytes:
        try:
            status = path.lstat()
        except OSError as exc:
            raise ValueError(f"git fixture {label} is unavailable") from exc
        _require(stat.S_ISREG(status.st_mode) and not stat.S_ISLNK(status.st_mode),
                 f"git fixture {label} is unsafe")
        try:
            return path.read_bytes()
        except OSError as exc:
            raise ValueError(f"git fixture {label} is unavailable") from exc

    return read_regular(git_dir / "config", "config"), read_regular(git_dir / "info" / "exclude", "info/exclude")


def snapshot_git_repository_controls(workspace: str | Path) -> dict[str, object]:
    """Capture the stable regular-file controls before a Git inspection."""
    config, info_exclude = _regular_git_control_bytes(_workspace_directory(workspace))
    return {
        "schema_version": GIT_CONTROLS_SCHEMA_VERSION,
        "git_dir_marker": ".git",
        "config_base64": base64.b64encode(config).decode("ascii"),
        "config_sha256": hashlib.sha256(config).hexdigest(),
        "info_exclude_base64": base64.b64encode(info_exclude).decode("ascii"),
        "info_exclude_sha256": hashlib.sha256(info_exclude).hexdigest(),
        "git_runtime": git_runtime_identity(),
    }


def _validate_git_controls(workspace: Path, controls: object) -> str:
    fields = {"schema_version", "git_dir_marker", "config_base64", "config_sha256", "info_exclude_base64", "info_exclude_sha256", "git_runtime"}
    _require(isinstance(controls, Mapping) and set(controls) == fields, "git fixture controls are malformed")
    _require(controls["schema_version"] == GIT_CONTROLS_SCHEMA_VERSION and controls["git_dir_marker"] == ".git",
             "git fixture controls have an unsupported schema")
    expected: list[bytes] = []
    for field in ("config", "info_exclude"):
        encoded, digest = controls[f"{field}_base64"], controls[f"{field}_sha256"]
        _require(isinstance(encoded, str) and isinstance(digest, str), "git fixture controls are malformed")
        try:
            value = base64.b64decode(encoded.encode("ascii"), validate=True)
        except (UnicodeError, ValueError) as exc:
            raise ValueError("git fixture controls are malformed") from exc
        _require(hashlib.sha256(value).hexdigest() == digest, "git fixture controls have an invalid digest")
        expected.append(value)
    actual = _regular_git_control_bytes(workspace)
    _require(tuple(expected) == actual, "git fixture controls do not match workspace")
    runtime = controls["git_runtime"]
    _require(isinstance(runtime, Mapping) and set(runtime) == {"path", "version", "helper_sha256"},
             "git fixture controls are malformed")
    _require(all(isinstance(runtime[key], str) for key in runtime), "git fixture controls are malformed")
    actual_runtime = git_runtime_identity()
    _require(runtime == actual_runtime, "git fixture runtime identity does not match")
    return actual_runtime["path"]


def inspect_git_repository(workspace: str | Path, controls: object) -> dict[str, object]:
    """Validate a sealed Git workspace after validating its local configuration."""
    target = _workspace_directory(workspace)
    git = _validate_git_controls(target, controls)
    with tempfile.TemporaryDirectory(prefix="native-eval-git-inspect-") as temporary:
        config = Path(temporary) / "config"
        config.write_text("", encoding="utf-8")
        return _read_git_receipt(target, git, _git_environment(config))


def materialize_workspace(plan: Mapping[str, object], workspace: str | Path) -> dict[str, object]:
    """Populate v1 fixtures or the one fixed, local-only v2 Git recipe."""
    _require(isinstance(plan, Mapping), "fixture plan has malformed fields")
    version = plan.get("schema_version")
    if version == SCHEMA_VERSION:
        _require(set(plan) == {"schema_version", "source_root", "fixtures"}, "fixture plan has malformed fields")
        source_root, target = _source_root_and_workspace(plan, workspace)
        copied = _write_records(target, _fixture_records(plan["fixtures"], source_root))
        return {"copied": copied, "git_repository": None}

    _require(version == GIT_SCHEMA_VERSION, "fixture plan has an unsupported schema version")
    _require(set(plan) == {"schema_version", "source_root", "fixtures", "git_repository"},
             "fixture plan has malformed fields")
    source_root, target = _source_root_and_workspace(plan, workspace)
    _require(not any(target.iterdir()), "git fixture workspace must be empty")
    git_plan = plan["git_repository"]
    _require(isinstance(git_plan, Mapping) and set(git_plan) in (
        {"recipe", "baseline"},
        {"recipe", "baseline", "worktrees"},
        {"recipe", "baseline", "feature_deletions"},
        {"recipe", "baseline", "worktrees", "feature_deletions"},
    ),
             "git fixture has malformed fields")
    _require(git_plan["recipe"] == GIT_FIXTURE_RECIPE, "git fixture has an unsupported recipe")
    worktrees = _worktree_records(git_plan["worktrees"]) if "worktrees" in git_plan else []
    baseline = _fixture_records(git_plan["baseline"], source_root, label_prefix="git baseline")
    _require(bool(baseline), "git fixture baseline must be nonempty")
    feature = _fixture_records(plan["fixtures"], source_root)
    feature_deletions = (
        _feature_deletion_paths(git_plan["feature_deletions"], baseline, feature)
        if "feature_deletions" in git_plan else []
    )
    _require(bool(feature) or bool(feature_deletions),
             "git fixture feature overlay must add, replace, or delete a file")
    all_destinations = [destination for destination, _payload in baseline + feature]
    _require(not worktrees or all(path.parts[0].casefold() != ".worktrees" for path in all_destinations),
             "git worktree fixtures reserve the .worktrees directory")
    _require(all(destination.parts[0].casefold() not in _GIT_RESERVED_ROOTS for destination in all_destinations),
             "git fixture cannot target a reserved runtime path")
    _validate_no_cross_overlap(baseline, feature)
    _git_executable()
    copied = _write_records(target, baseline)
    state = _git_repository(target)
    try:
        copied.extend(_write_records(target, feature, replace=frozenset(destination for destination, _payload in baseline)))
        _apply_feature_deletions(target, feature_deletions)
        receipt = _finish_git_repository(target, state)
        linked = _materialize_worktrees(target, state, receipt, worktrees) if worktrees else []
    finally:
        temporary = state.get("temporary")
        if isinstance(temporary, tempfile.TemporaryDirectory):
            temporary.cleanup()
    result = {"copied": copied, "git_repository": receipt}
    if worktrees:
        result["worktrees"] = linked
    return result


def _worktree_records(value: object) -> list[dict[str, str]]:
    """Validate the entire bounded topology before creating any Git state."""
    _require(isinstance(value, list) and 1 <= len(value) <= 4,
             "git worktrees must contain one to four entries")
    paths: set[str] = set()
    branches: set[str] = set()
    result = []
    for row in value:
        _require(isinstance(row, dict) and set(row) == {"path", "branch", "revision"},
                 "git worktree entry has malformed fields")
        path, branch, revision = row["path"], row["branch"], row["revision"]
        _require(isinstance(path, str) and re.fullmatch(r"\.worktrees/[a-z0-9][a-z0-9-]{0,63}", path) is not None,
                 "git worktree path must be a confined .worktrees child")
        _require(isinstance(branch, str) and re.fullmatch(r"scenario/[a-z0-9][a-z0-9-]{0,63}", branch) is not None,
                 "git worktree branch must be a scenario branch")
        _require(revision in ("baseline", "feature"), "git worktree revision must be baseline or feature")
        _require(path not in paths and branch not in branches, "git worktrees contain a duplicate path or branch")
        paths.add(path)
        branches.add(branch)
        result.append(dict(row))
    return result


def _materialize_worktrees(
    workspace: Path, state: dict[str, object], receipt: dict[str, object], rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    """Create actual linked worktrees without hooks, remotes, or external paths."""
    git, environment, hooks = state["git"], state["environment"], state["hooks"]
    exclude = workspace / ".git" / "info" / "exclude"
    exclude.parent.mkdir(exist_ok=True)
    with exclude.open("a", encoding="utf-8") as stream:
        stream.write("\n/.worktrees/\n")
    result = []
    for row in rows:
        target = workspace / row["path"]
        commit = receipt[f"{row['revision']}_commit"]
        _run_git(git, workspace, environment, ["-c", f"core.hooksPath={hooks}", "-c", "core.fsmonitor=false",
                 "worktree", "add", "--quiet", "-b", row["branch"], str(target), commit], "create linked worktree")
        head = _run_git(git, target, environment, ["rev-parse", "HEAD"], "read linked HEAD")
        branch = _run_git(git, target, environment, ["symbolic-ref", "--short", "HEAD"], "read linked branch")
        common = _run_git(git, target, environment, ["rev-parse", "--git-common-dir"], "read linked common directory")
        clean = not _run_git(git, target, environment, ["status", "--porcelain=v1"], "check linked worktree")
        _require(head == commit and branch == row["branch"] and clean
                 and (target / common).resolve() == (workspace / ".git").resolve(),
                 "git linked worktree receipt invariants failed")
        result.append({**row, "head": head, "clean": clean})
    return result


def _validate_no_cross_overlap(
    baseline: list[tuple[PurePosixPath, bytes]], feature: list[tuple[PurePosixPath, bytes]],
) -> None:
    baseline_destinations = {destination for destination, _payload in baseline}
    for destination, _payload in feature:
        for baseline_destination in baseline_destinations:
            nested = destination.parts == baseline_destination.parts[:len(destination.parts)]
            nested = nested or baseline_destination.parts == destination.parts[:len(baseline_destination.parts)]
            _require(destination == baseline_destination or not nested, "git fixture destinations overlap")


def populate_workspace(plan: Mapping[str, object], workspace: str | Path) -> list[str]:
    """Copy exact staged v1 fixture bytes into a confined workspace."""
    _require(isinstance(plan, Mapping) and plan.get("schema_version") == SCHEMA_VERSION,
             "populate_workspace only accepts v1 fixture plans")
    result = materialize_workspace(plan, workspace)
    copied = result["copied"]
    _require(isinstance(copied, list) and all(isinstance(item, str) for item in copied), "fixture result is malformed")
    return copied


def _receipt_path(value: str, workspace: Path) -> Path:
    candidate = Path(value)
    _require(candidate.is_absolute(), "fixture receipt path must be absolute")
    try:
        candidate.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise ValueError("fixture receipt path is unavailable") from exc
    else:
        raise ValueError("fixture receipt path already exists")
    parent = candidate.parent
    try:
        status = parent.lstat()
        resolved_parent = parent.resolve(strict=True)
    except OSError as exc:
        raise ValueError("fixture receipt parent is unavailable") from exc
    _require(stat.S_ISDIR(status.st_mode) and not stat.S_ISLNK(status.st_mode),
             "fixture receipt parent is unsafe")
    resolved_candidate = resolved_parent / candidate.name
    _require(not resolved_candidate.is_relative_to(workspace), "fixture receipt path must be outside workspace")
    return resolved_candidate


def _write_receipt(path: Path, result: dict[str, object]) -> None:
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise ValueError("fixture receipt path already exists") from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    receipt_value: str | None = None
    if len(arguments) == 3 and arguments[0] == "--receipt-path":
        receipt_value, plan_value = arguments[1:]
    elif len(arguments) == 1:
        plan_value = arguments[0]
    else:
        raise SystemExit("usage: native_eval_fixture_setup.py [--receipt-path PATH] PLAN.json")
    plan = load_plan(plan_value)
    if plan.get("schema_version") == SCHEMA_VERSION:
        _require(receipt_value is None, "fixture receipt path is only supported for v2 plans")
        print(json.dumps({"schema_version": SCHEMA_VERSION, "copied": populate_workspace(plan, Path.cwd())}, separators=(",", ":")))
    else:
        workspace = _workspace_directory(Path.cwd())
        receipt = _receipt_path(receipt_value, workspace) if receipt_value is not None else None
        result = {"schema_version": GIT_SCHEMA_VERSION, **materialize_workspace(plan, workspace)}
        if receipt is not None:
            _write_receipt(receipt, result)
        print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = (
    "GIT_CONTROLS_SCHEMA_VERSION", "GIT_FIXTURE_RECIPE", "GIT_SCHEMA_VERSION", "SCHEMA_VERSION",
    "git_runtime_identity", "inspect_git_repository", "load_plan", "main", "materialize_workspace", "populate_workspace",
    "snapshot_git_repository_controls",
)
