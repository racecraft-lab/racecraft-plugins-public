# LLM Integration Checklist: G56R-002 Capability Discovery

**Purpose**: Validate that model, effort, surface, and exact-treatment requirements are source-bound and cannot infer undocumented platform behavior.
**Created**: 2026-07-16
**Feature**: [spec.md](../spec.md)

## Source Authority and Candidate Admission

- [x] CHK001 Is current canonical OpenAI documentation the only authority allowed to admit a model, effort, field, or platform behavior? [Authority, Spec §Evidence Basis, FR-001, FR-003]
- [x] CHK002 Must all 22 current `OPENAI-DOC-*` records be revalidated before freeze, with historical `OSL-*` rows excluded from current authority? [Completeness, Spec §FR-001; Research §Source-Ledger Refresh Rules]
- [x] CHK003 Are changed sources limited to claim-scoped invalidation rather than snapshot-wide or historical-ledger rewriting? [Consistency, Spec §FR-001; Research §Source-Ledger Refresh Rules]
- [x] CHK004 Is runtime discovery limited to narrowing source-admitted candidates rather than adding a model, effort, or role binding? [Scope, Spec §FR-003; Plan §Evidence and Data Boundaries]
- [x] CHK005 Does a new role/model binding require a canonical-ledger model plus source and agent-contract rationale? [Traceability, Spec §FR-003]

## Surface Matrix and Normalization

- [x] CHK006 Is one `client_identity_id` defined strongly enough to prove app-server, CLI, and picker observations came from the same pinned build? [Clarity, Spec §Clarifications Session 1; Data Model §ClientIdentity]
- [x] CHK007 Are deterministic collection methods and fixed inputs required independently for all three surfaces? [Completeness, Spec §Clarifications Session 1; Research §Surface Collection Decisions]
- [x] CHK008 Does app-server collection use documented discovery while CLI and picker remain secondary runtime observations? [Authority, Research §Current Official Evidence Bindings]
- [x] CHK009 Is normalization restricted to the canonical ledger model ID and canonical effort token, with raw labels preserved? [Integrity, Spec §Clarifications Session 1; Data Model §SurfaceMatrix]
- [x] CHK010 Are aliases limited to versioned one-to-one mappings supported by official field evidence or a same-build machine identifier? [Clarity, Spec §Clarifications Session 1]
- [x] CHK011 Must disagreement records preserve every surface value and avoid choosing a winning surface? [Consistency, Spec §Clarifications Session 1; Data Model §Disagreement]
- [x] CHK012 Is picker omission of a hidden model treated as consistent only under a complete recorded visibility policy? [Edge case, Spec §Clarifications Session 1]
- [x] CHK013 Are hidden observations retained while independent current-ledger admission remains mandatory? [Authority, Spec §FR-003]
- [x] CHK014 Are ordinary missing, hidden, or contradictory observations tuple-local exclusions, with aggregate invalidity limited to attribution/integrity failures? [Failure isolation, Spec §Clarifications Session 1; Data Model §SurfaceMatrix]

## Telemetry and Exact Treatment

- [x] CHK015 Is every desired telemetry field keyed by pinned client, surface, and field path without cross-surface inheritance? [Completeness, Spec §Clarifications Session 2; Data Model §TelemetryProfileEntry]
- [x] CHK016 Do all seven telemetry classifications define their official-source, completeness, and permitted-claim semantics? [Clarity, Spec §Clarifications Session 2; Research §Telemetry Classification Semantics]
- [x] CHK017 Are omitted profile entries `undocumented` and prohibited from supporting treatment? [Fail closed, Spec §Clarifications Session 2]
- [x] CHK018 Does configured-route proof bind consumed materialization, agent/model/effort, IDs, hashes, client, overrides, launch, and complete reroute monitoring? [Evidence quality, Spec §Clarifications Session 2; Data Model §ConfiguredRouteProof]
- [x] CHK019 Is configured-route proof limited to requested/assigned intent rather than an undocumented effective model or effort? [Authority, Spec §FR-005]
- [x] CHK020 Does effective model/effort evidence require a profile-supported native field and a satisfied completeness rule? [Treatment integrity, Spec §Clarifications Session 2]
- [x] CHK021 Are returned effort, effective model, speed, token categories, parent attribution, and every other absent value explicitly non-fabricable? [Negative requirement, Spec §FR-005]
- [x] CHK022 Are typed null/missing/unavailable/not-applicable/undocumented states separate from the `unknown` disposition? [Data semantics, Spec §Clarifications Session 2; Data Model §ObservationValue]

## Reroute and Probe Boundaries

- [x] CHK023 Are resolver-selected fallback fields immutable and separate from post-assignment service-reroute events? [Boundary, Spec §FR-006, FR-007; Data Model §RouteResolution]
- [x] CHK024 Is `model/rerouted` limited to its documented event fields without inferring effort, named-agent identity, or no-reroute coverage? [Authority, Spec §Evidence Basis; Research §Current Official Evidence Bindings]
- [x] CHK025 Does every service reroute make the requested route non-scorable, with ambiguous or unapproved destinations hard-failing treatment? [Safety, Spec §FR-007]
- [x] CHK026 Is the one-canary path permitted only when documented discovery is unavailable and bounded to pinned-environment availability evidence? [Scope, Spec §FR-004; Data Model §CanaryResult]
- [x] CHK027 Are the 30-second timeout, 64 KiB cap, zero-retry snapshot rule, closed error taxonomy, and tuple-local unknown outcome testable? [Measurability, Spec §Clarifications Session 3]
- [x] CHK028 Are scoring, qualification, ranking, preference, resolver policy, fallback order, installation, defaults, agent configuration, and payload work excluded? [Scope, Spec §FR-008; Plan §Technical Context]

## Result

- 28 items checked.
- 0 unresolved gaps.
- Parent fallback produced this checklist after the delegated checklist executor stalled without changing the worktree; independent consensus review is still required before G4.
