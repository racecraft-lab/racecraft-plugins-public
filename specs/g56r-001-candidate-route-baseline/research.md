# Phase 0 Research: G56R-001 Candidate Route Baseline

## Decision 1: Freeze An Execution-Time Official Source Snapshot

**Decision**: The implementation report refreshes official OpenAI documentation
when the report is authored, records retrieval date and source metadata, then
freezes that snapshot for G56R-001.

**Rationale**: The roadmap requires current official documentation only.
Scaffold-time or remembered facts can drift before implementation. Continuous
refresh through review would make the report unstable and hard to audit.

**Alternatives Considered**:

- Scaffold-time snapshot: rejected because it may be stale before G56R-002
  consumes it.
- Continuous refresh: rejected because it creates review churn and undermines a
  dated evidence baseline.

## Decision 2: Publish One Canonical Report

**Decision**: The implementation produces one report at
`docs/ai/research/codex-agent-route-candidates.md`.

**Rationale**: One report keeps source records, role contracts, candidate
routes, fixture backlog, telemetry questions, and the go/no-go result together
with stable cross-references.

**Alternatives Considered**:

- Separate source, role, candidate, and fixture documents: rejected because
  cross-file drift would be harder to review.
- Report plus runtime JSON manifest: rejected because G56R-001 is
  documentation-only and must not introduce runtime policy artifacts.

## Decision 3: Use Stable Record IDs Instead Of Free-Form Claims

**Decision**: The report uses stable IDs for
`OfficialSourceLedgerRecord`, `EffortSurfaceRecord`,
`AgentContractRecord`, `CandidateRouteRecord`, `FixtureBacklogRecord`,
`TraceabilityRecord`, and `GoNoGoDecision` entries.

**Rationale**: Stable IDs make count checks, source bindings, and later G56R-002
handoff validation deterministic.

**Alternatives Considered**:

- Narrative-only report: rejected because reviewers could not mechanically
  confirm exact counts or bindings.
- Runtime schema file: rejected because schema enforcement is out of scope for
  this research spike.

## Decision 4: Treat Roadmap And Legacy Models As Inputs, Not An Approved Set

**Decision**: Roadmap seed models and legacy project-input model guidance are
reviewed against the execution-time official source ledger. Unsupported,
deprecated, withdrawn, or undocumented entries cannot become source-bound
candidates or executable routes.

**Rationale**: Candidate admission must fail closed when official documentation
does not support the model, effort, or required client surface.

**Alternatives Considered**:

- Keep all roadmap seeds regardless of official support: rejected because it
  would violate the evidence authority contract.
- Include every documented model without role filtering: rejected because
  G56R-001 is a role-contract baseline, not a general model catalog.

## Decision 5: Record Declared Role Sources Separately From Effective Runtime

**Decision**: Role contract records capture declared TOML fields, source files,
hashes, mutation expectations, grounding, tool/skill/MCP contracts, output
shape, and client surface. Effective runtime sandbox, approvals, loaded tools,
parent overrides, exact treatment, model, and effort are marked
`runtime_verification_needed`.

**Rationale**: Repository files can define role intent and declared source
configuration, but G56R-001 cannot prove runtime exact treatment.

**Alternatives Considered**:

- Treat TOML declarations as effective runtime proof: rejected because parent
  policy and runtime behavior must be verified later.
- Omit effective runtime fields: rejected because G56R-002 needs explicit
  capability and telemetry questions.

## Decision 6: Keep Claude Parity Roles As Project Inputs Only

**Decision**: `consensus-synthesizer` and `gate-validator` are included as
parity-only comparison records with `active_codex_route_status=absent`.

**Rationale**: They define desired future role contracts but are not current
active Codex TOML agents.

**Alternatives Considered**:

- Exclude parity roles: rejected because the roadmap requires twelve role
  contracts.
- Treat Claude metadata as Codex platform proof: rejected because it is
  `project_input`, not official documentation.

## Decision 7: Define Fixture Backlog Records Without Payloads

**Decision**: The report records exactly three current prompt-emulation Codex
fixtures and nine missing executable fixture specifications. Historical
prompt-emulation evidence is labeled `non_release_evidence`.

**Rationale**: G56R-003 needs executable fixture specifications, but G56R-001
must not create or run live fixture payloads.

**Alternatives Considered**:

- Create fixture payloads now: rejected because it expands beyond the research
  spike.
- Record broad fixture categories only: rejected because future specs need
  stable IDs, telemetry needs, success oracles, and blocking dependencies.

## Decision 8: Use Deterministic Document Validation

**Decision**: Verification combines marker search, count checks, cross-reference
review, changed-file scope review, diff hygiene, Layer 1 validation, and the
default repository suite.

**Rationale**: The implementation artifact is documentation, so validation
should prove traceability, counts, source authority, and scope rather than
runtime behavior.

**Alternatives Considered**:

- Live model probes: rejected because runtime discovery belongs to G56R-002.
- Manual-only review: rejected because exact counts and scope boundaries are
  central acceptance criteria.

## Decision 9: Defer Availability, Preference, Fallback, And Qualification

**Decision**: Candidate records may be source-bound for discovery only.
Executable model/effort tuple admission remains blocked until G56R-002 proves
supported efforts for the pinned client. Candidate records must not claim
availability, executability, qualification, preference, efficiency, or fallback
order. Before G56R-003 freezes the executable candidate set, G56R-002 may add a
role/model binding only for a model already present in the G56R-001
official-source ledger, and only when it records role-contract rationale or
explicit exclusion evidence.

**Rationale**: Official documentation can bound candidate eligibility, while
runtime capability discovery, telemetry profiling, exact treatment, scoring,
and fallback policy belong to later G56R specs.

**Alternatives Considered**:

- Rank candidates in G56R-001: rejected because no qualification evidence is in
  scope.
- Use local availability as an admission source: rejected because local runtime
  state cannot replace official documentation.
