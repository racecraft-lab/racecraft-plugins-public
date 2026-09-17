"""Provider-free staging for the canonical Codex native-evaluation runtime."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import shutil
import stat
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


SCHEMA_VERSION = "native-eval-codex-runtime/v1"
CHECKOUT_ROOT = Path(__file__).resolve().parents[3]
PRODUCT_ROOT = CHECKOUT_ROOT / "speckit-pro"
_PRODUCT_IMPORT_LOCK = threading.RLock()


class RuntimeStageError(ValueError):
    """Raised before a runtime could be staged without ambiguity or overwrite."""


@dataclass(frozen=True)
class CodexRuntimeStage:
    """Paths and deterministic proof for one staged Codex runtime."""

    payload_root: Path
    agent_root: Path
    pythonpath: str
    runtime_identity: str
    proof: dict[str, Any]


@dataclass(frozen=True)
class _ProductApis:
    build_payloads: Callable[[Path, Path], None]
    source_roster: Callable[[Path], dict[str, Any]]
    materialize: Callable[..., Any]
    required_agents: tuple[str, ...]
    source_agent_files: tuple[str, ...]
    optional_helper: str


def stage_codex_runtime(
    repo_root: str | Path,
    build_root: str | Path,
    workspace: str | Path,
) -> CodexRuntimeStage:
    """Build and stage the exact checkout's complete Codex payload and agents."""

    repo = _data_repo_root(repo_root)
    build = Path(build_root).absolute()
    target = Path(workspace).absolute()
    payload_destination = target / ".agents"
    agent_destination = target / ".codex" / "agents"
    _preflight(repo, build, target, payload_destination, agent_destination)
    _validate_source_inputs(repo)

    apis = _load_product_apis()
    source_agent_root = repo / "speckit-pro" / "codex-agents"
    source_roster, built_payload, payload_files = _build_validated_payload(
        apis,
        repo,
        build,
        source_agent_root,
    )
    materializations = _materialize_default_agents(
        apis,
        source_agent_root,
    )
    staged_files = _stage_outputs(
        target,
        built_payload,
        payload_files,
        materializations,
    )
    proof = _proof(apis, source_roster, staged_files, materializations)
    runtime_identity = _runtime_identity(proof)
    return CodexRuntimeStage(
        payload_root=payload_destination,
        agent_root=agent_destination,
        pythonpath=str(payload_destination),
        runtime_identity=runtime_identity,
        proof=proof,
    )


def _build_validated_payload(
    apis: _ProductApis,
    repo: Path,
    build: Path,
    source_agent_root: Path,
) -> tuple[dict[str, Any], Path, list[dict[str, Any]]]:
    source_roster = _validate_roster(
        apis.source_roster(source_agent_root),
        apis.source_agent_files,
        label="source",
    )
    apis.build_payloads(repo, build)
    built_payload = build / "codex" / "speckit-pro"
    if not built_payload.is_dir() or built_payload.is_symlink():
        raise RuntimeStageError("product builder did not create a safe Codex payload")
    built_roster = _validate_roster(
        apis.source_roster(built_payload / "codex-agents"),
        apis.source_agent_files,
        label="built payload",
    )
    if built_roster != source_roster:
        raise RuntimeStageError("built payload agent roster differs from trusted source roster")
    payload_files = _tree_records(built_payload)
    _require_payload_members(payload_files)
    return source_roster, built_payload, payload_files


def _stage_outputs(
    workspace: Path,
    built_payload: Path,
    payload_files: list[dict[str, Any]],
    materializations: list[tuple[dict[str, Any], bytes]],
) -> list[dict[str, Any]]:
    payload_destination = workspace / ".agents"
    agent_destination = workspace / ".codex" / "agents"
    _copy_tree_without_links(built_payload, payload_destination)
    staged_files = _tree_records(payload_destination)
    if staged_files != payload_files:
        raise RuntimeStageError("staged payload bytes differ from product builder output")
    (workspace / ".codex").mkdir(exist_ok=True)
    agent_destination.mkdir()
    for record, destination_bytes in materializations:
        destination = workspace / record["destination_path"]
        with destination.open("xb") as handle:
            handle.write(destination_bytes)
        if destination.read_bytes() != destination_bytes:
            raise RuntimeStageError(f"materialized agent bytes changed while writing: {destination.name}")
    return staged_files


def _proof(
    apis: _ProductApis,
    source_roster: dict[str, Any],
    staged_files: list[dict[str, Any]],
    materializations: list[tuple[dict[str, Any], bytes]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "payload": {
            "root": ".agents",
            "file_count": len(staged_files),
            "tree_sha256": _digest(staged_files),
            "files": staged_files,
        },
        "roster": source_roster,
        "materializations": [record for record, _ in materializations],
        "optional_helper": {
            "name": apis.optional_helper,
            "source_path": f".agents/codex-agents/{apis.optional_helper}.toml",
            "activated": False,
        },
        "pythonpath_relative": ".agents",
    }


def _data_repo_root(value: str | Path) -> Path:
    raw = Path(value).absolute()
    if not raw.is_dir() or raw.is_symlink():
        raise RuntimeStageError("repo_root must be an existing non-symlink directory")
    candidate = raw.resolve()
    plugin_root = candidate / "speckit-pro"
    if not plugin_root.is_dir() or plugin_root.is_symlink():
        raise RuntimeStageError("repo_root is missing the plugin source tree")
    return candidate


def _preflight(
    repo: Path,
    build: Path,
    workspace: Path,
    payload_destination: Path,
    agent_destination: Path,
) -> None:
    protected = ((repo / "speckit-pro").resolve(), (repo / "dist").resolve(strict=False))
    for label, candidate in (("build_root", build), ("workspace", workspace)):
        resolved = candidate.resolve(strict=False)
        if any(_inside(resolved, root) for root in protected):
            raise RuntimeStageError(f"{label} must not be inside plugin source or dist")
    if build.exists() or build.is_symlink():
        raise RuntimeStageError("build_root must be a new isolated path")
    if not workspace.is_dir() or workspace.is_symlink():
        raise RuntimeStageError("workspace must be an existing non-symlink directory")
    if _overlaps(build.resolve(strict=False), workspace.resolve()):
        raise RuntimeStageError("build_root and workspace must be disjoint")
    if payload_destination.exists() or payload_destination.is_symlink():
        raise RuntimeStageError("workspace .agents destination already exists")
    if agent_destination.exists() or agent_destination.is_symlink():
        raise RuntimeStageError("workspace .codex/agents destination already exists")
    codex_root = workspace / ".codex"
    if codex_root.exists() and (codex_root.is_symlink() or not codex_root.is_dir()):
        raise RuntimeStageError("workspace .codex must be a non-symlink directory")


def _overlaps(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _inside(candidate: Path, root: Path) -> bool:
    return candidate == root or root in candidate.parents


def _validate_source_inputs(repo: Path) -> None:
    plugin_root = repo / "speckit-pro"
    for directory, directories, files in os.walk(plugin_root, followlinks=False):
        parent = Path(directory)
        for name in (*directories, *files):
            path = parent / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise RuntimeStageError(
                    f"unsafe source member must be a regular file or directory: {path.relative_to(repo)}"
                )
    license_path = repo / "LICENSE"
    if license_path.exists() or license_path.is_symlink():
        mode = license_path.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise RuntimeStageError("unsafe source member must be a regular file: LICENSE")


def _load_product_apis() -> _ProductApis:
    with _PRODUCT_IMPORT_LOCK:
        return _load_product_apis_locked()


def _load_product_apis_locked() -> _ProductApis:
    product_root = PRODUCT_ROOT
    _reject_foreign_product_modules(product_root)
    original_path = list(sys.path)
    sys.path[:] = [str(product_root), *[
        entry for entry in original_path if not _same_path(entry, product_root)
    ]]
    try:
        importlib.invalidate_caches()
        modules = {
            "payloads": importlib.import_module("speckit_pro_runner.gates.payloads"),
            "install": importlib.import_module("speckit_pro_runner.helpers.install"),
            "materializer": importlib.import_module("speckit_pro_runner.agent_materialization"),
        }
        _require_module_path(
            modules["payloads"],
            product_root / "speckit_pro_runner" / "gates" / "payloads.py",
        )
        _require_module_path(
            modules["install"],
            product_root / "speckit_pro_runner" / "helpers" / "install.py",
        )
        _require_module_path(
            modules["materializer"],
            product_root / "speckit_pro_runner" / "agent_materialization.py",
        )
        install = modules["install"]
        return _ProductApis(
            build_payloads=modules["payloads"].build_installed_plugin_payloads,
            source_roster=install.codex_agent_source_roster,
            materialize=modules["materializer"].materialize_agent_policy,
            required_agents=tuple(install.CODEX_REQUIRED_AGENT_NAMES),
            source_agent_files=tuple(install.CODEX_SOURCE_AGENT_TOML_NAMES),
            optional_helper=install.CODEX_OPTIONAL_HELPER_NAME,
        )
    finally:
        sys.path[:] = original_path


def _reject_foreign_product_modules(product_root: Path) -> None:
    for name, module in tuple(sys.modules.items()):
        if name != "speckit_pro_runner" and not name.startswith("speckit_pro_runner."):
            continue
        origins: list[Path] = []
        module_file = getattr(module, "__file__", None)
        if isinstance(module_file, str):
            origins.append(Path(module_file).resolve())
        package_paths = getattr(module, "__path__", ())
        origins.extend(Path(value).resolve() for value in package_paths if isinstance(value, str))
        if not origins or any(not _inside(origin, product_root) for origin in origins):
            raise RuntimeStageError(f"preloaded product module has a foreign origin: {name}")


def _same_path(value: Any, expected: Path) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return Path(value or ".").resolve() == expected.resolve()
    except OSError:
        return False


def _require_module_path(module: ModuleType, expected: Path) -> None:
    raw = getattr(module, "__file__", None)
    if not isinstance(raw, str) or Path(raw).resolve() != expected.resolve():
        raise RuntimeStageError(f"product implementation was not loaded from trusted checkout: {module.__name__}")


def _validate_roster(
    raw: Any,
    expected_names: tuple[str, ...],
    *,
    label: str,
) -> dict[str, Any]:
    if not isinstance(raw, dict) or "code" in raw:
        code = raw.get("code", "malformed") if isinstance(raw, dict) else "malformed"
        raise RuntimeStageError(f"{label} agent roster rejected: {code}")
    if not isinstance(raw.get("schema_version"), str) or not raw["schema_version"]:
        raise RuntimeStageError(f"{label} agent roster has no schema version")
    roster_id = raw.get("source_roster_id")
    if not isinstance(roster_id, str) or not roster_id.startswith("sha256:"):
        raise RuntimeStageError(f"{label} agent roster has no identity")
    records = raw.get("files")
    if not isinstance(records, list):
        raise RuntimeStageError(f"{label} agent roster files must be a list")
    names = [_roster_record(record, label) for record in records]
    if len(names) != len(set(names)):
        raise RuntimeStageError(f"{label} agent roster contains duplicate files")
    if tuple(names) != tuple(expected_names):
        missing = sorted(set(expected_names) - set(names))
        extra = sorted(set(names) - set(expected_names))
        raise RuntimeStageError(
            f"{label} agent roster mismatch; missing={missing!r}; extra={extra!r}"
        )
    return json.loads(json.dumps(raw, sort_keys=True))


def _roster_record(record: Any, label: str) -> str:
    if not isinstance(record, dict) or set(record) != {"name", "sha256"}:
        raise RuntimeStageError(f"{label} agent roster contains a malformed record")
    name = record["name"]
    digest = record["sha256"]
    if not isinstance(name, str) or not isinstance(digest, str) or len(digest) != 64:
        raise RuntimeStageError(f"{label} agent roster contains a malformed record")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise RuntimeStageError(f"{label} agent roster contains a malformed digest") from exc
    return name


def _tree_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if path.is_symlink():
            raise RuntimeStageError(f"runtime tree contains a symlink: {path.relative_to(root)}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise RuntimeStageError(f"runtime tree contains a non-file member: {path.relative_to(root)}")
        value = path.read_bytes()
        records.append({
            "path": path.relative_to(root).as_posix(),
            "byte_count": len(value),
            "sha256": _digest(value),
        })
    if not records:
        raise RuntimeStageError("runtime payload is empty")
    return records


def _require_payload_members(records: list[dict[str, Any]]) -> None:
    paths = {record["path"] for record in records}
    required = {
        ".codex-plugin/plugin.json",
        "codex-hooks.json",
        "README.md",
    }
    missing = sorted(required - paths)
    required_prefixes = ("codex-agents/", "skills/", "speckit_pro_runner/")
    missing.extend(prefix for prefix in required_prefixes if not any(path.startswith(prefix) for path in paths))
    if missing:
        raise RuntimeStageError(f"built Codex payload is incomplete: {missing!r}")


def _materialize_default_agents(
    apis: _ProductApis,
    source_root: Path,
) -> list[tuple[dict[str, Any], bytes]]:
    expected_files = tuple(sorted(
        (*[f"{name}.toml" for name in apis.required_agents], f"{apis.optional_helper}.toml"),
    ))
    if apis.source_agent_files != expected_files or len(expected_files) != len(set(expected_files)):
        raise RuntimeStageError("product default-agent inventory differs from trusted source roster")
    result: list[tuple[dict[str, Any], bytes]] = []
    for filename in apis.source_agent_files:
        relative = Path(filename)
        if relative.name != filename or relative.suffix != ".toml" or not relative.stem:
            raise RuntimeStageError(f"default agent filename is not canonical: {filename}")
        name = relative.stem
        source_relative = f"speckit-pro/codex-agents/{name}.toml"
        source = source_root / filename
        if not source.is_file() or source.is_symlink():
            raise RuntimeStageError(f"default agent source is missing or unsafe: {name}")
        source_bytes = source.read_bytes()
        materialized = apis.materialize(
            source_relative_path=source_relative,
            source_bytes=source_bytes,
            candidate_route=None,
            parent_controls=None,
        )
        destination_bytes = getattr(materialized, "destination_bytes", None)
        if not isinstance(destination_bytes, bytes):
            raise RuntimeStageError(f"materializer returned no destination bytes: {name}")
        if destination_bytes != source_bytes:
            raise RuntimeStageError(f"default materialization changed source bytes: {name}")
        proof = {
            "name": name,
            "source_path": source_relative,
            "destination_path": f".codex/agents/{name}.toml",
            "materialization_id": materialized.materialization_id,
            "materializer_version": materialized.materializer_version,
            "source_binding": materialized.source_binding,
            "materializer_binding": materialized.materializer_binding,
            "candidate_route": materialized.candidate_route,
            "parent_controls": materialized.parent_controls,
            "selected_model": materialized.selected_model,
            "selected_model_reasoning_effort": materialized.selected_model_reasoning_effort,
            "non_route_fields_digest": materialized.non_route_fields_digest,
            "non_route_fields_unchanged": materialized.non_route_fields_unchanged,
            "destination_bytes_digest": materialized.destination_bytes_digest,
            "instruction_digest": materialized.instruction_digest,
            "configuration_digest": materialized.configuration_digest,
            "byte_count": materialized.byte_count,
        }
        result.append((proof, destination_bytes))
    return result


def _copy_tree_without_links(source: Path, destination: Path) -> None:
    _tree_records(source)
    try:
        shutil.copytree(source, destination)
    except FileExistsError as exc:
        raise RuntimeStageError("workspace .agents destination appeared during staging") from exc


def _runtime_identity(proof: dict[str, Any]) -> str:
    return _digest({
        "schema_version": proof["schema_version"],
        "payload_tree_sha256": proof["payload"]["tree_sha256"],
        "roster": proof["roster"],
        "materializations": proof["materializations"],
        "optional_helper": proof["optional_helper"],
        "pythonpath_relative": proof["pythonpath_relative"],
    })


def _digest(value: Any) -> str:
    if isinstance(value, bytes):
        raw = value
    else:
        raw = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


__all__ = (
    "CodexRuntimeStage",
    "RuntimeStageError",
    "stage_codex_runtime",
)
