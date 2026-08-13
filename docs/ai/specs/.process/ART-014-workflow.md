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
| Clarify | `/speckit-clarify` | ✅ Complete | 3 sessions, 3 consensus items all resolved in Round 1, 0 markers remain |
| Plan | `/speckit-plan` | ✅ Complete | G3 pass, 0 markers. plan.md + research.md + quickstart.md; data-model and contracts justifiably skipped |
| Checklist | `/speckit-checklist` | ✅ Complete | 3 domains, 83 items, 19 gaps all closed. 2 security items routed to consensus, both resolved |
| Tasks | `/speckit-tasks` | ✅ Complete | G5 pass, 27 tasks across 6 phases, 0 markers. One scope gap found and fixed: the plan declared 5 files, FR-013c needs a 6th |
| Analyze | `/speckit-analyze` | ✅ Complete | G6 pass. 9 findings (0 critical, 2 high, 5 medium, 2 low), all remediated, 0 after 2 loops, nothing reopened |
| Confidence Gate | G6.5 | ⏳ Pending | Pre-Implement composite confidence |
| Implement | `/speckit-implement` | ✅ Complete | 27 tasks, G7 pass. Full gate 7385/7385, +7 over the 7378 baseline, zero failures |
| Post | Post-Implementation | ✅ Complete | 11 of 12 done; PR #433 open. Review remediation runs on a loop until the PR is reviewed |

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
| After Q8 and Q11 added authored files (3, 5, 13, modify) | 235 | 1 | ok |
| **Adopted — after Clarify and Checklist grew the requirement set to 24 (3, 5, 24, modify)** | **317** | **1** | **ok** |

**Third amendment, recorded at the security consensus.** The requirement count
rose from 13 to 24 across three clarify sessions and three checklist domains, and
the estimator was re-run rather than left stale, which is the failure ART-015
exists to prevent. The figure moves 235 to 317, still one slice and still under
the 400 ceiling. **No file was added**: every new requirement lands in the five
already-declared files, and FR-006b in particular is a single-line change to the
guard, which is production file one of four. The growth is requirement density
rather than surface area, which is the shape a repair specification should have.

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
| 2 | Comparison Semantics And The Corpus Contract | 5 asked, 4 resolved from evidence, 1 routed to consensus | Added FR-004a (asymmetric resolution), FR-004b (byte-exact, no case folding), FR-004c (out-of-boundary fails), FR-004d (branch ordering). Amended FR-005 (explicit whitespace check), FR-012 (two controls, one fixture, `.git` marker as a file), SC-002 (denominator pinned to the baseline commit), and the PR packet requirements (reproducible corpus harness plus a mismatch canary). Spec 15 → 19 normative requirements |
| 3 | Documentation Truth And Platform Reach | 5 asked, 3 resolved from evidence, 2 routed to consensus | Found three statements in the shipped authority block that this change makes false, not one. Added FR-013a, FR-013b, FR-013c. Both consensus items resolved without adding scope: the second failure sentence needs no new requirement, and no documentation assertion is added. Spec 19 → 22 normative requirements |

#### Session 2 Findings

Three findings, each of which would have produced evidence that looked green and
proved nothing.

**The corpus proof could have been vacuous.** The repository root is derived from
the **state** path, not the workflow path. A harness that synthesizes its state
into a scratch directory outside the tree resolves no root, FR-006 skips, and all
54 files report a pass while the comparison never runs. The recorded reproducer
must therefore write its state inside the repository and carry a deliberately
mismatched canary in the same harness. The canary is the only thing that
distinguishes 54 genuine passes from 54 silent skips.

**The negative control could have passed for the wrong reason**, for the same
underlying cause: a `tempfile` fixture with no repository marker skips the
comparison, so both controls pass and the negative one proves nothing. FR-012 now
requires the fixture to write a `.git` marker as a file, which arms the check and
exercises the worktree case at once.

**A whitespace-only `workflow_file` slips past the malformed branch.** Verified:
`_is_normalized_repo_path("  ")` and `_is_normalized_repo_path(" ")` both return
`True`, because a run of spaces is a valid POSIX path part. FR-005's whitespace
requirement was being satisfied only by accident, landing in the mismatch branch
and printing a blank path. FR-005 now requires an explicit check.

**Corpus counts, verified independently.** 54 files at baseline `3af4764e`, 55
tracked now; the difference is exactly this specification's own in-flight
workflow file. SC-002 pins the denominator to the baseline commit.

### Session 3 Staged Documentation Prose

Drafted during Clarify, applied during Implement. Clarify settles wording; it
does not edit shipped files. Phase 7 uses these verbatim.

**Word budgets, measured.** Claude autopilot `SKILL.md` body is 6213 of 8000
words, so 1787 spare and length is not a constraint. Codex autopilot `SKILL.md`
body is 7795 of 8000, so 205 spare, which is why the Codex side gets a
four-word descriptor amendment rather than prose.

**1. Replace the Claude `SKILL.md` authority block**, correcting the three false
statements FR-013a names. The lead-in loses its repair claim, which moves into
the marker-evidence bullet where it is still true:

```text
That precedence is scoped to the status table and does not generalize. The
state file stays authoritative for two things the coverage guard enforces
directly:

- **Which workflow file is active.** When the state names a `workflow_file` and
  a repository root resolves, that value is the authority. A mismatch fails with
  a message that opens with the exact sentence "supplied workflow does not match
  autopilot state workflow_file authority" and appends both compared paths. The
  comparison is skipped when the state names no `workflow_file`, because a state
  naming none asserts no authority, and skipped again when no repository root
  resolves. A malformed state value fails, and so does a supplied workflow that
  resolves outside the repository. Branch order and the reason behind each
  verdict live in
  [`references/workflow-file-protocol.md`](./references/workflow-file-protocol.md).
- **PR Marker Plan Evidence status**, which must equal
  `pr_marker_plan.status` exactly. Repairing the workflow file to match the
  state is the correct move here.
```

The FR-004a asymmetry survives the compression on purpose: "malformed **state**
value" is the state side, "supplied workflow that resolves outside the
repository" is the supplied side. Do not blur them into one phrase about values.

**2. New `## workflow_file State Authority` section** in
`references/workflow-file-protocol.md`, placed after the `Stage` section and
before PR Marker Plan Evidence, so the two precedence rules sit adjacent and
their opposite directions are visible together. It carries the five ordered
branches from FR-004d, the FR-004a asymmetry, and the FR-004b byte-exact rule.

**3. Condensed mirror** of the same section appended to
`codex-skills/speckit-autopilot/references/workflow-file-protocol-codex.md`.

**4. Claude-side expected-commit paragraph** (FR-013, Q7/Q8) placed directly
after the guard invocation block, mirroring where Codex carries it, and citing
**ART-016** for its not-yet-wired status. The Claude tree carries no
`--expected-base-commit` or `--expected-head-commit` string today; the only
occurrences are the three Codex files.

**5. References index descriptors** amended on both platforms (FR-013c).

**6. No Layer 1 assertion and no `CODEX-PARITY-NOTES.md` entry** for the main
Q5 decision. That file's stated scope is recording where the two variants are
deliberately *not* mirrors and listing the strings the validator pins. This
change is parity-restoring and pins nothing, so an entry would make that ledger
wrong. (The narrower question of whether to pin the authority sentence is with
consensus.)

### Corpus Regression Evidence

Captured before any implementation work, because the BEFORE half can only be
measured against unmodified code. Reproducible from this section alone, which is
what the PR packet requirements demand.

**Denominator, pinned to the baseline commit:**

```text
git ls-tree -r --name-only 3af4764e -- docs/ai/specs/.process/ | grep -- '-workflow\.md$'
```

54 files. The working tree tracks 55; the extra one is this specification's own
in-flight `ART-014-workflow.md`, excluded by construction because it is not in
the baseline tree.

**Synthesized state shape**, one per corpus file:

```json
{"workflow_file": "<repo-relative path>", "spec_id": "<id>", "plan": [{"step": "Specify"}]}
```

Written to a path **inside the repository**, and passed to the guard in a form
from which a repository root actually resolves. Both halves are load-bearing, and
the second is subtler than it first appeared.

The repository root is derived from the state path **as supplied**, not from a
resolved form. So the condition is not merely "the file lives inside the
repository": it is that the path as passed, combined with the working directory,
lets the parent walk find a repository marker. Measured on this tree:

| State path as supplied | Working directory | Root resolves |
|---|---|---|
| relative | repository root | yes, as `.` |
| absolute | anywhere | yes |
| relative | a subdirectory such as `docs/` | **no** |

**The before-half run used the relative form with the working directory at the
repository root**, so the root resolved as `.` and the measurement is valid. It
was one directory change away from being silently vacuous, which is worth stating
plainly rather than leaving as an implicit precondition. The after-half must use
the same discipline, and the recorded evidence must say which form it used.

This correction supersedes the looser phrasing recorded when the before-half was
captured, which said only that the state must sit inside the repository. That
condition is necessary and not sufficient.

**Invocation:**

```text
python3 speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py \
  --workflow <corpus file> --state <in-repo state> --rule status-evidence
```

**Results:**

| Run | Expectation | BEFORE (measured 2026-08-12) | AFTER (measured 2026-08-12) |
|---|---|---|---|
| 54 corpus files, state names the matching workflow | exit 0 | **54 of 54 exit 0** | **54 of 54 exit 0**, zero input errors, `workflow_authority_errors` present and empty on all 54 |
| Canary: state names a *different* workflow | exit 1 after the repair | **exit 0**, `workflow_checkpoint_errors` empty, `workflow_authority_errors` absent | **exit 1**, `workflow_checkpoint_errors` empty, `workflow_authority_errors` non-empty |

The canary is the whole point of the harness. Fifty-four passes prove nothing on
their own, because a skipped comparison and a satisfied comparison both exit 0.
The canary is the run that must change from 0 to 1; if it still exits 0 after the
change, the repair did not take regardless of what the other 54 report.

**After-half conditions, recorded so the pair is comparable.** The state path was
supplied in the **relative form with the working directory at the repository
root**, the same form the before-half used. The file was written to
`art-014-corpus-state.json` at the repository root and deleted when the run
finished. Every one of the 54 returned a full 25-key report rather than the
input-error object, so no recorded pass is an input error in disguise.

**A correction to how this evidence was first framed**, made during the manual
UAT of 2026-08-13. The original wording claimed the empty-but-**present**
`workflow_authority_errors` key on all 54 confirmed that a repository root had
resolved, "because a skipped comparison leaves the key absent". That inference
does not hold within the after-half. The repaired guard writes the key into the
report unconditionally, so a skipped comparison also yields present-and-empty at
exit 0 — reproduced by running the identical mismatched canary with the state
file outside the tree. Presence separates repaired code from unrepaired code, not
a satisfied comparison from a skipped one. What actually establishes that these
54 comparisons ran is that they and the canary used the identical state path and
working directory, and the canary demonstrably resolved a root and emitted the
identity message.

The canary supplied `docs/ai/specs/.process/ART-001-workflow.md` while the state
named `docs/ai/specs/.process/ART-002-workflow.md`, and the armed key reported:

```text
supplied workflow does not match autopilot state workflow_file authority: supplied docs/ai/specs/.process/ART-001-workflow.md, state names docs/ai/specs/.process/ART-002-workflow.md
```

The before-half emitted no such message because the comparison never ran. That
absence-to-message flip, not the unchanged 54, is what shows the repair took.

### Consensus Resolution Log

| # | Phase / Session | Item | Categories | Round | Analysts | Verdict | Applied |
|---|---|---|---|---|---|---|---|
| 1 | Clarify S2 | When the supplied workflow resolves outside a successfully resolved repository root, does the guard fail or skip? | `[codebase] [security]` | 1 | all 3 (security always fans out) | **FAIL**, unanimous 3 of 3, all high confidence, no escape to Round 2 | FR-004c and FR-004d added to `spec.md` |
| 2 | Clarify S3 | Must the shipped documentation quote the second failure sentence, "workflow file is outside the authorized repository"? | `[security] [spec]` | 1 | all 3 (security always fans out) | **OMIT**, 2 of 3. Codebase high, spec-context high, security dissenting at high | No new FR. FR-013's enumeration stays closed |
| 3 | Clarify S3 | Should a test pin the `workflow_file` authority sentence in both protocol references? | `[spec] [codebase]` | 1 | codebase, spec-context | **NO-ASSERT**. Spec-context high; codebase ASSERT at medium, having explicitly deferred the deciding spec-intent signal to spec-context | Recorded as a deferred idea below, not implemented |
| 4 | Checklist, security | Should repository-root resolution resolve the state path before walking, or is the spelling-dependent skip acceptable? | `[security]` | 1 | all 3 | **RESOLVE**, 2 of 3. Security high, codebase medium, spec-context dissenting at high on scope grounds | FR-006b added; FR-006a's second inducing input marked closed |
| 5 | Checklist, security | Should the spec accept that a caller passing a different `--rule` bypasses the newly armed key? | `[security]` | 1 | all 3 | **ACCEPT**, 2 of 3. Spec-context high, codebase high, security dissenting at medium | No change; already ratified in Assumptions |

**Item 4, why the scope objection lost.** The spec-context lens argued ACCEPT
well: the roadmap's Scope lists three items, none of which is touching a shared
resolution helper, and this project has a standing practice of recording a
residual risk and deferring the fix, which produced ART-016 and ART-017.

Two things outweighed it. First, the codebase lens dismantled the premise the
acceptance rested on. The security checklist declined to propose a fix because
the helper is shared, but tracing all three call sites shows **no consumer depends
on the unresolved form**: every one already normalizes independently before use,
at `:689`, `:973`, `:1267`, `:1323`, `:1581`, and `:3456`, and `_read_repo_bytes`
already applies exactly this defensive normalization to exactly this value. No
test locks the current behaviour in either, because every fixture builds absolute
temporary paths. The blast radius of changing it is not large; the blast radius of
**not** changing it is, because a false-negative root silently disables 16
`repo_root`-gated conditions in `validate_projection_integrity`, not just this
comparison.

Second, the scope objection reads the roadmap too narrowly. Its first Scope item
is "un-short-circuit the comparison". A root resolution that returns nothing for a
file genuinely inside the repository is another short-circuit that stops the
comparison from running, of the same kind as the marker-plan precondition this
specification already exists to remove. Closing it is inside the stated scope
rather than beyond it, and it costs no additional file: the guard is already
production file one of four.

**A correction to the panel's own record.** The codebase lens stated that this
project's corpus-evidence harness had already produced vacuous passes through this
exact defect. It did not. The before-half run used the relative form with the
working directory at the repository root, so the root resolved as `.` and the 54
of 54 measurement stands, as re-verified. The hazard was real and narrowly missed,
which is a good argument for FR-006b, but it was not realised and the record
should not say it was.

**Item 5, why ACCEPT was straightforward.** The `--rule` mechanism is documented
as deliberately caller-scoped in three independent first-party places that
predate this specification, and 12 of the 20 existing problem keys already carry
the identical bypass, including `checkpoint_source_fingerprint_errors`, the key
this guard's identity errors are folded into today. The dissent rated itself
medium and stated that its dividing line was a synthesis across sources rather
than a rule any one source states. Both alternatives were weighed and rejected
during the original interview.

**Item 2, why OMIT beat a well-argued MENTION.** The security lens made the
strongest external case in this run, grounded in CWE-1059, NIST SP 800-61r2,
OWASP fail-securely, and a structurally identical precedent in GCC 14, which
promoted implicit-function-declaration from warning to error and used the
documentation update as the vehicle for the promised clarity. It also supplied
the risk evidence: operators who cannot find an explanation for a security halt
disable the control, which is the documented SELinux pattern.

It lost on repository-specific evidence, not on quality. The spec's author typed
the FR-004c sentence verbatim and then wrote FR-013's three-item enumeration
seventy lines later without it. That enumeration then survived the commit that
introduced FR-004c, which edited FR-012 thirteen lines away, and survived a
session dedicated entirely to documentation truthfulness. Independently, of the
three problem keys already gated before this change, only one is named anywhere
in shipped prose: in this codebase gated does not imply documented, so silence
about a specific error string is the norm rather than a defect.

**What OMIT does and does not settle.** It settles that no requirement compels
*quoting the literal string*. It does not remove the obligation to describe the
branch: FR-013b requires the protocol reference to carry the branch order and the
reason behind each verdict, and the out-of-boundary case is one of those
branches. The staged reference prose therefore still documents that branch, and
names the message inside a description it must contain anyway. That is an
editorial choice with no requirement behind it and no measurable cost in an
uncapped reference file, and it is the part of the security lens's argument that
survives the majority verdict.

**Item 3, why this is not a genuine tie.** The codebase lens found real
precedent for asserting, including the fact that `workflow-file-protocol.md` is
already pinned in `tests/speckit-pro/unit/test-reviewability-marker-guidance.py`
under a content requirement with no companion test requirement. It capped itself
at medium and said plainly that the remaining signal, whether this author meant
to scope testing out of FR-013, belonged to another lens. Spec-context supplied
that signal at high confidence: design-concept Q11 chose the shared reference
precisely to avoid duplicating a sentence into two files "that nothing asserts
agree", so prose-parity risk was considered and answered with placement rather
than a test. US2's automated Independent Test and US3's manual-review Independent
Test have differed since the first commit and survived three clarify passes.

It also corrected a premise this orchestrator had accepted: a documentation pin
would **not** have caught the ART-014 defect. The mismatch sentence was quoted
verbatim in `SKILL.md` throughout the defect's entire life, so an `assertIn`
would have passed the whole time. The defect was an inert code path, which
FR-010 and FR-011 already cover. A prose pin defends against trim survival, a
real but different risk.

**Deferred idea, not filed as a roadmap entry.** Pinning the authority sentence
in both protocol references is a reasonable test-hygiene improvement, and
`CODEX-PARITY-NOTES.md` documents a real 1,070-to-500-line trim showing the risk
is not hypothetical. It is deferred rather than implemented because the declared
budget names a closed set of five authored files, and this repository has its own
recorded lesson, ART-015, about signals growing without re-running the estimator.
It is recorded here and in the pull request's known gaps rather than as a roadmap
entry, because unlike ART-016 and ART-017 no shipped artifact cites it, and
creating an entry nothing references would itself be the scope growth the verdict
rejected.

**Why unanimous rather than close.** The three lenses converged from independent
evidence. The codebase lens found five existing call sites using the shape
`repo_root and _repo_file(...) is None → append error`, where the `and`
short-circuit already separates "root unavailable" from "path escapes an
available root" and grants the free pass only to the first. The spec-context lens
found the same branch already coded inside the very function being modified, at
`:1322-1325`, failing rather than skipping, and established that none of the
eleven recorded interview decisions poses this scenario: Q4 settled "root cannot
be resolved", which is a different fact. The security lens grounded it externally
in CWE-706, CWE-22, CWE-59, OWASP's fail-securely rule, CWE-636, Zip Slip, and
PEP 706, the last being the closest available precedent, since Python's core team
faced the identical operation in `tarfile` after CVE-2007-4559 and chose to raise
and terminate rather than skip.

**A divergence the panel resolved.** The session-2 executor and the spec-context
lens both held that the out-of-boundary case should reuse the existing sentence
at `:1325`, while the codebase lens argued for the FR-009 documented prefix. The
reuse position wins on the narrower reading: FR-009's contract governs the
identity-mismatch message specifically, and a distinct sentence tells a
maintainer what is actually wrong, since an out-of-boundary path has no
repository-relative form to print in a mismatch message.

**The YAGNI objection was tested and failed.** Constitution principle VI bars
error handling for impossible scenarios. This branch is not that: once FR-001's
unconditional resolution exists, `Path.relative_to()` raises `ValueError` on any
non-subpath by ordinary Python semantics, so the branch is mechanically reached.
The only alternative to handling it is an unhandled exception.

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
| `plan.md` | ✅ | 8 design sections, an ordered 8-step implementation sequence, all 22 requirements mapped |
| `research.md` | ✅ | Not an unknowns burndown, since Clarify left zero markers. Records the three seams the settled inputs did not determine, each found by reading code |
| `data-model.md` | ⏭️ Skipped | The spec's Key Entities are conceptual vocabulary, not persisted structures. No state field added, no schema touched. The one new construct is a source constant fully specified in the plan |
| `contracts/` | ⏭️ Skipped | No external interface change: no new flag, no new `--rule` value, no schema file touched. The report gains one key, an additive change to an unversioned stdout payload, whose enforced record is the FR-011 completeness test |
| `quickstart.md` | ✅ | Seven runnable validation scenarios mapped to success criteria |

**Gate G3:** ✅ PASS, `plan.md exists with 0 unresolved markers`. Privacy scan
across the feature directory is clean.

#### Plan Findings

Three findings, two of which would have shipped a defect.

**1. The return shape is a seam the constraints underdetermined.** Today
`build_report` folds this function's entire error list into
`workflow_checkpoint_errors`, including the gated path's own errors. Re-keying
the whole return is the small diff and is wrong twice: it moves the gated
comparison's reporting key, which FR-002 forbids, and it newly arms every
gated-path error under `status-evidence` for the Codex flow, which is precisely
the blast radius FR-008 exists to prevent. The plan specifies a three-tuple so
the new key carries only identity errors. `build_report` is the sole consumer, so
this touches one call site.

**2. `state.get("workflow_file") is None` would reintroduce the bug.** FR-003
skips on an absent field, and the edge cases classify an explicit `null` as
malformed, which fails. `.get()` collapses those two into one value, so a nulled
field would become a silent opt-out. Verified: `"workflow_file" not in state`
distinguishes them and `.get(...) is None` does not. The plan requires the
membership test.

**3. A latent fragility in the existing controls.** The current `RuleScopingTests`
fixture writes an absolute `workflow_file` into a temp root with no repository
marker. After this change all three methods newly flow through the helper and
stay green only because no `.git` resolves above a system temp directory, which
is an environmental accident rather than a correctness property. Verified by
walking the parents of a real temp directory: no marker found. The plan requires
re-running them and, if red, fixing the fixture rather than the helper.

**Parser correction applied.** The declared-operations block uses `MODIFIED`, not
`MODIFY`. The parser accepts only `^\s*[-*]\s+(NEW|MODIFIED)\s+([^\s]+)\s*$`, so
`MODIFY` is silently dropped and the estimate degrades to no input. Verified: all
5 entries now parse.

**A third inert governance check, recorded not fixed.** The plan-phase
`estimate-reviewable-loc` returns `projected: 0, production: 0` against 5 declared
files. `is_production_file` matches a path prefix of `src/`, `app/`, `lib/`, or
`scripts/`, or a JS, TS, or SQL extension. This repository's Python guard lives at
`speckit-pro/skills/speckit-autopilot/scripts/…`, which does not *start* with
`scripts/`, and `.py` is absent from the extension list, so **every Python file in
this repository scores as non-production** and the plan-phase budget gate is
structurally blind to the repo's primary language. This is adjacent to ART-015 but
distinct: ART-015 is about never re-invoking the estimator, whereas this is the
estimator mis-classifying its input. It is recorded here and in the pull request's
known gaps rather than opened as a roadmap entry, on the same rule applied to the
deferred documentation pin: nothing shipped cites it, so creating an entry would
be unrequested scope. The slice remains governed by the spec's own slice-estimator
figures, 235 reviewable LOC across 4 production files, and both estimators agree
the slice is within budget.

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
| error-handling | 32 | 6 found, 6 remediated, 0 remaining | FR-002, FR-004a, FR-006, FR-009, plan D1/D2/D5 |
| data-integrity | 24 | 7 found, 7 remediated, 0 remaining | Edge Cases, SC-002, SC-006, US2 AS1, Key Entities, plan D1/D5/D8 |
| security | 27 | 6 found, 6 remediated, 0 remaining | FR-006a, FR-006b, Assumptions, plan D5/D8 |
| **Total** | **83** | **19 found, 19 remediated, 0 remaining** | |

#### Domain 1 Findings, error-handling

Six gaps, all closed with evidence, no new requirement identifiers minted and no
consensus routing needed. Two involve committed tests and are worth recording in
full, because both bound how the implementation may be written.

**The guard will carry two identity messages, not one.** After this change the
untouched gated path still emits the bare sentence while the new block emits the
prefixed one with both paths appended. Read without scoping, FR-009 looked like
an instruction to rewrite the gated message, which would contradict FR-002. It is
not a stylistic point: `tests/speckit-pro/unit/test-autopilot-phase-coverage.py`
asserts that sentence against `report["workflow_checkpoint_errors"]`, which is a
**list**, so the assertion is an exact element match and appending paths to the
gated message would fail it. FR-009 is now scoped to the message reported under
`workflow_authority_errors`, and FR-002's "leave the gated path alone" is what
keeps a committed test green rather than merely being a scoping preference.

**One existing test does resolve a repository root, contradicting the simpler
story.** The plan's earlier reasoning was that existing fixtures stay green
because no repository marker resolves above a system temporary directory. That
holds for `test-autopilot-bookkeeping-guard.py` but not for
`test-autopilot-phase-coverage.py`, which runs `git init` on its temporary root,
so the new comparison genuinely executes there. It stays green for a different
and better reason: that fixture sets `workflow_file` to `workflow.md` and writes
the workflow at exactly that relative path, so the comparison matches. That file
owns the only committed coverage of the FR-002 gated error paths, which is why
identifying it mattered.

**Placement is tighter than "first line".** The helper runs immediately after the
existing `read_text(workflow)` call, not before it. Above that line the spec's own
missing-file edge case would become false, since the input-error exit depends on
the read happening first.

**No branch may raise.** Every operation the comparison performs now has a stated
outcome. Verified against Python 3.11.0: `Path.resolve()` raises `RuntimeError` on
a symlink loop, `read_text` raises `OSError` with `ELOOP` on the same input, and
`resolve()` on a merely nonexistent path does not raise. The plan's argument
rests on `read_text` running first rather than on version-specific `resolve()`
behaviour, which is the durable form of the claim.

**Skips are indistinguishable from passes at the exit code, and that is
accepted.** The property was previously stated only inside a fixture rationale
and the canary rationale. It is now stated where the skip requirements are
defined, naming the compensating evidence, so a reader does not mistake it for an
oversight.

#### Domain 2 Findings, data-integrity

Seven gaps, all closed by edit. Two corrected claims that were simply false, and
one is a process defect affecting the gate this phase reports to.

**A claim this run had asserted was wrong.** The spec's edge case read "Both must
remain valid after this change" of the two tracked state slots. Measured: the
legacy `.specify/autopilot-state.json` exits **2** today with
`autopilot state must contain a plan array`, so it does not validate now and did
not before, for a reason unrelated to this change. The claim is replaced by the
narrower true one, that this change adds no *new* failure to either slot. FR-003's
absent-field skip is unaffected and still correct: the comparison runs first,
skips because the field is absent, and the exit 2 arrives later from the missing
plan array.

**The absent-field skip had no verification evidence anywhere.** It is the branch
that keeps a tracked state file working, and neither control in the FR-012 pair
exercises it, because both set `workflow_file`. The plan now requires a third
method, deliberately outside the FR-012 pair so that pair keeps its
single-variable framing, asserted against a repository-marked fixture root so the
skip can be attributed to the absent field rather than to an unresolvable root.

**The denominator was reproducible only from this workflow file.** The baseline
commit and the command that yields 54 now appear in the plan as well, so the
figure can be re-derived from the spec directory alone. SC-002's present-tense
"the tracked corpus now holds 55" was also retensed into a drift-proof rule, since
another specification's workflow landing before this one merges would have
falsified the sentence.

**Vocabulary drift inside the spec.** FR-010 fixes a closed three-value
vocabulary while an acceptance scenario and the entity definition each still
offered two, which FR-010b actively falsified for the three keys it marks
`advisory-accidental`. Both now defer to FR-010's vocabulary.

**A fourth silently-inert governance check, and this one gates G4.**
`count-markers` matches the literal token `\[Gap\]`. The combined form
`[Gap, Spec §A]` and the style the checklist skill's own examples demonstrate,
`[Coverage, Gap]`, both count as zero. A checklist full of real findings therefore
reads as clean, and the documentation teaches the invisible form. The executor hit
this directly: its first count returned `total: 0` against seven real gaps.
Audited for this feature: every marker written here used the standalone `[Gap]`
form, and the feature directory now contains no `Gap` token of any form, so the
zero reported at G4 is genuine rather than an artifact of the pattern.

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
| **Total Tasks** | 27 (T001-T027) |
| **Phases** | 6: Setup 1, Foundational 5, US1 6, US2 3, US3 7, Polish 5 |
| **Parallel Opportunities** | 2 (T019, T020 — the only genuinely different-file pair) |
| **User Stories Covered** | 3 of 3 (US1 6 tasks, US2 3, US3 7) |

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, the autopilot SKILL runs
the read-only atomicity classifier and records its decision here. This is a
**placeholder** until then; leave the cells blank during scoping.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | The change is one reviewable unit; no split seam was detected. |
| **Releasable** | `true` | Not a destructive migration and not concurrency-sensitive. |
| **Signals** | `change-shape:modify-heavy` | Every declared operation modifies an existing file; nothing is net-new. |
| **Warnings** | none | No release-safety risk attached. |

Because the route is not `split-PR`, layer planning is recorded as
`layer_plan.status = skipped` and the run continues with route context, per the
protocol's non-split branch.

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
| Mode | `advisory`, resolved at Step 0.6b |
| Composite confidence | none computed |
| Verdict | `soft_skip`, treated as proceed |
| Evidence | The helper reports `no confidence emit found` against a 0.90 threshold. No synthesizer emitted a `Confidence: X.XX` line, because all five consensus items resolved in Round 1 on analyst verdicts rather than through a synthesizer scoring pass. Under advisory mode a `soft_skip` proceeds; under strict mode this would have stopped for an operator decision. |

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

### Pre-Change Baseline, Recorded By T001

Captured before any source edit, because the contrast this records is
unmeasurable once the repair lands. Measured 2026-08-12 on the
`art-014-phase-guard-enforcement-repair` worktree, macOS, CPython 3.11.

**Suite is green before the change.**

```text
python3 tests/speckit-pro/run-all.py --layer 4
→ speckit-pro test suite: 5745/5745 passed
→ L4: 5745/5745
→ PASS test-autopilot-bookkeeping-guard (17/17)
```

**The defect, reproduced once under the autopilot's own invocation.** The
fixture is the T002 shape: a temporary root carrying a `.git` **file** marker, a
supplied workflow at the repository-relative `docs/supplied-workflow.md`, the
state written beside it and passed **absolute**, and the state's `workflow_file`
set to the repository-relative `docs/a-different-workflow.md`, which names a
different specification.

```text
python3 speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py \
  --workflow <supplied workflow> --state <state> --rule status-evidence
```

| Observation | Measured before the change |
|---|---|
| Exit code | **0** — the mismatched run reports success |
| `workflow_authority_errors` in the report | **absent from the report entirely** |
| Printed `status` field | `fail`, on unrelated pre-existing coverage debt |

The last row is worth separating from the first two. The report's own `status`
already reads `fail`, yet the exit code is 0, because `--rule status-evidence`
scopes the exit code to three keys and the coverage debt is not one of them.
That is the `--rule` behaviour spec.md's Assumptions records, not a second
defect, and it is why the exit code rather than the printed status is the
measurement of record for SC-001.

**Pre-change counts, re-derived rather than copied.** Both were re-measured
against the report above, not read from an earlier artifact.

| Count | Measured | Spec Assumptions | Agreement |
|---|---|---|---|
| Emitted problem keys (report keys minus the four metadata keys `status`, `workflow_file`, `state_file`, `plan_step_count`) | 20 | 20 | ✅ |
| Keys reachable by a named rule (`RULE_PROBLEM_KEYS`) | 8 | 8 | ✅ |
| — of those, `status-evidence` | 3 | 3 | ✅ |
| — of those, `coverage` | 5 | 5 | ✅ |
| Advisory keys (emitted minus reachable) | 12 | 12 | ✅ |

The 20 emitted keys, in sorted order: `changed_file_manifest_errors`,
`checkpoint_evidence_errors`, `checkpoint_file_errors`,
`checkpoint_source_fingerprint_errors`, `completed_phase_pending_fields`,
`duplicate_state_steps`, `emission_mapping_errors`, `in_progress_errors`,
`marker_plan_status_errors`, `missing_state_post_items`,
`missing_state_prefixes`, `missing_workflow_post_items`,
`missing_workflow_sections`, `missing_workflow_tokens`,
`projection_status_errors`, `stage_mirror_errors`, `state_order_errors`,
`state_status_errors`, `workflow_checkpoint_errors`,
`workflow_status_evidence_errors`.

**No drift to report.** Every re-derived count matches the spec's Assumptions,
so nothing here needed reporting as a disagreement.

### Post-Change Measurements, Recorded By T008 And T012

Measured on the same worktree, macOS, CPython 3.11, against the same T002
fixture the baseline above used. The "before" halves come from that baseline, so
each contrast sits in one place.

**The two halves, observed.** tasks.md predicts a three-stage progression of the
same negative control. Each stage was run and recorded rather than reasoned
about.

| After | Negative-control exit | `workflow_authority_errors` | Suite |
|---|---|---|---|
| T002 and T003 written, before any guard edit | 0 | key absent entirely | 17/19 |
| T009 and T010 added, still before T007 | 0 | key absent entirely | 17/21 |
| T007 complete (key merged) | **0** | **non-empty**, the identity message | 20/21 |
| T008 complete (key registered) | **1** | non-empty | **21/21** |

The third row is the one that matters for review. Detection and gating are
separate halves, and the mismatch was fully reported for a whole stage while the
run still exited 0. A reviewer who reverts T008 alone returns to that row.

The FR-006b control (T003) turns green one stage earlier, at T007 rather than
T008, because it asserts key presence and non-emptiness and deliberately asserts
no exit code. tasks.md places it at the T008 checkpoint; the observed flip is at
T007. That is a precision correction to the task note, not a behaviour
difference: FR-006b is about whether the comparison evaluates, which is settled
once the key is merged.

**Post-change counts, re-derived from a real report rather than copied.**

| Count | Before | After | SC-006 pins | Agreement |
|---|---|---|---|---|
| Emitted problem keys | 20 | 21 | 20 → 21 | ✅ |
| Keys reachable by a named rule | 8 | 9 | 8 → 9 | ✅ |
| — of those, `status-evidence` | 3 | 4 | 3 → 4 | ✅ |
| — of those, `coverage` | 5 | 5 | unchanged | ✅ |
| Advisory keys | 12 | 12 | unchanged | ✅ |

`workflow_authority_errors` is the only key added, and it appears in exactly one
rule tuple, `status-evidence`. `workflow_checkpoint_errors` appears in no tuple,
which FR-008 requires. The advisory set is unchanged member for member, so no
existing key changed reachability.

**T011: the two existing files that newly flow through the comparison.** Both
were re-run rather than reasoned about, because both stay green for reasons that
are fixture details rather than intents.

| File | Before | After | Why it stays green |
|---|---|---|---|
| `tests/speckit-pro/unit/test-autopilot-phase-coverage.py` | 39/39 | 39/39 | Its `git init` root means the comparison genuinely evaluates there. The fixture sets `workflow_file` to `workflow.md` and writes the supplied workflow at that same repository-relative path, so the comparison matches. |
| `RuleScopingTests` in `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py` | 3/3 | 3/3 | An absolute `workflow_file` and no repository marker, so the unresolvable-root skip still wins before the malformed check can fire. |

The phase-coverage "before" figure was taken after the comparison went
unconditional and before the key was merged, which is the window where a break
would have shown. Neither file needed a fixture repair, so neither was modified
and neither enters the Declared File Operations.

**T012: the Scenario 3 branch walk.** One input varied at a time against the
T002 fixture. Temporary paths are elided as `<tmp>`. The exit column separates
the two non-zero codes, because a control asserting only "non-zero" would be
satisfied by an unrelated input failure: 1 is a rule violation and 2 is an input
error, which prints `status: input_error` and no report at all.

| Vary | Exit | Observed verdict |
|---|---|---|
| baseline, state names the supplied workflow | 0 | empty list |
| remove the `workflow_file` **key** | 0 | empty list |
| `workflow_file` = JSON `null` | 1 | **malformed**, not identity |
| `workflow_file` = `""` | 1 | malformed |
| `workflow_file` = `"  "` | 1 | **malformed**, not identity |
| `workflow_file` = number `42` | 1 | malformed |
| `workflow_file` = a list | 1 | malformed |
| delete the `.git` marker | 0 | empty list |
| state names a different workflow | 1 | identity mismatch |
| supply a workflow outside the temporary root | 1 | `workflow file is outside the authorized repository` |
| control: supplied workflow does not exist | **2** | `input_error`, `could not read file: <tmp>/docs/no-such-workflow.md` |

Every malformed row printed the same sentence:
`autopilot state workflow_file is not a normalized repository-relative path`. The
identity row printed
`supplied workflow does not match autopilot state workflow_file authority:
supplied docs/supplied-workflow.md, state names docs/a-different-workflow.md`.

**The two rows that could have passed for the wrong reason, checked rather than
assumed.**

- The whitespace row. `_is_normalized_repo_path("  ")` and
  `_is_normalized_repo_path(" ")` were both called directly and both return
  `True`, because a run of spaces is a valid POSIX path part. Without branch 3's
  explicit check the value would clear branch 4 and land in branch 6, reported as
  an identity mismatch against a blank path: the wrong error class and an
  unreadable message. The observed malformed verdict is therefore attributable to
  branch 3 existing and preceding branch 4, not to branch 4 catching it.
- The `null` row. Branch 1 tests key membership. Had it tested
  `state.get("workflow_file") is None`, a nulled field would have taken the skip
  and exited 0 with an empty list, which is the silent opt-out FR-005 exists to
  prevent. The observed exit 1 is what distinguishes the two spellings.

The last two rows also confirm the ordering claim from the opposite direction:
an unreadable supplied workflow raises before the comparison is reached, so it
exits 2 rather than producing any authority verdict. That is `read_text` staying
the first statement of `_authorized_workflow_text`.

### Documentation Truth Read-Through, Recorded By T022

The verification of record for SC-007. The consensus panel resolved that no
automated assertion is added (Consensus item 3, NO-ASSERT), so this manual
read-through is the whole of the evidence.

**Method.** The statement set was enumerated by search rather than from memory of
the files edited, so the claim "zero shipped statements promise unperformed
enforcement" is checkable rather than asserted:

```text
grep -rn "validate-autopilot-phase-coverage\|workflow_file authority\|supplied workflow does not match\|workflow_authority_errors\|coverage guard" speckit-pro/ --include="*.md"
```

Thirty hits across eight shipped files, on both platforms. Each was read and
given a verdict.

| # | Location | Statement | Verdict |
|---|---|---|---|
| 1 | CC `SKILL.md` §Workflow File Update Protocol | The authority bullet: identity is authoritative when the state names a `workflow_file` and a root resolves; mismatch opens with the exact sentence and appends both paths; both skip conditions named; malformed state value and out-of-boundary supplied workflow both fail | **True**, and rewritten this phase (T016). Quotes the message as a **prefix**, not an exact full string |
| 2 | CC `SKILL.md` §Workflow File Update Protocol | "Repairing the workflow file to match the state is the correct move here" | **True**, and now scoped to the PR Marker Plan Evidence bullet only (T016). It was false of the identity bullet, whose repair rewrites the state instead |
| 3 | CC `SKILL.md` Step 1.1 | Expected-commit append contract, both OIDs fetched live, blocking on missing or stale authority | **True as a contract, labelled not-yet-wired** (T017). States plainly that the Claude flow does not fetch those values yet and cites **ART-016** |
| 4 | CC `SKILL.md` Step 0.6d | "The guard's workflow-identity check is **inert** under every invocation the phase loop issues: run against a state file naming a different specification it exits **0** and reports `pass`" — and, below it, "the guard is **equally inert** for all of them" | **Was false → corrected in this run.** This is the exact behavior ART-014 repairs; after T008 that invocation exits 1 with a non-empty `workflow_authority_errors`. Found by this read-through, not by Clarify, whose FR-013a inventory was scoped to the authority block. See the correction note below |
| 5 | CC `SKILL.md` §References | Workflow File Protocol descriptor | **True**, amended to name the `workflow_file` state authority (T018) |
| 6 | CC `references/workflow-file-protocol.md` | New `## workflow_file State Authority` section: five ordered branches with a reason each, resolution asymmetry, byte-exact rule | **True** (T019). Branch order and messages verified against the helper at `validate-autopilot-phase-coverage.py` branches 1-7 |
| 7 | CDX `references/workflow-file-protocol-codex.md` | Condensed mirror of the same section | **True** (T020). Five branches and the byte-exact rule survive the compression |
| 8 | CDX `SKILL.md` §References | Workflow File Update Protocol for Codex descriptor | **True**, amended to name the `workflow_file` state authority (T021) |
| 9 | CDX `SKILL.md` Step 1.1, `references/phase-execution-codex.md`, `references/task-list-canonical-codex.md` | The expected-commit append contract, three sites | **True and wired on Codex.** This is the platform that supplies live commit values, so no caveat is owed here |
| 10 | Both platforms, five sites | The invocation contract: `--rule status-evidence` scopes the exit code to the bookkeeping rule, the full report still prints, exit 0 required to advance | **True.** `RULE_PROBLEM_KEYS["status-evidence"]` now carries four keys and the report still prints every key |
| 11 | Both platforms, three sites | A status row contradicting a gate verdict recorded elsewhere fails the guard (`workflow_status_evidence_errors`); a two-sided `Stage` disagreement fails as `stage_mirror_errors` | **True.** Both keys are registered in `status-evidence` |
| 12 | Both platforms, two sites | The guard matches post-implementation checkpoints by exact name equality, so a `skipped:`-prefixed name reads as missing | **True**, and untouched by this change |

**Count of shipped statements promising unperformed enforcement: zero.** Row 4
was the one false statement, and it is corrected rather than carried.

**Roadmap identifiers verified before citation.** ART-016 (`Claude-Side Live PR
Commit Authority`, ⏳ Ready, no dependencies) and ART-017 (`Arm The
Accidentally-Advisory State Bookkeeping Checks`, ⏳ Ready, blocked by ART-014)
both exist in `docs/ai/specs/html-artifacts-technical-roadmap.md`. A shipped
document naming an identifier that does not exist would repeat the defect class
this specification repairs, so this was checked rather than assumed.

**The Step 0.6d correction, recorded in full.** The replaced text read:

```text
- **This runs before the Step 1 coverage guard, not after.** The guard's
  workflow-identity check is inert under every invocation the phase loop
  issues: run against a state file naming a different specification it exits
  **0** and reports `pass`. Ordering re-initialisation after the guard
  therefore leaves the slot unprotected, not merely late — nothing downstream
  would catch the stale identity.
- The trigger is **unscoped by stage**. Any stage can be the one that finds a
  foreign slot, and the guard is equally inert for all of them.
```

The ordering directive it justifies is unchanged and still correct. Only its
reason inverts. Before this change, reclaim-before-guard mattered because the
guard would not catch a stale identity at all. Now it matters more: the guard
halts a run whose state names a different specification, so ordering
re-initialisation after the guard would stop every legitimate reclaim at Step
1.1 before the slot is rewritten. Reclaiming first rewrites `workflow_file` from
the target, and the comparison then finds two references that agree — which is
also why this repair does not break the reclaim path.

Confirmed Claude-only. A case-insensitive search for `inert` and `reclaim`
across `codex-skills/` returns one unrelated hit about confidence-mode flag
inertness. The Codex flow states the correct ordering already, running the guard
after writing or repairing `autopilot-state.json`, and never claimed inertness.

**One observation, deliberately not edited.** The Claude Step 2 loop instructs
that on a nonzero guard exit the operator should "repair the plan and the
workflow status table". That remediation hint is now incomplete for one failure
mode, because an identity mismatch is repaired by re-pointing the run or
reclaiming the slot rather than by editing the plan or the status table. It is
not a false claim about what the guard does, so it does not fail the User Story 3
test, and it is recorded here rather than edited. Widening the read-through into
adjacent remediation prose is the scope creep this phase's own non-goals warn
against.

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Setup | T001 | ✅ 1/1 | Pre-change baseline recorded before any source edit |
| 2 - Foundational | T002-T006 | ✅ 5/5 | Controls RED first for the right reason; helper, root resolution, and the three-tuple widening |
| 3 - US1 Registration | T007-T012 | ✅ 6/6 | Both by-design reds turned green; the canary now exits 1 |
| 4 - US2 Audit Map | T013-T015 | ✅ 3/3 | 21 keys classified; the completeness test proven to bite |
| 5 - US3 Documentation | T016-T022 | ✅ 7/7 | Staged prose applied on both platforms; the read-through found and corrected a fourth false statement outside the authority block |
| 6 - Polish | T023-T027 | ✅ 4/4 + T026 to post-impl | 28 generated paths refreshed; after-half 54/54; gate 7385/7385 |

#### The Repair, Proven

The canary recorded before any code changed has flipped. Same invocation, same
inputs, opposite verdict:

| Run | Before | After |
|---|---|---|
| State names a different workflow, `--rule status-evidence` | exit **0** | exit **1** |
| State names the supplied workflow | exit 0 | exit **0** |
| `workflow_checkpoint_errors` (gated path, FR-002) | `[]` | `[]`, still unarmed |
| Rule-reachable keys | 8 | **9** (`status-evidence` 4, `coverage` 5) |

The message is the one the shipped documentation has quoted since before ART-006
found the defect, now carrying both compared paths:

```text
supplied workflow does not match autopilot state workflow_file authority:
supplied docs/ai/specs/.process/ART-006-workflow.md,
state names docs/ai/specs/.process/CAR-001-workflow.md
```

#### Classification Record, Verified

21 entries against 21 emitted keys, with **zero unclassified and zero classified
keys that are never emitted**. Split: 9 `gated`, 9 `advisory-deliberate`, 3
`advisory-accidental`. The three accidental entries are `in_progress_errors`,
`duplicate_state_steps`, and `state_order_errors`, each naming ART-017 as the
entry that will arm them. Their reasons state why the shipped corpus-predates
justification cannot apply: all three are invariants of the state file the
current run just wrote, so no legacy artifact can violate them.

**T015, the bite proof.** Run as a probe against the module rather than by
editing shipped source, so the guard carries no residue. With the real report the
completeness check finds nothing missing and passes. With one throwaway key
injected it fails and names the offender:

```text
the guard emits problem keys with no PROBLEM_KEY_INTENT verdict:
a_future_unclassified_key
```

That discharges SC-005: a future specification cannot add a problem key without
recording a verdict for it.

**Executor note.** The US2 executor stopped mid-verification while diagnosing a
Layer 4 baseline, after completing T013 and T014. The orchestrator verified its
output independently and performed T015 directly. Nothing was assumed from the
incomplete report; the map, the counts, and the bite were each re-derived from a
real report in the main session.

---

## Post-Implementation Checklist

The canonical closeout. Every row must reach Complete or an explicit
`Skipped` before the run may report completion.

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ✅ Complete | 4 pass, 1 warn (unrelated parked spec) |
| Post: Verify Implementation | ✅ Complete | Pass on substance; canary reproduced across a7369749^ and a7369749 |
| Post: Verify Tasks Phantom Check | ✅ Complete | Reported honestly that it cannot judge unticked tasks; list has since been ticked 27 of 27 |
| Post: Code Review | ✅ Complete | approve-with-comments, zero blocking; both comments acted on |
| Post: Integration Suite | ✅ Complete | 7393/7393, zero failures, +15 over the 7378 baseline |
| Post: Reviewability Diff Gate | ✅ Complete | Over by +350 LOC, warn band, root cause diagnosed and recorded in the PR |
| Post: Self-Review | ✅ Complete | 4 questions; 3 findings became code changes rather than known gaps |
| Post: UAT Runbook Generation | ✅ Complete | Skipped fail-open, helper deferred; quickstart's 7 scenarios are the acceptance basis |
| Post: PR Body Generation | ✅ Complete | One release-note fence, zero absolute paths |
| Post: PR Creation | ✅ Complete | PR #433 open against main |
| Post: Review Remediation | 🔄 In Progress | Loop job scheduled every 5 minutes against PR #433. First check: no comments, early gates pass |
| Post: Retrospective | ✅ Complete | 100% adherence, 0 critical. Written to `.process/ART-014-retrospective.md`; opened ART-018 |

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

**Banking the canary before writing any code.** The single most valuable artifact
of the run was a measurement taken before the first edit: a state naming a
different specification, exiting 0. Everything afterwards had something to be
measured against, and the claim "the defect is fixed" reduced to one number
changing. Fifty-four corpus passes proved nothing on their own, because a skipped
comparison and a satisfied one both exit 0.

**Verifying agent reports rather than relaying them.** Every substantive claim in
this run was re-derived in the main session before being acted on. That caught a
symlink-loop crash report that was wrong, a "the guard was reverted" conclusion of
my own drawn from a torn read, and a corpus-harness precondition I had stated too
loosely.

**Consensus that argued rather than voted.** Five items routed to three lenses.
Two verdicts went against the recommendation the executor offered, one went
against the orchestrator's own framing, and in every case the deciding evidence
was something no single lens held.

### Challenges Encountered

**The estimator was faithful and still wrong by 2x.** It was re-invoked at every
amendment, which is precisely what ART-015 asks for, and still projected 337
against a real 687. The miss is ART-015's own deferred second limitation: a
requirement whose deliverable is bulk inside one existing file.

**Three collaboration failures, all one shape.** A probe artifact left in shipped
source; a stopped agent's byte-exact restore silently undoing an orchestrator fix;
a torn read during a flush that looked like a reversion. Each was a write whose
provenance the orchestrator could not see.

**Stalling.** Twice I ended a turn with a summary instead of a dispatch. The rule
is that a turn ends with a live agent or a finished run.

### Patterns to Reuse

**A check that reports zero must be able to prove it can detect one.** This is the
run's durable lesson and it generalizes past this spec. It is why the corpus
harness carries a canary, why the completeness test was proven to bite, and why
ART-018 exists.

**Record the verdict, not just the value.** The classification map's worth is that
every advisory key now states why advisory is correct for it. Three keys could not
answer that question, which is how they were found.

**Treat an agent stop as a write-invalidation event, not a pause.** Re-derive from
the diff before building on anything that agent owned.

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

---

## Post-Implementation: Reviewability Diff Gate And Self-Review

Measured at `a7369749` against base `3af4764e`. The runner helper
`final-reviewability-backstop` is registered `deferred` in
`speckit_pro_runner/helpers/registry.py:373`, so it was not invoked as an active
helper. The real diff was measured directly with `git diff --numstat` instead.

### Diff Measurement — the six authored files

| File | + | - |
|---|---|---|
| `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | 323 | 16 |
| `speckit-pro/skills/speckit-autopilot/SKILL.md` | 32 | 13 |
| `speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md` | 39 | 0 |
| `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` | 2 | 1 |
| `speckit-pro/codex-skills/speckit-autopilot/references/workflow-file-protocol-codex.md` | 41 | 0 |
| `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py` | 250 | 1 |
| **Total (six authored)** | **687** | **31** |
| Five production only (excludes the test file) | 437 | 30 |

Excluded from the measurement: 28 generated paths (`dist/`,
`tests/speckit-pro/unit/fixtures/plugin-bash-confinement/`,
`docs/ai/specs/.process/XPLAT-009-*.json`) and 2 process records
(`ART-014-workflow.md`, `autopilot-state.json`). The full commit touches 50
paths; only 687 of its 7564 insertions are authored.

### Budget Verdict — OVER the declaration, warn band, not blocking

Declared: 337 projected reviewable LOC, 5 production files, 10 total, one slice,
within budget, warn 400, block 800.

| Framing | Real | vs 337 | vs warn 400 | vs block 800 |
|---|---|---|---|---|
| Six authored, added | 687 | **+350 (2.04x)** | over | under |
| Six authored, added+removed | 718 | +381 (2.13x) | over | under |
| Five production, added | 437 | +100 (1.30x) | over | under |
| Five production, added+removed | 467 | +130 (1.39x) | over | under |

**The projection was wrong, and by roughly double.** The verdict is
convention-independent: every framing above lands over the declared 337 and over
warn 400, and every framing stays under block 800. The declared figure came from
the slice estimator's modify-weighted formula, `(3x25 + 6x40 + 24x15) / 2 =
337.5`, which prices a MODIFIED file at about 20 effective LOC. Two files broke
that price: `PROBLEM_KEY_INTENT` is a 225-line record classifying 21 keys
(`validate-autopilot-phase-coverage.py:257-481`), and the new test classes add
250 lines. That decomposition explains the overrun; it does not excuse it. The
estimator's per-file weight does not model a requirement (FR-010) whose
deliverable *is* prose volume inside one file.

A second declaration miss, recorded for the same reason: the plan declared 10
total files by counting `dist/claude`, `dist/codex`, and two fixture proofs as 4
group entries. As files, those groups are 28 paths, and 14 further spec and
roadmap artifacts also changed.

### Self-Review — the mandatory four questions

**1. Does the change do what the specification says, and only that?** Yes.
Nothing unrequested shipped. Every hunk traces to a requirement: the guard's new
key and helper to FR-001/FR-007
(`validate-autopilot-phase-coverage.py:1529-1583`, `:4360`); the `.resolve()` in
`_repository_root` to FR-006b (`:900-908`); the 225-line classification record to
FR-010/FR-010a/FR-010b (`:257-481`); the Step 0.6c reclaim-ordering rewrite to
FR-013, because the old text asserting the check "is inert under every invocation
the phase loop issues" became false the moment it was armed
(`speckit-pro/skills/speckit-autopilot/SKILL.md:376-385`); the expected-commit
caveat to FR-013 (`SKILL.md:494-504`); the references-index line to FR-013c
(`SKILL.md:828`, `codex-skills/.../SKILL.md:1053-1055`). The honest residue is
imprecision in spec text, not shipped scope: FR-006b claims resolution "is shared
with two other call sites" (`spec.md:230`), and `git show
3af4764e:...validate-autopilot-phase-coverage.py` shows three (lines 1313, 1552,
2005).

**2. What is most likely to be wrong?** The single riskiest line is
`resolved = path.resolve()` at `validate-autopilot-phase-coverage.py:905`.
`_repository_root` is a shared helper with three pre-existing callers besides the
new one (`:1607` the frozen PR-head comparison, `:1854`
`validate_changed_file_manifest`, `:2307` `validate_projection_integrity`). All
three now resolve a root for inputs that previously resolved none, so they
evaluate where they used to skip. Under the scoped `--rule status-evidence`
invocation this cannot move the exit code, because none of their keys is in that
tuple. Under an invocation with no `--rule`, `passed = all(not values for values
in problems.values())` at `:4367` gates *every* key, so a relatively-spelled
state path can newly flip a previously-passing run to exit 1 on paths FR-002
meant to freeze. FR-006b asserts the change "is safe for every existing caller"
(`spec.md:227`); that assertion ships untested. Second-order, and a footnote
rather than the headline: `_workflow_authority_errors`'s docstring states "No
branch raises" (`:1533`), but `Path.resolve()` raises `OSError` on a symlink
loop, and `build_report` has no handler, so that input would print a traceback
instead of the JSON the autopilot parses.

**3. What did we not test?** Two branches of the new five-branch contract have
zero unit coverage. Branch 3, the malformed-value fail required by FR-005
(`:1552-1560`), and branch 4, the outside-the-repository fail required by FR-004c
(`:1568-1570`). No test asserts either message string: grep for `outside the
authorized` and `not a normalized` across
`tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py` returns nothing. The
+7 test delta is exactly 4 `WorkflowAuthorityTests` plus 3
`ProblemKeyClassificationTests`, and the corpus canary exercises branch 5 only,
so nothing else reaches them. Both branches are reachable and both return a
distinct operator-facing string. The second gap is FR-006b's safety claim for the
three pre-existing `_repository_root` callers, which no test exercises.

**4. What would a reviewer most want to know that the diff does not show?**
Four things. First, the diff reads as 7564 insertions but only 687 lines are
authored; the generated copies under `dist/` and the confinement fixtures
quadruple the apparent size and are refreshed by
`scripts/refresh-release-artifacts.py`. Second, the 54-of-54 corpus regression
and the flipped canary are a one-time recorded run, not a committed test, so
nothing in CI re-proves them. Third, `PROBLEM_KEY_INTENT` is never read at
runtime: the only reference in the guard is its definition at `:274`, and the
test suite is its sole consumer, so 225 shipped lines are inert data whose value
is entirely as a review record. Fourth, under a `pr-marker-plan.v2` invocation
carrying `--expected-head-commit`, a genuine mismatch now reports **twice** under
two keys with two different message formats: the frozen text without paths at
`:1621-1623` under `workflow_checkpoint_errors`, and the new text with both paths
at `:1573-1576` under `workflow_authority_errors`. That duplication follows from
FR-002's freeze and is intentional, but it is invisible from the hunks alone.

### Blockers

None. The overrun is warn-band and never approaches block 800. The self-review is
reporting-only by the phase contract. The two untested branches and the untested
FR-006b safety claim belong in the pull request's known-gaps section, which T026
already reserves, rather than in a stop condition.
