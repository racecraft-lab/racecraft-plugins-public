"""Repository-root, request-path and trusted file-read primitives shared by runner core and helpers."""

from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .envelope import diagnostic


CAPTURE_LIMIT_BYTES = 16 * 1024


BOUNDED_TEXT_INPUT_BYTES = 32 * 1024
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")


PATH_KEYS = {
    "changed_files",
    "config_path",
    "feature_dir",
    "g3_attempts_path",
    "packet_path",
    "plan_file",
    "spec_file",
    "record_path",
    "ledger_path",
    "tasks_file",
    "repo_root",
    "target",
    "workflow_file",
    "worktree_root_override",
}


def resolve_repo_root(inputs: dict[str, Any]) -> Path | dict[str, Any]:
    invocation_root = find_repo_root(Path.cwd())
    if invocation_root is None:
        return path_diagnostic(
            "missing_prerequisite",
            "could not locate repository root for read-only helper request",
            {"repo_root": normalize_display(Path.cwd())},
        )
    raw = inputs.get("repo_root")
    if raw is not None and not isinstance(raw, str):
        return path_diagnostic("invalid_input", "repo_root must be a string path", {"field": "repo_root"})
    if isinstance(raw, str) and looks_like_windows_absolute_path(raw) and os.name != "nt":
        return path_diagnostic("unsupported_path", "path escapes the repo/plugin trust boundary", {"field": "repo_root", "path": normalize_display(raw)})
    if raw:
        candidate = Path(normalize_path_input(raw))
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        if not path_stays_in_trust_boundary(candidate, invocation_root):
            return path_diagnostic("unsupported_path", "path escapes the repo/plugin trust boundary", {"field": "repo_root", "path": normalize_display(raw)})
    return invocation_root


def find_repo_root(start: Path) -> Path | None:
    candidates = [start, *start.parents] if start.is_dir() else [start.parent, *start.parent.parents]
    # The nearest trusted marker wins so installed-cache runs inside nested
    # consumer worktrees cannot be captured by an ancestor source checkout.
    for candidate in candidates:
        root = candidate.resolve(strict=False)
        runner_dir = candidate / "speckit-pro" / "speckit_pro_runner"
        if runner_dir.is_dir() and path_stays_in_trust_boundary(runner_dir, root):
            return root
        specify_dir = candidate / ".specify"
        if specify_dir.is_dir() and path_stays_in_trust_boundary(specify_dir, root):
            return root
    return None


def _validate_plan_repair_context_paths(
    helper_id: str,
    inputs: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any] | None:
    context_paths = inputs.get("context_paths")
    if not isinstance(context_paths, dict) or not (1 <= len(context_paths) <= 16):
        return path_diagnostic(
            "invalid_input",
            "context_paths must contain from 1 through 16 entries",
            {"helper_id": helper_id, "field": "context_paths"},
        )
    for context_id, raw_path in context_paths.items():
        if not isinstance(context_id, str) \
                or re.fullmatch(r"[a-z0-9][a-z0-9._-]*", context_id) is None:
            return path_diagnostic(
                "invalid_input",
                "context_paths contains a noncanonical context id",
                {"helper_id": helper_id, "field": "context_paths"},
            )
        if not isinstance(raw_path, str) or not raw_path:
            return path_diagnostic(
                "invalid_input",
                "context_paths values must be non-empty string paths",
                {"helper_id": helper_id, "field": f"context_paths.{context_id}"},
            )
        path_diag = validate_path_value(
            helper_id, f"context_paths.{context_id}", raw_path, repo_root,
        )
        if path_diag is not None:
            return path_diag
    return None


def validate_bounded_inputs(
    helper_id: str,
    inputs: dict[str, Any],
    repo_root: Path,
    *,
    mutation_operation: str | None = None,
    mutation_operation_deferred: bool = False,
) -> dict[str, Any] | None:
    for key, value in iter_input_strings(inputs):
        if len(value.encode("utf-8")) > BOUNDED_TEXT_INPUT_BYTES:
            return diagnostic(
                "invalid_input",
                "helper input string exceeds the bounded input limit",
                details={"helper_id": helper_id, "field": key, "limit_bytes": BOUNDED_TEXT_INPUT_BYTES},
                remediation_summary="Send smaller deterministic helper inputs.",
                remediation_actions=["Use fixture files instead of large inline strings.", "Retry with bounded helper input."],
            )
    args = inputs.get("args")
    if args is not None:
        return diagnostic(
            "invalid_input",
            "structured helper requests must not provide raw args",
            details={"helper_id": helper_id},
            remediation_summary="Use helper-specific structured input fields so reported argv cannot diverge from executed behavior.",
            remediation_actions=["Remove inputs.args.", "Retry with the helper-specific fields from fixture-manifest.json."],
        )
    for key in PATH_KEYS:
        value = inputs.get(key)
        if isinstance(value, str) and value:
            permits_registered_or_explicit_external_path = (
                helper_id == "resolve-workflow-binding" and key == "workflow_file"
            ) or (
                helper_id == "resolve-scaffold-worktree-placement" and key == "worktree_root_override"
            )
            if permits_registered_or_explicit_external_path:
                if "\x00" in value:
                    return path_diagnostic(
                        "invalid_input",
                        "path contains a NUL byte",
                        {"helper_id": helper_id, "field": key},
                    )
                if looks_like_windows_absolute_path(value) and os.name != "nt":
                    return path_diagnostic(
                        "unsupported_path",
                        "path uses an unsupported absolute-path form",
                        {"helper_id": helper_id, "field": key, "path": normalize_display(value)},
                    )
                continue
            path_diag = validate_path_value(helper_id, key, value, repo_root)
            if path_diag is not None:
                return path_diag
    if inputs.get("write_mode") is True:
        if mutation_operation and mutation_operation_deferred:
            mutation_action = (
                f"The registered {mutation_operation} operation remains deferred; keep this request read_only."
            )
        elif mutation_operation:
            mutation_action = (
                f"Submit a separate runner request with helper_id and operation {mutation_operation}."
            )
        else:
            mutation_action = "Inspect mutation-registry-dispatch for a registered Python mutation operation."
        return diagnostic(
            "unsupported_mode",
            "write-mode helper behavior is out of scope for runner read-only dispatch",
            details={"helper_id": helper_id},
            remediation_summary="Use only registered read-only helper modes.",
            remediation_actions=["Remove write_mode from the request.", mutation_action],
        )
    if helper_id == "render-plan-repair-context":
        path_diag = _validate_plan_repair_context_paths(helper_id, inputs, repo_root)
        if path_diag is not None:
            return path_diag
    if helper_id in {"detect-commands", "detect-presets"}:
        raw_root = inputs.get("repo_root")
        if isinstance(raw_root, str) and raw_root:
            target_root = resolve_input_path(raw_root, repo_root)
            if not trusted_dir_exists(target_root, repo_root):
                return path_diagnostic(
                    "invalid_input",
                    "repo_root must be a directory",
                    {"helper_id": helper_id, "field": "repo_root", "path": normalize_display(raw_root)},
                )
    if helper_id == "validate-pr-workflow-contract":
        changed_files = inputs.get("changed_files")
        if changed_files is not None:
            if not isinstance(changed_files, str):
                return path_diagnostic(
                    "invalid_input",
                    "changed_files must be a single path to a changed-files list",
                    {"helper_id": helper_id, "field": "changed_files"},
                )
            if "\n" in changed_files or "\r" in changed_files:
                return path_diagnostic(
                    "invalid_input",
                    "changed_files must be a single path, not an inline file list",
                    {"helper_id": helper_id, "field": "changed_files"},
                )
            if changed_files:
                path_diag = validate_path_value(helper_id, "changed_files", changed_files, repo_root)
                if path_diag is not None:
                    return path_diag
    return None


def canonicalize_inputs(helper_id: str, inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    canonical = dict(inputs)
    path_keys_by_helper = {
        "check-prerequisites": {"workflow_file"},
        "detect-commands": {"repo_root"},
        "detect-presets": {"repo_root"},
        "count-markers": {"feature_dir"},
        "validate-gate": {"feature_dir", "workflow_file"},
        "reviewability-gate": {"target"},
        "estimate-reviewable-loc": {"plan_file"},
        "resolve-confidence-mode": {"config_path"},
        "resolve-autopilot-stage": {"workflow_file"},
        "render-plan-repair-context": {"g3_attempts_path"},
        # Real path inputs only. Every key here is run through request_path_display,
        # whose normalize_path_input rewrites each backslash, so a reviewer comment
        # body listed here would be corrupted before the deny-set ever runs.
        "sweep-pr-feedback": {"workflow_file", "feature_dir"},
        "sweep-isolation-session": {"workflow_file"},
        "preview-isolation-session": {"workflow_file", "artifact_path"},
        # The freshness helper reads one path and only one: every git fact it
        # needs arrives as request data.
        "check-artifact-freshness": {"workflow_file"},
        "confidence-gate": {"workflow_file"},
        "aggregate-crl": {"workflow_file"},
        "generate-spec-index-check": {"repo_root"},
        "o5-topology": {"target"},
        "atomicity-route": {"feature_dir", "workflow_file"},
        "plan-layers-feature-dir": {"feature_dir"},
        "partition-phase7-tasks": {"tasks_file"},
        "validate-task-execution": {"tasks_file"},
        "validate-execution-record": {"workflow_file", "record_path"},
        "execution-control": {"workflow_file", "spec_file", "ledger_path"},
        "execute-verification": {"workflow_file", "ledger_path"},
        "task-results": {"tasks_file", "journal_file", "prior_journal_file"},
        "validate-pr-workflow-contract": {"repo_root", "changed_files"},
        "validate-pr-packet-read-only": {"packet_path"},
    }
    for key in path_keys_by_helper.get(helper_id, set()):
        value = canonical.get(key)
        if isinstance(value, str) and value:
            canonical[key] = request_path_display(value, repo_root)
    return canonical


def validate_path_value(helper_id: str, field: str, raw: str, repo_root: Path) -> dict[str, Any] | None:
    if "\x00" in raw:
        return path_diagnostic("invalid_input", "path contains a NUL byte", {"helper_id": helper_id, "field": field})
    if looks_like_windows_absolute_path(raw) and os.name != "nt":
        return path_diagnostic(
            "unsupported_path",
            "path escapes the repo/plugin trust boundary",
            {"helper_id": helper_id, "field": field, "path": normalize_display(raw)},
        )
    candidate = Path(normalize_path_input(raw))
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    resolved = candidate.resolve(strict=False)
    allowed_roots = [repo_root, repo_root / "speckit-pro"]
    if not any(is_relative_to(resolved, allowed) for allowed in allowed_roots):
        return path_diagnostic(
            "unsupported_path",
            "path escapes the repo/plugin trust boundary",
            {"helper_id": helper_id, "field": field, "path": normalize_display(raw)},
        )
    return None


def make_result(stdout: str, stderr: str = "", exit_code: int = 0) -> dict[str, Any]:
    return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code}


def json_text(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"


def path_diagnostic(code: str, message: str, details: dict[str, Any]) -> dict[str, Any]:
    return diagnostic(
        code,
        message,
        details=details,
        remediation_summary="Use repo-relative paths that stay inside the declared trust boundary.",
        remediation_actions=["Remove traversal or external absolute paths.", "Retry from the repository root."],
    )


def normalize_display(value: str | Path) -> str:
    text = str(value).replace("\\", "/")
    parts: list[str] = []
    for part in text.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            else:
                parts.append(part)
        else:
            parts.append(part)
    return "." if not parts else PurePosixPath(*parts).as_posix()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def resolve_input_path(raw: Any, repo_root: Path) -> Path:
    value = normalize_path_input(raw)
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def request_path_display(raw: Any, repo_root: Path) -> str:
    value = normalize_path_input(raw)
    if not value:
        return ""
    return repo_relative(resolve_input_path(value, repo_root), repo_root)


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix()
    except ValueError:
        parts = path.resolve(strict=False).parts
        if "specs" in parts:
            idx = parts.index("specs")
            return str(PurePosixPath(*parts[idx:]))
        return path.as_posix()


def trusted_file_exists(path: Path, repo_root: Path) -> bool:
    fd = trusted_open_regular_file(path, repo_root)
    if fd is None:
        return False
    try:
        return True
    finally:
        try:
            os.close(fd)
        except OSError:
            # Best-effort descriptor cleanup; existence checks should not fail on close errors.
            pass


def trusted_dir_exists(path: Path, repo_root: Path) -> bool:
    if descriptor_read_supported():
        fd = trusted_open_directory(path, repo_root)
        if fd is None:
            return False
        try:
            return True
        finally:
            try:
                os.close(fd)
            except OSError:
                # Best-effort descriptor cleanup; existence checks should not fail on close errors.
                pass
    return path.is_dir() and path_stays_in_trust_boundary(path, repo_root)


def path_stays_in_trust_boundary(path: Path, repo_root: Path) -> bool:
    resolved = path.resolve(strict=False)
    return is_relative_to(resolved, repo_root.resolve(strict=False))


def trusted_text(path: Path, repo_root: Path | None = None) -> str | None:
    content = trusted_bytes(path, repo_root)
    return None if content is None else content.decode("utf-8", errors="replace")


def trusted_bytes(path: Path, repo_root: Path | None = None, *, limit: int | None = None) -> bytes | None:
    if repo_root is not None:
        return trusted_bytes_descriptor(path, repo_root, limit=limit)
    try:
        if not path.is_file():
            return None
        with path.open("rb") as stream:
            content = stream.read() if limit is None else stream.read(limit + 1)
        return content if limit is None or len(content) <= limit else None
    except OSError:
        return None


def trusted_bytes_descriptor(path: Path, repo_root: Path, *, limit: int | None = None) -> bytes | None:
    fd = trusted_open_regular_file(path, repo_root)
    if fd is None:
        return None
    try:
        chunks: list[bytes] = []
        size = 0
        while True:
            chunk = os.read(fd, 1024 * 1024 if limit is None else min(1024 * 1024, limit + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            if limit is not None and size > limit:
                return None
            chunks.append(chunk)
        return b"".join(chunks)
    except OSError:
        return None
    finally:
        try:
            os.close(fd)
        except OSError:
            # Best-effort descriptor cleanup after a completed or failed read.
            pass


def trusted_open_regular_file(path: Path, repo_root: Path) -> int | None:
    if not descriptor_read_supported():
        return None
    repo_root = repo_root.resolve(strict=False)
    target = path if path.is_absolute() else repo_root / path
    try:
        relative = target.relative_to(repo_root)
    except ValueError:
        return None
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        return None
    target_name = relative.parts[-1]
    if target_name in {"", ".", ".."} or "/" in target_name:
        return None
    try:
        root_mode = repo_root.lstat().st_mode
        if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
            return None
        parent_fd = os.open(repo_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW)
    except (OSError, NotImplementedError):
        return None
    fd = -1
    try:
        for part in relative.parts[:-1]:
            next_fd = os.open(
                part,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW,
                dir_fd=parent_fd,
            )
            os.close(parent_fd)
            parent_fd = next_fd
        # Check the opened descriptor without waiting for a writer if an untrusted leaf is a FIFO.
        fd = os.open(target_name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd)
        file_stat = os.fstat(fd)
        if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
            os.close(fd)
            return None
        return fd
    except (OSError, NotImplementedError):
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                # Close failures during an already-failed guarded open are best-effort cleanup.
                pass
        return None
    finally:
        try:
            os.close(parent_fd)
        except OSError:
            # The caller should see the original read result, not a best-effort close failure.
            pass


def trusted_open_directory(path: Path, repo_root: Path) -> int | None:
    if not descriptor_read_supported():
        return None
    repo_root = repo_root.resolve(strict=False)
    target = path if path.is_absolute() else repo_root / path
    try:
        relative = target.relative_to(repo_root)
    except ValueError:
        return None
    if any(part in {"", ".", ".."} for part in relative.parts):
        return None
    try:
        root_mode = repo_root.lstat().st_mode
        if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
            return None
        current_fd = os.open(repo_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW)
    except (OSError, NotImplementedError):
        return None
    try:
        for part in relative.parts:
            next_fd = os.open(
                part,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW,
                dir_fd=current_fd,
            )
            os.close(current_fd)
            current_fd = next_fd
        dir_stat = os.fstat(current_fd)
        if stat.S_ISLNK(dir_stat.st_mode) or not stat.S_ISDIR(dir_stat.st_mode):
            os.close(current_fd)
            return None
        return current_fd
    except (OSError, NotImplementedError):
        try:
            os.close(current_fd)
        except OSError:
            # Best-effort cleanup while returning an unsupported/unsafe directory result.
            pass
        return None


def descriptor_read_supported() -> bool:
    return os.name != "nt" and hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_NONBLOCK")


def tree_entry_signature(info: os.stat_result) -> tuple[int, ...]:
    """Identity and mutation evidence for a captured filesystem entry.

    A directory's times, size and link count also move when an ignored bytecode cache appears in it,
    so a directory is compared by identity and mode here, and by its captured entries in read_tree_directory.
    """
    if stat.S_ISDIR(info.st_mode):
        return (info.st_dev, info.st_ino, info.st_mode)
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def captured_tree_names(fd: int) -> list[str]:
    """A directory's entries a tree snapshot captures: everything but bytecode caches."""
    return sorted(name for name in os.listdir(fd) if name != "__pycache__" and not name.endswith(".pyc"))


def read_tree_file(fd: int, before: os.stat_result, byte_limit: int | None) -> bytes:
    """Read one single-link descriptor, optionally bounded to its captured size."""
    if before.st_nlink != 1:
        raise OSError("hard-linked tree file refused")
    with os.fdopen(os.dup(fd), "rb") as stream:
        content = stream.read() if byte_limit is None else stream.read(byte_limit + 1)
    if byte_limit is not None and (len(content) > byte_limit or len(content) != before.st_size):
        raise OSError("tree file exceeded its byte limit or changed size")
    return content


@dataclass(frozen=True)
class TreeEntryReadOptions:
    signatures: dict[Path, tuple[int, ...]] | None = None
    byte_limit: int | None = None


_DEFAULT_TREE_ENTRY_READ_OPTIONS = TreeEntryReadOptions()


def read_tree_entry(
    parent_fd: int,
    name: str,
    expected: os.stat_result | None = None,
    *,
    options: TreeEntryReadOptions = _DEFAULT_TREE_ENTRY_READ_OPTIONS,
) -> dict[Path, tuple[int, bytes | None]]:
    """Read one entry through its parent descriptor; reject links and changing evidence."""
    signatures, byte_limit = options.signatures, options.byte_limit
    before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if expected is not None and tree_entry_signature(before) != tree_entry_signature(expected):
        raise OSError("tree entry changed before capture")
    if not (stat.S_ISDIR(before.st_mode) or stat.S_ISREG(before.st_mode)):
        raise OSError("tree entry must be a regular file or directory")
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    if stat.S_ISDIR(before.st_mode):
        flags |= os.O_DIRECTORY
    fd = os.open(name, flags, dir_fd=parent_fd)
    try:
        if tree_entry_signature(before) != tree_entry_signature(os.fstat(fd)):
            raise OSError("tree entry changed while opening")
        if stat.S_ISDIR(before.st_mode):
            captured = read_tree_directory(fd, signatures=signatures)
        else:
            captured = {Path(): (stat.S_IMODE(before.st_mode), read_tree_file(fd, before, byte_limit))}
        after = os.fstat(fd)
        named = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if tree_entry_signature(before) != tree_entry_signature(after) or tree_entry_signature(after) != tree_entry_signature(named):
            raise OSError("tree entry changed while reading")
        if signatures is not None:
            signatures[Path()] = tree_entry_signature(before)
        return captured
    finally:
        os.close(fd)


def read_tree_directory(fd: int, *, signatures: dict[Path, tuple[int, ...]] | None = None) -> dict[Path, tuple[int, bytes | None]]:
    """Capture a directory without ever traversing a child pathname."""
    captured: dict[Path, tuple[int, bytes | None]] = {Path(): (stat.S_IMODE(os.fstat(fd).st_mode), None)}
    names = captured_tree_names(fd)
    immediate_signatures = {}
    for name in names:
        immediate_signatures[name] = tree_entry_signature(os.stat(name, dir_fd=fd, follow_symlinks=False))
        child_signatures: dict[Path, tuple[int, ...]] = {}
        options = TreeEntryReadOptions(signatures=child_signatures)
        for relative, entry in read_tree_entry(fd, name, options=options).items():
            captured[Path(name) / relative] = entry
        if signatures is not None:
            signatures.update((Path(name) / relative, signature) for relative, signature in child_signatures.items())
    # Every captured entry must still be there, unchanged, with nothing added beside it.
    if captured_tree_names(fd) != names or any(
            tree_entry_signature(os.stat(name, dir_fd=fd, follow_symlinks=False)) != signature
            for name, signature in immediate_signatures.items()):
        raise OSError("tree directory changed while reading")
    return captured


def trusted_tree_snapshot(path: Path, repo_root: Path, *, expected: os.stat_result | None = None) -> dict[Path, tuple[int, bytes | None]]:
    """Capture one coherent tree, bound to a no-follow parent and entry identity.

    Callers consume these bytes rather than reopen the captured source by pathname.
    Missing, linked, special, hard-linked or concurrently changed entries raise OSError.
    """
    if repo_root.is_symlink():
        raise OSError("linked tree root refused")
    parent_fd = trusted_open_directory(path.parent, repo_root)
    if parent_fd is None:
        raise OSError("unsafe tree parent")
    try:
        before = os.fstat(parent_fd)
        signatures: dict[Path, tuple[int, ...]] = {}
        captured = read_tree_entry(parent_fd, path.name, expected, options=TreeEntryReadOptions(signatures=signatures))
        checked_signatures: dict[Path, tuple[int, ...]] = {}
        checked = read_tree_entry(
            parent_fd,
            path.name,
            expected,
            options=TreeEntryReadOptions(signatures=checked_signatures),
        )
        # A later sibling can change a subtree whose local checks already completed.
        if signatures != checked_signatures or captured != checked:
            raise OSError("tree changed after capture")
        check_fd = trusted_open_directory(path.parent, repo_root)
        if check_fd is None:
            raise OSError("tree parent changed while reading")
        try:
            if tree_entry_signature(before) != tree_entry_signature(os.fstat(check_fd)):
                raise OSError("tree parent changed while reading")
        finally:
            os.close(check_fd)
        return captured
    finally:
        os.close(parent_fd)


def create_tree_directory(parent_fd: int, name: str) -> int:
    """Create/open a child directory without following a pre-existing or swapped link."""
    try:
        os.mkdir(name, dir_fd=parent_fd)
    except FileExistsError:
        # Reuse only after the no-follow directory open below validates the entry.
        pass
    return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)


def write_tree_snapshot(path: Path, captured: dict[Path, tuple[int, bytes | None]], root: Path) -> None:
    """Publish captured bytes using no-follow directories and exclusively created leaves.

    Writes stay on the opened directories even if another process renames them. No later
    pathname replace, unlink, truncation or metadata operation can follow a swapped leaf.
    """
    root_fd = open_tree_parent(path, root)
    try:
        write_tree_entries(root_fd, Path(path.name), captured)
    finally:
        os.close(root_fd)


def open_tree_parent(path: Path, root: Path) -> int:
    """Create/open the parent chain under root, binding every component without links."""
    if not descriptor_read_supported():
        raise OSError("descriptor-relative tree writes unavailable")
    relative = path.relative_to(root)
    if not relative.parts or ".." in relative.parts:
        raise OSError("tree destination escapes root")
    fd = trusted_open_directory(root, Path(root.anchor))
    if fd is None:
        raise OSError("unsafe tree publication root")
    try:
        for part in relative.parts[:-1]:
            next_fd = create_tree_directory(fd, part)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def write_tree_entries(root_fd: int, relative: Path, captured: dict[Path, tuple[int, bytes | None]]) -> None:
    """Write each captured entry through directory descriptors; never mutate existing files."""
    for suffix, (mode, content) in captured.items():
        target = relative / suffix
        if ".." in target.parts or target.is_absolute():
            raise OSError("unsafe captured tree path")
        fd = os.dup(root_fd)
        try:
            parts = target.parts if content is None else target.parts[:-1]
            for part in parts:
                next_fd = create_tree_directory(fd, part)
                os.close(fd)
                fd = next_fd
            if content is not None:
                leaf_fd = os.open(target.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode & 0o777, dir_fd=fd)
                with os.fdopen(leaf_fd, "wb") as stream:
                    stream.write(content)
        finally:
            os.close(fd)


def trusted_lines(path: Path, repo_root: Path | None = None) -> list[str]:
    text = trusted_text(path, repo_root)
    return [] if text is None else text.splitlines()


def looks_like_windows_absolute_path(raw: str) -> bool:
    return bool(WINDOWS_DRIVE_RE.match(raw) or raw.startswith("\\\\") or raw.startswith("//"))


def normalize_path_input(raw: Any) -> str:
    return str(raw).replace("\\", "/")


def iter_input_strings(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(prefix or "<input>", value)]
    if isinstance(value, list):
        result: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            result.extend(iter_input_strings(item, f"{prefix}[{index}]" if prefix else f"[{index}]"))
        return result
    if isinstance(value, dict):
        result: list[tuple[str, str]] = []
        for key, item in value.items():
            field = f"{prefix}.{key}" if prefix else str(key)
            result.extend(iter_input_strings(item, field))
        return result
    return []


_TEST_PATH_RE = re.compile(r"(^|/)(tests?|__tests__|spec|src/test)/|(^|/)test_[^/]*\.py$|_test\.(py|go)$|(Test|Tests|Spec)\.(java|kt|swift|cs)$|_spec\.rb$|\.(test|spec)\.[cm]?[jt]sx?$")


def is_test_path(path: str) -> bool:
    """True when the path or file name marks a test file in any stack detect-commands knows."""
    return bool(_TEST_PATH_RE.search(path))
