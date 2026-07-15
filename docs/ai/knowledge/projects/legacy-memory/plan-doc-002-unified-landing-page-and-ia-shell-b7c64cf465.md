---
type: "speckit-legacy-memory-record"
title: "DOC-002 Unified Landing Page and IA Shell"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-b7c64cf46559ed33"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-002 Unified Landing Page and IA Shell

[Source: .specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md]
**Branch**: `codex/doc-002-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-14

### Scope

DOC-002 converted the DOC-001 Astro/Starlight recommendation and route-level IA
handoff into a concrete docs-site shell. It created the `docs-site/` package,
config, lockfile, content collection, landing page, 11 route shells, sidebar
groups, Pages-ready base path, and link-validation scripts.

### Architecture / Approach

- Use Astro with Starlight under `docs-site/`.
- Keep root README and plugin README as source evidence only.
- Use Pages-base absolute links for GitHub Pages compatibility and
  `starlight-links-validator` compatibility.
- Keep shell content skeletal where DOC-003 through DOC-010 own full content.
- Preserve the source tree versus generated install payload distinction on the
  landing/reference surfaces.

### Test Strategy

- `cd docs-site && pnpm check`
- `cd docs-site && pnpm build`
- `cd docs-site && pnpm validate:links`
- `cd docs-site && pnpm validate`
- In-app browser UAT across all 11 docs routes.
- `bash tests/speckit-pro/run-all.sh`

### Cleanup Notes

`specs/doc-002-unified-landing-page-and-ia-shell` was removed from active
`specs/**` cleanup after PRs #173-#177 merged. The original T041 PR-packet task
remains a historical unchecked task because PR #177 fixed the autopilot
continuation bug that caused the packet path to pause.

---
