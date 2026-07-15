---
type: "speckit-legacy-memory-record"
title: "XPLAT-005 Read-Only Helper Port"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-5c440dc6c15f2d97"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-005 Read-Only Helper Port

[Source: specs/xplat-005-read-only-helper-port]

XPLAT-005 shipped the first real helper behavior ports onto the Python
standard-library runner. It added an explicit read-only helper registry,
runner dispatch for prerequisite, detection, marker-count, gate, reviewability,
confidence, topology, atomicity, layer-planning, spec-index check, workflow
contract, and PR-packet validation-only behavior, plus helper promotion records
that distinguish Python-authoritative helpers from Bash-reference-only and
out-of-scope mutation helpers.

The feature preserves the XPLAT-004 JSON envelope, stdout/stderr/exit-code
contract, typed path handling, shell-disabled subprocess policy, and
source-checkout runner metadata. It deliberately avoids active Claude Code or
Codex skill/hook/generated-payload/install cutover, public platform claims,
write/regenerate modes, PR body generation, PR emission, split state, restack,
artifact relocation, install repair, autoheal, and user-local mutation work.

### Requirements Preserved

- Read-only/advisory helpers have deterministic runner equivalents with
  bounded JSON responses, diagnostics, remediation text, and exit mappings.
- Source-checkout Bash helpers remain temporary references for parity through
  XPLAT-007.
- Helper request fixtures, Bash-reference comparisons, synthetic path cases,
  and malformed-input coverage are committed under the Layer 4 fixture tree.
- Scope evidence records zero active Claude/Codex cutover and zero
  mutation-helper promotion, except bounded PR-review packet rendering
  remediation needed to describe the real XPLAT-005 feature scope.

### Success Criteria

XPLAT-005 is successful because PR #276 added the read-only helper registry,
runner helper ports, Python-authoritative promotion records, parity fixtures,
runner metadata refresh, and Layer 4 helper gates without switching installed
plugin invocation paths or making public native-platform support claims.
XPLAT-006 is now unblocked for mutation, install, and PR-emission helper ports.

### Cleanup Note

Archived into project memory on 2026-07-03 after PR #276 merged at
`c4642f50ae99172170798a49f0c8fd990891c0f9`. The active
`specs/xplat-005-read-only-helper-port/` folder was removed from `specs/**` in
post-merge cleanup after preserving the helper parity spec inputs under
`tests/speckit-pro/unit/fixtures/read-only-helpers/read-only-helper-feature/`.
Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-07-03-xplat-005-post-merge-hygiene.md`.
