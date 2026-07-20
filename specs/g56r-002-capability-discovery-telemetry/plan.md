# Implementation Plan: Capability Discovery, Telemetry Profile, and Exact-Treatment Contract

**Branch**: `g56r-002-capability-discovery-telemetry` | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/g56r-002-capability-discovery-telemetry/spec.md`

## Summary

Add two Python 3.11 standard-library public entry points and focused internal
modules to the existing Layer 6 harness. The capability entry point normalizes
pinned Codex surface evidence, applies claim-scoped source
admission, enforces the bounded canary contract, and emits a content-addressed
candidate freeze. The treatment entry point validates telemetry profiles, route-resolution and
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
installer changes, agent changes, unrelated payload changes, or fallback ordering.
Finding-driven shared schema or validator hardening must regenerate its existing
payload and installed-cache proof copies from source.

**Scale/Scope**: Twelve named-agent contracts, the G56R-001 source-bound route
set, one pinned client identity, three observation surfaces, and the eight
required replay classes

**Reviewability Budget**: Primary surface `harness/adapter`; secondary surface
`schema/data contract`; target 265 reviewable LOC, approximately 2 public
entry points and 10 implementation files. The scaffold estimate is 297 LOC. Stay one
slice unless the authoritative plan estimate exceeds 400 LOC or the three
increments cease to be independently testable.

**Authoritative plan estimate**: `pass`, 0 projected production LOC, 8 new and
2 modified files. The helper does not classify Python modules below
`tests/speckit-pro/` as production, so its zero is a path-classification limit,
not a size claim. The binding human estimate remains 297 reviewable LOC; the
400-LOC split trigger remains enforced. The exact current base-to-head path set
is governed separately by the changed-file manifest below because independent
review remediation expanded process, schema, and generated-proof surfaces.

**Implementation checkpoint**: Independent review rejected the original
two-monolith size exception. The current remediation preserves two public entry
points while separating source refresh, observations, matrix/canary logic,
private retention, freeze construction, JSON-schema validation, trace graphs,
fixture replay, and successor construction into focused modules. The current
implementation spans 23 modules and 5,107 source lines, but the largest module
is 381 lines, below the 400-line per-module boundary. The aggregate size block
is handled by the existing US1/US2/US3 marker and stacked-PR checkpoints; no
current `no_safe_boundary` implementation exception remains. Historical
checkpoint evidence retains the measurements that were true at those immutable
heads. The authoritative current marker state is persisted in
`docs/ai/specs/.process/autopilot-state.json`.

## Declared File Operations

The authoritative operation set is
`specs/g56r-002-capability-discovery-telemetry/.process/changed-file-manifest.json`.
It classifies every path from base
`48d72a5dfe1dd971bef6ddcdcd7a67752c9975ec` through the current `HEAD` by
operation, marker ownership, process/generated category, and provenance. The
manifest includes itself and this plan. T039 must compare the manifest exactly
to `git diff --name-status 48d72a5dfe1dd971bef6ddcdcd7a67752c9975ec..HEAD`;
an omitted, extra, or differently classified operation keeps T039 incomplete.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Decision | Evidence |
|---|---|---|
| Library-first and CLI contracts | Pass | Two stable public entry points delegate to focused collection, normalization, retention, schema, and replay modules; no new framework |
| Test-first development | Pass | Each increment starts with focused failing fixtures and unit assertions before implementation |
| Integration testing | Pass | Offline replay covers surface joins, treatment, reroutes, hashes, and failure dispositions |
| Observability | Pass | Every desired field has a profile entry with source, completeness, claim, typed state, and evidence |
| Simplicity and YAGNI | Pass | Reuse Layer 6 and the shared G56R taxonomy; no cross-vendor prober or installer seam |
| Source authority | Pass | Only current canonical OpenAI documentation admits platform claims; runtime data can only narrow |
| Reviewability | Pass after safe subdivision | Aggregate size remains marker-split, while every current implementation module is below 400 source lines |

No correctness, safety, or current size exception is requested. Growth that
pushes any focused module to 400 lines, recreates mixed responsibilities, or
couples independently reviewed markers is a new stop condition.

## Architecture and Ownership

### Capability entry point and focused modules

- `codex_capabilities.py` preserves the public import and CLI boundary through an
  exact supported export set; private trust primitives remain available only
  from their owning focused modules.
- Contract, source, observation, and matrix modules validate `client_identity_id`, surface collection metadata, canonical
  model/effort normalization, hidden visibility, and disagreement records.
- Private-I/O and retention modules revalidate current source-record digests, carry claim-scoped invalidations,
  never modify historical `OSL-*` rows.
- Freeze and canary modules validate one injected, approved `CanaryExecutor` result per
  `(snapshot, model, effort)`, including the 30-second, 64 KiB, zero-retry,
  process-tree-termination contract and closed result envelope. A
  repository-owned, versioned, default-empty executor-ID allowlist is the trust
  anchor; fail closed without a separately reviewed admitted executor.
- Publication modules sanitize allowlisted evidence, emit canonical JSON/SHA-256, and build the
  append-only candidate freeze.

### Treatment entry point and focused modules

- `treatment_trace_schema.py` preserves the public validation/replay CLI boundary.
- Authority, model, and field modules validate single-client telemetry-profile ownership, complete keys, and
  classification/claim semantics; absent surface bindings never authorize
  top-level treatment claims.
- Bundle modules validate the content-addressed six-ID objective join, reciprocal acyclic trace
  graphs, controlled-environment consistency,
  configured-route proof, typed observation-state rules, structured treatment
  failures, owning-ID uniqueness, route resolution, exact treatment,
  resource/lifecycle fields, and separate service-reroute destination proof
  with preserved detailed failure reasons. Retained inputs use descriptor-relative
  component walks, strict JSON bounds, and deny-by-default path sanitization.
  Controlled environments and qualification evidence live in explicit owner
  registries; synthetic qualification records exercise replay but never
  authorize live continuation.
- Fixture and replay modules replay committed fixtures twice offline and reject hash drift, undeclared
  fields, raw-store dependencies, inferred values, or nondeterminism.

### Orchestration seam

Do not modify `run-efficiency-benchmarks.py`. Each public entry point exposes
the existing importable functions plus a narrow `main(argv)` for operator
collection or offline validation. The focused unit test loads the entry points directly,
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
  verification fails on missing or overdue bytes. Cleanup first persists a
  content-addressed deletion intent, then unlinks the raw bytes through the
  validated parent descriptor, proves zero links and the verified content
  identity, directory-fsyncs the raw root, and only then persists the terminal
  deletion completion record. Registration and cleanup share an atomic
  private-root lock, and destructive cleanup derives its timestamp from current
  UTC. Append-only writes directory-fsync both final-name publication and
  temporary-name removal; any alternate hard link blocks cleanup.
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
├── codex_capabilities.py                  # public capability import/CLI boundary
├── codex_capability_cli.py                # command dispatch
├── codex_capability_contract.py           # bounds and contract validation
├── codex_capability_freeze.py             # freeze construction/publication
├── codex_capability_io.py                 # strict JSON and descriptor I/O
├── codex_capability_matrix.py             # matrix and canary decisions
├── codex_capability_observations.py       # observation normalization
├── codex_capability_private.py            # private retained-byte writes
├── codex_capability_publish_io.py         # publication read-back
├── codex_capability_retention.py          # cleanup and retention lifecycle
├── codex_capability_retention_records.py  # append-only retention records
├── codex_capability_sources.py            # source refresh/admission
├── treatment_trace_schema.py              # public treatment import/CLI boundary
├── treatment_trace_authority.py           # authority and owner joins
├── treatment_trace_bundle.py              # bundle validation
├── treatment_trace_cli.py                 # command dispatch
├── treatment_trace_fields.py              # closed field inventory
├── treatment_trace_fixture.py             # fixture validation
├── treatment_trace_io.py                  # retained-file and path I/O
├── treatment_trace_json_schema.py         # executable schema parity
├── treatment_trace_model.py               # neutral record validation
├── treatment_trace_replay.py              # deterministic replay
└── treatment_trace_successor.py           # successor lineage validation

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
validation behind two adjacent Layer 6 public entry points, with focused
single-responsibility sibling modules below 400 lines. Keep deterministic tests in the
default unit layer, live collection out of CI, and the sanitized handoff beside
the G56R-001 research artifacts.

## PR Review Packet Source

The final packet must summarize the two-entry-point and focused-module contract, why runtime evidence
only narrows the official ledger, non-goals, review order (schemas → fixtures →
adapter → trace validator → handoff), file/LOC budget, FR/SC traceability,
focused/full verification, any unknown tuples or unobserved surfaces, raw-store
retention, and rollback by removing the new modules/fixtures/handoff and suite
registration. There is no feature flag and no shipped runtime change.

## Complexity Tracking

No constitution violation requires justification.
