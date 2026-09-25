# Tasks: Autopilot, Gate, and PR-Emission Repair

**Input**: HRNS-015 spec, plan, research, data model, contracts, quickstart, workflow Tasks Prompt, and ratified design concept. **Execution limit**: the entire automated implementation, startup, repair, and final checks has a two-hour budget. Every behavior task begins with a failing fixture and records RED before its minimal fix and GREEN. No task may be checked off from prose alone. Both hosts ship together for every host-facing behavior. Tests live under `tests/speckit-pro/` and freeze any needed historical prose in their own fixtures; tests never open a temporary feature spec path at run time.

**Reviewability status**: the proposed eleven-increment candidate path allocation is fully named in [slice-inventory.md](.process/slice-inventory.md): A1 24, A2 16, A3 21, B1 22, B2 22, B3 17, C1a1 20, C1a2 15, C1b 23, C2a 18, C2b 23. All planned sets fit ≤4 production and ≤24 total paths, counting compact fixture children, generated payload/trust files, and conservative reference-page candidates. This corrects the five-PR breaches and C1a's omitted generated `tests.md` path. Actual reviewable LOC/diffs are unmeasured. The installed `pr_marker_plan` validator rejects legitimate duplicate declared paths across successive markers; no valid persisted plan, G6 pass, or emitted PR is claimed until that product contract is repaired. The advisory `atomicity-route` stays `one-navigable-PR`. Every behavior task starts RED, makes the minimal fix, and proves GREEN; each increment then refreshes/generated checks and measures its own exact diff before its PR.

## Proposed review increments and marker boundaries

A1 owns T003–T004 (US1); A2 owns T005 (US2); A3 owns T006–T008 (US3 and PRD/roadmap); B1 owns T009–T010 (US4/5); B2 owns T011–T014 (US6); B3 owns T015–T017 (US7/8); C1a1 owns T018 (US9); C1a2 owns T019 (US10 Post boundary); C1b owns T020–T021 (US10 teardown); C2a owns T022–T025 (US11/12 and status envelope); C2b owns T026–T030 (remaining US13 and US14). T001/T002 establish the inventory, and T031 follows all eleven checkpoints. Both host variants of a behavior stay in its one increment. Repeated `read_only.py`, `suite-manifest.json`, runner trust files, and host guidance are counted anew in each owning PR; the marker validator currently cannot represent this, so marker persistence and emission stop until fixed.

At each listed checkpoint, register any new test in the suite manifest, refresh `dist` and generated reference pages, run the increment's targeted fixtures and quick suite, record RED/GREEN, host parity, actual reviewable LOC, production count, all changed paths, title/release-note checks, and fresh marker fingerprints. A file or LOC cap failure, unlisted fixture, stale fingerprint, or unsafe fold stops publication. Candidate counts alone never pass a gate.

| Increment | Required tasks | Candidate paths | Production paths | Independent checkpoint |
| --- | --- | ---: | ---: | --- |
| A1 | T003–T004 | 24 | 3 | release-note only |
| A2 | T005 | 16 | 1 | packet-only untracked guard |
| A3 | T006–T008 | 21 | 2 | current verdict and PRD/roadmap scope |
| B1 | T009–T010 | 22 | 2 | marker counter and spec-index freshness |
| B2 | T011–T014 | 22 | 2 | exact named entry and slice rows |
| B3 | T015–T017 | 17 | 2 | refactor estimate and declared commands |
| C1a1 | T018 | 20 | 1 | 13 Post rows and legacy resume |
| C1a2 | T019 | 15 | 1 | persisted Post completion boundary |
| C1b | T020–T021 | 23 | 4 | executor team teardown |
| C2a | T022–T025 | 18 | 0 | review feedback, blind spot, status request |
| C2b | T026–T030 | 23 | 0 | scaffold/phase requests and workflow links |

## Phase 1: Setup (shared evidence)

**Goal**: Establish exact reviewable ownership before any code change. **Independent test**: each of the eleven proposed increments has a distinct source/generated/test/refactor candidate ledger, including repeated shared paths, with production classification and explicitly unmeasured actual LOC/diff.

- [ ] T001 Inventory every planned authored, fixture, shared input, `dist`, reference, and index path per slice and distinct required-refactor files; record operation, owner, production classification, and counts in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` (FR-026; do not infer generated fan-out or count repeat touches as distinct).

## Phase 2: Foundational budget gate

**Goal**: Keep the two-hour delivery reviewable. **Independent test**: eleven complete named candidate sets fit four production and 24 total paths; actual LOC/diffs and the repeated-path marker contract remain explicit stops before PR emission.

- [ ] T002 Reconcile the complete eleven-increment candidate inventory, Plan's `not_estimated` result, historical five-PR revision of Q11, current `one-navigable-PR` advisory, repeated shared paths, conservative reference candidates, and the present invalid marker contract in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; stop marker persistence/emission until the product contract is repaired and actual per-increment gates pass (FR-026).

## Phase 3: User Story 1 — final release note (P1, Increment A1)

**Goal**: A final packet accepts one valid optional note. **Independent test**: the emitted body passes the feature-PR release-note policy; invalid note and draft cases fail or omit as specified (FR-001–003, FR-026).

- [ ] T003 [US1] Add failing fixture for valid, blank, non-string, fence-breaking, absent, and draft `release_note` in `tests/speckit-pro/unit/test-pr-packet-repair.py` and `tests/speckit-pro/unit/fixtures/pr-packet-repair/final-note.json`; record RED for FR-001, FR-002, FR-003 before changing packet code.
- [ ] T004 [US1] Implement only the optional final note/schema/body/structure contract and paired host instructions in `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`, `speckit-pro/skills/speckit-autopilot/SKILL.md`, and `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`; run the T003 fixture GREEN and release-note validator, then register the new test, refresh A1's exact generated outputs, run targeted and quick suites, and record A1's RED/GREEN, host parity, path/production/LOC gate and marker checkpoint before T005 (FR-001, FR-002, FR-003, FR-026).

## Phase 4: User Story 2 — packet-only untracked files (P1, Increment A2)

**Goal**: The current packet's three untracked files do not block its own mutation. **Independent test**: validate and refresh pass for only canonical packet files; second packet, unrelated file, tracked edit, and unreadable status block (FR-004–005, FR-026).

- [ ] T005 [US2] First add failing fixture and record RED for both mutation helpers and every negative case, then implement the scoped guard in `tests/speckit-pro/unit/test-pr-packet-repair.py`, `tests/speckit-pro/unit/fixtures/pr-packet-repair/packet-only-untracked.json`, `speckit-pro/speckit_pro_runner/helpers/mutation.py`, `speckit-pro/skills/speckit-autopilot/references/post-implementation.md`, and `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md`; record GREEN without force-add or ignore-rule changes; refresh A2's exact generated/trust outputs, run targeted and quick suites, and record A2's path/production/LOC and marker checkpoint before T006 (FR-004, FR-005, FR-026).

## Phase 5: User Story 3 — current confidence verdict (P1, Increment A3)

**Goal**: Final body reflects current G6.5 Verdict. **Independent test**: first emission and refresh show current protected verdict; missing/invalid verdict blocks, with no overview fallback (FR-006, FR-026).

- [ ] T006 [US3] First add failing first-emission, stale-body refresh, and missing-verdict fixtures and record RED; then repair rendering/validation and paired host packet guidance in `tests/speckit-pro/unit/test-pr-packet-repair.py`, `tests/speckit-pro/unit/fixtures/pr-packet-repair/current-verdict.json`, `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `speckit-pro/skills/speckit-autopilot/SKILL.md`, and `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`; record GREEN; use the compact fixture child `tests/speckit-pro/unit/fixtures/pr-packet-repair/current-verdict.json` and retain A3's own diff/LOC checkpoint at T008 (FR-006, FR-026).

## Phase 6: A3 integration and validation

**Goal**: Preserve the packet contract and amend the approved PRD and roadmap scope. **Independent test**: A3 verdict fixture, quick suite, generated refresh, reference check, title and release-note checks pass; measured path/LOC budget fits.

- [ ] T007 Amend AC-16.2/16.5/16.8/16.10 and HRNS-015/HRNS-019 eleven-increment/deferred scope in `docs/prd-harness-engineering-uplift.md` and `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`; remove stale #642 status and verify against FR-027.
- [ ] T008 Verify the A1-registered packet test in `tests/speckit-pro/suite-manifest.json`, regenerate A3 `dist` and reference outputs, run A3 fixtures and the quick suite, measure all authored/generated changed paths and LOC, and record red/green, host parity, and budget evidence in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; stop before publication if A3 exceeds limits (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-026, FR-027).

## Phase 7: User Story 4 — visible marker counts (P1, Increment B1)

**Goal**: G1–G4 and count-markers agree on visible Gap and clarification markers. **Independent test**: exact comma-token tags, two per line, visible prose, and inline/fenced/indented code have expected counts and details (FR-007–008, FR-026).

- [ ] T009 [US4] First add failing marker fixtures including compound tags, two tags on one line, quotation/code visibility, and clarification detail; record RED, then repair the shared counter and both host gate instructions in `tests/speckit-pro/unit/test-marker-visibility.py`, `tests/speckit-pro/unit/fixtures/marker-visibility/cases.json`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `speckit-pro/skills/speckit-autopilot/references/gate-validation.md`; verify the shared guidance in both generated host payloads; record GREEN (FR-007, FR-008, FR-026).

## Phase 8: User Story 5 — tracked spec index (P1, Increment B1)

**Goal**: Required artifact consistency detects stale tracked spec indexes. **Independent test**: stale check fails, refresh repairs, untracked nested candidate stays absent, staged addition stays eligible (FR-009–010).

- [ ] T010 [US5] First freeze the historical stale-index text under `tests/speckit-pro/unit/fixtures/spec-index-freshness/historical-stale-index.md` and add failing RED cases in `tests/speckit-pro/unit/test-spec-index-freshness.py`; then repair source-index membership and the named refresh/check step in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `scripts/refresh-release-artifacts.py`, regenerate `specs/formal-001-selective-formal-methods/SPEC-MOC.md`, update `AGENTS.md`, and record GREEN with untracked/staged cases; register the B1 tests, refresh generated/trust/index/reference outputs, run targeted and quick suites, and record B1's RED/GREEN, host parity, path/production/LOC gate and marker checkpoint before T011 (FR-009, FR-010).

## Phase 9: User Story 6 — named reviewability entry (P1, Increment B2)

**Goal**: Issue #637's exact selected entry controls budget, exception, and split results. **Independent test**: original `multi`, `pragma`, `nobudget` reproductions and added selected-section, greenfield, primary-surface, aggregate, and malformed-slice cases pass (FR-011–014, FR-028–029).

- [ ] T011 [US6] Add failing-first issue #637 `multi`, `pragma`, `nobudget`, missing `spec_id`, and neighboring-entry fixtures in `tests/speckit-pro/unit/test-reviewability-scope.py` and `tests/speckit-pro/unit/fixtures/reviewability-scope/cases.json`; record RED before any gate fix (FR-011, FR-012, FR-013).
- [ ] T012 [US6] Require the required spec identifier input, isolate the exact authored `### <spec_id>:` section and its primary surfaces, fail closed on missing fields, and accept only selected typed refactor, infra, or upgrade exceptions in `speckit-pro/speckit_pro_runner/helpers/registry.py`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `tests/speckit-pro/unit/test-reviewability-scope.py`, and `tests/speckit-pro/unit/fixtures/reviewability-scope/cases.json`; record T011 GREEN (FR-011, FR-012, FR-013).
- [ ] T013 [US6] Add failing-first complete/incomplete/duplicate/extra/non-numeric/at-block slice rows and greenfield LOC-only fixtures in `tests/speckit-pro/unit/test-reviewability-scope.py` and `tests/speckit-pro/unit/fixtures/reviewability-scope/cases.json`; record RED for top-level sums, ordered `slice_results`, and blocked rows (FR-014, FR-028, FR-029).
- [ ] T014 [US6] Implement exact ordered slice budget evaluation and aggregate fields in `speckit-pro/speckit_pro_runner/helpers/read_only.py`; update paired host guidance and placeholders in `speckit-pro/skills/speckit-autopilot/references/gate-validation.md`, `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md`, and `tests/speckit-pro/unit/test-reviewability-scope.py`; record T013 GREEN without a new exception class or literal accepted pragma example; register the B2 test, refresh generated/trust/reference outputs, run targeted and quick suites, and record B2's RED/GREEN, host parity, path/production/LOC gate and marker checkpoint before T015 (FR-014, FR-026, FR-028, FR-029).

## Phase 10: User Story 7 — refactor-aware estimate (P2, Increment B3)

**Goal**: Required distinct refactor files change estimate and slice count. **Independent test**: refactor signal adds 40 LOC per distinct extra file after baseline/modify logic, missing or invalid signal leaves baseline, spike precedence holds (FR-015).

- [ ] T015 [US7] First add failing RED estimate cases, then add only the required-refactor signal to `tests/speckit-pro/unit/test-size-estimate-refactors.py` and `speckit-pro/speckit_pro_runner/helpers/read_only.py`; record GREEN and reconcile distinct refactor files against the T001 inventory (FR-015).

## Phase 11: User Story 8 — declared quality commands (P1, Increment B3)

**Goal**: The four approved quality slots accept explicit commands with provenance. **Independent test**: declared precedence, undeclared detection, malformed/unknown command G0 failure, and unchanged thresholds/basis (FR-016, FR-026).

- [ ] T016 [US8] First add failing RED command cases, then implement four-slot validation/precedence and additive `command_sources` plus gate source in `tests/speckit-pro/unit/test-declared-quality-commands.py`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `.specify/quality-gates.json`, and paired host guidance in `speckit-pro/skills/speckit-autopilot/references/gate-validation.md`; record GREEN without parsing agent-document tables (FR-016, FR-026).

## Phase 12: B3 integration and validation

**Goal**: Budgeted gates/counters pass with tracked index regeneration. **Independent test**: B3 fixtures, quick suite, generated refresh/reference check and actual path/LOC gate pass.

- [ ] T017 Recalculate the **distinct** required-refactor estimate using the repaired helper, register the two new B3 tests in `tests/speckit-pro/suite-manifest.json`, regenerate B3 `dist`, reference and runner-trust outputs, run B3 fixtures and quick suite, and record measured file/LOC/host-parity evidence in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; stop on any over-limit or incomplete B3 inventory (FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-026, FR-028, FR-029).

## Phase 13: User Story 9 — 13 canonical Post rows (P1, Increment C1a1)

**Goal**: Claude, Codex, and workflow template show the same 13 names. **Independent test**: exact once/order/count match and legacy 11-row resume preserves only unique exact-name statuses (FR-017–018, FR-026).

- [ ] T018 [US9] First add failing RED 11-versus-13 and legacy resume fixtures, then align the canonical guard, both host skill/list guidance, and workflow template in `tests/speckit-pro/unit/test-post-completion.py`, `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`, `speckit-pro/skills/speckit-autopilot/SKILL.md`, `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`, `speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md`, `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md`, and `speckit-pro/skills/speckit-coach/templates/workflow-template.md`; record GREEN; register the C1a1 test, refresh exact generated/reference outputs, run targeted and quick suites, and record C1a1's RED/GREEN, host parity, path/production/LOC gate and marker checkpoint before T019 (FR-017, FR-018, FR-026).

## Phase 14: User Story 10 — complete Post and teams (P1, C1a2 then C1b)

**Goal**: Full completion has a verified Post state and no active executor team. **Independent test**: both persisted records reject missing/duplicate/pending/in-progress/mismatch/unjustified skips; only validated extension absence permits identical skip, and each team-capable executor proves cleanup (FR-018–019, FR-026).

- [ ] T019 [US10, C1a2] First add failing RED completion-boundary cases for both records, `✅ Complete` mapping, legacy 11 rows, out-of-stage skip reactivation, and the sole registry-plus-directory-validated `skipped: <extension> not installed` case; then repair the guard and both host completion call sites in `tests/speckit-pro/unit/test-post-completion.py`, `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`, `speckit-pro/skills/speckit-autopilot/SKILL.md` and `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`, and both post-implementation references. Keep staged-run return distinct. Before T020, refresh C1a2's exact dist/reference outputs (its test was registered in C1a1), run targeted and quick suites, and record RED/GREEN, host parity, actual path/production/LOC gate, and marker checkpoint evidence; stop on any new path or failed gate (FR-017, FR-018, FR-026).
- [ ] T020 [US10, C1b] First add failing RED structural/result cases for all eight executor definitions, then require child result or supported stop, graceful shutdown, no-active-child and completed-cleanup evidence in `tests/speckit-pro/layer1-structural/test-team-teardown.py`, `speckit-pro/agents`, `speckit-pro/codex-agents`, and the shared `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md`; review the formal lifecycle Post subset read-only and stop for re-inventory before any edit; record GREEN and unresolved confirmations (FR-019, FR-026).

## Phase 15: C1b integration and validation

**Goal**: Confirm executor teardown after C1a1 and C1a2 have passed their marker checkpoints. **Independent test**: the eight-definition structural fixture, quick suite, generated refresh/reference check, and measured 23-candidate-path/production/LOC gate pass.

- [ ] T021 Register the C1b structural test in `tests/speckit-pro/suite-manifest.json`, regenerate its exact `dist` outputs and conservative generated agent and test reference pages, run C1b fixtures and quick suite, and record actual distinct paths/LOC, host parity, and marker checkpoint evidence in the PR packet; stop before C1b emission if any new path or measured limit fails (FR-019, FR-026).

## Phase 16: User Story 11 — complete review feedback after push (P1, Increment C2a)

**Goal**: Resolve-pr exhausts pages and acts only on a verified matching remote head. **Independent test**: >100 threads/comments, failed page/cursor, failed verify/push/head match, and serial confirmed resolution cases (FR-020–021, FR-026).

- [ ] T022 [US11] First add failing RED multi-page thread/comment and failed-page/cursor fixtures, then specify complete GraphQL cursor traversal on both hosts in `tests/speckit-pro/unit/test-resolve-pr-protocol.py`, `speckit-pro/skills/speckit-resolve-pr/SKILL.md`, and `speckit-pro/codex-skills/speckit-resolve-pr/SKILL.md`; record GREEN (FR-020, FR-026).
- [ ] T023 [US11] First add failing RED verification, push, fresh `headRefOid`, retry, serial reply/resolve, and resolved-readback fixtures, then enforce the publication order in `tests/speckit-pro/unit/test-resolve-pr-protocol.py`, `speckit-pro/skills/speckit-resolve-pr/SKILL.md`, and `speckit-pro/codex-skills/speckit-resolve-pr/SKILL.md`; record GREEN and retained local-commit evidence on failure (FR-021, FR-026).

## Phase 17: User Story 12 — wait for blind-spot result (P1, Increment C2a)

**Goal**: A late nonempty analyst result is used. **Independent test**: >5-minute result is `ran`; dispatch error, empty return, and explicit operator abandonment record distinct matching header/status reasons (FR-022–023, FR-026).

- [ ] T024 [US12] First add failing RED late-result and three no-findings cases, then remove fixed wait and persist the Design Concept `Blind-spot pass` reason on both hosts in `tests/speckit-pro/unit/test-scaffold-blindspot.py`, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, and `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`; record GREEN without inferring abandonment from elapsed time (FR-022, FR-023, FR-026).

## Phase 18: User Story 13 — complete named helper requests (P2, C2a then C2b)

**Goal**: Five named failure sites carry accepted full envelopes on both hosts. **Independent test**: status index/topology, scaffold reviewability/placement, and phase index-write examples all pass registry validation (FR-024, FR-026).

- [ ] T025 [US13] First add failing RED status index/topology envelope fixtures, then repair both host examples in `tests/speckit-pro/unit/test-status-envelope-contract.py`, `speckit-pro/skills/speckit-status/SKILL.md`, and `speckit-pro/codex-skills/speckit-status/SKILL.md`; record GREEN; register C2a's three new tests, refresh exact generated/reference outputs, run targeted and quick suites, and record C2a's RED/GREEN, host parity, path/production/LOC gate and marker checkpoint before T026 (FR-024, FR-026).
- [ ] T026 [US13] First add failing RED scaffold reviewability/placement envelope fixtures, then repair both host examples in `tests/speckit-pro/unit/test-scaffold-envelope-contract.py`, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, and `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`; record GREEN and retain C2b checkpoint at T030 (FR-024, FR-026).
- [ ] T027 [P] [US13] First add failing RED phase index-write envelope fixture, then repair both host examples in `tests/speckit-pro/unit/test-phase-envelope-contract.py`, `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`, and `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`; record GREEN and retain C2b checkpoint at T030 (FR-024, FR-026).

## Phase 19: User Story 14 — real workflow links (P2, Increment C2b)

**Goal**: Issue #638's generated link reaches scaffold output while valid legacy links survive. **Independent test**: new template, verified legacy target, and broken legacy target cases all resolve to real workflow files (FR-025–026).

- [ ] T028 [US14] Add failing-first issue #638 generated-template, verified-existing-legacy, and broken-legacy fixtures in `tests/speckit-pro/unit/test-roadmap-workflow-links.py` and `tests/speckit-pro/unit/fixtures/roadmap-workflow-links/cases.json`; record RED before changing template or scaffold (FR-025).
- [ ] T029 [US14] Correct new links and broken-legacy repair while preserving verified existing targets in `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md`, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`, `speckit-pro/README.md`, and `tests/speckit-pro/unit/test-roadmap-workflow-links.py`; record T028 GREEN on both hosts (FR-025, FR-026).

## Phase 20: C2b integration and validation

**Goal**: Complete C2 with both host instructions and no HRNS-019 expansion. **Independent test**: C2b fixtures, quick suite, generated refresh/reference check and actual path/LOC gate pass.

- [ ] T030 Register the three new C2b tests in `tests/speckit-pro/suite-manifest.json`, regenerate `dist` and `docs-site/src/content/docs/reference`, run C2b fixtures and quick suite, measure authored/generated paths and LOC, and record host parity in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; stop on an incomplete or over-limit C2b inventory (FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027).

## Phase 21: Polish and cross-cutting validation

**Goal**: Prove the exact eleven planned increments before release. **Independent test**: full CI suite, artifact consistency, docs quality, lint, PR title/release-note fences, and requirement-to-file/red-green traceability pass with recorded commands and outcomes.

- [ ] T031 Run final acceptance, full CI, artifact, docs, lint, exact title/release-note, and per-slice budget gates; record every FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028, FR-029/SC-001–011 fixture and result plus non-goals/deferred HRNS-019/017 in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; any unavailable or failed check remains explicit (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028, FR-029).

## Dependencies and execution order

- T001 → T002 blocks every story. A1 runs US1 → checkpoint T004; A2 runs US2 → checkpoint T005; A3 runs US3 → T007/T008; B1 runs US4/5 → checkpoint T010; B2 runs US6 → checkpoint T014; B3 runs US7/8 → T017; C1a1 runs US9 → checkpoint T018; C1a2 runs US10 Post boundary → checkpoint T019; C1b runs teardown → T021; C2a runs US11/12/status → checkpoint T025; C2b runs remaining envelopes/links → T030; T031 follows all eleven gates.
- In each two-checkbox TDD unit (T003–004, T011–012, T013–014, T028–029), the fixture must fail before its paired fix and the pair stays in one adjacent batch. Every single-checkbox behavior task explicitly runs RED → repair → GREEN within the same task. Batches contain at most four tasks.
- T025 checkpoints C2a before T026/T027 begin C2b; T026 and T027 may run in parallel only after T025 because they edit disjoint scaffold and phase files. All repeated helper, trust, manifest, and host paths are owned sequentially across increments. A parallel unit never owns a path another active unit owns.
- The old A/B/C2 breaches and C1a `tests.md` omission are addressed by eleven named candidate sets, with no lost FR. The current marker validator still blocks repeated shared paths; no marker is valid until repaired. Each marker also stops on an actual over-cap diff, unmeasured or failed LOC gate, stale fingerprints, or unsafe fold. Generated paths and FR-018/019 remain in scope.

## Implementation strategy

Start with US1 as the MVP because HRNS-016 depends on packet emission. At each increment, preserve RED evidence, make the smallest repair, prove GREEN, run the quick suite, regenerate dist/reference artifacts, and measure the exact final diff. The broad CI and policy checks belong to T031. Stop optional expansion if the two-hour whole-spec budget cannot include repairs and final checks; report unfinished required tasks instead of checking them off.
