---
type: "speckit-legacy-memory-record"
title: "DOC-001 interactive documentation framework and IA spike"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-b0ee696dc689de7d"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-001 interactive documentation framework and IA spike

[Source: .specify/memory/archive-reports/2026-06-13-doc-001-post-merge-hygiene.md]
**Branch**: `codex/doc-001-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-13

### Scope

DOC-001 was a research-only spike. It selected Astro/Starlight, recorded
report-only DOC-002 package/build/test command roles, and produced the route
level IA handoff for the interactive documentation roadmap.

### Architecture / Approach

- Keep the durable recommendation in
  `docs/ai/research/interactive-documentation-framework-spike.md`.
- Treat the merged PR #163 commit as the recovery authority for raw SpecKit
  artifacts under `specs/doc-001-static-docs-framework-and-ia-spike/**`.
- Preserve DOC-001 workflow/process notes under `docs/ai/specs/.process/`.
- Remove only the completed active spec folder from `specs/**`.
- Mark DOC-001 complete in the interactive documentation roadmaps and
  traceability matrix so DOC-002 can start from the accepted Astro/Starlight
  recommendation and IA skeleton.
- Regenerate the roadmap-MOC generated INDEX after removing the active spec
  folder so generated links do not point to archived specs.

### Test Strategy

- Verify JSON state files parse.
- Verify no active `specs/**` feature directories remain after cleanup.
- Verify no generated roadmap-MOC link points at the removed DOC-001 spec
  folder.
- Run `bash tests/speckit-pro/run-all.sh` after cleanup.

### Cleanup Notes

`specs/doc-001-static-docs-framework-and-ia-spike` was removed from active
`specs/**` cleanup after PR #163 merged. No test fixture or production script
depended on the live DOC-001 spec folder.

---
