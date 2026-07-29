# Tasks: G56R-004 Policy Controls and Adaptive Comparators

**Input**: `specs/g56r-004-policy-controls-adaptive-comparators/spec.md`,
`plan.md`, `docs/ai/specs/.process/G56R-004-design-concept.md`, and completed
checklists for data integrity, error handling, LLM integration, and
performance.

**Organization**: One dependency-ordered P1 slice for User Story 1. RED tasks are immediately followed by their GREEN implementation task.

**Implementation boundary**: Use only the 12 implementation paths declared in `plan.md`. Do not edit the suite manifest, frozen G56R-003/CAR-003/CAR-004 artifacts, generated payloads, installed-cache proofs, generated reference pages, vendored content, or live-smoke raw captures.

## Allowed Implementation Paths

- `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/policy-control-registry.schema.json`
- `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/control-comparison.schema.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/policy-control-registry.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/control-comparison.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/partition-registry-entries.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/replay-cases.json`
- `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py`
- `tests/speckit-pro/layer6-efficiency/lib/codex_control_comparison.py`
- `tests/speckit-pro/layer6-efficiency/lib/codex_control_smoke.py`
- `tests/speckit-pro/unit/test-policy-control-contracts.py`
- `tests/speckit-pro/unit/test-control-comparison-dominance.py`
- `tests/speckit-pro/unit/test-twin-handoff-completeness.py`

## Phase 1: Baseline and Guardrails

**Purpose**: Establish the starting state and keep the implementation bounded before edits begin.

- [X] T001 [P] Run baseline repository verification before edits using the existing owners `tests/speckit-pro/unit/test-policy-control-contracts.py`, `tests/speckit-pro/unit/test-control-comparison-dominance.py`, and `tests/speckit-pro/unit/test-twin-handoff-completeness.py`; record the baseline result outside the implementation paths for PR notes only. Sources: `spec.md` SC-001-SC-019; `plan.md` Technical Context, Testing, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [X] T002 [P] Confirm the edit target set is limited to the six new schema/fixture paths and three new helper paths under `tests/speckit-pro/layer6-efficiency/`, plus the three existing unit owners under `tests/speckit-pro/unit/`; do not add implementation paths. Sources: `spec.md` Reviewability Budget; `plan.md` Declared File Operations, Reviewability Budget; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [X] T003 [P] Confirm live ChatGPT sign-in smoke execution remains operator-only and unrun while deterministic replay and smoke plan/seal validation are implemented in `tests/speckit-pro/layer6-efficiency/lib/codex_control_smoke.py` and `tests/speckit-pro/unit/test-policy-control-contracts.py`. Sources: `spec.md` FR-035-FR-039, SC-014-SC-017; `plan.md` Technical Context, Performance Goals; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.

---

## Phase 2: User Story 1 - Freeze Policy Controls Before Final Routing Outcomes Exist (Priority: P1) MVP

**Goal**: Freeze Codex-local policy controls, adaptive replay behavior, comparison semantics, reserved partitions, and smoke sealing as deterministic repository-only evidence before G56R-011 observes final static-core outcomes.

**Independent Test**: The three declared Layer 4 owners validate the schemas, fixtures, helpers, mirror completeness, deterministic replay, comparison behavior, reserved-objective refusal, smoke plan/seal behavior, and review traceability without live model execution.

### RED/GREEN Tasks

- [X] T004 [US1] RED: Add failing registry schema/fixture tests in `tests/speckit-pro/unit/test-policy-control-contracts.py` for exact three controls, unique `control_kind`, Codex IDs, content-address preimages, and frozen binding digest failure. Sources: `spec.md` FR-001-FR-005, SC-001-SC-003; `plan.md` Declared File Operations, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [X] T005 [US1] GREEN: Create `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/policy-control-registry.schema.json` and `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/policy-control-registry.json` to satisfy T004 without editing frozen artifacts. Sources: `spec.md` FR-001-FR-005, SC-001-SC-003; `plan.md` Declared File Operations, Implementation Boundaries; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [X] T006 [US1] RED: Add failing bidirectional mirror tests in `tests/speckit-pro/unit/test-twin-handoff-completeness.py` for the CAR-004 category 1-6 subset derivable from the registry schema/fixture available after T005, including registry-owned shapes, required sets, the single sanctioned `justified_high_effort` divergence, and registry-owned zeros, units, enums, and numerics. Sources: `spec.md` FR-002, FR-006-FR-007, FR-040, SC-004; `plan.md` Test Ownership, Constraints; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [X] T007 [US1] GREEN: Implement registry-owned mirror derivation and validation helpers in `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py`, backed by `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/policy-control-registry.json`; defer comparison-owned category 1-6 members and partition-owned members to their later RED/GREEN pairs rather than treating the T007 subset as the final completeness proof. Sources: `spec.md` FR-002, FR-006-FR-007, FR-040, SC-004; `plan.md` Declared File Operations, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T008 [US1] RED: Add failing unpinned-control tests in `tests/speckit-pro/unit/test-policy-control-contracts.py` for one inherited parent arm, parent context identity, absent local overrides, and produced-evidence read-back. Sources: `spec.md` FR-008-FR-009, FR-037, SC-015; `plan.md` Test Ownership, Constraints; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T009 [US1] GREEN: Add unpinned control validation to `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py` and the matching control instance in `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/policy-control-registry.json`. Sources: `spec.md` FR-008-FR-009, FR-037, SC-015; `plan.md` Declared File Operations, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T010 [US1] RED: Add failing adaptive-ladder tests in `tests/speckit-pro/unit/test-policy-control-contracts.py` for admitted ordered G56R-003 tuples, hash-relevant route order, cross-model rationales, duplicate or omitted route rejection, and invalidation on drift. Sources: `spec.md` FR-010-FR-011, FR-017, SC-005; `plan.md` Test Ownership, Implementation Boundaries; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T011 [US1] GREEN: Add adaptive ladder definitions and invalidation checks in `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/policy-control-registry.json` and `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py`. Sources: `spec.md` FR-010-FR-011, FR-017, SC-005; `plan.md` Declared File Operations, Implementation Boundaries; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T012 [US1] RED: Add failing adaptive signal-resolution tests in `tests/speckit-pro/unit/test-policy-control-contracts.py` for closed observed sources, total single-valued response mapping, precedence, plane/code consistency, terminal/code consistency, and unknown closed-domain refusal. Sources: `spec.md` FR-012-FR-013, SC-006; `plan.md` Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T013 [US1] GREEN: Implement adaptive signal mapping in `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py` and deterministic cases in `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/replay-cases.json`. Sources: `spec.md` FR-012-FR-013, SC-006; `plan.md` Declared File Operations, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T014 [US1] RED: Add failing adaptive movement and breach tests in `tests/speckit-pro/unit/test-policy-control-contracts.py` for one escalation per objective, no floor or ceiling wrap, three-clean-pass de-escalation, non-scorable streak exclusion, retry/cancellation breach pairings, budget-trigger responses, and `service_reroute`. Sources: `spec.md` FR-014-FR-016, SC-007; `plan.md` Test Ownership, Performance Goals; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T015 [US1] GREEN: Implement adaptive movement, retry/cancellation, budget-trigger, and platform-reroute replay behavior in `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py` and `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/replay-cases.json`. Sources: `spec.md` FR-014-FR-016, SC-007; `plan.md` Declared File Operations, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T016 [US1] RED: Add failing justified-high-effort tests in `tests/speckit-pro/unit/test-policy-control-contracts.py` for the bound route ID, model, effort, successor freeze digest, route-evidence digest, eligibility predicate, rationale, no fallback, and produced-evidence read-back. Sources: `spec.md` FR-018-FR-019, FR-023, SC-008, SC-015; `plan.md` Implementation Boundaries, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T017 [US1] GREEN: Add justified-high-effort binding data and validation in `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/policy-control-registry.json` and `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py`. Sources: `spec.md` FR-018-FR-019, FR-023, SC-008, SC-015; `plan.md` Declared File Operations, Implementation Boundaries; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T018 [US1] RED: Add failing parent-plus-children aggregation tests in `tests/speckit-pro/unit/test-policy-control-contracts.py` for child inclusion, all eight decision dimensions, raw-token members, cache diagnostics, null acceptance, non-completed floor-to-zero, missing terminal fail-closed, and unobserved cache preservation. Sources: `spec.md` FR-020-FR-022, SC-009; `plan.md` Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T019 [US1] GREEN: Implement parent-plus-children aggregation in `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py` with coverage fixtures in `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/replay-cases.json`. Sources: `spec.md` FR-020-FR-022, SC-009; `plan.md` Declared File Operations, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T020 [US1] RED: Add failing comparison contract tests in `tests/speckit-pro/unit/test-control-comparison-dominance.py` for eligibility gates, eight dimensions, direction rules, 10% margins, confidence method, multiplicity, zero denominator, inconclusive or no-verdict mapping, no weighted score, and comparison-owned category 1-6 mirror members including null-valued no-worse-only margins for `acceptance`, `compactions`, `retries`, and `terminal_state`. Sources: `spec.md` FR-002, FR-006-FR-007, FR-024-FR-028, FR-040, SC-004, SC-010; `plan.md` Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T021 [US1] GREEN: Create `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/control-comparison.schema.json`, `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/control-comparison.json`, and `tests/speckit-pro/layer6-efficiency/lib/codex_control_comparison.py` to satisfy T020, proving the comparison-owned category 1-6 mirror members and preserving nulls, zeros, units, enums, and numerics exactly. Sources: `spec.md` FR-002, FR-006-FR-007, FR-024-FR-028, FR-040, SC-004, SC-010; `plan.md` Declared File Operations, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T022 [US1] RED: Add failing verdict and release-claim tests in `tests/speckit-pro/unit/test-control-comparison-dominance.py` for total verdict-to-claim-class mapping, dominant messaging restrictions, static shipment for operational simplicity, and no final G56R-011 dominance conclusion. Sources: `spec.md` FR-029-FR-030, SC-011; `plan.md` Test Ownership, PR Review Packet Source; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T023 [US1] GREEN: Implement verdict-to-claim mapping in `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/control-comparison.json` and `tests/speckit-pro/layer6-efficiency/lib/codex_control_comparison.py`. Sources: `spec.md` FR-029-FR-030, SC-011; `plan.md` Declared File Operations, PR Review Packet Source; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T024 [US1] RED: Add failing reserved-partition tests in `tests/speckit-pro/unit/test-policy-control-contracts.py` for content-addressed G56R-011 reserved and G56R-004 smoke partitions, partition-owned category 1-6 mirror members, mutual disjointness, replay refusal, smoke plan refusal, smoke seal refusal, and zero scored or selection/cohort objective consumption. Sources: `spec.md` FR-002, FR-006-FR-007, FR-031-FR-033, FR-040, SC-004, SC-012; `plan.md` Test Ownership, Performance Goals; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T025 [US1] GREEN: Create `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/partition-registry-entries.json` and implement reserved-objective guards in `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py` and `tests/speckit-pro/layer6-efficiency/lib/codex_control_smoke.py`, proving the partition-owned category 1-6 mirror members available only after the partition fixture exists. Sources: `spec.md` FR-002, FR-006-FR-007, FR-031-FR-033, FR-040, SC-004, SC-012; `plan.md` Declared File Operations, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T026 [US1] RED: Add failing deterministic replay tests in `tests/speckit-pro/unit/test-policy-control-contracts.py` requiring every control fixture to replay twice byte-identically with governed evidence and zero outcome-bearing scored rows. Sources: `spec.md` FR-034, SC-013; `plan.md` Test Ownership, Performance Goals; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T027 [US1] GREEN: Implement deterministic replay cases and byte-stable governed output in `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/replay-cases.json` and `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py`. Sources: `spec.md` FR-034, SC-013; `plan.md` Declared File Operations, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T028 [US1] RED: Add failing smoke plan/seal tests in `tests/speckit-pro/unit/test-policy-control-contracts.py` for exactly one ChatGPT-sign-in smoke per control, authorization-withheld as `unrun`, API-key or ambiguous auth refusal, all mirrored ceilings, raw-token identity, elapsed wall-clock scope, child-dispatch attempt exclusion, produced-evidence exact treatment, and all three unordered cache-isolation pairs. Sources: `spec.md` FR-035-FR-038, SC-014-SC-016; `plan.md` Technical Context, Performance Goals, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T029 [US1] GREEN: Implement non-live smoke planning, refusal, bound checking, exact-treatment read-back validation, and cache-isolation validation in `tests/speckit-pro/layer6-efficiency/lib/codex_control_smoke.py`, with any required governed fixture metadata in `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/replay-cases.json`. Sources: `spec.md` FR-035-FR-038, SC-014-SC-016; `plan.md` Declared File Operations, Performance Goals, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T030 [US1] RED: Add failing raw-capture exclusion tests in `tests/speckit-pro/unit/test-policy-control-contracts.py` that reject committed live model text, prompts, responses, operator-local paths, unsanitized captures, and path-based cache roots while admitting governed summaries, digests, refusal records, and non-raw replay fixtures. Sources: `spec.md` FR-039, SC-017; `plan.md` Technical Context, Constraints; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T031 [US1] GREEN: Implement repository-safe smoke summary and refusal sanitization in `tests/speckit-pro/layer6-efficiency/lib/codex_control_smoke.py` and non-raw evidence fixtures in `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/replay-cases.json`. Sources: `spec.md` FR-039, SC-017; `plan.md` Declared File Operations, Technical Context; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T032 [US1] RED: Add failing final twin reconciliation tests in `tests/speckit-pro/unit/test-twin-handoff-completeness.py` that re-run the full category 1-6 derivation across registry-owned, comparison-owned, and partition-owned Codex artifacts in both directions; fail on any missing, extra, invented, drifted, duplicated, or silently omitted mirror member; and for any genuinely unrepresentable member, name the member, preserve the CAR-004 obligation, record a declined disposition, and forbid frozen-contract edits. Sources: `spec.md` FR-002, FR-006-FR-007, FR-040-FR-041, SC-004, SC-018; `plan.md` Unresolved For Consensus, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T033 [US1] GREEN: Implement final full bidirectional completeness, no-omission, and unmirrorable-member disposition checks in `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py` without weakening Codex fixtures or editing frozen artifacts. Sources: `spec.md` FR-002, FR-006-FR-007, FR-040-FR-041, SC-004, SC-018; `plan.md` Declared File Operations, Unresolved For Consensus; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.

**Checkpoint**: User Story 1 should now be testable independently through the three declared Layer 4 owners, with live smoke still unrun unless an operator separately authorizes it.

---

## Phase 3: Verification and Review Evidence

**Purpose**: Prove the completed slice, produce reviewer-ready traceability, and keep out-of-scope surfaces untouched.

- [ ] T034 Build the PR review-packet traceability from changed implementation paths, known gaps, operator-only smoke status, rollback or non-applicability notes, and no production-routing change statement; source the mapping from `tests/speckit-pro/unit/test-policy-control-contracts.py`, `tests/speckit-pro/unit/test-control-comparison-dominance.py`, and `tests/speckit-pro/unit/test-twin-handoff-completeness.py`. Sources: `spec.md` FR-042, SC-019; `plan.md` PR Review Packet Source, Reviewability Budget; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T035 Run narrow verification for `tests/speckit-pro/unit/test-policy-control-contracts.py`, `tests/speckit-pro/unit/test-control-comparison-dominance.py`, and `tests/speckit-pro/unit/test-twin-handoff-completeness.py`; fix only the 12 allowed implementation paths if failures expose task-scope defects. Sources: `spec.md` SC-001-SC-019; `plan.md` Test Ownership, Testing; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T036 Run docs reference generation and checking required for changed test-tree Python in `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py`, `tests/speckit-pro/layer6-efficiency/lib/codex_control_comparison.py`, and `tests/speckit-pro/layer6-efficiency/lib/codex_control_smoke.py`; do not hand-edit generated reference pages. Sources: `spec.md` FR-042, SC-019; `plan.md` Testing, PR Review Packet Source; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T037 Run broader repository verification after narrow checks pass, covering the three declared unit owners and the unchanged structural registration of `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py`, `tests/speckit-pro/layer6-efficiency/lib/codex_control_comparison.py`, and `tests/speckit-pro/layer6-efficiency/lib/codex_control_smoke.py`. Sources: `spec.md` SC-001-SC-019; `plan.md` Testing, Test Ownership; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.
- [ ] T038 Final safety check: confirm no live smoke was run, no raw captures were committed, no suite-manifest change was made, and no frozen artifact was edited while the implemented evidence remains confined to `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/replay-cases.json` and `tests/speckit-pro/layer6-efficiency/lib/codex_control_smoke.py`. Sources: `spec.md` FR-005, FR-035-FR-039, SC-014-SC-017; `plan.md` Technical Context, Implementation Boundaries; `docs/ai/specs/.process/G56R-004-design-concept.md` selected decisions.

---

## Dependencies and Execution Order

- **Phase 1**: Run T001-T003 before any file edit.
- **Phase 2**: Execute every RED/GREEN pair in order. Each GREEN task depends on the immediately preceding RED task failing for the intended reason.
- **Phase 3**: Run T034-T038 after all RED/GREEN pairs pass.

## Parallel Opportunities

- T001, T002, and T003 are parallel-safe because they are read-only guardrail checks.
- After implementation, independent reviewers can inspect the schema/fixture files, helper modules, and unit owners in parallel, but code edits should follow the dependency order above.

## Coverage Matrix

| Coverage | Tasks |
|----------|-------|
| FR-001-FR-005 | T004-T005 |
| FR-006-FR-007 | T006-T007, T020-T021, T024-T025, T032-T033 |
| FR-008-FR-009 | T008-T009 |
| FR-010-FR-017 | T010-T015 |
| FR-018-FR-023 | T016-T019 |
| FR-024-FR-030 | T020-T023 |
| FR-031-FR-034 | T024-T027 |
| FR-035-FR-039 | T028-T031, T038 |
| FR-040-FR-041 | T006-T007, T020-T021, T024-T025, T032-T033 |
| FR-042 | T034-T037 |
| SC-001-SC-003 | T004-T005 |
| SC-004 | T006-T007, T020-T021, T024-T025, T032-T033 |
| SC-005 | T010-T011 |
| SC-006 | T012-T013 |
| SC-007 | T014-T015 |
| SC-008 | T016-T017 |
| SC-009 | T018-T019 |
| SC-010 | T020-T021 |
| SC-011 | T022-T023 |
| SC-012 | T024-T025 |
| SC-013 | T026-T027 |
| SC-014-SC-016 | T028-T029, T038 |
| SC-017 | T030-T031, T038 |
| SC-018 | T032-T033 |
| SC-019 | T034-T037 |

## Implementation Strategy

1. Complete the read-only baseline and guardrail tasks.
2. Work through the 15 RED/GREEN pairs in order.
3. Stop if FR-041 discovers a genuinely unrepresentable mirror-required member; record the declined disposition and raise the paired roadmap reconciliation item before continuing.
4. Run narrow verification, docs reference generation/checking for changed test-tree Python, broader repository verification, and the final safety check.
5. Keep operator-only live smoke unrun unless a human separately authorizes it outside this task list.

## Unresolved Items

- Operator-only live smoke execution remains unrun by design.
- FR-041 has no known reconciliation item at task-generation time; implementation must stop only if a concrete unmirrorable member is discovered.
