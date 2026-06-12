# Tasks: Reviewer-ready PR packet contract

**Input**: Design documents from `/specs/prsg-012-reviewer-ready-pr-packet-contract/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/pr-packet.schema.json, quickstart.md

**Tests**: Required. Start with failing Layer 4 packet validation and title/body generation fixtures before implementation.

**Reviewability**: PRSG-012 stays within the reviewability block threshold with a bounded total-file warning. Keep production/reference changes centered on the shared packet schema, validator, PR body generation, PR emission, and mirrored autopilot guidance. If implementation exceeds 800 reviewable LOC, 8 production files, 25 total files, or more than one primary surface without a ratified exception, stop and split before adding more tasks.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different scripts/fixtures/files and has no dependency on an incomplete task
- **[Story]**: Which user story the task maps to, using [US1], [US2], [US3], or [US4]
- Every task includes exact file paths

## Phase 1: Foundation - Contract, Fixtures, and Validator Skeleton

**Purpose**: Establish the packet contract shape and failing Layer 4 evidence before changing runtime behavior.

- [x] T001 Create failing valid single-packet Layer 4 fixtures in `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/valid-single.json` and `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/bodies/valid-single.md`
- [x] T002 Create failing valid split-packet Layer 4 fixtures in `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/valid-split.json` and `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/bodies/valid-split.md`
- [x] T003 Create failing invalid packet fixtures in `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-title-token.json`, `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-missing-evidence.json`, and `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-malformed-json.json`, covering title/body stale placeholders, unexpanded variables, hidden template comments, example text, schema-invalid shape, and banned labels
- [x] T004 Add failing validator fixture assertions for pass, validation failure, and input error cases in `tests/speckit-pro/layer4-scripts/test-validate-pr-packet.sh`
- [x] T005 Add failing title/body generation assertions for generated packet metadata and rendered body paths in `tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh`
- [x] T006 Add failing PR emission command assertions for `gh pr create --base`, `--head`, `--title`, and `--body-file` in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`
- [x] T007 Copy the planned packet schema into the shared runtime contract at `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`
- [x] T008 Create the executable validator skeleton with input parsing, deterministic exit-code branches, and JSON output path handling in `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh`
- [x] T009 Verify the reviewability budget against the planned file scope and record any split decision in `specs/prsg-012-reviewer-ready-pr-packet-contract/tasks.md`

**Checkpoint**: Layer 4 fixtures cover the validator, generated title/body packet fields, and PR create command arguments. The PR branch must stay green before review.

## Phase 2: User Story 1 - Specific Conventional PR Titles (Priority: P1) MVP

**Goal**: Single-PR and split-PR packets own specific conventional titles, and PR creation uses those generated titles.

**Independent Test**: Run the Layer 4 generation and emission tests, then inspect the rendered packet titles and mocked `gh pr create` invocations for conventional, public-readable `--title` values.

### Tests for User Story 1

- [ ] T010 [US1] Extend title fixtures for branch/spec/slice-token rejection and explicit metadata-only type/scope override validation in `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-title-token.json`
- [ ] T011 [US1] Assert single-PR generated title metadata defaults to `feat(speckit-pro):` in `tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh`
- [ ] T012 [US1] Assert split-PR `gh pr create` calls include packet target values through `--base`/`--head`, packet title values through `--title`, and rendered body files through `--body-file` in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`

### Implementation for User Story 1

- [ ] T013 [US1] Generate single-PR `generated_title` metadata from the feature display title in `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh`
- [ ] T014 [US1] Generate split-PR `generated_title` metadata from marker source boundaries or layer-plan increment names in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- [ ] T015 [US1] Implement conventional title validation, explicit metadata-only type/scope override validation, and banned-token rejection in `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh`
- [ ] T016 [US1] Pass generated packet target, title, and body values to split PR creation with `gh pr create --base --head --title --body-file` in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- [ ] T017 [US1] Update single-PR creation guidance to use generated packet target, title, and body values in `speckit-pro/skills/speckit-autopilot/references/post-implementation.md`

**Checkpoint**: US1 is complete when packet title fixtures pass and no PR creation path derives titles from branch names, spec IDs, slice IDs, task IDs, file paths, or body prose.

## Phase 3: User Story 2 - Structured Reviewer Body (Priority: P1)

**Goal**: Render canonical reviewer sections, required source markers, scope and verification evidence, Known Gaps, and the literal `## UAT Runbook` compatibility heading.

**Independent Test**: Render a valid packet body and confirm the required headings, source markers, UAT compatibility heading, verification evidence, scope evidence, and banned-label rejection in Layer 4.

### Tests for User Story 2

- [ ] T018 [US2] Add body heading order, source marker, UAT, traceability, verification, scope, and Known Gaps assertions in `tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh`
- [ ] T019 [US2] Add validator assertions for missing, duplicated, and out-of-order headings; headings satisfied only by packet JSON, host template content, code fences, comments, generated fixtures, `.process` files, or generated zones; stale placeholders; unexpanded variables; example text; banned labels; missing source markers; missing traceability mappings; missing verification evidence; and missing scope evidence in `tests/speckit-pro/layer4-scripts/test-validate-pr-packet.sh`
- [ ] T020 [P] [US2] Add body fixture coverage for required canonical sections, traceability mappings, UAT compatibility, and source/verification/scope evidence in `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/bodies/valid-single.md`

### Implementation for User Story 2

- [ ] T021 [US2] Render `Summary`, `What Changed`, `Why It Matters`, `How To Review`, `How To UAT`, `Verification`, `Scope`, and `Known Gaps` in stable order in `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh`
- [ ] T022 [US2] Preserve the literal `## UAT Runbook` compatibility heading and UAT source evidence in `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh`
- [ ] T023 [US2] Render source markers, traceability mappings, verification evidence, scope evidence, non-goals, and known-gap language in `speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md`
- [ ] T024 [US2] Validate canonical body heading order and canonical-block ownership, stale placeholders, unexpanded variables, example text, banned labels, source markers, traceability mappings, verification evidence, scope evidence, and UAT compatibility in `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh`

**Checkpoint**: US2 is complete when valid rendered bodies pass and missing or stale reviewer evidence blocks before PR creation.

## Phase 4: User Story 3 - Pre-create Validation Block (Priority: P1)

**Goal**: Every PR creation path validates the rendered packet before `gh pr create`, blocks invalid packets, writes deterministic evidence, and preserves split-PR resume state.

**Independent Test**: Run packet validation against valid and invalid fixtures for single-PR and split-PR modes, then confirm invalid packets make zero mocked `gh pr create` attempts and write packet-specific evidence.

### Tests for User Story 3

- [ ] T025 [US3] Add input-error fixture arguments for missing, unreadable, directory-valued, invalid-JSON, schema-invalid, and no-feature-dir packet inputs in `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-missing-packet.args`
- [ ] T026 [US3] Add split partial-failure resume fixture in `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/split-partial-failure-state.json`
- [ ] T027 [US3] Assert deterministic validation JSON, stdout `input_error` envelopes with `no-path` when no feature directory can be derived, stderr lines, exit codes, zero `gh pr create` attempts, deterministic workflow event ids, and workflow event supersede behavior in `tests/speckit-pro/layer4-scripts/test-validate-pr-packet.sh`
- [ ] T028 [US3] Assert split PR emission validates before each slice PR, blocks invalid packets, preserves prior PR evidence, ignores stale failed validation records as authorization, and does not duplicate earlier PRs in `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`

### Implementation for User Story 3

- [ ] T029 [US3] Write validation results under `specs/prsg-012-reviewer-ready-pr-packet-contract/.process/pr-packets/<packet_id>/validation.json` from `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh`, or emit the same `input_error` JSON envelope to stdout with `validation_result_path: "no-path"` when no target feature directory can be derived
- [ ] T030 [US3] Emit deterministic failed-run stderr lines and distinguish `validation_failure` exit `1` from `input_error` exit `2`, including the `validation_result_path_or_no-path` field, in `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh`
- [ ] T031 [US3] Append or supersede blocking workflow events with deterministic event ids in `docs/ai/specs/.process/PRSG-012-workflow.md` from `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh`
- [ ] T032 [US3] Invoke `validate-pr-packet.sh` before each split `gh pr create --base --head --title --body-file` call in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- [ ] T033 [US3] Preserve `.process/prs.json`, Spec MOC PRS table, workflow evidence, and `autopilot-state.json` references during split partial failure handling, then reconcile existing PR records before retry so corrected packets cannot duplicate earlier PRs, in `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- [ ] T034 [US3] Update single-PR post-implementation guidance to require current packet validation before `gh pr create --base --head --title --body-file` and to use only newly passed validation results in `speckit-pro/skills/speckit-autopilot/references/post-implementation.md`

**Checkpoint**: US3 is complete when all invalid packets block before PR creation and valid packets are the only path to `gh pr create --base --head --title --body-file`.

## Phase 5: User Story 4 - Safe Prose Refinement (Priority: P2)

**Goal**: Maintainers can edit sanctioned narrative fields while protected governance sections, evidence, UAT, traceability, scope, and verification remain validator-protected.

**Independent Test**: Edit only sanctioned prose fields and confirm validation passes, then edit protected generated content and confirm validation fails with exact invariant evidence.

### Tests for User Story 4

- [ ] T035 [US4] Add sanctioned prose edit fixture coverage in `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/bodies/valid-single-edited.md`
- [ ] T036 [US4] Add protected edit rejection fixture in `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-protected-edit.json`
- [ ] T037 [US4] Assert editable boundary comments, protected fingerprint elision, unknown comment rejection, stale template comment rejection, and host template coexistence outside the protected canonical packet block in `tests/speckit-pro/layer4-scripts/test-validate-pr-packet.sh`

### Implementation for User Story 4

- [ ] T038 [US4] Render exact full-line editable marker pairs for `summary`, `what_changed`, and `why_it_matters` in `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh`
- [ ] T039 [US4] Store editable field metadata and protected body fingerprints with editable blocks elided in `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh`
- [ ] T040 [US4] Reject protected body changes, malformed editable boundaries, unknown HTML comments, stale template comments, and host template interference in `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh`
- [ ] T041 [US4] Document sanctioned editable fields and protected governance limits in `speckit-pro/skills/speckit-autopilot/references/post-implementation.md`

**Checkpoint**: US4 is complete when sanctioned prose edits pass and protected evidence edits fail with deterministic remediation evidence.

## Phase 6: Polish - Functional Evals, Replay, Parity, and Docs

**Purpose**: Update higher-layer evidence and mirrored guidance after the runtime and Layer 4 contract pass.

- [ ] T042 [P] Update Claude Code Layer 3 functional eval expectations for generated title/body, explicit `--base --head --title --body-file`, pre-create validation, and no post-create repair fallback in `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json`
- [ ] T043 [P] Update Codex Layer 3 functional eval expectations for generated title/body, explicit `--base --head --title --body-file`, pre-create validation, and no post-create repair fallback in `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`
- [ ] T044 Update Layer 7 replay fixture ordering for split PR packet validation before each slice PR in `tests/speckit-pro/layer7-integration/dispatch-fixtures/18-post-impl-parallel-subagents/prompt.txt`
- [ ] T045 Update Layer 7 replay expected packet validation evidence in `tests/speckit-pro/layer7-integration/dispatch-fixtures/18-post-impl-parallel-subagents/expected.json`
- [ ] T046 [P] Update Layer 7 replay documentation for reviewer-ready packet validation in `tests/speckit-pro/layer7-integration/dispatch-fixtures/18-post-impl-parallel-subagents/README.md`
- [ ] T047 Update Layer 7 parser fixture evidence for packet validation before PR creation in `tests/speckit-pro/layer7-integration/dispatch-fixtures/18-post-impl-parallel-subagents/parser-fixture.jsonl`
- [ ] T048 Update Layer 8 parity workflow expectations for mirrored autopilot guidance, explicit PR target/title/body arguments, and pre-create validation ordering in `tests/speckit-pro/layer8-parity/01-post-impl-parity/workflow.md`
- [ ] T049 Update Layer 8 parity expected equivalence for shared schema and validator references, no duplicate Codex validator/schema copies, and no post-create repair fallback in `tests/speckit-pro/layer8-parity/01-post-impl-parity/expected-equivalence.json`
- [ ] T050 [P] Update Layer 8 parity documentation and tolerance notes in `tests/speckit-pro/layer8-parity/01-post-impl-parity/README.md` and `tests/speckit-pro/layer8-parity/01-post-impl-parity/tolerance.json`
- [ ] T051 Update primary autopilot guidance for packet generation, validation, and PR creation behavior in `speckit-pro/skills/speckit-autopilot/SKILL.md`
- [ ] T052 Update Codex mirrored autopilot guidance without duplicating schema or validator copies in `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
- [ ] T053 Update Codex post-implementation reference for packet validation parity in `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md`
- [ ] T054 Run structural validation through `bash tests/speckit-pro/run-all.sh --layer 1` using `tests/speckit-pro/run-all.sh`
- [ ] T055 Run Layer 4 script validation through `bash tests/speckit-pro/run-all.sh --layer 4` using `tests/speckit-pro/run-all.sh`
- [ ] T056 Run default deterministic verification through `bash tests/speckit-pro/run-all.sh` using `tests/speckit-pro/run-all.sh`

**Checkpoint**: Polish is complete when Layer 3, Layer 7, Layer 8, primary guidance, Codex guidance, and deterministic verification all reflect the same packet contract.

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Foundation**: No dependencies. Start here and make Layer 4 fixtures fail first.
- **US1, US2, US3**: Depend on Phase 1. They are all P1, but execution should follow US1 title metadata, US2 body rendering, then US3 pre-create validation wiring because each layer feeds the next.
- **US4**: Depends on US2 body rendering and US3 validator behavior.
- **Polish**: Depends on selected user stories and passing Layer 4 evidence.

### User Story Dependencies

- **US1 (P1)**: Requires validator skeleton and packet schema from Phase 1.
- **US2 (P1)**: Requires packet schema and body fixture baseline from Phase 1.
- **US3 (P1)**: Requires US1 title values and US2 body files so validation can gate actual PR creation inputs.
- **US4 (P2)**: Requires US2 canonical body blocks and US3 validator output behavior.

### Within Each User Story

- Write or update failing fixtures and tests before implementation.
- Generate packet metadata before validating it.
- Render body files before validating rendered body content.
- Validate packets before `gh pr create`.
- Update guidance after runtime behavior is fixture-backed.

## Parallel Opportunities

- T020 can run while T018 and T019 are in progress because it only edits the valid body fixture, not the shared test scripts.
- T042 and T043 can run in parallel because they update separate Claude Code and Codex Layer 3 eval files.
- T046 can run in parallel with T044/T045/T047 after the Layer 7 behavior is agreed because it updates only the README.
- T050 can run in parallel with T048/T049 after the Layer 8 parity behavior is agreed because it updates documentation and tolerance files.

## Parallel Example: Higher-layer Evidence

```bash
Task: "Update Claude Code Layer 3 functional eval expectations for generated title/body, explicit --base/--head/--title/--body-file use, and pre-create validation in tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json"
Task: "Update Codex Layer 3 functional eval expectations for generated title/body, explicit --base/--head/--title/--body-file use, and pre-create validation in tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 Foundation.
2. Complete US1 for generated packet-owned titles.
3. Validate US1 independently with Layer 4 title/body and emission assertions.

### Incremental Delivery

1. Add US2 canonical body rendering and evidence validation.
2. Add US3 pre-create validation gating and deterministic evidence.
3. Add US4 safe prose refinement protections.
4. Finish Polish evidence and mirrored guidance.

### Verification

1. Run `bash tests/speckit-pro/run-all.sh --layer 1`.
2. Run `bash tests/speckit-pro/run-all.sh --layer 4`.
3. Run `bash tests/speckit-pro/run-all.sh`.

## Notes

- `[P]` appears only where tasks do not touch the same script or fixture.
- The shared validator and packet schema stay under `speckit-pro/skills/speckit-autopilot/`.
- Codex-facing guidance references the shared primary schema and validator; it must not introduce duplicate copies.
- Post-create PR auto-repair remains out of scope for PRSG-012.
- Foundation reviewability checkpoint: `reviewability-gate.sh tasks specs/prsg-012-reviewer-ready-pr-packet-contract` still reports the recorded size-only task-plan block (`reviewable_loc=2240`, `total_files=73`). Atomicity remains `one-navigable-PR`; no split layer plan is required, and marker-plan evidence remains the downstream PR preparation path.
