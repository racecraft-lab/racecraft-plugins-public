#!/usr/bin/env python3
"""CAR-003 exact-treatment runner: prove the treatment before scoring anything.

This module is repository-only harness code and makes **no live model calls**.
The live campaign is operator-only; everything here reads already-recorded
evidence — a session transcript, a per-model usage breakdown, an observed
environment, a trace record.

It is a **thin adapter**, not a second implementation. The one canonical
materializer lives in plugin source at
``speckit-pro/speckit_pro_runner/materializer.py``; this module imports and
calls it and deliberately defines no parsed-only or evaluation-side substitute
(FR-006).

Consumed unmodified: ``treatment_trace_io`` for the CAR-002 canonical JSON
serialization, ``treatment_trace_model`` for the trace identity and digest
helpers built on it, and ``treatment_trace_authority`` for the closed shared
taxonomies. No vocabulary is coined here that either the shared treatment-record
contract or the CAR-003 additive-records contract already publishes.

What the module proves, in the order an attempt is evaluated:

1. **Mandatory observations** (FR-009). Every field the versioned manifest names
   carries a non-null observed value and a classification other than
   ``unavailable``; anything else records ``mandatory_telemetry_missing``.
2. **What actually ran** (FR-009, SC-021). The named agent is the
   ``speckit-pro:<name>`` spawn read from the run transcript, never from the
   dispatch request that asked for it, and the effective model is read from the
   per-model usage breakdown, never inferred from configuration.
3. **Environment conformance** (FR-042, FR-051). Every attempt binds a versioned
   contract before execution; a confirmed divergence and an unobservable
   environment land on different planes with different closed codes.
4. **Disposition and eligibility** (FR-030, FR-031). Conditions are derived
   independently, every fired code is unioned into ``disposition_reasons``, and
   the terminal disposition is the highest-precedence bucket.
5. **Trace binding** (FR-010, FR-032). Every assigned attempt gets a new
   immutable trace; bundles reference it by ID and digest and re-derive their
   projections from it.
6. **Cache isolation** (FR-049). Each arm records the root it actually used as a
   digest, and a pair that cannot show distinct roots contributes nothing.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

if __package__:  # pragma: no cover - the lib is imported flat by the suite
    from .treatment_trace_model import digest, execution_trace_identity
    from . import treatment_trace_authority as shared_authority
else:
    from treatment_trace_model import digest, execution_trace_identity
    import treatment_trace_authority as shared_authority


REPO_ROOT = Path(__file__).resolve().parents[4]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from speckit_pro_runner import materializer  # noqa: E402

CONTRACT_ROOT = REPO_ROOT / "specs" / "car-003-evaluation-runner-scoring" / "contracts"
ADDITIVE_SCHEMA_PATH = CONTRACT_ROOT / "car-003-additive-records.schema.json"
SHARED_CONTRACT_PATH = shared_authority.SCHEMA_PATH
TRACE_CONTRACT_PATH = REPO_ROOT / "docs" / "ai" / "research" / "claude-trace-contract.schema.json"
MANDATORY_MANIFEST_PATH = (
    REPO_ROOT / "docs" / "ai" / "research" / "claude-car-003-mandatory-observation-manifest.json"
)

SCHEMA_VERSION = "1.0.0"
ENVIRONMENT_CONTRACT_VERSION = "1.0.0"


class TreatmentRunnerError(AssertionError):
    """An exact-treatment check failed closed."""


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


# ---------------------------------------------------------------------------
# T031 — the single shipped materializer, adapted, never re-implemented.
# ---------------------------------------------------------------------------

materialize_agent_definition = materializer.materialize
verify_materialization_proof = materializer.verify_content_hash_proof
verify_materialization_destination = materializer.verify_destination_path
materialization_proof_fields = materializer.treatment_record_fields
MaterializationError = materializer.MaterializationError


# ---------------------------------------------------------------------------
# Closed vocabularies. Every member below is read from a committed contract or
# reused verbatim from one; none is coined here.
# ---------------------------------------------------------------------------

TREATMENT_DISPOSITIONS: tuple[str, ...] = tuple(
    _load_json(SHARED_CONTRACT_PATH)["$defs"]["treatmentTrace"]["properties"]["treatment_disposition"]["enum"]
)
DISPOSITION_REASON_CODES: frozenset[str] = frozenset(shared_authority.DISPOSITION_REASON_CODES)

# FR-031: the shared disposition-bucket precedence, specified so independent
# Claude-side and Codex-side implementations classify identical evidence
# identically. There is no condition-level tie-break.
DISPOSITION_PRECEDENCE = ("hard_fail", "non_scorable_rerouted", "unknown", "proven")

# Codes whose bucket the shared contract fixes as ``unknown`` rather than
# ``hard_fail``; read from the shared treatment-failure disposition mapping.
_UNKNOWN_BUCKET_CODES = frozenset(
    code for code, bucket in shared_authority.FAILURE_DISPOSITIONS.items() if bucket == "unknown"
) | {"effective_treatment_or_reroute_evidence_missing"}

# FR-034: platform alias re-pointing reuses this shared member; no Claude-only
# code is coined for it.
_NON_SCORABLE_BUCKET_CODES = frozenset({"service_reroute_requested_route_non_scorable"})

# Reasons that support rather than disqualify a record. A proven record still
# carries a reason, because the shared array is non-empty by contract.
PROVEN_REASON = "configured_route_proof_and_complete_reroute_monitoring"
_PROVEN_BUCKET_CODES = frozenset({PROVEN_REASON, "profile_supported_effective_treatment"})

# Closed score-plane codes reused verbatim (FR-034). None is new.
MANDATORY_TELEMETRY_MISSING = "mandatory_telemetry_missing"
TREATMENT_INFRASTRUCTURE_FAILURE = "treatment_infrastructure_failure"
REQUIRED_EVIDENCE_MISSING = "required_evidence_missing"
INFRASTRUCTURE_FAILURE = "infrastructure_failure"
TRACE_REFERENCE_INTEGRITY_FAILURE = "trace_reference_integrity_failure"
BINDING_DIGEST_MISMATCH = "binding_digest_mismatch"

PLANE_NONE = "none"
PLANE_TREATMENT = "treatment"
PLANE_EVIDENCE_BOUNDARY = "evidence_boundary"
PLANE_INFRASTRUCTURE = "infrastructure"
PLANE_SCHEMA = "schema"

# The slice of the total FR-034 code-to-plane mapping this module can fire. The
# complete table lands with the score bundle; an unlisted code fails closed on
# the schema plane exactly as that requirement directs.
_FAILURE_PLANES = {
    "none": PLANE_NONE,
    MANDATORY_TELEMETRY_MISSING: PLANE_TREATMENT,
    TREATMENT_INFRASTRUCTURE_FAILURE: PLANE_TREATMENT,
    REQUIRED_EVIDENCE_MISSING: PLANE_EVIDENCE_BOUNDARY,
    INFRASTRUCTURE_FAILURE: PLANE_INFRASTRUCTURE,
    BINDING_DIGEST_MISMATCH: PLANE_SCHEMA,
}

TERMINAL_INCONCLUSIVE = "inconclusive"


def failure_plane_for(failure_code: str) -> str:
    """Derive the plane from the code; an unlisted code fails closed."""
    return _FAILURE_PLANES.get(failure_code, PLANE_SCHEMA)


# ---------------------------------------------------------------------------
# T033 — the mandatory-observation manifest and its completeness check (FR-009).
# ---------------------------------------------------------------------------

REQUIRED_EVIDENCE_CATEGORIES: tuple[str, ...] = tuple(
    _load_json(ADDITIVE_SCHEMA_PATH)["$defs"]["mandatoryObservationManifest"]["properties"][
        "required_fields"
    ]["items"]["properties"]["category"]["enum"]
)


@lru_cache(maxsize=4)
def _read_manifest(path: str) -> Mapping[str, Any]:
    manifest = _load_json(Path(path))
    recorded = manifest.get("manifest_digest")
    recomputed = digest(_canonical({key: value for key, value in manifest.items() if key != "manifest_digest"}))
    if recorded != recomputed:
        raise TreatmentRunnerError("mandatory-observation manifest digest does not match its own content")
    return MappingProxyType(manifest)


def load_mandatory_manifest(path: Path | None = None) -> Mapping[str, Any]:
    """Load the versioned manifest, verifying it still digests to its own record.

    Deep-copied on the way out. A ``MappingProxyType`` is read-only at its top
    level only, so handing out the cached record would let one caller edit the
    manifest — through ``required_fields`` or ``nullable_exemptions`` — that
    every later caller in the process then reads as authoritative.
    """
    cached = _read_manifest(str(path or MANDATORY_MANIFEST_PATH))
    return MappingProxyType(copy.deepcopy(dict(cached)))


def mandatory_field_paths(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    """The distinct field paths the manifest declares mandatory, in order."""
    seen: list[str] = []
    for entry in manifest["required_fields"]:
        if entry["field_path"] not in seen:
            seen.append(entry["field_path"])
    return tuple(seen)


def check_mandatory_observations(
    observations: Iterable[Mapping[str, Any]], *, manifest: Mapping[str, Any]
) -> tuple[str, ...]:
    """Fire ``mandatory_telemetry_missing`` unless every mandatory field is observed.

    A mandatory field must be present, carry ``observation_state=observed_value``
    with a non-null value, and carry a classification other than ``unavailable``.
    Fields the frozen schema declares nullable keep their explicit nulls only
    while they stay off this manifest.
    """
    observed = {entry["field_path"]: entry for entry in observations}
    for field_path in mandatory_field_paths(manifest):
        entry = observed.get(field_path)
        if entry is None:
            return (MANDATORY_TELEMETRY_MISSING,)
        if entry.get("observation_state") != "observed_value" or entry.get("value") is None:
            return (MANDATORY_TELEMETRY_MISSING,)
        if entry.get("classification") == "unavailable":
            return (MANDATORY_TELEMETRY_MISSING,)
    return ()


# ---------------------------------------------------------------------------
# T034 — read what ran, not what was requested (FR-009, SC-021).
# ---------------------------------------------------------------------------

DISPATCH_NAMESPACE_PREFIX = "speckit-pro:"
SOURCE_RUN_TRANSCRIPT = "run_transcript"
SOURCE_PER_MODEL_USAGE = "per_model_usage_breakdown"


def read_dispatch_namespace(transcript: Mapping[str, Any] | None) -> str | None:
    """The plugin-namespaced spawn the run actually performed.

    A request records what was intended, not what was delivered, so the value is
    read from the transcript alone. A spawn without the plugin namespace is not
    the named agent and yields ``None`` rather than a repaired guess.
    """
    for event in (transcript or {}).get("events", ()):
        if event.get("type") != "agent_spawn":
            continue
        agent = event.get("agent")
        if isinstance(agent, str) and agent.startswith(DISPATCH_NAMESPACE_PREFIX):
            return agent
    return None


def read_observed_model_id(usage_breakdown: Mapping[str, Any] | None) -> str | None:
    """The effective model, from the per-model usage breakdown alone.

    Configuration, the requested alias, and the resolved route are all excluded
    by construction: an effective model inferred from configuration cannot
    witness a divergence between what was configured and what ran. A breakdown
    naming several models cannot establish one effective model and fails closed.
    """
    models = tuple(usage_breakdown or ())
    return models[0] if len(models) == 1 else None


def record_exact_treatment(
    *,
    transcript: Mapping[str, Any] | None,
    usage_breakdown: Mapping[str, Any] | None,
    dispatch_request: Mapping[str, Any],
) -> dict[str, Any]:
    """The observed half of a treatment record, with its sources named."""
    return {
        "dispatch_namespace": read_dispatch_namespace(transcript),
        "dispatch_namespace_source": SOURCE_RUN_TRANSCRIPT,
        "observed_model_id": read_observed_model_id(usage_breakdown),
        "observed_model_id_source": SOURCE_PER_MODEL_USAGE,
        # Recorded as intent only. It is never read as evidence of delivery.
        "requested_agent": dispatch_request.get("agent"),
    }


# ---------------------------------------------------------------------------
# T035 — the versioned environment contract (FR-042, FR-051).
# ---------------------------------------------------------------------------

ENV_OVERRIDE_PROOF_MEMBERS: tuple[str, ...] = tuple(
    _load_json(TRACE_CONTRACT_PATH)["$defs"]["unsetProof"]["required"]
)

PERMITTED_CLIENT_VERSION_RANGE = ("2.1.196", "2.2.0")
PINNED_PARENT_SESSION = "opus/high"

ENVIRONMENT_CONFORMANT = "conformant"
ENVIRONMENT_DIVERGENT = "divergent"
ENVIRONMENT_UNOBSERVABLE = "unobservable"

# The proof members the contract constrains. The remaining three are recorded
# caveats, not pinned values, so comparing them would manufacture divergence.
_CONSTRAINED_OVERRIDE_MEMBERS = (
    "fallback_model_unset",
    "fallbackModel_unset",
    "claude_code_subagent_model_unset",
    "available_models_absent",
    "config_dir_isolation",
)

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)")


@dataclass(frozen=True)
class EnvironmentConformance:
    """One attempt's environment measured against the contract it bound."""

    status: str
    failure_plane: str
    failure_code: str
    blocks_scoring: bool
    terminal_member: str | None
    diverged_fields: tuple[str, ...]
    unobservable_fields: tuple[str, ...]


def bind_environment_contract(**overrides: Any) -> dict[str, Any]:
    """Bind the versioned contract an attempt must conform to, before execution.

    Every pinned value already exists on the frozen CAR-002 route-resolution and
    runtime-snapshot records; none is a parallel field.
    """
    contract: dict[str, Any] = {
        "schema_version": ENVIRONMENT_CONTRACT_VERSION,
        "fast_mode_state": "off",
        "client_version_range": PERMITTED_CLIENT_VERSION_RANGE,
        "parent_session_configuration": PINNED_PARENT_SESSION,
        "env_override_proof": {
            "fallback_model_unset": True,
            "fallbackModel_unset": True,
            "claude_code_subagent_model_unset": True,
            "available_models_absent": True,
            "enforce_available_models_observed": None,
            "config_dir_isolation": "none",
            "inherit_equivalent_to_unset": None,
            "org_restriction_gap": None,
        },
        "authentication_mode": "subscription",
    }
    contract.update(overrides)
    return contract


def _version_tuple(value: str) -> tuple[int, int, int] | None:
    match = _VERSION_RE.match(value)
    return (int(match.group(1)), int(match.group(2)), int(match.group(3))) if match else None


def _client_version_in_range(observed: str, bounds: Sequence[str]) -> bool | None:
    parsed = _version_tuple(observed)
    if parsed is None:
        return None
    low, high = (_version_tuple(bound) for bound in bounds)
    return low is not None and high is not None and low <= parsed < high


def check_environment_conformance(
    contract: Mapping[str, Any], observed: Mapping[str, Any]
) -> EnvironmentConformance:
    """Compare an observed environment against its bound contract.

    A **confirmed divergence** is a treatment-plane deviation. An **unobservable**
    environment is an evidence-completeness failure returning inconclusive: a
    condition with no evidence cannot be classified as having deviated, so the
    two never share a code. Unobservability wins when both would apply.
    """
    diverged: list[str] = []
    unobservable: list[str] = []

    for field in ("fast_mode_state", "parent_session_configuration", "authentication_mode"):
        value = observed.get(field)
        pinned = contract[field]
        if value is None or value == "unknown":
            unobservable.append(field)
        elif value != pinned:
            diverged.append(field)

    client_version = observed.get("client_version")
    if not isinstance(client_version, str):
        unobservable.append("client_version")
    else:
        in_range = _client_version_in_range(client_version, contract["client_version_range"])
        if in_range is None:
            unobservable.append("client_version")
        elif not in_range:
            diverged.append("client_version")

    proof = observed.get("env_override_proof")
    if not isinstance(proof, Mapping):
        unobservable.append("env_override_proof")
    else:
        for member in _CONSTRAINED_OVERRIDE_MEMBERS:
            if member not in proof or proof[member] is None:
                unobservable.append(f"env_override_proof.{member}")
            elif proof[member] != contract["env_override_proof"][member]:
                diverged.append(f"env_override_proof.{member}")

    if unobservable:
        return EnvironmentConformance(
            status=ENVIRONMENT_UNOBSERVABLE,
            failure_plane=PLANE_EVIDENCE_BOUNDARY,
            failure_code=REQUIRED_EVIDENCE_MISSING,
            blocks_scoring=True,
            terminal_member=TERMINAL_INCONCLUSIVE,
            diverged_fields=tuple(diverged),
            unobservable_fields=tuple(unobservable),
        )
    if diverged:
        return EnvironmentConformance(
            status=ENVIRONMENT_DIVERGENT,
            failure_plane=PLANE_TREATMENT,
            failure_code=TREATMENT_INFRASTRUCTURE_FAILURE,
            blocks_scoring=True,
            terminal_member=None,
            diverged_fields=tuple(diverged),
            unobservable_fields=(),
        )
    return EnvironmentConformance(
        status=ENVIRONMENT_CONFORMANT,
        failure_plane=PLANE_NONE,
        failure_code="none",
        blocks_scoring=False,
        terminal_member=None,
        diverged_fields=(),
        unobservable_fields=(),
    )


def environment_exclusion_report(
    conformances: Iterable[EnvironmentConformance],
) -> dict[str, Any]:
    """The exclusion count FR-051 requires beside every qualification claim."""
    evaluated = tuple(conformances)
    excluded_by_code: dict[str, int] = {}
    for result in evaluated:
        if result.blocks_scoring:
            excluded_by_code[result.failure_code] = excluded_by_code.get(result.failure_code, 0) + 1
    return {
        "attempts_evaluated": len(evaluated),
        "attempts_excluded": sum(excluded_by_code.values()),
        "excluded_by_code": excluded_by_code,
    }


# ---------------------------------------------------------------------------
# T036, T037 — disposition and score eligibility (FR-030, FR-031).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoreEligibility:
    """Whether a pre-score record may be scored, and why not when it may not."""

    eligible: bool
    treatment_disposition: str
    disposition_reasons: tuple[str, ...]
    blocking_reasons: tuple[str, ...]


def disposition_bucket(code: str) -> str:
    """The precedence bucket one condition code belongs to."""
    if code not in DISPOSITION_REASON_CODES:
        raise TreatmentRunnerError(f"{code!r} is not a member of the shared disposition-reason set")
    if code in _PROVEN_BUCKET_CODES:
        return "proven"
    if code in _NON_SCORABLE_BUCKET_CODES:
        return "non_scorable_rerouted"
    if code in _UNKNOWN_BUCKET_CODES:
        return "unknown"
    return "hard_fail"


def resolve_disposition(conditions: Iterable[str]) -> tuple[str, tuple[str, ...]]:
    """Union every fired code; select the highest-precedence bucket as terminal.

    Each condition is derived independently by the caller and every one of them
    is retained: no non-terminal cause is discarded, and there is no
    condition-level tie-break that suppresses one co-firing code in favour of
    another.
    """
    reasons: list[str] = []
    for code in conditions:
        if code not in reasons:
            reasons.append(code)
    buckets = {disposition_bucket(code) for code in reasons}
    for candidate in DISPOSITION_PRECEDENCE:
        if candidate in buckets:
            return candidate, tuple(reasons)
    return "proven", (PROVEN_REASON,)


def evaluate_score_eligibility(record: Mapping[str, Any]) -> ScoreEligibility:
    """The conjunctive score-eligibility predicate (FR-030).

    ``scorable`` is necessary but never sufficient: it is derived solely from the
    record class and speaks only to platform-initiated route change, so
    ``scorable=false`` forces ineligibility while ``scorable=true`` admits
    nothing on its own.
    """
    manifest = load_mandatory_manifest()
    disposition, reasons = resolve_disposition(record.get("conditions", ()))

    proof = record.get("materialization_proof")
    materialization_proved = bool(record.get("installed_policy_proof")) or bool(
        isinstance(proof, Mapping) and proof.get("verified")
    )

    blocking: list[str] = []
    if disposition != "proven":
        blocking.append("treatment_disposition")
    if not materialization_proved:
        blocking.append("materialization_proof")
    if not record.get("configured_route_proof_matches"):
        blocking.append("configured_route_proof")
    if check_mandatory_observations(record.get("observations", ()), manifest=manifest):
        blocking.append("mandatory_observations")
    if not record.get("route_change_monitoring_complete"):
        blocking.append("route_change_monitoring")
    if not record.get("environment_conformant"):
        blocking.append("environment_conformance")
    if not record.get("scorable"):
        blocking.append("scorable")

    return ScoreEligibility(
        eligible=not blocking,
        treatment_disposition=disposition,
        disposition_reasons=reasons,
        blocking_reasons=tuple(blocking),
    )


# ---------------------------------------------------------------------------
# T038 — immutable traces and foreign-key bundle references (FR-010, FR-032).
# ---------------------------------------------------------------------------

FROZEN_OUTCOME_KEYS = ("status", "telemetry_ref", "notes")


def new_execution_trace(
    bindings: Mapping[str, Any], *, assignment_id: str, assigned_at: str
) -> Mapping[str, Any]:
    """Create one new immutable trace for one assigned attempt.

    Every assigned attempt gets a trace regardless of score eligibility. Identity
    folds the assignment and its pre-execution timestamp into the CAR-002 content
    identity, so two attempts sharing every binding still receive distinct IDs.
    The frozen ``outcome`` shape is carried unextended; scores live in the
    separate score bundle.
    """
    trace = json.loads(json.dumps(bindings))
    trace["assignment_id"] = assignment_id
    trace["assigned_at"] = assigned_at
    trace["outcome"] = {"status": "completed", "telemetry_ref": None, "notes": None}
    trace["acceptance"] = None
    trace["execution_trace_id"] = digest(
        {
            "trace_identity": execution_trace_identity(trace),
            "assignment_id": assignment_id,
            "assigned_at": assigned_at,
        }
    )
    trace["objective_binding"] = dict(
        trace["objective_binding"], execution_trace_id=trace["execution_trace_id"]
    )
    return MappingProxyType(trace)


def trace_digest(trace: Mapping[str, Any]) -> str:
    """SHA-256 over the CAR-002 canonical JSON serialization of the whole trace."""
    return "sha256:" + hashlib.sha256(_canonical(dict(trace))).hexdigest()


def derive_resource_vector(trace: Mapping[str, Any]) -> dict[str, Any]:
    """The score bundle's resource vector, projected from the trace."""
    tokens = trace.get("raw_token_vector") or {}
    return {
        "input_tokens": tokens.get("input_tokens"),
        "cached_input_tokens": tokens.get("cached_input_tokens"),
        "output_tokens": tokens.get("output_tokens"),
        "wall_time_ms": trace.get("wall_time_ms"),
        "retries": trace.get("retries"),
    }


def derive_reasoning_token_report(trace: Mapping[str, Any]) -> dict[str, Any]:
    """Reasoning tokens, reported for every attempt and never decision-bearing."""
    tokens = trace.get("raw_token_vector") or {}
    return {
        "reasoning_output_tokens": tokens.get("reasoning_output_tokens"),
        "output_tokens": tokens.get("output_tokens"),
        "decision_bearing": False,
    }


def bind_score_bundle(trace: Mapping[str, Any]) -> dict[str, Any]:
    """Reference a trace by ID and digest; never embed or mutate it."""
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_trace_binding": {
            "id": trace["execution_trace_id"],
            "digest": trace_digest(trace),
        },
        "resource_vector": derive_resource_vector(trace),
        "reasoning_token_report": derive_reasoning_token_report(trace),
    }


def verify_bundle_references(
    bundle: Mapping[str, Any], traces: Iterable[Mapping[str, Any]]
) -> tuple[str, ...]:
    """Recompute the bound digest; a mismatch or dangling reference blocks."""
    binding = bundle["execution_trace_binding"]
    for trace in traces:
        if trace["execution_trace_id"] == binding["id"]:
            if trace_digest(trace) == binding["digest"]:
                return ()
            break
    return (TRACE_REFERENCE_INTEGRITY_FAILURE,)


def verify_bundle_projections(
    bundle: Mapping[str, Any], trace: Mapping[str, Any]
) -> tuple[str, ...]:
    """The digest-verified trace is the sole source of truth for both projections."""
    if bundle["resource_vector"] != derive_resource_vector(trace):
        return (BINDING_DIGEST_MISMATCH,)
    if bundle["reasoning_token_report"] != derive_reasoning_token_report(trace):
        return (BINDING_DIGEST_MISMATCH,)
    return ()


# ---------------------------------------------------------------------------
# T039 — observed per-arm cache isolation (FR-049).
# ---------------------------------------------------------------------------

CACHE_OBSERVED_DISJOINT = "observed_disjoint"
CACHE_OBSERVED_SHARED = "observed_shared"
CACHE_UNOBSERVED = "unobserved"


def cache_root_digest(root_label: str) -> str:
    """Digest a cache root. Roots are recorded as digests, never as paths."""
    return "sha256:" + hashlib.sha256(root_label.encode("utf-8")).hexdigest()


def _arm_isolation(own: str | None, paired: str | None) -> dict[str, Any]:
    own_digest = cache_root_digest(own) if own is not None else None
    paired_digest = cache_root_digest(paired) if paired is not None else None
    if own_digest is None or paired_digest is None:
        status, disjoint = CACHE_UNOBSERVED, None
    elif own_digest == paired_digest:
        status, disjoint = CACHE_OBSERVED_SHARED, False
    else:
        status, disjoint = CACHE_OBSERVED_DISJOINT, True
    return {
        "status": status,
        "arm_cache_root_digest": own_digest,
        "paired_arm_cache_root_digest": paired_digest,
        "roots_disjoint": disjoint,
    }


def observe_paired_cache_isolation(
    arm_a_root: str | None, arm_b_root: str | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Record what each arm actually used, not what the policy precommitted to."""
    return _arm_isolation(arm_a_root, arm_b_root), _arm_isolation(arm_b_root, arm_a_root)


def pair_contributes_resource_comparison(
    arm_a: Mapping[str, Any], arm_b: Mapping[str, Any]
) -> bool:
    """A pair that cannot be shown to have used distinct roots contributes nothing.

    ``cached_input_tokens`` is a decision-bearing dimension, so an unverified
    cache artifact would otherwise enter the dominance result directly as though
    it were a route property.
    """
    return all(
        arm["status"] == CACHE_OBSERVED_DISJOINT and arm["roots_disjoint"] is True
        for arm in (arm_a, arm_b)
    )
