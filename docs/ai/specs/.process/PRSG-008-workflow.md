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
| Clarify | `/speckit-clarify` | Complete | JSON envelope, diagnostic codes, and autopilot hook behavior pinned; G2 passed. |
| Plan | `/speckit-plan` | Complete | Parser approach, contract artifacts, fixtures, and autopilot hook design created; G3 passed. |
| Checklist | `/speckit-checklist` | Complete | api-contracts, error-handling, and data-integrity checklists complete; G4 passed. |
| Tasks | `/speckit-tasks` | Complete | 45 TDD-first tasks generated across 7 phases; G5 passed. |
| Analyze | `/speckit-analyze` | Complete | Design-concept/spec/plan/tasks consistency checked; G6 passed after remediation. |
| Implement | `/speckit-implement` | Complete | Layer 4 RED to GREEN completed; G7 and post-review validation passed. |

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

**Constitution Check:** Initial spec gate verified at G1. Script-safety and
test-coverage checks passed at G7 with `bash -n`, Layer 4, Layer 1, and the
default deterministic suite.

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

- [x] `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh <feature-dir>` reads `<feature-dir>/tasks.md`, writes no files, emits stable JSON to stdout, and writes concise diagnostics to stderr.
- [x] Output includes ordered increments with semantic IDs (`foundation`, `us1`, `us2`, `polish`), ordered tasks, checkbox status, `[P]` parallel metadata, repo-relative file/test paths, source line numbers, dependencies, warnings, and advisory size metadata.
- [x] Missing required headings, invalid dependency references, dependency cycles, or impossible ordering fail with exit `1` and machine-readable JSON diagnostics.
- [x] Usage errors or unreadable inputs fail with exit `2`; successful plans exit `0`.
- [x] Planner stays independent from `atomicity-route.sh`; `speckit-autopilot` orchestrates planner execution after PRSG-007 routing and before implementation.
- [x] PRSG-008 creates no branches, PR bodies, restack metadata, or multi-PR topology; PRSG-009 owns emission.
- [x] Contract lives under `specs/prsg-008-layer-planner/contracts/plan-layers.output.md` plus a schema fixture.
- [x] Layer 4 tests cover at least one real SpecKit `tasks.md` fixture and malformed cases for missing headings, empty sections, cycles, invalid references, and path extraction.

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
| 1 | JSON contract and schema | 5 | Accepted a single versioned envelope, embedded increment/task objects, shared diagnostic shape, `todo`/`done` task status enum, and counts-only advisory size metadata. |
| 2 | Invalid-plan diagnostics | 5 | Required dependency and delivery headings; empty declared increments, duplicate IDs, malformed tasks, cycles, and contradictory/unknown ordering fail exit 1; missing refs remain warnings. |
| 3 | Autopilot hook point | 5 | Planner runs immediately after post-G5 atomicity route recording and before Analyze only for route `split-PR`; successful envelopes persist to state, workflow gets a summary, and exit 1/2 stop before implementation. |

### Consensus Resolution Log

| Phase | Item | Round | Routed Categories | Outcome | Analysts Used |
|-------|------|-------|-------------------|---------|---------------|
| Clarify Session 1 | Advisory size metadata LOC hints vs counts only | 1 | `[spec, codebase]` | Counts-only metadata chosen for v1; no LOC hints, thresholds, or PRSG-006 verdict semantics. | spec-context-analyst, codebase-analyst |

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
| `plan.md` | Complete | Bash/JQ parser approach, declared file operations, constitution check, and autopilot handoff design. |
| `research.md` | Complete | 8 parser, schema, diagnostics, fixture, and orchestration decisions. |
| `data-model.md` | Complete | LayerPlan, Increment, Task, Diagnostic, and autopilot state model. |
| `contracts/plan-layers.output.md` | Complete | Human-readable planner output contract. |
| `contracts/plan-layers.schema.json` | Complete | Schema parsed successfully with `jq empty`. |
| `quickstart.md` | Complete | Valid, deterministic, invalid, warning, input-error, and autopilot handoff scenarios. |
| G3 | Passed | `validate-gate.sh G3 specs/prsg-008-layer-planner` passed; reviewability estimator returned `status=pass`. |

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
| api-contracts | 30 | 4 found, 4 fixed, 0 open | FR-010a, FR-014k, FR-014l, FR-014m |
| error-handling | 29 | 0 found, 0 open | FR-014g, FR-014h, FR-015, FR-018 |
| data-integrity | 27 | 3 found, 3 fixed, 0 open | FR-014n, FR-014o, FR-014p |

### Addressing Gaps

- API contract gaps were closed by adding input-error diagnostic codes, semantic
  increment ID grammar, diagnostic severity constraints, and closed per-code
  `details` payload requirements.
- Data-integrity gaps were closed by adding deterministic `depends_on` and cycle
  path ordering, supported checkbox-state rules, and repo-relative path
  normalization rules based on the Git repository root.
- Error-handling had no remaining gaps after review.
- G4 passed with `0 [Gap]` markers in `spec.md` and `plan.md`.

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
| Total Tasks | 45 |
| Phases | 7 |
| Parallel Opportunities | 18 |
| User Stories Covered | US1, US2, US3, US4 |
| G5 | Passed: `validate-gate.sh G5 specs/prsg-008-layer-planner` found 45 tasks. |

---

## Atomicity Route

This workflow is downstream of PRSG-007. After Tasks/G5, the autopilot records the
actual PRSG-008 route here by running:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/prsg-008-layer-planner
```

| Field | Value | Meaning |
|-------|-------|---------|
| Route | `one-navigable-PR` | Planner execution is not required for this autopilot run because split planning is relevant only for `split-PR`. |
| Releasable | `true` | No destructive or concurrency-sensitive release warning was emitted. |
| Signals | `change-shape:modify-heavy` | PRSG-007 structural detector output. |
| Warnings | `[]` | No release-safety warnings. |

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

**Current run:** Skipped. The recorded route is `one-navigable-PR`, so
`plan-layers.sh` is not required before Analyze/Implementation for this run.

**Implemented behavior:** For future `split-PR` routes, autopilot now runs
`plan-layers.sh` immediately after route recording and before Analyze or
implementation. Exit `0` persists the full layer-plan envelope and carries
warnings forward; exit `1`/`2` stops before implementation with planner
diagnostics. Non-split routes keep the explicit skipped state.

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
| A1 | Medium | SC-002 performance target had no explicit task coverage. | Added generated 200-task performance coverage to T003, T015, T042, and the Success Criteria Coverage table in `tasks.md`. |
| A2 | Medium | `plan.md` fixture inventory omitted `invalid-dependency` and `malformed-task` fixtures required by `tasks.md`. | Added both fixture paths to declared file operations and the project tree in `plan.md`. |
| A3 | High | Planner schema did not enforce status-specific invariants for `ok`, `invalid_plan`, and `input_error`. | Added contract Status Invariants and Draft-07 conditional schema constraints. |
| A4 | Medium | Reviewability file-count projection in `spec.md` was stale versus the fixture-heavy plan. | Updated production and total file projections to match planned runtime/prose plus fixture/contract/test files. |

**Analyze Result:** All findings remediated. G6 passed with `0 CRITICAL/HIGH`
markers. Schema JSON parses with `jq empty`.

📊 Confidence: 0.94

- Task understanding: 0.95
- Approach clarity: 0.94
- Requirements alignment: 0.94
- Risk assessment: 1.00
- Completeness: 0.89

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
| Foundation | T001-T020 | 20 | Contract, fixtures, and RED harness landed; RED evidence progressed from `6/15` to `8/50` before production script creation. |
| Parser | T021-T036 | 16 | `plan-layers.sh` implements input errors, stable envelope, ordered increments, references, warnings, invalid-plan diagnostics, and schema-shaped output. |
| Autopilot wiring | T037-T040 | 4 | Claude and Codex skill surfaces run planner only for `split-PR`; Codex eval id 30 covers stop/continue/skip behavior. |
| Polish | T041-T045 | 5 | Validation evidence captured below; PRSG-009 branch/PR emission remains out of scope. |

### Validation Evidence

| Command | Result |
|---------|--------|
| `bash -n speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` | Passed |
| `test -x speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` | Passed |
| `bash tests/speckit-pro/layer4-scripts/test-plan-layers.sh` | Passed: `66/66` |
| `bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh specs/prsg-008-layer-planner` | Passed: `status=ok`, 6 increments, 45 tasks |
| `bash tests/speckit-pro/run-all.sh --layer 4` | Passed: `1029/1029` |
| `bash tests/speckit-pro/run-all.sh --layer 1` | Passed: `887/887` |
| `bash tests/speckit-pro/run-all.sh` | Passed: `2106/2106` |

### Traceability

| Requirement area | Evidence |
|------------------|----------|
| Stable planner envelope and read-only behavior | `plan-layers.sh`, contract schema, and `test-plan-layers.sh` valid/determinism/read-only assertions. |
| Ordered increments and task metadata | `valid-real`, `checkbox-state`, and generated 200-task fixture assertions. |
| Warning behavior | `invalid-reference` and `missing-references` fixtures exit `0` with structured warnings. |
| Invalid-plan and input-error diagnostics | `missing-headings`, `invalid-dependency`, `dependency-cycle`, `empty-increment`, `malformed-task`, and input-error assertions. |
| Autopilot handoff | Claude/Codex skill prose and Codex eval id 30 cover `split-PR` run, warning carry-forward, exit `1`/`2` stop, and non-split skip. |
| PRSG-009 non-goals | Planner and skill prose explicitly avoid branch creation, PR body generation, restacking, and stacked-PR topology. |

Reviewability-Exception: infra

This exception is scoped to the fixture-heavy contract and package-mirror
footprint for PRSG-008. The diff gate reports `reviewable_loc=0` and
`production_files=0`; the block is total-file-count driven.

---

## Post-Implementation Checklist

- [x] `plan-layers.sh` passes `bash -n` and is executable.
- [x] Layer 4 planner tests pass.
- [x] Layer 1 structural validation passes.
- [x] No workflow placeholders or unresolved contract tokens remain.
- [x] The planner is read-only under fixture runs.
- [x] PRSG-009 deferred branch/PR emission remains out of scope.

### Post-Implementation Results

| Item | Result |
|------|--------|
| Doctor Extension Check | Passed: 5 PASS, 0 WARN, 0 FAIL. |
| Verify Implementation | Initial verify found one critical, one high, and two medium issues. Follow-up verify found the Python helper still present, the live PRSG-008 tasks plan failing, and non-happy-path schema validation incomplete. Remediation replaced the planner with Bash parsing plus `jq` JSON assembly, normalized paths from the target feature repo root, taught Foundation to cover Setup/Foundational task sections, asserted `path-normalization`, and schema-validates invalid-plan, warning, path-normalization, and input-error outputs. |
| Verify Tasks Phantom Check | Passed: 45/45 completed tasks verified; report written to `specs/prsg-008-layer-planner/verify-tasks-report.md`. |
| Code Review | Skipped: review extension not installed. |
| Integration Suite | Passed: `bash tests/speckit-pro/run-all.sh` reported `2106/2106`. |
| Cleanup | Skipped: cleanup extension not installed. |
| Reviewability Diff Gate | Passed via infra exception: `reviewable_loc=0`, `production_files=0`, `total_files=40`, `exception_honored=true`. |
| Self-Review | Completed; see `## Self-Review`. |
| UAT Runbook Generation | Completed: `specs/prsg-008-layer-planner/.process/uat-runbook.md` generated and locally polished because `uat-runbook-author` is not registered in this Codex session. |
| PR Body Generation | Completed: generated via `generate-pr-body.sh`, filled in plain-English sections, and verified `speckit-pro-review-packet-source` plus `## UAT Runbook`. |
| PR Creation | Completed: https://github.com/racecraft-lab/racecraft-plugins-public/pull/138 |
| Review Remediation | Completed: remediated 4 Copilot comments by fixing UAT diagnostic wording, contradictory-order details, longer cycle detection, and redundant `.` path normalization. Re-ran focused planner tests, Layer 4, Layer 1, privacy scan, and default suite. |
| Retrospective | Completed: `specs/prsg-008-layer-planner/retrospective.md` records completion, review remediation, validation evidence, and follow-up lessons. |

## Self-Review

1. **Tests executed?** Yes. Repository build/typecheck/lint/unit/integration
   commands are not defined for this shell-test plugin repo. Executed and
   passed: `bash tests/speckit-pro/layer4-scripts/test-plan-layers.sh`
   (`66/66`), direct live-feature planner run (`status=ok`, 6 increments,
   45 tasks), `bash tests/speckit-pro/run-all.sh --layer 4` (`1029/1029`),
   `bash tests/speckit-pro/run-all.sh --layer 1` (`887/887`), privacy scan
   (`9/9`), and `bash tests/speckit-pro/run-all.sh` (`2106/2106`).
2. **Edge cases?** Covered. Schema and valid/read-only coverage is in
   `tests/speckit-pro/layer4-scripts/test-plan-layers.sh:851`; checkbox and
   `[P]` metadata at `:890`; invalid-plan diagnostics at `:906`; warning
   diagnostics at `:961`; input errors at `:993`; script safety at `:1070`;
   determinism, generated 200-task performance, and read-only checks at
   `:1081`. Non-happy-path outputs now call the actual schema validator.
3. **Requirements matched?** Yes. `tasks.md` maps every FR to completed
   tasks in `specs/prsg-008-layer-planner/tasks.md:234`, and verify-tasks
   reported 45/45 completed tasks verified with 0 flagged items.
4. **Follow-up?** No `[TODO]`, `[DEFERRED]`, or `[OUT-OF-SCOPE]` markers were
   found in `spec.md`, `plan.md`, `tasks.md`, or this workflow. PRSG-009
   branch/PR emission remains the documented downstream non-goal.

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
