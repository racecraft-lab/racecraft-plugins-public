---
description: "Task list for ART-008 slice 2 — Artifact Freshness"
---

# Tasks: ART-008 slice 2 — Artifact Freshness

**Input**: Design documents from `specs/art-008-feedback-sweep-slice-2/`

**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories),
`research.md`, `data-model.md`, `contracts/check-artifact-freshness.md`,
`quickstart.md`

**Tests**: Test tasks are included and are mandatory. `spec.md` FR-031 requires
Layer 4 fixture-driven unit coverage for the freshness helper, and FR-033a
requires the same of the corroboration surface. Every helper task below follows
strict TDD: write the fixture case, run the targeted test and confirm it FAILS,
then implement, then run it again and confirm it PASSES.

**Reviewability**: This slice crosses **one warn and no block**. The binding
figure is `plan.md` §"Reviewability Budget, derived by hand": ~690 production
reviewable LOC against a 400 warn, 5 production files against a 6 warn, 12
authored files against a 15 warn, one primary surface. The plan-phase
estimator's `{"status":"pass","projected":0}` is an **absent measurement**, not
evidence of fitness, and MUST NOT be cited as one. T014 is the mandatory
checkpoint that records this before implementation begins.

**Organization**: Tasks are grouped by user story so each story can be
implemented and verified as an increment.

**Success criteria**: Task-level citations name an `SC-` id only where a single
task discharges that criterion outright — T055 (SC-003), T071 (SC-008), T079
(SC-005), T080 (SC-007). The other four are satisfied across several tasks
rather than by one, so the binding map is the traceability table in
`quickstart.md` §Traceability, which covers all eight. Read that table, not this
list, to check success-criteria coverage.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete work)
- **[Story]**: `US1`, `US2`, `US3` — maps to the user stories in `spec.md`
- Every task names an exact repo-relative file path

## Path Conventions

Repository root is the base for every path. This is a plugin marketplace repo,
not a `src/`-shaped application:

- Plugin source: `speckit-pro/`
- Repository-only tests: `tests/speckit-pro/`
- Generated payloads and proofs: `dist/`, and the runner trust metadata under
  `speckit-pro/speckit_pro_runner/`
- Docs site: `docs-site/`

## Verification commands

| Name | Command | When |
|---|---|---|
| `HELPER_TEST` | `python3 tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` | registration and inventory work |
| `FRESHNESS_TEST` | `python3 tests/speckit-pro/unit/test-artifact-freshness.py` | every helper red/green cycle |
| `LAYER1` | `python3 tests/speckit-pro/run-all.py --layer 1` | reference prose and structural parity |
| `LAYER4` | `python3 tests/speckit-pro/run-all.py --layer 4` | broader unit sweep after a helper phase |
| `FULL_VERIFY` | `python3 tests/speckit-pro/run-all.py` | **once**, in Polish, after regeneration |

> **Do not run `FULL_VERIFY` mid-phase.** Any edit to `speckit-pro/` source
> reddens roughly six gate tests on stale `dist/` payloads and proof hashes
> until `python3 scripts/refresh-release-artifacts.py` runs in T075. Mid-phase,
> gate on the targeted command named in the task.

## Locating shipped sentences: they are hard-wrapped

Several tasks below say to locate a shipped sentence by its text "since line
numbers drift". Read this before trying it. The shipped reference prose is
hard-wrapped at roughly 76 columns, so most target sentences span two lines and
**a grep for the quoted sentence returns nothing**. Search the single-line
fragment instead. Each fragment below was measured in this worktree and matches
exactly once on the surface named.

| Task | Target sentence | Greppable fragment (one match) |
|---|---|---|
| T048 | FR-027 stop-report clause, Claude | `states that the draft artifact pages regenerate once` |
| T048 | FR-027 meta-paragraph, Claude | `interface slice 2 replaces` |
| T049 | FR-027 clause, Codex | `the draft artifact pages regenerate once slice 2 lands` |
| T049 | FR-027 meta-paragraph, Codex | `interface slice 2 replaces` |
| T052 | FR-015b enumeration 1, the reply-point dichotomy, both surfaces | `stop aborts before the` |
| T052 | FR-015b enumeration 2, the run-ending conditions, both surfaces | `conditions that end a run in this sequence` |
| T053 | FR-015d redaction-stop trigger, both surfaces | `every commit is pushed and every` |
| T066 | FR-024a one-line-report sentence, both surfaces | `as a one-line report` |
| T067 | FR-022 invariant, both surfaces | `The sweep never writes the` |
| T068 | FR-033b sentence, both surfaces | `reads that report rather than taking an observation of its` |
| T069 | FR-033b's second target, `speckit-pro/skills/speckit-autopilot/SKILL.md` | `one read-only observation` |

The line numbers the tasks cite are correct as measured, but they drift as the
preceding prose tasks land. The fragments do not.

## Non-goals guard (from the design concept, carried into every phase)

No task below crosses any of these. Each is restated so a reviewer can check
the claim rather than take it:

| Non-goal | Where the task list honours it |
|---|---|
| No slice-1 behavior change | Every prose task adds a **sentence**; none rewrites or deletes shipped text except the two FR-027 promise passages, which slice 1 itself declared an interface slice 2 replaces. FR-020's bookkeeping-commit rule and slice 1's reply behavior are untouched (T039, T041). |
| No content-hash staleness | The verdict surface joins on supplied ancestry records only (T027). FR-002 forbids hashing, and no task computes or compares page bytes. |
| No second bookkeeping store | The helper reads exactly one path, the workflow file (T026, T027, T037). The FR-018a snapshot is run-scoped transport, always removed, never read as a record (T042). FR-003 is asserted in T027 and re-checked in T072. |
| No second `Draft PR` row writer | The sweep writes no row. FR-014's refresh changes the cell **through the emission machinery**, and FR-039 records it on the machinery's own commit (T041, T044). T067 scopes the shipped "never writes the row on any path" sentence rather than qualifying it. |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a known-green baseline and satisfy the worktree
preflight the later regeneration tail depends on.

- [ ] T001 Record the pre-change baseline by running `python3 tests/speckit-pro/run-all.py` from the repository root and capturing the pass/fail counts into the workflow record; a red baseline must be resolved or explicitly noted before any source edit, so that later failures are attributable to this slice
- [ ] T002 [P] Install docs-site dependencies once for this worktree with `pnpm --dir docs-site install --frozen-lockfile`, the prerequisite for the `pnpm --dir docs-site reference:generate` in T077
- [ ] T003 [P] Configure the generated-artifact merge driver for this clone with `git config merge.generated.name "keep ours; regenerate after merge"` and `git config merge.generated.driver "exit 0"`, so a later `git merge origin/main` resolves `dist/` and proof paths without text-merging content hashes

**Checkpoint**: Baseline recorded, docs-site installed, merge driver defined.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Register `check-artifact-freshness` and wire its test inventory.
Every user story rests on this registration existing.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

**⚠️ Two order-sensitive hazards, named so they are not discovered by failing**
(`plan.md` §Project Structure, `contracts/check-artifact-freshness.md`
§Registration checklist): `fixture-manifest.json` is compared for **exact list
equality** against `EXPECTED_HELPERS`, so the new entry must sit at the same
index in both; and the bash-reference id list is asserted equal to
`EXPECTED_HELPERS` minus `NO_BASH_ANCESTOR`, so omitting the `NO_BASH_ANCESTOR`
addition fails an assertion a reader would not expect.

- [ ] T004 [P] Create the request fixture `tests/speckit-pro/unit/fixtures/read-only-helpers/requests/check-artifact-freshness.json` carrying a complete valid `verdict`-surface request (`schema_version`, `helper_id`, `operation`, `mode: read_only`, and `inputs` with `workflow_file` plus an `artifacts_observation` whose `ok` is the JSON literal `true`), modelled on the sibling `requests/sweep-pr-feedback.json` (FR-004)
- [ ] T005 [P] Create the Layer 4 module `tests/speckit-pro/unit/test-artifact-freshness.py` with the fixture-loading harness only — no cases yet — following the pattern `tests/speckit-pro/unit/test-feedback-sweep-parse.py` established, reading `freshness-cases.json` and `expected-envelopes.json` and asserting each case's envelope (FR-031)
- [ ] T006 [P] Create the empty-but-valid fixture pair `tests/speckit-pro/unit/fixtures/artifact-freshness/freshness-cases.json` and `tests/speckit-pro/unit/fixtures/artifact-freshness/expected-envelopes.json`, so T005's harness loads and the directory is named for durable behavior rather than for the spec id (FR-031)
- [ ] T007 [P] Append `"check-artifact-freshness"` to `EXPECTED_HELPERS`, add it to `NO_BASH_ANCESTOR`, and add its `HELPER_CASES` entry supplying `workflow_file` and a valid `artifacts_observation` in `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py`; record in a comment beside the `NO_BASH_ANCESTOR` addition that this is new behavior with no deleted `.sh` ancestor and that inventing a `source_script` would record a lie in a provenance manifest (FR-004)
- [ ] T008 Append the matching `check-artifact-freshness` record to `tests/speckit-pro/unit/fixtures/read-only-helpers/fixture-manifest.json` **at the same index** it occupies in `EXPECTED_HELPERS`, carrying `promotion_status`, `failure_classes`, `rejected_stdout_schema`, `deterministic_remediation`, `subprocess_policy`, `path_boundary_policy`, `authoritative_command` pointing at T004's fixture, and `rollback`, shaped on the `sweep-pr-feedback` record (FR-004)
- [ ] T009 [P] Declare `tests/speckit-pro/unit/test-artifact-freshness.py` as a Layer 4 member in `tests/speckit-pro/suite-manifest.json` (FR-031)
- [ ] T010 Run `HELPER_TEST` and confirm it FAILS on the unregistered helper id, recording which assertions are red so the green in T013 is checked against a known list (FR-004)
- [ ] T011 [P] Add the `check-artifact-freshness` `HelperEntry` to `speckit-pro/speckit_pro_runner/helpers/registry.py` beside `sweep-pr-feedback`, with `script` as `None`, promotion `python_authoritative`, comparison `python_only`, and `authoritative_request("check-artifact-freshness")` (FR-004)
- [ ] T012 [P] Add the three registration touch points plus the surface router to `speckit-pro/speckit_pro_runner/helpers/read_only.py`: the allowed-path-inputs entry `{"workflow_file"}`, an argument-derivation branch returning `[]` because the whole request arrives on stdin and no field is interpolated into a command, the dispatch-table entry, and a `check_artifact_freshness` router over a **closed** `named_surface` set of `verdict` / `removal_diff` / `corroborate_refresh` where absent-or-explicit-`null` means `verdict` (tested with `is None`, not truthiness, so the empty string stays an input error) and a fourth value is a malformed request rather than a surface to discover; the three surface bodies stay stubs here (FR-004, FR-028)
- [ ] T013 Run `HELPER_TEST` and confirm the registry-level and inventory assertions now PASS — `test_fixture_manifests_cover_registered_helpers` in particular. `test_helper_python_authoritative_records` executes the helper end-to-end and stays RED until the verdict surface lands in T028; record that it is the single expected remaining failure rather than treating this phase as fully green (FR-004)
- [ ] T014 Record the reviewability checkpoint in the workflow file before implementation proceeds: cite `plan.md` §"Reviewability Budget, derived by hand" as the binding figure (~690 production LOC, WARN on reviewable LOC, no block, 5 production files, 12 authored files, one primary surface), state explicitly that the estimator's `pass` with `projected: 0` is an absent measurement and must not be cited as evidence of fitness, record the split lever (deferring the description-refresh half) as **derived and rejected** because the deferred refresh would have no trigger to fire on once the regeneration commit landed, and record the >800 contingency: if implementation lands above the block, the crossing is size-only and takes the recorded acceptance path following the `PRSG-013` precedent rather than a mid-implementation re-slice

**Checkpoint**: The helper is registered and its inventory is consistent. One
known end-to-end failure remains, clearing in T028.

---

## Phase 3: User Story 1 - Amended sweep leaves current pages (Priority: P1) 🎯 MVP

**Goal**: An autopilot run whose sweep classified at least one comment
`amended` regenerates the whole draft page set against the amended planning
record and refreshes the pull-request description **before** it emits the stop
report, so the reviewer at the re-review stop reads pages describing the
amended plan.

**Independent Test**: Run the sweep on a draft pull request carrying a comment
that consensus resolves to an amendment. Confirm the run regenerates the pages
and refreshes the description before the stop report, that the regenerated
pages carry the amended content, that the regeneration commit is newer than
every `Commit` named by an `amended` row, and that the stop report no longer
carries the slice-1 promise sentence.

### Tests for User Story 1 — verdict surface (write FIRST, confirm they FAIL) ⚠️

> Cases go in `tests/speckit-pro/unit/fixtures/artifact-freshness/freshness-cases.json`
> with expected envelopes in the sibling `expected-envelopes.json`. Both files
> are shared, so these tasks are **not** parallel with one another.

- [ ] T015 [US1] Add verdict fixture cases reaching each of the four closed verdicts on its own condition — `no_pages`, `stale`, `undeterminable`, `current` — to `tests/speckit-pro/unit/fixtures/artifact-freshness/freshness-cases.json`, with expected envelopes carrying `verdict`, `last_artifacts_commit`, `amended_rows_read`, `deciding_rows`, `undeterminable_rows`, and the echoed `pages` (FR-005, FR-001)
- [ ] T016 [US1] Add the two precedence cases to the same fixture pair: `no_pages` winning over a log full of `amended` rows, and `stale` winning over a co-occurring undeterminable row while that row still appears in `undeterminable_rows` (FR-005, FR-006, FR-007)
- [ ] T017 [US1] Add the FR-007a case — `artifacts_dir_state: present`, `last_artifacts_commit` null, one joinable `amended` row → `stale` — and the FR-007b companion where the only `amended` row is matched but unresolved → `undeterminable`, never `stale`, to the same fixture pair (FR-007a, FR-007b)
- [ ] T018 [US1] Add the FR-007b encoding case to the same fixture pair: a resolved row supplied with `is_ancestor_of_artifacts_commit` as `false` because `last_artifacts_commit` is null, proving the pinned encoding reaches `stale` through the ordinary stale test rather than through a special null-commit branch (FR-007b)
- [ ] T019 [US1] Add the FR-008 equality case to the same fixture pair: an `amended` `Commit` cell holding an abbreviated sha paired with a full-sha `last_artifacts_commit` that resolves to the same commit → `current`, the pairing a string comparison would get wrong; and the FR-009 pair — one older row plus one newer row → `stale`, two older rows → `current` (FR-008, FR-009, FR-002)
- [ ] T020 [US1] Add one FR-006 case per closed reason to the same fixture pair — `missing_commit_cell`, `empty_commit_cell`, `unresolvable_commit`, `no_matching_observation_record`, `malformed_row` — each surfaced with its own row `#` and reason rather than dropped (FR-006, FR-004a)
- [ ] T021 [US1] Add the observation-validation cases to the same fixture pair: `ok` as `1`, as `"true"`, and absent, each returning verdict `undeterminable` with reason `unusable_observation` at exit 0 and never exit 2, because a failed gather may not block the run (FR-004a, FR-023)
- [ ] T022 [US1] Add the **dual-anchoring regression case** to the same fixture pair: a `Feedback Sweep Log` data row whose `Disposition` cell carries an escaped `\|`, so the bare-pipe split yields nine cells instead of eight, with an expected envelope proving the `Commit` read is correct — the one case the hazard exists for, since a left-anchored index fails silently and in the direction that reads a stale page set as current (FR-004, FR-006)
- [ ] T023 [US1] Add the two structural cases to the same fixture pair: a workflow file with no `Feedback Sweep Log` heading, yielding zero `amended` rows with the verdict decided by directory state alone; and a data row with **fewer** cells than the header, which is malformed and undeterminable rather than an error (FR-006)
- [ ] T024 [US1] Add the input-error cases to the same fixture pair: `workflow_file` missing, blank, or unreadable; `artifacts_observation` absent or not an object; `artifacts_dir_state` outside the closed three — each exit 2 with a one-line `error:` diagnostic, the asymmetry against T021 being deliberate (a malformed *request* is the caller's defect; a failed *observation* is a fact about the world) (FR-004, FR-023)
- [ ] T025 [US1] Run `FRESHNESS_TEST` and confirm every case from T015 through T024 FAILS against the T012 stub, recording the failure list

### Implementation for User Story 1 — verdict surface

- [ ] T026 [US1] Implement the dual-anchored `Feedback Sweep Log` read in `speckit-pro/speckit_pro_runner/helpers/read_only.py`, reusing the shipped heading-anchored table read (anchor on the heading text, break `inside` on any line starting with `#`, skip the table rule row, find the header by column name) rather than writing a second parser, and deriving anchors from the header row: `#` and `Class` from the **left**, `Commit` at `-2` and `CRL #` at `-1` from the **right**, because `sweep_table_cells` splits on the bare pipe with no escape handling and a piped `Disposition` shifts every column to its right (FR-004, FR-003)
- [ ] T027 [US1] Implement the ancestry join and verdict precedence in the same file: match each `amended` row's `Commit` cell text **verbatim** against `artifacts_observation.amended_commits[].cell`, evaluate `no_pages` → `stale` → `undeterminable` → `current` in that order, and build the response envelope per `data-model.md` §3 with `pages` echoed unchanged. The helper MUST NOT resolve a sha, order two commits, run `git merge-base`, hash or compare page content, or read any path but the workflow file (FR-001, FR-002, FR-003, FR-004, FR-004a, FR-005, FR-006, FR-007, FR-007a, FR-007b, FR-008, FR-009)
- [ ] T028 [US1] Implement observation validation in the same file: `ok` must be the JSON literal `true` to be read at all, following `observation_pull_requests`' rule, with any other value returning the `undeterminable` verdict rather than an input error; validate `artifacts_dir_state` against the closed three; keep every genuine request defect at exit 2 (FR-004a, FR-023)
- [ ] T029 [US1] Run `FRESHNESS_TEST` and `HELPER_TEST` and confirm both PASS, including the `test_helper_python_authoritative_records` case T013 recorded as the expected remaining failure

### Tests for User Story 1 — removal-diff surface (write FIRST, confirm they FAIL) ⚠️

- [ ] T030 [US1] Add the removal-diff cases to `tests/speckit-pro/unit/fixtures/artifact-freshness/freshness-cases.json` and its expected-envelope sibling: a deselected page yielding one removal; a `gap` page present in `reselected_pages` yielding **no** removal, because a gapped page is still selected; an empty `reselected_pages` removing every observed page; a stem present only in `reselected_pages` ignored as a new page the author dispatch writes; and the input errors where either array is absent, not an array, or carries a non-string (FR-012a, FR-023)
- [ ] T031 [US1] Add the FR-012b/FR-018a **disjointness** case to the same fixture pair: a run carrying one `generated` page and one per-page `gap` produces a removal set that excludes the gapped page, so the per-page deletion path and the zero-generated replay path never co-fire. Replay itself is orchestrator behavior with no helper code to test, so this fixture pins the helper half of the boundary and T042 pins the orchestrator half in prose — recorded here so the consensus item reads as deliberately mapped rather than dropped (FR-012b, FR-018a)
- [ ] T032 [US1] Run `FRESHNESS_TEST` and confirm the T030 and T031 cases FAIL

### Implementation for User Story 1 — removal-diff surface

- [ ] T033 [US1] Implement the `removal_diff` surface in `speckit-pro/speckit_pro_runner/helpers/read_only.py` as a pure set difference — members of `observed_pages` absent from `reselected_pages`, matched by the manifest entry id kept as the filename stem, emitted in `observed_pages` order so the output is stable and diffable, echoing both inputs. It reads no file and **deletes nothing**: the system performs the deletion, stages it in the FR-018 commit, and reports each removal as its own outcome (FR-012, FR-012a)
- [ ] T034 [US1] Run `FRESHNESS_TEST` and confirm the removal-diff cases PASS

### Tests for User Story 1 — corroboration surface (write FIRST, confirm they FAIL) ⚠️

- [ ] T035 [US1] Add the corroboration cases to `tests/speckit-pro/unit/fixtures/artifact-freshness/freshness-cases.json` and its expected-envelope sibling: all six statuses (`match`, `no_record`, `skipped`, `pr_closed`, `pr_missing`, `identity_mismatch`) reached through the shipped classifier; a `Draft PR` row sitting inside an HTML comment classifying `no_record`, which proves the comment blanking; a malformed `Draft PR` row classifying `no_record` rather than raising; and `ok` short of the literal `true` classifying `skipped` with the request's reason preserved. Every response carries all five record keys, `null` where a status has nothing to say (FR-033a, FR-034)
- [ ] T036 [US1] Run `FRESHNESS_TEST` and confirm the T035 cases FAIL

### Implementation for User Story 1 — corroboration surface

- [ ] T037 [US1] Implement the `corroborate_refresh` surface in `speckit-pro/speckit_pro_runner/helpers/read_only.py` by calling the two shipped pure functions **verbatim** — `workflow_draft_pr_row(HTML_COMMENT_RE.sub("", text).splitlines())` then `corroborate_draft_pr(row, observation)`, the same pair `resolve_autopilot_stage` calls — and adding **no branch of its own**, because FR-034 assigns each status the behavior the ART-007 contract already gives it and that guarantee holds only when the same code decides the status in both places. Carry the HTML-comment blanking across for the reason the shipped call site records: a commented-out row must never become evidence. Keep the surface on this registration's single read path, the workflow file (FR-033a, FR-034, FR-004)
- [ ] T038 [US1] Run `FRESHNESS_TEST` and `LAYER4` and confirm both PASS, closing the helper half of this story

### Reference prose for User Story 1 — Claude surface

> These tasks all edit `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`,
> so they are sequential. Each **adds** prose; none rewrites or deletes shipped
> text except T043.

- [ ] T039 [US1] Add the freshness evaluation and the nine-step regeneration sequence to `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`: evaluate the verdict, on `stale` re-dispatch the shipped `speckit-pro:artifact-author` agent against the **amended** planning record, compute and apply the removal set, delete the superseded file behind each per-page gap, verify the written pages through the machinery's own two on-disk tests, commit, push, observe, refresh, record. State that step 0 is a **placement, not a new step**: the whole sequence runs after slice 1's reply point, so every reply the run owes is already posted before this slice's first new failure point, which is what leaves slice 1's reply behavior literally unchanged. State that re-selection reads the shipped gallery manifest against the amended record rather than replaying the page list the previous run produced, that every selected page is authored **fresh** with no patch or partial update, and that this slice introduces no second page-authoring path (FR-010, FR-011, FR-013, FR-015, FR-015a)
- [ ] T040 [US1] Add the per-page-gap deletion rule (step 3b) to the same file: a selected page whose regeneration returns a `gap`, in a run that produced at least one `generated` page, has any pre-existing file at its path removed, and that removal is reported **inside the page's own `gap` outcome** rather than as a separate `removed` outcome, which FR-012 reserves for deselection. Give the shipped ground: a plausible-looking document about a plan that is not this one is worse than no document at all, and a page about the right feature and the wrong superseded plan is that hazard one degree sharper. State the exclusion explicitly — a whole-set gap deletes nothing — and state that FR-012a keeps a gapped page out of the removal set because the page is still selected, which governs the deselection diff alone and is not licence to leave the superseded file in the tree (FR-012, FR-012b)
- [ ] T041 [US1] Add the three commit shapes, kept apart, to the same file: the **regeneration** commit staging `specs/<feature>/artifacts/` and nothing else with the `docs` type, taken only when the run's final post-verification outcome set contains at least one `generated` page; the **record** commit staging the workflow file path alone with the `chore` type, reusing the plan-stage terminal step's own commit verbatim and taken only when the `Draft PR` cell actually changed; and slice 1's **bookkeeping** commit, unchanged. State that no commit absorbs another, that an empty regeneration commit is never taken because it records nothing and cannot move the join, and that writing the regeneration commit on the no-comment leg does not contradict slice 1's rule, which governs the bookkeeping commit only (FR-018, FR-019, FR-020, FR-039)
- [ ] T042 [US1] Add FR-018a's two-directional guarantee to the same file: from the sweep onward the regeneration commit is the **only** commit that stages any path under the artifacts directory — the rule does not reach backward to the plan-stage boundary commit, which legitimately carries the first generation — because the phase hosting the sweep ends in a whole-worktree commit that would otherwise absorb whatever the sweep left uncommitted there and move the join. Then add the working-tree half: the reused machinery writes pages directly into the directory and deletes every page failing verification **before** the commit decision exists, so a run can empty a directory it promised not to move, and an emptied directory reads `no_pages` on the next join, which outranks `stale`, so the FR-038 retry never fires. Specify the adopted mechanism as **snapshot-and-replay**: snapshot the artifacts directory bytes immediately after the FR-004 observation and before the author dispatch, and replay only when the final verified `generated` count is zero — FR-018's own commit gate, never a proxy such as "did a commit land". State why a git-restore path is rejected: on the FR-007a history no commit has ever touched the directory, so git holds no copy. State that the snapshot is run-scoped, gitignored through a self-ignoring `.gitignore`, always removed, and its removal reported — transport, not a store, so FR-003 is not implicated. Name its path: it goes under `specs/<feature>/.process/feedback-sweep/`, the byproduct directory slice 1 already governs, because that rule says every file the sweep writes for its own transport goes there "and nowhere else" and names "any scratch the run needs" among them. State that it must **not** go under `specs/<feature>/artifacts/`, where FR-004 would observe it as a page and FR-012a's stem-matched diff would compute it as a deselection removal, deleting the restore copy — and where FR-018a's own exclusivity rule forbids it anyway. Then fix the ordering: slice 1 removes that byproduct directory before the run proceeds or stops, on every path, and the regeneration sequence now sits before that point, so **the replay decision must complete before the byproduct removal**. Ordered the other way the removal destroys the bytes FR-018a exists to restore, on exactly the zero-generated path it was written for. The removal itself is unchanged and still runs on every path. State that any restoration performed is reported as a run-level line beside the commit sha and is **not** a fourth member of FR-024's three-value page-outcome vocabulary; a restored page's own outcome is the `gap` explaining why it was not regenerated (FR-018a, FR-003, FR-024)
- [ ] T043 [US1] Add FR-019a's push rule to the same file: the push is **inside** the regeneration step, not a step after it, so the dedicated commit is not complete until it is on the remote, and a failed push ends the emission sequence there — the refresh must not run against pages the remote does not show, which is the same sequencing the reused machinery already applies between its own push and its create-or-refresh step. Split by leg: on a sweep that amended, a failed push stops the run immediately, because the re-review stop's pull request must already show current pages; on a leg that amended nothing, it does **not** convert the proceed into a stop, and the local commit rides up with the branch's next push. On both legs state that the condition is unrecoverable inside this slice — the commit is local and complete, so the join reads the directory as current on the next run and no later sweep regenerates or re-attempts the skipped refresh — and name the two-step manual resume path the operator owes: push the branch, then refresh the description directly (FR-019a, FR-017, FR-023)
- [ ] T044 [US1] Add the refresh call site to the same file: it takes its **own** live read-only observation at the moment of the refresh rather than reusing the entry gate's, because a pull request can be closed or replaced while the sweep runs and the later read is the current evidence — the same principle the reused create-or-refresh terminal step already applies to its own second read. Pin the query shape as the entry gate's, `gh pr list --head <branch> --state all --json number,url,state,isDraft,headRefName`, and state that `--state all` is load-bearing because it is what makes a closed pull request distinguishable from an absent one, a distinction the machinery's own existence test cannot produce. State that the classification is the same six-status logic reused verbatim, and give each status the behavior the ART-007 contract already assigns it at its terminal step, with **no status opening a second pull request** (FR-014, FR-033, FR-033a, FR-034)
- [ ] T045 [US1] Add FR-034a's two dead branches and FR-035's divergence to the same file: `no_record` is **unreachable** here, because the sweep is reached only on an entry-gate `match`, which requires the row, and the sweep is forbidden from writing it, so nothing between the gate and the refresh can clear it — which matters because the shipped row's behavior falls through to creation, and this slice creates on no path; and `skipped` has **one** live branch, not two, because at this call site the classifier's own input is the observation just taken, so a `skipped` classification is itself the evidence the tool could not be reached. State that neither may be implemented as a fallthrough to creation, and that should either classify despite this, the attempt ends with nothing created and the row left as found, with a caught `no_record` reported as an orchestrator invariant violation rather than an operator-fixable pull-request state. Then state FR-035's divergence: a discrepancy or an unreachable tool ends the refresh attempt **only** — it does not change the stop-or-proceed decision, does not unwind a regeneration commit that already landed, and is never reported as a page failure — because ART-007's terminal step sits at a stage boundary the run stops at regardless, while the sweep may proceed into task work (FR-034, FR-034a, FR-035, FR-023)

### Reference prose for User Story 1 — Codex mirror

- [ ] T046 [US1] Mirror T039 through T045 into `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`, describing the regeneration dispatch in **Codex-native terms**: the Claude-only-vocabulary regex runs over the concatenated Codex runtime documents and rejects `TaskCreate`, `TaskUpdate`, `Agent(`, `Bash(`, `Opus-class`, `Opus 4.6`, `/model opus`, `/effort max`, `/speckit.`, `/speckit:`, `run /<command>`, and `general-purpose agent`, so the Claude prose's `Agent(` dispatch block must be described without that literal. Leave the mirror's three pinned strings — `estimate-reviewable-loc`, `over_budget`, `not_estimated` — untouched; the assertions are file-wide, so an edit removing a surrounding block trips them even though none sits in the edited region (FR-029)
- [ ] T047 [US1] Run `LAYER1` and confirm the Codex structural validator passes on both the vocabulary regex over the concatenated runtime documents and the three pinned helper strings (FR-029)

### The slice-1 promise comes out (User Story 1 acceptance scenario 4)

> These two are independent deletions in different files. The lines they remove
> are **replaced** by the outcome lines T057 and T058 add in User Story 3;
> read those tasks together, since the removal alone would leave the report part
> silent about the pages.

- [ ] T048 [P] [US1] Remove both slice-1 promise passages from `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`: the stop-report clause stating that the draft artifact pages regenerate once slice 2 lands, and the meta-paragraph calling that sentence an interface slice 2 replaces (cited at `:1857-1858` and `:1874-1876` in `plan.md` §Reporting; locate by the sentence text, since line numbers drift as the preceding tasks land) (FR-027)
- [ ] T049 [P] [US1] Remove the same two passages from `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` (cited at `:1495-1496` and `:1506-1509`; locate by sentence text) (FR-027)

**Checkpoint**: The helper's three surfaces pass their fixtures, the
regeneration and refresh sequence is documented on both platforms, and no
report anywhere promises a future slice. User Story 1 is independently
demonstrable.

---

## Phase 4: User Story 2 - Clean sweep repairs pages a prior run left stale (Priority: P2)

**Goal**: A run whose sweep amends nothing still notices that the pages on disk
are older than the recorded amendments, regenerates, refreshes, and **proceeds
without stopping**, so a single interrupted run cannot leave the pages
permanently stale.

**Independent Test**: Leave the artifacts directory at a commit older than an
`amended` row's commit, then run a sweep that handles nothing new. Confirm the
run reads `stale`, regenerates, refreshes, and proceeds without stopping; then
run a further sweep and confirm it reads `current` and does nothing, so the
repair is not repeated.

**Depends on**: User Story 1's verdict surface (T027) and regeneration sequence
prose (T039–T045). The repair path is the same machinery reached from a
different leg.

- [ ] T050 [US2] Add the every-leg evaluation rule to `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`: freshness is evaluated on **every** sweep leg the run reaches, including the leg that amends nothing and the leg that handles no comment at all, because the recovery case surfaces only on those legs. Scope it to the entry gate: the evaluation runs inside the sweep, so it is reached only on corroboration status `match`; on `no_record` the sweep does not run and there is no pull request to refresh; on the four stopping statuses no evaluation occurs and stale pages stay stale — which is a deferral, not a lost repair, because the join is durable and reads the same `amended` rows on the first `match` run after the operator resolves the gate (FR-016)
- [ ] T051 [US2] Add the amended-nothing leg's behavior to the same file: on a `stale` verdict that leg regenerates and refreshes and then **proceeds without stopping**, because repairing stale pages must never convert a proceed into a stop. State that nothing new was amended, so there is nothing new to re-review (FR-017)
- [ ] T052 [US2] Add FR-015b's **two** scoping sentences to the same file, by the added-sentence technique and never by rewriting or deleting shipped text. First, scope the enumeration of stops that abort before the reply point and post no reply (its sixth member being a failed push) to the **amendment** push slice 1 owns. That sentence is an exhaustive dichotomy — three named stops after the reply point, "every other stop" before it — so excluding the artifacts push from the member list is not sufficient on its own; the added sentence must **also** place the amended-leg stop positively on the after-reply-point side, stating that a run reaching it has already posted every reply it owes. Second, scope the enumeration of conditions that end a run in this sequence where it names a failed push, because the artifacts push is non-run-ending on the leg that amended nothing while the shipped list is unconditional. Neither edit may add to or remove from the members either enumeration already carries. This scopes the FR-019a prose T043 added; read the two together (FR-015b, FR-019a, FR-017)
- [ ] T053 [US2] Add FR-015d's ordering rule to the same file: on the leg where at least one comment was handled and nothing was classified `amended`, the regeneration sequence reaches its own **terminal outcome** — in the fail-open sense, so a per-page gap, a whole-set gap, or a failed artifacts push each end the sequence at their own reported outcome — before slice 1's post-publication redaction stop evaluates whether to fire. Add no stop condition and change no decision: the stop still fires on exactly the ground slice 1 fixed, with the same report shape and resume path. Give the reason: the shipped trigger reads "once every write the run owes has landed", and this leg now owes the artifacts commit, its push, and the refresh, so evaluating from the reply point alone would falsify the shipped sentence "this stop replaces the proceed at that same point" and would turn a stop defined as notification-after-publication into a gate blocking writes on the strength of an unrelated redaction event. Where a push failure leaves the commit local, the stop still fires and its report carries FR-019a's manual resume path beside the redaction report. State that the amended leg needs no separate rule, that the no-comment leg is vacuous, and that a run on which the redaction stop fires is still a run the freshness evaluation is required on. Scope the shipped "stop once every commit is pushed and every reply is posted" sentence by an added sentence naming the regeneration sequence's terminal outcome among the writes this leg owes (FR-015d, FR-023, FR-016)
- [ ] T054 [US2] Add FR-037's whole-set semantics to the same file: a whole-set regeneration failure still runs the description refresh, which carries the whole-set gap as a single row through the three-sink contract, and leaves the stop-or-proceed decision unchanged. It leaves the artifacts directory **entirely unmoved**: no page is deleted, the per-page deletion of T040 is excluded, and the deselection removal is **withheld** even though the removal set is otherwise computable — because withholding it is what keeps the commit from being taken, which is the only thing keeping the join reading `stale` so the next leg retries. State that a removal landing alone here would move the directory, mark the whole set current, and strand every gapped page permanently stale for the sake of deleting one file, and that nothing is lost by waiting because re-selection recomputes the same deselection on the retry (FR-037, FR-012, FR-012b)
- [ ] T055 [US2] Add FR-038's repairability rule to the same file: the join repairs an **interrupted** run, never a **gapped** one. Any commit touching the artifacts directory marks the set current on the next join, including one carrying only removals and one carrying only a subset of the selected pages, so per-page gaps inside a run that took that commit are the operator's to act on and no later run re-attempts them. What decides whether a later leg retries is whether the artifacts commit was taken, never the shape of the shortfall. State the convergence property explicitly: after a `stale` run regenerates and commits, the directory's last commit is newer than every `amended` row that existed, so recovery from an interrupted run takes exactly one subsequent run and the repair is never repeated (FR-038, FR-001, SC-003)
- [ ] T056 [US2] Mirror T050 through T055 into `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` under the same Codex-native vocabulary constraint as T046, then run `LAYER1` and confirm it passes (FR-029)

**Checkpoint**: The recovery leg is documented on both platforms and cannot
convert a proceed into a stop. User Stories 1 and 2 both hold.

---

## Phase 5: User Story 3 - One honest report of what the pages now are (Priority: P3)

**Goal**: Whatever the run did to the pages, the operator reads one account of
it — per-page outcomes, the regeneration commit, and the refresh result — in
the single run report every leg already emits, collapsing to one line when the
pages were already current.

**Independent Test**: Run each of the three cases — amended-and-regenerated,
clean-and-repaired, clean-and-already-current — and confirm the report in each
names the per-page outcomes, the regeneration commit, and the refresh result,
with the already-current case collapsing to one line and no case promising a
future slice.

**Depends on**: User Story 1's sequence prose and User Story 2's leg prose.
These tasks extend the report those sequences produce.

- [ ] T057 [US3] Extend the **what-already-landed** part's closed enumeration once, in the **shared report-shape section** of `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`, with one outcome line per page reading `generated`, `gap`, or `removed`, every gap naming what was missing and why. Place it in the shared section rather than in the amended-leg bullet, because the evaluation runs on every leg and an amended-leg edit would miss the recovery path that is the whole of User Story 2. These lines are what **replace** the promise passages T048 and T049 removed (FR-024, FR-027)
- [ ] T058 [US3] Add the run-level lines to the same part of the same file: the regeneration commit's short sha and the outcome of the description refresh, with a failure's manual resume path belonging to the **resume-path** part instead; and FR-018a's restoration line beside the commit sha, which is a run-level line and not a fourth page-outcome value (FR-025, FR-018a)
- [ ] T059 [US3] Add the collapse rule to the same file: on a sweep that amended nothing and found the pages already current, the freshness contribution collapses to a **single line** naming the commit the pages are current as of, with no per-page outcome list. State that this scopes the freshness lines, not the report — the report's other mandatory parts are unchanged (FR-026)
- [ ] T060 [US3] Add the three-sink statement to the same file: every shortfall regeneration produces still reaches the reused machinery's three sinks — the description's gap rows, the `Draft PR` row's note, and the run report — with one substitution named explicitly, that at this Phase 7 call site the third sink is the **run report** on both the stop and proceed legs, because the plan-stage stop report the shipped sink table names does not exist here (FR-021)
- [ ] T061 [US3] Add the two-gap-shapes table to the same file, reported apart because they differ in **repairability** rather than in severity: a per-page gap beside a generated page moves the directory, takes the commit, and is not retried — the gap is the operator's; a whole-set gap moves nothing, takes no commit, and is regenerated by the next sweep leg; a deselection removal landing alone moves the directory, takes the commit, and is not retried, with the report naming the removal as the reason. State that a report calling the first two both "gap" and stopping there would leave an operator unable to tell work that will be retried from work that will not (FR-038, FR-024)
- [ ] T062 [US3] Add the removal-reporting rule and the refresh-failure rule to the same file: every removal is named as its own outcome and is **never silent**; and when the description refresh fails, the report names that failure as its own outcome distinct from the regeneration outcome, states in as many words that once the regeneration commit has landed a re-run does **not** retry the failed refresh — because the join then reads the directory as current, so a later sweep regenerates nothing and refreshes nothing — and names the operator's manual resume path (FR-012, FR-036)
- [ ] T063 [US3] Add the **per-status** resume paths to the resume-path part of the same file, one per stopping status rather than one shared line, for the reason the shipped corroboration gate already gives — the stopping statuses have different fixes and one shared path would send an operator to the wrong repair: `skipped` names fixing the tool; `pr_closed` names reopening the pull request; `pr_missing` names correcting or clearing the `Draft PR` row; and a refresh that failed against a reachable pull request names refreshing the description directly, outside the automated sequence. State that neither `pr_closed` nor `pr_missing` is repaired by refreshing a description, which is why the generic path may not stand in for them, and that when the failure traces to the recorded and live identities disagreeing the report names **both** identities (FR-036, FR-034)
- [ ] T064 [US3] Add the `undeterminable` report rule to the same file: the verdict triggers no regeneration, no refresh, and no commit, and moves the stop-or-proceed decision in neither direction — on a sweep that amended, FR-015's stop still fires on that independent ground. The run report names the verdict, each affected row's `#` and reason, and the operator's manual resume path, through the run report **alone**; the three sinks do not apply, since no regeneration occurred to produce a shortfall for them to carry. Give the convergence reason: this slice writes no log row and no second store is permitted, so nothing in scope can clear the condition, and an action keyed to it would repeat on every later clean sweep without end (FR-005a, FR-003, FR-021)
- [ ] T065 [US3] Add FR-039's record-commit reporting to the same file: a failure of the record commit or its push is reported through the refresh outcome and never blocks the run, and the report **must not** claim the row repairs itself on a later sweep, because the machinery's repair rule recovers an unwritten row only on a later refresh that reaches this step and no later sweep reaches it once the regeneration commit has landed. Name the resume path the way FR-036 names its own: the pull request is correct on the remote and only the record is unwritten, so the row is repaired by hand or by a later run reaching the plan-stage create-or-refresh step, which this slice never schedules (FR-039, FR-023, FR-025)
- [ ] T066 [US3] Add FR-024a's scoping sentence to the same file, beside the shipped sentence stating that a run observing no comment at all reports that "as a one-line report rather than an absent one". Place the one-line characterization on the **per-comment dispositions** its own paragraph is about — a run seeing no comment still says so in one line instead of omitting the part — and state that the freshness evaluation contributes its own lines to the what-already-landed part on that leg, so a report there is one line of dispositions plus however many lines the freshness outcome requires. Note that reading the shipped sentence as a promise about the whole report would also conflict with FR-018a's restoration line, which lands in that same part on a leg that generated nothing. Add no member to either enumeration and change no report part's contents (FR-024a, FR-016, FR-018a)
- [ ] T067 [US3] Add FR-022's scoping sentence to the same file, beside the shipped invariant "The sweep never writes the `Draft PR` row on any path", which **survives verbatim**. Scope it to the sweep's own writes and name the FR-014 refresh's row write as the **machinery's**, since the row keeps exactly one writer and this slice supplies only the trigger and the timing. Preserve the stated ground: the sentence exists so a run cannot repair a record it just failed to corroborate, and the refresh is reached only after an entry-gate `match` (FR-022, FR-014, FR-039)
- [ ] T068 [US3] Add FR-033b's scoping sentence to the same file, beside the shipped sentence stating that the sweep reads Step 0.6c's report "rather than taking an observation of its own" under "Phase 7 Setup: The Corroboration Gate". Scope it to the entry gate's **sweep-or-not decision alone** — the one decision Step 0.6c's pre-phase observation was taken for — so it is not read as forbidding the refresh call site T044 adds deeper inside Phase 7, which runs only after the gate has passed and the sweep has already amended. Note that this is not a new kind of observation: the create-or-refresh terminal step already takes a second live read distinct from Step 0.6c's, on the documented principle that the two reads are separate and the later one is the current evidence (FR-033b, FR-033)
- [ ] T069 [US3] Apply the same FR-033b scoping to the phrase "one read-only observation per run" in `speckit-pro/skills/speckit-autopilot/SKILL.md`, scoping it to Step 0.6c's own step rather than to every corroboration read a run may take. That phrase occurs exactly once in the tree and occurs there (cited at `:372` in `plan.md`; locate by the phrase, not the line) (FR-033b)
- [ ] T070 [US3] Mirror T057 through T068 into `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` under the same Codex-native vocabulary constraint as T046. The Codex `SKILL.md` is deliberately **not** edited: its body measures 7998 of its 8000-word cap, and its parallel Step 0.6c wording already carries the scoping T069 adds and makes no unqualified per-run claim, so parity is discharged by the mirror's own scoping sentence (FR-029, FR-030, FR-033b)
- [ ] T071 [US3] Run `LAYER1` and confirm both platform surfaces pass, then read both files side by side and confirm they describe the same behavior, since the structural checks confirm file-level coverage only and prose equivalence is verified by review (FR-029, SC-008)

**Checkpoint**: All three user stories are independently demonstrable. The
report states what the pages are rather than promising what a future slice will
do to them.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Discharge the platform constraints and the repository's
generated-artifact contract, then gate on the full suite.

### Platform constraints

- [ ] T072 [P] Audit `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py` for the runtime constraint: Python 3.11+ standard library only, no third-party import, no `subprocess`, no Bash, no `jq`, and no network reach from any of the three surfaces (FR-028, FR-004)
- [ ] T073 [P] Verify `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` is **byte-unchanged** by this slice with `git diff --stat`, so its two words of headroom under the 8000-word cap are unspent. If a measurement is needed at all, take it with the Layer 1 validator's own `_body` helper in `tests/speckit-pro/layer1-structural/validate-codex-skills.py`, never a plain word count, which counts different tokens (FR-030)
- [ ] T074 [P] Confirm the freshness helper's Layer 4 module and fixtures satisfy the contract's coverage obligations by checking each bullet of `specs/art-008-feedback-sweep-slice-2/contracts/check-artifact-freshness.md` §"Layer 4 coverage obligations" against `tests/speckit-pro/unit/fixtures/artifact-freshness/freshness-cases.json`, and that every case can actually fail rather than passing vacuously (FR-031)

### Generated-artifact tail

> This tail is mandatory, not optional. CI's `artifact-consistency` job fails
> the pull request when it is skipped, so a stale artifact cannot land.

- [ ] T075 Run `python3 scripts/refresh-release-artifacts.py` from the repository root to recompute the runner trust metadata (`speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and `.sha256`), rebuild both payloads under `dist/claude/` and `dist/codex/`, content-sync the installed-cache fixtures, and refresh the proof tree hashes. Then run it a **second** time and confirm it makes no further change, since the refresh is idempotent and a second-run diff means the first run was incomplete (FR-032)
- [ ] T076 Verify the installed-cache fixture copies were content-synced by T075 rather than hand-edited, by confirming `git diff` shows changes at all six paths under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/` that the plan's generated surface declares — the two `read_only.py` copies, the two `registry.py` copies, `claude/.../phase-execution.md`, and `codex/.../phase-execution-codex.md` — and that each matches its `speckit-pro/` source byte for byte. Never hand-edit a generated payload; if one is out of step, re-run T075 (FR-032)
- [ ] T077 Run `pnpm --dir docs-site reference:generate` to refresh `docs-site/src/content/docs/reference/tests.md`, which enumerates test paths and is restaled by the new test module and the new fixture directory. Depends on T002's `pnpm --dir docs-site install --frozen-lockfile` (FR-032)

### Final gate

- [ ] T078 Run `FULL_VERIFY` — `python3 tests/speckit-pro/run-all.py` — from the repository root and confirm zero failures across every layer. This is the only full-suite run in the task list; T001's baseline is what it is compared against. The Layer 6 Codex qualification corpus is included in this gate: this slice ships no new agent definition and modifies none, so its sha256 chain should be unaffected, and a `source digest does not match role source bytes` failure here means an agent definition was touched and must be reverted or the corpus regenerated (FR-032)
- [ ] T079 Validate the executable scenarios in `specs/art-008-feedback-sweep-slice-2/quickstart.md` — Scenario 1 (the verdict is reproducible offline), Scenario 2 (the dual-anchored `Commit` read survives a piped disposition), Scenario 6 (both platforms describe the same behavior), and Scenario 7 (the generated-artifact contract is discharged). Scenarios 3, 4, and 5 need a released plugin, because the autopilot runs from the cached plugin and an end-to-end sweep cannot run against the working tree; record that limit and its discharge path in the workflow file's post-implementation checklist rather than attempting a live run, mirroring how slice 1 recorded its own (SC-005, FR-029, FR-032)
- [ ] T080 Confirm no run report or reference file anywhere states that pages will regenerate in a future slice, by grepping both platform reference surfaces and both `SKILL.md` files for the promise wording, so the T048 and T049 removals are complete rather than partial (FR-027, SC-007)
- [ ] T081 Generate or update the PR review packet with what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes. Review order reads the freshness helper and its fixtures **first**, since the join rule is what every other requirement depends on, then the regeneration and reporting prose, then the platform mirror. Scope budget cites `plan.md` §"Reviewability Budget, derived by hand" as the binding figure and states that the estimator's `pass` is an absent measurement. Known gaps name the three quickstart scenarios T079 deferred and the reason

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies; can start immediately
- **Foundational (Phase 2)**: depends on Setup; **blocks all user stories**
- **User Story 1 (Phase 3)**: depends on Foundational
- **User Story 2 (Phase 4)**: depends on User Story 1's verdict surface (T027) and its regeneration-sequence prose (T039–T045)
- **User Story 3 (Phase 5)**: depends on User Stories 1 and 2, whose sequences produce the report these tasks extend
- **Polish (Phase 6)**: depends on every source and prose edit being final, because T075 regenerates from them

### The prompt's ordering, mapped to phases

`helper + fixtures` → Phase 2 and Phase 3 tasks T015–T038.
`reference prose (both platforms)` → T039–T049.
`regeneration/refresh wiring` → T039–T045 (Claude), T046 (Codex), T050–T056.
`report sentences` → T057–T071.
`payload + proof + docs regeneration` → T075–T078.

### Within each user story

- Fixture cases are written and confirmed **failing** before the surface that satisfies them is implemented
- The dual-anchored table read (T026) precedes the join it feeds (T027)
- All three helper surfaces precede the prose describing what the orchestrator does with them
- The Claude reference precedes its Codex mirror, so the mirror is written from finished prose rather than in parallel with a moving target
- The promise removals (T048, T049) and their replacement lines (T057) are read together

### Ordering hazards, named so they are not discovered by failing

1. **`fixture-manifest.json` index** (T008): compared for exact list equality against `EXPECTED_HELPERS`, so the new entry must sit at the same index in both.
2. **`NO_BASH_ANCESTOR`** (T007): omitting it fails the bash-reference list assertion rather than the one a reader would expect.
3. **Foundational green is partial** (T013): `test_helper_python_authoritative_records` runs the helper end-to-end and cannot pass until T028.
4. **Codex pinned strings** (T046, T056, T070): `estimate-reviewable-loc`, `over_budget`, and `not_estimated` are asserted file-wide, so an edit removing a surrounding block trips them even outside the edited region.
5. **Do not run `FULL_VERIFY` mid-phase**: a `speckit-pro/` edit reddens gate tests on stale payloads until T075.
6. **T053 edits between T048's two deletions**: on the Claude surface the FR-015d redaction-stop trigger sits at `:1869`, between the promise clause T048 removes at `:1857-1858` and the meta-paragraph it removes at `:1874-1876`; the Codex targets interleave the same way. T048 runs in Phase 3 and T053 in Phase 4, so every line number in that neighbourhood has already shifted by the time T053 runs. Locate by the fragments in §"Locating shipped sentences", never by the cited line.
7. **Replay before byproduct removal** (T042): the FR-018a snapshot lives in the sweep's byproduct directory, which slice 1 removes on every path before the run proceeds or stops. The replay decision must complete first, or the restore copy is gone on exactly the zero-generated path it exists for.

### Parallel Opportunities

- T002 and T003 run in parallel
- T004, T005, T006, T007, and T009 touch five different files and run in parallel
- T011 (`registry.py`) and T012 (`read_only.py`) touch different files and run in parallel
- T048 and T049 are independent deletions in different files
- T072, T073, and T074 are independent read-only audits
- **Not parallel**: every fixture-case task (T015–T024, T030, T031, T035) writes the same two JSON files; every Claude prose task writes the same `phase-execution.md`

---

## Parallel Example: Phase 2 Foundational

```bash
# Four different files, no shared content:
Task: "Create the request fixture in tests/speckit-pro/unit/fixtures/read-only-helpers/requests/check-artifact-freshness.json"
Task: "Create the Layer 4 module tests/speckit-pro/unit/test-artifact-freshness.py"
Task: "Create the fixture pair under tests/speckit-pro/unit/fixtures/artifact-freshness/"
Task: "Declare the module in tests/speckit-pro/suite-manifest.json"

# Then, after the RED in T010:
Task: "Add the HelperEntry to speckit-pro/speckit_pro_runner/helpers/registry.py"
Task: "Add the registration touch points and router to speckit-pro/speckit_pro_runner/helpers/read_only.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational — **blocks everything**
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: the helper's three surfaces pass their fixtures, the regeneration sequence is documented on both platforms, and the promise passages are gone
5. This is the slice's core: an amended sweep leaves current pages

### Incremental Delivery

1. Setup + Foundational → the helper is registered and its inventory consistent
2. Add User Story 1 → an amended sweep regenerates and refreshes before stopping (MVP)
3. Add User Story 2 → an interrupted run's stale pages are repaired on the next clean sweep, without converting a proceed into a stop
4. Add User Story 3 → the operator reads one honest account of what the pages now are
5. Polish → the generated-artifact tail and the full-suite gate

### Why the stories cannot be reordered

User Story 2 is the recovery path for the mechanism User Story 1 builds, and
User Story 3 reports on both. Delivering 2 or 3 first would leave a helper
nothing calls, which is the same reason `spec.md` records for not splitting this
slice further.

---

## Notes

- `[P]` means different files with no dependency on incomplete work
- Every helper task is TDD: fixture first, confirm RED, implement, confirm GREEN
- Every prose task **adds** a sentence; the only deletions in this slice are the two FR-027 promise passages, which slice 1 itself declared an interface slice 2 replaces
- Commit after each task or logical group; the orchestrator owns commits
- Repo-relative paths only, everywhere, including in any prose these tasks author
