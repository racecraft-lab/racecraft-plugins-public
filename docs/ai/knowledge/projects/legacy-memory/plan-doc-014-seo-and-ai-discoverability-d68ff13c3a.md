---
type: "speckit-legacy-memory-record"
title: "DOC-014 SEO and AI Discoverability"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-d68ff13c3ae8a0a4"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-014 SEO and AI Discoverability

[Source: specs/doc-014-seo-and-ai-discoverability]

DOC-014 was a docs-site infrastructure slice on Astro/Starlight. It added
static build-time discoverability outputs: crawler policy, llms digests,
per-page Markdown, schema graph, OG cards, sitemap freshness, descriptions,
quality validation, and SEO Playwright tests. New dependencies were
`starlight-llms-txt`, `astro-og-canvas` plus CanvasKit, and `@astrojs/sitemap`.
Verification used the docs-site validation path and SEO-specific Playwright
coverage. The noindex staging guard remains until DOC-012.

Cleanup note: the active spec folder was removed after PR #264 merged. Recovery
commands and provenance are recorded in the completed-active-specs archive
report.
