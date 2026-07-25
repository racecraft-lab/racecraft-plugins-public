# Tasks: G56R-003 Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/`, `quickstart.md`, and the four completed domain checklists.

**Method**: Strict red-green-refactor TDD. A RED task must record the focused
failing command and expected failure before its paired GREEN task begins. A
GREEN task implements only enough behavior to pass. REFACTOR tasks preserve
green tests while tightening names, duplication, contracts, and evidence.

**Review order**: Slice 1 → Slice 2 → Slice 3. Shared manifests, schemas,
registries, and generated artifacts are serial even when nearby fixture files
are marked `[P]`.

## Slice 1 — Capability, Materialization, and Trace

**Goal**: Publish an additive non-empty successor freeze, use one shipped
exact-byte materializer, and emit score-eligibility treatment evidence through
new immutable G56R-003 traces under the unchanged G56R-002 contract.

**Independent test**: From sanitized deterministic catalog and agent-policy
fixtures, publish a valid successor freeze, materialize exact TOML bytes, emit
a new treatment trace, and prove that malformed/empty/stale evidence,
misdelivery, reroute, or missing mandatory observations cannot score.

- [ ] T001 [US1] [FR-001] RED: add an immutability regression that snapshots every existing G56R-002 capability/trace artifact and fails if successor publication changes an old path, ID, or byte in `tests/speckit-pro/unit/test-codex-successor-capability.py`
- [ ] T002 [US1] [FR-002] [FR-027] RED: add sanitized pinned-catalog collection fixtures covering command/client/build metadata, opaque account/environment boundaries, raw/parsed digests, defaults, efforts, timestamps, private evidence refs, and deny-by-default field rejection in `tests/speckit-pro/unit/test-codex-successor-capability.py`
- [ ] T003 [US1] [FR-003] [FR-004] [FR-005] [FR-029] RED: add table-driven source/runtime intersection cases for effort normalization, diagnostic-only surfaces, hidden/alias/aggregate/default entries, Ultra/topology controls, and every closed tuple exclusion in `tests/speckit-pro/unit/test-codex-successor-capability.py`
- [ ] T004 [US1] [FR-028] RED: add publication blockers for empty intersection, malformed/stale/untrusted/unsanitized collection, missing provenance, retention failure, identity/digest mismatch, and historical mutation in `tests/speckit-pro/unit/test-codex-successor-capability.py`
- [ ] T005 [US1] [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-027] [FR-028] [FR-029] GREEN: implement the smallest additive collector, sanitizer, source/runtime intersection, authority-failure separation, and freeze publisher in `tests/speckit-pro/layer6-efficiency/lib/codex_successor_capability.py`
- [ ] T006 [US1] [FR-001] [FR-028] GREEN: author the implementation successor contract in `tests/speckit-pro/layer6-efficiency/contracts/successor-capability-freeze.schema.json` and bind the validator to its version/digest without changing `capability-freeze.schema.json`
- [ ] T007 [US1] [FR-001] [FR-003] [FR-029] REFACTOR: consolidate canonical digest/tuple ordering through existing G56R-002 capability helpers, remove duplicate collection logic, rerun `python3 tests/speckit-pro/unit/test-codex-successor-capability.py`, and record green evidence
- [ ] T008 [US2] [FR-006] [FR-008] RED: add golden exact-byte, UTF-8, instruction-digest, configuration-digest, source-binding, idempotence, and parsed-equivalence-is-insufficient tests in `tests/speckit-pro/unit/test-agent-materialization.py`
- [ ] T009 [US2] [FR-006] RED: add an import-contract test proving Layer 6 and the planned G56R-006 consumer use `speckit_pro_runner.agent_materialization.materialize_agent_policy`, with no evaluation-only renderer, in `tests/speckit-pro/unit/test-agent-materialization.py`
- [ ] T010 [US2] [FR-006] [FR-008] GREEN: implement the pure Python 3.11 standard-library materializer and immutable result type in `speckit-pro/speckit_pro_runner/agent_materialization.py`
- [ ] T011 [US2] [FR-006] REFACTOR: keep writing/execution orchestration outside the materializer, remove redundant byte rendering, rerun `python3 tests/speckit-pro/unit/test-agent-materialization.py`, and record green evidence
- [ ] T012 [US2] [FR-007] [FR-008] RED: add qualification-adapter tests that preserve `run-efficiency-benchmarks.py` and `quality-scorer.py` as smoke-only while requiring installed-policy or exact-byte proof before treatment acceptance in `tests/speckit-pro/unit/test-codex-qualification-contracts.py`
- [ ] T013 [US2] [FR-009] [FR-030] RED: add a complete mandatory-observation matrix for named agent, requested/configured route, instructions, sandbox, permissions, skills, tools, MCP startup/schema, parent controls, client, context, reroute monitoring, profile nulls, and disallowed missing/unavailable/undocumented states in `tests/speckit-pro/unit/test-codex-qualification-contracts.py`
- [ ] T014 [US2] [FR-010] [FR-031] RED: add replay cases requiring one new immutable trace per assignment and non-scorable service reroute plus hard-failed different-agent, ambiguous, unapproved, and unidentifiable delivery in `tests/speckit-pro/unit/test-codex-qualification-contracts.py`
- [ ] T015 [US2] [FR-009] [FR-010] [FR-030] [FR-031] GREEN: implement G56R-002-backed treatment eligibility, assignment-to-trace bindings, closed delivery disposition, and immutable trace emission in `tests/speckit-pro/layer6-efficiency/lib/qualification_contracts.py`
- [ ] T016 [US2] [FR-007] [FR-008] [FR-009] [FR-010] GREEN: implement the thin durable entry point and `publish-successor-freeze` plus treatment-preparation commands in `tests/speckit-pro/layer6-efficiency/run-codex-qualification.py`
- [ ] T017 [US2] [FR-010] REFACTOR: reuse existing `treatment_trace_model.py`, `treatment_trace_bundle.py`, content-addressed IO, and replay helpers; prove no copied trace schema or mutation path remains; rerun the two focused Slice 1 test files
- [ ] T018 [US2] [FR-026] RED: extend runner trust tests so adding shipped materializer source fails until the runner manifest, checksum, payloads, installed-cache proofs, and release evidence are regenerated in `tests/speckit-pro/unit/test-agent-materialization.py`
- [ ] T019 [US2] [FR-026] GREEN: run `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py`, review only generator-owned outputs, and rerun `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py --check`
- [ ] T020 [US1] [US2] [FR-001] [FR-006] [FR-010] [FR-026] REFACTOR: register the Slice 1 tests in `tests/speckit-pro/suite-manifest.json`, run the focused files plus `python3 tests/speckit-pro/run-all.py --layer 4`, inspect `git diff --check`, and record Slice 1 G7 evidence

## Slice 2 — Corpus and Blinded Scoring

**Goal**: Govern exactly twelve role contracts, gate invalid fixtures and
treatments before scoring, collect two independent blind ballots, adjudicate
decision-affecting disagreement, and emit immutable sanitized score bundles
with closed failure and invalidation taxonomies.

**Independent test**: Validate the twelve-role manifest, skip the two
non-executable roles, keep helper statistics separate, score a deterministic
fixture through two blind ballots, and fail closed for every fixture,
treatment, scorer, ballot, adjudicator, partition, schema, and evidence leak.

- [ ] T021 [US3] [FR-011] [FR-012] [FR-033] RED: add role-corpus contract tests for exact 12-member identity, 11 required-core roles, 9 executable core roles, 2 governed non-executable roles, helper separation, fixture digest/oracle/review fields, and admitted-route-only scheduling in `tests/speckit-pro/unit/test-codex-qualification-corpus.py`
- [ ] T022 [US3] [FR-011] [FR-012] [FR-033] GREEN: author `tests/speckit-pro/layer6-efficiency/contracts/role-corpus.schema.json` and implement standard-library validation/scheduling in `tests/speckit-pro/layer6-efficiency/lib/qualification_corpus.py`
- [ ] T023 [P] [US3] [FR-011] [FR-033] GREEN: author the independently reviewable `analyze-executor` fixture contract at `tests/speckit-pro/layer6-efficiency/fixtures-codex/analyze-executor/fixture.json`
- [ ] T024 [P] [US3] [FR-011] [FR-033] GREEN: author the independently reviewable `checklist-executor` fixture contract at `tests/speckit-pro/layer6-efficiency/fixtures-codex/checklist-executor/fixture.json`
- [ ] T025 [P] [US3] [FR-011] [FR-033] GREEN: author the independently reviewable `clarify-executor` fixture contract at `tests/speckit-pro/layer6-efficiency/fixtures-codex/clarify-executor/fixture.json`
- [ ] T026 [P] [US3] [FR-011] [FR-033] GREEN: author the independently reviewable `codebase-analyst` fixture contract at `tests/speckit-pro/layer6-efficiency/fixtures-codex/codebase-analyst/fixture.json`
- [ ] T027 [P] [US3] [FR-011] [FR-033] GREEN: author the independently reviewable `domain-researcher` fixture contract at `tests/speckit-pro/layer6-efficiency/fixtures-codex/domain-researcher/fixture.json`
- [ ] T028 [P] [US3] [FR-011] [FR-033] GREEN: author the independently reviewable `implement-executor` fixture contract at `tests/speckit-pro/layer6-efficiency/fixtures-codex/implement-executor/fixture.json`
- [ ] T029 [P] [US3] [FR-011] [FR-033] GREEN: author the independently reviewable `phase-executor` fixture contract at `tests/speckit-pro/layer6-efficiency/fixtures-codex/phase-executor/fixture.json`
- [ ] T030 [P] [US3] [FR-011] [FR-033] GREEN: author the independently reviewable `spec-context-analyst` fixture contract at `tests/speckit-pro/layer6-efficiency/fixtures-codex/spec-context-analyst/fixture.json`
- [ ] T031 [P] [US3] [FR-011] [FR-033] GREEN: author the independently reviewable `uat-runbook-author` fixture contract at `tests/speckit-pro/layer6-efficiency/fixtures-codex/uat-runbook-author/fixture.json`
- [ ] T032 [P] [US3] [FR-011] [FR-012] [FR-033] GREEN: author the governed non-executable `consensus-synthesizer` fixture contract at `tests/speckit-pro/layer6-efficiency/fixtures-codex/consensus-synthesizer/fixture.json`
- [ ] T033 [P] [US3] [FR-011] [FR-012] [FR-033] GREEN: author the governed non-executable `gate-validator` fixture contract at `tests/speckit-pro/layer6-efficiency/fixtures-codex/gate-validator/fixture.json`
- [ ] T034 [P] [US3] [FR-011] [FR-012] [FR-033] GREEN: author the separate optional-helper fixture contract at `tests/speckit-pro/layer6-efficiency/fixtures-codex/autopilot-fast-helper/fixture.json`
- [ ] T035 [US3] [FR-011] [FR-012] [FR-013] GREEN: serialize all twelve reviewed fixture bindings through the single-owner `tests/speckit-pro/layer6-efficiency/fixtures-codex/corpus-manifest.json`, with helper statistics and partition binding separate
- [ ] T036 [US3] [FR-011] [FR-012] [FR-033] REFACTOR: validate every fixture against current role source digests and acceptance oracles, reject stale/non-executable scheduling, rerun `python3 tests/speckit-pro/unit/test-codex-qualification-corpus.py`, and record green evidence
- [ ] T037 [US3] [FR-014] RED: add deterministic hard-gate fixtures for role, safety, grounding, mutation, tool, output, and acceptance pass/fail/missing evidence in `tests/speckit-pro/unit/test-codex-qualification-scoring.py`
- [ ] T038 [US3] [FR-015] [FR-035] RED: add semantic ballot tests requiring two distinct scorer identities/executions, blind artifact digest, one frozen rubric, current calibration, and rejection of missing/stale/non-blind/duplicate ballots in `tests/speckit-pro/unit/test-codex-qualification-scoring.py`
- [ ] T039 [US3] [FR-015] [FR-035] RED: add disagreement fixtures requiring a current frozen third adjudicator distinct from both primary scorers, with complete provenance, in `tests/speckit-pro/unit/test-codex-qualification-scoring.py`
- [ ] T040 [US3] [FR-014] [FR-015] [FR-035] GREEN: implement deterministic gate ordering, blinded ballot validation, disagreement detection, and third-adjudicator resolution in `tests/speckit-pro/layer6-efficiency/lib/qualification_scoring.py`
- [ ] T041 [US3] [FR-016] [FR-032] [FR-034] RED: add score-bundle contract tests for every required upstream ID/digest, closed disposition/plane/code/invalidation enums, `none` coupling, additive invalidation, and immutable trace reference in `tests/speckit-pro/unit/test-codex-qualification-scoring.py`
- [ ] T042 [US3] [FR-016] [FR-032] [FR-034] GREEN: author `tests/speckit-pro/layer6-efficiency/contracts/score-bundle.schema.json` and implement immutable score-bundle construction in `tests/speckit-pro/layer6-efficiency/lib/qualification_scoring.py`
- [ ] T043 [US3] [FR-027] [FR-036] RED: add sensitive-evidence negatives for raw prompts/responses/transcripts, personal scorer mappings, account/auth/credential/session/cookie/header/private-host/absolute-path/remote/billing fields, and unknown keys in `tests/speckit-pro/unit/test-codex-qualification-scoring.py`
- [ ] T044 [US3] [FR-016] [FR-034] [FR-036] GREEN: implement sanitized evidence-reference allowlisting, opaque scorer/adjudicator bindings, and additive invalidation records in `tests/speckit-pro/layer6-efficiency/lib/qualification_scoring.py`
- [ ] T045 [US3] [FR-014] [FR-015] [FR-034] REFACTOR: remove free-form failure codes and any path that creates ballots before deterministic gates or exact treatment, rerun the corpus/scoring tests, and record green evidence
- [ ] T046 [US3] [FR-011] [FR-012] [FR-016] REFACTOR: add deterministic replay proving required-core and helper summaries are separate and unchanged for identical bundles in `tests/speckit-pro/layer6-efficiency/lib/qualification_replay.py`
- [ ] T047 [US3] [FR-011] [FR-014] [FR-035] GREEN: register Slice 2 tests and governed fixture data in `tests/speckit-pro/suite-manifest.json` without parallel writes to the shared manifest
- [ ] T048 [US3] [FR-011] [FR-016] [FR-034] REFACTOR: run the two focused Slice 2 test files plus `python3 tests/speckit-pro/run-all.py --layer 4`, scan committed fixtures for sensitive fields, inspect `git diff --check`, and record Slice 2 G7 evidence

## Slice 3 — Experiment Policy, Statistics, and Calibration

**Goal**: Freeze immutable comparison and analysis contracts, apply the
assigned-attempt quality-first decision sequence, support deterministic replay,
and run only explicit budgeted calibration that cannot qualify a route.

**Independent test**: Replay paired frozen score bundles through binding,
partition, completeness, floor, non-inferiority, and Pareto gates; exercise all
attrition/rerun/budget/cache/tail cases; and prove calibration can freeze a
schema-valid plan but cannot emit route policy.

- [ ] T049 [US4] [FR-013] [FR-022] [FR-037] [FR-038] RED: add structural tests for partition, immutable assignment, experiment policy, complete campaign ceilings, and schema-governed analysis-plan fields in `tests/speckit-pro/unit/test-codex-qualification-contracts.py`
- [ ] T050 [US4] [FR-013] [FR-022] GREEN: author the closed-partition, explicit-local/replay, full-pair-rerun, and complete-budget contract in `tests/speckit-pro/layer6-efficiency/contracts/experiment-policy.schema.json`
- [ ] T051 [US4] [FR-017] [FR-018] [FR-021] [FR-022] [FR-023] [FR-038] GREEN: author workload strata, p95 guardrails, cache isolation, floors, paired cluster adjustment, sample-size assumptions, multiplicity, attrition, rerun, budgets, racing/futility, and terminal rules in `tests/speckit-pro/layer6-efficiency/contracts/analysis-plan.schema.json`
- [ ] T052 [US4] [FR-019] [FR-024] [FR-032] GREEN: author ordered analysis gates and closed decision outcomes in `tests/speckit-pro/layer6-efficiency/contracts/analysis-decision.schema.json`
- [ ] T053 [US4] [FR-037] RED: add pre-execution binding tests covering comparison set, candidate/comparator routes, role, fixture, task, instruction/config hashes, snapshot/freeze, route resolution, materialization, policy, plan, partition, and additive refresh invalidation in `tests/speckit-pro/unit/test-codex-qualification-contracts.py`
- [ ] T054 [US4] [FR-013] [FR-037] GREEN: implement immutable comparison assignment, partition registry validation, and contract loading in `tests/speckit-pro/layer6-efficiency/lib/qualification_contracts.py`
- [ ] T055 [US4] [FR-037] REFACTOR: prohibit post-execution rebinding and cross-partition reuse, rerun the focused contract tests, and record green evidence
- [ ] T056 [US4] [FR-017] RED: add absolute semantic/reliability floor pass/fail/uncertain golden cases in `tests/speckit-pro/unit/test-codex-qualification-statistics.py`
- [ ] T057 [US4] [FR-018] RED: add task-paired, role/fixture-cluster-adjusted non-inferiority confidence-bound cases for frozen margins, power, alpha, sample sizes, assumptions, and multiplicity in `tests/speckit-pro/unit/test-codex-qualification-statistics.py`
- [ ] T058 [US4] [FR-018] [FR-019] RED: add raw-vector Pareto candidate/comparator dominance, tie, mixed, and uncertain cases proving no hidden weighted score in `tests/speckit-pro/unit/test-codex-qualification-statistics.py`
- [ ] T059 [US4] [FR-018] [FR-038] RED: add frozen workload-strata, minimum-unique-task, unknown-stratum, long-horizon, p95 resource/duration, and cache-state/order-leakage negatives in `tests/speckit-pro/unit/test-codex-qualification-statistics.py`
- [ ] T060 [US4] [FR-017] [FR-018] [FR-019] GREEN: implement floors, paired/cluster-adjusted non-inferiority, multiplicity, and unweighted Pareto sequencing in `tests/speckit-pro/layer6-efficiency/lib/qualification_statistics.py`
- [ ] T061 [US4] [FR-018] [FR-038] GREEN: implement workload manifest, p95 guardrail, sample-size assumption, and cache-isolation validators in `tests/speckit-pro/layer6-efficiency/lib/qualification_statistics.py`
- [ ] T062 [US4] [FR-017] [FR-018] [FR-019] REFACTOR: make ordered gate short-circuiting explicit, remove any average-only or unpaired comparison path, rerun focused statistics tests, and record green evidence
- [ ] T063 [US4] [FR-020] [FR-021] RED: add candidate failure/timeout/cancel/budget/abandonment acceptance-zero cases, unknown attrition evidence-boundary cases, transient harness classification, rerun-cap, complete-pair-only, and incomplete-after-cap cases in `tests/speckit-pro/unit/test-codex-qualification-statistics.py`
- [ ] T064 [US4] [FR-020] [FR-021] GREEN: implement assigned-attempt inclusion, unclassifiable attrition blocking, frozen attrition cap, and complete-pair rerun decisions in `tests/speckit-pro/layer6-efficiency/lib/qualification_statistics.py`
- [ ] T065 [US4] [FR-020] [FR-021] REFACTOR: remove complete-case filtering and one-arm retry paths, rerun terminal/attrition golden cases, and record green evidence
- [ ] T066 [US4] [FR-022] [FR-038] RED: add missing/exceeded attempts, wall-clock, raw-input, cached-input, output, candidate-count, and confirmation-entry budget cases in `tests/speckit-pro/unit/test-codex-qualification-statistics.py`
- [ ] T067 [US4] [FR-022] [FR-038] GREEN: implement fail-closed campaign budget validation shared by experiment policy and frozen analysis plan in `tests/speckit-pro/layer6-efficiency/lib/qualification_statistics.py`
- [ ] T068 [US4] [FR-013] [FR-019] [FR-024] RED: add calibration, screening, selection, cohort-lock, and integrated-confirmation partition fixtures proving G56R-003 accepts only non-qualification calibration and rejects final policy/default/aggregate/release outputs in `tests/speckit-pro/unit/test-codex-qualification-statistics.py`
- [ ] T069 [US4] [FR-013] [FR-019] [FR-024] GREEN: implement calibration-only decision restrictions and explicit inconclusive/no-qualification handling in `tests/speckit-pro/layer6-efficiency/lib/qualification_statistics.py`
- [ ] T070 [US4] [FR-010] [FR-032] RED: add clean-checkout replay cases that validate every ID/digest, recompute the ordered analysis output, and match decision ID/digest byte-for-byte without network or live writes in `tests/speckit-pro/unit/test-codex-qualification-statistics.py`
- [ ] T071 [US4] [FR-010] [FR-032] GREEN: implement deterministic experiment/score/plan/decision replay in `tests/speckit-pro/layer6-efficiency/lib/qualification_replay.py`
- [ ] T072 [US4] [FR-010] [FR-032] REFACTOR: remove embedded trace or mutable upstream data from replay bundles, rerun clean-checkout replay fixtures, and record green evidence
- [ ] T073 [US4] [FR-022] [FR-023] [FR-024] RED: add CLI tests requiring explicit confirmation, pinned client/snapshot, calibration partition, complete budgets, operator-only raw root, frozen scorer/rubric/adjudicator IDs, workload/cache policy, and refusal of implicit live or outcome-bearing partitions in `tests/speckit-pro/unit/test-codex-qualification-contracts.py`
- [ ] T074 [US4] [FR-022] [FR-023] GREEN: implement explicit `calibrate`, deterministic `replay`, and `freeze-analysis-plan` commands in `tests/speckit-pro/layer6-efficiency/run-codex-qualification.py`
- [ ] T075 [US4] [FR-023] [FR-038] RED: add analysis-plan freeze tests proving calibration provenance, independent review, schema validity, complete numeric rules, and absence of G56R-007 through G56R-010 outcomes at freeze time in `tests/speckit-pro/unit/test-codex-qualification-statistics.py`
- [ ] T076 [US4] [FR-023] [FR-038] GREEN: implement versioned post-calibration pre-cohort analysis-plan freeze and additive invalidation in `tests/speckit-pro/layer6-efficiency/lib/qualification_statistics.py`
- [ ] T077 [US4] [FR-013] [FR-019] [FR-020] [FR-021] [FR-024] [FR-027] [FR-034] [FR-038] RED: add consolidated negative fixtures rejecting final route-policy IDs, integrated-confirmation consumption, live-default CI, raw/private evidence, arm-only retries, post-hoc thresholds, trace mutation, duplicate materializers, cache leakage, unknown attrition, unrestricted failure codes, and missing budget ceilings in `tests/speckit-pro/unit/test-codex-qualification-statistics.py`
- [ ] T078 [US4] [FR-013] [FR-019] [FR-024] REFACTOR: collapse decision production to one deterministic replay path, confirm `run_codex_role_eval.py` remains absent, rerun all G56R-003 focused tests, and record green evidence
- [ ] T079 [US4] [FR-025] GREEN: register all Slice 3 tests and deterministic replay fixtures in `tests/speckit-pro/suite-manifest.json`, preserving serial ownership of the shared manifest
- [ ] T080 [US4] [FR-025] REFACTOR: run `python3 tests/speckit-pro/run-all.py --layer 4`, inspect `git diff --check`, review the Slice 3 authored/generated boundary, and record Slice 3 G7 evidence

## Final Cross-Slice Verification

- [ ] T081 [US1] [US2] [US3] [US4] [FR-001] [FR-010] [FR-016] [FR-025] RED: run the complete focused G56R-003 unit set from a clean process and record any cross-slice ordering, import, fixture, schema, or replay failure before final fixes
- [ ] T082 [US1] [US2] [US3] [US4] [FR-001] [FR-010] [FR-016] GREEN: apply only the minimum cross-slice fixes required by T081 and rerun the complete focused set to green
- [ ] T083 [US1] [US2] [US3] [US4] [FR-025] REFACTOR: run `python3 -u tests/speckit-pro/run-all.py` and preserve the full zero-failure evidence
- [ ] T084 [US2] [FR-026] REFACTOR: run `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py --check` after all authored and generated outputs are final
- [ ] T085 [US1] [US2] [US3] [US4] [FR-025] REFACTOR: validate the exact intended final PR title through the repository release-readiness gate using `<type>(<lowercase-scope>): <plain English description>`
- [ ] T086 [US1] [US2] [US3] [US4] [FR-025] REFACTOR: perform final self-review for G56R-002 immutability, source/generated boundaries, sensitive-evidence allowlist, three-slice reviewability, and complete requirements traceability

## Dependencies and Parallel Safety

- Slice 1 is required before Slice 2 because corpus scoring consumes the
  successor freeze, materializer, and treatment eligibility.
- Slice 2 is required before Slice 3 because analysis consumes immutable score
  bundles.
- Within Slice 2, T023–T034 are parallel-safe because each task owns one
  disjoint fixture directory. T035 is the sole corpus-manifest serializer and
  starts only after all twelve complete.
- Shared files are always serial:
  `run-codex-qualification.py`, `qualification_contracts.py`,
  `qualification_scoring.py`, `qualification_statistics.py`,
  `qualification_replay.py`, every shared schema, and
  `suite-manifest.json`.
- Generated release artifacts are owned only by T019/T084 and never hand
  edited.

## Requirement Traceability

| Requirement | Tasks |
|---|---|
| FR-001 | T001, T005–T007, T081 |
| FR-002 | T002, T005 |
| FR-003 | T003, T005, T007 |
| FR-004 | T003, T005 |
| FR-005 | T003, T005 |
| FR-006 | T008–T011, T020 |
| FR-007 | T012, T016 |
| FR-008 | T008, T010, T012, T016 |
| FR-009 | T013, T015–T016 |
| FR-010 | T014–T017, T070–T072, T081–T082 |
| FR-011 | T021–T036, T047–T048 |
| FR-012 | T021–T022, T032–T036, T046 |
| FR-013 | T035, T049, T054, T068–T069, T077 |
| FR-014 | T037, T040, T045, T047 |
| FR-015 | T038–T040, T045 |
| FR-016 | T041–T044, T046, T048, T081–T082 |
| FR-017 | T051, T056, T060, T062 |
| FR-018 | T051, T057–T062 |
| FR-019 | T052, T058, T060, T068–T069, T077 |
| FR-020 | T063–T065, T077 |
| FR-021 | T051, T063–T065, T077 |
| FR-022 | T049–T051, T066–T067, T073–T074 |
| FR-023 | T051, T073–T076 |
| FR-024 | T052, T068–T069, T073, T077 |
| FR-025 | T079–T083, T085–T086 |
| FR-026 | T018–T020, T084 |
| FR-027 | T002, T005, T043, T077 |
| FR-028 | T004–T006 |
| FR-029 | T003, T005, T007 |
| FR-030 | T013, T015 |
| FR-031 | T014–T015 |
| FR-032 | T041–T042, T052, T070–T072 |
| FR-033 | T021–T036 |
| FR-034 | T041–T045, T077 |
| FR-035 | T038–T040, T045 |
| FR-036 | T043–T044 |
| FR-037 | T049, T053–T055 |
| FR-038 | T049, T051, T059, T061, T066–T067, T075–T077 |

All 38 functional requirements have at least one RED task, GREEN task, or
explicit verification/refactor task, and each user story remains independently
testable at its slice boundary.
