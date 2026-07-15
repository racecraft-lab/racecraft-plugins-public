---
type: "speckit-project-map"
title: "Interactive Documentation Roadmap - Map of Content"
description: "Durable project map for Interactive Documentation Roadmap - Map of Content."
resource: "docs/ai/specs/interactive-documentation-technical-roadmap.md"
tags: ["project-map","speckit"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "interactive-documentation"
x-speckit-project: "interactive-documentation"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-rank: 1
x-speckit-legacy-status: "DOC-001 through DOC-011 plus DOC-013 and DOC-014 archived; DOC-012 and DOC-015 through DOC-021 pending"
x-speckit-sources: ["docs/ai/specs/interactive-documentation-technical-roadmap.md|27a779c853b8b63ba4e7b7bf0deeb31855b86ea3dead5131a886fdf1d5914128"]
x-speckit-migration-sources: ["docs/ai/specs/interactive-documentation-roadmap-MOC.md|c0119252529b2a7b1ec3c3e484e56de604189e33f92b04ac51541cf446238fa9"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
x-speckit-legacy-view: "docs/ai/specs/interactive-documentation-roadmap-MOC.md"
x-speckit-legacy-up: "[Interactive Documentation Roadmap](interactive-documentation-technical-roadmap.md)"
x-speckit-legacy-related: ["[PRD](../../prd-interactive-documentation.md)","[Traceability](../../traceability-interactive-documentation.md)"]
---
# Interactive Documentation Roadmap - Map of Content

Source of truth: `docs/ai/specs/interactive-documentation-technical-roadmap.md`.

## Curated map

Navigation map for the Racecraft interactive documentation roadmap.

## Epics (curated)

### Foundation

- DOC-001: Static docs framework and IA spike
- DOC-002: Unified landing page and IA shell

**Why:** Select the site stack and establish the task-first navigation shell before adding platform-specific content.

### Activation

- DOC-003: Claude Code marketplace installation path
- DOC-004: Codex marketplace installation path
- DOC-005: First successful workflow tutorial and lifecycle explainer
- DOC-006: Safe interactive selector and validation aids

**Why:** The primary v1 success path is install to first successful `speckit-pro` run across both platforms.

### Trust And Maintenance

- DOC-007: Command, workflow, manifest, and file-layout reference
- [DOC-008: Troubleshooting, security, trust, update, rollback](../../../../../.specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md) (archived after PR #220)
- [DOC-009: Maintainer and contributor release workflow](../../../../../.specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md) (archived after PR #219)

**Why:** Users and contributors need reliable reference, diagnostics, trust boundaries, and release-readiness workflows.

### Quality

- [DOC-010: Search, accessibility, deep links, docs validation](../../../../../.specify/memory/archive-reports/2026-06-19-doc-010-post-merge-hygiene.md) (archived after PRs #232-#236)

**Why:** The site needs findability, accessibility, stable support links, responsive behavior, and CI checks after the main content exists.

### Production Readiness

- [DOC-011: GitHub Pages build-and-deploy pipeline](../../../../../.specify/memory/archive-reports/2026-06-23-doc-011-post-merge-hygiene.md) (archived after PR #243)
- [DOC-014: SEO and AI discoverability](../../../../../.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md) (archived after PR #264)

**Why:** The site now has a staging deploy workflow, non-indexing guard, and
discoverability metadata/crawler surfaces. DOC-012 remains the final
custom-domain and public-indexing launch gate.
