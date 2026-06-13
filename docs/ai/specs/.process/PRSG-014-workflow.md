# SpecKit Workflow: PRSG-014 - Optional gh-stack stack manager integration

**Template Version**: 1.0.0
**Created**: 2026-06-13
**Purpose**: Reusable template for executing the PRSG-014 SpecKit workflow with autopilot.

---

## How to Use This Template

1. Start autopilot with this file:

   ```bash
   $speckit-autopilot docs/ai/specs/.process/PRSG-014-workflow.md
   ```

2. Keep `docs/ai/specs/.process/PRSG-014-design-concept.md` open as the source
   of truth for the Grill Me decisions behind this scaffold.

3. Track phase status in the table below as autopilot advances.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`$speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open Questions
live at:

```text
docs/ai/specs/.process/PRSG-014-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The Specify
and Clarify prompts below were populated from that interview, so the design
concept doc is the source of truth for any decision captured during scoping.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the autopilot
> loop. Once this workflow file is populated and autopilot begins,
> clarifications happen via `/speckit-clarify` and the consensus protocol.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Pending | Scaffolded, not run |
| Clarify | `/speckit-clarify` | Pending | Recommended |
| Plan | `/speckit-plan` | Pending | Resolve `gh-stack` command/version behavior |
| Checklist | `/speckit-checklist` | Pending | Run for each recommended domain |
| Tasks | `/speckit-tasks` | Pending | Generate after plan and checklist gaps are resolved |
| Analyze | `/speckit-analyze` | Pending | Cross-check spec, plan, tasks, and design concept |
| Implement | `/speckit-implement` | Pending | Execute only after G6 approval |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

Each phase requires human review and approval before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Stack-manager ambiguity resolved and documented |
| G3 | After Plan | Architecture approved, constitution gates pass, dependencies identified |
| G4 | After Checklist | All requirement-quality gaps addressed |
| G5 | After Tasks | Task coverage verified, dependencies ordered |
| G6 | After Analyze | No critical consistency issues remain |
| G7 | After Each Implementation Phase | Tests pass, manual verification complete |

---

## Prerequisites

### Constitution Validation

Before starting any workflow phase, verify alignment with the project constitution
at `.specify/memory/constitution.md`:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | Preserve the `speckit-pro/` authoring layout, mirrored Codex skill layout, and `tests/speckit-pro/` sibling test suite. | `bash tests/speckit-pro/run-all.sh --layer 1` |
| Script Safety | Any changed Bash script keeps `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, and clear `jq` JSON handling. | `bash -n` on touched scripts plus targeted Layer 4 tests |
| Test Coverage Before Merge | New stack-manager detection, fallback, schema, and restack behavior require deterministic Layer 4 coverage before merge. | Targeted Layer 4 fake-CLI fixtures, then `bash tests/speckit-pro/run-all.sh` |
| KISS, Simplicity & YAGNI | Add a helper only where it has multiple real callers; avoid speculative stack-manager abstractions beyond emission and restack. | Plan Complexity Tracking plus code review |
| Conventional Commits | PR titles and generated packet titles remain public-readable conventional commits. | PRSG-012 packet validation plus PR title CI |

**Constitution Check:** Pending

### Scaffold Preflight Evidence

| Check | Result | Notes |
|-------|--------|-------|
| `specify` CLI | Passed | Available on `PATH` |
| Reviewability setup gate | Passed | `reviewability-gate.sh setup docs/ai/specs/pr-size-governance-technical-roadmap.md` returned `status=pass` with no warnings or blockers |
| Reviewability preset | Installed | `.specify/presets/speckit-pro-reviewability` refreshed; plan template changed |
| Preset resolution | Passed | `spec-template`, `plan-template`, and `tasks-template` resolve to `speckit-pro-reviewability v1.0.0` |
| Slice-size advisory | OK | `estimated_loc=325`, `suggested_slices=1`, `status=ok`; no split question required |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-014 |
| **Name** | Optional gh-stack stack manager integration |
| **Branch** | `prsg-014-optional-gh-stack-stack-manager-integration` |
| **Dependencies** | PRSG-009 multi-PR emission; PRSG-013 marker checkpoints and live marker emission; PRSG-012 title/body validation when landed |
| **Enables** | Optional stack-manager hardening for split PR create/sync/restack |
| **Priority** | P2 |

### Success Criteria Summary

- [ ] Autopilot detects whether `gh-stack` is available, supported, compatible with the repo, compatible with the branch topology, and safe to dry-run.
- [ ] Emission/restack evidence persists `gh_stack.available`, `gh_stack.supported`, `gh_stack.reason`, selected stack manager, command plan, version/support outcome, fallback reason, and PR/branch topology.
- [ ] When support detection passes, stack-aware create/sync/restack behavior preserves PRSG-013 marker order, branch names, explicit base topology, and PRSG-012 title/body validation.
- [ ] Unsupported, missing, or ambiguous `gh-stack` environments fall back to explicit `gh pr create/edit --base --head --body-file` before mutation.
- [ ] After any partial `gh-stack` mutation, failures block with recoverable state instead of mixing stack managers.
- [ ] Layer 4 fixtures with fake `gh-stack` and fake `gh`, Layer 7 live-safe replay, and Layer 8 parity expectations cover supported and fallback paths.

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on what and why, not implementation details. Output: `specs/prsg-014-optional-gh-stack-stack-manager-integration/spec.md`

### Specify Prompt

```bash
/speckit-specify Add optional gh-stack stack-manager integration so autopilot can use native stack create/sync/restack when deterministic support checks pass, while preserving explicit gh base/head fallback everywhere else.
```

#### Detailed Prompt

```bash
/speckit-specify

## Feature: Optional gh-stack stack manager integration

### Problem Statement
PRSG-009 and PRSG-013 can emit stacked PRs through explicit `gh pr create/edit`
base/head commands, and `restack.sh` can retarget later PRs after earlier PRs
merge. That deterministic fallback must remain canonical, but repositories that
already support `gh-stack` should be able to use it to reduce manual stack
creation, sync, and restack burden.

### Users
- SpecKit operators running autopilot on split-PR specs.
- Maintainers reviewing generated stacked PRs.
- Autopilot maintainers who need deterministic evidence and recoverable failure
  states for stack-manager decisions.

### User Stories
- US1: As an operator, I can see deterministic `gh-stack` support detection and
  fallback reasons before stack-manager commands mutate branch or PR topology.
- US2: As an operator, I can let autopilot use `gh-stack` for stack-aware PR
  creation/sync when support checks pass, while unsupported repos keep the
  explicit `gh` path.
- US3: As a maintainer, I can restack after squash merges through `gh-stack`
  when safe, or through existing `restack.sh --apply` fallback otherwise.
- US4: As a reviewer, I can inspect emitted evidence showing the command plan,
  selected stack manager, fallback reason, version/support outcome, and topology.

### Constraints
- `gh-stack` is optional. Missing, unsupported, ambiguous, or unsafe
  environments fall back before mutation.
- Do not mix managers after partial `gh-stack` mutation. Block with recoverable
  evidence if a mutation has already happened.
- Preserve PRSG-013 marker order, branch names, and explicit base topology.
- Preserve PRSG-012 PR packet title/body generation and validation before PR
  creation.
- Prefer a shared `detect-stack-manager.sh` because both emission and restack
  need the same decision record.
- Keep detection/emission/restack logic single-copy in shared scripts. Update
  Claude Code and Codex guidance in lockstep.

### Out of Scope
- Making `gh-stack` a required dependency.
- Duplicating stack-manager scripts under `codex-skills/`.
- Adding unrelated stack-manager features beyond create/sync/restack, fallback,
  evidence, and safety.
- Retrying explicit `gh` after partial `gh-stack` mutation.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | Pending |
| User Stories | Pending |
| Acceptance Criteria | Pending |

### Files Generated

- [ ] `specs/prsg-014-optional-gh-stack-stack-manager-integration/spec.md`

---

## Phase 2: Clarify

**When to run:** After Specify, before Plan. Maximum 5 targeted questions per session.

### Clarify Prompts

#### Session 1: Detection Contract Focus

```bash
/speckit-clarify Focus on gh-stack detection: command availability, version capture, usable status output, repo compatibility, branch topology compatibility, safe dry-run semantics, and exact JSON fields for `available`, `supported`, `reason`, selected manager, and command plan.
```

#### Session 2: Mutation and Fallback Focus

```bash
/speckit-clarify Focus on stack-manager mutation boundaries: which steps count as irreversible mutation, when fallback to explicit `gh` is allowed, what recoverable blocked state must include after partial `gh-stack` mutation, and how retries avoid duplicate PRs.
```

#### Session 3: Emission and Restack Focus

```bash
/speckit-clarify Focus on stack-aware emission and restack: how `multi-pr-emission.sh` should preserve PRSG-013 marker order, branch names, explicit base topology, and PRSG-012 packet validation while selecting between `gh-stack` and explicit `gh`; how `restack.sh` records equivalent evidence.
```

#### Session 4: Parity and Test Focus

```bash
/speckit-clarify Focus on proof: fake `gh-stack` and fake `gh` Layer 4 fixtures, schema compatibility, Layer 7 live-safe replay expectations, and L8 Claude/Codex parity for operator guidance without duplicate scripts.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Detection Contract | Pending | |
| 2 | Mutation and Fallback | Pending | |
| 3 | Emission and Restack | Pending | |
| 4 | Parity and Test | Pending | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/prsg-014-optional-gh-stack-stack-manager-integration/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Runtime: Bash scripts and Markdown skill guidance in `speckit-pro/`
- JSON/state: `jq`, emission/restack schemas, `.process/prs.json`, `autopilot-state.json`, workflow evidence
- GitHub operations: `gh` CLI remains canonical fallback
- Optional stack manager: `gh-stack` extension when installed, supported, compatible, and safe before mutation
- Tests: shell Layer 4 fixtures with fake `gh-stack` and fake `gh`; Layer 7 replay; Layer 8 parity fixtures

## Constraints
- `gh-stack` is selected only after deterministic support checks pass.
- Explicit `gh pr create/edit --base --head --body-file` remains the fallback path.
- Fallback is allowed before mutation only. After partial `gh-stack` mutation, block with recoverable state.
- Preserve PRSG-013 marker order, branch naming, and explicit base topology.
- Preserve PRSG-012 PR packet generation and validation before PR creation.
- Shared script behavior must stay single-copy; Codex updates are guidance/parity, not duplicate script implementations.
- Keep shell logic direct and testable; use `jq` for JSON, not ad hoc string parsing.

## Architecture Notes
- Inspect `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`,
  `restack.sh`, existing emission/restack schemas, and PRSG-013 marker evidence
  before designing changes.
- Prefer a shared `detect-stack-manager.sh` that prints deterministic JSON for
  emission and restack callers.
- Extend evidence schemas compatibly rather than replacing existing PRSG-009,
  PRSG-012, or PRSG-013 records.
- Plan fake command fixtures before implementation so supported, unsupported,
  ambiguous, missing, dry-run-failed, and partial-mutation cases are testable.
- Resolve exact `gh-stack` subcommands and version support in research before
  tasks are generated.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Pending | Technical context, execution flow |
| `research.md` | Pending | `gh-stack` command/version behavior and fallback rationale |
| `data-model.md` | Pending | Evidence/state schema extensions |
| `contracts/` | Pending | JSON schemas for stack-manager evidence if needed |
| `quickstart.md` | Pending | Operator verification for supported and fallback paths |

---

## Phase 4: Domain Checklists

**When to run:** After Plan. These validate requirement quality across spec and plan.

### Recommended Domains

1. **integration** - `gh-stack` and `gh` are external CLI integrations with compatibility and version behavior.
2. **error-handling** - Fallback, partial mutation, recoverable blocked state, and retry behavior are the highest-risk areas.
3. **reliability** - Stack topology evidence, deterministic command plans, and replay-safe behavior need validation.
4. **security** - Shell command construction, branch names, body-file paths, and CLI arguments must avoid unsafe interpolation.

### Checklist Prompts

```bash
/speckit-checklist integration

Focus on PRSG-014 requirements:
- `gh-stack` command availability, version, status, repo compatibility, topology compatibility, and dry-run semantics
- Fallback to explicit `gh pr create/edit --base --head --body-file`
- Consistency between detection output, emission behavior, restack behavior, and schema evidence
- Pay special attention to unsupported or ambiguous extension behavior.
```

```bash
/speckit-checklist error-handling

Focus on PRSG-014 requirements:
- Fallback is allowed only before mutation
- Partial `gh-stack` mutation blocks with recoverable state
- Retry behavior avoids duplicate PRs and ambiguous topology
- Pay special attention to how failed `gh-stack` commands are classified.
```

```bash
/speckit-checklist reliability

Focus on PRSG-014 requirements:
- Deterministic command plans and evidence paths
- PRSG-013 marker order and branch topology preservation
- Layer 4 fake-CLI fixtures and Layer 7 replay expectations
- Pay special attention to resume behavior after blocked stack-manager operations.
```

```bash
/speckit-checklist security

Focus on PRSG-014 requirements:
- Quoted shell arguments for branches, PR body paths, and command plans
- No unsafe eval or untrusted string execution
- Clear handling of fake CLI fixture paths in tests
- Pay special attention to command injection risks in optional `gh-stack` invocation.
```

### Checklist Results

| Domain | Items | Gaps | Status |
|--------|-------|------|--------|
| integration | Pending | Pending | Pending |
| error-handling | Pending | Pending | Pending |
| reliability | Pending | Pending | Pending |
| security | Pending | Pending | Pending |

---

## Phase 5: Tasks

**When to run:** After checklist gaps are resolved. Output: `specs/prsg-014-optional-gh-stack-stack-manager-integration/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

Generate tasks for PRSG-014 using:
- `specs/prsg-014-optional-gh-stack-stack-manager-integration/spec.md`
- `specs/prsg-014-optional-gh-stack-stack-manager-integration/plan.md`
- `docs/ai/specs/.process/PRSG-014-design-concept.md`

Task boundaries must preserve the design concept decisions:
- Optional `gh-stack` strategy only after deterministic support checks
- Shared detection script consumed by emission and restack
- Fallback before mutation only; recoverable block after partial mutation
- Create/sync and restack in scope; unrelated stack-manager features out of scope
- Shared scripts plus mirrored Claude/Codex guidance

Prioritize tests before implementation:
- Fake `gh-stack`/`gh` Layer 4 fixtures for supported, unsupported, missing,
  ambiguous, dry-run-failed, fallback, and partial-mutation cases
- Schema/evidence assertions for selected manager, reasons, command plan, and topology
- L8 parity fixture updates for Claude/Codex guidance
```

### Task Generation Results

| Metric | Value |
|--------|-------|
| Total Tasks | Pending |
| Parallel Opportunities | Pending |
| Test Tasks | Pending |

---

## Phase 6: Analyze

**When to run:** After Tasks, before implementation.

### Analyze Prompt

```bash
/speckit-analyze

Cross-check PRSG-014 artifacts:
- `spec.md`
- `plan.md`
- `tasks.md`
- `docs/ai/specs/.process/PRSG-014-design-concept.md`
- Any evidence schemas and script contracts introduced for stack-manager selection

Flag drift between:
- Opportunistic `gh-stack` selection and canonical explicit-gh fallback
- Before-mutation fallback and after-mutation recoverable block behavior
- Shared script implementation and mirrored Claude/Codex guidance
- PRSG-013 marker order preservation and PRSG-012 packet validation requirements
- Checklist gaps and generated tasks
```

### Analyze Results

| Severity | Count | Status |
|----------|-------|--------|
| Critical | Pending | Pending |
| Warning | Pending | Pending |
| Info | Pending | Pending |

---

## Phase 7: Implement

**When to run:** After Analyze has no critical findings and human approval is given.

### Implement Prompt

```bash
/speckit-implement

Implement PRSG-014 from:
- `specs/prsg-014-optional-gh-stack-stack-manager-integration/tasks.md`
- `specs/prsg-014-optional-gh-stack-stack-manager-integration/plan.md`
- `docs/ai/specs/.process/PRSG-014-design-concept.md`

Honor the Q&A decisions:
- `gh-stack` is optional and selected only after support checks pass.
- Shared detection feeds both emission and restack.
- Fallback happens before mutation only.
- Partial `gh-stack` mutation blocks with recoverable state.
- Create/sync and restack are in scope; unrelated stack-manager features are not.
- Shared scripts stay single-copy while Claude/Codex guidance stays aligned.

Verification should include targeted Layer 4 fake-CLI tests first, then the
smallest broader suite that covers changed surfaces. Finish with
`bash tests/speckit-pro/run-all.sh` before PR emission when feasible.
```

### Implementation Results

| Metric | Value |
|--------|-------|
| Tasks Completed | Pending |
| Tests Added/Updated | Pending |
| Verification | Pending |

---

## PR and Review Notes

- Generated PR titles must remain public-readable conventional commits.
- Generated PR bodies must include stack-manager evidence without burying or
  weakening PRSG-012 packet sections.
- Known fallback behavior is not a failure; it is an expected path when
  `gh-stack` is unavailable, unsupported, ambiguous, or unsafe before mutation.
- Any partial-mutation block must include enough state for an operator to resume
  or repair without duplicating PRs.
