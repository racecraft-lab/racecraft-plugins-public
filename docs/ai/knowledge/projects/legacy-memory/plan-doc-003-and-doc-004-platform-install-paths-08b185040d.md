---
type: "speckit-legacy-memory-record"
title: "DOC-003 and DOC-004 platform install paths"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-08b185040dcceed9"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-003 and DOC-004 platform install paths

[Source: .specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md]
**Branch**: `codex/doc-003-004-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-15

### Scope

DOC-003 and DOC-004 completed the platform-specific install tier for the
interactive documentation roadmap. DOC-003 owns the Claude Code install route;
DOC-004 owns the Codex install route, README alignment, generated payload
documentation sync, and Codex custom-agent registration guidance.

### Architecture / Approach

- Keep `docs-site/src/content/docs/install/claude-code.md` and
  `docs-site/src/content/docs/install/codex.md` structurally aligned while
  preserving platform-specific commands and trust boundaries.
- Retain historical workflow/process evidence under `docs/ai/specs/.process/`.
- Record recovery commands before removing active spec folders.
- Regenerate the roadmap-MOC generated INDEX after cleanup so active links do
  not point at archived spec folders.

### Test Strategy

- Confirm PR #187 and PR #186 are merged to `main`.
- Validate JSON state files after rewriting archive state.
- Regenerate and check SpecKit generated indexes.
- Verify active `specs/**` contains only `specs/.gitkeep` after cleanup.
- Run docs-site validation and the deterministic SpecKit test suite.

### Cleanup Notes

`specs/doc-003-claude-code-marketplace-installation-path` and
`specs/doc-004-codex-marketplace-installation-path` were removed from active
`specs/**` cleanup after PR #187 and PR #186 merged. Recovery commands and
provenance are recorded in the DOC-003/DOC-004 archive report.

---
