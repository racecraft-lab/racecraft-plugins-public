---
type: "speckit-legacy-memory-record"
title: "XPLAT-004 Cross-Platform Runner Foundation"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-890c565ab416c201"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-004 Cross-Platform Runner Foundation

[Source: specs/xplat-004-cross-platform-runner-foundation]

XPLAT-004 shipped the first implementation slice for the cross-platform runtime
lane. It added a source-checkout Python 3.11+ standard-library runner package at
`speckit-pro/speckit_pro_runner/`, module-style invocation through
`<python> -m speckit_pro_runner`, JSON request/response envelope validation,
`runtime-info` and `preflight` operations, deterministic diagnostics, typed
path records, shell-disabled subprocess fixture records, platform/plugin-root
detection, and runner source metadata checks.

The runner records identity and integrity through
`speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and
`speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`. The Layer 4 runner
test suite and fixtures live under `tests/speckit-pro/unit/`,
including the archived runbook fixture contract now preserved at
`tests/speckit-pro/unit/fixtures/speckit-pro-runner/platform-runbook-fixtures.md`
and the changed-files fallback fixture at
`tests/speckit-pro/unit/fixtures/speckit-pro-runner/runner-foundation-changed-files.txt`.

### Requirements Preserved

- Accept versioned JSON requests and emit one JSON stdout response with
  line-delimited JSON stderr diagnostics.
- Report source-checkout runtime identity, Python version, platform,
  architecture, plugin root, `specify` availability, metadata pointers, and
  runner identity through `runtime-info` and `preflight`.
- Fail closed for invalid JSON, unsupported schema, missing fields, unsupported
  operations, missing Python 3.11+, missing `specify`, missing plugin root, and
  invalid runner metadata.
- Keep contract fixtures synthetic; no existing helpers were ported in
  XPLAT-004.
- Preserve explicit non-claim boundaries: installed-cache launch proof, native
  UAT, generated payload propagation, active Claude/Codex cutover, and public
  platform support claims remain downstream work.

### Success Criteria

XPLAT-004 is successful because PR #274 added the runner foundation, manifest
and checksum metadata, contract fixtures, Layer 4 tests, and verification
evidence without switching active skills, hooks, generated payloads, install
behavior, or public documentation claims. XPLAT-005 is now unblocked for
read-only helper parity.

### Cleanup Note

Archived into project memory on 2026-07-01 after PR #274 merged at
`cef3ed260dabf73833d3de82f82cacdb2c7758fa`. The active
`specs/xplat-004-cross-platform-runner-foundation/` folder was removed from
`specs/**` in post-merge cleanup. Recovery commands and provenance are recorded
in `.specify/memory/archive-reports/2026-07-01-xplat-004-post-merge-hygiene.md`.
