---
description: "Task list for Draft-PR Emission (ART-007)"
---

# Tasks: Draft-PR Emission

**Input**: Design documents from `specs/art-007-draft-pr-emission/`

**Prerequisites**: plan.md (16 declared file operations), spec.md (13 FRs, 3 user
stories, 8 success criteria), research.md (15 decisions), data-model.md (6
entities), contracts/ (4 contracts)

**Tests**: Requested. This feature is implemented test-first. Every new helper
branch and every new fixture path gets its failing test before implementation.
Tests live under `tests/speckit-pro/` — repository-only, never inside the shipped
plugin directory — and every test filename is an existing one named for durable
behavior, never for the spec ID.

**Verification commands**: `python3 tests/speckit-pro/run-all.py` is both
UNIT_TEST and FULL_VERIFY. There is no build, typecheck, or lint step; the stack
is Markdown, JSON, and standard-library Python. Iterate with
`--layer 4` (helpers, schemas, fixtures) or `--layer 1` (structural, payload).

**Reviewability**: The plan ratified this as one vertical slice and T004 records
that verdict rather than reopening it. Machine gates pass — `estimate-reviewable-loc`
returns 0 projected against 400/800 thresholds, and the advisory spec-size
estimator returns `{"estimated_loc": 335, "suggested_slices": 1, "status": "ok"}`
at the spec's projected ten production files and
`{"estimated_loc": 355, "suggested_slices": 1, "status": "ok"}` at the plan's
eleven — `ok` and one slice at either input.
By hand count the change is 16 files (11 under `speckit-pro/`, 5 under
`tests/speckit-pro/`), one above the 15-file warn line and well under the 25-file
block line. Primary surface harness/adapter, secondary docs/process — one primary
surface, so the multi-surface rule holds. **Split decision: no split.** Task
generation added no file beyond the sixteen the plan declares.

**Organization**: Tasks are grouped by user story so each story can be
implemented, tested, and delivered independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact repo-relative file paths in descriptions

## Path Conventions

This is a coding-agent plugin repository, not a `src/` application:

- **Shipped plugin**: `speckit-pro/` — skills, agents, reference docs, runner helpers
- **Claude surface**: `speckit-pro/skills/`, `speckit-pro/agents/`
- **Codex surface**: `speckit-pro/codex-skills/`, `speckit-pro/codex-agents/`
- **Repository-only tests**: `tests/speckit-pro/unit/`
- **Generated, never hand-edited**: `dist/claude/**`, `dist/codex/**`, installed-cache
  proofs, payload evidence, generated docs reference pages

## Boundaries This Task List Must Not Cross

Carried from the spec's Out of Scope and the design concept's Non-goals. No task
below crosses them, and several encode them as explicit negative constraints:

- **No edit to any of the twelve governed Layer 6 corpus agent definitions**,
  including `uat-runbook-author`. Copying its frontmatter shape is safe; editing
  its file is not. T034 verifies the corpus digest chain did not move.
- **No state-file mirror** of the draft-PR identity. The workflow file is the
  sole store (T024).
- **No release-note fence** in a draft PR body (T021).
- **No hosting layer** for artifacts. They are committed and opened locally.
- **No `gh pr reopen` from automation.** It is prose in the operator's resume
  path only (T041).
- **No second pull request** in any discrepancy class (T041).
- **No `jq`, and no `--jq` flag, in any prose that lands under `speckit-pro/`.**
  The active-path guard at
  `speckit-pro/speckit_pro_runner/gates/active_path_guard.py` matches `--jq` as a
  jq command dependency, and `speckit-pro/` is one of its scan roots, so a `--jq`
  example copied into `phase-execution.md`, either `SKILL.md`, or an agent
  definition fails Layer 4. There are zero `--jq` uses in shipped source today.
  The corroboration observation takes `--json` and the helper parses it
  (T036, T039); constitution VI requires a structured parser either way.

---

## Phase 1: Setup (Worktree Preflight)

**Purpose**: The three facts the repository's worktree preflight names. The test
suite itself needs no bootstrap.

- [ ] T001 Establish the green baseline before any edit: run `python3 tests/speckit-pro/run-all.py` and confirm Layers 1, 4, and 5 finish with zero failures, so every later failure is attributable to this change
- [ ] T002 [P] Install docs-site dependencies once for this worktree with `pnpm --dir docs-site install --frozen-lockfile`, required before the `reference:generate` that three tracked `.py` changes under `tests/speckit-pro/` will make necessary in T049
- [ ] T003 [P] Define the generated-artifact merge driver for this clone with `git config merge.generated.name "keep ours; regenerate after merge"` and `git config merge.generated.driver "exit 0"` — driver code cannot be committed, so an undefined driver leaves `.gitattributes` rules inert

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The draft mode on the pull-request packet contract. This is the
shared prerequisite the emission surface stands on: User Story 1 cannot open a
draft pull request from a packet the validator rejects.

**⚠️ CRITICAL**: User Story 1 cannot begin until this phase is complete.

The relaxation lands in **two independent places** per research D2 — the JSON
schema, and the read-only validator's hand-written evidence assertions, which are
not schema-driven. Relaxing one without the other ships a draft mode incapable of
passing its own validator; this is the single most likely defect in the feature.

- [ ] T004 Record the ratified reviewability verdict in the implementation notes before any implementation begins: restate plan.md's settled result — machine gates pass (`estimate-reviewable-loc` projects 0 by its own production-file definition; the advisory estimator returns 335 LOC and 1 suggested slice at the spec's projected ten production files and 355 LOC and 1 suggested slice at the plan's eleven, `ok` at both), hand count is 16 total files, one above the 15-file warn line and under the 25-file block line, and the **split decision is no split**. Do not recompute a fresh verdict: the hand count of 11 production files would otherwise trip a naive block reading that the plan already ratified against
- [ ] T005 [P] Capture the SC-008 baseline: run `python3 tests/speckit-pro/run-all.py --layer 4` and record the pre-change outcome of every existing `pr-packet` fixture assertion (one valid `single`, six invalid `single` variants, one valid `split`) in terminal output only — add no file to the repository
- [ ] T006 [P] Author the paired draft fixture `tests/speckit-pro/unit/fixtures/pr-packet/valid-draft.json` and `tests/speckit-pro/unit/fixtures/pr-packet/bodies/valid-draft.md`: `"mode": "draft"`, empty `verification_evidence`, empty `scope_evidence.changed_files`, empty `uat.how_to_uat`, no `split_slice`, and `required_headings` of exactly `["Artifacts", "Resume"]`. The body carries only the Artifacts index table and the Resume block. Generate the two together — `protected_body_fingerprint.value` is a sha256 over the normalised body (LF endings, rstrip, final newline) and the binding is pairwise, with no digest manifest for this directory (FR-005, FR-008)
- [ ] T007 Write the five failing draft-validation tests in `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` per contracts/draft-packet-mode.md section 6: a valid draft packet passes with no verification, changed-file, or UAT evidence; a draft packet carrying `split_slice` fails; a draft body missing either required heading fails; a draft body whose `Artifacts` table carries only gap rows still passes, which is the deterministic half of FR-004's zero-artifact fail-open mandate and the only part of it a unit test can reach — build that body variant in memory, leaving the fixture pair as the populated case so no fixture is added; an unknown `mode` value is still rejected. Confirm all five FAIL before implementing (FR-005, FR-008, FR-004)
- [ ] T008 Add `"draft"` to the `mode` enum at **both** schema sites in `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`: `properties.mode` becomes `["single", "split", "draft"]` and `$defs.validation_result.properties.mode` becomes `["single", "split", "draft", null]`. The validation-result copy is what the write-side validator stamps onto persisted evidence; omitting it makes a valid draft packet's own validation record unrepresentable (FR-005)
- [ ] T009 Add the draft relaxation as a **second** `allOf` branch in `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`, alongside the existing `split_slice` branch and never merged into it: under `mode == "draft"`, `verification_evidence` accepts `minItems: 0`, `scope_evidence.changed_files` accepts `minItems: 0`, and `uat.how_to_uat` accepts any string. Requiredness is relaxed but presence is not — all three keys stay in their `required` lists so `additionalProperties: false` and the object shapes are untouched. Leave the `split_slice` branch and its `else` arm byte-identical (FR-005, SC-008)
- [ ] T010 [P] Make the two hand-written evidence assertions mode-aware in `speckit-pro/speckit_pro_runner/helpers/read_only.py` by guarding `evidence.verification` and `evidence.scope.changed_files` behind `data.get("mode") != "draft"`. These two are not schema-driven; no other assertion in the validator consults evidence contents (FR-005, research D2)
- [ ] T011 Verify the foundation: run `python3 tests/speckit-pro/run-all.py --layer 4` and confirm the five T007 tests now pass **and** every fixture outcome recorded in T005 is unchanged. A green draft test beside a changed `single` expectation is a regression, not a pass (SC-008)

**Checkpoint**: Draft mode validates. User Story 1 can begin.

---

## Phase 3: User Story 1 - Plan stage ends at an open draft pull request (Priority: P1) 🎯 MVP

**Goal**: Turn a private branch state into a review surface. The plan stage
commits its artifacts, opens a draft pull request whose description indexes them,
records that pull request's identity on the workflow file, and stops with a
report the operator can act on without hunting.

**Independent Test**: Run a plan stage to completion with the final gate
resolving pass. Confirm a draft pull request exists for the branch, its
description carries an artifacts index and a resume/status block, the workflow
file carries the pull request's number and URL, and the stop report repeats the
URL, the index, and the resume instruction. **This must hold even when zero
artifacts were generated** — which is why this story, not User Story 2, owns the
three-sink fail-open structure.

### Tests for User Story 1 ⚠️

> Write these FIRST and confirm they FAIL before implementing.

- [ ] T012 [P] [US1] Write the five failing `Draft PR` row-reader tests in `tests/speckit-pro/unit/test-autopilot-stage-resolution.py` per contracts/draft-pr-row.md section 7: a present row parses to the right number, URL, and gap note; an absent row returns `None` and is not an error; a commented-out row is not read as present; a row with a gap note after the link still parses the identity; a malformed value yields `None` rather than a traceback. Build workflow-file text in memory as the shipped suite already does — add no fixture files. Confirm all five FAIL (FR-009)
- [ ] T013 [P] [US1] Write the failing draft-emission tests in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`: `pr-packet-output` emits a draft packet and its paired body; the mode gate rejects an unknown mode naming field `mode`; `required_headings` for draft is exactly `Artifacts, Resume` while `single` and `split` keep today's eight in today's order. Confirm they FAIL (FR-005, FR-008)

### Implementation for User Story 1

- [ ] T014 [US1] Add the draft value to the mode gate in `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`: accept `single`, `split`, or `draft`, and reject anything else through `invalid_packet_input` with `field="mode"`. The default when `mode` is absent stays `"single"` — draft mode is never implicit (FR-005)
- [ ] T015 [US1] Give `required_headings()` a `mode` parameter in `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`: draft returns the two FR-008 blocks (`Artifacts`, `Resume`); every other value returns today's eight in today's order. The call site already threads the result through as packet data, so the body structure checker needs no change at all. Add no `split_slice` analogue for draft — draft mode attaches no new required sub-object (FR-008)
- [ ] T016 [P] [US1] Add `workflow_draft_pr_row(lines)` beside the shipped `workflow_recorded_stage(lines)` in `speckit-pro/speckit_pro_runner/helpers/read_only.py`, reusing `workflow_table_rows` and `AUTOPILOT_BASIC_INFO_HEADING` unchanged. Match the key case-insensitively after stripping `*`, backticks, and spaces; return the parsed `{number, url, gap_note}` or `None` when the row is absent. Keep this to three near-duplicate lines — do **not** introduce a generic `workflow_scalar_row(lines, key)` abstraction until a third caller exists (FR-009, constitution VI)
- [ ] T017 [P] [US1] Add a `## The Draft PR Entry` section to `speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md`, modelled on the adjacent `## The Stage Entry`: placement in `## Specification Context` → `### Basic Information` and never in `## Workflow Overview` (whose rows are phase status records), the grammar `| **Draft PR** | [#<number>](<url>) |` with an optional gap note after the link in the same cell, the two legal states, and the write rules (FR-009)
- [ ] T018 [US1] Write the terminal-step emission sequence into `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` in FR-013's exact order: generate the artifacts, take the existing stage-boundary commit, push the branch, create or refresh the draft pull request, write the draft-PR record, then take a **separate** bookkeeping commit carrying that record and push it. Leave the stage-boundary commit's message (`chore(SPEC-XXX): close the plan stage boundary`), its staged path set, and its non-emptiness byte-identical, and keep the draft-PR record out of it. The bookkeeping commit stages the workflow **file**, never the workflow directory, which also holds untracked run byproducts. State that no step is retried automatically, that the operator re-run is the recovery path, and that a re-run reaching an already-committed step takes a no-op commit that the sequence continues past rather than treating as a failure (FR-013)
- [ ] T019 [US1] Add the strict-mode short-circuit to `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` as a **return before generation**, not a wrapper around it: on a blocked final gate under strict mode, preserve the shipped contract byte-for-byte — the boundary commit is still taken, a non-terminal blocked `Confidence Gate` row is recorded, the stage STOPs — and open no pull request and generate no artifact pages (FR-006)
- [ ] T020 [US1] Write FR-007's two-way existence test and create-or-refresh into `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`: before creating, test **both** the workflow file's `Draft PR` row and a live query for an open pull request on the head branch, and treat either positive as proof one exists, because the record is written after creation and an interrupted run leaves a pull request with no record. When an open pull request exists, refresh its description and its title if the title changed, repair or write the record, and report that existing URL. Create only when neither positive fires. Self-validate the final-shape conventional title (`<type>(<lowercase-scope>): <plain English description>`, scope lowercase per research D4) through the release-readiness title check **before** creation, and on failure refuse to create and report through FR-010's could-not-be-opened path (FR-007, SC-007)
- [ ] T021 [US1] Write the FR-008 body composition into `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`: the description carries exactly two blocks — an artifacts index table with Artifact, Purpose, and a copy-paste Open command, and a resume/status block. The orchestrator builds both and passes the finished Markdown as `inputs.body`, used verbatim, so the `build_packet_body` fallback is never reached in draft mode. Forbid explicitly: a release-note fence, any verification, scope, or UAT section, and any placeholder final-writeup content. The draft PR's checks do not run while it is in draft state, so no fence is needed or wanted (FR-008)
- [ ] T022 [US1] Write the FR-004 three-sink fail-open structure into `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`: a generation failure of any size still opens the pull request, with the shortfall visible in the index (gap-marked rows — one per selected page, or a single whole-set row when selection itself could not run), in the stop report, and in the workflow row's gap note. Every gap row names what is missing and why, so the same shortfall is legible in all three sinks. A run producing zero artifacts still opens the pull request and its index table is present under its heading carrying only gap rows, never omitted and never empty. State the sink-reachability rule with it: each sink binds only the runs that reach it, so a run that stops at create-or-refresh under an FR-011 discrepancy or before creation under an FR-013 sequence failure writes no description and no row, and its shortfall reaches the stop report alone — that is the run not getting there, not a fail-open violation. The stop report is the one sink every such run reaches (FR-004, SC-003)
- [ ] T023 [US1] Write five of FR-010's six stop-report shapes into `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` — the sixth, the corroboration-discrepancy shape, is T041's, and T045 sweeps all six for wording consistency: emission ran (URL, artifact index, resume instructions); gate blocked (the blocked gate named in place of a URL); pull request could not be opened (say so, name the resume path, note the artifacts are already committed); branch push failed (name the failed push, state that no pull request was opened and no `Draft PR` row was written); bookkeeping commit or its push failed after create-or-refresh (carry the URL, say the record did not reach the remote). Each failure shape names the step that failed, the state it left behind, and the resume path (FR-010, SC-006)
- [ ] T024 [US1] Write the FR-009 `Draft PR` row write rules into `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`: written only after creation or refresh succeeds, carried by the bookkeeping commit and never folded into the boundary commit, repaired when a pull request exists but the row is missing or wrong, and **rewritten whole from the current run's outcome every time** so a stale gap note never survives a refresh that no longer fell short. State that the workflow file is the only place this identity is stored — **no state-file mirror** — and that writing this row neither counts against nor re-triggers the `Stage` row's own write cadence, because the two are matched by key and this identity has no mirror to keep in step (FR-009)
- [ ] T025 [US1] Mirror the emission sequence and both gate arms into `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` in the Codex mirror's own voice: the FR-013 order with its preserved boundary commit and separate bookkeeping commit, the FR-006 strict-mode short-circuit before generation, and the FR-007 two-way existence test with title self-validation. The two files are independently written mirrors, not line-for-line equivalents, and no test compares their prose — verify by hand against T018, T019, and T020 (FR-006, FR-007, FR-013)
- [ ] T026 [US1] Mirror the body contract, the three-sink fail-open structure with its sink-reachability rule, the same five of FR-010's six stop-report shapes T023 writes (T042 mirrors the sixth), and the `Draft PR` row rule into `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`. The row rule rides this file on Codex rather than the protocol mirror, because `workflow-file-protocol-codex.md` carries no `Stage` entry section — Codex documents the `Stage` row here, and following each platform's existing home costs one file per platform (FR-004, FR-008, FR-009, FR-010)
- [ ] T027 [US1] Verify User Story 1 deterministically: run `python3 tests/speckit-pro/run-all.py --layer 4` and confirm the T012 row-reader tests and the T013 packet-producer tests pass with the T005 baseline still unchanged. The live end-to-end arm of this story's independent test is quickstart Scenario 5, run in T052

**Checkpoint**: A pass or warn plan stage ends at an open draft pull request with an indexed body, a recorded row, and an actionable stop report — including with zero artifacts. This is the MVP.

---

## Phase 4: User Story 2 - Planning artifacts are authored from the planning record (Priority: P2)

**Goal**: A dedicated authoring subagent reads the feature's planning record,
picks which shipped draft-stage templates apply, fills their marked regions, and
writes the finished pages into the feature's `artifacts/` directory so they ride
the same commit as the rest of the stage.

**Independent Test**: Point the authoring step at a feature whose planning record
is complete, run it alone, and confirm the expected set of pages is written into
the `artifacts/` directory with their marked regions filled and no placeholder
text left behind. Force one template to fail and confirm the remaining pages are
still written.

**Depends on**: User Story 1's three-sink structure (T022), which this story feeds
real per-entry outcomes into. Emission already fails open, so this story layers
content onto a hand-off that already works.

- [ ] T028 [P] [US2] Create `speckit-pro/agents/artifact-author.md`: YAML frontmatter mirroring the `uat-runbook-author` shape confirmed on disk in research D11 — `model: sonnet`, a distinct `color`, `disallowedTools: Skill, Agent, TeamCreate, SendMessage`, `maxTurns: 30`, `effort: max` — with `name: artifact-author` matching the filename stem and the `^[a-zA-Z0-9][a-zA-Z0-9-]{2,49}$` pattern, and a trigger-quality `description` naming when to dispatch and the fail-open promise. Then write the body: the six inputs (spec, plan, tasks, design concept, gallery manifest, templates), manifest-driven selection, the fill rules, the output path, and the per-entry result. **Copy `uat-runbook-author`'s shape; never edit its file** — it is inside the governed corpus (FR-001, FR-002, FR-003)
- [ ] T029 [P] [US2] Create `speckit-pro/codex-agents/artifact-author.toml`: flat TOML with no frontmatter fence, carrying `name` (`artifact-author`, matching the filename stem exactly), `description`, `model = "gpt-5.5"`, `model_reasoning_effort = "xhigh"`, `sandbox_mode = "workspace-write"` (the agent writes files), and `developer_instructions` holding instructions identical in substance to T028's body. Include **none** of the Claude-only fields `tools`, `disallowedTools`, `permissionMode`, `color`, `maxTurns`, `background`, `effort` — the Codex agent validator sweeps for them (FR-001)
- [ ] T030 [P] [US2] Add `"artifact-author.toml"` to `REQUIRED_CODEX_AGENT_NAMES` in `speckit-pro/speckit_pro_runner/helpers/install.py`. The frozenset is closed in both directions — the bundle loader fails with `incomplete_agent_bundle` on a missing file **or an unexpected one** — so shipping the TOML without this edit makes every Codex install refuse the bundle (research D10)
- [ ] T031 [US2] Confirm the existing bundle-loader coverage still holds without adding a test file: the test in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` copies the real `speckit-pro/codex-agents/` directory, deletes one file, and asserts `incomplete_agent_bundle`, pinning no literal filename list — so the new agent and the frozenset move together and the assertion stays true. Run `python3 tests/speckit-pro/run-all.py --layer 4` to prove it (constitution IV)
- [ ] T032 [US2] Write the artifact-generation dispatch into `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` as the first step of the FR-013 sequence: dispatch `artifact-author`, filter the gallery manifest to `stage: "draft-pr"` entries and apply each entry's trigger (`implementation-plan` and `spec-explainer` always; `code-approaches` only on `competing_approaches`; `module-map` only on `brownfield_change`), then feed the per-entry `generated` or `gap` outcomes into the three sinks T022 built. A page with any unfilled slot counts as a **gap for that page, not a partial success**. Templates and the manifest are read-only inputs — writing into `speckit-pro/artifact-gallery/` is a defect (FR-002, FR-003, FR-004)
- [ ] T033 [US2] Mirror the artifact-generation dispatch and its selection routing into `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` (FR-002, FR-003, FR-004)
- [ ] T034 [US2] Verify User Story 2 in quickstart Scenario 4's command order, which matters because Layer 1 payload conformance checks shipped bytes: run `python3 scripts/refresh-release-artifacts.py` **first**, then `python3 tests/speckit-pro/run-all.py --layer 1`, then `--layer 4`. Confirm both new definitions pass the payload frontmatter sweep, Claude/Codex agent existence parity passes, the Codex install helper accepts the bundle, and the Layer 6 corpus governance test still reports exactly twelve roles with **no** `source digest does not match role source bytes` failure — that error would mean a governed agent definition was edited, which this feature forbids

**Checkpoint**: User Stories 1 and 2 both work. The pull request now carries real content, and a generation failure still cannot prevent the hand-off.

---

## Phase 5: User Story 3 - Stage auto-detect corroborates the recorded pull request (Priority: P3)

**Goal**: On resume, stage auto-detect reads the draft-PR record, checks it
against the live pull request, and when the two disagree logs the discrepancy and
proceeds using the workflow file's value, which is authoritative.

**Independent Test**: Seed a workflow file with a draft-PR record, run stage
auto-detect against a matching live pull request, and confirm the stage resolves
with no discrepancy logged. Repeat against a record that cannot be corroborated
and confirm a discrepancy is logged while the workflow file's value is the one
used.

**Depends on**: `workflow_draft_pr_row` from User Story 1 (T016), which supplies
the recorded identity this story corroborates.

- [ ] T035 [P] [US3] Write the failing corroboration tests in `tests/speckit-pro/unit/test-autopilot-stage-resolution.py` per contracts/stage-corroboration.md section 8: each of the six statuses produced by its own input; the precedence rule that an extra open pull request outranks a missing recorded number; `ok: false` yielding `skipped` and never a discrepancy for each reason class; an absent `Draft PR` row yielding `no_record` with no observation taken; a malformed observation yielding `skipped` rather than a traceback; the resolved `stage` identical with and without the observation; and the eight pre-existing envelope keys unchanged. Build workflow text in memory — no new fixture files. Confirm they FAIL (FR-011)
- [ ] T036 [US3] Add the optional `pr_observation` input key to `resolve-autopilot-stage` in `speckit-pro/speckit_pro_runner/helpers/read_only.py`, read from the stdin JSON request's `inputs` (argv stays reserved for `--help` and `--version`). Fail closed on evidence and open on outcome: anything other than `ok: true` with a parseable `pull_requests` array yields `skipped` with its `reason`. The tool being absent, unauthenticated, cancelled, rate-limited, or emitting unparseable output are all the same class, and none of them is evidence that a recorded pull request is gone. The helper must never shell out to `gh` or touch the network — no runner helper does today (FR-011)
- [ ] T037 [US3] Implement the six-status classifier in `speckit-pro/speckit_pro_runner/helpers/read_only.py` with contracts/stage-corroboration.md's precedence, first match wins, evaluated only against a successful observation: (1) an open pull request on the head branch whose number differs from the recorded number → `identity_mismatch`; (2) the recorded number open but its live URL differing → `identity_mismatch`; (3) the recorded number closed or merged → `pr_closed` carrying `merged`; (4) the recorded number absent from the observation → `pr_missing`; (5) anything else → `match`. Preconditions run first: an absent row → `no_record` with no observation; an absent or unsuccessful observation → `skipped`. Rule 1 before rule 4 is load-bearing, so a branch that grew a second pull request reports the conflict rather than the absence. The vocabulary is closed at exactly six with no aliases and no alternate casing (FR-011)
- [ ] T038 [US3] Add the `corroboration` object to the `resolve-autopilot-stage` envelope in `speckit-pro/speckit_pro_runner/helpers/read_only.py` carrying `status`, `recorded`, `observed`, `merged`, and `reason`. It is **always present**, so a run that could not check is distinguishable from one that checked and agreed. Leave the eight existing envelope keys untouched, and ensure corroboration never changes the resolved stage, never blocks stage resolution, and never stops the run (FR-011)
- [ ] T039 [P] [US3] Add the Step 0.6c corroboration prose to `speckit-pro/skills/speckit-autopilot/SKILL.md`: take one read-only observation per run — `gh pr list --head <branch> --state all --json number,url,state,isDraft,headRefName` — **only when the `Draft PR` row is present**, pass it to `resolve-autopilot-stage` as `pr_observation`, and print one `Draft PR: <status> — ...` line beside the `Stage:` line the step already prints. Record that same line durably in the workflow file's Step 0.6c record for the three discrepancy statuses only, written in the same edit turn as the `Stage` row so it lands in the same commit; `match`, `no_record`, and `skipped` write nothing durable. Scope the trigger to the row's presence, not the stage — it runs on an explicit `--stage` argument and on a resolved stage other than plan, where the status is still reported and a discrepancy still recorded (FR-011)
- [ ] T040 [US3] Mirror the Step 0.6c corroboration prose into `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`, keeping the observation, the report line, the discrepancy-only durable write, and the row-presence trigger identical to T039 (FR-011)
- [ ] T041 [US3] Add the terminal-step consequences for all six statuses to `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`: `match` refreshes the recorded pull request and reports its URL; `no_record` falls through to FR-007's live existence test; `skipped` **never creates** — the present row is already a positive under the two-way test — refreshing when the tool is reachable and otherwise reporting through FR-010's could-not-be-opened path. The three discrepancies create nothing, refresh nothing, record nothing, and leave the row exactly as found; each stop report names the discrepancy and the manual resume path (`pr_closed`: the number, the URL, and reopening manually with `gh pr reopen <number>` **as the operator's own step, never automation's**, then re-run; `pr_missing`: the recorded identity, then correct or clear the row and re-run; `identity_mismatch`: both identities, then correct or clear the row and re-run). All three end the attempt at create-or-refresh **after** generation, the boundary commit, and the push — never earlier, because ending earlier would strand the durable discrepancy line that reaches version history only in a commit this stage goes on to take. State that this is fail-open and does not invoke FR-006's blocked-stop contract, that **no second pull request is opened in any discrepancy class**, and that the resolution-time observation and FR-007's emission-time query are two separate reads, so the terminal step must not treat the earlier observation as current evidence — the whole stage runs between them (FR-010, FR-011)
- [ ] T042 [US3] Mirror the six-status terminal-step consequences into `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` (FR-010, FR-011)
- [ ] T043 [US3] Verify User Story 3: run `python3 tests/speckit-pro/run-all.py --layer 4` and confirm all six statuses, the precedence rule, the stage-invariance assertion, and the eight untouched envelope keys pass, and that no unsuccessful observation produces a discrepancy instead of `skipped`

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T044 Document FR-012 in `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` and its Codex mirror: when final reviewability later requires splitting the work across multiple pull requests, the draft pull request becomes the **first slice** of the stack rather than being closed or superseded, so the review thread already collected on it survives. The packet identity is stable across that transition, which is what preserves the thread. Confirm nothing this feature adds closes, supersedes, or recreates the draft pull request (FR-012)
- [ ] T045 Wording-consistency pass across **all six** FR-010 stop-report shapes in both `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` and `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` — the five T023 writes plus the discrepancy shape T041 writes, which FR-010's own enumeration ends on and which must not be left out of the pass: every failure shape names the step that failed, the state it left behind, and the resume path, in the same one-line style Step 0.6c already uses, so the stop report alone is sufficient to hand off (FR-010, SC-006)
- [ ] T046 [P] Verify Claude/Codex prose parity by hand across the four mirrored surfaces — `phase-execution.md` against `phase-execution-codex.md`, and the Step 0.6c blocks in the two `SKILL.md` files. No test compares their prose, so keeping them in step is the author's obligation rather than CI's
- [ ] T047 [P] Verify the two agent definitions say the same thing: `speckit-pro/agents/artifact-author.md`'s body and `speckit-pro/codex-agents/artifact-author.toml`'s `developer_instructions` must be identical in substance on selection, filling, output paths, and failure semantics, with only the runtime primitives differing. No test compares them (FR-001)
- [ ] T048 Run `python3 scripts/refresh-release-artifacts.py` to regenerate `dist/claude/**`, `dist/codex/**`, the runner trust metadata restaled by the `pr_emission.py`, `read_only.py`, and `install.py` edits, the installed-cache fixtures, and the payload evidence. Hand-edit none of it. Note that `--check` compares against the **committed** tree and so exits 1 on a regeneration that is correct but not yet committed; that exit is expected and resolves on commit
- [ ] T049 Run `pnpm --dir docs-site reference:generate` to refresh the generated docs-site test reference, restaled by the three tracked `.py` changes under `tests/speckit-pro/`. `refresh-release-artifacts.py` does not cover this surface
- [ ] T050 Run the full gate `python3 tests/speckit-pro/run-all.py` and confirm Layers 1, 4, and 5 finish with zero failures
- [ ] T051 Run quickstart scenarios 1 through 4, which are deterministic and need no network. Scenario 1 is the tripwire for this feature's most likely single defect: a draft packet must validate with no verification, changed-file, or UAT evidence, which fails if the schema was relaxed but the validator's two hand-written assertions were not
- [ ] T052 **Operator-gated** — run quickstart scenarios 5 through 7 against an installed and authenticated `gh` on a repository fork you are willing to open and close draft pull requests on: the pass and warn arms, the strict-mode block that opens nothing, and Scenario 7's six sub-runs — zero artifacts, partial generation, re-entry with an open pull request, re-entry with a closed one, creation refused by title self-validation, and the two FR-013 sequence failures. An autonomous implement run without `gh` credentials must report this task as not run rather than marking it complete
- [ ] T053 Generate this feature's own implementation PR review packet in `single` mode with what changed, why, non-goals, review order, scope budget, traceability mapping each FR to changed files and verification evidence, verification evidence, known gaps, and rollback notes. This binds the implementation pull request for ART-007, not the draft pull requests the feature emits — those carry only the two FR-008 blocks
- [ ] T054 Validate the exact final pull-request title against the repository release-readiness gate before creating the pull request or marking it ready. The live gate requires `<type>(<lowercase-scope>): <plain English description>`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **blocks User Story 1**
- **User Story 1 (Phase 3)**: Depends on Foundational. The MVP
- **User Story 2 (Phase 4)**: Depends on User Story 1's three-sink structure (T022) and its Codex mirror (T026)
- **User Story 3 (Phase 5)**: Depends on User Story 1's row reader (T016) and its terminal-step create-or-refresh (T020)
- **Polish (Phase 6)**: Depends on all three stories

### User Story Dependencies

Unlike the generic template's assumption, these three stories are **not** fully
independent, and the plan is explicit about why: this is one vertical slice where
every part is inert without the others.

- **User Story 1 (P1)**: Depends only on Foundational. Independently valuable and independently testable — it opens a pull request even with zero artifacts
- **User Story 2 (P2)**: Consumes US1's fail-open sinks. Its own authoring step is independently testable in isolation (write pages into `artifacts/`, force one template to fail)
- **User Story 3 (P3)**: Consumes US1's `Draft PR` row reader. Independently testable in isolation — the classifier is deterministic, offline, and needs no pull request to exist

### Within Each User Story

- Tests are written and confirmed FAILING before implementation
- Helpers before the prose that dispatches them
- Claude surface before its Codex mirror, since the mirror is verified by hand against it
- Story complete and checkpointed before the next priority

### Same-File Serialization

These tasks share a file and must run in sequence, never in parallel:

- `pr-packet.schema.json`: T008 → T009
- `pr_emission.py`: T014 → T015
- `read_only.py`: T010 → T016 → T036 → T037 → T038
- `phase-execution.md`: T018 → T019 → T020 → T021 → T022 → T023 → T024 → T032 → T041 → T044 → T045
- `phase-execution-codex.md`: T025 → T026 → T033 → T042 → T044 → T045
- `test-autopilot-stage-resolution.py`: T012 → T035
- `test-speckit-pro-mutation-helpers.py`: T013 → T031

### Parallel Opportunities

16 of 54 tasks are marked [P]. The largest wins are the two independent test
files at the head of User Story 1 and the three independent agent-registration
files in User Story 2.

---

## Parallel Example: User Story 1

```bash
# The two failing test suites touch different files — write them together:
Task: "Write the five failing Draft PR row-reader tests in tests/speckit-pro/unit/test-autopilot-stage-resolution.py"
Task: "Write the failing draft-emission tests in tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py"

# Once the tests are red, these three surfaces are independent:
Task: "Add workflow_draft_pr_row(lines) in speckit-pro/speckit_pro_runner/helpers/read_only.py"
Task: "Add the Draft PR Entry section to speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md"
# (pr_emission.py's T014 → T015 pair runs as its own serial thread alongside these)
```

## Parallel Example: User Story 2

```bash
# Three registration surfaces, three different files:
Task: "Create speckit-pro/agents/artifact-author.md"
Task: "Create speckit-pro/codex-agents/artifact-author.toml"
Task: "Add artifact-author.toml to REQUIRED_CODEX_AGENT_NAMES in speckit-pro/speckit_pro_runner/helpers/install.py"
```

## Parallel Example: User Story 3

```bash
# The helper thread and the Claude skill prose are independent:
Task: "Write the failing corroboration tests in tests/speckit-pro/unit/test-autopilot-stage-resolution.py"
Task: "Add the Step 0.6c corroboration prose to speckit-pro/skills/speckit-autopilot/SKILL.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — three preflight facts
2. Complete Phase 2: Foundational — draft packet mode, in **both** places
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: a pass or warn plan stage ends at an open draft pull request with an indexed body, a recorded row, and an actionable stop report — including with zero artifacts generated

That stopping point is a real deliverable. The reviewer gets a pull request, a
scope statement, and a resume path even before any artifact page exists.

### Incremental Delivery

1. Setup + Foundational → draft mode validates
2. Add User Story 1 → the hand-off exists → **MVP**
3. Add User Story 2 → the hand-off carries real content
4. Add User Story 3 → resume corroborates the record
5. Polish → regenerate, verify parity, run the gate

### Sequencing Note

Do not parallelize the three stories across separate workers. They share
`phase-execution.md` and `phase-execution-codex.md` heavily, and both files are
long reference documents where concurrent edits collide. Run the stories in
priority order and take the [P] wins inside each one.

---

## Notes

- [P] = different files, no dependencies on incomplete tasks
- Every test file above is an existing file named for durable behavior; the two
  new fixtures follow the shipped `valid-<mode>.json` convention. No filename is
  coupled to the spec ID
- `suite-manifest.json` needs no new entry — no new test file is added
- Confirm tests FAIL before implementing; a test that passes before the change
  is testing something else
- Commit after each task or logical group
- The generated-artifact contract is T048 and T049, not an assumption. CI's
  `artifact-consistency` job fails the pull request if the regeneration is skipped
- `chore(SPEC-XXX): close the plan stage boundary` in T018 is the shipped commit
  message template quoted verbatim, where `SPEC-XXX` is substituted at runtime.
  It is not a placeholder left in this document
