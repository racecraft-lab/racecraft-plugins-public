#!/usr/bin/env python3
"""Public treatment validation and replay API for G56R-002."""

from __future__ import annotations

import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from treatment_trace_cli import *

__all__ = [
    "ABSOLUTE_PATH_RE", "APP_SERVER_FIELDS", "AUTHORIZED_PROFILE_CLASSIFICATIONS",
    "AUTHORIZED_PROFILE_CONDITIONS", "AUTHORIZED_PROFILE_SOURCES", "AUTHORIZED_PROHIBITED_CLAIMS",
    "CANCELLATION_REASON_CODES", "CAPABILITY_FIXTURE_PATH", "CAPABILITY_MODULE_PATH",
    "CLAIM_BY_CLASS", "CLASSIFICATIONS", "COMPLETENESS_BY_CLASS", "CREDENTIAL_RE",
    "DIGEST_RE", "DISPOSITION_REASON_CODES", "EVIDENCE_REF_RE", "FAILURE_DISPOSITIONS",
    "FALLBACK_REASON_CODES", "HAS_DESCRIPTOR_RELATIVE_IO", "HOSTNAME_RE",
    "INTERNAL_DERIVED_FIELDS", "INTERNAL_HOSTNAME_RE", "IP_CANDIDATE_RE", "IS_WINDOWS",
    "MANIFEST_PATH", "MAX_COLLECTION_ITEMS", "MAX_INPUT_BYTES", "MAX_NESTING_DEPTH",
    "MAX_RETAINED_STRING_LENGTH", "MAX_TOTAL_NODES", "OBJECTIVE_ID_FIELDS",
    "OBSERVATION_STATES", "PII_RE", "REMOTE_RE", "REPLAY_CASES",
    "REPLAY_DIGEST_MANIFEST_PATH", "REPLAY_DISCOVERY_MODEL_DELTAS", "REPLAY_FIXTURE_PATHS",
    "REPLAY_HOSTNAME_RE", "REPLAY_RUNTIME_EFFORT_AUTHORITY", "REPLAY_RUNTIME_EFFORT_AUTHORITY_ID",
    "REPLAY_TRACE_BASELINE_DIGESTS", "REROUTE_REASON_CODES", "REVISION_RE", "RFC3339_UTC_RE",
    "ROOT", "SANITIZED_IDENTIFIER_RE", "SCHEMA_PATH", "SCHEMA_VERSION", "SOURCE_RE",
    "SPEC_ID_RE", "SURFACES", "TELEMETRY_INVENTORY", "TRACE_KEYS", "TRAVERSAL_RE",
    "TREATMENT_FIXTURE_PATH", "UNLABELED_CREDENTIAL_RE", "build_treatment_successor",
    "canonical_bytes", "canonical_fixture_bytes", "content_id", "digest",
    "execution_trace_identity", "main", "profile_entry", "replay_fixture", "schema_file_digest",
    "telemetry_profile_id", "validate_treatment_bundle",
]

for _private_name in tuple(globals()):
    if _private_name not in __all__ and not _private_name.startswith("__"):
        del globals()[_private_name]
del _private_name


if __name__ == "__main__":
    raise SystemExit(main())
