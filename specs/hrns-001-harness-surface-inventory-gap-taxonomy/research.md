# Research: Harness Surface Inventory and Gap Taxonomy

## Decision: One Markdown taxonomy artifact

**Decision**: Use `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md` as
the single canonical artifact.

**Rationale**: The user-validated Design Concept chose a reviewable planning
artifact, not runtime metadata. A single document keeps AC-1.1 through AC-1.10
traceability visible to downstream HRNS authors without creating a registry
consumer before one exists.

**Alternatives considered**:

- Markdown plus JSON/YAML registry — rejected because HRNS-001 has no runtime
  consumer and this would expand scope.
- Roadmap-only sections — rejected because downstream specs need a durable,
  focused artifact that can be linked and reviewed independently.

## Decision: Verified repository source is factual authority

**Decision**: Treat verified merged repository source as current factual
authority. Generated payloads, installed caches, fixtures, raw transcripts,
unreviewed chat, and derived indexes are excluded as factual authority and may
only be cited as drift or secondary evidence.

**Rationale**: AC-1.8 and the Design Concept require source precedence.
Conflicts between source and generated copies must become gap findings, not
implicit source rewrites.

**Alternatives considered**:

- Include generated payloads as authority — rejected because generated copies
  can lag source.
- Include unreviewed chat/transcripts — rejected because they are not reviewed
  repository evidence.

## Decision: Stable gap IDs use `HRNS-GAP-###`

**Decision**: Every retained gap row uses a zero-padded `HRNS-GAP-###` ID and a
single canonical row. Surface summaries must reference the canonical row rather
than duplicating ownership or lifecycle state.

**Rationale**: Stable IDs make downstream HRNS ownership and later lifecycle
updates reviewable over time. The row shape satisfies AC-1.2 through AC-1.5 and
the Clarify decision.

**Alternatives considered**:

- Descriptive row names only — rejected because cross-spec traceability is
  fragile.
- Per-surface duplicate rows — rejected because ownership and state would drift.

## Decision: Candidate matrix is evidence-only and non-binding

**Decision**: The external-candidate matrix records reference evidence only.
It must not install, prototype, adopt, or require any external dependency.

**Rationale**: The PRD non-goals explicitly forbid adopting LangGraph, CrewAI,
OpenHands, Temporal, Braintrust, Langfuse, Phoenix, LangSmith, OpenAI Agents
SDK, AutoGen, Semantic Kernel, Haystack, DSPy, promptfoo, Inspect AI,
Guardrails AI, Pydantic, or other platforms without a dedicated spec,
supply-chain review, privacy review, and rollback plan.

**Alternatives considered**:

- Spike selected candidates now — rejected because that would turn HRNS-001
  into implementation research.
- Names and links only — rejected because downstream dependency decisions would
  be under-grounded.

## Decision: Starting candidate set

**Decision**: Start from PRD OQ-6 and AC-1.10: Pydantic, JSON Schema,
OpenTelemetry/OpenInference, LangGraph, OpenAI Agents SDK, LangSmith, Langfuse,
Phoenix, Braintrust, promptfoo, Inspect AI, DSPy, and the pinned OKF v0.1
specification/reference repository. Optional rows may include PRD non-goal
examples only when current primary evidence is captured.

**Rationale**: OQ-6 names the initial deeper-spike candidates; AC-1.6 and
AC-1.10 define the required matrix fields and OKF posture.

**Alternatives considered**:

- Exhaustively evaluate every PRD non-goal example — rejected for HRNS-001
  reviewability unless evidence is needed by downstream ownership.
- Defer all candidates — rejected because HRNS-003 through HRNS-014 need a
  reference baseline before choosing implementation or dependency work.

## Decision: External evidence protocol

**Decision**: Each external candidate row must cite dated primary evidence:
official specifications, official documentation, source repositories,
release/maturity records, and license sources as applicable. Rows record as-of
date, observed version or commit, maturity/normative status, unknown fields,
compatibility gaps, and recommendation.

**Rationale**: External maturity, licensing, versions, and product behavior are
drift-prone. Unsupported fields must remain `unknown` rather than being filled
from memory or inference.

**Alternatives considered**:

- Vendor comparison pages or secondary articles — rejected as insufficient
  authority for row-level decisions.
- Maintainer judgment without citations — rejected because auditability is a
  success criterion.

## Decision: OKF posture

**Decision**: The matrix records the normative OKF v0.1 specification pin from
the PRD and treats Google Cloud knowledge-catalog reference tooling as
interoperability evidence only.

**Rationale**: The PRD identifies the pinned OKF spec as normative and states
that reference agents, validator, server, client, and UI are not required
runtime dependencies.

**Alternatives considered**:

- Adopt reference tooling as required — rejected by PRD non-goals.
- Move the normative pin during HRNS-001 — rejected; pin movement requires a
  reviewed compatibility change.

## Decision: Completion proof

**Decision**: Completion requires AC-1.1 through AC-1.10 crosswalk, surface
coverage proof, evidence-class coverage proof, self-improvement loop coverage,
Markdown link review, intentional-deferment ownership, generated-index check,
and the smallest applicable repository checks selected in quickstart.

**Rationale**: This proves the docs/process artifact without adding validator
code or runtime behavior.

**Alternatives considered**:

- Manual review only — rejected because omissions would be hard to detect.
- New taxonomy validator — rejected because HRNS-001 explicitly excludes new
  validator/runtime work.
