---
type: "speckit-legacy-memory-record"
title: "XPLAT-005 Read-Only Helper Port"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-467ced540695346d"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-005 Read-Only Helper Port

[Source: specs/xplat-005-read-only-helper-port]

XPLAT-005 implemented the bounded read-only/advisory helper migration on top of
the XPLAT-004 runner. The production surface lives under
`speckit-pro/speckit_pro_runner/helpers/` and extends the runner envelope,
runtime metadata, and dispatch path without changing active installed-plugin
invocation surfaces.

### Technical Approach

- Add a small explicit helper registry rather than dynamic discovery, so
  mutation helpers cannot be exposed by accident.
- Group read-only behavior in `helpers/read_only.py` and preserve current Bash
  helper argv shape, stdout/stderr text, JSON stdout semantics, and exit codes
  through source-checkout Bash-reference comparisons.
- Classify each helper as `python_authoritative`, `bash_reference_only`, or
  `out_of_scope` with authoritative request fixtures and rollback notes.
- Keep `generate-spec-index` limited to `--check` and keep
  `validate-pr-packet` limited to read-only validation output; write,
  persistence, and PR-body generation remain downstream.
- Refresh runner manifest/checksum metadata for the new helper source files.
- Preserve fixture inputs under
  `tests/speckit-pro/unit/fixtures/read-only-helpers/` so Layer 4
  remains runnable after the active XPLAT-005 spec folder is archived.

### Testing Strategy

XPLAT-005 verification uses the read-only helper Layer 4 entrypoint,
`bash tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.sh`,
the runner Layer 4 entrypoint, `bash tests/speckit-pro/run-all.sh --layer 4`,
Layer 1 structural validation, spec-index checks, JSON validation, diff
hygiene, PR-packet validation, workflow-contract validation, and a local macOS
source-checkout runtime-info smoke through the runner fixture suite. Native
installed-cache UAT, generated payload propagation, update/autoheal proof,
mutation-helper verification, and public claim validation remain XPLAT-006 and
XPLAT-007 responsibilities.

### Cleanup Notes

`specs/xplat-005-read-only-helper-port` was removed from active `specs/**` in
the post-merge cleanup after PR #276 merged. Recovery commands and provenance
are recorded in the XPLAT-005 archive report. Minimal spec inputs needed by
helper parity tests were copied to the read-only helper fixture tree before
cleanup.
