#!/usr/bin/env python3
"""Public treatment validation and replay API for G56R-002.

This compatibility facade provides namespace hygiene, not an in-process
security boundary. Run callers that can mutate Python module state in a
separate process before relying on validation or replay results.
"""

from __future__ import annotations

import importlib.util
import sys
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from uuid import uuid4

LIB_DIR = Path(__file__).resolve().parent
_TREATMENT_DEPENDENCY_NAMES = (
    "treatment_trace_capability",
    "treatment_trace_authority",
    "treatment_trace_io",
    "treatment_trace_json_schema",
    "treatment_trace_model",
    "treatment_trace_fields",
    "treatment_trace_bundle",
    "treatment_trace_fixture",
    "treatment_trace_replay",
    "treatment_trace_successor",
    "treatment_trace_cli",
)
_runtime_package = f"_g56r_treatment_runtime_{uuid4().hex}"
_package = ModuleType(_runtime_package)
_package.__package__ = _runtime_package
_package.__path__ = [str(LIB_DIR)]
_package.__spec__ = ModuleSpec(_runtime_package, loader=None, is_package=True)
sys.modules[_runtime_package] = _package
try:
    _cli_name = f"{_runtime_package}.treatment_trace_cli"
    _cli_spec = importlib.util.spec_from_file_location(
        _cli_name,
        LIB_DIR.joinpath("treatment_trace_cli.py").resolve(strict=True),
    )
    if _cli_spec is None or _cli_spec.loader is None:
        raise RuntimeError("cannot load treatment CLI dependency")
    _cli = importlib.util.module_from_spec(_cli_spec)
    sys.modules[_cli_name] = _cli
    _cli_spec.loader.exec_module(_cli)
    for _export_name in _cli.__all__:
        globals()[_export_name] = getattr(_cli, _export_name)

    for _dependency_name in _TREATMENT_DEPENDENCY_NAMES:
        _qualified_name = f"{_runtime_package}.{_dependency_name}"
        _dependency = sys.modules.get(_qualified_name)
        _expected_path = LIB_DIR.joinpath(f"{_dependency_name}.py").resolve(strict=True)
        _actual_file = getattr(_dependency, "__file__", None)
        try:
            _actual_path = Path(_actual_file).resolve(strict=True) if isinstance(_actual_file, str) else None
        except OSError as exc:
            raise RuntimeError(f"treatment dependency {_dependency_name} cannot be resolved") from exc
        if _actual_path != _expected_path:
            raise RuntimeError(f"treatment dependency {_dependency_name} does not resolve to {_expected_path}")
finally:
    for _module_name in tuple(sys.modules):
        if _module_name == _runtime_package or _module_name.startswith(f"{_runtime_package}."):
            sys.modules.pop(_module_name, None)

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
    "OBSERVATION_EVIDENCE_VERSION", "CONSUMPTION_EVIDENCE_VERSION",
    "SOURCE_EVIDENCE_VERSION", "TREATMENT_EVIDENCE_SET_VERSION",
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
