# Tasks: Autopilot, Gate, and PR-Emission Repair

**Input**: HRNS-015 spec, plan, research, data model, contracts, quickstart, workflow Tasks Prompt, and ratified design concept. **Execution limit**: the entire automated implementation, startup, repair, and final checks has a two-hour budget. Every behavior task begins with a failing acceptance case and records RED before its minimal fix and GREEN. No task may be checked off from prose alone. Both hosts ship together for every host-facing behavior. Tests live under `tests/speckit-pro/` and freeze historical prose in test-owned fixtures; tests never open a temporary feature spec at run time.

**Reviewability status**: [slice-inventory.md](.process/slice-inventory.md) names 19 one-story candidate increments, each with six recurring tracked workflow/process/evidence paths and ≤4 production/≤24 total candidate paths. The four mixed-story markers and the eleven-increment path omissions are superseded. Reused registered test modules keep A1, B2, and C1a inside the cap while retaining RED/GREEN cases. Actual reviewable LOC and diffs remain unmeasured. The installed `pr_marker_plan` validator still rejects legitimate repeated declared paths across successive markers, so no valid persisted plan, G6 pass, or emitted PR is claimed until that product contract is repaired. The advisory `atomicity-route` stays `one-navigable-PR`.

## Proposed review increments and marker boundaries

Every marker has exactly one US identity. An unsplit story uses `usN`; repeated sequential story parts use unique `usN-partK` IDs with `parent_marker_id=usN`, matching the installed marker contract. A1a/A1b finish US1, B2a/B2b finish US6, C1a2/C1b1/C1b2 finish US10, and C2a3/C2b1 finish US13. T007 amends the cross-cutting PRD/roadmap scope within A2. T001/T002 establish the inventory; T033 follows all checkpoints. Both host variants of each behavior remain in the same increment.

At every checkpoint, refresh generated outputs, run its RED/GREEN acceptance cases and quick suite, verify host parity, measure exact changed paths and reviewable LOC, run title/release-note gates, and record marker fingerprints. A new output or over-limit diff stops publication and requires reallocation. Candidate counts alone never pass a gate.

| Increment | Marker ID | US | Required tasks | Candidate paths | Production paths |
| --- | --- | --- | --- | ---: | ---: |
| A1a | `us1-part1` | US1 | T003–T004 | 24 | 2 |
| A1b | `us1-part2` | US1 | T005 | 24 | 2 |
| A2 | `us2` | US2 | T006–T007 | 24 | 1 |
| A3 | `us3` | US3 | T008–T009 | 24 | 2 |
| B1a | `us4` | US4 | T010 | 22 | 1 |
| B1b | `us5` | US5 | T011 | 23 | 2 |
| B2a | `us6-part1` | US6 | T012–T013 | 22 | 2 |
| B2b | `us6-part2` | US6 | T014–T015 | 23 | 1 |
| B3a | `us7` | US7 | T016 | 18 | 1 |
| B3b | `us8` | US8 | T017–T018 | 22 | 2 |
| C1a1 | `us9` | US9 | T019 | 24 | 1 |
| C1a2 | `us10-part1` | US10 | T020 | 21 | 1 |
| C1b1 | `us10-part2` | US10 | T021 | 21 | 2 |
| C1b2 | `us10-part3` | US10 | T022–T023 | 21 | 2 |
| C2a1 | `us11` | US11 | T024–T025 | 14 | 0 |
| C2a2 | `us12` | US12 | T026 | 14 | 0 |
| C2a3 | `us13-part1` | US13 | T027 | 14 | 0 |
| C2b1 | `us13-part2` | US13 | T028–T029 | 21 | 0 |
| C2b2 | `us14` | US14 | T030–T032 | 22 | 0 |

## Phase 1: Setup (shared evidence)

**Goal**: Establish exact reviewable ownership before any code change. **Independent test**: each of the 19 proposed increments has a distinct source/generated/test/refactor candidate ledger, including repeated shared paths, with production classification and explicitly unmeasured actual LOC/diff.

- [ ] T001 Inventory every authored, fixture, shared, generated, trust, index, and process/evidence candidate path by increment in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; classify production paths and distinct required refactors, including repeated paths in each owning PR (FR-026).

## Phase 2: Foundational budget gate

**Goal**: Keep the two-hour delivery reviewable. **Independent test**: 19 complete named candidate sets fit four production and 24 total paths; actual LOC/diffs and the repeated-path marker contract remain explicit stops before PR emission.

- [ ] T002 Reconcile all 19 one-story candidate sets with Plan’s `not_estimated` result, Q11’s historical four/five-slice decisions, the current `one-navigable-PR` advisory, and the invalid repeated-path marker contract; stop marker persistence/emission until the product contract and actual per-increment gates pass (FR-026).

## Phase 3: User Story 1 — final release note (P1, A1a then A1b)

**Goal**: A final packet accepts one valid optional note. **Independent test**: the emitted body passes the feature-PR release-note policy; invalid note and draft cases fail or omit as specified (FR-001–003, FR-026).

- [ ] T003 [US1] Add failing-first valid, blank, non-string, fence-breaking, absent, and draft `release_note` cases to the existing registered `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`; use inline cases and record RED before renderer/schema edits (FR-001, FR-003).
- [ ] T004 [US1] Implement optional note input/rendering as prefilled protected content in `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`, `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`, and paired Claude/Codex autopilot skills; leave the fourth editable marker pair for A1b; prove T003 GREEN, refresh A1a outputs, run targeted and quick suites, then record A1a path/production/LOC, host parity, and marker checkpoint before T005 (FR-001, FR-003, FR-026).
- [ ] T005 [US1] Add failing-first protected-heading, balanced-fence, editable-content, and policy cases in the existing registered `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py`; then add the fourth editable marker pair in `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`, update `speckit-pro/speckit_pro_runner/helpers/read_only.py` so only enclosed note content is elided while heading, markers, and fence structure stay protected, and update paired Claude/Codex autopilot skills. Prove the release-note validator passes. Prove GREEN, refresh A1b outputs, run targeted and quick suites, and record A1b path/production/LOC, host parity, and marker checkpoint before T006 (FR-002, FR-026).

## Phase 4: User Story 2 — packet-only untracked files (P1, Increment A2)

**Goal**: The current packet's three untracked files do not block its own mutation. **Independent test**: validate and refresh pass for only canonical packet files; second packet, unrelated file, tracked edit, and unreadable status block (FR-004–005, FR-026).

- [ ] T006 [US2] First add failing packet-only/unrelated/second-packet/tracked/unreadable-status cases in the existing registered `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` and `tests/speckit-pro/unit/fixtures/pr-packet-repair/packet-only-untracked.json`; record RED, then repair `speckit-pro/speckit_pro_runner/helpers/mutation.py` and paired post-implementation references; prove GREEN without force-add or ignore-rule changes (FR-004, FR-005, FR-026).
- [ ] T007 Amend AC-16.2/16.5/16.8/16.10 and HRNS-015/HRNS-019 scope in `docs/prd-harness-engineering-uplift.md` and `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`; remove stale #642 status. Refresh A2 outputs, run its tests and quick suite, and record A2 path/production/LOC, host parity, and marker checkpoint before T008 (FR-027).

## Phase 5: User Story 3 — current confidence verdict (P1, Increment A3)

**Goal**: Final body reflects current G6.5 Verdict. **Independent test**: first emission and refresh show current protected verdict; missing/invalid verdict blocks, with no overview fallback (FR-006, FR-026).

- [ ] T008 [US3] Add failing-first first-emission, stale-body refresh, and missing-verdict cases inline in the existing registered `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`; then repair `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, and paired autopilot skills; prove the protected current G6.5 Verdict line GREEN without overview fallback (FR-006, FR-026).

## Phase 6: A3 integration and validation

**Goal**: Preserve the current-verdict packet contract after A2 has aligned PRD and roadmap scope. **Independent test**: A3 verdict fixture, quick suite, generated refresh, reference check, title and release-note checks pass; measured path/LOC budget fits.

- [ ] T009 Refresh A3 dist/reference/trust outputs, run its verdict cases and quick suite plus title/release-note checks, measure all actual changed paths and LOC, and record A3 RED/GREEN, host parity, and marker checkpoint in the slice inventory; stop before publication on any limit or failed gate (FR-006, FR-026).

## Phase 7: User Story 4 — visible marker counts (P1, Increment B1a)

**Goal**: G1–G4 and count-markers agree on visible Gap and clarification markers. **Independent test**: exact comma-token tags, two per line, visible prose, and inline/fenced/indented code have expected counts and details (FR-007–008, FR-026).

- [ ] T010 [US4] First add failing marker cases for compound tags, two tags per line, and visible versus inline/fenced/indented code; record RED, then repair `speckit-pro/speckit_pro_runner/helpers/read_only.py` and shared gate guidance, verify both host payloads, and prove GREEN. Register the new test, refresh B1a outputs, run targeted/quick suites, and record B1a budget/marker checkpoint (FR-007, FR-008, FR-026).

## Phase 8: User Story 5 — tracked spec index (P1, Increment B1b)

**Goal**: Required artifact consistency detects stale tracked spec indexes. **Independent test**: stale check fails, refresh repairs, untracked nested candidate stays absent, staged addition stays eligible (FR-009–010).

- [ ] T011 [US5] Freeze historical stale-index prose under the test fixture and add RED tracked/untracked/staged cases; repair `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `scripts/refresh-release-artifacts.py`, and root `AGENTS.md`, regenerate `specs/formal-001-selective-formal-methods/SPEC-MOC.md`, and prove GREEN. Register the new test, refresh B1b outputs, run targeted/quick suites, and record B1b budget/marker checkpoint (FR-009, FR-010, FR-026).

## Phase 9: User Story 6 — named reviewability entry (P1, B2a then B2b)

**Goal**: Issue #637's exact selected entry controls budget, exception, and split results. **Independent test**: original `multi`, `pragma`, `nobudget` reproductions and added selected-section, greenfield, primary-surface, aggregate, and malformed-slice cases pass (FR-011–014, FR-028–029).

- [ ] T012 [US6] Add failing-first #637 `multi`, `pragma`, `nobudget`, missing `spec_id`, and neighboring-entry cases inline in the existing registered `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py`; record RED before gate edits (FR-011–013).
- [ ] T013 [US6] Require exact `spec_id`, isolate its authored roadmap section/primary surfaces, fail closed on missing fields, and accept only valid typed exceptions in `speckit-pro/speckit_pro_runner/helpers/registry.py`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, the existing read-only helper test, and paired gate guidance; prove T012 GREEN, refresh B2a outputs, run targeted/quick suites, and record B2a budget/marker checkpoint (FR-011–013, FR-026).
- [ ] T014 [US6] Add failing-first complete/incomplete/duplicate/extra/non-numeric/over-line slice-row and greenfield LOC-only cases inline in the existing registered read-only helper test; record RED for aggregates, ordered `slice_results`, and blocked rows (FR-014, FR-028, FR-029).
- [ ] T015 [US6] Implement exact ordered slice budgets and greenfield LOC-only allowance in `speckit-pro/speckit_pro_runner/helpers/read_only.py`; update paired gate guidance and `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md`; prove T014 GREEN without a new exception class, refresh B2b outputs, run targeted/quick suites, and record B2b budget/marker checkpoint (FR-014, FR-026, FR-028, FR-029).

## Phase 10: User Story 7 — refactor-aware estimate (P2, Increment B3a)

**Goal**: Required distinct refactor files change estimate and slice count. **Independent test**: refactor signal adds 40 LOC per distinct extra file after baseline/modify logic, missing or invalid signal leaves baseline, spike precedence holds (FR-015).

- [ ] T016 [US7] Add failing-first required-refactor estimate cases, then update `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `tests/speckit-pro/unit/test-size-estimate-refactors.py`; prove GREEN, confirm distinct refactor paths against the inventory, register the test, refresh B3a outputs, run targeted/quick suites, and record B3a budget/marker checkpoint (FR-015, FR-026).

## Phase 11: User Story 8 — declared quality commands (P1, Increment B3b)

**Goal**: The four approved quality slots accept explicit commands with provenance. **Independent test**: declared precedence, undeclared detection, malformed/unknown command G0 failure, and unchanged thresholds/basis (FR-016, FR-026).

- [ ] T017 [US8] Add failing-first declared-command precedence, undeclared detection, malformed/unknown G0 failure cases; then implement four-slot config/provenance in `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `.specify/quality-gates.json`, `tests/speckit-pro/unit/test-declared-quality-commands.py`, and paired gate guidance; prove GREEN without parsing agent-document tables (FR-016, FR-026).

## Phase 12: B3b integration and validation

**Goal**: Budgeted gates/counters pass with tracked index regeneration. **Independent test**: B3 fixtures, quick suite, generated refresh/reference check and actual path/LOC gate pass.

- [ ] T018 Register the new B3b test in `tests/speckit-pro/suite-manifest.json`, regenerate B3b dist/reference/trust outputs, run targeted/quick suites, and record RED/GREEN, actual file/LOC count, host parity, and marker checkpoint in the slice inventory; stop on any over-limit or incomplete inventory (FR-016, FR-026).

## Phase 13: User Story 9 — 13 canonical Post rows (P1, Increment C1a1)

**Goal**: Claude, Codex, and workflow template show the same 13 names. **Independent test**: exact once/order/count match and legacy 11-row resume preserves only unique exact-name statuses (FR-017–018, FR-026).

- [ ] T019 [US9] Add RED 11-versus-13 canonical Post and legacy-resume cases inline in the existing registered `tests/speckit-pro/unit/test-autopilot-phase-coverage.py`; then align `POST_STEPS`, both host skill/list guidance, and workflow template. Prove GREEN, refresh C1a1 outputs, run targeted/quick suites, and record C1a1 path/production/LOC, host parity, and marker checkpoint (FR-017, FR-026).

## Phase 14: User Story 10 — complete Post and teams (P1, C1a2 then C1b1/C1b2)

**Goal**: Full completion has a verified Post state and no active executor team. **Independent test**: both persisted records reject missing/duplicate/pending/in-progress/mismatch/unjustified skips; only validated extension absence permits identical skip, and each team-capable executor proves cleanup (FR-018–019, FR-026).

- [ ] T020 [US10] Add RED persisted workflow/state completion cases in the existing registered phase-coverage test for missing/duplicate/pending/in-progress/mismatch/skips/legacy resume; then repair the guard and both host completion call sites and post references. Prove GREEN, refresh C1a2 outputs, run targeted/quick suites, and record C1a2 budget/marker checkpoint before T021 (FR-018, FR-026).
- [ ] T021 [US10] Add failing RED structural/result cases for Claude and Codex `phase-executor` and `analyze-executor`; require child result or supported stop, graceful shutdown, no-active-child, and completed-cleanup evidence in those four exact agent definitions plus shared agent-team reference. Register the structural test, prove GREEN, refresh C1b1 outputs, run targeted/quick suites, and record C1b1 budget/marker checkpoint (FR-019, FR-026).
- [ ] T022 [US10] Add failing RED structural/result cases for Claude and Codex `checklist-executor` and `implement-executor`; apply the same teardown result contract to those four exact definitions and shared agent-team reference. Update the structural test, prove GREEN, and review formal lifecycle Post subset read-only; stop for re-inventory before any lifecycle edit (FR-019, FR-026).

## Phase 15: C1b2 integration and validation

**Goal**: Confirm executor teardown after C1a1 and C1a2 have passed their marker checkpoints. **Independent test**: the eight-definition structural fixture, quick suite, generated refresh/reference check, and measured 23-candidate-path/production/LOC gate pass.

- [ ] T023 Refresh C1b2 exact dist/agent/test reference outputs, run its structural cases and quick suite, and record all eight definitions’ GREEN evidence plus C1b2 actual paths/LOC, host parity, and marker checkpoint; stop before PR emission on any new path or failed gate (FR-019, FR-026).

## Phase 16: User Story 11 — complete review feedback after push (P1, Increment C2a1)

**Goal**: Resolve-pr exhausts pages and acts only on a verified matching remote head. **Independent test**: >100 threads/comments, failed page/cursor, failed verify/push/head match, and serial confirmed resolution cases (FR-020–021, FR-026).

- [ ] T024 [US11] Add RED multi-page thread/comment and failed-page/cursor cases, then specify complete GraphQL cursor traversal in both resolve-pr host skills and `tests/speckit-pro/unit/test-resolve-pr-protocol.py`; prove GREEN (FR-020, FR-026).
- [ ] T025 [US11] Add RED verification, push, fresh `headRefOid`, retry, serial reply/resolve, and resolved-readback cases, then enforce publication order in both resolve-pr host skills and the same test; prove GREEN, register the test, refresh C2a1 outputs, run targeted/quick suites, and record C2a1 budget/marker checkpoint (FR-021, FR-026).

## Phase 17: User Story 12 — wait for blind-spot result (P1, Increment C2a2)

**Goal**: A late nonempty analyst result is used. **Independent test**: >5-minute result is `ran`; dispatch error, empty return, and explicit operator abandonment record distinct matching header/status reasons (FR-022–023, FR-026).

- [ ] T026 [US12] Add RED late-result and three no-findings cases, then remove the fixed blind-spot wait and persist distinct Design Concept header/status reasons in both scaffold host skills and `tests/speckit-pro/unit/test-scaffold-blindspot.py`; prove GREEN, register the test, refresh C2a2 outputs, run targeted/quick suites, and record C2a2 budget/marker checkpoint (FR-022, FR-023, FR-026).

## Phase 18: User Story 13 — complete named helper requests (P2, C2a3 then C2b1)

**Goal**: Five named failure sites carry accepted full envelopes on both hosts. **Independent test**: status index/topology, scaffold reviewability/placement, and phase index-write examples all pass registry validation (FR-024, FR-026).

- [ ] T027 [US13] Add RED status index/topology envelope cases, then provide complete accepted examples in both status host skills and `tests/speckit-pro/unit/test-status-envelope-contract.py`; prove GREEN, register the test, refresh C2a3 outputs, run targeted/quick suites, and record C2a3 budget/marker checkpoint (FR-024, FR-026).
- [ ] T028 [US13] Add RED scaffold reviewability/placement envelope cases, then repair both scaffold host examples and `tests/speckit-pro/unit/test-scaffold-envelope-contract.py`; prove GREEN (FR-024, FR-026).
- [ ] T029 [US13] Add RED phase index-write envelope cases, then repair both phase-execution host references and `tests/speckit-pro/unit/test-phase-envelope-contract.py`; prove GREEN, register both tests, refresh C2b1 outputs, run targeted/quick suites, and record C2b1 budget/marker checkpoint (FR-024, FR-026).

## Phase 19: User Story 14 — real workflow links (P2, Increment C2b2)

**Goal**: Issue #638's generated link reaches scaffold output while valid legacy links survive. **Independent test**: new template, verified legacy target, and broken legacy target cases all resolve to real workflow files (FR-025–026).

- [ ] T030 [US14] Add failing-first #638 template, verified legacy, and broken legacy link cases in `tests/speckit-pro/unit/test-roadmap-workflow-links.py` and its compact fixture; record RED (FR-025).
- [ ] T031 [US14] Correct the roadmap template links, broken-legacy repair, both scaffold host skills, and `speckit-pro/README.md`; preserve verified existing targets and prove T030 GREEN (FR-025, FR-026).

## Phase 20: C2b2 integration and validation

**Goal**: Complete C2 with both host instructions and no HRNS-019 expansion. **Independent test**: C2b fixtures, quick suite, generated refresh/reference check and actual path/LOC gate pass.

- [ ] T032 Register the workflow-link test, regenerate C2b2 dist/reference outputs, run targeted/quick suites, and record C2b2 actual path/LOC, host parity, and marker checkpoint in the slice inventory; stop on incomplete or over-limit diff (FR-025, FR-026).

## Phase 21: Polish and cross-cutting validation

**Goal**: Prove the exact 19 planned increments before release. **Independent test**: full CI suite, artifact consistency, docs quality, lint, PR title/release-note fences, and requirement-to-file/red-green traceability pass with recorded commands and outcomes.

- [ ] T033 Run final acceptance, full CI, artifact, docs, lint, exact title/release-note, and all 19 per-increment budget gates; record FR-001–029 and SC-001–011 fixture/results plus non-goals/deferred HRNS-019/017 in the slice inventory. Any unavailable or failed gate remains explicit (FR-001–029).

## Dependencies and execution order

- T001 → T002 blocks all behavior. Marker order is A1a → A1b → A2 → A3 → B1a → B1b → B2a → B2b → B3a → B3b → C1a1 → C1a2 → C1b1 → C1b2 → C2a1 → C2a2 → C2a3 → C2b1 → C2b2. Each checkpoint completes before the next increment begins; T033 follows all 19.
- T003/T004, T012/T013, T014/T015, and T030/T031 remain adjacent RED-then-GREEN units. Other behavior tasks record RED and GREEN inside one task. At most four tasks are assigned to one implementation batch. T007 is cross-cutting scope prose inside the A2 marker and must finish before A3.
- T028 and T029 may run in parallel only if their exact scaffold and phase file ownership is disjoint; otherwise run sequentially. Repeated helper, trust, test, manifest, host, workflow, state, and evidence paths are owned sequentially across increments. No active parallel unit shares a path.
- The 19 named candidate sets correct H3–H7’s grouped path and mixed-story defects. The current marker validator still rejects legitimate repeated paths; no marker is valid until repaired. Each PR also stops on actual over-cap diff, unmeasured/failed LOC gate, stale fingerprint, or unsafe fold. All 29 FRs, including FR-018/019, remain in scope.

## Implementation strategy

Start with US1 because HRNS-016 depends on packet emission. At each increment preserve RED evidence, make the smallest repair, prove GREEN, run the quick suite, regenerate source-derived artifacts, and measure its exact final diff. Full CI and policy checks belong to T033. Stop optional expansion if the two-hour whole-spec budget cannot include repairs and final checks; report unfinished required tasks instead of checking them off.
