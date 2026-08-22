# SpecKit Workflow: ART-017 — Arm The Accidentally-Advisory State Bookkeeping Checks

**Template Version**: 1.0.0
**Created**: 2026-08-22
**Purpose**: Executable planning workflow for ART-017, populated from the technical roadmap and the setup-mode Grill Me interview.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`$speckit-pro:speckit-scaffold-spec ART-017`. The full Q&A log, Goals,
Non-goals, and settled design decisions live at:

```text
docs/ai/specs/.process/ART-017-design-concept.md
```

Re-read it before every phase. All five surfaced blind-spot findings were
resolved across eight questions; the design concept is the source of truth for
rule routing, negative-control isolation, corpus evidence, documentation scope,
failure shape, and ART-008 integration ordering.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ⏳ Pending | |
| Clarify | `/speckit-clarify` | ⏳ Pending | Optional but recommended |
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

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | Treat authored plugin/test changes as release inputs; regenerate payloads, installed-cache proofs, and docs references instead of hand-editing generated copies | `python3 scripts/refresh-release-artifacts.py`; `pnpm --dir docs-site reference:generate`; artifact-consistency checks |
| II. Cross-Platform Runtime & Script Safety | Keep the guard on Python 3.11+ standard library and preserve structured JSON output; add no active Bash or `jq` path | `python3 tests/speckit-pro/run-all.py --layer 4` |
| IV. Test Coverage Before Merge | Add one isolated negative control per armed key plus the tracked workflow/state-pair regression in the existing Layer 4 test | Targeted unittest, then `python3 tests/speckit-pro/run-all.py` |
| VI. KISS, Simplicity & YAGNI | Add exactly three explicit rule members and three atomic verdict flips; do not redesign rule scoping or derive a new abstraction | Code review against `ART-017-design-concept.md` Non-goals |

**Constitution Check:** ⏳ Pending — the planning-stage autopilot records the G0 baseline and verifies these rows before G1.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-017 |
| **Name** | Arm The Accidentally-Advisory State Bookkeeping Checks |
| **Branch** | `art-017-state-bookkeeping-checks` |
| **Dependencies** | ART-014, satisfied by PR #433 and archived 2026-08-13 |
| **Enables** | Honest state bookkeeping under the invocation the autopilot already issues |
| **Priority** | P3 |
| **Stage** | plan |
| **Roadmap tools** | None declared |

### Reviewability Budget And Split Decision

The setup-mode `reviewability-gate` returned `status: warn`, `pass: true`, and
no blockers. Its raw roadmap-wide scan reported `40` reviewable LOC, `3`
production files, `5` total files, and three primary surfaces
(`docs/process`, `harness/adapter`, `seed/config`); only the surface count crossed
the warn threshold. The ART-017-specific Grill Me estimator used one behavior
story, three authored files, seven scoped requirements, and
`new_vs_modify=modify`, returning `estimated_loc: 125`,
`suggested_slices: 1`, `status: ok`.

**Split decision: one vertical slice, no split.** Rule membership, intent
classification, isolated exit-code proofs, the tracked-pair regression, and the
narrow authored explanation form one independently testable capability. Splitting
membership from verdicts would violate the existing exact-consistency invariant.
Re-estimate from the real plan at G3 and whenever the declared requirement or
authored-file set changes. Before ready/merge, rebase after ART-008 as needed,
regenerate shared artifacts, and use the actual diff gate as final authority.

### Success Criteria Summary

- [ ] `in_progress_errors`, `duplicate_state_steps`, and `state_order_errors`
      are explicit members of the existing `status-evidence` rule, and no other
      advisory key is newly armed.
- [ ] Each key's `PROBLEM_KEY_INTENT` verdict changes atomically from
      `advisory-accidental` to `gated`, with a reason that states the current-run
      state invariant it protects.
- [ ] A shared clean builder plus three isolated negative controls prove each
      key independently makes the exact `--rule status-evidence` invocation exit
      `1`; the other two new problem lists remain empty in each case.
- [ ] The clean control exits `0`, and pre-existing structural coverage debt is
      still reported without becoming blocking under `status-evidence`.
- [ ] Every tracked workflow with an adjacent `autopilot-state.json` exits `0`
      under the exact scoped invocation.
- [ ] The emitted JSON report shape and existing problem-key values remain
      unchanged; only scoped exit-code authority and the intent verdicts move.
- [ ] The authored autopilot paragraph distinguishes legacy coverage debt from
      the three blocking state invariants without duplicating key-level prose
      across other references.
- [ ] Generated Codex/payload/proof/reference surfaces are regenerated through
      repository tooling; targeted tests, docs reference checks, and the full
      Python suite pass after the final main rebase.

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/art-017-state-bookkeeping-checks/spec.md`

### Specify Prompt

```text
/speckit-specify Define ART-017 so three current-run state invariants independently fail the exact status-evidence invocation that already reports them, while legacy coverage debt remains advisory.
```

#### Detailed Prompt (for complex specs)

```text
/speckit-specify

## Feature: Arm The Accidentally-Advisory State Bookkeeping Checks

### Problem Statement

`validate_state` already emits `in_progress_errors`,
`duplicate_state_steps`, and `state_order_errors`, but none is selected by the
`status-evidence` rule that both autopilot variants invoke after phase
transitions. The report can therefore name a malformed state file while the
autopilot still receives exit `0`. ART-014 reproduced this defect and classified
all three keys as `advisory-accidental`; ART-017 makes that classification and
runtime behavior truthful.

### Users

SpecKit Pro maintainers running or resuming the autopilot on Claude Code or
Codex. Both distributions consume the same authored guard behavior.

### User Stories

- US1 — As an autopilot operator, I need a state with multiple in-progress
  steps, duplicate steps, or reordered checkpoints to halt the current run so
  it cannot advance from contradictory bookkeeping.
- US2 — As a maintainer, I need each emitted problem key's intent record, rule
  membership, negative control, and corpus evidence to agree so an advisory
  accident cannot survive as a green gate.

### Constraints

- Add exactly the three named keys to the existing `status-evidence` tuple;
  never group all `validate_state` results or introduce a new rule.
- Flip rule membership and each `PROBLEM_KEY_INTENT` verdict atomically.
- Preserve the full JSON report shape and values. Only the scoped return code
  and the three verdicts change.
- Use one shared clean workflow/state builder with three isolated mutations;
  each negative control proves its key alone makes the exact invocation exit
  `1` while the other two new lists remain empty.
- Add an explicit regression over every tracked workflow with an adjacent
  `autopilot-state.json`; a workflow without an adjacent state is outside that
  pair corpus, not synthesized silently.
- Narrow only the existing authored guard paragraph, then regenerate mirrors,
  payloads, proofs, and docs references through repository tooling.
- Python 3.11+ standard library only. Follow strict RED → GREEN → REFACTOR TDD.
- Treat `docs/ai/specs/.process/ART-017-design-concept.md` as the source of truth
  for the eight settled decisions and their rationale.

### Out of Scope

- The nine remaining advisory keys.
- Reworking `--rule` scoping or adding a new rule/invocation.
- Arming legacy `missing_state_prefixes` or `missing_state_post_items` coverage
  debt under `status-evidence`.
- A new failure-summary schema, fail-fast behavior, or hand-edited generated
  mirrors.
- Stacking on ART-008; ART-017 develops independently and serializes only the
  final rebase/regeneration boundary.
```

### Specify Results

<!-- Fill in after running the command -->

| Metric | Value |
|--------|-------|
| Functional Requirements | <!-- e.g., FR-001 through FR-020 --> |
| User Stories | <!-- Count --> |
| Acceptance Criteria | <!-- Count --> |

### Files Generated

- [ ] `specs/art-017-state-bookkeeping-checks/spec.md`

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

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

### Clarify Prompts

The design concept contains no deferred Open Questions. Clarify should verify
that the generated spec encodes the settled decisions below and ask only when a
new ambiguity or contradiction appears.

#### Session 1: Rule Authority And Failure Contract

```text
/speckit-clarify Verify exact rule authority and failure semantics: only the three ART-017 keys join status-evidence; membership and gated verdicts remain atomic; legacy coverage keys stay report-only; the complete JSON report shape is preserved.
```

#### Session 2: Negative Controls And Corpus Evidence

```text
/speckit-clarify Verify the evidence contract: one shared clean builder, one isolated mutation per armed key, target-key and exit-code assertions, other-new-key emptiness assertions, a clean control, and exact discovery rules for tracked workflow/autopilot-state.json pairs.
```

#### Session 3: Integration And Generated Artifacts

```text
/speckit-clarify Verify the release boundary: narrow the authored autopilot paragraph only, regenerate derived Codex/payload/proof/reference surfaces, preserve ART-008 independence, and require a latest-main rebase plus regeneration and full-suite proof before ready or merge.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/art-017-state-bookkeeping-checks/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Runtime: Python 3.11+ standard library
- Behavior surface: `validate-autopilot-phase-coverage.py` plus one authored Markdown skill paragraph
- State contract: JSON `autopilot-state.json` plan-step uniqueness, ordering, and single-in-progress invariants
- Testing: existing `unittest` module through `python3 tests/speckit-pro/run-all.py`
- Release tooling: `scripts/refresh-release-artifacts.py` and docs reference generation/checking

## Constraints
- Re-read `docs/ai/specs/.process/ART-017-design-concept.md`; it is the source of truth for scope and rationale.
- Quote and implement the user's routing decision: "Use status-evidence (Recommended)." Add exactly the three named keys and no helper-level grouping.
- Quote and implement the atomicity decision: "Keep them atomic (Recommended)." Rule membership and each `gated` verdict must change together.
- Preserve legacy coverage behavior: `missing_state_prefixes` and `missing_state_post_items` remain visible but nonblocking under `status-evidence`.
- Preserve the full JSON report shape, existing key names, and values; only scoped exit authority and intent verdicts change.
- Keep all authored tooling Python 3.11+ standard library; no Bash or `jq` implementation path.
- Do not hand-edit `speckit-pro/codex-skills/**`, `dist/**`, installed-cache proofs, or generated docs references.

## Architecture Notes
- Authored production files are limited to:
  1. `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`
  2. `speckit-pro/skills/speckit-autopilot/SKILL.md`
- Authored test file: `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`.
- "Shared clean builder (Recommended)": create one known-good workflow/state pair and three isolated mutations. For each, assert the target key, the other two new keys are empty, and `--rule status-evidence` exits `1`; retain a clean `0` control.
- "Tracked workflow-state pairs (Recommended)": explicitly discover tracked workflows with adjacent `autopilot-state.json` files and run the exact scoped invocation for every pair. Do not synthesize a state for workflows without one.
- "Narrow existing paragraph (Recommended)": distinguish legacy structural coverage debt from current-run state invariants in the authored skill only, then regenerate derived surfaces.
- "Rebase then regenerate (Recommended)": ART-017 may develop beside ART-008, but final integration waits for a latest-main rebase, shared-artifact regeneration, docs-reference generation/checking, and the full suite.
- Keep one vertical slice. The forward estimator returned 125 LOC and one slice; the setup gate warned only on roadmap-wide surface count and returned no blocker.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales (if needed) |
| `data-model.md` | ⏳ | Entities and types |
| `contracts/` | ⏳ | API specifications |
| `quickstart.md` | ⏳ | Developer onboarding |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Before running any checklists, read `spec.md` and `plan.md` and identify which domains apply. Look for these signals:

| Signal in Your Spec/Plan | Recommended Domain |
|---|---|
| API endpoints, REST routes, request/response models | **api-contracts** |
| User-facing UI, components, forms, layouts | **ux** |
| Keyboard navigation, screen readers, WCAG, ARIA | **accessibility** |
| Auth, tokens, secrets, input validation, user roles | **security** |
| Response time budgets, caching, query performance | **performance** |
| Database schemas, migrations, data validation | **data-integrity** |
| LLM prompts, model calls, embeddings, token limits | **llm-integration** |
| SSE, WebSocket, streaming, real-time events | **streaming-protocol** |
| Error handling, retries, fallbacks, degradation | **error-handling** |
| State lifecycle, sessions, caching, persistence | **state-management** |

**Target: 2-4 domains.** Prioritize domains where the spec has the most complexity or risk.

### Step 2: Run Enriched Checklist Prompts

For each domain, include spec-specific focus areas in the prompt — not just the bare domain name.

#### 1. State Management Checklist

Why this domain: the feature turns uniqueness, ordering, and
single-in-progress properties of `autopilot-state.json.plan` into blocking
state-lifecycle invariants.

```text
/speckit-checklist state-management

Focus on ART-017 requirements:
- Exact semantics for duplicate plan-step names, checkpoint ordering, and more than one in-progress step
- Clean-state behavior and independence of the three problem lists
- Boundaries between live state invariants and legacy structural coverage lists
- Pay special attention to: every malformed-state scenario must identify one invariant and move the exact scoped exit code
```

#### 2. Error Handling Checklist

Why this domain: ART-017 deliberately changes process failure authority while
preserving the complete JSON diagnostic contract.

```text
/speckit-checklist error-handling

Focus on ART-017 requirements:
- Exit `1` for each isolated invariant under `--rule status-evidence`
- Exit `0` for the shared clean control and tracked clean pairs
- Full-report preservation even when the scoped rule fails
- Pay special attention to: no unrelated gated key may be the reason a negative control exits non-zero
```

#### 3. Reliability Checklist

Why this domain: the repair is only trustworthy if durable workflow/state
pairs, authored/generated parity, and final integration all remain reproducible.

```text
/speckit-checklist reliability

Focus on ART-017 requirements:
- Deterministic discovery and validation of every tracked adjacent workflow/state pair
- Authored-source ownership versus generated Codex, payload, proof, and docs-reference surfaces
- Final latest-main rebase, regeneration, targeted checks, and full-suite evidence while ART-008 develops separately
- Pay special attention to: a clean local test must not mask stale generated artifacts or an unvalidated tracked state pair
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| state-management | | | |
| error-handling | | | |
| reliability | | | |
| **Total** | | | |

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/art-017-state-bookkeeping-checks/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: RED controls → atomic guard/verdict change → corpus proof → prose → regeneration → verification
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story, not by technical layer

## Implementation Phases
1. Setup — capture the clean baseline and build the shared clean workflow/state fixture
2. US1 — add three isolated failing controls, then atomically arm the keys and flip their verdicts
3. US2 — add the tracked workflow/state-pair regression and narrow the authored explanation
4. Integration — regenerate derived artifacts and docs references, then run targeted and full verification

## Constraints
- Read `spec.md`, `plan.md`, and `docs/ai/specs/.process/ART-017-design-concept.md` before generating tasks.
- Preserve the design concept's Non-goals; do not add a new rule, arm other advisory keys, redesign report output, or hand-edit generated files.
- Encode the Q&A "why": `status-evidence` is the only rule the current autopilot invocation consults; membership and verdicts are one invariant; each negative control must isolate its key; tracked pairs catch durable-state regressions synthetic fixtures miss.
- Use strict RED → GREEN → REFACTOR sequencing. The three negative controls must fail for the expected missing rule authority before production edits begin.
- Keep authored edits to the two production files and one existing unit-test file unless Plan explicitly proves an additional authored surface is required and re-estimates the budget.
- A tracked `.py` change under `tests/speckit-pro/**` requires lockfile-matched docs dependencies plus `reference:generate` and `reference:check` before completion.
- Final readiness waits for the ART-008 integration boundary chosen in Q8: rebase latest main, regenerate, then run the full suite.
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
**placeholder** until then — leave the cells blank during scoping. The classifier
emits one machine-readable decision; the SKILL is what writes it into this section
(the script never writes a file of its own). This route is recorded only here in the
workflow file — never in the spec map. It is read downstream by the layer-planner and
multi-PR emission work that builds on top of it; recording it now wires no PR creation
or branch splitting on its own.

The decision answers "can this change be split into multiple small PRs safely?" by
inspecting the change's structural seams (independent additive capabilities), not its
line count. Surface the four fields the SKILL extracts from the emitted decision:

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | | Any release-safety warning attached to the change (empty when there is no releasability risk). |

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/art-017-state-bookkeeping-checks
```

See the classifier script at
[`speckit-autopilot/scripts/atomicity-route`](../../speckit-autopilot/scripts/atomicity-route).

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Cross-artifact consistency across `spec.md`, `plan.md`, `tasks.md`, and `docs/ai/specs/.process/ART-017-design-concept.md`; the design concept is authoritative for the eight settled scoping decisions.
2. Rule authority — exactly the three named state-invariant keys join `status-evidence`; no other advisory or coverage key is armed, and no new rule or invocation appears.
3. Intent integrity — each new membership and `PROBLEM_KEY_INTENT` verdict flip is represented as one atomic task/requirement, preserving the exact-consistency test.
4. Evidence isolation — every armed key has a RED negative control from the shared clean builder, asserts the other two new lists stay empty, and proves the exact scoped exit `1`; the clean control proves `0`.
5. Corpus completeness — tasks define deterministic tracked workflow/adjacent-state discovery and an exact-invocation regression without silently synthesizing missing states.
6. Failure-contract stability — no task changes the JSON report shape, key names, full-report emission, or legacy coverage visibility.
7. Scope and file accuracy — authored edits remain the validator, authored autopilot `SKILL.md`, and existing bookkeeping-guard test unless a justified amendment updates the reviewability estimate.
8. Integration hygiene — derived surfaces are regenerated rather than hand-edited, docs reference steps are present for the tracked Python test change, and final readiness waits for latest-main rebase/regeneration/full-suite evidence after ART-008 coordination.
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

**When to run:** After Phase 6 commits and before Phase 7 begins. Gate semantics
are unchanged; this section records the verdict so a later session can read it.

| Field | Value |
|-------|-------|
| Mode | <!-- advisory (default) or strict --> |
| Composite confidence | <!-- 0.00-1.00 --> |
| Verdict | <!-- proceed / remediate / stop --> |
| Evidence | <!-- what the score was computed from --> |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```text
/speckit-implement

## Approach: TDD-First

For each task, follow this cycle:

1. **RED**: Write failing test defining expected behavior
2. **GREEN**: Implement minimum code to make test pass
3. **REFACTOR**: Clean up while tests still pass
4. **VERIFY**: Manual verification of acceptance criteria

### Pre-Implementation Setup

Before starting any task:
1. Read `tasks.md`, `plan.md`, and `docs/ai/specs/.process/ART-017-design-concept.md`; use the Q&A log for the reason behind every scope boundary.
2. Verify `git rev-parse --abbrev-ref HEAD` is `art-017-state-bookkeeping-checks` and `git status --porcelain` is clean.
3. Preserve the G0 full-suite baseline recorded by the planning stage; run `python3 tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py` as the targeted starting check.
4. Before any docs reference command, run the documented worktree bootstrap `pnpm --dir docs-site install --frozen-lockfile` if this worktree has not already done so.

### Implementation Notes
- Follow strict RED → GREEN → REFACTOR. Add the shared clean builder and three isolated failing tests before editing `RULE_PROBLEM_KEYS` or `PROBLEM_KEY_INTENT`.
- In GREEN, add only `in_progress_errors`, `duplicate_state_steps`, and `state_order_errors` to `status-evidence`, and flip their three verdicts to `gated` in the same implementation step.
- Keep the existing report construction and `main()` rule-selection algorithm unchanged. The chosen answer was "Preserve report shape (Recommended)."
- Add the tracked workflow/state-pair regression using repository-relative discovery and the exact `--rule status-evidence` argv; do not invent states for workflows without an adjacent file.
- Narrow only the authored paragraph in `speckit-pro/skills/speckit-autopilot/SKILL.md`; do not hand-edit Codex mirrors, `dist/**`, installed-cache proofs, or generated docs.
- After authored changes, run `python3 scripts/refresh-release-artifacts.py`, `pnpm --dir docs-site reference:generate`, and `pnpm --dir docs-site reference:check`, followed by the targeted test and `python3 tests/speckit-pro/run-all.py`.
- Before ready or merge, implement Q8 exactly: rebase onto current `main`, regenerate all shared artifacts again, and rerun the full suite. Do not stack ART-017 on ART-008.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | | | |
| 2 - User Story 1 | | | |
| 3 - User Story 2 | | | |
| 4 - Polish | | | |

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

- [ ] All tasks marked complete in tasks.md
- [ ] Targeted bookkeeping-guard unittest passes
- [ ] Full suite passes: `python3 tests/speckit-pro/run-all.py`
- [ ] Docs references regenerate and check clean
- [ ] Release artifacts regenerate and artifact-consistency is clean
- [ ] Linting: N/A — repository uses the Python-authoritative suite
- [ ] Build: N/A — no separate build surface for this Python/Markdown repair
- [ ] Manual verification complete
- [ ] PR created and reviewed
- [ ] Merged to main branch

---

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

- [ ] **TODO — restore the Codex same-task scaffold-to-autopilot handoff.**
      SpecKit Pro 2.27.0 still emits the new-task, relative-workflow recovery
      form even when the generated worktree is a registered descendant that can
      be bound safely. The unmerged local branch
      `fix-codex-same-task-autopilot` at `7ccc8a994` contains an earlier guarded
      absolute-path implementation based on 2.25.0. Rebase or supersede that
      repair on current `main`, preserve its descendant/path/subagent binding
      checks, regenerate release artifacts, verify the installed Codex payload,
      and ship it in a tagged release. This platform follow-up is outside
      ART-017's state-bookkeeping implementation scope.

### Patterns to Reuse

-

---

## Project Structure Reference

```
speckit-pro/
├── skills/speckit-autopilot/
│   ├── SKILL.md
│   └── scripts/validate-autopilot-phase-coverage.py
tests/speckit-pro/
└── unit/test-autopilot-bookkeeping-guard.py
docs/ai/specs/.process/
├── ART-017-design-concept.md
└── ART-017-workflow.md
specs/art-017-state-bookkeeping-checks/
└── SPEC-MOC.md
```

---

Populated from the SpecKit workflow template, the ART-017 roadmap entry, the
project constitution, repository source, the blind-spot pass, and the setup-mode
Design Concept interview.
