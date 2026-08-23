# Tasks: G56R-005 Model Availability, Fallback, and Recovery Simulation

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/fallback-recovery-contract.md](./contracts/fallback-recovery-contract.md)

## Phase 1: Foundation

- [X] T001 [P] Add Codex fallback schemas in `tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/route-policy.schema.json`, `tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/route-resolution-report.schema.json`, and `tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/recovery-record.schema.json` (FR-001, FR-003, FR-018).
- [X] T002 [P] Add `tests/speckit-pro/layer6-efficiency/fixtures-codex-fallback/fallback-recovery-corpus.json` with all required scenario rows plus the reviewed bundled-source roster identity and required/optional classifications represented (FR-016, FR-021).
- [X] T003 Add failing schema identity, source-roster drift, and fixture coverage tests in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` before implementation (FR-016, FR-021, SC-001, SC-006).
- [X] T004 Register `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` in `tests/speckit-pro/suite-manifest.json` after the first failing test exists (FR-022).

## Phase 2: User Story 1 - Deterministic Route Resolution

- [X] T005 Add failing preferred-absence, effort, discovery, availability, treatment, exhaustion, and single-terminal tests in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` (FR-003, FR-004, FR-005, FR-010).
- [X] T006 Implement the pure resolver in `tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py` and prove it in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` with strict override pre-check, ordered walk, loop-on-arrival detection, fixed diagnostic ordering, and no import of the frozen Claude resolver or shared resolver core (FR-002, FR-003, FR-007, FR-010, FR-019, SC-004).
- [X] T007 Add three-run route-diagnostic and terminal byte-stability assertions in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` (SC-002, SC-003).

## Phase 3: User Story 2 - Service Reroute Attribution

- [X] T008 Add failing reroute-attribution and scoring-split cases in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` and `tests/speckit-pro/layer6-efficiency/fixtures-codex-fallback/fallback-recovery-corpus.json` (FR-008, FR-009, SC-005).
- [X] T009 Implement separate service-reroute attribution in `tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py` and prove plugin reason order in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` (FR-008, SC-005).
- [X] T010 Implement scoring eligibility in `tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py` and prove approved/qualified versus unapproved/ineligible cases in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` (FR-009, SC-005).
- [X] T011 Implement treatment digest comparison in `tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py` and prove model/effort-only deltas in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` (FR-006).

## Phase 4: User Story 3 - Fake-Home Recovery And Optional Helper

- [X] T012 Add failing helper, current-roster, drift, counter-separation, and required-core atomicity cases in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` and `tests/speckit-pro/layer6-efficiency/fixtures-codex-fallback/fallback-recovery-corpus.json` (FR-011, FR-016).
- [X] T013 Add failing fake-home boundary, seed immutability, no-write, rollback, cleanup, previous-known-good, and rollback-failure cases in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` and `tests/speckit-pro/layer6-efficiency/fixtures-codex-fallback/fallback-recovery-corpus.json` (FR-015, FR-016, FR-017).
- [X] T014 Implement canonical fake-home state manifests and IDs in `tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py` and verify excluded host metadata in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` (FR-017, FR-018).
- [X] T015 Implement the staged fake-home adapter and Recovery Records in `tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py` and prove bounded rollback/cleanup in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` (FR-015, FR-016, FR-017, FR-018).
- [X] T016 Derive and bind the bundled-source roster in `tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py`, validate the helper classification against `speckit-pro/codex-agents/autopilot-fast-helper.toml`, and prove fail-closed identity drift in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` (FR-011, FR-016).

## Phase 5: User Story 4 - Bounded Sequential Harness

- [X] T017 Add failing bound, cancellation, inheritance, substitution, recursion, and HITL-rejection cases in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` and `tests/speckit-pro/layer6-efficiency/fixtures-codex-fallback/fallback-recovery-corpus.json` (FR-012, FR-013, FR-014, SC-007).
- [X] T018 Implement the bounded non-recursive harness in `tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py` and prove deterministic counters and terminal precedence in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` (FR-012, FR-013, FR-014, SC-007).
- [X] T019 Add host-data exclusion assertions in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` for canonical replay output (FR-018).

## Phase 6: Polish - Review Evidence And Verification

- [X] T020 Add FR/SC traceability evidence to `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` and `tests/speckit-pro/layer6-efficiency/fixtures-codex-fallback/fallback-recovery-corpus.json` (FR-022, SC-008).
- [X] T021 Run `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` and preserve passing output for PR evidence.
- [X] T022 Run Layer 4 through `tests/speckit-pro/run-all.py` and preserve deterministic harness evidence.
- [X] T023 Run the full suite through `tests/speckit-pro/run-all.py` and preserve the result.
- [X] T024 Run generated-artifact, docs-reference, spec-index, and scope checks for `tests/speckit-pro/suite-manifest.json` and all changed test-surface files, including `pnpm --dir docs-site reference:generate`/`reference:check` when the tracked `tests/speckit-pro/` change contract applies and `python3 scripts/refresh-release-artifacts.py --check` to prove payload/release artifacts remain unchanged (FR-020, SC-009).
- [X] T025 Prepare the PR packet from `specs/g56r-005-model-availability-fallback-recovery/plan.md` with non-goals, review order, traceability, verification, rollback, explicit live-smoke-unrun evidence, and proof that production routing, payload/version/release artifacts, checkpoint/resume behavior, and frozen Claude/G56R-004 contracts were not modified (FR-019, FR-020, SC-008, SC-009).

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation**: No prerequisites.
- **US1**: Depends on Foundation.
- **US2**: Depends on US1.
- **US3**: Depends on Foundation and US1.
- **US4**: Depends on US1 and US3.
- **Polish**: Depends on US1, US2, US3, and US4.

Within those increments, T005 must fail before T006; T008 before T009/T010;
T012/T013 before T014/T015/T016; and T017 before T018.

### Incremental Delivery

1. Complete Foundation: T001-T004
2. Complete US1: T005-T007
3. Complete US2: T008-T011
4. Complete US3: T012-T016
5. Complete US4: T017-T019
6. Complete Polish: T020-T025

### User Story Dependencies

- **US1**: Independently demonstrates deterministic route resolution.
- **US2**: Extends the qualified-route report with separate reroute attribution.
- **US3**: Extends the resolved-route contract through the fake-home adapter.
- **US4**: Wraps route and recovery behavior in the bounded sequential harness.

## Parallel Opportunities

- T001 and T002 are marked `[P]` because schemas and fixture seeds touch disjoint files.
- Story RED tests are dependency-separable but share one focused test module, so they are not marked `[P]`.
- Verification tasks T021-T024 are sequential because each broadens confidence.
