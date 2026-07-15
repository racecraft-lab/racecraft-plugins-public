---
type: "speckit-legacy-memory-record"
title: "XPLAT-007 Python Tooling and Release-Gate Migration"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-d7628e8ce7218e17"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-007 Python Tooling and Release-Gate Migration

[Source: specs/xplat-007-python-tooling-and-release-gate-migration]

XPLAT-007 implemented active repo-local Python gate migration on top of the
XPLAT-004 runner, XPLAT-005 read-only helper records, and XPLAT-006
mutation/install/PR-emission contracts. The production surface lives under
`speckit-pro/speckit_pro_runner/gates/`, with gate request, case, promotion,
and contract evidence under
`tests/speckit-pro/unit/fixtures/runner-gates/`.

### Technical Approach

- Add an explicit `gates/` package rather than a generic command framework, so
  suite, payload, install, release-readiness, and guard behavior remain
  reviewable and bounded.
- Preserve the existing JSON-envelope runner contract, diagnostics, status to
  exit-code mapping, and shell-disabled subprocess policy.
- Promote suite/eval, payload, install-verification, release-readiness, and
  active-path guard operations through `python -m speckit_pro_runner` request
  fixtures.
- Keep release payload behavior limited to test payload evidence and fixture or
  temporary roots; generated release payload selection and publication remain
  XPLAT-008.
- Update plugin PR and release workflows so plugin validation dispatches to
  Python runner gates instead of Bash or `jq` release logic.
- Preserve XPLAT-007 contract schemas in the gate fixture tree so Layer 4 tests
  remain runnable after the active spec folder is archived.

### Testing Strategy

XPLAT-007 verification uses Python standard-library focused tests,
`python3 tests/speckit-pro/unit/test-speckit-pro-gates.py`, runner
request fixtures for default suite, layer, AI-eval, integration, parity,
payload evidence, install verification, release readiness, live release
readiness, and active-path guard behavior, plus the default deterministic
repository suite. GitHub PR checks on #284 through #287 verified the sliced
implementation before archive cleanup.

### Cleanup Notes

`specs/xplat-007-python-tooling-and-release-gate-migration` was removed from
active `specs/**` in the post-merge cleanup after PR #287 merged. Recovery
commands and provenance are recorded in the XPLAT-007 archive report. Contract
schemas needed by gate tests were copied to the XPLAT-007 gate fixture tree
before cleanup. XPLAT-008 is now ready for installed Claude/Codex cutover,
release payload publication, native installed-plugin UAT, update/autoheal, and
public release readiness.
