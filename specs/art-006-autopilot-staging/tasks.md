# Tasks: Autopilot Staging

**Input**: Design documents from `specs/art-006-autopilot-staging/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: REQUIRED. FR-015 and FR-015a mandate a unit test with golden
fixtures, and the implement phase runs strict red-green-refactor per task. Every
test task below is ordered before the implementation it covers and must be
confirmed RED first.

**Reviewability**: The declared budget is **459 reviewable LOC** against 400
warn / 800 block, and **17 total files** against 15 warn / 25 block — warn on two
dimensions, block on none (plan.md:153-199). One slice, no split. T012 is the
mandatory pre-implementation reviewability checkpoint the preset template
requires past the 400-LOC warn line. **No task below may add a file outside the
Declared File Operations block at plan.md:99-115.**

**Organization**: Tasks are grouped by user story so each story can be
implemented, tested, and reviewed independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact repo-relative file paths in descriptions

## Path Conventions

This is an agent-orchestration plugin, not an application. Paths are
repo-relative from the repository root:

- Shared runner logic: `speckit-pro/speckit_pro_runner/helpers/`
- Claude distribution: `speckit-pro/skills/speckit-autopilot/`
- Codex distribution: `speckit-pro/codex-skills/speckit-autopilot/`
- Repository tests: `tests/speckit-pro/`

**Standard library only.** Python 3.11+, no new Bash and no `jq` dependency
(plan.md:41-42, constitution §II).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Capture the two baselines the run is measured against, and satisfy
the one worktree bootstrap the polish phase needs.

- [x] T001 Record pre-change baselines by running `python3 tests/speckit-pro/run-all.py` (expect zero failures; record the total test count) and the Codex body word count from quickstart.md §6 (`tests/speckit-pro/lib/structural_helpers.py` module-level `body()`, expected **7671 words, headroom 329**). Both figures are compared against at the end of the run; the test count is the prerequisite baseline FR-010a forbids overwriting.
- [x] T002 [P] Bootstrap the docs-site dependencies once for this worktree with `pnpm --dir docs-site install --frozen-lockfile` — required by root `AGENTS.md` "Worktree Preflight" before the `reference:generate` step in T041, and by nothing else in this slice.

**Checkpoint**: Baselines recorded, worktree ready.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared `resolve-autopilot-stage` runner operation and its golden
fixtures. FR-012 requires resolution to exist **once** as a registered runner
operation both distributions reach by operation identifier, so every user story
below consumes this and none of them can start until it exists.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 Create `tests/speckit-pro/unit/test-autopilot-stage-resolution.py` with module-level golden fixtures (the literal pattern `tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py:102-143` already uses, so no separate fixture file is added) covering: the closed vocabulary `plan|implement|full` (FR-001), explicit `--stage` resolution returning `source: "argv"`, and all four exit-2 rejection cases from contracts/stage-invocation.md:166-169 — unrecognised value, repeated `--stage` with differing values, `--from-phase` outside an **explicitly named** stage's range, and `--stage` with no value. Confirm RED (the operation does not exist yet).
- [x] T004 In `tests/speckit-pro/unit/test-autopilot-stage-resolution.py`, assert the **request-layer diagnostics separately from process exit codes**: a malformed `autopilot_args` yields the `invalid_input` diagnostic and a path outside the trust boundary yields `unsupported_path`, which has **no entry in the runner's exit-code map and is therefore not an exit code at all**; only the operation's own rejections are exit 2 (contracts/stage-invocation.md:190-207, api-contracts checklist CHK023). Do not write any fixture asserting exit 2 for a trust-boundary path. Confirm RED.
- [x] T005 Register the new test in `tests/speckit-pro/suite-manifest.json` under `layers[id="4"].scripts` as `{"path": "tests/speckit-pro/unit/test-autopilot-stage-resolution.py", "label": "test-autopilot-stage-resolution", "baseline": null}`, matching the existing entry shape. This manifest is the only dispatch roster — an unregistered file silently never runs. Verify with the snippet at quickstart.md:117-124 and confirm `run-all.py --layer 4` now dispatches it (still RED).
- [x] T006 In `speckit-pro/speckit_pro_runner/helpers/read_only.py`, beside `resolve_confidence_mode` (`:1081`), add `AUTOPILOT_STAGES = ("plan", "implement", "full")`, the stage→phase-range map from data-model.md:17-20, and `parse_stage_args(args)` reading `--stage` and `--from-phase` out of the invocation argv. The `--from-phase` range conflict is tested **only against an explicitly named stage** (FR-007) — an auto-detected stage never conflicts with `--from-phase`, because rejecting that pair would strand the operator at the one boundary the argument exists to cross. Turns T003's argv assertions GREEN.
- [x] T007 In `tests/speckit-pro/unit/test-autopilot-stage-resolution.py`, add fixtures for the workflow-file reader: a `Stage` row present in `### Basic Information`, a `Stage` row absent (→ `recorded_stage: null`, **not an error**, FR-008a), the FR-006a predicate over the six planning rows **plus** `Confidence Gate`, an **absent** `Confidence Gate` row that does **not** block, a **present but non-terminal** one that **does** block, and an unreadable file / unparseable `## Workflow Overview` table rejected as exit 2 rather than degraded to a default (FR-007, contracts/stage-invocation.md:209-222). Confirm RED.
- [x] T008 In `speckit-pro/speckit_pro_runner/helpers/read_only.py`, implement `workflow_stage_signals(text)` reading the `Stage` row and deriving planning completeness from the `## Workflow Overview` table. Reuse the terminal-status vocabulary but **NOT** `ADVISORY_PHASES` (`tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py:82`, `frozenset({"Confidence Gate"})`): that frozenset excludes the row from the **ordering** rule only, because the phase loop does not drive it (`:260`), which is a different question from whether planning finished. Inheriting it here is the exact FR-006a mistake — it would resolve `implement` straight after a strict-mode gate stop. Turns T007 GREEN.
- [x] T009 In `speckit-pro/speckit_pro_runner/helpers/read_only.py`, implement `resolve_autopilot_stage(inputs, repo_root)` returning the JSON envelope of contracts/stage-invocation.md:135-156 (`stage`, `source`, `basis`, `recorded_stage`, `planning_complete`, `confidence_gate_status`, `from_phase`), exit 2 with a one-line `error:` diagnostic on pre-flight rejection following the `--strict`/`--advisory` precedent at `read_only.py:1084-1085`. Wire it into `PY_HELPERS` (`:4012`), the `canonicalize_inputs` path keys, and `explicit_or_derived_args`. JSON rather than a bare token because three consumers need three fields (research.md:125-141).
- [x] T010 Register the operation in `speckit-pro/speckit_pro_runner/helpers/registry.py` beside `resolve-confidence-mode` (`:171-178`). This deliberately turns the existing `test_fixture_manifests_cover_registered_helpers` RED (`tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:338-346` asserts `fixture_ids == EXPECTED_HELPERS` exactly) — that failure is this task's red step.
- [x] T011 Turn T010 GREEN: add `resolve-autopilot-stage` to `EXPECTED_HELPERS` (`tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:51`), add the record to `tests/speckit-pro/unit/fixtures/read-only-helpers/fixture-manifest.json`, create the authoritative request fixture `tests/speckit-pro/unit/fixtures/read-only-helpers/requests/resolve-autopilot-stage.json` (shape at contracts/stage-invocation.md:112-123), and add a named `NO_BASH_ANCESTOR` carve-out to the Bash-reference comprehension at `:346`. This operation is new behaviour with no deleted `.sh` predecessor, so a fabricated `source_script` would record a lie in a provenance manifest (research.md:81-122). Do **not** invent a `.sh` path.
- [x] T012 **Reviewability checkpoint before any user-story work.** Re-run the setup-mode reviewability gate per quickstart.md:28-33 and confirm the posture is still `"status":"warn"`, `"pass":true`, `"blockers":[]`, one primary surface (`harness/adapter`). The declared position is 459 LOC / 17 files (plan.md:153-157, itemised at :185-199). Record the split decision as **one slice, no split** (plan.md:200-209). If a blocker appears, or the file list grows past the Declared File Operations block, STOP and escalate rather than adding implementation tasks.

**Checkpoint**: The shared resolver exists, is registered, is dispatched by the
suite, and the budget is re-confirmed. User stories can now begin.

---

## Phase 3: User Story 1 - Stop cleanly after planning (Priority: P1) 🎯 MVP

**Goal**: A `--stage plan` run works through Specify → Analyze, runs the
confidence gate as its terminal step, records the stage durably, commits that
boundary, and stops without starting implementation.

**Independent Test**: Run the autopilot against a fresh workflow file with
`--stage plan`. Confirm Analyze completes, G6.5 runs as the terminal step, no
implementation task starts, the `Stage` row reads `plan`, and the boundary is a
**commit** — not uncommitted working-tree state (quickstart.md:171-177).

### Tests for User Story 1

> **NOTE: Write these FIRST and confirm they FAIL before implementing.**

- [x] T013 [US1] In `tests/speckit-pro/unit/test-autopilot-stage-resolution.py`, add the planning-stage state fixture whose Implement entry **and every `Post:` entry** carry the out-of-stage status, asserting all four FR-011 constraints: the marker occupies the **status** field, the entry **name is byte-identical** to its canonical name (the coverage guard matches post-implementation checkpoints by exact name equality, so a prefixed name reads as a *missing* checkpoint), the marker text contains no `pending` substring **in any casing**, and the shape is `skipped: <reason>` (FR-015, data-model.md:96-110). Confirm RED.
- [x] T014 [P] [US1] In `tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py`, add a subTest asserting that a `Stage` row, **when present**, carries one of the three literals, and that a file with **no** `Stage` row is accepted. Reuse `workflow_files(*WORKFLOW_DIRS)` (`:146`, `:285`) so the assertion inherits the **two-directory** sweep at `:30` — `(SPEC_DIR / ".process", SPEC_DIR)` — rather than a fresh `.process/`-only glob, which would leave six workflow files unchecked and would not deliver SC-006's tree-wide guarantee (plan.md:29-37). Confirm RED against a deliberately bad fixture value.

### Implementation for User Story 1

- [x] T015 [US1] Add the out-of-stage marking rules to `speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md`, reusing the `skipped: <reason>` shape already documented at `:3` and `:56` for absent extensions so one search finds both kinds of skip. State explicitly that the status field carries the marker and the entry name does not change, and that a planning-stage run marks the Implement phase and every `Post:` entry. The canonical list is **never truncated** per stage. Turns T013 GREEN.
- [x] T016 [US1] Make T014 GREEN in `tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py` and confirm the validator still passes against all 57 existing workflow files — 56 of which carry no `Stage` row, so absence must stay legal (spec.md:236-243, quickstart.md:101-102).
- [x] T017 [P] [US1] Add `stage` (closed enum `plan|implement|full`) and `prior_run_note` (string) to `speckit-pro/skills/speckit-autopilot/contracts/autopilot-state-status.schema.json`. Both are **already written** by the running autopilot with no schema behind them (data-model.md:66-73). The object declares no `additionalProperties: false`, so the addition is backward-compatible with every state file on disk, and `validate_state_status` (`speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:3930`) begins closing the stage vocabulary for free.
- [x] T018 [US1] In `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`, add `stage_mirror_errors(workflow_text, state)` — when both stores carry a stage and they differ, report it; absence on either side is legal — importing the resolver from the runner package and returning an empty error list when the package is not importable, the same posture `validate_state_status` already takes so an extracted copy cannot manufacture a false violation (research.md:42-65). **Then register `"stage_mirror_errors"` inside the `status-evidence` tuple of `RULE_PROBLEM_KEYS` (`:238-239`)**, which today reads `("workflow_status_evidence_errors", "state_status_errors")`. Without that registration the check is computed, printed, and **inert**, because `main()` extends the selected keys only from the chosen rule (`:4042`) and the autopilot always invokes `--rule status-evidence` (`speckit-pro/skills/speckit-autopilot/SKILL.md:398`). Verify per quickstart.md:85-92: mismatch the state file's `stage`, re-run, and confirm the guard now exits **1**, not 0.
- [x] T019 [US1] In `speckit-pro/skills/speckit-autopilot/SKILL.md`: extend the usage synopsis at `:293` with `[--stage plan|implement|full]` **and** the `[--strict | --advisory]` pair the Codex synopsis at `speckit-pro/codex-skills/speckit-autopilot/SKILL.md:544` already advertises — the Claude side already resolves those flags from argv at `:328-336`, so that half is documentation catching up to shipped behaviour, not new capability (FR-002); add **Step 0.6c** immediately after the 0.6b confidence-mode bullet at `:327-336`, running `resolve-autopilot-stage`, recording `AUTOPILOT_STAGE`, and STOPping before Phase 0 on exit 2 in the same fail-fast shape 0.6b already uses; reword the unpinned anti-stall line at `:50-51` ("do not stop early, complete all 7 phases") to bind to the **resolved stage**, which a `--stage plan` run contradicts verbatim; and add a one-line `resolve-autopilot-stage` entry to the registered-operation list at `:735-740`.
- [x] T020 [US1] In `speckit-pro/skills/speckit-autopilot/SKILL.md`, record the `Stage` authority as **its own clause** in the store-precedence documentation around `:661-680`. It **MUST NOT** be added to the two-item list at `:672-680` — that list enumerates the fields for which the **state file** wins (active workflow file, PR Marker Plan Evidence status), which is the opposite direction. The `Stage` rule is workflow-file-wins, mirror-repaired-from-it (FR-008, data-model.md:112-126).
- [x] T021 [US1] In `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`: (a) make the Step 1 phase scan **stage-bounded** — the shipped scan at `SKILL.md:365-366` takes "the first phase with status `⏳ Pending` or `🔄 In Progress`", and a `⚠ Blocked` row matches **neither** arm, so after a strict-mode gate stop the unmodified scan skips the blocked `Confidence Gate` row and lands on the implementation row while the resolved stage reads `plan` — the flagship silent failure; a resolved stage must never start a phase outside its own range, and a non-terminal `Confidence Gate` row must make the planning stage re-enter **at the confidence gate**; (b) document G6.5 (`:563-565`, "After Phase 6 commits and before Phase 7 begins") as the plan stage's terminal step; (c) add the plan-stage **terminal commit** taken *after* the gate resolves, carrying a message naming the stage boundary rather than a phase — a distinct commit, not a renamed analyze-phase commit, and non-empty regardless of whether `Stage` changed because the gate row always advances off pending (research.md:364-376); and (d) bring the six per-phase `git add specs/ && git commit` lines at `:233`, `:286`, `:352`, `:398`, `:523`, `:561` in line with the enumerated trio already used at `SKILL.md:436` (`git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json`), never a directory-wide add. **Leave the Phase 7 `git add -A` commit at `SKILL.md:437` untouched** — FR-009a scopes the enumeration to bookkeeping commits only, and narrowing the implementation commit would silently drop every implementation change.
- [x] T022 [US1] In `speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md`, document the durable `Stage` entry as a row in `### Basic Information`, its **at-most-twice-per-run** write cadence (once at resolution during opening preparation, again at the plan-stage terminal commit only if the resolved stage changed, never refreshed on phase transitions), and the rule that the authoritative entry and its state mirror are written in the **same edit turn** and land in the **same commit**, so an interrupted run cannot leave a committed disagreement (FR-008b, data-model.md:129-147).
- [x] T023 [US1] Verify User Story 1 end to end per quickstart.md:171-177 and the FR-011 canonical-list check at quickstart.md:192-197: `--stage plan` completes Analyze and G6.5, starts no implementation task, leaves `Stage: plan`, and produces a stage-boundary **commit** staging only the enumerated trio.

**Checkpoint**: User Story 1 is fully functional — this is the MVP. A maintainer
can obtain a reviewable planning result and a committed boundary (SC-001).

---

## Phase 4: User Story 2 - Resume into implementation later (Priority: P2)

**Goal**: `--stage implement` in a fresh session, possibly a different working
copy, resumes at Implement and runs through the post-implementation steps
without redoing planning work.

**Independent Test**: With a workflow file left at a completed planning stage,
start a fresh session in a different working copy and request `--stage
implement`. Confirm it begins at Implement, re-runs none of the six planning
phases, and reads the recorded verdict rather than re-running the gate
(quickstart.md:179-186).

### Tests for User Story 2

- [x] T024 [US2] In `tests/speckit-pro/unit/test-autopilot-stage-resolution.py`, add fixtures for `confidence_gate_status`: the field echoes the `Confidence Gate` **status row** — the same row FR-006a's predicate reads — and is `null` when the row is absent; it must **not** be derived from free-text gate-record prose, because prose records vary between files and a bare composite score is not a verdict (the same score proceeds under advisory mode and stops under strict). Include a **non-terminal** verdict fixture, the state a strict-mode stop leaves behind (FR-010a, contracts/stage-invocation.md:155). Confirm RED.

### Implementation for User Story 2

- [x] T025 [US2] Implement `confidence_gate_status` in the `resolve_autopilot_stage` envelope in `speckit-pro/speckit_pro_runner/helpers/read_only.py`, reading the `Confidence Gate` status row via the `workflow_stage_signals` reader added in T008. Turns T024 GREEN.
- [x] T026 [US2] In `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`, add the implementation-stage entry: it MUST NOT re-run the pre-implement confidence gate and MUST read the recorded verdict from the `Confidence Gate` row instead; it MUST still **accept** the confidence-mode flags rather than rejecting them (the Codex surface advertises them unconditionally and FR-013 confines Codex changes to additive ones) while emitting an explicit diagnostic that the gate is not run in this stage and the recorded verdict is read — so an accepted flag never silently does nothing; and when that verdict is **non-terminal**, the same diagnostic MUST name it and state that the run is proceeding past a boundary the gate refused. Naming the implementation stage explicitly remains sufficient to proceed; crossing silently is what must not happen. Also reword the strict-mode STOP guidance at `:620-624`, which today reads "Operator may resume with `--from-phase implement`", to name `--stage implement` — the direct expression of the same intent. The `--from-phase` form keeps working under FR-007, so no operator following older guidance is stranded.
- [x] T027 [US2] In `speckit-pro/skills/speckit-autopilot/SKILL.md`, document slot reclaim at opening preparation: when an invocation of **any** stage targets a workflow file the single-slot state file does not currently name, rewrite `workflow_file`, `spec_id`, `feature_dir`, `branch`, `status`, `stage`, and `plan` **from the target workflow file BEFORE the coverage guard runs** (FR-012a). Reclaiming is normal operation, not an error. The trigger is deliberately unscoped by stage: the guard's workflow-identity check is inert for every stage — run against a state file naming a different specification it exits 0 and reports `pass` (research.md:401-412) — so ordering re-initialisation after the guard leaves it unprotected, not merely late. Record the reclaimed run's `status` **verbatim** in the documented `prior_run_note` field added in T017, so an `in_progress` slot is distinguishable from a `completed` or `completed_archived` one (FR-012b). It MUST NOT block: the state file carries no liveness evidence.
- [x] T028 [US2] In `speckit-pro/skills/speckit-autopilot/SKILL.md`, document that opening preparation **preserves** an already-recorded prerequisite test-count baseline rather than overwriting it — the later gate verifies an increase against that baseline and a post-planning recount would make the comparison vacuous — and that a newly observed count which differs is recorded as a **non-blocking drift diagnostic** instead of replacing the baseline (FR-010a). Also document the resume protocol shared by both distributions, closing the parity gap where the Codex side documents recovery only for a *missing* state file and the Claude side documents none at all (FR-012).
- [x] T029 [US2] Verify User Story 2 end to end per quickstart.md:179-186 from a **different working copy** and a fresh session: begins at Implement, re-runs no planning phase, reads the recorded G6.5 verdict, preserves the recorded baseline, reconstructs everything from the workflow file alone, and accepts a confidence-mode flag with the explicit diagnostic. Confirm the pull-request marker-plan carve-out is honoured — that evidence keeps its own stricter stop-rather-than-infer rule and is **not** relaxed to satisfy FR-010 (SC-003).

**Checkpoint**: User Stories 1 and 2 both work. A plan stage followed later by an
implement stage produces the same end result as one uninterrupted full run
(SC-002).

---

## Phase 5: User Story 3 - Bare invocation resolves its own stage (Priority: P3)

**Goal**: With no stage named, the autopilot reads the workflow file's own status
table, resolves `implement` when the planning phases are all complete and `plan`
otherwise, and reports the choice and its basis before work begins.

**Independent Test**: Run with no stage against two workflow files — one with
planning incomplete, one complete — and confirm each resolves to the expected
stage and reports the resolution before starting (quickstart.md:188-190).

### Tests for User Story 3

- [x] T030 [US3] In `tests/speckit-pro/unit/test-autopilot-stage-resolution.py`, add the auto-detection golden fixtures (SC-004): empty `autopilot_args` against planning-incomplete → `stage: "plan"`, `source: "auto-detect"`, with a `basis` naming the first non-terminal phase and its status; empty args against all-predicate-rows-terminal → `stage: "implement"`; explicit `--stage implement` against planning-incomplete → `implement`, because an explicitly named stage always overrides auto-detection; and the strict-mode-stop case where the six planning rows are terminal but `Confidence Gate` is blocked → `plan`, **not** `implement`. Confirm RED.

### Implementation for User Story 3

- [x] T031 [US3] In `speckit-pro/speckit_pro_runner/helpers/read_only.py`, implement the auto-detection branch of `resolve_autopilot_stage`: consume `planning_complete` from `workflow_stage_signals`, set `source` to `"argv"` or `"auto-detect"`, and build the `basis` string the orchestrator prints. Explicit `--stage` always wins (contracts/stage-invocation.md:69-73). Turns T030 GREEN.
- [x] T032 [US3] In `speckit-pro/skills/speckit-autopilot/SKILL.md`, make Step 0.6c print the resolved stage and its basis **before any phase work begins** (FR-006). When the slot reclaim of T027 found a predecessor recorded `in_progress`, that fact is surfaced in this same report — it is the only available signal that a second run may still be live (FR-012b) — and it does not block.
- [x] T033 [US3] Verify User Story 3 end to end per quickstart.md:188-190 against two workflow files, one planning-incomplete and one complete, confirming each resolves to the expected stage and reports the choice and basis before phase work begins.

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: The Codex distribution, the cross-distribution parity assertion, and
the generated-artifact regeneration that every source edit above requires.

- [x] T034 [P] Add the cross-distribution **argument-parity assertion** to `tests/speckit-pro/unit/test-autopilot-stage-resolution.py`: feed both distributions' documented argv forms — the Claude ordering at contracts/stage-invocation.md:14-20 and the Codex ordering at `:38-44` — through the one `resolve-autopilot-stage` operation and assert identical resolution across the full fixture set (FR-015a, SC-007). Argument order in a synopsis is presentation only; the resolver reads argv by name. This assertion does **not** go in `tests/speckit-pro/layer1-structural/validate-codex-parity.py`, whose checks are existence-only by design and whose counted baseline would need regenerating.
- [x] T035 Make three additive edits to `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`: append `[--stage plan|implement|full]` to the argv line at `:544`; add one pointer sentence directing the reader to the stage section of `references/phase-execution-codex.md`; and add a **Step 0.6c** bullet beside the existing 0.6b confidence-mode bullet at `:571-579`, running `resolve-autopilot-stage` and STOPping before Phase 0 on exit 2. **The Step 0.6c bullet belongs in the capped skill body, not in a reference file** — `references/phase-execution-codex.md` opens at `## Contents`/`## Canonical Order`/`## Main Execution Loop` and carries **no opening-preparation section**, so a rejection sited there would run *after* phase work began and could satisfy neither FR-007 nor SC-005 (api-contracts checklist CHK022/CHK045). Budget: this is the **third** capped-body edit, ≈54 words of the 329 available.
- [x] T036 Add all **remaining** Codex stage prose to `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`, which is uncapped: the stage-bounded loop, the plan stage's terminal commit after G6.5, the implementation-stage recorded-verdict read and its diagnostic, and the shared resume protocol. Every edit is additive — the four string-pinned sentences (`tests/speckit-pro/layer1-structural/validate-codex-skills.py:292`, `:295`, `:306-310`, `:313-318`) must survive verbatim, and they read `runtime_doc`, which folds referenced files in.
- [x] T037 [P] Add the out-of-stage `skipped: <reason>` marking rules to `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md`, matching T015. Constraints (a) name byte-identical and (b) no `pending` substring are the two that bind on **both** distributions, because both derive from the shared phase-coverage guard rather than from either skill body's prose. The pre-final audit that tolerates the marker is Codex-only; the Claude distribution ships no equivalent completion audit (FR-011, api-contracts checklist CHK039).
- [x] T038 Re-measure the Codex body word count with the quickstart.md:128-137 snippet and confirm it is under the 8000-word cap enforced at `tests/speckit-pro/layer1-structural/validate-codex-skills.py:168-171` (**measured result: 7795, headroom 205** from a 7671 baseline — the three T035 edits cost 124 words, more than the ≈54 budgeted and well over the ≈24 that predated the Step 0.6c relocation; downstream specs inherit 205, not 275), then run `python3 tests/speckit-pro/run-all.py --layer 1` and confirm the four string-pinned sentences still pass.
- [x] T039 Confirm the `description` frontmatter of both autopilot skills is **unchanged**. Layer 2 trigger evals are `default:false` and `live_only:true`, so CI will not run them — if and only if a description changed, run the Layer 2 trigger eval manually and record the result. No description change is planned by plan.md, so the expected outcome is "unchanged, no manual eval required".
- [x] T040 **Regenerate the release artifacts — this must run AFTER every source edit above is final.** Run `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py`, which rebuilds `dist/claude/**` and `dist/codex/**`, content-syncs `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/**`, and recomputes the runner manifest and `.sha256`. **Never hand-edit a generated payload.** The refresh is idempotent, so run it a second time and confirm `git status` reports no further changes; a dirty tree after the second run means something is still out of sync.
- [x] T041 Regenerate the docs-site test reference with `pnpm --dir docs-site reference:generate`. This is a **separate** step — `scripts/refresh-release-artifacts.py` does not regenerate docs-site reference pages — and it is required because a tracked `.py` file under `tests/speckit-pro/` changed (`tests/speckit-pro/AGENTS.md:13`). Depends on T002.
- [x] T042 Run the full validation walk: `python3 tests/speckit-pro/run-all.py` with zero failures and a total test count **greater** than the T001 baseline (if it did not increase, the new test is missing from the dispatch roster), plus the quickstart.md §1–§7 checks in order.
- [x] T043 Generate the PR review packet per spec.md:471-478: what changed, why, non-goals, review order, scope budget, traceability mapping each requirement to changed files and verification evidence, known gaps, and rollback notes. Rollback is a plain revert — the feature adds an argument and a table row, and a workflow file carrying a stale `Stage` row still validates because absence and presence are both legal (plan.md:210-217). Deferred work names its owner: draft-pull-request corroboration and the scaffold-side chain implementation go to the downstream ART specifications.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS all user stories** — FR-012 makes the registered runner operation the single implementation of stage resolution, so nothing downstream can be built against a second copy of the rule.
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on US2 or US3.
- **User Story 2 (Phase 4)**: Depends on Foundational. Depends on **US1** in practice, because resuming requires the durable state US1 produces (spec.md:61-64). T024/T025 are technically independent of US1 and may start earlier.
- **User Story 3 (Phase 5)**: Depends on Foundational only. A convenience layer over US1 and US2 — explicitly naming a stage always works, so it can ship last (spec.md:96-98).
- **Polish (Phase 6)**: Depends on all three stories. **T040 must be the last source-affecting task**; T041 follows it; T042 verifies after both.

### Within Each User Story

- Tests are written and confirmed FAILING before implementation.
- Shared runner logic before the distributions that call it.
- Both distributions before the generated-artifact regeneration.

### Sequencing constraints carried from plan.md:475-489

1. **Reclaim before guard** (T027). Ordering re-initialisation after the coverage guard is not merely late, it is unprotected — the workflow-identity check is inert today.
2. **Terminal commit after the gate** (T021). The plan-stage commit is taken after G6.5 resolves so the verdict is captured; it is a distinct commit, not a renamed analyze-phase commit.
3. **Regenerate last** (T040). A second run on unchanged source is a no-op.

### Parallel Opportunities

- T002 runs in parallel with T001.
- T014 and T017 touch different files from the rest of US1 and are marked [P].
- T034 and T037 touch different files and are marked [P].
- Once Foundational completes, US1 and the US3 resolver work (T030/T031) can proceed in parallel; the US1 distribution prose (T019–T022) and the US3 reporting edit (T032) both touch `SKILL.md` and must not.

---

## Parallel Example: Foundational → User Story 1

```bash
# After T012, these touch disjoint files and can run together:
Task: "T014 Stage-row assertions in tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py"
Task: "T017 stage + prior_run_note in speckit-pro/skills/speckit-autopilot/contracts/autopilot-state-status.schema.json"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational — CRITICAL, blocks all stories.
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: run the US1 independent test at quickstart.md:171-177.
5. US1 alone already delivers SC-001 — a reviewable planning result and a
   committed boundary with zero implementation-phase work.

### Incremental Delivery

1. Setup + Foundational → the shared resolver exists and is registered.
2. Add US1 → the boundary can be reached and committed (MVP).
3. Add US2 → the boundary can be crossed from a fresh session.
4. Add US3 → the boundary resolves itself on a bare invocation.
5. Polish → both distributions in step, generated artifacts refreshed.

### Sequential, not parallel-team

This slice is one vertical capability across two distributions with a single
shared resolver. The `SKILL.md` files are edited by several tasks each, so
splitting the stories across developers would collide. Run it sequentially.

---

## Traceability

| Requirement | Tasks |
|---|---|
| FR-001 stage vocabulary | T003, T006, T014/T016 |
| FR-002 both distributions accept `--stage`; synopsis repair | T019, T035, T034 |
| FR-003 plan stage range + terminal gate | T021, T023 |
| FR-004 implement stage range | T026, T029 |
| FR-005 full stage | T006, T030 |
| FR-006 / FR-006a auto-detection + predicate row set | T007, T008, T030, T031, T032 |
| FR-007 pre-flight rejection, explicit-only conflict, unreadable file | T003, T004, T006, T007, T019, T035 |
| FR-008 / FR-008a / FR-008b durable store, absence legal, write cadence | T017, T020, T022 |
| FR-009 / FR-009a terminal commit, staged path set, stage-bounded scan | T021, T023 |
| FR-010 / FR-010a fresh-session resume, recorded verdict, baseline | T024, T025, T026, T028, T029 |
| FR-011 out-of-stage `skipped:` marker | T013, T015, T037 |
| FR-012 / FR-012a / FR-012b shared resolver, slot reclaim, predecessor status | T009, T010, T011, T027, T028, T032 |
| FR-013 Codex additive, word cap, pinned sentences | T035, T036, T038 |
| FR-014 / FR-014a two enforcement surfaces, problem key registered | T014, T016, T018 |
| FR-015 / FR-015a golden fixtures, filename rule, parity assertion | T003, T005, T013, T030, T034 |
| FR-016 chain contract (documentation only) | already delivered in `contracts/scaffold-autopilot-chain.md`; no implementation task |
| SC-001 | T023 |
| SC-002 | T029 |
| SC-003 | T029 |
| SC-004 | T030 |
| SC-005 | T003, T004 |
| SC-006 | T014, T016 |
| SC-007 | T034 |
| SC-008 | T038, T042 |

---

## Notes

- [P] tasks = different files, no dependencies.
- Verify every test task FAILS before implementing against it.
- Commit after each task or logical group, staging the enumerated trio for
  bookkeeping commits and never the workflow directory.
- **No task adds a file outside the Declared File Operations block at
  plan.md:99-115.** If the decomposition appears to require one, stop and
  escalate rather than expanding the slice.
- **No tracked script or test filename may contain a live spec-family token.**
  `tests/speckit-pro/unit/test-unit-layout.py:144-149` matches
  `<family>[-_]\d{3}[a-z]?` against families derived from `docs/ai/specs/**`, so
  `art-006` in a filename is a hard failure;
  `test-autopilot-stage-resolution.py` does not match at all.
- **Non-goals crossed: none.** Every task was checked against the design
  concept's Non-goals — no task creates a draft pull request, sweeps review
  feedback, implements the scaffold-side chain, changes gate pass/fail
  semantics, truncates the canonical task list, adds a harness stop hook, or
  introduces a Bash dependency.
- **Settled decisions re-opened: none.** The `skipped:` marker token, the
  additive-only Codex rule, fail-fast pre-flight conflict handling, `--stage
  implement` re-running Phase 0, and the documentation-only chain contract are
  all consumed as settled, not re-derived.
