# Feature Specification: CAR-002 Capability Probing, Telemetry Profile, and Exact-Treatment Contract

**Feature Branch**: `car-002-capability-probing-telemetry`

**Created**: 2026-07-16

**Status**: Draft

**Input**: User description: "Capability probing, telemetry profile, and exact-treatment trace contract for the Claude agent routing (CAR) evaluation campaign. CAR-001 froze 12 agent contracts and 37 candidate routes but deferred every executable-route claim behind six capability questions (CAP-Q1..CAP-Q6). Freeze the executable candidate set for the pinned Claude Code client by capturing a committed runtime capability snapshot from recorded probe evidence, publish a versioned telemetry capability profile, and publish binding route-resolution and exact-treatment replay trace contracts that CAR-003..CAR-011 consume — with all live probing operator-only and every repository/CI test deterministic (zero live model calls)."

## User Scenarios & Testing *(mandatory)*

<!--
  User stories map to the three ratified vertical work packages from the
  design concept (docs/ai/specs/.process/CAR-002-design-concept.md, Q8):
  WP1 = snapshot capture, WP2 = telemetry + trace contracts, WP3 = synthetic
  replay validation. Each story is independently testable against committed
  synthetic fixtures without any live model call.
-->

### User Story 1 - Capture and commit the runtime capability snapshot (Priority: P1)

An operator runs the probe tool locally against the pinned Claude Code client
and commits a validated `runtime_capability_snapshot` that answers the CAR-001
capability questions (CAP-Q1..CAP-Q6) with recorded evidence: the
alias-to-dated-ID bindings for opus/sonnet/haiku/fable, the bare-platform
behavior when an unavailable model is dispatched, and how alias re-pointing is
detected. The snapshot is the single canonical evidence artifact that unblocks
downstream scoring.

**Why this priority**: This is the MVP and the reason the spec exists. Without a
committed snapshot answering CAP-Q1..Q6, CAR-003 cannot score outcomes because
the executable candidate subset is never frozen. It is the first work package
(WP1) and delivers standalone value even if no other story ships.

**Independent Test**: Run the operator probe tool in an environment with a
working `claude` CLI; confirm it produces a snapshot at
`docs/ai/research/claude-runtime-capability-snapshot.json` that validates
against the schema, records one shared evidence set per unique (model, effort)
tuple, and either answers each capability question with evidence or marks it
explicitly open. The write path is independently verifiable via the fail-closed
writer (an invalid observation aborts the write).

**Acceptance Scenarios**:

1. **Given** a pinned `claude` CLI and the deduplicated probe matrix, **When** the operator runs the probe tool, **Then** a snapshot is written at the canonical path recording alias→dated-ID bindings for all four aliases and one shared evidence set per unique (model, effort) tuple, bounded at roughly 20 live invocations.
2. **Given** the unavailable-model probe, **When** an unavailable model ID is dispatched, **Then** the snapshot records the observation for both the `-p --model` surface and the subagent-frontmatter dispatch surface separately, each with proof that `--fallback-model`/`fallbackModel` was unset.
3. **Given** a probe observation that fails schema validation, **When** the writer attempts to persist it, **Then** the snapshot write aborts and no snapshot file is created or overwritten.
4. **Given** a capability question that cannot be answered from a bounded probe (for example alias re-pointing that cannot be safely induced), **When** the snapshot is written, **Then** that question is recorded as an explicit open/gap entry rather than an assumed value or a run failure.

---

### User Story 2 - Publish the versioned telemetry capability profile (Priority: P2)

A maintainer reads a versioned telemetry capability profile scoped to the
pinned Claude Code client that classifies every telemetry field into one of four
categories — `stable_native`, `derived`, `derived_from_controlled_configuration`,
or `unavailable` — with null-valued fields preserved so that "unavailable" is
always distinguishable from "absent."

**Why this priority**: The profile is the second work package (WP2) and is what
lets downstream specs reason about which telemetry they may trust natively
versus derive. It builds on the snapshot fields captured in US1 but delivers
independent value as a review artifact.

**Independent Test**: Validate the committed telemetry profile against its
`telemetry_profile` schema definition; confirm every field carries exactly one
of the four classification labels and that null-valued fields are present rather
than dropped.

**Acceptance Scenarios**:

1. **Given** the telemetry profile document, **When** it is validated against the schema, **Then** every field carries exactly one of the four classification labels and the profile records the pinned client version it describes.
2. **Given** a telemetry field with no observed value, **When** the profile is written, **Then** the field is preserved with a null value and classified (typically `unavailable`), never omitted.

---

### User Story 3 - Publish route-resolution and exact-treatment replay contracts (Priority: P2)

Downstream specs (CAR-003 through CAR-011) consume `route_resolution` and
exact-treatment replay schemas as binding contracts. Each `route_resolution`
record binds agent, model, effort, instruction hash, mutation contract, client
version, fast-mode state, and env-override proof; the exact-treatment replay
record captures the full treatment identity needed to reproduce one evaluated
invocation.

**Why this priority**: The trace contracts are the second half of WP2 and are
the interface every downstream CAR spec builds on. They are prioritized with US2
because they ship in the same work package, and they are independently testable
against synthetic fixtures.

**Independent Test**: Validate synthetic `route_resolution` and exact-treatment
records against their `$defs` in the single JSON Schema contract; confirm all
required binding fields are present and that a downstream consumer can reproduce
a treatment from the record alone.

**Acceptance Scenarios**:

1. **Given** a synthetic `route_resolution` record, **When** it is validated against its `$def`, **Then** validation requires agent, requested model alias, resolved dated model ID, effort, instruction hash, mutation contract, client version, fast-mode state, and env-override proof to all be present.
2. **Given** an exact-treatment replay record, **When** a downstream consumer reads it, **Then** the record carries the complete route-resolution binding plus the observed record class and outcome, sufficient to replay the treatment without re-probing.

---

### User Story 4 - Deterministically validate the contracts and snapshot in CI (Priority: P3)

CI deterministically validates the schema contract, the four synthetic record
classes (success, null, unavailable, misdelivery), and the committed snapshot on
every run — with zero live model calls. This is the trust anchor that lets the
schemas be relied on as binding contracts.

**Why this priority**: This is the third work package (WP3) — the capstone.
Determinism is a hard repository requirement, but this story depends on the
schema definitions from US2/US3 and the snapshot from US1, so it ships last.
Note that US1 already provides write-time validation via the fail-closed writer;
US4 adds the continuous CI enforcement and the full synthetic-fixture matrix.

**Independent Test**: Run `python3 tests/speckit-pro/run-all.py` on a machine
with no `claude` CLI and no network; confirm the suite validates all four
synthetic record-class fixtures plus the committed snapshot against the schema
and passes with zero live model calls.

**Acceptance Scenarios**:

1. **Given** committed synthetic fixtures for all four record classes, **When** the deterministic test runs in CI, **Then** each fixture is validated against the schema and the committed snapshot is validated, all without any live model call.
2. **Given** a synthetic fixture that drifts from the schema, **When** the deterministic test runs, **Then** the test fails closed and blocks merge.
3. **Given** an environment with no `claude` CLI installed, **When** the default repository suite runs, **Then** it completes successfully because no test path performs live probing.

---

### Edge Cases

- **Malformed probe payload**: When a probe returns an unparseable `--output-format json` payload, the writer treats it as an observation but cannot schema-validate it, so the snapshot write aborts (fail-closed) rather than committing a partial record.
- **Fallback chain fires despite unset configuration**: When the unavailable-model probe triggers the documented native fallback chain even though `--fallback-model`/`fallbackModel` is unset, the observation is flagged so bare-platform behavior is not misread as availability.
- **Alias re-pointing between runs**: When an alias resolves to a different dated ID than a prior run, the route-change detection rule flags observed ≠ previously-resolved as CAP-Q6 evidence; if re-pointing cannot be safely induced within a bounded probe, CAP-Q6 remains open in the snapshot.
- **API models endpoint unreachable**: When the operator environment uses subscription (not API-key) authentication and the models endpoint is unreachable, its absence is recorded as a gap, not a run failure; the run records the authentication mode.
- **Narrowed availability on re-probe**: When a re-probe yields fewer accepted tuples than the committed snapshot, the replacement snapshot records the narrowed availability; runtime probing narrows availability but never removes a platform fact established from documentation.
- **Budget overrun**: When a probe matrix would exceed the roughly 20-invocation bound, that indicates a matrix-definition error and is surfaced before any live call is made.
- **Undocumented effort surface**: When the effort-configuration surface for non-interactive `claude -p` is not found in canonical documentation, the effort-acceptance probe method is recorded as a labeled inference / proposed policy, never as an established platform fact.

## Requirements *(mandatory)*

### Functional Requirements

#### Probe execution boundary and determinism

- **FR-001**: The probe capability MUST ship as a single operator-invoked entrypoint that is the only path permitted to execute live `claude` CLI calls; no repository or CI test may invoke it or make any live model call.
- **FR-002**: All repository and CI tests MUST remain deterministic, validating schemas against committed synthetic fixtures and the committed snapshot, and MUST pass on a machine with no `claude` CLI and no network access.

#### Probe matrix and budget

- **FR-003**: The probe matrix MUST dedupe the 37 candidate routes to unique (model, effort) tuples, executing one alias-canary invocation per unique model alias (for ID binding, CAP-Q1..Q4) plus one configuration-acceptance check per unique (model, effort) tuple, bounded at roughly 20 live invocations worst case.
- **FR-004**: Every candidate route in the snapshot MUST cite the shared evidence of its (model, effort) tuple; the system MUST NOT probe the 37 routes individually.
- **FR-005**: All probes within a single snapshot MUST use one identical fixed canary prompt, and the snapshot MUST record the canary text and its hash so the invariant is verifiable.

#### Capability answers (CAP-Q1..CAP-Q6)

- **FR-006**: The snapshot MUST record the alias-to-dated-ID binding for each of the opus, sonnet, haiku, and fable aliases (CAP-Q1) from its canary observation.
- **FR-007**: The snapshot MUST answer CAP-Q1..CAP-Q6, and MUST record any question that cannot be answered from a bounded probe as an explicit open/gap entry rather than a failure or an assumed value.
- **FR-008**: The snapshot MUST represent alias re-pointing (CAP-Q6) as a route-change detection rule over observed-versus-resolved model IDs; an induced re-pointing probe MUST be used only if it can be bounded, otherwise CAP-Q6 MUST be kept explicitly open in the snapshot.

#### Unavailable-model probe (CAP-Q5)

- **FR-009**: The unavailable-model probe MUST cover both surfaces — `claude -p --model <unavailable-id>` and a minimal subagent-frontmatter dispatch naming the same unavailable ID — recording each surface's observation separately.
- **FR-010**: Both unavailable-model probes MUST record proof that `--fallback-model`/`fallbackModel` configuration is unset at probe time, so the documented native fallback chain cannot mask bare-platform behavior.

#### Snapshot artifact and evidence capture

- **FR-011**: The probe tool MUST write one canonical committed snapshot at `docs/ai/research/claude-runtime-capability-snapshot.json`, beside the CAR-001 candidate manifest; a re-probe MUST replace the file in place, relying on git history to preserve prior snapshots.
- **FR-012**: For each probe, the snapshot MUST store the complete `--output-format json` stdout as raw evidence, with all home/user paths normalized to `<home>` per the existing release-readiness sanitization convention.
- **FR-013**: Each stored raw-evidence payload MUST carry a SHA-256 hash of its sanitized bytes; sanitization MUST occur before the snapshot is written, and no unsanitized raw payload (absolute home/user paths or machine-local session paths) may be committed.
- **FR-014**: Each probe run MUST record the authentication mode of the operator environment (API key versus subscription); if the API models endpoint is unreachable in that mode, its absence MUST be recorded as a gap, not a failure.

#### Schema contracts

- **FR-015**: The four record contracts — `runtime_capability_snapshot`, `telemetry_profile`, `route_resolution`, and exact-treatment replay — MUST be published as one review-visible JSON Schema file with a `$def` for each record type, located under `docs/ai/research/`.
- **FR-016**: The schema MUST be validated by standard-library-only Python logic in `claude_trace_schema.py` (no third-party dependencies), mirroring the CAR-001 manifest-schema plus parity-validator pattern.
- **FR-017**: The JSON Schema contract MUST remain platform-neutral, readable and checkable by Codex-side parity work without executing Python.

#### Telemetry capability profile

- **FR-018**: The telemetry capability profile MUST be versioned and scoped to the pinned Claude Code client version, which the profile records.
- **FR-019**: The telemetry profile MUST classify every field as exactly one of `stable_native`, `derived`, `derived_from_controlled_configuration`, or `unavailable`.
- **FR-020**: The telemetry profile MUST preserve null-valued fields (nulls are recorded and classified, not dropped) so that "unavailable" is distinguishable from "absent."

#### Trace contracts (route resolution and exact-treatment replay)

- **FR-021**: The `route_resolution` record MUST bind, at minimum, agent identity, requested model alias, resolved dated model ID, effort level, instruction (system-prompt) hash, mutation contract, client version, fast-mode state, and env-override proof.
- **FR-022**: The exact-treatment replay record MUST capture the complete treatment identity needed to reproduce one evaluated invocation — the `route_resolution` binding plus the observed record class and outcome — sufficient for CAR-003..CAR-011 to consume it as a binding contract without re-probing.

#### Validation enforcement and record classes

- **FR-023**: The probe writer MUST validate every observation against the schema before writing the snapshot; any invalid observation MUST abort the snapshot write (fail-closed), so no invalid snapshot can be committed.
- **FR-024**: A deterministic unit test MUST validate committed synthetic fixtures for all four record classes plus the committed snapshot on every CI run.
- **FR-025**: Each of the four record classes MUST have a committed synthetic fixture: success (well-formed populated record), null (null fields preserved, not dropped), unavailable (unavailable-model observation), and misdelivery (a record whose delivered treatment does not match the resolved route).

#### Evidence authority

- **FR-026**: Platform capability claims in the snapshot and profile MUST be sourced only from canonical `code.claude.com/docs/**` or `platform.claude.com/docs/**` pages; runtime probing MAY narrow availability but MUST NOT establish a platform fact absent from documentation.
- **FR-027**: Missing or conflicting platform documentation MUST fail closed — the affected capability is recorded as unresolved/unavailable and never assumed — and any effort-acceptance method that relies on an undocumented configuration surface MUST be recorded as a labeled inference / proposed policy.

#### Repository integration

- **FR-028**: The `claude_trace_schema.py` validator MUST be registered in `tests/speckit-pro/suite-manifest.json` with Layer 4 unit coverage, so no implementation is complete until the Python-authoritative default suite passes with zero failures.

### Reviewability Notes *(if applicable)*

- No typed reviewability exception (refactor, infra, or upgrade) is claimed. All
  changes are additive net-new artifacts (a JSON Schema contract, a stdlib
  validator with unit coverage, an operator-only probe tool, synthetic fixtures,
  and committed research documents); none rewrite or migrate existing shipped
  payload, guidance, or agent frontmatter.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter (the operator-only probe tool plus the `claude_trace_schema.py` stdlib validator).
- **Secondary surfaces, if any**: schema (the single JSON Schema contract with four `$defs`); seed/config (four synthetic record-class fixtures); docs/process (the committed `claude-runtime-capability-snapshot.json` and the telemetry capability profile under `docs/ai/research/`).
- **Projected reviewable LOC**: Roughly 860 total across the feature (shared size estimator: 4 user stories, ~10 files, ~24 FRs → `estimated_loc: 860`, `suggested_slices: 3`, `status: warn`). Concrete lower estimates exist (roadmap sized CAR-002 at 265 LOC; the same-day setup gate measured 395 reviewable LOC, just under the 400 ceiling). Each of the three work packages targets well under the 400 reviewable-LOC ceiling.
- **Projected production files**: ~10 (probe tool module(s), `claude_trace_schema.py`, the JSON Schema contract, the snapshot JSON, the telemetry profile, four synthetic fixtures, the Layer 4 unit test, and the `suite-manifest.json` registration).
- **Projected total files**: ~13 (production files plus spec, plan, and tasks artifacts).
- **Budget result**: split required — decomposed into three vertical work packages so no PR exceeds the review ceiling.
- **Split decision**: Ratified 3-slice split (design concept Q8), declared as work packages at Plan for PRSG split-PR routing: **WP1** — `runtime_capability_snapshot` schema `$def` + operator probe tool + committed snapshot (US1); **WP2** — telemetry capability profile + `route_resolution` and exact-treatment replay contracts (US2, US3); **WP3** — synthetic replay validation across all four record classes plus committed-snapshot validation in CI (US4).

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope
  budget, traceability, verification evidence, known gaps, and rollback or
  feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue (for example, corpus
  execution, scoring, statistics, and fallback ordering are deferred to CAR-003
  and later).

### Key Entities *(include if feature involves data)*

- **Runtime capability snapshot**: The single committed JSON artifact that answers CAP-Q1..CAP-Q6. Holds probe metadata (pinned client version, authentication mode, canary text and hash, timestamp), per-tuple shared evidence, alias→dated-ID bindings, unavailable-model observations per surface, and open/gap entries for unanswerable questions.
- **Probe observation (record)**: A single recorded probe result belonging to one of four classes — success, null, unavailable, or misdelivery — carrying the sanitized raw `--output-format json` payload and its SHA-256 hash.
- **(model, effort) tuple**: The deduplicated probe unit — a unique model alias crossed with an effort level — whose shared evidence every resolving candidate route cites.
- **Telemetry capability profile**: The versioned, per-client document that classifies every telemetry field as `stable_native`, `derived`, `derived_from_controlled_configuration`, or `unavailable`, preserving nulls.
- **route_resolution record**: The binding of agent, requested model alias, resolved dated model ID, effort, instruction hash, mutation contract, client version, fast-mode state, and env-override proof.
- **Exact-treatment replay record**: The reproducible-treatment contract (route_resolution binding plus observed record class and outcome) consumed by CAR-003..CAR-011.
- **JSON Schema contract**: One review-visible schema file with `$defs` for the four record types, under `docs/ai/research/`.
- **Probe tool / writer**: The operator-only entrypoint that runs the bounded probe matrix, sanitizes and validates observations, and fail-closed writes the snapshot.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can produce a committed snapshot that addresses all six capability questions (CAP-Q1..CAP-Q6) — each either answered with recorded evidence or explicitly marked open — in a single probe run bounded at roughly 20 live invocations.
- **SC-002**: Zero live model calls occur during any repository or CI test run; the full deterministic suite passes offline (no `claude` CLI, no network).
- **SC-003**: All four record classes (success, null, unavailable, misdelivery) have committed synthetic fixtures that the validation suite checks on every run (100% record-class coverage).
- **SC-004**: No invalid observation can reach the committed snapshot; the writer aborts before writing in 100% of invalid-observation cases.
- **SC-005**: Every one of the 37 candidate routes resolves to exactly one (model, effort) tuple and cites that tuple's shared evidence (100% route-to-tuple evidence coverage, zero routes without cited evidence).
- **SC-006**: Every field in the telemetry profile carries exactly one of the four classification labels and null-valued fields are preserved (100% field classification, zero dropped nulls).
- **SC-007**: A reviewer can read and check all four record contracts from a single JSON Schema file without executing any Python.
- **SC-008**: A downstream CAR spec (CAR-003..CAR-011) can bind a `route_resolution` or exact-treatment record from the published schema without needing any capability question that CAR-002 was responsible for answering.

## Assumptions

- **Pinned client**: The snapshot and telemetry profile are scoped to one pinned `claude` CLI version, recorded in the snapshot metadata; a different client version requires a re-probe.
- **Operator environment**: The operator runs the probe tool in an environment with a working `claude` CLI and valid authentication; the authentication mode (API key versus subscription) is recorded per run.
- **Effort-configuration surface**: The configuration surface for setting reasoning effort on a non-interactive `claude -p` invocation is pinned from canonical documentation during the research phase; if it is undocumented, the effort-acceptance probe method is recorded as a labeled inference / proposed policy (FR-027), never assumed.
- **Alias re-pointing (CAP-Q6)**: Alias re-pointing is represented as a route-change detection rule over observed-versus-resolved IDs and is kept open in the snapshot if it cannot be safely induced within a bounded probe (FR-008).
- **Fixed canary**: A single minimal canary prompt text is used identically across all probes in a snapshot; only the invariant matters, and the exact text plus its hash are recorded (decided at Plan).
- **Consumption gate satisfied**: The scaffold-time consumption gate is met — amendment PR #362 merged and the parity validator passed 18/18 on branch base b57d21a8 — so the CAR-001 manifest's CAP-Q entries are the authoritative probe backlog this spec draws from.
- **Toolchain**: Repository tooling is Python 3.11+ standard library only; verification is `python3 tests/speckit-pro/run-all.py` (there is no separate build, typecheck, or lint surface).
- **Out of scope**: Corpus execution, scoring, statistics, and fallback ordering are deferred to CAR-003 and later; no payload, guidance, agent-frontmatter, prompt, or default edits are made; no live probing runs in CI or at test time.
