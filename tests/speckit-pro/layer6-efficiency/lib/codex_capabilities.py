#!/usr/bin/env python3
"""Public capability evidence API and command-line entry point for G56R-002."""

from __future__ import annotations

import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from codex_capability_cli import main
from codex_capability_contract import (
    APPROVED_CANARY_EXECUTORS,
    APPROVED_LIVE_COLLECTION_METHODS,
    CANONICAL_MANIFEST_DIGEST,
    CANONICAL_MANIFEST_SCHEMA_VERSION,
    CANONICAL_MANIFEST_SNAPSHOT_ID,
    DELETION_INTENTS_DIR,
    DELETION_RECORDS_DIR,
    ERROR_TERMINALS,
    EXTRACT_NORMALIZATION,
    HAS_DESCRIPTOR_RELATIVE_IO,
    PENDING_TELEMETRY_PROFILE_ID,
    PRIVATE_TEMPORARY_PREFIX,
    PRIVATE_REFRESH_MAX_BYTES,
    PUBLICATION_INTENTS_DIR,
    PUBLICATION_RECEIPTS_DIR,
    RAW_EVIDENCE_PENDING_DAYS,
    RAW_EVIDENCE_RETENTION_DAYS,
    RETENTION_LOCK_FILE,
    RETENTION_RECORDS_DIR,
    SCHEMA_VERSION,
    SURFACES,
    canonical_bytes,
    digest,
)
from codex_capability_freeze import (
    build_canary_successor,
    build_freeze,
    build_runtime_snapshot,
    publish_with_raw_evidence_retention,
    validate_freeze,
    validate_tuple_decisions,
)
from codex_capability_io import digest_regular_file
from codex_capability_matrix import (
    evaluate_surface_matrix,
    validate_canary_result,
    validate_canary_results,
    validate_surface_matrix,
)
from codex_capability_observations import (
    build_client_identity,
    build_repository_binding,
    candidate_tuples_from_manifest,
    candidate_tuples_from_published,
    fixture_observation,
    repository_binding_from_checkout,
    sanitize,
    unknown_observation,
    validate_observation,
    validate_repository_binding,
    validate_work_item,
)
from codex_capability_private import (
    materialize_source_capture,
    materialize_unknown_capture,
    read_content_addressed_private_file,
    read_private_external_file,
    validate_canary_evidence,
    validate_content_addressed_private_file,
    validate_private_external_file,
    validate_raw_evidence_root,
    validate_source_capture_evidence,
    validate_unknown_observation_evidence,
)
from codex_capability_retention import reconcile_raw_evidence_retention
from codex_capability_sources import (
    normalize_source_refreshes,
    validate_manifest,
    validate_published_source_refreshes,
    validate_source_refreshes,
)

del LIB_DIR, Path, sys
globals().pop("annotations", None)

__all__ = (
    "APPROVED_CANARY_EXECUTORS", "APPROVED_LIVE_COLLECTION_METHODS",
    "CANONICAL_MANIFEST_DIGEST", "CANONICAL_MANIFEST_SCHEMA_VERSION",
    "CANONICAL_MANIFEST_SNAPSHOT_ID", "DELETION_INTENTS_DIR", "DELETION_RECORDS_DIR",
    "ERROR_TERMINALS", "EXTRACT_NORMALIZATION", "HAS_DESCRIPTOR_RELATIVE_IO",
    "PENDING_TELEMETRY_PROFILE_ID", "PRIVATE_REFRESH_MAX_BYTES", "PRIVATE_TEMPORARY_PREFIX",
    "PUBLICATION_INTENTS_DIR", "PUBLICATION_RECEIPTS_DIR",
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
