---
type: "speckit-legacy-memory-record"
title: "DOC-010 Search, Accessibility, Deep Links, Docs Validation"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-57b7d7afa1476cab"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-010 Search, Accessibility, Deep Links, Docs Validation

[Source: specs/doc-010-search-accessibility-deep-links-docs-validation]
**Branch**: `doc-010-search-accessibility-deep-links-docs-validation` · **Status**: Completed · **Archived**: 2026-06-19

### Summary

DOC-010 completed the final interactive documentation hardening slice. It keeps
the existing Astro/Starlight and Starlight/Pagefind search stack, improves
support-oriented findability, stabilizes shareable anchors and generated
reference links, improves accessible interactive-aid and static fallback
behavior, and adds deterministic docs-site validation plus compact Playwright
smoke evidence.

### User Stories

- **US1 - Find and share support guidance.** First-time users, support
  responders, and maintainers can search, browse glossary entries, and share
  stable links to install, troubleshooting, reference, and release workflow
  content.
- **US2 - Use interactive aids accessibly.** Keyboard and screen-reader-oriented
  users can use `SafeInstallAids` and `LifecycleFlow`, or their static
  fallbacks, without pointer-only or inaccessible dynamic behavior.
- **US3 - Run one matching docs validation path.** Maintainers and contributors
  can run `pnpm --dir docs-site validate` locally and see a matching
  conditional `validate-docs` PR Checks gate.
- **US4 - Review minimal browser evidence.** Reviewers can inspect compact
  desktop and mobile smoke evidence for the six logical DOC-010 routes without
  reviewing a broad visual snapshot suite.

### Functional Requirements

- Preserve the existing docs-site stack, routes, and search provider.
- Provide stable support anchors and deterministic link/anchor validation for
  install, recovery, troubleshooting, glossary, generated reference, and release
  workflow content.
- Preserve or improve keyboard navigation, visible focus, labels, semantic
  controls, polite status announcements, responsive behavior, and static
  fallback content in the interactive docs aids.
- Provide one local docs validation path that runs generated reference checks,
  Astro checks, build/link validation, safe-aids validation, docs-quality
  validation, and minimal Playwright smoke.
- Add a `validate-docs` PR Checks job that uses job-level changed-file
  detection and preserves plugin matrix semantics for plugin-only changes.
- Keep automated validation within checked-in source and local preview
  boundaries; do not execute install snippets, inspect local user state, follow
  marketplace flows, submit analytics, or perform destructive behavior.

### Success Criteria

- DOC-010 designated support anchors, glossary terms, generated reference
  sections, troubleshooting entries, and release workflow details have stable
  links or intentional exceptions.
- Interactive aids retain essential guidance through keyboard-friendly controls
  and static fallback content.
- Local and CI docs validation cover generated references, site checks,
  safe-aids validation, docs-quality validation, and bounded browser smoke.
- Compact browser smoke covers `/`, `/choose-your-path/`,
  `/spec-kit-lifecycle/`, `/glossary/`, `/reference/skills/`, and
  `/contribute-and-release/` across desktop and mobile.
- PR packet evidence records validation, manual accessibility evidence, compact
  smoke artifact behavior, known gaps, automation-safety notes, and rollback
  guidance.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup after PRs #232
through #236 merged. Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-19-doc-010-post-merge-hygiene.md`.
