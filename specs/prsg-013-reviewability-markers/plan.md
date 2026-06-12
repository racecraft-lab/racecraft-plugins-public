# Implementation Plan: Non-Stopping Reviewability Markers

**Branch**: `prsg-013-reviewability-markers` | **Date**: 2026-06-12 | **Spec**: `specs/prsg-013-reviewability-markers/spec.md`

**Input**: Feature specification from `specs/prsg-013-reviewability-markers/spec.md`

## Summary

Autopilot will treat parseable reviewability sizing results as PR-shaping input, persist a top-level `pr_marker_plan`, implement and checkpoint in marker order, and let final PR emission consume those markers instead of stopping on full-diff size alone. Correctness and safety gates remain blocking, while valid size-only `warn` or `block` results become structured evidence for scoped PR packets.

## Technical Context

**Language/Version**: Bash 4+ shell scripts, Markdown skill guidance, JSON Schema 2020-12

**Primary Dependencies**: `bash`, `jq`, `git`, `gh` at PR-emission boundaries, existing SpecKit Pro shell harness

**Storage**: Repository files only: `autopilot-state.json`, workflow evidence blocks, JSON contract schemas, and generated PR packet artifacts

**Testing**: Layer 4 shell fixtures, Layer 3 functional evals, structural validation, and default `bash tests/speckit-pro/run-all.sh`

**Target Platform**: SpecKit Pro plugin marketplace surfaces for Claude and Codex

**Project Type**: Shell and Markdown plugin automation with JSON state contracts

**Performance Goals**: Deterministic marker planning and PR-emission decisions in shell fixtures; no network dependency before `gh`-based PR emission

**Constraints**: Reviewability sizing must not stop implementation for a valid spec; correctness and safety gates still stop; `reviewability-gate.sh tasks` remains caller-compatible unless a compatibility-safe extension is proven; marker state is persisted in `autopilot-state.json` and workflow evidence, not as authoritative `tasks.md` mutations; implementation checkpoints preserve marker order

**Scale/Scope**: Three user stories, sixteen functional requirements, one top-level marker-plan state object, one final-backstop marker-aware outcome, and one Layer 3 eval covering the end-to-end behavior

**Reviewability Budget**: Primary surface `harness/adapter`; secondary surfaces `docs/process` and `scheduler/runtime`; projected full-feature reviewable LOC 700-1,200; projected production files 8-10; projected total files 16-18; budget result is warning accepted with required marker-based split evidence. The implementation must produce scoped PR markers whose individual review scopes are expected to stay below single-PR review limits, or carry structured warnings when no safe subdivision exists.

## Declared File Operations

- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/post-implementation.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md
- NEW speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/contracts/final-reviewability-gate-state.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/contracts/multi-pr-emission-state.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md
- MODIFIED tests/speckit-pro/layer4-scripts/test-plan-layers.sh
- MODIFIED tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh
- MODIFIED tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
- MODIFIED tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json
- MODIFIED tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| Plugin Structure Compliance | PASS | Changes stay inside the existing `speckit-pro/` plugin layout and its test suite. |
| Script Safety | PASS | Script changes must preserve `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, checked results, executability, and `bash -n` validity. |
| Semantic Versioning | PASS | No manual plugin version edit is planned; release-please remains authoritative. |
| Test Coverage Before Merge | PASS | Layer 4 fixtures cover marker planning, final backstop, and multi-PR emission; Layer 3 functional eval covers the non-stopping autopilot contract. |
| Conventional Commits | PASS | No commit is created by this phase; implementation PR title must use a valid conventional commit. |
| KISS, Simplicity & YAGNI | PASS | The design adds one persisted marker-plan contract and extends existing shell/guidance surfaces instead of introducing a new orchestration layer. |
| Reviewability Budget | WARNING ACCEPTED | The full feature exceeds single-PR review budget, but the split decision is to keep PRSG-013 as one spec and require marker-based implementation checkpoints and PR emission. |

**Primary review surface**: `harness/adapter`

**Secondary review surfaces**: `docs/process`, `scheduler/runtime`

**Split decision**: Keep PRSG-013 as one prerequisite spec because the behavior is one product outcome. Implementation and emission must use markers for Foundation, each user story, and safe in-story subdivisions. If a story has no safe subdivision, the original story marker continues with a structured warning. If hazard collapse is required, implementation still checkpoints original markers and emits one full-spec PR with marker evidence.

**PR review packet source**: Marker-aware PR packets must include what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, rollback or feature-flag notes, and structured marker warnings.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-013-reviewability-markers/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── pr-marker-plan.schema.json
│   └── marker-split-result.schema.json
├── checklists/
│   └── requirements.md
├── SPEC-MOC.md
└── spec.md
```

### Source Code (repository root)

```text
speckit-pro/
├── skills/speckit-autopilot/
│   ├── SKILL.md
│   ├── contracts/
│   │   ├── pr-marker-plan.schema.json
│   │   ├── final-reviewability-gate-state.schema.json
│   │   └── multi-pr-emission-state.schema.json
│   ├── references/
│   │   ├── phase-execution.md
│   │   ├── post-implementation.md
│   │   └── workflow-file-protocol.md
│   └── scripts/
│       ├── plan-layers.sh
│       ├── final-reviewability-backstop.sh
│       └── multi-pr-emission.sh
└── codex-skills/speckit-autopilot/
    ├── SKILL.md
    └── references/
        ├── phase-execution-codex.md
        └── post-implementation-codex.md

tests/speckit-pro/
├── layer4-scripts/
│   ├── test-plan-layers.sh
│   ├── test-final-reviewability-backstop.sh
│   └── test-multi-pr-emission.sh
└── layer3-functional/
    ├── evals/speckit-autopilot-evals.json
    └── codex-evals/speckit-autopilot-evals.json
```

**Structure Decision**: Extend the existing autopilot shell/guidance surfaces and their Codex mirrors. Marker planning belongs with layer planning because it is derived from generated task structure; final backstop and multi-PR emission consume the persisted marker plan instead of inferring boundaries from one mixed diff.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Full-feature reviewability warning above single-PR budget | The behavior spans task gate handling, marker persistence, implementation ordering, final backstop, and PR emission, which must agree on one contract. | Splitting into separate specs would leave intermediate states where sizing is non-stopping but PR emission cannot consume durable markers, or PR emission expects markers that earlier phases do not produce. |
| Marker-plan state contract added | PR emission needs durable, fingerprinted evidence that survives resume and cannot rely on transient prose edits. | Rewriting `tasks.md` with marker comments would make generated task prose authoritative state and would be harder to validate for staleness. |
