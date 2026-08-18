# Tasks: ART-004 Gallery Completion - Design & Prototyping

**Input**: Design documents from `specs/art-004-gallery-completion-design-prototyping/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and completed checklists.

**Tests**: Required. The workflow requires strict RED/GREEN/REFACTOR/VERIFY ordering.

**Reviewability**: Execute as three ordered review slices already approved by G3:

| Slice | Scope | Gate result | Parallel rule |
|---|---|---|---|
| 1 | Keyboard foundation | pass, 160 reviewable LOC, 3 production files, 4 total files | Only disjoint template repairs may run in parallel after RED tests exist |
| 2 | Read-only ports | warn, 590 reviewable LOC, 4 production files, 7 total files | Only individual HTML ports may run in parallel; manifest, tests, generated outputs, and docs are serial |
| 3 | Decision ports | warn, 520 reviewable LOC, 2 production files, 5 total files | Only individual HTML ports may run in parallel; manifest, tests, generated outputs, and docs are serial |

## Format: `[ID] [P?] [Story] Description`

- `[P]` means the task touches a disjoint source file and does not touch the shared manifest, shared tests, generated output, payload, proof, or documentation surface.
- `[US1]`, `[US2]`, and `[US3]` map to the user stories in `spec.md`.
- Tasks without a user story label are shared setup, foundational, or polish tasks.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the execution root, approved topology, and pinned-source inputs before implementation begins.

- [x] T001 VERIFY confirm branch `art-004-gallery-completion-design-prototyping`, execution root, and unrelated local changes with `git status --short` in the registered ART-004 worktree root
- [x] T002 VERIFY confirm G3 remains non-blocking by reading the three approved slice contracts in `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-1-keyboard-foundation.md`, `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-2-read-only-ports.md`, and `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-3-decision-ports.md`, then confirm the deferred tasks-mode `reviewability-gate` fallback remains tied to G0 setup evidence, `160/pass`, `590/warn`, `520/warn`, and the human-approved split
- [x] T003 VERIFY retrieve the six pinned upstream sources at commit `58c305be97f47b26b678f2c07dec01d4242268ec` into `/private/tmp/art-004-upstream/` for read-only implementation evidence
- [x] T004 VERIFY confirm no implementation task will hand-edit generated payload, installed-cache proof, or generated reference paths listed in `specs/art-004-gallery-completion-design-prototyping/plan.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the serial review route and baseline validation commands that block all user-story implementation.

- [x] T005 RED run `python3 tests/speckit-pro/run-all.py` and preserve the baseline result for comparison with later changes in `tests/speckit-pro/run-all.py`
- [x] T006 VERIFY run the setup-mode reviewability gate against `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-1-keyboard-foundation.md`
- [x] T007 VERIFY run the setup-mode reviewability gate against `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-2-read-only-ports.md`
- [x] T008 VERIFY run the setup-mode reviewability gate against `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-3-decision-ports.md`
- [x] T009 VERIFY stop before implementation if any gate returns `block` and record the failed gate path in `specs/art-004-gallery-completion-design-prototyping/plan.md`

**Checkpoint**: Foundation ready only when all three approved slice gates remain non-blocking.

---

## Phase 3: User Story 1 - Keyboard-Scroll Wide Regions (Priority: P1, Slice 1)

**Goal**: A keyboard-only reader can focus, identify, and horizontally scroll every wide region in shipped gallery artifacts.

**Independent Test**: Open `code-approaches`, `implementation-plan`, and `module-map` over `file://`, navigate by keyboard, confirm each repaired horizontal region receives focus in source order, exposes a specific accessible name, scrolls with the keyboard, and does not trap focus.

### Tests for User Story 1

- [x] T010 [US1] RED add durable Layer 4 collector coverage for declared keyboard-scroll regions, missing `tabindex="0"`, missing `role="group"`, missing or generic `aria-label`, positive `tabindex`, and undeclared horizontal overflow styling in `tests/speckit-pro/unit/test-artifact-gallery.py`
- [x] T011 [US1] RED add the in-memory negative fixture named `test_rejects_declared_scroll_region_without_keyboard_route` in `tests/speckit-pro/unit/test-artifact-gallery.py`
- [x] T012 [US1] RED prove the five existing affected horizontal-scroll containers fail before repair in `tests/speckit-pro/unit/test-artifact-gallery.py`

### Implementation for User Story 1

- [x] T013 [P] [US1] GREEN add `data-rc-keyboard-scroll="horizontal"`, `tabindex="0"`, `role="group"`, and a specific `aria-label` to the affected horizontal region in `speckit-pro/artifact-gallery/templates/code-approaches.html`
- [x] T014 [P] [US1] GREEN add `data-rc-keyboard-scroll="horizontal"`, `tabindex="0"`, `role="group"`, and specific `aria-label` values to the affected horizontal regions in `speckit-pro/artifact-gallery/templates/implementation-plan.html`
- [x] T015 [P] [US1] GREEN add `data-rc-keyboard-scroll="horizontal"`, `tabindex="0"`, `role="group"`, and specific `aria-label` values to the affected horizontal regions in `speckit-pro/artifact-gallery/templates/module-map.html`
- [x] T016 [US1] REFACTOR keep the keyboard-scroll guard helpers durable and capability-named, with `gallery_root` as the first argument, in `tests/speckit-pro/unit/test-artifact-gallery.py`
- [x] T017 [US1] VERIFY run focused Layer 4 gallery tests for keyboard-scroll behavior in `tests/speckit-pro/unit/test-artifact-gallery.py`
- [x] T018 [US1] VERIFY complete `file://` keyboard-scroll UAT for `code-approaches`, `implementation-plan`, and `module-map` using the ART-004 matrix in `specs/art-004-gallery-completion-design-prototyping/quickstart.md`
- [x] T019 [US1] VERIFY record Safari Tab or Option-Tab reachability, source-order focus, visible focus, accessible names, arrow-key scroll change, and no keyboard trap for repaired regions in `specs/art-004-gallery-completion-design-prototyping/quickstart.md`
- [x] T020 [US1] VERIFY regenerate derived payloads and installed-cache proof files from source with `python3 scripts/refresh-release-artifacts.py`
- [x] T021 [US1] VERIFY regenerate generated reference pages affected by tracked test/source changes with `pnpm --dir docs-site reference:generate` for `docs-site/src/content/docs/reference/tests.md` and `docs-site/src/content/docs/reference/source-vs-dist.md`
- [x] T022 [US1] VERIFY run `python3 tests/speckit-pro/run-all.py`, `python3 scripts/refresh-release-artifacts.py --check`, and `pnpm --dir docs-site reference:check` against `tests/speckit-pro/run-all.py`

**Checkpoint**: User Story 1 is complete when the global guard passes for repaired artifacts and manual keyboard-scroll UAT is recorded separately from ART-003.

---

## Phase 4: User Story 2 - Open Complete Design Artifacts Offline (Priority: P2, Slice 2)

**Goal**: A reader can open the four read-only ports directly from disk, inspect every distinct upstream-derived section and interaction, and see no export-looking affordance.

**Independent Test**: Open `design-system`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations` over `file://` while offline, compare the visible sections and interactions against the pinned source inventory, verify keyboard and theme behavior, and confirm the manifest changes are status-only.

### Tests for User Story 2

- [x] T023 [US2] RED add read-only port file-presence, attribution, canonical `BRAND-KIT` and `GALLERY-HEAD`, no-export-affordance, status-only manifest drift, and offline-contract coverage in `tests/speckit-pro/unit/test-artifact-gallery.py`
- [x] T024 [US2] RED add read-only fill-region floors for `design-system`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations`, including `interaction-prototype.views`, in `tests/speckit-pro/unit/test-artifact-fill-regions.py`
- [x] T025 [US2] RED extend keyboard-scroll non-vacuity coverage for new read-only wide regions in `tests/speckit-pro/unit/test-artifact-gallery.py`

### Implementation for User Story 2

- [x] T026 [P] [US2] GREEN create the self-contained offline `design-system` port with color, typography, spacing, shape, components, canonical markers, attribution, keyboard-scroll declarations, brand-kit fallbacks, both themes, non-color meaning, and reduced-motion behavior in `speckit-pro/artifact-gallery/templates/design-system.html`
- [x] T027 [P] [US2] GREEN create the self-contained offline `animation-prototype` port with completion-stage, easing-controls, keyframes, CSS snippet, task reset, canonical markers, attribution, keyboard controls, both themes, non-color meaning, and reduced-motion behavior in `speckit-pro/artifact-gallery/templates/animation-prototype.html`
- [x] T028 [P] [US2] GREEN create the self-contained offline `interaction-prototype` port with retained views, interaction notes, open questions, reorder or linked-screen behavior, reset cleanup, canonical markers, attribution, keyboard controls, both themes, non-color meaning, and reduced-motion behavior in `speckit-pro/artifact-gallery/templates/interaction-prototype.html`
- [x] T029 [P] [US2] GREEN create the self-contained offline `svg-illustrations` port with Queue, Retry, Fan-out/Fan-in illustrations, captions, palette rules, inline SVG references, canonical markers, attribution, keyboard-scroll declarations, both themes, non-color meaning, and no `Download SVG` control in `speckit-pro/artifact-gallery/templates/svg-illustrations.html`
- [x] T030 [US2] GREEN flip only `design-system`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations` from `planned` to `shipped` in `speckit-pro/artifact-gallery/manifest.json`
- [x] T031 [US2] REFACTOR tighten read-only coverage for stable selectors, source inventory, compaction boundaries, and durable capability names in `tests/speckit-pro/unit/test-artifact-gallery.py`
- [x] T032 [US2] REFACTOR tighten fill-region and list-slot coverage for the four read-only ports in `tests/speckit-pro/unit/test-artifact-fill-regions.py`
- [x] T033 [US2] VERIFY run focused gallery and fill-region tests for read-only ports in `tests/speckit-pro/unit/test-artifact-gallery.py` and `tests/speckit-pro/unit/test-artifact-fill-regions.py`
- [x] T034 [US2] VERIFY complete offline `file://` UAT for the four read-only ports, including keyboard-only controls, visible state, reset or cleanup outcome, Safari keyboard path, brand font fallback readability, both-theme contrast, non-color meaning, and reduced motion in `specs/art-004-gallery-completion-design-prototyping/quickstart.md`
- [x] T035 [US2] VERIFY regenerate derived payloads and installed-cache proof files from source with `python3 scripts/refresh-release-artifacts.py`
- [x] T036 [US2] VERIFY regenerate generated reference pages affected by tracked source/test changes with `pnpm --dir docs-site reference:generate` for `docs-site/src/content/docs/reference/tests.md` and `docs-site/src/content/docs/reference/source-vs-dist.md`
- [x] T037 [US2] VERIFY run `python3 tests/speckit-pro/run-all.py`, `python3 scripts/refresh-release-artifacts.py --check`, and `pnpm --dir docs-site reference:check` against `tests/speckit-pro/run-all.py`

**Checkpoint**: User Story 2 read-only scope is complete when the four slice-2 ports are shipped, read-only behavior is enforced, and generated outputs match authoritative source.

---

## Phase 5: User Story 3 - Export a Selected Design Decision (Priority: P3, Slice 3)

**Goal**: A reader chooses one visual direction or one base component variant, records a rationale, and copies the live decision as prompt or Markdown with a selectable fallback on clipboard refusal.

**Independent Test**: Open `visual-designs` and `component-variants` over `file://`, select decisions, enter rationale, use both copy controls, exercise incomplete input validation, simulate clipboard refusal modes, and verify the fallback contains the same live payload and stale attempts cannot overwrite newer state.

### Tests for User Story 3

- [x] T038 [US3] RED add decision-port file-presence, attribution, canonical-block, export-control, status-only manifest drift, and offline-contract coverage for `visual-designs` and `component-variants` in `tests/speckit-pro/unit/test-artifact-gallery.py`
- [x] T039 [US3] RED add decision-port fill-region and list-slot coverage for `visual-designs.directions` and `component-variants.variants` in `tests/speckit-pro/unit/test-artifact-fill-regions.py`
- [x] T040 [US3] RED add decision-export coverage for persistent radio selection, rationale validation, exact prompt and Markdown payload order, `#export-status`, labelled fallback textarea, clipboard refusal modes, stale fallback invalidation, and stale invocation suppression in `tests/speckit-pro/unit/test-artifact-gallery.py`
- [x] T041 [US3] RED extend keyboard-scroll, keyboard-control, name/role/state/value, no-positive-tabindex, contrast, non-color meaning, and reduced-motion coverage for the two decision ports in `tests/speckit-pro/unit/test-artifact-gallery.py`

### Implementation for User Story 3

- [x] T042 [P] [US3] GREEN create the self-contained offline `visual-designs` port with design brief, background toggle, four directions, exact source attribution, canonical markers, one persistent chosen direction, required rationale, prompt and Markdown exports, clipboard fallback, keyboard controls, both themes, non-color meaning, and reduced-motion behavior in `speckit-pro/artifact-gallery/templates/visual-designs.html`
- [x] T043 [P] [US3] GREEN create the self-contained offline `component-variants` port with variant controls, six component-state families, live snippet, padding reset to `20px`, border reset to `hairline`, shadow reset to `shown`, one persistent chosen base variant, required rationale, prompt and Markdown exports, clipboard fallback, keyboard controls, both themes, non-color meaning, and reduced-motion behavior in `speckit-pro/artifact-gallery/templates/component-variants.html`
- [x] T044 [US3] GREEN flip only `visual-designs` and `component-variants` from `planned` to `shipped` in `speckit-pro/artifact-gallery/manifest.json`
- [x] T045 [US3] REFACTOR remove only local duplication that obscures decision-export behavior while preserving the single-file no-shared-runtime contract in `speckit-pro/artifact-gallery/templates/visual-designs.html` and `speckit-pro/artifact-gallery/templates/component-variants.html`
- [x] T046 [US3] REFACTOR tighten decision-export tests around durable selectors and exact refusal semantics in `tests/speckit-pro/unit/test-artifact-gallery.py`
- [x] T047 [US3] VERIFY run focused gallery and fill-region tests for decision ports in `tests/speckit-pro/unit/test-artifact-gallery.py` and `tests/speckit-pro/unit/test-artifact-fill-regions.py`
- [x] T048 [US3] VERIFY complete `file://` UAT for valid prompt copy, valid Markdown copy, missing-choice validation, missing-rationale validation, whitespace-only rationale validation, unavailable Clipboard API, non-callable `writeText`, synchronous exception, rejected write promise, denied permission, local-file security restriction, focused fallback textarea, stale fallback clearing, and stale-copy-settle behavior in `specs/art-004-gallery-completion-design-prototyping/quickstart.md`
- [x] T049 [US3] VERIFY complete `file://` UAT for decision-port offline readability, keyboard-only operation, visible focus, logical source order, Safari Tab or Option-Tab path, names/roles/states/values, visible labels or instructions, both-theme contrast, non-color meaning, typeface fallback, and reduced-motion behavior in `specs/art-004-gallery-completion-design-prototyping/quickstart.md`
- [x] T050 [US3] VERIFY regenerate derived payloads and installed-cache proof files from source with `python3 scripts/refresh-release-artifacts.py`
- [x] T051 [US3] VERIFY regenerate generated reference pages affected by tracked source/test changes with `pnpm --dir docs-site reference:generate` for `docs-site/src/content/docs/reference/tests.md` and `docs-site/src/content/docs/reference/source-vs-dist.md`
- [x] T052 [US3] VERIFY run `python3 tests/speckit-pro/run-all.py`, `python3 scripts/refresh-release-artifacts.py --check`, and `pnpm --dir docs-site reference:check` against `tests/speckit-pro/run-all.py`

**Checkpoint**: User Story 3 is complete when both decision ports ship, export payloads derive from live state, clipboard refusal uses the exact fallback path, and all generated outputs agree with source.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final serial evidence, review packet readiness, roadmap disposition, and release-readiness checks.

- [ ] T053 VERIFY compare `speckit-pro/artifact-gallery/manifest.json` before and after implementation and prove exactly six status values changed from `planned` to `shipped` with no identifier, category, title, stage, trigger, source, `when_to_use`, signal vocabulary, or `exports` drift
- [ ] T054 VERIFY prove the nine ART-004 and repaired artifact IDs are swept by the global guard in `tests/speckit-pro/unit/test-artifact-gallery.py`
- [ ] T055 VERIFY prove all required fill regions and list slots from the Functional Fidelity Inventory are covered in `tests/speckit-pro/unit/test-artifact-fill-regions.py`
- [ ] T056 VERIFY run the complete manual `file://` UAT matrix for the six new ports and three repaired artifacts in `specs/art-004-gallery-completion-design-prototyping/quickstart.md`
- [ ] T057 VERIFY record PR review evidence for what changed, why, non-goals, review order, scope budget, traceability, verification, known gaps, and rollback or feature-flag notes in `docs/ai/specs/.process/ART-004-workflow.md`
- [ ] T058 GREEN mark ART-020 superseded by ART-004 without changing unrelated roadmap rows in `docs/ai/specs/html-artifacts-technical-roadmap.md`
- [ ] T059 VERIFY run `python3 tests/speckit-pro/run-all.py`, `python3 scripts/refresh-release-artifacts.py --check`, `pnpm --dir docs-site reference:check`, and `git diff --check` against `tests/speckit-pro/run-all.py`
- [ ] T060 VERIFY validate the exact prospective PR title `feat(speckit-pro): complete design gallery artifacts` against the repository release-readiness gate and record the result in `docs/ai/specs/.process/ART-004-workflow.md`

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends on | Blocks |
|---|---|---|
| Phase 1 Setup | None | Phase 2 |
| Phase 2 Foundational | Phase 1 | All user stories |
| Phase 3 US1 / Slice 1 | Phase 2 | Slice 2 and Slice 3 |
| Phase 4 US2 / Slice 2 | Phase 3 | Slice 3 |
| Phase 5 US3 / Slice 3 | Phase 4 | Final polish |
| Phase 6 Polish | Phase 5 | PR readiness |

### User Story Dependencies

| Story | Dependency | Reason |
|---|---|---|
| US1 | Setup and Foundation | Repairs the inherited accessibility defect before new ports copy the pattern |
| US2 | US1 | Read-only ports must inherit the keyboard-scroll declaration and guard contract |
| US3 | US1 and US2 | Decision ports depend on the same artifact, manifest, accessibility, and generated-output contracts |

### RED/GREEN/REFACTOR/VERIFY Ordering

| Story | RED | GREEN | REFACTOR | VERIFY |
|---|---|---|---|---|
| US1 | T010-T012 | T013-T015 | T016 | T017-T022 |
| US2 | T023-T025 | T026-T030 | T031-T032 | T033-T037 |
| US3 | T038-T041 | T042-T044 | T045-T046 | T047-T052 |
| Cross-cutting | T005 | T058 | None | T001-T004, T006-T009, T053-T057, T059-T060 |

## Parallel Opportunities

Only these tasks are marked `[P]` because each touches one disjoint HTML file and no shared manifest, shared tests, generated outputs, payloads, proofs, or documentation:

| Parallel set | Tasks | Must complete before |
|---|---|---|
| Slice 1 template repairs | T013, T014, T015 | T016 |
| Slice 2 read-only ports | T026, T027, T028, T029 | T030 |
| Slice 3 decision ports | T042, T043 | T044 |

## Parallel Example: User Story 1

```text
Task: "T013 GREEN repair code-approaches keyboard-scroll region in speckit-pro/artifact-gallery/templates/code-approaches.html"
Task: "T014 GREEN repair implementation-plan keyboard-scroll regions in speckit-pro/artifact-gallery/templates/implementation-plan.html"
Task: "T015 GREEN repair module-map keyboard-scroll regions in speckit-pro/artifact-gallery/templates/module-map.html"
```

## Parallel Example: User Story 2

```text
Task: "T026 GREEN create design-system in speckit-pro/artifact-gallery/templates/design-system.html"
Task: "T027 GREEN create animation-prototype in speckit-pro/artifact-gallery/templates/animation-prototype.html"
Task: "T028 GREEN create interaction-prototype in speckit-pro/artifact-gallery/templates/interaction-prototype.html"
Task: "T029 GREEN create svg-illustrations in speckit-pro/artifact-gallery/templates/svg-illustrations.html"
```

## Parallel Example: User Story 3

```text
Task: "T042 GREEN create visual-designs in speckit-pro/artifact-gallery/templates/visual-designs.html"
Task: "T043 GREEN create component-variants in speckit-pro/artifact-gallery/templates/component-variants.html"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 through T022.
3. Stop and validate keyboard-only horizontal scrolling independently for the three repaired artifacts.

### Incremental Delivery

1. Deliver US1 / Slice 1 keyboard foundation and generated-source agreement.
2. Deliver US2 / Slice 2 read-only ports and generated-source agreement.
3. Deliver US3 / Slice 3 decision ports and generated-source agreement.
4. Complete polish and release-readiness checks.

### Parallel Team Strategy

Parallel work is allowed only inside the three listed `[P]` sets. Shared manifest, shared test literals, generated payloads, installed-cache proofs, and generated reference docs must remain serialized in task order.

## Traceability

### Functional Requirements

| Requirement | Tasks |
|---|---|
| FR-001 | T023-T030, T038-T044, T053 |
| FR-002 | T026-T029, T042-T043, T034, T049, T056 |
| FR-003 | T023-T029, T031-T034, T038-T043, T055-T056 |
| FR-004 | T003, T023, T026-T029, T038, T042-T043 |
| FR-005 | T023, T026-T029, T038, T042-T043 |
| FR-006 | T023, T030, T038, T044, T053 |
| FR-007 | T038, T040, T042, T048 |
| FR-008 | T038, T040, T043, T048 |
| FR-009 | T023, T026-T029, T031, T034 |
| FR-010 | T038, T040, T042-T043, T046, T048 |
| FR-011 | T010-T019, T025-T029, T041-T043, T049, T054 |
| FR-012 | T010-T019 |
| FR-013 | T010-T012, T016-T017, T025, T041, T054 |
| FR-014 | T002, T006-T009, T058 |
| FR-015 | T010, T018-T019, T025-T029, T034, T041-T043, T049, T056 |
| FR-016 | T010, T018-T019, T040-T043, T046, T048-T049, T056 |
| FR-017 | T026-T029, T034, T041-T043, T049, T056 |

### Success Criteria

| Success criterion | Tasks |
|---|---|
| SC-001 | T023-T030, T034, T038-T044, T049, T056 |
| SC-002 | T010-T019, T025-T029, T041-T043, T049, T054, T056 |
| SC-003 | T010-T017, T025, T041, T054 |
| SC-004 | T038-T040, T042-T043, T046-T048 |
| SC-005 | T023, T030, T038, T044, T053 |
| SC-006 | T020-T022, T035-T037, T050-T052, T059 |
| SC-007 | T002, T006-T009 |
| SC-008 | T018-T019, T034, T048-T049, T056 |
| SC-009 | T026-T029, T034, T041-T043, T049, T056 |

### Checklists

| Checklist | Tasks |
|---|---|
| requirements | T001-T004, T053-T060 |
| ux | T023-T034, T038-T045, T056-T057 |
| accessibility | T010-T019, T025-T029, T034, T041-T043, T049, T054, T056 |
| error-handling | T038-T040, T046-T048, T050-T053, T059 |

## Notes

- Generated paths are regenerated by authoritative commands only; no task hand-edits generated mirrors.
- The six new HTML ports are not parallel-safe with manifest or generated integration work; only the source-file creation tasks are parallel-safe.
- Test and fixture names must use durable capability names, not ART-004 or ART-020.
- Keep implementation on the approved ordered slices even though ART-004 remains one combined branch and delivery.
