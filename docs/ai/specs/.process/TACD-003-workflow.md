# SpecKit Workflow: TACD-003 - Prerequisite and Documentation Messaging

**Template Version**: 1.0.0
**Created**: 2026-06-18
**Purpose**: Execute TACD-003 through the SpecKit workflow and prepare the prerequisite/documentation messaging slice for autopilot.

---

## How to Use This Workflow

1. Run the phases in order from the `tacd-003-prerequisite-and-documentation-messaging` branch.
2. Re-read the design concept before each phase.
3. Treat the TACD-001 spike report, TACD-002 merged behavior, and TACD-003 roadmap section as controlling source evidence.
4. Keep implementation bounded to prerequisite/user-facing messaging. Broad static/eval enforcement belongs to TACD-004.
5. Track progress in the status tables below.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`$speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/TACD-003-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The design
concept is the source of truth for setup-time scoping decisions.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the autopilot
> loop. Once autopilot begins, clarifications happen via `/speckit-clarify` and
> the consensus protocol, never via Grill Me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | `spec.md` created; G1 passed with 0 clarification markers |
| Clarify | `/speckit-clarify` | Complete | Three sessions answered; G2 passed with 0 clarification markers |
| Plan | `/speckit-plan` | Complete | `plan.md`, `research.md`, and `quickstart.md` created; G3 passed |
| Checklist | `/speckit-checklist` | Complete | Three checklists complete; G4 passed with 0 `[Gap]` markers |
| Tasks | `/speckit-tasks` | Complete | `tasks.md` created; G5 passed with 32 tasks |
| Analyze | `/speckit-analyze` | Complete | 3 findings remediated; marker counter clean; G6 ready |
| Implement | `/speckit-implement` | Complete | G7 passed; default deterministic suite passed |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

Each phase requires human review and approval before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories are clear; no unresolved `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Advisory wording and docs/test boundaries are documented |
| G3 | After Plan | Architecture, affected files, and focused verification are approved |
| G4 | After Checklist | All `[Gap]` markers are addressed or explicitly out of scope |
| G5 | After Tasks | Tasks are ordered, testable, and trace to the TACD-003 acceptance criteria |
| G6 | After Analyze | No CRITICAL issues remain; WARNING items are reviewed |
| G7 | After Implementation | Focused and default deterministic checks pass, or failures are documented with next action |

---

## Prerequisites

### Constitution Validation

Before starting any workflow phase, verify alignment with
`.specify/memory/constitution.md`:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | Keep changes inside the existing `speckit-pro` plugin and docs/spec process paths | `bash tests/speckit-pro/run-all.sh --layer 1` when structure changes |
| Script Safety | Bash changes keep `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, and `jq` for JSON | `bash -n speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` plus relevant Layer 4 tests |
| Semantic Versioning | Do not manually edit plugin version fields unless release tooling requires it | Git diff review |
| Test Coverage Before Merge | Changed prerequisite behavior has focused deterministic coverage | Relevant Layer 4 test plus `bash tests/speckit-pro/run-all.sh` before PR |
| Conventional Commits | Setup and implementation commits use conventional commit format | Git commit message review |
| KISS, Simplicity & YAGNI | Keep advisory behavior explicit and small; do not add installers, broad scanners, or speculative abstractions | Plan and code review |

**Constitution Check:** Verified

### Reviewability Setup Gate

The setup gate was run against the technical roadmap:

```json
{"mode":"setup","status":"warn","pass":true,"reviewable_loc":202,"production_files":0,"total_files":7,"primary_surface_count":2,"primary_surfaces":["docs/process","harness/adapter"],"warnings":["primary surfaces 2 exceeds warn threshold 1"],"blockers":[]}
```

This warning comes from the broader roadmap including TACD-004. The initial
TACD-003 roadmap entry itself recorded:

- Primary surface: docs/process
- Projected reviewable LOC: 142
- Production files: 1
- Total files: 5
- Budget result: within budget

Split decision from Grill Me: keep TACD-003 as one vertical slice. Later
checklist remediation expanded the active guidance file set; `plan.md` now
declares 8 modified implementation files, while the task-mode reviewability
gate below is a separate size-only marker-planning input.

### Autopilot Preflight

| Check | Status | Evidence |
|-------|--------|----------|
| Model and effort | Verified | Codex config uses `gpt-5.5` with `model_reasoning_effort = "xhigh"`; required custom agents are installed at `gpt-5.5`/`xhigh` |
| Prerequisites script | Passed | `check-prerequisites.sh docs/ai/specs/.process/TACD-003-workflow.md` returned `all_pass=true` |
| Confidence gate mode | Advisory | `resolve-confidence-mode.sh --` returned `advisory` |
| Archive sweep | Completed | No eligible previous active specs; current target excluded; cleanup disabled on feature branch |
| Tier-2 relocation | Suppressed | Active target already has `SPEC-MOC.md` with `structureVersion: 1`; no root PROCESS artifacts |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| Spec ID | TACD-003 |
| Name | Prerequisite and Documentation Messaging |
| Branch | `tacd-003-prerequisite-and-documentation-messaging` |
| Spec Directory | `specs/tacd-003-prerequisite-and-documentation-messaging` |
| Dependencies | TACD-001, TACD-002 |
| Enables | TACD-004 |
| Priority | P1 |
| Roadmap | `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md` |
| PRD | `docs/prd-tool-agnostic-capability-discovery.md` |
| Design Concept | `docs/ai/specs/.process/TACD-003-design-concept.md` |

### Source Evidence

- TACD-003 roadmap section: `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md`
- TACD PRD acceptance criteria AC-3.1 through AC-3.4: `docs/prd-tool-agnostic-capability-discovery.md`
- TACD-001 spike report and allowlist: `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- TACD-002 archive report: `.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md`
- Existing prerequisite script: `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh`
- Existing active docs: `speckit-pro/skills/speckit-autopilot/references/prerequisites.md`, `speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md`, `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md`, `speckit-pro/skills/speckit-coach/references/autopilot-guide.md`

### Success Criteria Summary

- [ ] AC-3.1: The autopilot prerequisite check replaces the hardcoded optional MCP server report with a generic, non-blocking capability advisory.
- [ ] AC-3.2: User-facing docs and coaching references explain that SpecKit Pro is tool-agnostic for research/context capabilities and degrades gracefully when fewer capabilities are installed.
- [ ] AC-3.3: Active guidance names capabilities, not tool IDs, except where a platform schema or exact file reference requires a concrete identifier.
- [ ] AC-3.4: Missing optional capabilities do not fail prerequisites; they only lower evidence confidence or require user escalation when no acceptable fallback exists.

### Scope Decisions From Grill Me

- Q1: Cover both prerequisite advisory behavior and active docs messaging.
- Q2: Use capability categories in active guidance; allow concrete IDs only for platform metadata, exact file references, or historical provenance.
- Q3: Missing optional capabilities should produce a non-blocking confidence advisory, not a setup failure.
- Q4: Include focused deterministic tests now; leave broad static/eval enforcement to TACD-004.
- Q5: Update active prerequisite/user-facing docs, not archives or generated duplicates.
- Q6: Keep as one implementation slice; estimator result was `{"estimated_loc":142,"suggested_slices":1,"status":"ok"}`.

---

## Phase 1: Specify

**When to run:** At the start of the feature specification. Focus on WHAT and
WHY, not implementation details. Output:
`specs/tacd-003-prerequisite-and-documentation-messaging/spec.md`

### Specify Prompt

```bash
/speckit-specify

## Feature: Prerequisite and Documentation Messaging

### Problem Statement
SpecKit Pro still has active prerequisite and user-facing messaging that presents
a fixed named optional-tool set for research/context capabilities. TACD-001
decided that active guidance should be capability-first, and TACD-002 updated
agent behavior to use the shared capability-discovery directive. TACD-003 must
align setup output and active docs with that implemented behavior.

### Users
- SpecKit Pro users running autopilot without optional research/context
  capabilities installed.
- SpecKit Pro users with stronger optional capabilities installed who should
  still benefit through discovery rather than hardcoded vendor preference.
- Maintainers and reviewers validating that active guidance no longer presents a
  fixed optional-tool contract.

### User Stories
1. As a user running autopilot, I want prerequisite checks to tell me whether
   research/context capability coverage may affect confidence without blocking
   setup when fallbacks exist.
2. As a user reading prerequisite docs, I want tool-agnostic capability guidance
   so I understand fallback behavior without being told to install a fixed
   optional-tool set.
3. As a maintainer, I want focused deterministic coverage for changed
   prerequisite output or active docs references so TACD-003 does not regress
   before TACD-004 adds broader enforcement.

### Functional Requirements
- Replace the hardcoded optional MCP report in `check-prerequisites.sh` with a
  generic non-blocking capability advisory.
- Preserve prerequisite success when optional capabilities are missing and an
  acceptable fallback path exists.
- Update active prerequisite, limitation, and coach/autopilot guidance to explain
  capability-first discovery and confidence/fallback behavior.
- Avoid concrete optional tool IDs in active guidance, except for platform
  metadata, exact file references, or historical provenance.
- Add or update focused deterministic tests for changed prerequisite output or
  active docs assertions.

### Constraints
- Do not rework active agent behavior already shipped in TACD-002.
- Do not add broad static/eval enforcement; TACD-004 owns that.
- Do not add installers, marketplace integration, or a new recommended tool set.
- Do not hand-edit generated payloads unless the source change requires a
  documented regeneration step.
- Keep the slice within the TACD-003 reviewability budget.

### Out of Scope
- Removing historical archive/changelog references.
- Rewriting fixture-only named-tool examples unless they represent active user
  guidance.
- Changing final Layer 3 eval expectations before TACD-004.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 10 |
| User Stories | 3 |
| Acceptance Criteria | 6 |
| G1 Gate | Passed: `spec.md` exists with 0 `[NEEDS CLARIFICATION]` markers |
| Reviewability Budget | Primary `docs/process`; secondary `harness/adapter`; 250 reviewable LOC; 6 production files; 9 total files; within budget |

### Files Generated

- [x] `specs/tacd-003-prerequisite-and-documentation-messaging/spec.md`
- [x] `specs/tacd-003-prerequisite-and-documentation-messaging/checklists/requirements.md`

### SpecKit Traceability Markers

Use markers such as `[US1]`, `[US2]`, `[FR-001]`, `[NEEDS CLARIFICATION]`,
`[P]`, and `[Gap]` so later phases can trace requirements through tasks.

---

## Phase 2: Clarify

**When to run:** After Specify, if any wording, surface, or verification boundary
can be interpreted multiple ways. Maximum 5 targeted questions.

### Clarify Prompts

#### Session 1: Advisory Wording

```bash
/speckit-clarify Focus on TACD-003 prerequisite advisory wording:
- Define the exact capability categories the prerequisite script should report.
- Confirm the advisory stays non-blocking when fallbacks exist.
- Clarify when confidence degradation should be surfaced versus when user
  escalation is needed.
- Ensure the language avoids concrete optional tool IDs except for approved
  metadata, exact file references, or historical provenance.
```

#### Session 2: Active Docs Boundary

```bash
/speckit-clarify Focus on TACD-003 active documentation scope:
- Identify which prerequisite, limitation, and coach/autopilot docs users read
  before running autopilot.
- Confirm archives, generated payloads, and fixture-only prose are out of scope
  unless they act as active guidance.
- Check that docs separate repo-specific guidance from platform/vendor behavior.
```

#### Session 3: Focused Verification Boundary

```bash
/speckit-clarify Focus on TACD-003 verification boundary:
- Decide which existing deterministic tests should assert changed prerequisite
  output or active docs wording.
- Keep broad named-tool enforcement, pointer coverage, and functional eval
  expectations assigned to TACD-004.
- Verify the test plan is enough for TACD-003 without duplicating TACD-004.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Advisory wording | 4 answered | Use categories `codebase context`, `library documentation`, `web/domain research`, and `source extraction`; emit one non-blocking `capability_coverage` advisory with `pass=true`; escalate only when no acceptable evidence path exists after fallback; concrete names allowed only for metadata, exact file references, generated source-derived duplicates, or historical provenance |
| 2 | Active docs boundary | 5 answered | Active scope is the four roadmap docs plus adjacent autopilot entrypoint summaries only when they repeat preflight or limitation wording; generated payloads are regenerated from source rather than hand-edited; archives/changelogs/fixtures stay out unless reused as current setup guidance or expected behavior; setup docs use the four Session 1 categories and point to the broader directive for agent behavior; platform behavior claims require official vendor evidence |
| 3 | Focused verification boundary | 5 answered | Extend `test-check-prerequisites.sh` for `capability_coverage` JSON behavior; add narrow assertions only for changed active docs; keep `test-generate-spec-index.sh` as Phase 1 blocker coverage only; defer Layer 3 eval expectation updates, Layer 5 pointer coverage, and broad named-tool enforcement to TACD-004; completion test plan is `bash -n` for the prerequisite script, focused Layer 4 tests, and the default deterministic suite before PR |

Consensus: Sessions 1, 2, and 3 had no unresolved items; consensus steps skipped.

---

## Phase 3: Plan

**When to run:** After spec and clarifications are finalized. Output:
`specs/tacd-003-prerequisite-and-documentation-messaging/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Shell: Bash with `set -euo pipefail`; use `jq` for JSON work.
- Docs: Markdown under `speckit-pro/skills/**/references/` and
  `speckit-pro/codex-skills/**/references/`.
- Tests: Shell-based deterministic tests under `tests/speckit-pro/`.
- Runtime: Claude Code and Codex plugin guidance, with shared source files and
  generated payloads treated carefully.

## Constraints
- Use the simplest explicit change that satisfies AC-3.1 through AC-3.4.
- Keep prerequisite output generic and capability-based.
- Missing optional capabilities must not fail prerequisites by themselves.
- Avoid hardcoded optional-tool preference wording in active guidance.
- Preserve concrete IDs only for platform metadata, exact file references, or
  historical/provenance contexts.
- Do not touch broad static/eval enforcement for TACD-004 except to leave clear
  handoff notes.

## Architecture Notes
- `check-prerequisites.sh` currently emits an informational MCP server check.
  Replace the fixed named-server report with a capability advisory that remains
  non-blocking.
- Active docs should explain capability-first discovery, fallback behavior, and
  confidence/evidence impact in vendor-neutral terms.
- Tests should be focused where existing prerequisite or docs assertions already
  live. Do not build a new broad scanner in TACD-003.
- The design concept selected "Advisory + docs", "Capabilities only",
  "Non-blocking confidence note", "Focused tests now", "Active prereq docs",
  and "One slice".

## Reviewability Budget
- TACD-003 roadmap budget: 142 projected reviewable LOC, 1 production file,
  5 total files, within budget.
- Setup gate warning: broader roadmap spans two primary surfaces; record but do
  not split TACD-003 unless implementation grows beyond plan.

## Candidate Files
- `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh`
- `speckit-pro/skills/speckit-autopilot/references/prerequisites.md`
- `speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md`
- `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md`
- `speckit-pro/skills/speckit-coach/references/autopilot-guide.md`
- Adjacent autopilot skill entrypoint summaries only when they repeat active
  preflight or limitation wording.
- Relevant focused tests under `tests/speckit-pro/`
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Declares 8 modified files and focused verification |
| `research.md` | Complete | Records advisory shape, category list, docs boundary, generated payload rule, and verification boundary |
| `data-model.md` | Not expected | No database or persistent data model planned |
| `contracts/` | Not expected | No API contract planned |
| `quickstart.md` | Complete | Lists implementation checks, verification commands, and PR packet checklist |

Plan gate: G3 passed with `plan.md` present and 0 unresolved markers.

Reviewability estimator: `estimate-reviewable-loc.sh plan.md` returned
`status=pass`, `projected=0`, `declared_files.modified=8`,
`declared_files.total_entries=8`. The plan records the current budget:
190 projected reviewable LOC, 1 production file, 8 total implementation files.

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan`. Validate both spec and plan together.

### Recommended Domains

#### 1. Error Handling Checklist

Why this domain: TACD-003 changes missing-capability behavior and confidence
fallback messaging. The main risk is accidentally turning an informational
condition into a blocker or hiding fallback quality.

```bash
/speckit-checklist error-handling

Focus on TACD-003 requirements:
- Missing optional research/context capabilities remain non-blocking when
  fallbacks exist.
- Advisory output explains confidence degradation without implying a fixed
  install requirement.
- User escalation is required only when no acceptable evidence path exists.
- Pay special attention to: consistency between `check-prerequisites.sh`, docs,
  and the design concept's "Non-blocking confidence note" decision.
```

#### 2. Integration Checklist

Why this domain: The messaging has to align Claude and Codex runtime guidance
without overclaiming platform behavior or hardcoding optional connector names.

```bash
/speckit-checklist integration

Focus on TACD-003 requirements:
- Claude and Codex prerequisite docs express the same capability-first contract.
- Concrete IDs appear only where platform metadata, exact file references, or
  historical provenance require them.
- Generated payloads are not hand-edited unless a source regeneration step is
  explicit.
- Pay special attention to: keeping repo guidance separate from official
  platform/vendor behavior.
```

#### 3. Reliability Checklist

Why this domain: The prerequisite check is a pre-flight health signal. Users
need transparent, stable output that preserves autopilot progress.

```bash
/speckit-checklist reliability

Focus on TACD-003 requirements:
- Prerequisite output remains deterministic and parseable.
- Existing setup checks still report actionable failures for true blockers.
- Focused tests cover changed advisory behavior.
- Pay special attention to: no broad TACD-004 enforcement logic landing early in
  TACD-003.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| error-handling | 14 | 2 found, 0 remaining | Added FR-012 and SC-006 for escalation boundary; expanded plan scope for adjacent active guidance |
| integration | 13 | 2 found, 0 remaining | Clarified Claude/Codex prerequisite parity and repo-vs-platform evidence boundary |
| reliability | 15 | 2 found, 0 remaining | Added FR-013/FR-014 and SC-007/SC-008 for JSON parseability and true-blocker preservation |
| Total | 42 | 6 found, 0 remaining | G4 passed: 0 `[Gap]` markers |

---

## Phase 5: Tasks

**When to run:** After checklists complete and gaps are resolved. Output:
`specs/tacd-003-prerequisite-and-documentation-messaging/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Use TDD where script output changes are involved.
- Keep tasks small and traceable to AC-3.1 through AC-3.4.
- Order work as: focused tests or fixtures, prerequisite script update, docs
  update, validation.
- Mark parallel-safe docs-only tasks with [P] only if they do not depend on the
  final script output wording.
- Reference `docs/ai/specs/.process/TACD-003-design-concept.md`, especially
  Goals, Non-goals, and Q1-Q6.

## Implementation Guidance
- Start with existing tests for `check-prerequisites.sh` or docs-reference
  assertions if present.
- Replace the named optional-tool report with generic capability advisory text.
- Update active prerequisite/user-facing docs in vendor-neutral language.
- Keep TACD-004 handoff explicit for broad static/eval enforcement.

## Constraints
- Do not edit archives or generated payloads by default.
- Do not add installers or marketplace integration.
- Do not create a broad scanner or eval update in this slice.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | 32 |
| Phases | 6 task phases; 5 planner increments |
| Parallel Opportunities | 4 docs-only tasks marked `[P]` (`T016`-`T019`) |
| User Stories Covered | 3 |
| G5 Gate | Passed: 32 tasks found |
| Reviewability Task Gate | Size-only `block`; continued to marker planning |
| Evidence | `specs/tacd-003-prerequisite-and-documentation-messaging/.process/reviewability/tasks-gate.json` |

---

## Atomicity Route

This section is filled after the Tasks phase / gate G5. The route is recorded
only here in the workflow file.

| Field | Value | Meaning |
|-------|-------|---------|
| Route | `one-navigable-PR` | Structural route from `atomicity-route.sh` |
| Releasable | `true` | No release-safety warning returned |
| Signals | `change-shape:modify-heavy` | Decisive detector finding |
| Warnings | None | No route warnings returned |
| Evidence | `specs/tacd-003-prerequisite-and-documentation-messaging/.process/reviewability/atomicity-route.json` | Repo-relative route evidence |

### Reviewability Marker Plan

| Field | Value |
|-------|-------|
| Gate status / mode / exit | `block` / `tasks` / `1` |
| Proceed decision | Valid current size-only block; continue to marker planning |
| Fingerprint status | Current in `autopilot-state.json` |
| Marker plan status | `collapsed` |
| Ordered marker IDs | `full-spec` |
| Review order | `full-spec` executes `T001`-`T032` |
| Checkpoints | Pending: `specs/tacd-003-prerequisite-and-documentation-messaging/.process/marker-plan/full-spec-checkpoint.json` |
| Warnings | Task heuristic estimates 1280 reviewable LOC and 46 referenced files |
| Final marker split | Placeholder: `hazard_collapsed` single-marker path |
| Packet validation | Pending |
| PR mappings | Pending |

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Constitution alignment: script safety, KISS/YAGNI, and focused test coverage.
2. Cross-artifact consistency across spec.md, plan.md, tasks.md, and
   docs/ai/specs/.process/TACD-003-design-concept.md.
3. Scope drift: no broad TACD-004 static/eval enforcement, no installer work, no
   historical archive cleanup.
4. Traceability: every task maps to AC-3.1 through AC-3.4 or an approved
   validation task.
5. Wording consistency: active guidance names capabilities, not fixed optional
   tool IDs, except for approved metadata/file/provenance contexts.
```

### Analyze Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | HIGH | Script-safety validation was implied but not explicit in `plan.md`, `tasks.md`, and `quickstart.md`, even though the constitution and clarify record require Bash syntax validation for the edited prerequisite script. | Added `bash -n speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` to the plan testing contract, T013, T023, and quickstart verification. |
| A2 | MEDIUM | Reviewability/file-count bookkeeping drifted across spec, plan, and workflow evidence after checklist remediation expanded the active guidance file set from 5 to 8 implementation files. | Reconciled `spec.md`, `plan.md`, and this workflow log to the current 8-file declared plan while preserving the G5 size-only task gate evidence. |
| A3 | MEDIUM | Task traceability for validation-only work was present through FR/SC references, but `tasks.md` did not explicitly show which non-AC tasks were approved validation tasks; T027 also claimed AC traceability in the summary without citing AC-3.1 through AC-3.4 on the task line. | Added AC-3.1 through AC-3.4 to T027, updated the AC coverage rows, and added an approved validation task mapping that preserves the 32-task count. |

G6 verification: marker counter returned `{"type":"findings","total":0,"critical":0,"high":0,"medium":0,"low":0}` after remediation, and `validate-gate.sh G6` returned pass with 0 CRITICAL/HIGH findings.

### Pre-Implementation Confidence Gate

| Field | Value |
|-------|-------|
| Mode | `advisory` |
| Status | `soft_skip` |
| Reason | No synthesizer confidence emit was present in the workflow file |
| Recommended action | Continue; no blocking confidence result exists |
| Evidence | `confidence-gate.sh docs/ai/specs/.process/TACD-003-workflow.md --mode advisory` returned `NO_DATA` |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed with no blocking gaps.

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD-First Where Behavior Changes

For prerequisite script behavior:
1. RED: Add or update a focused test for the generic non-blocking capability
   advisory.
2. GREEN: Update `check-prerequisites.sh` with the smallest explicit change.
3. REFACTOR: Keep JSON construction clear and shell-safe.
4. VERIFY: Run the focused test and relevant deterministic suite.

For docs:
1. Update active prerequisite/user-facing guidance after script wording is clear.
2. Keep language vendor-neutral and capability-first.
3. Preserve concrete IDs only for platform metadata, exact file references, or
   historical provenance.

## Pre-Implementation Setup
1. Verify branch: `git rev-parse --abbrev-ref HEAD`.
2. Verify worktree cleanliness except expected SpecKit artifacts: `git status --short`.
3. Re-read `docs/ai/specs/.process/TACD-003-design-concept.md`.
4. Re-read TACD-001/TACD-002 source evidence if wording is ambiguous.

## Implementation Notes
- The design concept's selected answers are load-bearing: Advisory + docs,
  Capabilities only, Non-blocking confidence note, Focused tests now, Active
  prereq docs, One slice.
- If implementation discovers the slice exceeds budget, stop and revisit the
  split decision instead of silently expanding scope.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation and focused tests | T001-T008 | Complete | RED confirmed on old optional-tool report; focused assertions added for `capability_coverage`, JSON shape, missing-optional success, true blocker preservation, and changed docs |
| Prerequisite advisory behavior | T009-T013 | Complete | `check-prerequisites.sh` now emits one successful `capability_coverage` advisory; `bash -n` and focused prerequisite test pass |
| Active docs messaging | T014-T021 | Complete | Active Claude/Codex prerequisite, limitation, coach, and autopilot guidance now uses capability-first fallback wording |
| Validation and PR packet | T022-T032 | Complete | Layer 4 and Layer 1 passed; Layer 1 regenerated source-derived `dist/` payload copies; PR packet evidence still generated in post-implementation |

---

## Post-Implementation Checklist

- [x] `specs/tacd-003-prerequisite-and-documentation-messaging/tasks.md` complete
- [x] Focused prerequisite/docs tests pass
- [x] `bash tests/speckit-pro/run-all.sh --layer 1` passes if structure changed
- [x] Source-derived `dist/` payload copies regenerated by Layer 1 payload validation
- [x] `bash tests/speckit-pro/run-all.sh` passed: 3163/3163
- [ ] `bash tests/speckit-pro/run-all.sh --layer 4` passes if script behavior changed
- [ ] `bash tests/speckit-pro/run-all.sh` passes before PR
- [ ] `git diff --check` passes
- [ ] Reviewability/final PR packet checks run per autopilot guidance
- [ ] Known TACD-004 handoffs are documented
- [ ] PR created and reviewed

---

## Lessons Learned

### What Worked Well

- Pending

### Challenges Encountered

- Pending

### Patterns to Reuse

- Pending

---

## Project Structure Reference

```text
speckit-pro/
  skills/
    speckit-autopilot/
      scripts/check-prerequisites.sh
      references/prerequisites.md
      references/plugin-limitations.md
    speckit-coach/
      references/autopilot-guide.md
  codex-skills/
    speckit-autopilot/
      references/prerequisites-codex.md
tests/
  speckit-pro/
docs/
  ai/
    specs/
      .process/TACD-003-design-concept.md
      .process/TACD-003-workflow.md
      tool-agnostic-capability-discovery-technical-roadmap.md
```

---

Template based on the shared SpecKit workflow template, populated for TACD-003.
