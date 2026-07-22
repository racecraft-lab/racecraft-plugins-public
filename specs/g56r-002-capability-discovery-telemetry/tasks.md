# Tasks: G56R-002 Capability Discovery and Exact Treatment

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), and all completed [checklists/](checklists/)

**Tests**: Strict TDD is mandatory. For each increment, record RED before the
smallest GREEN implementation, then REFACTOR and VERIFY without changing the
predeclared dispositions.

**Reviewability**: The capability adapter triggered the 400-LOC boundary and is
now safely subdivided behind its stable facade into 13 capability modules totaling
3,337 source lines (3,031 nonblank, non-comment); every capability module is at
or below 388 source lines. The treatment validator remains 1,912 source lines
(1,762 nonblank, non-comment), for 5,249 source lines (4,793 nonblank,
non-comment) across 14 production modules in the current US2 marker. T001-T015
no longer relies on a `no_safe_boundary` exception. The treatment-only size
exception remains scoped to T016-T025, while T026-T039 remains a separate
ordered marker; a capability module above 400 lines or broken independent
verification is still blocking.

**Format**: Every task includes an exact path, user-story marker, functional
requirement references, and an objective acceptance check. `[P]` is used only
for generated surfaces that do not share files or mutable inputs.

## Phase 1: User Story 1 - Capability Freeze (Priority: P1)

**Goal**: Revalidate current authority, bind one pinned client/surface matrix,
and publish an append-only tuple freeze with lossless exclusions.

**Independent Test**: Replay the sanitized 22-source/three-surface fixture and
prove that only source-admitted, supported, agreeing tuples are included; all
other tuples retain explicit tuple-local reasons and the freeze hash is stable.

### RED — Fixtures and Tests

- [x] T001 [US1] [FR-001] Verify `docs/ai/research/codex-agent-route-candidate-manifest.json` contains exactly 22 unique current `OPENAI-DOC-*` records, no active `OSL-*` IDs, valid claim bindings, and five effort-surface records whose malformed or undocumented values cannot admit a tuple before creating any G56R-002 fixture; Acceptance: a focused read-only assertion reports 22 current records, zero historical-active records, and explicitly rejects inherited punctuation-only effort tokens as authority.
- [x] T002 [US1] [FR-001] [FR-002] Create the sanitized source-refresh, client-identity, and app-server/CLI/picker matrix cases in `tests/speckit-pro/unit/fixtures/capability-treatment-replay/capability-matrix.json`, including current, changed, inaccessible, hidden, alias, disagreement, partial, duplicate-key, hash-failure, and zero-eligible cases; Acceptance: `python3 -m json.tool tests/speckit-pro/unit/fixtures/capability-treatment-replay/capability-matrix.json` passes and no raw or machine-specific value is present.
- [x] T003 [US1] [FR-001] [FR-002] Add failing canonical-JSON, digest, 22-row refresh, allowlisted-domain, client-identity, and three-surface binding tests to `tests/speckit-pro/unit/test-codex-capability-contract.py`; Acceptance: the focused test fails because `tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py` does not yet provide the required contract.
- [x] T004 [US1] [FR-002] [FR-003] Extend the same `tests/speckit-pro/unit/test-codex-capability-contract.py` RED suite for canonical model/effort joins, one-to-one aliases, hidden-picker visibility, lossless disagreements, tuple-local exclusion, aggregate invalidity, and zero-eligible freeze validity; Acceptance: every case has one explicit expected disposition and the focused test remains RED.
- [x] T005 [US1] [FR-004] Add RED tests in `tests/speckit-pro/unit/test-codex-capability-contract.py` for one canary per snapshot/model/effort, the closed result envelope, default-empty repository approval allowlist, required contract/implementation/result digests, timeout/output-cap/process-tree acknowledgements, zero retry, arbitrary self-approval rejection, every terminal class, raw-root containment/permissions, and deny-by-default sanitization; Acceptance: the tests launch no process, prove a structurally matching fake approval cannot authenticate caller-supplied bytes or promote availability, and fail only on missing adapter behavior, not malformed fixtures.
- [x] T006 [US1] [FR-003] [FR-004] Add RED tests in `tests/speckit-pro/unit/test-codex-capability-contract.py` for content-addressed snapshot/freeze IDs, complete tuple-decision hashing, immutable successor IDs, source/runtime authority separation, and raw-evidence exclusion; Acceptance: the suite demonstrates that editing any bound input changes a successor ID and that runtime-only admission is rejected.

### GREEN — Smallest Capability Adapter

- [x] T007 [US1] [FR-001] [FR-002] Implement canonical JSON/SHA-256, current-ledger and effort-surface selection/validation, punctuation-only/undocumented effort non-admission, allowlisted source-refresh records, and `client_identity_id` validation in `tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py`; Acceptance: T003 tests pass while T004–T006 remain the only RED cases.
- [x] T008 [US1] [FR-002] [FR-003] Implement versioned surface observations, canonical model/effort normalization, one-to-one alias checks, hidden visibility, disagreement preservation, aggregate invalidity, and tuple-local decisions in `tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py`; Acceptance: T004 tests pass with no surface winner or inferred value.
- [x] T009 [US1] [FR-004] Implement the closed canary result contract, versioned default-empty repository approval allowlist, fail-closed external/self-asserted executor paths, closed terminal taxonomy, descriptor-bound external raw-store and private-input validation, permission/single-link checks, deterministic pseudonymization, JSON-native allowlist sanitization, pre-parse JSON resource bounds, and canonical sanitized fixture output in `tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py`; Acceptance: T005 passes, nested path/link/replacement and alternate-container regressions fail closed, standalone canary envelopes always remain `unknown`, published canary arrays remain empty until trusted invocation or verifiable attestation exists, and no default path launches a process or network request.
- [x] T010 [US1] [FR-003] [FR-004] Implement runtime snapshot, executable tuple, append-only freeze, successor validation, and narrow `refresh-sources`, `identify-client`, `collect`, reserved fail-closed `canary --executor-result`, and `freeze` command dispatch in `tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py`; Acceptance: T006 passes, every caller-supplied executor result fails closed before consumption, and unsupported arguments fail nonzero without shell execution.

### REFACTOR and VERIFY

- [x] T011 [US1] [FR-001] [FR-004] Refactor only duplication introduced in the capability adapter while preserving the Codex-specific facade, stdlib-only imports, bounded inputs/outputs/timeouts, and every GREEN disposition; Acceptance: the focused test remains green, descriptor tree walking stays in the existing I/O responsibility, and every capability module remains below 400 source lines.
- [x] T012 [US1] [FR-001] Revalidate all 22 current source records through `tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py` into an operator-local temporary refresh file, recording canonical URLs, bounded extracts, digests, outcomes, and claim-scoped invalidations without rewriting `docs/ai/research/codex-agent-route-candidate-manifest.json`; Acceptance: 22 unique refresh outcomes exist and every adverse result names only its bound claims/routes.
- [x] T013 [US1] [FR-002] [FR-004] Collect or explicitly mark unknown the pinned app-server, CLI, and picker observations through `tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py`, keeping raw bytes under a configured external `raw_evidence_root`; Acceptance: all observations share one client identity, tracked outputs are sanitized, and any incomplete surface excludes only affected tuples.
- [x] T014 [US1] [FR-001] [FR-003] Publish the sanitized append-only handoff in `docs/ai/research/codex-g56r-002-executable-candidate-freeze.json` and its authority/method/unknown/deletion narrative in `docs/ai/research/codex-g56r-002-capability-evidence.md`; Acceptance: both artifacts bind the current ledger, snapshot, matrix, telemetry placeholder, all tuple decisions, hashes, and successor rule with zero raw live values.
- [x] T015 [US1] [FR-001] [FR-004] Run the US1 independent test in `tests/speckit-pro/unit/test-codex-capability-contract.py` and inspect the exact diff for source-authority drift, lossy normalization, retry, or raw evidence; Acceptance: focused tests pass and the diff contains none of those violations.

**Checkpoint**: Capability freeze is independently valid before treatment
schema work begins.

## Phase 2: User Story 2 - Telemetry and Exact-Treatment Contracts (Priority: P2)

**Goal**: Validate the closed telemetry inventory, six-ID objective join,
separate resolver/service behavior, and null-preserving treatment trace.

**Independent Test**: Replay profile, configured-proof, effective-evidence,
misdelivery, and reroute records and receive the predeclared proven, unknown,
non-scorable, or hard-fail disposition without fabricating a field.

### RED — Schema and Null Semantics

- [x] T016 [US2] [FR-005] [FR-006] Create sanitized telemetry-profile, configured-route, controlled-environment, six-ID objective, route-resolution, destination-assessment, structured treatment-failure, and exact-treatment records in `tests/speckit-pro/unit/fixtures/capability-treatment-replay/treatment-replay.json`; Acceptance: `python3 -m json.tool tests/speckit-pro/unit/fixtures/capability-treatment-replay/treatment-replay.json` passes and every closed-inventory field has source/class/completeness/claim/observation-rule metadata.
- [x] T017 [US2] [FR-005] Add RED tests for all seven classifications, profile-key uniqueness, cross-surface non-inheritance, omitted-as-undocumented, required observation-state rules, typed value/null/evidence behavior, configured-proof consumption, and missing-as-unknown behavior in `tests/speckit-pro/unit/test-codex-capability-contract.py`; Acceptance: failures identify only missing `treatment_trace_schema.py` behavior.
- [x] T018 [US2] [FR-002] [FR-006] Add RED tests for all six non-null objective IDs, the controlled-environment owner registry and client/surface/repository/candidate/work-item equality, duplicate owning IDs, preferred/attempted/assigned/effective route fields, agent/model/effort/configuration hashes, sandbox/approvals/mutation class, expected/loaded skills/MCP/tools, parent configuration, client/overrides, delivery canary, context, and parent-child graph in `tests/speckit-pro/unit/test-codex-capability-contract.py`; Acceptance: a missing/duplicate environment owner or mismatched binding deterministically fails while repeated foreign-key references remain valid.
- [x] T019 [US2] [FR-006] [FR-007] Add RED tests for structured treatment failures, raw token vector, request/turn count, wall time, retries, compaction, validation, cancellation, failed/abandoned work, terminal state, outcome/acceptance, raw reroute events, separate destination route/agent/prequalification assessments, ambiguous joins, same-agent prequalified continuation, and non-scorable/hard-fail dispositions in `tests/speckit-pro/unit/test-codex-capability-contract.py`; Acceptance: each failure class has one explicit expected result, missing/mismatched destination proof hard-fails, and resolver fields never change after a service reroute.

### GREEN — Neutral Schema Validator

- [x] T020 [US2] [FR-005] Implement telemetry-profile entry validation, single-client closed-inventory ownership, class/claim semantics, profile-key uniqueness, required observation-state rules, and typed value/null/evidence validation in `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py`; Acceptance: T017 passes with missing/native fields never inferred and an absent surface binding never authorizing a top-level claim.
- [x] T021 [US2] [FR-002] [FR-005] [FR-006] Implement configured-route proof, six-ID foreign-key and owning-ID uniqueness validation, controlled-environment and experiment-policy owner lookup and consistency, content-addressed route/policy/trace IDs, reciprocal acyclic trace-graph validation, exact agent/configuration/tooling treatment fields, structured treatment failures, and route-resolution validation in `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py`; Acceptance: T018 passes, missing owners and malformed graphs fail, repeated foreign-key references remain allowed, configured proof establishes requested assignment only after complete observed reroute monitoring, and an observed supported route with canonical model/effort reaches the effective-evidence success path without claiming an undocumented effective-effort field.
- [x] T022 [US2] [FR-006] [FR-007] Implement resource/lifecycle validation, raw service-reroute association, separate destination assessment, read-only qualification-evidence registry lookup, requested-route non-scorability, same-agent `owned_external` continuation, synthetic-fixture non-authority, and missing/mismatched/unknown/unapproved/ambiguous hard-fail rules in `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py`; Acceptance: T019 passes, qualification evidence is consumed but never created, synthetic records cannot authorize live continuation, and every disposition preserves resolver evidence plus the exact detailed reroute cause.

### REFACTOR and VERIFY

- [x] T023 [US2] [FR-005] [FR-007] Refactor shared validation primitives only within `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py`, retaining vendor-neutral record shapes and leaving Codex collection in `codex_capabilities.py`; Acceptance: focused tests, executable JSON-Schema parity, descriptor-relative retained-file loading through one identity-bound directory snapshot with directory-race detection, sanitized parser/CLI failures, complete path privacy, one-day bounded pending claims participate in the latest effective deletion deadline and reject late promotion, append-only writers acquire the shared parent-directory lock before `.capability-evidence-write-*` visibility, source and unknown-attempt captures accept concurrent winners only after exact-byte verification, both materializers hold the retention lock through permanent deletion-tombstone inspection and publication, source bodies require normalized plain text with no raw markup, source-ID-sorted digest recomputation during normalization and raw validation, and full binding invalidation on body change, crash-retained reserved temporaries recover only after directory, temporary, and exact directory-relative inode proof, linked temporaries additionally require exact target/byte proof, post-unlink hard-link races never republish or accept a substitute inode, pseudonyms are generated only at explicit profile fields, and authority/condition/lifecycle negative cases remain green without a cross-vendor probing abstraction.
- [x] T024 [US2] [FR-005] [FR-006] Bind the published telemetry profile, validated treatment-contract digest, and exact retained treatment-evidence-set digest into `docs/ai/research/codex-g56r-002-executable-candidate-freeze.json`, creating a strictly later successor freeze ID rather than editing the prior content identity in place; Acceptance: the actual published successor directly passes the canonical treatment-aware validator, every treatment-bound publication/successor API requires externally supplied expected IDs, the successor references the prior ID, only an included, source-admitted, availability-supported, surface-agreed tuple can publish `proven`, excluded tuples retain non-authoritative dispositions, publication does not predate any bound route resolution or non-null observation capture, retained source/observation/canary evidence is semantically revalidated before registration, retention deadlines derive from trusted registration, a durable intent governs the exact record set before output, an identity-bound append-only output is re-read as exact canonical single-link bytes before the matching receipt, recovered existing outputs preserve that invariant, capability JSON fails closed beyond 64 nesting levels or 100,000 total nodes, source-capture size/type bounds apply before parsing or hashing, and an identical concurrent capture is adopted only after verified content identity and parent-directory synchronization.
- [x] T025 [US2] [FR-005] [FR-007] Run the US2 independent test in `tests/speckit-pro/unit/test-codex-capability-contract.py` and inspect the diff for configured-as-effective, missing-reroute-as-none, service-as-resolver, or fabricated null values; Acceptance: focused tests pass and none of the four prohibited patterns exists.

**Checkpoint**: Capability freeze and treatment contracts are independently
green before replay integration.

## Phase 3: User Story 3 - Sanitized Synthetic Replay (Priority: P3)

**Goal**: Prove byte-stable, offline dispositions for every required success
and failure class before any outcome-bearing G56R-003 run.

**Independent Test**: Validate hashes before parsing and replay the complete
fixture set twice with identical normalized outputs, dispositions, and digests
without network or raw-store access.

### RED — Complete Replay Matrix

- [ ] T026 [US3] [FR-008] Extend `tests/speckit-pro/unit/fixtures/capability-treatment-replay/treatment-replay.json` with success, explicit-null, unavailable, misdelivery, approved same-agent reroute, unapproved/unidentifiable reroute, discovery loss, and surface disagreement cases plus expected dispositions; Acceptance: all eight classes are present, sanitized, schema-versioned, and the adjacent digest manifest placeholders are the only intentionally failing values.
- [ ] T027 [US3] [FR-008] Add RED tests for digest-manifest lookup, raw-byte hash-before-parse, undeclared-field rejection, raw-store/network prohibition, canonical serialization, two-pass equality, fixture-local pseudonyms, and canary non-promotion in `tests/speckit-pro/unit/test-codex-capability-contract.py`; Acceptance: the test fails on missing replay behavior or digest mismatch before fixture parsing and never contacts external state.

### GREEN — Deterministic Replay

- [ ] T028 [US3] [FR-008] Implement fixture provenance validation, out-of-band digest-manifest lookup, raw-byte hash-before-parse, normalized dispositions, two-pass comparison, and narrow `replay --fixture --digest-manifest --repeat` dispatch in `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py`; Acceptance: T027 passes offline and `--repeat` rejects values other than the contract-required two for the committed fixture.
- [ ] T029 [US3] [FR-008] Create `tests/speckit-pro/unit/fixtures/capability-treatment-replay/fixture-digests.json` and replace its placeholders with SHA-256 values over the exact canonical bytes of `capability-matrix.json` and `treatment-replay.json`; Acceptance: both raw-byte hashes validate before fixture parsing and a one-byte mutation fails.
- [ ] T030 [US3] [FR-008] Run the US3 independent replay through `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py` with the committed digest manifest; Acceptance: two offline passes return byte-identical normalized output, dispositions, and digests for all eight classes.

## Phase 4: Integration, Documentation, and Polish [US1] [US2] [US3]

- [ ] T031 [US1] [FR-001] [FR-008] Register `tests/speckit-pro/unit/test-codex-capability-contract.py` in `tests/speckit-pro/suite-manifest.json` with a unique label and deterministic default-layer execution; Acceptance: suite-manifest validation and the focused test both pass.
- [ ] T032 [P] [US3] [FR-008] Regenerate `docs-site/src/content/docs/reference/tests.md` from repository sources with `pnpm --dir docs-site reference:generate` and verify it with `pnpm --dir docs-site reference:check`; Acceptance: the generated page contains the new test entry and has no hand-edited content.
- [ ] T033 [P] [US1] [FR-003] Regenerate `specs/g56r-002-capability-discovery-telemetry/SPEC-MOC.md` with the authoritative spec-index helper and run its check mode; Acceptance: the generated backlinks include tasks/checklists/contracts and the index check is clean.
- [ ] T034 [US1] [FR-004] [FR-008] Execute every command in `specs/g56r-002-capability-discovery-telemetry/quickstart.md` that is deterministic and offline, and review operator-only commands without launching repeated probes; Acceptance: focused replay and documented commands match the implemented CLI while raw collection remains outside CI.
- [ ] T035 [US1] [FR-001] [FR-008] Run `python3 -u tests/speckit-pro/run-all.py --layer 1` and the focused G56R-002 test; Acceptance: both pass with no generated-reference or source-authority regression.
- [ ] T036 [US2] [FR-005] [FR-008] Run `python3 -u tests/speckit-pro/run-all.py`, `pnpm --dir docs-site reference:check`, JSON validation, and `git diff --check`; Acceptance: the full deterministic suite and all hygiene checks pass.
- [ ] T037 [US3] [FR-008] Audit tracked changes and history against the prohibited-scope contract in `docs/ai/specs/.process/G56R-002-workflow.md` for raw live responses, credentials, absolute paths, repository remotes, corpus/scorer/qualification/ranking/preference/fallback-order/installer/agent/payload/default/version changes, Bash, `jq`, third-party packages, or a cross-vendor prober; Acceptance: all prohibited-scope counts are zero or confined to explicit non-goal prose.
- [ ] T038 [US1] [FR-003] [FR-008] Re-run the reviewability gate against `docs/ai/specs/.process/G56R-002-workflow.md` and inspect implementation LOC/files; Acceptance: the stable capability facade exports exactly its supported public API and no private trust primitives, every focused capability module remains below 400 source lines, the current marker plan preserves independently verified US1/US2/US3 checkpoints, and no correctness or safety exception remains for capability code.
- [ ] T039 [US1] [FR-001] [FR-008] Validate the final PR title and changed-file contract through the release-readiness gate invoked by `.github/workflows/pr-checks.yml` using a lowercase conventional scope; Acceptance: `<type>(<lowercase-scope>): <plain English description>` passes with the exact planned changed-file set.

## Dependencies & Execution Order

1. T001 blocks every source claim.
2. T002–T006 establish RED; T007–T010 make the capability increment GREEN;
   T011–T015 complete and verify US1.
3. T016–T019 must remain RED until US1 is green; T020–T025 complete US2.
4. T026–T027 establish replay RED; T028–T030 complete US3.
5. T031 blocks generated reference and full-suite work. T032 and T033 may run
   in parallel because they modify independent generated files. T034–T039 are
   sequential final gates.

### Incremental Delivery

1. Deliver and verify the US1 capability-freeze contract before opening the
   treatment module.
2. Add US2 telemetry and exact-treatment validation without changing US1
   candidate dispositions.
3. Add US3 offline replay without network, raw-store, scorer, or qualification
   dependencies.
4. Complete polish only after all three independent checkpoints are green.

## Parallel Opportunities

- **2 tasks**: T032 and T033 after T031.
- No implementation task is parallelized across the 13 production modules;
  the accepted increment order is the safer review path.

## Traceability Summary

| Requirement | Tasks |
|---|---|
| FR-001 | T001–T003, T007, T012, T014, T031, T035, T039 |
| FR-002 | T002–T004, T007–T008, T013, T018, T021 |
| FR-003 | T004, T006, T008, T010, T014, T024, T033, T038 |
| FR-004 | T005–T006, T009–T011, T013, T034 |
| FR-005 | T016–T017, T020–T021, T023–T025, T036 |
| FR-006 | T016, T018–T022, T024 |
| FR-007 | T019, T022–T023, T025 |
| FR-008 | T026–T039 |

## Deferred Work

- Corpus execution, scoring, statistics, qualification, ranking, and candidate
  preference remain G56R-003.
- Resolver/fallback policy and installation remain G56R-006.
- Agent TOML, generated payload, defaults, and release/version changes remain
  outside G56R-002.
- No deferred item is required for G56R-002 contract or replay acceptance.
