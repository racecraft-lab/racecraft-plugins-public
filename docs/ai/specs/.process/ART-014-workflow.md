# SpecKit Workflow: ART-014 — Phase-Guard Enforcement Repair

**Template Version**: 1.0.0
**Created**: 2026-08-12
**Purpose**: Executable workflow for ART-014. The prompts below are populated from the technical roadmap and the Grill Me interview run during `/speckit-pro:speckit-scaffold-spec`.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec` on 2026-08-12. The full Q&A log, Goals,
Non-goals, Evidence Base, and Open Questions live at:

```text
docs/ai/specs/.process/ART-014-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. Eleven
questions were asked and answered; the design concept doc is the source of truth
for every scoping decision it records. Its **Evidence Base** section carries the
empirical reproduction of the defect and the measured regression baseline, both
run against commit `3af4764e`. Do not re-derive those numbers; verify them if you
doubt them, and record any drift.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol, never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | 13 FRs, 3 user stories, 12 acceptance scenarios. G1 helper passed; 2 markers found by hand, routed to Clarify |
| Clarify | `/speckit-clarify` | 🔄 In Progress | 3 sessions. Required: 2 open markers |
| Plan | `/speckit-plan` | ⏳ Pending | |
| Checklist | `/speckit-checklist` | ⏳ Pending | Run for each domain |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Confidence Gate | G6.5 | ⏳ Pending | Pre-Implement composite confidence |
| Implement | `/speckit-implement` | ⏳ Pending | |
| Post | Post-Implementation | ⏳ Pending | Canonical 12-item closeout |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

G6.5 is advisory by default, so no phase of the main loop flips its row. Leaving
it Pending is legitimate and does not make the rows below it read as out of
order; record the verdict in [Phase 6.5](#phase-65-confidence-gate) when the
gate runs.

### Phase Gates (SpecKit Best Practice)

Each phase requires **human review and approval** before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All user stories clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Ambiguities resolved, decisions documented |
| G3 | After Plan | Architecture approved, constitution gates pass, dependencies identified |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Task coverage verified, dependencies ordered |
| G6 | After Analyze | No `CRITICAL` issues, `WARNING` items reviewed |
| G6.5 | Before Implement | Composite confidence meets the autonomous implementation threshold |
| G7 | After Each Implementation Phase | Tests pass, manual verification complete |

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project
constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| II. Cross-Platform Runtime & Script Safety | Guard stays on Python 3.11+ standard library; no new Bash or `jq` dependency | `python3 tests/speckit-pro/run-all.py --layer 4` |
| IV. Test Coverage Before Merge | The new guard behavior has Layer 4 unit coverage under `tests/speckit-pro/unit/`, declared in `suite-manifest.json` | `python3 tests/speckit-pro/run-all.py` |
| VI. KISS, Simplicity & YAGNI | One new helper, one new problem key, one classification map. No abstraction layer, no configurability nobody asked for | Code review against the design concept's Non-goals |
| I. Plugin Structure Compliance | Editing the guard restales generated payloads; the artifact contract is accounted for before the work is called done | `python3 scripts/refresh-release-artifacts.py`, then CI `artifact-consistency` |

**Constitution Check:** ✅ PASS, recorded 2026-08-12 before Phase 1.

`python3 tests/speckit-pro/run-all.py` returned **7378/7378 passed, zero
failures** (L1 1447, L4 5745, L5 186; toolchain preflight ok). That satisfies
principle IV's quality gate, and principles I and II by way of the Layer 1 and
Layer 4 gates inside the same run. Principle VI is a review-time judgment and is
checked at Analyze and Code Review, not by a command.

**G0 test-count baseline: 7378.** Captured here before any implementation work,
which is what makes the G7 comparison meaningful. Preserve it. Do not recompute
it in a later session, including a `--stage implement` resume: a baseline
recaptured after this run's own tests would compare the tree against itself and
pass unconditionally. If a later observation differs, record it as a
non-blocking drift diagnostic naming both numbers and keep this value.

### Environment Recorded At Phase 0

| Field | Value |
|-------|-------|
| Branch | `art-014-phase-guard-enforcement-repair` (worktree) |
| `on_feature_branch` | `false`. Non-numeric branch; SpecKit resolves the feature directory through `.specify/feature.json` → `specs/art-014-phase-guard-enforcement-repair` |
| PROJECT_COMMANDS | `UNIT_TEST` and `FULL_VERIFY` = `python3 tests/speckit-pro/run-all.py`; BUILD, TYPECHECK, LINT are `N/A` for this stack |
| PRESET_CONVENTIONS | `speckit-pro-reviewability` v1.0.0 supplies the spec, plan, and tasks templates |
| Extensions | all 8 installed: agent-context, archive, checkpoint, git, retrospective, speckit-utils, verify, verify-tasks |
| `PROJECT_IMPLEMENTATION_AGENT` | `speckit-pro:phase-executor` (fallback; the two project agents are a release auditor and a skill reviewer, neither an implementation agent) |
| `CONFIDENCE_GATE_MODE` | `advisory` |
| `AGENT_TEAMS_AVAILABLE` | `true` |
| Stage | `full`, source `argv`, basis `explicit --stage full` |
| State slot | reclaimed from `docs/ai/specs/.process/ART-012-workflow.md`; `prior_run_note` = `completed_archived` |
| Coverage guard | exit 0, report `status: pass`, all problem keys empty |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-014 |
| **Name** | Phase-Guard Enforcement Repair |
| **Branch** | `art-014-phase-guard-enforcement-repair` |
| **Dependencies** | None. Found during ART-006, which deliberately did not fix it |
| **Enables** | Trustworthy phase-guard verdicts |
| **Priority** | P2 |
| **Stage** | full |

Resolved 2026-08-12 from an explicit `--stage full`. Auto-detect would have
returned `plan`, because on a fresh scaffold the first non-terminal planning
phase is always Specify; the operator chose the full range so the run continues
through Implement and the post-implementation closeout. This row is the
authoritative durable store; `autopilot-state.json.stage` mirrors it for the
active run only.

### Reviewability Budget And Split Decision

The setup gate returned `status: warn`, `pass: true`, `blockers: []`. The single
warning is `primary surfaces 3 exceeds warn threshold 1`, which the helper derives
from the roadmap document as a whole rather than from this spec: it regex-scans
the whole file and takes the **last** match for each figure, so the LOC it
reported (90) is ART-015's number, not ART-014's. Recording the budget and split
decision is what the warn path requires.

| Signal set | Reviewable LOC | Slices | Status |
|---|---|---|---|
| Roadmap-declared (~120 LOC, 2 production, 5 total, modify-weighted) | 120 | 1 | ok |
| Grill-me initial (3 stories, 3 files, 13 FRs, modify) | 195 | 1 | ok |
| **Adopted — after Q8 and Q11 added authored files (3, 5, 13, modify)** | **235** | **1** | **ok** |

**Split decision: one slice, no split.** The work is vertical. It cuts
end-to-end through guard logic, error reporting, rule registration, tests, and
documentation, and every part of it exists to make one capability true: a
mismatched workflow halts the run. Splitting would put the comparison in one PR
and the registration that makes it matter in another, which is a strictly worse
review unit than the whole vertical.

**Budget amendment recorded at scaffold time.** The roadmap declares ~2
production files and ~5 total. Q8 (Claude-side flag documentation) and Q11 (the
paired `workflow-file-protocol` references) raised the authored count:

- Production files (4): the guard,
  `speckit-pro/skills/speckit-autopilot/SKILL.md`,
  `speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md`,
  `speckit-pro/codex-skills/speckit-autopilot/references/workflow-file-protocol-codex.md`
- Test files (1): `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`
- Generated, never hand-edited (4): `dist/claude`, `dist/codex`, and two
  installed-cache proofs under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/`

Production files at 4 stay under the warn threshold of 6; reviewable LOC at 235
stays under 400. Re-estimate at G3 against the real plan artifacts, and again at
any amendment. Re-check at the PR-time diff-mode gate, which measures the real
diff rather than a forward guess.

### Success Criteria Summary

- [ ] The identity comparison runs on the invocation the autopilot actually
      issues, with no `pr-marker-plan.v2` and no `--expected-head-commit`
- [ ] A state naming a different specification produces a non-zero exit under
      `--rule status-evidence`, which it does not today
- [ ] The failure message keeps `supplied workflow does not match autopilot state
      workflow_file authority` as its prefix and names both paths after it
- [ ] A state that omits `workflow_file` still passes; a state whose
      `workflow_file` is malformed fails
- [ ] A run whose state file sits outside a git repository still passes
- [ ] The existing `pr-marker-plan.v2` plus `--expected-head-commit` byte
      comparison behaves exactly as it does today
- [ ] All 54 corpus workflow files under `docs/ai/specs/.process/*-workflow.md`
      still exit 0 under `--rule status-evidence` with a matching state
- [ ] Every problem key the report emits is classified in `PROBLEM_KEY_INTENT`,
      and a test fails if a future key is added without a verdict
- [ ] Exactly one key is newly armed: `workflow_authority_errors`
- [ ] `SKILL.md`'s authority claim is true as written, including the skip
      conditions
- [ ] Both `workflow-file-protocol` references state the authority rule
- [ ] The Claude `SKILL.md` documents the `--expected-*-commit` flags and says
      plainly that the Claude flow does not yet supply them
- [ ] Generated payloads and installed-cache proofs are refreshed;
      `artifact-consistency` passes

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT**
and **WHY**, not implementation details. Output:
`specs/art-014-phase-guard-enforcement-repair/spec.md`

### Specify Prompt

```text
/speckit-specify Make the autopilot phase guard's workflow-identity check actually enforce the authority its documentation promises, and record per problem key whether advisory status is deliberate
```

#### Detailed Prompt (for complex specs)

```text
/speckit-specify

## Feature: Phase-Guard Enforcement Repair

### Problem Statement

speckit-pro/skills/speckit-autopilot/SKILL.md documents
autopilot-state.json.workflow_file as authoritative for which workflow is active,
and quotes the failure message a mismatch produces: "supplied workflow does not
match autopilot state workflow_file authority". That message cannot be produced
by the invocation the autopilot actually issues. Two independent defects, both
reproduced by execution during scoping against a state naming a different
specification:

1. _authorized_workflow_text returns no errors unless the state carries a
   pr-marker-plan.v2 schema AND --expected-head-commit was supplied. A normal
   autopilot run satisfies neither, so the two paths are never compared. Measured:
   workflow_checkpoint_errors comes back empty, exit 0.
2. Its errors are folded into workflow_checkpoint_errors, which is absent from
   the status-evidence tuple of RULE_PROBLEM_KEYS. The autopilot always invokes
   --rule status-evidence and main() scopes the exit code to the selected rule's
   keys, so even a produced error cannot fail the run. Measured: with the
   preconditions satisfied the documented message IS produced, and the exit code
   is still 0; dropping --rule makes the same run exit 1.

Separately, 12 of the guard's 20 problem keys cannot move the exit code under any
named rule. SKILL.md justifies the coverage lists as deliberately advisory
because the existing workflow corpus predates them. Nothing distinguishes those
deliberate cases from keys that are advisory by accident, which is exactly how
this defect survived.

### Users

Maintainers running /speckit-pro:speckit-autopilot on either platform. The guard
is one shared script; the Codex distribution ships the same skills/ path, so both
platforms inherit the repair and both inherit the new failure.

### User Stories

- US1 — A mismatched workflow halts the run. As a maintainer resuming autopilot
  in the wrong worktree, or against a stale state slot, I get a non-zero exit and
  a message naming both paths, instead of a run that proceeds against the wrong
  specification and reports pass.
- US2 — Advisory status is a recorded decision, not an accident. As a maintainer
  reading the guard, I can tell for every problem key whether it is gated or
  deliberately advisory and why, and a future key cannot be added without a
  verdict.
- US3 — Every documented claim about this guard is true on the platform it
  appears on. As a maintainer on either platform, the documentation I read
  describes enforcement that actually happens, or says plainly that it does not
  yet.

### Constraints

- The identity comparison runs unconditionally, in its own block placed before
  the marker-plan and head-commit gate. The existing gated PR-head byte
  comparison keeps its current semantics untouched, because the Codex flow
  genuinely supplies those OIDs from live PR metadata.
- Absence of state.workflow_file is not an error. A state that does not name a
  workflow asserts no authority. A malformed value IS an error, so a garbage
  value cannot silently disable the check.
- An unresolvable repository root is not an error. It means the comparison does
  not run, matching the precedent validate_state_status already sets in the same
  file for an extracted copy.
- Exactly one new key is armed: workflow_authority_errors, added to the
  status-evidence tuple. workflow_checkpoint_errors is NOT widened, because it is
  produced at four other sites by validate_workflow_checkpoint_bindings and
  widening it would arm every PR Marker Plan Evidence binding check at once.
- The documented sentence stays intact as the message prefix; both paths are
  appended after it.
- Python 3.11+ standard library only. No new Bash or jq dependency.
- The measured baseline is 54 of 54 corpus workflow files exiting 0 under
  --rule status-evidence. That must still hold.

### Out of Scope

- Arming any advisory key other than workflow_authority_errors. Anything the
  audit finds accidentally advisory becomes a roadmap follow-up carrying its
  evidence, not work in this slice.
- Changing what the coverage lists check.
- Re-litigating the --rule scoping mechanism, which is deliberate and documented.
- Making workflow_file a mandatory state field. That is a migration, not a
  repair; the tracked .specify/autopilot-state.json has no such field today.
- Wiring the Claude autopilot to fetch live PR baseRefOid and headRefOid. This
  spec documents the gap; the runtime work is its own spec.
- A committed test that walks the live docs/ai/specs/.process/ corpus.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | FR-001 through FR-013 (13) |
| User Stories | 3 (US1 mismatched workflow halts P1, US2 advisory status recorded P2, US3 documentation truthful P3) |
| Acceptance Criteria | 12 acceptance scenarios, 8 measurable success criteria |
| `[NEEDS CLARIFICATION]` markers | **2** (see the gate note below) |
| Gate G1 | Helper reported `pass: true, markers: 0`. Verified by hand as a **false pass**; routed to Clarify on the true count |
| Privacy scan | clean, no absolute paths in `spec.md` |
| Reviewability budget carried into spec | 235 reviewable LOC, 4 production files, 9 total, one slice, within budget |

**G1 gate note: the marker counter has a false-pass bug, and it is the same
defect class this spec exists to repair.** `validate-gate` counts the pattern
`\[NEEDS CLARIFICATION\]`, with the closing bracket immediately after the word.
The preset spec template prescribes the colon form and demonstrates it twice in
its own example requirements: `[NEEDS CLARIFICATION: auth method not specified
- email/password, SSO, OAuth?]`. The colon form never matches, so the gate
counted 0 against a file that carries 2. Measured on this spec:

| Pattern | Matches in `spec.md` |
|---|---|
| `\[NEEDS CLARIFICATION\]` (what the gate counts) | 0 |
| `\[NEEDS CLARIFICATION:` (what the template emits) | 2 |

Phase 2 is conditional on G1 detecting markers, so taking the gate at its word
would have skipped Clarify entirely and silently dropped both open questions.
The autopilot proceeded on the true count. This is out of scope for ART-014,
which owns the phase-coverage guard rather than the runner's gate helper, and it
is recorded here as a follow-up candidate.

The two markers are the design concept's own Open Questions, so they are
expected rather than a defect in the spec:

1. Which roadmap identifier replaces the `ART-0NN` placeholder in the
   documentation note about the unwired Claude-side commit fetch.
2. Whether the two tracked autopilot state slots are read by different callers,
   and so whether this change records the finding only or also converges them.

### Files Generated

- [x] `specs/art-014-phase-guard-enforcement-repair/spec.md` (293 lines)

### SpecKit Traceability Markers

Use these markers in spec.md for traceability through later phases:

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] User searches by query` |
| `[FR-001]` | Functional requirement | `[FR-001] API returns paginated results` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Auth method [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Can run alongside other tasks` |
| `[Gap]` | Missing coverage | `[Gap] No task covers error handling` |

---

## Phase 2: Clarify

**When to run:** When spec has areas that could be interpreted multiple ways.
10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

### Clarify Prompts

Seeded from the design concept's Open Questions. Do **not** re-litigate anything
the grill-me interview settled. Eleven decisions have determinate answers cited
in the design concept's Q&A log: comparison placement (Q1), problem key (Q2),
absent and malformed field semantics (Q3), unresolvable repo root (Q4), audit
form (Q5), arm scope (Q6), the `--expected-head-commit` documentation decision
(Q7 and Q8), message wording (Q9), corpus proof form (Q10), and the Codex
documentation home (Q11). Treat all eleven as given.

#### Session 1: The Advisory Audit

```text
/speckit-clarify Focus on the per-key advisory audit, NOT on whether to do it and
NOT on what to do with the result. Both are settled: design-concept Q5 fixes the
form as a PROBLEM_KEY_INTENT map inside
speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
with a test asserting no emitted key is missing from it, and Q6 fixes the outcome
as arm-only-the-identity-key with everything else recorded and any accidental
case filed as a roadmap follow-up. Measured starting point: the report emits 20
problem keys, 8 of which are reachable by a named rule (status-evidence: 3, plus
workflow_authority_errors makes 4; coverage: 5) and 12 of which are advisory.
What is still open and must be settled here: what a verdict string must contain
to count as a real classification rather than a restatement of the key name; what
the closed vocabulary of verdicts is, if any, beyond gated and advisory; how the
completeness test discovers the emitted key set without hardcoding a parallel
list that can itself drift; whether a key that is currently unreachable because
its producing function returns early under every realistic state counts as
deliberately advisory or as untested; and where a follow-up roadmap ID gets
recorded once the audit finds an accidental case, given the map is in a shipped
source file.
```

#### Session 2: Comparison Semantics And The Corpus Contract

```text
/speckit-clarify Focus on the exact semantics of the unconditional identity
comparison. Placement is settled by design-concept Q1 (its own block before the
marker-plan and head-commit gate, existing gated path untouched), the skip and
fail truth table by Q3 (absent skips, malformed fails, mismatched fails) and Q4
(unresolvable repo root skips), and the message wording by Q9 (documented
sentence as prefix, both paths appended). Do not reopen any of those. What is
still open: whether the supplied workflow path is compared after resolving
symlinks and how that interacts with a path that resolves outside the repository
root, which the existing gated code treats as an error; what happens when the
supplied workflow file does not exist on disk at all; whether the comparison is
case-sensitive on a case-insensitive filesystem, which macOS and CI Linux would
answer differently; how the 54-of-54 corpus regression is executed and recorded
so the evidence is reproducible from the workflow file alone; and whether the
positive control belongs in the same test as the negative control or as its own
case.
```

#### Session 3: Documentation Truth And Platform Reach

```text
/speckit-clarify Focus on making the documentation claims true. The homes are
settled: design-concept Q11 puts the workflow_file authority statement in BOTH
speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md and
speckit-pro/codex-skills/speckit-autopilot/references/workflow-file-protocol-codex.md,
and Q7/Q8 put the --expected-base-commit and --expected-head-commit contract in
the Claude SKILL.md together with an explicit statement that the Claude flow does
not yet fetch those OIDs. Do not reopen either home. What is still open: the
exact wording of the SKILL.md authority bullet now that the check has skip
conditions the current sentence does not mention; whether the SKILL.md bullet
should point at workflow-file-protocol.md rather than restate the rule, given the
sentence must stay quotable as the message prefix; what follow-up roadmap ID
replaces the ART-0NN placeholder in the unwired-status note and whether that ID
must exist before this spec can merge; whether the Codex SKILL.md needs any
pointer at all now that the reference carries the rule; and whether adding a
Codex-side string requires the three-step ritual of editing the file, adding the
assertion to validate-codex-skills.py, and updating CODEX-PARITY-NOTES.md.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | The Advisory Audit | 5 open items, all resolved from evidence, 0 routed to consensus | Verdict vocabulary widened from two values to three after the audit found an accidentally-advisory key. FR-010 rewritten, FR-010a and FR-010b added, FR-011 tightened to derive the key set from a real report. Both spec markers cleared. ART-016 and ART-017 opened in the roadmap. Spec 13 → 15 normative requirements, 0 markers |
| 2 | Comparison Semantics And The Corpus Contract | | |
| 3 | Documentation Truth And Platform Reach | | |

#### Session 1 Findings

The audit produced one substantive discovery, reproduced by execution rather
than argued from the source.

**`in_progress_errors`, `duplicate_state_steps`, and `state_order_errors` are
advisory by accident, not by design.** All three come from `validate_state`,
which also produces two keys that *are* gated under the `coverage` rule, so the
split is per-key rather than per-function. `SKILL.md` justifies advisory status
on the grounds that the existing workflow corpus predates the checks. That
reasoning holds for the coverage lists and fails for these three: they are
invariants of the state file the current run just wrote, so no legacy artifact
can violate them.

Negative control, run against a state file with two steps marked `in_progress`:

| Invocation | `in_progress_errors` | Exit |
|---|---|---|
| no `--rule` | fires, naming both steps | 1 |
| `--rule status-evidence` (what the autopilot issues) | fires, naming both steps | **0** |

A working check, wholly inert under the real invocation. That is the same shape
as the workflow-identity defect this specification repairs. All three keys are
empty against this run's live state and across the corpus, so arming them later
carries no measured regression cost. Per the scoping decision to arm only the
identity key, ART-014 records the verdict and ART-017 arms them.

**Marker resolutions.** The `ART-0NN` placeholder resolves to **ART-016**, and
the two-state-slot question resolves to record-only, because the slots have
different writers: the workflow-directory slot is the current run pointer, while
`.specify/autopilot-state.json` is the older slot still rewritten by post-merge
archive hygiene. Both roadmap entries were created by this change, so no shipped
document cites an identifier that does not exist.

**Executor note.** The `clarify-executor` subagent signalled idle without
returning its question set, twice, so the orchestrator performed session 1's
analysis directly in the main session. Rule 5 already assigns the orchestrator
the answering and editing role; only the question-drafting step was lost. Every
finding above carries its own `file:line` or execution evidence and none of it
depends on the subagent's output.

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation
blueprint. Output: `specs/art-014-phase-guard-enforcement-repair/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Language: Python 3.11+ standard library only (constitution II). No third-party
  imports, no new Bash or jq dependency.
- Guard: speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
  (4116 lines at scaffold time)
- Tests: unittest, Layer 4 under tests/speckit-pro/unit/, declared in
  tests/speckit-pro/suite-manifest.json
- Distribution: one authored guard under speckit-pro/skills/. There is no
  speckit-pro/codex-skills/speckit-autopilot/scripts/ directory; the Codex
  distribution ships the same skills/ path. Four other tracked copies are
  generated: dist/claude, dist/codex, and two installed-cache proofs.

## Constraints

- Placement (design-concept Q1): add a helper that runs unconditionally at the
  top of _authorized_workflow_text, before the pr-marker-plan.v2 and
  expected_head_commit early returns. Those two early returns change from
  returning [] to returning the helper's errors. The gated PR-head byte
  comparison below them is untouched, because the Codex flow supplies those OIDs
  per codex-skills/speckit-autopilot/SKILL.md and its two references.
- Reporting (design-concept Q2): the helper's errors go to a NEW
  workflow_authority_errors key, not into workflow_checkpoint_errors. Add only
  that key to the status-evidence tuple of RULE_PROBLEM_KEYS. Do not widen
  workflow_checkpoint_errors: it is produced at four other sites by
  validate_workflow_checkpoint_bindings, all checking PR Marker Plan Evidence
  table bindings, and widening it arms all of them against a corpus that has
  never had to satisfy them.
- Truth table (design-concept Q3 and Q4): absent or non-string workflow_file
  skips; malformed path fails; mismatch fails; unresolvable repository root
  skips. The skip cases exist because the tracked .specify/autopilot-state.json
  has no workflow_file at all, and because validate_state_status already sets the
  extracted-copy precedent in the same file.
- Message (design-concept Q9): keep "supplied workflow does not match autopilot
  state workflow_file authority" as an exact prefix, then append the supplied
  path and the path the state names. Tests assert the prefix, not the full
  string.
- Audit (design-concept Q5 and Q6): add PROBLEM_KEY_INTENT classifying all 20
  emitted keys plus the new one, with a test asserting the report emits nothing
  unclassified. Arm exactly one key.
- Documentation (design-concept Q7, Q8, Q11): the authority rule goes in both
  workflow-file-protocol references; the --expected-*-commit contract plus its
  unwired-on-Claude status goes in the Claude SKILL.md.

## Architecture Notes

- Report assembly merges eight per-check dicts into `problems`. The new key needs
  its own dict in that merge, not an extend into an existing one.
- main() scopes the exit code to the selected rule's keys. Registering the key is
  what makes the comparison load-bearing; the comparison alone is not enough, and
  neither is registration alone. Both halves are required and each is
  independently testable.
- Editing the guard restales generated payloads. Run
  `python3 scripts/refresh-release-artifacts.py` and account for the two
  installed-cache proofs before calling the work done. CI's artifact-consistency
  job fails the PR otherwise.
- Re-read docs/ai/specs/.process/ART-014-design-concept.md during planning for
  any context these constraints did not capture, in particular the Evidence Base
  section's three-way reproduction table and the measured 54-of-54 baseline.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales (if needed) |
| `data-model.md` | ⏳ | Likely N/A; this spec adds no entities |
| `contracts/` | ⏳ | Likely N/A; no new API surface |
| `quickstart.md` | ⏳ | Developer onboarding |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan`. Validates both spec AND plan together.

### Step 1: Analyze Spec for Recommended Domains

Signals present in this spec, from the grill-me interview:

| Signal | Recommended Domain |
|---|---|
| Error handling, skip-versus-fail truth table, degradation when the repo root is unavailable | **error-handling** |
| Legacy state shapes, a tracked state missing the field the check reads, malformed path values | **data-integrity** |
| A guard whose whole purpose is refusing to proceed against the wrong specification; a check that can be silently disabled | **security** |

Three domains. Skip **ux**, **accessibility**, **api-contracts**,
**performance**, **llm-integration**, and **streaming-protocol**: this spec has
no user-facing surface, no API, no budget, and no model or stream involvement.
**state-management** overlaps data-integrity here and would mostly duplicate it;
fold any state-lifecycle question into the data-integrity run.

### Step 2: Run Enriched Checklist Prompts

#### 1. error-handling Checklist

<!-- Why this domain: the spec is almost entirely a decision about when a check
     errors, when it stays silent, and what the operator sees when it does. -->

```text
/speckit-checklist error-handling

Focus on ART-014 requirements:
- Every branch of the skip-versus-fail truth table has a stated expected outcome:
  absent workflow_file, non-string workflow_file, malformed path, matching path,
  mismatched path, unresolvable repository root
- The failure message names both paths and keeps the documented sentence as an
  exact prefix
- A run that skips the comparison is indistinguishable from a run that passes it,
  from the exit code's perspective, and that is intentional and stated
- The existing gated PR-head byte comparison's error paths are unchanged
- Pay special attention to: the case where the supplied workflow file does not
  exist on disk, which no answered interview question covers
```

#### 2. data-integrity Checklist

<!-- Why this domain: two tracked state files disagree on whether the field the
     check reads exists at all, and the spec must not break either. -->

```text
/speckit-checklist data-integrity

Focus on ART-014 requirements:
- The tracked .specify/autopilot-state.json, which has no workflow_file, still
  passes after the change
- The tracked docs/ai/specs/.process/autopilot-state.json, which names
  docs/ai/specs/.process/ART-012-workflow.md, is compared
- Path normalization rules are stated: what counts as normalized, and how
  backslashes, absolute paths, and .. segments are rejected
- The 54-of-54 corpus baseline is stated as a measured fact with the command that
  produces it, so it is reproducible
- Pay special attention to: whether the two state slots are read by different
  callers, which the design concept flags as an open question
```

#### 3. security Checklist

<!-- Why this domain: the guard's job is refusing to act on the wrong
     specification; a check that can be silently disabled is the failure mode. -->

```text
/speckit-checklist security

Focus on ART-014 requirements:
- No input value can silently disable the identity comparison; a malformed
  workflow_file fails rather than skips
- A workflow path resolving outside the repository root is rejected
- The new key cannot be bypassed by a caller passing a different --rule, or if it
  can, that is stated as accepted and why
- The PROBLEM_KEY_INTENT completeness test cannot pass while a key is
  unclassified, including a key added by a future spec
- Pay special attention to: whether skipping on an unresolvable repository root
  creates an exploitable path, given an attacker who controls where the state
  file lives
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| error-handling | | | |
| data-integrity | | | |
| security | | | |
| **Total** | | | |

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap. Is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why, and check it against
   the design concept's Non-goals before accepting it as out of scope

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output:
`specs/art-014-phase-guard-enforcement-repair/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: the comparison and the registration are independently
  testable and BOTH are required; neither alone fixes the defect
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story, not by technical layer

## Implementation Phases
1. Foundation — the identity helper and its truth table, with the negative
   control written first per TDD
2. US1 — registration under workflow_authority_errors and the exit-code move
3. US2 — PROBLEM_KEY_INTENT and the completeness test
4. US3 — documentation across SKILL.md and both workflow-file-protocol
   references
5. Polish — generated-artifact refresh, corpus regression evidence run

## Constraints
- Test files live in tests/speckit-pro/unit/. The negative control belongs in
  test-autopilot-bookkeeping-guard.py, which already describes itself as the
  negative-fixture suite for the guard's --rule exit-code scoping. Layer 4 is
  "Unit Tests" in tests/speckit-pro/suite-manifest.json.
- Do NOT hand-edit dist/ payloads or the installed-cache proofs under
  tests/speckit-pro/unit/fixtures/plugin-bash-confinement/. They are regenerated
  by scripts/refresh-release-artifacts.py.
- Bound task generation by the design concept's Non-goals. Flag any task that
  would arm a second problem key, make workflow_file mandatory, commit a live
  corpus walk, or wire the Claude live-PR-OID fetch. Those are out of scope and a
  task proposing one is a scoping error, not a nice-to-have.
- The design concept's Q&A log carries the "why" behind each decision. Use it for
  test specifications and edge-case handling; a decision recorded there that no
  task reflects is a gap to surface before coding, not something to drop.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | |
| **Phases** | |
| **Parallel Opportunities** | |
| **User Stories Covered** | |

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, the autopilot SKILL runs
the read-only atomicity classifier and records its decision here. This is a
**placeholder** until then; leave the cells blank during scoping.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change. |
| **Signals** | | The decisive detector findings behind the route and releasability reading. |
| **Warnings** | | Any release-safety warning attached to the change. |

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/art-014-phase-guard-enforcement-repair
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Cross-artifact consistency across spec.md, plan.md, tasks.md AND
docs/ai/specs/.process/ART-014-design-concept.md.

Focus on:
1. Constitution alignment — Python 3.11+ stdlib only, Layer 4 coverage declared
   in suite-manifest.json, KISS (one helper, one key, one map; no abstraction
   layer)
2. Coverage gaps — every FR and user story has tasks; both halves of the fix
   (comparison and registration) are covered independently
3. Drift from the design concept — its Goals, Non-goals, and eleven recorded
   decisions are the source of truth for scoping. If a downstream artifact
   contradicts one, the downstream artifact is wrong unless it carries an
   explicit revision note. Check in particular: has anything crept in that arms a
   second problem key, mandates workflow_file, commits a live corpus walk, or
   wires the Claude live-PR-OID fetch?
4. Numbers — the design concept's Evidence Base records 20 problem keys, 12
   advisory, 54 corpus files, and a 54-of-54 baseline, all measured at commit
   3af4764e. If any artifact restates these, they must agree. If the tree has
   moved, re-measure and record the drift rather than silently updating.
5. Generated-artifact accounting — the plan or tasks must include the
   refresh-release-artifacts step; a guard change without it fails CI.
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| `CRITICAL` | Blocks implementation, violates constitution | **Must fix before G6 gate** |
| `HIGH` | Significant gap, impacts quality | Should fix |
| `MEDIUM` | Improvement opportunity | Review and decide |
| `LOW` | Minor inconsistency | Note for future |

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 6.5: Confidence Gate

**When to run:** After Phase 6 commits and before Phase 7 begins.

| Field | Value |
|-------|-------|
| Mode | |
| Composite confidence | |
| Verdict | |
| Evidence | |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```text
/speckit-implement

## Approach: TDD-First

For each task, follow this cycle:

1. RED: Write failing test defining expected behavior
2. GREEN: Implement minimum code to make test pass
3. REFACTOR: Clean up while tests still pass
4. VERIFY: Manual verification of acceptance criteria

The negative control is the natural first RED. It must fail against today's guard
for the right reason: exit 0 where 1 is expected. If it fails for any other
reason, the fixture is wrong, not the guard.

### Pre-Implementation Setup

1. Confirm you are in the art-014-phase-guard-enforcement-repair worktree and on
   that branch, not main
2. Run `python3 tests/speckit-pro/run-all.py` and record the baseline test count
   before changing anything
3. Reproduce the defect once yourself, so the fix is verified against an observed
   failure rather than a described one

### Implementation Notes

- Consult docs/ai/specs/.process/ART-014-design-concept.md for the "why" behind
  each decision. Its Q&A log records what was recommended, what was chosen, and
  the reasoning, including two answers where the operator chose against the
  recommendation (Q7) and the follow-up that resolved the tension it created
  (Q8).
- The message prefix is load-bearing: `SKILL.md`, the roadmap, the ART-006
  retrospective, and an archive report all quote it. Two of those are archived
  and must not be edited. Keep the prefix exact.
- The ART-0NN placeholder in the SKILL.md unwired-status note must be replaced
  with a real roadmap ID before merge.
- Corpus regression evidence: run the guard across every
  docs/ai/specs/.process/*-workflow.md with a state naming the matching workflow,
  under --rule status-evidence, before and after. Record both counts in this
  workflow file and in the PR body. The pre-change measurement at scaffold time
  was 54 of 54 exiting 0.
- After any guard edit: `python3 scripts/refresh-release-artifacts.py`, then
  verify the two installed-cache proofs and both dist/ copies moved with it.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | | | |
| 2 - US1 Registration | | | |
| 3 - US2 Audit Map | | | |
| 4 - US3 Documentation | | | |
| 5 - Polish | | | |

---

## Post-Implementation Checklist

The canonical closeout. Every row must reach Complete or an explicit
`Skipped` before the run may report completion.

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ⏳ Pending | |
| Post: Verify Implementation | ⏳ Pending | |
| Post: Verify Tasks Phantom Check | ⏳ Pending | |
| Post: Code Review | ⏳ Pending | |
| Post: Integration Suite | ⏳ Pending | |
| Post: Reviewability Diff Gate | ⏳ Pending | |
| Post: Self-Review | ⏳ Pending | |
| Post: UAT Runbook Generation | ⏳ Pending | |
| Post: PR Body Generation | ⏳ Pending | |
| Post: PR Creation | ⏳ Pending | |
| Post: Review Remediation | ⏳ Pending | |
| Post: Retrospective | ⏳ Pending | |

Repository quality gates (constitution):

- [ ] All tasks marked complete in tasks.md
- [ ] Full suite passes: `python3 tests/speckit-pro/run-all.py` (zero failures)
- [ ] Layer 1 structural validation passes
- [ ] Layer 4 unit coverage exists for the new guard behavior and is declared in
      `tests/speckit-pro/suite-manifest.json`
- [ ] Generated artifacts refreshed: `python3 scripts/refresh-release-artifacts.py`
- [ ] Corpus regression recorded: before and after counts, both 54 of 54
- [ ] PR title validates against the release-readiness gate:
      `<type>(<lowercase-scope>): <plain English description>`
- [ ] Exactly one non-empty ` ```release-note ` fence in the PR body
- [ ] PR created and reviewed

---

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

-

### Patterns to Reuse

-

---

## Project Structure Reference

```text
racecraft-plugins-public/
├── speckit-pro/
│   ├── skills/speckit-autopilot/
│   │   ├── SKILL.md                             # authority documentation
│   │   ├── references/workflow-file-protocol.md # authority rule (Claude)
│   │   └── scripts/
│   │       └── validate-autopilot-phase-coverage.py   # the guard
│   └── codex-skills/speckit-autopilot/
│       └── references/workflow-file-protocol-codex.md # authority rule (Codex)
├── tests/speckit-pro/
│   ├── suite-manifest.json                      # layer membership
│   └── unit/
│       ├── test-autopilot-bookkeeping-guard.py  # negative controls, --rule scoping
│       └── test-autopilot-phase-coverage.py     # broader guard coverage
├── dist/{claude,codex}/                         # generated, never hand-edited
├── docs/ai/specs/
│   ├── html-artifacts-technical-roadmap.md
│   └── .process/                                # design concepts, workflows
└── specs/art-014-phase-guard-enforcement-repair/
    └── SPEC-MOC.md
```

---

Template based on SpecKit best practices. Populated for ART-014 by
`/speckit-pro:speckit-scaffold-spec` on 2026-08-12.
