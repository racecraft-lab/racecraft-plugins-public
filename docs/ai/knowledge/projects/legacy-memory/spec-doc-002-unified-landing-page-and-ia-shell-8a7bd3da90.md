---
type: "speckit-legacy-memory-record"
title: "DOC-002 Unified Landing Page and IA Shell"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-8a7bd3da901426e6"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-002 Unified Landing Page and IA Shell

[Source: .specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md]
**Branch**: `codex/doc-002-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-14

### Summary

DOC-002 created the first usable Astro/Starlight docs-site shell for Racecraft
Public Plugins. It added the `docs-site/` package/config baseline, pnpm lockfile,
landing page, Diataxis sidebar groups, all 11 top-level route shells, a
source-vs-generated-payload explanation, Pages-ready base-path handling, and
internal-link validation through `starlight-links-validator`.

### User Stories

- First-time users can understand the marketplace, `speckit-pro`, supported
  platforms, and next steps from the first page.
- Users can navigate Tutorials, How-to, Reference, and Explanation routes through
  the docs shell.
- Maintainers can validate the shell with docs-site check/build/link scripts
  before later content specs fill in full platform guidance.

### Acceptance Criteria

- AC-2.1: Landing page states marketplace purpose, current plugin, primary
  value, and supported platforms in one screen.
- AC-2.2: IA exposes Tutorials, How-to, Reference, and Explanation sections.
- AC-2.3: Claude Code and Codex paths are selectable from the first interaction.
- AC-2.4: Docs distinguish authoring source `speckit-pro/` from generated
  install payloads under `dist/claude/**` and `dist/codex/**`.
- AC-2.5: Every top-level nav label has a stated purpose and success criterion.

### Cleanup Note

`specs/doc-002-unified-landing-page-and-ia-shell` was removed from active
`specs/**` cleanup after PRs #173-#177 merged and recovery commands were
recorded in
`.specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md`.

---
