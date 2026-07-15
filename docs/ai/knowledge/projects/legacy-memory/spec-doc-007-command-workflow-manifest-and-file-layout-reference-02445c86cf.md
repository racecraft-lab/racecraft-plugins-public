---
type: "speckit-legacy-memory-record"
title: "DOC-007 Command, workflow, manifest, and file-layout reference"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-02445c86cf41abd9"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-007 Command, workflow, manifest, and file-layout reference

[Source: .specify/memory/archive-reports/2026-06-17-doc-007-post-merge-hygiene.md]
**Branch**: `codex/doc-007-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-17

### Summary

DOC-007 added a deterministic generated reference library for the public docs
site. It covers SpecKit Pro skill surfaces, agents and subagents, manifests,
hooks, scripts, tests, and source-vs-dist layout with stable deep links,
source citations, and explicit inferred notes.

### User Stories And Requirements

- Users can look up plugin commands, skills, manifests, and generated payload
  responsibilities from stable documentation links.
- Maintainers can regenerate reference pages and detect drift before generated
  docs fall behind source files.
- Agents can cite exact source and generated payload paths when answering
  workflow, install, or troubleshooting questions.
- Reference pages separate checked source facts from inferred guidance.
- Existing install, first-run, lifecycle, and choose-your-path routes link into
  the reference library instead of duplicating full inventories.

### Edge Cases

- Missing source files are caught by reference generation and docs validation.
- Source-only and generated-payload-only paths remain separate so install docs
  do not tell users to install the mixed authoring tree.
- Source facts and inferred notes remain visibly distinct to reduce accidental
  overstatement.

### Success Criteria

- Generated reference pages exist for skills, agents, manifests, hooks,
  scripts, tests, and source-vs-dist layout.
- Docs validation runs the reference check.
- Existing docs routes deep-link into the generated reference pages.
- Every generated local reference is backed by a checked file path.

### Cleanup Note

The DOC-007 workflow evidence folder was removed from active `specs/**`
cleanup after PR #208 merged. Recovery commands and provenance are recorded in
the DOC-007 archive report.

---
