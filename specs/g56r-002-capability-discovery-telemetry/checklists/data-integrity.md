# Data Integrity Checklist: G56R-002 Evidence Contracts

**Purpose**: Validate stable identity, lossless joins, immutable evidence, null preservation, and deterministic fixture provenance before implementation.
**Created**: 2026-07-16
**Feature**: [spec.md](../spec.md)

## Identity and Referential Integrity

- [x] CHK001 Are stable IDs defined for source refreshes, client identity, surface observations/matrix, capability snapshots, candidate tuples/freezes, telemetry profiles, route resolutions, objective bindings, traces, and fixtures? [Completeness, Data Model §§Source and Surface Records through Fixture Provenance]
- [x] CHK002 Must every app-server, CLI, and picker observation bind the same `client_identity_id` before joining? [Referential integrity, Spec §Clarifications Session 1; Data Model §SurfaceMatrix]
- [x] CHK003 Does every executable tuple bind current official-source, effort-surface, agent-contract, candidate-route, and runtime-snapshot evidence? [Traceability, Spec §FR-003; Data Model §ExecutableCandidateTuple]
- [x] CHK004 Are all six objective IDs mandatory and non-null while later aggregate IDs remain explicit null until their owners exist? [Foreign keys, Spec §FR-006; Data Model §ObjectiveBinding]
- [x] CHK005 Must route-resolution and treatment-trace references resolve to the same snapshot, candidate, agent contract, client, and objective? [Consistency, Data Model §§ObjectiveBinding, RouteResolution, TreatmentTrace]
- [x] CHK006 Are orphan source records, observations, tuple decisions, profile entries, resolutions, reroute events, and traces rejectable by the planned validators? [Failure mode, Plan §Architecture and Ownership; Data Model §Relationship Map]

## Current-Ledger and Historical Boundaries

- [x] CHK007 Is the refresh set exactly 22 unique current `OPENAI-DOC-*` records rather than historical `OSL-*` evidence? [Boundary, Spec §FR-001; Capability Freeze Schema §official_source_refreshes]
- [x] CHK008 Does every refresh record bind the prior G56R-001 record digest, current facts, claim bindings, and claim-scoped invalidations? [Provenance, Data Model §OfficialSourceRefresh]
- [x] CHK009 Can an adverse source outcome invalidate only dependent claims/routes without mutating the G56R-001 manifest in place? [Immutability, Research §Source-Ledger Refresh Rules]
- [x] CHK010 Are stale, duplicate, missing, or non-allowlisted current-source bindings required to fail freeze validation? [Fail closed, Research §Source-Ledger Refresh Rules; Plan §Architecture and Ownership]

## Normalization and Exclusion Integrity

- [x] CHK011 Is the tuple join key limited to canonical ledger model ID and canonical effort token? [Lossless join, Spec §Clarifications Session 1]
- [x] CHK012 Are raw labels and every per-surface value retained alongside normalized keys? [Provenance, Spec §Clarifications Session 1; Data Model §Disagreement]
- [x] CHK013 Must alias mappings be versioned, one-to-one, and reject ambiguity or duplicates? [Uniqueness, Spec §Clarifications Session 1; Data Model §SurfaceMatrix]
- [x] CHK014 Are hidden, missing, unknown, and disagreement outcomes tuple-local unless aggregate identity/integrity prevents attribution? [Failure isolation, Spec §Clarifications Session 1]
- [x] CHK015 Does every considered tuple receive exactly one included/excluded decision with explicit reasons? [Completeness, Spec §SC-002; Capability Freeze Schema §tupleDecision]
- [x] CHK016 Can a freeze with zero included tuples remain structurally valid without implying support or success? [Edge case, Research §Implementation-Time Evidence Gap; Data Model §CandidateFreeze]

## Null and State Preservation

- [x] CHK017 Are typed values stored separately from `observed_value`, `explicit_null`, `missing`, `unavailable`, `not_applicable`, and `undocumented` states? [Semantics, Spec §Clarifications Session 2; Data Model §ObservationValue]
- [x] CHK018 Is `unknown` a disposition rather than a string or replacement value? [Clarity, Spec §Clarifications Session 2]
- [x] CHK019 Are zero, false, configured intent, and cross-surface values prohibited as substitutes for missing observations? [Loss prevention, Spec §FR-005; Data Model §ObservationValue]
- [x] CHK020 Are telemetry classifications keyed per client/surface/field with omission treated as `undocumented` rather than inherited? [Completeness, Data Model §TelemetryProfileEntry]

## Hashing, Immutability, and Retention

- [x] CHK021 Does the candidate freeze ID cover schema version, client identity, current-ledger digest, surface-matrix digest, and all tuple decisions? [Content addressing, Spec §Clarifications Session 1; Data Model §CandidateFreeze]
- [x] CHK022 Must any source, build, evidence, normalization, telemetry, or disposition change create a successor freeze/snapshot rather than mutate a published record? [Immutability, Plan §Evidence and Data Boundaries]
- [x] CHK023 Are raw evidence, sanitized evidence, method inputs, aggregate integrity, fixtures, instructions, and configurations individually hash-bound where required? [Provenance, Data Model §§SurfaceObservation, TreatmentTrace, Fixture Provenance]
- [x] CHK024 Are timestamps defined for refresh, collection windows, snapshots, resolution, traces, publication, and deletion evidence? [Temporal integrity, Data Model §Conventions and entity fields]
- [x] CHK025 Is `raw_evidence_root` outside the repository with operator-only permissions, a 30-day lifetime, and a surviving digest/deletion record? [Retention, Spec §Clarifications Session 3; Plan §Evidence and Data Boundaries]

## Sanitized Fixture Provenance

- [x] CHK026 Does deny-by-default sanitization remove credentials, headers, cookies, user content, account IDs, hostnames, absolute paths, and repository remotes? [Privacy, Spec §Clarifications Session 3]
- [x] CHK027 Are required joins replaced only by deterministic fixture-local pseudonyms and schema-allowlisted fields? [Determinism, Data Model §Fixture Provenance and Replay]
- [x] CHK028 Are schema version, sanitizer version, raw digest, fixture digest, and expected disposition required for each fixture? [Traceability, Spec §Clarifications Session 3]
- [x] CHK029 Is canonical UTF-8 JSON serialization defined precisely enough for byte-stable SHA-256 validation? [Measurability, Spec §Clarifications Session 3; Data Model §Conventions]
- [x] CHK030 Must replay reject undeclared fields, hash drift, raw-store/network dependencies, and nondeterministic output? [Integrity gate, Spec §FR-008; Data Model §Fixture Provenance and Replay]

## Result

- 30 items checked.
- 0 unresolved gaps.
- Custom Python validators must enforce cross-record uniqueness and foreign-key invariants that JSON Schema cannot express alone; this ownership is explicit in `plan.md` and `data-model.md`.
