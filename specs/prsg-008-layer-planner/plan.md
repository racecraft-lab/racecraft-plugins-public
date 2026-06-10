# Implementation Plan: PRSG-008 Layer Planner

**Branch**: `prsg-008-layer-planner` | **Date**: 2026-06-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/prsg-008-layer-planner/spec.md`

## Summary

Implement a read-only Bash/JQ planner that accepts one feature directory, parses
`tasks.md` into deterministic semantic increments, and emits one versioned JSON
envelope on stdout. The planner stays independent from PRSG-007 routing logic;
`speckit-autopilot` owns the orchestration point after post-G5 atomicity route
recording and runs the planner only when the recorded route is exactly
`split-PR`.

The output contract uses `ok`, `invalid_plan`, and `input_error` statuses with
shared diagnostic objects, embedded increment/task payloads, and counts-only
advisory size metadata. PRSG-008 does not create branches, PR bodies, stacked
topology, or PRSG-006 budget verdicts.

## Technical Context

**Language/Version**: Bash compatible with the repository shell test suite on macOS and Linux

**Primary Dependencies**: `jq`, shell builtins, and existing repository test harnesses

**Storage**: N/A for `plan-layers.sh`; successful autopilot calls persist the returned JSON envelope to existing workflow state surfaces

**Testing**: Layer 4 shell tests under `tests/speckit-pro/layer4-scripts/`, Layer 1 structural validation, and default `bash tests/speckit-pro/run-all.sh`

**Target Platform**: Claude Code and Codex plugin consumers running local shell workflows

**Project Type**: Plugin shell harness and skill orchestration

**Performance Goals**: Complete planning for `tasks.md` files with up to 200 tasks in under 1 second on a typical development machine

**Constraints**: Read-only parser, deterministic JSON, concise stderr summaries, no subagents, no branch operations, no PRSG-009 topology, no LOC hints, no budget thresholds

**Scale/Scope**: One planner script, one output contract, Layer 4 fixtures/tests, and scoped autopilot prose/handoff updates

**Reviewability Budget**: Primary surface is the planner script plus Layer 4 fixtures/tests. Production script target is approximately 350 LOC. Expected implementation remains under the preset reviewability warning thresholds because extra files are fixture coverage, not additional runtime surfaces.

## Declared File Operations

The reviewability estimator reads this block before `tasks.md` exists.

- NEW speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- NEW specs/prsg-008-layer-planner/contracts/plan-layers.output.md
- NEW specs/prsg-008-layer-planner/contracts/plan-layers.schema.json
- NEW tests/speckit-pro/layer4-scripts/test-plan-layers.sh
- NEW tests/speckit-pro/layer4-scripts/fixtures/plan-layers/valid-real/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/plan-layers/missing-headings/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/plan-layers/invalid-dependency/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/plan-layers/dependency-cycle/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/plan-layers/invalid-reference/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/plan-layers/empty-increment/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/plan-layers/missing-references/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/plan-layers/checkbox-state/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/plan-layers/path-normalization/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/plan-layers/malformed-task/tasks.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-design gate result: PASS.

- **I. Plugin Structure Compliance**: PASS. The runtime script remains inside the existing `speckit-pro` skill tree, and tests remain outside the shipped plugin payload under `tests/speckit-pro/`.
- **II. Script Safety**: PASS by design. The new script must start with `#!/usr/bin/env bash`, use `set -euo pipefail`, quote variables, and pass `bash -n`.
- **III. Semantic Versioning**: PASS. PRSG-008 does not require manual version edits.
- **IV. Test Coverage Before Merge**: PASS by plan. The new shell script receives Layer 4 unit coverage and Layer 1 structural validation.
- **V. Conventional Commits**: PASS. No commit is created in this phase; any future PR title must use the repository conventional-commit format.
- **VI. KISS, Simplicity & YAGNI**: PASS. The parser is a single read-only script with explicit JSON output and no speculative branch or PR topology.

Reviewability preset result: PASS. The production runtime surface is the planner
script plus narrowly scoped autopilot handoff prose. Fixture count is intentional
because malformed-plan behavior is part of the contract.

Post-design gate result: PASS. The Phase 1 artifacts preserve the same scope,
contract, and fixture strategy without adding a second runtime system.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-008-layer-planner/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── plan-layers.output.md
│   └── plan-layers.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
speckit-pro/
├── skills/
│   └── speckit-autopilot/
│       ├── SKILL.md
│       └── scripts/
│           └── plan-layers.sh
└── codex-skills/
    └── speckit-autopilot/
        └── SKILL.md

tests/
└── speckit-pro/
    └── layer4-scripts/
        ├── test-plan-layers.sh
        └── fixtures/
            └── plan-layers/
                ├── valid-real/
                ├── missing-headings/
                ├── invalid-dependency/
                ├── dependency-cycle/
                ├── invalid-reference/
                ├── empty-increment/
                ├── missing-references/
                ├── checkbox-state/
                ├── path-normalization/
                └── malformed-task/
```

**Structure Decision**: Keep the parser in the existing autopilot skill script
directory so it ships with the orchestration skill, keep contracts with the spec
for PRSG-009 consumption, and keep fixtures/tests in the repository test suite
so they do not ship in plugin payloads.

## Phase 0 Research Decisions

See [research.md](research.md) for the decision log. The plan uses the accepted
Clarify decisions as resolved constraints: one versioned JSON envelope, embedded
increments and tasks, strict invalid-plan codes, advisory counts only, required
task headings, and autopilot execution only for `split-PR`.

## Phase 1 Design Decisions

See [data-model.md](data-model.md) for entities and validation rules, and
[contracts/plan-layers.output.md](contracts/plan-layers.output.md) with
[contracts/plan-layers.schema.json](contracts/plan-layers.schema.json) for the
consumer contract.

Autopilot integration belongs in the existing `speckit-autopilot` skill flow:

- After post-G5 atomicity route recording, inspect the recorded route.
- If route is `split-PR`, run `plan-layers.sh <feature-dir>` before Analyze or implementation prompt construction.
- On exit `0`, persist the full envelope to `autopilot-state.json`, summarize it in the workflow `## Layer Plan` section, and carry warnings forward.
- On exit `1`, stop before implementation with the fixed invalid-plan stop line from the spec and the planner diagnostics.
- On exit `2`, stop before implementation with a distinct input-error message and the planner diagnostics.
- For all other PRSG-007 routes, skip layer planning while preserving route warnings as context.

Data-integrity normalization decisions:

- Resolve the worktree anchor with `git -C "$feature_dir" rev-parse --show-toplevel`; all output paths are normalized relative to that root so a nested `.worktrees/...` checkout never leaks the parent checkout path.
- Normalize references by removing leading `./` and redundant `.` segments before validation. Do not emit absolute paths or paths that remain outside the worktree root after normalization; report those as `reference_not_found` warnings with the original reference string.
- De-duplicate `depends_on` by semantic increment ID, then emit dependencies in authoritative execution order. For `dependency_cycle`, choose the first affected increment in authoritative order and emit a single stable cycle path from that increment.
- Treat `[ ]`, `[x]`, and `[X]` as the only supported checkbox states. Unsupported task-like checkbox states fail as `malformed_task` and never produce a third task status.
- De-duplicate normalized `files` and `tests` arrays and emit them with `LC_ALL=C` lexical ordering so repeated runs cannot drift due to source-reference or filesystem enumeration order.

## Complexity Tracking

No constitution or reviewability violations are introduced by this plan.
