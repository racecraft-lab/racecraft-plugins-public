"""Provider-free preparation for explicitly requested native evaluation tools."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "native-eval-toolchain/v1"
CLAUDE_PLUGIN_SCHEMA_VERSION = "native-eval-toolchain/claude-plugin-v1"
_LAUNCHER_DIRECTORY = Path(".codex/native-eval-tool-bin")
_CLAUDE_RUNTIME_DIRECTORY = Path(".native-toolchain")
_CLAUDE_BIN_DIRECTORY = Path("bin")
_CLAUDE_PYTHON_RUNTIME = ".speckit-python3-runtime"
_ALLOWED_TOOLS = frozenset({"specify", "uv"})
_SAFE_OWNER_IDS = frozenset({0, os.geteuid()}) if hasattr(os, "geteuid") else frozenset({0})
_MAX_LINKS = 32
_MAX_TREE_ENTRIES = 100_000
_MAX_FILE_BYTES = 256 * 1024 * 1024
_MAX_TREE_BYTES = 2 * 1024 * 1024 * 1024
_PROBE_TIMEOUT_SECONDS = 10


class NativeToolchainError(ValueError):
    """Raised when an installed toolchain cannot be admitted without ambiguity."""


@dataclass(frozen=True)
class PreparedNativeToolchain:
    """Controller-owned launch paths and the proof needed to revalidate them."""

    workspace: Path
    launcher_dir: Path | None
    launchers: dict[str, Path]
    path_entries: tuple[Path, ...]
    environment: dict[str, str]
    readonly_roots: tuple[Path, ...]
    runtime_identity: dict[str, Any]


def prepare_native_toolchain(
    workspace: str | Path,
    *,
    required_tools: Collection[str],
    specify_executable: str | Path | None = None,
    uv_executable: str | Path | None = None,
) -> PreparedNativeToolchain:
    """Prepare only the named installed tools; no tool is enabled implicitly."""

    target = _safe_workspace(workspace)
    tools = _required_tools(required_tools)
    receipts: dict[str, dict[str, Any]] = {}
    if "specify" in tools:
        receipts["specify"] = _inspect_specify(
            _discover_executable("specify", specify_executable), target
        )
    if "uv" in tools:
        receipts["uv"] = _inspect_uv(_discover_executable("uv", uv_executable), target)

    launcher_dir: Path | None = None
    launchers: dict[str, Path] = {}
    created_launcher: Path | None = None
    created_launcher_dir = False
    try:
        if "specify" in receipts:
            launcher_dir = target / _LAUNCHER_DIRECTORY
            if launcher_dir.exists() or launcher_dir.is_symlink():
                raise NativeToolchainError("native tool launcher directory must not pre-exist")
            launcher_dir.mkdir(mode=0o700)
            created_launcher_dir = True
            created_launcher = launcher_dir / "specify"
            launcher_bytes = _specify_launcher_bytes(receipts["specify"])
            with created_launcher.open("xb") as handle:
                handle.write(launcher_bytes)
            os.chmod(created_launcher, 0o555)
            os.chmod(launcher_dir, 0o555)
            launchers["specify"] = created_launcher
        if "uv" in receipts:
            launchers["uv"] = Path(receipts["uv"]["executable"]["resolved_path"])

        identity = _runtime_identity(target, tools, receipts, launchers)
        prepared = PreparedNativeToolchain(
            workspace=target,
            launcher_dir=launcher_dir,
            launchers=launchers,
            path_entries=_path_entries(tools, launchers),
            environment=_fixed_environment(),
            readonly_roots=_readonly_roots(receipts),
            runtime_identity=identity,
        )
        verify_native_toolchain(prepared)
        return prepared
    except Exception:
        if created_launcher_dir and launcher_dir is not None and launcher_dir.exists():
            os.chmod(launcher_dir, 0o700)
        if created_launcher is not None and created_launcher.exists():
            created_launcher.unlink()
        if created_launcher_dir and launcher_dir is not None and launcher_dir.exists():
            launcher_dir.rmdir()
        raise


def prepare_claude_plugin_toolchain(
    plugin_root: str | Path,
    *,
    required_tools: Collection[str],
    specify_executable: str | Path | None = None,
) -> PreparedNativeToolchain:
    """Stage a relocatable Specify runtime entirely inside a Claude plugin."""

    target = _safe_plugin_root(plugin_root)
    tools = _required_tools(required_tools)
    if tools != ("specify",):
        raise NativeToolchainError("Claude plugin toolchain currently supports only Specify")
    receipt = _inspect_specify(
        _discover_executable("specify", specify_executable), target
    )
    receipts = {"specify": receipt}
    runtime_root = target / _CLAUDE_RUNTIME_DIRECTORY
    bin_root = target / _CLAUDE_BIN_DIRECTORY
    created_bin = False
    created_runtime = False
    launcher = bin_root / "specify"
    python_link = bin_root / "python3"
    python_runtime_link = bin_root / _CLAUDE_PYTHON_RUNTIME
    created_outputs: list[Path] = []
    try:
        if runtime_root.exists() or runtime_root.is_symlink():
            raise NativeToolchainError("Claude plugin toolchain directory must not pre-exist")
        if bin_root.exists() or bin_root.is_symlink():
            _safe_directory(bin_root, "Claude plugin bin directory")
            if not os.access(bin_root, os.W_OK):
                raise NativeToolchainError("Claude plugin bin directory is not controller-writable")
        else:
            bin_root.mkdir(mode=0o700)
            created_bin = True
        for output in (launcher, python_link, python_runtime_link):
            if output.exists() or output.is_symlink():
                raise NativeToolchainError(f"Claude plugin output must not pre-exist: {output.name}")

        runtime_root.mkdir(mode=0o700)
        created_runtime = True
        staged_python = _stage_claude_runtime(runtime_root, receipt)

        python_name = Path(receipt["interpreter"]["resolved_path"]).name
        staged_python_executable = staged_python / "bin" / python_name
        if not staged_python_executable.is_file():
            raise NativeToolchainError("staged Specify Python executable is missing")
        python_runtime_link.symlink_to(os.path.relpath(staged_python_executable, bin_root))
        created_outputs.append(python_runtime_link)

        handle = python_link.open("xb")
        created_outputs.append(python_link)
        with handle:
            handle.write(_claude_python_launcher_bytes())
        os.chmod(python_link, 0o555)

        handle = launcher.open("xb")
        created_outputs.append(launcher)
        with handle:
            handle.write(_claude_specify_launcher_bytes(receipt))
        os.chmod(launcher, 0o555)
        if created_bin:
            os.chmod(bin_root, 0o555)

        launchers = {"specify": launcher}
        identity = _claude_runtime_identity(target, receipts, launchers)
        prepared = PreparedNativeToolchain(
            workspace=target,
            launcher_dir=bin_root,
            launchers=launchers,
            path_entries=(bin_root,),
            environment=_fixed_environment(),
            readonly_roots=(runtime_root, bin_root, target / "speckit_pro_runner"),
            runtime_identity=identity,
        )
        verify_native_toolchain(prepared)
        return prepared
    except Exception:
        if created_bin and bin_root.exists() and not bin_root.is_symlink():
            os.chmod(bin_root, 0o700)
        for output in reversed(created_outputs):
            if output.exists() or output.is_symlink():
                output.unlink()
        if created_runtime and runtime_root.exists() and not runtime_root.is_symlink():
            _remove_created_tree(runtime_root)
        if created_bin and bin_root.exists() and not any(bin_root.iterdir()):
            bin_root.rmdir()
        raise


def _stage_claude_runtime(
    runtime_root: Path,
    receipt: dict[str, Any],
) -> Path:
    source_python = Path(receipt["python_root"])
    source_specify = Path(receipt["tool_root"])
    staged_python = runtime_root / "python"
    staged_specify = runtime_root / "specify"
    mappings = ((source_python, staged_python), (source_specify, staged_specify))
    _copy_protected_tree(
        source_python,
        staged_python,
        mappings,
        ignore_python_bytecode_caches=True,
    )
    _copy_protected_tree(source_specify, staged_specify, mappings)
    os.chmod(runtime_root, 0o555)
    return staged_python


def verify_native_toolchain(prepared: PreparedNativeToolchain) -> None:
    """Fail closed if controller bytes or an admitted installation changed."""

    identity = prepared.runtime_identity
    _require_identity_digest(identity)
    if identity.get("schema_version") == CLAUDE_PLUGIN_SCHEMA_VERSION:
        target = _safe_plugin_root(prepared.workspace)
        _verify_claude_plugin_toolchain(prepared, target)
        return
    if identity.get("schema_version") != SCHEMA_VERSION:
        raise NativeToolchainError("native toolchain runtime identity schema is unsupported")
    target = _safe_workspace(prepared.workspace)
    tools = _required_tools(identity.get("required_tools", ()))
    receipts = identity.get("tools")
    if not isinstance(receipts, dict) or set(receipts) != set(tools):
        raise NativeToolchainError("native toolchain identity has an invalid tool receipt set")

    current: dict[str, dict[str, Any]] = {}
    if "specify" in tools:
        current["specify"] = _inspect_specify(
            Path(receipts["specify"]["source_path"]),
            target,
            expected_versions=(
                receipts["specify"]["python_version"],
                receipts["specify"]["version"],
            ),
        )
        launcher = prepared.launchers.get("specify")
        expected = target / _LAUNCHER_DIRECTORY / "specify"
        if launcher != expected:
            raise NativeToolchainError("Specify launcher is outside the controller-owned path")
        _require_exact_file(launcher, _specify_launcher_bytes(current["specify"]), 0o555)
        _safe_directory(launcher.parent, "native tool launcher directory", expected_mode=0o555)
    if "uv" in tools:
        current["uv"] = _inspect_uv(
            Path(receipts["uv"]["source_path"]),
            target,
            expected_version=receipts["uv"]["version"],
        )
        if prepared.launchers.get("uv") != Path(current["uv"]["executable"]["resolved_path"]):
            raise NativeToolchainError("uv launcher no longer names the admitted executable")

    if current != receipts:
        raise NativeToolchainError("installed native toolchain changed after preparation")
    _verify_versions(current, target)
    expected_identity = _runtime_identity(target, tools, current, prepared.launchers)
    if expected_identity != identity:
        raise NativeToolchainError("native toolchain runtime identity is stale")
    if prepared.path_entries != _path_entries(tools, prepared.launchers):
        raise NativeToolchainError("native toolchain PATH entries changed after preparation")
    if prepared.readonly_roots != _readonly_roots(current):
        raise NativeToolchainError("native toolchain read-only roots changed after preparation")
    if prepared.environment != expected_identity["environment"]["fixed"]:
        raise NativeToolchainError("native toolchain environment changed after preparation")


def _required_tools(values: Collection[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise NativeToolchainError("required_tools must be a collection of tool names")
    if not values:
        raise NativeToolchainError("at least one native tool must be requested explicitly")
    if any(not isinstance(value, str) for value in values):
        raise NativeToolchainError("native tool names must be strings")
    tools = tuple(sorted(set(values)))
    unknown = set(tools) - _ALLOWED_TOOLS
    if unknown:
        raise NativeToolchainError(f"unsupported native tool request: {sorted(unknown)!r}")
    return tools


def _safe_workspace(value: str | Path) -> Path:
    raw = Path(value).absolute()
    _safe_directory(raw, "workspace")
    control = raw / ".codex"
    _safe_directory(control, "workspace .codex")
    return raw.resolve()


def _safe_plugin_root(value: str | Path) -> Path:
    raw = Path(value).absolute()
    _safe_directory(raw, "Claude plugin root")
    return raw.resolve()


def _discover_executable(name: str, explicit: str | Path | None) -> Path:
    if explicit is None:
        discovered = shutil.which(name)
        if not discovered:
            raise NativeToolchainError(f"required installed tool is unavailable: {name}")
        candidate = Path(discovered)
    else:
        candidate = Path(explicit)
    if not candidate.is_absolute():
        raise NativeToolchainError(f"{name} executable must be an absolute path")
    return candidate


def _inspect_specify(
    source: Path,
    workspace: Path,
    *,
    expected_versions: tuple[str, str] | None = None,
) -> dict[str, Any]:
    entry = _executable_receipt(source, "Specify entry point")
    entry_path = Path(entry["resolved_path"])
    if entry_path.name != "specify" or entry_path.parent.name != "bin":
        raise NativeToolchainError("Specify entry point must be the installed tool bin/specify")
    tool_root = entry_path.parent.parent
    shebang = _read_shebang(entry_path)
    python = _executable_receipt(Path(shebang), "Specify Python interpreter")
    python_path = Path(python["resolved_path"])
    if python_path.parent.name != "bin":
        raise NativeToolchainError("Specify Python must resolve inside a versioned runtime bin")
    python_root = python_path.parent.parent

    python_tree = _tree_receipt(
        python_root,
        "Specify Python runtime",
        ignore_python_bytecode_caches=True,
    )
    tool_tree = _tree_receipt(tool_root, "Specify tool installation")
    python_version = (
        _probe_version(
            [str(python_path), "--version"],
            workspace,
            expected=r"Python ([0-9]+)\.([0-9]+)\.[0-9]+",
        )
        if expected_versions is None
        else expected_versions[0]
    )
    version_match = re.fullmatch(r"Python ([0-9]+)\.([0-9]+)\.[0-9]+", python_version)
    if version_match is None or int(version_match.group(1)) < 3 or (
        int(version_match.group(1)) == 3 and int(version_match.group(2)) < 11
    ):
        raise NativeToolchainError("Specify requires a protected Python 3.11+ runtime")
    site_packages = tool_root / "lib" / (
        f"python{version_match.group(1)}.{version_match.group(2)}"
    ) / "site-packages"
    _safe_directory(site_packages, "Specify site-packages")
    distribution = _specify_distribution_receipt(site_packages)
    specify_version = (
        _probe_version(
            [str(python_path), str(entry_path), "--version"],
            workspace,
            expected=r"specify [0-9]+\.[0-9]+\.[0-9]+(?:[-+._a-zA-Z0-9]*)?",
            additions={"PYTHONPATH": str(site_packages)},
        )
        if expected_versions is None
        else expected_versions[1]
    )
    if not re.fullmatch(
        r"specify [0-9]+\.[0-9]+\.[0-9]+(?:[-+._a-zA-Z0-9]*)?",
        specify_version,
    ):
        raise NativeToolchainError("stored Specify version is malformed")
    return {
        "source_path": str(source),
        "executable": entry,
        "interpreter": python,
        "python_version": python_version,
        "version": specify_version,
        "tool_root": str(tool_root),
        "tool_tree": tool_tree,
        "python_root": str(python_root),
        "python_tree": python_tree,
        "site_packages": str(site_packages),
        "distribution": distribution,
    }


def _specify_distribution_receipt(site_packages: Path) -> dict[str, Any]:
    candidates = sorted(site_packages.glob("specify_cli-*.dist-info"))
    if len(candidates) != 1:
        raise NativeToolchainError("Specify distribution metadata is missing or ambiguous")
    root = candidates[0]
    _safe_directory(root, "Specify distribution metadata")
    metadata_path = root / "METADATA"
    direct_url_path = root / "direct_url.json"
    metadata = _read_regular_file(metadata_path, "Specify distribution METADATA")
    direct_url_bytes = _read_regular_file(direct_url_path, "Specify distribution direct_url.json")
    try:
        metadata_text = metadata.decode("utf-8")
        direct_url = json.loads(direct_url_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise NativeToolchainError("Specify distribution metadata is malformed") from error
    name = next((line[6:].strip() for line in metadata_text.splitlines() if line.startswith("Name: ")), None)
    version = next((line[9:].strip() for line in metadata_text.splitlines() if line.startswith("Version: ")), None)
    if name != "specify-cli" or not isinstance(version, str) or not version:
        raise NativeToolchainError("Specify distribution name or version is invalid")
    if not isinstance(direct_url, dict):
        raise NativeToolchainError("Specify distribution direct URL is malformed")
    return {
        "root": str(root),
        "name": name,
        "version": version,
        "metadata_sha256": hashlib.sha256(metadata).hexdigest(),
        "direct_url_sha256": hashlib.sha256(direct_url_bytes).hexdigest(),
        "direct_url": direct_url,
    }


def _inspect_uv(
    source: Path,
    workspace: Path,
    *,
    expected_version: str | None = None,
) -> dict[str, Any]:
    executable = _executable_receipt(source, "uv executable")
    executable_path = Path(executable["resolved_path"])
    if executable_path.name != "uv" or executable_path.parent.name != "bin":
        raise NativeToolchainError("uv executable must resolve to an installed bin/uv")
    install_root = executable_path.parent.parent
    install_tree = _tree_receipt(install_root, "uv installation")
    version = (
        _probe_version(
            [str(executable_path), "--version"],
            workspace,
            expected=r"uv [0-9]+\.[0-9]+\.[0-9]+(?:[^\r\n]*)?",
        )
        if expected_version is None
        else expected_version
    )
    if not re.fullmatch(r"uv [0-9]+\.[0-9]+\.[0-9]+(?:[^\r\n]*)?", version):
        raise NativeToolchainError("stored uv version is malformed")
    return {
        "source_path": str(source),
        "executable": executable,
        "version": version,
        "install_root": str(install_root),
        "install_tree": install_tree,
    }


def _verify_versions(receipts: dict[str, dict[str, Any]], workspace: Path) -> None:
    if "specify" in receipts:
        receipt = receipts["specify"]
        python = receipt["interpreter"]["resolved_path"]
        entrypoint = receipt["executable"]["resolved_path"]
        observed_python = _probe_version(
            [python, "--version"],
            workspace,
            expected=r"Python ([0-9]+)\.([0-9]+)\.[0-9]+",
        )
        observed_specify = _probe_version(
            [python, entrypoint, "--version"],
            workspace,
            expected=r"specify [0-9]+\.[0-9]+\.[0-9]+(?:[-+._a-zA-Z0-9]*)?",
            additions={"PYTHONPATH": receipt["site_packages"]},
        )
        if (observed_python, observed_specify) != (
            receipt["python_version"],
            receipt["version"],
        ):
            raise NativeToolchainError("Specify runtime version changed after preparation")
    if "uv" in receipts:
        receipt = receipts["uv"]
        observed = _probe_version(
            [receipt["executable"]["resolved_path"], "--version"],
            workspace,
            expected=r"uv [0-9]+\.[0-9]+\.[0-9]+(?:[^\r\n]*)?",
        )
        if observed != receipt["version"]:
            raise NativeToolchainError("uv version changed after preparation")


def _executable_receipt(source: Path, label: str) -> dict[str, Any]:
    absolute = source.absolute()
    resolved, links = _resolve_links(absolute, label)
    metadata = resolved.lstat()
    if not stat.S_ISREG(metadata.st_mode) or not os.access(resolved, os.X_OK):
        raise NativeToolchainError(f"{label} must resolve to an executable regular file")
    _require_protected(metadata, label)
    body = _read_regular_file(resolved, label)
    return {
        "source_path": str(absolute),
        "resolved_path": str(resolved),
        "links": links,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "mode": stat.S_IMODE(metadata.st_mode),
        "uid": metadata.st_uid,
    }


def _resolve_links(source: Path, label: str) -> tuple[Path, list[dict[str, Any]]]:
    current = Path(os.path.normpath(str(source)))
    links: list[dict[str, Any]] = []
    seen: set[tuple[Path, tuple[str, ...]]] = set()
    for _ in range(_MAX_LINKS + 1):
        found = _first_link(current, label)
        if found is None:
            if not current.exists():
                raise NativeToolchainError(f"{label} does not exist")
            return current, links
        link, suffix = found
        state = (link, suffix)
        if state in seen:
            raise NativeToolchainError(f"{label} contains a symlink cycle")
        seen.add(state)
        metadata = link.lstat()
        if metadata.st_uid not in _SAFE_OWNER_IDS:
            raise NativeToolchainError(f"{label} symlink has an untrusted owner")
        target = os.readlink(link)
        links.append(
            {
                "path": str(link),
                "target": target,
                "uid": metadata.st_uid,
                "mode": stat.S_IMODE(metadata.st_mode),
            }
        )
        replacement = Path(target)
        if not replacement.is_absolute():
            replacement = link.parent / replacement
        current = Path(os.path.normpath(str(replacement.joinpath(*suffix))))
    raise NativeToolchainError(f"{label} has too many symlink indirections")


def _first_link(path: Path, label: str) -> tuple[Path, tuple[str, ...]] | None:
    if not path.is_absolute():
        raise NativeToolchainError(f"{label} must be absolute")
    cursor = Path(path.anchor)
    parts = path.parts[1:]
    for index, part in enumerate(parts):
        cursor /= part
        try:
            metadata = cursor.lstat()
        except FileNotFoundError as error:
            raise NativeToolchainError(f"{label} does not exist") from error
        if stat.S_ISLNK(metadata.st_mode):
            return cursor, tuple(parts[index + 1 :])
    return None


def _is_python_bytecode_cache(name: str, metadata: os.stat_result) -> bool:
    """Return whether one installed-runtime entry is generated Python bytecode."""

    return (
        stat.S_ISDIR(metadata.st_mode) and name == "__pycache__"
    ) or (
        stat.S_ISREG(metadata.st_mode) and name.endswith(".pyc")
    )


def _is_python_bytecode_cache_path(path: Path) -> bool:
    """Return whether a relative path resolves inside generated bytecode state."""

    return "__pycache__" in path.parts or path.name.endswith(".pyc")


def _tree_receipt_entries(
    directory: Path, label: str, ignore_python_bytecode_caches: bool,
) -> list[tuple[os.DirEntry[str], os.stat_result]]:
    try:
        entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
    except OSError as error:
        raise NativeToolchainError(f"cannot inspect {label}") from error
    admitted = []
    for entry in entries:
        metadata = entry.stat(follow_symlinks=False)
        if ignore_python_bytecode_caches and _is_python_bytecode_cache(
            entry.name, metadata
        ):
            continue
        admitted.append((entry, metadata))
    return admitted


def _tree_receipt(
    root: Path,
    label: str,
    *,
    ignore_python_bytecode_caches: bool = False,
) -> dict[str, Any]:
    """Hash a protected tree, optionally excluding generated Python bytecode."""

    _safe_directory(root, label)
    records: list[dict[str, Any]] = []
    total_bytes = 0

    def visit(directory: Path) -> None:
        nonlocal total_bytes
        for entry, metadata in _tree_receipt_entries(
            directory, label, ignore_python_bytecode_caches
        ):
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            mode = stat.S_IMODE(metadata.st_mode)
            base: dict[str, Any] = {"path": relative, "mode": mode, "uid": metadata.st_uid}
            if stat.S_ISDIR(metadata.st_mode):
                _require_protected(metadata, f"{label} directory {relative}")
                records.append({**base, "kind": "directory"})
                visit(path)
            elif stat.S_ISREG(metadata.st_mode):
                _require_protected(metadata, f"{label} file {relative}")
                body = _read_regular_file(path, f"{label} file {relative}")
                total_bytes += len(body)
                if total_bytes > _MAX_TREE_BYTES:
                    raise NativeToolchainError(f"{label} exceeds the admitted byte limit")
                records.append(
                    {
                        **base,
                        "kind": "file",
                        "bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                    }
                )
            elif stat.S_ISLNK(metadata.st_mode):
                if metadata.st_uid not in _SAFE_OWNER_IDS:
                    raise NativeToolchainError(f"{label} symlink has an untrusted owner: {relative}")
                records.append({**base, "kind": "symlink", "target": os.readlink(path)})
            else:
                raise NativeToolchainError(f"{label} contains a special file: {relative}")
            if len(records) > _MAX_TREE_ENTRIES:
                raise NativeToolchainError(f"{label} exceeds the admitted entry limit")

    visit(root)
    return {
        "entries": len(records),
        "bytes": total_bytes,
        "sha256": _digest(records),
    }


def _staged_symlink_target(
    resolved: Path,
    source_roots: tuple[tuple[Path, Path], ...],
    ignore_python_bytecode_caches: bool,
) -> Path | None:
    """Map one admitted symlink target into its staged tree."""

    for source_root, staged_root in source_roots:
        try:
            relative = resolved.relative_to(source_root)
        except ValueError:
            continue
        if ignore_python_bytecode_caches and _is_python_bytecode_cache_path(relative):
            raise NativeToolchainError(
                "installed runtime symlink resolves into excluded Python bytecode caches"
            )
        return staged_root / relative
    return None


def _copy_protected_tree(
    source: Path,
    destination: Path,
    mappings: tuple[tuple[Path, Path], ...],
    *,
    ignore_python_bytecode_caches: bool = False,
) -> None:
    """Copy an admitted tree, excluding only generated bytecode when requested."""

    _safe_directory(source, "installed runtime source")
    source_roots = tuple((root.resolve(), staged) for root, staged in mappings)
    destination.mkdir(mode=0o700)

    def visit(source_dir: Path, destination_dir: Path) -> None:
        entries = sorted(os.scandir(source_dir), key=lambda entry: entry.name)
        for entry in entries:
            source_path = Path(entry.path)
            destination_path = destination_dir / entry.name
            metadata = entry.stat(follow_symlinks=False)
            if ignore_python_bytecode_caches and _is_python_bytecode_cache(
                entry.name, metadata
            ):
                continue
            if stat.S_ISDIR(metadata.st_mode):
                _require_protected(metadata, f"installed runtime directory {source_path}")
                destination_path.mkdir(mode=0o700)
                visit(source_path, destination_path)
                os.chmod(destination_path, 0o555)
            elif stat.S_ISREG(metadata.st_mode):
                _require_protected(metadata, f"installed runtime file {source_path}")
                body = _read_regular_file(source_path, f"installed runtime file {source_path}")
                with destination_path.open("xb") as handle:
                    handle.write(body)
                mode = 0o555 if stat.S_IMODE(metadata.st_mode) & 0o111 else 0o444
                os.chmod(destination_path, mode)
            elif stat.S_ISLNK(metadata.st_mode):
                if metadata.st_uid not in _SAFE_OWNER_IDS:
                    raise NativeToolchainError("installed runtime symlink has an untrusted owner")
                try:
                    resolved = source_path.resolve(strict=True)
                except (OSError, RuntimeError) as error:
                    raise NativeToolchainError("installed runtime contains an invalid symlink") from error
                staged_target = _staged_symlink_target(
                    resolved, source_roots, ignore_python_bytecode_caches
                )
                if staged_target is None:
                    raise NativeToolchainError("installed runtime symlink resolves outside admitted roots")
                destination_path.symlink_to(
                    os.path.relpath(staged_target, destination_path.parent),
                    target_is_directory=resolved.is_dir(),
                )
            else:
                raise NativeToolchainError("installed runtime contains a special file")

    visit(source, destination)
    os.chmod(destination, 0o555)


def _remove_created_tree(root: Path) -> None:
    os.chmod(root, 0o700)
    for path in root.rglob("*"):
        if path.is_dir() and not path.is_symlink():
            os.chmod(path, 0o700)
    for path in sorted(root.rglob("*"), key=lambda candidate: len(candidate.parts), reverse=True):
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            os.chmod(path, 0o700)
            path.rmdir()
    root.rmdir()


def _safe_directory(path: Path, label: str, *, expected_mode: int | None = None) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise NativeToolchainError(f"{label} must be an existing directory") from error
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise NativeToolchainError(f"{label} must be a non-symlink directory")
    _require_protected(metadata, label)
    if expected_mode is not None and stat.S_IMODE(metadata.st_mode) != expected_mode:
        raise NativeToolchainError(f"{label} mode changed after preparation")


def _require_protected(metadata: os.stat_result, label: str) -> None:
    if metadata.st_uid not in _SAFE_OWNER_IDS:
        raise NativeToolchainError(f"{label} has an untrusted owner")
    if stat.S_IMODE(metadata.st_mode) & 0o022:
        raise NativeToolchainError(f"{label} is group/world writable")


def _read_regular_file(path: Path, label: str) -> bytes:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode):
        raise NativeToolchainError(f"{label} must be a regular file")
    if metadata.st_size > _MAX_FILE_BYTES:
        raise NativeToolchainError(f"{label} exceeds the admitted file limit")
    try:
        body = path.read_bytes()
    except OSError as error:
        raise NativeToolchainError(f"cannot read {label}") from error
    if len(body) != metadata.st_size:
        raise NativeToolchainError(f"{label} changed while it was read")
    after = path.lstat()
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
    ):
        raise NativeToolchainError(f"{label} changed while it was read")
    return body


def _read_shebang(path: Path) -> str:
    body = _read_regular_file(path, "Specify entry point")
    first_line = body.splitlines()[0] if body else b""
    if not first_line.startswith(b"#!") or len(first_line) > 4096:
        raise NativeToolchainError("Specify entry point has no bounded absolute Python shebang")
    try:
        interpreter = first_line[2:].decode("utf-8")
    except UnicodeDecodeError as error:
        raise NativeToolchainError("Specify shebang is not UTF-8") from error
    if not interpreter.startswith("/") or any(character.isspace() for character in interpreter):
        raise NativeToolchainError("Specify shebang must name one absolute Python interpreter")
    return interpreter


def _probe_version(
    argv: list[str],
    workspace: Path,
    *,
    expected: str,
    additions: dict[str, str] | None = None,
) -> str:
    environment = {
        "HOME": str(workspace),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONSAFEPATH": "1",
    }
    if additions:
        environment.update(additions)
    try:
        result = subprocess.run(
            argv,
            cwd=workspace,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=_PROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise NativeToolchainError("native tool version probe could not complete") from error
    output = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(expected, output):
        raise NativeToolchainError("native tool version probe returned an invalid result")
    return output


def _specify_launcher_bytes(receipt: dict[str, Any]) -> bytes:
    python = json.dumps(receipt["interpreter"]["resolved_path"])
    entrypoint = json.dumps(receipt["executable"]["resolved_path"])
    site_packages = json.dumps(receipt["site_packages"])
    script = f'''#!{receipt["interpreter"]["resolved_path"]} -I
import os
from pathlib import Path
import sys

workspace = Path(__file__).resolve(strict=True).parents[2]
allowed = ("LANG", "LC_ALL", "LC_CTYPE", "LOGNAME", "PATH", "TERM", "TMPDIR", "USER")
environment = {{key: os.environ[key] for key in allowed if key in os.environ}}
environment.update({{
    "HOME": str(workspace),
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONNOUSERSITE": "1",
    "PYTHONPATH": {site_packages},
    "PYTHONSAFEPATH": "1",
}})
python = {python}
entrypoint = {entrypoint}
os.execve(python, [python, entrypoint, *sys.argv[1:]], environment)
'''
    return script.encode("utf-8")


def _claude_python_launcher_bytes() -> bytes:
    script = f'''#!/usr/bin/env -S {_CLAUDE_PYTHON_RUNTIME} -I
import os
from pathlib import Path
import sys

plugin = Path(__file__).resolve(strict=True).parents[1]
python = plugin / "bin" / {_CLAUDE_PYTHON_RUNTIME!r}
workspace = Path.cwd().resolve(strict=True)
allowed = ("LANG", "LC_ALL", "LC_CTYPE", "LOGNAME", "PATH", "TERM", "TMPDIR", "USER")
environment = {{key: os.environ[key] for key in allowed if key in os.environ}}
environment.update({{
    "GIT_CONFIG_NOSYSTEM": "1",
    "HOME": str(workspace),
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONNOUSERSITE": "1",
    "PYTHONPATH": str(plugin),
    "PYTHONSAFEPATH": "1",
}})
os.execve(str(python), [str(python), "-B", "-P", "-s", *sys.argv[1:]], environment)
'''
    return script.encode("utf-8")


def _claude_specify_launcher_bytes(receipt: dict[str, Any]) -> bytes:
    version = re.fullmatch(
        r"Python ([0-9]+)\.([0-9]+)\.[0-9]+", receipt["python_version"]
    )
    if version is None:
        raise NativeToolchainError("stored Specify Python version is malformed")
    python_name = Path(receipt["interpreter"]["resolved_path"]).name
    site_relative = (
        Path("lib")
        / f"python{version.group(1)}.{version.group(2)}"
        / "site-packages"
    )
    script = f'''#!/usr/bin/env -S python3 -I
import os
from pathlib import Path
import sys

plugin = Path(__file__).resolve(strict=True).parents[1]
runtime = plugin / ".native-toolchain"
python = runtime / "python" / "bin" / {python_name!r}
entrypoint = runtime / "specify" / "bin" / "specify"
site_packages = runtime / "specify" / {site_relative.as_posix()!r}
workspace = Path.cwd().resolve(strict=True)
allowed = ("LANG", "LC_ALL", "LC_CTYPE", "LOGNAME", "PATH", "TERM", "TMPDIR", "USER")
environment = {{key: os.environ[key] for key in allowed if key in os.environ}}
environment.update({{
    "HOME": str(workspace),
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONNOUSERSITE": "1",
    "PYTHONPATH": str(site_packages),
    "PYTHONSAFEPATH": "1",
}})
os.execve(str(python), [str(python), str(entrypoint), *sys.argv[1:]], environment)
'''
    return script.encode("utf-8")


def _verify_claude_plugin_toolchain(
    prepared: PreparedNativeToolchain,
    target: Path,
) -> None:
    identity = prepared.runtime_identity
    if identity.get("transport") != "claude-plugin-bin":
        raise NativeToolchainError("Claude plugin toolchain transport is invalid")
    tools = _required_tools(identity.get("required_tools", ()))
    if tools != ("specify",):
        raise NativeToolchainError("Claude plugin toolchain supports only Specify")
    receipts = identity.get("tools")
    if not isinstance(receipts, dict) or set(receipts) != {"specify"}:
        raise NativeToolchainError("Claude plugin toolchain receipt set is invalid")
    receipt = receipts["specify"]
    current = _inspect_specify(
        Path(receipt["source_path"]),
        target,
        expected_versions=(receipt["python_version"], receipt["version"]),
    )
    if current != receipt:
        raise NativeToolchainError("installed native toolchain changed after preparation")

    runtime_root = target / _CLAUDE_RUNTIME_DIRECTORY
    bin_root = target / _CLAUDE_BIN_DIRECTORY
    source_runner = target / "speckit_pro_runner"
    _safe_directory(runtime_root, "Claude plugin toolchain directory", expected_mode=0o555)
    _safe_directory(bin_root, "Claude plugin bin directory")
    python_root = runtime_root / "python"
    staged = identity.get("staged")
    observed_staged = _claude_staged_identity(
        target,
        runtime_root,
        bin_root,
    )
    if observed_staged != staged:
        raise NativeToolchainError("staged Claude plugin toolchain changed after preparation")
    _verify_internal_tree_links(runtime_root)

    python_name = Path(receipt["interpreter"]["resolved_path"]).name
    python_link = bin_root / "python3"
    _require_exact_file(python_link, _claude_python_launcher_bytes(), 0o555)
    python_runtime_link = bin_root / _CLAUDE_PYTHON_RUNTIME
    if not python_runtime_link.is_symlink():
        raise NativeToolchainError("Claude plugin Python runtime link is missing")
    expected_target = os.path.relpath(python_root / "bin" / python_name, bin_root)
    if os.readlink(python_runtime_link) != expected_target:
        raise NativeToolchainError("Claude plugin Python runtime link changed after preparation")
    try:
        python_runtime_link.resolve(strict=True).relative_to(runtime_root)
    except (OSError, RuntimeError, ValueError) as error:
        raise NativeToolchainError("Claude plugin Python link escapes the staged runtime") from error

    launcher = prepared.launchers.get("specify")
    expected_launcher = bin_root / "specify"
    if launcher != expected_launcher:
        raise NativeToolchainError("Specify launcher is outside the Claude plugin bin directory")
    _require_exact_file(launcher, _claude_specify_launcher_bytes(current), 0o555)
    if prepared.launcher_dir != bin_root:
        raise NativeToolchainError("Claude plugin launcher directory changed after preparation")
    if prepared.path_entries != (bin_root,):
        raise NativeToolchainError("Claude plugin PATH entries changed after preparation")
    if prepared.readonly_roots != (runtime_root, bin_root, source_runner):
        raise NativeToolchainError("Claude plugin read-only roots changed after preparation")
    if prepared.environment != _fixed_environment():
        raise NativeToolchainError("native toolchain environment changed after preparation")

    expected_identity = _claude_runtime_identity(target, {"specify": current}, prepared.launchers)
    if expected_identity != identity:
        raise NativeToolchainError("native toolchain runtime identity is stale")
    observed_version = _probe_version(
        [str(expected_launcher), "--version"],
        target,
        expected=r"specify [0-9]+\.[0-9]+\.[0-9]+(?:[-+._a-zA-Z0-9]*)?",
        additions={"PATH": f"{bin_root}:/usr/bin:/bin"},
    )
    if observed_version != receipt["version"]:
        raise NativeToolchainError("relocated Specify version changed after preparation")


def _verify_internal_tree_links(root: Path) -> None:
    for path in root.rglob("*"):
        if not path.is_symlink():
            continue
        try:
            path.resolve(strict=True).relative_to(root)
        except (OSError, RuntimeError, ValueError) as error:
            raise NativeToolchainError("staged native toolchain contains an external symlink") from error


def _staged_tree_record(
    plugin_root: Path,
    root: Path,
    label: str,
    *,
    ignore_python_bytecode_caches: bool = False,
) -> dict[str, Any]:
    _safe_directory(root, label, expected_mode=0o555)
    return _tree_record(
        plugin_root,
        root,
        label,
        ignore_python_bytecode_caches=ignore_python_bytecode_caches,
    )


def _tree_record(
    plugin_root: Path,
    root: Path,
    label: str,
    *,
    ignore_python_bytecode_caches: bool = False,
) -> dict[str, Any]:
    return {
        "path": root.relative_to(plugin_root).as_posix(),
        "mode": stat.S_IMODE(root.lstat().st_mode),
        "tree": _tree_receipt(
            root,
            label,
            ignore_python_bytecode_caches=ignore_python_bytecode_caches,
        ),
    }


def _claude_runner_record(
    plugin_root: Path,
    python_link: Path,
) -> dict[str, Any]:
    runner_root = plugin_root / "speckit_pro_runner"
    _safe_directory(runner_root, "Claude plugin SpecKit Pro runner")
    record = _tree_record(
        plugin_root,
        runner_root,
        "Claude plugin SpecKit Pro runner",
        ignore_python_bytecode_caches=True,
    )
    record["version"] = _probe_version(
        [str(python_link), "-m", "speckit_pro_runner", "--version"],
        plugin_root,
        expected=r"speckit-pro-runner [0-9]+\.[0-9]+\.[0-9]+(?:[-+._a-zA-Z0-9]*)?",
        additions={"PATH": f"{python_link.parent}:/usr/bin:/bin"},
    )
    return record


def _claude_staged_identity(
    plugin_root: Path,
    runtime_root: Path,
    bin_root: Path,
) -> dict[str, Any]:
    python_root = runtime_root / "python"
    return {
        "directories": {
            "runtime": _directory_record(plugin_root, runtime_root),
            "bin": _directory_record(plugin_root, bin_root),
        },
        "python": _staged_tree_record(
            plugin_root,
            python_root,
            "staged Python runtime",
            ignore_python_bytecode_caches=True,
        ),
        "runner": _claude_runner_record(
            plugin_root,
            bin_root / "python3",
        ),
        "specify": _staged_tree_record(
            plugin_root,
            runtime_root / "specify",
            "staged Specify runtime",
        ),
    }


def _claude_runtime_identity(
    plugin_root: Path,
    receipts: dict[str, dict[str, Any]],
    launchers: dict[str, Path],
) -> dict[str, Any]:
    runtime_root = plugin_root / _CLAUDE_RUNTIME_DIRECTORY
    bin_root = plugin_root / _CLAUDE_BIN_DIRECTORY
    launcher = launchers["specify"]
    launcher_body = _read_regular_file(launcher, "Claude plugin Specify launcher")
    python_link = bin_root / "python3"
    python_body = _read_regular_file(python_link, "Claude plugin Python launcher")
    identity: dict[str, Any] = {
        "schema_version": CLAUDE_PLUGIN_SCHEMA_VERSION,
        "transport": "claude-plugin-bin",
        "required_tools": ["specify"],
        "tools": receipts,
        "staged": _claude_staged_identity(
            plugin_root,
            runtime_root,
            bin_root,
        ),
        "launchers": {
            "specify": {
                "path": launcher.relative_to(plugin_root).as_posix(),
                "bytes": len(launcher_body),
                "sha256": hashlib.sha256(launcher_body).hexdigest(),
                "mode": stat.S_IMODE(launcher.lstat().st_mode),
            },
            "python3": {
                "path": python_link.relative_to(plugin_root).as_posix(),
                "bytes": len(python_body),
                "sha256": hashlib.sha256(python_body).hexdigest(),
                "mode": stat.S_IMODE(python_link.lstat().st_mode),
            },
            "python-runtime": {
                "path": (bin_root / _CLAUDE_PYTHON_RUNTIME).relative_to(plugin_root).as_posix(),
                "kind": "internal-symlink",
                "target": os.readlink(bin_root / _CLAUDE_PYTHON_RUNTIME),
            },
        },
        "path_entries": ["bin"],
        "readonly_roots": [".native-toolchain", "bin", "speckit_pro_runner"],
        "environment": {
            "home": "$SUBJECT_CWD",
            "preserved": ["LANG", "LC_ALL", "LC_CTYPE", "LOGNAME", "PATH", "TERM", "TMPDIR", "USER"],
            "fixed": _fixed_environment(),
        },
        "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    identity["identity_sha256"] = _digest(identity)
    return identity


def _directory_record(plugin_root: Path, path: Path) -> dict[str, Any]:
    metadata = path.lstat()
    return {
        "path": path.relative_to(plugin_root).as_posix(),
        "mode": stat.S_IMODE(metadata.st_mode),
        "uid": metadata.st_uid,
    }


def _runtime_identity(
    workspace: Path,
    tools: tuple[str, ...],
    receipts: dict[str, dict[str, Any]],
    launchers: dict[str, Path],
) -> dict[str, Any]:
    launcher_records: dict[str, dict[str, Any]] = {}
    for name, path in sorted(launchers.items()):
        if name == "specify":
            body = _read_regular_file(path, "Specify launcher")
            metadata = path.lstat()
            launcher_records[name] = {
                "path": path.relative_to(workspace).as_posix(),
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "mode": stat.S_IMODE(metadata.st_mode),
            }
        else:
            launcher_records[name] = {"path": str(path), "kind": "resolved-installed-binary"}
    identity: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "required_tools": list(tools),
        "tools": receipts,
        "launchers": launcher_records,
        "readonly_roots": [str(path) for path in _readonly_roots(receipts)],
        "environment": {
            "home": "$WORKSPACE",
            "preserved": ["LANG", "LC_ALL", "LC_CTYPE", "LOGNAME", "PATH", "TERM", "TMPDIR", "USER"],
            "fixed": _fixed_environment(),
        },
        "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    identity["identity_sha256"] = _digest(identity)
    return identity


def _fixed_environment() -> dict[str, str]:
    return {
        "GIT_CONFIG_NOSYSTEM": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONSAFEPATH": "1",
    }


def _readonly_roots(receipts: dict[str, dict[str, Any]]) -> tuple[Path, ...]:
    roots: set[Path] = set()
    if "specify" in receipts:
        roots.add(Path(receipts["specify"]["tool_root"]))
        roots.add(Path(receipts["specify"]["python_root"]))
    if "uv" in receipts:
        roots.add(Path(receipts["uv"]["install_root"]))
    return tuple(sorted(roots, key=str))


def _path_entries(tools: tuple[str, ...], launchers: dict[str, Path]) -> tuple[Path, ...]:
    entries: list[Path] = []
    if "specify" in tools:
        entries.append(launchers["specify"].parent)
    if "uv" in tools:
        entries.append(launchers["uv"].parent)
    return tuple(entries)


def _require_exact_file(path: Path | None, expected: bytes, expected_mode: int) -> None:
    if path is None:
        raise NativeToolchainError("required native tool launcher is missing")
    metadata = path.lstat()
    _require_protected(metadata, "native tool launcher")
    if stat.S_IMODE(metadata.st_mode) != expected_mode:
        raise NativeToolchainError("native tool launcher mode changed after preparation")
    if _read_regular_file(path, "native tool launcher") != expected:
        raise NativeToolchainError("native tool launcher bytes changed after preparation")


def _require_identity_digest(identity: dict[str, Any]) -> None:
    if not isinstance(identity, dict):
        raise NativeToolchainError("native toolchain runtime identity must be an object")
    supplied = identity.get("identity_sha256")
    content = {key: value for key, value in identity.items() if key != "identity_sha256"}
    if not isinstance(supplied, str) or supplied != _digest(content):
        raise NativeToolchainError("native toolchain runtime identity digest is invalid")


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()
