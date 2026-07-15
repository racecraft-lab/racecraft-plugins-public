---
type: "speckit-legacy-memory-record"
title: "DOC-007 command, workflow, manifest, and file-layout reference"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-d16ab59e1882762d"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-007 command, workflow, manifest, and file-layout reference

[Source: .specify/memory/archive-reports/2026-06-17-doc-007-post-merge-hygiene.md]
**Branch**: `codex/doc-007-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-17

### Scope

DOC-007 completed the reference-library tier for the interactive documentation
roadmap. It owns generated reference pages for skills, agents, manifests,
hooks, scripts, tests, and source-vs-dist layout, plus the deterministic
generator and reference check used by docs validation.

### Architecture / Approach

- Build reference pages from checked-in source files rather than hand-copying
  large inventories into docs content.
- Keep one generator at `docs-site/scripts/generate-reference-pages.mjs`.
- Write generated Markdown under `docs-site/src/content/docs/reference/`.
- Use source citations and inferred notes so reference pages distinguish
  repository facts from practical guidance.
- Link install, first-run, lifecycle, and safe-path docs into generated
  reference anchors.
- Add the `speckit-archive-cleanup` plugin skill so future post-merge archive
  hygiene follows this same branch, memory, cleanup, generation, and
  verification pattern.

### Test Strategy

- Confirm PR #208 merged to `main`.
- Validate JSON state after replacing active DOC-007 autopilot state.
- Regenerate and check SpecKit generated indexes.
- Verify active `specs/**` contains only expected active specs after cleanup.
- Regenerate and check docs-site reference pages.
- Rebuild generated plugin payloads after adding the new skill.
- Run docs-site validation, docs-site link validation, and the deterministic
  SpecKit test suite.

### Cleanup Notes

`specs/doc-007-command-workflow-manifest-and-file-layout-reference` was removed
from active `specs/**` cleanup after PR #208 merged. Recovery commands and
provenance are recorded in the DOC-007 archive report.
