---
type: "speckit-legacy-memory-record"
title: "DOC-007 Command, Workflow, Manifest, and File-Layout Reference"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-b8db58fc4354f0f1"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-007 Command, Workflow, Manifest, and File-Layout Reference

[Source: .specify/memory/archive-reports/2026-06-17-doc-007-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-17
- **Cleanup branch**: `codex/doc-007-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/doc-007-command-workflow-manifest-and-file-layout-reference`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/doc-007-command-workflow-manifest-and-file-layout-reference`

### Provenance

| PR | Title | Merge commit | Tree reference |
|----|-------|--------------|----------------|
| #208 | `docs(DOC-007): add generated reference pages` | `2f5ee096e903723e1ab0133c699bda5a22ae2172` | `67d3b8890b09605150b9cf300543d7a7ba517045` |

### Summary

DOC-007 completed the generated reference library for skills, agents,
manifests, hooks, scripts, tests, and source-vs-dist layout. The canonical
shipped docs and validation files are:

- `docs-site/scripts/generate-reference-pages.mjs`
- `docs-site/src/content/docs/reference.md`
- `docs-site/src/content/docs/reference/skills.md`
- `docs-site/src/content/docs/reference/agents.md`
- `docs-site/src/content/docs/reference/manifests.md`
- `docs-site/src/content/docs/reference/hooks.md`
- `docs-site/src/content/docs/reference/scripts.md`
- `docs-site/src/content/docs/reference/tests.md`
- `docs-site/src/content/docs/reference/source-vs-dist.md`

This cleanup also added `speckit-archive-cleanup` as a plugin skill so future
post-merge archive hygiene can be invoked directly.

### Recovery Commands

```text
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/spec.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/plan.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/tasks.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/SPEC-MOC.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/contracts/reference-generator.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/contracts/reference-inventory.schema.json
git checkout 2f5ee096e903723e1ab0133c699bda5a22ae2172 -- specs/doc-007-command-workflow-manifest-and-file-layout-reference
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-17-doc-007-post-merge-hygiene.md`.
