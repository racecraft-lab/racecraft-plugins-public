# Tasks: Autopilot, Gate, and PR-Emission Repair

**Input**: HRNS-015 spec, plan, research, data model, contracts, quickstart, workflow Tasks Prompt, and ratified design concept. **Execution limit**: the entire automated implementation, startup, repair, and final checks has a two-hour budget. Every behavior task begins with a failing fixture and records RED before its minimal fix and GREEN. No task may be checked off from prose alone. Both hosts ship together for every host-facing behavior. Tests live under `tests/speckit-pro/` and freeze any needed historical prose in their own fixtures; tests never open a temporary feature spec path at run time.

**Reviewability status**: **unqualified**. The Plan-phase refactor-inclusive result is `not_estimated`; its 1,442 LOC and file counts are provisional. T001 records complete *distinct* authored and generated path operations and distinct required-refactor files for each slice. T002 enforces the budget before any implementation; T017 reruns the updated refactor-aware estimator. Each slice must have no more than four production files, fewer than 25 total changed paths including generated outputs, and a passing actual LOC gate. A task that would exceed any bound stops for split or rescope before its fix. Q11's A → B → C1 → C2 decision remains the design baseline; the C1 conflict below is a blocking Analyze/G6.5 decision, not an approved extra PR or exception.

## Confirmed C1 file-budget conflict

The *minimum* C1 source set in the Plan contains 12 distinct authored paths: the Post guard, Claude and Codex autopilot `SKILL.md`, the workflow template, and four Claude plus four Codex executor definitions. Existing dist packaging gives those paths 14 distinct generated counterparts: two guard copies, two autopilot SKILL copies, two workflow-template copies, and eight executor copies. **12 + 14 = 26 paths before tests**. The planned new Post and teardown test modules plus required suite-manifest registration make the confirmed planned lower bound **at least 29**, five above the maximum of 24. This excludes task-list, Post guidance, phase/gate references, lifecycle review, reference pages, and additional fixtures. T021 cannot claim a passing C1 budget. A reviewable alternative for Analyze/G6.5 is to separate C1 Post completion from executor teardown into C1a/C1b PRs, then remeasure each; that changes Q11's four-PR decision and requires explicit ratification before implementation. A policy exception or omitted generated paths is not assumed.

| Slice | Known production candidates | Budget evidence before implementation |
| --- | --- | --- |
| A | `pr_emission.py`, `read_only.py`, `mutation.py`, packet schema | Four candidates; generated/test/document paths still require T001 inventory. |
| B | `read_only.py`, `registry.py`, `refresh-release-artifacts.py`, quality-gates config | Four candidates; exact distinct refactor and generated/index paths still require T001 inventory. |
| C1 | Post guard; optional formal lifecycle module only if the 13-row contract requires it | 26-path minimum already breaches total-file limit; T001 must enumerate all paths. |
| C2 | No Python/schema/config change planned | Host, template, fixture, generated, and reference path inventory still required. |

## Phase 1: Setup (shared evidence)

**Goal**: Establish exact reviewable ownership before any code change. **Independent test**: each of A, B, C1, C2 has a distinct, source/generated/test/refactor path ledger with production classification and a measured or explicitly unmeasured result.

- [ ] T001 Inventory every planned authored, fixture, shared input, `dist`, reference, and index path per slice and distinct required-refactor files; record operation, owner, production classification, and counts in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` (FR-026; do not infer generated fan-out or count repeat touches as distinct).

## Phase 2: Foundational budget gate

**Goal**: Keep a two-hour, four-slice delivery reviewable. **Independent test**: no behavior task starts while any slice lacks a complete distinct inventory, exceeds four production files or 24 total files, or has an unqualified refactor-inclusive estimate; C1's confirmed conflict is surfaced for Analyze/G6.5 rather than marked pass.

- [ ] T002 Reconcile the inventory, the Plan's `not_estimated` result, slice LOC warn/block lines, and the four-PR decision in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; stop the affected slice on an incomplete or over-limit inventory and propose the smallest reviewable rescope for ratification (FR-026).

## Phase 3: User Story 1 — final release note (P1, Slice A)

**Goal**: A final packet accepts one valid optional note. **Independent test**: the emitted body passes the feature-PR release-note policy; invalid note and draft cases fail or omit as specified (FR-001–003, FR-026).

- [ ] T003 [US1] Add failing fixture for valid, blank, non-string, fence-breaking, absent, and draft `release_note` in `tests/speckit-pro/unit/test-pr-packet-repair.py` and `tests/speckit-pro/unit/fixtures/pr-packet-repair`; record RED for FR-001, FR-002, FR-003 before changing packet code.
- [ ] T004 [US1] Implement only the optional final note/schema/body/structure contract and paired host instructions in `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`, `speckit-pro/skills/speckit-autopilot/SKILL.md`, and `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`; run the T003 fixture GREEN and the release-note validator (FR-001, FR-002, FR-003, FR-026).

## Phase 4: User Story 2 — packet-only untracked files (P1, Slice A)

**Goal**: The current packet's three untracked files do not block its own mutation. **Independent test**: validate and refresh pass for only canonical packet files; second packet, unrelated file, tracked edit, and unreadable status block (FR-004–005, FR-026).

- [ ] T005 [US2] First add failing fixture and record RED for both mutation helpers and every negative case, then implement the scoped guard in `tests/speckit-pro/unit/test-pr-packet-repair.py`, `tests/speckit-pro/unit/fixtures/pr-packet-repair`, `speckit-pro/speckit_pro_runner/helpers/mutation.py`, `speckit-pro/skills/speckit-autopilot/references/post-implementation.md`, and `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md`; record GREEN without force-add or ignore-rule changes (FR-004, FR-005, FR-026).

## Phase 5: User Story 3 — current confidence verdict (P1, Slice A)

**Goal**: Final body reflects current G6.5 Verdict. **Independent test**: first emission and refresh show current protected verdict; missing/invalid verdict blocks, with no overview fallback (FR-006, FR-026).

- [ ] T006 [US3] First add failing first-emission, stale-body refresh, and missing-verdict fixtures and record RED; then repair rendering/validation and paired host packet guidance in `tests/speckit-pro/unit/test-pr-packet-repair.py`, `tests/speckit-pro/unit/fixtures/pr-packet-repair`, `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `speckit-pro/skills/speckit-autopilot/SKILL.md`, and `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`; record GREEN (FR-006, FR-026).

## Phase 6: Slice A integration and validation

**Goal**: Preserve the packet contract and amend the approved PRD and roadmap scope. **Independent test**: A fixtures, quick suite, generated refresh, reference check, title and release-note checks pass; measured path/LOC budget fits.

- [ ] T007 Amend AC-16.2/16.5/16.8/16.10 and HRNS-015/HRNS-019 four-slice/deferred scope in `docs/prd-harness-engineering-uplift.md` and `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`; remove stale #642 status and verify against FR-027.
- [ ] T008 Register the new A tests in `tests/speckit-pro/suite-manifest.json`, regenerate `dist` and `docs-site/src/content/docs/reference`, run A fixtures and the quick suite, measure all authored/generated changed paths and LOC, and record red/green, host parity, and budget evidence in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; stop before publication if A exceeds limits (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-026, FR-027).

## Phase 7: User Story 4 — visible marker counts (P1, Slice B)

**Goal**: G1–G4 and count-markers agree on visible Gap and clarification markers. **Independent test**: exact comma-token tags, two per line, visible prose, and inline/fenced/indented code have expected counts and details (FR-007–008, FR-026).

- [ ] T009 [US4] First add failing marker fixtures including compound tags, two tags on one line, quotation/code visibility, and clarification detail; record RED, then repair the shared counter and both host gate instructions in `tests/speckit-pro/unit/test-marker-visibility.py`, `tests/speckit-pro/unit/fixtures/marker-visibility`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `speckit-pro/skills/speckit-autopilot/references/gate-validation.md`; verify the shared guidance in both generated host payloads; record GREEN (FR-007, FR-008, FR-026).

## Phase 8: User Story 5 — tracked spec index (P1, Slice B)

**Goal**: Required artifact consistency detects stale tracked spec indexes. **Independent test**: stale check fails, refresh repairs, untracked nested candidate stays absent, staged addition stays eligible (FR-009–010).

- [ ] T010 [US5] First freeze the historical stale-index text under `tests/speckit-pro/unit/fixtures/spec-index-freshness` and add failing RED cases in `tests/speckit-pro/unit/test-spec-index-freshness.py`; then repair source-index membership and the named refresh/check step in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `scripts/refresh-release-artifacts.py`, regenerate `specs/formal-001-selective-formal-methods/SPEC-MOC.md`, update `AGENTS.md`, and record GREEN with untracked/staged cases (FR-009, FR-010).

## Phase 9: User Story 6 — named reviewability entry (P1, Slice B)

**Goal**: Issue #637's exact selected entry controls budget, exception, and split results. **Independent test**: original `multi`, `pragma`, `nobudget` reproductions and added selected-section, greenfield, primary-surface, aggregate, and malformed-slice cases pass (FR-011–014, FR-028–029).

- [ ] T011 [US6] Add failing-first issue #637 `multi`, `pragma`, `nobudget`, missing `spec_id`, and neighboring-entry fixtures in `tests/speckit-pro/unit/test-reviewability-scope.py` and `tests/speckit-pro/unit/fixtures/reviewability-scope`; record RED before any gate fix (FR-011, FR-012, FR-013).
- [ ] T012 [US6] Require the required spec identifier input, isolate the exact authored `### <spec_id>:` section and its primary surfaces, fail closed on missing fields, and accept only selected typed refactor, infra, or upgrade exceptions in `speckit-pro/speckit_pro_runner/helpers/registry.py`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `tests/speckit-pro/unit/test-reviewability-scope.py`, and `tests/speckit-pro/unit/fixtures/reviewability-scope`; record T011 GREEN (FR-011, FR-012, FR-013).
- [ ] T013 [US6] Add failing-first complete/incomplete/duplicate/extra/non-numeric/at-block slice rows and greenfield LOC-only fixtures in `tests/speckit-pro/unit/test-reviewability-scope.py` and `tests/speckit-pro/unit/fixtures/reviewability-scope`; record RED for top-level sums, ordered `slice_results`, and blocked rows (FR-014, FR-028, FR-029).
- [ ] T014 [US6] Implement exact ordered slice budget evaluation and aggregate fields in `speckit-pro/speckit_pro_runner/helpers/read_only.py`; update paired host guidance and placeholders in `speckit-pro/skills/speckit-autopilot/references/gate-validation.md`, `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md`, and `tests/speckit-pro/unit/test-reviewability-scope.py`; record T013 GREEN without a new exception class or literal accepted pragma example (FR-014, FR-026, FR-028, FR-029).

## Phase 10: User Story 7 — refactor-aware estimate (P2, Slice B)

**Goal**: Required distinct refactor files change estimate and slice count. **Independent test**: refactor signal adds 40 LOC per distinct extra file after baseline/modify logic, missing or invalid signal leaves baseline, spike precedence holds (FR-015).

- [ ] T015 [US7] First add failing RED estimate cases, then add only the required-refactor signal to `tests/speckit-pro/unit/test-size-estimate-refactors.py` and `speckit-pro/speckit_pro_runner/helpers/read_only.py`; record GREEN and reconcile distinct refactor files against the T001 inventory (FR-015).

## Phase 11: User Story 8 — declared quality commands (P1, Slice B)

**Goal**: The four approved quality slots accept explicit commands with provenance. **Independent test**: declared precedence, undeclared detection, malformed/unknown command G0 failure, and unchanged thresholds/basis (FR-016, FR-026).

- [ ] T016 [US8] First add failing RED command cases, then implement four-slot validation/precedence and additive `command_sources` plus gate source in `tests/speckit-pro/unit/test-declared-quality-commands.py`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `.specify/quality-gates.json`, and paired host guidance in `speckit-pro/skills/speckit-autopilot/references/gate-validation.md`; record GREEN without parsing agent-document tables (FR-016, FR-026).

## Phase 12: Slice B integration and validation

**Goal**: Budgeted gates/counters pass with tracked index regeneration. **Independent test**: B fixtures, quick suite, generated refresh/reference check and actual path/LOC gate pass.

- [ ] T017 Recalculate the **distinct** required-refactor estimate using the repaired helper, register the new B tests in `tests/speckit-pro/suite-manifest.json`, regenerate `dist`, `docs-site/src/content/docs/reference`, and the tracked index, run B fixtures and quick suite, and record measured file/LOC/host-parity evidence in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; stop on any over-limit or incomplete B inventory (FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-026, FR-028, FR-029).

## Phase 13: User Story 9 — 13 canonical Post rows (P1, Slice C1)

**Goal**: Claude, Codex, and workflow template show the same 13 names. **Independent test**: exact once/order/count match and legacy 11-row resume preserves only unique exact-name statuses (FR-017–018, FR-026).

- [ ] T018 [US9] First add failing RED 11-versus-13 and legacy resume fixtures, then align the canonical guard, both host skill/list guidance, and workflow template in `tests/speckit-pro/unit/test-post-completion.py`, `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`, `speckit-pro/skills/speckit-autopilot/SKILL.md`, `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`, `speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md`, `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md`, and `speckit-pro/skills/speckit-coach/templates/workflow-template.md`; record GREEN (FR-017, FR-018, FR-026).

## Phase 14: User Story 10 — complete Post and teams (P1, Slice C1)

**Goal**: Full completion has a verified Post state and no active executor team. **Independent test**: both persisted records reject missing/duplicate/pending/in-progress/mismatch/unjustified skips; only validated extension absence permits identical skip, and each team-capable executor proves cleanup (FR-018–019, FR-026).

- [ ] T019 [US10] First add failing RED completion-boundary fixtures for both records, `✅ Complete` mapping, legacy 11 rows, out-of-stage skip reactivation, and the sole registry-plus-directory-validated `skipped: <extension> not installed` case; then repair the guard and both host completion call sites in `tests/speckit-pro/unit/test-post-completion.py`, `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`, `speckit-pro/skills/speckit-autopilot/SKILL.md`, and `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`; record GREEN and keep staged-run return distinct (FR-018, FR-026).
- [ ] T020 [US10] First add failing RED structural/result fixtures for all eight executor definitions, then require child result or supported stop, graceful shutdown, no-active-child and completed-cleanup evidence in `tests/speckit-pro/layer1-structural/test-team-teardown.py`, `speckit-pro/agents`, and `speckit-pro/codex-agents`; review `speckit-pro/speckit_pro_runner/formal/lifecycle.py` and edit it only if its Post subset fails; record GREEN and unresolved confirmations (FR-019, FR-026).

## Phase 15: Slice C1 integration and validation

**Goal**: Confirm C1 behavior and resolve its file-budget conflict before publication. **Independent test**: C1 fixtures, quick suite, generated refresh/reference check and complete path accounting; the confirmed 29-path planned floor cannot be marked pass under the current limit.

- [ ] T021 Register the new C1 tests in `tests/speckit-pro/suite-manifest.json`, regenerate `dist` and `docs-site/src/content/docs/reference`, run C1 fixtures and quick suite, and record actual distinct files/LOC and an Analyze/G6.5 rescope decision in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; do not publish C1 while it remains above 24 files (FR-017, FR-018, FR-019, FR-026).

## Phase 16: User Story 11 — complete review feedback after push (P1, Slice C2)

**Goal**: Resolve-pr exhausts pages and acts only on a verified matching remote head. **Independent test**: >100 threads/comments, failed page/cursor, failed verify/push/head match, and serial confirmed resolution cases (FR-020–021, FR-026).

- [ ] T022 [US11] First add failing RED multi-page thread/comment and failed-page/cursor fixtures, then specify complete GraphQL cursor traversal on both hosts in `tests/speckit-pro/unit/test-resolve-pr-protocol.py`, `speckit-pro/skills/speckit-resolve-pr/SKILL.md`, and `speckit-pro/codex-skills/speckit-resolve-pr/SKILL.md`; record GREEN (FR-020, FR-026).
- [ ] T023 [US11] First add failing RED verification, push, fresh `headRefOid`, retry, serial reply/resolve, and resolved-readback fixtures, then enforce the publication order in `tests/speckit-pro/unit/test-resolve-pr-protocol.py`, `speckit-pro/skills/speckit-resolve-pr/SKILL.md`, and `speckit-pro/codex-skills/speckit-resolve-pr/SKILL.md`; record GREEN and retained local-commit evidence on failure (FR-021, FR-026).

## Phase 17: User Story 12 — wait for blind-spot result (P1, Slice C2)

**Goal**: A late nonempty analyst result is used. **Independent test**: >5-minute result is `ran`; dispatch error, empty return, and explicit operator abandonment record distinct matching header/status reasons (FR-022–023, FR-026).

- [ ] T024 [US12] First add failing RED late-result and three no-findings cases, then remove fixed wait and persist the Design Concept `Blind-spot pass` reason on both hosts in `tests/speckit-pro/unit/test-scaffold-blindspot.py`, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, and `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`; record GREEN without inferring abandonment from elapsed time (FR-022, FR-023, FR-026).

## Phase 18: User Story 13 — complete named helper requests (P2, Slice C2)

**Goal**: Five named failure sites carry accepted full envelopes on both hosts. **Independent test**: status index/topology, scaffold reviewability/placement, and phase index-write examples all pass registry validation (FR-024, FR-026).

- [ ] T025 [P] [US13] First add failing RED status index/topology envelope fixtures, then repair both host examples in `tests/speckit-pro/unit/test-status-envelope-contract.py`, `speckit-pro/skills/speckit-status/SKILL.md`, and `speckit-pro/codex-skills/speckit-status/SKILL.md`; record GREEN (FR-024, FR-026).
- [ ] T026 [P] [US13] First add failing RED scaffold reviewability/placement envelope fixtures, then repair both host examples in `tests/speckit-pro/unit/test-scaffold-envelope-contract.py`, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, and `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`; record GREEN (FR-024, FR-026).
- [ ] T027 [P] [US13] First add failing RED phase index-write envelope fixture, then repair both host examples in `tests/speckit-pro/unit/test-phase-envelope-contract.py`, `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`, and `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`; record GREEN (FR-024, FR-026).

## Phase 19: User Story 14 — real workflow links (P2, Slice C2)

**Goal**: Issue #638's generated link reaches scaffold output while valid legacy links survive. **Independent test**: new template, verified legacy target, and broken legacy target cases all resolve to real workflow files (FR-025–026).

- [ ] T028 [US14] Add failing-first issue #638 generated-template, verified-existing-legacy, and broken-legacy fixtures in `tests/speckit-pro/unit/test-roadmap-workflow-links.py` and `tests/speckit-pro/unit/fixtures/roadmap-workflow-links`; record RED before changing template or scaffold (FR-025).
- [ ] T029 [US14] Correct new links and broken-legacy repair while preserving verified existing targets in `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md`, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`, `speckit-pro/README.md`, and `tests/speckit-pro/unit/test-roadmap-workflow-links.py`; record T028 GREEN on both hosts (FR-025, FR-026).

## Phase 20: Slice C2 integration and validation

**Goal**: Complete C2 with both host instructions and no HRNS-019 expansion. **Independent test**: C2 fixtures, quick suite, generated refresh/reference check and actual path/LOC gate pass.

- [ ] T030 Register the new C2 tests in `tests/speckit-pro/suite-manifest.json`, regenerate `dist` and `docs-site/src/content/docs/reference`, run C2 fixtures and quick suite, measure authored/generated paths and LOC, and record host parity in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; stop on an incomplete or over-limit C2 inventory (FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027).

## Phase 21: Polish and cross-cutting validation

**Goal**: Prove the exact four planned increments before release. **Independent test**: full CI suite, artifact consistency, docs quality, lint, PR title/release-note fences, and requirement-to-file/red-green traceability pass with recorded commands and outcomes.

- [ ] T031 Run final acceptance, full CI, artifact, docs, lint, exact title/release-note, and per-slice budget gates; record every FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028, FR-029/SC-001–011 fixture and result plus non-goals/deferred HRNS-019/017 in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; any unavailable or failed check remains explicit (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028, FR-029).

## Dependencies and execution order

- T001 → T002 blocks every story. Slice A runs US1 → US2 → US3 → T007/T008; Slice B runs US4 → US5 → US6 → US7 → US8 → T017; Slice C1 runs US9 → US10 → T021; Slice C2 runs US11 → US12 → US13 → US14 → T030; T031 follows all four slice gates.
- In each two-checkbox TDD unit (T003–004, T011–012, T013–014, T028–029), the fixture must fail before its paired fix and the pair stays in one adjacent batch. Every single-checkbox behavior task explicitly runs RED → repair → GREEN within the same task. Batches contain at most four tasks.
- T025, T026, and T027 are parallel-safe only after T024: they edit disjoint status, scaffold, and phase files with separate fixture files. All other shared helper/host paths are ordered to avoid concurrent edits. A parallel unit never owns a path another active unit owns.
- The planned C1 lower-bound breach is a hard stop. Analyze/G6.5 must determine a ratified rescope or PR split, with a fresh inventory and budget, before C1 implementation can be considered complete. Do not silently exclude generated paths or downgrade FR-018/019.

## Implementation strategy

Start with US1 as the MVP because HRNS-016 depends on packet emission. At each slice, preserve RED evidence, make the smallest repair, prove GREEN, run the quick suite, regenerate dist/reference artifacts, and measure the exact final diff. The broad CI and policy checks belong to T031. Stop optional expansion if the two-hour whole-spec budget cannot include repairs and final checks; report unfinished required tasks instead of checking them off.
