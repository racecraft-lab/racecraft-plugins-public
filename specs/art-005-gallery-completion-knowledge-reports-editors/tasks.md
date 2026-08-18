# Tasks: ART-005 - Gallery Completion - Knowledge, Reports & Editors

**Input**: Design artifacts in `specs/art-005-gallery-completion-knowledge-reports-editors/`

**Tests**: Strict RED -> GREEN -> REFACTOR/VERIFY is mandatory. A slice does not
start implementation until its focused tests fail for the intended missing
behavior, and it does not advance until focused, structural, full-suite,
generated-artifact, reviewability, and `file://` UAT checks pass.

**Delivery topology**: One specification and workflow; seven sequential stacked
review slices in manifest order. Shared manifest, test, generated, and UAT files
are serial ownership boundaries. No two slices execute in parallel.

**Reviewability stop rule**: Recalculate each slice before source work, after the
template/test changes, before generated refresh, and before PR creation. Stop the
affected slice if actual authored LOC plus declared remaining work would reach
800, or if final authored LOC reaches 800. Never split a template or infer an
exception from the seven-slice decision. Separately count the complete physical
diff: a total-file block may continue only when every excess path is a required
source-derived generated output or the single `tasks.md` control-plane path and
the result is recorded as size-only; any other blocker stops.

## Phase 1: Setup

**Purpose**: Re-establish the exact source, branch, and verification baseline
before any slice changes implementation files.

- [x] T001 Verify the active worktree is `.worktrees/art-005-gallery-completion-knowledge-reports-editors`, the branch is `art-005-gallery-completion-knowledge-reports-editors`, and `git status --short` contains no implementation drift before using `specs/art-005-gallery-completion-knowledge-reports-editors/plan.md` [FR-018, SC-008]
- [x] T002 [P] Recompute SHA-256 for all seven files under `/private/tmp/art-005-upstream-58c305be97f47b26b678f2c07dec01d4242268ec/` and compare every value with `specs/art-005-gallery-completion-knowledge-reports-editors/research.md` and `specs/art-005-gallery-completion-knowledge-reports-editors/spec.md`; if the scratch cache is absent, rehydrate the seven root files from the exact pinned upstream commit per `research.md` and stop on any digest mismatch [FR-002]
- [x] T003 [P] Re-run the pre-implementation baseline with `tests/speckit-pro/run-all.py` for Layer 1, Layer 4, and the default suite; stop and record any regression before changing `speckit-pro/artifact-gallery/manifest.json` [FR-003, SC-001]
- [x] T004 Verify the seven rows in `speckit-pro/artifact-gallery/manifest.json` still match the ID/source/role/export table in `specs/art-005-gallery-completion-knowledge-reports-editors/spec.md` and all remain `planned` before Slice 1 [FR-001, FR-004-FR-007]
- [x] T005 Verify `speckit-pro/artifact-gallery/theme-toggle.html`, `speckit-pro/artifact-gallery/brand-kit.css`, `speckit-pro/artifact-gallery/SPA-CONTRACT.md`, and `speckit-pro/artifact-gallery/UPSTREAM-NOTICE.md` are the unchanged canonical/runtime sources every slice must consume [FR-003, FR-019]

---

## Phase 2: Foundational Preconditions

**Purpose**: Lock the serial stack, generated-artifact route, evidence schema,
and reviewability measurement before the first user-story slice.

**Critical**: These are verification-only preconditions. Do not create later
branches, templates, UAT files, or shared test edits in this phase.

- [x] T006 Confirm the branch/predecessor table and one-template atomic boundary in `specs/art-005-gallery-completion-knowledge-reports-editors/contracts/slice-topology-contract.md`; do not create Slice 2-7 branches before their predecessor PR is open [FR-004, FR-018]
- [x] T007 Verify `scripts/refresh-release-artifacts.py`, `docs-site/package.json`, and `docs-site/pnpm-lock.yaml` are available; confirm docs dependencies are installed before any `docs-site/src/content/docs/reference/tests.md` regeneration [FR-003, FR-019]
- [x] T008 Verify the row schemas and required matrices in `specs/art-005-gallery-completion-knowledge-reports-editors/contracts/uat-evidence-contract.md` before Slice 1 creates `.process/uat-runbook.md`, `.process/uat-results.md`, and `.process/uat-results.json` [FR-015, FR-024, SC-007]
- [x] T009 Use `git diff --numstat <slice-base>...HEAD -- <declared-authored-paths>` for authored LOC and a separate unscoped `git diff --name-only <slice-base>...HEAD` ledger for every implementation-authored, `tasks.md` control-plane, and generated path; record both at every checkpoint in `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md` once it exists, and treat the runner's HTML-classification `0` as advisory per `plan.md` [FR-016-FR-018, SC-008]
- [x] T010 Re-run G4 marker validation against `specs/art-005-gallery-completion-knowledge-reports-editors/checklists/accessibility.md`, `ux.md`, `data-integrity.md`, and `error-handling.md`; stop if any `[Gap]` reappears before editing `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-014, FR-021-FR-024]

**Checkpoint**: Source identity, contracts, tests, stack topology, and the
reviewability stop path are ready. Slice 1 may begin.

---

## Phase 3: User Story 1 / Slice 1 - Slide Deck (Priority: P1)

**Goal**: Ship one accessible, representative, standalone `slide-deck` reader
on the current feature branch.

**Independent Test**: Open
`speckit-pro/artifact-gallery/templates/slide-deck.html` over `file://`, traverse
the named slide controls by keyboard, verify current-position/focus behavior and
representative fills, and confirm there is no export control.

- [x] T011 [US1] Confirm the Slice 1 declared seven authored paths and 670-LOC ceiling in `specs/art-005-gallery-completion-knowledge-reports-editors/plan.md`; stop before RED if recalculation would reach 800 [FR-016-FR-018, SC-008]
- [x] T012 [US1] RED: add `slide-deck` reader, canonical-block, attribution, no-export, named-navigation/current-position, hidden-slide, focus, reduced-motion, responsive, and ART-020 scroll-contract assertions to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-003, FR-005-FR-006, FR-013-FR-014, FR-022; US1]
- [x] T013 [US1] RED: add `FLOOR["slide-deck"] = ("deck-title", "slides", "speaker-notes")`, `LIST_SLOTS["slide-deck"] = ("slides",)`, and two-anchor expectations to `tests/speckit-pro/unit/test-artifact-fill-regions.py` [FR-020; US1]
- [x] T014 [US1] RED proof: run `tests/speckit-pro/unit/test-artifact-gallery.py` and `tests/speckit-pro/unit/test-artifact-fill-regions.py` and require failures caused by missing `speckit-pro/artifact-gallery/templates/slide-deck.html`, its planned manifest status, and missing fill inventory before any implementation change [FR-004, FR-020; US1]
- [x] T015 [US1] GREEN: create `speckit-pro/artifact-gallery/templates/slide-deck.html` from pinned `09-slide-deck.html` with byte-identical canonical blocks, attribution/inventory comments, required fills, Racecraft branding, named controls, `Slide X of Y`, deterministic focus, no autorotation, responsive/reduced-motion behavior, and no export path [FR-002-FR-006, FR-013-FR-014, FR-020-FR-022; US1]
- [x] T016 [US1] GREEN: change only `slide-deck.status` from `planned` to `shipped` in `speckit-pro/artifact-gallery/manifest.json`, retaining its source fields and `exports: []` [FR-004-FR-006; US1]
- [x] T017 [US1] GREEN proof: rerun both focused modules in `tests/speckit-pro/unit/` and require all new `slide-deck` assertions to pass before refactor [FR-003-FR-006, FR-014, FR-020; US1]
- [x] T018 [US1] REFACTOR: simplify only `speckit-pro/artifact-gallery/templates/slide-deck.html` while preserving functional fidelity, flat explicit logic, canonical bytes, all focused tests, and the 670-LOC ceiling [FR-003, FR-017, FR-019; US1]
- [x] T019 [US1] Create `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-runbook.md`, `.process/uat-results.md`, and `.process/uat-results.json` with the contract metadata/schema and Slice 1 rows, including evidence-backed producer-only `not_applicable` results [FR-015, FR-024, SC-007; US1]
- [x] T020 [US1] Measure the seven implementation-authored Slice 1 paths with an explicit `git diff --numstat` pathspec and record actual/remaining/final LOC against 670 in `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`; stop before generation if projected or final authored LOC reaches 800 [FR-016-FR-018, SC-008; US1]
- [x] T021 [US1] Regenerate source-derived payload, installed-cache, proof, XPLAT evidence, and `docs-site/src/content/docs/reference/tests.md` from `speckit-pro/artifact-gallery/templates/slide-deck.html` using `scripts/refresh-release-artifacts.py` and the docs `reference:generate` command; never hand-edit `dist/` or fixture mirrors [FR-003, FR-019; US1]
- [x] T022 [US1] After focused, Layer 1, Layer 4, full-suite, generated-check, and spec-index checks pass, commit a Slice 1 source checkpoint; execute the complete cumulative UAT row set at that commit against `speckit-pro/artifact-gallery/templates/slide-deck.html` over `file://` at 360 and at least 1280 CSS px, set the JSON top-level `sourceCommit` to the checkpoint, and record results in a later evidence commit [FR-015, FR-024, SC-001-SC-002, SC-005-SC-007, SC-010; US1]
- [x] T023 [US1] VERIFY and boundary: prove the Slice 1 source paths did not change after the UAT checkpoint; re-run focused, Layer 1, Layer 4, full suite, `scripts/refresh-release-artifacts.py --check`, and spec-index checks; record the complete Git-path ledger as seven implementation-authored paths plus any `tasks.md` control-plane and generated paths; stop on authored/non-size blockers or record a generated/control-plane-only total-file block as size-only; generate and validate the required PR packet, commit the evidence, push, and open PR 1 before creating Slice 2 [FR-004, FR-013-FR-019, FR-024, SC-001-SC-002, SC-007-SC-008; US1]

**Checkpoint**: `slide-deck` is independently reviewable and PR 1 is open.

---

## Phase 4: User Story 1 / Slice 2 - Concept Explainer (Priority: P1)

**Goal**: Add one accessible transient-simulation `concept-explainer` reader on
the branch cut from Slice 1 after PR 1 opens.

**Independent Test**: Open
`speckit-pro/artifact-gallery/templates/concept-explainer.html` over `file://`,
exercise add/remove/reset and slider limits, verify visible counts/boundary
feedback and representative fills, and confirm reload resets transient state.

- [x] T024 [US1] After PR 1 opens, create `art-005-gallery-completion-knowledge-reports-editors-slice-2` from the Slice 1 head and confirm the Slice 2 seven-path ledger plus 535-LOC ceiling in `specs/art-005-gallery-completion-knowledge-reports-editors/plan.md` [FR-016-FR-018, SC-008]
- [x] T025 [US1] RED: add `concept-explainer` reader, transient control/reset, visible count/limit feedback, no-export, accessibility, responsive, and ART-020 scroll assertions to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-003, FR-005-FR-006, FR-013-FR-014, FR-021-FR-022; US1]
- [x] T026 [US1] RED: add the exact `concept-title`, `principles`, `worked-example`, and two-item `simulation-scenarios` contract to `tests/speckit-pro/unit/test-artifact-fill-regions.py` [FR-020; US1]
- [x] T027 [US1] RED proof: run both focused modules in `tests/speckit-pro/unit/` and require failures for missing `speckit-pro/artifact-gallery/templates/concept-explainer.html`, planned status, controls, and fills [FR-004, FR-020-FR-022; US1]
- [x] T028 [US1] GREEN: create `speckit-pro/artifact-gallery/templates/concept-explainer.html` from pinned `15-research-concept-explainer.html` with canonical blocks, required fills, transient consistent-hashing simulation, reset, visible counts/min-max feedback, status semantics, responsive/reduced-motion handling, and no export [FR-002-FR-006, FR-013-FR-014, FR-020-FR-022; US1]
- [x] T029 [US1] GREEN: flip only `concept-explainer.status` to `shipped` in `speckit-pro/artifact-gallery/manifest.json` and retain `exports: []` plus every other row value [FR-004-FR-006; US1]
- [x] T030 [US1] GREEN proof: rerun `tests/speckit-pro/unit/test-artifact-gallery.py` and `tests/speckit-pro/unit/test-artifact-fill-regions.py` until all Slice 1 and Slice 2 assertions pass [FR-003-FR-006, FR-020-FR-022; US1]
- [x] T031 [US1] REFACTOR only `speckit-pro/artifact-gallery/templates/concept-explainer.html` for explicit session-only behavior and simple code while preserving the 535-LOC ceiling and focused green state [FR-012, FR-017, FR-019; US1]
- [x] T032 [US1] Measure and record the seven implementation-authored Slice 2 paths against the 535 ceiling in `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`; stop before generated refresh at 800 authored LOC or more [FR-016-FR-018, SC-008; US1]
- [x] T033 [US1] Regenerate authoritative outputs from `speckit-pro/artifact-gallery/templates/concept-explainer.html` with `scripts/refresh-release-artifacts.py` and docs `reference:generate`, checking the exact Claude/Codex dist and installed-cache template mirrors plus generated proofs [FR-003, FR-019; US1]
- [x] T034 [US1] Run focused, Layer 1, Layer 4, default-suite, `scripts/refresh-release-artifacts.py --check`, and spec-index checks, then commit the Slice 2 source checkpoint containing stable source, tests, generated outputs, and existing UAT carriers [FR-003, FR-013-FR-015, SC-001-SC-002; US1]
- [x] T035 [US1] Re-execute the complete cumulative UAT row set for Slices 1-2 at the Slice 2 source checkpoint, including direct-`file://` fills, controls, min/max boundaries, reset, accessibility, responsive layout, manifest parity, and reader-only recovery `not_applicable` evidence; replace the JSON rows, set top-level `sourceCommit` to the checkpoint, and update all three files under `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-*` [FR-015, FR-021-FR-024, SC-001-SC-002, SC-007, SC-009-SC-010; US1]
- [x] T036 [US1] Prove the Slice 2 source paths did not change after its UAT checkpoint; recheck final authored LOC below 800 and the complete authored/control-plane/generated Git-path ledger; stop on authored/non-size blockers or record a generated/control-plane-only total-file block as size-only; generate and validate the required Slice 2 PR packet, commit evidence, push, and open PR 2 before Slice 3 [FR-015-FR-019, FR-024, SC-007-SC-008; US1]

**Checkpoint**: User Story 1 is independently complete across Slices 1-2.

---

## Phase 5: User Story 2 / Slice 3 - Status Report (Priority: P2)

**Goal**: Ship a complete static `status-report` reader without an export path.

**Independent Test**: Open
`speckit-pro/artifact-gallery/templates/status-report.html` over `file://` and
verify complete summary, landed, in-flight, blocked, and next-action content at
both review widths with reader-only manifest semantics.

- [x] T037 [US2] After PR 2 opens, create `art-005-gallery-completion-knowledge-reports-editors-slice-3` from Slice 2 and confirm the seven-path ledger plus 560-LOC ceiling in `specs/art-005-gallery-completion-knowledge-reports-editors/plan.md` [FR-016-FR-018, SC-008]
- [x] T038 [US2] RED: add `status-report` static-reader, semantic headings/lists, no-export, accessibility, responsive, and ART-020 assertions to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-003, FR-005-FR-006, FR-013-FR-014, FR-022; US2]
- [x] T039 [US2] RED: add exact `summary`, `landed`, `in-flight`, `blocked`, and `next-actions` fill floors with two anchors in every list slot to `tests/speckit-pro/unit/test-artifact-fill-regions.py` [FR-020; US2]
- [x] T040 [US2] RED proof: run both focused modules under `tests/speckit-pro/unit/` and require intended failures for missing `speckit-pro/artifact-gallery/templates/status-report.html`, status, and fills [FR-004, FR-020; US2]
- [x] T041 [US2] GREEN: create `speckit-pro/artifact-gallery/templates/status-report.html` from pinned `11-status-report.html` with canonical blocks, complete representative content, semantic sections/lists, text-backed status meaning, responsive/reduced-motion behavior, and no export [FR-002-FR-006, FR-013-FR-014, FR-020, FR-022; US2]
- [x] T042 [US2] GREEN: flip only `status-report.status` to `shipped` in `speckit-pro/artifact-gallery/manifest.json`, preserving source and `exports: []` [FR-004-FR-006; US2]
- [x] T043 [US2] GREEN proof: rerun `tests/speckit-pro/unit/test-artifact-gallery.py` and `tests/speckit-pro/unit/test-artifact-fill-regions.py` until Slices 1-3 remain green [FR-003-FR-006, FR-020; US2]
- [x] T044 [US2] REFACTOR only `speckit-pro/artifact-gallery/templates/status-report.html` for simple semantic markup and audited tokens while preserving the 560-LOC ceiling [FR-003, FR-014, FR-017, FR-019; US2]
- [x] T045 [US2] Measure and record the seven implementation-authored Slice 3 paths against 560 in `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`; stop before regeneration if final or projected authored LOC reaches 800 [FR-016-FR-018, SC-008; US2]
- [x] T046 [US2] Regenerate outputs from `speckit-pro/artifact-gallery/templates/status-report.html` using `scripts/refresh-release-artifacts.py` and docs `reference:generate`; verify source-derived Claude/Codex dist, installed-cache, proof, XPLAT, and test-reference paths [FR-003, FR-019; US2]
- [x] T047 [US2] Run focused, Layer 1, Layer 4, full-suite, generated-artifact, and spec-index checks, then commit the Slice 3 source checkpoint containing stable source, tests, generated outputs, and existing UAT carriers [FR-003, FR-013-FR-015, SC-001-SC-002; US2]
- [x] T048 [US2] Re-execute the complete cumulative UAT row set for Slices 1-3 at the Slice 3 source checkpoint, including `file://`, representative-content, accessibility, responsive, manifest-parity, and producer-only `not_applicable` evidence; replace the JSON rows, set top-level `sourceCommit` to the checkpoint, and update all three files under `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-*` [FR-015, FR-022, FR-024, SC-001-SC-002, SC-005-SC-007, SC-010; US2]
- [x] T049 [US2] Prove the Slice 3 source paths did not change after its UAT checkpoint; recheck final authored LOC below 800 and the complete authored/control-plane/generated Git-path ledger; stop on authored/non-size blockers or record a generated/control-plane-only total-file block as size-only; generate and validate the required Slice 3 PR packet, commit evidence, push, and open PR 3 before Slice 4 [FR-015-FR-019, FR-024, SC-007-SC-008; US2]

---

## Phase 6: User Story 2 / Slice 4 - Incident Report (Priority: P2)

**Goal**: Ship a complete static `incident-report` reader with an accessible
timeline and no export path.

**Independent Test**: Open
`speckit-pro/artifact-gallery/templates/incident-report.html` over `file://` and
verify complete incident summary, timeline, impact, root cause, and follow-ups.

- [x] T050 [US2] After PR 3 opens, create `art-005-gallery-completion-knowledge-reports-editors-slice-4` from Slice 3 and confirm the seven-path ledger plus 620-LOC ceiling in `specs/art-005-gallery-completion-knowledge-reports-editors/plan.md` [FR-016-FR-018, SC-008]
- [x] T051 [US2] RED: add `incident-report` static reader, anchored timeline/report navigation, semantic structure, no-export, accessibility, responsive, and ART-020 assertions to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-003, FR-005-FR-006, FR-013-FR-014, FR-022; US2]
- [x] T052 [US2] RED: add exact `summary`, `timeline`, `impact`, `root-cause`, and `follow-ups` fills with two anchored timeline/follow-up items to `tests/speckit-pro/unit/test-artifact-fill-regions.py` [FR-020; US2]
- [x] T053 [US2] RED proof: run both focused modules in `tests/speckit-pro/unit/` and require intended missing-template/status/fill failures for `speckit-pro/artifact-gallery/templates/incident-report.html` [FR-004, FR-020; US2]
- [x] T054 [US2] GREEN: create `speckit-pro/artifact-gallery/templates/incident-report.html` from pinned `12-incident-report.html` with canonical blocks, required fills, complete incident content, accessible anchors/headings/lists, text-backed meaning, responsive/reduced-motion behavior, and no export [FR-002-FR-006, FR-013-FR-014, FR-020, FR-022; US2]
- [x] T055 [US2] GREEN: flip only `incident-report.status` to `shipped` in `speckit-pro/artifact-gallery/manifest.json`, retaining `exports: []` [FR-004-FR-006; US2]
- [x] T056 [US2] GREEN proof: rerun `tests/speckit-pro/unit/test-artifact-gallery.py` and `tests/speckit-pro/unit/test-artifact-fill-regions.py` until Slices 1-4 all pass [FR-003-FR-006, FR-020; US2]
- [x] T057 [US2] REFACTOR only `speckit-pro/artifact-gallery/templates/incident-report.html` for simple semantic navigation and token use without exceeding the 620 ceiling [FR-003, FR-014, FR-017, FR-019; US2]
- [x] T058 [US2] Measure and record the seven implementation-authored Slice 4 paths against 620 in `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`; stop at projected or final 800 authored LOC [FR-016-FR-018, SC-008; US2]
- [x] T059 [US2] Regenerate authoritative outputs for `speckit-pro/artifact-gallery/templates/incident-report.html` through `scripts/refresh-release-artifacts.py` and docs `reference:generate`; inspect the exact source-derived mirrors and proofs [FR-003, FR-019; US2]
- [x] T060 [US2] Run focused, Layer 1, Layer 4, full-suite, `scripts/refresh-release-artifacts.py --check`, and spec-index checks, then commit the Slice 4 source checkpoint containing stable source, tests, generated outputs, and existing UAT carriers [FR-003, FR-013-FR-015, SC-001-SC-002; US2]
- [x] T061 [US2] Re-execute the complete cumulative UAT row set for Slices 1-4 at the Slice 4 source checkpoint, including direct-`file://`, content, timeline, accessibility, responsive, manifest-parity, and producer-only `not_applicable` rows; replace the JSON rows, set top-level `sourceCommit` to the checkpoint, and update all three files under `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-*` [FR-015, FR-022, FR-024, SC-001-SC-002, SC-005-SC-007, SC-010; US2]
- [x] T062 [US2] Prove the Slice 4 source paths did not change after its UAT checkpoint; recheck final authored LOC below 800 and the complete authored/control-plane/generated Git-path ledger; stop on authored/non-size blockers or record a generated/control-plane-only total-file block as size-only; generate and validate the required Slice 4 PR packet, commit evidence, push, and open PR 4 before Slice 5 [FR-015-FR-019, FR-024, SC-007-SC-008; US2]

**Checkpoint**: User Story 2 is independently complete across Slices 3-4.

---

## Phase 7: User Story 3 / Slice 5 - Triage Board (Priority: P3)

**Goal**: Ship a keyboard-operable, memory-only triage editor with deterministic
column Markdown and complete visible clipboard recovery.

**Independent Test**: Edit/reorder/filter
`speckit-pro/artifact-gallery/templates/triage-board.html` over `file://`, prove
current-order Markdown plus issue appendix, and execute the complete clipboard,
boundary, accessibility, data-integrity, and race matrix.

- [x] T063 [US3] After PR 4 opens, create `art-005-gallery-completion-knowledge-reports-editors-slice-5` from Slice 4 and confirm the seven-path ledger plus 785-LOC ceiling in `specs/art-005-gallery-completion-knowledge-reports-editors/plan.md`; stop if recalculation reaches 800 [FR-016-FR-018, SC-008]
- [x] T064 [US3] RED: add `triage-board` producer, exact control label, session reset, named board/columns/tickets/filters, keyboard move/reorder, visible empty/filter states, semantic status, responsive, and prohibited-path assertions to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-003, FR-007, FR-012-FR-014, FR-019, FR-021-FR-022; US3]
- [x] T065 [US3] RED: add deterministic `now/next/later/cut` and ticket-field order, empty-column text, Markdown escaping, duplicate-ticket issue appendix, live-snapshot, stale-cache, and exact-message assertions to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-009-FR-011, FR-023; US3]
- [x] T066 [US3] RED: add zero/one-attempt clipboard capability, absent/non-callable, permission-denied, generic rejection, synchronous throw, failure-success-failure, and both superseded-settlement guard assertions to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-010-FR-011, SC-003-SC-004, SC-007; US3]
- [x] T067 [US3] RED: add `triage-items` list and `column-labels` fill inventory with two anchored items to `tests/speckit-pro/unit/test-artifact-fill-regions.py` [FR-020; US3]
- [x] T068 [US3] RED proof: run both focused modules under `tests/speckit-pro/unit/` and require failures caused by missing `speckit-pro/artifact-gallery/templates/triage-board.html`, planned status, producer contract, and fills [FR-004, FR-007, FR-009-FR-011, FR-020-FR-023; US3]
- [x] T069 [US3] GREEN: create the accessible memory-only board UI and editing model in `speckit-pro/artifact-gallery/templates/triage-board.html`, including keyboard movement/reordering, focus retention, filters/reset, visible empty states, and status announcements [FR-002-FR-003, FR-012-FR-014, FR-020-FR-022; US3]
- [x] T070 [US3] GREEN: implement one fresh-snapshot `Copy as Markdown` serializer in `speckit-pro/artifact-gallery/templates/triage-board.html` with column/ticket order, deterministic escaping, fixed `## Issues`, duplicate preservation, raw/special-character fidelity, and no cache [FR-007, FR-009-FR-010, FR-023; US3]
- [x] T071 [US3] GREEN: implement invocation-currency and the exact zero/one-attempt success/fallback state machine in `speckit-pro/artifact-gallery/templates/triage-board.html`, with labeled selectable focused fallback, normalized messages, stale-state replacement, and no hidden copy/download [FR-011, FR-019, SC-004; US3]
- [x] T072 [US3] GREEN: flip only `triage-board.status` to `shipped` in `speckit-pro/artifact-gallery/manifest.json`, preserving `exports: ["markdown"]` [FR-004, FR-007; US3]
- [x] T073 [US3] GREEN proof: rerun both focused modules in `tests/speckit-pro/unit/` and require all Slices 1-5 assertions to pass [FR-003-FR-014, FR-020-FR-023; US3]
- [x] T074 [US3] REFACTOR only `speckit-pro/artifact-gallery/templates/triage-board.html` for explicit flat logic while retaining all focused tests and at least 15 LOC headroom below the 800 block [FR-017, FR-019, SC-008; US3]
- [x] T075 [US3] Measure all seven implementation-authored Slice 5 paths with an explicit `git diff --numstat` pathspec and record actual/remaining/final LOC against 785 in `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`; stop before generation at 800 authored LOC [FR-016-FR-018, SC-008; US3]
- [x] T076 [US3] Regenerate outputs for `speckit-pro/artifact-gallery/templates/triage-board.html` with `scripts/refresh-release-artifacts.py` plus docs `reference:generate`; run focused, Layer 1, Layer 4, full-suite, generated, and spec-index checks; then commit the Slice 5 source checkpoint with stable source, tests, outputs, and existing UAT carriers [FR-003-FR-004, FR-013-FR-015, FR-019, SC-001-SC-002; US3]
- [x] T077 [US3] Re-execute the complete cumulative UAT row set for Slices 1-5 at the Slice 5 source checkpoint, including direct-`file://` editing/order, keyboard movement, empty/filter states, live freshness, duplicates, empty/all-empty board, Unicode/special characters, issue order, exact clipboard/fallback equality, every failure class, sequential transition, both races, reset, accessibility, and responsiveness; replace JSON rows and set top-level `sourceCommit` to the checkpoint in all three ART-005 `.process/uat-*` files [FR-015, FR-021-FR-024, SC-003-SC-007, SC-009-SC-011; US3]
- [x] T078 [US3] Prove the Slice 5 source paths did not change after its UAT checkpoint; recheck final authored LOC below 800 and the complete authored/control-plane/generated Git-path ledger; stop on authored/non-size blockers or record a generated/control-plane-only total-file block as size-only; generate and validate the required Slice 5 PR packet, commit evidence, push, and open PR 5 before Slice 6 [FR-015-FR-019, FR-024, SC-007-SC-008; US3]

---

## Phase 8: User Story 3 / Slice 6 - Feature Flags (Priority: P3)

**Goal**: Ship a memory-only feature-flag editor whose Markdown contains one
lossless, deterministic, typed JSON block.

**Independent Test**: Change
`speckit-pro/artifact-gallery/templates/feature-flags.html` over `file://`, prove
typed group/flag state and issue ordering round-trip, then execute the complete
clipboard and recovery matrix.

- [x] T079 [US3] After PR 5 opens, create `art-005-gallery-completion-knowledge-reports-editors-slice-6` from Slice 5 and confirm the seven-path ledger plus 780-LOC ceiling in `specs/art-005-gallery-completion-knowledge-reports-editors/plan.md` [FR-016-FR-018, SC-008]
- [x] T080 [US3] RED: add `feature-flags` producer, exact control, memory reset, named groups/controls, dependency/invalid/empty feedback, semantic status, accessibility, responsive, and prohibited-path assertions to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-003, FR-007, FR-012-FR-014, FR-019, FR-021-FR-022; US3]
- [x] T081 [US3] RED: add exact schema/version/wrapper/group/flag/issue field order, typed/null values, one JSON fence, `JSON.stringify(value, null, 2)` round-trip, duplicate group/flag preservation, raw invalid rollout/dependency evidence, special characters, and issue ordering to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-008, FR-010, FR-023, SC-011-SC-012; US3]
- [x] T082 [US3] RED: add the complete zero/one-attempt clipboard, sequential-transition, and two-race guard matrix for `feature-flags` to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-010-FR-011, SC-003-SC-004, SC-007; US3]
- [x] T083 [US3] RED: add `flags` list and `environment-notes` fill inventory with two anchored flags to `tests/speckit-pro/unit/test-artifact-fill-regions.py` [FR-020; US3]
- [x] T084 [US3] RED proof: run both focused modules in `tests/speckit-pro/unit/` and require missing-template/status/schema/fill failures for `speckit-pro/artifact-gallery/templates/feature-flags.html` [FR-004, FR-007-FR-011, FR-020-FR-023; US3]
- [x] T085 [US3] GREEN: create the accessible memory-only flag/group editing UI in `speckit-pro/artifact-gallery/templates/feature-flags.html` with dependency, invalid, empty, and unavailable feedback plus reset/status behavior [FR-002-FR-003, FR-012-FR-014, FR-020-FR-022; US3]
- [x] T086 [US3] GREEN: implement fresh-snapshot fenced-JSON Markdown serialization in `speckit-pro/artifact-gallery/templates/feature-flags.html` with exact typed schemas/order, duplicate/raw-invalid preservation, deterministic issues, special-character round-trip, and no cache [FR-007-FR-010, FR-023, SC-003, SC-011-SC-012; US3]
- [x] T087 [US3] GREEN: implement the exact invocation-current clipboard success/fallback matrix in `speckit-pro/artifact-gallery/templates/feature-flags.html`, including normalized messages, focus, latest fallback replacement, and stale-settlement suppression [FR-011, FR-019, SC-004, SC-007; US3]
- [x] T088 [US3] GREEN: flip only `feature-flags.status` to `shipped` in `speckit-pro/artifact-gallery/manifest.json`, preserving `exports: ["markdown"]` [FR-004, FR-007; US3]
- [x] T089 [US3] GREEN proof: rerun both focused modules under `tests/speckit-pro/unit/` and require all Slices 1-6 assertions to pass [FR-003-FR-014, FR-020-FR-023; US3]
- [x] T090 [US3] REFACTOR only `speckit-pro/artifact-gallery/templates/feature-flags.html` for simple explicit state/serialization logic while preserving 20 LOC headroom below 800 [FR-017, FR-019, SC-008; US3]
- [x] T091 [US3] Measure all seven implementation-authored Slice 6 paths and record actual/remaining/final LOC against 780 in `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`; stop at 800 authored LOC before generated refresh [FR-016-FR-018, SC-008; US3]
- [x] T092 [US3] Regenerate outputs for `speckit-pro/artifact-gallery/templates/feature-flags.html` through `scripts/refresh-release-artifacts.py` and docs `reference:generate`; run focused, Layer 1, Layer 4, full-suite, generated, and spec-index checks; then commit the Slice 6 source checkpoint with stable source, tests, outputs, and existing UAT carriers [FR-003-FR-004, FR-013-FR-015, FR-019, SC-001-SC-002; US3]
- [ ] T093 [US3] Re-execute the complete cumulative UAT row set for Slices 1-6 at the Slice 6 source checkpoint, including direct-`file://` typed state, JSON round-trip, group/flag order, duplicates, raw invalid rollout/dependency, nulls/empties, multiple issues, special characters, freshness, exact equality, every recovery class, sequential transition, both races, reset, accessibility, and responsive feedback; replace JSON rows and set top-level `sourceCommit` to the checkpoint in all three ART-005 `.process/uat-*` files [FR-015, FR-021-FR-024, SC-003-SC-007, SC-009-SC-012; US3]
- [ ] T094 [US3] Prove the Slice 6 source paths did not change after its UAT checkpoint; recheck final authored LOC below 800 and the complete authored/control-plane/generated Git-path ledger; stop on authored/non-size blockers or record a generated/control-plane-only total-file block as size-only; generate and validate the required Slice 6 PR packet, commit evidence, push, and open PR 6 before Slice 7 [FR-015-FR-019, FR-024, SC-007-SC-008; US3]

---

## Phase 9: User Story 3 / Slice 7 - Prompt Tuner (Priority: P3)

**Goal**: Ship a memory-only prompt editor with lossless, ordered, derived
preview state inside one deterministic fenced JSON block, then close the stack.

**Independent Test**: Change templates, slots, samples, fields, and previews in
`speckit-pro/artifact-gallery/templates/prompt-tuner.html` over `file://`; prove
the exact schema/round-trip and complete clipboard recovery matrix.

- [ ] T095 [US3] After PR 6 opens, create `art-005-gallery-completion-knowledge-reports-editors-slice-7` from Slice 6 and confirm the seven-path ledger plus 790-LOC ceiling and 10-LOC headroom in `specs/art-005-gallery-completion-knowledge-reports-editors/plan.md` [FR-016-FR-018, SC-008]
- [ ] T096 [US3] RED: add `prompt-tuner` producer, exact control, memory reset, labeled template/slot/sample/field/preview controls, empty/invalid feedback, semantic status, accessibility, responsive, and prohibited-path assertions to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-003, FR-007, FR-012-FR-014, FR-019, FR-021-FR-022; US3]
- [ ] T097 [US3] RED: add exact prompt schema/version/field order, first-occurrence slot-field order, derived preview, one JSON fence, round-trip, duplicate slot/sample preservation, raw invalid slot evidence, empty/null rules, Unicode/multiline/special characters, and deterministic issues to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-008, FR-010, FR-023, SC-011-SC-012; US3]
- [ ] T098 [US3] RED: add the complete zero/one-attempt clipboard, sequential-transition, and two-race guard matrix for `prompt-tuner` to `tests/speckit-pro/unit/test-artifact-gallery.py` [FR-010-FR-011, SC-003-SC-004, SC-007; US3]
- [ ] T099 [US3] RED: add `prompt-variants` list and `evaluation-notes` fill inventory with two anchored variants to `tests/speckit-pro/unit/test-artifact-fill-regions.py` [FR-020; US3]
- [ ] T100 [US3] RED proof: run both focused modules in `tests/speckit-pro/unit/` and require missing-template/status/schema/fill failures for `speckit-pro/artifact-gallery/templates/prompt-tuner.html` [FR-004, FR-007-FR-011, FR-020-FR-023; US3]
- [ ] T101 [US3] GREEN: create the accessible memory-only prompt/sample editing UI in `speckit-pro/artifact-gallery/templates/prompt-tuner.html` with labels, reset, visible empty/invalid states, derived previews, semantic status, responsive behavior, and required fills [FR-002-FR-003, FR-012-FR-014, FR-020-FR-022; US3]
- [ ] T102 [US3] GREEN: implement fresh-snapshot fenced-JSON Markdown serialization in `speckit-pro/artifact-gallery/templates/prompt-tuner.html` with exact schema/order, first-occurrence fields, duplicate/raw-invalid preservation, deterministic issues, and lossless multiline/Unicode/special-character values [FR-007-FR-010, FR-023, SC-003, SC-011-SC-012; US3]
- [ ] T103 [US3] GREEN: implement the exact invocation-current clipboard success/fallback matrix in `speckit-pro/artifact-gallery/templates/prompt-tuner.html`, including normalized messages, focus, latest fallback replacement, and both stale-settlement directions [FR-011, FR-019, SC-004, SC-007; US3]
- [ ] T104 [US3] GREEN: flip only `prompt-tuner.status` to `shipped` in `speckit-pro/artifact-gallery/manifest.json`, preserving `exports: ["markdown"]` [FR-004, FR-007; US3]
- [ ] T105 [US3] GREEN proof: rerun both focused modules under `tests/speckit-pro/unit/` and require all seven template, manifest, export, accessibility, and fill contracts to pass [FR-001-FR-014, FR-020-FR-023; US3]
- [ ] T106 [US3] REFACTOR only `speckit-pro/artifact-gallery/templates/prompt-tuner.html` for simple explicit editing/serialization logic without consuming the 10-LOC stop margin or weakening focused tests [FR-017, FR-019, SC-008; US3]
- [ ] T107 [US3] Measure all seven implementation-authored Slice 7 paths and record actual/remaining/final LOC against 790 in `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`; stop immediately if actual plus remaining work or final authored LOC reaches 800 [FR-016-FR-018, SC-008; US3]
- [ ] T108 [US3] Regenerate outputs for `speckit-pro/artifact-gallery/templates/prompt-tuner.html` through `scripts/refresh-release-artifacts.py` and docs `reference:generate`; run focused, Layer 1, Layer 4, full-suite, generated, and spec-index checks; then commit the Slice 7 source checkpoint with stable source, tests, outputs, and existing UAT carriers [FR-003-FR-004, FR-013-FR-015, FR-019, SC-001-SC-002; US3]
- [ ] T109 [US3] Re-execute the complete cumulative UAT row set for all seven artifacts at the Slice 7 source checkpoint, including direct-`file://` prompt order, duplicates, raw invalid slots, empty/null states, JSON round-trip, issue order, special characters, freshness, exact equality, every recovery class, sequential transition, both races, reset, accessibility, responsiveness, and every carried-forward row; replace JSON rows, set top-level `sourceCommit` to the checkpoint, and record stack-wide totals in the ART-005 `.process/uat-*` files [FR-015, FR-021-FR-024, SC-001-SC-007, SC-009-SC-012; US3]
- [ ] T110 [US3] Prove the Slice 7 source paths did not change after its UAT checkpoint; re-run final focused/full/generated/spec-index checks and record the complete authored/control-plane/generated Git-path ledger; stop on authored/non-size blockers or record a generated/control-plane-only total-file block as size-only [FR-003-FR-004, FR-015-FR-019, FR-024, SC-002, SC-007-SC-008; US3]
- [ ] T111 [US3] Generate and validate the required Slice 7 PR packet with complete UAT and scope evidence for the diff rooted at `speckit-pro/artifact-gallery/templates/prompt-tuner.html`, commit the evidence, push, and open PR 7 [FR-015-FR-019, FR-024, SC-007-SC-008; US3]

**Checkpoint**: User Story 3 and all seven implementation slices are
independently functional and reviewable.

---

## Phase 10: Stack-Wide Closeout

**Purpose**: Prove the completed stacked result without adding implementation
scope or hand-editing generated surfaces.

- [ ] T112 Verify every ART-005 row in `speckit-pro/artifact-gallery/manifest.json` is `shipped`, the four readers remain `exports: []`, the three producers remain `exports: ["markdown"]`, and all seven exact template paths exist [FR-001, FR-004-FR-007, SC-001-SC-002]
- [ ] T113 Run the cumulative focused gallery/fill modules and Layer 1/Layer 4/default suites through `tests/speckit-pro/run-all.py`, preserving zero failures on the Slice 7 stack head [FR-003, FR-020, SC-001-SC-002]
- [ ] T114 Run `scripts/refresh-release-artifacts.py --check` and docs reference generation/check against `docs-site/src/content/docs/reference/tests.md`; require source/dist/installed-cache/proof parity without manual generated edits [FR-003, FR-019]
- [ ] T115 Audit `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.json` against `contracts/uat-evidence-contract.md` for all required artifact, accessibility, responsive, boundary, data-integrity, and error-handling rows plus exact tested commits [FR-015, FR-024, SC-005-SC-007, SC-009-SC-012]
- [ ] T116 Recompute each slice's final seven-path authored `git diff --numstat` ledger and complete physical Git-path ledger against its predecessor; record the 670/535/560/620/785/780/790 authored verdicts plus every `tasks.md` control-plane/generated path and any size-only total-file block in `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`; stop any authored slice at 800 or on any non-size blocker [FR-016-FR-018, SC-008]
- [ ] T117 Verify no changes exist in `speckit-pro/artifact-gallery/SPA-CONTRACT.md`, `brand-kit.css`, `theme-toggle.html`, already-shipped templates, workflow routing, version manifests, or export vocabulary outside the seven declared rows [FR-019]
- [ ] T118 Audit the seven already-generated PR packets against `specs/art-005-gallery-completion-knowledge-reports-editors/spec.md`, `plan.md`, `tasks.md`, and `.process/uat-results.md`, proving each packet maps requirements/success criteria to its exact changed files, source checkpoint, checks, size-only findings, known gaps, and rollback notes before final handoff [FR-015-FR-018, FR-024, SC-007-SC-008]
- [ ] T119 Validate the seven stacked branch/PR bases and titles against `specs/art-005-gallery-completion-knowledge-reports-editors/contracts/slice-topology-contract.md`, then leave implementation ready for post-implementation verification and archival without merging or modifying `docs/ai/specs/.process/ART-005-*` archival paths [FR-018-FR-019]

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup T001-T005 must complete before Foundational T006-T010.
- T002 and T003 are the only safe parallel pair; both are read-only and touch
  different evidence paths.
- Slice 1 starts only after T001-T010.
- Each later slice starts only after its predecessor slice is complete and its
  PR is open: T023 -> T024, T036 -> T037, T049 -> T050, T062 -> T063,
  T078 -> T079, and T094 -> T095.
- Stack-wide closeout T112-T119 starts only after T111.

### User Story Dependencies

- **US1 (P1)**: Slices 1-2; complete T011-T036. Slice 1 is the first reviewable
  increment, but full US1 requires both reader artifacts.
- **US2 (P2)**: Slices 3-4; begins after US1's second PR opens and completes
  T037-T062.
- **US3 (P3)**: Slices 5-7; begins after US2's second PR opens and completes
  T063-T111.
- Every story remains independently testable at its checkpoint, but shared-file
  ownership and the operator-selected stack prohibit story-level parallel work.

### Within Every Slice

1. Bind the branch and reviewability ceiling.
2. Add focused RED tests and prove they fail for the intended reason.
3. Add exactly one template and its one manifest status flip.
4. Prove GREEN, then REFACTOR without broadening scope.
5. Measure before generated refresh; stop at the 800 authored-LOC threshold.
6. Regenerate from authoritative source, run all checks, and commit a source
   checkpoint.
7. Re-execute cumulative direct `file://` UAT at that checkpoint, record both
   authored and complete physical-path ledgers, validate the PR packet, and open
   the predecessor PR before the next branch.

## Parallel Opportunities

- T002 (upstream digest verification) and T003 (repository test baseline) may
  run in parallel after T001 because both are read-only and use different paths.
- No task that edits `speckit-pro/artifact-gallery/manifest.json`, either shared
  Layer 4 test module, any generated mirror/proof, or any ART-005 `.process/uat-*`
  file is parallelizable.
- No slices or user stories are parallelizable; the explicit seven-slice stack
  serializes them.

## Implementation Strategy

### MVP

The smallest complete user-story MVP is US1: finish Slices 1-2 (T011-T036).
Slice 1 alone is an independently reviewable delivery unit, but it does not
complete the two-artifact US1 acceptance boundary.

### Incremental Delivery

1. Complete Setup and Foundational checks.
2. Deliver one template per PR in the recorded stack order.
3. Stop and validate at every slice checkpoint; never batch a later template
   into an earlier PR.
4. Complete T112-T119 only from the seven-slice stack head.

## Notes

- Task checkboxes are orchestration metadata; implementation-authored LOC uses
  the seven declared paths in `plan.md`, while the complete physical Git-path
  ledger includes and separately labels the one `tasks.md` control-plane path.
- Generated outputs are changed only by their authoritative generators.
- `[P]` appears only on read-only setup checks; all implementation tasks are
  intentionally serial.
- A blocked reviewability checkpoint stops the affected slice for an explicit
  operator decision. It does not authorize a hidden split, exception, or scope
  reduction.
