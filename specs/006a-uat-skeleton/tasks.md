---
description: "Task list for SPEC-006a: Deterministic UAT Runbook Skeleton + PR Body Integration"
---

# Tasks: Deterministic UAT Runbook Skeleton + PR Body Integration

**Input**: Design documents from `specs/006a-uat-skeleton/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), contracts/generate-uat-skeleton-cli.md, quickstart.md

**Tests**: TDD-first (bash flavor) is REQUIRED for this feature. For every `generate-uat-skeleton.sh` behavior, a Layer 4 assertion is added (RED — must fail) BEFORE the script logic that satisfies it (GREEN). Test command throughout: `cd speckit-pro && bash tests/run-all.sh --layer 4`.

**Reviewability**: Budget is ~670 reviewable LOC, 4 production files (`generate-uat-skeleton.sh`, `uat-runbook-template.md`, modified `generate-pr-body.sh`, `test-generate-uat-skeleton.sh`), 11 total files (incl. vendored fixture + lockstep Codex/reference doc edits). All counts are under the 800 LOC / 8 production-file / 25 total-file block thresholds. A reviewability checkpoint task (T006) records the budget before any implementation begins. Do not expand past budget — split into SPEC-006b instead.

**Organization**: Tasks are grouped by user story (US1-US4) to enable independent implementation and testing. The single shared script `generate-uat-skeleton.sh` is touched by US1-US4, so its implementation tasks are sequential (not `[P]`); each story's Layer 4 assertion is independent and the RED→GREEN order holds within the story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

This is a **Claude Code plugin marketplace** (not a single-project app). All paths are relative to the repo root (the worktree `.worktrees/006a-uat-skeleton/`). Production code lives under `speckit-pro/skills/speckit-autopilot/`; tests under `speckit-pro/tests/layer4-scripts/`. There is NO `scripts/` or `templates/` dir under `speckit-pro/codex-skills/speckit-autopilot/` — the Codex variant invokes the single shared script by its `skills/...` path (see plan.md "Codex Parity"). NO task touches `speckit-pro/agents/` or `speckit-pro/codex-agents/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the baseline is green and the reuse target is where the plan pinned it, before any file is created.

- [x] T001 Confirm baseline green and reviewability preset resolves: `cd speckit-pro && bash tests/run-all.sh --layer 1` exits 0, and `specify preset resolve tasks-template` shows the `speckit-pro-reviewability` top layer. Confirm `jq` is on PATH.
- [x] T002 Re-verify the reuse target for FR-002 (Decision 1): confirm `extract_heading_section()` is still defined at `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` lines 45-65 (open at L45, close `}` at L65) and that `grep -n 'BASH_SOURCE' speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` returns zero matches (no source guard → copy verbatim, do not source). Record the confirmed line range as a note for T007.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the fixture directory + vendored snapshot, the empty template scaffold, and the empty Layer 4 test harness — the shared substrate every user-story RED assertion and the template-driven script will write into.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete (US1-US4 RED tests land in the T005 harness; the script renders against the T004 template; SC-001/the full-spec fixture reads T003).

- [x] T003 [P] Create the fixtures directory and vendor the full-spec snapshot: `mkdir -p speckit-pro/tests/layer4-scripts/fixtures` then copy `specs/004-integration-verification/spec.md` (from the parent repo) to `speckit-pro/tests/layer4-scripts/fixtures/spec-full-snapshot.md` as a frozen copy (FR-015, design concept Q4 — fixture data, never read live). The snapshot MUST contain `### User Story` headings so SC-001's `grep -c '^### User Story'` parity check is exercisable.
- [x] T004 [P] Scaffold the empty template file `speckit-pro/skills/speckit-autopilot/templates/uat-runbook-template.md` with the eight section headers in the fixed order required by FR-010 (Header, Env Setup, Per-Story Acceptance Tests, FR Coverage Matrix, Negative-Path Tests, Self-Review Findings, Sign-off, Rollback) and a leading provenance comment. Section bodies are filled by the script in later phases; this task only fixes the section order and headers.
- [x] T005 [P] Scaffold the empty Layer 4 test harness `speckit-pro/tests/layer4-scripts/test-generate-uat-skeleton.sh`: strict-mode shebang (`#!/usr/bin/env bash`, `set -euo pipefail`), source `tests/lib/assertions.sh`, set up the `mktemp -d` + `trap` cleanup pattern (copied from `test-ensure-reviewability-preset.sh`), resolve `SCRIPT_UNDER_TEST` to `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh`, and end with `test_summary`. No assertions yet — RED assertions are added per-story in Phases 3-7. File is auto-discovered by `tests/run-all.sh --layer 4`.
- [x] T006 Verify the reviewability budget against the planned task/file scope and record the split decision: confirm the change stays at 4 production files / ~670 LOC / 11 total files (within the 800/8/25 block thresholds per plan.md Reviewability Budget), and that no task adds files under `speckit-pro/agents/` or `speckit-pro/codex-agents/`. Record "remains one spec; LLM test prose + author agents deferred to SPEC-006b" before implementation begins.

**Checkpoint**: Foundation ready — fixture vendored, template scaffolded, test harness in place, budget recorded. User story implementation can now begin.

---

## Phase 3: User Story 1 - Reviewer sees a UAT Runbook in the PR body (Priority: P1) 🎯 MVP

**Goal**: A reviewer opens the PR description and sees a `## UAT Runbook` section listing every user story from the spec with checkbox steps — full content embedded inline when the runbook is under 50,000 chars, an excerpt + link otherwise.

**Independent Test**: Run `generate-uat-skeleton.sh` against the vendored full-spec snapshot (which has user stories), then run `generate-pr-body.sh` for that feature dir; confirm the PR body contains a `## UAT Runbook` (H2) heading with one acceptance-test block per user story. Delivers value even if US2-US4 are unbuilt.

### Tests for User Story 1 (RED — write FIRST, must FAIL before implementation) ⚠️

- [x] T007 [US1] Add RED assertions to `speckit-pro/tests/layer4-scripts/test-generate-uat-skeleton.sh` against the vendored `fixtures/spec-full-snapshot.md`: (a) script exits 0; (b) output runbook exists (`assert_file_exists`); (c) every `### User Story` in the fixture appears as a Per-Story Acceptance Test block (count parity with `grep -c '^### User Story' fixtures/spec-full-snapshot.md` — SC-001); (d) all eight FR-010 section headers are present in fixed order; (e) the FR Coverage Matrix contains a deterministic anchor link per story (Decision 4). Run `cd speckit-pro && bash tests/run-all.sh --layer 4` and confirm these FAIL (script does not yet exist). Covers FR-001, FR-010, SC-001.
- [x] T008 [US1] Add RED assertions for the size-aware PR-body embed to `speckit-pro/tests/layer4-scripts/test-generate-pr-body.sh` (extend the existing test): (a) when `<feature-dir>/uat-runbook.md` is present and under 50,000 chars, the generated PR body contains the literal `## UAT Runbook` (H2) heading followed by the full runbook content (`cat`, blank lines preserved — Decision 2); (b) when the runbook is at/over 50,000 chars, the body contains `## UAT Runbook` + the first 60 lines (`head -60`) + a relative link `[Full runbook](./uat-runbook.md)`; (c) when the runbook is absent, the body still contains the `## UAT Runbook` heading plus a one-line stub note (fail-open). Run Layer 4 and confirm these FAIL. Covers FR-013, SC-005.

### Implementation for User Story 1

- [x] T009 [US1] Create `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh` (strict mode `#!/usr/bin/env bash` + `set -euo pipefail`; quoted vars; `local`-scoped functions; `[[ ]]` over `[ ]`). Implement: argv parsing (`argv[1]`=spec path, `argv[2]`=output path; feature dir via `dirname "$argv[1]"`; no extra positionals); the copied-verbatim `extract_heading_section()` from `generate-pr-body.sh` L45-65 with the provenance comment `# Copied verbatim from generate-pr-body.sh lines 45-65 (FR-002). Keep in sync if that helper changes.`; parse `### User Story N - <Title> (Priority: PN)` headings and `- **FR-NNN**:` / `- **SC-NNN**:` bullets (nested/multi-line bullets reproduced verbatim as indented continuation lines). Render Header + Env Setup + Per-Story Acceptance Tests + FR Coverage Matrix (with explicit script-emitted anchors per Decision 4) against `uat-runbook-template.md`. Make T007 GREEN. Covers FR-001, FR-002, FR-010.
- [x] T010 [US1] Fill the `uat-runbook-template.md` (`speckit-pro/skills/speckit-autopilot/templates/uat-runbook-template.md`) Header (spec ID, branch, static PR placeholder `**PR:** <set on PR open>` per FR-011, generation timestamp), Env Setup, Per-Story Acceptance Tests, and FR Coverage Matrix section bodies so the script's render in T009 produces a complete runbook. Covers FR-010, FR-011.
- [x] T011 [US1] Modify `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` to add a **dedicated, size-aware `## UAT Runbook` block** per plan.md "FR-013 Wiring": emit the literal `## UAT Runbook` at **H2**; do NOT add it to the line-171 `for heading in ...` loop and do NOT route it through `append_missing_section()`/`extract_heading_section()` (those truncate at 40 lines and strip blanks). Read `"$FEATURE_DIR/uat-runbook.md"`: if absent, emit the heading + a one-line stub note and continue (fail-open); if present, `size=$(wc -c < ...)` — when `size -lt 50000`, `cat` the full file (Decision 2); else `head -60` + `[Full runbook](./uat-runbook.md)`. Append the block after the `for heading` loop (~L173) and before the trailing HTML comment (L175-182), so it lands once. Make T008 GREEN. Covers FR-013, SC-005.

**Checkpoint**: US1 fully functional — a spec with user stories produces a runbook embedded as `## UAT Runbook` in the PR body. This is the MVP.

---

## Phase 4: User Story 2 - Reviewer of an infrastructure spec sees an FR/SC-keyed runbook (Priority: P1)

**Goal**: A spec with zero `### User Story` headings still produces a runbook — keyed by FR-NNN and SC-NNN with a header note explaining the fallback. Generation is never silently skipped.

**Independent Test**: Run the script against a synthetic spec with zero `### User Story` headings; confirm the runbook contains the FR/SC fallback header note plus at least one FR-keyed and one SC-keyed test section, and the script exits 0.

### Tests for User Story 2 (RED — write FIRST, must FAIL before implementation) ⚠️

- [x] T012 [US2] Add RED assertions to `speckit-pro/tests/layer4-scripts/test-generate-uat-skeleton.sh` using an inline `mktemp` synthetic zero-stories spec (populated `### Functional Requirements` + `### Measurable Outcomes`, no `### User Story`): (a) script exits 0 (generation never skipped); (b) runbook contains the fallback header note (e.g., "This spec has no user stories; tests are keyed by FR/SC."); (c) runbook contains at least one FR-keyed and one SC-keyed test section (SC-002). Run Layer 4 and confirm FAIL. Covers FR-003, SC-002.

### Implementation for User Story 2

- [x] T013 [US2] Extend `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh` with the zero-user-stories branch: when no `### User Story` headings are found, emit the fallback header note and key the Per-Story section by FR-NNN/SC-NNN instead; MUST NOT skip generation or exit nonzero. Make T012 GREEN. Covers FR-003.

**Checkpoint**: US1 AND US2 both work independently — both spec shapes (with and without user stories) produce a runbook.

---

## Phase 5: User Story 3 - Autopilot resume regenerates the runbook deterministically (Priority: P2)

**Goal**: On each autopilot resume the runbook regenerates deterministically from current spec state — no merge with prior reviewer hand-edits, no stale content, no skip-if-present.

**Independent Test**: Run the script twice against the same spec and confirm the two output files are byte-identical; hand-edit the runbook between runs and confirm the second run overwrites it without merging.

### Tests for User Story 3 (RED — write FIRST, must FAIL before implementation) ⚠️

- [x] T014 [US3] Add RED assertions to `speckit-pro/tests/layer4-scripts/test-generate-uat-skeleton.sh`: (a) run the script twice against the vendored `fixtures/spec-full-snapshot.md` to two output paths and assert the two files are byte-identical (`diff` / `assert_eq` on contents — FR-007); (b) write a sentinel hand-edit line into an existing runbook, re-run, and assert the sentinel is gone (overwrite, no merge/append/skip). Run Layer 4 and confirm FAIL. Covers FR-007.

### Implementation for User Story 3

- [x] T015 [US3] Ensure `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh` writes `argv[2]` via unconditional deterministic overwrite (truncate-and-write; no append, no skip-if-present, no `--force` flag — YAGNI per contract). Confirm output is timestamp-stable or that any timestamp is fixed/derived so two runs against an unchanged spec are byte-identical. Make T014 GREEN. Covers FR-007.

**Checkpoint**: US1, US2, US3 independently functional — resume idempotency holds.

---

## Phase 6: User Story 4 - Self-Review findings echoed for offline review (Priority: P2)

**Goal**: A maintainer reading the runbook from a clone sees the Self-Review findings echoed in (extracted from the workflow file at the `## Self-Review` heading) so the runbook is self-contained offline. Standalone runs (no workflow file) degrade to a graceful stub.

**Independent Test**: Run with `--workflow-file` pointing at a file that has a `## Self-Review` heading; confirm the runbook's Self-Review Findings section contains the echoed block. Run without the flag; confirm a graceful stub line appears and the script still succeeds.

### Tests for User Story 4 (RED — write FIRST, must FAIL before implementation) ⚠️

- [x] T016 [US4] Add RED assertions to `speckit-pro/tests/layer4-scripts/test-generate-uat-skeleton.sh`: (a) with `--workflow-file` pointing at an inline `mktemp` file containing a `## Self-Review` section, the runbook's Self-Review Findings section contains the extracted block (via the copied `extract_heading_section()`); (b) with the flag absent OR the file lacking a `## Self-Review` heading, the section emits the stub line `**Self-Review:** <not available — workflow file not provided>` and the script still exits 0. Run Layer 4 and confirm FAIL. Covers FR-009.

### Implementation for User Story 4

- [x] T017 [US4] Extend `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh` with the optional `--workflow-file <path>` flag: when supplied, extract the `## Self-Review` block via the copied `extract_heading_section()` helper and echo it into the Self-Review Findings section; when absent/unreadable/heading-missing, emit the graceful stub and still exit 0. Make T016 GREEN. Covers FR-009.

**Checkpoint**: All four user stories independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Remaining FRs that span stories (PROJECT_COMMANDS formatter, Rollback, clarification-marker propagation, duplicate-ID + missing-spec error paths), the remaining edge-case fixtures (FR-015 coverage), Codex/reference lockstep doc edits (FR-014), and final verification of every SC.

### Cross-cutting script behaviors (each RED before GREEN)

- [x] T018 Add RED assertions then implement the `UAT_PROJECT_COMMANDS` Env Setup formatter (FR-008): assertions in `test-generate-uat-skeleton.sh` for (a) unset → `<unknown — autopilot did not pass PROJECT_COMMANDS>` placeholders; (b) set-but-malformed JSON → same placeholders (fail-soft, no crash); (c) a key present with literal `N/A` renders as unavailable, distinct from the unset placeholder. Then implement the formatter in `generate-uat-skeleton.sh` (pure `jq` formatter over the `BUILD`/`TYPECHECK`/`LINT`/`LINT_FIX`/`UNIT_TEST`/`INTEGRATION_TEST`/`SINGLE_FILE_INTEGRATION` key set; MUST NOT re-run `detect-commands.sh`) and the Env Setup template body in `uat-runbook-template.md`. Make GREEN. Covers FR-008.
- [x] T019 Add RED assertion then implement the Rollback section (FR-012) in `generate-uat-skeleton.sh` + `uat-runbook-template.md`: assertion for (a) a spec/plan with a `## Rollback` heading → that block is extracted (spec first, `plan.md` in the same feature dir as fallback); (b) neither has it → synthesized stanza `git revert <SHA>; see plan.md for data-migration considerations`. Make GREEN. Covers FR-012.
- [x] T020 Add RED assertion then implement clarification-marker propagation (FR-005) in `generate-uat-skeleton.sh`: using an inline `mktemp` spec whose US/FR/SC/Edge bullet carries a `NEEDS CLARIFICATION` marker (bare and colon-question forms — fixed-string `grep -F`, Decision 3), assert the runbook reproduces that bullet with an unresolved-clarification annotation (e.g., `**WARN:** unresolved clarification`) rather than dropping it; propagation scoped to parsed bullets only. Make GREEN. Covers FR-005.
- [x] T021 Add RED assertions then implement the duplicate-ID + exit-code/stdout behaviors (FR-004, FR-006) in `generate-uat-skeleton.sh`: (a) inline `mktemp` duplicate-FR spec → first-seen entry kept and a plain unprefixed stderr line names the duplicated ID (assert stderr content, exit 0); (b) wrong/missing argv → exit 2; (c) missing/unreadable spec → exit 1 with NO partial runbook written; (d) silent stdout on success (assert empty stdout). Make GREEN. Covers FR-004, FR-006.

### Remaining Layer 4 fixtures (FR-015 — five-fixture coverage)

- [x] T022 Confirm `test-generate-uat-skeleton.sh` exercises all five FR-015 fixtures end to end: vendored full-spec snapshot (T007), synthetic zero-stories (T012), synthetic duplicate-FR (T021), synthetic `NEEDS CLARIFICATION` marker (T020), and missing-spec error case (T021). Add any not yet present. Run `cd speckit-pro && bash tests/run-all.sh --layer 4` and confirm exit 0 (SC-003). Covers FR-015, SC-003.

### Codex + reference lockstep doc edits (FR-014 — land in the SAME commit as the CC edits)

> The new script and template are single-copy under `skills/`; the Codex variant invokes them by path. The lockstep surface is the SKILL.md + three reference doc twins ONLY. Do NOT create `scripts/` or `templates/` under `codex-skills/`. Do NOT touch `agents/` or `codex-agents/`.

- [x] T023 Update Claude Code autopilot docs to reference the new UAT skeleton step: (a) `speckit-pro/skills/speckit-autopilot/SKILL.md` — add `generate-uat-skeleton.sh` to the Step 3 / script-inventory reference; (b) `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` — add the new UAT-generation step (invoke `generate-uat-skeleton.sh` fail-open after Self-Review, before PR-body generation, passing `--workflow-file` and `UAT_PROJECT_COMMANDS`); (c) `speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` — bump the task-count entry 12 → 13. Covers FR-014.
- [x] T024 [P] Mirror the T023 edits into the Codex twins (same content, runtime-appropriate primitives): (a) `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`; (b) `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md`; (c) `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md`. The Codex post-implementation step invokes the shared `skills/.../scripts/generate-uat-skeleton.sh` by path. Land in the same commit as T023. Covers FR-014. `[P]` against T023 (different files); content must match T023.

### Final verification (every SC mapped to a command)

- [x] T025 Run shellcheck + `bash -n` on `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh` and the modified `generate-pr-body.sh`; resolve all findings (constitution Principle II, shellcheck-clean CI gate).
- [x] T026 Standalone smoke (SC-001): `UAT_PROJECT_COMMANDS='{"BUILD":"make","UNIT_TEST":"make test"}' bash speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh specs/004-integration-verification/spec.md /tmp/smoke-runbook.md` — confirm the runbook contains every user story (`grep -c '^### User Story'` parity). Covers SC-001.
- [x] T027 Run the full verification gate: `cd speckit-pro && bash tests/run-all.sh --layer 4` exits 0 (SC-003), `bash tests/run-all.sh --layer 1` exits 0 (SC-004 — Codex parity preserved, no new agent files), and the default `bash tests/run-all.sh` (L1+L4+L5) exits 0. Confirm `git diff --name-only` includes NO path under `speckit-pro/agents/` or `speckit-pro/codex-agents/`. Covers SC-003, SC-004.
- [x] T028 Generate/update the PR review packet (what changed, why, non-goals → SPEC-006b, review order, scope budget ~670 LOC/4 prod/11 total, traceability FR-001..015 + SC-001..005, verification evidence, known gaps, rollback). Confirm SC-005 path is documented for post-merge autopilot smoke (a real autopilot PR after merge shows `## UAT Runbook` + committed `uat-runbook.md`). Conventional Commits + plain-English public-readable per CLAUDE.md. Covers SC-005.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately (T001, T002 verify baseline + reuse target).
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS all user stories. T003/T004/T005 are `[P]` (different files); T006 (budget) gates implementation start.
- **User Stories (Phases 3-6)**: All depend on Foundational. US1 (P1) is the MVP. Because all four stories edit the single shared `generate-uat-skeleton.sh`, their implementation tasks run **sequentially** (US1 → US2 → US3 → US4), not in parallel; the per-story RED test always precedes the story's GREEN impl.
- **Polish (Phase 7)**: Cross-cutting script behaviors (T018-T021) depend on the script existing (T009). Codex/reference lockstep (T023/T024) depends on the script + template being final. Final verification (T025-T028) depends on everything.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational. The script's first slice + template bodies + PR-body wiring. No dependency on other stories.
- **US2 (P1)**: Adds the zero-stories branch to the script created in US1 (T013 depends on T009).
- **US3 (P2)**: Hardens the script's write path (T015 depends on T009).
- **US4 (P2)**: Adds the `--workflow-file` flag to the script (T017 depends on T009).

### Within Each User Story (TDD-first, bash flavor)

- The Layer 4 RED assertion (must FAIL) is written and run BEFORE the script logic that makes it GREEN.
- Then REFACTOR while green; no new abstractions unless a second call site exists.
- Test command throughout: `cd speckit-pro && bash tests/run-all.sh --layer 4`.

### Parallel Opportunities

- **Foundational**: T003 (fixture), T004 (template scaffold), T005 (test harness) are `[P]` — three different files.
- **Polish cross-cutting**: T018 (Env Setup), T019 (Rollback), T020 (clarification markers), T021 (duplicate-ID + exit codes) all edit the shared `generate-uat-skeleton.sh`, so they are NOT `[P]` — they run sequentially like the US1-US4 script slices.
- **Codex lockstep**: T024 (`-codex.md` doc twins) is `[P]` against T023 (CC doc edits) — different files — but its content must match T023 and both land in the same commit (Layer 1 parity).
- The single shared `generate-uat-skeleton.sh` is NOT parallel-safe across stories — US1-US4 impl tasks (T009, T013, T015, T017) are sequential.

---

## Parallel Example: Foundational Phase

```bash
# Launch the three foundational scaffolds together (different files, no deps):
Task: "T003 Vendor fixtures/spec-full-snapshot.md from specs/004 spec.md"
Task: "T004 Scaffold uat-runbook-template.md with 8 section headers in fixed order"
Task: "T005 Scaffold test-generate-uat-skeleton.sh harness (strict mode + assertions.sh + mktemp/trap)"
```

## Parallel Example: Codex Lockstep (same commit)

```bash
# CC doc edits and their Codex twins are different files — edit in parallel, commit together:
Task: "T023 Update CC SKILL.md + post-implementation.md + task-list-canonical.md"
Task: "T024 Mirror into codex SKILL.md + post-implementation-codex.md + task-list-canonical-codex.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (baseline green, reuse target pinned).
2. Complete Phase 2: Foundational (fixture + template scaffold + test harness + budget).
3. Complete Phase 3: User Story 1 (script slice + template bodies + PR-body wiring).
4. **STOP and VALIDATE**: run `cd speckit-pro && bash tests/run-all.sh --layer 4`; confirm `## UAT Runbook` renders for a spec with stories.

### Incremental Delivery

1. Setup + Foundational → substrate ready.
2. US1 → MVP (runbook in PR body for story-bearing specs).
3. US2 → infra specs covered (FR/SC fallback).
4. US3 → resume idempotency.
5. US4 → Self-Review echo.
6. Polish → cross-cutting FRs, remaining fixtures, Codex/reference lockstep, full verification.

### Single-Developer Note

This feature is one shared script + one template + one PR-body edit + one test file, so most implementation is inherently sequential on the script. The `[P]` markers apply to the foundational scaffolds, the distinct polish render-sections, and the Codex doc twins — not to the core script slices.

---

## Traceability (FR/SC → task)

Every FR-001..FR-015 maps to at least one implementation task; every SC-001..SC-005 maps to a verification task/command.

| Requirement | Task(s) | Verification |
|---|---|---|
| FR-001 (parse US/FR/SC/Edge; argv contract; nested bullets verbatim) | T009 | T007 full-spec fixture; T026 smoke |
| FR-002 (reuse `extract_heading_section`, copied verbatim) | T002, T009 | Code review (provenance comment); T007 |
| FR-003 (zero-stories → FR/SC keying + header note, never skip) | T013 | T012 zero-stories fixture; SC-002 |
| FR-004 (duplicate IDs → first-seen + plain stderr) | T021 | T021 duplicate-FR assertion |
| FR-005 (propagate clarification markers w/ annotation) | T020 | T020 clarification-marker fixture |
| FR-006 (exit 0/2/1; silent stdout; stderr diagnostics) | T021 | T021 exit-code + empty-stdout assertions |
| FR-007 (deterministic overwrite, no merge) | T015 | T014 run-twice byte-identical + sentinel assertions |
| FR-008 (`UAT_PROJECT_COMMANDS` env; placeholders when unset/malformed; `N/A` distinct) | T018 | T018 env-set/unset/malformed assertions |
| FR-009 (`--workflow-file` flag; Self-Review echo; stub when absent) | T017 | T016 with/without `--workflow-file` |
| FR-010 (template 8-section fixed order; absent Edge Cases → header+stub; matrix anchors) | T004, T010, T009 | T007 section-presence + anchor assertions |
| FR-011 (static PR placeholder; no post-PR rewrite) | T010 | Code review; T007 header assertion |
| FR-012 (Rollback from spec/plan, else synthesized stanza) | T019 | T019 with/without `## Rollback` heading |
| FR-013 (`## UAT Runbook` H2 in PR body; `cat` < 50k, `head -60`+link else; fail-open stub) | T011 | T008 size-aware embed assertions; SC-005 |
| FR-014 (CC + Codex lockstep; no new agent files) | T023, T024 | T027 (`run-all.sh --layer 1`) |
| FR-015 (Layer 4 test, 5 fixtures incl. vendored snapshot) | T003, T005, T022 | T027 (`run-all.sh --layer 4`) |
| SC-001 (run vs specs/004 → all stories present) | T026 | `grep -c '^### User Story'` parity (vendored snapshot in tests via T007) |
| SC-002 (zero-stories → fallback note + FR/SC sections) | T013 | T012 zero-stories fixture |
| SC-003 (`run-all.sh --layer 4` exits 0) | T022, T027 | CI `pr-checks.yml` matrix |
| SC-004 (`run-all.sh --layer 1` exits 0; Codex parity) | T023, T024, T027 | CI `pr-checks.yml` matrix |
| SC-005 (`## UAT Runbook` in autopilot PR body + committed runbook) | T011, T023, T024, T028 | T008 stub/embed assertions; post-merge autopilot smoke |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks.
- [Story] label maps each user-story task to US1-US4 for traceability.
- TDD-first (bash flavor): the Layer 4 RED assertion always precedes the GREEN script change within a story; test command is `cd speckit-pro && bash tests/run-all.sh --layer 4`.
- The single shared `generate-uat-skeleton.sh` makes US1-US4 impl tasks sequential — do not attempt to parallelize them.
- Codex `-codex.md` doc twins (T024) must match the CC doc edits (T023) and land in the SAME commit (Layer 1 parity stays green at every commit).
- NO task touches `speckit-pro/agents/` or `speckit-pro/codex-agents/`, and NO task copies the script/template into `speckit-pro/codex-skills/` — the Codex variant invokes the single shared copy by path (plan.md "Codex Parity").
- Conventional Commits prefix on every commit (`feat(speckit-pro):` / `test(speckit-pro):` / `docs(speckit-pro):`); PR title + body plain-English public-readable per CLAUDE.md.
- Stay within the reviewability budget (T006); split into SPEC-006b rather than expanding the task list.
