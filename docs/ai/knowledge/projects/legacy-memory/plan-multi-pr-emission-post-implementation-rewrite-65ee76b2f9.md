---
type: "speckit-legacy-memory-record"
title: "Multi-PR emission (post-implementation rewrite)"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-65ee76b2f97d05d6"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Multi-PR emission (post-implementation rewrite)

[Source: specs/prsg-009-multi-pr-emission]
**Branch**: `prsg-009-multi-pr-emission` · **Status**: Completed · **Archived**: 2026-06-11

### Dependencies & Versions

- Bash + `jq`, `git`, and GitHub CLI (`gh`); no package manager, compiled build
  step, Python runtime, or workflow CI changes in the shipped behavior.
- Reuses PRSG-008 layer-plan JSON as the only slice source and the existing
  `generate-spec-index.sh` sentinel generator for schema v2 PRS table rendering.
- `gh-stack` is optional and only used when safely detected for an existing
  active stack; explicit `gh pr create --base --head --body-file` remains the
  required PR creation path.

### Architecture / Approach

- `multi-pr-emission.sh`: validates layer-plan/state inputs, prepares slice
  branches and PR commands, writes candidate state/PRS/command JSON, supports
  fixture-backed PR reconciliation, persists successful slice PR state, and
  blocks on failed scoped verification before opening a PR.
- `generate-pr-body.sh --slice-packet <json-file>`: preserves the legacy
  positional path while adding reviewer-visible slice sections for scope,
  verification, traceability, restack/rollback, known gaps, and full regression
  evidence.
- `generate-spec-index.sh`: renders PRS schemaVersion 2 rows with order, slice,
  PR, status, branch, base, SHA, scope, and verification columns while keeping
  schema v1 compatibility.
- `restack.sh`: provides dry-run-first restack planning/apply behavior with
  deterministic JSON stdout, stable stderr diagnostics, and exit codes for
  success, conflicts, input error, dirty tree, and git/gh failure.
- Claude and Codex post-implementation references were updated together so the
  two runtime surfaces describe the same multi-PR emission contract.

### Test Strategy

- `bash tests/speckit-pro/unit/test-multi-pr-emission.sh` passed `81/81`.
- `bash tests/speckit-pro/unit/test-restack.sh` passed `32/32`.
- `bash tests/speckit-pro/unit/test-generate-pr-body.sh` passed `44/44`.
- `bash tests/speckit-pro/unit/test-generate-spec-index.sh` passed `86/86`.
- `bash tests/speckit-pro/run-all.sh` passed `2300/2300` after active spec cleanup.
- PR #145 CI recorded successful PR Checks, CodeQL, Release, `test(speckit-pro)`,
  `validate-plugins`, `validate-pr-title`, and `detect` for merge commit
  `a3361d50e3dfc5463fb2d5dbb2737a3525637a32`.

### Cleanup Notes

`specs/prsg-009-multi-pr-emission` was removed from active `specs/**` cleanup on
2026-06-11 after the PRSG-009 contract schemas were preserved under
`speckit-pro/skills/speckit-autopilot/contracts/` and the emitter's schema path
reporting was repointed to payload-included contracts.

---
