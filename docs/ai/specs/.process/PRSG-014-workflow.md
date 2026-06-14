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
| Specify | `/speckit-specify` | Complete | Created spec.md and requirements checklist; G1 passed with 0 clarification markers |
| Clarify | `/speckit-clarify` | Complete | Four focused sessions complete; G2 passed |
| Plan | `/speckit-plan` | Complete | Created plan.md, research.md, data-model.md, quickstart.md, and stack-manager decision contract; G3 passed |
| Checklist | `/speckit-checklist` | Complete | 4 domains; 13 gaps found / 13 fixed; G4 marker count clean |
| Tasks | `/speckit-tasks` | Complete | Generated 71 test-first tasks; G5 passed with 0 markers |
| Analyze | `/speckit-analyze` | Complete | 4 findings (0C/1H/3M/0L) remediated; marker counter clean; G6 passed |
| Implement | `/speckit-implement` | Complete | Implemented optional stack-manager detection, emission/restack evidence threading, guidance parity, and verification; G7 passed |

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

**Constitution Check:** Verified during autopilot preflight

### Scaffold Preflight Evidence

| Check | Result | Notes |
|-------|--------|-------|
| `specify` CLI | Passed | Available on `PATH` |
| Reviewability setup gate | Passed | `reviewability-gate.sh setup docs/ai/specs/pr-size-governance-technical-roadmap.md` returned `status=pass` with no warnings or blockers |
| Reviewability preset | Installed | `.specify/presets/speckit-pro-reviewability` refreshed; plan template changed |
| Preset resolution | Passed | `spec-template`, `plan-template`, and `tasks-template` resolve to `speckit-pro-reviewability v1.0.0` |
| Slice-size advisory | OK | `estimated_loc=325`, `suggested_slices=1`, `status=ok`; no split question required |
| Archive sweep startup | Passed | Archive extension installed; only active `specs/**` directory is the current PRSG-014 target, so no prior spec was eligible for archival or cleanup |
| Autopilot prerequisite check | Passed | `check-prerequisites.sh docs/ai/specs/.process/PRSG-014-workflow.md` returned `all_pass=true` on branch `prsg-014-optional-gh-stack-stack-manager-integration` |
| Codex agent availability | Passed | Required SpecKit Pro custom agents are installed in the user Codex agent registry with `gpt-5.5` / `xhigh` settings |
| Confidence gate mode | Advisory | `resolve-confidence-mode.sh` resolved `advisory` for this invocation |

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

- [x] Autopilot detects whether `gh-stack` is available through `gh stack`, supported, compatible with the repo, compatible with the branch topology, and safe by read-only proof before mutation.
- [x] Emission/restack evidence persists `gh_stack.available`, `gh_stack.supported`, `gh_stack.reason`, selected stack manager, command plan, version/support outcome, fallback reason, and PR/branch topology.
- [x] When support detection passes, stack-aware create/sync/restack behavior preserves PRSG-013 marker order, branch names, explicit base topology, and PRSG-012 title/body validation.
- [x] Unsupported, missing, or ambiguous `gh-stack` environments fall back to explicit `gh pr create/edit --base --head --body-file` before mutation.
- [x] After any partial `gh-stack` mutation, failures block with recoverable state instead of mixing stack managers.
- [x] Layer 4 fake-CLI fixtures, Layer 7 live-safe replay, and Layer 8 operator guidance parity expectations cover supported, fallback, and blocked paths.

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
| Functional Requirements | 28 after security checklist remediation |
| User Stories | 4 |
| Acceptance Criteria | 11 |

### Files Generated

- [x] `specs/prsg-014-optional-gh-stack-stack-manager-integration/spec.md`
- [x] `specs/prsg-014-optional-gh-stack-stack-manager-integration/checklists/requirements.md`

### Specify Gate

| Gate | Result | Evidence |
|------|--------|----------|
| G1 | Passed | `validate-gate.sh G1 specs/prsg-014-optional-gh-stack-stack-manager-integration` returned `pass=true`, `markers=0` |

### Specify Follow-up Focus

- `[codebase]` Confirm exact `gh-stack` command/version capability matrix for create/sync/restack.
- `[spec]` Finalize stack-manager evidence field names with minimal schema churn.
- `[domain]` Define what counts as safe pre-mutation `gh-stack` read-only proof.
- `[security]` Confirm command argument safety expectations for branch names, body paths, and command plans.

---

## Phase 2: Clarify

**When to run:** After Specify, before Plan. Maximum 5 targeted questions per session.

### Clarify Prompts

#### Session 1: Detection Contract Focus

```bash
/speckit-clarify Focus on gh-stack detection: command availability, version capture, usable status output, repo compatibility, branch topology compatibility, safe read-only proof semantics, and exact JSON fields for `available`, `supported`, `reason`, selected manager, and command plan.
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
| 1 | Detection Contract | 5 | Accepted `gh stack` as canonical runtime invocation, a shared `stack_manager_decision` object, read-only `gh stack view --json` plus synthetic command plan as pre-mutation proof, topology compatibility from SpecKit PRS/marker state, and array-of-argv command plan records. |
| 2 | Mutation and Fallback | 5 | Accepted first attempted topology-changing command as the no-fallback mutation boundary; fallback only before mutating `gh stack` attempts; recoverable blocked state fields; retry reconciliation by slice/head/base/PR/head SHA/packet identity; ambiguous side effects classified as `partial_mutation_unknown` with `fallback_allowed=false`. |
| 3 | Emission and Restack | 5 | Accepted packet-owned PR metadata as authoritative before `gh stack` topology linking; stack-wide packet/marker preflight before first mutating `gh stack` command; shared top-level `stack_manager_decision` evidence plus per-operation manager/argv/status; supported restack via `gh stack rebase --upstack <first-remaining-branch>` only behind version/capability proof; argv-only command execution with validated refs/paths and bounded output tails. |
| 4 | Parity and Test | 5 | Accepted Layer 4 fake-CLI fixtures as authoritative stack-manager behavior proof, a shared versioned `stack-manager-decision` schema with explicit schema fields, Layer 7 as orchestration/live-safe proof only, Layer 8 as operator guidance parity for Claude Code and Codex without duplicate scripts, and Plan-owned `gh stack` command/version matrix resolution. |

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|----------------------|------------|-------|---------|------------|---------------|
| 1 | Clarify | Safe read-only proof for `gh stack` | [domain, codebase] | 1->2 | escape-hatch then 3/3 | Safe pre-mutation proof is read-only availability/version/support evidence plus parseable `gh stack view --json` topology checked against SpecKit PRS/marker state; mutating commands are never detection dry-runs, so detection records a synthetic command plan and falls back before mutation when proof is missing or ambiguous. | codebase-analyst, domain-researcher, spec-context-analyst |
| 2 | Clarify | Packet-owned PR metadata before stack linking | [domain, codebase] | 1 | both-agree | Supported emission renders and validates all PR packets, creates or updates PRs with packet-owned explicit `gh pr create/edit`, then uses `gh stack link` or a proven equivalent only for topology linking/sync. | codebase-analyst, domain-researcher |
| 3 | Clarify | Safe supported restack subcommand | [domain, codebase] | 1 | both-agree | Supported restack may use `gh stack rebase --upstack <first-remaining-branch>` plus required proven sync/push only when the installed version matrix proves exact noninteractive scope support; otherwise `restack.sh --apply` / `gh pr edit --base` remains the fallback before mutation. | codebase-analyst, domain-researcher |
| 4 | Clarify | Argv-only command execution | [security] | 1 | 3/3 | Stack-manager command plans are executable only as argv arrays; command strings are display-only, refs/body paths are validated before inclusion, and stdout/stderr evidence is bounded. | codebase-analyst, spec-context-analyst, domain-researcher |
| 5 | Clarify | L8 Claude/Codex parity without duplicate scripts | [codebase, spec-context] | 1 | both-agree | L8 proves operator guidance parity for supported, fallback, and blocked stack-manager flows; Claude Code and Codex guidance point to shared scripts/contracts, PRSG-014 adds no Codex-only stack-manager implementation, and transcript-level Claude/Codex parity is out of scope until a stable Codex replay/transcript harness and schema exist. | codebase-analyst, spec-context-analyst |

### Clarify Gate

| Gate | Result | Evidence |
|------|--------|----------|
| G2 | Passed | `validate-gate.sh G2 specs/prsg-014-optional-gh-stack-stack-manager-integration` returned `pass=true`, `markers=0` |

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
- Tests: shell Layer 4 fixtures with fake `gh` dispatching canonical `gh stack`; Layer 7 replay; Layer 8 operator guidance parity fixtures

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
  ambiguous, missing, read-only-proof-failed, topology-incompatible, fallback,
  partial-mutation, duplicate-retry, supported-restack, and fallback-restack
  cases are testable.
- Resolve exact `gh-stack` subcommands and version support in research before
  tasks are generated.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Technical context, command capability matrix, constitution gates, reviewability estimate, and implementation flow |
| `research.md` | Complete | `gh stack` v0.0.5 command/version behavior, private-preview fail-closed rationale, selected commands, and fallback rationale |
| `data-model.md` | Complete | Stack-manager decision, command plan, topology evidence, execution evidence, and recoverable block state |
| `contracts/` | Complete | Planning contract for `stack-manager-decision.v1` |
| `quickstart.md` | Complete | Operator and fixture validation for supported, fallback, blocked, retry, restack, replay, and parity paths |

### Plan Gate

| Gate | Result | Evidence |
|------|--------|----------|
| G3 | Passed | `validate-gate.sh G3 specs/prsg-014-optional-gh-stack-stack-manager-integration` returned `pass=true`, `markers=0`; reviewability estimator returned `status=pass` for 14 declared file entries. |

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
- `gh-stack` command availability, version, read-only status proof, repo compatibility, topology compatibility, and support semantics
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
| integration | 12 | 2 found / 2 fixed | Complete |
| error-handling | 16 | 4 found / 4 fixed | Complete |
| reliability | 16 | 2 found / 2 fixed | Complete |
| security | 15 | 5 found / 5 fixed | Complete |

### Checklist Gate

| Gate | Result | Evidence |
|------|--------|----------|
| G4 | Passed | `validate-gate.sh G4 specs/prsg-014-optional-gh-stack-stack-manager-integration` returned `pass=true`, `markers=0`; four checklist domains covered 59 items and resolved 13 gaps with no unresolved consensus items. |

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
- Fake `gh`/`gh stack` Layer 4 fixtures for supported, unsupported, missing,
  ambiguous, read-only-proof-failed, topology-incompatible, fallback,
  partial-mutation, duplicate-retry, supported-restack, and fallback-restack cases
- Schema/evidence assertions for selected manager, reasons, command plan, and topology
- L8 parity fixture updates for Claude/Codex guidance
```

### Task Generation Results

| Metric | Value |
|--------|-------|
| Total Tasks | 71 |
| Parallel Opportunities | 24 |
| Test Tasks | 45 |

### Tasks Gate

| Gate | Result | Evidence |
|------|--------|----------|
| G5 | Passed | `validate-gate.sh G5 specs/prsg-014-optional-gh-stack-stack-manager-integration` returned `pass=true`, `markers=0`, `task_count=71` |

### Task Reviewability Gate

| Check | Result | Evidence |
|-------|--------|----------|
| Task-mode reviewability | Size-only block; continue to marker planning | `specs/prsg-014-optional-gh-stack-stack-manager-integration/.process/reviewability/tasks-gate.json` records `status=block`, `mode=tasks`, `exit_code=1`, `is_size_only=true`, `reviewable_loc=2840`, `total_files=111`, and no correctness or safety blocker. |

### Atomicity Route

| Field | Value |
|-------|-------|
| Route | `one-navigable-PR` |
| Releasable | `true` |
| Signals | `context:consumer-locality:out-of-tree`, `change-shape:modify-heavy` |
| Warnings | None |
| Evidence | `specs/prsg-014-optional-gh-stack-stack-manager-integration/.process/atomicity/route.json` |

### PR Marker Plan

| Field | Value |
|-------|-------|
| Status | Planned |
| Marker IDs | `foundation`, `us1`, `us2`, `us3`, `us4` |
| Review Order | `foundation` -> `us1` -> `us2` -> `us3` -> `us4` |
| Polish Folding | `T066`-`T071` folded into `us4` as nearest preceding non-polish scope |
| Warning | Reviewability sizing result is marker-planning input |
| Evidence | `specs/prsg-014-optional-gh-stack-stack-manager-integration/.process/marker-plan/pr-marker-plan.json` |

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
| Critical | 0 | Complete |
| High | 1 | Remediated |
| Medium | 3 | Remediated |
| Low | 0 | Complete |

**Finding remediation:**

- F1 [HIGH]: Packet-validation fallback wording in `plan.md` could be read as allowing explicit-`gh` fallback after invalid PRSG-012 packet validation, contradicting packet-owned title/body validation before PR creation.
  - Fix: Changed the error classification rules so stack-manager planning/read-only/topology failures may fall back only when packets are valid, while PRSG-012 packet-validation failures hard-block before `gh stack`, explicit `gh pr create/edit`, or manager switching; added matching quickstart and task coverage.
  - Source: `docs/ai/specs/pr-size-governance-technical-roadmap.md` PRSG-012 packet contract; `research.md` Decisions 3-4; local `gh stack link --help` confirms branch args can push/create PRs.
- F2 [MEDIUM]: `plan.md` declared stale Layer 7/8 fixture paths that did not match generated tasks or existing test harness layout.
  - Fix: Updated declared file operations and project structure to use `tests/speckit-pro/layer7-integration/dispatch-fixtures/22-prsg-014-stack-manager-replay/` and `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/`.
  - Source: existing `tests/speckit-pro/layer7-integration/dispatch-fixtures/*` and `tests/speckit-pro/layer8-parity/*` layout.
- F3 [MEDIUM]: Checklist artifacts still had unchecked items after the workflow/state recorded 13 gaps fixed and G4 clean.
  - Fix: Marked verified checklist items complete with task/source citations in integration, error-handling, and security checklists.
  - Source: `tasks.md` T013-T065 coverage and G4 marker counter evidence.
- F4 [MEDIUM]: `tasks.md` carried only the initial 325 LOC reviewability estimate and did not expose the actual post-G5 size-only block or PRSG-013 marker plan.
  - Fix: Added the post-G5 task reviewability result, marker order (`foundation -> us1 -> us2 -> us3 -> us4`), and T066-T071 polish folding to the task reviewability note.
  - Source: `.process/reviewability/tasks-gate.json`, `.process/marker-plan/pr-marker-plan.json`, and PRSG-013 non-stopping marker-plan guidance.

**Verification:** marker counter reports 0 findings after remediation; G6 validation passed.

**Unresolved for consensus:** None.

### Confidence Gate

| Check | Result | Evidence |
|-------|--------|----------|
| G6.5 | Soft-skipped in advisory mode | `confidence-gate.sh docs/ai/specs/.process/PRSG-014-workflow.md --threshold 0.90 --mode advisory` returned `NO_DATA`; no synthesizer confidence emit was present. Per advisory-mode protocol, this is recorded as a plugin-regression note and Phase 7 may proceed. |

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
| Tasks Completed | 71 / 71 |
| Tests Added/Updated | Layer 4 detector/emission/restack tests and fixtures; Layer 7 replay fixture; Layer 8 guidance parity fixture |
| Implementation Commit | `03da8f3c8587d911e6adbbb8361966c80b8cc717` |
| Verification | `test-detect-stack-manager: 18/18`, `test-multi-pr-emission: 159/159`, `test-restack: 33/33`, Layer 1 `979/979`, Layer 4 `1768/1768`, Layer 7 all fixtures passed, Layer 8 `12/12`, default suite `2937/2937` |

### Implementation Evidence

| Area | Evidence |
|------|----------|
| Shared detector | `speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh` |
| Shared schema | `speckit-pro/skills/speckit-autopilot/contracts/stack-manager-decision.schema.json` |
| Emission integration | `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` persists `stack_manager_decision`, `stack_manager_evidence_path`, command-plan, topology, and PRS evidence references |
| Restack integration | `speckit-pro/skills/speckit-autopilot/scripts/restack.sh` emits stack-manager decision/evidence in apply output and keeps dry-run pure |
| Guidance parity | `speckit-pro/skills/speckit-autopilot/references/post-implementation.md`, `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`, and `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md` |
| Marker checkpoints | `specs/prsg-014-optional-gh-stack-stack-manager-integration/.process/marker-plan/pr-marker-plan.json` now records complete checkpoints for `foundation`, `us1`, `us2`, `us3`, and `us4` at implementation commit `03da8f3` |

### Implement Gate

| Gate | Result | Evidence |
|------|--------|----------|
| G7 | Passed | `bash tests/speckit-pro/run-all.sh` passed `2937/2937` after the final detector classification fix; focused Layer 4, Layer 7, and Layer 8 validation also passed. |

---

## PR and Review Notes

- Generated PR titles must remain public-readable conventional commits.
- Generated PR bodies must include stack-manager evidence without burying or
  weakening PRSG-012 packet sections.
- Known fallback behavior is not a failure; it is an expected path when
  `gh-stack` is unavailable, unsupported, ambiguous, or unsafe before mutation.
- Any partial-mutation block must include enough state for an operator to resume
  or repair without duplicating PRs.
