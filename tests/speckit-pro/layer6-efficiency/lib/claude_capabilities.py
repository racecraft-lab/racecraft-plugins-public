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

import argparse
import contextlib
import hashlib
import json
import os
import re
import subprocess
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
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
# Run-local session/request identifiers (the `--output-format json` payload's
# `session_id`/`uuid` values) carry no evidentiary value — alias→ID binding and
# config acceptance come from `modelUsage`, not the session ID — and the repo's
# tree-wide privacy scan redacts raw UUIDs, so they are normalized too.
SESSION_ID_TOKEN = "<session-id>"
SANITIZATION_MARKER = "home_paths_and_session_ids_normalized_utf8"

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
_HOME_SANITIZERS = (_PRIVATE_VAR_RE, _TMP_TRANSCRIPT_RE, _HOME_PATH_RE, _HYPHENATED_HOME_RE)
# Mirror the committed privacy-scan UUID rule verbatim
# (tests/speckit-pro/unit/test-privacy-scan.py `UUID_PATTERN`) so a sanitized
# payload can never leave a raw run-local session/request UUID in the snapshot.
_SESSION_UUID_RE = re.compile(
    r"[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}",
    re.IGNORECASE,
)


def sanitize_home_paths(text: str) -> str:
    """Normalize home/user paths, machine-local session paths, and run-local
    session/request UUIDs to fixed tokens (FR-012/FR-013).

    Deterministic and idempotent: every documented home/user path form
    (``/Users/<u>``, ``/home/<u>``, ``C:\\Users\\<u>``, hyphenated ``-Users-<u>``)
    and machine-local session path (macOS ``/private/var/folders`` temp trees and
    ``/private/tmp/claude-<n>`` session paths) collapses to ``<home>``, and every
    raw session/request UUID collapses to ``<session-id>`` (matching the repo's
    tree-wide privacy-scan UUID rule), so no unsanitized absolute path or raw
    run-local identifier can be committed.
    """
    sanitized = text
    for pattern in _HOME_SANITIZERS:
        sanitized = pattern.sub(HOME_TOKEN, sanitized)
    sanitized = _SESSION_UUID_RE.sub(SESSION_ID_TOKEN, sanitized)
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
    groups: dict[str, dict[str, Any]] = {}
    for route in routes:
        model = route["model_selector"]["requested_value"]
        effort = route["effort_selector"]["requested_value"]
        tuple_id = derive_tuple_id(model, effort)
        group = groups.get(tuple_id)
        if group is None:
            # dict insertion order is first-appearance order, so no parallel
            # order list is needed to preserve it.
            groups[tuple_id] = {"model": model, "effort": effort, "count": 1}
        else:
            group["count"] += 1
    specs = tuple(
        TupleSpec(
            tuple_id=tuple_id,
            model=group["model"],
            effort_requested=group["effort"],
            route_count=group["count"],
        )
        for tuple_id, group in groups.items()
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


# =============================================================================
# T011 — the SINGLE live ``claude`` boundary (subprocess) + operator CLI
# =============================================================================
# Everything below either builds an argument array (pure, offline-testable) or
# wraps ``subprocess.run`` (the one place a live ``claude`` process may spawn).
# The pure driver ``run_bounded_probe_matrix`` above never reaches it; only the
# operator ``main()`` wires the real :class:`LiveClaudeInvoker` in. Importing the
# module spawns nothing.

SCHEMA_VERSION = "1.0.0"

# The pinned CLI binary and the operator-run controls (FR-003/FR-011).
CLAUDE_BIN = "claude"
DEFAULT_TIMEOUT_SECONDS = 120.0
# A plausibly-unavailable dated model ID dispatched on both CAP-Q5 surfaces
# (an old major line the pinned client no longer resolves). Operator-overridable.
DEFAULT_UNAVAILABLE_MODEL_ID = "claude-opus-3-0"
# The throwaway subagent probe agent name (its file is generated and removed at
# probe time, never committed — R12/constitution I).
PROBE_AGENT_NAME = "car002-probe"
DEFAULT_AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
# The one canonical committed snapshot path, beside the CAR-001 manifest (FR-011).
SNAPSHOT_OUTPUT_PATH = REPO_ROOT / "docs" / "ai" / "research" / "claude-runtime-capability-snapshot.json"
# The corroborating (never alias-establishing) catalog endpoint, called ONLY in
# api_key mode (FR-014, research R7).
MODELS_ENDPOINT_URL = "https://api.anthropic.com/v1/models"

# alias → CAR-001 capability question (manifest CAP-Q1..Q4 bindings).
ALIAS_CAPABILITY_QUESTIONS = (
    ("opus", "CAP-Q1"),
    ("sonnet", "CAP-Q2"),
    ("haiku", "CAP-Q3"),
    ("fable", "CAP-Q4"),
)

# The subagent-surface ``inherit`` caveat threshold (research R13): ``inherit``
# equals unset only on this client version or later.
SUBAGENT_INHERIT_MIN_VERSION = "2.1.196"

# Documented-then-labeled dispatch-equivalence caveats (R6/R12; FR-026/FR-027).
DISPATCH_CAVEAT_PRINT_MODEL = (
    "Direct `-p --model` dispatch of an unavailable ID; the observed outcome path "
    "is a labeled observation, not a certified platform fact (FR-026/FR-027)."
)
DISPATCH_CAVEAT_SUBAGENT = (
    "File-based `.claude/agents` frontmatter dispatched via an @agent mention "
    "approximates but is not proven equivalent to the plugin-namespaced production "
    "Agent-tool routing; recorded as labeled inference (research R12)."
)

# The CAP-Q6 route-change detection rule, left open in the bounded matrix (R11).
CAPQ6_DETECTION_NOTE = (
    "Alias re-pointing (CAP-Q6) is a route-change detection rule over "
    "observed-versus-resolved model IDs, left open in the bounded matrix: inducing "
    "re-pointing requires an ANTHROPIC_DEFAULT_<MODEL>_MODEL override that "
    "structurally collides with the FR-010 unset-proof (research R11)."
)

# Plain-text ``--print`` clamp-warning markers (research R6). Their presence names
# an applied effort below the requested one; absence is observed acceptance.
_EFFORT_CLAMP_MARKERS = ("clamp", "capped", "lowered", "reduced to", "limited to", "downgraded")


class ProbeWriteAborted(ClaudeCapabilitiesError):
    """A schema-invalid observation aborts the snapshot write — nothing is committed (FR-023/SC-004)."""


@dataclass(frozen=True)
class ProbeCommand:
    """One resolved live-invocation command: the exact ``claude`` argument array,
    the prompt, and the output mode the pure classifier will read."""

    argv: tuple[str, ...]
    prompt: str
    output_mode: str


def build_probe_command(
    planned: PlannedInvocation,
    *,
    unavailable_model_id: str = DEFAULT_UNAVAILABLE_MODEL_ID,
    agent_name: str = PROBE_AGENT_NAME,
    canary_text: str = CANARY_TEXT,
) -> ProbeCommand:
    """Build the ``claude`` argument array for one planned invocation (pure).

    * alias canary — ``-p <canary> --output-format json --model <alias>`` (reads
      the resolved dated ID from ``modelUsage``, CAP-Q1..Q4);
    * config acceptance — plain-text ``-p`` with ``--model``/``--effort`` (which
      warns on a clamp rather than clamping silently under JSON output, R6);
    * unavailable ``print_model`` — ``-p <canary> --output-format json --model
      <unavailable-id>``;
    * unavailable ``subagent_frontmatter`` — a fresh, non-``--bare`` ``-p`` with an
      explicit ``@agent-<name>`` mention and **no** per-invocation ``--model`` (a
      per-call model would preempt the frontmatter value under test, R4/R12).

    No command ever passes ``--fallback-model`` (the FR-010 unset-proof is
    structural on this surface).
    """
    if planned.purpose == PURPOSE_ALIAS_CANARY:
        argv = [CLAUDE_BIN, "-p", canary_text, "--output-format", "json", "--model", str(planned.model_alias)]
        return ProbeCommand(argv=tuple(argv), prompt=canary_text, output_mode=OUTPUT_MODE_JSON)
    if planned.purpose == PURPOSE_CONFIG_ACCEPTANCE:
        argv = [CLAUDE_BIN, "-p", canary_text, "--model", str(planned.model_alias)]
        if planned.effort_requested is not None:
            argv += ["--effort", str(planned.effort_requested)]
        return ProbeCommand(argv=tuple(argv), prompt=canary_text, output_mode=OUTPUT_MODE_PLAIN_TEXT)
    if planned.purpose == PURPOSE_UNAVAILABLE_PROBE:
        if planned.surface == "subagent_frontmatter":
            prompt = f"@agent-{agent_name} {canary_text}"
            argv = [CLAUDE_BIN, "-p", prompt, "--output-format", "json"]
            return ProbeCommand(argv=tuple(argv), prompt=prompt, output_mode=OUTPUT_MODE_JSON)
        argv = [CLAUDE_BIN, "-p", canary_text, "--output-format", "json", "--model", str(unavailable_model_id)]
        return ProbeCommand(argv=tuple(argv), prompt=canary_text, output_mode=OUTPUT_MODE_JSON)
    raise ClaudeCapabilitiesError(f"unknown probe purpose {planned.purpose!r}")


def invoke_claude_cli(command: ProbeCommand, *, timeout_seconds: float) -> ProbeInvocationResult:
    """The ONE path permitted to spawn a live ``claude`` process (FR-001).

    ``subprocess.run`` with an argument array, ``shell=False``, ``text=True`` UTF-8
    capture, an explicit per-invocation timeout, and explicit return-code handling
    (constitution II). A timeout or an un-spawnable binary is mapped to a
    non-returning transport failure (``return_code is None``) — never a platform
    observation, so it can never be misread as "unavailable" (FR-026). Tests reach
    this only with ``subprocess.run`` monkeypatched, so no live call ever occurs.
    """
    try:
        # argv[0] MUST be the ``"claude"`` string literal (not the ``CLAUDE_BIN``
        # constant, which a module-level Name does not statically resolve to inside
        # this function) so the XPLAT-010 repository Bash-confinement guard can prove
        # the executable is a non-Bash literal — the same literal-command idiom the
        # shipped ``read_only.py`` uses (``["git", ...]``). ``CLAUDE_BIN == "claude"``
        # and ``command.argv[0] == CLAUDE_BIN``, so this equals ``list(command.argv)``
        # at runtime; the dynamic probe args follow.
        completed = subprocess.run(
            ["claude", *command.argv[1:]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            shell=False,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return ProbeInvocationResult(return_code=None, timed_out=True, output_mode=command.output_mode)
    except OSError:
        # e.g. the pinned ``claude`` binary is not on PATH — a transport failure,
        # not a platform observation.
        return ProbeInvocationResult(return_code=None, network_error=True, output_mode=command.output_mode)
    return ProbeInvocationResult(
        return_code=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        output_mode=command.output_mode,
    )


# =============================================================================
# T014 — the FR-009 subagent-frontmatter dispatch mechanism (research R12)
# =============================================================================


def build_probe_agent_markdown(agent_name: str, model_id: str, *, canary_text: str = CANARY_TEXT) -> str:
    """The throwaway probe agent file: YAML frontmatter naming the unavailable
    dated model ID (research R12). Generated at probe time, never committed."""
    return (
        "---\n"
        f"name: {agent_name}\n"
        "description: >-\n"
        "  CAR-002 throwaway unavailable-model probe agent, generated at probe time\n"
        "  and removed on every exit path. Uncommitted; not a shipped agent.\n"
        f"model: {model_id}\n"
        "---\n\n"
        f"{canary_text}\n"
    )


@contextlib.contextmanager
def staged_probe_agent(
    agents_dir: Path | str,
    agent_name: str,
    model_id: str,
    *,
    canary_text: str = CANARY_TEXT,
) -> Iterator[Path]:
    """Stage the throwaway ``.claude/agents/<name>.md`` for the dispatch, then
    remove it on **every** exit path — success, abort, or timeout (try/finally) —
    so an aborted run leaves no probe residue (spec Assumptions CAP-Q5)."""
    directory = Path(agents_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{agent_name}.md"
    path.write_text(build_probe_agent_markdown(agent_name, model_id, canary_text=canary_text), encoding="utf-8")
    try:
        yield path
    finally:
        # Idempotent cleanup: a missing file is expected and benign (the dispatch
        # may have already removed it, or an early abort ran before the write).
        with contextlib.suppress(FileNotFoundError):
            path.unlink()


class LiveClaudeInvoker:
    """The real ``LiveInvoker`` wired into :func:`run_bounded_probe_matrix` by the
    operator ``main()`` only. Builds each command, stages/removes the throwaway
    probe agent for the subagent surface (T014), and calls the single subprocess
    boundary. Construction spawns nothing."""

    def __init__(
        self,
        *,
        unavailable_model_id: str = DEFAULT_UNAVAILABLE_MODEL_ID,
        agent_name: str = PROBE_AGENT_NAME,
        agents_dir: Path | str | None = None,
        canary_text: str = CANARY_TEXT,
    ) -> None:
        self.unavailable_model_id = unavailable_model_id
        self.agent_name = agent_name
        self.agents_dir = Path(agents_dir) if agents_dir is not None else DEFAULT_AGENTS_DIR
        self.canary_text = canary_text

    def __call__(self, planned: PlannedInvocation, *, timeout_seconds: float) -> ProbeInvocationResult:
        command = build_probe_command(
            planned,
            unavailable_model_id=self.unavailable_model_id,
            agent_name=self.agent_name,
            canary_text=self.canary_text,
        )
        if planned.purpose == PURPOSE_UNAVAILABLE_PROBE and planned.surface == "subagent_frontmatter":
            with staged_probe_agent(
                self.agents_dir, self.agent_name, self.unavailable_model_id, canary_text=self.canary_text
            ):
                return invoke_claude_cli(command, timeout_seconds=timeout_seconds)
        return invoke_claude_cli(command, timeout_seconds=timeout_seconds)


# =============================================================================
# T012 — capability-answer + evidence-capture logic (pure given probe results)
# =============================================================================


def detect_authentication_mode(env: Mapping[str, str]) -> str:
    """``api_key`` when ``ANTHROPIC_API_KEY``/``ANTHROPIC_AUTH_TOKEN`` is present,
    else ``subscription`` (documented signals; FR-014, research R7)."""
    if env.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_AUTH_TOKEN"):
        return "api_key"
    return "subscription"


def _client_version_ge(version: str | None, target: str) -> bool:
    def parts(value: str) -> list[int]:
        out: list[int] = []
        for chunk in str(value).split("."):
            digits = "".join(ch for ch in chunk if ch.isdigit())
            out.append(int(digits) if digits else 0)
        return out

    left, right = parts(version or "0"), parts(target)
    width = max(len(left), len(right))
    left += [0] * (width - len(left))
    right += [0] * (width - len(right))
    return left >= right


def build_unset_proof(
    *,
    env: Mapping[str, str],
    settings: Mapping[str, Any] | None = None,
    client_version: str | None = None,
    config_dir_isolation: str = "none",
    probe_argvs: Iterable[Iterable[str]] | None = None,
) -> dict[str, Any]:
    """The FR-010 unset-proof, drawn from the actual operator environment (research R13).

    Proves ``--fallback-model``/``fallbackModel``, ``CLAUDE_CODE_SUBAGENT_MODEL``,
    and ``availableModels`` (absent, not an empty list) are unset. ``enforce`` is
    recorded for audit (inert when ``availableModels`` is unset); the ``inherit``
    caveat is version-gated (``inherit`` == unset only on client >= v2.1.196).

    ``--fallback-model`` and ``fallbackModel`` are two distinct surfaces and are
    proven from distinct sources: ``fallback_model_unset`` reflects the actual
    probe-invocation argv (the ``--fallback-model`` CLI flag), while
    ``fallbackModel_unset`` reflects the resolved settings key. When ``probe_argvs``
    is omitted the CLI-flag proof defaults to true because the probe's own command
    builder never emits ``--fallback-model`` on any surface (see
    :func:`build_probe_command`).
    """
    settings = settings or {}
    if probe_argvs is None:
        cli_fallback_model_unset = True
    else:
        cli_fallback_model_unset = not any(
            "--fallback-model" in tuple(argv) for argv in probe_argvs
        )
    subagent_model = env.get("CLAUDE_CODE_SUBAGENT_MODEL")
    inherit_caveat: str | None = None
    if not subagent_model:
        subagent_unset = True
    elif subagent_model == "inherit":
        subagent_unset = _client_version_ge(client_version, SUBAGENT_INHERIT_MIN_VERSION)
        inherit_caveat = (
            f"CLAUDE_CODE_SUBAGENT_MODEL=inherit equals unset only on client "
            f">= v{SUBAGENT_INHERIT_MIN_VERSION}; recorded client version "
            f"{client_version or 'unknown'} (research R13)."
        )
    else:
        subagent_unset = False
    enforce = settings.get("enforceAvailableModels")
    return {
        "fallback_model_unset": cli_fallback_model_unset,
        "fallbackModel_unset": "fallbackModel" not in settings,
        "claude_code_subagent_model_unset": subagent_unset,
        "available_models_absent": "availableModels" not in settings,
        "enforce_available_models_observed": None if enforce is None else str(enforce),
        "config_dir_isolation": config_dir_isolation,
        "inherit_equivalent_to_unset": inherit_caveat,
        "org_restriction_gap": None,
    }


def parse_result_payload(raw_stdout: str) -> dict[str, Any] | None:
    """Parse a ``--output-format json`` payload; ``None`` when unparseable/non-object."""
    try:
        parsed = json.loads(raw_stdout)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def primary_model_id(payload: dict[str, Any] | None) -> str | None:
    """The effective dated model ID = the ``modelUsage`` key (there is no scalar
    ``model`` field; research R3). ``None`` when absent."""
    if not isinstance(payload, dict):
        return None
    usage = payload.get("modelUsage")
    if isinstance(usage, dict):
        return next(iter(usage), None)
    return None


def cross_check_remap(requested_id: str, observed_model_id: str | None) -> bool:
    """True when the observed model differs from the requested ID — the
    requested-vs-observed cross-check that flags a soft remap / fallback (R4)."""
    return observed_model_id is not None and observed_model_id != requested_id


def _evidence_text(result: ProbeInvocationResult) -> str:
    """The raw payload to store as evidence: stdout, else stderr, else a marker
    (``rawEvidence.raw_output`` requires ``minLength: 1``)."""
    return result.stdout or result.stderr or "(no probe output captured)"


def build_raw_evidence(raw_text: str) -> dict[str, str]:
    """Sanitize to ``<home>`` first, then hash the exact sanitized UTF-8 bytes and
    store the payload verbatim (FR-012/FR-013; research R9)."""
    sanitized = sanitize_home_paths(raw_text or "")
    return {
        "raw_output": sanitized,
        "raw_output_sha256": payload_sha256(sanitized),
        "sanitization": SANITIZATION_MARKER,
    }


def build_alias_binding(alias: str, tuple_id: str, result: ProbeInvocationResult) -> dict[str, Any]:
    """One alias→dated-ID binding from its canary ``modelUsage`` (CAP-Q1..Q4, FR-006)."""
    payload = parse_result_payload(result.stdout)
    return {
        "alias": alias,
        "resolved_dated_model_id": primary_model_id(payload),
        "tuple_id": tuple_id,
        "raw_evidence": build_raw_evidence(_evidence_text(result)),
    }


def classify_effort_acceptance(result: ProbeInvocationResult) -> tuple[str, str]:
    """(``effort_acceptance``, ``effort_probe_output_mode``) as a labeled observation,
    never certification (research R6).

    Plain-text ``--print`` warns on a clamp: a clamp marker ⇒ ``clamped``; a
    non-zero exit ⇒ ``rejected``; otherwise the observed ⇒ ``accepted``. Under
    JSON output the org cap clamps silently, so acceptance is ``observation_only``
    with the ``json_no_org_cap_assumed`` mode recorded.
    """
    if result.output_mode == OUTPUT_MODE_PLAIN_TEXT:
        if result.return_code != 0:
            return ("rejected", "plain_text_print")
        text = (result.stdout or "").lower()
        if any(marker in text for marker in _EFFORT_CLAMP_MARKERS):
            return ("clamped", "plain_text_print")
        return ("accepted", "plain_text_print")
    return ("observation_only", "json_no_org_cap_assumed")


def dispatch_equivalence_caveat(surface: str) -> str:
    """The per-surface labeled-inference caveat (R12)."""
    return DISPATCH_CAVEAT_SUBAGENT if surface == "subagent_frontmatter" else DISPATCH_CAVEAT_PRINT_MODEL


def classify_unavailable_outcome(
    result: ProbeInvocationResult, *, requested_id: str, observed_model_id: str | None
) -> str:
    """Classify the ``print_model`` unavailable-model outcome among the documented
    paths (R4/R12).

    Reads the DIRECT ``-p --model <unavailable-id>`` result, whose ``modelUsage``
    is the requested dispatch's own result: a non-zero exit carrying an error body
    ⇒ ``hard_rejection``; a zero exit whose observed model differs from the
    requested unavailable ID ⇒ ``soft_remap``; otherwise ``undetermined`` (no
    availability claim derives from it — CAP-Q5 stays open).

    This is NOT valid on the ``subagent_frontmatter`` surface, whose top-level
    result is the PARENT session that narrated the dispatch (its ``modelUsage`` is
    the parent's model, not the subagent's) — use
    :func:`classify_subagent_unavailable_outcome` there.
    """
    if result.return_code not in (0, None) and (result.stdout or result.stderr):
        return "hard_rejection"
    if result.return_code == 0 and observed_model_id is not None and observed_model_id != requested_id:
        return "soft_remap"
    return "undetermined"


# Documented access/existence error phrases that, co-occurring with the
# requested-unavailable model id in a narrated result, evidence a terminal
# model-access rejection at the subagent boundary — the parent `-p` session
# narrates the subagent's spawn-time failure while itself exiting 0 on the
# parent's own model. Kept deterministic; the subagent-surface reading is labeled
# inference, not certified fact (FR-027).
_MODEL_ACCESS_ERROR_MARKERS = (
    "doesn't exist",
    "does not exist",
    "isn't accessible",
    "is not accessible",
    "not accessible",
    "may not have access",
    "don't have access",
    "do not have access",
    "no access to it",
    "api error",
    "model-access error",
    "model access error",
)


def _signals_terminal_model_access_error(
    payload: dict[str, Any] | None, result: ProbeInvocationResult, requested_id: str
) -> bool:
    """True when the result evidences a terminal model-access rejection of
    ``requested_id`` (the requested-unavailable model never ran).

    Three deterministic signals: a non-zero exit carrying an error body (a
    print_model-style direct rejection, or a parent that itself exits non-zero
    with a body); a structured top-level ``is_error``/``api_error_status``; or a
    narrated model-access error — the requested-unavailable id co-occurring with a
    documented access/existence error phrase in the result text (the subagent
    parent narrates the subagent's spawn-time failure while exiting 0).
    """
    if result.return_code not in (0, None) and (result.stdout or result.stderr):
        return True
    if isinstance(payload, dict):
        if payload.get("is_error") is True:
            return True
        if payload.get("api_error_status") not in (None, "", False):
            return True
    text = ((result.stdout or "") + "\n" + (result.stderr or "")).lower()
    return requested_id.lower() in text and any(
        marker in text for marker in _MODEL_ACCESS_ERROR_MARKERS
    )


def classify_subagent_unavailable_outcome(
    result: ProbeInvocationResult,
    *,
    requested_id: str,
    payload: dict[str, Any] | None = None,
    subagent_observed_model_id: str | None = None,
) -> tuple[str, str | None]:
    """Classify the ``subagent_frontmatter`` unavailable outcome (labeled inference).

    Returns ``(observed_outcome, observed_model_id)``.

    On this surface the top-level ``--output-format json`` result describes the
    PARENT ``-p`` session that dispatched the subagent via an ``@agent-<name>``
    mention and narrated the outcome; its ``modelUsage`` is the PARENT's model and
    MUST NOT be read as the subagent's observed model (FR-026/FR-027; the false
    remap this once produced is root-cause LOW-2). So:

    * a terminal model-access error for the requested-unavailable id at the
      subagent boundary means the subagent never ran ⇒ ``("hard_rejection", None)``;
    * a genuine substitution is asserted ONLY from the subagent's OWN observed
      model (never the parent's top-level ``modelUsage``); when that
      subagent-scoped model is present and differs from the requested id ⇒
      ``("soft_remap", <subagent model>)``;
    * otherwise the parent narration does not determine the subagent outcome ⇒
      ``("undetermined", None)`` (no availability claim derives from it; CAP-Q5
      stays open).
    """
    if payload is None:
        payload = parse_result_payload(result.stdout)
    if _signals_terminal_model_access_error(payload, result, requested_id):
        return "hard_rejection", None
    if subagent_observed_model_id is not None and subagent_observed_model_id != requested_id:
        return "soft_remap", subagent_observed_model_id
    return "undetermined", None


def build_unavailable_observation(
    *,
    surface: str,
    requested_unavailable_model_id: str,
    result: ProbeInvocationResult,
    unset_proof: dict[str, Any],
) -> dict[str, Any]:
    """One per-surface unavailable-model observation with the requested-vs-observed
    cross-check and the FR-010 unset-proof (CAP-Q5, FR-009/FR-010).

    The ``print_model`` surface reads the direct ``-p --model <id>`` result, whose
    ``modelUsage`` is the requested dispatch's own result. The
    ``subagent_frontmatter`` surface's top-level result is instead the PARENT
    session that narrated the dispatch, so its ``modelUsage`` is the parent's model
    and is NEVER read as the subagent's observed model (root-cause LOW-2): its
    outcome is derived from the dispatch signal and it carries no subagent-scoped
    observed model here, so the assemble flow records only ``hard_rejection`` or
    ``undetermined`` — never a parent-model soft remap.
    """
    payload = parse_result_payload(result.stdout)
    if surface == "subagent_frontmatter":
        observed_outcome, observed = classify_subagent_unavailable_outcome(
            result, requested_id=requested_unavailable_model_id, payload=payload
        )
    else:
        observed = primary_model_id(payload)
        observed_outcome = classify_unavailable_outcome(
            result, requested_id=requested_unavailable_model_id, observed_model_id=observed
        )
    return {
        "surface": surface,
        "requested_unavailable_model_id": requested_unavailable_model_id,
        "observed_outcome": observed_outcome,
        "observed_model_id": observed,
        "unset_proof": unset_proof,
        "remap_flagged": cross_check_remap(requested_unavailable_model_id, observed),
        "dispatch_equivalence_caveat": dispatch_equivalence_caveat(surface),
        "raw_evidence": build_raw_evidence(_evidence_text(result)),
    }


@dataclass(frozen=True)
class ModelsEndpointResult:
    """The api_key-mode corroborating catalog (``evidence``) and/or the recorded
    ``gap`` when it is not applicable/unreachable (FR-014, research R7)."""

    evidence: dict[str, Any] | None
    gap: dict[str, Any] | None


def _default_models_fetch(env: Mapping[str, str]) -> dict[str, Any]:  # pragma: no cover - live network boundary
    """GET ``/v1/models`` via ``urllib`` (stdlib). The single network boundary,
    reached only in api_key mode during a real operator run; tests inject a fake."""
    import urllib.request

    api_key = env.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_AUTH_TOKEN") or ""
    request = urllib.request.Request(
        MODELS_ENDPOINT_URL,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed https endpoint
        return json.loads(response.read().decode("utf-8"))


def corroborate_models_endpoint(
    authentication_mode: str,
    *,
    fetch: Callable[[Mapping[str, str]], dict[str, Any]] | None = None,
    env: Mapping[str, str] | None = None,
) -> ModelsEndpointResult:
    """Call ``GET /v1/models`` ONLY in api_key mode; store the catalog as
    corroborating (never alias-establishing) evidence, else record a gap (FR-014,
    research R7). An unreachable endpoint is a recorded gap, never a run failure.
    """
    if authentication_mode != "api_key":
        return ModelsEndpointResult(
            evidence=None,
            gap={
                "subject": "models_endpoint",
                "reason": (
                    "GET /v1/models is called only in api_key mode; under subscription auth its "
                    "catalog corroboration is unavailable and recorded as a gap (research R7)."
                ),
                "disposition": "gap",
            },
        )
    fetcher = fetch or _default_models_fetch
    try:
        catalog = fetcher(env or {})
    except Exception as exc:  # noqa: BLE001 - unreachable endpoint is a recorded gap, never a failure
        return ModelsEndpointResult(
            evidence={
                "access_status": "unreachable",
                "dated_model_ids": [],
                "per_model_effort_flags": {},
                "note": (
                    f"GET /v1/models unreachable in api_key mode: {type(exc).__name__} "
                    "(recorded gap, not a run failure; research R7)."
                ),
            },
            gap=None,
        )
    data = catalog.get("data", []) if isinstance(catalog, dict) else []
    dated_model_ids = [entry.get("id") for entry in data if isinstance(entry, dict) and entry.get("id")]
    return ModelsEndpointResult(
        evidence={
            "access_status": "accessible",
            "dated_model_ids": dated_model_ids,
            "per_model_effort_flags": {},
            "note": (
                "GET /v1/models corroboration in api_key mode; API-catalog presence corroborates, "
                "never establishes, coding-client availability (FR-026/research R7)."
            ),
        },
        gap=None,
    )


def build_snapshot_id(captured_at_utc: str, version: int) -> str:
    """``CAR-002-RCS-<YYYY-MM-DD>-V<n>`` with the date drawn from the capture
    timestamp, so the identity cannot silently disagree with it (FR-011)."""
    return f"CAR-002-RCS-{str(captured_at_utc)[:10]}-V{int(version)}"


def build_capability_answers(
    alias_bindings: list[dict[str, Any]], unavailable_observations: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """One ``capabilityAnswer`` per CAP-Q1..Q6 (FR-007). CAP-Q1..Q4 = the alias
    bindings; CAP-Q5 = the unavailable-model observations (labeled inference,
    open when every outcome is undetermined); CAP-Q6 = the route-change detection
    rule, always open (R11)."""
    by_alias = {binding["alias"]: binding for binding in alias_bindings}
    answers: list[dict[str, Any]] = []
    for alias, question_id in ALIAS_CAPABILITY_QUESTIONS:
        binding = by_alias.get(alias)
        resolved = binding["resolved_dated_model_id"] if binding else None
        answers.append(
            {
                "capability_question_id": question_id,
                "status": "answered" if (binding is not None and resolved is not None) else "open",
                "answer": resolved,
                "evidence_refs": [binding["tuple_id"]] if binding else [],
                "label": "observation",
            }
        )
    q5_answered = any(obs["observed_outcome"] != "undetermined" for obs in unavailable_observations)
    q5_answer = "; ".join(
        f"{obs['surface']}:{obs['observed_outcome']}" for obs in unavailable_observations
    ) or None
    answers.append(
        {
            "capability_question_id": "CAP-Q5",
            "status": "answered" if q5_answered else "open",
            "answer": q5_answer,
            "evidence_refs": [obs["surface"] for obs in unavailable_observations],
            "label": "labeled_inference",
        }
    )
    answers.append(
        {
            "capability_question_id": "CAP-Q6",
            "status": "open",
            "answer": CAPQ6_DETECTION_NOTE,
            "evidence_refs": [],
            "label": "labeled_inference",
        }
    )
    return answers


def build_open_gaps(models_endpoint: ModelsEndpointResult | None = None) -> list[dict[str, Any]]:
    """Explicit open/gap entries for bounded-matrix-unanswerable questions: the
    CAP-Q6 detection rule (open) plus any recorded models-endpoint gap (FR-007/FR-027)."""
    gaps: list[dict[str, Any]] = [
        {"subject": "CAP-Q6 alias re-pointing", "reason": CAPQ6_DETECTION_NOTE, "disposition": "open"}
    ]
    if models_endpoint is not None and models_endpoint.gap is not None:
        gaps.append(models_endpoint.gap)
    return gaps


def gate_probe_run_dispositions(probe_run: ProbeRun) -> None:
    """Enforce the three fail-closed dispositions over every probe result BEFORE a
    snapshot is assembled or written (FR-023; spec "Malformed probe payload" /
    "Partial probe matrix").

    Each result is classified through :func:`classify_probe_disposition`:

    * disposition (1) ``abort_write`` — a ``--output-format json`` payload that
      does not parse — raises :class:`ProbeWriteAborted` so no snapshot file is
      written or overwritten (a silently-omitted tuple would break the SC-005
      join);
    * disposition (2) ``abort_run`` — a transport failure with no interpretable
      signal (a non-zero exit with no parseable error body; the driver already
      catches timeout/network) — raises :class:`ProbeRunAborted` and is NEVER
      recorded as "unavailable" (FR-026);
    * disposition (3) ``record`` — any interpretable observation (including a
      null/absent field or an undetermined outcome). A plain-text ``--print``
      observation is always interpretable by :func:`classify_effort_acceptance`,
      so JSON parseability is not required of it.
    """
    for planned, result in probe_run.results:
        if result.output_mode == OUTPUT_MODE_JSON:
            payload_parseable = parse_result_payload(result.stdout) is not None
        else:
            payload_parseable = True
        disposition = classify_probe_disposition(
            result, payload_parseable=payload_parseable, observation_schema_valid=True
        )
        if disposition == DISPOSITION_ABORT_RUN:
            raise ProbeRunAborted(
                f"probe invocation {planned.purpose!r} is a transport failure with no "
                "interpretable platform signal; run aborted, nothing committed — no "
                "automatic retries (FR-003/FR-026)."
            )
        if disposition == DISPOSITION_ABORT_WRITE:
            raise ProbeWriteAborted(
                f"probe invocation {planned.purpose!r} returned an unparseable "
                "`--output-format json` payload; snapshot write aborted, nothing "
                "committed (fail-closed, FR-023/SC-004)."
            )


def assemble_runtime_capability_snapshot(
    probe_run: ProbeRun,
    *,
    captured_at_utc: str,
    version: int,
    pinned_client_version: str,
    authentication_mode: str,
    unset_proof: dict[str, Any],
    unavailable_model_id: str,
    models_endpoint: ModelsEndpointResult | None = None,
) -> dict[str, Any]:
    """Assemble a schema-shaped ``runtimeCapabilitySnapshot`` from a bounded probe
    run plus the environment-derived facts (CAP-Q1..Q6; FR-006..FR-014). The
    result validates against the ``runtimeCapabilitySnapshot`` ``$def`` via the
    fail-closed writer (T009's dispositions). Pure given the probe results.

    Fail-closed: every probe result is first gated through the three dispositions
    (:func:`gate_probe_run_dispositions`), so an unparseable ``--output-format
    json`` payload aborts the write BEFORE any snapshot is built or committed —
    it never degrades to a schema-valid null binding (FR-023).
    """
    gate_probe_run_dispositions(probe_run)
    canaries = [(p, r) for p, r in probe_run.results if p.purpose == PURPOSE_ALIAS_CANARY]
    configs = [(p, r) for p, r in probe_run.results if p.purpose == PURPOSE_CONFIG_ACCEPTANCE]
    unavailable = [(p, r) for p, r in probe_run.results if p.purpose == PURPOSE_UNAVAILABLE_PROBE]

    resolved_by_model = {
        planned.model_alias: primary_model_id(parse_result_payload(result.stdout))
        for planned, result in canaries
    }

    tuple_evidence: list[dict[str, Any]] = []
    primary_tuple_by_model: dict[str, str] = {}
    for planned, result in configs:
        acceptance, output_mode = classify_effort_acceptance(result)
        model = planned.model_alias
        tuple_evidence.append(
            {
                "tuple_id": planned.tuple_id,
                "model_requested": model,
                "effort_requested": planned.effort_requested,
                "resolved_dated_model_id": resolved_by_model.get(model),
                "effort_acceptance": acceptance,
                "effort_probe_output_mode": output_mode,
                "raw_evidence": build_raw_evidence(_evidence_text(result)),
            }
        )
        if model is not None:
            primary_tuple_by_model.setdefault(model, planned.tuple_id)

    alias_bindings = [
        build_alias_binding(
            planned.model_alias,
            primary_tuple_by_model.get(planned.model_alias) or derive_tuple_id(planned.model_alias, None),
            result,
        )
        for planned, result in canaries
    ]

    unavailable_observations = [
        build_unavailable_observation(
            surface=planned.surface,
            requested_unavailable_model_id=unavailable_model_id,
            result=result,
            unset_proof=unset_proof,
        )
        for planned, result in unavailable
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "runtime_capability_snapshot_id": build_snapshot_id(captured_at_utc, version),
        "captured_at_utc": captured_at_utc,
        "pinned_client_version": pinned_client_version,
        "authentication_mode": authentication_mode,
        "canary": canary_metadata(),
        "tuple_evidence": tuple_evidence,
        "alias_bindings": alias_bindings,
        "unavailable_observations": unavailable_observations,
        "models_endpoint_evidence": models_endpoint.evidence if models_endpoint is not None else None,
        "capability_answers": build_capability_answers(alias_bindings, unavailable_observations),
        "open_gaps": build_open_gaps(models_endpoint),
    }


def write_snapshot_fail_closed(
    snapshot: dict[str, Any],
    path: Path | str,
    *,
    validate: Callable[[dict[str, Any]], Any] | None = None,
) -> str:
    """Validate against the schema BEFORE writing; any invalid observation aborts
    the write and commits nothing (fail-closed, FR-023/SC-004). Returns
    :data:`DISPOSITION_RECORD` on a committed write."""
    if validate is None:  # lazy import so importing this module has no schema dependency
        from claude_trace_schema import validate_runtime_capability_snapshot as validate  # type: ignore[no-redef]
    try:
        validate(snapshot)
    except Exception as exc:  # noqa: BLE001 - any validation failure is fail-closed
        raise ProbeWriteAborted(
            "snapshot failed schema validation; write aborted, nothing committed "
            f"(FR-023/SC-004): {exc}"
        ) from exc
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return DISPOSITION_RECORD


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_arg_parser() -> argparse.ArgumentParser:
    """The operator CLI (quickstart Part A). Stdlib ``argparse`` only."""
    parser = argparse.ArgumentParser(
        prog="claude_capabilities",
        description=(
            "CAR-002 operator capability probe (quickstart Part A). The single operator-invoked "
            "entrypoint permitted to make live `claude` calls (FR-001); never run by CI or tests."
        ),
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS,
        help="explicit per-invocation timeout in seconds (FR-003)",
    )
    parser.add_argument(
        "--unavailable-model-id", default=DEFAULT_UNAVAILABLE_MODEL_ID,
        help="the unavailable dated model ID dispatched on both CAP-Q5 surfaces",
    )
    parser.add_argument(
        "--pinned-client-version", default=None,
        help="the pinned `claude` CLI version this snapshot scopes (FR-018)",
    )
    parser.add_argument(
        "--output", type=Path, default=SNAPSHOT_OUTPUT_PATH,
        help="canonical committed snapshot output path (FR-011)",
    )
    parser.add_argument(
        "--version-number", type=int, default=1,
        help="the V<n> suffix for the snapshot ID; bump monotonically on re-probe (FR-011)",
    )
    parser.add_argument(
        "--agents-dir", type=Path, default=None,
        help="directory for the throwaway subagent probe file (defaults to <repo>/.claude/agents)",
    )
    parser.add_argument(
        "--config-dir-isolation", choices=("none", "partial_defense_in_depth"), default="none",
        help="records whether an isolated CLAUDE_CONFIG_DIR was layered in (defense-in-depth only, R13)",
    )
    return parser


def main(argv: list[str] | None = None, *, env: Mapping[str, str] | None = None) -> int:
    """Operator entrypoint (quickstart Part A) — the ONLY place the real live
    invoker is wired into :func:`run_bounded_probe_matrix`. Runs the bounded
    matrix, assembles the snapshot, and fail-closed writes it. Never invoked by a
    test with a live ``claude`` on PATH.
    """
    args = build_arg_parser().parse_args(argv)
    environment = dict(os.environ if env is None else env)

    authentication_mode = detect_authentication_mode(environment)
    matrix = build_probe_matrix()
    plan = plan_probe_invocations(matrix)
    enforce_invocation_budget(len(plan))

    invoker = LiveClaudeInvoker(
        unavailable_model_id=args.unavailable_model_id,
        agents_dir=args.agents_dir,
    )
    probe_run = run_bounded_probe_matrix(plan, invoker, timeout_seconds=args.timeout)

    models_endpoint = corroborate_models_endpoint(authentication_mode, env=environment)
    # The exact argvs the probe actually ran, so the --fallback-model CLI-flag
    # proof reflects the real invocations (distinct from the fallbackModel setting).
    probe_argvs = [
        build_probe_command(planned, unavailable_model_id=args.unavailable_model_id).argv
        for planned, _ in probe_run.results
    ]
    unset_proof = build_unset_proof(
        env=environment,
        settings={},
        client_version=args.pinned_client_version,
        config_dir_isolation=args.config_dir_isolation,
        probe_argvs=probe_argvs,
    )
    snapshot = assemble_runtime_capability_snapshot(
        probe_run,
        captured_at_utc=_utc_now_z(),
        version=args.version_number,
        pinned_client_version=args.pinned_client_version or "unknown",
        authentication_mode=authentication_mode,
        unset_proof=unset_proof,
        unavailable_model_id=args.unavailable_model_id,
        models_endpoint=models_endpoint,
    )
    write_snapshot_fail_closed(snapshot, args.output)
    return 0


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
    # T011 — live boundary + operator CLI
    "SCHEMA_VERSION",
    "CLAUDE_BIN",
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_UNAVAILABLE_MODEL_ID",
    "PROBE_AGENT_NAME",
    "DEFAULT_AGENTS_DIR",
    "SNAPSHOT_OUTPUT_PATH",
    "MODELS_ENDPOINT_URL",
    "ProbeCommand",
    "ProbeWriteAborted",
    "build_probe_command",
    "invoke_claude_cli",
    "LiveClaudeInvoker",
    "build_arg_parser",
    "main",
    # T014 — subagent-frontmatter dispatch
    "build_probe_agent_markdown",
    "staged_probe_agent",
    # T012 — capability answers + evidence capture
    "detect_authentication_mode",
    "build_unset_proof",
    "parse_result_payload",
    "primary_model_id",
    "cross_check_remap",
    "build_raw_evidence",
    "build_alias_binding",
    "classify_effort_acceptance",
    "dispatch_equivalence_caveat",
    "classify_unavailable_outcome",
    "classify_subagent_unavailable_outcome",
    "build_unavailable_observation",
    "ModelsEndpointResult",
    "corroborate_models_endpoint",
    "build_snapshot_id",
    "build_capability_answers",
    "build_open_gaps",
    "gate_probe_run_dispositions",
    "assemble_runtime_capability_snapshot",
    "write_snapshot_fail_closed",
    "ALIAS_CAPABILITY_QUESTIONS",
)


if __name__ == "__main__":  # pragma: no cover — operator-only entry (FR-001); tests import, never execute
    raise SystemExit(main())
