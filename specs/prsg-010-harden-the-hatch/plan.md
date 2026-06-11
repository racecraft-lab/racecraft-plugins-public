# Implementation Plan: PRSG-010 Harden the Hatch + O5 Monster Epics

**Branch**: `prsg-010-harden-the-hatch` | **Date**: 2026-06-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/prsg-010-harden-the-hatch/spec.md`

## Summary

PRSG-010 hardens the final reviewability boundary so unexcepted blocking diffs
stop before PR body generation, single PR creation, or multi-PR emission. The
implementation will preserve the existing reviewability gate exit contract,
add a machine-readable final backstop/re-slicing handoff, introduce an O5 parent
manifest model for flat sibling child specs, and promote contextual routing
signals only when deterministic fixture-backed evidence is high confidence.

Delivery is intentionally split as an ordered stack: final-gate backstop,
contextual router probes, O5 manifest/status support, then docs/parity/polish.

## Technical Context

**Language/Version**: Bash 4+ shell scripts, Markdown skills, YAML
manifests, and JSON Schema 2020-12 contracts

**Primary Dependencies**: `bash`, `jq`, `git`, `gh` at PR-emission boundaries,
SpecKit templates, Claude/Codex skill mirrors

**Storage**: Repository files only: feature artifacts, contract schemas,
workflow state JSON, and generated re-slicing packets

**Testing**: `bash tests/speckit-pro/run-all.sh --layer 1`,
`bash tests/speckit-pro/run-all.sh --layer 4`,
`bash tests/speckit-pro/run-all.sh`, plus Layer 8 parity when mirrored skill
prose changes. Focused backward-compatibility checks for PRSG-010 include
`bash tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh`,
`bash tests/speckit-pro/layer4-scripts/test-reviewability-gate.sh`,
`bash tests/speckit-pro/layer4-scripts/test-atomicity-route.sh`,
`bash tests/speckit-pro/layer4-scripts/test-plan-layers.sh`, and
`bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` when the
slice touches the corresponding flat-spec, typed-exception, PRSG-007,
PRSG-008, or PRSG-009 compatibility surface.

**Target Platform**: Claude Code and Codex plugin marketplace workflows on
macOS/Linux shell environments

**Project Type**: Plugin marketplace with deterministic shell orchestration and
Markdown skill surfaces

**Performance Goals**: Deterministic output for identical inputs; O5 topology
validation and routing probes run with linear file scans over declared feature
artifacts and fixtures

**Constraints**: No nested O5 child specs in v1; typed exceptions remain
available; weak contextual evidence is advisory only; stop-before-PR handling
must occur before PR body generation, `gh pr create`, or `multi-pr-emission.sh`

**Scale/Scope**: 3 user stories, 23 functional requirements, 8 success
criteria, and a planned four-slice implementation stack

**Reviewability Budget**: Primary surface `harness/adapter`; secondary surfaces
`docs/process` and `seed/config`; projected reviewable LOC 1,700 before slicing;
projected production files 8; projected total files 39 before slicing; budget
result split required; split decision is an ordered stack with target slices at
or under 700 reviewable LOC and independently reviewable file surfaces.

## Declared File Operations

### PRSG-010A - Final Reviewability Backstop

- NEW speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh
- NEW speckit-pro/skills/speckit-autopilot/contracts/final-reviewability-gate-state.schema.json
- NEW speckit-pro/skills/speckit-autopilot/contracts/reslicing-packet.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/post-implementation.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/block-no-exception/gate-result.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/valid-refactor-exception/exception.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/generated-boilerplate/template.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/gate-error/gate-result.json
- NEW tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh
- MODIFIED tests/speckit-pro/layer4-scripts/test-reviewability-gate.sh

### PRSG-010B - Contextual Router Probes

- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh
- NEW speckit-pro/skills/speckit-autopilot/contracts/routing-decision.schema.json
- MODIFIED tests/speckit-pro/layer4-scripts/test-atomicity-route.sh
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-guarded-cutover/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-release-held/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-weak-evidence/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-consumer-locality/tasks.md

### PRSG-010C - O5 Parent/Child Support

- NEW speckit-pro/skills/speckit-autopilot/scripts/o5-topology.sh
- NEW speckit-pro/skills/speckit-autopilot/contracts/o5-parent-manifest.schema.json
- MODIFIED speckit-pro/skills/speckit-scaffold-spec/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md
- MODIFIED speckit-pro/skills/speckit-status/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-status/SKILL.md
- NEW tests/speckit-pro/layer4-scripts/test-o5-topology.sh
- NEW tests/speckit-pro/layer4-scripts/fixtures/o5-topology/valid-parent/o5-parent-manifest.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/o5-topology/invalid-topology/o5-parent-manifest.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/o5-topology/mixed-child-states/o5-parent-manifest.json
- MODIFIED tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh

### PRSG-010D - Docs, Templates, Parity, And Polish

- MODIFIED docs/ai/specs/pr-size-governance-technical-roadmap.md
- MODIFIED .specify/presets/speckit-pro-reviewability/templates/spec-template.md
- MODIFIED .specify/templates/spec-template.md
- MODIFIED tests/speckit-pro/layer1-structural/validate-scripts.sh
- NEW tests/speckit-pro/layer8-parity/03-prsg-010-backstop-o5-routing/README.md
- NEW tests/speckit-pro/layer8-parity/03-prsg-010-backstop-o5-routing/workflow.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-design gate status: PASS with required split.

- Plugin Structure Compliance: PASS. Changes stay inside existing `speckit-pro`
  skill, script, contract, and test directories.
- Script Safety: PASS. New shell scripts must use `#!/usr/bin/env bash`,
  `set -euo pipefail`, quoted variables, explicit exit codes, and Layer 4
  fixture coverage.
- Semantic Versioning: PASS. No manual version edits are planned.
- Test Coverage Before Merge: PASS. Script behavior lands with Layer 4 tests;
  skill/template changes land with Layer 1 and Layer 8 parity coverage where
  mirrored prose changes.
- Conventional Commits: PASS. Commit/PR title will use a specific conventional
  commit scope.
- KISS, Simplicity & YAGNI: PASS. O5 v1 uses one parent manifest plus flat child
  specs; final backstop uses a focused wrapper/handoff script instead of
  redesigning PRSG-009 emission.

For all specs, the generated plan MUST also define:

- The primary review surface and any secondary surfaces.
- Whether the spec stays within the reviewability budget from the project
  constitution: warn above 400 reviewable LOC, 6 production files, 15 total
  files, or more than one primary surface; block above 800 reviewable LOC,
  8 production files, 25 total files, or more than one primary surface unless a
  ratified split exception exists.
- The exact split decision when the budget is exceeded, including follow-up
  spec IDs or issue IDs for deferred work.
- The PR review packet source: what changed, why, non-goals, review order,
  scope budget, traceability, verification, known gaps, and rollback/flags.

Post-design gate status: PASS with the same split requirement. No constitution
exception is required because the feature is explicitly planned as an ordered
split stack rather than a single oversized PR.

### Split Plan

| Slice | Scope | Primary files | Verification |
|-------|-------|---------------|--------------|
| PRSG-010A | Final reviewability backstop and re-slicing packet | final backstop script, autopilot post-implementation references, backstop schemas | Layer 4 final-backstop fixtures covering concrete `operator_steps` for PRSG-007 reroute, PRSG-008 layer-plan regeneration, and PRSG-009 handoff selection, existing `test-reviewability-gate.sh` typed-exception fixtures preserved or intentionally updated with rationale, Layer 1 structural, default verify |
| PRSG-010B | Contextual routing probes and production routing schema | `atomicity-route.sh`, production routing schema, router fixtures | Layer 4 atomicity-router fixtures and schema validation for every router fixture output, including contextual-probe success, weak-evidence, paired baseline-vs-weak-evidence fixtures that prove the conservative route is unchanged, no decisive contextual signal is emitted, weak/conflicting evidence appears only as closed-enum hints, and existing PRSG-007 dogfood/contract fixtures remain valid unless an intentional fixture update is documented |
| PRSG-010C | O5 parent manifest, flat child validation, status rollup guidance | O5 topology script, scaffold/status skills and Codex mirrors, O5 schema | Layer 4 O5 topology fixtures covering branch/path exact-match failures, mixed child states with every declared child emitted exactly once, generated `SPEC-MOC.md` zones regenerated only through `generate-spec-index.sh`, legacy/current flat `specs/*` scan regression using the existing spec-index fixtures, scaffold/status guidance assertions that normal split-PR remains default unless O4 cannot slice thin enough, Layer 8 parity, and Layer 1 structural |
| PRSG-010D | Boilerplate removal, docs, parity, and review-packet polish | roadmap/templates, parity fixture, structural assertions | Layer 1 structural, Layer 8 parity mapped to every changed Claude/Codex mirror surface, default verify, PRSG-008 `plan-layers` and PRSG-009 `multi-pr-emission` fixture compatibility evidence when referenced by final packet or review-packet polish, and negative checks that generated exception education names the valid classes/provenance rules without emitting a standalone valid pragma |

### Backward Compatibility Guardrails

- Flat spec discovery: O5 support must remain additive to the existing
  `specs/*/SPEC-MOC.md` scan. Implementation must rerun the existing
  `test-generate-spec-index.sh` fixture set and prove ordinary flat specs stay
  byte-identical unless a change is explicitly documented as intentional.
- Typed exceptions: the current `Reviewability-Exception: refactor|infra|upgrade`
  positive fixtures and invalid-class/casing/trailing-prose negative fixtures
  must keep passing. PRSG-010 may intentionally update generated-provenance or
  code-fence cases, but each intentional fixture change must name the PRSG-010
  provenance rule it implements.
- PRSG-007/008/009 compatibility: PRSG-010 recovery metadata consumes existing
  routing, layer-plan, and multi-PR contracts; it must not rewrite those
  contracts. Rerun `test-atomicity-route.sh`, `test-plan-layers.sh`, and
  `test-multi-pr-emission.sh` for slices that touch their inputs, outputs, or
  handoff wording, and document any intentional fixture update in the task or
  test name.
- Mirror parity: every changed Claude skill/reference surface must either have
  its Codex mirror updated in the same slice or be documented as a single
  shared runtime-agnostic artifact. Evidence must include Layer 1 Codex parity
  checks and the PRSG-010 Layer 8 parity fixture/dry-run with fields mapped to
  the changed autopilot, scaffold, and status mirrors.

### PR Review Packet Source

PR body generation should draw from this plan, the spec, `tasks.md`, and the
workflow evidence:

- What changed: final backstop, contextual router probes, O5 topology, and
  generated-boilerplate cleanup.
- Why: protect reviewer time, support monster-epic coordination, and keep
  routing deterministic.
- Non-goals: no nested O5 children, no disabling typed exceptions, no PRSG-009
  emission redesign, no old-spec migration.
- Review order: PRSG-010A, PRSG-010B, PRSG-010C, PRSG-010D.
- Scope budget: split required, each slice targets 700 or fewer reviewable LOC.
- Traceability: map FR-001..FR-009 to PRSG-010A, FR-017..FR-022 to PRSG-010B,
  FR-010..FR-016 to PRSG-010C, and FR-023 plus docs/parity to PRSG-010D.
- Verification: record the exact structural, script-unit, default, and parity
  commands run for each slice.
- Known gaps: name only explicitly deferred follow-up specs or issues.
- Rollback/flags: script and skill changes are reverted by the slice commit; no
  runtime feature flag is required.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-010-harden-the-hatch/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
speckit-pro/
├── skills/
│   ├── speckit-autopilot/
│   │   ├── SKILL.md
│   │   ├── contracts/
│   │   ├── references/
│   │   └── scripts/
│   ├── speckit-scaffold-spec/SKILL.md
│   └── speckit-status/SKILL.md
├── codex-skills/
│   ├── speckit-autopilot/
│   ├── speckit-scaffold-spec/
│   └── speckit-status/
└── tests/
    └── layer references remain under repository-level tests/speckit-pro/

tests/speckit-pro/
├── layer1-structural/
├── layer3-functional/
├── layer4-scripts/
└── layer8-parity/

.specify/
└── templates/ and presets/speckit-pro-reviewability/templates/

docs/ai/specs/
└── pr-size-governance-technical-roadmap.md
```

**Structure Decision**: Use the existing single-plugin layout. New deterministic
logic belongs in `speckit-pro/skills/speckit-autopilot/scripts/` with contracts
in `speckit-pro/skills/speckit-autopilot/contracts/`; Claude/Codex mirrors stay
paired for skill prose; tests remain in the established Layer 1, Layer 4, and
Layer 8 suites.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The plan uses existing plugin surfaces and an ordered split stack. | Not applicable. |
