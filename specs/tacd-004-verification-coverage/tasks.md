---
description: "Task list for TACD-004 — Verification Coverage"
---

# Tasks: Verification Coverage (TACD-004)

**Input**: Design documents from `/specs/tacd-004-verification-coverage/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, quickstart.md

**Tests**: This feature IS test/verification coverage. The "implementation" tasks
ARE deterministic checks (Layers 1/4/5) plus a build-script fix and eval fixtures.
TDD is explicitly requested: every new guard starts from a FAILING deliberate-
regression fixture (proving it is non-vacuous per FR-012), then is made to pass.
Run regressions locally; do NOT commit them.

**Reviewability**: Spec budget is ~292 reviewable LOC, 1 production file
(`scripts/build-plugin-payloads.sh`), ~10 total files, primary surface =
harness/adapter. Regenerated `dist/**` is source-derived and excepted (FR-013).
A reviewability checkpoint task (T009A) is included before implementation begins.
If task work expands past 400 reviewable LOC / 6 production files / 15 total files,
stop and revisit the split decision instead of adding tasks.

**Organization**: Tasks are grouped by user story so each story is independently
implementable and testable. Phase order follows the workflow Tasks prompt:
Layer 5 (US1) → Layer 1 pointer/resolution (US2) → payload fix + completeness (US4)
→ eval rewrites + behavior scenarios (US3) → full-suite validation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Every task lists exact repo-root-relative file paths

## Path Conventions

- Repository root is the worktree
  `.worktrees/tacd-004-verification-coverage/`; all paths below are
  repo-root-relative. There is no `src/` tree — the "source code" of this slice is
  shell validators under `tests/speckit-pro/`, the Python payload builder under
  `scripts/`, and JSON eval fixtures under `tests/speckit-pro/layer3-functional/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working surface and baseline before any check changes.

- [ ] T001 Confirm branch and clean tree: `git rev-parse --abbrev-ref HEAD` shows `tacd-004-verification-coverage` and `git status --short` shows only expected SpecKit artifacts (do not create or switch branches).
- [ ] T002 Capture the green baseline by running `bash tests/speckit-pro/run-all.sh` from repo root and recording the Layer 1/4/5 pass counts; this is the reference the new checks must return to after each deliberate regression is reverted.
- [ ] T003 [P] Re-read `docs/ai/specs/.process/TACD-004-design-concept.md` (Goals, Non-goals, Q1–Q8) and `specs/tacd-004-verification-coverage/research.md` (Decisions 1–6) to lock the load-bearing scope answers before editing checks.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared inventory/allowlist conventions that several
validators reuse, and confirm the reviewability budget, before story work begins.

**⚠️ CRITICAL**: No user-story validator work begins until this phase is complete.

- [ ] T004 Inventory the active-agent set used by the named-tool guard (US1) and the pointer/resolution checks (US2): list `speckit-pro/agents/*.md` (11 Claude agents) and `speckit-pro/codex-agents/*.toml` (10 Codex agents); record the capability-dependent in-scope subset — the agents that actually reference `capability-discovery.md` (verified by inspection: `analyze-executor`, `checklist-executor`, `clarify-executor`, `codebase-analyst`, `domain-researcher`, `implement-executor` in BOTH runtimes, since the directive's applicability rule covers artifact-edit and gate-remediation work, not only research/context-gathering) — and the enumerated out-of-scope exclusion set (`consensus-synthesizer`, `gate-validator`, `phase-executor`, `spec-context-analyst`, `uat-runbook-author` on the Claude side; `phase-executor`, `spec-context-analyst`, `uat-runbook-author`, `autopilot-fast-helper` on the Codex side) with a one-line reason each, per spec FR-003 and the spec Assumptions, so "uncovered" cannot be confused with "out of scope". Derive the in-scope set from the literal directive reference rather than a hardcoded short list, so the pointer-coverage validator (T017) iterates the real referencing set.
- [ ] T005 Confirm the spike-approved category allowlist and the false-positive carve-outs the named-tool guard must honor (generic `mcp`/`MCP` vocabulary; exact schema/dependency metadata identifiers; fixtures; historical provenance) from `docs/ai/research/tool-agnostic-capability-discovery-spike.md`; record the vendor-qualified detection shape `mcp__<vendor>__<tool>` minus the allowlist (research Decision 1). Do not redefine the allowlist — reuse it.
- [ ] T006 Confirm the `dist/**` resolution model is prefix re-rooting (not a runtime-relative `../references/…` walk): the in-source repo-root-relative path token `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` must resolve under BOTH `dist/claude/<token>` and `dist/codex/<token>` (research Decision 3 / FR-004); verify both targets currently exist before writing the resolution check.
- [ ] T007 Confirm the Layer 1 registration site in `tests/speckit-pro/run-all.sh` (Claude block ~lines 137–149, Codex block ~lines 153–158) where new validators MUST be enumerated to execute in the default run (FR-011), and note the existing validator conventions to mirror (`#!/usr/bin/env bash`, `set -euo pipefail`, `source ../lib/assertions.sh`, `REPO_ROOT` via `cd "$(dirname "$0")/../../.."`, `chmod +x`).
- [ ] T009A Verify the reviewability budget against the planned task/file scope (1 production file `scripts/build-plugin-payloads.sh`; 1 reworked Layer 5 validator; up to 3 new Layer 1 validators; `run-all.sh` registration; 4 eval files; `dist/**` regeneration excepted) and record the split decision (remains one spec) or an exception before implementation. Stop and revisit the split if scope exceeds 400 reviewable LOC / 6 production files / 15 total files.

**Checkpoint**: Inventory, allowlist, resolution model, registration site, and budget are confirmed — user-story validator work can begin.

---

## Phase 3: User Story 1 - Named-tool regression cannot land unnoticed (Priority: P1) 🎯 MVP [US1]

**Goal**: A deterministic Layer 5 guard FAILS when active Claude/Codex agent guidance
reintroduces a hardcoded named optional-tool preference outside the approved category
allowlist; the named-MCP requirement is removed from the tool-scoping contract entirely.

**Independent Test**: Add a fixture in which an active agent names a specific
`mcp__<vendor>__*` tool outside the allowlist, run `--layer 5`, confirm the guard
FAILS naming the file/token; revert and confirm green. Confirm the guard does NOT fire
on the generic `mcp` vocabulary or on exact schema/dependency metadata IDs (acceptance
scenarios 1–3). Confirm tool-scoping no longer requires any named vendor MCP set
(scenario 4).

### Tests for User Story 1 (RED first — prove non-vacuity) ⚠️

> Write/exercise the failing regression FIRST and confirm FAIL before implementing the guard. Do not commit the regression.

- [ ] T010 [US1] RED: temporarily add a hardcoded named vendor tool (e.g. `mcp__<vendor>__search`) to one active agent under `speckit-pro/agents/` or `speckit-pro/codex-agents/`, run `bash tests/speckit-pro/run-all.sh --layer 5`, and confirm the (not-yet-added) named-tool guard would catch it — i.e. record the expected failing assertion before implementing it (FR-012, SC-001, AC-4.1). Revert the fixture.

### Implementation for User Story 1

- [ ] T011 [US1] Remove the named MCP tool assertions from the `implement-executor` research-tools loop in `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh` (the five `mcp__tavily-mcp__*`, `mcp__context7__*`, `mcp__RepoPrompt__*` lines, ~lines 243–251), keeping `WebSearch WebFetch`, so the scoping contract no longer names a vendor MCP set (FR-002, AC-4.1 scenario 4). Keep the edit surgical — do not disturb other Layer 5 expectations.
- [ ] T012 [US1] Add the named-tool regression guard to `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh`: scan active Claude agent source (`speckit-pro/agents/*.md`) and active Codex agent source (`speckit-pro/codex-agents/*.toml`) for a vendor-qualified `mcp__<vendor>__<tool>` pattern, subtract the approved category allowlist and false-positive carve-outs from T005 (generic `mcp`/`MCP`, exact schema/dependency metadata IDs), and FAIL with a message naming the offending file and token (FR-001, SC-001).
- [ ] T013 [US1] Make the guard fail-closed: if the active-agent glob matches nothing or a file read fails, the guard FAILS rather than passing on zero work; rely on `set -euo pipefail` plus an explicit empty-set assertion (FR-012).
- [ ] T014 [US1] GREEN + non-vacuity proof: run `bash tests/speckit-pro/run-all.sh --layer 5`; confirm green on the clean tree, then re-apply the T010 regression and confirm the guard FAILS (names file/token), then revert and confirm green. Also confirm no false positive on generic-`mcp`-only content and on schema/dependency IDs (AC-4.1 scenarios 1–3).

**Checkpoint**: Layer 5 names no vendor MCP set and a deliberate named-tool regression fails the guard — US1 is independently functional.

---

## Phase 4: User Story 2 - Directive pointers are proven to exist and resolve (Priority: P1) [US2]

**Goal**: Layer 1 pointer-coverage proves each capability-dependent active agent
references `capability-discovery.md` (or an enumerated approved equivalent), and Layer
1 target-resolution proves the referenced directive resolves at the path each runtime
loads it from inside `dist/claude/**` AND `dist/codex/**`.

**Independent Test**: Run pointer-coverage against the active-agent inventory and
confirm in-scope agents are covered; break a pointer (strip the reference from an
in-scope agent) and confirm pointer-coverage FAILS naming the agent. Rename/remove the
directive at a referenced path inside a built tree and confirm target-resolution FAILS
for both runtimes (acceptance scenarios 1–4). Claude/Codex parity holds (FR-009).

### Tests for User Story 2 (RED first — prove non-vacuity) ⚠️

> Exercise each broken-input regression FIRST and confirm FAIL before implementing. Do not commit the regressions.

- [ ] T015 [US2] RED: record the expected pointer-coverage failure by temporarily stripping the `capability-discovery.md` reference from one in-scope agent (e.g. `speckit-pro/agents/domain-researcher.md`), confirming the planned check would FAIL and name the uncovered agent (FR-012, SC-002, US2 scenario 2). Revert.
- [ ] T016 [US2] RED: record the expected target-resolution failure by temporarily renaming/removing the directive at `dist/claude/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` (and the `dist/codex/**` sibling), confirming the planned check would FAIL for BOTH runtimes (FR-012, SC-002, US2 scenarios 3–4). Restore via rebuild.

### Implementation for User Story 2

- [ ] T017 [US2] Create `tests/speckit-pro/layer1-structural/validate-capability-pointer.sh` (FR-003): iterate the active-agent inventory; assert each in-scope (capability-dependent) agent references `capability-discovery.md` by literal path OR appears in the enumerated approved-equivalent allowlist; enumerate the out-of-scope exclusion set literally (from T004) with a one-line reason each; FAIL naming any uncovered in-scope agent. The in-scope set is the directive-referencing set recorded in T004 (the 6 referencing agents in both runtimes), NOT a shorter hardcoded subset — an in-scope agent that omits the pointer must FAIL, not be quietly dropped. The allowlist and exclusion set are literal enumerations (not heuristics) and MUST NOT be widened to silence an in-scope agent that omits the pointer (FR-003, FR-009, SC-002). Begin with `#!/usr/bin/env bash` + `set -euo pipefail`, `source ../lib/assertions.sh`, `chmod +x`.
- [ ] T018 [US2] Create `tests/speckit-pro/layer1-structural/validate-capability-resolution.sh` (FR-004): for each pointer found, extract the in-source repo-root-relative path token verbatim and assert it resolves under BOTH `dist/claude/<token>` and `dist/codex/<token>` (prefix re-rooting per research Decision 3); FAIL on a path correct in source but absent in either built tree — never pass on source-tree presence alone (FR-004, FR-009, SC-002). Begin with `#!/usr/bin/env bash` + `set -euo pipefail`, `chmod +x`.

  > Per plan.md note: pointer-coverage and target-resolution MAY be combined into a single `validate-capability-pointer.sh` if both rules read clearly in one file; the LOC estimate is unaffected. T017/T018 stay separate by default for a clean review surface.

- [ ] T019 [US2] Make both Layer 1 validators fail-closed: if the active-agent glob matches nothing, a referenced `dist/**` target is absent, or a `jq`/file read fails, the validator FAILS rather than reporting success on zero work (FR-012); rely on `set -euo pipefail` plus explicit empty-set / missing-target assertions.
- [ ] T020 [US2] Register `validate-capability-pointer.sh` and `validate-capability-resolution.sh` in `tests/speckit-pro/run-all.sh` alongside the other Layer 1 validators (Claude block ~lines 137–149) so they execute in the default run — an unregistered validator does not satisfy FR-011 (FR-011).
- [ ] T021 [US2] GREEN + non-vacuity proof: run `bash tests/speckit-pro/run-all.sh --layer 1`; confirm green on the clean tree, then re-apply the T015 pointer regression (confirm pointer FAIL names the agent) and the T016 resolution regression (confirm resolution FAIL for both runtimes), reverting/rebuilding after each, and confirm green (SC-002, AC-4.2).

**Checkpoint**: Pointer-coverage and target-resolution pass for Claude and Codex, fail on a broken pointer/path, and are registered in the default suite — US2 is independently functional.

---

## Phase 5: User Story 4 - Installed skills ship complete bodies (Priority: P1) [US4]

**Goal**: `strip_codex_guard` strips only the Codex guard section (heading → next `## `
heading or EOF), `dist/**` is rebuilt from source so all skill bodies are restored, and
a deterministic Layer 1 body-completeness check FAILS if any built Claude SKILL.md is
truncated relative to its source minus the guard section.

**Independent Test**: Rebuild from source and confirm every built Claude SKILL.md
retains its full body (last non-guard source heading survives; body length within
tolerance of source-minus-guard); the 8 currently-truncated skills are restored.
Introduce a deliberately truncated built SKILL.md and confirm body-completeness FAILS
naming the skill (acceptance scenarios 1–4). Suite stays green with no live AI eval.

### Tests for User Story 4 (RED first — prove non-vacuity) ⚠️

> Exercise the truncation regression FIRST and confirm FAIL before implementing the check. Do not commit the regression.

- [ ] T022 [US4] RED: record the expected body-completeness failure by temporarily truncating one built `dist/claude/speckit-pro/skills/<skill>/SKILL.md` (drop the trailing non-guard heading / cut the body), confirming the planned check would FAIL and name the truncated skill (FR-012, SC-005, US4 scenario 3). Restore via rebuild.

### Implementation for User Story 4

- [ ] T023 [US4] Fix `strip_codex_guard` in `scripts/build-plugin-payloads.sh` (FR-007): replace the line-wrapped magic-terminator scan (`"fallback guard was triggered."` substring, ~lines 77–90) with a section-boundary scan — from the `## Codex Skill-Selection Guard` heading, skip the heading line, consume until the next line that `startswith("## ")` OR EOF, and do not emit the consumed range; collapse the trailing special-case block into the same boundary logic. A SKILL.md with no guard heading is left untouched (edge case "Skill with no guard block"). Keep the builder's existing safety structure; this is a localized change.
- [ ] T024 [US4] Regenerate `dist/**` from source by running `bash scripts/build-plugin-payloads.sh` (FR-007, FR-013); do NOT hand-edit any payload. Confirm the 8 previously-truncated Claude skills now match source-minus-guard (use the quickstart.md §2 body-length loop) and that `git diff --exit-code -- dist` is clean after committing the regenerated payloads.
- [ ] T025 [US4] Create `tests/speckit-pro/layer1-structural/validate-payload-completeness.sh` (FR-008): for every built Claude `SKILL.md`, assert (1) the structural anchor — the last non-guard `## ` heading in the source SKILL.md is present in `dist/claude/**/SKILL.md`; and (2) the length tolerance — built body length is within a small slack of source-minus-guard, where the guard section is computed PER SKILL using the SAME heading-to-next-`## `/EOF boundary as the fixed `strip_codex_guard` (never a single fixed line-count constant), so the check and the builder cannot disagree (FR-008). FAIL naming any truncated skill. Begin with `#!/usr/bin/env bash` + `set -euo pipefail`, `chmod +x`.
- [ ] T026 [US4] Make the body-completeness check fail-closed: if the Claude skills glob matches nothing, a source/built SKILL.md is missing, or a read fails, the check FAILS rather than passing on zero work (FR-012); rely on `set -euo pipefail` plus explicit empty-set / missing-file assertions.
- [ ] T027 [US4] Register `validate-payload-completeness.sh` in `tests/speckit-pro/run-all.sh` alongside the other Layer 1 validators (Claude block ~lines 137–149) so it executes in the default run (FR-011).
- [ ] T028 [US4] GREEN + non-vacuity proof: run `bash tests/speckit-pro/run-all.sh --layer 1`; confirm green with all bodies restored, then re-apply the T022 truncation regression and confirm body-completeness FAILS naming the skill, then rebuild and confirm green (SC-005, AC-4.4 — no live AI eval dependency).

**Checkpoint**: All Claude skill bodies are restored, the body-completeness check fails on a truncated payload and is registered in the default suite — US4 is independently functional.

---

## Phase 6: User Story 3 - Eval expectations enforce vendor-neutral, capability-first answers (Priority: P2) [US3]

**Goal**: The optional-tool expectations across all four eval files are rewritten so
each asserts BOTH the absence of a preferred named set AND an affirmative
capability-first answer; five behavior-observable scenarios are added as committed
fixtures; Claude/Codex parity holds. No live model run gates merge.

**Independent Test**: Inspect each of the four eval files and confirm every
optional-tool expected output asserts both absence and an affirmative answer; confirm
the five scenarios (installed-capability discovery, fallback, evidence path,
citations/local-file references, lowered confidence) are present as fixtures and
validate without a live run; confirm Claude/Codex parity per scenario (acceptance
scenarios 1–3). All four files remain valid JSON.

### Implementation for User Story 3

> The four eval-file edits touch four different files with no shared helper to land first, so they are `[P]`-parallel-safe (per the workflow Tasks prompt). Apply each edit in Claude/Codex parity (FR-009).

- [ ] T029 [P] [US3] Rewrite the optional-tool expectations in `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json` (FR-005): each optional-tool `expected_output`/`expectations` asserts an ABSENCE arm (no Tavily/Context7/RepoPrompt named preference) AND an AFFIRMATIVE arm (describes installed-capability discovery + vendor-neutral fallback). Keep the file valid JSON; preserve the existing eval schema (`id`, `prompt`, `expected_output`, `expectations`).
- [ ] T030 [P] [US3] Rewrite the optional-tool expectations in `tests/speckit-pro/layer3-functional/evals/speckit-coach-evals.json` with the same absence + affirmative rule (FR-005); keep valid JSON and the existing schema.
- [ ] T031 [P] [US3] Rewrite the optional-tool expectations in `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json` in parity with T029 (FR-005, FR-009); keep valid JSON and the existing schema.
- [ ] T032 [P] [US3] Rewrite the optional-tool expectations in `tests/speckit-pro/layer3-functional/codex-evals/speckit-coach-evals.json` in parity with T030 (FR-005, FR-009); keep valid JSON and the existing schema.
- [ ] T033 [US3] Add the five behavior-observable scenarios as committed fixtures across the four eval files (FR-006): (1) installed-capability discovery, (2) fallback when named tools are unavailable, (3) evidence path, (4) citations/local-file references, (5) lowered confidence when fallback quality is lower — each validated by committed fixtures, none requiring a live model run to gate merge. Mirror across Claude and Codex (FR-009).
- [ ] T034 [US3] Validate eval JSON + parity + absence-arm: run the quickstart.md §4 commands — `jq -e .` on all four files (valid JSON), and `grep -lE "[Tt]avily|[Cc]ontext7|RepoPrompt"` confirms no re-taught named preference remains in optional-tool expectations (any retained string is historical/provenance or a deliberate absence-arm reference); confirm Claude/Codex parity per scenario (SC-003, AC-4.3, FR-009). No live `claude -p` run gates merge (FR-006).

**Checkpoint**: All four eval files are vendor-neutral (absence + affirmative), carry the five behavior scenarios in parity, and remain valid JSON — US3 is independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Whole-suite validation, script safety, and the PR review packet.

- [ ] T035 Run the full default deterministic suite `bash tests/speckit-pro/run-all.sh` and confirm Layers 1, 4, 5 pass with zero failures, including the new Layer 1 validators and the reworked Layer 5 checks, with no dependency on live AI eval execution (SC-004, AC-4.4, FR-010, FR-011).
- [ ] T036 [P] Script safety (constitution II): run `bash -n` on `scripts/build-plugin-payloads.sh` and on each new/changed validator (`validate-capability-pointer.sh`, `validate-capability-resolution.sh`, `validate-payload-completeness.sh`, `validate-tool-scoping.sh`); confirm each new validator begins with `#!/usr/bin/env bash` + `set -euo pipefail`, is executable (`chmod +x`), and `git diff --check` reports no whitespace errors.
- [ ] T037 Run the full quickstart.md validation (§1 suite, §2 payload rebuild + body-length table + `git diff --exit-code -- dist`, §3 the (a)–(d) deliberate-regression flips locally without committing them, §4 eval JSON/parity, §5 script safety) and confirm every "Expected" holds.
- [ ] T038 Generate or update the PR review packet per spec PR Review Packet Requirements + quickstart.md checklist: what changed, why, non-goals, review order, scope budget, traceability (AC-4.1→`validate-tool-scoping.sh`; AC-4.2→`validate-capability-pointer.sh`/`validate-capability-resolution.sh`; AC-4.3→four eval files; AC-4.4→`run-all.sh`; SC-Payload→`strip_codex_guard` + `dist/**` rebuild + `validate-payload-completeness.sh`) → changed files → verification evidence, known gaps (list any non-empty approved-equivalent allowlist entry + reason), and rollback notes (revert PR; payload fix is forward-only). Keep the PR title/body public-readable and conventional-commits-prefixed (`fix(speckit-pro):`).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup; BLOCKS all user stories (it fixes the inventory, allowlist, resolution model, registration site, and budget the validators reuse).
- **User Stories (Phases 3–6)**: All depend on Foundational. Workflow-mandated order is US1 → US2 → US4 → US3, but each story is independently testable and could be staffed in parallel after Foundational.
- **Polish (Phase 7)**: Depends on all user stories being complete (full-suite + quickstart validation + PR packet).

### User Story Dependencies

- **US1 (P1, Layer 5)**: After Foundational — no dependency on other stories.
- **US2 (P1, Layer 1 pointer/resolution)**: After Foundational — independent of US1. Target-resolution (T018) assumes `dist/**` is committed in sync; if run before US4's rebuild it still resolves against the currently-committed `dist/**`, but cleanest sequencing runs US4's rebuild before final whole-suite validation.
- **US4 (P1, payload fix + completeness)**: After Foundational — the `strip_codex_guard` fix (T023) MUST land before the `dist/**` rebuild (T024) so the rebuild restores full bodies, and before the body-completeness check goes green (T028).
- **US3 (P2, eval rewrites)**: After Foundational — independent of US1/US2/US4 (JSON fixture edits only). The four file edits (T029–T032) are `[P]` parallel-safe.

### Within Each User Story

- RED regression fixture is exercised and confirmed FAILING before the guard/check is implemented (TDD / FR-012).
- Remove named-MCP set (US1) before / alongside adding the guard; build-fix before rebuild (US4); validator created before it is registered in `run-all.sh`.
- Story complete (green + non-vacuity proof) before moving to the next priority.

### Parallel Opportunities

- T003 (re-read design docs) is `[P]` within Setup.
- The four eval-file edits T029, T030, T031, T032 are `[P]` — four different files, no shared helper.
- T036 (script-safety `bash -n`) is `[P]` within Polish.
- After Foundational, US1 / US2 / US3 / US4 could be worked in parallel by different developers (US4's internal fix→rebuild→check order still applies).

---

## Parallel Example: User Story 3 (eval rewrites)

```bash
# Launch the four eval-file rewrites together (different files, no shared helper):
Task: "Rewrite optional-tool expectations in tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json"
Task: "Rewrite optional-tool expectations in tests/speckit-pro/layer3-functional/evals/speckit-coach-evals.json"
Task: "Rewrite optional-tool expectations in tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json"
Task: "Rewrite optional-tool expectations in tests/speckit-pro/layer3-functional/codex-evals/speckit-coach-evals.json"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories).
3. Complete Phase 3: US1 — Layer 5 named-MCP removal + named-tool guard.
4. **STOP and VALIDATE**: re-add a named vendor tool, confirm the guard FAILS, revert, confirm green (`--layer 5`). The vendor-neutral contract is now locked at the tool-scoping layer.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 (Layer 5 guard) → test independently → contract locked at tool-scoping.
3. US2 (Layer 1 pointer/resolution) → test independently → directive pointers proven to resolve in both built trees.
4. US4 (payload fix + completeness) → test independently → all skill bodies restored, truncation guarded.
5. US3 (eval rewrites + scenarios) → test independently → observable behavior locked vendor-neutral.
6. Polish → full suite + quickstart + PR packet.

### TDD / Non-Vacuity Discipline (FR-012)

Every new guard (T012 named-tool, T017 pointer, T018 resolution, T025 body-completeness)
is preceded by a deliberate-regression RED task (T010, T015, T016, T022) that confirms
the guard FAILS when the contract is violated, and each is made fail-closed on empty/
missing input. Regressions are run locally and NOT committed.

---

## Notes

- [P] tasks = different files, no dependencies on an incomplete task.
- [Story] label maps each user-story task to its spec user story for traceability.
- The default deterministic suite (`bash tests/speckit-pro/run-all.sh`) must stay green
  and must NOT depend on live AI eval execution (FR-010); the eval rewrites (US3) are
  Layer 3 fixtures validated by replay/committed fixtures only (FR-006).
- `dist/**` is regenerated ONLY from source via the builder; never hand-edited (FR-013).
- No scope drift: no agent decision-logic, prerequisite-script, or docs-wording changes
  (spec Out of Scope); extend Layers 1/4/5 in place — no new test layer, no broad
  scanner (FR-011).
- Commit after each task or logical group; keep the production fix a `fix(speckit-pro):`
  change.

---

## Requirement → Task Traceability

Every FR-001…FR-013 maps to at least one task (drives gate G5). Acceptance criteria
AC-4.1–AC-4.4 and SC-Payload (SC-001…SC-005) are covered.

| Requirement | Tasks |
|-------------|-------|
| FR-001 (named-tool guard) | T010, T012, T013, T014 |
| FR-002 (remove named MCP set) | T011 |
| FR-003 (pointer-coverage) | T004, T015, T017, T021 |
| FR-004 (dist/** target-resolution) | T006, T016, T018, T021 |
| FR-005 (eval rewrite: absence + affirmative) | T029, T030, T031, T032, T034 |
| FR-006 (five behavior scenarios, replay fixtures) | T033, T034 |
| FR-007 (strip_codex_guard fix + rebuild) | T023, T024 |
| FR-008 (body-completeness check, per-skill baseline) | T022, T025, T028 |
| FR-009 (Claude/Codex parity, evals + pointer/resolution) | T017, T018, T031, T032, T033, T034 |
| FR-010 (default suite green, no live AI eval) | T002, T028, T034, T035 |
| FR-011 (extend in place + register validators) | T007, T020, T027, T035 |
| FR-012 (non-vacuity + fail-closed) | T010, T013, T014, T015, T016, T019, T021, T022, T026, T028 |
| FR-013 (dist from source only, no hand-edit) | T024 |
| AC-4.1 / SC-001 | T010, T011, T012, T014 |
| AC-4.2 / SC-002 | T015, T016, T017, T018, T021 |
| AC-4.3 / SC-003 | T029–T033, T034 |
| AC-4.4 / SC-004 | T035, T037 |
| SC-Payload / SC-005 | T022, T023, T024, T025, T028 |
