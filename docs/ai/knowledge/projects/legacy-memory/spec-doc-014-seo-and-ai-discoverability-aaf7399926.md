---
type: "speckit-legacy-memory-record"
title: "DOC-014 SEO and AI Discoverability"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-aaf7399926ea037b"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-014 SEO and AI Discoverability

[Source: specs/doc-014-seo-and-ai-discoverability]

DOC-014 shipped the docs-site discoverability baseline before public launch
while preserving the staging noindex guard. It added a dynamic three-tier
crawler-access policy, `starlight-llms-txt` whole-site digests, per-page
Markdown routes, JSON-LD route-data injection, per-page Open Graph cards,
git-backed sitemap freshness, visible last-updated behavior, meta descriptions
for all content pages, a quality gate requiring descriptions, focused SEO
Playwright coverage, and the AI-discoverability success metric document. DOC-012
still owns the public custom-domain/indexing launch; DOC-015 owns prose and
meta-description quality refresh.

Cleanup note: archived on 2026-06-29 after PR #264 merged at
`6c24f56885f09755dd85e0a451deb923e5ef437a`. The active
`specs/doc-014-seo-and-ai-discoverability/` folder was removed; recovery
commands are recorded in
`.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`.
