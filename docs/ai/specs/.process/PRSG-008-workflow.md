# SpecKit Workflow: PRSG-008 — Layer-planner: tasks.md to ordered increments

**Template Version**: 1.0.0
**Created**: 2026-06-09
**Purpose**: Autopilot-ready workflow for PRSG-008. The phase prompts below were enriched from the Grill Me interview captured in the Design Concept doc.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`$speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open Questions
live at:

```text
docs/ai/specs/.process/PRSG-008-design-concept.md
```

Re-read it before each phase. The design concept is the source of truth for
planner contract choices captured during setup.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the autopilot
> loop. Once autopilot begins, clarifications happen via `/speckit-clarify` and
> the consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | `spec.md` and requirements checklist created; G1 passed with 0 clarification markers. |
| Clarify | `/speckit-clarify` | In Progress | Pin JSON field names, invalid-plan diagnostics, and advisory metadata fields. |
| Plan | `/speckit-plan` | Pending | Design parser, schema contract, fixtures, and autopilot integration point. |
| Checklist | `/speckit-checklist` | Pending | Recommended domains: api-contracts, error-handling, data-integrity. |
| Tasks | `/speckit-tasks` | Pending | Generate TDD tasks for schema, fixtures, script, docs, and Codex parity. |
| Analyze | `/speckit-analyze` | Pending | Check design-concept/spec/plan/tasks consistency and downstream PRSG-009 contract safety. |
| Implement | `/speckit-implement` | Pending | Implement via Layer 4 RED to GREEN, then L1/L4/L5 validation. |

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | No `[NEEDS CLARIFICATION]` markers; output schema and failure policy are stated. |
| G2 | After Clarify | Planner JSON fields, diagnostic shape, and optional advisory metadata are pinned. |
| G3 | After Plan | Bash+jq approach, schema fixture, parser strategy, and autopilot hook are approved. |
| G4 | After Checklist | All `[Gap]` markers are addressed or explicitly scoped out. |
| G5 | After Tasks | Every FR has task coverage; malformed fixture cases are present before implementation. |
| G6 | After Analyze | No `CRITICAL`; no drift between design concept, spec, plan, and tasks. |
| G7 | After Implementation | Layer 4 planner tests, Layer 1 structural tests, and tool-scoping tests pass. |

---

## Prerequisites

### Constitution Validation

Verify against `.specify/memory/constitution.md` before G1:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| II. Script Safety | `plan-layers.sh` starts with `#!/usr/bin/env bash` and `set -euo pipefail`; variables quoted; `bash -n` clean; executable. | `bash -n speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` |
| IV. Test Coverage | New script has Layer 4 tests with realistic and malformed fixtures. | `bash tests/speckit-pro/run-all.sh --layer 4` |
| VI. KISS / YAGNI | Planner is read-only, independent of `atomicity-route.sh`, and does not create PR branches or PR bodies. | Plan review + code review |

**Constitution Check:** Initial spec gate verified at G1; script-safety and
test-coverage checks remain pending until implementation creates
`plan-layers.sh`.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-008 |
| **Name** | Layer-planner: tasks.md to ordered increments |
| **Branch** | `prsg-008-layer-planner` |
| **Feature directory** | `specs/prsg-008-layer-planner` |
| **Dependencies** | PRSG-007 complete: atomicity router emits route before planner wiring. |
| **Enables** | PRSG-009 multi-PR emission; PRSG-010 hatch hardening. |
| **Priority** | P1 — Phase 4 split-PR engine |
| **Budget** | Roadmap target ~350 production LOC. |

### Success Criteria Summary

- [ ] `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh <feature-dir>` reads `<feature-dir>/tasks.md`, writes no files, emits stable JSON to stdout, and writes concise diagnostics to stderr.
- [ ] Output includes ordered increments with semantic IDs (`foundation`, `us1`, `us2`, `polish`), ordered tasks, checkbox status, `[P]` parallel metadata, repo-relative file/test paths, source line numbers, dependencies, warnings, and advisory size metadata.
- [ ] Missing required headings, invalid dependency references, dependency cycles, or impossible ordering fail with exit `1` and machine-readable JSON diagnostics.
- [ ] Usage errors or unreadable inputs fail with exit `2`; successful plans exit `0`.
- [ ] Planner stays independent from `atomicity-route.sh`; `speckit-autopilot` orchestrates planner execution after PRSG-007 routing and before implementation.
- [ ] PRSG-008 creates no branches, PR bodies, restack metadata, or multi-PR topology; PRSG-009 owns emission.
- [ ] Contract lives under `specs/prsg-008-layer-planner/contracts/plan-layers.output.md` plus a schema fixture.
- [ ] Layer 4 tests cover at least one real SpecKit `tasks.md` fixture and malformed cases for missing headings, empty sections, cycles, invalid references, and path extraction.

---

## Phase 1: Specify

**When to run:** Start here. Focus on WHAT and WHY. Output: `specs/prsg-008-layer-planner/spec.md`.

### Specify Prompt

```bash
/speckit-specify

## Feature: Layer-planner — PRSG-008

### Problem Statement
Phase 4 needs an executable layer plan before PRSG-009 can emit stacked PRs.
PRSG-007 classifies whether split planning is relevant, but it does not parse
`tasks.md` into ordered increments. PRSG-008 ships that parser as a read-only
script: given a feature directory, emit a deterministic JSON layer plan from
`tasks.md`.

### Users
- `speckit-autopilot`, which runs the planner after atomicity routing and before
  implementation when split planning is relevant.
- PRSG-009, which will consume the planner contract to emit N PRs in dependency
  order.
- Maintainers reviewing task decomposition and malformed-plan diagnostics.

### User Stories
- [US1] Planner CLI: `plan-layers.sh <feature-dir>` reads `<feature-dir>/tasks.md`
  and emits stable JSON to stdout. It is read-only and independent from
  `atomicity-route.sh`.
- [US2] Increment parsing: parse `Foundation`, user-story phases, and `Polish`
  into ordered increments using explicit `## Dependencies & Execution Order` and
  `### Incremental Delivery` as authoritative, then validate against task order.
- [US3] Diagnostics and contracts: define a schema-backed output contract and fail
  malformed plans with structured JSON errors plus concise stderr summaries.
- [US4] Autopilot wiring: after PRSG-007 route recording, have `speckit-autopilot`
  run the planner before implementation when split planning is relevant; stop
  before implementation if planner validation fails.

### Key Decisions From Design Concept
- Stable JSON to stdout; diagnostics to stderr; no repository writes.
- Input is a feature directory, not stdin or only a tasks file.
- Exit codes: `0` success, `1` invalid plan, `2` usage/input error.
- Increment IDs are semantic: `foundation`, `us1`, `us2`, `polish`.
- Preserve `[P]` as `parallel: true` metadata inside the same increment.
- Preserve checkbox state and source line numbers for traceability.
- Missing file/test references are warnings, not failures.
- PRSG-008 is planner-only; branch/PR emission remains PRSG-009.

### Constraints
- Plain bash + jq only; honor constitution script-safety requirements.
- Roadmap budget target is ~350 production LOC.
- Parser must be deterministic and fixture-testable.
- Do not duplicate PRSG-006 reviewability gates or PRSG-007 routing logic.

### Out of Scope
- No branch creation, PR body generation, restacking, or multi-PR topology.
- No hard reviewability gate; advisory metadata only.
- No inference of missing file/test ownership from neighboring tasks.
- No direct mutation of workflow files by `plan-layers.sh`.
```

### Files Expected

- [x] `specs/prsg-008-layer-planner/spec.md`
- [x] `specs/prsg-008-layer-planner/checklists/requirements.md`

### Specify Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `spec.md` | Complete | 4 user stories, 20 functional requirements, 8 measurable success criteria. |
| `checklists/requirements.md` | Complete | All quality and readiness checks passed. |
| G1 | Passed | `validate-gate.sh G1 specs/prsg-008-layer-planner` returned pass with 0 markers. |

---

## Phase 2: Clarify

**When to run:** After Specify if any planner contract detail remains ambiguous.

### Clarify Prompts

#### Session 1: JSON contract and schema

```bash
/speckit-clarify Focus on the plan-layers JSON contract: exact top-level fields,
increment object fields, task object fields, status enums, warning/error object
shape, semantic increment IDs, source-line format, and whether advisory size
metadata includes LOC hints or only task/file counts. Align with PRSG-009 as the
downstream consumer.
```

#### Session 2: Invalid-plan diagnostics

```bash
/speckit-clarify Focus on invalid tasks.md behavior: missing required headings,
empty increment sections, invalid dependency references, dependency cycles,
missing files/tests, malformed checkbox tasks, and how each maps to exit 1 vs
warnings. Pin the JSON error codes and stderr summaries.
```

#### Session 3: Autopilot hook point

```bash
/speckit-clarify Focus on speckit-autopilot wiring: after atomicity route, before
implementation, only when split planning is relevant. Define how planner output is
carried into implementation context and what exact stop message appears when the
planner returns exit 1.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | JSON contract and schema | Pending | |
| 2 | Invalid-plan diagnostics | Pending | |
| 3 | Autopilot hook point | Pending | |

---

## Phase 3: Plan

**When to run:** After the spec and clarify decisions are stable. Output: `specs/prsg-008-layer-planner/plan.md`.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Runtime: Bash scripts with jq for JSON.
- Test framework: shell Layer 4 tests under `tests/speckit-pro/layer4-scripts/`.
- Structural gates: Layer 1 validation under `tests/speckit-pro/layer1-structural/`.
- Plugin surfaces: `speckit-pro/skills/speckit-autopilot/` and Codex mirror prose where behavior changes are described.

## Architecture Notes
- Implement `plan-layers.sh` as a read-only parser in
  `speckit-pro/skills/speckit-autopilot/scripts/`.
- Input is a feature directory; `tasks.md` is resolved as `<feature-dir>/tasks.md`.
- Parse task headings into increments: `foundation`, `us1...usN`, `polish`.
- Use explicit `## Dependencies & Execution Order` and `### Incremental Delivery`
  sections as authoritative DAG input, then validate against task order.
- Preserve `[P]` as task metadata, not a separate increment.
- Normalize extracted file/test paths to repo-relative paths.
- Emit structured invalid-plan JSON to stdout and concise human summaries to stderr.
- Keep `plan-layers.sh` independent from `atomicity-route.sh`; orchestration lives in
  the autopilot skill.

## Reviewability Budget
- Primary surface: planner script + L4 fixtures/tests.
- Target: ~350 production LOC.
- Keep schema/contract docs review-visible in `specs/prsg-008-layer-planner/contracts/`.
- No PRSG-009 branch topology or PR body emission in this spec.

## Contract Artifacts
- `contracts/plan-layers.output.md`
- JSON schema fixture for planner output.
- Positive fixture from a real SpecKit `tasks.md`.
- Malformed fixtures: missing headings, cycles, invalid references, empty sections,
  missing file/test paths, and checkbox-state preservation.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Pending | |
| `research.md` | Pending | Parser and schema decisions if needed. |
| `data-model.md` | Pending | Increment, task, dependency edge, diagnostic objects. |
| `contracts/plan-layers.output.md` | Pending | Schema-backed contract. |
| `quickstart.md` | Pending | Manual planner runs and expected outputs. |

---

## Phase 4: Domain Checklists

**When to run:** After Plan.

### Recommended Domains

| Domain | Why |
|--------|-----|
| api-contracts | The planner JSON schema is a downstream contract for PRSG-009. |
| error-handling | Exit codes, malformed-plan errors, and stderr diagnostics are load-bearing. |
| data-integrity | DAG ordering, source line traceability, path normalization, and task status preservation must be deterministic. |

### Checklist Prompts

```bash
/speckit-checklist api-contracts

Focus on PRSG-008 requirements:
- JSON contract fields and enum values are complete and stable.
- Error object shape is machine-readable and fixture-testable.
- PRSG-009 can consume the output without re-parsing task prose.
```

```bash
/speckit-checklist error-handling

Focus on PRSG-008 requirements:
- Missing headings, invalid references, cycles, unreadable inputs, and malformed tasks
  map to the correct exit codes.
- Invalid plans produce structured JSON errors to stdout and concise stderr summaries.
- Missing file/test references are warnings, not failures.
```

```bash
/speckit-checklist data-integrity

Focus on PRSG-008 requirements:
- Dependency DAG is deterministic and cycle-safe.
- Source line numbers and checkbox state are preserved.
- Repo-relative path normalization is unambiguous across worktrees.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| api-contracts | Pending | Pending | |
| error-handling | Pending | Pending | |
| data-integrity | Pending | Pending | |

---

## Phase 5: Tasks

**When to run:** After checklist gaps are resolved. Output: `specs/prsg-008-layer-planner/tasks.md`.

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Start with RED Layer 4 fixtures and schema validation before implementing parser logic.
- Add malformed fixtures for missing headings, invalid dependencies, dependency cycles,
  empty sections, missing file/test references, and checkbox-state preservation.
- Implement the script in small increments: CLI/input validation, heading discovery,
  task extraction, dependency parsing, DAG validation, path/test extraction, JSON output.
- Add autopilot prose/wiring tasks after the script contract is green.
- Mirror user-facing behavior changes into Codex skill files.

## Required Task Coverage
- `plan-layers.sh` script safety and executable bit.
- Contract doc and schema fixture under `specs/prsg-008-layer-planner/contracts/`.
- Layer 4 test file and committed fixtures.
- Autopilot integration after atomicity route and before implementation.
- No branch/PR emission tasks in this spec.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | Pending |
| Phases | Pending |
| Parallel Opportunities | Pending |
| User Stories Covered | Pending |

---

## Atomicity Route

This workflow is downstream of PRSG-007. After Tasks/G5, the autopilot records the
actual PRSG-008 route here by running:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/prsg-008-layer-planner
```

| Field | Value | Meaning |
|-------|-------|---------|
| Route | Pending | Expected likely `split-PR` or `one-navigable-PR` depending on task seams. |
| Releasable | Pending | `true` unless destructive/concurrency signatures appear. |
| Signals | Pending | Detector findings from PRSG-007. |
| Warnings | Pending | Release-safety warnings, if any. |

---

## Layer Plan

After the atomicity route is recorded, PRSG-008 adds and wires the planner. The
expected manual command for validation is:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh specs/prsg-008-layer-planner
```

Planner output is read-only JSON to stdout. If atomicity routing says split
planning is relevant and this command exits `1`, autopilot must stop before
implementation and surface the planner diagnostics.

---

## Phase 6: Analyze

**When to run:** After generating tasks.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Consistency between Design Concept Q1-Q24, spec.md, plan.md, tasks.md, and the
   planner contract.
2. Whether malformed-plan behavior maps cleanly to exit 1 vs exit 2.
3. Whether PRSG-008 remains planner-only and avoids PRSG-009 branch/PR emission.
4. Whether PRSG-009 can consume the output without inventing missing structure.
5. Whether Codex mirror prose carries the same behavior as the Claude skill surface.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| Pending | | | |

---

## Phase 7: Implement

**When to run:** After Analyze passes.

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD First
1. Write RED Layer 4 tests and fixtures for the planner contract.
2. Implement the smallest parser slice that makes each fixture green.
3. Keep `plan-layers.sh` read-only: stdout JSON, stderr diagnostics, no file writes.
4. Wire autopilot after PRSG-007 route recording and before implementation.
5. Mirror behavior prose into Codex surfaces.
6. Verify Layer 4, then Layer 1, then the default suite.

## Validation Commands
- `bash tests/speckit-pro/run-all.sh --layer 4`
- `bash tests/speckit-pro/run-all.sh --layer 1`
- `bash tests/speckit-pro/run-all.sh`

## Implementation Notes
- Do not call `atomicity-route.sh` inside `plan-layers.sh`.
- Do not create PR branches or PR bodies.
- Preserve checkbox state and source line numbers.
- Treat missing file/test paths as warnings.
- Fail dependency cycles with structured diagnostics.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | Pending | 0 | Contract and fixtures. |
| Parser | Pending | 0 | CLI, headings, tasks, DAG, path/test extraction. |
| Autopilot wiring | Pending | 0 | Run after atomicity route, before implementation. |
| Polish | Pending | 0 | Docs, Codex mirror, validation. |

---

## Post-Implementation Checklist

- [ ] `plan-layers.sh` passes `bash -n` and is executable.
- [ ] Layer 4 planner tests pass.
- [ ] Layer 1 structural validation passes.
- [ ] No workflow placeholders or unresolved contract tokens remain.
- [ ] The planner is read-only under fixture runs.
- [ ] PRSG-009 deferred branch/PR emission remains out of scope.

---

## Project Structure Reference

```text
speckit-pro/
  skills/speckit-autopilot/scripts/plan-layers.sh
  skills/speckit-autopilot/SKILL.md
  codex-skills/speckit-autopilot/SKILL.md
tests/speckit-pro/layer4-scripts/test-plan-layers.sh
tests/speckit-pro/layer4-scripts/fixtures/plan-layers/
specs/prsg-008-layer-planner/
  SPEC-MOC.md
  spec.md
  plan.md
  tasks.md
  contracts/plan-layers.output.md
```
