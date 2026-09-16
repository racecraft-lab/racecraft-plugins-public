"""Controller-side, read-only Git observations for native-evaluation fixtures."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
from typing import Any, Mapping

from native_eval_fixture_setup import (
    GIT_COMMAND_TIMEOUT_SECONDS,
    GIT_FIXTURE_RECIPE,
    _git_environment,
    _validate_git_controls,
    _workspace_directory,
)


SCHEMA_VERSION = "native-eval-git-observation/v1"
WORKTREE_SCHEMA_VERSION = "native-eval-git-worktrees/v1"
TOPOLOGY_SCHEMA_VERSION = "native-eval-git-topology/v1"
TOPOLOGY_COMPARISON_SCHEMA_VERSION = "native-eval-git-topology-comparison/v1"
RECEIPT_SCHEMA_VERSION = "native-eval-git-fixture/v1"
MAX_COMMITS = 50
MAX_PATHS = 2_000
MAX_TOTAL_COMMIT_PATHS = 5_000
MAX_OUTPUT_BYTES = 1_048_576
MAX_MESSAGE_BYTES = 16_384
_HEX = frozenset("0123456789abcdef")


class GitObservationError(ValueError):
    """Raised when a complete, trustworthy Git observation is unavailable."""


def observe_git_state(
    workspace: str | Path,
    controls: object,
    initial_receipt: object,
) -> dict[str, Any]:
    """Return bounded Git outcome evidence relative to the initial feature commit."""

    receipt = _validate_receipt(initial_receipt)
    try:
        target = _workspace_directory(workspace)
        git = _validate_git_controls(target, controls)
    except ValueError as exc:
        raise GitObservationError(str(exc)) from exc

    with tempfile.TemporaryDirectory(prefix="native-eval-git-observe-") as temporary:
        temporary_root = Path(temporary)
        config = temporary_root / "config"
        hooks = temporary_root / "hooks"
        config.write_text("", encoding="utf-8")
        hooks.mkdir(mode=0o700)
        try:
            environment = _observation_environment(_git_environment(config), hooks)
        except ValueError as exc:
            raise GitObservationError(str(exc)) from exc
        return _observe(target, git, environment, receipt)


def observe_registered_worktrees(
    workspace: str | Path,
    controls: object,
    initial_receipt: object,
    expected_worktrees: object,
) -> dict[str, Any]:
    """Observe only the declared linked worktrees after proving every Git link is confined."""

    receipt = _validate_receipt(initial_receipt)
    rows = _validate_expected_worktrees(expected_worktrees, receipt)
    try:
        target = _workspace_directory(workspace)
        git = _validate_git_controls(target, controls)
    except ValueError as exc:
        raise GitObservationError(str(exc)) from exc
    with tempfile.TemporaryDirectory(prefix="native-eval-git-worktrees-") as temporary:
        temporary_root = Path(temporary)
        config = temporary_root / "config"
        hooks = temporary_root / "hooks"
        config.write_text("", encoding="utf-8")
        hooks.mkdir(mode=0o700)
        environment = _observation_environment(_git_environment(config), hooks)
        _preflight_registered_worktrees(target, rows)
        listed = _worktree_listing(git, target, environment)
        expected_paths = {target, *(target / row["path"] for row in rows)}
        _need(set(listed) == expected_paths,
              "registered Git worktree topology does not match the controller declaration")
        observed = []
        for row in rows:
            child = target / row["path"]
            current = listed[child]
            observed.append({
                "initial": dict(row),
                "head": current["head"],
                "branch": current["branch"],
                "status": _status(git, child, environment),
            })
        return {"schema_version": WORKTREE_SCHEMA_VERSION, "worktrees": observed}


def snapshot_git_topology(
    workspace: str | Path,
    controls: object,
    initial_receipt: object,
) -> dict[str, Any]:
    """Return an opt-in, controller-attested snapshot of actual local Git topology."""

    receipt = _validate_receipt(initial_receipt)
    try:
        target = _workspace_directory(workspace)
        git = _validate_git_controls(target, controls)
    except ValueError as exc:
        raise GitObservationError(str(exc)) from exc
    with tempfile.TemporaryDirectory(prefix="native-eval-git-topology-") as temporary:
        temporary_root = Path(temporary)
        config = temporary_root / "config"
        hooks = temporary_root / "hooks"
        config.write_text("", encoding="utf-8")
        hooks.mkdir(mode=0o700)
        environment = _observation_environment(_git_environment(config), hooks)
        children = _preflight_dynamic_worktrees(target)
        listed = _worktree_listing(git, target, environment)
        expected = {target, *children}
        _need(set(listed) == expected,
              "registered Git worktree topology does not match confined filesystem state")
        worktrees = []
        for path in sorted(expected, key=lambda item: _topology_path(target, item)):
            row = listed[path]
            worktrees.append({
                "path": _topology_path(target, path), "head": row["head"],
                "branch": row["branch"],
                "status": _topology_status(git, path, environment, path == target),
            })
        return _validate_topology({
            "schema_version": TOPOLOGY_SCHEMA_VERSION,
            "initial_feature_commit": receipt["feature_commit"],
            "branches": _local_branches(git, target, environment),
            "worktrees": worktrees,
        })


def observe_git_topology(
    workspace: str | Path,
    controls: object,
    initial_receipt: object,
    baseline: object,
) -> dict[str, Any]:
    """Compare a caller-captured actual topology snapshot with current confined state."""

    initial = _validate_topology(baseline, baseline=True)
    current = snapshot_git_topology(workspace, controls, initial_receipt)
    _need(initial["initial_feature_commit"] == current["initial_feature_commit"],
          "Git topology baseline belongs to another fixture")
    return {
        "schema_version": TOPOLOGY_COMPARISON_SCHEMA_VERSION,
        "initial": initial,
        "current": current,
    }


def _validate_expected_worktrees(
    value: object, receipt: Mapping[str, object],
) -> list[dict[str, Any]]:
    _need(isinstance(value, list) and 1 <= len(value) <= 4,
          "expected Git worktrees are malformed")
    paths: set[str] = set()
    branches: set[str] = set()
    result = []
    for row in value:
        _need(isinstance(row, Mapping)
              and set(row) == {"path", "branch", "revision", "head", "clean"},
              "expected Git worktree entry is malformed")
        path, branch, revision = row["path"], row["branch"], row["revision"]
        _need(isinstance(path, str)
              and re.fullmatch(r"\.worktrees/[a-z0-9][a-z0-9-]{0,63}", path) is not None,
              "expected Git worktree path is malformed")
        _need(isinstance(branch, str)
              and re.fullmatch(r"scenario/[a-z0-9][a-z0-9-]{0,63}", branch) is not None,
              "expected Git worktree branch is malformed")
        _need(revision in {"baseline", "feature"},
              "expected Git worktree revision is malformed")
        _need(row["head"] == receipt[f"{revision}_commit"] and row["clean"] is True,
              "expected Git worktree receipt is inconsistent")
        _need(path not in paths and branch not in branches,
              "expected Git worktrees contain duplicates")
        paths.add(path)
        branches.add(branch)
        result.append(dict(row))
    return result


def _worktree_listing(
    git: str, workspace: Path, environment: dict[str, str],
) -> dict[Path, dict[str, str | None]]:
    raw = _git(
        git, workspace, environment, ["worktree", "list", "--porcelain", "-z"],
        "list registered worktrees",
    )
    _need(raw.endswith(b"\0\0"), "registered Git worktree list is malformed")
    records: dict[Path, dict[str, str | None]] = {}
    for block in raw[:-2].split(b"\0\0"):
        fields = block.split(b"\0")
        _need(len(fields) == 3 and fields[0].startswith(b"worktree ")
              and fields[1].startswith(b"HEAD ")
              and (fields[2].startswith(b"branch refs/heads/") or fields[2] == b"detached"),
              "registered Git worktree list is malformed")
        raw_path = _decode_text(fields[0][len(b"worktree "):], "registered worktree path")
        path = Path(raw_path)
        _need(path.is_absolute(), "registered Git worktree path is malformed")
        head = _need_oid(
            _decode_text(fields[1][len(b"HEAD "):], "registered worktree HEAD"),
            "registered worktree HEAD",
        )
        branch = None if fields[2] == b"detached" else _decode_text(
            fields[2][len(b"branch refs/heads/"):], "registered worktree branch",
        )
        _need(branch is None or bool(branch), "registered Git worktree branch is malformed")
        _need(path not in records, "registered Git worktree paths are duplicated")
        records[path] = {"head": head, "branch": branch}
    return records


def _topology_path(workspace: Path, path: Path) -> str:
    _need(path == workspace or path.is_relative_to(workspace / ".worktrees"),
          "registered Git worktree path escaped the disposable repository")
    if path == workspace:
        return "."
    relative = path.relative_to(workspace).as_posix()
    _need(re.fullmatch(r"\.worktrees/[a-z0-9][a-z0-9-]{0,63}", relative) is not None,
          "registered Git worktree path is malformed")
    return relative


def _branch_name(value: object, label: str) -> str:
    _need(isinstance(value, str) and 1 <= len(value) <= 255 and "\\" not in value
          and ".." not in value and "@{" not in value and not value.startswith("/")
          and not value.endswith("/") and all(
              part not in {"", ".", ".."} and not part.endswith(".lock")
              and all(32 <= ord(character) < 127 for character in part)
              for part in value.split("/")
          ), f"{label} is malformed")
    return value


def _local_branches(git: str, workspace: Path, environment: dict[str, str]) -> list[dict[str, str]]:
    raw = _git(
        git, workspace, environment,
        ["for-each-ref", "--format=%(refname:short)%00%(objectname)", "refs/heads"],
        "list local branches",
    )
    rows = []
    names: set[str] = set()
    for record in raw.splitlines():
        fields = record.split(b"\0")
        _need(len(fields) == 2, "local branch list is malformed")
        name = _branch_name(_decode_text(fields[0], "local branch name"), "local branch name")
        head = _need_oid(_decode_text(fields[1], "local branch HEAD"), "local branch HEAD")
        _need(name not in names, "local branch list contains duplicates")
        names.add(name)
        rows.append({"name": name, "head": head})
    _need(rows == sorted(rows, key=lambda row: row["name"]), "local branch list is not sorted")
    return rows


def _preflight_dynamic_worktrees(workspace: Path) -> list[Path]:
    """Prove every dynamic child is confined before Git can inspect it."""

    git_root = _preflight_common_git(workspace)
    root_status = _lstat_optional(workspace / ".worktrees", "Git worktree root")
    admin_status = _lstat_optional(git_root / "worktrees", "Git worktree admin root")
    if root_status is None:
        _need(admin_status is None, "Git worktree roots are inconsistent")
        return []
    worktree_root = _real_directory(workspace / ".worktrees", "Git worktree root")
    children = sorted(_directory_entries(worktree_root, "Git worktree root"))
    if admin_status is None:
        _need(not children, "Git worktree roots are inconsistent")
        return []
    for child in children:
        _topology_path(workspace, child)
        _real_directory(child, "registered Git worktree")
    admin_root = _real_directory(git_root / "worktrees", "Git worktree admin root")
    administrators = {
        _validate_linked_git_marker(workspace, child, admin_root) for child in children
    }
    _need(_directory_entries(admin_root, "Git worktree admin root") == administrators,
          "Git worktree admin root contains unbound entries")
    return children


def _preflight_common_git(workspace: Path) -> Path:
    git_root = _real_directory(workspace / ".git", "Git common directory")
    for name in ("commondir", "gitdir", "config.worktree"):
        _need(_lstat_optional(git_root / name, f"Git common {name}") is None,
              f"Git common directory contains forbidden {name}")
    _safe_head(git_root / "HEAD", "Git common HEAD")
    _regular_metadata(git_root / "index", "Git common index", MAX_OUTPUT_BYTES)
    info = _real_directory(git_root / "info", "Git common info")
    _need(_directory_entries(info, "Git common info") == {info / "exclude"},
          "Git common info contains undeclared entries")
    packed_refs = _lstat_optional(git_root / "packed-refs", "Git packed refs")
    if packed_refs is not None:
        _regular_metadata(git_root / "packed-refs", "Git packed refs", MAX_OUTPUT_BYTES)
    _real_tree(git_root / "refs", "Git common refs")
    _real_tree(git_root / "objects", "Git common objects")
    _need(not (git_root / "objects" / "info" / "alternates").exists(),
          "Git common objects declare an external alternate")
    return git_root


def _validate_topology(value: object, *, baseline: bool = False) -> dict[str, Any]:
    _need(isinstance(value, Mapping) and set(value) == {
        "schema_version", "initial_feature_commit", "branches", "worktrees",
    } and value.get("schema_version") == TOPOLOGY_SCHEMA_VERSION,
          "Git topology baseline is malformed")
    feature = _need_oid(value.get("initial_feature_commit"), "Git topology feature commit")
    branches = value.get("branches")
    worktrees = value.get("worktrees")
    _need(isinstance(branches, list) and isinstance(worktrees, list),
          "Git topology baseline is malformed")
    normalized_branches = []
    for row in branches:
        _need(isinstance(row, Mapping) and set(row) == {"name", "head"},
              "Git topology branch is malformed")
        normalized_branches.append({
            "name": _branch_name(row.get("name"), "Git topology branch"),
            "head": _need_oid(row.get("head"), "Git topology branch HEAD"),
        })
    _need(normalized_branches == sorted(normalized_branches, key=lambda row: row["name"])
          and len({row["name"] for row in normalized_branches}) == len(normalized_branches),
          "Git topology branches are malformed")
    normalized_worktrees = []
    for row in worktrees:
        _need(isinstance(row, Mapping) and set(row) == {"path", "head", "branch", "status"},
              "Git topology worktree is malformed")
        path = row.get("path")
        _need(path == "." or isinstance(path, str)
              and re.fullmatch(r"\.worktrees/[a-z0-9][a-z0-9-]{0,63}", path) is not None,
              "Git topology worktree path is malformed")
        branch = row.get("branch")
        _need(branch is None or isinstance(branch, str), "Git topology worktree branch is malformed")
        normalized_worktrees.append({
            "path": path, "head": _need_oid(row.get("head"), "Git topology worktree HEAD"),
            "branch": None if branch is None else _branch_name(branch, "Git topology worktree branch"),
            "status": _status_value(row.get("status"), "Git topology worktree status"),
        })
    _need(normalized_worktrees == sorted(normalized_worktrees, key=lambda row: row["path"])
          and len({row["path"] for row in normalized_worktrees}) == len(normalized_worktrees)
          and [row["path"] for row in normalized_worktrees].count(".") == 1,
          "Git topology worktrees are malformed")
    branch_heads = {row["name"]: row["head"] for row in normalized_branches}
    for row in normalized_worktrees:
        if row["branch"] is not None:
            _need(row["branch"] in branch_heads and branch_heads[row["branch"]] == row["head"],
                  "Git topology worktree branch does not match the branch table")
    if baseline:
        root = next(row for row in normalized_worktrees if row["path"] == ".")
        _need(root["head"] == feature,
              "Git topology baseline root does not match the initial feature commit")
        _need(root["branch"] is not None,
              "Git topology baseline root is detached")
    return {
        "schema_version": TOPOLOGY_SCHEMA_VERSION, "initial_feature_commit": feature,
        "branches": normalized_branches, "worktrees": normalized_worktrees,
    }


def _status_value(value: object, label: str) -> dict[str, Any]:
    _need(isinstance(value, Mapping) and set(value) == {
        "clean", "tracked_dirty", "untracked_dirty", "tracked", "untracked",
    } and all(type(value[key]) is bool for key in ("clean", "tracked_dirty", "untracked_dirty")),
          f"{label} is malformed")
    tracked = value.get("tracked")
    untracked = value.get("untracked")
    _need(isinstance(tracked, list) and isinstance(untracked, list), f"{label} is malformed")
    normalized_tracked = []
    for row in tracked:
        _need(isinstance(row, Mapping) and set(row) == {"path", "index", "worktree"}
              and isinstance(row.get("path"), str) and isinstance(row.get("index"), str)
              and isinstance(row.get("worktree"), str) and len(row["index"]) == 1
              and len(row["worktree"]) == 1, f"{label} is malformed")
        _safe_path(row["path"].encode("utf-8"), label)
        normalized_tracked.append(dict(row))
    for path in untracked:
        _need(isinstance(path, str), f"{label} is malformed")
        _safe_path(path.encode("utf-8"), label)
    _need(normalized_tracked == sorted(normalized_tracked, key=lambda row: row["path"])
          and untracked == sorted(set(untracked))
          and value["clean"] is (not normalized_tracked and not untracked)
          and value["tracked_dirty"] is bool(normalized_tracked)
          and value["untracked_dirty"] is bool(untracked), f"{label} is malformed")
    return {"clean": value["clean"], "tracked_dirty": value["tracked_dirty"],
            "untracked_dirty": value["untracked_dirty"], "tracked": normalized_tracked,
            "untracked": list(untracked)}


def _regular_text(path: Path, label: str, limit: int = 4096) -> str:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise GitObservationError(f"{label} is unavailable") from exc
    _need(stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
          and metadata.st_nlink == 1 and metadata.st_size <= limit,
          f"{label} is unsafe")
    try:
        return path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        raise GitObservationError(f"{label} is unavailable") from exc


def _real_directory(path: Path, label: str) -> Path:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise GitObservationError(f"{label} is unavailable") from exc
    _need(stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode),
          f"{label} is unsafe")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise GitObservationError(f"{label} is unavailable") from exc
    _need(resolved == path.absolute(), f"{label} is unsafe")
    return resolved


def _directory_entries(path: Path, label: str) -> set[Path]:
    try:
        return set(path.iterdir())
    except OSError as exc:
        raise GitObservationError(f"{label} cannot be enumerated") from exc


def _regular_metadata(path: Path, label: str, limit: int) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise GitObservationError(f"{label} is unavailable") from exc
    _need(stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
          and metadata.st_nlink == 1 and metadata.st_size <= limit,
          f"{label} is unsafe")


def _lstat_optional(path: Path, label: str) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise GitObservationError(f"{label} is unavailable") from exc


def _safe_head(path: Path, label: str) -> None:
    text = _regular_text(path, label)
    _need(text.endswith("\n") and text.count("\n") == 1, f"{label} is malformed")
    value = text[:-1]
    if value.startswith("ref: "):
        reference = value[len("ref: "):]
        parts = reference.split("/")
        _need(reference.startswith("refs/heads/") and len(parts) >= 3
              and all(part not in {"", ".", ".."} and not part.endswith(".lock")
                      for part in parts)
              and "\\" not in reference and ".." not in reference and "@{" not in reference
              and all(32 <= ord(character) < 127 for character in reference),
              f"{label} is malformed")
    else:
        _need_oid(value, label)


def _real_tree(path: Path, label: str, *, max_entries: int = 512) -> None:
    _real_directory(path, label)
    pending = [path]
    count = 0
    while pending:
        directory = pending.pop()
        for entry in _directory_entries(directory, label):
            count += 1
            _need(count <= max_entries, f"{label} exceeds its bounded entry count")
            try:
                metadata = entry.lstat()
            except OSError as exc:
                raise GitObservationError(f"{label} entry is unavailable") from exc
            _need(not stat.S_ISLNK(metadata.st_mode), f"{label} contains an unsafe link")
            if stat.S_ISDIR(metadata.st_mode):
                pending.append(entry)
            else:
                _need(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1,
                      f"{label} contains an unsafe entry")


def _preflight_registered_worktrees(
    workspace: Path, rows: list[dict[str, Any]],
) -> None:
    """Prove every path Git list/status may follow before invoking Git."""

    worktree_root = _real_directory(workspace / ".worktrees", "Git worktree root")
    expected_children = {workspace / row["path"] for row in rows}
    _need(_directory_entries(worktree_root, "Git worktree root") == expected_children,
          "Git worktree root contains undeclared entries")

    git_root = _real_directory(workspace / ".git", "Git common directory")
    for name in ("commondir", "gitdir", "config.worktree"):
        _need(_lstat_optional(git_root / name, f"Git common {name}") is None,
              f"Git common directory contains forbidden {name}")
    _safe_head(git_root / "HEAD", "Git common HEAD")
    _regular_metadata(git_root / "index", "Git common index", MAX_OUTPUT_BYTES)
    info = _real_directory(git_root / "info", "Git common info")
    _need(_directory_entries(info, "Git common info") == {info / "exclude"},
          "Git common info contains undeclared entries")
    packed_refs = _lstat_optional(git_root / "packed-refs", "Git packed refs")
    if packed_refs is not None:
        _regular_metadata(git_root / "packed-refs", "Git packed refs", MAX_OUTPUT_BYTES)
    _real_tree(git_root / "refs", "Git common refs")
    _real_tree(git_root / "objects", "Git common objects")
    _need(not (git_root / "objects" / "info" / "alternates").exists(),
          "Git common objects declare an external alternate")

    admin_root = _real_directory(git_root / "worktrees", "Git worktree admin root")
    declared_admin: set[Path] = set()
    for child in expected_children:
        declared_admin.add(_validate_linked_git_marker(workspace, child, admin_root))
    _need(_directory_entries(admin_root, "Git worktree admin root") == declared_admin,
          "Git worktree admin root contains undeclared entries")


def _validate_linked_git_marker(
    workspace: Path, child: Path, admin_root: Path,
) -> Path:
    _real_directory(child, "declared Git worktree")
    marker = child / ".git"
    text = _regular_text(marker, "Git worktree marker")
    _need(text.startswith("gitdir: ") and text.endswith("\n") and text.count("\n") == 1,
          "Git worktree marker is malformed")
    declared_admin = Path(text[len("gitdir: "):-1])
    _need(declared_admin.is_absolute(), "Git worktree marker is malformed")
    _need(declared_admin.parent == admin_root and ".." not in declared_admin.parts,
          "Git worktree marker escaped the disposable repository")
    admin = declared_admin
    _real_directory(admin, "Git worktree admin directory")
    # Which optional entries Git materializes here depends on its version and on
    # the operations that have run, so the contract is "every required entry is
    # present and nothing outside the declared set appears" rather than an exact
    # directory listing. Anything else still fails closed, and the message names
    # the offending entries instead of only reporting that the sets differ.
    required_admin_entries = {
        admin / "HEAD", admin / "commondir", admin / "gitdir", admin / "index",
    }
    optional_admin_entries = {admin / "ORIG_HEAD", admin / "logs", admin / "refs"}
    present_admin_entries = _directory_entries(admin, "Git worktree admin directory")
    missing_admin_entries = sorted(
        path.name for path in required_admin_entries - present_admin_entries
    )
    _need(not missing_admin_entries,
          f"Git worktree admin directory is missing required entries: {missing_admin_entries}")
    undeclared_admin_entries = sorted(
        path.name
        for path in present_admin_entries - required_admin_entries - optional_admin_entries
    )
    _need(not undeclared_admin_entries,
          f"Git worktree admin directory contains undeclared entries: {undeclared_admin_entries}")
    common = _regular_text(admin / "commondir", "Git worktree common directory")
    _need(common == "../..\n", "Git worktree common directory is malformed")
    _need((admin / "../..").resolve(strict=True) == (workspace / ".git").resolve(strict=True),
          "Git worktree common directory escaped the disposable repository")
    gitdir = _regular_text(admin / "gitdir", "Git worktree reverse marker")
    _need(gitdir.endswith("\n") and gitdir.count("\n") == 1,
          "Git worktree reverse marker is malformed")
    _need(Path(gitdir[:-1]) == marker.absolute(),
          "Git worktree reverse marker does not match the declared worktree")
    _safe_head(admin / "HEAD", "Git worktree HEAD")
    if admin / "ORIG_HEAD" in present_admin_entries:
        _need_oid(_regular_text(admin / "ORIG_HEAD", "Git worktree ORIG_HEAD").strip(),
                  "Git worktree ORIG_HEAD")
    _regular_metadata(admin / "index", "Git worktree index", MAX_OUTPUT_BYTES)
    if admin / "logs" in present_admin_entries:
        logs = _real_directory(admin / "logs", "Git worktree logs")
        _need(_directory_entries(logs, "Git worktree logs") == {logs / "HEAD"},
              "Git worktree logs contain undeclared entries")
        _regular_metadata(logs / "HEAD", "Git worktree HEAD log", MAX_OUTPUT_BYTES)
    if admin / "refs" in present_admin_entries:
        refs = _real_directory(admin / "refs", "Git worktree private refs")
        _need(not _directory_entries(refs, "Git worktree private refs"),
              "Git worktree private refs contain undeclared entries")
    return admin


def _validate_receipt(value: object) -> dict[str, Any]:
    fields = {
        "schema_version",
        "recipe",
        "baseline_commit",
        "baseline_tree",
        "feature_commit",
        "feature_tree",
        "origin_main",
        "head",
        "branch",
        "clean",
        "nonempty_diff",
    }
    _need(isinstance(value, Mapping) and set(value) == fields, "initial Git receipt is malformed")
    receipt = dict(value)
    _need(receipt["schema_version"] == RECEIPT_SCHEMA_VERSION, "initial Git receipt has an unsupported schema")
    _need(receipt["recipe"] == GIT_FIXTURE_RECIPE, "initial Git receipt has an unsupported recipe")
    for field in ("baseline_commit", "baseline_tree", "feature_commit", "feature_tree", "origin_main", "head"):
        _need_oid(receipt[field], f"initial Git receipt {field}")
    _need(receipt["baseline_commit"] == receipt["origin_main"], "initial Git receipt baseline/origin mismatch")
    _need(receipt["feature_commit"] == receipt["head"], "initial Git receipt feature/head mismatch")
    _need(receipt["baseline_commit"] != receipt["feature_commit"], "initial Git receipt has no feature commit")
    _need(receipt["baseline_tree"] != receipt["feature_tree"], "initial Git receipt has no feature tree change")
    _need(receipt["branch"] == "feature", "initial Git receipt branch is malformed")
    _need(
        receipt["clean"] is True and receipt["nonempty_diff"] is True,
        "initial Git receipt invariants are malformed",
    )
    return json.loads(json.dumps(receipt, sort_keys=True))


def _observation_environment(base: dict[str, str], hooks: Path) -> dict[str, str]:
    return {
        **base,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_PAGER": "cat",
        "PAGER": "cat",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.hooksPath",
        "GIT_CONFIG_VALUE_0": str(hooks),
    }


def _observe(
    workspace: Path,
    git: str,
    environment: dict[str, str],
    receipt: dict[str, Any],
) -> dict[str, Any]:
    baseline = receipt["baseline_commit"]
    feature = receipt["feature_commit"]
    origin_main = _oid_text(
        _git(
            git,
            workspace,
            environment,
            ["rev-parse", "--verify", "refs/remotes/origin/main^{commit}"],
            "read origin/main",
        ),
        "origin/main",
    )
    baseline_actual = _verified_commit(git, workspace, environment, baseline, "baseline")
    feature_actual = _verified_commit(git, workspace, environment, feature, "feature")
    head = _oid_text(
        _git(git, workspace, environment, ["rev-parse", "--verify", "HEAD^{commit}"], "read HEAD"),
        "HEAD",
    )
    _need(
        origin_main == receipt["origin_main"] == baseline_actual,
        "initial baseline or origin/main no longer matches",
    )
    _validate_initial_trees_and_parent(workspace, git, environment, receipt, feature_actual)
    ancestor_code, ancestor_output = _git_result(
        git,
        workspace,
        environment,
        ["merge-base", "--is-ancestor", feature, head],
        "check initial feature ancestry",
        allowed_returncodes=frozenset({0, 1}),
    )
    _need(not ancestor_output, "Git ancestry check returned unexpected output")
    _need(ancestor_code == 0, "initial feature commit is not an ancestor of HEAD")

    branch_code, branch_output = _git_result(
        git,
        workspace,
        environment,
        ["symbolic-ref", "--quiet", "--short", "HEAD"],
        "read branch",
        allowed_returncodes=frozenset({0, 1}),
    )
    if branch_code == 0:
        branch = _decode_text(branch_output, "branch").strip()
    else:
        _need(not branch_output, "Git detached branch check returned unexpected output")
        branch = None
    _need(branch is None or bool(branch), "Git branch output is malformed")
    commits = _new_commits(git, workspace, environment, feature, head)
    status = _status(git, workspace, environment)
    changed_paths = _path_list(
        _git(
            git,
            workspace,
            environment,
            ["diff", "--name-only", "-z", "--no-renames", "--no-ext-diff", "--no-textconv", feature, head, "--"],
            "read paths changed from initial feature",
        ),
        "paths changed from initial feature",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "initial": {
            "baseline_commit": baseline,
            "feature_commit": feature,
            "feature_tree": receipt["feature_tree"],
        },
        "head": head,
        "branch": branch,
        "origin_main": origin_main,
        "status": status,
        "commit_count": len(commits),
        "commits_added": commits,
        "changed_tracked_paths_from_initial_feature": changed_paths,
    }


def _validate_initial_trees_and_parent(
    workspace: Path,
    git: str,
    environment: dict[str, str],
    receipt: dict[str, Any],
    feature: str,
) -> None:
    baseline_tree = _oid_text(
        _git(
            git,
            workspace,
            environment,
            ["rev-parse", f"{receipt['baseline_commit']}^{{tree}}"],
            "read baseline tree",
        ),
        "baseline tree",
    )
    feature_tree = _oid_text(
        _git(git, workspace, environment, ["rev-parse", f"{feature}^{{tree}}"], "read feature tree"),
        "feature tree",
    )
    parents = _decode_lines(
        _git(git, workspace, environment, ["rev-list", "--parents", "-n", "1", feature], "read feature parent"),
        "feature parent",
    )
    _need(
        baseline_tree == receipt["baseline_tree"]
        and feature_tree == receipt["feature_tree"]
        and parents == [f"{feature} {receipt['baseline_commit']}"],
        "initial Git receipt objects no longer match",
    )


def _new_commits(
    git: str,
    workspace: Path,
    environment: dict[str, str],
    feature: str,
    head: str,
) -> list[dict[str, Any]]:
    lines = _decode_lines(
        _git(
            git,
            workspace,
            environment,
            ["rev-list", "--reverse", "--topo-order", f"{feature}..{head}"],
            "list new commits",
        ),
        "new commit list",
    )
    _need(len(lines) <= MAX_COMMITS, f"new commit count exceeds limit {MAX_COMMITS}")
    commits: list[dict[str, Any]] = []
    total_paths = 0
    for line in lines:
        commit = _need_oid(line, "new commit")
        message = _commit_message(git, workspace, environment, commit)
        paths = _path_list(
            _git(
                git,
                workspace,
                environment,
                [
                    "diff",
                    "--name-only",
                    "-z",
                    "--no-renames",
                    "--no-ext-diff",
                    "--no-textconv",
                    f"{commit}^",
                    commit,
                    "--",
                ],
                f"read paths for commit {commit}",
            ),
            f"paths for commit {commit}",
        )
        total_paths += len(paths)
        _need(
            total_paths <= MAX_TOTAL_COMMIT_PATHS,
            f"new commit path count exceeds limit {MAX_TOTAL_COMMIT_PATHS}",
        )
        commits.append({"commit": commit, "message": message, "paths": paths})
    return commits


def _commit_message(git: str, workspace: Path, environment: dict[str, str], commit: str) -> str:
    raw = _git(git, workspace, environment, ["cat-file", "commit", commit], f"read commit {commit}")
    _headers, separator, message = raw.partition(b"\n\n")
    _need(bool(separator), "Git commit object is malformed")
    _need(len(message) <= MAX_MESSAGE_BYTES, f"Git commit message exceeds limit {MAX_MESSAGE_BYTES}")
    return _decode_text(message, f"commit {commit} message")


def _status(git: str, workspace: Path, environment: dict[str, str]) -> dict[str, Any]:
    _reject_gitlinks(git, workspace, environment)
    raw = _git(
        git,
        workspace,
        environment,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"],
        "read status",
    )
    tracked: list[dict[str, str]] = []
    untracked: list[str] = []
    entries = _nul_entries(raw, "Git status")
    _need(len(entries) <= MAX_PATHS, f"Git status path count exceeds limit {MAX_PATHS}")
    for entry in entries:
        _need(len(entry) >= 4 and entry[2:3] == b" ", "Git status output is malformed")
        code = _decode_text(entry[:2], "Git status code")
        path = _safe_path(entry[3:], "Git status path")
        if code == "??":
            untracked.append(path)
            continue
        _need("?" not in code and "!" not in code and code != "  ", "Git status code is malformed")
        tracked.append({"path": path, "index": code[0], "worktree": code[1]})
    tracked.sort(key=lambda record: record["path"])
    untracked.sort()
    return {
        "clean": not tracked and not untracked,
        "tracked_dirty": bool(tracked),
        "untracked_dirty": bool(untracked),
        "tracked": tracked,
        "untracked": untracked,
    }


def _topology_status(
    git: str, workspace: Path, environment: dict[str, str], hide_worktree_root: bool,
) -> dict[str, Any]:
    """Read status while omitting only the separately-attested dynamic worktree root."""

    _reject_gitlinks(git, workspace, environment)
    raw = _git(
        git, workspace, environment,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"],
        "read topology status",
    )
    entries = _nul_entries(raw, "Git topology status")
    if hide_worktree_root:
        entries = [entry for entry in entries if not entry.startswith(b"?? .worktrees/")]
    _need(len(entries) <= MAX_PATHS, f"Git topology status path count exceeds limit {MAX_PATHS}")
    tracked: list[dict[str, str]] = []
    untracked: list[str] = []
    for entry in entries:
        _need(len(entry) >= 4 and entry[2:3] == b" ", "Git topology status output is malformed")
        code = _decode_text(entry[:2], "Git topology status code")
        path = _safe_path(entry[3:], "Git topology status path")
        if code == "??":
            untracked.append(path)
            continue
        _need("?" not in code and "!" not in code and code != "  ",
              "Git topology status code is malformed")
        tracked.append({"path": path, "index": code[0], "worktree": code[1]})
    tracked.sort(key=lambda record: record["path"])
    untracked.sort()
    return {
        "clean": not tracked and not untracked,
        "tracked_dirty": bool(tracked), "untracked_dirty": bool(untracked),
        "tracked": tracked, "untracked": untracked,
    }


def _reject_gitlinks(git: str, workspace: Path, environment: dict[str, str]) -> None:
    """Fail closed before status can traverse an indexed nested repository."""

    raw = _git(git, workspace, environment, ["ls-files", "--stage", "-z"], "inspect index entries")
    entries = _nul_entries(raw, "Git index")
    _need(len(entries) <= MAX_PATHS, f"Git index path count exceeds limit {MAX_PATHS}")
    for entry in entries:
        header, separator, path = entry.partition(b"\t")
        _need(bool(separator), "Git index entry is malformed")
        fields = header.split(b" ")
        _need(len(fields) == 3 and fields[0].isdigit() and len(fields[0]) == 6
              and fields[2] in {b"0", b"1", b"2", b"3"}, "Git index entry is malformed")
        _need_oid(_decode_text(fields[1], "Git index object"), "Git index object")
        _safe_path(path, "Git index path")
        _need(fields[0] != b"160000", "Git index contains a gitlink")


def _path_list(raw: bytes, label: str) -> list[str]:
    entries = _nul_entries(raw, label)
    _need(len(entries) <= MAX_PATHS, f"{label} count exceeds limit {MAX_PATHS}")
    paths = [_safe_path(entry, label) for entry in entries]
    _need(len(paths) == len(set(paths)), f"{label} contains duplicate paths")
    return sorted(paths)


def _nul_entries(raw: bytes, label: str) -> list[bytes]:
    if not raw:
        return []
    _need(raw.endswith(b"\0"), f"{label} output is truncated or malformed")
    entries = raw[:-1].split(b"\0")
    _need(all(entries), f"{label} output contains an empty record")
    return entries


def _safe_path(raw: bytes, label: str) -> str:
    value = _decode_text(raw, label)
    path = PurePosixPath(value)
    _need(
        bool(value)
        and "\\" not in value
        and not path.is_absolute()
        and path.as_posix() == value
        and all(part not in {"", ".", ".."} for part in path.parts),
        f"{label} is not a canonical relative path",
    )
    return value


def _verified_commit(
    git: str,
    workspace: Path,
    environment: dict[str, str],
    commit: str,
    label: str,
) -> str:
    return _oid_text(
        _git(git, workspace, environment, ["rev-parse", "--verify", f"{commit}^{{commit}}"], f"verify {label}"),
        label,
    )


def _git(
    git: str,
    workspace: Path,
    environment: dict[str, str],
    arguments: list[str],
    label: str,
) -> bytes:
    _code, output = _git_result(git, workspace, environment, arguments, label)
    return output


def _git_result(
    git: str,
    workspace: Path,
    environment: dict[str, str],
    arguments: list[str],
    label: str,
    *,
    allowed_returncodes: frozenset[int] = frozenset({0}),
) -> tuple[int, bytes]:
    executable = shutil.which("git")
    candidate = git if os.path.isabs(git) else shutil.which(git)
    _need(
        isinstance(executable, str)
        and candidate is not None
        and str(Path(candidate).resolve()) == str(Path(executable).resolve()),
        f"Git {label} executable does not match the pinned git runtime",
    )
    command = [executable, "--no-pager", *arguments]
    try:
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            completed = subprocess.run(
                command,
                cwd=workspace,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                check=False,
                timeout=GIT_COMMAND_TIMEOUT_SECONDS,
            )
            stdout_size = stdout.tell()
            stderr_size = stderr.tell()
            _need(
                stdout_size <= MAX_OUTPUT_BYTES and stderr_size <= MAX_OUTPUT_BYTES,
                f"Git {label} output exceeds limit {MAX_OUTPUT_BYTES}",
            )
            stdout.seek(0)
            output = stdout.read()
    except subprocess.TimeoutExpired as exc:
        raise GitObservationError(f"Git {label} timed out") from exc
    except OSError as exc:
        raise GitObservationError(f"Git {label} could not execute") from exc
    _need(completed.returncode in allowed_returncodes, f"Git {label} failed")
    return completed.returncode, output


def _decode_lines(raw: bytes, label: str) -> list[str]:
    text = _decode_text(raw, label)
    if not text:
        return []
    _need(text.endswith("\n"), f"{label} output is truncated or malformed")
    lines = text[:-1].split("\n")
    _need(all(lines), f"{label} output contains an empty record")
    return lines


def _oid_text(raw: bytes, label: str) -> str:
    text = _decode_text(raw, label)
    _need(text.endswith("\n") and text.count("\n") == 1, f"{label} output is malformed")
    text = text[:-1]
    _need_oid(text, label)
    return text


def _need_oid(value: object, label: str) -> str:
    _need(
        isinstance(value, str)
        and len(value) in {40, 64}
        and all(character in _HEX for character in value),
        f"{label} is not a full object id",
    )
    return value


def _decode_text(raw: bytes, label: str) -> str:
    try:
        return raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise GitObservationError(f"{label} returned invalid UTF-8") from exc


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise GitObservationError(message)


__all__ = (
    "GitObservationError", "TOPOLOGY_COMPARISON_SCHEMA_VERSION", "TOPOLOGY_SCHEMA_VERSION",
    "observe_git_state", "observe_git_topology", "observe_registered_worktrees",
    "snapshot_git_topology",
)
