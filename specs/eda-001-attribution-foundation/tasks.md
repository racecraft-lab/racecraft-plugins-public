# Tasks: Attribution Foundation

**Input**: `specs/eda-001-attribution-foundation/spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and `docs/ai/specs/.process/EDA-001-design-concept.md`.

**Organization**: Three user stories; six phases; two complete PR slices. Every checkbox is intentionally unchecked. These are implementation instructions, not verification results.

**Tests**: Required TDD. Write each test before the content or validator behavior it guards, execute the focused command, capture the intended failing assertion, then implement and rerun. A missing test script, unrelated exception, or already-passing assertion is not red proof. Complete all members of a TDD unit together; never mark a test-only member green. The execution sidecar binds every task, dependency, ownership set, and adjacent unit of at most four tasks.

**Reviewability**: Preserve the two-slice decision. The 625/650 LOC figures are planning estimates; neither proves the final budget. Eleven authored implementation files are enumerated by Plan; generated files come only from actual regeneration receipts. T001 checks the scope before implementation; T019 and T027 measure each concrete slice. A Markdown/JSON `not_estimated` result is not a budget pass.

## Format: `[ID] [P?] [Story] Description`

- `[P]` means disjoint files and satisfied prerequisites permit parallel execution.
- `[US1]`, `[US2]`, and `[US3]` map to the specification's stories.
- All paths are repository-relative. The focused command is `python3 tests/speckit-pro/unit/test-upstream-skill-attribution.py`.
- Read each applicable scoped `AGENTS.md` before implementation. Keep tests and fixtures under `tests/speckit-pro/unit/`; tests must never read a feature spec at run time.

## Phase 1: Setup and scope checkpoint

**Purpose**: Establish the bounded implementation scope and prepared toolchain without changing settings, versions, or other roadmap budgets.

- [ ] T001 Confirm the two-slice scope in `specs/eda-001-attribution-foundation/plan.md` against `specs/eda-001-attribution-foundation/tasks.md`, check the 11 declared authored files and one primary surface against the reviewability preset, and give the parent a pre-implementation scope receipt; verify the prepared Python/lint/docs environments and applicable scoped agent instructions. Acceptance: preserve US1+US2 in slice 1 and US3 in slice 2; report any concrete budget expansion before implementation, with no guessed budget pass (FR-013, FR-017, FR-018).

## Phase 2: Foundation — frozen evidence and synthetic cases

**Purpose**: Prepare independent inputs before authored notices or ledger content. The two `[P]` tasks own different files; neither depends on the other.

- [ ] T002 [P] Freeze the raw fork MIT bytes at `c55ee46073ed923f86ce59a5eb3b6d895095d1b7` in `tests/speckit-pro/unit/fixtures/upstream-skill-attribution/mattpocock-LICENSE.txt` and extract the exact pinned tree into `tests/speckit-pro/unit/fixtures/upstream-skill-attribution/inventory.json`, joining the unique skill names to the owner/disposition map in `specs/eda-001-attribution-foundation/data-model.md`. Acceptance: nonempty license with its final newline; exactly 38 sorted paths, bucket totals 18/7/4/9, 14 IGNORE owners EDA-001, 24 delivery owners EDA-002–EDA-010, no EDA-011 owner; missing, duplicate, or ambiguous joins fail (FR-001, FR-005, FR-007, FR-017).
- [ ] T003 [P] Create `tests/speckit-pro/unit/fixtures/upstream-skill-attribution/credit-cases.json` with synthetic Markdown, frontmatter-bearing Markdown, skill entry-point, TOML, and Python bodies, both quoted metadata styles, allowed Python prefixes, directory selections, and a shared-file multi-source case; include named header pass/fail cases and isolated frontmatter-placement mutations from `specs/eda-001-attribution-foundation/contracts/credits.md`. Acceptance: each positive case declares a nonempty expected file/source set; before/inside frontmatter, after body text, and unclosed-frontmatter negatives retain otherwise valid inputs and target placement diagnostics; no actual derivative is authored (FR-009–FR-012, FR-018).
- [ ] T004 Create `tests/speckit-pro/unit/fixtures/upstream-skill-attribution/valid-ledger.json` independently of the future shipped ledger, using the frozen inventory and the owning destination surfaces in `docs/ai/specs/engineering-discipline-adoption-technical-roadmap.md`. Acceptance: complete canonical 38-row zero-landed state with all 24 delivery rows planned, 14 explanatory IGNORE reasons, substantive omission notes only on ask-matt/wayfinder/triage, exact owners and buckets, and empty slice-1 transitive arrays; planned destinations are safe repository-relative paths and are not created by this feature (FR-002–FR-008, FR-013, FR-017, FR-018).

**Checkpoint**: Frozen expected evidence is independent of mutable authored content. Fixture creation alone is not a passing attribution gate. T002 and T003 may run together after T001; T004 waits for both.

## Phase 3: User Story 1 - Find the MIT notice and inventory (Priority: P1; Slice 1)

**Goal**: Ship the Matt notice, all 38 declared rows, and a visible README acknowledgment.

**Independent test**: The focused test accepts the actual canonical zero-landed ledger and notice, rejects isolated notice/ledger input mutations, and resolves the README link. T017–T018 additionally verify the two regenerated payloads.

### TDD unit: Matt notice and acknowledgment (T005–T006)

- [ ] T005 [US1] Write notice and acknowledgment assertions first in `tests/speckit-pro/unit/test-upstream-skill-attribution.py`, using the frozen Matt license and temporary repository-shaped roots. Acceptance: prove the focused command fails specifically for the absent authored notice or acknowledgment before writing either; cover a missing notice filename diagnostic, missing/duplicate License section or text block, altered license bytes/final newline, source/fork/tag/pin identity, ledger link, and the resolved acknowledgment link (FR-001, FR-012, FR-017–FR-019).
- [ ] T006 [US1] Implement the minimal raw-byte notice checking in `tests/speckit-pro/unit/test-upstream-skill-attribution.py`, author `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/UPSTREAM-NOTICE.md`, and add the Matt acknowledgment in `speckit-pro/README.md`. Acceptance: one exact license block retains the independent fixture's final newline, identity includes both repository URLs/tag/SHA and the modified-landed-derivative explanation, the sibling ledger reference names its planned path and the acknowledgment link resolves, and every T005 positive/targeted negative passes the same focused command (FR-001, FR-012, FR-017–FR-019).

### TDD unit: Canonical zero-landed ledger (T007–T008)

- [ ] T007 [US1] Extend `tests/speckit-pro/unit/test-upstream-skill-attribution.py` with the independent valid-ledger case and isolated inventory/schema/format mutations before creating the shipped ledger. Acceptance: capture the expected missing-ledger red result; assert missing/unparseable ledger filenames and input defects without invented row identities, duplicate JSON keys/non-finite values, unknown fields/types, conditional fields, exact owner/disposition/bucket/path membership/order, 38-count substituted paths, safe destination strings, IGNORE reasons, the three omission notes, and canonical raw bytes; row flip proof changes only that row (FR-002–FR-008, FR-012, FR-017).
- [ ] T008 [US1] Implement closed input/schema/canonical-byte validation in `tests/speckit-pro/unit/test-upstream-skill-attribution.py` and create `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/ledger.json` from independently reviewed evidence. Acceptance: perform parse/schema/order checks before landed-file selection, emit filename plus available row/path/field diagnostics, keep delivery rows planned and slice-1 arrays empty, reject all T007 mutations, and pass the focused command without deriving expected inventory or owners from the shipped ledger (FR-002–FR-008, FR-012, FR-013, FR-017, FR-018).

**Checkpoint**: US1 content and zero-landed validation are usable; slice 1 is deliverable only after US2 and its packaging/checks. Neither the README nor notice validation may depend on US3.

## Phase 4: User Story 2 - Reject missing derivative credits (Priority: P1; Slice 1)

**Goal**: Validate synthetic landed files and register the gate without landing any real row.

**Independent test**: The focused command accepts each positive Markdown/TOML/Python/SKILL case with a nonzero selected-file count, and rejects each targeted destination/header/metadata mutation with the landed row, selected filename, and failed field or placement defect.

### TDD unit: Landed destination selection (T009–T010)

- [ ] T009 [US2] Add destination-selection assertions to `tests/speckit-pro/unit/test-upstream-skill-attribution.py` using `tests/speckit-pro/unit/fixtures/upstream-skill-attribution/credit-cases.json`. Acceptance: prove red for unimplemented file/directory selection; cover missing destinations, empty directories, excluded-only selections, nested authored Markdown/TOML/Python files, repository escapes, explicit generated/vendored/fixture/notice exclusions, and a shared file selected by several landed rows (FR-009, FR-012, FR-017, FR-018).
- [ ] T010 [US2] Implement destination discovery and per-file aggregation in `tests/speckit-pro/unit/test-upstream-skill-attribution.py`. Acceptance: use explicit test-local repository categories, materialize synthetic cases beneath temporary repository-shaped roots, preserve authored reference directories, select every eligible file in sorted order, aggregate/deduplicate source paths, reject empty selection and resolved escapes, assert nonzero checked-file counts in every positive landed case, and turn T009 green (FR-009, FR-012, FR-017, FR-018).

### TDD unit: File-level header syntax and placement (T011–T012)

- [ ] T011 [US2] Add ordered-header assertions to `tests/speckit-pro/unit/test-upstream-skill-attribution.py` from `tests/speckit-pro/unit/fixtures/upstream-skill-attribution/credit-cases.json`. Acceptance: prove red for missing enforcement; isolate wrong repository/path set/SHA/modified state/notice/order/syntax and duplicate blocks; pair frontmatter-bearing Markdown and SKILL positives with before/inside frontmatter, after body text, and unclosed-frontmatter failures, asserting the landed path, selected file, and placement defect (FR-010, FR-012, FR-017).
- [ ] T012 [US2] Implement format-specific header validation in `tests/speckit-pro/unit/test-upstream-skill-attribution.py`. Acceptance: require one HTML comment for Markdown or ordered comment lines for TOML/Python, derive sorted sources from selected landed rows, preserve frontmatter first, allow only the documented Python prefix, reject unrelated preceding body blocks, check each selected file separately, and turn every T011 case green without section-level markers or existing loader-validator changes (FR-009, FR-010, FR-012, FR-017, FR-018).

### TDD unit: Matching SKILL metadata (T013–T014)

- [ ] T013 [US2] Add designated metadata-scalar assertions to `tests/speckit-pro/unit/test-upstream-skill-attribution.py` using `tests/speckit-pro/unit/fixtures/upstream-skill-attribution/credit-cases.json`. Acceptance: prove red for unenforced credits; include both valid quoted styles and multi-source order, missing/duplicate metadata or credits, wrong types, unquoted/block/invalid-quote forms, wrong identifiers/order/separators, and otherwise valid header/metadata disagreement with targeted diagnostics (FR-011, FR-012, FR-017).
- [ ] T014 [US2] Implement the bounded standard-library quoted-scalar recognizer in `tests/speckit-pro/unit/test-upstream-skill-attribution.py`. Acceptance: decode the designated single/double quoted value, compare the exact sorted identifiers joined by semicolon and space against the same selected source set used for the header, reject ambiguous duplicates and unsupported forms, turn T013 green, and retain T011's SKILL placement proofs without claiming general YAML or host display support (FR-010–FR-012, FR-017, FR-018).

### TDD unit: Suite integration and non-vacuous proof (T015–T016)

- [ ] T015 [US2] Add integration assertions in `tests/speckit-pro/unit/test-upstream-skill-attribution.py` that inspect `tests/speckit-pro/suite-manifest.json` and execute the complete slice-1 positive/negative fixture set. Acceptance: capture red for missing registration before changing the manifest; require exactly one membership in the existing unit layer/default dispatch, assert all 38 inventory rows and nonzero positive landed file counts, and demonstrate one passing and one targeted failing landed case without changing the real planned ledger (FR-007, FR-012, FR-013, FR-017).
- [ ] T016 [US2] Register the durable test once in `tests/speckit-pro/suite-manifest.json`, complete any minimal integration changes in `tests/speckit-pro/unit/test-upstream-skill-attribution.py`, and rerun the focused command. Acceptance: T015 turns green; the default manifest routes the test, every specified slice-1 mutation has a targeted diagnostic, and the implementation uses only Python 3.11+ standard library with no runtime feature-spec reads or real landed rows (FR-012, FR-013, FR-017, FR-018).

### Slice 1 packaging and acceptance boundary (T017–T019)

**Purpose**: Complete the US1+US2 vertical slice before adding HumanLayer behavior. The parent owns Git, gate recording, branch splitting, and PR emission.

- [ ] T017 [US2] Regenerate slice-1 `dist` with `scripts/refresh-release-artifacts.py` and `docs-site/src/content/docs/reference` with the existing reference generator; include the authored `speckit-pro` and `tests/speckit-pro` inputs in the receipt. Acceptance: run the exact regeneration commands below, inspect the actual changed-path inventory, verify Matt notice and ledger raw bytes in both payloads, and make no generated-file hand edits, packaging changes, or authored version edits (FR-001, FR-013, FR-017–FR-019).
- [ ] T018 [US2] Run every slice-1 verification command specified below against `tests/speckit-pro/unit/test-upstream-skill-attribution.py`, the registered suite in `tests/speckit-pro/suite-manifest.json`, generated `dist`, and `docs-site`. Acceptance: record exact exit codes and failed assertions; after the parent's source/generated commit, require the artifact drift check to exit zero; keep hosted container checks distinct from local evidence and repair within existing scope before claiming success (FR-001–FR-013, FR-017–FR-019).
- [ ] T019 [US2] Assemble the slice-1 review receipt from `specs/eda-001-attribution-foundation/plan.md`, `specs/eda-001-attribution-foundation/quickstart.md`, and the actual source/generated diff for the parent. Acceptance: measured LOC/production/total-file counts, requirement-to-file/evidence traceability, red/green proofs, review order, non-goals, limitations and rollback are concrete; state US3 remains the second slice and derivatives belong to EDA-002–EDA-010, with EDA-011 close-out. The parent validates the actual final title/release-note fence and emits the first PR (FR-013, FR-018).

**SLICE BOUNDARY**: Slice 1 contains T001–T019 (US1+US2, foundation, regeneration, acceptance). Slice 2 begins at T020, depends on accepted slice 1, and contains US3 plus final regeneration/checks. Emit two PRs through the parent's atomicity route; do not combine these budgets or begin derivative delivery before both notices are present.

## Phase 5: User Story 3 - Separate HumanLayer notice (Priority: P2; Slice 2)

**Goal**: Add the exact-source HumanLayer MIT notice and enforce its one required `pr` linkage regardless of planned status.

**Independent test**: The focused command accepts the final planned ledger and both notices, and rejects isolated missing/malformed HumanLayer notice, source, pin, path, holder, license, or link cases. T025–T026 verify both payloads.

- [ ] T020 [US3] Freeze the raw humanlayer/skills MIT license at `bba9d13ab34f0a87f1cc33df4dd196372393ddfc` in `tests/speckit-pro/unit/fixtures/upstream-skill-attribution/humanlayer-LICENSE.txt` and verify the copied source at `https://github.com/humanlayer/skills/blob/bba9d13ab34f0a87f1cc33df4dd196372393ddfc/plugins/show-me/skills/show-me/SKILL.md`. Acceptance: retain the exact nonempty bytes/final newline and Copyright (c) 2026 HumanLayer, record the public pinned copied-source identity, and do not use the superseded Apache/head fallback or refreeze Matt evidence (FR-014, FR-016, FR-017, FR-018).

### TDD unit: Separate HumanLayer notice (T021–T022)

- [ ] T021 [US3] Add HumanLayer notice assertions to `tests/speckit-pro/unit/test-upstream-skill-attribution.py` using `tests/speckit-pro/unit/fixtures/upstream-skill-attribution/humanlayer-LICENSE.txt`. Acceptance: capture red for the missing required notice before writing it; target missing-file diagnostics, wrong source/commit/copied path/public URL, missing/duplicate License sections/blocks, changed holder/content byte, and altered final newline on otherwise valid inputs (FR-012, FR-014, FR-016, FR-017).
- [ ] T022 [US3] Author `speckit-pro/skills/speckit-coach/references/upstream/humanlayer-show-me/UPSTREAM-NOTICE.md` and implement its holder-specific checking in `tests/speckit-pro/unit/test-upstream-skill-attribution.py`. Acceptance: one exact MIT text block matches the independent HumanLayer fixture, names the verified repository/commit/path and holder, includes `https://github.com/humanlayer/skills/blob/bba9d13ab34f0a87f1cc33df4dd196372393ddfc/plugins/show-me/skills/show-me/SKILL.md`, and turns every T021 case green with no copied derivative content (FR-014, FR-016–FR-018).

### TDD unit: Exact transitive source enforcement (T023–T024)

- [ ] T023 [US3] Add mandatory transitive-link assertions to `tests/speckit-pro/unit/test-upstream-skill-attribution.py` before modifying the real `pr` row. Acceptance: capture red for the missing source even with pr planned; target missing/empty/duplicate entries, unknown fields/types, wrong project/SHA/copied path/MIT identifier/holder/notice path, missing linked notice, and nonempty sources on other initial rows, asserting the row/field or notice filename defect (FR-003, FR-012, FR-014–FR-017).
- [ ] T024 [US3] Add the exact six-field HumanLayer record to only `pr` in `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/ledger.json` and `tests/speckit-pro/unit/fixtures/upstream-skill-attribution/valid-ledger.json`, then implement required linkage in `tests/speckit-pro/unit/test-upstream-skill-attribution.py`. Acceptance: project humanlayer/skills, commit `bba9d13ab34f0a87f1cc33df4dd196372393ddfc`, the copied source path identified by `https://github.com/humanlayer/skills/blob/bba9d13ab34f0a87f1cc33df4dd196372393ddfc/plugins/show-me/skills/show-me/SKILL.md`, license `MIT`, holder `HumanLayer`, and the authored HumanLayer notice path match exactly; all other arrays stay empty, all delivery rows stay planned, all T023 cases turn green, and no runtime slice flag is introduced (FR-003, FR-014–FR-018).

## Phase 6: Polish and final acceptance (slice 2)

**Purpose**: Package the complete attribution foundation and produce actual verification evidence for the second PR.

- [ ] T025 Regenerate final `dist` with `scripts/refresh-release-artifacts.py` and `docs-site/src/content/docs/reference` with the existing reference generator, carrying all authored `speckit-pro` and `tests/speckit-pro` inputs. Acceptance: record actual generated paths/counts, compare both Matt notice/ledger and HumanLayer notice raw bytes in Claude and Codex payloads, and reject unexpected behavior, manual payload changes, or version changes (FR-001, FR-014–FR-018).
- [ ] T026 Run every final verification command below for `tests/speckit-pro/unit/test-upstream-skill-attribution.py`, `tests/speckit-pro/suite-manifest.json`, `dist`, and `docs-site`, including all quickstart scenarios in `specs/eda-001-attribution-foundation/quickstart.md`. Acceptance: actual integer exit code zero for focused tests, quick/CI suites, privacy, configured lint/type, docs, and post-parent-commit artifact consistency; record hosted required-check outcomes separately, retain all negative proofs and nonzero positive selections, and do not substitute pending commands or partial checks for success (FR-001–FR-019).
- [ ] T027 Assemble the final slice-2 review receipt from `specs/eda-001-attribution-foundation/plan.md`, `specs/eda-001-attribution-foundation/quickstart.md`, and actual source/generated changes for the parent. Acceptance: measured budget and traceability, exact HumanLayer source/public URL, notice/license/link proofs, all verification outcomes, no unresolved scope additions, known limitations and rollback are reviewable; parent validates the actual final title/release-note fence and required hosted checks before ready state. The ledger keeps ordinary text merges; derivatives, fork edits, section markers, PARTIAL, and other roadmap budget changes are absent (FR-013–FR-019).

## Verification commands and evidence rules

Execute for each slice, after its implementation and regeneration:

```text
python3 tests/speckit-pro/unit/test-upstream-skill-attribution.py
python3 tests/speckit-pro/run-all.py
python3 scripts/run-python-lint.py run ruff
python3 scripts/run-python-lint.py run mypy
python3 tests/speckit-pro/unit/test-privacy-scan.py
SPECKIT_SKIP_TOOLCHAIN_CHECK=1 GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_NOSYSTEM=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-default-suite.json
python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate
pnpm --dir docs-site reference:check
pnpm --dir docs-site validate:quality
```

Regeneration belongs to T017/T025 and precedes the remaining checks; this list is not an instruction to regenerate twice. In an unbootstrapped fresh worktree, install docs dependencies with `pnpm --dir docs-site install --frozen-lockfile` before the docs commands. Use the existing prepared lint/type environment; no unapproved installation or version substitution. After the parent commits authored and generated files together, execute `python3 scripts/refresh-release-artifacts.py --check`. Its pre-commit failure cannot be recast as a successful drift check. Classify docs inputs through the existing repository classifier; if the actual receipt crosses a full-docs trigger, execute the repository's full docs validation command as well.

Both payload roots are `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`; use byte comparisons against the corresponding authored notice/ledger. The parent owns the exact conventional PR-title and release-note validations in root AGENTS.md, hosted required checks including both container preflights, and recording final gate receipts. No claim of success is made until each command's exact native handle has terminated with an integer exit code of zero. Environment errors remain evidence, not a permission to weaken assertions.

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation**: Depends on no prerequisites.
- **User Story 1 (P1)**: Depends on Foundation.
- **User Story 2 (P1)**: Depends on Foundation and User Story 1.
- **User Story 3 (P2)**: Depends on Foundation and User Story 2, including accepted slice-1 packaging T017–T019.
- **Polish**: Depends on User Story 1, User Story 2, and User Story 3.

The layer helper represents foundation, story, and final-polish increments. It does not encode multi-story PR groups or a second polish increment. T017–T019 are the shared slice-1 packaging/acceptance checkpoint within US2 completion; their task semantics and ownership remain unchanged. The parent must retain the ratified PR grouping: slice 1 T001–T019 (US1+US2), slice 2 T020–T027 (US3 plus final polish). Story increments are not additional PR authorization.

| Phase | Prerequisite | Closed outcome |
| --- | --- | --- |
| 1 | None | Scope/environment checkpoint |
| 2 | T001 | Independent frozen fixtures |
| US1 | T002–T004 | Matt notice, acknowledgment, canonical ledger |
| US2 | US1 | Complete credit checker and registration |
| Slice-1 boundary | US2 | Regenerated and verified first vertical slice |
| US3 | Accepted slice 1 | Separate pinned notice and exact pr linkage |
| Final polish | US3 | Regenerated and verified complete foundation |

The sidecar gives task-level prerequisites. Each two-task behavioral unit is adjacent and shares its capability/route; its red member must precede its implementation member. Units never cross a story or slice boundary. Validators and notices use a single test file, so later story units run serially. T020 is a story-specific source-fixture prerequisite, not derivative work.

## Parallel execution examples

- Foundation: after T001, T002 and T003 may execute together; their owned fixture paths are disjoint. T004 waits for both.
- US1: execute T005→T006 and then T007→T008; shared test ownership prevents parallel execution.
- US2: execute T009→T010, T011→T012, T013→T014, and T015→T016 in order; the same validator and fixture evidence are shared.
- US3: execute T020, T021→T022, and T023→T024 in order; the HumanLayer fixture, validator, and ledger changes are dependent.
- Packaging/checks: no parallel write lanes; generated tasks own their shared inputs and output roots conservatively. Do not omit those roots to create a parallel wave.

## Implementation strategy and bounds

### Incremental Delivery

1. Complete Foundation: T001–T004 establish scope and frozen fixture evidence.
2. Complete User Story 1: T005–T008 deliver the Matt notice, acknowledgment, and canonical ledger.
3. Complete User Story 2: T009–T019 deliver credit validation, registration, and shared slice-1 packaging/acceptance. This closes ratified PR slice 1, containing US1+US2 and T001–T019.
4. Complete User Story 3: T020–T024 deliver the pinned HumanLayer notice and required transitive linkage after accepted slice 1.
5. Complete Polish: T025–T027 regenerate and verify the complete foundation. This closes ratified PR slice 2, containing US3 and T020–T027.

The minimum deliverable is slice 1 (US1+US2), because unenforced content alone does not satisfy FR-013. Slice 2 then completes the holder-specific foundation before other EDA specs add derivatives. Keep the planned 11 authored files; mutate negative cases in memory instead of growing the fixture footprint.

Target the automated two-hour envelope: startup/scope 5 minutes, fixtures 10, US1 15, US2 35, slice-1 packaging/checks 10, US3 15, final packaging/checks 15, and repairs 15. These are scheduling allocations, not measured runtimes. Record actual elapsed time; budget pressure never authorizes skipped proofs, fabricated passes, or scope expansion.

**Non-goal check**: No task authorizes derivative content, fork edits, section-level markers, PARTIAL disposition, other roadmap budget edits, ledger assignment to the generated merge driver, packaging/loader changes, or manual version edits. Synthetic temporary fixture bodies solely exercise validation. Historical Apache/head notes in the design interview are superseded by the current MIT exact-source decision. Any implementation need crossing these boundaries must be reported to the parent before the change.
