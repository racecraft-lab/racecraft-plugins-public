---
type: "speckit-legacy-memory-record"
title: "Deterministic UAT Runbook Skeleton + PR Body Integration"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-e9c54467af442c06"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Deterministic UAT Runbook Skeleton + PR Body Integration

[Source: specs/006a-uat-skeleton]
**Branch**: `006a-uat-skeleton` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added deterministic UAT runbook generation and PR-body embedding: a script that
extracts user stories, FR/SC coverage, rollback, clarification markers, and
self-review context into a stable runbook, plus PR-body compatibility handling.
The full-spec test dependency remains preserved in the vendored
`tests/speckit-pro/unit/fixtures/uat-runbook-generation/full-spec.md` fixture.

### Cleanup Note

The active spec folder was removed after PR #99 merge provenance and recovery
commands were recorded.

---
