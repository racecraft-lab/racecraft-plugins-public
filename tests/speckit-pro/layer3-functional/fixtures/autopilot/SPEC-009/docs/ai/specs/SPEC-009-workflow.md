<!-- fixture-kind: deterministic-synthetic-testdata; setup input only, not executed workflow evidence. -->

# SpecKit Workflow: SPEC-009 — Search & Database

**Template Version**: 1.0.0
**Purpose**: Deterministic setup input for provider-free Autopilot boundary tests.

This is a populated workflow shape, not a run record. The materializer copies it
into a disposable project and the actor records observed results in a separate
run trace. No phase, gate, provider, or foreground result below is claimed.

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | `/speckit-specify` | ⏳ Pending | setup input; produce `spec.md` |
| Clarify | `/speckit-clarify` | ⏳ Pending | two bounded sessions; parent answers questions |
| Plan | `/speckit-plan` | ⏳ Pending | produce `plan.md` from approved requirements |
| Checklist | `/speckit-checklist` | ⏳ Pending | requirements and data-integrity domains |
| Tasks | `/speckit-tasks` | ⏳ Pending | dependency-ordered task list |
| Analyze | `/speckit-analyze` | ⏳ Pending | cross-artifact consistency and confidence emit |
| Confidence Gate | G6.5 | ⏳ Pending | pre-Implement composite confidence |
| Implement | `/speckit-implement` | ⏳ Pending | no implementation is authorized by setup |
| Post | Post-Implementation | ⏳ Pending | canonical 12-item closeout |

### Basic Information

| Field | Value |
|---|---|
| Spec ID | SPEC-009 |
| Name | Search & Database |
| Branch | `009-search-database` |
| Stage | full |
| Registered worktree | `.worktrees/009-search-database/` |
| Feature directory | `specs/009-search-database/` |
| Status | setup_only; not_started |

### Phase Gates

| Gate | Checkpoint |
|---|---|
| G1 | After Specify |
| G2 | After Clarify |
| G3 | After Plan |
| G4 | After Checklist |
| G5 | After Tasks |
| G6 | After Analyze |
| G6.5 | Before Implement |
| G7 | After each implementation phase |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

## Prerequisites

The actor must run the structured `check-prerequisites` helper from the actual
materialized worktree and record its response. It must not infer CLI,
constitution, command, workflow, or branch results from this fixture. No
constitution check is recorded here because the fixture does not execute it.

## Specification Context

### Basic Information

| Field | Value |
|---|---|
| Spec ID | SPEC-009 |
| Name | Search & Database |
| Branch | `009-search-database` |
| Dependencies | none |
| Enables | none |
| Priority | P1 |

### Success Criteria Summary

- [ ] A user can search project records with a deterministic query contract.
- [ ] Results have documented ordering and freshness behavior.
- [ ] Invalid input and storage failures have explicit user-visible handling.

## Phase 1: Specify

**Prompt:**

```text
Run /speckit-specify for SPEC-009 Search & Database. Define the user-visible
search behavior, required fields, deterministic ordering, freshness expectation,
and failure handling. Write only the feature spec under the bound WORKFLOW_ROOT.
Do not invoke grill-me; unresolved questions return to the parent.
```

**Expected setup input:** `phase-artifacts/spec.md` is copied as pre-state only.
The executor must report its actual output path and gate result; this fixture
does not mark G1 complete.

## Phase 2: Clarify

### Clarify Prompts

**Session 1 — Query behavior:**

```text
Run /speckit-clarify for SPEC-009, focusing on query fields, empty results,
ordering, pagination, and invalid input. Return at most five questions to the
parent. Never invoke grill-me inside Autopilot.
```

**Session 2 — Storage and freshness:**

```text
Run /speckit-clarify for SPEC-009, focusing on storage failure behavior,
freshness guarantees, retries, and observable errors. Return at most five
questions to the parent. Never invoke grill-me inside Autopilot.
```

Questions are parent-owned. If a question remains unresolved, route it through
the documented category consensus flow and stop/surface it when consensus cannot
resolve it. No Clarify result is recorded by this setup fixture.

## Phase 3: Plan

**Prompt:**

```text
Run /speckit-plan for SPEC-009 using the approved spec and the repository's
existing patterns. Produce a bounded implementation plan covering query
validation, deterministic ordering, storage access, error handling, tests, and
observability. Keep all writes under WORKFLOW_ROOT and report G3 only from its actual gate result.
```

**Expected setup input:** `phase-artifacts/plan.md` is a setup-only note, not a
completed plan.

## Phase 4: Domain Checklists

### Requirements Checklist

```text
Run /speckit-checklist requirements for SPEC-009. Cross-check every success
criterion and functional requirement against spec.md and plan.md. Mark genuine
gaps with [Gap], route tagged ambiguity through consensus, and report the
observed checklist result. Do not invoke grill-me.
```

### Data-Integrity Checklist

```text
Run /speckit-checklist data-integrity for SPEC-009. Check deterministic result
ordering, freshness, storage failure handling, and rollback-safe behavior against
spec.md and plan.md. Report gaps and evidence; report G4 only from its actual gate result and do not
invoke grill-me.
```

**Expected setup input:** `phase-artifacts/checklist.md` is not a verdict.

## Phase 5: Tasks

**Prompt:**

```text
Run /speckit-tasks for SPEC-009. Derive small dependency-ordered tasks from
spec.md, plan.md, and the checklist outputs. Include tests and mark only truly
parallel-safe tasks with [P]. Keep task paths repository-relative and report the
actual task count. Report G5 only from its actual gate result; do not invoke grill-me.
```

**Expected setup input:** `phase-artifacts/tasks.md` contains no completed tasks.

## Phase 6: Analyze

**Prompt:**

```text
Run /speckit-analyze for SPEC-009. Cross-check requirements, plan, checklists,
and tasks for contradictions, missing coverage, and constitution alignment.
Emit unresolved findings with category tags and a confidence breakdown for the
pre-Implement gate. Do not edit implementation code and do not invoke grill-me.
```

**Expected setup input:** `phase-artifacts/analysis.md` contains no analysis
verdict. The Analyze consensus task is mandatory when findings are unresolved.

## Phase 6.5: Confidence Gate

This gate is resolved from the actual Analyze emit and configured mode. The actor
must record mode, composite score, threshold, verdict, and any remediation in
the run evidence. This fixture intentionally leaves the workflow row Pending.

| Field | Value |
|---|---|
| Mode | unobserved |
| Composite confidence | unobserved |
| Verdict | unobserved |
| Evidence | must be recorded from the actual Analyze response |

## Phase 7: Implement

**Prompt:**

```text
Run /speckit-implement for SPEC-009 only after the real G6.5 decision permits
it. Follow TDD red-green-refactor-verify, execute tasks in dependency order, and
record each task's actual evidence and commit. A failed gate or missing user
input stops the run; it is never escalated to grill-me.
```

No implementation task, commit, test, or G7 result is present in this setup.

## Post-Implementation Checklist

Every item must be observed Complete or explicitly Skipped before a real run may
report completion. The fixture records all items as pending.

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ⏳ Pending | unobserved |
| Post: Verify Implementation | ⏳ Pending | unobserved |
| Post: Verify Tasks Phantom Check | ⏳ Pending | unobserved |
| Post: Code Review | ⏳ Pending | unobserved |
| Post: Integration Suite | ⏳ Pending | unobserved |
| Post: Reviewability Diff Gate | ⏳ Pending | unobserved |
| Post: Self-Review | ⏳ Pending | unobserved |
| Post: UAT Runbook Generation | ⏳ Pending | unobserved |
| Post: PR Body Generation | ⏳ Pending | unobserved |
| Post: PR Creation | ⏳ Pending | unobserved |
| Post: Review Remediation | ⏳ Pending | unobserved |
| Post: Retrospective | ⏳ Pending | unobserved |

## Evidence Boundary

No phase, consensus round, gate, provider call, Git checkpoint, or foreground
interaction has run. `git-history/checkpoints.json` is a schema for recording
actual disposable-Git observations; its null commit IDs are intentional. This
fixture must never be presented as a passing workflow or as live status.
