# Tasks: Phase-Guard Enforcement Repair

**Input**: Design documents from `specs/art-014-phase-guard-enforcement-repair/`

**Prerequisites**: [plan.md](./plan.md) (required), [spec.md](./spec.md) (required
for user stories), [research.md](./research.md), [quickstart.md](./quickstart.md),
[checklists/](./checklists/)

**Tests**: Test tasks are included and are **required**. FR-011 and FR-012 mandate
committed coverage, and the workflow prompt fixes a TDD order in which the
negative control is written before the code it constrains.

**Reviewability**: Within budget, matching plan.md: 337 projected reviewable LOC,
5 production files, 10 total files, one primary surface (harness/adapter) with
docs/process secondary. No typed exception is claimed and none is needed. These
are the re-run figures, raised during this phase from 235 LOC across 4 production
files and 9 total when the plan's Declared File Operations gained its sixth entry
and the estimator was re-run on the grown requirement set; spec.md's Reviewability
Budget revision note records why, and every verdict is unchanged. The task count
below is higher than that LOC figure suggests because verification steps, evidence
runs, and generated-artifact refreshes are itemized separately from the edits that
cause them. Ten of the twenty-seven tasks (T001, T011, T012, T015, T022, T023,
T024, T025, T026, T027) change no authored source file: they record a measurement,
re-run existing coverage, regenerate generated artifacts, or run the gate. The
slice estimator (`estimated_loc 337`, `suggested_slices 1`, `status ok`) is the
authoritative budget signal here, not a task-count multiplier.

**Organization**: Tasks are grouped by user story so each story can be
implemented, tested, and reviewed as an independent increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, repository root. Every path below is repository-relative.

- Guard under test: `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`
- Layer 4 unit tests: `tests/speckit-pro/unit/`
- Workflow record: `docs/ai/specs/.process/ART-014-workflow.md`

## Project Commands

| Purpose | Command |
|---|---|
| Unit test (Layer 4) | `python3 tests/speckit-pro/run-all.py --layer 4` |
| Full verify | `python3 tests/speckit-pro/run-all.py` |
| Build / Typecheck / Lint | N/A |

---

## The two halves, and why the ordering below is what it is

The defect has two independent causes and **neither one alone repairs it**. The
task order makes that mechanically visible rather than asserting it, through a
three-stage progression of the same negative control:

| After | Negative-control exit | `workflow_authority_errors` in the report |
|---|---|---|
| T002 written (before any guard edit) | 0 | key absent entirely |
| Phase 2 complete (comparison runs) | 0 | key still absent — the helper computes errors nothing consumes |
| T007 complete (key merged) | 0 | **non-empty** — detected, still not gating |
| T008 complete (key registered) | **non-zero** | non-empty |

A reviewer who wants to confirm the claim reverts T008 alone and watches the exit
code fall back to 0 while the report keeps reporting the mismatch.

---

## Non-Goals — a task proposing any of these is a scoping error

Bounded by the spec's Non-goals and Assumptions. None of the following appears
below, and none may be added:

- **Arming a second problem key.** FR-008 forbids adding
  `workflow_checkpoint_errors` to any rule tuple; it is produced at four other
  sites by `validate_workflow_checkpoint_bindings` and widening it would arm
  every PR Marker Plan Evidence binding check at once. Exactly one key is armed
  (SC-006).
- **Making `workflow_file` mandatory.** That is a migration, not a repair.
  Absence stays permitted (FR-003), and the tracked slot at
  `.specify/autopilot-state.json` that carries no such field must keep
  validating.
- **Committing a live corpus walk.** The D8 proof is a one-time recorded run.
  The process directory holds live data and an in-flight specification mid-repair
  can legitimately fail the guard, so a committed walk would turn CI red on
  unrelated pull requests.
- **Wiring the Claude live-PR-OID fetch.** ART-016 owns it. This change documents
  the gap and cites that entry; it does not close it.
- **Rewriting the gated pull-request-head path.** FR-002 freezes its
  preconditions, semantics, and reporting key. The duplicate identity report on
  that path is an accepted consequence recorded in plan.md D2, not a defect to
  clean up.
- **Editing `dist/` payloads or the installed-cache proofs by hand.** They are
  generated (T023).
- **Adding a Layer 1 assertion or a `CODEX-PARITY-NOTES.md` entry.** Plan D6
  rules both out: this change is parity-restoring and pins nothing, so an entry
  would make that ledger wrong.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Record the pre-change contrast that every later claim is measured
against. No repository file changes in this phase.

- [ ] T001 Record the pre-change baseline into `docs/ai/specs/.process/ART-014-workflow.md` before editing any source: run `python3 tests/speckit-pro/run-all.py --layer 4` and confirm it is green, then run the guard `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` once against a mismatched state under the autopilot's own invocation (`--rule status-evidence`, no commit flags, no `pr_marker_plan`) and record that it exits 0 with `workflow_authority_errors` absent from the report entirely. Also re-derive and record the pre-change counts: 20 emitted problem keys (report keys minus the four metadata keys `status`, `workflow_file`, `state_file`, `plan_step_count`) and 8 reachable by a named rule (`status-evidence` 3 + `coverage` 5 in `RULE_PROBLEM_KEYS`). **Acceptance**: the recorded contrast for SC-001 exists and the counts match the spec's Assumptions; a disagreement is drift to report in the workflow file, never a number to quietly change. [Spec §SC-001, §SC-006, §Assumptions; Quickstart §Scenario 1 "Expected before the change"; Research §Measurements]

**Checkpoint**: The "before" half of every contrast is on the record.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Make the workflow-identity comparison run on the invocation the
autopilot actually issues. Tests are written first and stay **red** through the
whole phase — that is the intended state, because the comparison running is only
half the repair.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T002 Write the FR-012 shared fixture builder and the **negative control test method first**, in a new test case class in `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`, and verify it FAILS before writing any guard code. The builder takes exactly one parameter, the state's `workflow_file` value, so the FR-012 pair is a controlled comparison. It MUST create a temporary root and write the repository-root marker `.git` there **as a file, not a directory** — `_repository_root` tests `(candidate / ".git").exists()`, which either satisfies, and without the marker branch 2 skips under FR-006 and both controls pass **vacuously**; writing it as a file also exercises the git-worktree case every real autopilot run for this repository takes. It MUST write the workflow under a repository-relative subpath of that root, write the state beside it, set the state's `workflow_file` to a repository-**relative** path against that root (an absolute one is rejected as malformed by branch 4), invoke the guard by subprocess with `--rule status-evidence` and no commit flags and no marker-plan schema, and return the exit code with the parsed report. The negative control points the state at a **different** workflow and asserts a non-zero exit, a non-empty `workflow_authority_errors`, and that the first entry **starts with** the FR-009 prefix (assert the prefix, never the full string, so path formatting can change without breaking the test). **Acceptance**: the new test case class is added to the explicit class tuple in `build_suite()` in the same file — that enumeration is not auto-discovering, so an unregistered class is silently skipped and the control proves nothing; and the test runs RED with the recorded reason being exit 0 and the key absent, matching T001. [Spec §FR-012, §FR-009; Plan §D5]

- [ ] T003 Add the FR-006b control as a further method in `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`: a state file that sits **inside** the repository fixture but is named to the guard by a **relative path from a subdirectory** must now resolve a repository root and evaluate the comparison. Point that state at a mismatching workflow and assert a non-empty `workflow_authority_errors`. **Acceptance**: written before T004 and verified RED; the recorded reason for the red is that root resolution returns `None` for this spelling today, so the comparison skips while the state file sits untouched inside the tree. This control is what distinguishes FR-006b's repair from a no-op, because the FR-006 verdict for a genuinely-outside state is deliberately unchanged. It goes green at the T008 checkpoint, not in this phase. [Spec §FR-006b third bullet, §FR-006a second inducing input]

- [ ] T004 Resolve the state path before walking its parents in `_repository_root` (currently at line 676) of `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`, so whether the comparison evaluates depends on where the state file **is** rather than on how the caller spelled the path and which directory they ran from. **Acceptance**: T003's control changes its recorded reason (a root now resolves); the FR-006 verdict is unchanged for a state genuinely outside any repository, which still finds no marker and still skips; and the two other call sites at lines 1552 and 2005 are **verified, not assumed**, to be unaffected — read each one and confirm it already normalizes the value independently before use, per plan.md's safety argument. If either does not, report it rather than widening this task. [Spec §FR-006b]

- [ ] T005 Add the module-level authority helper next to `_authorized_workflow_text` in `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`, taking the supplied workflow path, the state path, and the state dict, and returning a list of errors. Implement the seven branches in exactly the FR-004d order, because an earlier skip must win over a later failure. Seven and five are the same order counted at two levels, not a disagreement: FR-004d names the five branches that carry a requirement-level verdict, and the implementation refines them into seven by splitting malformed into its two checks (3 and 4, which must be separate for the reason recorded below) and adding the terminal pass (7). Documentation follows FR-004d's five per T019 and T020; code follows all seven. The branches: (1) `"workflow_file"` absent from the state → skip, return `[]`; (2) `_repository_root(state_path)` returns `None` → skip, return `[]`; (3) value is not a `str`, or is empty, or is whitespace-only → fail, malformed; (4) value is not a normalized repository-relative path → fail, malformed; (5) the supplied workflow resolves outside the repository root → fail, out-of-boundary; (6) the two references differ → fail, identity mismatch; (7) otherwise → pass, return `[]`. **Acceptance**, each item load-bearing with a distinct failure mode:
  - Branch 1 tests **key membership**, `"workflow_file" not in state` — never `state.get("workflow_file") is None`, which returns `None` for both an absent key and an explicit JSON `null` and so collapses a skip verdict with a fail verdict, making a nulled field the silent opt-out FR-005 exists to prevent.
  - Branch 3 is an **explicit** whitespace check placed **before** branch 4, because `_is_normalized_repo_path("  ")` and `_is_normalized_repo_path(" ")` both return `True` — a run of spaces is a valid POSIX path part — so without it a whitespace-only value falls through to branch 6 and is reported as an identity mismatch with a blank path, the wrong error class and an unreadable message.
  - Branch 4 delegates to the existing `_is_normalized_repo_path`, whose rule is stricter than "looks like a path" and does **not** fold case, which is what keeps it consistent with FR-004b rather than quietly normalizing a mis-cased value into a match.
  - Resolution is **asymmetric** per FR-004a: the **supplied** side is resolved against the repository root and rendered POSIX (`workflow.resolve().relative_to(repo_root.resolve()).as_posix()`); the **state** side is compared as the literal string it holds, with no filesystem resolution, because it is machine-written and already constrained by branch 4. Only the supplied side has spelling freedom.
  - Comparison is a plain byte-exact `!=`. No `str.lower()`, no `os.path.samefile`, no `Path.samefile` — byte-exact is the only rule returning the same verdict on the case-insensitive filesystem this repository is developed on and the case-sensitive one it is tested on.
  - **No branch raises**; every outcome is a return. `build_report` has no handler, and an uncaught exception prints a traceback instead of the JSON report the autopilot parses. `relative_to()` raising `ValueError` on a non-subpath is branch 5 by design, not an escape.
  - Messages: branch 5 reuses the sentence the same file already emits at line 1325, `workflow file is outside the authorized repository` (the FR-009 prefix governs the identity message only, and an out-of-boundary path has no repository-relative form to print in a mismatch message); branches 3 and 4 reuse the sentence at line 1331, `autopilot state workflow_file is not a normalized repository-relative path`; branch 6 opens with the exact documented sentence unmodified, `supplied workflow does not match autopilot state workflow_file authority`, and appends both compared paths after it.
  [Spec §FR-003, §FR-004, §FR-004a, §FR-004b, §FR-004c, §FR-004d, §FR-005, §FR-006, §FR-009; Plan §D1; Research §R2]

- [ ] T006 Widen `_authorized_workflow_text` in `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` from `tuple[str, list[str]]` to a **3-tuple**, `(text, checkpoint_errors, authority_errors)`, and update the single unpacking call site in `build_report` (line 4022). Call T005's helper **unconditionally, immediately after the existing `read_text(workflow)` call** and before the marker-plan and expected-commit gate, and make its result the third element on **every** return path including the two early returns at lines 1310 and 1312. The **second** element keeps carrying exactly what it carries today. **Acceptance**:
  - The three-tuple is required, not stylistic. Folding the whole return into the existing key is the smaller diff and is wrong twice: it would move the gated pull-request-head comparison's reporting key, which **FR-002 forbids**, and because the new key is registered in `status-evidence` it would newly arm **every** gated-path error (`workflow repository root is unavailable`, the `expected_head_commit` authority error, `workflow is absent from the authorized PR head`, `workflow at the authorized PR head is not UTF-8`, and the byte mismatch) for the Codex flow that genuinely supplies live commit values — the exact blast radius **FR-008** exists to prevent.
  - The helper runs **after** `read_text(workflow)`, never before it. Keeping that read as the function's first statement is what makes the spec's missing-supplied-workflow edge case true as written, and it is what discharges the no-raise argument: a path that was read successfully was traversable, so the `RuntimeError` that `Path.resolve()` raises on a symlink loop is already unreachable by the time the helper resolves anything.
  - `build_report` is verified to be the only consumer (definition at line 1298, single unpacking call at line 4022), so this touches exactly one call site.
  - After this task the third element is computed but **not yet consumed**: the report still carries no `workflow_authority_errors` key and T002 and T003 are still red. That is correct.
  [Spec §FR-001, §FR-002, §FR-008; Plan §D2; Research §R1]

**Checkpoint**: The comparison runs unconditionally on the autopilot's own
invocation. The exit code has not moved and cannot yet, because nothing consumes
the helper's findings. T002 and T003 remain red.

---

## Phase 3: User Story 1 - A mismatched workflow halts the run (Priority: P1) 🎯 MVP

**Goal**: A run whose state names a different specification stops instead of
proceeding, and the message names both files so the maintainer can tell which one
to repair. This is the defect the specification exists to fix and the only story
that changes runtime behavior.

**Independent Test**: Point the guard at a workflow file while the state names a
different one, using the exact invocation the autopilot issues (`--rule
status-evidence`, no commit flags, no marker-plan schema). The run must exit
non-zero and print a message containing both paths. Re-point the state at the
matching workflow and the same invocation must exit zero.

### Implementation for User Story 1

- [ ] T007 [US1] Give the new key its own dict in the `problems` merge in `build_report` in `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`, alongside the eight per-check dicts already merged at lines 4050-4059, and **delete** the `workflow_checkpoint_result["workflow_checkpoint_errors"].extend(...)` fold at lines 4031-4033. An `extend` into an existing dict puts the errors under an existing key and arms nothing new. **Acceptance**: `workflow_authority_errors` appears in the report on **every** run — on skip and on pass as an empty list, not only when it carries an error — because the FR-011 completeness test derives its key set from a real report and a conditionally-absent key would pass unclassified. T002 and T003 now show a **non-empty** `workflow_authority_errors` while still exiting 0; that intermediate state is the proof that detection and gating are separate halves. [Spec §FR-007, §FR-011; Plan §D3.1]

- [ ] T008 [US1] Add `"workflow_authority_errors"` to the `status-evidence` tuple in `RULE_PROBLEM_KEYS` (lines 239-254) in `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`, **and to nothing else**. **Acceptance**: T002's negative control and T003's FR-006b control both turn GREEN — this is the task that makes SC-001 true. `workflow_checkpoint_errors` is **not** added to any tuple (FR-008). Re-derive and confirm the post-change arithmetic SC-006 pins: emitted keys 20 → 21; keys reachable by a named rule 8 → 9, with `status-evidence` moving 3 → 4 and `coverage` unchanged at 5; the 12 advisory keys stay advisory; no existing key changes reachability. [Spec §FR-007, §FR-008, §SC-001, §SC-006; Plan §D3.2]

### Tests for User Story 1

- [ ] T009 [US1] Add the FR-012 **positive control** as a separate test method in `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`, sharing T002's fixture builder and differing from the negative control in **exactly one value**, the state's `workflow_file`, which here names the workflow actually supplied. Assert exit 0 and `workflow_authority_errors == []`. **Acceptance**: two separate methods, not one parameterized method, so each failure names its own claim and the pair reads as a controlled comparison. The positive control is what proves the negative control is detecting a mismatch rather than failing everything. [Spec §FR-012; Plan §D5]

- [ ] T010 [US1] Add a **third** test method in `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py` for the FR-003 absent-field skip, placed deliberately **outside** the FR-012 controlled pair so that pair keeps differing in exactly one value: against the same repository-marked fixture root, a state carrying **no `workflow_file` key at all** must exit 0 with an empty `workflow_authority_errors`. **Acceptance**: this is the one branch neither FR-012 control exercises — both of them set `workflow_file` and differ only in its value, and the existing `RuleScopingTests` sets it too while reaching branch 2 rather than branch 1. It is also the branch the corpus evidence structurally cannot cover, because every synthesized corpus state sets the field, and it is what keeps the tracked slot at `.specify/autopilot-state.json` working. Without this method the absent-field guarantee rests on reading the code. [Spec §FR-003, §FR-012; Plan §D5; Checklist data-integrity CHK004]

- [ ] T011 [US1] Re-run **both** existing test files that newly flow through the now-unconditional comparison, and repair fixtures rather than the helper if either turns red. First, `tests/speckit-pro/unit/test-autopilot-phase-coverage.py`: it runs `git init` on its temporary root so the gated path can work at all, so branch 2 does **not** skip there and every validator run inside that fixture newly flows through branches 3 to 6 for real. It stays green by construction because the fixture sets the state's `workflow_file` to `workflow.md` and writes the supplied workflow at that same repository-relative path, so the comparison matches. That is a fixture detail rather than an intent, which is why it is verified rather than assumed. Second, the three existing `RuleScopingTests` methods in `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`: they write an **absolute** path into the state's `workflow_file` and create no repository marker, and stay green only because branch 2 skips first, no `.git` resolving above a system temporary directory on either macOS or Linux. **Acceptance**: both files green. If either turns red the correct fix is to make that fixture's `workflow_file` repository-relative against a root it controls — **never** to weaken the helper. Neither file is modified if both pass, which is why neither appears in the Declared File Operations. [Spec §FR-002; Plan §D5; Research §R3; Checklist error-handling CHK029]

- [ ] T012 [US1] Walk the quickstart Scenario 3 branch table manually against the T002 fixture, varying one input at a time, and record the results in `docs/ai/specs/.process/ART-014-workflow.md`. This is the only verification covering FR-004c, FR-005, and the FR-004d ordering, none of which has a committed test. Cases: remove the `workflow_file` **key** → exit 0, empty list; set it to JSON `null` → non-zero with the **malformed** message, not the identity message; set it to `""` → non-zero, malformed; set it to `"  "` → non-zero, **malformed and not identity**; set it to a number or a list → non-zero, malformed; delete the `.git` marker → exit 0, empty list; supply a workflow outside the temporary root → non-zero with `workflow file is outside the authorized repository`. **Acceptance**: two rows pass for the wrong reason if the branch order is wrong and must be read carefully — the whitespace row lands in the identity branch and prints a blank path unless FR-005's explicit check exists, and the `null` row skips silently unless branch 1 tests key membership. Distinguish the rule-violation exit from the input-error exit code 2, so a control asserting only "non-zero" is not satisfied by an unrelated input failure. [Spec §FR-003, §FR-004c, §FR-004d, §FR-005, §FR-006; Quickstart §Scenario 3; Checklist error-handling CHK018]

**Checkpoint**: User Story 1 is fully functional and testable independently.
SC-001 and SC-003 hold. Reverting T008 alone drops the exit code back to 0 while
the report still reports the mismatch, which is the reviewable demonstration that
both halves were required.

---

## Phase 4: User Story 2 - Advisory status is a recorded decision, not an accident (Priority: P2)

**Goal**: For any problem key, a maintainer can tell whether it can fail a run or
is deliberately advisory, and why. The absence of that record is how the User
Story 1 defect survived.

**Independent Test**: Read the classification record and confirm every problem key
the guard can emit carries a verdict and a reason. Then add a throwaway key to the
report without adding it to the record and confirm the test fails.

### Tests for User Story 2

- [ ] T013 [US2] Write the FR-011 completeness test **first** in `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py` and verify it fails: build a **real** report by invoking the guard, subtract the four metadata keys (`status`, `workflow_file`, `state_file`, `plan_step_count`), and assert the remaining key set is covered by `PROBLEM_KEY_INTENT`, **naming any key that is missing**. Also assert every verdict is drawn from the closed three-value vocabulary and every reason is a non-empty string. **Acceptance**: the emitted key set is derived from a real report and **never** from a second hardcoded list — a parallel list drifts out of step exactly as the classification record itself could, which is the whole failure mode being closed. One report suffices only because every per-check function returns its full key set on every return path including its early returns, so no key is ever conditionally absent; record that this is a property of the code the test relies on rather than one the test checks, and that a future key emitted only under some state shapes would pass unclassified — the correct response then is to extend the fixture to a state shape that emits it, never to relax the assertion. Verified two ways during Checklist: a thin synthesized state and the tracked current-run state produce identical report key sets at 24 keys, 20 problem plus 4 metadata. [Spec §FR-011, §SC-005; Plan §D5; Checklist security CHK027]

### Implementation for User Story 2

- [ ] T014 [US2] Add the module-level `PROBLEM_KEY_INTENT` mapping to `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`, mapping all 21 post-change emitted keys to a verdict from the closed three-value vocabulary (`gated`, `advisory-deliberate`, `advisory-accidental`) plus a reason, sized against T013 until it passes. Two values are insufficient, because the audit found keys that are advisory by accident rather than by design. The split is 9 `gated` (`workflow_status_evidence_errors`, `state_status_errors`, `stage_mirror_errors`, `workflow_authority_errors`, `missing_workflow_sections`, `missing_workflow_tokens`, `missing_workflow_post_items`, `missing_state_prefixes`, `missing_state_post_items`), 3 `advisory-accidental` (`in_progress_errors`, `duplicate_state_steps`, `state_order_errors`), and 9 `advisory-deliberate` (`changed_file_manifest_errors`, `checkpoint_evidence_errors`, `checkpoint_file_errors`, `checkpoint_source_fingerprint_errors`, `completed_phase_pending_fields`, `emission_mapping_errors`, `marker_plan_status_errors`, `projection_status_errors`, `workflow_checkpoint_errors`). **Acceptance**: restating the key name is not a reason. An `advisory-deliberate` reason states what makes advisory status **correct** for that key; each of the three `advisory-accidental` reasons names **ART-017** as the follow-up that will arm it. The three accidental verdicts are mandatory: the shipped justification for advisory status is that the existing workflow corpus predates the checks, which is true of the coverage lists but false of these three, because they are invariants of the state file the current run just wrote and no legacy artifact can violate them. This task records the verdict and **does not arm them** — arming is ART-017's scope. [Spec §FR-010, §FR-010a, §FR-010b, §SC-004; Plan §D4]

- [ ] T015 [US2] Prove the completeness test bites: add a throwaway problem key to the report in `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` **without** adding it to `PROBLEM_KEY_INTENT`, run `python3 tests/speckit-pro/run-all.py --layer 4`, confirm the suite fails and **names the missing key**, then revert the throwaway key and confirm the suite is green again. **Acceptance**: not optional. A completeness test that cannot fail is the same category of defect this specification exists to repair. Record the observed failure message in `docs/ai/specs/.process/ART-014-workflow.md`, and confirm `git diff` is clean for the guard's throwaway key afterwards. [Spec §SC-005; Quickstart §Scenario 4]

**Checkpoint**: User Stories 1 and 2 both work independently. SC-004 and SC-005
hold, and the count of keys with an unexplained advisory status is zero.

---

## Phase 5: User Story 3 - Every documented claim about this guard is true on the platform it appears on (Priority: P3)

**Goal**: Whatever the shipped documentation says about this guard either happens,
or the document says plainly that it does not happen yet and names what will make
it happen.

**Independent Test**: Read each shipped statement about this guard on both
platforms and confirm each one either describes behavior the guard performs or
labels itself as not yet wired.

**Source of wording**: apply the prose staged verbatim in the "Session 3 Staged
Documentation Prose" section of `docs/ai/specs/.process/ART-014-workflow.md`.
Clarify settled the wording; this phase applies it without redrafting.

**Division of labour, fixed by FR-013b**: the skill document keeps the quotable
sentence and names both skip conditions, because an operator whose run halts greps
the skill body for the sentence they just saw; the protocol reference owns the
branch order and the reason behind each verdict. The skill document must **not**
become a second copy of the truth table, and must **not** be reduced to a bare
pointer that removes the quotable sentence.

### Implementation for User Story 3

- [ ] T016 [US3] Replace the authority block at lines 752-759 of `speckit-pro/skills/speckit-autopilot/SKILL.md` with the staged replacement, correcting the three statements FR-013a names, each of which becomes false when this change lands: the unqualified "is the authority" claim, which is wrong because the comparison skips on an absent field and on an unresolvable repository root; the "fails with" exact-full-string claim, which FR-009 makes a prefix with both paths appended; and the lead-in's claim that repairing the workflow file to match is the correct move, which is true of the marker-evidence bullet beside it but false of the identity bullet, whose repair re-points the run or reclaims the state slot and rewrites the state from the invocation instead — so that claim moves into the marker-evidence bullet where it still holds. **Acceptance**: the FR-004a asymmetry survives the compression — "malformed **state** value" is the state side and "supplied workflow that resolves outside the repository" is the supplied side, and the two must not be blurred into one phrase about values. Both skip conditions are named. The quotable sentence is retained verbatim. [Spec §FR-013, §FR-013a, §FR-013b; Plan §D6.1]

- [ ] T017 [US3] Add the Claude-side expected-commit paragraph to `speckit-pro/skills/speckit-autopilot/SKILL.md` directly after the guard invocation block at line 477, mirroring where the Codex document carries it. It states the **same append contract** the Codex document carries **and** states plainly that the Claude flow does not yet fetch those values, citing **ART-016** by identifier. **Acceptance**: ART-016 is verified to exist in `docs/ai/specs/html-artifacts-technical-roadmap.md` before the citation is written — a shipped document naming an identifier that does not exist would repeat the defect class this specification repairs. The Claude tree carries no `--expected-base-commit` or `--expected-head-commit` string today; the only occurrences are the three Codex files, so this paragraph is the first Claude-side mention and must be labelled as not yet wired rather than as behavior. Word budget is not a constraint here: the Claude body measures 6213 of 8000 words. [Spec §FR-013, §Assumptions; Plan §D6.4]

- [ ] T018 [US3] Amend the Workflow File Protocol descriptor in the References index of `speckit-pro/skills/speckit-autopilot/SKILL.md` (line 809) so the new authority content is reachable from the index rather than only by full-text search. **Acceptance**: the descriptor names the `workflow_file` authority alongside the existing per-phase update table and Consensus Resolution Log schema. [Spec §FR-013c; Plan §D6.5]

- [ ] T019 [P] [US3] Add a `## workflow_file State Authority` section to `speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md`, placed **after** the `Stage` section and **before** PR Marker Plan Evidence, so the two precedence rules sit adjacent and their opposite directions are visible together. It carries the five ordered branches from FR-004d, the FR-004a resolution asymmetry, and the FR-004b byte-exact rule with the reason case is not folded. **Acceptance**: this file owns the branch order and the reason behind each verdict, per the FR-013b division of labour; it does not duplicate the skill document's quotable sentence framing. [Spec §FR-013, §FR-013b; Plan §D6.2]

- [ ] T020 [P] [US3] Append a condensed mirror of that authority section to `speckit-pro/codex-skills/speckit-autopilot/references/workflow-file-protocol-codex.md`, so the Codex platform carries the same `workflow_file` authority claim beside its related precedence rules. **Acceptance**: condensed rather than verbatim, matching how this file mirrors its Claude counterpart elsewhere; the five ordered branches and the byte-exact rule survive the compression. [Spec §FR-013, §US3 AS3; Plan §D6.3]

- [ ] T021 [US3] Amend the Workflow File Update Protocol descriptor in the References index of `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` (line 1053), which is the only references-index entry naming the protocol document on the Codex platform. FR-013c makes this a MUST ("on both platforms"), plan.md D6.5 requires it, and the staged prose item 5 requires it. **Declaration reconciled in Analyze**: this task once carried a scope flag, because the file was absent from the plan's then-five Declared File Operations, and the choice was between dropping a MUST and editing an undeclared file. Neither was taken. The plan's declaration now carries this file as its sixth entry, and the reviewability figures were re-run against six authored files rather than left to imply five. Nothing about the edit changed; only the declaration caught up with it. **Acceptance**: a four-word descriptor amendment, not prose — the Codex `SKILL.md` body measures 7795 of 8000 words with only 205 spare, which is exactly why the staged prose assigns this side a descriptor amendment rather than a paragraph. [Spec §FR-013c; Plan §D6.5, §Declared File Operations sixth entry]

- [ ] T022 [US3] Verify documentation truth across both platforms by manual read-through, per quickstart Scenario 7, and record the result in `docs/ai/specs/.process/ART-014-workflow.md`. The consensus panel resolved that no automated assertion is added, so this is the verification of record for SC-007. Confirm each of: the Claude `SKILL.md` authority bullet quotes the message as a **prefix** rather than an exact full string, names both skip conditions, and no longer claims that repairing the workflow file to match is the correct move for the identity bullet; the Claude-side expected-commit paragraph states the append contract **and** its not-yet-wired status citing ART-016; both platforms' protocol references carry the authority section with the branch order and the reason behind each verdict; the references index descriptor is amended on both platforms; and **ART-016 and ART-017 both exist** in `docs/ai/specs/html-artifacts-technical-roadmap.md`. **Acceptance**: the count of shipped statements promising unperformed enforcement is zero. [Spec §FR-013, §FR-013a, §FR-013b, §FR-013c, §SC-007; Quickstart §Scenario 7]

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Regenerate what the source edits restaled, record the evidence the PR
packet requires, and run the full gate.

- [ ] T023 Run `python3 scripts/refresh-release-artifacts.py` from the repository root and commit the result. Editing the guard restales four tracked copies: `dist/claude/`, `dist/codex/`, and the two installed-cache proofs under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/`. **Acceptance**: none of those four is hand-edited — they are generated, never authored, which is why they are deliberately absent from the Declared File Operations. CI's `artifact-consistency` job fails the pull request if this is skipped, so a stale payload cannot land. The Layer 6 Codex qualification corpus is **not** affected: it binds a digest chain over agent definition source bytes and no agent definition changes here. [Plan §D7; Spec §SC-008]

- [ ] T024 Regenerate the committed docs-site test reference page, required because a tracked `.py` file under `tests/speckit-pro/` changed. This is the one surface needing a bootstrap in a fresh worktree, so run `pnpm --dir docs-site install --frozen-lockfile` once first, then `pnpm --dir docs-site reference:generate`. **Acceptance**: `git status` is clean afterwards apart from the intended regeneration. [Plan §D7]

- [ ] T025 Run the after-half corpus regression and record both halves in `docs/ai/specs/.process/ART-014-workflow.md` and the PR body, reusing the **same harness** as the recorded before-half so the pair is comparable. Four properties are load-bearing and each has a silent failure mode: the denominator is pinned to baseline commit `3af4764e`, whose list is produced by `git ls-tree -r --name-only 3af4764e -- docs/ai/specs/.process/` filtered to names ending `-workflow.md` and returns 54, so it cannot drift as new specifications land and this specification's own in-flight workflow is excluded by construction; the synthesized state carries a `plan` array and a repository-relative `workflow_file`, without which the guard exits with the input-error code before any report prints and a recorded pass is an input error in disguise; the state file is written to a path **inside** the repository, because the repository root is derived from the **state** path and a state in a scratch directory outside the tree resolves no root, every comparison skips under FR-006, and all 54 report a pass while proving nothing; and — a **second** condition, not a restatement of the third — the state path is passed either **absolute** or **relative with the working directory at the repository root**, with the evidence **recording which form was used**. That condition governed the before-half, where writing the file inside the repository was necessary but not sufficient because the walk read the state path as supplied, so naming it relatively from a subdirectory produced the same 54 vacuous passes. T004's FR-006b fix closes that input, so the after-half does not depend on the spelling; keep the condition anyway, because reusing the identical harness is what makes the pair comparable and recording the form is what lets a reader tell a genuine after-half pass from one the old walk would also have produced. **Acceptance**: 54 of 54 still exit 0, and the deliberately mismatched canary in the same harness **flips from exit 0 to exit 1** with a non-empty `workflow_authority_errors`. The canary is the whole point: 54 passes prove nothing alone, because a skipped comparison and a satisfied comparison both exit 0, so if the canary still exits 0 the repair did not take regardless of what the other 54 report. This proof stays a one-time recorded run and is **not** wired into the committed suite. [Spec §SC-002, §PR Review Packet Requirements; Plan §D8; Quickstart §Scenario 6]

- [ ] T026 Generate the PR review packet into the pull-request description, sourcing traceability from `specs/art-014-phase-guard-enforcement-repair/tasks.md` and the evidence recorded in `docs/ai/specs/.process/ART-014-workflow.md`, with review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes. **Acceptance**: traceability maps each major requirement and success criterion to changed files and verification evidence; deferred work names its follow-up spec (ART-016 for the Claude live-PR-commit fetch, ART-017 for the three accidentally-advisory keys); the corpus regression evidence appears as a **before and after pair** with the canary result and the state-path form used, because that proof is a one-time recorded run rather than a committed test; and the FR-013c/Declared-File-Operations discrepancy from T021 is recorded under known gaps with its resolution. [Spec §PR Review Packet Requirements]

- [ ] T027 Run the full gate `python3 tests/speckit-pro/run-all.py` from the repository root and confirm **zero failures**, including the regenerated artifacts that editing the guard restaled. **Acceptance**: SC-008 holds and `git status` is clean. [Spec §SC-008; Quickstart §Scenario 5]

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Must run before any source edit, because
  it records a contrast that is unmeasurable afterwards.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS all user stories.**
- **User Story 1 (Phase 3)**: Depends on Foundational. Delivers the whole safety
  benefit on its own.
- **User Story 2 (Phase 4)**: Depends on Foundational. Independent of US1 in
  substance, but T013's completeness test derives its key set from a real report,
  which must already contain `workflow_authority_errors` (T007) for the new key to
  be classified rather than silently omitted. Sequence US1 first.
- **User Story 3 (Phase 5)**: Depends on Foundational for the behavior it
  describes to be true. Otherwise independent.
- **Polish (Phase 6)**: Depends on all three stories.

### User Story Dependencies

- **US1 (P1)**: No dependency on another story. This is the MVP.
- **US2 (P2)**: Soft dependency on T007 only, as above. Nothing in US2 changes
  runtime behavior.
- **US3 (P3)**: No code dependency. It documents what US1 and US2 make true, so
  it should not land before them or the documents describe unshipped behavior —
  the exact defect class this specification repairs.

### Within Each Phase

- Tests are written and verified **failing** before the implementation they
  constrain: T002 and T003 before T004 through T006; T013 before T014.
- The Foundational tests stay red for the whole phase by design. Red at the
  Phase 2 checkpoint is the expected state, not a defect.
- Guard edits (T004, T005, T006, T007, T008, T014) all land in the same file and
  are therefore strictly sequential; none is marked [P].

### Parallel Opportunities

- **T019 and T020** are the only genuinely parallel pair: different files
  (`references/workflow-file-protocol.md` and
  `references/workflow-file-protocol-codex.md`), no shared state, no ordering
  between them.
- T016, T017, and T018 all edit `speckit-pro/skills/speckit-autopilot/SKILL.md`
  and must be sequential despite belonging to the same story.
- T023 and T024 both regenerate artifacts but touch different trees; run T023
  first so the docs-site generation sees the settled test tree.

---

## Parallel Example: User Story 3

```bash
# The one safe parallel pair in this feature — different files, no ordering:
Task: "Add the workflow_file State Authority section to speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md"
Task: "Append the condensed authority mirror to speckit-pro/codex-skills/speckit-autopilot/references/workflow-file-protocol-codex.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — record the contrast while it is still measurable.
2. Complete Phase 2: Foundational (**CRITICAL** — blocks all stories).
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: the negative control exits non-zero, the positive
   control exits zero, the absent-field method exits zero, and both existing test
   files are still green.
5. At this point SC-001 and SC-003 hold and the shipped defect is repaired. US2
   and US3 add durability and truthfulness, not safety.

### Incremental Delivery

1. Setup + Foundational → the comparison runs, nothing gates yet.
2. Add US1 → the run halts on a mismatch → **MVP**.
3. Add US2 → advisory status becomes a recorded, test-enforced decision.
4. Add US3 → the shipped documentation matches the shipped behavior.
5. Polish → regenerate, record the evidence pair, run the full gate.

### Review Order Suggested For The PR

`RULE_PROBLEM_KEYS` and the `problems` merge first (the two-line change that moves
the exit code), then the helper and its truth table, then the return-shape widening
and its single call site, then the tests, then `PROBLEM_KEY_INTENT`, then the
documentation, then the generated artifacts last as a mechanical diff.

---

## Traceability

Every functional requirement maps to at least one task. Four requirements are
satisfied by verification or by a recorded decision rather than by an edit, and
are listed explicitly so no reader mistakes the absence of an edit for an
omission.

| Requirement | Task(s) |
|---|---|
| FR-001 unconditional placement | T006 |
| FR-002 gated path frozen | T006 (3-tuple rationale), T011 (re-run of its only committed coverage) — **no edit by design** |
| FR-003 absent field skips | T005 branch 1, T010, T012 |
| FR-004 mismatch fails | T005 branch 6, T002 |
| FR-004a resolution asymmetry | T005, T009 |
| FR-004b byte-exact | T005 |
| FR-004c out-of-boundary fails | T005 branch 5, T012 |
| FR-004d branch order | T005, T012 |
| FR-005 malformed fails, explicit whitespace check | T005 branches 3 and 4, T012 |
| FR-006 unresolvable root skips | T005 branch 2, T012 |
| FR-006a inducibility recorded and accepted | T025 (the harness discipline that record dictates) — **record-only, no edit** |
| FR-006b resolve before walking | T003, T004 |
| FR-007 new key, only key added | T007, T008 |
| FR-008 no second key armed | T008 (negative acceptance), Non-Goals |
| FR-009 message prefix plus both paths | T005, T002 |
| FR-010 closed three-value vocabulary | T014, T013 |
| FR-010a reason quality | T014 |
| FR-010b three accidental verdicts | T014 |
| FR-011 completeness from a real report | T013 |
| FR-012 controlled pair plus suite registration | T002, T009 |
| FR-013 documentation truthful on both platforms | T016, T017, T019, T020, T022 |
| FR-013a three corrections | T016 |
| FR-013b division of labour | T016, T019 |
| FR-013c index entry on both platforms | T018, T021 |
| SC-001 | T008, T002 |
| SC-002 | T025 |
| SC-003 | T002, T012 |
| SC-004 | T014 |
| SC-005 | T013, T015 |
| SC-006 | T001 (before), T008 (after) |
| SC-007 | T022 |
| SC-008 | T027 |

---

## Notes

- [P] tasks are different files with no dependency between them. Only T019 and
  T020 qualify.
- Every task cites the requirement it serves. A task that cannot be traced to one
  is a scoping error.
- Foundational tests are expected **red** at the Phase 2 checkpoint. Green there
  would mean the fixture is skipping the comparison, most likely a missing `.git`
  marker, and would be the vacuous pass FR-012 exists to prevent.
- If a re-measurement disagrees with a recorded count, that is drift to report in
  the workflow file, never a number to quietly change.
- **T021's declaration conflict is closed.** This phase carried it forward rather
  than deciding it alone: FR-013c and plan D6.5 both mandate editing
  `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`, which the plan's
  Declared File Operations did not list. Analyze resolved it the way the note
  asked, by amending the declaration to six entries and re-running the estimator,
  rather than by dropping the task. No unreconciled item remains.
