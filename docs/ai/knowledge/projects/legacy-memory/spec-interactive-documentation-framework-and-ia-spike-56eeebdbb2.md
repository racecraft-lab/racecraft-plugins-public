---
type: "speckit-legacy-memory-record"
title: "Interactive documentation framework and IA spike"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-56eeebdbb24c5131"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Interactive documentation framework and IA spike

[Source: specs/doc-001-static-docs-framework-and-ia-spike]
**Branch**: `doc-001-static-docs-framework-and-ia-spike` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

DOC-001 selected **Astro with Starlight** as the default stack for the future
interactive documentation site, with **pnpm** as the report-only package manager
recommendation for DOC-002. The canonical decision record is
`docs/ai/research/interactive-documentation-framework-spike.md`.

The spike compared Docusaurus/MDX, VitePress, Astro/Starlight, and a
repo-native Markdown fallback across static hosting, GitHub Pages deployment,
reusable component interactivity, search, versioning, accessibility, link
checking, docs-as-code workflow fit, maintenance load, package/build/test
command roles, and support class. Docusaurus/MDX remains the first fallback if a
true Astro/Starlight hard blocker appears during DOC-002.

### User Stories

- Maintainers can review one source-backed framework recommendation and see why
  alternatives were rejected or deferred.
- DOC-002 implementers can consume a route-level Diataxis IA skeleton and
  report-only command handoff without reopening stack selection.
- Reviewers can verify the spike remained research-only and did not add a site
  scaffold, package file, lockfile, CI workflow, generated payload, marketplace
  file, README migration, or plugin behavior change.

### Functional Requirements Captured

- Compare all four required candidates with current source evidence and support
  classes.
- Recommend one default stack for DOC-002 unless a hard blocker is recorded.
- Explain non-selected alternatives and fallback order.
- Record package manager, setup, install, development preview, production
  build, local static preview, deployment, and minimum validation command roles.
- Provide an 11-route IA skeleton covering Start, Install: Claude Code, Install:
  Codex, First Run, Choose Your Path, Reference, Troubleshooting, Security &
  Trust, Contribute & Release, Spec Kit Lifecycle, and Glossary.
- Keep DOC-001 research-only and defer docs-site implementation to DOC-002 or
  later DOC specs.

### Entities

- **Framework Candidate**: Docusaurus/MDX, VitePress, Astro/Starlight, or the
  repo-native fallback.
- **Evaluation Criterion**: A scored comparison dimension such as hosting,
  interactivity, search, versioning, accessibility, link checking, workflow fit,
  maintenance load, and commands.
- **IA Route**: A top-level documentation path with Diataxis mode, audience,
  purpose, source evidence, success criterion, shell owner, and content owner.
- **Spike Report**: The durable research artifact that records evidence,
  recommendation, IA, commands, non-goals, and verification scope.

### Edge Cases

- Temporarily unavailable framework docs require recorded evidence gaps rather
  than stale claims.
- If all candidates fail GitHub Pages from this repository, the report must
  record the blocker and use the least-risk fallback.
- Third-party or paid support must be distinguished from built-in or official
  first-party support.
- Conflicting source evidence must prefer the most current official source and
  record the conflict.
- IA routes without source evidence or measurable success criteria must be
  revised or omitted.

### Success Criteria

- The report covers 4 candidate stacks across at least 10 evaluation dimensions.
- A maintainer can identify the recommended stack and alternative rationales in
  under 5 minutes.
- The IA skeleton has no placeholder route values and includes every required
  route field.
- DOC-002 can identify package manager and minimum command roles from the report
  alone.
- The final DOC-001 diff changed 0 package, lockfile, site config, prototype,
  CI, README/plugin README migration, marketplace, generated payload, or plugin
  behavior files.

### Cleanup Note

`specs/doc-001-static-docs-framework-and-ia-spike` was removed from active
`specs/**` cleanup after PR #163 merged and recovery commands were recorded in
`.specify/memory/archive-reports/2026-06-13-doc-001-post-merge-hygiene.md`.

---
