#!/usr/bin/env python3
"""CAR-003 successor capability freeze: collection, admission, publication.

The freeze admits a model/effort tuple only when it appears in BOTH the
official-source candidate ledger and the pinned runtime catalog collected
through the **sole admitting surface** — the operator-run
``claude -p --model <alias-or-id>`` print-mode canary probe (FR-002). Every
other runtime surface is diagnostic: it may corroborate or invalidate an
admitted tuple, never admit one, because the catalog endpoint yields evidence
only under API-key authentication and no supported path may require an API key
(FR-004, FR-042).

This module is repository-only harness code. It performs **no live model
calls**: the live collection that feeds a real freeze is operator-only and
never runs in the default suite. Everything here operates on an already
collected record.

Reused, never modified: ``claude_capabilities`` for home-path and session-id
sanitization and for payload hashing, and the frozen CAR-002 trace contract for
the eight-member environment-override proof enumeration (FR-039).

**Exclusion-taxonomy split.** FR-029 closes the taxonomy but does not say which
of the two effort members covers which direction of the intersection. This
module fixes the split as:

* ``effort_not_source_admitted`` — the pinned runtime accepted the effort but
  the official-source ledger does not admit it.
* ``effort_source_not_admitted`` — the ledger admits the effort but the pinned
  runtime does not support it, either because it rejected the effort on the
  admitting surface or because the model is absent from the observed catalog.
* ``surface_evidence_incomplete`` — the model IS in the observed catalog but
  this rung of the ladder carries no admitting-surface observation. That is a
  probe-coverage gap, not a runtime refusal, and the two must not collapse.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[4]
RESEARCH_ROOT = REPO_ROOT / "docs" / "ai" / "research"
ARCHIVED_SNAPSHOT_PATH = RESEARCH_ROOT / "claude-runtime-capability-snapshot.json"
TRACE_CONTRACT_PATH = RESEARCH_ROOT / "claude-trace-contract.schema.json"

# FR-001, SC-001: the archived CAR-002 evidence set. Read, digested, and
# compared — never written.
CAR002_ARTIFACTS = (
    "docs/ai/research/claude-runtime-capability-snapshot.json",
    "docs/ai/research/claude-telemetry-capability-profile.json",
    "docs/ai/research/claude-trace-contract.schema.json",
)

SCHEMA_VERSION = "1.0.0"

# FR-002: the sole admitting runtime authority.
ADMITTING_SURFACE = "print_mode_canary_probe"

# FR-002, FR-004: what an observation that names no surface is read as. Missing
# provenance is a refusal, never a promotion: defaulting an unlabeled
# observation to the admitting surface would hand the one authority permitted to
# admit a tuple to the evidence that says least about where it came from. The
# sentinel sits outside both the admitting and the diagnostic sets, so
# :func:`classify_surface` refuses it and the rung it covers is recorded as
# ``surface_evidence_incomplete``.
UNLABELED_SURFACE = "unlabeled_surface"

# FR-004: corroborate or invalidate, never admit.
DIAGNOSTIC_SURFACES = (
    "subagent_frontmatter",
    "model_picker",
    "models_endpoint",
    "visible_default",
    "bundled_client",
)

# FR-002: effort admission is bounded by what configuration acceptance can
# establish. Acceptance proves the pinned client did not reject the value, not
# that the requested effort took effect in the run.
EFFORT_ADMISSION_CLAIM = {
    "basis": "configuration_acceptance",
    "verified_support": False,
    "bounded": True,
}

# FR-041: the four versioned refresh triggers.
REFRESH_TRIGGERS = (
    "client_change",
    "catalog_change",
    "alias_repoint",
    "source_ledger_change",
)

# FR-041: every trigger invalidates freeze admission, every unexecuted derived
# binding, and the affected experiment/score/decision bundles. Immutable traces,
# treatment records, and already-bound pairs survive.
_TRIGGER_INVALIDATES = (
    "freeze_admission",
    "unexecuted_bindings",
    "experiment_bundles",
    "score_bundles",
    "decision_bundles",
)
_TRIGGER_SURVIVES = ("execution_traces", "treatment_records", "bound_pairs")

INVALIDATION_TRIGGERS = tuple(
    {
        "trigger": trigger,
        "invalidates": [
            *_TRIGGER_INVALIDATES,
            *(["in_flight_attempts_for_alias"] if trigger == "alias_repoint" else []),
        ],
        "survives": list(_TRIGGER_SURVIVES),
    }
    for trigger in REFRESH_TRIGGERS
)

TRUSTED_COLLECTION_AUTHORITY = "operator_pinned_client"

# FR-028: a collection older than this is stale. The spec closes the failure
# member but not the window; 24 hours is this module's declared choice and is
# recorded on every publication attempt.
COLLECTION_MAX_AGE_HOURS = 24

# FR-002, FR-028: the mandatory provenance a collection record must carry. A
# record missing any of these is structurally ill-formed and records
# ``malformed_catalog`` — never ``untrusted_collection``, which stays reserved
# for a collection whose authority is in doubt.
REQUIRED_COLLECTION_FIELDS = (
    "schema_version",
    "record_kind",
    "collection_id",
    "collection_digest",
    "admitting_surface",
    "command_contract",
    "collection_method",
    "collection_authority",
    "client_version",
    "client_distribution",
    "account_boundary",
    "environment_boundary",
    "authentication_mode",
    "raw_catalog_digest",
    "parsed_catalog_digest",
    "observed_models",
    "alias_bindings",
    "visible_defaults",
    "supported_efforts",
    "effort_search_origin",
    "effort_admission",
    "collected_at_utc",
    "invalidation_criteria",
    "sanitization_status",
    "retention_status",
)


class SuccessorFreezeError(AssertionError):
    """Fail-closed error for a refused record, reason, or trigger."""


def canonical_json(record: Any) -> str:
    """Canonical JSON serialization: sorted keys, minimal separators, no NaN."""
    return json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def record_digest(record: Mapping[str, Any], *, digest_field: str | None = None) -> str:
    """``sha256:<64 hex>`` over the canonical JSON, excluding the digest field."""
    payload = {key: value for key, value in record.items() if key != digest_field}
    return "sha256:" + hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def build_collection_record(**fields: Any) -> dict[str, Any]:
    """Assemble a runtime catalog collection record and seal its digest.

    The effort-admission claim is stamped from the module constant rather than
    accepted from the caller: a record claiming verified effort support is
    refused outright, because the admitting surface can only establish that the
    pinned client did not reject the configuration (FR-002).
    """
    claim = fields.pop("effort_admission", None)
    if claim is not None and dict(claim) != EFFORT_ADMISSION_CLAIM:
        raise SuccessorFreezeError(
            "effort admission is bounded by configuration acceptance on the "
            f"admitting surface; refusing to record {claim!r} as verified support"
        )
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_kind": "runtime_catalog_collection",
        "admitting_surface": ADMITTING_SURFACE,
        "effort_admission": dict(EFFORT_ADMISSION_CLAIM),
    }
    record.update(fields)
    record["collection_digest"] = record_digest(record, digest_field="collection_digest")
    return record


def missing_provenance(record: Mapping[str, Any]) -> tuple[str, ...]:
    """Name every mandatory provenance field that is absent or null (FR-028)."""
    return tuple(field for field in REQUIRED_COLLECTION_FIELDS if record.get(field) is None)


# ---------------------------------------------------------------------------
# Closed exclusion taxonomy (FR-029, SC-003)
# ---------------------------------------------------------------------------

EXCLUSION_REASONS = (
    "source_not_admitted",
    "effort_not_source_admitted",
    "effort_source_not_admitted",
    "canonical_effort_unknown",
    "surface_evidence_incomplete",
    "surface_disagreement",
    "alias_repoint_unresolved",
    "availability_not_proven",
    "topology_control_not_candidate_effort",
)


@dataclass(frozen=True)
class ExcludedTuple:
    """One excluded model/effort tuple carrying a machine-checkable reason.

    The reason is validated against the closed taxonomy at construction, so a
    unilaterally coined member fails here rather than reaching a published
    freeze where it would widen a cross-platform enum by accident.
    """

    model: str
    effort: str
    reason: str

    def __post_init__(self) -> None:
        if self.reason not in EXCLUSION_REASONS:
            raise SuccessorFreezeError(
                f"{self.reason!r} is not a member of the closed exclusion taxonomy "
                f"{EXCLUSION_REASONS!r}"
            )

    def as_record(self) -> dict[str, str]:
        return {"model": self.model, "effort": self.effort, "reason": self.reason}


# ---------------------------------------------------------------------------
# Effort canonicalization (FR-003, FR-005, FR-040)
# ---------------------------------------------------------------------------

# FR-003: the closed ordered Claude ladder.
EFFORT_LADDER = ("low", "medium", "high", "xhigh", "max")

# FR-040: the documented origin of the within-model effort boundary search.
EFFORT_SEARCH_ORIGIN = "high"

# FR-003: the explicit evidence-backed normalization map. Every source value
# without an entry here records ``canonical_effort_unknown`` — omitted,
# ``inherit``, runtime-only, API-only, alias, and aggregate values all fall
# through by construction rather than by a hand-maintained denylist.
EFFORT_NORMALIZATION_MAP = {value: value for value in EFFORT_LADDER}

# FR-005: fast mode and any orchestration-topology-changing mode is a CAR-004
# policy-level control, never an ordinary per-agent effort candidate.
TOPOLOGY_CONTROL_EFFORTS = frozenset({"fast", "fast_mode", "fastmode"})


def normalization_map_digest() -> str:
    """Digest of the evidence-backed normalization map carried on the freeze."""
    return record_digest(EFFORT_NORMALIZATION_MAP)


def canonical_effort(value: Any) -> tuple[str | None, str | None]:
    """Map a source effort onto the ladder, or name why it cannot be mapped."""
    normalized = "" if value is None else str(value).strip().casefold()
    if normalized in TOPOLOGY_CONTROL_EFFORTS:
        return None, "topology_control_not_candidate_effort"
    canonical = EFFORT_NORMALIZATION_MAP.get(normalized)
    if canonical is None:
        return None, "canonical_effort_unknown"
    return canonical, None


def classify_surface(surface: str) -> str:
    """``admitting`` for the print-mode canary probe, ``diagnostic`` otherwise."""
    if surface == ADMITTING_SURFACE:
        return "admitting"
    if surface in DIAGNOSTIC_SURFACES:
        return "diagnostic"
    raise SuccessorFreezeError(
        f"{surface!r} is neither the admitting surface nor a declared diagnostic surface"
    )


def observation_admits(observation: Mapping[str, Any]) -> bool:
    """True only for an observation that names the sole admitting surface.

    An unlabeled observation is refused rather than classified: with no declared
    surface it can neither admit a tuple nor corroborate one, so it leaves the
    ladder rung it covers unprobed instead of standing in for a canary probe.
    """
    surface = observation.get("surface")
    if surface is None:
        surface = UNLABELED_SURFACE
    if surface == UNLABELED_SURFACE:
        return False
    return classify_surface(surface) == "admitting"


def ladder_coverage(
    collection: Mapping[str, Any], models: Sequence[str]
) -> dict[str, dict[str, Any]]:
    """Report admitting-surface ladder coverage per role-eligible model (FR-040)."""
    supported = collection.get("supported_efforts") or {}
    origin = collection.get("effort_search_origin", EFFORT_SEARCH_ORIGIN)
    coverage: dict[str, dict[str, Any]] = {}
    for model in models:
        probed = {
            observation.get("effort")
            for observation in supported.get(model, ())
            if observation_admits(observation)
        }
        coverage[model] = {
            "probed": [effort for effort in EFFORT_LADDER if effort in probed],
            "unprobed": [effort for effort in EFFORT_LADDER if effort not in probed],
            "search_origin": origin,
        }
    return coverage


# ---------------------------------------------------------------------------
# Set-intersection admission (FR-003, FR-004)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdmissionResult:
    """Outcome of intersecting the source ledger with the pinned runtime."""

    admitted: tuple[dict[str, str], ...]
    excluded: tuple[ExcludedTuple, ...]
    investigations: tuple[dict[str, str], ...]
    corroborated: frozenset[tuple[str, str]]


def _canonicalize_ledger(
    source_ledger: Mapping[str, Any],
) -> tuple[dict[str, set[str]], list[ExcludedTuple]]:
    admitted: dict[str, set[str]] = {}
    excluded: list[ExcludedTuple] = []
    for candidate in source_ledger.get("candidates") or ():
        model = candidate["model"]
        bucket = admitted.setdefault(model, set())
        for raw in candidate.get("efforts") or ():
            canonical, reason = canonical_effort(raw)
            if canonical is None:
                excluded.append(ExcludedTuple(model=model, effort=str(raw), reason=reason))
                continue
            bucket.add(canonical)
    return admitted, excluded


def _runtime_observations(
    collection: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Mapping[str, Any]]], dict[str, set[str]]]:
    """Split the catalog into admitting-surface acceptances and everything seen."""
    accepted: dict[str, dict[str, Mapping[str, Any]]] = {}
    observed: dict[str, set[str]] = {}
    for model, observations in (collection.get("supported_efforts") or {}).items():
        model_accepted: dict[str, Mapping[str, Any]] = {}
        model_observed: set[str] = set()
        for observation in observations:
            effort = observation.get("effort")
            model_observed.add(effort)
            if not observation_admits(observation):
                continue
            # The last admitting-surface observation for a rung decides it: a
            # re-probe that rejects an effort supersedes an earlier acceptance.
            if observation.get("acceptance") == "accepted":
                model_accepted[effort] = observation
            else:
                model_accepted.pop(effort, None)
        accepted[model] = model_accepted
        observed[model] = model_observed
    return accepted, observed


def _admitting_surface_efforts(collection: Mapping[str, Any], model: str) -> set[str]:
    return {
        observation.get("effort")
        for observation in (collection.get("supported_efforts") or {}).get(model, ())
        if observation_admits(observation)
    }


def admit_tuples(
    *,
    source_ledger: Mapping[str, Any],
    collection: Mapping[str, Any],
    diagnostics: Sequence[Mapping[str, Any]] = (),
    alias_findings: Sequence[Any] = (),
) -> AdmissionResult:
    """Admit the source/runtime intersection and name every exclusion.

    Diagnostic observations never enter the runtime side of the intersection.
    They corroborate an admitted tuple, or — on disagreement with the admitting
    probe — force a recorded investigation and exclude the tuple. Neither
    outcome is ever "logged and ignored" (FR-004).
    """
    source, excluded_list = _canonicalize_ledger(source_ledger)
    accepted, observed = _runtime_observations(collection)
    observed_models = set(collection.get("observed_models") or ())

    # FR-004: a disagreement between the admitting probe and a diagnostic
    # observation is resolved before admission, never after.
    investigations: list[dict[str, str]] = []
    disputed: set[tuple[str, str]] = set()
    corroborated: set[tuple[str, str]] = set()
    for observation in diagnostics:
        model = observation["model"]
        effort = observation["effort"]
        surface = observation["surface"]
        if classify_surface(surface) != "diagnostic":
            raise SuccessorFreezeError(
                f"{surface!r} is the admitting surface and cannot be supplied as a diagnostic"
            )
        admitting_acceptance = "accepted" if effort in accepted.get(model, {}) else "not_accepted"
        if observation.get("acceptance") == admitting_acceptance:
            corroborated.add((model, effort))
            continue
        disputed.add((model, effort))
        investigations.append(
            {
                "model": model,
                "effort": effort,
                "admitting_surface": ADMITTING_SURFACE,
                "admitting_acceptance": admitting_acceptance,
                "diagnostic_surface": surface,
                "diagnostic_acceptance": observation.get("acceptance"),
                "disposition": "excluded_pending_investigation",
            }
        )

    # FR-039: an unresolved alias re-point blocks admission for that alias.
    unresolved_aliases = {
        finding.record["requested_alias"] for finding in alias_findings if not finding.admits
    }

    archived = archived_snapshot_evidence_digests()
    collection_digests = collection_evidence_digests(collection)
    admitted: list[dict[str, str]] = []
    ledger_id = source_ledger.get("ledger_id")

    # A model the runtime observed but the ledger never listed can never be
    # admitted: runtime discovery constrains candidates, it never adds them.
    for model in sorted(observed_models - set(source)):
        for effort in sorted(observed.get(model, set())):
            excluded_list.append(
                ExcludedTuple(model=model, effort=effort, reason="source_not_admitted")
            )

    for model in sorted(source):
        probed = _admitting_surface_efforts(collection, model)
        for effort in EFFORT_LADDER:
            if effort not in source[model]:
                if effort in accepted.get(model, {}):
                    excluded_list.append(
                        ExcludedTuple(
                            model=model, effort=effort, reason="effort_not_source_admitted"
                        )
                    )
                continue
            if model not in observed_models or effort not in probed:
                # Absent from the catalog entirely is a runtime non-support;
                # a gap inside an observed model's ladder is an evidence gap.
                reason = (
                    "effort_source_not_admitted"
                    if model not in observed_models
                    else "surface_evidence_incomplete"
                )
                excluded_list.append(ExcludedTuple(model=model, effort=effort, reason=reason))
                continue
            observation = accepted.get(model, {}).get(effort)
            if observation is None:
                excluded_list.append(
                    ExcludedTuple(model=model, effort=effort, reason="effort_source_not_admitted")
                )
                continue
            if (model, effort) in disputed:
                excluded_list.append(
                    ExcludedTuple(model=model, effort=effort, reason="surface_disagreement")
                )
                continue
            if model in unresolved_aliases:
                excluded_list.append(
                    ExcludedTuple(model=model, effort=effort, reason="alias_repoint_unresolved")
                )
                continue
            runtime_digest = observation.get("evidence_digest")
            # FR-044: non-reuse is checked, not asserted. Evidence that resolves
            # to the archived snapshot — or to no record this collection owns —
            # cannot prove the pinned runtime still supports the tuple.
            if runtime_digest in archived or runtime_digest not in collection_digests:
                excluded_list.append(
                    ExcludedTuple(model=model, effort=effort, reason="availability_not_proven")
                )
                continue
            admitted.append(
                {
                    "candidate_route_id": f"{model}__{effort}",
                    "model": model,
                    "effort": effort,
                    "source_evidence_digest": record_digest(
                        {"ledger_id": ledger_id, "model": model, "effort": effort}
                    ),
                    "runtime_evidence_digest": runtime_digest,
                }
            )

    return AdmissionResult(
        admitted=tuple(admitted),
        excluded=tuple(excluded_list),
        investigations=tuple(investigations),
        corroborated=frozenset(corroborated),
    )


def collection_evidence_digests(collection: Mapping[str, Any]) -> frozenset[str]:
    """Every runtime evidence digest this collection record actually owns."""
    return frozenset(
        observation.get("evidence_digest")
        for observations in (collection.get("supported_efforts") or {}).values()
        for observation in observations
        if observation.get("evidence_digest")
    )


def archived_snapshot_evidence_digests() -> frozenset[str]:
    """Digests of the archived CAR-002 tuple evidence, for the non-reuse check."""
    snapshot = json.loads(ARCHIVED_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    return frozenset(record_digest(entry) for entry in snapshot.get("tuple_evidence", ()))


def resolves_to_archived_snapshot(digest: str) -> bool:
    """True when a runtime evidence digest names archived CAR-002 evidence."""
    return digest in archived_snapshot_evidence_digests()


# ---------------------------------------------------------------------------
# CAR-002 immutability and deny-by-default evidence inspection (FR-001, FR-027)
# ---------------------------------------------------------------------------


def car002_artifact_digests() -> dict[str, str]:
    """Current digest of every archived CAR-002 artifact.

    Hashes raw bytes. ``read_text`` opens in universal-newline mode, which
    rewrites ``\\r\\n`` to ``\\n`` before the bytes are ever hashed — so a
    line-ending mutation of an archived artifact would produce an identical
    digest and pass the immutability check unnoticed. An immutability proof
    that cannot see a byte change is not a proof.
    """
    return {
        path: "sha256:" + hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
        for path in CAR002_ARTIFACTS
    }


def car002_immutability_report(baseline: Mapping[str, str]) -> dict[str, list[str]]:
    """Compare the archived CAR-002 set against a baseline. Reports, never repairs."""
    current = car002_artifact_digests()
    return {
        "unchanged": [path for path in CAR002_ARTIFACTS if baseline.get(path) == current[path]],
        "mutated": [path for path in CAR002_ARTIFACTS if baseline.get(path) != current[path]],
    }


# FR-027, FR-036: deny by default. Only these top-level fields may appear on a
# committed collection record; anything else blocks publication rather than
# being silently stripped.
COLLECTION_FIELD_ALLOWLIST = frozenset(REQUIRED_COLLECTION_FIELDS) | {
    "authority_failures",
    "publication_state",
    "publication_record_digest",
    "sensitive_field_findings",
    "promoted_tuples",
    "collection_max_age_hours",
}

# Field names that carry operator-only content at any depth.
SENSITIVE_FIELD_NAMES = frozenset(
    {
        "access_token",
        "account_email",
        "account_id",
        "api_key",
        "auth_token",
        "authorization",
        "bearer_token",
        "billing_id",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "headers",
        "hostname",
        "organization_id",
        "plan_id",
        "private_host",
        "prompt",
        "raw_output",
        "raw_response",
        "repository_remote",
        "response",
        "session_id",
        "subscription_id",
        "transcript",
    }
)

_ABSOLUTE_PATH_RE = re.compile(r"/(?:Users|home)/[^\s\"']+")
_SESSION_UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE
)


def _sensitive_value(value: Any) -> bool:
    return isinstance(value, str) and bool(
        _ABSOLUTE_PATH_RE.search(value) or _SESSION_UUID_RE.search(value)
    )


def _walk_for_sensitive(node: Any, path: str, findings: list[str]) -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            child = f"{path}.{key}" if path else str(key)
            if str(key).casefold() in SENSITIVE_FIELD_NAMES:
                findings.append(child)
            _walk_for_sensitive(value, child, findings)
    elif isinstance(node, (list, tuple)):
        for index, value in enumerate(node):
            _walk_for_sensitive(value, f"{path}[{index}]", findings)
    elif _sensitive_value(node):
        findings.append(path)


def inspect_sensitive_fields(record: Mapping[str, Any]) -> tuple[str, ...]:
    """Name every non-allowlisted or operator-only field on a record (FR-027).

    Deny by default: an unknown top-level field is a finding on its own, and the
    nested walk catches an allowlisted field whose *value* leaks an absolute
    home path or a session identifier.
    """
    findings: list[str] = [key for key in record if key not in COLLECTION_FIELD_ALLOWLIST]
    _walk_for_sensitive(record, "", findings)
    ordered: list[str] = []
    for finding in findings:
        if finding and finding not in ordered:
            ordered.append(finding)
    return tuple(ordered)


# ---------------------------------------------------------------------------
# Fail-closed publication gate (FR-028, FR-044, SC-016)
# ---------------------------------------------------------------------------

AUTHORITY_FAILURES = (
    "empty_intersection",
    "malformed_source",
    "malformed_catalog",
    "stale_collection",
    "untrusted_collection",
    "sanitization_failed",
    "retention_failed",
    "identity_mismatch",
    "digest_mismatch",
    "historical_mutation",
)


@dataclass(frozen=True)
class FreezePublication:
    """Either an authoritative freeze, or diagnostic collection evidence only."""

    freeze: dict[str, Any] | None
    collection_record: dict[str, Any]
    authority_failures: tuple[str, ...]
    admission: AdmissionResult

    @property
    def published(self) -> bool:
        return self.freeze is not None


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _collection_is_stale(
    collection: Mapping[str, Any], pinned_client_version: str, published_at: str
) -> bool:
    if collection.get("client_version") != pinned_client_version:
        return True
    collected = _parse_timestamp(collection.get("collected_at_utc"))
    published = _parse_timestamp(published_at)
    if collected is None or published is None:
        return True
    if collected > published:
        return True
    return published - collected > timedelta(hours=COLLECTION_MAX_AGE_HOURS)


def _historical_freeze_binding() -> dict[str, str]:
    """Provenance reference proving the predecessor was read unmutated.

    FR-044: this is never a source of admitted tuples.
    """
    snapshot = json.loads(ARCHIVED_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    return {
        "id": snapshot["runtime_capability_snapshot_id"],
        "digest": car002_artifact_digests()[
            "docs/ai/research/claude-runtime-capability-snapshot.json"
        ],
    }


def publish_freeze(
    *,
    source_ledger: Mapping[str, Any],
    collection: Mapping[str, Any],
    freeze_id: str,
    published_at: str,
    pinned_client_version: str,
    runtime_snapshot_binding: Mapping[str, str] | None = None,
    historical_freeze_binding: Mapping[str, str] | None = None,
    car002_baseline: Mapping[str, str] | None = None,
    diagnostics: Sequence[Mapping[str, Any]] = (),
    alias_findings: Sequence[Any] = (),
) -> FreezePublication:
    """Publish an authoritative successor freeze, or fail closed with a reason.

    When any authority failure holds, **no freeze record is emitted at all**:
    the diagnostic evidence is the collection record carrying those failures, so
    the existence of a freeze record is itself the authoritative-publication
    signal (FR-044).
    """
    failures: list[str] = []

    candidates = (
        source_ledger.get("candidates") if isinstance(source_ledger, Mapping) else None
    )
    if not isinstance(candidates, list) or not candidates:
        failures.append("malformed_source")

    if missing_provenance(collection):
        failures.append("malformed_catalog")

    if _collection_is_stale(collection, pinned_client_version, published_at):
        failures.append("stale_collection")

    if collection.get("collection_authority") != TRUSTED_COLLECTION_AUTHORITY:
        failures.append("untrusted_collection")

    sensitive = inspect_sensitive_fields(collection)
    if collection.get("sanitization_status") != "passed" or sensitive:
        failures.append("sanitization_failed")

    if collection.get("retention_status") != "passed":
        failures.append("retention_failed")

    declared_binding = {
        "id": collection.get("collection_id"),
        "digest": collection.get("collection_digest"),
    }
    if runtime_snapshot_binding is not None and dict(runtime_snapshot_binding) != declared_binding:
        failures.append("identity_mismatch")

    if collection.get("collection_digest") != record_digest(
        collection, digest_field="collection_digest"
    ):
        failures.append("digest_mismatch")

    if car002_baseline is not None and car002_immutability_report(car002_baseline)["mutated"]:
        failures.append("historical_mutation")

    admission = admit_tuples(
        source_ledger=source_ledger if isinstance(source_ledger, Mapping) else {},
        collection=collection,
        diagnostics=diagnostics,
        alias_findings=alias_findings,
    )
    if not admission.admitted:
        failures.append("empty_intersection")

    ordered_failures = tuple(member for member in AUTHORITY_FAILURES if member in failures)

    record = dict(collection)
    record["sensitive_field_findings"] = sensitive
    record["authority_failures"] = list(ordered_failures)
    record["collection_max_age_hours"] = COLLECTION_MAX_AGE_HOURS
    # FR-044: the archived predecessor tuples are never promoted to an active
    # candidate set, whatever the outcome.
    record["promoted_tuples"] = []
    record["publication_state"] = "diagnostic_only" if ordered_failures else "published"
    # FR-033: the publication annotations above are added after the collection
    # sealed its own identity digest, so they carry a digest of their own.
    # ``collection_digest`` stays the collection's identity — it is what the
    # freeze binds — while ``publication_record_digest`` makes the emitted
    # diagnostic record verifiable at replay instead of only re-derivable.
    record["publication_record_digest"] = record_digest(
        record, digest_field="publication_record_digest"
    )

    if ordered_failures:
        return FreezePublication(
            freeze=None,
            collection_record=record,
            authority_failures=ordered_failures,
            admission=admission,
        )

    freeze: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "candidate_freeze_id": record_digest(
            {
                "freeze_id": freeze_id,
                "runtime_snapshot": collection["collection_digest"],
                "source_ledger": source_ledger.get("ledger_digest"),
            }
        ),
        "freeze_digest": "",
        "historical_freeze_binding": dict(historical_freeze_binding)
        if historical_freeze_binding is not None
        else _historical_freeze_binding(),
        "source_ledger_binding": {
            "id": source_ledger.get("ledger_id"),
            "digest": source_ledger.get("ledger_digest"),
        },
        "runtime_snapshot_binding": dict(declared_binding),
        "normalization_map_digest": normalization_map_digest(),
        "admitting_surface": ADMITTING_SURFACE,
        "authentication_mode": collection["authentication_mode"],
        "admitted_tuples": [dict(tuple_) for tuple_ in admission.admitted],
        "excluded_tuples": [item.as_record() for item in admission.excluded],
        "authority_failures": [],
        "published_at": published_at,
        # Deep-copied: ``dict(entry)`` would hand the emitted freeze the module
        # constant's own ``invalidates`` and ``survives`` list objects, so one
        # caller editing a published record would rewrite the declaration every
        # later freeze is built from.
        "invalidation_triggers": copy.deepcopy(list(INVALIDATION_TRIGGERS)),
    }
    freeze["freeze_digest"] = record_digest(freeze, digest_field="freeze_digest")
    return FreezePublication(
        freeze=freeze,
        collection_record=record,
        authority_failures=(),
        admission=admission,
    )


# ---------------------------------------------------------------------------
# Alias re-point detection (FR-039, FR-045, FR-046 — closes CAP-Q6)
# ---------------------------------------------------------------------------

# FR-039: the five observables detection must read.
ALIAS_REPOINT_OBSERVABLES = (
    "requested_alias",
    "freeze_bound_identity",
    "run_observed_identity",
    "env_override_proof",
    "client_version",
)

FREEZE_BOUND_IDENTITY_SOURCE = "car_003_successor_freeze"


def _env_override_proof_members() -> tuple[str, ...]:
    """The eight-member proof, reused from the frozen CAR-002 contract.

    FR-039 forbids re-coining this enumeration: without the frozen list,
    "every local override is proven unset" names no closed override surface and
    its completeness is unfalsifiable.
    """
    contract = json.loads(TRACE_CONTRACT_PATH.read_text(encoding="utf-8"))
    return tuple(contract["$defs"]["unsetProof"]["required"])


ENV_OVERRIDE_PROOF_MEMBERS = _env_override_proof_members()

# The four members whose truth is what "proven unset" actually asserts. The
# remaining four are observation fields, not unset assertions.
OVERRIDE_UNSET_BOOLEANS = (
    "fallback_model_unset",
    "fallbackModel_unset",
    "claude_code_subagent_model_unset",
    "available_models_absent",
)


@dataclass(frozen=True)
class AliasRepointFinding:
    """A bounded attribution for one requested alias."""

    record: dict[str, Any]
    attribution: str
    admits: bool
    exclusion_reason: str | None
    behavioral_only: bool


def detect_alias_repoint(
    observation: Mapping[str, Any],
    *,
    published_freeze_binding: Mapping[str, str] | None = None,
) -> AliasRepointFinding:
    """Attribute an observed-identity divergence for a requested alias.

    The identity the run is compared against is read from **CAR-003's own
    successor freeze**, never from the identically named run-time
    route-resolution field and never from the archived CAR-002 snapshot. The
    ``candidate_freeze_binding`` makes that provenance verifiable at replay
    instead of self-declared, so ``published_freeze_binding`` is required
    evidence: with nothing to compare the binding against, "verifiable at
    replay" degrades to the observation's own word for it, and an observation
    carrying no binding at all would attribute a divergence on no provenance.
    An absent published binding is therefore ``alias_repoint_unresolved``.

    Attribution is bounded by its enumerated cause set rather than proven:
    documented serving-infrastructure changes can alter observable behavior with
    the model identity and weights unchanged (FR-045).
    """
    binding = dict(observation.get("candidate_freeze_binding") or {})
    archived_id = json.loads(ARCHIVED_SNAPSHOT_PATH.read_text(encoding="utf-8"))[
        "runtime_capability_snapshot_id"
    ]
    binding_ok = (
        bool(binding)
        and observation.get("freeze_bound_identity_source") == FREEZE_BOUND_IDENTITY_SOURCE
        and binding.get("id") != archived_id
        and published_freeze_binding is not None
        and binding == dict(published_freeze_binding)
    )

    proof = dict(observation.get("env_override_proof") or {})
    proof_complete = all(member in proof for member in ENV_OVERRIDE_PROOF_MEMBERS)
    overrides_unset = all(proof.get(member) is True for member in OVERRIDE_UNSET_BOOLEANS)
    client_unchanged = observation.get("client_version_at_freeze") == observation.get(
        "client_version_at_run"
    )
    divergent = observation.get("run_observed_identity") != observation.get(
        "freeze_bound_identity"
    )
    behavioral_only = not divergent and bool(observation.get("behavioral_divergence_observed"))

    if not binding_ok:
        attribution = "alias_repoint_unresolved"
    elif not divergent:
        attribution = "no_divergence"
    elif not proof_complete or not overrides_unset:
        attribution = "alias_repoint_unresolved"
    elif not client_unchanged:
        attribution = "alias_repoint_unresolved"
    elif observation.get("plugin_initiated_substitution"):
        attribution = "resolver_fallback"
    elif observation.get("requested_route_unchanged"):
        attribution = "platform_route_change"
    else:
        attribution = "alias_repoint_unresolved"

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_kind": "alias_repoint_attribution",
        "attribution_id": observation["attribution_id"],
        "attribution_digest": "",
        "execution_trace_binding": dict(observation["execution_trace_binding"]),
        "candidate_freeze_binding": binding,
        "requested_alias": observation["requested_alias"],
        "freeze_bound_identity": observation["freeze_bound_identity"],
        # The const the contract declares. A declared source other than the
        # CAR-003 freeze is not echoed here — it is refused as
        # alias_repoint_unresolved above, which is the machine-checkable signal.
        "freeze_bound_identity_source": FREEZE_BOUND_IDENTITY_SOURCE,
        "run_observed_identity": observation["run_observed_identity"],
        "override_proof_complete": proof_complete,
        "client_version_at_freeze": observation["client_version_at_freeze"],
        "client_version_at_run": observation["client_version_at_run"],
        "attribution": attribution,
        "attribution_bounded": True,
        "behavioral_only_divergence": behavioral_only,
        "validated_by": observation.get("validated_by", "unvalidated_in_band"),
        "recorded_at": observation["recorded_at"],
    }
    record["attribution_digest"] = record_digest(record, digest_field="attribution_digest")

    # A CONFIRMED re-point must block admission just as firmly as an
    # unattributable one. Admitting only on "not unresolved" inverts the rule:
    # the strongest possible evidence that the alias moved — an observed
    # identity differing from the freeze-bound identity, with a complete
    # override proof and an unchanged client — would be admitted, while merely
    # unproven evidence would be excluded. A tuple whose alias no longer serves
    # the bound identity is not a candidate for that identity (FR-039).
    #
    # `behavioral_only` is the one divergence that does NOT block: it is a
    # documented serving-infrastructure change with the identity unchanged,
    # which FR-045 records as bounded diagnostic context rather than a re-point.
    # Only an UNATTRIBUTABLE divergence blocks freeze admission, and that is
    # deliberate rather than fail-open. A confirmed re-point is handled on a
    # different plane: FR-039 makes it non-scorable for the requested *run*,
    # which the score-eligibility predicate enforces through
    # `non_scorable_rerouted` — it does not disqualify the alias from the
    # successor freeze. Blocking admission here would mean a re-pointed alias
    # could never be admitted at all, which defeats the purpose of publishing a
    # successor freeze: the freeze exists to record the new binding. An
    # unattributable divergence is different in kind — a binding that cannot be
    # attributed cannot be published on any evidence.
    admits = attribution != "alias_repoint_unresolved"
    exclusion_reason = None if admits else "alias_repoint_unresolved"
    return AliasRepointFinding(
        record=record,
        attribution=attribution,
        admits=admits,
        exclusion_reason=exclusion_reason,
        behavioral_only=behavioral_only,
    )


# ---------------------------------------------------------------------------
# Versioned refresh triggers (FR-041)
# ---------------------------------------------------------------------------


def refresh_trigger_effects(trigger: str) -> dict[str, Any]:
    """What one trigger invalidates and what survives it."""
    for entry in INVALIDATION_TRIGGERS:
        if entry["trigger"] == trigger:
            return {key: list(value) if isinstance(value, list) else value
                    for key, value in entry.items()}
    raise SuccessorFreezeError(
        f"{trigger!r} is not one of the four versioned refresh triggers {REFRESH_TRIGGERS!r}"
    )


def apply_refresh_trigger(
    trigger: str,
    evidence: Mapping[str, Any],
    *,
    repointed_alias: str | None = None,
) -> dict[str, Any]:
    """Apply one refresh trigger to an evidence graph, additively.

    Surviving records are **marked** invalidated, never rebound: an already-bound
    pair keeps its binding and gains an invalidation mark, so replay still sees
    what was actually executed.
    """
    effects = refresh_trigger_effects(trigger)
    survived = {name: list(evidence.get(name, ())) for name in _TRIGGER_SURVIVES}
    non_scorable: list[str] = []
    if trigger == "alias_repoint" and repointed_alias is not None:
        non_scorable = [
            attempt["attempt_id"]
            for attempt in evidence.get("in_flight_attempts", ())
            if attempt.get("requested_alias") == repointed_alias
        ]
    return {
        "trigger": trigger,
        "additive": True,
        "invalidated": {
            "freeze_admission": True,
            "unexecuted_bindings": list(evidence.get("unexecuted_bindings", ())),
            "experiment_bundles": list(evidence.get("experiment_bundles", ())),
            "score_bundles": list(evidence.get("score_bundles", ())),
            "decision_bundles": list(evidence.get("decision_bundles", ())),
        },
        "survived": survived,
        "marked_invalidated": sorted(
            identifier for names in survived.values() for identifier in names
        ),
        "rebound": [],
        "non_scorable_attempts": non_scorable,
        # FR-041: a source-ledger change alone never admits a tuple the pinned
        # runtime never supported — re-admission still runs the intersection.
        "admits_runtime_unsupported": False,
        "invalidates": effects["invalidates"],
        "survives": effects["survives"],
    }
