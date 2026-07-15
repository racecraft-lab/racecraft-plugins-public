---
type: "speckit-legacy-memory-record"
title: "Generated index/PRs/backlinks + status integration + phase-gate regen"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-87016f8108be4606"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Generated index/PRs/backlinks + status integration + phase-gate regen

[Source: specs/prsg-003-spec-index]
**Branch**: `prsg-003-spec-index` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added deterministic spec index regeneration: generated INDEX, PRS, and BACKLINKS
zones, whole-zone sentinel replacement, stale generated-zone protection, status
integration, and phase-gate regen hooks. The generator and fixtures now carry the
behavior; the active source spec folder is no longer required.

### Cleanup Note

The active spec folder was removed after PR #121 merge provenance and recovery
commands were recorded.

---
