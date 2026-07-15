---
type: "speckit-legacy-memory-record"
title: "XPLAT-007 Python Tooling and Release-Gate Migration"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-bb73b523a5742504"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-007 Python Tooling and Release-Gate Migration

[Source: specs/xplat-007-python-tooling-and-release-gate-migration]

XPLAT-007 shipped the Python-authoritative repo-local gate substrate needed
before installed Claude/Codex runtime cutover. It added runner gate modules for
suite, payload, install-verification, release-readiness, and active-path guard
behavior, wired those operations through the existing Python runner envelope,
updated plugin CI dispatch to call Python gates, recorded promotion and parity
evidence, refreshed runner metadata, and added deterministic Layer 4 gate
coverage.

The feature preserves the XPLAT-004 runner contract, XPLAT-005 read-only helper
records, and XPLAT-006 mutation/install/PR-emission boundaries while replacing
active repo-local validation and release-readiness command paths. It
deliberately avoids active Claude Code or Codex installed-runtime invocation
cutover, generated release payload publication, public platform claims, native
installed-plugin UAT, update, and autoheal readiness. Those public release
proofs remain XPLAT-008.

### Requirements Preserved

- Active repo-local suite, payload, install-verification, release-readiness, and
  active-path guard behavior has Python 3.11+ standard-library runner
  entrypoints.
- Promotion records and fixtures distinguish Python-authoritative gates from
  inactive historical/parity evidence and XPLAT-008 cutover surfaces.
- Remaining workflow shell is constrained to dispatch glue that invokes Python
  gates, not plugin validation, packaging, install, release, or runtime logic.
- Test payload evidence remains fixture/source-checkout evidence only and does
  not select, publish, or cut over generated release payloads.
- Active-path guard coverage fails on active Bash, `.sh`, `jq`, shell parsing,
  shell interpolation, `shell=True`, `os.system`, command-string subprocess
  use, Git Bash, WSL, and PowerShell helper regressions.

### Success Criteria

XPLAT-007 is successful because PRs #284, #285, #286, and #287 added the gate
package, runner dispatch, Python-authoritative gate operations, CI dispatch
updates, maintainer command updates, promotion records, test payload evidence,
install and release-readiness fixtures, active no-shell guard, focused Layer 4
tests, and full GitHub PR verification without making XPLAT-008 public release
claims.

### Cleanup Note

Archived into project memory on 2026-07-05 after the final XPLAT-007 PR #287
merged at `0ff2d8d731698cde02b334cdc3b2a377216b5d45`. The active
`specs/xplat-007-python-tooling-and-release-gate-migration/` folder was removed
from `specs/**` in post-merge cleanup after preserving contract schemas under
`tests/speckit-pro/unit/fixtures/runner-gates/contracts/`.
Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-07-05-xplat-007-post-merge-hygiene.md`.
