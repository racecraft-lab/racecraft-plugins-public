# Implementation Plan: Capability Discovery, Telemetry Profile, and Exact-Treatment Contract

**Branch**: `g56r-002-capability-discovery-telemetry` | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/g56r-002-capability-discovery-telemetry/spec.md`

## Summary

Add two Python 3.11 standard-library modules to the existing Layer 6 harness.
The first normalizes pinned Codex surface evidence, applies claim-scoped source
admission, enforces the bounded canary contract, and emits a content-addressed
candidate freeze. The second validates telemetry profiles, route-resolution and
exact-treatment records, and deterministic synthetic replay. One sanitized
research handoff and two compact replay fixtures prove the contracts without
committing raw live responses or performing qualification.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Python standard library only (`dataclasses`,
`hashlib`, `json`, `pathlib`, `subprocess`, and `typing`)

**Storage**: Canonical JSON in Git for sanitized fixtures and the frozen
handoff; a required content-addressed `raw_evidence_root` outside the repository
for operator-only live captures

**Testing**: Existing repository Python test convention, focused unit replay,
Layer 1 structural validation, the generated docs-site test reference check,
and the full deterministic suite

**Target Platform**: The pinned Codex client on macOS, Linux, or Windows;
repository replay is platform-neutral and offline. Operator-only raw-evidence
workflows run on POSIX and fail closed on Windows pending equivalent DACL checks

**Project Type**: Repository-owned test harness and evidence contract

**Performance Goals**: Deterministic fixture replay in under one second; live
canary hard-bounded to 30 seconds and 64 KiB combined output

**Constraints**: No third-party packages, Bash, `jq`, raw live responses in Git,
retries within a snapshot, inferred platform facts, qualification, scoring,
installer changes, agent changes, payload regeneration, or fallback ordering

**Scale/Scope**: Twelve named-agent contracts, the G56R-001 source-bound route
set, one pinned client identity, three observation surfaces, and the eight
required replay classes

**Reviewability Budget**: Primary surface `harness/adapter`; secondary surface
`schema/data contract`; target 265 reviewable LOC, approximately 2 production
modules and 10 implementation files. The scaffold estimate is 297 LOC. Stay one
slice unless the authoritative plan estimate exceeds 400 LOC or the three
increments cease to be independently testable.

**Authoritative plan estimate**: `pass`, 0 projected production LOC, 8 new and
2 modified files. The helper does not classify Python modules below
`tests/speckit-pro/` as production, so its zero is a path-classification limit,
not a size claim. The binding human estimate remains 297 reviewable LOC; the
400-LOC split trigger remains enforced.

**Implementation checkpoint**: The capability adapter is 2,470 source lines
and 2,243 nonblank, non-comment lines after finding-driven US2 retention
remediation. The treatment validator is 1,633 source lines and 1,497 nonblank,
non-comment lines, so the current two-module US2 marker totals 4,103 source
lines and 3,740 nonblank, non-comment lines and the 400-LOC trigger is active.
Capability work T001-T015 remains one review marker under a typed size-only
exception because source refresh, surface authority, tuple decisions, and the
published freeze validator share one integrity boundary and have no safe
internal split. This exception permits the completed capability checkpoint
only; later growth is limited to finding-driven successor-validation integrity
work in `codex_capabilities.py`. Treatment
work T016-T025 remains a separate module and marker, while replay plus polish
T026-T039 remains a third marker. The authoritative marker state is persisted
in `docs/ai/specs/.process/autopilot-state.json`.

## Declared File Operations

- NEW tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py
- NEW tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py
- NEW tests/speckit-pro/unit/test-g56r-002-capability-telemetry.py
- NEW tests/speckit-pro/unit/fixtures/capability-treatment-replay/capability-matrix.json
- NEW tests/speckit-pro/unit/fixtures/capability-treatment-replay/treatment-replay.json
- NEW tests/speckit-pro/unit/fixtures/capability-treatment-replay/fixture-digests.json
- MODIFIED tests/speckit-pro/suite-manifest.json
- MODIFIED docs-site/src/content/docs/reference/tests.md
- NEW docs/ai/research/codex-g56r-002-executable-candidate-freeze.json
- NEW docs/ai/research/codex-g56r-002-capability-evidence.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Decision | Evidence |
|---|---|---|
| Library-first and CLI contracts | Pass | Two importable modules own collection/normalization and schema/replay behavior; no new framework |
| Test-first development | Pass | Each increment starts with focused failing fixtures and unit assertions before implementation |
| Integration testing | Pass | Offline replay covers surface joins, treatment, reroutes, hashes, and failure dispositions |
| Observability | Pass | Every desired field has a profile entry with source, completeness, claim, typed state, and evidence |
| Simplicity and YAGNI | Pass | Reuse Layer 6 and the shared G56R taxonomy; no cross-vendor prober or installer seam |
| Source authority | Pass | Only current canonical OpenAI documentation admits platform claims; runtime data can only narrow |
| Reviewability | Typed size-only exception | Capability implementation exceeded 400 LOC; T001-T015 has no safe internal integrity boundary, and T016-T039 remains split into two later markers |

No correctness or safety exception is requested. The capability marker carries
only the typed size exception above. Any further growth of that module, a third
production module, or coupling between later markers is a new stop condition.

## Architecture and Ownership

### `codex_capabilities.py`

- Validate `client_identity_id`, surface collection metadata, canonical
  model/effort normalization, hidden visibility, and disagreement records.
- Revalidate current source-record digests and carry claim-scoped invalidations;
  never modify historical `OSL-*` rows.
- Validate one injected, approved `CanaryExecutor` result per
  `(snapshot, model, effort)`, including the 30-second, 64 KiB, zero-retry,
  process-tree-termination contract and closed result envelope. A
  repository-owned, versioned, default-empty executor-ID allowlist is the trust
  anchor; fail closed without a separately reviewed admitted executor.
- Sanitize allowlisted evidence, emit canonical JSON/SHA-256, and build the
  append-only candidate freeze.

### `treatment_trace_schema.py`

- Validate single-client telemetry-profile ownership, complete keys, and
  classification/claim semantics; absent surface bindings never authorize
  top-level treatment claims.
- Validate the content-addressed six-ID objective join, reciprocal acyclic trace
  graphs, controlled-environment consistency,
  configured-route proof, typed observation-state rules, structured treatment
  failures, owning-ID uniqueness, route resolution, exact treatment,
  resource/lifecycle fields, and separate service-reroute destination proof
  with preserved detailed failure reasons. Retained inputs use descriptor-relative
  component walks, strict JSON bounds, and deny-by-default path sanitization.
  Controlled environments and qualification evidence live in explicit owner
  registries; synthetic qualification records exercise replay but never
  authorize live continuation.
- Replay committed fixtures twice offline and reject hash drift, undeclared
  fields, raw-store dependencies, inferred values, or nondeterminism.

### Orchestration seam

Do not modify `run-efficiency-benchmarks.py`. Each module exposes importable
pure functions plus a narrow `main(argv)` for operator collection or offline
validation. The focused unit test loads the underscore-named modules directly,
matching the existing Layer 6 library pattern. This keeps qualification and the
current benchmark runner out of G56R-002.

## Ordered Increments

### Increment 1 — Capability freeze [US1] [FR-001..FR-004]

1. Add failing tests and a sanitized surface-matrix fixture for identity,
   normalization, hidden status, disagreement, aggregate invalidity, source
   admission, canary bounds, redaction, and immutable freeze IDs.
2. Implement `codex_capabilities.py` until the focused tests pass.
3. Generate the sanitized candidate-freeze handoff. Operator-only live
   observations may populate evidence, but missing CLI or picker evidence stays
   unknown and excludes only its tuple.

### Increment 2 — Treatment contracts [US2] [FR-005..FR-007]

1. Add failing trace/profile cases for all classifications, configured-route
   proof, six-ID joins, typed null states, resource/lifecycle fields, and
   resolver-versus-service-reroute separation.
2. Implement `treatment_trace_schema.py` until every case has its predeclared
   disposition.
3. Bind the handoff to a versioned telemetry profile without inferring any
   unavailable field.

### Increment 3 — Synthetic replay [US3] [FR-008]

1. Add success, explicit-null, unavailable, misdelivery, approved reroute,
   unapproved reroute, discovery-loss, and surface-disagreement records.
2. Validate fixture bytes against the out-of-band digest manifest before
   parsing and replay the full set twice without network or raw-store access.
3. Register the focused test, regenerate the docs-site test reference, and run
   the applicable repository gates.

## TDD and Verification Strategy

For each increment: write a failing focused assertion, run it to record RED,
implement the smallest behavior, rerun for GREEN, then refactor without changing
dispositions. Required final checks:

1. Focused G56R-002 unit test.
2. JSON parsing and canonical fixture-hash verification.
3. Layer 1 structural suite.
4. Docs-site test-reference check/regeneration because test Markdown/Python
   surfaces change.
5. Full `python3 -u tests/speckit-pro/run-all.py` deterministic suite.
6. `git diff --check` and reviewability backstop.

Live collection is operator-only, non-scored, and never a default CI gate.
Repository tests must pass with the network disabled and no raw evidence store.

## Evidence and Data Boundaries

- `raw_evidence_root` must resolve outside the repository, use `0700`
  directories and single-link `0600` files, and retain captures for 30 days after freeze
  publication. Source refresh copies and binds the exact aggregate body capture
  into that store. Publication stages content-addressed retention records and
  makes them governing only by appending a receipt after the exact freeze bytes
  exist; failed-publication records cannot extend deletion. Deterministic
  verification fails on missing or overdue bytes, and cleanup
  appends and directory-fsyncs a content-addressed deletion record before
  removing the raw bytes and directory-fsyncing the raw root. Registration and
  cleanup share an atomic private-root lock, and destructive cleanup derives its
  timestamp from current UTC. Append-only writes directory-fsync both final-name
  publication and temporary-name removal; any alternate hard link blocks cleanup.
- Committed fixtures are deny-by-default sanitized, schema-allowlisted,
  canonical UTF-8 JSON with sorted keys and compact separators, and SHA-256
  bound to exact bytes by the adjacent out-of-band digest manifest.
- Official-document refresh outcomes remain per `OPENAI-DOC-*` record. A changed
  source invalidates only bound claims/routes; the G56R-001 historical record is
  not rewritten as current evidence.
- A published freeze is append-only. Any source, build, evidence,
  normalization, or disposition change creates a successor freeze ID, and every
  treatment-bound publication or successor API requires externally supplied
  trusted profile and contract IDs.

## Project Structure

### Documentation (this feature)

```text
specs/g56r-002-capability-discovery-telemetry/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── capability-freeze.schema.json
│   └── treatment-record.schema.json
└── tasks.md
```

### Source and tests

```text
tests/speckit-pro/layer6-efficiency/lib/
├── codex_capabilities.py
└── treatment_trace_schema.py

tests/speckit-pro/unit/
├── test-g56r-002-capability-telemetry.py
└── fixtures/capability-treatment-replay/
    ├── capability-matrix.json
    ├── treatment-replay.json
    └── fixture-digests.json

docs/ai/research/
├── codex-g56r-002-executable-candidate-freeze.json
└── codex-g56r-002-capability-evidence.md
```

**Structure Decision**: Keep vendor-specific collection and neutral evidence
validation in two adjacent Layer 6 modules. Keep deterministic tests in the
default unit layer, live collection out of CI, and the sanitized handoff beside
the G56R-001 research artifacts.

## PR Review Packet Source

The final packet must summarize the two-module contract, why runtime evidence
only narrows the official ledger, non-goals, review order (schemas → fixtures →
adapter → trace validator → handoff), file/LOC budget, FR/SC traceability,
focused/full verification, any unknown tuples or unobserved surfaces, raw-store
retention, and rollback by removing the new modules/fixtures/handoff and suite
registration. There is no feature flag and no shipped runtime change.

## Complexity Tracking

No constitution violation requires justification.
