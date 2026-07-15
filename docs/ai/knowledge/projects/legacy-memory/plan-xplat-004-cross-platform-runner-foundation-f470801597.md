---
type: "speckit-legacy-memory-record"
title: "XPLAT-004 Cross-Platform Runner Foundation"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-f470801597d89498"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-004 Cross-Platform Runner Foundation

[Source: specs/xplat-004-cross-platform-runner-foundation]

XPLAT-004 implemented the small Python standard-library runner foundation
required before helper parity work can begin. The source package lives under
`speckit-pro/speckit_pro_runner/` and is invoked with
`<python> -m speckit_pro_runner` from a source checkout using JSON stdin/stdout.
It includes envelope helpers, runtime/preflight reporting, deterministic
diagnostics, typed path records, source metadata verification, and
shell-disabled subprocess fixture records.

### Technical Approach

- Keep the runner source inside the `speckit-pro/` plugin package with no new
  runtime dependency beyond Python 3.11+ standard library and the official
  Spec Kit / `specify` prerequisite boundary.
- Preserve XPLAT-002 JSON envelope, path, subprocess, diagnostic, and exit-code
  contract shape for downstream helper ports.
- Implement only `runtime-info`, `preflight`, and synthetic fixture behavior in
  XPLAT-004; real read-only helpers move to XPLAT-005 and mutation/install/PR
  helpers move to XPLAT-006.
- Store runner identity and checksum metadata in
  `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and
  `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`.
- Preserve the Windows/Linux source-checkout runbook fixture contract under the
  Layer 4 fixture tree so tests do not depend on active `specs/**` content
  after archive cleanup.
- Preserve the changed-files fallback fixture under the Layer 4 fixture tree so
  no-cutover assertions remain runnable when Git diff context is unavailable.

### Testing Strategy

XPLAT-004 verification uses the runner-specific Layer 4 entrypoint,
`bash tests/speckit-pro/run-all.sh --layer 4`, Layer 1 structural validation,
the default deterministic suite, spec-index checks, diff hygiene, manifest JSON
validation, PR-packet validation, and G7 task validation. Native installed-cache
UAT, generated payload propagation, update/autoheal proof, and public claim
validation remain XPLAT-007 responsibilities.

### Cleanup Notes

`specs/xplat-004-cross-platform-runner-foundation` was removed from active
`specs/**` in the post-merge cleanup after PR #274 merged. Recovery commands
and provenance are recorded in the XPLAT-004 archive report.
