#!/usr/bin/env python3
"""Pure (non-live) probe logic for the CAR-002 operator capability probe.

This module holds everything the operator probe tool computes **without** talking
to a live ``claude`` CLI: the bounded probe matrix (the 37 CAR-001 candidate
routes deduplicated to their 6 unique ``(model, effort)`` tuples), ``tuple_id``
derivation, the fixed canary text and its hash, ``<home>`` sanitization of raw
payloads, per-payload SHA-256 over the sanitized bytes, the three fail-closed
dispositions that gate whether a snapshot is written, and the FR-003 budget /
timeout / no-retry controls.

The single live boundary is kept strictly out of this module. The bounded matrix
is driven through an injected ``LiveInvoker`` seam (:func:`run_bounded_probe_matrix`);
the real invoker — the only path permitted to spawn ``claude`` (via ``subprocess``,
argument array, ``shell=False``, explicit timeout) — is implemented separately
(T011) and passed in. Tests inject a fake invoker, so every check here runs with
zero live model calls (FR-001/FR-002). The capability-answer / evidence-capture
logic (T012) and the subagent-frontmatter dispatch mechanism (T014) build on top
of this module; they are not implemented here.

Standard library only — no third-party dependencies (constitution II).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MANIFEST_PATH = REPO_ROOT / "docs" / "ai" / "research" / "claude-agent-route-candidate-manifest.json"

# The single fixed canary used identically across every probe in one snapshot
# (FR-005; research R8). Exact UTF-8 bytes, no trailing newline; the content is
# measurement-irrelevant, so only byte-invariance across a snapshot is contractual.
CANARY_TEXT = "Reply with the single word: ok"

# ``<home>`` normalization token + the schema ``rawEvidence.sanitization`` const it
# corresponds to (FR-012/FR-013; research R9). Reuses the release-readiness
# ``str(Path.home()) -> "<home>"`` convention, generalized to every documented
# home/user path form plus machine-local session paths so it is deterministic and
# environment-independent.
HOME_TOKEN = "<home>"
SANITIZATION_MARKER = "home_paths_normalized_utf8"

# ``tuple_id = "<model>__<effort>"``; a JSON-null effort segment is the literal
# ``none`` (research R1).
NULL_EFFORT_TOKEN = "none"
TUPLE_ID_SEPARATOR = "__"

# Roughly-20 live-invocation ceiling (FR-003; spec "Budget overrun" edge case). An
# overrun is a matrix-definition error surfaced before any live call is made.
INVOCATION_BUDGET_CEILING = 20

# Planned live-invocation purposes.
PURPOSE_ALIAS_CANARY = "alias_canary"
PURPOSE_CONFIG_ACCEPTANCE = "config_acceptance"
PURPOSE_UNAVAILABLE_PROBE = "unavailable_probe"

# The two FR-009 unavailable-model probe surfaces (matches the schema
# ``unavailableObservation.surface`` enum).
UNAVAILABLE_SURFACES = ("print_model", "subagent_frontmatter")

# Live-invocation output modes.
OUTPUT_MODE_JSON = "json"
OUTPUT_MODE_PLAIN_TEXT = "plain_text"

# The three fail-closed dispositions (spec "Partial probe matrix" edge case; FR-023).
DISPOSITION_ABORT_WRITE = "abort_write"  # (1) schema-invalid / unparseable observation
DISPOSITION_ABORT_RUN = "abort_run"      # (2) transport failure — never "unavailable"
DISPOSITION_RECORD = "record"            # (3) interpretable platform observation (incl. undetermined)
PROBE_DISPOSITIONS = frozenset({DISPOSITION_ABORT_WRITE, DISPOSITION_ABORT_RUN, DISPOSITION_RECORD})


class ClaudeCapabilitiesError(AssertionError):
    """Base error for the CAR-002 probe logic (mirrors ``ClaudeTraceContractError``)."""


class BudgetOverrunError(ClaudeCapabilitiesError):
    """The precomputed matrix cardinality exceeds the live-invocation budget ceiling."""


class ProbeRunAborted(ClaudeCapabilitiesError):
    """A transport/infrastructure failure aborts the run — no retries, nothing committed."""


def _sha256_hex(text: str) -> str:
    """SHA-256 hex digest over the exact UTF-8 bytes of ``text``."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Computed once over the exact canary bytes (FR-005/FR-013).
CANARY_SHA256 = _sha256_hex(CANARY_TEXT)


# -- Fixed canary ------------------------------------------------------------


def canary_metadata() -> dict[str, str]:
    """The snapshot ``canary`` block: the fixed text and its byte hash (FR-005)."""
    return {"text": CANARY_TEXT, "canary_sha256": CANARY_SHA256}


# -- <home> sanitization + per-payload hashing -------------------------------
# Mirror the committed privacy-scan path families
# (tests/speckit-pro/unit/test-privacy-scan.py) so a sanitized payload can never
# leave a home/user or machine-local session path in the committed snapshot.

_HOME_PATH_RE = re.compile(
    r"(?:/(?:Users|home)/|[A-Za-z]:[\\/]+Users[\\/]+)[A-Za-z0-9_.\-]+", re.IGNORECASE
)
_HYPHENATED_HOME_RE = re.compile(r"-Users-[A-Za-z0-9_.\-]+", re.IGNORECASE)
_PRIVATE_VAR_RE = re.compile(r"/private/var/folders/[A-Za-z0-9_/\.\-]+", re.IGNORECASE)
_TMP_TRANSCRIPT_RE = re.compile(r"/private/tmp/claude-[0-9]+", re.IGNORECASE)
_SANITIZERS = (_PRIVATE_VAR_RE, _TMP_TRANSCRIPT_RE, _HOME_PATH_RE, _HYPHENATED_HOME_RE)


def sanitize_home_paths(text: str) -> str:
    """Normalize home/user paths and machine-local session paths to ``<home>``.

    Deterministic and idempotent: every documented home/user path form
    (``/Users/<u>``, ``/home/<u>``, ``C:\\Users\\<u>``, hyphenated ``-Users-<u>``)
    and machine-local session path (macOS ``/private/var/folders`` temp trees and
    ``/private/tmp/claude-<n>`` session paths) collapses to the ``<home>`` token,
    so no unsanitized absolute path can be committed (FR-012/FR-013).
    """
    sanitized = text
    for pattern in _SANITIZERS:
        sanitized = pattern.sub(HOME_TOKEN, sanitized)
    return sanitized


def payload_sha256(sanitized_payload: str) -> str:
    """SHA-256 over the exact sanitized UTF-8 bytes, so the hash reproduces from
    the committed verbatim string (FR-013)."""
    return _sha256_hex(sanitized_payload)


# -- tuple_id derivation + bounded probe matrix ------------------------------


def derive_tuple_id(model: str, effort_requested: str | None) -> str:
    """``"<model>__<effort>"`` lowercased; a JSON-null effort becomes ``none`` (R1)."""
    model_token = str(model).lower()
    effort_token = NULL_EFFORT_TOKEN if effort_requested is None else str(effort_requested).lower()
    return f"{model_token}{TUPLE_ID_SEPARATOR}{effort_token}"


@dataclass(frozen=True)
class TupleSpec:
    """One deduplicated ``(model, effort)`` probe tuple and how many CAR-001 routes
    resolve to it (the count is derived on demand, never persisted — SC-005)."""

    tuple_id: str
    model: str
    effort_requested: str | None
    route_count: int


@dataclass(frozen=True)
class ProbeMatrix:
    """The bounded probe matrix: the unique tuples the 37 routes reduce to."""

    tuples: tuple[TupleSpec, ...]
    total_routes: int

    @property
    def cardinality(self) -> int:
        return len(self.tuples)

    @property
    def tuple_ids(self) -> tuple[str, ...]:
        return tuple(spec.tuple_id for spec in self.tuples)

    @property
    def model_aliases(self) -> tuple[str, ...]:
        """Unique model aliases in first-appearance order (one canary each)."""
        ordered: list[str] = []
        for spec in self.tuples:
            if spec.model not in ordered:
                ordered.append(spec.model)
        return tuple(ordered)


def build_probe_matrix(manifest: dict[str, Any] | None = None) -> ProbeMatrix:
    """Dedupe the CAR-001 candidate routes to their unique ``(model, effort)`` tuples.

    Groups every ``candidate_route`` by ``(model_selector.requested_value,
    effort_selector.requested_value)``; the committed 37-route manifest reduces to
    6 tuples (research R1). The route→tuple map is computed here, never persisted
    (FR-004/SC-005). Pass ``manifest`` to test against synthetic inputs; otherwise
    the committed manifest is loaded.
    """
    if manifest is None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    routes = manifest["candidate_routes"]
    order: list[str] = []
    groups: dict[str, dict[str, Any]] = {}
    for route in routes:
        model = route["model_selector"]["requested_value"]
        effort = route["effort_selector"]["requested_value"]
        tuple_id = derive_tuple_id(model, effort)
        group = groups.get(tuple_id)
        if group is None:
            groups[tuple_id] = {"model": model, "effort": effort, "count": 1}
            order.append(tuple_id)
        else:
            group["count"] += 1
    specs = tuple(
        TupleSpec(
            tuple_id=tuple_id,
            model=groups[tuple_id]["model"],
            effort_requested=groups[tuple_id]["effort"],
            route_count=groups[tuple_id]["count"],
        )
        for tuple_id in order
    )
    return ProbeMatrix(tuples=specs, total_routes=len(routes))


# -- Planned live invocations + budget ---------------------------------------


@dataclass(frozen=True)
class PlannedInvocation:
    """One planned live invocation intent (what the live boundary will execute)."""

    purpose: str
    model_alias: str | None = None
    effort_requested: str | None = None
    tuple_id: str | None = None
    surface: str | None = None


def plan_probe_invocations(matrix: ProbeMatrix) -> tuple[PlannedInvocation, ...]:
    """Expand the matrix into the precomputed live-invocation plan (FR-003).

    One alias-canary per unique model alias (ID binding, CAP-Q1..Q4) + one
    configuration-acceptance check per unique tuple + one unavailable-model probe
    per FR-009 surface. Its length is the precomputed live-invocation count the
    budget bounds — distinct from :attr:`ProbeMatrix.cardinality` (the tuple
    count) — and is kept within the ~20-invocation ceiling.
    """
    planned: list[PlannedInvocation] = []
    for alias in matrix.model_aliases:
        planned.append(PlannedInvocation(purpose=PURPOSE_ALIAS_CANARY, model_alias=alias))
    for spec in matrix.tuples:
        planned.append(
            PlannedInvocation(
                purpose=PURPOSE_CONFIG_ACCEPTANCE,
                model_alias=spec.model,
                effort_requested=spec.effort_requested,
                tuple_id=spec.tuple_id,
            )
        )
    for surface in UNAVAILABLE_SURFACES:
        planned.append(PlannedInvocation(purpose=PURPOSE_UNAVAILABLE_PROBE, surface=surface))
    return tuple(planned)


def enforce_invocation_budget(cardinality: int, *, ceiling: int = INVOCATION_BUDGET_CEILING) -> None:
    """Raise :class:`BudgetOverrunError` if the plan exceeds the ceiling (FR-003).

    Called before any live invocation so a matrix-definition error surfaces
    without a single ``claude`` call being made.
    """
    if cardinality > ceiling:
        raise BudgetOverrunError(
            f"probe matrix cardinality {cardinality} exceeds the {ceiling}-invocation "
            "budget ceiling — matrix-definition error surfaced before any live call"
        )


# -- Fail-closed disposition gating ------------------------------------------


@dataclass(frozen=True)
class ProbeInvocationResult:
    """The raw result of one live invocation, produced by the ``LiveInvoker`` seam.

    Pure classification consumes it without any live call. ``return_code`` is
    ``None`` when the process never returned (timeout / spawn failure).
    """

    return_code: int | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    network_error: bool = False
    output_mode: str = OUTPUT_MODE_JSON

    def is_unambiguous_transport_failure(self) -> bool:
        """A timeout, network failure, or non-returning process — abort, no retry."""
        return self.timed_out or self.network_error or self.return_code is None


def classify_probe_disposition(
    result: ProbeInvocationResult,
    *,
    payload_parseable: bool,
    observation_schema_valid: bool,
) -> str:
    """Gate one probe result into one of the three fail-closed dispositions.

    (2) A transport/infrastructure failure with no interpretable platform signal
    (timeout, network failure, or a non-zero exit with no parseable error body)
    aborts the run and is NEVER recorded as "unavailable" (recording it would
    falsely narrow platform availability, FR-026).
    (1) Otherwise, an unparseable payload or a schema-invalid observation aborts
    the snapshot write (fail-closed — a silently-omitted tuple would break the
    SC-005 join).
    (3) Otherwise an interpretable platform observation — including an
    *undetermined* unavailable-probe outcome — is recorded and the snapshot is
    written (no availability claim derives from an undetermined observation).
    """
    if result.is_unambiguous_transport_failure():
        return DISPOSITION_ABORT_RUN
    if result.return_code != 0 and not payload_parseable:
        # Non-zero exit with no parseable error body — transport failure, not a
        # platform observation.
        return DISPOSITION_ABORT_RUN
    if not payload_parseable:
        return DISPOSITION_ABORT_WRITE
    if not observation_schema_valid:
        return DISPOSITION_ABORT_WRITE
    return DISPOSITION_RECORD


# -- Bounded-matrix driver + live-boundary seam ------------------------------

# The single live boundary. The pure logic never calls ``claude``; it drives the
# matrix through an injected invoker with the call signature
# ``invoke(planned, *, timeout_seconds) -> ProbeInvocationResult``. T011 supplies
# the real invoker (subprocess); tests supply a fake.
LiveInvoker = Callable[..., ProbeInvocationResult]


@dataclass(frozen=True)
class ProbeRun:
    """The outcome of a bounded matrix run: recorded probe metadata + results."""

    metadata: dict[str, Any]
    results: tuple[tuple[PlannedInvocation, ProbeInvocationResult], ...]


def build_probe_run_metadata(
    *,
    timeout_seconds: float,
    budget_ceiling: int = INVOCATION_BUDGET_CEILING,
    planned_invocations: int | None = None,
) -> dict[str, Any]:
    """Record the probe controls in snapshot probe metadata (FR-003).

    The explicit per-invocation timeout value is recorded here alongside the
    budget ceiling, the no-automatic-retries fact, and the fixed canary.
    """
    metadata: dict[str, Any] = {
        "per_invocation_timeout_seconds": timeout_seconds,
        "invocation_budget_ceiling": budget_ceiling,
        "automatic_retries": 0,
        "canary": canary_metadata(),
    }
    if planned_invocations is not None:
        metadata["planned_invocations"] = planned_invocations
    return metadata


def run_bounded_probe_matrix(
    planned: Iterable[PlannedInvocation],
    invoke: LiveInvoker,
    *,
    timeout_seconds: float,
    budget_ceiling: int = INVOCATION_BUDGET_CEILING,
) -> ProbeRun:
    """Drive the bounded matrix through the injected live ``invoke`` seam (FR-003).

    Pure orchestration — it never spawns a process itself:

    * the budget overrun is surfaced BEFORE any live call (raises
      :class:`BudgetOverrunError`);
    * every invocation is passed the explicit per-invocation ``timeout_seconds``,
      whose value is recorded in the returned probe metadata;
    * there are NO automatic retries — the first unambiguous transport failure
      raises :class:`ProbeRunAborted` and the operator reruns.
    """
    planned_invocations = tuple(planned)
    enforce_invocation_budget(len(planned_invocations), ceiling=budget_ceiling)
    metadata = build_probe_run_metadata(
        timeout_seconds=timeout_seconds,
        budget_ceiling=budget_ceiling,
        planned_invocations=len(planned_invocations),
    )
    results: list[tuple[PlannedInvocation, ProbeInvocationResult]] = []
    for item in planned_invocations:
        result = invoke(item, timeout_seconds=timeout_seconds)
        if result.is_unambiguous_transport_failure():
            raise ProbeRunAborted(
                f"live probe invocation {item.purpose!r} failed at the transport layer "
                "(timeout / network); no automatic retries — operator rerun required"
            )
        results.append((item, result))
    return ProbeRun(metadata=metadata, results=tuple(results))


__all__ = (
    "CANARY_TEXT",
    "CANARY_SHA256",
    "HOME_TOKEN",
    "SANITIZATION_MARKER",
    "NULL_EFFORT_TOKEN",
    "INVOCATION_BUDGET_CEILING",
    "PURPOSE_ALIAS_CANARY",
    "PURPOSE_CONFIG_ACCEPTANCE",
    "PURPOSE_UNAVAILABLE_PROBE",
    "UNAVAILABLE_SURFACES",
    "OUTPUT_MODE_JSON",
    "OUTPUT_MODE_PLAIN_TEXT",
    "DISPOSITION_ABORT_WRITE",
    "DISPOSITION_ABORT_RUN",
    "DISPOSITION_RECORD",
    "PROBE_DISPOSITIONS",
    "ClaudeCapabilitiesError",
    "BudgetOverrunError",
    "ProbeRunAborted",
    "TupleSpec",
    "ProbeMatrix",
    "PlannedInvocation",
    "ProbeInvocationResult",
    "ProbeRun",
    "LiveInvoker",
    "canary_metadata",
    "sanitize_home_paths",
    "payload_sha256",
    "derive_tuple_id",
    "build_probe_matrix",
    "plan_probe_invocations",
    "enforce_invocation_budget",
    "classify_probe_disposition",
    "build_probe_run_metadata",
    "run_bounded_probe_matrix",
)
