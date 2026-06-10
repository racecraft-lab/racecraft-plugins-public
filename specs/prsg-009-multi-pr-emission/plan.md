# Implementation Plan: PRSG-009 multi-PR emission

**Branch**: `prsg-009-multi-pr-emission` | **Date**: 2026-06-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/prsg-009-multi-pr-emission/spec.md`

## Summary

PRSG-009 changes the post-implementation autopilot flow from one flattened PR to
one ordered PR per PRSG-008 layer-plan slice. The design reuses the existing
`plan-layers.sh` output as the only slice source, adds deterministic emission and
restack script surfaces, extends PR body and PRS rendering contracts for slice
metadata, and preserves Claude/Codex reference parity.

## Technical Context

**Language/Version**: Bash scripts with Markdown reference documentation.

**Primary Dependencies**: `git`, `gh`, `jq`; optional `gh-stack` only for safely
detected restack/sync operations on an existing stack.

**Storage**: Filesystem JSON/Markdown state: `docs/ai/specs/.process/autopilot-state.json`,
`specs/prsg-009-multi-pr-emission/.process/prs.json`, per-slice emission evidence
under `specs/prsg-009-multi-pr-emission/.process/emission/<slice_id>/`, and
generated `SPEC-MOC.md` PRS rows.

**Testing**: Shell test harness:
`bash tests/speckit-pro/run-all.sh --layer 1`,
`bash tests/speckit-pro/run-all.sh --layer 4`, and
`bash tests/speckit-pro/run-all.sh`.

**Target Platform**: Local macOS/Linux shell environments used by the
`speckit-pro` plugin.

**Project Type**: Claude/Codex plugin marketplace with skill reference files and
Bash helper scripts.

**Performance Goals**: Deterministic, idempotent resume/reconciliation over a
small layer-plan input. Each slice operation must fail fast before `gh pr create`
when verification fails or reconciliation is ambiguous.

**Constraints**: Reuse PRSG-008 layer-plan output; do not add new slicing,
routing, or atomicity heuristics; use explicit `gh pr create --base --head
--body-file`; keep full regression verification separate from per-slice scoped
verification; do not modify `.github/workflows/pr-checks.yml`; preserve Claude
and Codex parity for mirrored references.

**Scale/Scope**: One active feature spec, usually 1-6 layer-plan slices, one PR
per slice, and bounded JSON/Markdown evidence per slice.

**Reviewability Budget**: Primary surface `docs/process`; secondary surfaces
`harness/adapter` and `seed/config`; projected reviewable LOC 350-650 excluding
generated distribution mirrors; projected production files 6; projected total
files 10-12; budget result is warning accepted because the emission, resume,
PRS, and restack contracts are coupled.

## Declared File Operations

- MODIFIED speckit-pro/skills/speckit-autopilot/references/post-implementation.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh
- NEW speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh
- NEW speckit-pro/skills/speckit-autopilot/scripts/restack.sh

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Result | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | Changes stay inside the existing `speckit-pro` skill/reference/script and repo-root test surfaces. No plugin manifest or directory layout changes are planned. |
| II. Script Safety | PASS | New/modified scripts will use `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, `jq` for JSON, deterministic stderr, and Layer 4 script tests. |
| III. Semantic Versioning | PASS | No manual version edits. Release-please remains responsible for version changes after a conventional PR merge. |
| IV. Test Coverage Before Merge | PASS | Layer 1 covers structural/parity impact; Layer 4 covers `generate-pr-body.sh`, `generate-spec-index.sh`, `multi-pr-emission.sh`, and `restack.sh`; default verify remains the final regression gate. |
| V. Conventional Commits | PASS | Implementation PR title can use `feat(speckit-pro): emit one pull request per review slice`. |
| VI. KISS, Simplicity & YAGNI | PASS | PRSG-009 consumes PRSG-008 output directly, adds no new slicing heuristics, keeps `gh-stack` optional, and keeps restack mutation behind explicit `--apply`. |

**Reviewability decision**: Warning accepted. The planned production-file count
is at the warning boundary, but splitting the spec would separate emission,
resume, PRS rendering, and restack contracts that must share one state model.
Deferred deeper atomicity backstops remain in PRSG-010.

**PR review packet source**: The slice packet generated during emission supplies
review order, branch/base refs, declared file scope, scoped verification
evidence, traceability, known gaps, and restack/rollback notes. Full regression
evidence is stored once before emission and referenced by each slice packet.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-009-multi-pr-emission/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── multi-pr-emission-state.schema.json
│   ├── prs-v2.schema.json
│   ├── restack-output.schema.json
│   └── slice-packet.schema.json
└── tasks.md              # Created by /speckit-tasks, not this phase
```

### Source Code (repository root)

```text
speckit-pro/
├── skills/speckit-autopilot/
│   ├── references/post-implementation.md
│   └── scripts/
│       ├── generate-pr-body.sh
│       ├── generate-spec-index.sh
│       ├── multi-pr-emission.sh
│       └── restack.sh
└── codex-skills/speckit-autopilot/
    └── references/post-implementation-codex.md

tests/speckit-pro/
├── layer1-structural/
│   └── validate-codex-parity.sh
└── layer4-scripts/
    ├── test-generate-pr-body.sh
    ├── test-generate-spec-index.sh
    ├── test-multi-pr-emission.sh
    └── test-restack.sh
```

**Structure Decision**: Keep behavior in the existing autopilot reference and
script surfaces. Add only two new script helpers: `multi-pr-emission.sh` for the
slice emission/resume contract and `restack.sh` for deterministic dry-run-first
restack behavior.

## Complexity Tracking

No constitution-blocking violations. The reviewability warning is accepted in
the Constitution Check because the affected state contracts are coupled.

## Phase 0 Research

See [research.md](research.md).

## Phase 1 Design

See [data-model.md](data-model.md), [quickstart.md](quickstart.md), and the
contract schemas under [contracts/](contracts/).

## Verification Gates

| Gate | Command | Purpose |
|------|---------|---------|
| Structural | `bash tests/speckit-pro/run-all.sh --layer 1` | Validate plugin structure, script presence, and Codex parity. |
| Script unit | `bash tests/speckit-pro/run-all.sh --layer 4` | Validate PR body packets, PRS v2 rendering, emission stop/resume behavior, and restack exit contracts. |
| Default verify | `bash tests/speckit-pro/run-all.sh` | Final deterministic regression across Layers 1, 4, and 5. |
| Layer 8 parity | `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run` | Run only if implementation changes dispatch/parity fixture surfaces. |
| Layer 7 integration | Not planned | Only required if dispatch graph behavior changes. |

## Post-Design Constitution Check

PASS. Phase 1 artifacts preserve the same boundaries: no workflow CI edits, no
new slicing heuristics, no manual version changes, and no additional production
surfaces beyond the six declared files.
