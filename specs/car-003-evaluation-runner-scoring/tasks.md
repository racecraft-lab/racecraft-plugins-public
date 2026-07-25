---

description: "Task list for CAR-003 evaluation runner, fixtures, scoring, and statistical analysis"
---

# Tasks: Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Input**: Design documents from `specs/car-003-evaluation-runner-scoring/`

**Prerequisites**: `plan.md`, `spec.md` (58 FRs, SC-001…SC-025, four resolved
Clarify sessions), `research.md`, `data-model.md`, `contracts/` (8 schemas),
`quickstart.md`, `checklists/` (4 domains, all gaps closed).

**Tests**: REQUIRED. This feature is implemented under strict TDD — every
implementation task is preceded by a test task that MUST be written first and
MUST be observed FAILING before the implementation lands.

**Verification command**: `python3 tests/speckit-pro/run-all.py`. This is the
only gate. There is no BUILD, TYPECHECK, or LINT command in this repository.
Baseline is green at **3251/3251** with zero live calls; any later failure is
attributable to CAR-003.

**Organization**: Tasks are grouped by user story. Story-to-slice mapping is
fixed by `plan.md` and MUST NOT be reordered.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `[US1]`…`[US4]`; Setup, Foundational, and Polish carry no label
- Every task names an exact repository-relative file path

## Path Conventions

- Shipped plugin source: `speckit-pro/speckit_pro_runner/`
- Repository-only harness: `tests/speckit-pro/layer6-efficiency/lib/`
- Unit tests: `tests/speckit-pro/unit/`
- Replay fixtures: `tests/speckit-pro/layer6-efficiency/fixtures/`
- Published evidence: `docs/ai/research/`

All paths in this file are repository-relative. Absolute paths MUST NOT appear
in any authored artifact — the tree-wide privacy scan fails on them.

## Review Slices (ordered — do NOT reorder)

| Slice | Stories | Scope | Authored files | Logic LOC | Shipped production files |
|---|---|---|---|---|---|
| 1 — roadmap Work Package A, **keep intact** | US1 + US2 | Successor freeze, canonical materializer, exact-treatment runner | 11 | 735 | 1 |
| 2 | US3 | Governed corpus, hard gates, blinded scoring | 7 | 533 | 0 |
| 3 | US4 | Experiment policy, statistics, calibration pilot | 7 | 590 | 0 |

Whole feature: 23 authored files, 1,858 reviewable LOC, 1 shipped production
file (`speckit-pro/speckit_pro_runner/materializer.py`).

**Reviewability note (read before running the tasks-mode gate).** The mechanical
tasks-mode estimator projects reviewable LOC as `task count x 40` and classifies
production files by path prefix. Neither heuristic fits this repository: the
Python lives under `speckit-pro/` and `tests/speckit-pro/`, and this task list is
deliberately fine-grained for TDD. The authoritative figures are the hand-derived
per-slice numbers above, ratified in `plan.md` **Reviewability Gate** and checked
by the setup-mode gate. A tasks-mode block on `86 x 40` is a known false positive
and MUST NOT be used to split Work Package A, which FR-025 and the roadmap
require to stay intact.

## Standing Constraints

- **One materializer.** It is implemented once, under
  `speckit-pro/speckit_pro_runner/`. No task may implement it under `tests/` and
  relocate it later — that would run the artifact and hash regeneration ritual
  twice.
- **Consume, do not modify**:
  `tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py`,
  `claude_trace_schema.py`, `treatment_trace_io.py`, `treatment_trace_bundle.py`,
  `treatment_trace_authority.py`.
- **Never modify** archived CAR-002 evidence or its schemas, nor the repo-level
  shared contracts at `tests/speckit-pro/layer6-efficiency/contracts/`
  (`capability-freeze.schema.json`, `marker-checkpoint.schema.json`,
  `treatment-record.schema.json`). Those are byte-identical across the Claude and
  Codex worktrees; a unilateral edit is a cross-platform break.
- **Python 3.11+ standard library only.** No new Bash, no `jq`, no new packages.
- **Live-campaign tasks are OPERATOR-ONLY** and never run in the default suite.
  The default suite is deterministic replay with zero live model calls.
- Tasks marked **OPERATOR-ONLY** below are excluded from
  `python3 tests/speckit-pro/run-all.py` by construction.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the branch and measurement baseline every later task is
judged against.

- [x] T001 Sync the default branch into this branch before any slice-1 edit, then confirm `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py` is still unmodified on both the default branch and the in-flight Codex twin branch; resolve any overlap on that file by `git merge`, never rebase (FR-043)
- [x] T002 [P] Record the pre-change baseline in the slice-1 PR packet notes: run `python3 tests/speckit-pro/run-all.py` and capture the 3251/3251 result plus wall-clock, establishing the 6-minute CI budget reference and the zero-live-call starting point (FR-057, SC-019)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared, jointly-owned surface and the reviewability decision.
Both must land before any module work begins.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 Re-verify the reviewability budget against this task list's actual file and slice scope and record the split decision (three ordered slices, Work Package A intact) in `specs/car-003-evaluation-runner-scoring/plan.md` Reviewability Gate; a regenerated set larger than twelve artifacts means re-run the gate and record the result, never split Work Package A (FR-025, SC-013)
- [x] T004 [P] TDD RED: add a failing assertion in `tests/speckit-pro/unit/test-exact-treatment-runner.py` that the dual-platform prompt-emulation runner and the lexical quality scorer emit a non-release marker in their results metadata, and that no historical smoke result can be read as route qualification evidence; observe FAIL before T005 (FR-007)
- [x] T005 Demote the shared dual-platform smoke runner: add the `non_release_evidence` marker to results metadata in `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py` and make T004 pass. **This file is jointly owned with the in-flight Codex twin branch.** It is currently 495 lines and neither the default branch nor the twin has modified it, so this side may land first. T001 must have synced the default branch; resolve any later overlap by `git merge`, never rebase. This is the ONLY task that edits this file (FR-007, FR-043)

**Checkpoint**: Shared surface claimed, reviewability decision recorded. Slice 1
module work can begin.

---

## Phase 3: User Story 1 - Publish Successor Capability Freeze (Priority: P1) — Slice 1

**Goal**: Publish a versioned, non-empty, additive successor capability freeze
admitting only tuples present in both the official-source candidate ledger and
the pinned runtime, while CAR-002 stays byte-unchanged.

**Independent Test**: Collect the pinned runtime catalog, compare against the
official-source ledger, and verify the new freeze is additive, non-empty,
source-bound, and traceable with zero CAR-002 mutation — `quickstart.md`
section 3b.

**Slice**: 1 (roadmap Work Package A — keep intact)

### Tests for User Story 1 (write FIRST, observe FAIL)

- [x] T006 [P] [US1] TDD RED: create `tests/speckit-pro/unit/test-successor-capability-freeze.py` asserting that `specs/car-003-evaluation-runner-scoring/contracts/successor-capability-freeze.schema.json` and `car-003-additive-records.schema.json` parse, and that the closed exclusion taxonomy is exactly the nine members `source_not_admitted`, `effort_not_source_admitted`, `effort_source_not_admitted`, `canonical_effort_unknown`, `surface_evidence_incomplete`, `surface_disagreement`, `alias_repoint_unresolved`, `availability_not_proven`, `topology_control_not_candidate_effort` (FR-029, SC-003)
- [x] T007 [US1] TDD RED: in `tests/speckit-pro/unit/test-successor-capability-freeze.py`, assert the collection record carries command contract, client version and distribution, sanitized account and environment boundary, raw and parsed catalog digests, observed models, alias bindings, defaults, supported efforts, timestamps, and invalidation criteria, and that effort admission is recorded as a bounded configuration-acceptance claim rather than as verified support (FR-002)
- [x] T008 [US1] TDD RED: in `tests/speckit-pro/unit/test-successor-capability-freeze.py`, assert set-intersection admission (a runtime-only tuple is excluded `source_not_admitted`), that a diagnostic surface can corroborate or invalidate but never admit, that a probe/diagnostic disagreement forces recorded investigation or exclusion rather than being logged and ignored, that fast mode records `topology_control_not_candidate_effort`, that an unmapped source effort records `canonical_effort_unknown`, and that the full ordered ladder `low`, `medium`, `high`, `xhigh`, `max` is probed per role-eligible model with `high` recorded as the documented search origin (FR-003, FR-004, FR-005, FR-040, SC-002, SC-018)
- [x] T009 [US1] TDD RED: in `tests/speckit-pro/unit/test-successor-capability-freeze.py`, assert every one of the ten closed authority failures blocks publication — empty intersection, malformed source, malformed catalog, stale collection, untrusted collection, failed sanitization, failed retention, identity mismatch, digest mismatch, attempted historical mutation — that missing required provenance maps to `malformed_catalog` and not `untrusted_collection`, that no freeze record is emitted at all when authority failures exist, and that a tuple whose `runtime_evidence_digest` resolves to the archived CAR-002 snapshot is rejected with `availability_not_proven` (FR-028, FR-044, SC-016)
- [x] T010 [US1] TDD RED: in `tests/speckit-pro/unit/test-successor-capability-freeze.py`, assert 100% of CAR-002 artifact paths and IDs are byte-unchanged after freeze generation, and that a snapshot containing any non-allowlisted account, authentication, credential, raw-response, private-host, absolute-path, remote, billing, or plan field blocks publication rather than being silently stripped (FR-001, FR-027, SC-001, SC-015)
- [x] T011 [US1] TDD RED: in `tests/speckit-pro/unit/test-successor-capability-freeze.py`, assert alias re-point detection reads all five observables (requested alias, identity resolved by CAR-003's own successor freeze, run-observed identity from the per-model usage breakdown, complete eight-member `env_override_proof`, pinned client version at freeze and run time); that unchanged route plus proven-unset overrides plus unchanged client version yields platform attribution never reported as a SpecKit Pro fallback; that a plugin-initiated substitution yields resolver fallback; that an incomplete proof, `claude_code_subagent_model_unset=false`, a changed client version, or a freeze binding resolving to the archived snapshot each record `alias_repoint_unresolved` and block admission; and that a behavioral difference with no identity change is a separate diagnostic condition (FR-039, FR-045, SC-017)
- [x] T012 [US1] TDD RED: in `tests/speckit-pro/unit/test-successor-capability-freeze.py`, assert all four refresh triggers (client change, catalog change, alias re-point, source-ledger change) invalidate freeze admission and every unexecuted derived binding, additively invalidate affected experiment, score, and decision bundles, leave immutable traces and already-bound pairs unchanged and marked invalidated rather than rebound, mark in-flight attempts for a re-pointed alias non-scorable, and that a source-ledger change alone never admits a tuple the pinned runtime never supported (FR-041)

### Implementation for User Story 1

- [x] T013 [US1] Create `tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py` with the runtime catalog collection record and its provenance-completeness check, driven from `contracts/successor-capability-freeze.schema.json`; reuse `lib/claude_capabilities.py` for sanitization and payload hashing without modifying it (FR-002) — makes T007 pass
- [x] T014 [US1] Implement set-intersection admission, the diagnostic-corroborate-never-admit rule, the recorded-disagreement path, and topology-control classification in `tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py` (FR-003, FR-004, FR-005) — makes the admission half of T008 pass
- [x] T015 [US1] Implement the evidence-backed effort normalization map onto the ordered ladder `low`…`max` and the per-model supported-effort recording, including `high` as the documented search origin and `canonical_effort_unknown` for unmapped values, in `tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py` (FR-003, FR-040) — makes the ladder half of T008 pass
- [x] T016 [US1] Implement the closed exclusion-taxonomy emitter so every excluded tuple carries a machine-checkable reason, in `tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py` (FR-029) — makes T006 pass
- [x] T017 [US1] Implement the fail-closed publication gate in `tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py`: the ten-condition authority-failure mapping, the emit-no-freeze-record diagnostic-only state, the machine-checkable non-reuse check binding each admitted tuple's runtime evidence to this freeze's own collection record, the deny-by-default allowlist inspection, and the CAR-002 immutability assertion (FR-001, FR-027, FR-028, FR-044) — makes T009 and T010 pass
- [x] T018 [US1] Implement the alias re-point detector and the additive attribution record in `tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py`, carrying the `{id, digest}` binding to the specific CAR-003 freeze the resolved identity was read from and recording the elimination argument as bounded by its enumerated cause set (FR-039, FR-045) — makes T011 pass
- [x] T019 [US1] Implement the four versioned refresh triggers and their additive-invalidation semantics in `tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py`, recording per trigger which evidence is invalidated and which survives (FR-041) — makes T012 pass
- [x] T020 [P] [US1] Author `tests/speckit-pro/layer6-efficiency/fixtures/car-003-alias-repoint-replay.json` supplying a divergent observed identity below the live trigger path while environment overrides remain genuinely unset, so detector validation never requires setting the override the proof requires unset; keep it bounded in size so suite cost does not scale with campaigns (FR-046, FR-057)
- [x] T021 [US1] Register `tests/speckit-pro/unit/test-successor-capability-freeze.py` in the Layer 4 (`"id": "4"`) `scripts` array of `tests/speckit-pro/suite-manifest.json` — each entry is an object `{"path", "label", "baseline"}`, not a bare path string, with `"baseline": null` for these unit tests and confirm `python3 tests/speckit-pro/run-all.py --layer 4` is green
- [ ] T022 [US1] **OPERATOR-ONLY, NEVER IN THE DEFAULT SUITE.** As the first operator action of slice 1, run the `claude -p --model <alias-or-id>` print-mode canary probe on the pinned client over the full ordered effort ladder for every role-eligible model under an explicit, local, pinned, budgeted invocation, and publish `docs/ai/research/claude-car-003-successor-capability-freeze.json`. Record the result whichever way it resolves, including whether the `opus` alias has re-pointed since the archived snapshot. Verify the published file passes deny-by-default sensitive-field inspection and contains no absolute paths or session identifiers (FR-002, FR-040, SC-002, SC-018, SC-015)

**Checkpoint**: The successor freeze publishes or fails closed with a recordable
reason, and CAP-Q6 has an answer.

---

## Phase 4: User Story 2 - Prove Exact Treatment Before Scoring (Priority: P1) — Slice 1

**Goal**: Materialize and run the actual named-agent policy through one canonical
shipped materializer, prove the exact treatment each candidate received, and emit
immutable replayable traces before any outcome is scored.

**Independent Test**: Materialize an admitted executable route, run a disposable
calibration objective, and verify all mandatory treatment evidence exists before
any score bundle is accepted — `quickstart.md` sections 3a, 3d, and 6.

**Slice**: 1 (roadmap Work Package A — keep intact)

### Tests for User Story 2 (write FIRST, observe FAIL)

- [ ] T023 [P] [US2] TDD RED: create `tests/speckit-pro/unit/test-canonical-agent-materializer.py` asserting that hashing the destination file's exact UTF-8 bytes read back from disk reproduces the recorded hash; that six drift classes parsed-field equivalence cannot see each change the hash (key order, whitespace, comments, unknown keys, line endings, encoding); that a hash computed from the in-memory render buffer is rejected as proof; that the destination path is verified separately and absent from the digest preimage so identical content at a different path hashes identically; and that a definition declaring `hooks`, `mcpServers`, or `permissionMode` cannot be proved by the materialization branch (FR-006, FR-008)
- [ ] T024 [US2] TDD RED: in `tests/speckit-pro/unit/test-exact-treatment-runner.py`, assert every field named by the versioned mandatory-observation manifest carries a non-null observed value and a classification other than `unavailable`; that an `unavailable` or null mandatory field records `mandatory_telemetry_missing` and blocks scoring; that the named agent is the `speckit-pro:<name>` spawn read from the run transcript rather than from the dispatch request; and that the effective model is read from the per-model usage breakdown with zero configuration-inferred substitutes (FR-009, SC-021)
- [ ] T025 [US2] TDD RED: in `tests/speckit-pro/unit/test-exact-treatment-runner.py`, assert every attempt binds a versioned environment contract before execution pinning `fast_mode_state=off`, a permitted client-version range, the parent-session model and effort, all eight members of `env_override_proof` with `claude_code_subagent_model_unset=true`, and the expected `authentication_mode`; that a confirmed divergence records `treatment_infrastructure_failure` on the treatment plane; that an unobservable environment records `required_evidence_missing` on the evidence-boundary plane and returns inconclusive; that the two never share a code; and that an authentication-mode divergence blocks outcome scoring rather than passing through (FR-042, FR-051, SC-020)
- [ ] T026 [US2] TDD RED: in `tests/speckit-pro/unit/test-exact-treatment-runner.py`, assert the score-eligibility predicate admits only `treatment_disposition=proven` with materialization or installed-policy proof, matching configured-route proof, complete mandatory observations, complete route-change monitoring, and environment conformance; that `scorable=false` forces ineligibility while `scorable=true` alone does not admit an outcome; that with several disqualifiers co-firing every fired code appears in `disposition_reasons` with no non-terminal cause discarded; and that the terminal disposition is the highest-precedence bucket `hard_fail` > `non_scorable_rerouted` > `unknown` > `proven` with no condition-level tie-break (FR-030, FR-031, SC-004)
- [ ] T027 [US2] TDD RED: in `tests/speckit-pro/unit/test-exact-treatment-runner.py`, assert each assigned attempt creates a new immutable `execution_trace_id` under the CAR-002 trace contract; that bundles reference traces by ID and digest without embedding or mutating them and without extending the frozen `exactTreatmentReplay.outcome` shape; that the trace digest is SHA-256 over the CAR-002 canonical JSON serialization and is recomputed at acceptance and replay; that a mismatched or dangling reference produces `trace_reference_integrity_failure` and blocks the decision bundle rather than rewriting either artifact; and that `resource_vector` and `reasoning_token_report` are re-derived from the digest-verified trace with any disagreement failing closed as `binding_digest_mismatch` on the schema plane (FR-010, FR-032)
- [ ] T028 [US2] TDD RED: in `tests/speckit-pro/unit/test-exact-treatment-runner.py`, assert paired arms execute with distinct per-arm cache roots, that each arm records observed isolation evidence naming the root actually used and its disjointness from the paired arm's, and that a pair recording `observed_shared` or `unobserved` contributes zero resource comparisons (FR-049, SC-024)

### Implementation for User Story 2

- [ ] T029 [US2] Create `speckit-pro/speckit_pro_runner/materializer.py` — the single shipped materialization contract owning rendered destination bytes and instruction/configuration digests; standard library only, no import reaching back into `tests/` (FR-006)
- [ ] T030 [US2] Implement the content-hash proof in `speckit-pro/speckit_pro_runner/materializer.py`: SHA-256 over destination bytes read back from disk after write with no normalization, re-serialization, newline translation, trailing-newline insertion, or key reordering; the destination path verified separately and excluded from the preimage; the in-memory-buffer path rejected; the bounded-equivalence guard rejecting any definition declaring `hooks`, `mcpServers`, or `permissionMode`; and the served branch plus loader scope recorded on the treatment record (FR-008) — makes T023 pass
- [ ] T031 [US2] Create `tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py` as the thin Layer 6 adapter that imports and calls the shipped materializer from `speckit-pro/speckit_pro_runner/materializer.py`; it MUST NOT define a second or parsed-only materializer (FR-006)
- [ ] T032 [P] [US2] Author `docs/ai/research/claude-car-003-mandatory-observation-manifest.json` — the versioned additive manifest naming every required treatment-profile field, since the frozen CAR-002 telemetry profile constrains only list cardinality and never enumerates the fields (FR-009)
- [ ] T033 [US2] Implement the mandatory-observation loader and completeness check in `tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py`, reading the manifest from T032 and recording `mandatory_telemetry_missing` for any null or `unavailable` mandatory field while leaving schema-nullable non-manifest fields permitted (FR-009)
- [ ] T034 [US2] Implement real-dispatch exact-treatment recording in `tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py`: the `speckit-pro:<name>` spawn read from the session transcript into `dispatch_namespace`, and the effective model read from the per-model usage breakdown into `observed_model_id`, never inferred from configuration, the requested alias, or the resolved route (FR-009) — makes T024 pass
- [ ] T035 [US2] Implement the versioned environment contract binding and pre-execution conformance check in `tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py`, pinning and comparing existing frozen CAR-002 fields only, with the confirmed-divergence and unobservable-environment branches on distinct closed codes and the authentication-mode comparison blocking scoring on divergence; report the count of attempts excluded on this ground (FR-042, FR-051) — makes T025 pass
- [ ] T036 [US2] Implement the score-eligibility predicate in `tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py`, treating the frozen `exactTreatmentReplay.scorable` flag as necessary but not sufficient and reading `treatment_disposition` from the shared treatment-record contract without introducing a parallel vocabulary (FR-030)
- [ ] T037 [US2] Implement independent derivation of every disqualifying condition, the union of fired codes into `disposition_reasons`, and terminal selection by the shared disposition-bucket precedence in `tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py` (FR-031) — makes T026 pass
- [ ] T038 [US2] Implement immutable `execution_trace_id` creation, foreign-key-style bundle references, canonical-JSON trace digest recomputation, the `trace_reference_integrity_failure` invalidation path, and re-derivation of `resource_vector` and `reasoning_token_report` from the digest-verified trace in `tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py`, consuming `lib/treatment_trace_io.py`, `lib/treatment_trace_bundle.py`, and `lib/treatment_trace_authority.py` unmodified (FR-010, FR-032) — makes T027 pass
- [ ] T039 [US2] Implement per-arm cache-state isolation and observed isolation evidence in `tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py`, recording the distinct cache root each arm used and its disjointness, and excluding pairs that cannot show distinct roots from the resource comparison (FR-049) — makes T028 pass
- [ ] T040 [US2] Register `tests/speckit-pro/unit/test-canonical-agent-materializer.py` and `tests/speckit-pro/unit/test-exact-treatment-runner.py` in the Layer 4 (`"id": "4"`) `scripts` array of `tests/speckit-pro/suite-manifest.json` — each entry is an object `{"path", "label", "baseline"}`, not a bare path string, with `"baseline": null` for these unit tests and confirm `python3 tests/speckit-pro/run-all.py --layer 4` is green
- [ ] T041 [US2] **Generated-artifact contract — a required step, not a footnote.** Because `speckit-pro/speckit_pro_runner/materializer.py` ships in the plugin payload, run `python3 scripts/refresh-release-artifacts.py` to regenerate `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`, `speckit-pro-runner.sha256`, `install_inventory.json`, `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json`, and both install payloads under `dist/claude/speckit-pro/speckit_pro_runner/` and `dist/codex/speckit-pro/speckit_pro_runner/`. Confirm the refresh is idempotent (a second run makes no further changes), hand-edit none of the outputs, then prove plugin-shaped resolution by copying `speckit-pro/` alone into an empty temporary directory with no `tests/` tree and importing the module from that copy. Re-run `python3 tests/speckit-pro/run-all.py --layer 1` (FR-026, SC-014)

**Checkpoint**: Slice 1 complete. Exact treatment is provable before any outcome
is scored, the shipped module resolves in a plugin-shaped layout, and the
generated tree is synchronized. **Slice 1 PR may open here.**

---

## Phase 5: User Story 3 - Score Governed Twelve-Role Corpus (Priority: P2) — Slice 2

**Goal**: Evaluate one governed twelve-role corpus through deterministic hard
gates and blinded semantic ballots with explicit closed failure classes.

**Independent Test**: Run the governed corpus against admitted executable routes
and verify deterministic gates, blind ballots, adjudication, failure classes, and
provenance are complete for every accepted score bundle — `quickstart.md`
section 4.

**Slice**: 2

### Tests for User Story 3 (write FIRST, observe FAIL)

- [ ] T042 [P] [US3] TDD RED: create `tests/speckit-pro/unit/test-role-corpus-governance.py` asserting the corpus contains exactly twelve role contracts — the eleven required-core roles plus `autopilot-fast-helper`; that each entry carries independent `required_core` and `executable` booleans; that `autopilot-fast-helper` carries `executable=false`, binds every contract field anyway, has no candidate route bindings, emits no score bundle, and is not counted as attrition; and that it is analyzed separately from required-core primary statistics (FR-011, FR-012, SC-005)
- [ ] T043 [US3] TDD RED: in `tests/speckit-pro/unit/test-role-corpus-governance.py`, assert every fixture binds role/source digest, objective, evidence partition, permitted tools, mutation contract, expected artifacts, acceptance oracle, fixture digest, and independent validity review; that each digest is SHA-256 over the canonical JSON serialization of the record excluding its own digest field, emitted as `sha256:<64 hex>`; and that a fixture digest mismatch fails the fixture BEFORE candidate scoring (FR-033)
- [ ] T044 [P] [US3] TDD RED: create `tests/speckit-pro/unit/test-score-bundle-adjudication.py` asserting all seven deterministic hard gates `role`, `safety`, `grounding`, `mutation`, `tool`, `output`, `acceptance` are required for every executed role with unique names and no per-role subset; that a missing gate result fails closed with `failure_plane=schema` and `failure_code=required_evidence_missing` rather than reading as a pass; and that no semantic ballot is collected until every required gate has passed (FR-014)
- [ ] T045 [US3] TDD RED: in `tests/speckit-pro/unit/test-score-bundle-adjudication.py`, assert each ballot binds exactly one blinded-artifact digest as its sole scored input; that a blinded artifact containing any freeze-bound model identity, alias, effort value, agent frontmatter key, or route identifier fails the mechanical leak check with `ballot_non_blind` and blocks scoring; that a scorer or adjudicator whose observed identity from the per-model usage breakdown falls in a candidate's model family is rejected; that a scorer whose observed identity diverges from its declared route blocks that ballot rather than degrading it; and that presentation order is randomized under a recorded seed with no paraphrase or style-normalization step (FR-035, FR-047)
- [ ] T046 [US3] TDD RED: in `tests/speckit-pro/unit/test-score-bundle-adjudication.py`, assert two distinct scorer identities and execution records with a frozen rubric version and digest and current calibration; that a decision-affecting disagreement routes to a frozen third adjudicator whose provenance attaches to the bundle; that complete fixture, scorer, treatment, candidate, adjudicator, and infrastructure provenance is preserved; that every ballot records whether the scorer inferred candidate provenance and from what signal; and that a recorded inference does not silently invalidate the ballot but is reported as a residual so blinding is never described as complete (FR-015, FR-016, FR-048, SC-006)
- [ ] T047 [US3] TDD RED: in `tests/speckit-pro/unit/test-score-bundle-adjudication.py`, assert the four closed taxonomies are set-equal to the Codex twin's committed enums; that `failure_plane` is derived from `failure_code` by the total single-valued mapping in FR-034 with an unlisted pair failing closed as `schema_invalid`; that `score_disposition=accepted` holds if and only if `failure_plane`, `failure_code`, and `invalidation_reason` are all `none`; that `gate_failed` and `non_scorable` each carry non-`none` plane and code and `invalidated` carries a non-`none` reason; that platform alias re-pointing reuses the shared `service_reroute_requested_route_non_scorable` code rather than coining a Claude-only member; that the capability-plane `alias_repoint_unresolved` is not repurposed here; and that the three repo-level shared contracts under `tests/speckit-pro/layer6-efficiency/contracts/` are unmodified (FR-034)
- [ ] T048 [US3] TDD RED: in `tests/speckit-pro/unit/test-score-bundle-adjudication.py`, assert both halves of the evidence-boundary ignore rule — that the named consolidated baseline file is tracked and that a representative per-run raw output beside it is still ignored — and that the allow entry names the baseline file explicitly rather than un-ignoring a directory (FR-027)

### Implementation for User Story 3

- [ ] T049 [US3] Create `tests/speckit-pro/layer6-efficiency/lib/claude_role_corpus.py` implementing twelve-role corpus governance, the independent `required_core` and `executable` booleans, the run-only-admitted-executable-routes rule, contract retention for non-executable roles, and separate analysis of `autopilot-fast-helper` (FR-011, FR-012) — makes T042 pass
- [ ] T050 [US3] Implement fixture contract binding and the canonical-JSON digest preimage with recomputation at acceptance and replay, failing the fixture before candidate scoring on mismatch, in `tests/speckit-pro/layer6-efficiency/lib/claude_role_corpus.py` (FR-033) — makes T043 pass
- [ ] T051 [P] [US3] Author `tests/speckit-pro/layer6-efficiency/fixtures/car-003-role-corpus.json` with all twelve role contracts, bounded in size so suite cost does not scale with accumulated cohort evidence (FR-011, FR-057)
- [ ] T052 [US3] Create `tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py` implementing the seven deterministic hard gates, each recording gate name, pass/fail, and evidence digest, with fail-closed handling of a missing gate result and a ballot barrier until all seven pass (FR-014) — makes T044 pass
- [ ] T053 [US3] Implement the mechanical blinded-artifact leak check against freeze-bound model identities, aliases, effort values, agent frontmatter, and route identifiers in `tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py`, recording `ballot_non_blind` and blocking scoring on failure (FR-035)
- [ ] T054 [US3] Implement two-ballot collection with distinct scorer identities and execution records, frozen rubric binding, complete provenance, and frozen third-adjudicator routing on decision-affecting disagreement in `tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py` (FR-015, FR-016)
- [ ] T055 [US3] Implement static same-family exclusion enforced against the scorer's and adjudicator's run-observed route identity with the FR-039 divergence check, seeded presentation-order randomization, and the bounded blinding residual record on every ballot, in `tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py` (FR-047, FR-048) — makes T045 and T046 pass
- [ ] T056 [US3] Implement the closed score taxonomies, the total single-valued `failure_code` to `failure_plane` mapping, the `score_disposition` binding, additive invalidation on fixture, scorer, rubric, adjudicator, treatment, capability, partition, or schema change, and the operator-only boundary keeping raw prompts, responses, transcripts, and identity mappings out of committed evidence, in `tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py` (FR-034, FR-036) — makes T047 pass
- [ ] T057 [US3] Add the allow rule naming the consolidated baseline file explicitly to `tests/speckit-pro/layer6-efficiency/.gitignore` while keeping per-run raw outputs ignored; do not un-ignore the directory (FR-027) — makes T048 pass
- [ ] T058 [US3] Register `tests/speckit-pro/unit/test-role-corpus-governance.py` and `tests/speckit-pro/unit/test-score-bundle-adjudication.py` in the Layer 4 (`"id": "4"`) `scripts` array of `tests/speckit-pro/suite-manifest.json` — each entry is an object `{"path", "label", "baseline"}`, not a bare path string, with `"baseline": null` for these unit tests and confirm `python3 tests/speckit-pro/run-all.py --layer 4` is green

**Checkpoint**: Slice 2 complete. The governed corpus scores through hard gates
and blinded ballots with closed failure classes. **Slice 2 PR may open here.**

---

## Phase 6: User Story 4 - Freeze Calibration Analysis Plan (Priority: P3) — Slice 3

**Goal**: Run a calibration-only pilot, freeze the numeric analysis plan, and
replay paired decision behavior without creating final route policies or
consuming final cohort evidence.

**Independent Test**: Run only disposable calibration objectives, freeze the
analysis plan, and replay decisions from versioned bundles while proving no final
cohort or integrated-confirmation partition was consumed — `quickstart.md`
sections 5 and 8.

**Slice**: 3

### Tests for User Story 4 (write FIRST, observe FAIL)

- [ ] T059 [P] [US4] TDD RED: create `tests/speckit-pro/unit/test-experiment-policy-partitions.py` asserting every fixture, experiment, score, and decision bundle references a registry-bound `partition_id` with closed type `calibration`, `screening`, `selection`, `cohort_lock`, or `integrated_confirmation`; that a Partition Registry Entry binds `partition_id`, `partition_type`, `qualification_eligible`, an objective-set digest over the deduplicated lexicographically sorted `objective_ids`, a frozen timestamp, and the owning spec; that an objective ID appearing in two registered partitions fails closed with `failure_plane=partition`; that `partition_type` and `qualification_eligible` are immutable after freeze; that calibration always carries `qualification_eligible=false`; and that CAR-003 consumes only `qualification_eligible=false` calibration objectives (FR-013, FR-033)
- [ ] T060 [US4] TDD RED: in `tests/speckit-pro/unit/test-experiment-policy-partitions.py`, assert every pair immutably binds comparison set, partition, candidate and comparator routes, role, fixture, task, instruction and configuration hashes, capability snapshot and freeze, route resolution, materialization, assigned order, pre-execution timestamp, and experiment policy before execution; that a `qualification_eligible=true` pair binds the frozen analysis plan while EVERY `qualification_eligible=false` pair binds the versioned calibration protocol instead; that binding both is rejected; that the substitution holds transitively so a policy governing an ineligible partition binds the calibration protocol; and that a later refresh creates an additive invalidation and never rebinds an existing pair (FR-037)
- [ ] T061 [US4] TDD RED: in `tests/speckit-pro/unit/test-experiment-policy-partitions.py`, assert the experiment-policy budget equals the frozen analysis-plan budget for qualification-eligible partitions and may be tighter only for calibration with any inequality failing closed on `failure_plane=partition`; that live-campaign budgets carry separate ceilings for attempts, wall-clock duration, raw input tokens, cache-write tokens by TTL class, cache-read tokens, output tokens, candidate count, and confirmation-entry count; that the TTL-class key space is closed to exactly `ephemeral_5m` and `ephemeral_1h` and is the same key set used by the additive cache diagnostic; and that workload-stratum membership is bound in the pre-execution assignment from a non-empty basis drawn only from the closed pre-execution set with `derived_from_realized_outcomes=false`, that the long-horizon stratum carries its own sample size and minimum unique-task count, and that a task matching no registered stratum returns inconclusive (FR-022, FR-038, FR-052, SC-022)
- [ ] T062 [P] [US4] TDD RED: create `tests/speckit-pro/unit/test-analysis-decision-ladder.py` asserting the ladder runs strictly in order — absolute semantic and reliability floors, then task-paired cluster-adjusted non-inferiority, then the resource comparison — and that a stage not reached records `not_evaluated` rather than being omitted (FR-017, FR-018, SC-007)
- [ ] T063 [US4] TDD RED: in `tests/speckit-pro/unit/test-analysis-decision-ladder.py`, assert the Pareto comparison uses exactly the eight decision-bearing dimensions `input_tokens`, `cached_input_tokens`, `output_tokens`, duration, retries, compactions, acceptance, terminal state, set-equal to the Codex twin's frozen policy; that direction of preference is declared per dimension with the six resource dimensions lower-is-better, acceptance higher-is-better, and terminal state categorical so any difference makes the comparison mixed; that `reasoning_output_tokens` is recorded and reported for every attempt but is not a Pareto dimension; and that cache-write-by-TTL-class and cache-read breakdowns live in the additive diagnostic record and are not Pareto dimensions (FR-018, FR-049, FR-058)
- [ ] T064 [US4] TDD RED: in `tests/speckit-pro/unit/test-analysis-decision-ladder.py`, assert each non-qualifying condition maps to its specific closed terminal member — failed gate, failed floor, and failed non-inferiority to `no_qualification`; tie, mixed dominance, statistical uncertainty, incomplete evidence, rerun-cap exhaustion, exceeded or unclassifiable attrition, unobservable environment, and campaign-budget exhaustion to `inconclusive`; binding, partition-eligibility, or reference-integrity failure to `invalid`; a completed calibration partition to `calibration_complete` — and that no weighted ranking is forced and no scalar score or price coefficient appears anywhere in the bundle (FR-019, SC-008)
- [ ] T065 [US4] TDD RED: in `tests/speckit-pro/unit/test-analysis-decision-ladder.py`, assert candidate-caused failures, timeouts, cancellations, budget exhaustion, and abandoned work stay in the estimand at acceptance zero with no complete-case filtering; that a campaign ceiling reached between the two arms of a pair records `infrastructure_failure` and not `candidate_budget_exhausted`, is treated as incomplete rather than one-armed, and is never completed by a one-arm rerun; that reruns are capped per comparison pair, count reruns not attempts, and are complete-pair and arm-symmetric with zero one-arm reruns; that each rerun binds an immutable transient-classification record carrying its arm-blind evidence digest, its own digest, and a timestamp created before either arm's outcome digest exists; that a rerun whose record is absent or post-dates an outcome digest is not granted and the pair returns inconclusive; and that superseded pairs are retained immutably and marked superseded with exactly one terminal complete pair per assignment in primary statistics (FR-020, FR-021, FR-056, SC-009, SC-010)
- [ ] T066 [US4] TDD RED: in `tests/speckit-pro/unit/test-analysis-decision-ladder.py`, assert every frozen p95 guardrail declares guarded quantity and unit, denominator, comparator, margin distinct from the non-inferiority margins, confidence method, missing-data rule that is not silent exclusion of failed or timed-out attempts, direction, and multiplicity family declared distinct from the three FR-050 families; that `minimum_unique_tasks` is declared per stratum and a stratum below its floor returns inconclusive rather than passing or being skipped; that a guardrail breach returns no qualification and is never traded off or weighted; that the multiplicity declaration addresses the conjunctive stage, the Pareto disjunctive half, and the across-ladder family separately and records cluster-adjusted variance estimation as a precondition rather than a multiplicity control; and that racing and futility declarations record every planned interim look with its information fraction, its stopping boundary, futility bindingness, complete-pair stop scope, and stopped-not-completed reporting, with any look added, moved, or repeated after an outcome is visible invalidating the declaration (FR-050, FR-053, FR-054, FR-055, SC-023, SC-025)
- [ ] T067 [US4] TDD RED: in `tests/speckit-pro/unit/test-analysis-decision-ladder.py`, assert no final preferred or fallback route policy, installed default, aggregate identity, release claim, or outcome-bearing cohort decision is created; that the `qualified` terminal state is unreachable from a calibration partition; that a changed ceiling or threshold after freeze produces a new versioned analysis plan with a new id and digest whose outcomes are not pooled with the superseded plan's; and that deterministic replay reconstructs byte-identical terminal decisions from the frozen experiment, score, analysis, and decision bundles on a clean checkout (FR-023, FR-024, FR-056, SC-011, SC-012)

### Implementation for User Story 4

- [ ] T068 [US4] Create `tests/speckit-pro/layer6-efficiency/lib/claude_experiment_policy.py` implementing the Partition Registry Entry, the closed partition-type set, objective-level disjointness with the sorted-deduplicated objective-set digest, post-freeze immutability, and the calibration-only consumption rule (FR-013) — makes T059 pass
- [ ] T069 [US4] Implement immutable pre-execution pair binding and the calibration-protocol substitution keyed on `qualification_eligible` — including the transitive policy-level substitution and rejection of binding both — plus additive invalidation instead of rebinding on refresh, in `tests/speckit-pro/layer6-efficiency/lib/claude_experiment_policy.py` (FR-037) — makes T060 pass
- [ ] T070 [US4] Implement the analysis-plan-authoritative budget equality check, the eight live-campaign ceilings with the closed two-member TTL-class key space shared with the cache diagnostic, and pre-execution workload-stratum binding from the closed non-realized basis with the powered long-horizon stratum and the `unknown_stratum_policy` inconclusive outcome, in `tests/speckit-pro/layer6-efficiency/lib/claude_experiment_policy.py` (FR-022, FR-038, FR-052) — makes T061 pass
- [ ] T071 [US4] Create `tests/speckit-pro/layer6-efficiency/lib/claude_analysis_decision.py` implementing the ordered decision ladder with absolute semantic and reliability floors evaluated before task-paired cluster-adjusted non-inferiority, and `not_evaluated` for any stage not reached (FR-017, FR-018) — makes T062 pass
- [ ] T072 [US4] Implement eight-dimension Pareto dominance with per-dimension declared direction of preference, categorical terminal-state handling, and the reasoning-token report emitted alongside every dominance result, in `tests/speckit-pro/layer6-efficiency/lib/claude_analysis_decision.py` (FR-018, FR-049, FR-058) — makes T063 pass
- [ ] T073 [US4] Implement the closed terminal-member mapping including the explicit `inconclusive` state, the no-weighted-ranking and no-scalar-score guards, price data as diagnostic context only, and the guard forbidding final route policies, installed defaults, aggregate identities, and release claims with `qualified` unreachable from a calibration partition, in `tests/speckit-pro/layer6-efficiency/lib/claude_analysis_decision.py` (FR-019, FR-024) — makes T064 pass
- [ ] T074 [US4] Implement assigned-attempt estimand retention at acceptance zero with no complete-case filtering, capped complete-pair arm-symmetric rerun governance with the immutable transient-classification record and its pre-outcome ordering check, immutable retention of superseded pairs, and the campaign-ceiling versus candidate-budget separation, in `tests/speckit-pro/layer6-efficiency/lib/claude_analysis_decision.py` (FR-020, FR-021, FR-056) — makes T065 pass
- [ ] T075 [US4] Implement the fully declared p95 guardrail comparisons, per-stratum `minimum_unique_tasks` floors returning inconclusive below the floor, the three-family multiplicity declaration with cluster-adjusted variance as a precondition, the guardrail family declared distinct from those three, and the racing and futility declarations with interim looks, boundaries, bindingness, complete-pair stop scope, and stopped-not-completed reporting, in `tests/speckit-pro/layer6-efficiency/lib/claude_analysis_decision.py` (FR-050, FR-053, FR-054, FR-055) — makes T066 pass
- [ ] T076 [P] [US4] Author `tests/speckit-pro/layer6-efficiency/fixtures/car-003-calibration-replay.json` carrying frozen experiment, score, analysis, and decision bundles for deterministic replay, bounded in count and size so suite cost does not scale per campaign (SC-011, FR-057) — makes T067 pass
- [ ] T077 [US4] Register `tests/speckit-pro/unit/test-experiment-policy-partitions.py` and `tests/speckit-pro/unit/test-analysis-decision-ladder.py` in the Layer 4 (`"id": "4"`) `scripts` array of `tests/speckit-pro/suite-manifest.json` — each entry is an object `{"path", "label", "baseline"}`, not a bare path string, with `"baseline": null` for these unit tests and confirm `python3 tests/speckit-pro/run-all.py --layer 4` is green
- [ ] T078 [US4] **OPERATOR-ONLY, NEVER IN THE DEFAULT SUITE.** Follow `specs/car-003-evaluation-runner-scoring/quickstart.md` section 8 item 2 to run the calibration pilot against only disposable `qualification_eligible=false` calibration objectives under an explicit, local, pinned, budgeted invocation with all eight ceilings set. Prove exact dispatch, scoring, and statistical plumbing end to end and collect the variance estimates the analysis plan needs. Verify no screening, selection, cohort-lock, or integrated-confirmation objective was consumed, and that all committed evidence passes deny-by-default sensitive-field inspection with no absolute paths and no session identifiers (FR-023, SC-015)
- [ ] T079 [US4] Author `docs/ai/research/claude-car-003-analysis-plan.json` freezing workload strata, p95 guardrails, margins, sample sizes and assumptions, power, alpha, the three multiplicity families, racing and futility rules, attrition caps, campaign budgets, cache policy, and terminal rules, using the T078 calibration estimates. This MUST happen after the pilot and before any CAR-007 through CAR-010 cohort outcome exists (FR-023, FR-038, SC-012)

**Checkpoint**: Slice 3 complete. The decision platform is frozen and replayable
and no final route policy exists. **Slice 3 PR may open here.**

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T080 [P] Verify the suite budget: run `python3 tests/speckit-pro/run-all.py` and confirm the CAR-003 additions keep it within the declared 6-minute CI wall-clock budget derived from the ~4m30s baseline, that deterministic replay of a frozen bundle is p95 under 10 seconds on a clean developer checkout, and that the replay fixtures are bounded in count and size rather than growing per campaign; anything exceeding the budget moves behind the operator-only live path (FR-057, SC-019)
- [ ] T081 [P] Run the tree-wide privacy and sensitive-field scan across every CAR-003 artifact under `specs/car-003-evaluation-runner-scoring/`, `tests/speckit-pro/layer6-efficiency/fixtures/`, and `docs/ai/research/`, confirming zero absolute home paths, zero session identifiers, zero raw captures, and only allowlisted sanitized boundary evidence (FR-027, FR-036, SC-015)
- [ ] T082 Generate the slice 1 PR review packet from the nine sections required by `specs/car-003-evaluation-runner-scoring/spec.md` "PR Review Packet Requirements", covering what changed, why, non-goals, review order, scope budget (735 LOC, 11 authored files, 23 changed paths, 1 production file), traceability from FR-001…FR-010, FR-026…FR-032, FR-039…FR-046, FR-051 to changed files and verification evidence, known gaps, and rollback notes; validate the PR title against the release-readiness gate as `<type>(speckit-pro): <plain English description>`
- [ ] T083 Generate the slice 2 PR review packet from the same nine sections of `specs/car-003-evaluation-runner-scoring/spec.md`, scope budget 533 LOC across 7 authored files, and traceability from FR-011…FR-016, FR-027, FR-033…FR-036, FR-047, FR-048
- [ ] T084 Generate the slice 3 PR review packet from the same nine sections of `specs/car-003-evaluation-runner-scoring/spec.md`, scope budget 590 LOC across 7 authored files, and traceability from FR-013, FR-017…FR-024, FR-037, FR-038, FR-049, FR-050, FR-052…FR-058
- [ ] T085 Re-run `python3 scripts/refresh-release-artifacts.py` after the final slice and confirm it is a no-op, proving no unsynchronized shipped-source change remains (FR-026, SC-014)
- [ ] T086 Run `specs/car-003-evaluation-runner-scoring/quickstart.md` end to end, sections 1 through 7, and confirm the full gate is green at the 3251 baseline plus the new tests, with zero live calls and a clean payload boundary (SC-019)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies. T001 must precede any edit to
  `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py`.
- **Foundational (Phase 2)**: depends on Setup. Blocks all user stories.
- **User Stories (Phases 3-6)**: run in the fixed slice order. Slice 1 is
  US1 + US2 and is roadmap Work Package A, which must stay intact. Slice 2 is
  US3. Slice 3 is US4.
- **Polish (Phase 7)**: depends on all three slices.

### User Story Dependencies

- **US1 (P1, slice 1)**: depends only on Foundational. Delivers the freeze that
  US2's route admission and US3's blinding leak check read from.
- **US2 (P1, slice 1)**: depends on Foundational; consumes the US1 freeze for
  alias-divergence checks. Ships the only production file, so T041 carries the
  generated-artifact contract for the whole feature.
- **US3 (P2, slice 2)**: depends on slice 1 landing. Reads the US1 freeze for
  leak-check identities and the US2 treatment record for score eligibility.
- **US4 (P3, slice 3)**: depends on slice 2 landing. Consumes US3 score bundles.

### Within Each User Story

- Every test task is written and observed FAILING before its paired
  implementation task.
- Fixtures may be authored in parallel with module logic — different files.
- Suite-manifest registration comes after the test files exist, never before, or
  `run-all.py` fails on a missing path.
- Operator-only tasks (T022, T078) run outside the default suite and never in CI.

### Parallel Opportunities

- T002 runs alongside T001's merge.
- T004 (Foundational test) is parallel-safe against T003.
- The first test file of each story (T006, T023, T042, T044, T059, T062) is
  parallel-safe against the others because each creates a distinct file.
- Fixture authoring (T020, T051, T076) and manifest authoring (T032) are
  parallel-safe against module logic in the same story.
- T080 and T081 are parallel-safe in Polish.
- Within a story, tasks editing the same module or the same test file are
  sequential and carry no `[P]`.

**Parallel task count**: 14 of 86 tasks are marked `[P]` — T002, T004, T006,
T020, T023, T032, T042, T044, T051, T059, T062, T076, T080, T081.

---

## Parallel Example: Slice 1 kickoff

```bash
# After T001 and T003, launch the two slice-1 test files together:
Task: "T006 Create tests/speckit-pro/unit/test-successor-capability-freeze.py"
Task: "T023 Create tests/speckit-pro/unit/test-canonical-agent-materializer.py"

# Fixtures and the observation manifest are independent of module logic:
Task: "T020 Author tests/speckit-pro/layer6-efficiency/fixtures/car-003-alias-repoint-replay.json"
Task: "T032 Author docs/ai/research/claude-car-003-mandatory-observation-manifest.json"
```

---

## Implementation Strategy

### MVP: Slice 1 (US1 + US2)

1. Phase 1 Setup — sync the default branch, capture the baseline.
2. Phase 2 Foundational — claim the shared smoke runner first, record the
   reviewability decision.
3. Phase 3 US1 — successor freeze publishes or fails closed.
4. Phase 4 US2 — exact treatment provable, materializer ships, generated tree
   synchronized.
5. **STOP and VALIDATE**: `quickstart.md` sections 3 and 6, full suite green.
6. Open the slice 1 PR. Work Package A stays intact — do not subdivide it.

### Incremental Delivery

1. Slice 1 → freeze and treatment platform → PR 1.
2. Slice 2 → governed corpus, hard gates, blinded scoring → PR 2.
3. Slice 3 → policy, statistics, calibration pilot, frozen plan → PR 3.

Each slice is independently reviewable and adds value without breaking the
previous one. Every artifact is additive and versioned, so rolling back a slice
means reverting its commits — no CAR-002 record is mutated and no historical
evidence needs repair.

---

## Requirements Coverage

Every FR-001 through FR-058 maps to at least one task. No FR is uncovered.

| FR | Slice | Tasks |
|---|---|---|
| FR-001 | 1 | T010, T017 |
| FR-002 | 1 | T007, T013, T022 |
| FR-003 | 1 | T008, T014, T015 |
| FR-004 | 1 | T008, T014 |
| FR-005 | 1 | T008, T014 |
| FR-006 | 1 | T023, T029, T031 |
| FR-007 | 1 | T004, T005 |
| FR-008 | 1 | T023, T030 |
| FR-009 | 1 | T024, T032, T033, T034 |
| FR-010 | 1 | T027, T038 |
| FR-011 | 2 | T042, T049, T051 |
| FR-012 | 2 | T042, T049 |
| FR-013 | 3 | T059, T068 |
| FR-014 | 2 | T044, T052 |
| FR-015 | 2 | T046, T054 |
| FR-016 | 2 | T046, T054 |
| FR-017 | 3 | T062, T071 |
| FR-018 | 3 | T062, T063, T071, T072 |
| FR-019 | 3 | T064, T073 |
| FR-020 | 3 | T065, T074 |
| FR-021 | 3 | T065, T074 |
| FR-022 | 3 | T061, T070 |
| FR-023 | 3 | T067, T078, T079 |
| FR-024 | 3 | T067, T073 |
| FR-025 | all | T003 |
| FR-026 | 1, 3 | T041, T085 |
| FR-027 | 1, 2 | T010, T017, T048, T057 |
| FR-028 | 1 | T009, T017 |
| FR-029 | 1 | T006, T016 |
| FR-030 | 1 | T026, T036 |
| FR-031 | 1 | T026, T037 |
| FR-032 | 1 | T027, T038 |
| FR-033 | 2, 3 | T043, T050, T059 |
| FR-034 | 2 | T047, T056 |
| FR-035 | 2 | T045, T053 |
| FR-036 | 2 | T056, T081 |
| FR-037 | 3 | T060, T069 |
| FR-038 | 3 | T061, T070, T079 |
| FR-039 | 1 | T011, T018 |
| FR-040 | 1 | T008, T015, T022 |
| FR-041 | 1 | T012, T019 |
| FR-042 | 1 | T025, T035 |
| FR-043 | 1 | T001, T005 |
| FR-044 | 1 | T009, T017 |
| FR-045 | 1 | T011, T018 |
| FR-046 | 1 | T011, T020 |
| FR-047 | 2 | T045, T055 |
| FR-048 | 2 | T046, T055 |
| FR-049 | 1, 3 | T028, T039, T063, T072 |
| FR-050 | 3 | T066, T075 |
| FR-051 | 1 | T025, T035 |
| FR-052 | 3 | T061, T070 |
| FR-053 | 3 | T066, T075 |
| FR-054 | 3 | T066, T075 |
| FR-055 | 3 | T066, T075 |
| FR-056 | 3 | T065, T067, T074 |
| FR-057 | all | T002, T020, T051, T076, T080 |
| FR-058 | 3 | T063, T072 |

**Split-FR notes.** FR-027 spans slices 1 and 2: the freeze allowlist lands in
slice 1 (T010, T017) and the evidence-boundary ignore rule in slice 2 (T048,
T057). FR-049 spans slices 1 and 3: per-arm cache-isolation evidence lands with
the treatment runner in slice 1 (T028, T039) and the reasoning-token report plus
Pareto exclusion in slice 3 (T063, T072). FR-026 lands in slice 1 (T041, the only
slice changing shipped source) and is re-verified in Polish (T085). FR-033 is
exercised for fixture digests in slice 2 (T043, T050) and for the partition
objective-set digest in slice 3 (T059). FR-057 is cross-cutting: fixture-bounding
obligations sit on the fixture tasks and the wall-clock budget on T080.

**Tasks that intentionally trace to no numbered FR.** Seven tasks carry no FR
mapping because their obligation comes from the constitution or from a mandatory
`spec.md` section rather than from a functional requirement, and inventing an FR
reference for them would be false traceability:

- **T021, T040, T058, T077** (suite-manifest registration) discharge constitution
  Principle IV, which requires layer membership and dispatch to stay declared in
  `tests/speckit-pro/suite-manifest.json`. Without registration the new Layer 4
  tests exist but never run, so the Principle IV completion bar cannot be met.
- **T082, T083, T084** (per-slice PR review packets) discharge the `spec.md`
  section "PR Review Packet Requirements", which is mandatory and enumerates the
  nine sections each packet must carry. They also carry the FR-025 slice structure
  into the review artifact, but the packet contents are governed by that spec
  section, not by FR-025.

---

## Success Criteria Coverage

| SC | Tasks |
|---|---|
| SC-001 | T010, T017 |
| SC-002 | T008, T022 |
| SC-003 | T006, T016 |
| SC-004 | T026, T036 |
| SC-005 | T042, T049 |
| SC-006 | T046, T054 |
| SC-007 | T062, T071 |
| SC-008 | T064, T073 |
| SC-009 | T065, T074 |
| SC-010 | T065, T074 |
| SC-011 | T067, T076 |
| SC-012 | T067, T079 |
| SC-013 | T003 |
| SC-014 | T041, T085 |
| SC-015 | T010, T017, T022, T078, T081 |
| SC-016 | T009, T017 |
| SC-017 | T011, T018 |
| SC-018 | T008, T015, T022 |
| SC-019 | T002, T080, T086 |
| SC-020 | T025, T035 |
| SC-021 | T024, T034 |
| SC-022 | T061, T070 |
| SC-023 | T066, T075 |
| SC-024 | T028, T039 |
| SC-025 | T066, T075 |

---

## Notes

- `[P]` tasks touch different files and have no dependency on an incomplete task.
- `[Story]` labels map each task to its user story and therefore to its slice.
- Every implementation task names the test task it turns green; run that test and
  observe FAIL before writing implementation.
- The verification command is `python3 tests/speckit-pro/run-all.py`. Baseline
  3251/3251. Any later failure is attributable to CAR-003.
- Operator-only tasks are T022 (successor freeze collection) and T078
  (calibration pilot). Neither runs in the default suite or in CI.
- Do not extend the repo-level shared contracts under
  `tests/speckit-pro/layer6-efficiency/contracts/`. Three cross-platform
  coordination items are recorded in `plan.md` Known Gaps:
  1. **Score-bundle terminal-field constraints** — the `failure_code` to
     `failure_plane` mapping and the `score_disposition` binding. Deliberately
     **not** applied to `contracts/score-bundle.schema.json`, which carries no
     conditional subschemas. T047 asserts these rules against the Python
     implementation and MUST NOT add a one-sided schema constraint.
  2. **Experiment-policy binding cycle** — **already applied on this side.**
     `contracts/experiment-policy.schema.json` makes `analysis_plan_binding`
     conditional on `partition.qualification_eligible` rather than unconditionally
     required. T060 asserts behaviour the schema already enforces; the open work is
     bringing the Codex twin into line, not changing this side.
  3. **No `invalidation_reason` member for an analysis-plan or budget change** —
     FR-056 enforces non-pooling through `{id, digest}` binding identity instead.
     Deliberately not coined unilaterally; tracked as `checklists/performance.md`
     CHK051.

  None is slice-blocking.
- Avoid: implementing a second materializer, editing CAR-002 evidence, adding a
  taxonomy member unilaterally, or expanding this task list past the per-slice
  reviewability budget instead of re-running the setup-mode gate.
