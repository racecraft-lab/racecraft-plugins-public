# Implementation Plan: Reviewer-ready PR packet contract

**Branch**: `prsg-012-reviewer-ready-pr-packet-contract` | **Date**: 2026-06-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/prsg-012-reviewer-ready-pr-packet-contract/spec.md`

## Summary

Autopilot will render packet-owned PR titles and PR bodies for both single-PR and split-PR flows, validate the rendered packet before any `gh pr create`, and pass PR creation only through the packet target plus `--title` and `--body-file`. The implementation centers on one shared packet schema, one shared Bash validator, direct generation of canonical reviewer sections, and fixture-backed validation of allowed prose edits versus protected governance evidence.

## Technical Context

**Language/Version**: Bash 4+ shell scripts; JSON Schema 2020-12 contract files

**Primary Dependencies**: Bash, `jq`, `git`, `gh`

**Storage**: Repository files plus deterministic per-feature process output under `.process/pr-packets/<packet_id>/validation.json`; no database

**Testing**: Layer 1 structural validation; Layer 4 shell script unit tests; default deterministic suite; L3/L7/L8 fixture updates where packet behavior is represented

**Target Platform**: macOS/Linux shell execution inside the `speckit-pro` plugin workflow

**Project Type**: Claude Code/Codex plugin automation with Markdown workflow docs, shell scripts, JSON contracts, and shell fixtures

**Performance Goals**: Packet validation completes locally before networked PR creation; invalid packets make zero `gh pr create` attempts; validation output is deterministic for fixture comparison

**Constraints**: No new runtime dependencies beyond Bash, `jq`, `git`, and `gh`; keep scripts deterministic and fixture-friendly; preserve the legacy `speckit-pro-review-packet-source` marker and literal `## UAT Runbook` heading; reject internal title tokens, stale placeholders, unknown HTML comments outside code fences, and host template content that replaces the canonical packet block

**Scale/Scope**: Single-PR and split-PR autopilot packet generation paths; one spec, one slice; validation writes one JSON record per packet

**Reviewability Budget**: Primary surface is docs/process plus Bash automation; projected reviewable LOC about 350 with advisory estimator at 245; projected production files 4-6; projected total files under 15; budget result within budget; split decision is one spec, one slice

## Declared File Operations

- NEW speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json
- NEW speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/references/post-implementation.md
- MODIFIED speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md
- NEW tests/speckit-pro/layer4-scripts/test-validate-pr-packet.sh
- MODIFIED tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh
- MODIFIED tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/valid-single.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/valid-split.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-title-token.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-missing-evidence.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-protected-edit.json

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | Changes stay inside the existing `speckit-pro` plugin structure and repo-level `tests/speckit-pro/` suite. |
| II. Script Safety | PASS | New validator will use `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, explicit exit codes, and `bash -n` coverage through Layer 4. |
| III. Semantic Versioning | PASS | No manual version edits are planned; release-please remains the versioning path. |
| IV. Test Coverage Before Merge | PASS | New validator and changed generation/emission paths receive Layer 4 unit coverage, plus structural validation. |
| V. Conventional Commits | PASS | Packet-owned title metadata enforces `<type>(<scope>): <plain-English description>` before PR creation. |
| VI. KISS, Simplicity & YAGNI | PASS | One shared schema and one validator replace post-create repair; no new dependencies or speculative repair system. |

Reviewability gate: PASS. The plan stays below warning thresholds with about 350 projected reviewable LOC, 4-6 production files, and fewer than 15 total files. No typed reviewability exception is required.

PR review packet source for this spec: title/body packet generation, pre-create validation, safe prose refinement boundaries, UAT compatibility, scope/verification evidence, validation result JSON, and split-packet identity. Non-goals: post-create auto-repair and broad host-template migration.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-012-reviewer-ready-pr-packet-contract/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── pr-packet.schema.json
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
speckit-pro/
└── skills/
    └── speckit-autopilot/
        ├── contracts/
        │   ├── pr-packet.schema.json
        │   └── slice-packet.schema.json
        ├── references/
        │   └── post-implementation.md
        ├── scripts/
        │   ├── generate-pr-body.sh
        │   ├── multi-pr-emission.sh
        │   └── validate-pr-packet.sh
        └── templates/
            └── pr-description-template.md

tests/
└── speckit-pro/
    └── layer4-scripts/
        ├── test-generate-pr-body.sh
        ├── test-multi-pr-emission.sh
        ├── test-validate-pr-packet.sh
        └── fixtures/
            └── pr-packet/
```

**Structure Decision**: Use the existing `speckit-autopilot` contract/script/template/reference layout and repo-level Layer 4 shell tests. The new `pr-packet.schema.json` becomes the shared rendered packet contract, while existing `slice-packet.schema.json` remains slice evidence/source input.

## Complexity Tracking

No constitution violations or reviewability exceptions are planned.

## Phase 0 Research Results

Research is captured in [research.md](research.md). Key decisions:

- Use one shared rendered packet validator, not separate single/split validators.
- Treat `generated_title` as structured packet metadata with final value, conventional type/scope, public description, source evidence, and rejected candidates.
- Treat `target.base_branch` and `target.head_branch` as required packet metadata used for `gh pr create --base` and `--head`.
- Treat `body_file` as a repo-relative rendered Markdown path and `scope_evidence.changed_files` as the changed-file scope reviewers inspect.
- Generate canonical reviewer sections directly, while preserving the literal `## UAT Runbook` heading for SPEC-006a/b compatibility.
- Allow prose refinement only inside exact full-line editable marker pairs under `Summary`, `What Changed`, and `Why It Matters`.
- Store deterministic validation JSON under the target feature `.process/pr-packets/<packet_id>/validation.json`.
- Keep post-create auto-repair out of scope.

## Phase 1 Design Results

Design artifacts are captured in:

- [data-model.md](data-model.md)
- [contracts/pr-packet.schema.json](contracts/pr-packet.schema.json)
- [quickstart.md](quickstart.md)

### Post-Design Constitution Re-check

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | The planned files remain in existing plugin/test directories and this feature's planning directory. |
| II. Script Safety | PASS | Validator behavior is limited to deterministic Bash and `jq` checks with explicit validation JSON output. |
| III. Semantic Versioning | PASS | No manual version edits are part of the design. |
| IV. Test Coverage Before Merge | PASS | Quickstart requires Layer 1, Layer 4, and default deterministic verification. |
| V. Conventional Commits | PASS | Title validation is a central contract rule before `gh pr create`. |
| VI. KISS, Simplicity & YAGNI | PASS | One packet contract covers both single and split PR paths; repair of existing PRs is deferred. |

Post-design reviewability gate: PASS. The design remains one spec and one slice, with no G3 split required.
