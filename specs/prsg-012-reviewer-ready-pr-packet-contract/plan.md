# Implementation Plan: Reviewer-ready PR packet contract

**Branch**: `prsg-012-reviewer-ready-pr-packet-contract` | **Date**: 2026-06-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/prsg-012-reviewer-ready-pr-packet-contract/spec.md`

## Summary

Autopilot will render packet-owned PR titles and PR bodies for both single-PR and split-PR flows, validate the rendered packet before any `gh pr create`, and pass PR creation only through the packet target plus `--base`, `--head`, `--title`, and `--body-file`. The implementation centers on one shared packet schema, one shared Bash validator, direct generation of canonical reviewer sections, fixture-backed validation of allowed prose edits versus protected governance evidence, deterministic diagnostics for malformed inputs, and resume-safe split-PR blocking that preserves earlier opened PRs.

## Technical Context

**Language/Version**: Bash 4+ shell scripts; JSON Schema 2020-12 contract files

**Primary Dependencies**: Bash, `jq`, `git`, `gh`

**Storage**: Repository files plus deterministic per-feature process output under `.process/pr-packets/<packet_id>/validation.json`; no database

**Testing**: Layer 1 structural validation; Layer 4 shell script unit tests; Layer 3 Claude Code and Codex functional eval fixture updates; Layer 7 replay/integration fixture coverage for packet validation ordering; Layer 8 parity fixture coverage for Claude Code/Codex guidance equivalence; default deterministic suite

**Target Platform**: macOS/Linux shell execution inside the `speckit-pro` plugin workflow

**Project Type**: Claude Code/Codex plugin automation with Markdown workflow docs, shell scripts, JSON contracts, and shell fixtures

**Performance Goals**: Packet validation completes locally before networked PR creation; invalid packets and malformed packet inputs make zero `gh pr create` attempts; validation stdout/stderr and JSON output are deterministic for fixture comparison

**Constraints**: No new runtime dependencies beyond Bash, `jq`, `git`, and `gh`; keep scripts deterministic and fixture-friendly; preserve the legacy `speckit-pro-review-packet-source` marker and literal `## UAT Runbook` heading; reject internal title tokens, stale placeholders, unknown HTML comments outside code fences, and host template content that replaces the canonical packet block; use distinct exit `1` validation failures and exit `2` input errors with one deterministic stderr line

**Scale/Scope**: Single-PR and split-PR autopilot packet generation paths; one spec, one slice; validation writes one JSON record per packet

**Reviewability Budget**: Primary surface is docs/process plus Bash automation; projected reviewable LOC about 350 with advisory estimator at 245; projected production/reference files 6-8; projected total files about 20-24 after input-error, resume, functional-eval, integration, and parity fixture edits; budget result within block threshold with a bounded total-file warning; split decision is one spec, one slice

## Declared File Operations

- NEW speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json
- NEW speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/post-implementation.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md
- MODIFIED speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md
- NEW tests/speckit-pro/layer4-scripts/test-validate-pr-packet.sh
- MODIFIED tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh
- MODIFIED tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/valid-single.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/valid-split.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-title-token.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-missing-evidence.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-protected-edit.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-missing-packet.args
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-malformed-json.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/pr-packet/split-partial-failure-state.json
- MODIFIED tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json
- MODIFIED tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json
- MODIFIED tests/speckit-pro/layer7-integration/dispatch-fixtures/18-post-impl-parallel-subagents/README.md
- MODIFIED tests/speckit-pro/layer7-integration/dispatch-fixtures/18-post-impl-parallel-subagents/expected.json
- MODIFIED tests/speckit-pro/layer7-integration/dispatch-fixtures/18-post-impl-parallel-subagents/parser-fixture.jsonl
- MODIFIED tests/speckit-pro/layer7-integration/dispatch-fixtures/18-post-impl-parallel-subagents/prompt.txt
- MODIFIED tests/speckit-pro/layer8-parity/01-post-impl-parity/README.md
- MODIFIED tests/speckit-pro/layer8-parity/01-post-impl-parity/workflow.md
- MODIFIED tests/speckit-pro/layer8-parity/01-post-impl-parity/tolerance.json
- MODIFIED tests/speckit-pro/layer8-parity/01-post-impl-parity/expected-equivalence.json

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

Reviewability gate: PASS with bounded warning. The plan stays below block thresholds with about 350 projected reviewable LOC, 6-8 production/reference files, and about 20-24 total files after input-error, resume, functional-eval, integration, and parity fixture edits. No typed reviewability exception is required because the additional files extend existing evidence fixtures for one vertical packet contract.

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
    ├── requirements.md
    └── reliability.md
```

### Source Code (repository root)

```text
speckit-pro/
├── skills/
│   └── speckit-autopilot/
│       ├── contracts/
│       │   ├── pr-packet.schema.json
│       │   └── slice-packet.schema.json
│       ├── references/
│       │   └── post-implementation.md
│       ├── scripts/
│       │   ├── generate-pr-body.sh
│       │   ├── multi-pr-emission.sh
│       │   └── validate-pr-packet.sh
│       └── templates/
│           └── pr-description-template.md
└── codex-skills/
    └── speckit-autopilot/
        ├── SKILL.md
        └── references/
            └── post-implementation-codex.md

tests/
└── speckit-pro/
    ├── layer3-functional/
    │   ├── evals/
    │   │   └── speckit-autopilot-evals.json
    │   └── codex-evals/
    │       └── speckit-autopilot-evals.json
    ├── layer4-scripts/
    │   ├── test-generate-pr-body.sh
    │   ├── test-multi-pr-emission.sh
    │   ├── test-validate-pr-packet.sh
    │   └── fixtures/
    │       └── pr-packet/
    ├── layer7-integration/
    │   └── dispatch-fixtures/
    │       └── 18-post-impl-parallel-subagents/
    └── layer8-parity/
        └── 01-post-impl-parity/
```

**Structure Decision**: Use the existing `speckit-autopilot` contract/script/template/reference layout and repo-level Layer 4 shell tests. The new `pr-packet.schema.json` becomes the shared rendered packet contract, while existing `slice-packet.schema.json` remains slice evidence/source input. Codex-facing guidance stays as mirrored documentation only; it references the shared primary schema and validator instead of carrying duplicate copies.

## Reliability Evidence Plan

Workflow failure evidence:

- Blocking packet validation failures append reader-facing evidence to `docs/ai/specs/.process/<workflow-id>-workflow.md`; PRSG-012 uses `docs/ai/specs/.process/PRSG-012-workflow.md`.
- The validation JSON under `specs/prsg-012-reviewer-ready-pr-packet-contract/.process/pr-packets/<packet_id>/validation.json` remains authoritative. The workflow event mirrors the failure in operator-readable form.
- Each event uses a deterministic event id derived from packet or input identity, validation result path, and blocked status. Retries update or supersede that event instead of adding ambiguous duplicates.
- Event content must include packet or input id, mode and target when known, validation result path or `no-path`, deterministic stderr line, failed rule or reason, remediation summary, resume boundary, `pr_blocked`, and prior successful split PR references when relevant.

Shared validator reuse:

- The single-PR post-implementation path and the split-PR `multi-pr-emission.sh` path both invoke `validate-pr-packet.sh` before any `gh pr create` attempt.
- PR creation call sites may consume only the validator exit code and validation JSON; they must not duplicate rendered-title, rendered-body, protected-fingerprint, input-error, or remediation-rule logic.
- A passing validation result is the only path to `gh pr create --base <base_branch> --head <head_branch> --title <generated-title> --body-file <body_file>`.

Layer evidence:

- Layer 4: `test-validate-pr-packet.sh`, `test-generate-pr-body.sh`, and `test-multi-pr-emission.sh` cover valid single packets, valid split packets, invalid title tokens, missing body evidence, protected edit rejection, malformed input errors, deterministic stderr, workflow event emission, and split partial-failure resume.
- Layer 3: `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json` and `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json` include expectations that autopilot describes packet generation, validation before PR creation, `--base`/`--head`/`--title`/`--body-file` usage, deterministic blocked evidence, and no post-create repair fallback.
- Layer 7: `tests/speckit-pro/layer7-integration/dispatch-fixtures/18-post-impl-parallel-subagents/` extends the existing post-implementation dispatch fixture to capture the packet ordering contract: packet render, validator call, workflow evidence on failure, then PR creation only after pass; split packets validate before each slice PR.
- Layer 8: `tests/speckit-pro/layer8-parity/01-post-impl-parity/` extends the existing post-implementation parity fixture to compare Claude Code and Codex guidance for equivalent packet validation ordering, repo-relative evidence paths, blocked-remediation language, and absence of duplicate validator or schema copies.
- Developer-local evidence commands are documented in `quickstart.md`; default verification remains Layer 1, Layer 4, and the default deterministic suite.

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
- Treat missing, unreadable, invalid-JSON, and schema-invalid packet inputs as `input_error` records with exit `2`, a stable synthetic `_input-error-<hash>` identity when packet metadata is unavailable, and zero PR creation attempts.
- Treat rendered-content validation failures as exit `1` `validation_failure` records that trust parsed packet metadata, write packet-specific remediation evidence, and append workflow evidence before stopping.
- Emit one deterministic stderr line for every failed validator run so Layer 4 fixtures can compare diagnostics without timestamps, absolute paths, or host-specific text.
- On resume, always revalidate the current rendered packet and overwrite or supersede stale failed validation evidence before allowing PR creation.
- In split-PR mode, preserve prior successful PR records from PRSG-009 state surfaces, set the resume boundary to the failed packet, and reconcile existing PRs before retrying so a corrected packet does not duplicate earlier `gh pr create` calls.
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
