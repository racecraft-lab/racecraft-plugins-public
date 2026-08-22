# Tasks: G56R-005 Model Availability, Fallback, and Recovery Simulation

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/fallback-recovery-contract.md](./contracts/fallback-recovery-contract.md)

## Phase 1: Foundations

- [ ] T001 Add Codex fallback JSON schemas for route policy, route report, and recovery record under `tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/` (FR-001, FR-003, FR-018).
- [ ] T002 Add the fallback/recovery fixture corpus under `tests/speckit-pro/layer6-efficiency/fixtures-codex-fallback/fallback-recovery-corpus.json` with all required scenario rows represented (FR-021).
- [ ] T003 Add failing schema identity and fixture coverage tests in `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` before implementation (FR-021, SC-001).
- [ ] T004 Register the new focused test file in `tests/speckit-pro/suite-manifest.json` after the first failing test exists (FR-022).

## Phase 2: User Story 1 - Deterministic Route Resolution

- [ ] T005 Add failing tests for preferred absence, unsupported effort, discovery unavailable, availability probe success/failure, treatment probe failure, fallback exhaustion, and single terminal outcome (FR-003, FR-004, FR-005, FR-010).
- [ ] T006 Implement the pure route resolver in `tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py` with strict override pre-check, ordered walk, loop-on-arrival detection, and fixed diagnostic ordering (FR-002, FR-003, FR-007, FR-010).
- [ ] T007 Add replay byte-stability assertions for route diagnostics and terminal outcomes across three consecutive runs (SC-002, SC-003).

## Phase 3: User Story 2 - Service Reroute Attribution

- [ ] T008 Add failing tests for approved reroute, unapproved reroute, mixed service/plugin reasons, unqualified-adjacent target, and scoring eligibility split (FR-008, FR-009).
- [ ] T009 Implement service reroute attribution as a separate report section and keep plugin reasons in local deterministic order (FR-008).
- [ ] T010 Implement scoring eligibility so approved service evidence can preserve eligibility only for qualified immutable routes and unapproved evidence is ineligible (FR-009).
- [ ] T011 Add treatment digest comparisons that permit only model and effort changes and reject non-route mutations (FR-006).

## Phase 4: User Story 3 - Fake-Home Recovery And Optional Helper

- [ ] T012 Add failing tests for optional-helper unavailable, explicit no-helper continuation, helper counters separate from required-route counters, and required-agent success or atomic failure (FR-011).
- [ ] T013 Add failing tests for temporary-root-only writes, real-home/traversal/symlink rejection, immutable fixture seeds, atomic no-write, rollback, cleanup, previous-known-good preservation, and rollback failure disposition (FR-015, FR-016, FR-017).
- [ ] T014 Implement canonical fake-home state manifests and state IDs excluding absolute roots and host metadata (FR-017, FR-018).
- [ ] T015 Implement the staged fake-home adapter that writes only under `<fake_home_root>/.codex/agents`, rolls back touched managed files, runs bounded cleanup, and emits Recovery Records (FR-015, FR-016, FR-017, FR-018).
- [ ] T016 Encode the optional-helper rule so all bundled TOML source files are validated for integrity, while `autopilot-fast-helper.toml` is conditional optional helper state rather than required destination completeness (FR-011).

## Phase 5: User Story 4 - Bounded Sequential Harness

- [ ] T017 Add failing tests for retry, time, fan-out, context, cancellation, escalation, inherited model, inherited effort, generic substitution, and recursive/HITL rejection (FR-012, FR-013, FR-014).
- [ ] T018 Implement one non-recursive sequential replay harness with deterministic counters and terminal precedence for strict override, budgets, cancellation, writes, and route outcomes (FR-012, FR-013, FR-014).
- [ ] T019 Add replay assertions that outputs contain no absolute temporary roots, timestamps, inodes, or host-specific paths (FR-018).

## Phase 6: Review Evidence And Verification

- [ ] T020 Add traceability evidence in the focused test module or fixture metadata mapping every FR/SC to coverage and replay output (FR-022, SC-008).
- [ ] T021 Run `python3 tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` and preserve the passing output for PR evidence.
- [ ] T022 Run `python3 tests/speckit-pro/run-all.py --layer 4` and preserve the passing output for deterministic harness evidence.
- [ ] T023 Run `python3 tests/speckit-pro/run-all.py` and preserve the full-suite result.
- [ ] T024 Run generated-artifact and scope checks appropriate to changed `.py`/`.md` test-surface files, including docs reference generation/check if required by repository rules.
- [ ] T025 Prepare the PR packet with non-goals, review order, traceability, verification, rollback, and explicit live-smoke-unrun evidence.

## Dependencies

- T001-T004 must complete before user-story implementation tasks.
- T005 must fail before T006; T008 before T009/T010; T012/T013 before T014/T015/T016; T017 before T018.
- T020-T025 run after all implementation tasks.

## Parallel Opportunities

- T005, T008, T012, T013, and T017 can be drafted independently after T001-T004.
- T009/T010 and T014/T015 can proceed in parallel only after their RED tests exist.
- Verification tasks T021-T024 are sequential because each broadens confidence.
