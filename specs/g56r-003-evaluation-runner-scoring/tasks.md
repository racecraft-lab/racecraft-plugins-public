# Tasks: G56R-003 Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/`, `quickstart.md`, and the four completed domain checklists.

**Executor contract**: Every numbered task is independently assignable to one
`implement-executor` and contains a complete RED → VERIFY RED → GREEN → VERIFY
GREEN → REFACTOR → VERIFY cycle. A task is not complete without real failing
test evidence followed by focused green evidence.

**Review order**: Slice 1 → Slice 2 → Slice 3. Shared manifests, schemas,
registries, helpers, and generated artifacts have one serial owner.

## Slice 1 — Capability, Materialization, and Trace

**Goal**: Publish an additive non-empty successor freeze, use one shipped
exact-byte materializer, and emit score-eligibility treatment evidence through
new immutable G56R-003 traces under the unchanged G56R-002 contract.

- [x] T001 [US1] [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-027] [FR-028] [FR-029] Implement additive successor capability publication with strict TDD: RED table-driven immutability, pinned-catalog provenance, sanitization, effort normalization, diagnostic-surface, topology-control, exclusion, empty/malformed/stale/untrusted/identity/digest/retention/historical-mutation cases in `tests/speckit-pro/unit/test-codex-successor-capability.py`; GREEN the smallest collector/intersection/publisher in `tests/speckit-pro/layer6-efficiency/lib/codex_successor_capability.py` plus `tests/speckit-pro/layer6-efficiency/contracts/successor-capability-freeze.schema.json`; REFACTOR through existing G56R-002 capability and retention helpers; VERIFY the focused test and unchanged G56R-002 bytes
- [x] T002 [US2] [FR-006] [FR-008] Implement the shipped canonical agent materializer with strict TDD: RED golden exact UTF-8 bytes, instructions/config digests, source binding, idempotence, parsed-equivalence rejection, and Layer 6/G56R-006 import-contract cases in `tests/speckit-pro/unit/test-agent-materialization.py`; GREEN `speckit-pro/speckit_pro_runner/agent_materialization.py`; REFACTOR so callers retain file writes/execution and no evaluation renderer exists; VERIFY the focused test
- [x] T003 [US2] [FR-009] [FR-010] [FR-030] [FR-031] Implement exact-treatment eligibility and immutable trace joins with strict TDD: RED mandatory observation, permitted null, missing/unavailable/undocumented, installed/exact-byte proof, configured-route, reroute monitoring, service reroute, misdelivery, ambiguous/unapproved/unidentifiable delivery, and one-trace-per-assignment cases in `tests/speckit-pro/unit/test-codex-qualification-contracts.py`; GREEN G56R-002-backed validation in `tests/speckit-pro/layer6-efficiency/lib/qualification_contracts.py`; REFACTOR through existing treatment model/bundle/replay helpers without changing the old schema; VERIFY focused and adjacent G56R-002 tests
- [x] T004 [US2] [FR-007] [FR-008] [FR-009] [FR-010] Implement the thin durable qualification entry point with strict TDD: RED CLI cases proving legacy smoke remains non-release, publication/treatment commands use the shared materializer and refuse score-before-treatment in `tests/speckit-pro/unit/test-codex-qualification-contracts.py`; GREEN `tests/speckit-pro/layer6-efficiency/run-codex-qualification.py`; REFACTOR command parsing and deterministic JSON I/O with Python 3.11 standard library only; VERIFY focused CLI tests and absence of `run_codex_role_eval.py`
- [x] T005 [US2] [FR-026] Integrate shipped source trust with strict TDD: RED a runner-trust test that fails for the new unregistered materializer in `tests/speckit-pro/unit/test-agent-materialization.py`; GREEN register source and run `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py`; REFACTOR by keeping every manifest/checksum/payload/cache-proof/release-evidence edit generator-owned; VERIFY the focused trust test and `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py --check`
- [x] T006 [US1] [US2] [FR-001] [FR-006] [FR-010] [FR-025] [FR-026] Close Slice 1 with strict regression TDD: RED one end-to-end sanitized catalog→freeze→materialization→assignment→trace replay that initially exposes any missing join in `tests/speckit-pro/unit/test-codex-qualification-contracts.py`; GREEN only the minimum cross-module fix; REFACTOR registrations in `tests/speckit-pro/suite-manifest.json`; VERIFY all Slice 1 focused tests, `python3 tests/speckit-pro/run-all.py --layer 4`, `git diff --check`, generated drift, and Slice 1 G7 evidence

## Slice 2 — Corpus and Blinded Scoring

**Goal**: Govern exactly twelve role contracts, gate invalid fixtures and
treatments before scoring, collect two independent blind ballots, adjudicate
decision-affecting disagreement, and emit immutable sanitized score bundles
with closed failure and invalidation taxonomies.

- [x] T007 [US3] [FR-011] [FR-012] [FR-033] Implement the role-corpus contract and validator with strict TDD: RED exact membership, required-core/helper, executability, source/fixture/oracle/review digest, partition, tools, sandbox, expected artifact, stale fixture, and admitted-route-only scheduling cases in `tests/speckit-pro/unit/test-codex-qualification-corpus.py`; GREEN `tests/speckit-pro/layer6-efficiency/contracts/role-corpus.schema.json` and `tests/speckit-pro/layer6-efficiency/lib/qualification_corpus.py`; REFACTOR deterministic ordering and closed validation; VERIFY the focused test
- [x] T008 [P] [US3] [FR-011] [FR-033] Author the first disjoint executable fixture group with strict TDD: RED per-role contract expectations in `tests/speckit-pro/unit/test-codex-corpus-fixtures-a.py`; GREEN `fixture.json` for `analyze-executor`, `checklist-executor`, `clarify-executor`, and `codebase-analyst` under their respective `tests/speckit-pro/layer6-efficiency/fixtures-codex/` directories; REFACTOR shared field shape without touching the corpus manifest; VERIFY the group test
- [x] T009 [P] [US3] [FR-011] [FR-033] Author the second disjoint executable fixture group with strict TDD: RED per-role contract expectations in `tests/speckit-pro/unit/test-codex-corpus-fixtures-b.py`; GREEN `fixture.json` for `domain-researcher`, `implement-executor`, `phase-executor`, `spec-context-analyst`, and `uat-runbook-author`; REFACTOR shared field shape without touching the corpus manifest; VERIFY the group test
- [x] T010 [P] [US3] [FR-011] [FR-012] [FR-033] Author the non-executable/helper fixture group with strict TDD: RED governed-but-not-schedulable and helper-separation expectations in `tests/speckit-pro/unit/test-codex-corpus-fixtures-c.py`; GREEN `fixture.json` for `consensus-synthesizer`, `gate-validator`, and `autopilot-fast-helper`; REFACTOR shared field shape without touching the corpus manifest; VERIFY the group test
- [x] T011 [US3] [FR-011] [FR-012] [FR-013] Serialize the corpus with strict TDD after T008–T010: RED exact 12/11/9/2/1 counts, disjoint partition binding, non-executable skip, and helper-primary-statistic separation in `tests/speckit-pro/unit/test-codex-qualification-corpus.py`; GREEN the sole shared `tests/speckit-pro/layer6-efficiency/fixtures-codex/corpus-manifest.json`; REFACTOR deterministic role ordering and digest construction; VERIFY all four corpus test files
- [x] T012 [US3] [FR-014] Implement deterministic hard gates with strict TDD: RED role, safety, grounding, mutation, tool, output, acceptance, missing evidence, and gate-order cases in `tests/speckit-pro/unit/test-codex-qualification-scoring.py`; GREEN the smallest ordered gate engine in `tests/speckit-pro/layer6-efficiency/lib/qualification_scoring.py`; REFACTOR closed gate results and score-before-gates prohibition; VERIFY the focused test
- [x] T013 [US3] [FR-015] [FR-035] Implement blinded ballots and adjudication with strict TDD: RED distinct scorer/execution, blinded artifact, frozen rubric, current calibration, missing/stale/non-blind/duplicate ballot, disagreement, third-adjudicator provenance/currentness/non-reuse cases in `tests/speckit-pro/unit/test-codex-qualification-scoring.py`; GREEN ballot validation and adjudication in `qualification_scoring.py`; REFACTOR identity-independent deterministic records; VERIFY the focused test
- [x] T014 [US3] [FR-016] [FR-032] [FR-034] Implement immutable score bundles with strict TDD: RED every upstream ID/digest, closed disposition/plane/code/invalidation enums, `none` coupling, candidate terminals, unclassifiable attrition, additive invalidation, and no embedded/mutated trace cases in `tests/speckit-pro/unit/test-codex-qualification-scoring.py`; GREEN `tests/speckit-pro/layer6-efficiency/contracts/score-bundle.schema.json` and bundle construction in `qualification_scoring.py`; REFACTOR failure taxonomy dispatch; VERIFY the focused test
- [x] T015 [US3] [FR-016] [FR-027] [FR-034] [FR-036] Implement scorer evidence safety and replay with strict TDD: RED raw prompt/response/transcript, personal mapping, account/auth/credential/session/cookie/header/private-host/absolute-path/remote/billing, unknown-key, stale-version, and replay-drift cases in `tests/speckit-pro/unit/test-codex-qualification-scoring.py`; GREEN allowlisting, opaque bindings, evidence refs, additive invalidation, and deterministic score replay in `qualification_scoring.py` and `tests/speckit-pro/layer6-efficiency/lib/qualification_replay.py`; REFACTOR one sanitizer boundary; VERIFY the focused test and sensitive-field scan
- [x] T016 [US3] [FR-011] [FR-014] [FR-015] [FR-016] [FR-025] Close Slice 2 with strict regression TDD: RED one treatment-proven governed-fixture→hard-gates→two-ballots→adjudication→score replay plus separate helper summary in `tests/speckit-pro/unit/test-codex-qualification-scoring.py`; GREEN only the minimum cross-module fix; REFACTOR single-owner suite registration in `tests/speckit-pro/suite-manifest.json`; VERIFY all Slice 2 focused tests, Layer 4, sensitive-field scan, `git diff --check`, and Slice 2 G7 evidence

## Slice 3 — Experiment Policy, Statistics, and Calibration

**Goal**: Freeze immutable comparison and analysis contracts, apply the
assigned-attempt quality-first decision sequence, support deterministic replay,
and run only explicit budgeted calibration that cannot qualify a route.

- [x] T017 [US4] [FR-013] [FR-017] [FR-018] [FR-019] [FR-021] [FR-022] [FR-023] [FR-024] [FR-032] [FR-037] [FR-038] Implement calibration-protocol, experiment, analysis-plan, and decision contracts with strict TDD: RED eligibility-selected protocol/plan binding, closed partition, immutable pair binding, full budget, workload/p95/cache, floors/NI/Pareto, attrition/rerun, pre-cohort freeze, and ordered decision schema cases in `tests/speckit-pro/unit/test-codex-qualification-contracts.py`; GREEN `calibration-protocol.schema.json`, `experiment-policy.schema.json`, `analysis-plan.schema.json`, and `analysis-decision.schema.json` under `tests/speckit-pro/layer6-efficiency/contracts/`; REFACTOR shared ID/digest validation; VERIFY focused contracts
- [x] T018 [US4] [FR-013] [FR-037] Implement immutable comparison assignment and partition isolation with strict TDD: RED all pre-execution route/role/fixture/task/hash/snapshot/freeze/resolution/materialization/policy/calibration-protocol/partition joins, refresh invalidation, post-execution rebinding, and cross-partition reuse cases in `tests/speckit-pro/unit/test-codex-qualification-contracts.py`; GREEN assignment and partition validators in `qualification_contracts.py`; REFACTOR deterministic binding helpers; VERIFY focused contracts
- [x] T019 [US4] [FR-017] [FR-018] [FR-019] Implement quality-first statistical sequencing with strict TDD: RED semantic/reliability floors, paired role/fixture-cluster-adjusted non-inferiority confidence bounds, frozen margins/power/alpha/sample size/assumptions/multiplicity, and raw-vector candidate/comparator/tie/mixed/uncertain Pareto cases in `tests/speckit-pro/unit/test-codex-qualification-statistics.py`; GREEN `tests/speckit-pro/layer6-efficiency/lib/qualification_statistics.py`; REFACTOR explicit short-circuit order and prohibit hidden weights/unpaired comparisons; VERIFY the focused test
- [x] T020 [US4] [FR-018] [FR-038] Implement workload-tail and cache controls with strict TDD: RED strata/weights/long-horizon/minimum-task/unknown-stratum, p95 token/duration, cache-isolation, treatment-order leakage, and average-only cases in `test-codex-qualification-statistics.py`; GREEN validators in `qualification_statistics.py`; REFACTOR frozen policy bindings; VERIFY focused statistics
- [x] T021 [US4] [FR-020] [FR-021] [FR-034] Implement terminal, attrition, and rerun policy with strict TDD: RED candidate failure/timeout/cancel/budget/abandonment acceptance-zero, unclassifiable attrition, transient harness classification, attrition/rerun caps, complete-pair-only, one-arm, complete-case, and incomplete-after-cap cases in `test-codex-qualification-statistics.py`; GREEN assigned-attempt and rerun logic in `qualification_statistics.py`; REFACTOR closed dispositions; VERIFY focused statistics
- [x] T022 [US4] [FR-013] [FR-019] [FR-022] [FR-024] [FR-038] Implement complete budgets and calibration partition boundaries with strict TDD: RED missing/exceeded attempt, wall-clock, raw/cached/output tokens, candidates, confirmation entries, screening/selection/cohort-lock/integrated-confirmation, final policy/default/aggregate/release, failed gate/tie/mixed/incomplete/uncertain cases in `test-codex-qualification-statistics.py`; GREEN budget and calibration-only decision logic in `qualification_statistics.py`; REFACTOR one no-qualification path; VERIFY focused statistics
- [x] T023 [US4] [FR-010] [FR-022] [FR-023] [FR-032] Implement deterministic replay and explicit local CLI with strict TDD: RED clean-checkout ID/digest/recomputed-decision equality, no-network/no-live-write, explicit confirmation, pinned client/snapshot, calibration partition, budgets, operator-only raw root, scorer/rubric/adjudicator/workload/cache bindings, and implicit-live refusal in focused contract/statistics tests; GREEN replay in `qualification_replay.py` plus `calibrate`, `replay`, and `freeze-analysis-plan` commands in `run-codex-qualification.py`; REFACTOR one deterministic command/result path; VERIFY focused replay/CLI tests
- [x] T024 [US4] [FR-013] [FR-019] [FR-020] [FR-021] [FR-023] [FR-024] [FR-027] [FR-034] [FR-038] Implement analysis freeze and prohibited-boundary coverage with strict TDD: RED independent review/schema validity/numeric completeness/pre-cohort absence plus final route policy, integrated confirmation, live-default CI, raw evidence, arm-only retry, post-hoc threshold, trace mutation, duplicate materializer, cache leak, unknown attrition, unrestricted code, and missing budget cases in `test-codex-qualification-statistics.py`; GREEN versioned freeze/additive invalidation and minimum boundary fixes; REFACTOR audit-friendly errors; VERIFY all focused tests and absence of `run_codex_role_eval.py`
- [x] T025 [US1] [US2] [US3] [US4] [FR-001] [FR-010] [FR-016] [FR-025] [FR-026] Close Slice 3 and the feature with strict cross-slice regression TDD: RED one full sanitized source-ledger→successor→materialization→trace→corpus→score→analysis-plan→calibration-decision replay exposing any remaining join drift; GREEN only minimum cross-slice fixes; REFACTOR final `suite-manifest.json` registration; VERIFY all focused tests, G56R-002 regressions, `python3 -u tests/speckit-pro/run-all.py`, `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py --check`, `git diff --check`, exact PR-title release-readiness validation, and Slice 3 G7 evidence

## Dependencies and Parallel Safety

- T001–T006 are serial. Slice 1 must be green before Slice 2.
- T007 establishes the corpus validator. T008–T010 may then run in parallel
  because each owns disjoint fixture directories and a disjoint test file.
- T011 serializes their results into the sole shared corpus manifest.
- T012–T016 are serial. Slice 2 must be green before Slice 3.
- T017–T025 are serial because they share contract, statistics, replay, CLI,
  and suite-registration surfaces.
- Generated release artifacts are owned only by T005/T025 and are never hand
  edited.

## Requirement Traceability

| Requirement | Tasks |
|---|---|
| FR-001 | T001, T006, T025 |
| FR-002 | T001 |
| FR-003 | T001 |
| FR-004 | T001 |
| FR-005 | T001 |
| FR-006 | T002, T006 |
| FR-007 | T004 |
| FR-008 | T002, T004 |
| FR-009 | T003, T004 |
| FR-010 | T003–T004, T006, T023, T025 |
| FR-011 | T007–T011, T016 |
| FR-012 | T007, T010–T011 |
| FR-013 | T011, T017–T018, T022, T024 |
| FR-014 | T012, T016 |
| FR-015 | T013, T016 |
| FR-016 | T014–T016, T025 |
| FR-017 | T017, T019 |
| FR-018 | T017, T019–T020 |
| FR-019 | T017, T019, T022, T024 |
| FR-020 | T021, T024 |
| FR-021 | T017, T021, T024 |
| FR-022 | T017, T022–T023 |
| FR-023 | T017, T023–T024 |
| FR-024 | T017, T022, T024 |
| FR-025 | T006, T016, T025 |
| FR-026 | T005–T006, T025 |
| FR-027 | T001, T015, T024 |
| FR-028 | T001 |
| FR-029 | T001 |
| FR-030 | T003 |
| FR-031 | T003 |
| FR-032 | T014, T017, T023 |
| FR-033 | T007–T011 |
| FR-034 | T014–T015, T021, T024 |
| FR-035 | T013 |
| FR-036 | T015 |
| FR-037 | T017–T018 |
| FR-038 | T017, T020, T022, T024 |

All 38 functional requirements are mapped. Every numbered task is a complete
TDD unit that one implementation executor can own without crossing into a
later task.
