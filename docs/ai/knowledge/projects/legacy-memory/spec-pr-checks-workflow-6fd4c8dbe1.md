---
type: "speckit-legacy-memory-record"
title: "PR Checks Workflow"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-6fd4c8dbe13b60f8"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# PR Checks Workflow

[Source: specs/002-pr-checks-workflow]
**Branch**: `002-pr-checks-workflow` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added the pull-request validation workflow: plugin change detection, matrix
testing, conventional PR title validation, SHA-pinned checkout usage, skip-safe
docs-only behavior, and reviewer-readable failure annotations. The shipped
contract lives in `.github/workflows/pr-checks.yml`.

### Cleanup Note

The active spec folder was removed after PR #2 merge provenance and recovery
commands were recorded.

---
