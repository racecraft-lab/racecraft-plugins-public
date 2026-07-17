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
2. **Given** the unavailable-model probe, **When** an unavailable model ID is dispatched, **Then** the snapshot records the observation for both the `-p --model` surface and the subagent-frontmatter dispatch surface separately, each with proof that `--fallback-model`/`fallbackModel`, `CLAUDE_CODE_SUBAGENT_MODEL`, and `availableModels` were unset.
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
synthetic record-class fixtures plus the committed snapshot and the committed
telemetry-profile document against the schema and passes with zero live model
calls.

**Acceptance Scenarios**:

1. **Given** committed synthetic fixtures for all four record classes, **When** the deterministic test runs in CI, **Then** each fixture is validated against the schema and the committed snapshot is validated, all without any live model call.
2. **Given** a synthetic fixture that drifts from the schema, **When** the deterministic test runs, **Then** the test fails closed and blocks merge.
3. **Given** an environment with no `claude` CLI installed, **When** the default repository suite runs, **Then** it completes successfully because no test path performs live probing.

---

### Edge Cases

- **Malformed probe payload**: When a probe returns an unparseable `--output-format json` payload, the writer treats it as an observation but cannot schema-validate it, so the snapshot write aborts (fail-closed) rather than committing a partial record.
- **Interfering configuration fires despite unset-proof**: When the unavailable-model probe triggers the documented native fallback chain, a subagent model override, or a model-restriction mechanism even though the FR-010 unset-proof shows `--fallback-model`/`fallbackModel`, `CLAUDE_CODE_SUBAGENT_MODEL`, and `availableModels` unset at probe time, the observation is flagged so bare-platform behavior is not misread as availability.
- **Alias re-pointing between runs**: When an alias resolves to a different dated ID than a prior run, the route-change detection rule flags observed ≠ previously-resolved as CAP-Q6 evidence; if re-pointing cannot be safely induced within a bounded probe, CAP-Q6 remains open in the snapshot.
- **API models endpoint unreachable**: When the operator environment uses subscription (not API-key) authentication and the models endpoint is unreachable, its absence is recorded as a gap, not a run failure; the run records the authentication mode.
- **Narrowed availability on re-probe**: When a re-probe yields fewer accepted tuples than the committed snapshot, the replacement snapshot records the narrowed availability; runtime probing narrows availability but never removes a platform fact established from documentation.
- **Budget overrun**: When a probe matrix would exceed the roughly 20-invocation bound, that indicates a matrix-definition error and is surfaced before any live call is made.
- **Silently-clamped effort under JSON output**: Canonical docs state that with `json`/`stream-json` output an org effort cap clamps silently (plain-text `--print` emits a warning naming requested and applied levels). The effort-acceptance probe therefore runs in plain-text `--print` or records an explicit no-org-cap assumption; residual per-(model, effort) acceptance is labeled observation, never certification.
- **Partial probe matrix**: The snapshot is one atomic committed artifact — no partial snapshot is ever written. Three dispositions: (1) any observation failing schema validation, or an unparseable `--output-format json` payload, aborts the whole snapshot write (fail-closed — a silently-omitted tuple would make the SC-005 join resolve routes to zero tuples); (2) an infrastructure/transport failure with no interpretable platform signal (non-zero exit with no parseable error body, timeout, network failure) aborts the run with nothing committed, and is NOT recorded as "unavailable" — recording a transport failure as unavailable would falsely narrow platform availability (FR-026); (3) an interpretable platform observation — an unavailable-model result, the models endpoint unreachable in subscription mode, or a question unanswerable within the bounded matrix — is recorded as an explicit unavailable/gap/open observation and the snapshot is written.

## Requirements *(mandatory)*

### Functional Requirements

#### Probe execution boundary and determinism

- **FR-001**: The probe capability MUST ship as a single operator-invoked entrypoint that is the only path permitted to execute live `claude` CLI calls; no repository or CI test may invoke it or make any live model call.
- **FR-002**: All repository and CI tests MUST remain deterministic, validating schemas against committed synthetic fixtures and the committed snapshot, and MUST pass on a machine with no `claude` CLI and no network access.

#### Probe matrix and budget

- **FR-003**: The probe matrix MUST dedupe the 37 candidate routes to unique (model, effort) tuples, executing one alias-canary invocation per unique model alias (for ID binding, CAP-Q1..Q4) plus one configuration-acceptance check per unique (model, effort) tuple, bounded at roughly 20 live invocations worst case.
- **FR-004**: Every candidate route in the CAR-001 manifest MUST cite the shared evidence of its (model, effort) tuple by deterministic reference, computed by joining the manifest's `model_selector`/`effort_selector` fields against the snapshot's per-tuple evidence records, each keyed by a deterministic, computable `tuple_id` (exact `tuple_id` format is a Plan-level decision). The system MUST NOT probe the 37 routes individually, and the snapshot MUST NOT persist a duplicate `candidate_route_id`→`tuple_id` map (constitution VI: the join key already exists in the committed CAR-001 manifest).
- **FR-005**: All probes within a single snapshot MUST use one identical fixed canary prompt, and the snapshot MUST record the canary text and its hash so the invariant is verifiable.

#### Capability answers (CAP-Q1..CAP-Q6)

- **FR-006**: The snapshot MUST record the alias-to-dated-ID binding for each of the opus, sonnet, haiku, and fable aliases (CAP-Q1) from its canary observation.
- **FR-007**: The snapshot MUST answer CAP-Q1..CAP-Q6, and MUST record any question that cannot be answered from a bounded probe as an explicit open/gap entry rather than a failure or an assumed value.
- **FR-008**: The snapshot MUST represent alias re-pointing (CAP-Q6) as a route-change detection rule over observed-versus-resolved model IDs, recorded as an explicit open/gap entry in the primary bounded matrix (detection-rule-only): inducing re-pointing requires an `ANTHROPIC_DEFAULT_<MODEL>_MODEL`-style override that structurally collides with the FR-010 ambient unset-proof — the same run cannot both prove overrides absent and set one. Any induced re-pointing probe MUST run as a separate, explicitly-labeled phase with its own environment, never sharing the FR-010 unset-proof run, and be recorded as labeled inference.

#### Unavailable-model probe (CAP-Q5)

- **FR-009**: The unavailable-model probe MUST cover both surfaces — `claude -p --model <unavailable-id>` and a minimal subagent-frontmatter dispatch naming the same unavailable ID — recording each surface's observation separately (dispatch mechanism and reliability limits: see Assumptions).
- **FR-010**: Both unavailable-model probes MUST record proof — drawn from the actual operator environment used for the probe, not a synthetic or isolated substitute — that `--fallback-model`/`fallbackModel`, `CLAUDE_CODE_SUBAGENT_MODEL`, and `availableModels` (absent, not merely an empty list) are unset at probe time, so no documented native fallback, subagent model-override, or model-restriction mechanism can mask bare-platform behavior.

#### Snapshot artifact and evidence capture

- **FR-011**: The probe tool MUST write one canonical committed snapshot at `docs/ai/research/claude-runtime-capability-snapshot.json`, beside the CAR-001 candidate manifest; a re-probe MUST replace the file in place, relying on git history to preserve prior snapshots. The date embedded in `runtime_capability_snapshot_id` MUST equal the UTC date of the recorded capture timestamp, and a re-probe MUST increment the `V<n>` suffix monotonically; deterministic validation checks both, so the identity cannot silently disagree with the recorded timestamp.
- **FR-012**: For each probe, the snapshot MUST store the complete `--output-format json` stdout as raw evidence, with all home/user paths normalized to `<home>` per the existing release-readiness sanitization convention.
- **FR-013**: Each stored raw-evidence payload MUST carry a SHA-256 hash of its sanitized bytes, computed over the exact sanitized UTF-8 bytes of the stored payload, which MUST be committed verbatim as a string (not a parsed-and-reserialized object) so the hash reproduces from committed bytes; sanitization MUST occur before the snapshot is written, and no unsanitized raw payload (absolute home/user paths or machine-local session paths) may be committed.
- **FR-014**: Each probe run MUST record the authentication mode of the operator environment, derived from documented signals (`ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` present ⇒ API key; otherwise subscription). The `GET /v1/models` endpoint MUST be called only in API-key mode, with its returned dated IDs and per-model effort capability flags stored as corroborating — never alias-establishing — evidence (the endpoint documents no alias field, and API-catalog presence does not prove coding-client availability, FR-026); in subscription mode or any unreachable case its absence MUST be recorded as a gap, not a failure.

#### Schema contracts

- **FR-015**: The four record contracts — `runtime_capability_snapshot`, `telemetry_profile`, `route_resolution`, and exact-treatment replay — MUST be published as one review-visible JSON Schema file with a `$def` for each record type, located under `docs/ai/research/`. The schema file MUST follow the CAR-001 schema conventions (JSON Schema draft 2020-12, `$id`, `additionalProperties: false`, camelCase `$defs`, shared `sha256`/`nullableString` primitives) and pin an instance-level `schema_version` (const) that every record carries; the contract starts its own version line at `1.0.0`. ID-bearing fields MUST carry identical pattern constraints everywhere they appear across `$defs` (e.g. `runtime_capability_snapshot_id` is validated by the same pattern in the snapshot, route-resolution, and telemetry-profile `$defs`), so no `$def` accepts as free text an ID another `$def` pattern-enforces.
- **FR-016**: The schema MUST be validated by standard-library-only Python logic in `claude_trace_schema.py` (no third-party dependencies), mirroring the CAR-001 manifest-schema plus parity-validator pattern.
- **FR-017**: The JSON Schema contract MUST remain platform-neutral, readable and checkable by Codex-side parity work without executing Python.

#### Telemetry capability profile

- **FR-018**: The telemetry capability profile MUST be versioned and scoped to the pinned Claude Code client version, which the profile records.
- **FR-019**: The telemetry profile MUST classify every field as exactly one of `stable_native`, `derived`, `derived_from_controlled_configuration`, or `unavailable`. At minimum, the profile MUST classify the following `SDKResultMessage` fields (code.claude.com/docs/en/agent-sdk/typescript) as `stable_native`: `usage.input_tokens`, `usage.output_tokens`, `usage.cache_read_input_tokens`, the per-TTL pair `usage.cache_creation.ephemeral_5m_input_tokens`/`usage.cache_creation.ephemeral_1h_input_tokens`, the flat aggregate `usage.cache_creation_input_tokens` (documented as the sum of the per-TTL pair — an optional cross-check, not a substitute for the per-TTL breakdown), `num_turns`, `duration_ms`, and the `modelUsage` per-model key set together with its token-count sub-fields (`inputTokens`, `outputTokens`, `cacheReadInputTokens`, `cacheCreationInputTokens`, `contextWindow`). The profile MUST classify `total_cost_usd` and the `costUSD` sub-field within `modelUsage` as `derived` (documented client-side estimates from a bundled price table, code.claude.com/agent-sdk/cost-tracking), the effective model as `derived` (extracted from the `modelUsage` key set — `SDKResultMessage` carries no scalar `model` field), and effective reasoning effort as `derived_from_controlled_configuration` (no documented field returns it). A field whose exact result-message key or availability canonical documentation does not establish MUST be classified `unavailable` and recorded as a labeled observation, never assumed (FR-027).
- **FR-020**: The telemetry profile MUST preserve null-valued fields (nulls are recorded and classified, not dropped) so that "unavailable" is distinguishable from "absent."

#### Trace contracts (route resolution and exact-treatment replay)

- **FR-021**: The `route_resolution` record MUST bind, at minimum, agent identity, requested model alias, resolved dated model ID, effort level, instruction (system-prompt) hash, mutation contract, client version, fast-mode state, and env-override proof, and MUST carry the CAR-001 cross-reference IDs `candidate_route_id`, `agent_contract_id`, and `runtime_capability_snapshot_id` (reusing the manifest/snapshot strings verbatim) so each record joins to the CAR-001 manifest and the committed snapshot. The record MUST also bind nullable fallback-index and fallback-reason fields (AC-2.3) — populated by consumers only when a documented fallback chain fires, always null under CAR-002's unset-proof probes, nulls preserved — binding the trace fields without adding any fallback-ordering logic (which stays out of scope). The cross-reference IDs MUST be pattern-constrained in the schema (`candidate_route_id` matching the `CAR-001-CR-<NN>-<NN>` family; `agent_contract_id` matching `car.<name>.v<n>`), never free-text minimum-length strings.
- **FR-022**: The exact-treatment replay record MUST capture the complete treatment identity needed to reproduce one evaluated invocation — the `route_resolution` binding plus the observed record class and outcome — sufficient for CAR-003..CAR-011 to consume it as a binding contract without re-probing. The outcome's telemetry linkage MUST be resolvable: when the telemetry reference is non-null, deterministic validation MUST resolve it against the telemetry-profile field set (keeping AC-2.3's raw token categories, nulls preserved, reachable from the record); a dangling reference fails validation.

#### Validation enforcement and record classes

- **FR-023**: The probe writer MUST validate every observation against the schema before writing the snapshot; any invalid observation MUST abort the snapshot write (fail-closed), so no invalid snapshot can be committed. Partial-matrix outcomes follow the "Partial probe matrix" edge case: schema-invalid or unparseable observations abort the whole write; uninterpretable transport failures abort the run without recording "unavailable"; interpretable platform observations are recorded and the snapshot is written.
- **FR-024**: A deterministic unit test MUST validate committed synthetic fixtures for all four record classes plus the committed snapshot and the committed telemetry-profile document (against its `telemetry_profile` `$def`, enforcing SC-006's exactly-one-label and nulls-preserved requirements) on every CI run, and MUST additionally compute the route-to-tuple join for all 37 CAR-001 manifest candidate routes against the snapshot's per-tuple evidence (SC-005), failing closed if any route resolves to zero or to more than one tuple. The validator MUST also: recompute each stored `raw_output_sha256` over the committed sanitized payload bytes (and the canary hash over the recorded canary text) and fail on mismatch; verify no committed payload contains an unsanitized home/user/session path (re-checking the write-time FR-012/FR-013 guarantee continuously); and verify referential integrity — every `candidate_route_id`/`agent_contract_id` in a committed record resolves to an existing entry in the committed CAR-001 manifest, not merely a well-formed string.
- **FR-025**: Each of the four record classes MUST have a committed synthetic fixture, and every fixture MUST be a complete exact-treatment replay record carrying a full `route_resolution` binding: success (a fully-populated, scorable record), null (every nullable field present but null, not dropped), unavailable (the record class is unavailable, cross-referencing the corresponding unavailable observation in the committed snapshot via `runtime_capability_snapshot_id`, FR-021), and misdelivery (the observed/delivered model ID does not match the binding's resolved qualified ID, non-scorable, mirroring AC-2.3). The committed snapshot and the committed telemetry-profile document are validated separately (FR-024).

#### Evidence authority

- **FR-026**: Platform capability claims in the snapshot and profile MUST be sourced only from canonical `code.claude.com/docs/**` or `platform.claude.com/docs/**` pages; runtime probing MAY narrow availability but MUST NOT establish a platform fact absent from documentation.
- **FR-027**: Missing or conflicting platform documentation MUST fail closed — the affected capability is recorded as unresolved/unavailable and never assumed. The effort-configuration surface itself is documented (`--effort`; see Assumptions), but per-(model, effort) acceptance observed under silent-clamp-capable JSON output MUST be recorded as observation / labeled inference, never as a certified platform fact; any probe method step that canonical documentation does not establish MUST likewise be recorded as a labeled inference / proposed policy.

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
- **Split decision**: Ratified 3-slice split — 3 vertical work packages, design concept Q8 — with the concrete file-to-slice assignment resolved at Plan per design concept Open Question 5 ("exact file-to-slice assignment... deferred... once the concrete file list exists"), declared as work packages for PRSG split-PR routing: **WP1** — the complete JSON Schema contract with all four `$defs` (`runtime_capability_snapshot`, `telemetry_profile`, `route_resolution`, exact-treatment replay, FR-015) + the `claude_trace_schema.py` stdlib validator (FR-016) + its `suite-manifest.json` Layer 4 registration (FR-028) + the operator probe tool and fail-closed writer + committed snapshot (US1) — consolidated here because FR-015/FR-016/FR-028 each mandate exactly one schema file, one validator module, and one suite registration, and because the fail-closed writer (FR-023) cannot be built or tested without the schema it validates against; **WP2** — the telemetry capability profile document + `route_resolution`/exact-treatment replay fixtures, finalization, and CAR-003 handoff (US2, US3), consuming the schema WP1 already published rather than authoring new `$defs`; **WP3** — the four record-class synthetic fixtures, the deterministic validation test (extending the Layer 4 coverage WP1 registers), and the 37-route-to-tuple join validation (US4, SC-005). This consolidation shifts schema-foundation surfaces that Q8's narrative originally split across WP1/WP2 into WP1 alone; re-run the size estimator on WP1 at Plan and escalate at G5 rather than silently resolving if it breaches the 400 reviewable-LOC ceiling.

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

- **Runtime capability snapshot**: The single committed JSON artifact that answers CAP-Q1..CAP-Q6. Holds probe metadata (pinned client version, authentication mode, retrieval/probe method recorded as an explicit distinguishable element per AC-2.2 — bounded exact-invocation probe versus the API models endpoint under API-key authentication — canary text and hash, timestamp), per-tuple shared evidence, alias→dated-ID bindings, unavailable-model observations per surface, and open/gap entries for unanswerable questions. Identified by `runtime_capability_snapshot_id` in the form `CAR-002-RCS-<YYYY-MM-DD>-V<n>` (a re-probe bumps `V<n>`; git history preserves priors, FR-011), mirroring the CAR-001 snapshot-ID family.
- **Raw probe evidence (`rawEvidence` `$def`)**: A shared sub-component embedded within `runtime_capability_snapshot` entries — not one of the four top-level record classes validated by FR-025 — carrying the sanitized raw `--output-format json` payload and its SHA-256 hash for a single snapshot-side probe observation. Snapshot-side observations are one of the snapshot's alias→dated-ID bindings / per-tuple shared evidence, an unavailable-model observation, or an open/gap entry for an unanswerable question (optionally flagged per the interfering-configuration edge case); misdelivery does not apply at the snapshot layer. Represented by a `rawEvidence` `$def` — the exact sanitized payload committed verbatim as a string, plus `raw_output_sha256` and a `sanitization` const marker — deliberately distinct from CAR-001's bounded `boundedExtract` (700-char cap), because the ratified Q7 decision stores the full payload.
- **(model, effort) tuple**: The deduplicated probe unit — a unique model alias crossed with an effort level — whose shared evidence every resolving candidate route cites via a deterministic, computable `tuple_id` (a pure function of the CAR-001 manifest's `model_selector`/`effort_selector` fields on the resolving route; exact `tuple_id` format is a Plan-level decision). The CAR-001 manifest's 37 candidate routes currently reduce to 6 unique tuples.
- **Telemetry capability profile**: The versioned, per-client document that classifies every telemetry field as `stable_native`, `derived`, `derived_from_controlled_configuration`, or `unavailable`, preserving nulls. Identified by `telemetry_profile_id` in the form `CAR-002-TP-<YYYY-MM-DD>-V<n>`; the pinned client version is a recorded field (FR-018), not part of the ID. The Agent SDK's `SDKResultMessage` contract (code.claude.com/docs/en/agent-sdk/typescript) governs the field set returned under `claude -p --output-format json`; platform.claude.com/docs pages corroborate field semantics only, not the result-message shape. The effective model is extracted from the `modelUsage` key set, since `SDKResultMessage` carries no scalar `model` field. Field labels crosswalk from the CAR-001 candidate manifest's `source_class` taxonomy (`docs/ai/research/agent-route-candidate-manifest.schema.json`): `official_documentation` entries recording a returned value map to `stable_native`; `derived_from_controlled_configuration` maps to the same label; `undocumented` and `runtime_verification_needed`-only entries map to `unavailable`.
- **route_resolution record**: The binding of agent, requested model alias, resolved dated model ID, effort, instruction hash, mutation contract, client version, fast-mode state, and env-override proof. `route_resolution_id` is a per-invocation runtime identity minted by consumers (CAR-003+); CAR-002 fixes only the pattern — a non-empty unique string, recommended composition `candidate_route_id` + `runtime_capability_snapshot_id` + timestamp/uuid — and synthetic fixtures use deterministic literals (e.g. `CAR-002-RR-FIXTURE-001`).
- **Exact-treatment replay record**: The reproducible-treatment contract (route_resolution binding plus observed record class and outcome) consumed by CAR-003..CAR-011. It reuses `route_resolution_id` (plus an optional downstream-minted `execution_trace_id`, AC-2.3) rather than introducing a new CAR-002-owned identity.
- **JSON Schema contract**: One review-visible schema file with `$defs` for the four record types, under `docs/ai/research/`.
- **Probe tool / writer**: The operator-only entrypoint that runs the bounded probe matrix, sanitizes and validates observations, and fail-closed writes the snapshot.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can produce a committed snapshot that addresses all six capability questions (CAP-Q1..CAP-Q6) — each either answered with recorded evidence or explicitly marked open — in a single probe run bounded at roughly 20 live invocations.
- **SC-002**: Zero live model calls occur during any repository or CI test run; the full deterministic suite passes offline (no `claude` CLI, no network).
- **SC-003**: All four record classes (success, null, unavailable, misdelivery) have committed synthetic fixtures that the validation suite checks on every run (100% record-class coverage).
- **SC-004**: No invalid observation can reach the committed snapshot; the writer aborts before writing in 100% of invalid-observation cases.
- **SC-005**: Every one of the 37 CAR-001 manifest candidate routes resolves via the deterministic (model, effort) join to exactly one tuple and cites that tuple's shared evidence — zero routes resolve to zero tuples or to more than one tuple (100% route-to-tuple evidence coverage, zero routes without cited evidence). The snapshot MUST NOT store a duplicate per-route `candidate_route_id`→`tuple_id` map — the join is derived, not persisted (constitution VI).
- **SC-006**: Every field in the telemetry profile carries exactly one of the four classification labels and null-valued fields are preserved (100% field classification, zero dropped nulls).
- **SC-007**: A reviewer can read and check all four record contracts from a single JSON Schema file without executing any Python.
- **SC-008**: A downstream CAR spec (CAR-003..CAR-011) can bind a `route_resolution` or exact-treatment record from the published schema without needing any capability question that CAR-002 was responsible for answering.

## Assumptions

- **Pinned client**: The snapshot and telemetry profile are scoped to one pinned `claude` CLI version, recorded in the snapshot metadata; a different client version requires a re-probe.
- **Operator environment**: The operator runs the probe tool in an environment with a working `claude` CLI and valid authentication; the authentication mode (API key versus subscription) is recorded per run.
- **Effort-configuration surface**: Pinned to the documented `--effort` CLI flag (code.claude.com/docs/en/cli-reference — session-scoped, does not persist), with the `effortLevel` setting and `CLAUDE_CODE_EFFORT_LEVEL` env var as documented alternatives; the FR-027 labeled-inference fork does not fire for the surface itself. The probe matrix uses the per-model-supported subset of `low`/`medium`/`high`/`xhigh`/`max` (the `ultracode` session mode is not an effort level and is excluded). Because JSON-mode output applies an org effort cap silently (code.claude.com/docs/en/model-config: plain-text `--print` warns; `json`/`stream-json` clamps without warning), the effort-acceptance probe runs in plain-text `--print` or records an explicit no-org-cap assumption, and labels effort application as observation, not certification (FR-027).
- **Alias re-pointing (CAP-Q6)**: Alias re-pointing is represented as a route-change detection rule over observed-versus-resolved IDs and is detection-rule-only in the primary bounded matrix (FR-008): inducing it requires an `ANTHROPIC_DEFAULT_<MODEL>_MODEL`-style override that collides with the FR-010 ambient unset-proof. Any induced probe is a separate, explicitly-labeled phase with its own environment, recorded as labeled inference.
- **Fixed canary**: A single minimal canary prompt text is used identically across all probes in a snapshot: `Reply with the single word: ok` (exact UTF-8 bytes, no trailing newline). Its SHA-256 is computed over those exact bytes and stored in snapshot metadata alongside the raw-evidence hashes (FR-005/FR-013). The content is measurement-irrelevant — alias→ID binding and config acceptance come from the `--output-format json` metadata, not the reply — so only byte-invariance across a snapshot is contractual.
- **Unavailable-model probe mechanism (CAP-Q5)**: FR-009's subagent-frontmatter surface uses exactly one fixed dispatch mechanism — a file-based agent definition (`.claude/agents/<probe-name>.md`, YAML frontmatter naming the unavailable dated model ID) generated at probe time and not committed to the repository, invoked by an explicit `@agent-<probe-name>` mention in a fresh, non-`--bare` `claude -p` prompt (default `-p` loads project-level agent files the way an interactive session would). An inline `--agents '<JSON>'` definition is a documented Anthropic mechanism but does not satisfy FR-009 as written — it carries no YAML frontmatter and has zero precedent among this repo's file-based production and plugin agents — so it is not the required mechanism; an operator MAY run it in addition as a non-binding corroborating probe, since two structurally different dispatch mechanisms agreeing is stronger evidence than either alone. Two reliability limits MUST be recorded as labeled inference, not certified fact (FR-026/FR-027): which of the documented outcome paths (a soft remap evidenced via the result message's `modelUsage` field, a hard rejection error, or a silent fallback to an inherited model) this surface takes for a plain unavailable ID is not established by canonical documentation and is exactly the probe's observation to capture; and the equivalence between this project-level, unnamespaced file-agent-plus-mention dispatch and CAP-Q5's transfer target — the plugin-namespaced agents production routing dispatches via the Agent tool — is an inference, not a proven equivalence, that the snapshot entry MUST state.
- **Interference-surface set (FR-010)**: The unset-proof pins to `--fallback-model`/`fallbackModel`, `CLAUDE_CODE_SUBAGENT_MODEL`, and `availableModels` (absent — not merely an empty list — per code.claude.com/docs/en/model-config, already cited above for the effort-cap fact). Proof is drawn from the actual operator environment used for the probe run, not a synthetic or isolated stand-in; an isolated `CLAUDE_CONFIG_DIR` (code.claude.com/docs/en/debug-your-config) MAY be layered on in implementation as a defense-in-depth check, but its isolation is documented as partial — managed settings and already-exported shell env vars persist through it — so it does not by itself satisfy the proof obligation. `enforceAvailableModels` is documented on the same model-config page but is inert whenever `availableModels` is unset, so its observed value is recorded for audit completeness rather than gated as an independent unset requirement. On the subagent-frontmatter surface, `inherit` is equivalent to unset only when the pinned client version this snapshot records (FR-018) is v2.1.196 or later (code.claude.com/docs/en/sub-agents); on an earlier client, `inherit` instead forces the main-conversation model and is itself a masking risk. Organization-level model restrictions (Claude Enterprise) are entitlement-delivered at authentication and cannot be proven absent by local unset-proof; where the probe account may be subject to them, this MUST be recorded as an explicit labeled gap (FR-027), never assumed absent.
- **ID conventions**: CAR-002 committed artifacts use the CAR-001 spec-prefixed identity family — `runtime_capability_snapshot_id` = `CAR-002-RCS-<YYYY-MM-DD>-V<n>`, `telemetry_profile_id` = `CAR-002-TP-<YYYY-MM-DD>-V<n>` — mirroring `CAR-001-SNAPSHOT-2026-07-16-V2`. `route_resolution_id` is minted at runtime by consumers (CAR-003+); CAR-002 fixes only its pattern (non-empty unique string; recommended composition `candidate_route_id` + `runtime_capability_snapshot_id` + timestamp/uuid). Cross-references reuse the CAR-001 manifest's `agent_contract_id` (`car.<name>.v1`) and `candidate_route_id` (`CAR-001-CR-<NN>-<NN>`) strings verbatim.
- **Contract versioning**: The new JSON Schema contract's `schema_version` tracks that contract's own evolution and starts at `1.0.0`, independent of the CAR-001 manifest's `2.0.0` — "consistent with CAR-001" means the same pattern (const-pinned instance version + structural conventions), not the same number, which would falsely imply a v1 predecessor.
- **Consumption gate satisfied**: The scaffold-time consumption gate is met — amendment PR #362 merged and the parity validator passed 18/18 on branch base b57d21a8 — so the CAR-001 manifest's CAP-Q entries are the authoritative probe backlog this spec draws from.
- **Telemetry field grounding**: FR-019's field-to-label assignments are grounded in the Agent SDK's documented `SDKResultMessage` TypeScript contract (code.claude.com/docs/en/agent-sdk/typescript) and the cost-tracking page (code.claude.com/agent-sdk/cost-tracking); no canonical page prints a literal full `claude -p --output-format json` payload. Byte-for-byte key-spelling equivalence between raw CLI stdout and the documented type — in particular, confirming camelCase `modelUsage` (not the Python binding's snake_case `model_usage`, which does not govern CLI stdout) actually appears in raw stdout — remains a one-shot empirical confirmation carried to Plan; every field this confirmation has not yet run against is labeled observation, not certified fact (FR-027).
- **Toolchain**: Repository tooling is Python 3.11+ standard library only; verification is `python3 tests/speckit-pro/run-all.py` (there is no separate build, typecheck, or lint surface).
- **Out of scope**: Corpus execution, scoring, statistics, and fallback ordering are deferred to CAR-003 and later; no payload, guidance, agent-frontmatter, prompt, or default edits are made; no live probing runs in CI or at test time.
