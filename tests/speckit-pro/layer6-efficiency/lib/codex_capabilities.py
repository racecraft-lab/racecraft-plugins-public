#!/usr/bin/env python3
"""Public capability evidence API and command-line entry point for G56R-002."""

from __future__ import annotations

import importlib
import sys
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from uuid import uuid4

LIB_DIR = Path(__file__).resolve().parent


def _load_runtime_dependencies() -> dict[str, object]:
    dependency_names = (
        "codex_capability_contract",
        "codex_capability_io",
        "codex_capability_sources",
        "codex_capability_observations",
        "codex_capability_matrix",
        "codex_capability_private",
        "codex_capability_retention_records",
        "codex_capability_retention",
        "codex_capability_freeze",
        "codex_capability_publish_io",
        "codex_capability_cli",
    )
    created_package = None
    package_name = __package__
    if not package_name:
        package_name = f"_g56r_capability_runtime_{uuid4().hex}"
        if package_name in sys.modules:
            raise RuntimeError("capability runtime package identifier collided")
        package = ModuleType(package_name)
        package.__package__ = package_name
        package.__path__ = [str(LIB_DIR)]
        package.__spec__ = ModuleSpec(package_name, loader=None, is_package=True)
        sys.modules[package_name] = package
        created_package = package_name
    try:
        package = sys.modules.get(package_name)
        try:
            package_paths = tuple(
                Path(value).resolve(strict=True)
                for value in getattr(package, "__path__", ())
            )
        except OSError as exc:
            raise RuntimeError("capability runtime package cannot be resolved") from exc
        if package_paths != (LIB_DIR,):
            raise RuntimeError("capability runtime package is bound to another checkout")
        dependencies = {
            name: importlib.import_module(f".{name}", package_name)
            for name in dependency_names
        }
        for name, dependency in dependencies.items():
            module_file = getattr(dependency, "__file__", None)
            try:
                actual_path = (
                    Path(module_file).resolve(strict=True)
                    if isinstance(module_file, str)
                    else None
                )
            except OSError as exc:
                raise RuntimeError(f"capability dependency {name} cannot be resolved") from exc
            expected_path = LIB_DIR.joinpath(f"{name}.py").resolve(strict=True)
            if actual_path != expected_path:
                raise RuntimeError(
                    f"capability dependency {name} does not resolve to {expected_path}"
                )
        return dependencies
    finally:
        if created_package is not None:
            for module_name in tuple(sys.modules):
                if (
                    module_name == created_package
                    or module_name.startswith(f"{created_package}.")
                ):
                    sys.modules.pop(module_name, None)

_EXPORTS_BY_MODULE = (
    ("codex_capability_cli", ("main",)),
    (
        "codex_capability_contract",
        (
            "APPROVED_CANARY_EXECUTORS", "APPROVED_LIVE_COLLECTION_METHODS",
            "CANONICAL_MANIFEST_DIGEST", "CANONICAL_MANIFEST_SCHEMA_VERSION",
            "CANONICAL_MANIFEST_SNAPSHOT_ID", "DELETION_INTENTS_DIR",
            "DELETION_RECORDS_DIR", "ERROR_TERMINALS", "EXTRACT_NORMALIZATION",
            "HAS_DESCRIPTOR_RELATIVE_IO", "PENDING_TELEMETRY_PROFILE_ID",
            "PRIVATE_REFRESH_MAX_BYTES", "PUBLICATION_RECEIPTS_DIR",
            "RAW_EVIDENCE_PENDING_DAYS", "RAW_EVIDENCE_RETENTION_DAYS",
            "RETENTION_LOCK_FILE", "RETENTION_RECORDS_DIR", "SCHEMA_VERSION",
            "SURFACES", "canonical_bytes", "digest",
        ),
    ),
    (
        "codex_capability_freeze",
        (
            "build_canary_successor", "build_freeze", "build_runtime_snapshot",
            "publish_with_raw_evidence_retention", "validate_freeze",
            "validate_tuple_decisions",
        ),
    ),
    ("codex_capability_io", ("digest_regular_file",)),
    (
        "codex_capability_matrix",
        (
            "evaluate_surface_matrix", "validate_canary_result",
            "validate_canary_results", "validate_surface_matrix",
        ),
    ),
    (
        "codex_capability_observations",
        (
            "build_client_identity", "build_repository_binding",
            "candidate_tuples_from_manifest", "candidate_tuples_from_published",
            "fixture_observation", "repository_binding_from_checkout", "sanitize",
            "unknown_observation", "validate_observation",
            "validate_repository_binding", "validate_work_item",
        ),
    ),
    (
        "codex_capability_private",
        (
            "materialize_source_capture", "materialize_unknown_capture",
            "read_content_addressed_private_file", "read_private_external_file",
            "validate_canary_evidence", "validate_content_addressed_private_file",
            "validate_private_external_file", "validate_raw_evidence_root",
            "validate_source_capture_evidence", "validate_unknown_observation_evidence",
        ),
    ),
    ("codex_capability_retention", ("reconcile_raw_evidence_retention",)),
    (
        "codex_capability_sources",
        (
            "normalize_source_refreshes", "validate_manifest",
            "validate_published_source_refreshes", "validate_source_refreshes",
        ),
    ),
)
__capability_internal_modules__ = _load_runtime_dependencies()
for _owner_name, _export_names in _EXPORTS_BY_MODULE:
    _owner = __capability_internal_modules__[_owner_name]
    for _export_name in _export_names:
        globals()[_export_name] = getattr(_owner, _export_name)

del (
    LIB_DIR,
    ModuleSpec,
    ModuleType,
    Path,
    _EXPORTS_BY_MODULE,
    _export_name,
    _export_names,
    _load_runtime_dependencies,
    _owner,
    _owner_name,
    importlib,
    sys,
    uuid4,
)
globals().pop("annotations", None)

__all__ = (
    "APPROVED_CANARY_EXECUTORS", "APPROVED_LIVE_COLLECTION_METHODS",
    "CANONICAL_MANIFEST_DIGEST", "CANONICAL_MANIFEST_SCHEMA_VERSION",
    "CANONICAL_MANIFEST_SNAPSHOT_ID", "DELETION_INTENTS_DIR", "DELETION_RECORDS_DIR",
    "ERROR_TERMINALS", "EXTRACT_NORMALIZATION", "HAS_DESCRIPTOR_RELATIVE_IO",
    "PENDING_TELEMETRY_PROFILE_ID", "PRIVATE_REFRESH_MAX_BYTES", "PUBLICATION_RECEIPTS_DIR",
    "RAW_EVIDENCE_PENDING_DAYS", "RAW_EVIDENCE_RETENTION_DAYS", "RETENTION_LOCK_FILE",
    "RETENTION_RECORDS_DIR", "SCHEMA_VERSION", "SURFACES", "build_canary_successor",
    "build_client_identity", "build_freeze", "build_repository_binding",
    "build_runtime_snapshot", "candidate_tuples_from_manifest", "candidate_tuples_from_published",
    "canonical_bytes", "digest", "digest_regular_file", "evaluate_surface_matrix",
    "fixture_observation", "main", "materialize_source_capture", "materialize_unknown_capture",
    "normalize_source_refreshes", "publish_with_raw_evidence_retention",
    "read_content_addressed_private_file", "read_private_external_file",
    "reconcile_raw_evidence_retention", "repository_binding_from_checkout", "sanitize",
    "unknown_observation", "validate_canary_evidence", "validate_canary_result",
    "validate_canary_results", "validate_content_addressed_private_file", "validate_freeze",
    "validate_manifest", "validate_observation", "validate_private_external_file",
    "validate_published_source_refreshes", "validate_raw_evidence_root",
    "validate_repository_binding", "validate_source_capture_evidence", "validate_source_refreshes",
    "validate_surface_matrix", "validate_tuple_decisions", "validate_unknown_observation_evidence",
    "validate_work_item",
)


if __name__ == "__main__":
    raise SystemExit(main())
