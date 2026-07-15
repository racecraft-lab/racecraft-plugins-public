---
type: "speckit-legacy-memory-record"
title: "XPLAT-006 Mutation, Install, and PR-Emission Helper Port"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-f872298aa5ab229d"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-006 Mutation, Install, and PR-Emission Helper Port

[Source: specs/xplat-006-mutation-install-pr-emission-helper-port]

XPLAT-006 implemented the mutation-capable runner helper substrate on top of
the XPLAT-004 runner and XPLAT-005 read-only registry. The production surface
lives under `speckit-pro/speckit_pro_runner/helpers/`, with contract and parity
evidence under `tests/speckit-pro/unit/fixtures/mutation-helpers/`.

### Technical Approach

- Extend the explicit helper registry with mutation-capable helper records and
  deferred/out-of-scope handoff metadata instead of dynamic helper discovery.
- Keep promoted runner helper logic in Python 3.11+ standard library code, with
  no shell execution, package restore, or network dependency.
- Add shared mutation primitives in `helpers/mutation.py` for request/result
  normalization, operation records, path-boundary checks, dirty-worktree
  guards, atomic generated-file writes, partial-failure records, and no-op
  handling.
- Add install completeness and fake-home repair proof in `helpers/install.py`
  backed by `install_inventory.json`.
- Add generated PR-body output and dry-run command-plan proof in
  `helpers/pr_emission.py`; live GitHub/repo command-plan apply remains a
  deterministic deferred-live-mutation failure.
- Add `validate-autopilot-phase-coverage.py` and generated Codex/Claude mirrors
  to prevent future autopilot workflows from omitting Phase 6.5 or canonical
  Post steps.
- Preserve XPLAT-006 contract schemas in the mutation-helper fixture tree so
  Layer 4 tests remain runnable after the active spec folder is archived.

### Testing Strategy

XPLAT-006 verification uses Python standard-library focused tests,
`python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`,
`python3 tests/speckit-pro/unit/test-autopilot-phase-coverage.py`,
the runner and read-only helper Layer 4 suites, spec-index checks, JSON
validation, diff hygiene, PR-packet validation, workflow-contract validation,
reviewability gates, and the default deterministic suite. Native installed
Claude/Codex UAT, generated-payload selection/cutover, active repo-local Bash
gate replacement, update/autoheal proof, and public release claims remain
XPLAT-007 and XPLAT-008 responsibilities.

### Cleanup Notes

`specs/xplat-006-mutation-install-pr-emission-helper-port` was removed from
active `specs/**` in the post-merge cleanup after PR #281 merged. Recovery
commands and provenance are recorded in the XPLAT-006 archive report. Contract
schemas needed by helper tests were copied to the mutation-helper fixture tree
before cleanup.
