# Implementation Plan: Harness Surface Inventory and Gap Taxonomy

**Branch**: `hrns-001-harness-surface-inventory-gap-taxonomy` | **Date**: 2026-07-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/hrns-001-harness-surface-inventory-gap-taxonomy/spec.md`

## Summary

Create one source-grounded Markdown taxonomy at
`docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`. The artifact will
inventory current SpecKit Pro harness surfaces, classify retained gaps with
stable `HRNS-GAP-###` rows, separate authoritative evidence from generated or
derived copies, record external-candidate evidence as reference-only, and prove
coverage through AC-1.1 through AC-1.10 crosswalks. HRNS-001 stays docs/process
only: no runtime registry, dependency adoption, validator code, generated
payload edits, installed-cache edits, or vendored changes.

## Technical Context

**Language/Version**: N/A — Markdown planning artifact only

**Primary Dependencies**: None; external tools are reference candidates only

**Storage**: Repository Markdown files

**Testing**: `git diff --check`, runner `generate-spec-index-check`, targeted
placeholder/link review, and `python3 tests/speckit-pro/run-all.py --layer 1`
when final changed paths warrant structural validation

**Target Platform**: Repository documentation/process workflow

**Project Type**: docs/process

**Performance Goals**: N/A; artifact reviewability and traceability are the
quality goals

**Constraints**: Use verified merged repository source as factual authority;
cite dated official primary sources for external candidates; keep unsupported
external fields `unknown`; do not install, prototype, or adopt dependencies;
do not edit runtime helpers, policies, eval gates, traces, generated payloads,
installed caches, or vendored `.specify/**` content

**Scale/Scope**: One P1 story, AC-1.1 through AC-1.10, one canonical taxonomy
artifact, and no runtime/API surface

**Reviewability Budget**: Primary surface `docs/process`; projected 335
reviewable LOC, 4 production files, 8 total files, budget result within budget;
split decision is one docs/process slice

## Declared File Operations

- NEW docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md
- MODIFIED docs/ai/specs/.process/HRNS-001-workflow.md
- MODIFIED docs/ai/specs/.process/autopilot-state.json
- MODIFIED docs/ai/specs/harness-engineering-uplift-roadmap-MOC.md
- MODIFIED specs/hrns-001-harness-surface-inventory-gap-taxonomy/plan.md
- NEW specs/hrns-001-harness-surface-inventory-gap-taxonomy/research.md
- NEW specs/hrns-001-harness-surface-inventory-gap-taxonomy/data-model.md
- NEW specs/hrns-001-harness-surface-inventory-gap-taxonomy/quickstart.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Result | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | Pass | No plugin layout changes; repository-only validation remains under `tests/speckit-pro/` |
| II. Cross-Platform Runtime & Script Safety | Pass | Adds no active tooling, Bash, `jq`, package, runner, helper, or runtime dependency |
| III. Semantic Versioning | Pass | No plugin version or release metadata changes |
| IV. Test Coverage Before Merge | Pass | No new helper/gate/tool code; final proof uses existing docs/process checks and applicable Layer 1 validation |
| V. Conventional Commits | Pass | Phase commits use `feat(HRNS-001): ...`; final PR title must use a valid conventional commit |
| VI. KISS, Simplicity & YAGNI | Pass | One Markdown artifact, explicit tables, no schema registry or abstraction without a consumer |

Reviewability: within budget. No split exception or complexity justification is
required.

PR review packet source: the final PR body must summarize what changed, why,
non-goals, review order, scope budget, AC-1.1 through AC-1.10 traceability,
verification evidence, known gaps, and intentional deferrals.

## Project Structure

### Documentation (this feature)

```text
specs/hrns-001-harness-surface-inventory-gap-taxonomy/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md              # created by /speckit-tasks, not this phase
```

### Source Code (repository root)

```text
docs/ai/specs/
├── harness-engineering-uplift-gap-taxonomy.md
├── harness-engineering-uplift-roadmap-MOC.md
└── .process/
    ├── HRNS-001-workflow.md
    └── autopilot-state.json
```

**Structure Decision**: HRNS-001 is documentation/process only. The only
canonical deliverable is the Markdown taxonomy under `docs/ai/specs/`; the
feature-local files document planning, row semantics, and validation. No
`contracts/` directory is created because HRNS-001 exposes no runtime API,
helper schema, CLI command, or data registry.

## Phase 0 Research

Research decisions are recorded in [research.md](./research.md). All Phase 2
clarification markers are resolved; no unresolved clarification item remains
for planning.

## Phase 1 Design

Design artifacts:

- [data-model.md](./data-model.md) — conceptual row/entity semantics for the
  Markdown taxonomy.
- [quickstart.md](./quickstart.md) — reviewer validation procedure.
- `contracts/` — not created; no runtime interface exists.

## Post-Design Constitution Check

| Principle | Result | Evidence |
|-----------|--------|----------|
| Plugin Structure Compliance | Pass | Design edits remain docs/process only |
| Cross-Platform Runtime & Script Safety | Pass | No new executable tooling or shell dependency |
| Semantic Versioning | Pass | No manifest/version touch |
| Test Coverage Before Merge | Pass | Existing checks cover repo structure; no code requires new unit tests |
| Conventional Commits | Pass | Commit/PR convention remains explicit |
| KISS/Simplicity/YAGNI | Pass | Markdown tables and explicit review proof are simpler than a registry or validator |

No constitution violation or complexity exception is present.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
