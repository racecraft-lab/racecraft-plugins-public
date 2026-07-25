#!/usr/bin/env python3
"""CAR-003 score bundles: hard gates, blinded ballots, adjudication, taxonomies.

An outcome reaches a semantic scorer only after **all seven** deterministic hard
gates pass. The gate set is closed and there is no per-role subset; a missing
gate result fails closed rather than reading as a pass (FR-014).

Blinding is enforced **and bounded** (FR-035, FR-048). Each ballot binds exactly
one blinded-artifact digest as its sole scored input, and a mechanical leak check
runs first against freeze-bound model identities, aliases, effort values, agent
frontmatter, and route identifiers. Identifier stripping cannot remove stylistic
tells, so every ballot also records whether the scorer inferred provenance and
from what signal. The residual is reported; blinding is never called complete.

Same-family exclusion is static and declared in the frozen experiment policy, so
it carries no replay cost — but a freeze-time declaration cannot see a
**post-freeze** re-point of the scorer itself. Every scorer and adjudicator
therefore also records its run-observed identity in a Scorer Identity
Attestation, and ``family_exclusion_holds=false`` blocks bundle acceptance rather
than being recorded and ignored (FR-047).

Two design choices the requirements left open, both stated here so a reviewer can
see them rather than infer them:

* **Effort values are matched contextually, identity tokens are not.** ``low``,
  ``medium``, ``high``, ``xhigh``, and ``max`` are ordinary English; matching them
  as bare words would fail every artifact that mentions a high confidence or a max
  retry count, turning a blinding gate into noise. They leak only in a declaration
  context (``effort: xhigh``) or joined to an alias (``opus-high``). Model
  identities, aliases, and route identifiers are distinctive and are matched as
  whole tokens anywhere.
* **A missing gate and a duplicated gate are different failures.** An absent gate
  result is missing evidence, so it is filed on the evidence-boundary plane as
  ``(evidence_boundary, required_evidence_missing)`` — the row FR-034's total
  table already carries for that code. A duplicated gate name is a malformed
  record rather than an absent observation, so it is filed as
  ``(schema, schema_invalid)``. Both pairs are listed, so :func:`normalize_failure`
  passes them through unchanged and the sealed bundle records the same
  classification :func:`evaluate_gates` derived.

The digest helper is imported from ``claude_successor_freeze`` so one FR-033
preimage rule governs every CAR-003 digest. This module is
repository-only harness code and makes **no live model calls**: every score here
is a recorded fixture.
"""

from __future__ import annotations

import copy
import random
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

if __package__:  # pragma: no cover - the lib is imported flat by the suite
    from .claude_successor_freeze import record_digest
else:
    from claude_successor_freeze import record_digest


REPO_ROOT = Path(__file__).resolve().parents[4]
LAYER6_ROOT = REPO_ROOT / "tests" / "speckit-pro" / "layer6-efficiency"
SHARED_CONTRACT_DIR = LAYER6_ROOT / "contracts"

# Repo-level, byte-identical across the Claude and Codex worktrees. Read, never
# written: a unilateral edit is a cross-platform break.
SHARED_CONTRACT_PATHS = (
    SHARED_CONTRACT_DIR / "capability-freeze.schema.json",
    SHARED_CONTRACT_DIR / "marker-checkpoint.schema.json",
    SHARED_CONTRACT_DIR / "treatment-record.schema.json",
)

SCHEMA_VERSION = "1.0.0"


class ScoreBundleError(AssertionError):
    """Fail-closed error for a refused gate, ballot, adjudication, or bundle."""


# ---------------------------------------------------------------------------
# Deterministic hard gates (FR-014)
# ---------------------------------------------------------------------------

REQUIRED_GATES = ("role", "safety", "grounding", "mutation", "tool", "output", "acceptance")
GATE_RESULT_FIELDS = ("evidence_digest", "gate", "pass")

# FR-014, FR-034: an absent gate result is missing evidence, so it lands on the
# evidence-boundary plane the FR-034 table files its code under. A duplicated gate
# name is a malformed record, not an absent one, and stays on the schema plane so
# the two conditions are never filed together.
MISSING_GATE_FAILURE = ("evidence_boundary", "required_evidence_missing")
DUPLICATE_GATE_FAILURE = ("schema", "schema_invalid")
FAILED_GATE_FAILURE = ("candidate", "candidate_failed")


@dataclass(frozen=True)
class GateVerdict:
    """Outcome of checking one bundle's deterministic gate results."""

    complete: bool
    all_passed: bool
    missing: tuple[str, ...]
    failed: tuple[str, ...]
    failure_plane: str
    failure_code: str


def required_gates_for_role(role_id: str) -> tuple[str, ...]:
    """FR-014: every executed role records all seven; there is no subset."""
    if not role_id:
        raise ScoreBundleError("a gate set is required for a named role")
    return REQUIRED_GATES


def evaluate_gates(results: Sequence[Mapping[str, Any]]) -> GateVerdict:
    """Check gate completeness and outcome, failing closed on missing evidence."""
    seen: list[str] = []
    failed: list[str] = []
    for result in results:
        if tuple(sorted(result)) != GATE_RESULT_FIELDS:
            raise ScoreBundleError(f"a gate result must record exactly {GATE_RESULT_FIELDS}")
        gate = result["gate"]
        if gate not in REQUIRED_GATES:
            raise ScoreBundleError(f"{gate!r} is not a member of the closed hard-gate set")
        seen.append(gate)
        if not result["pass"]:
            failed.append(gate)

    missing = tuple(gate for gate in REQUIRED_GATES if gate not in seen)
    duplicated = len(set(seen)) != len(seen)
    if missing:
        plane, code = MISSING_GATE_FAILURE
        return GateVerdict(False, False, missing, tuple(failed), plane, code)
    if duplicated:
        plane, code = DUPLICATE_GATE_FAILURE
        return GateVerdict(False, False, (), tuple(failed), plane, code)
    if failed:
        plane, code = FAILED_GATE_FAILURE
        return GateVerdict(True, False, (), tuple(failed), plane, code)
    return GateVerdict(True, True, (), (), "none", "none")


def ballots_permitted(results: Sequence[Mapping[str, Any]]) -> bool:
    """FR-014: no semantic ballot is collected until every gate has passed."""
    verdict = evaluate_gates(results)
    return verdict.complete and verdict.all_passed


# ---------------------------------------------------------------------------
# Mechanical blinding leak check (FR-035)
# ---------------------------------------------------------------------------

AGENT_FRONTMATTER_KEYS = (
    "color",
    "description",
    "effort",
    "hooks",
    "isolation",
    "mcpservers",
    "model",
    "name",
    "permissionmode",
    "tools",
)
EFFORT_DECLARATION_KEYS = ("effort", "reasoning_effort", "reasoning-effort", "thinking_effort")
BALLOT_NON_BLIND = "ballot_non_blind"

# FR-014, FR-035: a leak check that was never run is missing evidence, not a
# pass. It lands on the evidence-boundary plane, distinct from the ballot-plane
# code a check that ran and failed records.
LEAK_CHECK_NOT_RUN = "leak_check_not_run"
MISSING_LEAK_EVIDENCE_FAILURE = ("evidence_boundary", "required_evidence_missing")


@dataclass(frozen=True)
class LeakFinding:
    """Outcome of the pre-ballot blinding leak check."""

    passed: bool
    hits: tuple[str, ...]
    failure_plane: str
    failure_code: str


def build_leak_lexicon(
    *,
    model_identities: Iterable[str],
    aliases: Iterable[str],
    efforts: Iterable[str],
    route_identifiers: Iterable[str],
    frontmatter_keys: Iterable[str] | None = None,
) -> dict[str, tuple[str, ...]]:
    """Split the freeze-bound identifiers into identity and contextual classes."""
    identity = tuple(
        sorted({token.lower() for token in (*model_identities, *aliases, *route_identifiers) if token})
    )
    return {
        "identity_tokens": identity,
        "alias_tokens": tuple(sorted({token.lower() for token in aliases if token})),
        "contextual_tokens": tuple(sorted({token.lower() for token in efforts if token})),
        "frontmatter_keys": tuple(
            sorted(
                {key.lower() for key in (AGENT_FRONTMATTER_KEYS if frontmatter_keys is None else frontmatter_keys)}
            )
        ),
    }


def leak_check(artifact_text: str, lexicon: Mapping[str, Sequence[str]]) -> LeakFinding:
    """Strip-and-refuse: any surviving identifier blocks the ballot."""
    haystack = artifact_text.lower()
    hits: list[str] = []

    for token in lexicon["identity_tokens"]:
        if re.search(rf"(?<![0-9a-z_]){re.escape(token)}(?![0-9a-z_])", haystack):
            hits.append(f"identity:{token}")

    aliases = "|".join(re.escape(alias) for alias in lexicon["alias_tokens"]) or r"(?!)"
    keys = "|".join(re.escape(key) for key in EFFORT_DECLARATION_KEYS)
    for token in lexicon["contextual_tokens"]:
        escaped = re.escape(token)
        declared = re.search(rf"(?:{keys})\s*[:=]\s*[\"']?{escaped}(?![0-9a-z_])", haystack)
        joined = re.search(rf"(?:{aliases})[-_]{escaped}(?![0-9a-z_])", haystack)
        if declared or joined:
            hits.append(f"effort:{token}")

    for key in lexicon["frontmatter_keys"]:
        if re.search(rf"^[ \t]*{re.escape(key)}[ \t]*:", haystack, flags=re.MULTILINE):
            hits.append(f"frontmatter:{key}")

    if hits:
        return LeakFinding(False, tuple(sorted(hits)), "ballot", BALLOT_NON_BLIND)
    return LeakFinding(True, (), "none", "none")


# ---------------------------------------------------------------------------
# Ballots, adjudication, and the blinding residual (FR-015, FR-016, FR-048)
# ---------------------------------------------------------------------------

BALLOT_FIELDS = (
    "ballot_digest",
    "ballot_id",
    "blinded_artifact_digest",
    "calibration_binding",
    "criterion_scores",
    "inference_signal",
    "presentation_order_seed",
    "provenance_inferred",
    "rubric_binding",
    "scorer_binding",
    "scorer_execution_id",
)

BLINDING_CLAIM = (
    "Blinding is enforced and bounded: identifier stripping cannot remove stylistic "
    "tells, so every ballot records whether provenance was inferred and from what "
    "signal, and that residual is reported alongside any qualification claim."
)

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def build_ballot(
    *,
    ballot_id: str,
    scorer_binding: Mapping[str, str],
    scorer_execution_id: str,
    calibration_binding: Mapping[str, str],
    rubric_binding: Mapping[str, str],
    blinded_artifact_digest: Any,
    criterion_scores: Mapping[str, float],
    provenance_inferred: bool,
    inference_signal: str | None = None,
    presentation_order_seed: str | None = None,
) -> dict[str, Any]:
    """Seal one ballot bound to exactly one blinded artifact (FR-035, FR-048)."""
    if not isinstance(blinded_artifact_digest, str) or not _DIGEST_RE.match(blinded_artifact_digest):
        raise ScoreBundleError(
            "a ballot binds exactly one blinded-artifact digest as its sole scored input"
        )
    if not criterion_scores:
        raise ScoreBundleError("a ballot must score at least one rubric criterion")
    if provenance_inferred and not inference_signal:
        raise ScoreBundleError("a recorded provenance inference must name its signal")
    ballot: dict[str, Any] = {
        "ballot_id": ballot_id,
        "scorer_binding": dict(scorer_binding),
        "scorer_execution_id": scorer_execution_id,
        "calibration_binding": dict(calibration_binding),
        "rubric_binding": dict(rubric_binding),
        "blinded_artifact_digest": blinded_artifact_digest,
        "criterion_scores": dict(criterion_scores),
        "provenance_inferred": bool(provenance_inferred),
        "inference_signal": inference_signal,
        "presentation_order_seed": presentation_order_seed,
    }
    ballot["ballot_digest"] = record_digest(ballot, digest_field="ballot_digest")
    return ballot


def scored_inputs(ballot: Mapping[str, Any]) -> tuple[str, ...]:
    """FR-035: the blinded artifact is the ballot's only scored input."""
    return (ballot["blinded_artifact_digest"],)


def ballot_verdicts(ballot: Mapping[str, Any], rubric: Mapping[str, Any]) -> dict[str, bool]:
    threshold = float(rubric["criterion_threshold"])
    return {name: float(score) >= threshold for name, score in ballot["criterion_scores"].items()}


def decision_affecting_disagreement(
    first: Mapping[str, Any], second: Mapping[str, Any], rubric: Mapping[str, Any]
) -> bool:
    """A disagreement matters when the two ballots reach different verdicts."""
    return ballot_verdicts(first, rubric) != ballot_verdicts(second, rubric)


def adjudicate(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
    *,
    adjudication_id: str,
    adjudicator_binding: Mapping[str, str],
    resolved_outcome: str,
) -> dict[str, Any]:
    """Route a decision-affecting disagreement to the frozen third adjudicator."""
    primaries = {first["scorer_binding"]["id"], second["scorer_binding"]["id"]}
    if adjudicator_binding["id"] in primaries:
        raise ScoreBundleError("adjudicator_reused_primary_scorer")
    adjudication: dict[str, Any] = {
        "adjudication_id": adjudication_id,
        "adjudicator_binding": dict(adjudicator_binding),
        "ballot_bindings": [
            {"id": ballot["ballot_id"], "digest": ballot["ballot_digest"]}
            for ballot in (first, second)
        ],
        "resolved_outcome": resolved_outcome,
    }
    adjudication["adjudication_digest"] = record_digest(adjudication, digest_field="adjudication_digest")
    return adjudication


@dataclass(frozen=True)
class BallotCollection:
    """Outcome of collecting the two required ballots behind the gate barrier."""

    accepted: bool
    ballots: tuple[Mapping[str, Any], ...]
    failure_plane: str
    failure_code: str
    reasons: tuple[str, ...] = ()


def _refused(plane: str, code: str, *reasons: str) -> BallotCollection:
    return BallotCollection(False, (), plane, code, reasons)


def collect_ballots(
    gate_results: Sequence[Mapping[str, Any]],
    *,
    ballots: Sequence[Mapping[str, Any]],
    rubric: Mapping[str, Any],
    current_calibrations: Sequence[str],
    leak_finding: LeakFinding | None = None,
    adjudication: Mapping[str, Any] | None = None,
) -> BallotCollection:
    """Two distinct scorers, one frozen rubric, current calibration, resolved
    disagreement — checked in that order so the earliest cause is reported.

    ``leak_finding`` is required evidence. An absent finding means the mechanical
    blinding check never ran, which is a missing-evidence refusal rather than a
    reason to collect the ballots unblinded.
    """
    verdict = evaluate_gates(gate_results)
    if not (verdict.complete and verdict.all_passed):
        return _refused(verdict.failure_plane, verdict.failure_code, "gate_barrier")

    if leak_finding is None:
        return _refused(*MISSING_LEAK_EVIDENCE_FAILURE, LEAK_CHECK_NOT_RUN)
    if not leak_finding.passed:
        return _refused(leak_finding.failure_plane, leak_finding.failure_code, BALLOT_NON_BLIND)

    if len(ballots) != 2:
        return _refused("ballot", "ballot_missing", "two_ballots_required")

    first, second = ballots
    if first["scorer_binding"]["id"] == second["scorer_binding"]["id"]:
        return _refused("scorer", "scorer_invalid", "scorer_identity_reused")
    if first["scorer_execution_id"] == second["scorer_execution_id"]:
        return _refused("scorer", "scorer_invalid", "scorer_execution_reused")

    frozen_rubric = rubric["rubric_binding"]
    if any(ballot["rubric_binding"] != frozen_rubric for ballot in ballots):
        return _refused("ballot", "ballot_rubric_stale", "rubric_not_frozen")

    calibrations = frozenset(current_calibrations)
    if any(ballot["calibration_binding"]["id"] not in calibrations for ballot in ballots):
        return _refused("scorer", "scorer_calibration_missing", "calibration_not_current")

    if decision_affecting_disagreement(first, second, rubric) and adjudication is None:
        return _refused(
            "adjudication", "adjudication_disagreement_unresolved", "adjudicator_not_recorded"
        )

    return BallotCollection(True, tuple(ballots), "none", "none", ())


def blinding_residual(
    *, leak_check_passed: bool, ballots: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """FR-048: report the residual rather than claiming blinding succeeded."""
    inferring = [ballot for ballot in ballots if ballot.get("provenance_inferred")]
    signal = next((ballot.get("inference_signal") for ballot in inferring), None)
    return {
        "leak_check_passed": bool(leak_check_passed),
        "provenance_inferred": bool(inferring),
        "inference_signal": signal,
    }


# ---------------------------------------------------------------------------
# Observed scorer identity and family exclusion (FR-047)
# ---------------------------------------------------------------------------

BALLOT_ROLES = ("scorer_a", "scorer_b", "adjudicator")
_ROLE_FAILURE_CODE = {
    "scorer_a": "scorer_invalid",
    "scorer_b": "scorer_invalid",
    "adjudicator": "adjudicator_invalid",
}


@dataclass(frozen=True)
class RouteDivergence:
    """FR-039 observed-versus-declared check applied to a scorer or adjudicator."""

    diverged: bool
    blocks_ballot: bool
    failure_plane: str
    failure_code: str


def check_scorer_route_divergence(
    *, declared_route_identity: str, observed_model_id: str | None
) -> RouteDivergence:
    """A scorer whose observed identity diverges blocks its ballot outright."""
    if observed_model_id == declared_route_identity:
        return RouteDivergence(False, False, "none", "none")
    return RouteDivergence(True, True, "scorer", "scorer_invalid")


def observed_family(model_id: str | None, family_declaration: Mapping[str, str]) -> str | None:
    """Resolve an observed identity to its declared family, or ``None``."""
    if not model_id:
        return None
    return family_declaration.get(model_id)


def build_scorer_identity_attestation(
    *,
    attestation_id: str,
    score_bundle_binding: Mapping[str, str],
    ballot_attestations: Sequence[Mapping[str, Any]],
    family_declaration: Mapping[str, str],
    candidate_families: Sequence[str],
    recorded_at: str,
) -> dict[str, Any]:
    """Record each scorer's and adjudicator's OBSERVED identity at ballot time.

    Static exclusion is declared at freeze time and cannot see a post-freeze
    re-point of the scorer itself, so the observed family is resolved here and an
    unresolvable identity fails closed rather than being read as out-of-family.
    """
    families = frozenset(candidate_families)
    entries: list[dict[str, Any]] = []
    for entry in ballot_attestations:
        role = entry["ballot_role"]
        if role not in BALLOT_ROLES:
            raise ScoreBundleError(f"{role!r} is not a member of the closed ballot-role set")
        model_id = entry.get("observed_model_id")
        family = observed_family(model_id, family_declaration)
        entries.append(
            {
                "ballot_role": role,
                "declared_family": entry["declared_family"],
                "observed_model_id": model_id,
                "observed_family": family,
                "family_exclusion_holds": family is not None and family not in families,
            }
        )
    attestation: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_kind": "scorer_identity_attestation",
        "attestation_id": attestation_id,
        "score_bundle_binding": dict(score_bundle_binding),
        "ballot_attestations": entries,
        "recorded_at": recorded_at,
    }
    attestation["attestation_digest"] = record_digest(attestation, digest_field="attestation_digest")
    return attestation


def attestation_findings(attestation: Mapping[str, Any]) -> tuple[str, ...]:
    """Name every ballot role whose observed identity breaks family exclusion."""
    return tuple(
        f"{entry['ballot_role']}:{_ROLE_FAILURE_CODE[entry['ballot_role']]}"
        for entry in attestation["ballot_attestations"]
        if not entry["family_exclusion_holds"]
    )


def attestation_blocks_acceptance(attestation: Mapping[str, Any]) -> bool:
    """FR-047: a false exclusion claim blocks acceptance, never just records it."""
    return bool(attestation_findings(attestation))


def presentation_order(items: Sequence[str], seed: str) -> tuple[str, ...]:
    """FR-047: seeded, replayable presentation-order randomization."""
    ordered = list(items)
    random.Random(seed).shuffle(ordered)
    return tuple(ordered)


# ---------------------------------------------------------------------------
# Closed score taxonomies (FR-034)
# ---------------------------------------------------------------------------

SCORE_DISPOSITIONS = ("accepted", "gate_failed", "non_scorable", "invalidated")

FAILURE_PLANE_BY_CODE: Mapping[str, str] = MappingProxyType(
    {
        "none": "none",
        "treatment_misdelivery": "treatment",
        "service_reroute": "treatment",
        "mandatory_telemetry_missing": "treatment",
        "treatment_infrastructure_failure": "treatment",
        "fixture_invalid": "fixture",
        "fixture_stale": "fixture",
        "fixture_partition_invalid": "fixture",
        "fixture_oracle_invalid": "fixture",
        "scorer_invalid": "scorer",
        "scorer_stale": "scorer",
        "scorer_calibration_missing": "scorer",
        "ballot_missing": "ballot",
        "ballot_non_blind": "ballot",
        "ballot_provenance_incomplete": "ballot",
        "ballot_rubric_stale": "ballot",
        "adjudication_disagreement_unresolved": "adjudication",
        "adjudicator_invalid": "adjudication",
        "adjudicator_stale": "adjudication",
        "adjudicator_reused_primary_scorer": "adjudication",
        "candidate_failed": "candidate",
        "candidate_timed_out": "candidate",
        "candidate_cancelled": "candidate",
        "candidate_budget_exhausted": "candidate",
        "candidate_abandoned": "candidate",
        "transient_harness_failure": "infrastructure",
        "infrastructure_failure": "infrastructure",
        "unclassifiable_attrition": "evidence_boundary",
        "sensitive_evidence_violation": "evidence_boundary",
        "required_evidence_missing": "evidence_boundary",
        "partition_mismatch": "partition",
        "partition_not_eligible": "partition",
        "cross_partition_reuse": "partition",
        "schema_invalid": "schema",
        "binding_digest_mismatch": "schema",
    }
)
FAILURE_CODES = tuple(FAILURE_PLANE_BY_CODE)
FAILURE_PLANES = tuple(dict.fromkeys(FAILURE_PLANE_BY_CODE.values()))

INVALIDATION_REASONS = (
    "none",
    "fixture_changed",
    "scorer_changed",
    "rubric_changed",
    "adjudicator_changed",
    "treatment_changed",
    "capability_changed",
    "partition_changed",
    "schema_changed",
)

# FR-034: platform alias re-pointing reuses the shared treatment-record reason;
# the capability-plane alias_repoint_unresolved stays on the capability freeze.
SERVICE_REROUTE_DISPOSITION_REASON = "service_reroute_requested_route_non_scorable"
SERVICE_REROUTE_FAILURE_CODE = "service_reroute"

# The stage a live failure came from picks between the two live-failure
# dispositions: a deterministic hard gate produces a candidate-plane outcome or a
# schema-plane malformation refusal; anything downstream, and any missing-evidence
# refusal, is non-scorable — evidence that was never produced cannot carry the
# "evidence sufficient, bar not cleared" reading FR-019 gives a failed gate.
GATE_STAGE_CODES = frozenset(
    {
        "candidate_failed",
        "candidate_timed_out",
        "candidate_cancelled",
        "candidate_budget_exhausted",
        "candidate_abandoned",
        "schema_invalid",
    }
)


def failure_plane_for(failure_code: str) -> str:
    """FR-034: the plane is derived from the code, never authored beside it."""
    try:
        return FAILURE_PLANE_BY_CODE[failure_code]
    except KeyError:
        raise ScoreBundleError(
            f"{failure_code!r} is not a member of the closed score failure-code taxonomy"
        ) from None


def normalize_failure(failure_plane: str, failure_code: str) -> tuple[str, str]:
    """Fail an unlisted (plane, code) pair closed to ``(schema, schema_invalid)``."""
    if FAILURE_PLANE_BY_CODE.get(failure_code) != failure_plane:
        return ("schema", "schema_invalid")
    return (failure_plane, failure_code)


def bind_disposition(failure_plane: str, failure_code: str, invalidation_reason: str) -> str:
    """FR-034: the disposition is bound to the failure fields, not recorded beside them."""
    if invalidation_reason not in INVALIDATION_REASONS:
        raise ScoreBundleError(f"{invalidation_reason!r} is not a closed invalidation reason")
    if invalidation_reason != "none":
        return "invalidated"
    plane, code = normalize_failure(failure_plane, failure_code)
    if plane == "none" and code == "none":
        return "accepted"
    return "gate_failed" if code in GATE_STAGE_CODES else "non_scorable"


def disposition_findings(bundle: Mapping[str, Any]) -> tuple[str, ...]:
    """Every violation of the FR-034 disposition binding; empty means consistent."""
    disposition = bundle["score_disposition"]
    plane = bundle["failure_plane"]
    code = bundle["failure_code"]
    reason = bundle["invalidation_reason"]
    if disposition not in SCORE_DISPOSITIONS:
        return (f"score_disposition {disposition!r} is not a closed member",)

    findings: list[str] = []
    all_none = plane == "none" and code == "none" and reason == "none"
    if disposition == "accepted" and not all_none:
        findings.append("accepted requires failure_plane, failure_code, and invalidation_reason none")
    if disposition != "accepted" and all_none:
        findings.append(f"{disposition} requires a live failure or invalidation field")
    if disposition in ("gate_failed", "non_scorable") and (plane == "none" or code == "none"):
        findings.append(f"{disposition} requires a non-none failure_plane and failure_code")
    if disposition == "invalidated" and reason == "none":
        findings.append("invalidated requires a non-none invalidation_reason")
    if code != "none" and normalize_failure(plane, code) != (plane, code):
        findings.append(f"({plane}, {code}) is not a listed plane/code pair")
    return tuple(findings)


def record_service_reroute(record: Mapping[str, Any]) -> dict[str, Any]:
    """FR-034: reuse the shared reroute reason; coin no Claude-only member."""
    updated = copy.deepcopy(dict(record))
    reasons = list(updated.get("disposition_reasons", []))
    if SERVICE_REROUTE_DISPOSITION_REASON not in reasons:
        reasons.append(SERVICE_REROUTE_DISPOSITION_REASON)
    updated["disposition_reasons"] = reasons
    updated["failure_code"] = SERVICE_REROUTE_FAILURE_CODE
    updated["failure_plane"] = failure_plane_for(SERVICE_REROUTE_FAILURE_CODE)
    return updated


# ---------------------------------------------------------------------------
# Score bundle assembly, provenance, and additive invalidation (FR-016, FR-034)
# ---------------------------------------------------------------------------

PROVENANCE_CLASSES: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "fixture": ("fixture_binding",),
        "scorer": ("ballots",),
        "treatment": (
            "treatment_contract_binding",
            "execution_trace_binding",
            "telemetry_profile_binding",
        ),
        "candidate": (
            "candidate_route_binding",
            "agent_contract_binding",
            "candidate_freeze_binding",
            "route_resolution_binding",
        ),
        "adjudicator": ("adjudication",),
        "infrastructure": (
            "runtime_snapshot_binding",
            "experiment_policy_binding",
            "partition_binding",
            "assignment_binding",
        ),
    }
)

PROVENANCE_BINDINGS = tuple(
    sorted(
        field_name
        for fields in PROVENANCE_CLASSES.values()
        for field_name in fields
        if field_name.endswith("_binding")
    )
)

REASONING_TOKEN_LIMITATION = (
    "reasoning_output_tokens is recorded and reported for every attempt but is not a "
    "Pareto dimension, because the twin's frozen policy omits it; the tokens are "
    "billed, so this is a stated limitation rather than a claim the cost is absent."
)

# FR-027, FR-036: deny by default. Any of these blocks publication rather than
# being silently stripped.
OPERATOR_ONLY_EVIDENCE_FIELDS = frozenset(
    {
        "absolute_path",
        "account_id",
        "api_key",
        "authorization",
        "billing_id",
        "cookie",
        "plan_id",
        "private_host",
        "raw_prompt",
        "raw_response",
        "repository_remote",
        "scorer_identity_map",
        "transcript",
    }
)


def build_score_bundle(
    *,
    score_bundle_id: str,
    bindings: Mapping[str, Mapping[str, str]],
    deterministic_gates: Sequence[Mapping[str, Any]],
    ballots: Sequence[Mapping[str, Any]],
    adjudication: Mapping[str, Any] | None,
    resource_vector: Mapping[str, Any],
    reasoning_output_tokens: int | None,
    evidence_refs: Sequence[str],
    leak_finding: LeakFinding | None = None,
    invalidation_reason: str = "none",
) -> dict[str, Any]:
    """Assemble one score bundle with its disposition bound to its failure fields.

    The blinding residual is **consumed, never asserted**. ``leak_finding`` is the
    recorded verdict of the mechanical check :func:`collect_ballots` runs; a
    bundle built without one cannot claim the check passed, and a bundle carrying
    no ballot has nothing a scorer could have been blinded to. Both fail closed
    rather than sealing as ``accepted`` on evidence that was never produced
    (FR-014, FR-035, FR-048).
    """
    missing_bindings = tuple(name for name in PROVENANCE_BINDINGS if name not in bindings)
    if missing_bindings:
        raise ScoreBundleError(f"score bundle is missing provenance bindings: {missing_bindings}")

    verdict = evaluate_gates(deterministic_gates)
    plane, code = normalize_failure(verdict.failure_plane, verdict.failure_code)
    leak_check_passed = leak_finding is not None and leak_finding.passed
    if plane == "none" and code == "none":
        # Checked in the order collect_ballots checks them, so the earliest
        # missing cause is the one the bundle records.
        if leak_finding is None:
            plane, code = normalize_failure(*MISSING_LEAK_EVIDENCE_FAILURE)
        elif not leak_finding.passed:
            plane, code = normalize_failure(leak_finding.failure_plane, leak_finding.failure_code)
        elif len(ballots) != 2:
            plane, code = normalize_failure("ballot", "ballot_missing")
    bundle: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "score_bundle_id": score_bundle_id,
        **{name: dict(bindings[name]) for name in PROVENANCE_BINDINGS},
        "deterministic_gates": [dict(result) for result in deterministic_gates],
        "ballots": [dict(ballot) for ballot in ballots],
        "adjudication": dict(adjudication) if adjudication is not None else None,
        "score_disposition": bind_disposition(plane, code, invalidation_reason),
        "failure_plane": plane,
        "failure_code": code,
        "invalidation_reason": invalidation_reason,
        "resource_vector": dict(resource_vector),
        "reasoning_token_report": {
            "reasoning_output_tokens": reasoning_output_tokens,
            "decision_bearing": False,
            "stated_limitation": REASONING_TOKEN_LIMITATION,
        },
        "blinding_residual": blinding_residual(
            leak_check_passed=leak_check_passed, ballots=ballots
        ),
        "evidence_refs": list(evidence_refs),
    }
    bundle["score_bundle_digest"] = record_digest(bundle, digest_field="score_bundle_digest")
    return bundle


def missing_provenance(bundle: Mapping[str, Any]) -> tuple[str, ...]:
    """FR-016: name every provenance class the bundle failed to preserve.

    ``adjudication`` counts as preserved when the key is present and explicitly
    null — a bundle whose ballots agreed still has to record that no adjudication
    was needed, rather than leaving the reader to infer it from an absent key.
    """
    findings: list[str] = []
    for provenance_class, fields in PROVENANCE_CLASSES.items():
        for field_name in fields:
            if field_name == "adjudication":
                if field_name not in bundle:
                    findings.append(f"{provenance_class}:{field_name}")
                continue
            value = bundle.get(field_name)
            if value is None or value == [] or value == ():
                findings.append(f"{provenance_class}:{field_name}")
    return tuple(sorted(findings))


def invalidate_bundle(bundle: Mapping[str, Any], reason: str) -> dict[str, Any]:
    """FR-034: invalidations are additive and never rewrite the prior bundle."""
    if reason not in INVALIDATION_REASONS or reason == "none":
        raise ScoreBundleError(f"{reason!r} is not a live closed invalidation reason")
    superseding = copy.deepcopy(dict(bundle))
    superseding["score_bundle_id"] = f"{bundle['score_bundle_id']}+{reason}"
    superseding["supersedes"] = {
        "id": bundle["score_bundle_id"],
        "digest": bundle["score_bundle_digest"],
    }
    superseding["invalidation_reason"] = reason
    superseding["score_disposition"] = bind_disposition(
        superseding["failure_plane"], superseding["failure_code"], reason
    )
    superseding["score_bundle_digest"] = record_digest(superseding, digest_field="score_bundle_digest")
    return superseding


def inspect_committed_evidence(record: Any, path: str = "") -> tuple[str, ...]:
    """Deny-by-default walk: any operator-only field blocks publication."""
    findings: list[str] = []
    if isinstance(record, Mapping):
        for key, value in record.items():
            where = f"{path}.{key}" if path else str(key)
            if str(key).lower() in OPERATOR_ONLY_EVIDENCE_FIELDS:
                findings.append(where)
            findings.extend(inspect_committed_evidence(value, where))
    elif isinstance(record, (list, tuple)):
        for index, value in enumerate(record):
            findings.extend(inspect_committed_evidence(value, f"{path}[{index}]"))
    return tuple(findings)


def evidence_boundary_failure(findings: Sequence[str]) -> tuple[str, str]:
    """Map an evidence-boundary finding onto its closed plane and code."""
    if findings:
        return ("evidence_boundary", "sensitive_evidence_violation")
    return ("none", "none")


# ---------------------------------------------------------------------------
# Evidence ignore boundary (FR-027)
# ---------------------------------------------------------------------------

RESULTS_DIR = LAYER6_ROOT / "results"
RESULTS_GITIGNORE_PATH = LAYER6_ROOT / ".gitignore"
CONSOLIDATED_BASELINE_NAME = "consolidated-baseline.json"
CONSOLIDATED_BASELINE_RELATIVE_ENTRY = f"results/{CONSOLIDATED_BASELINE_NAME}"
CONSOLIDATED_BASELINE_PATH = RESULTS_DIR / CONSOLIDATED_BASELINE_NAME
RAW_RESULT_PROBE_PATHS = (
    RESULTS_DIR / "claude-attempt-0001.json",
    RESULTS_DIR / "raw" / "claude-attempt-0001.jsonl",
)
